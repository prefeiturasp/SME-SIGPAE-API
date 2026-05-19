from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from num2words import num2words

from src.cardapio.base.api.serializers import (
    TipoUnidadeEscolarAgrupadoSerializer,
)
from src.cardapio.base.models import (
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from src.dados_comuns.utils import converte_numero_em_mes
from src.escola.models import FaixaEtaria
from src.medicao_inicial.utils import (
    normalizar_nome_campo,
    to_decimal_safe,
)

ORDEM_PRIORIDADE = {
    "REFEIÇÃO": 0,
    "REFEIÇÃO CIEJA E CMCT": 0,
    "REFEIÇÃO - CEU EMEF, CEU GESTÃO, EMEF, EMEFM": 0,
    "REFEIÇÃO - EJA": 1,
    "LANCHE": 2,
    "LANCHE 4H": 3,
    "KIT LANCHE": 99,
}


def obter_config_grupo(grupo_nome):
    grupos_relatorio = {
        "GRUPO 1": {
            "builder": build_relatorio_financeiro_grupo_cei,
            "template": "relatorio_financeiro/relatorio_ateste_financeiro_grupo_cei.html",
            "tipo_calculo": "faixa_etaria",
        },
        "GRUPO 2": {
            "builder": build_relatorio_financeiro_grupo_cemei,
            "template": "relatorio_financeiro/relatorio_ateste_financeiro_grupo_cemei.html",
            "tipo_calculo": None,
        },
        "GRUPO 5": {
            "builder": build_relatorio_financeiro_grupo_emebs,
            "template": "relatorio_financeiro/relatorio_ateste_financeiro_grupo_emebs.html",
            "tipo_calculo": "tipo_alimentacao",
        },
        "DEFAULT": {
            "builder": build_relatorio_financeiro_grupo_emei,
            "template": "relatorio_financeiro/relatorio_ateste_financeiro_grupo_emei.html",
            "tipo_calculo": "tipo_alimentacao",
        },
    }

    grupo_upper = grupo_nome.upper()
    for grupo, config in grupos_relatorio.items():
        if grupo != "DEFAULT" and grupo in grupo_upper:
            return config

    return grupos_relatorio["DEFAULT"]


def _buscar_valor_por_faixa(valores, faixa_uuid, tipo):
    """Busca um valor com base na faixa etária e tipo de valor.

    Args:
        valores (Iterable): Coleção de objetos com valores parametrizados.
        faixa_uuid (str): UUID da faixa etária.
        tipo (str): Tipo do valor ("UNITARIO", "REAJUSTE", etc.).

    Returns:
        Decimal: Valor encontrado ou Decimal("0") caso não exista.
    """
    if not valores:
        return Decimal("0")

    valor = next(
        (
            v.valor
            for v in valores
            if v.faixa_etaria
            and v.faixa_etaria.uuid == faixa_uuid
            and v.tipo_valor
            and v.tipo_valor.nome == tipo
        ),
        None,
    )

    return Decimal("0") if valor is None else to_decimal_safe(valor)


def _buscar_valor_por_tipo(valores, tipo_alimentacao, tipo_valor):
    """Busca valor com base no tipo de alimentação.

    A busca funciona em dois cenários:
        - Quando há `tipo_alimentacao`, compara pelo UUID.
        - Caso contrário, compara com `nome_campo`.

    Args:
        valores (Iterable): Coleção de objetos com valores.
        tipo_uuid (str): UUID ou identificador do tipo.
        tipo_valor (str): Tipo do valor ("UNITARIO", "REAJUSTE", "ACRESCIMO").
        tipo_refeicao (str): Tipo de refeição (usado em caso de EMEF (EJA e Refeição normal)).

    Returns:
        Decimal: Valor encontrado ou Decimal("0").
    """
    if not valores:
        return Decimal("0")

    tipo_refeicao = tipo_alimentacao.get("tipo_refeicao", "")

    valor = next(
        (
            v.valor
            for v in valores
            if (
                (
                    tipo_refeicao
                    and tipo_refeicao
                    in normalizar_nome_campo(getattr(v, "nome_campo", "").lower())
                )
                or (
                    not tipo_refeicao
                    and getattr(v, "tipo_alimentacao", None)
                    and str(v.tipo_alimentacao.uuid) == str(tipo_alimentacao["uuid"])
                )
                or (
                    not getattr(v, "tipo_alimentacao", None)
                    and str(getattr(v, "nome_campo", "")) == "kit_lanche"
                )
            )
            and v.tipo_valor
            and v.tipo_valor.nome == tipo_valor
        ),
        None,
    )

    return Decimal("0") if valor is None else to_decimal_safe(valor)


def _build_consolidado_total(alimentacao, dieta_a, dieta_b):
    """Gera o consolidado total do relatório.

    Args:
        alimentacao (dict): Dados de alimentação.
        dieta_a (dict): Dados da dieta tipo A.
        dieta_b (dict): Dados da dieta tipo B.

    Returns:
        dict: Contendo quantidade total, valor total e valor por extenso.
    """
    quantidade = (
        alimentacao["total_atendimentos"]
        + dieta_a["total_consumo"]
        + dieta_b["total_consumo"]
    )

    valor = alimentacao["valor_total"] + dieta_a["valor_total"] + dieta_b["valor_total"]

    return {
        "quantidade": int(quantidade),
        "valor": valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "valor_extenso": num2words(valor, lang="pt_BR", to="currency"),
    }


def _montar_cabecalho(relatorio_financeiro, tipos_unidades):
    """Monta os dados do cabeçalho do relatório.

    Args:
        relatorio_financeiro (Model): Instância do relatório financeiro.
        tipos_unidades (QuerySet): Tipos de unidades escolares com base no grupo educacional.

    Returns:
        dict: Dados formatados do cabeçalho.
    """
    iniciais = ", ".join([t.iniciais for t in tipos_unidades])

    grupo_com_unidades = (
        f"{relatorio_financeiro.grupo_unidade_escolar.nome} ({iniciais})"
    )

    data_referencia = (
        converte_numero_em_mes(int(relatorio_financeiro.mes)).upper()
        + f"/{relatorio_financeiro.ano}"
    )

    return {
        "data_geracao": datetime.now().strftime("%d/%m/%Y"),
        "hora_geracao": datetime.now().strftime("%H:%M"),
        "data_referencia": data_referencia,
        "grupo_unidade_escolar": grupo_com_unidades,
        "dre_lote": (
            f"{relatorio_financeiro.lote.nome.upper()} - "
            f"{relatorio_financeiro.lote.diretoria_regional.nome}"
        ),
    }


# =========================================================
# CEI
# =========================================================
def _build_tabela_alimentacao_cei(tabelas, faixas_etarias, totais_consumo):
    """Retorna dados para a tabela de alimentação do grupo CEI.

    Args:
        tabelas (QuerySet): Tabelas parametrizadas.
        faixas_etarias (QuerySet): Faixas etárias ativas.
        totais_consumo (dict): Dados de totais de consumo e atendimento.

    Returns:
        dict: Estrutura com linhas da tabela, total de atendimentos e valor total.
    """
    total_atendimentos = 0
    valor_total_geral = Decimal("0")
    linhas = []

    for periodo in ["INTEGRAL", "PARCIAL"]:
        tabela = next(
            (
                t
                for t in tabelas
                if t.nome == "Preço das Alimentações"
                and t.periodo_escolar
                and t.periodo_escolar.nome == periodo
            ),
            None,
        )

        valores_tabela = tabela.valores.all() if tabela else []

        for faixa in faixas_etarias:
            valor_unitario = _buscar_valor_por_faixa(
                valores_tabela, faixa.uuid, "UNITARIO"
            )
            valor_reajuste = _buscar_valor_por_faixa(
                valores_tabela, faixa.uuid, "REAJUSTE"
            )

            total_unitario = valor_unitario + valor_reajuste

            numero_atendimentos = totais_consumo.get(
                f"ALIMENTAÇÃO - {periodo}", {}
            ).get(str(faixa), 0)

            valor_total = total_unitario * to_decimal_safe(numero_atendimentos)

            total_atendimentos += numero_atendimentos
            valor_total_geral += valor_total

            linhas.append(
                {
                    "periodo": f"Período {periodo.capitalize()}",
                    "faixa": str(faixa),
                    "valor_unitario": valor_unitario,
                    "valor_reajuste": valor_reajuste,
                    "total_unitario": total_unitario,
                    "numero_atendimentos": int(numero_atendimentos),
                    "valor_total": valor_total,
                }
            )

    return {
        "linhas": linhas,
        "total_atendimentos": int(total_atendimentos),
        "valor_total": valor_total_geral,
    }


def _build_tabela_dieta_cei(tabelas, faixas_etarias, totais_consumo, tipo_dieta):
    """Retorna dados para a tabela de dieta especial do grupo CEI.

    Args:
        tabelas (QuerySet): Tabelas parametrizadas.
        faixas_etarias (QuerySet): Faixas etárias.
        totais_consumo (dict): Dados de totais de consumo e atendimento.
        tipo_dieta (str): Tipo de dieta ("TIPO A", "TIPO B").

    Returns:
        dict: Estrutura com linhas da tabela, total de atendimentos e valor total.
    """
    total_consumo = 0
    valor_total_geral = Decimal("0")
    linhas = []

    for periodo in ["INTEGRAL", "PARCIAL"]:
        tabela = next(
            (
                t
                for t in tabelas
                if tipo_dieta in t.nome.upper()
                and t.periodo_escolar
                and t.periodo_escolar.nome == periodo
            ),
            None,
        )

        valores_tabela = tabela.valores.all() if tabela else []

        for faixa in faixas_etarias:
            valor_unitario = _buscar_valor_por_faixa(
                valores_tabela, faixa.uuid, "UNITARIO"
            )
            valor_acrescimo = _buscar_valor_por_faixa(
                valores_tabela, faixa.uuid, "ACRESCIMO"
            )

            total_unitario = valor_unitario * (1 + (valor_acrescimo / 100))

            numero_consumo = totais_consumo.get(
                f"DIETA ESPECIAL - {tipo_dieta} - {periodo}",
                {},
            ).get(str(faixa), 0)

            valor_total = total_unitario * to_decimal_safe(numero_consumo)

            total_consumo += numero_consumo
            valor_total_geral += valor_total

            linhas.append(
                {
                    "periodo": f"Período {periodo.capitalize()}",
                    "faixa": str(faixa),
                    "valor_unitario": valor_unitario,
                    "valor_acrescimo": valor_acrescimo,
                    "total_unitario": total_unitario,
                    "numero_consumo": int(numero_consumo),
                    "valor_total": valor_total,
                }
            )

    return {
        "linhas": linhas,
        "total_consumo": int(total_consumo),
        "valor_total": valor_total_geral,
    }


def build_relatorio_financeiro_grupo_cei(
    relatorio_financeiro,
    tabelas,
    totais_consumo,
):
    """Retorna dados para o relatório financeiro do grupos por faixa etária (1 e 2).

    Args:
        relatorio_financeiro (Model): Instância do relatório.
        tabelas (QuerySet): Tabelas parametrizadas.
        totais_consumo (dict): Dados de totais de consumo e atendimento.

    Returns:
        dict: Estrutura completa do relatório.
    """
    faixas_etarias = FaixaEtaria.objects.filter(ativo=True)

    alimentacao = _build_tabela_alimentacao_cei(tabelas, faixas_etarias, totais_consumo)

    dieta_a = _build_tabela_dieta_cei(tabelas, faixas_etarias, totais_consumo, "TIPO A")

    dieta_b = _build_tabela_dieta_cei(tabelas, faixas_etarias, totais_consumo, "TIPO B")

    consolidado = _build_consolidado_total(alimentacao, dieta_a, dieta_b)

    tipos = relatorio_financeiro.grupo_unidade_escolar.tipos_unidades.all()

    return {
        "alimentacao": alimentacao,
        "dieta_a": dieta_a,
        "dieta_b": dieta_b,
        "consolidado": consolidado,
        "cabecalho": _montar_cabecalho(
            relatorio_financeiro,
            tipos,
        ),
    }


# =========================================================
# EMEI
# =========================================================
def _obter_tipos_alimentacao_por_unidades(uuids_unidades):
    """Obtém os tipos de alimentação únicos por unidades educacionais.

    Args:
        uuids_unidades (Iterable): Lista de UUIDs das unidades educacionais.

    Returns:
        list[dict]: Lista de tipos de alimentação com uuid e nome.
    """
    vinculos = (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
            ativo=True,
            tipo_unidade_escolar__ativo=True,
            tipo_unidade_escolar__uuid__in=uuids_unidades,
        )
        .select_related(
            "tipo_unidade_escolar",
            "periodo_escolar",
        )
        .prefetch_related("tipos_alimentacao")
    )

    dados_agrupados = TipoUnidadeEscolarAgrupadoSerializer.agrupar_vinculos_por_tipo_ue(
        vinculos
    )

    tipos_unicos = {}

    for tipo_ue in dados_agrupados:
        for vinculo in tipo_ue["vinculos"]:
            for tipo in vinculo.tipos_alimentacao.all():
                tipos_unicos[str(tipo.uuid)] = tipo.nome

    return [{"uuid": uuid, "nome": nome} for uuid, nome in tipos_unicos.items()]


