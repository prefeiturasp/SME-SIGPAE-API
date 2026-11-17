import datetime

from django.core.exceptions import ValidationError
from django.db.models import Sum
from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from src.dados_comuns.constants import TIPOS_UNIDADE_ESCOLAR

from ...api.serializers import (
    LogAlunosMatriculadosFaixaEtariaDiaSerializer,
    LogAlunosMatriculadosPeriodoEscolaSerializer,
)
from ...logs.api.filters import LogAlunosMatriculadosFaixaEtariaDiaFilter
from ...models import (
    Escola,
    LogAlunosMatriculadosFaixaEtariaDia,
    LogAlunosMatriculadosPeriodoEscola,
)


class LogAlunosMatriculadosPeriodoEscolaViewSet(ModelViewSet):
    serializer_class = LogAlunosMatriculadosPeriodoEscolaSerializer
    queryset = LogAlunosMatriculadosPeriodoEscola.objects.all()
    pagination_class = None

    def get_queryset(self):
        queryset = LogAlunosMatriculadosPeriodoEscola.objects.all()

        escola_uuid = self.request.query_params.get("escola_uuid", "")
        mes = self.request.query_params.get("mes", "")
        ano = self.request.query_params.get("ano", "")
        tipo_turma = self.request.query_params.get("tipo_turma", "")
        periodo_escolar = self.request.query_params.get("periodo_escolar", "")

        queryset = queryset.filter(
            escola__uuid=escola_uuid,
            criado_em__month=mes,
            criado_em__year=ano,
            tipo_turma=tipo_turma,
        )

        if periodo_escolar:
            if (
                Escola.objects.get(uuid=escola_uuid).eh_cemei
                and "Infantil" in periodo_escolar
            ):
                periodo = periodo_escolar.replace("Infantil ", "")
                queryset = queryset.filter(periodo_escolar__nome=periodo)
                if "INTEGRAL" in periodo_escolar:
                    queryset = queryset.filter(
                        cei_ou_emei=TIPOS_UNIDADE_ESCOLAR.EMEI.value
                    )
                else:
                    queryset = queryset.filter(cei_ou_emei="N/A")
            else:
                queryset = queryset.filter(periodo_escolar__uuid=periodo_escolar)

        return queryset

    @action(detail=False, url_path="quantidade-por-data")
    def quantidade_por_data(self, request):
        try:
            data = self.request.query_params.get("data", "")
            cei_ou_emei = self.request.query_params.get("cei_ou_emei", "N/A")
            infantil_ou_fundamental = self.request.query_params.get(
                "infantil_ou_fundamental", "N/A"
            )
            escola_uuid = self.request.query_params.get("escola_uuid", "")

            if not data:
                raise ValidationError("campo data é obrigatório")

            if not escola_uuid:
                raise ValidationError("campo escola_uuid é obrigatório")

            today = datetime.date.today()
            if data == today.strftime("%Y-%m-%d"):
                data = today - datetime.timedelta(days=1)

            resultado = LogAlunosMatriculadosPeriodoEscola.objects.filter(
                escola__uuid=escola_uuid,
                criado_em=data,
                cei_ou_emei=cei_ou_emei,
                infantil_ou_fundamental=infantil_ou_fundamental,
            ).aggregate(soma=Sum("quantidade_alunos"))

            soma_quantidade_alunos = resultado["soma"] or 0

            return Response(soma_quantidade_alunos, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"detail": e}, status=status.HTTP_400_BAD_REQUEST)


class LogAlunosMatriculadosFaixaEtariaDiaViewSet(ListModelMixin, GenericViewSet):
    serializer_class = LogAlunosMatriculadosFaixaEtariaDiaSerializer
    queryset = LogAlunosMatriculadosFaixaEtariaDia.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = LogAlunosMatriculadosFaixaEtariaDiaFilter
    pagination_class = None
