from datetime import datetime
import json

from django.template.loader import render_to_string

from sme_sigpae_api.dados_comuns.fluxo_status import SolicitacaoMedicaoInicialWorkflow
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.dados_comuns.utils import converte_numero_em_mes
from sme_sigpae_api.escola.models import DiretoriaRegional, Escola, Lote
from sme_sigpae_api.medicao_inicial.models import SolicitacaoMedicaoInicial
from sme_sigpae_api.produto.constants import STATUS_DICT
from sme_sigpae_api.relatorios.utils import html_to_pdf_file

def filtrar_por_acao(
    dados: list[dict], acao: str
) -> list[dict]:
    """
    Filtra uma lista de dicionários pelo campo 'acao'.
    
    Args:
        dados (list[dict]): _description_
        acao (str): _description_

    Returns:
        list[dict]: _description_
    """
    return [item for item in dados if item.get("acao") == acao]

def ajustes(logs, historico, extras):
    informacoes = []
    escola = extras["escola"]
    mes_ano = extras["data_solicitacao"]
    
    for log in logs:
        if log.status_evento_explicacao == STATUS_DICT[LogSolicitacoesUsuario.MEDICAO_ENVIADA_PELA_UE]:
            informacoes.append({
                "titulo": "RECEBIDO PARA ANÁLISE",
                "data": log.criado_em,
                "rf": log.usuario.registro_funcional,
                "nome": log.usuario.nome,
                "unidade": escola.nome,
                "dre": escola.diretoria_regional.nome
            })
        elif log.status_evento_explicacao == STATUS_DICT[LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA]:
            h = filtrar_por_acao(historico, SolicitacaoMedicaoInicialWorkflow.MEDICAO_CORRECAO_SOLICITADA)
            if h:
                informacoes.append({
                    "titulo": "DEVOLVIDO PARA AJUSTES PELA DRE",
                    "data": log.criado_em,
                    "rf": log.usuario.registro_funcional,
                    "nome": log.usuario.nome,
                    "mes_lancamento": mes_ano,
                    "alteracoes": h[0].get("alteracoes")
                })
            
        elif log.status_evento_explicacao == STATUS_DICT[LogSolicitacoesUsuario.MEDICAO_CORRIGIDA_PELA_UE]:
            h = filtrar_por_acao(historico, SolicitacaoMedicaoInicialWorkflow.MEDICAO_CORRIGIDA_PELA_UE)
            if h:
                informacoes.append({
                    "titulo": "CORRIGIDO PARA DRE",
                    "data": log.criado_em,
                    "rf": log.usuario.registro_funcional,
                    "nome": log.usuario.nome,
                    "mes_lancamento": mes_ano,
                    "alteracoes": h[0].get("alteracoes")
                })
        elif log.status_evento_explicacao == STATUS_DICT[LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_DRE]:
            informacoes.append({
                "titulo": "APROVADO PELA DRE",
                "data": log.criado_em,
                "rf": log.usuario.registro_funcional,
                "nome": log.usuario.nome,
            })
        elif log.status_evento_explicacao == STATUS_DICT[LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA_CODAE]:
            h = filtrar_por_acao(historico, SolicitacaoMedicaoInicialWorkflow.MEDICAO_CORRECAO_SOLICITADA_CODAE)
            if h:
                informacoes.append({
                    "titulo": "DEVOLVIDO PARA AJUSTES PELA CODAE",
                    "data": log.criado_em,
                    "rf": log.usuario.registro_funcional,
                    "nome": log.usuario.nome,
                    "mes_lancamento": mes_ano,
                    "alteracoes": h[0].get("alteracoes")
                })
        elif log.status_evento_explicacao == STATUS_DICT[LogSolicitacoesUsuario.MEDICAO_CORRIGIDA_PARA_CODAE]:
            h = filtrar_por_acao(historico, SolicitacaoMedicaoInicialWorkflow.MEDICAO_CORRIGIDA_PARA_CODAE)
            if h:
                informacoes.append({
                    "titulo": "CORRIGIDO PARA CODAE",
                    "data": log.criado_em,
                    "rf": log.usuario.registro_funcional,
                    "nome": log.usuario.nome,
                    "mes_lancamento": mes_ano,
                    "alteracoes": h[0].get("alteracoes")
                })
        elif log.status_evento_explicacao == STATUS_DICT[LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE]:
            if h:
                informacoes.append({
                    "titulo": "APROVADO PELA CODAE",
                    "data": log.criado_em,
                    "rf": log.usuario.registro_funcional,
                    "nome": log.usuario.nome,

                })

    return informacoes

def gera_relatorio_historico_correcoes_pdf(solicitacao_uuid):
    solicitacao = SolicitacaoMedicaoInicial.objects.get(uuid=solicitacao_uuid)
    logs = solicitacao.logs.order_by("criado_em")
    historico = json.loads(solicitacao.historico)
    data_solicitacao = f"{converte_numero_em_mes(int(solicitacao.mes))}/{solicitacao.ano}"
    informacoes = ajustes(logs, historico, {"escola": solicitacao.escola, "data_solicitacao": data_solicitacao})
    html_string = render_to_string(
        "relatorio_historico_correcoes_medicao.html",
        {
            "logs": informacoes,
            "solicitacao": solicitacao,
            "subtitulo": "RELATÓRIO DE HISTÓRICO DE MEDIÇÃO INICIAL",
        },
    )
    data_arquivo = datetime.today().strftime("%d/%m/%Y às %H:%M")
    html_string = html_string.replace("dt_file", data_arquivo)
    return html_to_pdf_file(html_string, "relatorio_historio_correcoes.pdf", True)
