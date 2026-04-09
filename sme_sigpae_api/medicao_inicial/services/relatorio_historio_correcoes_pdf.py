from datetime import datetime
import json

from django.template.loader import render_to_string
from sme_sigpae_api.dados_comuns.fluxo_status import SolicitacaoMedicaoInicialWorkflow
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.dados_comuns.utils import converte_numero_em_mes
from sme_sigpae_api.medicao_inicial.models import SolicitacaoMedicaoInicial
from sme_sigpae_api.produto.constants import STATUS_DICT
from sme_sigpae_api.relatorios.utils import html_to_pdf_file

def filtrar_historico_por_acao(
    historico_restante: list[dict], acao: str, data_log: datetime, tolerancia_segundos: int = 120
) -> list[dict]:
    """
    Busca e remove uma entrada específica do histórico baseado na ação e proximidade temporal com o log.
    Este método percorre a lista de histórico restante e localiza a primeira entrada que corresponda
    à ação especificada e que tenha sido criada dentro de uma janela de tolerância de tempo em relação
    ao log. Ao encontrar, remove a entrada do histórico restante para evitar duplicidade no processamento.

    Args:
        historico_restante (list[dict]): Lista de dicionários contendo as entradas do histórico ainda não processadas. 
            Cada entrada deve conter os campos 'acao' e 'criado_em' (formato "dd/mm/YYYY HH:MM:SS").
        acao (str): Código da ação a ser buscada no histórico (ex: "MEDICAO_CORRECAO_SOLICITADA_CODAE").
        data_log (datetime): Data e hora de criação do log que está sendo processado.
        tolerancia_segundos (int, optional):Janela de tempo em segundos para considerar que o histórico corresponde ao log. Defaults to 120.

    Returns:
        list[dict] | None: Retorna o dicionário do histórico encontrado e removido da lista original, ou None se nenhuma entrada correspondente for 
            encontrada dentro da tolerância.
    """
    for i, h in enumerate(historico_restante):
        if h.get("acao") == acao:
            data_hist = datetime.strptime(h["criado_em"], "%d/%m/%Y %H:%M:%S")
            diferenca = abs((data_log - data_hist).total_seconds())
            if diferenca <= tolerancia_segundos:
                return historico_restante.pop(i)
    return None

