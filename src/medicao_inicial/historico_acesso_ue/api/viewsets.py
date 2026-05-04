import datetime
import uuid

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import HistoricoAcessoMedicaoInicialUE


class HistoricoAcessoUEViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=["GET"], url_path="total-por-dre")
    def total_por_dre(self, request):
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")
        dre_uuid = request.query_params.get("dre_uuid")

        if not all([mes, ano, dre_uuid]):
            return Response(
                {"detail": "Parâmetros obrigatórios: mes, ano, dre_uuid"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            mes = int(mes)
            ano = int(ano)
            datetime.date(ano, mes, 1)
            uuid.UUID(dre_uuid)
        except (TypeError, ValueError):
            return Response(
                {"detail": "Parâmetros 'mes', 'ano' ou 'dre_uuid' inválidos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total = (
            HistoricoAcessoMedicaoInicialUE.objects.por_dre(dre_uuid)
            .ativos_no_mes_ano(mes=mes, ano=ano)
            .values("escola")
            .distinct()
            .count()
        )

        return Response(total, status=status.HTTP_200_OK)
