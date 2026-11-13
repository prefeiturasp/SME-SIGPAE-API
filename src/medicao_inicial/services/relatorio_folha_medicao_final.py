import calendar
import datetime
from decimal import Decimal

from django.db.models import F, Q
from unidecode import unidecode

from src.core.models import GrupoUnidadeEscolar
from src.medicao_inicial.models import DescontoFinanceiro
from src.medicao_inicial.services.relatorio_ateste_financeiro import (
    CEM,
    arredonda_centavos,
    montar_relatorio_financeiro,
    obter_config_grupo,
    parametrizacao_possui_reajuste,
    prepara_relatorio_para_template,
    rotulo_tipo_alimentacao,
    valor_por_extenso,
)
from src.medicao_inicial.utils import to_decimal_safe
from src.relatorios.templatetags.index import percentual_br
from src.terceirizada.models import Contrato

SEM_INFORMACAO = "-"
PREFIXO_NOME_DRE = "DIRETORIA REGIONAL DE EDUCACAO"
PREFIXO_PERIODO_LINHA = "Período "
SEM_SEGMENTO = "N/A"
PERIODO_REFEICAO_EJA = "NOITE"
ROTULO_REFEICAO_EJA = "REFEIÇÃO - EJA"
ROTULO_KIT_LANCHE = "KIT LANCHE"
TABELA_POR_TIPO_LANCAMENTO = {
    "ALIMENTACOES": "alimentacao",
    "DIETAS_TIPO_A": "dieta_a",
    "DIETAS_TIPO_B": "dieta_b",
}
TITULO_COLUNA_ALIMENTACAO = "ALIMENTAÇÃO"
TITULO_COLUNA_POR_GRUPO = {
    GrupoUnidadeEscolar.GRUPO_1.upper(): "FAIXA ETÁRIA",
    GrupoUnidadeEscolar.GRUPO_2.upper(): "FAIXA ETÁRIA OU ALIMENTAÇÃO",
}


def _buscar_contrato_vigente(lote, terceirizada, primeiro_dia, ultimo_dia):
    contratos = Contrato.objects.filter(lotes=lote).filter(
        Q(data_hora_encerramento__isnull=True)
        | Q(data_hora_encerramento__date__gte=primeiro_dia),
        Q(data_proposta__isnull=True) | Q(data_proposta__lte=ultimo_dia),
    )
    if terceirizada:
        contratos = contratos.filter(terceirizada=terceirizada)

    return contratos.order_by(
        "encerrado", F("data_proposta").desc(nulls_last=True)
    ).first()


def obter_dados_contratuais(relatorio_financeiro):
    """Retorna empresa, contrato e período de serviço do relatório financeiro.

    Args:
        relatorio_financeiro (Model): Instância do relatório financeiro.

    Returns:
        dict: Dados exibidos no modal "Gerar Medição Final" e na Folha.
    """
    lote = relatorio_financeiro.lote
    terceirizada = lote.terceirizada
    mes, ano = int(relatorio_financeiro.mes), int(relatorio_financeiro.ano)
    primeiro_dia = datetime.date(ano, mes, 1)
    ultimo_dia = datetime.date(ano, mes, calendar.monthrange(ano, mes)[1])

    contrato = _buscar_contrato_vigente(lote, terceirizada, primeiro_dia, ultimo_dia)

    tipos_unidade = relatorio_financeiro.grupo_unidade_escolar.tipos_unidades.order_by(
        "iniciais"
    ).values_list("iniciais", flat=True)

    return {
        "empresa_contratada": terceirizada.razao_social if terceirizada else None,
        "periodo_inicio": primeiro_dia.strftime("%d/%m/%Y"),
        "periodo_fim": ultimo_dia.strftime("%d/%m/%Y"),
        "lote": lote.nome,
        "dre": lote.diretoria_regional.nome if lote.diretoria_regional else None,
        "tipos_unidade": ", ".join(tipos_unidade),
        "numero_contrato": contrato.numero if contrato else None,
        "numero_processo_administrativo": contrato.processo if contrato else None,
    }


def _nome_curto_dre(nome_dre):
    if not nome_dre:
        return SEM_INFORMACAO

    nome = unidecode(nome_dre).upper().removeprefix(PREFIXO_NOME_DRE).strip()
    return nome if nome.startswith("DRE ") else f"DRE {nome}"


def _nome_lote(nome_lote):
    nome = nome_lote.upper()
    return nome if nome.startswith("LOTE") else f"LOTE {nome}"


