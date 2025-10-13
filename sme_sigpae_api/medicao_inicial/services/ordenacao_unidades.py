from sme_sigpae_api.dados_comuns import constants


def prioridade_por_tipo(tipo_unidade: str) -> tuple[int, int]:
    """
    Retorna (grupo, ordem_no_grupo) para ordenação.
    """
    if not tipo_unidade:
        return (999, 999)

    tipo = tipo_unidade.strip() if isinstance(tipo_unidade, str) else str(tipo_unidade)

    grupos = [
        (1, constants.ORDEM_UNIDADES_GRUPO_CEI),
        (2, constants.ORDEM_UNIDADES_GRUPO_CEMEI),
        (3, constants.ORDEM_UNIDADES_GRUPO_EMEI),
        (4, constants.ORDEM_UNIDADES_GRUPO_EMEF),
        (5, constants.ORDEM_UNIDADES_GRUPO_EMEBS),
    ]

    for grupo_id, ordem_dict in grupos:
        if tipo in ordem_dict:
            return (grupo_id, ordem_dict[tipo])

    return (999, 999)


def chave_ordenacao_unidade(obj) -> tuple:
    """
    Chave de ordenação: (grupo, ordem_no_grupo, tipo_unidade, nome_escola_upper)
    """
    escola_obj = getattr(obj, "escola", None)

    if escola_obj and hasattr(escola_obj, "nome"):
        escola_nome = escola_obj.nome or ""
    else:
        escola_nome = ""

    tipo_str = ""
    if escola_obj:
        tipo_unidade_obj = getattr(escola_obj, "tipo_unidade", None)
        if tipo_unidade_obj is not None:
            if hasattr(tipo_unidade_obj, "iniciais"):
                tipo_str = tipo_unidade_obj.iniciais or ""
            else:
                tipo_str = str(tipo_unidade_obj) if tipo_unidade_obj is not None else ""
    tipo_str = (tipo_str or "").strip()

    grupo, ordem = prioridade_por_tipo(tipo_str)

    return (grupo, ordem, tipo_str.upper(), escola_nome.strip().upper())


def ordenar_unidades(queryset_ou_lista):
    """
    Ordena unidades por grupo, subgrupo e nome alfabético.
    """
    lista = list(queryset_ou_lista)
    lista.sort(key=chave_ordenacao_unidade)
    return lista
