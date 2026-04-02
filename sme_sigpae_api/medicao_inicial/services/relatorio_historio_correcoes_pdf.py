from datetime import datetime
import json

from django.template.loader import render_to_string

from sme_sigpae_api.dados_comuns.utils import converte_numero_em_mes
from sme_sigpae_api.escola.models import DiretoriaRegional, Escola, Lote
from sme_sigpae_api.medicao_inicial.models import SolicitacaoMedicaoInicial
from sme_sigpae_api.relatorios.utils import html_to_pdf_file


def _formata_filtros(query_params: dict):
    mes, ano = query_params.get("mes_ano").split("_")
    filtros = f"{converte_numero_em_mes(int(mes))} - {ano}"

    dre_uuid = query_params.get("diretoria_regional")
    if dre_uuid:
        dre = DiretoriaRegional.objects.filter(uuid=dre_uuid).first()
        filtros += f" | {dre.nome}"

    lotes_uuid = query_params.get("lotes")
    if lotes_uuid:
        lotes = Lote.objects.filter(uuid__in=lotes_uuid).values_list("nome", flat=True)
        filtros += f" | {', '.join(lotes)}"

    escola_codigo_eol = query_params.get("escola")
    if escola_codigo_eol:
        escola_codigo_eol, *_ = escola_codigo_eol.split("-")
        escola = Escola.objects.filter(codigo_eol=escola_codigo_eol.strip()).first()
        filtros += f" | {escola.nome}"

    periodo_lancamento_de = query_params.get("periodo_lancamento_de")
    periodo_lancamento_ate = query_params.get("periodo_lancamento_ate")
    if periodo_lancamento_de and periodo_lancamento_ate:
        filtros += f" | Período de lançamento: {periodo_lancamento_de} até {periodo_lancamento_ate}"

    return filtros


def gera_relatorio_historico_correcoes_pdf(solicitacao_uuid):
    solicitacao = SolicitacaoMedicaoInicial.objects.get(uuid=solicitacao_uuid)
    logs = solicitacao.logs.order_by("criado_em")
    historico = json.loads(solicitacao.historico)
    
    html_string = render_to_string(
        "relatorio_historico_correcoes_medicao.html",
        {
            "logs": logs,
            "solicitacao": solicitacao,
            "subtitulo": "RELATÓRIO DE HISTÓRICO DE MEDIÇÃO INICIAL",
        },
    )

    return html_to_pdf_file(html_string, "relatorio_historio_correcoes.pdf", True)
