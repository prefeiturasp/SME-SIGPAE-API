import datetime

from django.core.exceptions import ValidationError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from sme_sigpae_api.cardapio.base.api.serializers import (
    CardapioSerializer,
    CombosVinculoTipoAlimentoSimplesSerializer,
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializer,
    MotivoDRENaoValidaSerializer,
    SubstituicaoDoComboVinculoTipoAlimentoSimplesSerializer,
    TipoAlimentacaoSerializer,
    VinculoTipoAlimentoSimplesSerializer,
)
from sme_sigpae_api.cardapio.base.api.serializers_create import (
    CardapioCreateSerializer,
    ComboDoVinculoTipoAlimentoSimplesSerializerCreate,
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializerCreate,
    SubstituicaoDoComboVinculoTipoAlimentoSimplesSerializerCreate,
    VinculoTipoAlimentoCreateSerializer,
)
from sme_sigpae_api.cardapio.base.models import (
    Cardapio,
    ComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
    MotivoDRENaoValida,
    SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.escola.api.viewsets import PeriodoEscolarViewSet
from sme_sigpae_api.escola.constants import PERIODOS_ESPECIAIS_CEMEI
from sme_sigpae_api.escola.models import Escola, PeriodoEscolar
from sme_sigpae_api.inclusao_alimentacao.models import (
    InclusaoAlimentacaoNormal,
    QuantidadePorPeriodo,
)


class CardapioViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    serializer_class = CardapioSerializer
    queryset = Cardapio.objects.all().order_by("data")

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CardapioCreateSerializer
        return CardapioSerializer


class TipoAlimentacaoViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    serializer_class = TipoAlimentacaoSerializer
    queryset = TipoAlimentacao.objects.all()


class HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    serializer_class = HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializer
    queryset = HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar.objects.all()

    @action(detail=False, url_path="escola/(?P<escola_uuid>[^/.]+)")
    def filtro_por_escola(self, request, escola_uuid=None):
        combos = HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar.objects.filter(
            escola__uuid=escola_uuid
        )
        page = self.paginate_queryset(combos)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializerCreate
        return HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializer


class VinculoTipoAlimentacaoViewSet(
    viewsets.ModelViewSet,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    lookup_field = "uuid"
    serializer_class = VinculoTipoAlimentoSimplesSerializer
    queryset = (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
            ativo=True
        )
    )

    @action(
        detail=False,
        url_path="tipo_unidade_escolar/(?P<tipo_unidade_escolar_uuid>[^/.]+)",
    )
    def filtro_por_tipo_ue(self, request, tipo_unidade_escolar_uuid=None):
        vinculos = (
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                tipo_unidade_escolar__uuid=tipo_unidade_escolar_uuid, ativo=True
            ).order_by("periodo_escolar__posicao")
        )
        page = self.paginate_queryset(vinculos)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def get_vinculos_inclusoes_evento_especifico(
        self, mes, ano, tipo_solicitacao, escola
    ):
        gupos_uuids = (
            InclusaoAlimentacaoNormal.objects.filter(
                data__month=int(mes),
                data__year=int(ano),
                motivo__nome="Evento Específico",
                grupo_inclusao__escola=escola,
                grupo_inclusao__status="CODAE_AUTORIZADO",
            )
            .values_list("grupo_inclusao__uuid", flat=True)
            .distinct()
        )

        periodos_escolares_uuids = escola.periodos_escolares().values_list(
            "uuid", flat=True
        )

        quantidades_por_periodo = QuantidadePorPeriodo.objects.filter(
            grupo_inclusao_normal__uuid__in=gupos_uuids
        ).exclude(periodo_escolar__uuid__in=periodos_escolares_uuids)

        periodos_escolares_uuids = quantidades_por_periodo.values_list(
            "periodo_escolar__uuid"
        ).distinct()
        vinculos = (
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                tipo_unidade_escolar__iniciais=escola.tipo_unidade.iniciais,
                periodo_escolar__nome__in=constants.PERIODOS_INCLUSAO_MOTIVO_ESPECIFICO,
                periodo_escolar__uuid__in=periodos_escolares_uuids,
            )
        )
        return vinculos

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{constants.VINCULOS_INCLUSOES_EVENTO_ESPECIFICO_AUTORIZADAS}",
    )
    def vinculos_inclusoes_evento_especifico_autorizadas(self, request):
        escola_uuid = request.query_params.get("escola_uuid")
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")
        tipo_solicitacao = request.query_params.get("tipo_solicitacao")
        escola = Escola.objects.get(uuid=escola_uuid)
        vinculos = self.get_vinculos_inclusoes_evento_especifico(
            mes, ano, tipo_solicitacao, escola
        )
        serializer = self.get_serializer(vinculos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def trata_inclusao_continua_medicao_inicial(self, request, escola, ano):
        mes = request.query_params.get("mes", None)
        periodos_escolares_inclusao_continua = None
        if mes:
            periodoEscolarViewset = PeriodoEscolarViewSet()
            response = periodoEscolarViewset.inclusao_continua_por_mes(request)
            if response.data and response.data.get("periodos", None):
                periodos_escolares_inclusao_continua = PeriodoEscolar.objects.filter(
                    uuid__in=list(response.data["periodos"].values())
                )
        periodos_para_filtrar = escola.periodos_escolares(ano)
        if periodos_escolares_inclusao_continua:
            periodos_para_filtrar = (
                periodos_para_filtrar | periodos_escolares_inclusao_continua
            )
        return periodos_para_filtrar

    @action(detail=False, url_path="escola/(?P<escola_uuid>[^/.]+)")
    def filtro_por_escola(self, request, escola_uuid=None):
        escola = Escola.objects.get(uuid=escola_uuid)
        ano = request.query_params.get("ano", datetime.date.today().year)
        periodos_para_filtrar = self.trata_inclusao_continua_medicao_inicial(
            request, escola, ano
        )
        
        from sme_sigpae_api.cardapio.utils import ordem_periodos
        from django.db.models import Case, IntegerField, Value, When
        ordem_personalizada = ordem_periodos(escola)
        condicoes_ordenacao = [
            When(periodo_escolar__nome=nome, then=Value(prioridade))
            for nome, prioridade in ordem_personalizada.items()
        ]
        
        if escola.eh_cemei:
            vinculos = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                periodo_escolar__nome__in=PERIODOS_ESPECIAIS_CEMEI,
                tipo_unidade_escolar__iniciais__in=["CEI DIRET", "EMEI"],
            )
        else:
            vinculos = (
                VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                    periodo_escolar__in=periodos_para_filtrar, ativo=True
                )
                .annotate(
                    ordem_personalizada=Case(
                        *condicoes_ordenacao,
                        default=Value(99),  # Valor alto para períodos não listados
                        output_field=IntegerField(),
                    )
                )
                .order_by("ordem_personalizada")
            )
            vinculos = vinculos.filter(tipo_unidade_escolar=escola.tipo_unidade)
        page = self.paginate_queryset(vinculos)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        url_path="atualizar_lista_de_vinculos",
        methods=["put"],
    )
    def atualizar_lista_de_vinculos(self, request):
        try:
            if "vinculos" not in request.data:
                raise AssertionError("vinculos é um parâmetro obrigatório")
            vinculos_from_request = request.data.get("vinculos", [])
            for vinculo in vinculos_from_request:
                vinculo_class = (
                    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar
                )
                instance = vinculo_class.objects.get(uuid=vinculo["uuid"])
                instance.tipos_alimentacao.set(
                    TipoAlimentacao.objects.filter(
                        uuid__in=vinculo["tipos_alimentacao"]
                    )
                )
                instance.save()
            vinculos_uuids = [vinculo["uuid"] for vinculo in vinculos_from_request]
            vinculos = vinculo_class.objects.filter(uuid__in=vinculos_uuids)
            page = self.paginate_queryset(vinculos)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        except AssertionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["GET"], url_path="motivo_inclusao_especifico")
    def motivo_inclusao_especifico(self, request):
        try:
            tipo_unidade_escolar_iniciais = request.query_params.get(
                "tipo_unidade_escolar_iniciais", ""
            )
            if tipo_unidade_escolar_iniciais:
                vinculos = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                    tipo_unidade_escolar__iniciais=tipo_unidade_escolar_iniciais,
                    periodo_escolar__nome__in=constants.PERIODOS_INCLUSAO_MOTIVO_ESPECIFICO,
                )
                serializer = self.get_serializer(vinculos, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                raise ValidationError(
                    "tipo_unidade_escolar_iniciais é obrigatório via query_params"
                )
        except ValidationError as e:
            return Response({"detail": e}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return VinculoTipoAlimentoCreateSerializer
        return VinculoTipoAlimentoSimplesSerializer


class CombosDoVinculoTipoAlimentacaoPeriodoTipoUEViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    lookup_field = "uuid"
    serializer_class = CombosVinculoTipoAlimentoSimplesSerializer
    queryset = ComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return ComboDoVinculoTipoAlimentoSimplesSerializerCreate
        return CombosVinculoTipoAlimentoSimplesSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.pode_excluir():
            return Response(
                data={
                    "detail": "Não pode excluir, o combo já tem movimentação no sistema"
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubstituicaoDoCombosDoVinculoTipoAlimentacaoPeriodoTipoUEViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    lookup_field = "uuid"
    serializer_class = SubstituicaoDoComboVinculoTipoAlimentoSimplesSerializer
    queryset = SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return SubstituicaoDoComboVinculoTipoAlimentoSimplesSerializerCreate
        return SubstituicaoDoComboVinculoTipoAlimentoSimplesSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.pode_excluir():
            return Response(
                data={
                    "detail": "Não pode excluir, o combo já tem movimentação no sistema"
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MotivosDRENaoValidaViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "uuid"
    queryset = MotivoDRENaoValida.objects.all()
    serializer_class = MotivoDRENaoValidaSerializer
