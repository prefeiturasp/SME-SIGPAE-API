from datetime import datetime, timedelta

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ...dieta_especial.solicitacao_dieta_especial.models import ClassificacaoDieta
from ...escola.models import EscolaPeriodoEscolar
from ..models import LancamentoDiario
from ..utils import (
    alteracoes_de_cardapio_por_escola_periodo_escolar_e_data,
    eh_feriado_ou_fds,
    matriculados_convencional_em_uma_data,
    matriculados_em_uma_data,
    mes_para_faixa,
    total_kits_lanche_por_escola_e_data,
    total_merendas_secas_por_escola_periodo_escolar_e_data,
)
from .filters import LancamentoDiarioFilter
from .serializers import LancamentoDiarioCreateSerializer, LancamentoDiarioSerializer


class LancamentoDiarioViewSet(ModelViewSet):
    lookup_field = "uuid"
    queryset = LancamentoDiario.objects.all()
    serializer_class = LancamentoDiarioCreateSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = LancamentoDiarioFilter

    def get_serializer_class(self):
        if self.action == "create":
            return LancamentoDiarioCreateSerializer
        return LancamentoDiarioSerializer

    def create(self, request):
        grupos = ["convencional", "grupoA", "grupoB"]

        for grupo in grupos:
            if grupo not in self.request.data:
                continue
            dados_grupo = self.request.data[grupo]
            dados_grupo["data"] = self.request.data["data_lancamento"]
            dados_grupo["escola_periodo_escolar"] = self.request.data[
                "escola_periodo_escolar"
            ]
            dados_grupo["criado_por"] = self.request.user.id
            if grupo != "convencional":
                dados_grupo["tipo_dieta"] = ClassificacaoDieta.objects.get(
                    nome="Tipo " + grupo[-1]
                ).id
            ser = LancamentoDiarioCreateSerializer(data=dados_grupo)
            ser.is_valid(raise_exception=True)
            ser.save()

        return Response("OK")

    @action(detail=False, url_path="por-mes", methods=["get"])
    def por_mes(self, request):
        data_inicial, data_final = mes_para_faixa(self.request.GET["mes"])
        escola_periodo_escolar = EscolaPeriodoEscolar.objects.get(
            uuid=self.request.GET["escola_periodo_escolar"]
        )
        qs = (
            self.get_queryset()
            .filter(
                data__range=(data_inicial, data_final),
                escola_periodo_escolar=escola_periodo_escolar,
            )
            .all()
        )

        datas = [
            data_inicial + timedelta(n)
            for n in range(int((data_final - data_inicial).days + 1))
        ]
        dados_a_retornar = []

        for data in datas:
            try:
                lancamento = qs.get(data=data, tipo_dieta__isnull=True)
                lancamento_serializado = self.get_serializer(lancamento).data
                quantidade_alunos = matriculados_convencional_em_uma_data(
                    escola_periodo_escolar, data
                )
            except LancamentoDiario.DoesNotExist:
                lancamento_serializado = None
                quantidade_alunos = None
            dados_a_retornar.append(
                {
                    "dia": data.day,
                    "eh_feriado_ou_fds": eh_feriado_ou_fds(data),
                    "quantidade_alunos": quantidade_alunos,
                    "lancamento": lancamento_serializado,
                }
            )
        return Response(dados_a_retornar)

    def lancamentos_diarios_com_sobremesa_doce_na_semana(
        self, escola_periodo_escolar, data
    ):
        primeiro_dia_da_semana = data - timedelta(days=data.weekday())
        ultimo_dia_da_semana = data + timedelta(days=6 - data.weekday())
        return LancamentoDiario.objects.filter(
            escola_periodo_escolar=escola_periodo_escolar,
            data__range=(primeiro_dia_da_semana, ultimo_dia_da_semana),
            eh_dia_de_sobremesa_doce=True,
        )

    @action(detail=False, url_path="dados-dia-periodo", methods=["get"])
    def dados_dia_periodo(self, request):
        data = datetime.strptime(self.request.GET["data"], "%d/%m/%Y").date()
        escola_periodo_escolar = EscolaPeriodoEscolar.objects.get(
            uuid=self.request.GET["escola_periodo_escolar"]
        )

        dados_a_retornar = {
            "kits_lanches": total_kits_lanche_por_escola_e_data(
                escola_periodo_escolar.escola, data
            ),
            "merenda_seca": total_merendas_secas_por_escola_periodo_escolar_e_data(
                escola_periodo_escolar, data
            ),
            "troca": alteracoes_de_cardapio_por_escola_periodo_escolar_e_data(
                escola_periodo_escolar, data
            ),
            "tem_sobremesa_doce_na_semana": self.lancamentos_diarios_com_sobremesa_doce_na_semana(
                escola_periodo_escolar, data
            ).count()
            > 0,
            "quantidade_alunos": matriculados_em_uma_data(escola_periodo_escolar, data),
        }

        return Response(dados_a_retornar)