def ajusta_informacoes_por_status(logs: LogSolicitacoesUsuario, historico: list[dict], extras: dict):
    """
    Processa os logs e o histórico para gerar uma lista estruturada de informações para o relatório.
    Este método itera sobre todos os logs de uma solicitação de medição, identifica o status de cada 
    evento e associa com as entradas correspondentes do histórico quando necessário. Para cada status,
    extrai informações relevantes como título da ação, data, usuário responsável e, quando aplicável,
    as alterações realizadas (no caso de correções solicitadas ou realizadas).
    
    A associação entre logs e histórico é feita através do método filtrar_historico_por_acao(),
    que garante que cada entrada do histórico seja usada apenas uma vez e corresponda temporalmente
    ao log apropriado.

    Args:
        logs (LogSolicitacoesUsuario): QuerySet ou lista de objetos de log ordenados cronologicamente. 
            Cada log contém status_evento_explicacao, criado_em e dados do usuário.
        historico (list[dict]):  Lista de dicionários com o histórico completo da solicitação, contendo ações e alterações registradas.
        extras (dict): Dicionário com informações complementares necessárias para o relatório.
                       Deve conter:
                       - 'escola': Objeto da escola com nome e diretoria_regional.nome
                       - 'data_solicitacao': String formatada com mês/ano da solicitação

    Returns:
        list[dict]: Lista de dicionários estruturados com as informações processadas para o relatório.
        Cada dicionário contém campos como 'titulo', 'data', 'rf', 'nome' e, opcionalmente,'unidade', 'dre', 'mes_lancamento' e 'alteracoes'.
    """
    informacoes = []
    escola = extras["escola"]
    mes_ano = extras["data_solicitacao"]
    historico_restante = historico.copy()
    
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
            historico_status = filtrar_historico_por_acao(historico_restante, SolicitacaoMedicaoInicialWorkflow.MEDICAO_CORRECAO_SOLICITADA, log.criado_em)
            if historico_status:
                informacoes.append({
                    "titulo": "DEVOLVIDO PARA AJUSTES PELA DRE",
                    "data": log.criado_em,
                    "rf": log.usuario.registro_funcional,
                    "nome": log.usuario.nome,
                    "mes_lancamento": mes_ano,
                    "alteracoes": historico_status.get("alteracoes")
                })
        elif log.status_evento_explicacao == STATUS_DICT[LogSolicitacoesUsuario.MEDICAO_CORRIGIDA_PELA_UE]:
            historico_status = filtrar_historico_por_acao(historico_restante, SolicitacaoMedicaoInicialWorkflow.MEDICAO_CORRIGIDA_PELA_UE, log.criado_em)
            if historico_status:
                informacoes.append({
                    "titulo": "CORRIGIDO PARA DRE",
                    "data": log.criado_em,
                    "rf": log.usuario.registro_funcional,
                    "nome": log.usuario.nome,
                    "mes_lancamento": mes_ano,
                    "alteracoes": historico_status.get("alteracoes")
                })
        elif log.status_evento_explicacao == STATUS_DICT[LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_DRE]:
            informacoes.append({
                "titulo": "APROVADO PELA DRE",
                "data": log.criado_em,
                "rf": log.usuario.registro_funcional,
                "nome": log.usuario.nome,
            })
        elif log.status_evento_explicacao == STATUS_DICT[LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA_CODAE]:
            historico_status = filtrar_historico_por_acao(historico_restante, SolicitacaoMedicaoInicialWorkflow.MEDICAO_CORRECAO_SOLICITADA_CODAE, log.criado_em)
            if historico_status:
                informacoes.append({
                    "titulo": "DEVOLVIDO PARA AJUSTES PELA CODAE",
                    "data": log.criado_em,
                    "rf": log.usuario.registro_funcional,
                    "nome": log.usuario.nome,
                    "mes_lancamento": mes_ano,
                    "alteracoes": historico_status.get("alteracoes")
                })
        elif log.status_evento_explicacao == STATUS_DICT[LogSolicitacoesUsuario.MEDICAO_CORRIGIDA_PARA_CODAE]:
            historico_status = filtrar_historico_por_acao(historico_restante, SolicitacaoMedicaoInicialWorkflow.MEDICAO_CORRIGIDA_PARA_CODAE, log.criado_em)
            if historico_status:
                informacoes.append({
                    "titulo": "CORRIGIDO PARA CODAE",
                    "data": log.criado_em,
                    "rf": log.usuario.registro_funcional,
                    "nome": log.usuario.nome,
                    "mes_lancamento": mes_ano,
                    "alteracoes": historico_status.get("alteracoes")
                })
        elif log.status_evento_explicacao == STATUS_DICT[LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE]:
            informacoes.append({
                "titulo": "APROVADO PELA CODAE",
                "data": log.criado_em,
                "rf": log.usuario.registro_funcional,
                "nome": log.usuario.nome,

            })

    return informacoes


def gera_relatorio_historico_correcoes_pdf(solicitacao_uuid: SolicitacaoMedicaoInicial):
    """
    Gera um relatório em PDF contendo o histórico completo de correções de uma solicitação de medição inicial.
    
    Este método é o ponto de entrada principal para a geração do relatório. Ele recupera a solicitação
    do banco de dados, processa seus logs e histórico, renderiza um template HTML com as informações
    e converte o resultado para um arquivo PDF pronto para download.
    
    O relatório gerado contém:
    - Cabeçalho com informações da solicitação (escola, mês/ano, número da solicitação)
    - Linha do tempo com todas as ações realizadas (envios, correções, aprovações)
    - Detalhes das alterações solicitadas e realizadas em cada etapa de correção
    - Identificação dos usuários responsáveis por cada ação
    - Data e hora de geração do relatório

    Args:
        solicitacao_uuid (SolicitacaoMedicaoInicial): UUID da solicitação de medição inicial a ser recuperada do banco de dados.

    Returns:
        HttpResponse | bytes: Retorna o arquivo PDF gerado como resposta HTTP para download, incluindo cabeçalhos apropriados para forçar o
            download do navegador.
    """
    solicitacao = SolicitacaoMedicaoInicial.objects.get(uuid=solicitacao_uuid)
    logs = solicitacao.logs.order_by("criado_em")
    historico = json.loads(solicitacao.historico)
    data_solicitacao = f"{converte_numero_em_mes(int(solicitacao.mes))}/{solicitacao.ano}"
    informacoes = ajusta_informacoes_por_status(logs, historico, {"escola": solicitacao.escola, "data_solicitacao": data_solicitacao})
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
