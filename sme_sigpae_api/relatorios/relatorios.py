import datetime
from calendar import monthrange

import environ
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db.models import F, FloatField, Sum
from django.template.loader import get_template, render_to_string

from sme_sigpae_api.paineis_consolidados.models import MoldeConsolidado

from ..cardapio.base.models import (
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from ..dados_comuns.fluxo_status import DietaEspecialWorkflow
from ..dados_comuns.fluxo_status import GuiaRemessaWorkFlow as GuiaStatus
from ..dados_comuns.fluxo_status import ReclamacaoProdutoWorkflow
from ..dados_comuns.models import LogSolicitacoesUsuario
from ..escola.constants import (
    PERIODOS_CEMEI_EVENTO_ESPECIFICO,
    PERIODOS_ESPECIAIS_CEMEI,
)
from ..escola.models import Codae, DiretoriaRegional, Escola
from ..imr.models import TipoOcorrencia
from ..kit_lanche.models import EscolaQuantidade
from ..logistica.api.helpers import retorna_status_guia_remessa
from ..medicao_inicial.models import ValorMedicao
from ..medicao_inicial.utils import (
    build_lista_campos_observacoes,
    build_tabela_relatorio_consolidado,
    build_tabela_somatorio_body,
    build_tabela_somatorio_body_cei,
    build_tabela_somatorio_dietas_body,
    build_tabelas_relatorio_medicao,
    build_tabelas_relatorio_medicao_cei,
    build_tabelas_relatorio_medicao_cemei,
    build_tabelas_relatorio_medicao_emebs,
)
from ..pre_recebimento.api.helpers import (
    formata_cnpj_ficha_tecnica,
    formata_telefone_ficha_tecnica,
    retorna_status_ficha_tecnica,
)
from ..pre_recebimento.models import InformacoesNutricionaisFichaTecnica
from ..relatorios.utils import (
    html_to_pdf_cancelada,
    html_to_pdf_file,
    html_to_pdf_multiple,
    html_to_pdf_response,
)
from ..terceirizada.models import Edital
from ..terceirizada.utils import transforma_dados_relatorio_quantitativo
from . import constants
from .utils import (
    conta_filtros,
    deleta_log_temporario_se_necessario,
    formata_justificativas_usuario_dre_codae,
    formata_logs,
    formata_logs_kit_lanche_unificado_cancelado_por_usuario_dre,
    formata_logs_kit_lanche_unificado_cancelado_por_usuario_escola,
    formata_motivos_inclusao,
    get_config_cabecario_relatorio_analise,
    get_diretorias_regionais,
    get_ultima_justificativa_analise_sensorial,
    get_width,
    todas_escolas_sol_kit_lanche_unificado_cancelado,
)

env = environ.Env()


def relatorio_filtro_periodo(
    request, query_set_consolidado, escola_nome="", dre_nome=""
):
    # TODO: se query_set_consolidado tiver muitos resultados, pode demorar no front-end
    # melhor mandar via celery pro email de quem solicitou
    # ou por padrão manda tudo pro celery
    request_params = request.GET

    tipo_solicitacao = request_params.get("tipo_solicitacao", "INVALIDO")
    status_solicitacao = request_params.get("status_solicitacao", "INVALIDO")
    data_inicial = datetime.datetime.strptime(
        request_params.get("data_inicial"), "%Y-%m-%d"
    )
    data_final = datetime.datetime.strptime(
        request_params.get("data_final"), "%Y-%m-%d"
    )
    filtro = {
        "tipo_solicitacao": tipo_solicitacao,
        "status": status_solicitacao,
        "data_inicial": data_inicial,
        "data_final": data_final,
    }

    html_string = render_to_string(
        "relatorio_filtro.html",
        {
            "diretoria_regional_nome": dre_nome,
            "escola_nome": escola_nome,
            "filtro": filtro,
            "query_set_consolidado": query_set_consolidado,
        },
    )
    return html_to_pdf_response(
        html_string, f"relatorio_filtro_de_{data_inicial}_ate_{data_final}.pdf"
    )


def relatorio_resumo_anual_e_mensal(request, resumos_mes, resumo_ano):
    meses = range(12)
    escola_nome = "ESCOLA"
    dre_nome = "DRE"
    filtro = {
        "tipo_solicitacao": "TODOS",
        "status": "TODOS",
        "data_inicial": "data_inicial",
        "data_final": "data_final",
    }

    html_string = render_to_string(
        "relatorio_resumo_mes_ano.html",
        {
            "diretoria_regional_nome": dre_nome,
            "escola_nome": escola_nome,
            "filtro": filtro,
            "resumos_mes": resumos_mes,
            "resumo_ano": resumo_ano,
            "meses": meses,
        },
    )
    return html_to_pdf_response(html_string, "relatorio_resumo_anual_e_mensal.pdf")


def relatorio_kit_lanche_unificado(request, solicitacao):
    qtd_escolas = EscolaQuantidade.objects.filter(
        solicitacao_unificada=solicitacao
    ).count()
    instituicao = request.user.vinculo_atual.instituicao
    usuario_eh_escola = isinstance(instituicao, Escola)
    usuario_eh_dre_ou_codae = isinstance(instituicao, DiretoriaRegional) or isinstance(
        instituicao, Codae
    )
    sol_unificada_escola = None
    justificativas_formatadas = None
    todos_kits_cancelados = None
    log_temporario = False
    uuid_log_temporario = False
    logs = solicitacao.logs

    if usuario_eh_escola:
        sol_unificada_escola = solicitacao.escolas_quantidades.filter(
            escola__uuid=instituicao.uuid
        )[0]
        if sol_unificada_escola.cancelado:
            inst_sol_unificada_escola = (
                sol_unificada_escola.cancelado_por.vinculo_atual.instituicao
            )
            if sol_unificada_escola.cancelado and isinstance(
                inst_sol_unificada_escola, Escola
            ):
                status_ev = LogSolicitacoesUsuario.ESCOLA_CANCELOU
                log_criado = LogSolicitacoesUsuario.objects.create(
                    descricao=str(solicitacao),
                    status_evento=status_ev,
                    solicitacao_tipo=LogSolicitacoesUsuario.SOLICITACAO_KIT_LANCHE_UNIFICADA,
                    usuario=sol_unificada_escola.cancelado_por,
                    uuid_original=solicitacao.uuid,
                    justificativa=sol_unificada_escola.cancelado_justificativa,
                    resposta_sim_nao=False,
                    criado_em=sol_unificada_escola.cancelado_em,
                )
                uuid_log_temporario = log_criado.uuid
                log_criado.criado_em = sol_unificada_escola.cancelado_em
                log_criado.save()
                log_temporario = True
                logs = formata_logs_kit_lanche_unificado_cancelado_por_usuario_escola(
                    solicitacao, uuid_log_temporario, logs
                )
            cancelado_pela_dre = (
                sol_unificada_escola.cancelado_por.tipo_usuario == "diretoriaregional"
            )
            if sol_unificada_escola.cancelado and cancelado_pela_dre:
                status_ev = LogSolicitacoesUsuario.DRE_CANCELOU
                log_criado = LogSolicitacoesUsuario.objects.create(
                    descricao=str(solicitacao),
                    status_evento=status_ev,
                    solicitacao_tipo=LogSolicitacoesUsuario.SOLICITACAO_KIT_LANCHE_UNIFICADA,
                    usuario=sol_unificada_escola.cancelado_por,
                    uuid_original=solicitacao.uuid,
                    justificativa=sol_unificada_escola.cancelado_justificativa,
                    resposta_sim_nao=False,
                    criado_em=sol_unificada_escola.cancelado_em,
                )
                uuid_log_temporario = log_criado.uuid
                log_criado.criado_em = sol_unificada_escola.cancelado_em
                log_criado.save()
                log_temporario = True
                logs = formata_logs_kit_lanche_unificado_cancelado_por_usuario_dre(
                    solicitacao, uuid_log_temporario, logs
                )
    if usuario_eh_dre_ou_codae:
        justificativas_formatadas = formata_justificativas_usuario_dre_codae(
            solicitacao
        )
        todos_kits_cancelados = todas_escolas_sol_kit_lanche_unificado_cancelado(
            solicitacao
        )
    html_string = render_to_string(
        "solicitacao_kit_lanche_unificado.html",
        {
            "solicitacao": solicitacao,
            "qtd_escolas": qtd_escolas,
            "fluxo": constants.FLUXO_PARTINDO_DRE,
            "width": get_width(constants.FLUXO_PARTINDO_DRE, logs),
            "logs": formata_logs(logs),
            "usuario_eh_escola": usuario_eh_escola,
            "usuario_eh_dre_ou_codae": usuario_eh_dre_ou_codae,
            "nome_instituicao": instituicao.nome,
            "justificativas_formatadas": justificativas_formatadas,
            "todos_kits_cancelados": todos_kits_cancelados,
            "sol_unificada_escola": sol_unificada_escola,
        },
    )
    deleta_log_temporario_se_necessario(
        log_temporario, solicitacao, uuid_log_temporario
    )
    return html_to_pdf_response(
        html_string, f"solicitacao_unificada_{solicitacao.id_externo}.pdf"
    )


def relatorio_alteracao_cardapio(request, solicitacao):  # noqa C901
    substituicoes = solicitacao.substituicoes_periodo_escolar
    formata_substituicoes = []

    for subs in substituicoes.all():
        tipos_alimentacao_de = subs.tipos_alimentacao_de.all()
        tipos_alimentacao_para = subs.tipos_alimentacao_para.all()

        tad_formatado = ""
        tap_formatado = ""

        for tad in tipos_alimentacao_de:
            if len(tad_formatado) > 0:
                tad_formatado = f"{tad_formatado}, {tad.nome}"
            else:
                tad_formatado = tad.nome

        for tap in tipos_alimentacao_para:
            if len(tap_formatado) > 0:
                tap_formatado = f"{tap_formatado}, {tap.nome}"
            else:
                tap_formatado = tap.nome

        resultado = {
            "periodo": subs.periodo_escolar.nome,
            "qtd_alunos": subs.qtd_alunos,
            "tipos_alimentacao_de": tad_formatado,
            "tipos_alimentacao_para": tap_formatado,
        }

        formata_substituicoes.append(resultado)

    escola = solicitacao.rastro_escola
    logs = solicitacao.logs
    html_string = render_to_string(
        "solicitacao_alteracao_cardapio.html",
        {
            "escola": escola,
            "solicitacao": solicitacao,
            "substituicoes": formata_substituicoes,
            "fluxo": constants.FLUXO_ALTERACAO_DE_CARDAPIO,
            "width": get_width(constants.FLUXO_ALTERACAO_DE_CARDAPIO, solicitacao.logs),
            "logs": formata_logs(logs),
        },
    )
    return html_to_pdf_response(
        html_string, f"alteracao_cardapio_{solicitacao.id_externo}.pdf"
    )


def relatorio_alteracao_cardapio_cei(request, solicitacao):
    escola = solicitacao.rastro_escola
    substituicoes = solicitacao.substituicoes_cei_periodo_escolar
    logs = solicitacao.logs
    html_string = render_to_string(
        "solicitacao_alteracao_cardapio_cei.html",
        {
            "escola": escola,
            "solicitacao": solicitacao,
            "substituicoes": substituicoes,
            "fluxo": constants.FLUXO_PARTINDO_ESCOLA,
            "width": get_width(constants.FLUXO_PARTINDO_ESCOLA, solicitacao.logs),
            "logs": formata_logs(logs),
        },
    )
    return html_to_pdf_response(
        html_string, f"alteracao_cardapio_{solicitacao.id_externo}.pdf"
    )


def relatorio_alteracao_alimentacao_cemei(request, solicitacao):  # noqa C901
    escola = solicitacao.rastro_escola
    logs = solicitacao.logs
    periodos_escolares_cei = []
    periodos_cei = []
    periodos_escolares_emei = []
    periodos_emei = []
    for each in solicitacao.substituicoes_cemei_cei_periodo_escolar.all():
        if each.periodo_escolar.nome not in periodos_escolares_cei:
            periodos_escolares_cei.append(each.periodo_escolar.nome)
    for each in solicitacao.substituicoes_cemei_emei_periodo_escolar.all():
        if each.periodo_escolar.nome not in periodos_escolares_emei:
            periodos_escolares_emei.append(each.periodo_escolar.nome)
    vinculos_class = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar
    vinculos_cei = vinculos_class.objects.filter(
        periodo_escolar__nome__in=PERIODOS_ESPECIAIS_CEMEI,
        tipo_unidade_escolar__iniciais__in=["CEI DIRET"],
    )
    vinculos_cei = vinculos_cei.order_by("periodo_escolar__posicao")
    vinculos_emei = vinculos_class.objects.filter(
        periodo_escolar__nome__in=PERIODOS_ESPECIAIS_CEMEI,
        tipo_unidade_escolar__iniciais__in=["EMEI"],
    )
    vinculos_emei = vinculos_emei.order_by("periodo_escolar__posicao")

    for vinculo in vinculos_cei:
        if vinculo.periodo_escolar.nome in periodos_escolares_cei:
            periodo = {}
            faixas = []
            periodo["nome"] = vinculo.periodo_escolar.nome
            qtd_solicitacao = (
                solicitacao.substituicoes_cemei_cei_periodo_escolar.filter(
                    periodo_escolar__nome=vinculo.periodo_escolar.nome
                )
            )
            for faixa in qtd_solicitacao:
                periodo["tipos_alimentacao_de"] = ", ".join(
                    faixa.tipos_alimentacao_de.values_list("nome", flat=True)
                )
                periodo["tipos_alimentacao_para"] = ", ".join(
                    faixa.tipos_alimentacao_para.values_list("nome", flat=True)
                )

                for f in faixa.faixas_etarias.all():
                    faixas.append(
                        {
                            "faixa_etaria": f.faixa_etaria.__str__,
                            "quantidade_alunos": f.quantidade,
                            "matriculados_quando_criado": f.matriculados_quando_criado,
                        }
                    )
            periodo["faixas_etarias"] = faixas

            periodo["total_solicitacao"] = sum(
                qtd_solicitacao.exclude(
                    faixas_etarias__quantidade__isnull=True
                ).values_list("faixas_etarias__quantidade", flat=True)
            )
            periodo["total_matriculados"] = sum(
                qtd_solicitacao.exclude(
                    faixas_etarias__matriculados_quando_criado__isnull=True
                ).values_list("faixas_etarias__matriculados_quando_criado", flat=True)
            )
            periodos_cei.append(periodo)

    for vinculo in vinculos_emei:
        if vinculo.periodo_escolar.nome in periodos_escolares_emei:
            periodo = {}
            periodo["nome"] = vinculo.periodo_escolar.nome
            qtd_solicitacao = (
                solicitacao.substituicoes_cemei_emei_periodo_escolar.filter(
                    periodo_escolar__nome=vinculo.periodo_escolar.nome
                )
            )
            periodo["tipos_alimentacao_de"] = ", ".join(
                qtd_solicitacao.exclude(
                    tipos_alimentacao_de__nome__isnull=True
                ).values_list("tipos_alimentacao_de__nome", flat=True)
            )
            periodo["tipos_alimentacao_para"] = ", ".join(
                qtd_solicitacao.exclude(
                    tipos_alimentacao_para__nome__isnull=True
                ).values_list("tipos_alimentacao_para__nome", flat=True)
            )
            periodo["total_solicitacao"] = sum(
                qtd_solicitacao.exclude(qtd_alunos__isnull=True).values_list(
                    "qtd_alunos", flat=True
                )
            )
            periodo["total_matriculados"] = sum(
                qtd_solicitacao.exclude(
                    matriculados_quando_criado__isnull=True
                ).values_list("matriculados_quando_criado", flat=True)
            )
            periodos_emei.append(periodo)
    data_final = None
    if solicitacao.data_final:
        data_final = solicitacao.data_final.strftime("%d/%m/%Y")
    html_string = render_to_string(
        "solicitacao_alteracao_cardapio_cemei.html",
        {
            "escola": escola,
            "solicitacao": solicitacao,
            "fluxo": constants.FLUXO_ALTERACAO_DE_CARDAPIO,
            "width": get_width(constants.FLUXO_ALTERACAO_DE_CARDAPIO, solicitacao.logs),
            "logs": formata_logs(logs),
            "periodos_cei": periodos_cei,
            "periodos_emei": periodos_emei,
            "periodos_escolares_emei": periodos_escolares_emei,
            "motivo": solicitacao.motivo,
            "data_de": solicitacao.data.strftime("%d/%m/%Y"),
            "data_ate": data_final,
        },
    )
    return html_to_pdf_response(
        html_string, f"alteracao_tipo_alimentacao_cemei_{solicitacao.id_externo}.pdf"
    )


def relatorio_dieta_especial_conteudo(solicitacao, request=None):
    if solicitacao.tipo_solicitacao == "COMUM":
        escola = solicitacao.rastro_escola
    else:
        escola = solicitacao.escola_destino
    escola_origem = solicitacao.rastro_escola
    logs = solicitacao.logs
    if solicitacao.logs.filter(
        status_evento=LogSolicitacoesUsuario.INICIO_FLUXO_INATIVACAO
    ).exists():
        if solicitacao.logs.filter(
            status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA
        ).exists():
            fluxo = constants.FLUXO_DIETA_ESPECIAL_INATIVACAO
        elif solicitacao.logs.filter(
            status_evento=LogSolicitacoesUsuario.ESCOLA_CANCELOU
        ).exists():
            fluxo = constants.FLUXO_DIETA_ESPECIAL_INATIVACAO_CANCELADO
        else:
            fluxo = constants.FLUXO_DIETA_ESPECIAL_INATIVACAO_INCOMPLETO
    else:
        fluxo = constants.FLUXO_DIETA_ESPECIAL
    eh_importado = solicitacao.eh_importado
    log_cancelamento = [
        log
        for log in logs
        if log.status_evento == LogSolicitacoesUsuario.ESCOLA_CANCELOU
    ]
    usuario = request.user
    html_string = render_to_string(
        "solicitacao_dieta_especial.html",
        {
            "escola": escola,
            "escola_origem": escola_origem,
            "lote": escola.lote,
            "solicitacao": solicitacao,
            "fluxo": fluxo,
            "width": get_width(fluxo, solicitacao.logs),
            "logs": formata_logs(logs),
            "eh_importado": eh_importado,
            "foto_aluno": solicitacao.aluno.foto_aluno_base64,
            "justificativa_cancelamento": (
                log_cancelamento[0].justificativa if log_cancelamento else None
            ),
            "tipo_usuario": usuario.tipo_usuario if usuario else None,
        },
    )
    return html_string


def relatorio_guia_de_remessa(guias, is_async=False):  # noqa C901
    SERVER_NAME = env.str("SERVER_NAME", default=None)
    page = None
    lista_pdfs = []
    for guia in guias:
        lista_imagens_conferencia = []
        lista_imagens_reposicao = []
        conferencias_individuais = []
        reposicoes_individuais = []
        reposicao = None
        insucesso = guia.insucessos.last() if guia.insucessos else None
        todos_alimentos = guia.alimentos.all().annotate(
            peso_total=Sum(
                F("embalagens__capacidade_embalagem") * F("embalagens__qtd_volume"),
                output_field=FloatField(),
            )
        )

        if (
            guia.status == GuiaStatus.PENDENTE_DE_CONFERENCIA
            or guia.status == GuiaStatus.CANCELADA
        ):
            conferencia = None
            reposicao = None
        elif guia.status == GuiaStatus.RECEBIDA:
            conferencia = guia.conferencias.last()

        else:
            conferencia = guia.conferencias.filter(eh_reposicao=False).last()
            reposicao = guia.conferencias.filter(eh_reposicao=True).last()
            if conferencia:
                conferencias_individuais = conferencia.conferencia_dos_alimentos.all()
            if reposicao:
                reposicoes_individuais = reposicao.conferencia_dos_alimentos.all()
            for alimento_guia in todos_alimentos:
                conferencias_alimento = []
                reposicoes_alimento = []
                for alimento_conferencia in conferencias_individuais:
                    if (
                        alimento_guia.nome_alimento
                        == alimento_conferencia.nome_alimento
                    ):
                        for embalagem in alimento_guia.embalagens.all():
                            if (
                                embalagem.tipo_embalagem
                                == alimento_conferencia.tipo_embalagem
                            ):
                                embalagem.qtd_recebido = (
                                    alimento_conferencia.qtd_recebido
                                )
                                embalagem.ocorrencia = alimento_conferencia.ocorrencia
                                embalagem.observacao = alimento_conferencia.observacao
                                embalagem.arquivo = alimento_conferencia.arquivo
                                if alimento_conferencia.arquivo:
                                    imagem = {
                                        "nome_alimento": alimento_guia.nome_alimento,
                                        "arquivo": alimento_conferencia.arquivo,
                                    }
                                    lista_filtrada = [
                                        a
                                        for a in lista_imagens_conferencia
                                        if a["nome_alimento"]
                                        == alimento_guia.nome_alimento
                                    ]
                                    if not lista_filtrada:
                                        lista_imagens_conferencia.append(imagem)
                                conferencias_alimento.append(embalagem)
                        alimento_guia.embalagens_conferidas = conferencias_alimento
                for alimento_reposicao in reposicoes_individuais:
                    if alimento_guia.nome_alimento == alimento_reposicao.nome_alimento:
                        for embalagem in alimento_guia.embalagens.all():
                            if (
                                embalagem.tipo_embalagem
                                == alimento_reposicao.tipo_embalagem
                            ):
                                embalagem.qtd_recebido = alimento_reposicao.qtd_recebido
                                embalagem.ocorrencia = alimento_reposicao.ocorrencia
                                embalagem.observacao = alimento_reposicao.observacao
                                embalagem.arquivo = alimento_reposicao.arquivo
                                if alimento_reposicao.arquivo:
                                    imagem = {
                                        "nome_alimento": alimento_guia.nome_alimento,
                                        "arquivo": alimento_reposicao.arquivo,
                                    }
                                    lista_filtrada = [
                                        a
                                        for a in lista_imagens_reposicao
                                        if a["nome_alimento"]
                                        == alimento_guia.nome_alimento
                                    ]
                                    if not lista_filtrada:
                                        lista_imagens_reposicao.append(imagem)
                                reposicoes_alimento.append(embalagem)
                        alimento_guia.embalagens_repostas = reposicoes_alimento

        if todos_alimentos:
            page = guia.as_dict()
            peso_total_pagina = round(
                sum(alimento.peso_total for alimento in todos_alimentos), 2
            )
            page["alimentos"] = todos_alimentos
            page["peso_total"] = peso_total_pagina
            page["status_guia"] = retorna_status_guia_remessa(page["status"])
            page["insucesso"] = insucesso
            page["conferencia"] = conferencia
            page["reposicao"] = reposicao
            page["lista_imagens_conferencia"] = lista_imagens_conferencia
            page["lista_imagens_reposicao"] = lista_imagens_reposicao

        html_template = get_template("logistica/guia_remessa/relatorio_guia.html")
        html_string = html_template.render(
            {
                "pages": [page],
                "URL": SERVER_NAME,
                "base_static_url": staticfiles_storage.location,
            }
        )

        data_arquivo = datetime.datetime.today().strftime("%d/%m/%Y às %H:%M")

        lista_pdfs.append(html_string.replace("dt_file", data_arquivo))

    if len(lista_pdfs) == 1:
        if guia.status == GuiaStatus.CANCELADA:
            return html_to_pdf_cancelada(
                lista_pdfs[0], f"guia_{guia.numero_guia}.pdf", is_async
            )
        else:
            return html_to_pdf_file(
                lista_pdfs[0], f"guia_{guia.numero_guia}.pdf", is_async
            )
    else:
        return html_to_pdf_multiple(lista_pdfs, "guias_de_remessa.pdf", is_async)


def relatorio_dieta_especial(request, solicitacao):
    html_string = relatorio_dieta_especial_conteudo(solicitacao, request)
    return html_to_pdf_response(
        html_string, f"dieta_especial_{solicitacao.id_externo}.pdf"
    )


def relatorio_dietas_especiais_terceirizada(dados):
    html_string = render_to_string(
        "relatorio_dietas_especiais_terceirizada.html", dados
    )
    return html_to_pdf_file(
        html_string, "produtos_homologados_por_terceirizada.pdf", True
    )


def relatorio_dieta_especial_protocolo(request, solicitacao):
    if solicitacao.tipo_solicitacao == "COMUM":
        escola = solicitacao.rastro_escola
    else:
        escola = solicitacao.escola_destino

    substituicao_ordenada = solicitacao.substituicoes.order_by("alimento__nome")

    referencia = "unidade" if escola.eh_parceira else "empresa"
    justificativa = obter_justificativa_dieta(solicitacao)
    html_string = render_to_string(
        "solicitacao_dieta_especial_protocolo.html",
        {
            "referencia": referencia,
            "escola": escola,
            "solicitacao": solicitacao,
            "substituicoes": substituicao_ordenada,
            "data_termino": solicitacao.data_termino,
            "log_autorizacao": solicitacao.logs.get(
                status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU
            ),
            "foto_aluno": solicitacao.aluno.foto_aluno_base64,
            "eh_dieta_especial": True,
            "eh_protocolo_dieta_especial": solicitacao.tipo_solicitacao
            == "ALTERACAO_UE",
            "motivo": (
                solicitacao.motivo_alteracao_ue.nome.split(" - ")[1]
                if solicitacao.motivo_alteracao_ue
                else None
            ),
            "justificativa": justificativa,
        },
    )
    if request:
        return html_to_pdf_response(
            html_string, f"dieta_especial_{solicitacao.id_externo}.pdf"
        )
    else:
        return html_string


def relatorio_inclusao_alimentacao_continua(request, solicitacao):
    escola = solicitacao.rastro_escola
    logs = solicitacao.logs
    html_string = render_to_string(
        "solicitacao_inclusao_alimentacao_continua.html",
        {
            "escola": escola,
            "solicitacao": solicitacao,
            "fluxo": constants.FLUXO_INCLUSAO_ALIMENTACAO,
            "width": get_width(constants.FLUXO_INCLUSAO_ALIMENTACAO, solicitacao.logs),
            "logs": formata_logs(logs),
            "week": {"D": 6, "S": 0, "T": 1, "Q": 2, "Qi": 3, "Sx": 4, "Sb": 5},
        },
    )
    return html_to_pdf_response(
        html_string, f"inclusao_alimentacao_continua_{solicitacao.id_externo}.pdf"
    )


def relatorio_inclusao_alimentacao_normal(request, solicitacao):
    escola = solicitacao.rastro_escola
    logs = solicitacao.logs
    html_string = render_to_string(
        "solicitacao_inclusao_alimentacao_normal.html",
        {
            "escola": escola,
            "solicitacao": solicitacao,
            "fluxo": constants.FLUXO_INCLUSAO_ALIMENTACAO,
            "width": get_width(constants.FLUXO_INCLUSAO_ALIMENTACAO, solicitacao.logs),
            "logs": formata_logs(logs),
        },
    )
    return html_to_pdf_response(
        html_string, f"inclusao_alimentacao_{solicitacao.id_externo}.pdf"
    )


def relatorio_inclusao_alimentacao_cei(request, solicitacao):
    escola = solicitacao.rastro_escola
    logs = solicitacao.logs
    if solicitacao.periodo_escolar:
        html_string = render_to_string(
            "solicitacao_inclusao_alimentacao_cei.html",
            {
                "escola": escola,
                "solicitacao": solicitacao,
                "fluxo": constants.FLUXO_PARTINDO_ESCOLA,
                "width": get_width(constants.FLUXO_PARTINDO_ESCOLA, solicitacao.logs),
                "logs": formata_logs(logs),
            },
        )
    else:
        qa = solicitacao.quantidade_alunos_por_faixas_etarias
        vinculos_class = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar
        inclusoes = []
        for periodo_externo in solicitacao.periodos_da_solicitacao(
            nivel_interno=False, nome_coluna="periodo_externo"
        ):
            inclusao = {"periodo_externo_nome": periodo_externo}
            vinculo = vinculos_class.objects.filter(
                periodo_escolar__nome=periodo_externo,
                ativo=True,
                tipo_unidade_escolar=escola.tipo_unidade,
            ).first()
            if vinculo:
                inclusao["tipos_alimentacao"] = ", ".join(
                    vinculo.tipos_alimentacao.values_list("nome", flat=True)
                )
            else:
                inclusao["tipos_alimentacao"] = ""
            if periodo_externo == "INTEGRAL":
                inclusao["periodos_internos"] = []
                for periodo_interno in solicitacao.periodos_da_solicitacao(
                    nivel_interno=True, nome_coluna="periodo"
                ):
                    p_faixas = qa.filter(
                        periodo__nome=periodo_interno,
                        periodo_externo__nome=periodo_externo,
                    )
                    total_inclusao = sum(
                        p_faixas.values_list("quantidade_alunos", flat=True)
                    )
                    total_matriculados = sum(
                        p_faixas.values_list("matriculados_quando_criado", flat=True)
                    )

                    p_faixas = [
                        {
                            "nome_faixa": x.faixa_etaria.__str__(),
                            "quantidade_alunos": x.quantidade_alunos,
                            "matriculados_quando_criado": x.matriculados_quando_criado,
                        }
                        for x in p_faixas
                    ]
                    inclusao["periodos_internos"].append(
                        {
                            "periodo_interno_nome": periodo_interno,
                            "quantidades_faixas": p_faixas,
                            "total_inclusao": total_inclusao,
                            "total_matriculados": total_matriculados,
                        }
                    )
            else:
                p_faixas = qa.filter(
                    periodo__nome=periodo_externo, periodo_externo__nome=periodo_externo
                )
                total_inclusao = sum(
                    p_faixas.values_list("quantidade_alunos", flat=True)
                )
                total_matriculados = sum(
                    p_faixas.values_list("matriculados_quando_criado", flat=True)
                )
                p_faixas = [
                    {
                        "nome_faixa": x.faixa_etaria.__str__(),
                        "quantidade_alunos": x.quantidade_alunos,
                        "matriculados_quando_criado": x.matriculados_quando_criado,
                    }
                    for x in p_faixas
                ]
                inclusao["quantidades_faixas"] = p_faixas
                inclusao["total_inclusao"] = total_inclusao
                inclusao["total_matriculados"] = total_matriculados
            inclusoes.append(inclusao)
        html_string = render_to_string(
            "novo_solicitacao_inclusao_alimentacao_cei.html",
            {
                "escola": escola,
                "solicitacao": solicitacao,
                "fluxo": constants.FLUXO_PARTINDO_ESCOLA,
                "width": get_width(constants.FLUXO_PARTINDO_ESCOLA, solicitacao.logs),
                "logs": formata_logs(logs),
                "inclusoes": inclusoes,
                "dias_motivos_da_inclusao_cei": solicitacao.inclusoes.all(),
            },
        )
    return html_to_pdf_response(
        html_string, f"inclusao_alimentacao_{solicitacao.id_externo}.pdf"
    )


def relatorio_inclusao_alimentacao_cemei(request, solicitacao):  # noqa C901
    escola = solicitacao.rastro_escola
    logs = solicitacao.logs
    periodos_escolares_cei = []
    periodos_cei = []
    periodos_escolares_emei = []
    periodos_emei = []
    eh_evento_especifico = False

    for each in solicitacao.quantidade_alunos_cei_da_inclusao_cemei.all():
        if each.periodo_escolar.nome not in periodos_escolares_cei:
            periodos_escolares_cei.append(each.periodo_escolar.nome)
    for each in solicitacao.quantidade_alunos_emei_da_inclusao_cemei.all():
        if each.periodo_escolar.nome not in periodos_escolares_emei:
            periodos_escolares_emei.append(each.periodo_escolar.nome)

    vinculos_class = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar
    vinculos_cei = vinculos_class.objects.filter(
        periodo_escolar__nome__in=PERIODOS_ESPECIAIS_CEMEI,
        tipo_unidade_escolar__iniciais__in=["CEI DIRET"],
    )
    vinculos_cei = vinculos_cei.order_by("periodo_escolar__posicao")
    vinculos_emei = vinculos_class.objects.filter(
        periodo_escolar__nome__in=PERIODOS_ESPECIAIS_CEMEI,
        tipo_unidade_escolar__iniciais__in=["EMEI"],
    )

    if solicitacao.dias_motivos_da_inclusao_cemei.filter(
        motivo__nome="Evento Específico"
    ):
        eh_evento_especifico = True
        vinculos_emei = vinculos_class.objects.filter(
            periodo_escolar__nome__in=PERIODOS_CEMEI_EVENTO_ESPECIFICO,
            tipo_unidade_escolar__iniciais__in=["EMEI"],
        )
    vinculos_emei = vinculos_emei.order_by("periodo_escolar__posicao")
    for vinculo in vinculos_cei:
        if vinculo.periodo_escolar.nome in periodos_escolares_cei:
            periodo = {}
            faixas = []
            periodo["nome"] = vinculo.periodo_escolar.nome
            periodo["tipos_alimentacao"] = ", ".join(
                vinculo.tipos_alimentacao.values_list("nome", flat=True)
            )
            qtd_solicitacao = (
                solicitacao.quantidade_alunos_cei_da_inclusao_cemei.filter(
                    periodo_escolar__nome=vinculo.periodo_escolar.nome
                )
            )
            for faixa in qtd_solicitacao:
                faixas.append(
                    {
                        "faixa_etaria": faixa.faixa_etaria.__str__,
                        "quantidade_alunos": faixa.quantidade_alunos,
                        "matriculados_quando_criado": faixa.matriculados_quando_criado,
                    }
                )
            periodo["faixas_etarias"] = faixas
            periodo["total_solicitacao"] = sum(
                qtd_solicitacao.values_list("quantidade_alunos", flat=True)
            )
            periodo["total_matriculados"] = sum(
                qtd_solicitacao.values_list("matriculados_quando_criado", flat=True)
            )
            periodos_cei.append(periodo)

    for vinculo in vinculos_emei:
        if vinculo.periodo_escolar.nome in periodos_escolares_emei:
            periodo = {}
            periodo["nome"] = vinculo.periodo_escolar.nome
            tipos_alimentacao = ", ".join(
                vinculo.tipos_alimentacao.exclude(
                    nome__icontains="Lanche Emergencial"
                ).values_list("nome", flat=True)
            )
            if (
                eh_evento_especifico
                and not solicitacao.escola.periodos_escolares().filter(
                    nome=periodo["nome"]
                )
            ):
                vinculo_integral = vinculos_emei.get(periodo_escolar__nome="INTEGRAL")
                tipos_alimentacao = ", ".join(
                    vinculo_integral.tipos_alimentacao.exclude(
                        nome__icontains="Lanche Emergencial"
                    ).values_list("nome", flat=True)
                )
            qtd_solicitacao = (
                solicitacao.quantidade_alunos_emei_da_inclusao_cemei.filter(
                    periodo_escolar__nome=vinculo.periodo_escolar.nome
                )
            )
            if qtd_solicitacao and qtd_solicitacao[0].tipos_alimentacao.all():
                tipos_alimentacao = ", ".join(
                    qtd_solicitacao[0]
                    .tipos_alimentacao.all()
                    .values_list("nome", flat=True)
                )
            periodo["tipos_alimentacao"] = tipos_alimentacao
            periodo["total_solicitacao"] = sum(
                qtd_solicitacao.values_list("quantidade_alunos", flat=True)
            )
            periodo["total_matriculados"] = sum(
                qtd_solicitacao.values_list("matriculados_quando_criado", flat=True)
            )
            periodos_emei.append(periodo)

    motivos = formata_motivos_inclusao(solicitacao.dias_motivos_da_inclusao_cemei.all())
    html_string = render_to_string(
        "solicitacao_inclusao_alimentacao_cemei.html",
        {
            "escola": escola,
            "solicitacao": solicitacao,
            "fluxo": constants.FLUXO_INCLUSAO_ALIMENTACAO,
            "width": get_width(constants.FLUXO_INCLUSAO_ALIMENTACAO, solicitacao.logs),
            "logs": formata_logs(logs),
            "motivos": motivos,
            "periodos_cei": periodos_cei,
            "periodos_escolares_cei": periodos_escolares_cei,
            "periodos_emei": periodos_emei,
            "periodos_escolares_emei": periodos_escolares_emei,
            "eh_evento_especifico": eh_evento_especifico,
        },
    )
    return html_to_pdf_response(
        html_string, f"inclusao_alimentacao_cemei_{solicitacao.id_externo}.pdf"
    )


def relatorio_kit_lanche_passeio(request, solicitacao):
    TEMPO_PASSEIO = {"0": "até 4 horas", "1": "de 5 a 7 horas", "2": "8 horas ou mais"}
    escola = solicitacao.rastro_escola
    logs = solicitacao.logs
    tempo_passeio_num = str(solicitacao.solicitacao_kit_lanche.tempo_passeio)
    tempo_passeio = TEMPO_PASSEIO.get(tempo_passeio_num)
    html_string = render_to_string(
        "solicitacao_kit_lanche_passeio.html",
        {
            "tempo_passeio": tempo_passeio,
            "escola": escola,
            "solicitacao": solicitacao,
            "quantidade_kits": solicitacao.solicitacao_kit_lanche.kits.all().count()
            * solicitacao.quantidade_alunos,
            "fluxo": constants.FLUXO_KIT_LANCHE_PASSEIO,
            "width": get_width(constants.FLUXO_KIT_LANCHE_PASSEIO, solicitacao.logs),
            "logs": formata_logs(logs),
        },
    )
    return html_to_pdf_response(
        html_string, f"solicitacao_avulsa_{solicitacao.id_externo}.pdf"
    )


def relatorio_kit_lanche_passeio_cei(request, solicitacao):
    escola = solicitacao.rastro_escola
    logs = solicitacao.logs
    html_string = render_to_string(
        "solicitacao_kit_lanche_passeio_cei.html",
        {
            "escola": escola,
            "solicitacao": solicitacao,
            "quantidade_kits": solicitacao.solicitacao_kit_lanche.kits.all().count()
            * solicitacao.quantidade_alunos,
            "fluxo": constants.FLUXO_PARTINDO_ESCOLA,
            "width": get_width(constants.FLUXO_PARTINDO_ESCOLA, solicitacao.logs),
            "logs": formata_logs(logs),
        },
    )
    return html_to_pdf_response(
        html_string, f"solicitacao_avulsa_{solicitacao.id_externo}.pdf"
    )


def relatorio_kit_lanche_passeio_cemei(request, solicitacao):
    TEMPO_PASSEIO = {0: "até 4 horas", 1: "de 5 a 7 horas", 2: "8 horas ou mais"}
    escola = solicitacao.rastro_escola
    logs = solicitacao.logs
    tempo_passeio_cei = None
    tempo_passeio_emei = None
    if solicitacao.tem_solicitacao_cei:
        tempo_passeio_cei = TEMPO_PASSEIO.get(solicitacao.solicitacao_cei.tempo_passeio)
    if solicitacao.tem_solicitacao_emei:
        tempo_passeio_emei = TEMPO_PASSEIO.get(
            solicitacao.solicitacao_emei.tempo_passeio
        )
    html_string = render_to_string(
        "solicitacao_kit_lanche_cemei.html",
        {
            "tempo_passeio_cei": tempo_passeio_cei,
            "tempo_passeio_emei": tempo_passeio_emei,
            "escola": escola,
            "solicitacao": solicitacao,
            "fluxo": constants.FLUXO_KIT_LANCHE_PASSEIO,
            "width": get_width(constants.FLUXO_KIT_LANCHE_PASSEIO, solicitacao.logs),
            "logs": formata_logs(logs),
        },
    )
    return html_to_pdf_response(
        html_string, f"solicitacao_kit_lanche_cemei_{solicitacao.id_externo}.pdf"
    )


def relatorio_inversao_dia_de_cardapio(request, solicitacao):
    escola = solicitacao.rastro_escola
    logs = solicitacao.logs
    data_de = (
        solicitacao.cardapio_de.data
        if solicitacao.cardapio_de
        else solicitacao.data_de_inversao
    )
    data_para = (
        solicitacao.cardapio_para.data
        if solicitacao.cardapio_para
        else solicitacao.data_para_inversao
    )
    html_string = render_to_string(
        "solicitacao_inversao_de_cardapio.html",
        {
            "escola": escola,
            "solicitacao": solicitacao,
            "data_de": data_de,
            "data_para": data_para,
            "fluxo": constants.FLUXO_INVERSAO_DIA_CARDAPIO,
            "width": get_width(constants.FLUXO_INVERSAO_DIA_CARDAPIO, solicitacao.logs),
            "logs": formata_logs(logs),
        },
    )
    return html_to_pdf_response(
        html_string, f"solicitacao_inversao_{solicitacao.id_externo}.pdf"
    )


def relatorio_suspensao_de_alimentacao(request, solicitacao):
    escola = solicitacao.rastro_escola
    logs = solicitacao.logs
    # TODO: GrupoSuspensaoAlimentacaoSerializerViewSet não tem motivo, quem
    # tem é cada suspensão do relacionamento
    suspensoes = solicitacao.suspensoes_alimentacao.all()
    quantidades_por_periodo = solicitacao.quantidades_por_periodo.all()
    existe_cancelamento = suspensoes.filter(cancelado=True).exists()
    html_string = render_to_string(
        "solicitacao_suspensao_de_alimentacao.html",
        {
            "escola": escola,
            "solicitacao": solicitacao,
            "suspensoes": suspensoes,
            "existe_cancelamento": existe_cancelamento,
            "quantidades_por_periodo": quantidades_por_periodo,
            "fluxo": constants.FLUXO_SUSPENSAO_ALIMENTACAO,
            "width": get_width(constants.FLUXO_SUSPENSAO_ALIMENTACAO, solicitacao.logs),
            "logs": formata_logs(logs),
        },
    )
    return html_to_pdf_response(
        html_string, f"solicitacao_suspensao_{solicitacao.id_externo}.pdf"
    )


def relatorio_suspensao_de_alimentacao_cei(request, solicitacao):
    escola = solicitacao.rastro_escola
    logs = solicitacao.logs
    periodos_escolares = solicitacao.periodos_escolares.all()
    html_string = render_to_string(
        "solicitacao_suspensao_de_alimentacao_cei.html",
        {
            "escola": escola,
            "solicitacao": solicitacao,
            "periodos_escolares": periodos_escolares,
            "fluxo": constants.FLUXO_SUSPENSAO_ALIMENTACAO,
            "width": get_width(constants.FLUXO_SUSPENSAO_ALIMENTACAO, solicitacao.logs),
            "logs": formata_logs(logs),
        },
    )
    return html_to_pdf_response(
        html_string, f"solicitacao_suspensao_cei_{solicitacao.id_externo}.pdf"
    )


def relatorio_produto_homologacao(request, produto):
    homologacao = produto.homologacao
    terceirizada = homologacao.rastro_terceirizada
    reclamacao = homologacao.reclamacoes.filter(
        status=ReclamacaoProdutoWorkflow.CODAE_ACEITOU
    ).first()
    logs = homologacao.logs
    lotes = terceirizada.lotes.all()
    justificativa_analise_sensorial = get_ultima_justificativa_analise_sensorial(
        produto
    )
    html_string = render_to_string(
        "homologacao_produto.html",
        {
            "terceirizada": terceirizada,
            "reclamacao": reclamacao,
            "homologacao": homologacao,
            "fluxo": constants.FLUXO_HOMOLOGACAO_PRODUTO,
            "width": get_width(constants.FLUXO_HOMOLOGACAO_PRODUTO, logs),
            "produto": produto,
            "diretorias_regionais": get_diretorias_regionais(lotes),
            "logs": formata_logs(logs),
            "justificativa_analise_sensorial": justificativa_analise_sensorial,
        },
    )
    return html_to_pdf_response(
        html_string, f"produto_homologacao_{produto.id_externo}.pdf"
    )


def relatorio_marcas_por_produto_homologacao(produtos, dados, filtros):
    html_string = render_to_string(
        "homologacao_marcas_por_produto.html",
        {
            "produtos": produtos,
            "hoje": datetime.date.today(),
            "dados": dados,
            "filtros": filtros,
        },
    )
    return html_to_pdf_file(
        html_string, "relatorio_marcas_por_produto_homologacao.pdf", True
    )


def produtos_suspensos_por_edital(produtos, data_final, nome_edital, filtros):
    html_string = render_to_string(
        "produtos_suspensos_por_edital.html",
        {
            "produtos": produtos,
            "total": len(produtos),
            "hoje": datetime.date.today().strftime("%d/%m/%Y"),
            "data_final": (
                data_final if data_final else datetime.date.today().strftime("%d/%m/%Y")
            ),
            "nome_edital": nome_edital,
            "filtros": filtros,
        },
    )
    return html_to_pdf_file(
        html_string, "relatorio_produto_suspenso_no_edital.pdf", True
    )


def relatorio_produtos_suspensos(produtos, filtros):
    if (
        filtros["cabecario_tipo"] == "CABECARIO_POR_DATA"
        and "data_suspensao_inicial" not in filtros
    ):
        data_suspensao_inicial = datetime.datetime.today()
        for produto in produtos:
            ultimo_log = produto.ultima_homologacao.ultimo_log
            if ultimo_log.criado_em < data_suspensao_inicial:
                data_suspensao_inicial = ultimo_log.criado_em
        filtros["data_suspensao_inicial"] = data_suspensao_inicial.strftime("%d/%m/%Y")

    html_string = render_to_string(
        "relatorio_suspensoes_produto.html", {"produtos": produtos, "config": filtros}
    )
    return html_to_pdf_response(html_string, "relatorio_suspensoes_produto.pdf")


def relatorio_produtos_em_analise_sensorial(produtos, filtros):
    data_incial_analise_padrao = produtos[0]["ultima_homologacao"][
        "log_solicitacao_analise"
    ]["criado_em"]
    contatos_terceirizada = produtos[0]["ultima_homologacao"]["rastro_terceirizada"][
        "contatos"
    ]
    config = get_config_cabecario_relatorio_analise(
        filtros, data_incial_analise_padrao, contatos_terceirizada
    )
    html_string = render_to_string(
        "relatorio_produto_em_analise_sensorial.html",
        {"produtos": produtos, "config": config},
    )
    return html_to_pdf_response(
        html_string, "relatorio_produtos_em_analise_sensorial.pdf"
    )


def relatorio_reclamacao(produtos, filtros):
    if (
        filtros["cabecario_tipo"] == "CABECARIO_POR_DATA"
        and "data_inicial_reclamacao" not in filtros
    ):
        data_inicial_reclamacao = datetime.datetime.today()
        for produto in produtos:
            reclamacao = produto.ultima_homologacao.reclamacoes.first()
            if reclamacao.criado_em < data_inicial_reclamacao:
                data_inicial_reclamacao = reclamacao.criado_em
        filtros["data_inicial_reclamacao"] = data_inicial_reclamacao.strftime(
            "%d/%m/%Y"
        )
    html_string = render_to_string(
        "relatorio_reclamacao.html", {"produtos": produtos, "config": filtros}
    )
    return html_to_pdf_response(html_string, "relatorio_reclamacao.pdf")


def relatorio_quantitativo_por_terceirizada(request, filtros, dados_relatorio):
    dados_relatorio_transformados = transforma_dados_relatorio_quantitativo(
        dados_relatorio
    )
    html_string = render_to_string(
        "relatorio_quantitativo_por_terceirizada.html",
        {
            "filtros": filtros,
            "dados_relatorio": dados_relatorio_transformados,
            "qtde_filtros": conta_filtros(filtros),
        },
    )
    return html_to_pdf_response(
        html_string, "relatorio_quantitativo_por_terceirizada.pdf"
    )


def relatorio_produto_analise_sensorial(request, produto):
    homologacao = produto.homologacao
    terceirizada = homologacao.rastro_terceirizada
    logs = homologacao.logs
    lotes = terceirizada.lotes.all()
    html_string = render_to_string(
        "homologacao_analise_sensorial.html",
        {
            "terceirizada": terceirizada,
            "homologacao": homologacao,
            "fluxo": constants.FLUXO_HOMOLOGACAO_PRODUTO,
            "width": get_width(constants.FLUXO_HOMOLOGACAO_PRODUTO, logs),
            "produto": produto,
            "diretorias_regionais": get_diretorias_regionais(lotes),
            "logs": formata_logs(logs),
            "ultimo_log": homologacao.logs.last(),
        },
    )
    return html_to_pdf_response(
        html_string, f"produto_homologacao_relatorio_{produto.id_externo}.pdf"
    )


def relatorio_produtos_agrupado_terceirizada(
    tipo_usuario, dados_agrupados, dados, filtros
):
    html_string = render_to_string(
        "relatorio_produtos_por_terceirizada.html",
        {
            "dados_agrupados": dados_agrupados,
            "dados": dados,
            "filtros": filtros,
            "qtde_filtros": conta_filtros(filtros),
            "exibe_coluna_terceirizada": tipo_usuario not in ["escola", "terceirizada"],
        },
    )
    return html_to_pdf_file(
        html_string, "produtos_homologados_por_terceirizada.pdf", True
    )


def relatorio_produto_analise_sensorial_recebimento(request, produto):
    homologacao = produto.homologacao
    terceirizada = homologacao.rastro_terceirizada
    logs = homologacao.logs
    lotes = terceirizada.lotes.all()
    html_string = render_to_string(
        "homologacao_analise_sensorial_recebimento.html",
        {
            "terceirizada": terceirizada,
            "homologacao": homologacao,
            "fluxo": constants.FLUXO_HOMOLOGACAO_PRODUTO,
            "width": get_width(constants.FLUXO_HOMOLOGACAO_PRODUTO, logs),
            "produto": produto,
            "diretorias_regionais": get_diretorias_regionais(lotes),
            "logs": formata_logs(logs),
            "ultimo_log": homologacao.logs.last(),
        },
    )
    return html_to_pdf_response(
        html_string, f"produto_homologacao_{produto.id_externo}.pdf"
    )


def get_relatorio_dieta_especial(campos, form, queryset, user, nome_relatorio):
    status = None
    if "status" in form.cleaned_data:
        status = dict(form.fields["status"].choices).get(
            form.cleaned_data["status"], ""
        )
    html_string = render_to_string(
        f"{nome_relatorio}.html",
        {
            "campos": campos,
            "status": status,
            "filtros": form.cleaned_data,
            "queryset": queryset,
            "user": user,
        },
    )
    return html_to_pdf_response(html_string, f"{nome_relatorio}.pdf")


def relatorio_quantitativo_solic_dieta_especial(campos, form, queryset, user):
    return get_relatorio_dieta_especial(
        campos,
        form,
        queryset,
        user,
        "relatorio_quantitativo_solicitacoes_dieta_especial",
    )


def relatorio_quantitativo_classificacao_dieta_especial(campos, form, queryset, user):
    return get_relatorio_dieta_especial(
        campos,
        form,
        queryset,
        user,
        "relatorio_quantitativo_classificacao_dieta_especial",
    )


def relatorio_quantitativo_diag_dieta_especial(campos, form, queryset, user):
    return get_relatorio_dieta_especial(
        campos,
        form,
        queryset,
        user,
        "relatorio_quantitativo_diagnostico_dieta_especial",
    )


def relatorio_quantitativo_diag_dieta_especial_somente_dietas_ativas(
    campos, form, queryset, user
):
    return get_relatorio_dieta_especial(
        campos,
        form,
        queryset,
        user,
        "relatorio_quantitativo_diagnostico_dieta_especial_somente_dietas_ativas",
    )


def relatorio_geral_dieta_especial(form, queryset, user):
    return get_relatorio_dieta_especial(
        None, form, queryset, user, "relatorio_dieta_especial"
    )


def relatorio_geral_dieta_especial_pdf(form, queryset, user):
    status = None
    if "status" in form.cleaned_data:
        status = dict(form.fields["status"].choices).get(
            form.cleaned_data["status"], ""
        )
    html_string = render_to_string(
        "relatorio_dieta_especial.html",
        {
            "status": status,
            "filtros": form.cleaned_data,
            "queryset": queryset,
            "user": user,
        },
    )
    return html_to_pdf_file(html_string, "relatorio_dieta_especial.pdf", is_async=True)


def get_total_por_periodo(tabelas, campo):
    dict_periodos_total_campo = {}
    for tabela in tabelas:
        periodos = tabela["periodos"]
        nomes_campos = tabela["nomes_campos"]

        if campo in nomes_campos:
            indices_campos = get_indices_campo(nomes_campos, campo)

            for indice_campo in indices_campos:
                periodo = get_periodo(periodos, indice_campo, tabela["len_periodos"])

                posicao_periodo = periodos.index(periodo)
                if posicao_periodo > 0:
                    indice_campo = (
                        sum(tabela["len_periodos"][:posicao_periodo]) + indice_campo
                    )

                dict_periodos_total_campo[periodo] = tabela["valores_campos"][-1][
                    indice_campo + 1
                ]
    return dict_periodos_total_campo


def get_indices_campo(nomes_campos, campo):
    return [i for i, nome_campo in enumerate(nomes_campos) if nome_campo == campo]


def get_periodo(periodos, indice_campo, len_periodos):
    if len(periodos) > 1:
        for idx, _ in enumerate(len_periodos):
            if indice_campo < sum([v for v in len_periodos[: (idx + 1)]]):
                return periodos[idx]
    return periodos[0]


def relatorio_solicitacao_medicao_por_escola(solicitacao):
    tabelas = build_tabelas_relatorio_medicao(solicitacao)
    dict_total_refeicoes = get_total_por_periodo(tabelas, "total_refeicoes_pagamento")
    dict_total_sobremesas = get_total_por_periodo(tabelas, "total_sobremesas_pagamento")
    tipos_contagem_alimentacao = solicitacao.tipos_contagem_alimentacao.values_list(
        "nome", flat=True
    )
    tipos_contagem_alimentacao = ", ".join(list(set(tipos_contagem_alimentacao)))
    tabela_observacoes = build_lista_campos_observacoes(solicitacao)

    primeira_tabela_somatorio, segunda_tabela_somatorio = build_tabela_somatorio_body(
        solicitacao, dict_total_refeicoes, dict_total_sobremesas
    )

    (
        primeira_tabela_somatorio_dietas_tipo_a,
        segunda_tabela_somatorio_dietas_tipo_a,
    ) = build_tabela_somatorio_dietas_body(solicitacao, "TIPO A")

    (
        primeira_tabela_somatorio_dietas_tipo_b,
        segunda_tabela_somatorio_dietas_tipo_b,
    ) = build_tabela_somatorio_dietas_body(solicitacao, "TIPO B")

    html_string = render_to_string(
        "relatorio_solicitacao_medicao_por_escola.html",
        {
            "solicitacao": solicitacao,
            "tipos_contagem_alimentacao": tipos_contagem_alimentacao,
            "responsaveis": solicitacao.responsaveis.all(),
            "assinatura_escola": solicitacao.assinatura_ue,
            "assinatura_dre": solicitacao.assinatura_dre,
            "quantidade_dias_mes": range(
                1, monthrange(int(solicitacao.ano), int(solicitacao.mes))[1] + 1
            ),
            "tabelas": tabelas,
            "tabela_observacoes": tabela_observacoes,
            "primeira_tabela_somatorio": primeira_tabela_somatorio,
            "segunda_tabela_somatorio": segunda_tabela_somatorio,
            "primeira_tabela_somatorio_dietas_tipo_a": primeira_tabela_somatorio_dietas_tipo_a,
            "segunda_tabela_somatorio_dietas_tipo_a": segunda_tabela_somatorio_dietas_tipo_a,
            "primeira_tabela_somatorio_dietas_tipo_b": primeira_tabela_somatorio_dietas_tipo_b,
            "segunda_tabela_somatorio_dietas_tipo_b": segunda_tabela_somatorio_dietas_tipo_b,
        },
    )

    return html_to_pdf_file(html_string, "relatorio_dieta_especial.pdf", is_async=True)


def relatorio_solicitacao_medicao_por_escola_cei(solicitacao):
    tabelas, dias_letivos = build_tabelas_relatorio_medicao_cei(solicitacao)
    tabelas_somatorios = build_tabela_somatorio_body_cei(solicitacao)
    tipos_contagem_alimentacao = solicitacao.tipos_contagem_alimentacao.values_list(
        "nome", flat=True
    )
    tipos_contagem_alimentacao = ", ".join(list(set(tipos_contagem_alimentacao)))
    tabela_observacoes = build_lista_campos_observacoes(solicitacao)
    html_string = render_to_string(
        "relatorio_solicitacao_medicao_por_escola_cei.html",
        {
            "solicitacao": solicitacao,
            "tipos_contagem_alimentacao": tipos_contagem_alimentacao,
            "responsaveis": solicitacao.responsaveis.all(),
            "assinatura_escola": solicitacao.assinatura_ue,
            "assinatura_dre": solicitacao.assinatura_dre,
            "quantidade_dias_mes": range(
                1, monthrange(int(solicitacao.ano), int(solicitacao.mes))[1] + 1
            ),
            "tabelas": tabelas,
            "dias_letivos": dias_letivos,
            "tabela_observacoes": tabela_observacoes,
            "tabelas_somatorios": tabelas_somatorios,
        },
    )
    return html_to_pdf_file(html_string, "relatorio_dieta_especial.pdf", is_async=True)


def relatorio_solicitacao_medicao_por_escola_cemei(solicitacao):
    tabelas = build_tabelas_relatorio_medicao_cemei(solicitacao)
    dict_total_refeicoes = get_total_por_periodo(tabelas, "total_refeicoes_pagamento")
    dict_total_sobremesas = get_total_por_periodo(tabelas, "total_sobremesas_pagamento")
    tipos_contagem_alimentacao = solicitacao.tipos_contagem_alimentacao.values_list(
        "nome", flat=True
    )
    tipos_contagem_alimentacao = ", ".join(list(set(tipos_contagem_alimentacao)))
    tabelas_somatorios_cei = build_tabela_somatorio_body_cei(solicitacao)
    tabelas_somatorios_infantil = build_tabela_somatorio_body(
        solicitacao, dict_total_refeicoes, dict_total_sobremesas
    )

    observacoes = build_lista_campos_observacoes(solicitacao)

    tabela_observacoes_cei = []
    tabela_observacoes_infantil = []

    for observacao in observacoes:
        if observacao[1] in ["INTEGRAL", "PARCIAL"]:
            tabela_observacoes_cei.append(observacao)
        else:
            tabela_observacoes_infantil.append(observacao)

    html_string = render_to_string(
        "relatorio_solicitacao_medicao_por_escola_cemei.html",
        {
            "solicitacao": solicitacao,
            "tipos_contagem_alimentacao": tipos_contagem_alimentacao,
            "responsaveis": solicitacao.responsaveis.all(),
            "assinatura_escola": solicitacao.assinatura_ue,
            "assinatura_dre": solicitacao.assinatura_dre,
            "tabelas": tabelas,
            "tabela_observacoes_cei": tabela_observacoes_cei,
            "tabela_observacoes_infantil": tabela_observacoes_infantil,
            "tabelas_somatorios_cei": tabelas_somatorios_cei,
            "tabelas_somatorios_infantil": tabelas_somatorios_infantil,
        },
    )

    return html_to_pdf_file(html_string, "relatorio_dieta_especial.pdf", is_async=True)


def relatorio_solicitacao_medicao_por_escola_emebs(solicitacao):
    tabelas = build_tabelas_relatorio_medicao_emebs(solicitacao)

    tipos_contagem_alimentacao = solicitacao.tipos_contagem_alimentacao.values_list(
        "nome", flat=True
    )
    tipos_contagem_alimentacao = ", ".join(list(set(tipos_contagem_alimentacao)))

    tabela_observacoes_infantil = build_lista_campos_observacoes(
        solicitacao, ValorMedicao.INFANTIL
    )

    tabela_observacoes_fundamental = build_lista_campos_observacoes(
        solicitacao, ValorMedicao.FUNDAMENTAL
    )

    dict_total_refeicoes = get_total_por_periodo(tabelas, "total_refeicoes_pagamento")
    dict_total_sobremesas = get_total_por_periodo(tabelas, "total_sobremesas_pagamento")

    (
        primeira_tabela_somatorio_infantil,
        segunda_tabela_somatorio_infantil,
    ) = build_tabela_somatorio_body(
        solicitacao,
        dict_total_refeicoes,
        dict_total_sobremesas,
        ValorMedicao.INFANTIL,
    )

    (
        primeira_tabela_somatorio_dietas_tipo_a_infantil,
        segunda_tabela_somatorio_dietas_tipo_a_infantil,
    ) = build_tabela_somatorio_dietas_body(
        solicitacao,
        "TIPO A",
        ValorMedicao.INFANTIL,
    )

    (
        primeira_tabela_somatorio_dietas_tipo_b_infantil,
        segunda_tabela_somatorio_dietas_tipo_b_infantil,
    ) = build_tabela_somatorio_dietas_body(
        solicitacao,
        "TIPO B",
        ValorMedicao.INFANTIL,
    )

    (
        primeira_tabela_somatorio_fundamental,
        segunda_tabela_somatorio_fundamental,
    ) = build_tabela_somatorio_body(
        solicitacao,
        dict_total_refeicoes,
        dict_total_sobremesas,
        ValorMedicao.FUNDAMENTAL,
    )

    (
        primeira_tabela_somatorio_dietas_tipo_a_fundamental,
        segunda_tabela_somatorio_dietas_tipo_a_fundamental,
    ) = build_tabela_somatorio_dietas_body(
        solicitacao,
        "TIPO A",
        ValorMedicao.FUNDAMENTAL,
    )

    (
        primeira_tabela_somatorio_dietas_tipo_b_fundamental,
        segunda_tabela_somatorio_dietas_tipo_b_fundamental,
    ) = build_tabela_somatorio_dietas_body(
        solicitacao,
        "TIPO B",
        ValorMedicao.FUNDAMENTAL,
    )

    html_string = render_to_string(
        "relatorio_solicitacao_medicao_por_escola_emebs.html",
        {
            "solicitacao": solicitacao,
            "tipos_contagem_alimentacao": tipos_contagem_alimentacao,
            "responsaveis": solicitacao.responsaveis.all(),
            "assinatura_escola": solicitacao.assinatura_ue,
            "assinatura_dre": solicitacao.assinatura_dre,
            "quantidade_dias_mes": range(
                1, monthrange(int(solicitacao.ano), int(solicitacao.mes))[1] + 1
            ),
            "tabelas": tabelas,
            "tabela_observacoes_infantil": tabela_observacoes_infantil,
            "tabela_observacoes_fundamental": tabela_observacoes_fundamental,
            "primeira_tabela_somatorio_infantil": primeira_tabela_somatorio_infantil,
            "segunda_tabela_somatorio_infantil": segunda_tabela_somatorio_infantil,
            "primeira_tabela_somatorio_dietas_tipo_a_infantil": primeira_tabela_somatorio_dietas_tipo_a_infantil,
            "segunda_tabela_somatorio_dietas_tipo_a_infantil": segunda_tabela_somatorio_dietas_tipo_a_infantil,
            "primeira_tabela_somatorio_dietas_tipo_b_infantil": primeira_tabela_somatorio_dietas_tipo_b_infantil,
            "segunda_tabela_somatorio_dietas_tipo_b_infantil": segunda_tabela_somatorio_dietas_tipo_b_infantil,
            "primeira_tabela_somatorio_fundamental": primeira_tabela_somatorio_fundamental,
            "segunda_tabela_somatorio_fundamental": segunda_tabela_somatorio_fundamental,
            "primeira_tabela_somatorio_dietas_tipo_a_fundamental": primeira_tabela_somatorio_dietas_tipo_a_fundamental,
            "segunda_tabela_somatorio_dietas_tipo_a_fundamental": segunda_tabela_somatorio_dietas_tipo_a_fundamental,
            "primeira_tabela_somatorio_dietas_tipo_b_fundamental": primeira_tabela_somatorio_dietas_tipo_b_fundamental,
            "segunda_tabela_somatorio_dietas_tipo_b_fundamental": segunda_tabela_somatorio_dietas_tipo_b_fundamental,
        },
    )
    return html_to_pdf_file(html_string, "relatorio_dieta_especial.pdf", is_async=True)


def relatorio_consolidado_medicoes_iniciais_emef(
    ids_solicitacoes, solicitacao, tipos_de_unidade
):
    primeira_tabela, segunda_tabela = build_tabela_relatorio_consolidado(
        ids_solicitacoes
    )

    html_string = render_to_string(
        "relatorio_consolidado_medicao_inicial.html",
        {
            "solicitacao": solicitacao,
            "primeira_tabela": primeira_tabela,
            "segunda_tabela": segunda_tabela,
            "assinatura": solicitacao.assinatura_dre,
            "grupo_unidade_escolar": tipos_de_unidade,
            "data_atual": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        },
    )

    return html_to_pdf_file(
        html_string, "pagina_inicial_relatorio_consolidado.pdf", is_async=True
    )


def get_pdf_guia_distribuidor(data=None, many=False):
    pages = []
    inicio = 0
    num_alimentos_pagina = 4
    for guia in data:
        todos_alimentos = guia.alimentos.all().annotate(
            peso_total=Sum(
                F("embalagens__capacidade_embalagem") * F("embalagens__qtd_volume"),
                output_field=FloatField(),
            )
        )
        while True:
            alimentos = todos_alimentos[inicio : inicio + num_alimentos_pagina]
            if alimentos:
                page = guia.as_dict()
                peso_total_pagina = round(
                    sum(alimento.peso_total for alimento in alimentos), 2
                )
                page["alimentos"] = alimentos
                page["peso_total"] = peso_total_pagina
                pages.append(page)
                inicio = inicio + num_alimentos_pagina
            else:
                break
        inicio = 0
    html_string = render_to_string(
        "logistica/guia_distribuidor/guia_distribuidor_v2.html", {"pages": pages}
    )
    data_arquivo = datetime.date.today().strftime("%d/%m/%Y")

    return html_to_pdf_response(
        html_string.replace("dt_file", data_arquivo), "guia_de_remessa.pdf"
    )


def get_pdf_cronograma(request, cronograma):
    logs = cronograma.logs
    html_string = render_to_string(
        "pre_recebimento/cronogramas/cronograma.html",
        {
            "empresa": cronograma.empresa,
            "contrato": cronograma.contrato,
            "cronograma": cronograma,
            "etapas": cronograma.etapas.all(),
            "programacoes": cronograma.programacoes_de_recebimento.all(),
            "logs": logs,
        },
    )
    data_arquivo = datetime.datetime.today().strftime("%d/%m/%Y às %H:%M")
    return html_to_pdf_response(
        html_string.replace("dt_file", data_arquivo),
        f"cronogram_{cronograma.numero}.pdf",
    )


def get_pdf_ficha_tecnica(request, ficha):
    informacoes_nutricionais = InformacoesNutricionaisFichaTecnica.objects.filter(
        ficha_tecnica=ficha
    )
    fabricante = ficha.fabricante
    cnpj_fabricante = formata_cnpj_ficha_tecnica(fabricante.cnpj)
    telefone_fabricante = formata_telefone_ficha_tecnica(fabricante.telefone)
    envasador_distribuidor = ficha.envasador_distribuidor
    cnpj_distribuidor = formata_cnpj_ficha_tecnica(envasador_distribuidor.cnpj)
    telefone_distribuidor = formata_telefone_ficha_tecnica(
        envasador_distribuidor.telefone
    )

    html_string = render_to_string(
        "pre_recebimento/ficha_tecnica/ficha_tecnica.html",
        {
            "ficha": ficha,
            "empresa": ficha.empresa,
            "status_ficha": retorna_status_ficha_tecnica(ficha.status),
            "tabela": list(informacoes_nutricionais),
            "logs": ficha.logs,
            "fabricante": fabricante,
            "cnpj_fabricante": cnpj_fabricante,
            "telefone_fabricante": telefone_fabricante,
            "envasador_distribuidor": envasador_distribuidor,
            "cnpj_distribuidor": cnpj_distribuidor,
            "telefone_distribuidor": telefone_distribuidor,
        },
    )
    data_arquivo = datetime.datetime.today().strftime("%d/%m/%Y às %H:%M")
    return html_to_pdf_response(
        html_string.replace("dt_file", data_arquivo),
        f"ficha_tecnica_{ficha.numero}.pdf",
    )


def relatorio_formulario_supervisao(formulario_supervisao):
    from ..imr.api.viewsets import FormularioSupervisaoModelViewSet

    edital = Edital.objects.get(uuid=formulario_supervisao.escola.editais[0])

    formulario_modelviewset = FormularioSupervisaoModelViewSet()
    tipo_unidade = formulario_supervisao.escola.tipo_unidade.iniciais

    tipos_ocorrencia = TipoOcorrencia.para_nutrisupervisores.filter(
        edital=edital
    ).exclude(
        categoria__nome__in=formulario_modelviewset._get_categorias_nao_permitidas(
            tipo_unidade
        )
    )

    html_string = render_to_string(
        "imr/relatorio_formulario_supervisao/index.html",
        {
            "formulario_supervisao": formulario_supervisao,
            "edital": edital.numero,
            "tipos_ocorrencia": tipos_ocorrencia,
            "log_envio_formulario": formulario_supervisao.logs.get(
                status_evento=LogSolicitacoesUsuario.RELATORIO_ENVIADO_PARA_CODAE
            ),
        },
    )
    data_arquivo = datetime.datetime.today().strftime("%d/%m/%Y às %H:%M")
    return html_to_pdf_file(
        html_string.replace("dt_file", data_arquivo),
        "relatorio_formulario_supervisao.pdf",
        is_async=True,
    )


def exportar_relatorio_notificacao(data, template_name, filename):
    data_arquivo = datetime.datetime.today().strftime("%d/%m/%Y às %H:%M")
    html_template = get_template(template_name)
    rendered_html = html_template.render({"dados": data})
    return html_to_pdf_file(
        rendered_html.replace("dt_file", data_arquivo), filename, is_async=True
    )


def formata_justificativa(solicitacao, status_evento_explicacao):
    justificativa = None
    status_solicitacao = solicitacao.status.state.name
    if status_solicitacao == DietaEspecialWorkflow.TERMINADA_AUTOMATICAMENTE_SISTEMA:
        justificativa = "Cancelamento automático por atingir data de término."
    elif status_solicitacao == DietaEspecialWorkflow.CANCELADO_ALUNO_NAO_PERTENCE_REDE:
        justificativa = (
            "Cancelamento automático para aluno não matriculado na rede municipal."
        )
    elif status_solicitacao == DietaEspecialWorkflow.CANCELADO_ALUNO_MUDOU_ESCOLA:
        justificativa = (
            "Cancelamento automático para aluno não matriculado na Unidade Educacional."
        )
    else:
        justificativa = status_evento_explicacao

    return justificativa


def obter_justificativa_dieta(solicitacao):
    status_dieta = solicitacao.status.state.name
    ativo = solicitacao.ativo
    log_recente = solicitacao.logs.last()
    data = log_recente.criado_em.strftime("%d/%m/%Y") if log_recente else ""
    status_cancelamentos = [
        DietaEspecialWorkflow.CANCELADO_ALUNO_MUDOU_ESCOLA,
        DietaEspecialWorkflow.CANCELADO_ALUNO_NAO_PERTENCE_REDE,
        DietaEspecialWorkflow.TERMINADA_AUTOMATICAMENTE_SISTEMA,
    ]
    cancelamento_padrao = status_dieta in status_cancelamentos and ativo
    cancelado_pela_escola = (
        status_dieta == DietaEspecialWorkflow.ESCOLA_CANCELOU and not ativo
    )

    justificativa = None
    if status_dieta in MoldeConsolidado.INATIVOS_STATUS_DIETA_ESPECIAL and not ativo:
        mensagem = "Autorização de novo protocolo de dieta especial"
        justificativa = f"Dieta Inativada em: {data} | Justificativa: {mensagem}"

    elif cancelamento_padrao or cancelado_pela_escola:
        mensagem = formata_justificativa(
            solicitacao, log_recente.status_evento_explicacao
        )
        justificativa = f"Dieta cancelada em: {data} | Justificativa: {mensagem}"

    return justificativa
