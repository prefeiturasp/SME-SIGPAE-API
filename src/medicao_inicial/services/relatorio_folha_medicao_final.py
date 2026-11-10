import calendar
import datetime

from django.db.models import F, Q
from unidecode import unidecode

from src.medicao_inicial.services.relatorio_ateste_financeiro import (
    montar_relatorio_financeiro,
    obter_config_grupo,
    parametrizacao_possui_reajuste,
    prepara_relatorio_para_template,
)
from src.terceirizada.models import Contrato

SEM_INFORMACAO = "-"
PREFIXO_NOME_DRE = "DIRETORIA REGIONAL DE EDUCACAO"


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


def _formata_consolidados(consolidados):
    """Aplica os rótulos e o extenso exibidos na tela aos consolidados."""
    tem_varios_blocos = len(consolidados) > 1
    formatados = []

    for indice, consolidado in enumerate(consolidados, start=1):
        titulo = consolidado["titulo"]
        eh_soma_geral = tem_varios_blocos and indice == len(consolidados)
        soma = "" if eh_soma_geral else f" {titulo[titulo.index('('):]}"
        formatados.append(
            {
                **consolidado,
                "titulo_quantidade": f"QUANTIDADE SERVIDA{soma}:",
                "titulo_valor": f"VALOR DO FATURAMENTO TOTAL{soma}:",
                "valor_extenso": _extenso_para_documento(consolidado["valor_extenso"]),
            }
        )

    return formatados


def montar_contexto_folha_medicao_final(relatorio_financeiro, parametrizacao):
    """Monta o contexto do template da Folha de Medição Final.

    Args:
        relatorio_financeiro (Model): Relatório com Medição Final gerada.
        parametrizacao (Model): Parametrização financeira vigente.

    Returns:
        dict: Contexto com tabelas, consolidados e responsáveis.
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
    return {
        **relatorio,
        "cabecalho": montar_cabecalho_folha(
            relatorio_financeiro, relatorio["cabecalho"]
        ),
        "consolidados": _formata_consolidados(relatorio["consolidados"]),
        "medicao_final": relatorio_financeiro.medicao_final,
        "possui_reajuste": parametrizacao_possui_reajuste(parametrizacao),
        "template_ateste": config["template"],
    }