def nome_arquivo_folha_medicao_final(relatorio_financeiro):
    """Monta o nome do arquivo, sem "/" e dentro do limite do campo `arquivo`."""
    lote = relatorio_financeiro.lote
    dre = lote.diretoria_regional.nome if lote.diretoria_regional else None
    nome = (
        f"Folha de Medição Final - {_nome_curto_dre(dre)} - "
        f"{relatorio_financeiro.grupo_unidade_escolar.nome} - "
        f"{relatorio_financeiro.mes}_{relatorio_financeiro.ano}.pdf"
    )
    return nome.replace("/", "-")


def montar_cabecalho_folha(relatorio_financeiro, cabecalho):
    """Complementa o cabeçalho calculado com os dados contratuais da Folha.

    Args:
        relatorio_financeiro (Model): Instância do relatório financeiro.
        cabecalho (dict): Cabeçalho montado pelo builder do grupo.

    Returns:
        dict: Dados exibidos no cabeçalho da Folha de Medição Final.
    """
    dados = obter_dados_contratuais(relatorio_financeiro)
    grupo_nome = relatorio_financeiro.grupo_unidade_escolar.nome

    return {
        **cabecalho,
        "dre_lote": f"{_nome_curto_dre(dados['dre'])} - {_nome_lote(dados['lote'])}",
        "empresa_contratada": dados["empresa_contratada"] or SEM_INFORMACAO,
        "numero_contrato": dados["numero_contrato"] or SEM_INFORMACAO,
        "numero_processo_administrativo": dados["numero_processo_administrativo"]
        or SEM_INFORMACAO,
        "grupo_unidade_escolar": f"{grupo_nome} ({dados['tipos_unidade']})",
        "periodo_servico": f"{dados['periodo_inicio']} À {dados['periodo_fim']}",
    }


def _extenso_para_documento(valor_extenso):
    return f"{valor_extenso[0].upper()}{valor_extenso[1:]}."


def _soma_do_titulo(titulo):
    """Extrai a soma do título do consolidado, ex.: "A + B + C"."""
    return titulo[titulo.index("(") + 1 : titulo.rindex(")")]


def _formata_consolidados(consolidados):
    """Aplica os rótulos e o extenso exibidos na tela aos consolidados."""
    tem_varios_blocos = len(consolidados) > 1
    formatados = []

    for indice, consolidado in enumerate(consolidados, start=1):
        titulo = consolidado["titulo"]
        eh_soma_geral = tem_varios_blocos and indice == len(consolidados)
        soma = "" if eh_soma_geral else f" ({_soma_do_titulo(titulo)})"
        formatados.append(
            {
                **consolidado,
                "titulo_quantidade": f"QUANTIDADE SERVIDA{soma}:",
                "titulo_valor": f"VALOR DO FATURAMENTO TOTAL{soma}:",
                "valor_extenso": _extenso_para_documento(consolidado["valor_extenso"]),
            }
        )

    return formatados


def _rotulo_linha_relatorio(linha):
    """Rótulo da linha das tabelas, ex.: "Integral - 04 a 05 meses" ou "LANCHE"."""
    if "faixa" in linha:
        periodo = linha["periodo"].removeprefix(PREFIXO_PERIODO_LINHA)
        return f"{periodo} - {linha['faixa']}"
    return linha["tipo"]


def _rotulo_desconto(desconto, grupo_nome):
    """Rótulo do desconto no mesmo formato das linhas das tabelas do relatório."""
    periodo = desconto.periodo_escolar.nome if desconto.periodo_escolar else ""

    if desconto.faixa_etaria:
        return f"{periodo.capitalize()} - {desconto.faixa_etaria}"
    if not desconto.tipo_alimentacao:
        return ROTULO_KIT_LANCHE
    if periodo == PERIODO_REFEICAO_EJA:
        return ROTULO_REFEICAO_EJA
    return rotulo_tipo_alimentacao(desconto.tipo_alimentacao.nome, grupo_nome)


def _segmento_desconto(desconto):
    """Retorna a turma (CEI/EMEI ou INFANTIL/FUNDAMENTAL) do desconto, se houver."""
    return next(
        (
            segmento
            for segmento in (desconto.cei_ou_emei, desconto.infantil_ou_fundamental)
            if segmento != SEM_SEGMENTO
        ),
        None,
    )


def _valor_unitario_desconto(relatorio, desconto, segmento, rotulo):
    """Busca o valor unitário na linha correspondente das tabelas do relatório."""
    secao = relatorio.get(segmento.lower(), {}) if segmento else relatorio
    tabela = secao.get(TABELA_POR_TIPO_LANCAMENTO[desconto.tipo_lancamento], {})

    return next(
        (
            linha["valor_unitario"]
            for linha in tabela.get("linhas", [])
            if _rotulo_linha_relatorio(linha) == rotulo
        ),
        Decimal("0"),
    )