def _build_tabela_alimentacao_emei(
    tabelas,
    tipos_alimentacao,
    totais_consumo,
    grupo_nome=None,
):
    """Retorna dados da tabela de alimentação para EMEI.

    Args:
        tabelas (QuerySet): Tabelas parametrizadas.
        tipos_alimentacao (list): Tipos de alimentação.
        totais_consumo (dict): Dados de totais de consumo e atendimento.
        grupo_nome (str): Nome do grupo de unidade escolar.

    Returns:
        dict: Estrutura com linhas da tabela, total de atendimentos e valor total.
    """
    total_atendimentos = 0
    valor_total_geral = Decimal("0")
    linhas = []

    tabela = next(
        (t for t in tabelas if "Preço das Alimentações" in t.nome and not t.periodo_escolar),
        None,
    )

    valores_tabela = tabela.valores.all() if tabela else []
    for tipo in tipos_alimentacao:
        valor_unitario = _buscar_valor_por_tipo(
            valores_tabela,
            tipo,
            "UNITARIO",
        )

        valor_reajuste = _buscar_valor_por_tipo(
            valores_tabela,
            tipo,
            "REAJUSTE",
        )

        total_unitario = valor_unitario + valor_reajuste

        tipo_refeicao = tipo.get("tipo_refeicao")
        if tipo_refeicao:
            if tipo_refeicao == "eja":
                nome_consumo = "refeicao_eja"
            else:
                nome_consumo = "refeicao"
        else:
            nome_consumo = normalizar_nome_campo(
                tipo["nome"],
                "GRUPO 3",
            ).lower()

        numero_atendimentos = totais_consumo.get(
            "ALIMENTAÇÃO",
            {},
        ).get(
            f"total_{nome_consumo}",
            0,
        )

        valor_total = total_unitario * to_decimal_safe(numero_atendimentos)

        total_atendimentos += numero_atendimentos
        valor_total_geral += valor_total

        alimentacao_nome = tipo["nome"].upper()
        linhas.append(
            {
                "tipo": f"{alimentacao_nome} CIEJA E CMCT" if grupo_nome == "GRUPO 6" and alimentacao_nome == "REFEIÇÃO" else alimentacao_nome,
                "valor_unitario": valor_unitario,
                "valor_reajuste": valor_reajuste,
                "total_unitario": total_unitario,
                "numero_atendimentos": int(numero_atendimentos),
                "valor_total": valor_total,
            }
        )

    linhas = sorted(linhas, key=lambda linha: ORDEM_PRIORIDADE.get(linha["tipo"], 10))

    return {
        "linhas": linhas,
        "total_atendimentos": int(total_atendimentos),
        "valor_total": valor_total_geral,
    }


