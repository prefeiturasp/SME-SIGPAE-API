
from django.template.loader import render_to_string
from sme_sigpae_api.relatorios.utils import html_to_pdf_file
from datetime import datetime
from sme_sigpae_api.escola.models import Lote


def gera_dicionario_relatorio_recreio(solicitacoes):
    dados = []
    for solicitacao in solicitacoes:
        alergias = solicitacao.alergias_intolerancias.all()
        alergias_lista = [a.descricao for a in alergias] if alergias else ['--']
        dados_solicitacoes = {
            "codigo_eol_aluno": solicitacao.aluno.codigo_eol,
            "nome_aluno": solicitacao.aluno.nome,
            "nome_escola": solicitacao.escola.nome,
            "escola_destino": solicitacao.escola_destino.nome if solicitacao.escola_destino else "--",
            "data_inicio": solicitacao.data_inicio.strftime("%d/%m/%Y") if solicitacao.data_inicio else "--",
            "data_fim": solicitacao.data_termino.strftime("%d/%m/%Y") if solicitacao.data_termino else "--",
            "classificacao": solicitacao.classificacao.nome if solicitacao.classificacao else "--",
            "alergias_intolerancias": ", ".join(alergias_lista),
        }
        dados.append(dados_solicitacoes)
    return dados


def gera_pdf_relatorio_recreio_nas_ferias(dados, user, lote):
    dre_lote = Lote.objects.get(uuid=lote)
    html_string = render_to_string(
        "relatorio_recreio_nas_ferias.html",
        {
            "dados": dados,
            "user": user,
            "total_dados": len(dados),
            "data_extracao": datetime.now().strftime("%d/%m/%Y"),
            "data_hora_geracao": datetime.now().strftime("%d/%m/%Y às %H:%M:%S"),
            "dre_lote": f"{dre_lote.diretoria_regional.iniciais} - {dre_lote.nome}"
        },
    )
    return html_to_pdf_file(
        html_string, "relatorio_recreio_nas_ferias.pdf", is_async=True
    )
