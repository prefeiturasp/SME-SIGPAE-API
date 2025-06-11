from sme_sigpae_api.medicao_inicial.models import Medicao


def get_nome_periodo(medicao: Medicao) -> str:
    return (
        medicao.periodo_escolar.nome
        if not medicao.grupo
        else (
            f"{medicao.grupo.nome} - {medicao.periodo_escolar.nome}"
            if medicao.periodo_escolar
            else medicao.grupo.nome
        )
    )


def update_periodos_alimentacoes(
    periodos_alimentacoes: dict, nome_periodo: str, lista_alimentacoes: list
) -> dict:
    if nome_periodo in periodos_alimentacoes:
        periodos_alimentacoes[nome_periodo] += lista_alimentacoes
    else:
        periodos_alimentacoes[nome_periodo] = lista_alimentacoes
    return periodos_alimentacoes


def get_categorias_dietas(medicao: Medicao) -> list:
    return list(
        medicao.valores_medicao.exclude(
            categoria_medicao__nome__icontains="ALIMENTAÇÃO"
        )
        .values_list("categoria_medicao__nome", flat=True)
        .distinct()
    )