def _build_tabela_dieta_emei(
    tabelas,
    tipos_alimentacao,
    totais_consumo,
    tipo_dieta,
    grupo_nome=None,
):
    """Retorna dados da tabela de dieta especial para EMEI.

    Args:
        tabelas (QuerySet): Tabelas parametrizadas.
        tipos_alimentacao (list): Tipos de alimentação.
        totais_consumo (dict): Dados de totais de consumo e atendimento.
        tipo_dieta (str): Tipo da dieta (A ou B).
        grupo_nome (str): Nome do grupo de unidade escolar.

    Returns:
        dict: Estrutura com linhas da tabela, total de atendimentos e valor total.
    """
    total_consumo = 0
    valor_total_geral = Decimal("0")
    linhas = []

    tabela = next(
        (t for t in tabelas if tipo_dieta in t.nome.upper() and not t.periodo_escolar),
        None,
    )

    valores_tabela = tabela.valores.all() if tabela else []

    for tipo in tipos_alimentacao:
        valor_unitario = _buscar_valor_por_tipo(
            valores_tabela,
            tipo,
            "UNITARIO",
        )

        valor_acrescimo = _buscar_valor_por_tipo(
            valores_tabela,
            tipo,
            "ACRESCIMO",
        )

        total_unitario = valor_unitario * (1 + (valor_acrescimo / 100))

        tipo_refeicao = tipo.get("tipo_refeicao")
        if tipo_refeicao:
            if tipo_refeicao == "eja":
                nome_consumo = "refeicao_eja"
            else:
                nome_consumo = "refeicao"
        else:
            nome_consumo = normalizar_nome_campo(
                tipo["nome"],
                grupo_nome,
            ).lower()

        numero_consumo = totais_consumo.get(
            f"DIETA ESPECIAL - {tipo_dieta}",
            {},
        ).get(nome_consumo, 0)

        valor_total = total_unitario * to_decimal_safe(numero_consumo)

        total_consumo += numero_consumo
        valor_total_geral += valor_total

        dieta_nome = tipo["nome"].upper()
        linhas.append(
            {
                "tipo": f"{dieta_nome} CIEJA E CMCT" if grupo_nome == "GRUPO 6" and dieta_nome == "REFEIÇÃO" else dieta_nome,
                "valor_unitario": valor_unitario,
                "valor_acrescimo": valor_acrescimo,
                "total_unitario": total_unitario,
                "numero_consumo": int(numero_consumo),
                "valor_total": valor_total,
            }
        )

    linhas = sorted(linhas, key=lambda linha: ORDEM_PRIORIDADE.get(linha["tipo"], 10))

    return {
        "linhas": linhas,
        "total_consumo": int(total_consumo),
        "valor_total": valor_total_geral,
    }


