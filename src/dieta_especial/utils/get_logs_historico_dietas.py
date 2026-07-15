from itertools import chain
from typing import List

from django.db.models import (
    CharField,
    F,
    IntegerField,
    Q,
    QuerySet,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce

from src.dieta_especial.logs_models.models import (
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
)

from ..constants import (
    UNIDADES_CEMEI,
    UNIDADES_EMEBS,
)


def _dados_dietas_escolas_cei(filtros: dict, eh_exportacao: bool = False) -> List[dict]:
    queryset = LogQuantidadeDietasAutorizadasCEI.objects.filter(**filtros)
    if eh_exportacao:
        queryset = queryset.filter(faixa_etaria__isnull=False)

    logs_dietas_escolas_cei = (
        queryset.select_related(
            "escola",
            "periodo_escolar",
            "escola__tipo_unidade",
            "classificacao",
            "faixa_etaria",
        )
        .annotate(
            nome_escola=F("escola__nome"),
            nome_periodo_escolar=Coalesce(F("periodo_escolar__nome"), Value(None)),
            tipo_unidade=F("escola__tipo_unidade__iniciais"),
            lote=F("escola__lote__nome"),
            dre=F("escola__lote__diretoria_regional__iniciais"),
            nome_classificacao=F("classificacao__nome"),
            quantidade_total=Sum("quantidade"),
            inicio=Coalesce(F("faixa_etaria__inicio"), Value(None)),
            fim=Coalesce(F("faixa_etaria__fim"), Value(None)),
            infantil_ou_fundamental=Value(None, output_field=CharField()),
            cei_ou_emei=Value(None, output_field=CharField()),
        )
        .values(
            "nome_escola",
            "tipo_unidade",
            "lote",
            "dre",
            "nome_classificacao",
            "nome_periodo_escolar",
            "infantil_ou_fundamental",
            "cei_ou_emei",
            "data",
            "quantidade_total",
            "inicio",
            "fim",
        )
        .order_by("nome_escola", "faixa_etaria__inicio")
    )

    return logs_dietas_escolas_cei


def _dados_dietas_escolas_comuns(filtros: dict) -> QuerySet[dict]:
    filtro_por_tipo_unidade = Q(
        Q(
            escola__tipo_unidade__iniciais__in=UNIDADES_EMEBS,
            periodo_escolar__isnull=True,
            cei_ou_emei="N/A",
            infantil_ou_fundamental__in=["FUNDAMENTAL", "INFANTIL"],
        )
        | Q(
            escola__tipo_unidade__iniciais__in=UNIDADES_CEMEI,
            periodo_escolar__nome="INTEGRAL",
            cei_ou_emei__in=["CEI", "EMEI"],
        )
    )
    logs_dietas_outras_escolas = (
        LogQuantidadeDietasAutorizadas.objects.filter(**filtros)
        .exclude(filtro_por_tipo_unidade)
        .select_related(
            "escola", "periodo_escolar", "escola__tipo_unidade", "classificacao"
        )
        .annotate(
            nome_escola=F("escola__nome"),
            nome_periodo_escolar=Coalesce(F("periodo_escolar__nome"), Value(None)),
            tipo_unidade=F("escola__tipo_unidade__iniciais"),
            lote=F("escola__lote__nome"),
            dre=F("escola__lote__diretoria_regional__iniciais"),
            nome_classificacao=F("classificacao__nome"),
            quantidade_total=Sum("quantidade"),
            inicio=Value(None, output_field=IntegerField()),
            fim=Value(None, output_field=IntegerField()),
        )
        .values(
            "nome_escola",
            "tipo_unidade",
            "lote",
            "dre",
            "nome_classificacao",
            "nome_periodo_escolar",
            "infantil_ou_fundamental",
            "cei_ou_emei",
            "data",
            "quantidade_total",
            "inicio",
            "fim",
        )
        .order_by("nome_escola")
    )

    return logs_dietas_outras_escolas


def get_logs_historico_dietas(filtros, eh_exportacao=False) -> list:
    log_escolas_cei = _dados_dietas_escolas_cei(filtros, eh_exportacao)
    log_escolas = _dados_dietas_escolas_comuns(filtros)
    if eh_exportacao:
        log_escolas = [
            log
            for log in log_escolas
            if log.get("nome_periodo_escolar") is not None
            or log.get("tipo_unidade") in {"CEU GESTAO", "CMCT"}
        ]
    log_dietas = sorted(
        chain(log_escolas_cei, log_escolas), key=lambda x: x["nome_escola"]
    )
    return log_dietas
