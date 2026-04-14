import json

from sme_sigpae_api.dados_comuns.utils import converte_numero_em_mes
from sme_sigpae_api.medicao_inicial.services.relatorio_historio_correcoes_pdf import (
    ajusta_informacoes_por_status,
    filtrar_historico_por_acao,
    gera_relatorio_historico_correcoes_pdf,
)
from sme_sigpae_api.relatorios.utils import extrair_texto_de_pdf


def test_gera_relatorio_historico_correcoes_pdf(
    solicitacao_com_historico_correcao,
):
    resultado = gera_relatorio_historico_correcoes_pdf(
        solicitacao_com_historico_correcao.uuid
    )
    texto = extrair_texto_de_pdf(resultado)

    assert "Sistema de Gestão do Programa de Alimentação Escolar" in texto
    assert "RELATÓRIO DE HISTÓRICO DE MEDIÇÃO INICIAL" in texto

    assert "RECEBIDO PARA ANÁLISE" in texto
    assert "Unidade Educacional" in texto
    assert "DRE" in texto

    assert "DEVOLVIDO PARA AJUSTES PELA DRE" in texto
    assert "Abril/2025" in texto
    assert "Correções Solicitadas" in texto
    assert "PERÍODO" in texto
    assert "TABELA DE LANÇAMENTO" in texto
    assert "CORREÇÕES" in texto
    assert "OBSERVAÇÃO" in texto
    assert "Manhã" in texto
    assert "Alimentação" in texto

    assert "CORRIGIDO PARA DRE" in texto
    assert "Correções Realizadas pela UE" in texto
    assert "Período Manhã" in texto
    assert "Tabela de Alimentação" in texto
    assert "DIAS 12" in texto
    assert "Lanche 4h" in texto
    assert "Repetição de Refeição" in texto

    assert "APROVADO PELA DRE" in texto
    assert "DEVOLVIDO PARA AJUSTES PELA CODAE" in texto

    assert "CORRIGIDO PARA CODAE" in texto
    assert "APROVADO PELA CODAE" in texto


def test_filtrar_historico_por_acao_remove_item(solicitacao_com_historico_correcao):
    historico = json.loads(solicitacao_com_historico_correcao.historico)
    assert len(historico) == 6
    result = filtrar_historico_por_acao(historico, "MEDICAO_CORRECAO_SOLICITADA")

    assert result is not None
    assert result["acao"] == "MEDICAO_CORRECAO_SOLICITADA"
    assert len(historico) == 5


def test_filtrar_historico_por_acao_nao_encontra(solicitacao_com_historico_correcao):
    historico = json.loads(solicitacao_com_historico_correcao.historico)
    assert len(historico) == 6
    result = filtrar_historico_por_acao(historico, "ACAO_INEXISTENTE")

    assert result is None
    assert len(historico) == 6


def test_filtrar_historico_por_acao_remove_apenas_uma_ocorrencia(
    solicitacao_com_historico_correcao,
):
    historico = json.loads(solicitacao_com_historico_correcao.historico)

    historico.append(historico[0].copy())

    result = filtrar_historico_por_acao(historico, "MEDICAO_CORRECAO_SOLICITADA")

    assert result is not None
    assert (
        len([h for h in historico if h["acao"] == "MEDICAO_CORRECAO_SOLICITADA"]) == 1
    )


def test_ajusta_informacoes_fluxo_completo(
    solicitacao_com_historico_correcao,
):
    solicitacao = solicitacao_com_historico_correcao

    logs = solicitacao.logs.order_by("criado_em")
    historico = json.loads(solicitacao.historico)

    data_solicitacao = (
        f"{converte_numero_em_mes(int(solicitacao.mes))}/{solicitacao.ano}"
    )

    result = ajusta_informacoes_por_status(
        logs,
        historico,
        {
            "escola": solicitacao.escola,
            "data_solicitacao": data_solicitacao,
        },
    )

    assert len(result) == 7

    titulos = [item["titulo"] for item in result]

    assert "RECEBIDO PARA ANÁLISE" in titulos
    assert "DEVOLVIDO PARA AJUSTES PELA DRE" in titulos
    assert "CORRIGIDO PARA DRE" in titulos
    assert "APROVADO PELA DRE" in titulos
    assert "DEVOLVIDO PARA AJUSTES PELA CODAE" in titulos
    assert "CORRIGIDO PARA CODAE" in titulos
    assert "APROVADO PELA CODAE" in titulos


def test_ajusta_informacoes_inclui_alteracoes_quando_tem_wf(
    solicitacao_com_historico_correcao,
):
    solicitacao = solicitacao_com_historico_correcao

    logs = solicitacao.logs.order_by("criado_em")
    historico = json.loads(solicitacao.historico)

    result = ajusta_informacoes_por_status(
        logs,
        historico,
        {
            "escola": solicitacao.escola,
            "data_solicitacao": "04/2025",
        },
    )

    itens_com_alteracoes = [item for item in result if "alteracoes" in item]

    assert len(itens_com_alteracoes) >= 1
    assert all("mes_lancamento" in item for item in itens_com_alteracoes)


def test_ajusta_informacoes_preenche_dados_ue(
    solicitacao_com_historico_correcao,
):
    solicitacao = solicitacao_com_historico_correcao

    logs = solicitacao.logs.order_by("criado_em")
    historico = json.loads(solicitacao.historico)

    result = ajusta_informacoes_por_status(
        logs,
        historico,
        {
            "escola": solicitacao.escola,
            "data_solicitacao": "04/2025",
        },
    )

    item_ue = next(item for item in result if item["titulo"] == "RECEBIDO PARA ANÁLISE")

    assert item_ue["unidade"] == solicitacao.escola.nome
    assert item_ue["dre"] == solicitacao.escola.diretoria_regional.nome


def test_ajusta_informacoes_consume_historico_sem_repetir(
    solicitacao_com_historico_correcao,
):
    solicitacao = solicitacao_com_historico_correcao

    logs = solicitacao.logs.order_by("criado_em")
    historico = json.loads(solicitacao.historico)

    result = ajusta_informacoes_por_status(
        logs,
        historico,
        {
            "escola": solicitacao.escola,
            "data_solicitacao": "04/2025",
        },
    )

    acoes = [item.get("alteracoes") for item in result if "alteracoes" in item]

    assert len(acoes) == len(set(map(str, acoes)))