def build_relatorio_financeiro_grupo_emei(
    relatorio_financeiro,
    tabelas,
    totais_consumo,
):
    """Gera os dados que serão exibidos no relatório financeiro para grupo por tipo de alimentação (2, 3 e 6).

    Args:
        relatorio_financeiro (Model): Instância do relatório.
        tabelas (QuerySet): Tabelas parametrizadas.
        totais_consumo (dict): Dados de totais de consumo e atendimento.

    Returns:
        dict: Estrutura completa do relatório.
    """
    grupo_unidade = relatorio_financeiro.grupo_unidade_escolar
    tipos_unidades = grupo_unidade.tipos_unidades.all()
    grupo_nome = grupo_unidade.nome.upper()

    eh_cieja = "GRUPO 6" in grupo_nome
    eh_emef = "GRUPO 4" in grupo_nome

    tipos_alimentacao = _obter_tipos_alimentacao_por_unidades(
        tipos_unidades.values_list("uuid", flat=True)
    )

    if eh_emef:
        novos_tipos = []

        for tipo in tipos_alimentacao:
            if tipo["nome"].upper() == "REFEIÇÃO":
                novos_tipos.extend(
                    [
                        {
                            "uuid": tipo["uuid"],
                            "nome": "REFEIÇÃO",
                        },
                        {
                            "uuid": tipo["uuid"],
                            "nome": "REFEIÇÃO - EJA",
                            "tipo_refeicao": "eja",
                        },
                    ]
                )
            else:
                novos_tipos.append(tipo)

        tipos_alimentacao = novos_tipos

    tipos_alimentacao.append(
        {
            "uuid": "kit_lanche",
            "nome": "KIT LANCHE",
        }
    )

    alimentacao = _build_tabela_alimentacao_emei(
        tabelas,
        tipos_alimentacao,
        totais_consumo,
        grupo_nome,
    )

    lista_dietas_a = ["LANCHE", "LANCHE 4H", "REFEIÇÃO"] if not eh_cieja else ["LANCHE 4H", "REFEIÇÃO"]

    tipos_dieta_a = [
        tipo
        for tipo in tipos_alimentacao
        if "REFEIÇÃO" in tipo["nome"].upper()
        or tipo["nome"].upper() in lista_dietas_a
    ]

    dieta_a = _build_tabela_dieta_emei(
        tabelas,
        tipos_dieta_a,
        totais_consumo,
        "TIPO A",
        grupo_nome,
    )

    lista_dietas_b = ["LANCHE", "LANCHE 4H"] if not eh_cieja else ["LANCHE 4H"]

    tipos_dieta_b = [
        tipo
        for tipo in tipos_alimentacao
        if tipo["nome"].upper() in lista_dietas_b
    ]

    dieta_b = _build_tabela_dieta_emei(
        tabelas,
        tipos_dieta_b,
        totais_consumo,
        "TIPO B",
        grupo_nome,
    )

    consolidado = _build_consolidado_total(
        alimentacao,
        dieta_a,
        dieta_b,
    )

    return {
        "alimentacao": alimentacao,
        "dieta_a": dieta_a,
        "dieta_b": dieta_b,
        "consolidado": consolidado,
        "cabecalho": _montar_cabecalho(
            relatorio_financeiro,
            tipos_unidades,
        ),
    }


