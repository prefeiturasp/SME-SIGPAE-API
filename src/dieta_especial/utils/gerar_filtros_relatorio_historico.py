from datetime import datetime

from django.core.exceptions import ValidationError
from django.http import QueryDict


def gerar_filtros_relatorio_historico(query_params: QueryDict) -> tuple:
    map_filtros = {
        "escola__tipo_gestao__uuid": query_params.get("tipo_gestao", None),
        "escola__tipo_unidade__uuid__in": query_params.getlist(
            "tipos_unidades_selecionadas", None
        ),
        "escola__lote__uuid": query_params.get("lote", None),
        "escola__uuid__in": query_params.getlist(
            "unidades_educacionais_selecionadas", None
        ),
        "periodo_escolar__uuid__in": query_params.getlist(
            "periodos_escolares_selecionadas", None
        ),
        "classificacao__id__in": query_params.getlist(
            "classificacoes_selecionadas", None
        ),
        "quantidade__gt": 0,
    }

    data_dieta = query_params.get("data")
    if not data_dieta:
        raise ValidationError("`data` é um parâmetro obrigatório.")
    try:
        formato = "%d/%m/%Y"
        data = datetime.strptime(data_dieta, formato)
    except ValueError:
        raise ValidationError(
            f"A data {data_dieta} não corresponde ao formato esperado 'dd/mm/YYYY'."
        )

    map_filtros.update(
        {"data__day": data.day, "data__month": data.month, "data__year": data.year}
    )

    filtros = {
        key: value for key, value in map_filtros.items() if value not in [None, []]
    }
    return filtros, data_dieta