def _montar_linha_desconto(desconto, relatorio, grupo_nome):
    segmento = _segmento_desconto(desconto)
    rotulo = _rotulo_desconto(desconto, grupo_nome)
    valor_unitario = _valor_unitario_desconto(relatorio, desconto, segmento, rotulo)
    clausula = desconto.clausula_desconto
    porcentagem = to_decimal_safe(clausula.porcentagem_desconto)
    tipo_lancamento = desconto.get_tipo_lancamento_display().upper()

    return {
        "unidades": sorted(
            escola.nome for escola in desconto.unidades_educacionais.all()
        ),
        "tipo_lancamento": (
            f"{tipo_lancamento} - {segmento}" if segmento else tipo_lancamento
        ),
        "faixa_ou_alimentacao": rotulo,
        "clausula": (
            f"{clausula.numero_clausula}. {clausula.item_clausula} - "
            f"({percentual_br(porcentagem)})"
        ),
        "quantidade": desconto.quantidade,
        "valor_unitario": valor_unitario,
        "total": arredonda_centavos(
            desconto.quantidade * valor_unitario * porcentagem / CEM
        ),
    }


def titulo_coluna_faixa_ou_alimentacao(grupo_nome):
    """Título da coluna de faixa etária/alimentação da Tabela de Desconto."""
    return TITULO_COLUNA_POR_GRUPO.get(grupo_nome.upper(), TITULO_COLUNA_ALIMENTACAO)


def montar_descontos_folha(relatorio_financeiro, relatorio):
    """Monta a Tabela de Desconto com os valores das tabelas do relatório.

    O valor unitário é o mesmo da linha correspondente nas tabelas do
    relatório e o total segue a regra do modal "Aplicar Descontos":
    quantidade x valor unitário x percentual da cláusula.

    Args:
        relatorio_financeiro (Model): Instância do relatório financeiro.
        relatorio (dict): Relatório calculado, preparado para o template.

    Returns:
        dict: Título da coluna de faixa etária/alimentação, linhas da tabela
            e o total (D), soma das linhas arredondadas.
    """
    grupo_nome = relatorio_financeiro.grupo_unidade_escolar.nome.upper()
    descontos = (
        DescontoFinanceiro.objects.filter(relatorio_financeiro=relatorio_financeiro)
        .select_related(
            "clausula_desconto", "tipo_alimentacao", "faixa_etaria", "periodo_escolar"
        )
        .prefetch_related("unidades_educacionais")
        .order_by("criado_em", "id")
    )
    linhas = [
        _montar_linha_desconto(desconto, relatorio, grupo_nome)
        for desconto in descontos
    ]

    return {
        "titulo_faixa_ou_alimentacao": titulo_coluna_faixa_ou_alimentacao(grupo_nome),
        "linhas": linhas,
        "total": sum((linha["total"] for linha in linhas), Decimal("0")),
    }


def montar_faturamento_final(consolidado_geral, total_descontos):
    """Calcula o Valor do Faturamento Final: consolidado geral menos os descontos.

    Args:
        consolidado_geral (dict): Último consolidado do relatório.
        total_descontos (Decimal): Total de descontos dos itens (D).

    Returns:
        dict: Rótulo, valor e valor por extenso do faturamento final.
    """
    valor = consolidado_geral["valor"] - total_descontos
    soma = _soma_do_titulo(consolidado_geral["titulo"])

    return {
        "titulo_valor": f"VALOR DO FATURAMENTO FINAL ({soma} - D):",
        "valor": valor,
        "valor_extenso": _extenso_para_documento(valor_por_extenso(valor)),
    }


def montar_contexto_folha_medicao_final(relatorio_financeiro, parametrizacao):
    """Monta o contexto do template da Folha de Medição Final.

    Args:
        relatorio_financeiro (Model): Relatório com Medição Final gerada.
        parametrizacao (Model): Parametrização financeira vigente.

    Returns:
        dict: Contexto com tabelas, descontos, consolidados e responsáveis.
    """
    config = obter_config_grupo(relatorio_financeiro.grupo_unidade_escolar.nome)
    relatorio = prepara_relatorio_para_template(
        montar_relatorio_financeiro(
            relatorio_financeiro,
            parametrizacao,
            config["builder"],
            config["tipo_calculo"],
        )
    )
    descontos = montar_descontos_folha(relatorio_financeiro, relatorio)
    return {
        **relatorio,
        "cabecalho": montar_cabecalho_folha(
            relatorio_financeiro, relatorio["cabecalho"]
        ),
        "consolidados": _formata_consolidados(relatorio["consolidados"]),
        "descontos": descontos,
        "faturamento_final": montar_faturamento_final(
            relatorio["consolidados"][-1], descontos["total"]
        ),
        "medicao_final": relatorio_financeiro.medicao_final,
        "possui_reajuste": parametrizacao_possui_reajuste(parametrizacao),
        "template_ateste": config["template"],
    }