# =========================================================
# CEMEI
# =========================================================
def build_relatorio_financeiro_grupo_cemei(
    relatorio_financeiro,
    parametrizacao,
    totais_consumo,
):
    """Retorna dados para o relatório financeiro do grupo CEMEI (tipo de alimentação e faixa etária).

    Args:
        relatorio_financeiro (Model): Instância do relatório.
        parametrizacao (Model): Configuração contendo tabelas.
        totais_consumo (dict): Dados de totais de consumo e atendimento.

    Returns:
        dict: Estrutura completa do relatório.
    """
    tabelas = parametrizacao.tabelas.all()

    relatorio_cei = build_relatorio_financeiro_grupo_cei(
        relatorio_financeiro,
        tabelas.filter(periodo_escolar__isnull=False),
        totais_consumo["FAIXA"],
    )

    relatorio_emei = build_relatorio_financeiro_grupo_emei(
        relatorio_financeiro,
        tabelas,
        totais_consumo["TIPO"],
    )

    consolidado_total = {
        "quantidade": relatorio_cei["consolidado"]["quantidade"] + relatorio_emei["consolidado"]["quantidade"],
        "valor": relatorio_cei["consolidado"]["valor"] + relatorio_emei["consolidado"]["valor"],
        "valor_extenso": num2words(
            relatorio_cei["consolidado"]["valor"] + relatorio_emei["consolidado"]["valor"],
            lang="pt_BR",
            to="currency"
        ),
    }

    return {
        "cabecalho": relatorio_cei["cabecalho"],
        "cei": relatorio_cei,
        "emei": relatorio_emei,
        "consolidados": [
            {
                **relatorio_cei["consolidado"],
                "titulo": "CONSOLIDADO CEI (A + B + C)",
                "titulo_quantidade": "QUANTIDADE SERVIDA (A+B+C):",
                "titulo_valor": "VALOR DO FATURAMENTO TOTAL (A+B+C):",
            },
            {
                **relatorio_emei["consolidado"],
                "titulo": "CONSOLIDADO INFANTIL - EMEI (INF. A + INF. B + INF. C)",
                "titulo_quantidade": "QUANTIDADE SERVIDA (INF. A+INF. B+INF. C):",
                "titulo_valor": "VALOR DO FATURAMENTO TOTAL (INF. A+INF. B+INF. C):",
            },
            {
                **consolidado_total,
                "titulo": "CONSOLIDADO TOTAL (A + B + C + INF. A + INF. B + INF. C)",
                "titulo_quantidade": "QUANTIDADE SERVIDA:",
                "titulo_valor": "VALOR DO FATURAMENTO TOTAL:",
            },
        ],
    }


# =========================================================
# EMEBS
# =========================================================
def build_relatorio_financeiro_grupo_emebs(
    relatorio_financeiro,
    parametrizacao,
    totais_consumo,
):
    """Retorna dados para o relatório financeiro do grupo EMEBS (tipo de alimentação INFANTIL e FUNDAMENTAL).

    Args:
        relatorio_financeiro (Model): Instância do relatório.
        parametrizacao (Model): Configuração contendo tabelas.
        totais_consumo (dict): Dados de totais de consumo e atendimento.

    Returns:
        dict: Estrutura completa do relatório.
    """
    tabelas = parametrizacao.tabelas.all()

    tabelas_infantil = [
        tabela
        for tabela in tabelas
        if "infantil" in tabela.nome.lower()
    ]

    relatorio_infantil = build_relatorio_financeiro_grupo_emei(
        relatorio_financeiro,
        tabelas_infantil,
        totais_consumo["INFANTIL"],
    )

    tabelas_fundamental = [
        tabela
        for tabela in tabelas
        if "fundamental" in tabela.nome.lower()
    ]

    relatorio_fundamental = build_relatorio_financeiro_grupo_emei(
        relatorio_financeiro,
        tabelas_fundamental,
        totais_consumo["FUNDAMENTAL"],
    )

    consolidado_total = {
        "quantidade": relatorio_infantil["consolidado"]["quantidade"] + relatorio_fundamental["consolidado"]["quantidade"],
        "valor": relatorio_infantil["consolidado"]["valor"] + relatorio_fundamental["consolidado"]["valor"],
        "valor_extenso": num2words(
            relatorio_infantil["consolidado"]["valor"] + relatorio_fundamental["consolidado"]["valor"],
            lang="pt_BR",
            to="currency"
        ),
    }

    return {
        "cabecalho": relatorio_infantil["cabecalho"],
        "infantil": relatorio_infantil,
        "fundamental": relatorio_fundamental,
        "consolidados": [
            {
                **relatorio_infantil["consolidado"],
                "titulo": "CONSOLIDADO CEI (A + B + C)",
                "titulo_quantidade": "QUANTIDADE SERVIDA (A+B+C):",
                "titulo_valor": "VALOR DO FATURAMENTO TOTAL (A+B+C):",
            },
            {
                **relatorio_fundamental["consolidado"],
                "titulo": "CONSOLIDADO INFANTIL - EMEI (INF. A + INF. B + INF. C)",
                "titulo_quantidade": "QUANTIDADE SERVIDA (INF. A+INF. B+INF. C):",
                "titulo_valor": "VALOR DO FATURAMENTO TOTAL (INF. A+INF. B+INF. C):",
            },
            {
                **consolidado_total,
                "titulo": "CONSOLIDADO TOTAL (A + B + C + INF. A + INF. B + INF. C)",
                "titulo_quantidade": "QUANTIDADE SERVIDA:",
                "titulo_valor": "VALOR DO FATURAMENTO TOTAL:",
            },
        ],
    }
