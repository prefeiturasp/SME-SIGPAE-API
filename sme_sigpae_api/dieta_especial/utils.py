import re
from collections import Counter
from datetime import date, datetime
from typing import List

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Sum
from django.template.loader import render_to_string
from rest_framework.pagination import PageNumberPagination

from sme_sigpae_api.dieta_especial.models import (
    ClassificacaoDieta,
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
)
from sme_sigpae_api.escola.models import Lote
from sme_sigpae_api.medicao_inicial.models import SolicitacaoMedicaoInicial
from sme_sigpae_api.perfil.models import Usuario
from sme_sigpae_api.relatorios.relatorios import relatorio_dieta_especial_conteudo
from sme_sigpae_api.relatorios.utils import html_to_pdf_email_anexo

from ..dados_comuns.constants import TIPO_SOLICITACAO_DIETA
from ..dados_comuns.fluxo_status import DietaEspecialWorkflow
from ..dados_comuns.utils import envia_email_unico, envia_email_unico_com_anexo_inmemory
from ..escola.models import Aluno, FaixaEtaria, PeriodoEscolar
from ..paineis_consolidados.models import SolicitacoesCODAE
from .constants import ETAPA_INFANTIL
from .models import LogDietasAtivasCanceladasAutomaticamente, SolicitacaoDietaEspecial


def dietas_especiais_a_terminar():
    return SolicitacaoDietaEspecial.objects.filter(
        data_termino__lt=date.today(),
        ativo=True,
        status__in=[
            DietaEspecialWorkflow.CODAE_AUTORIZADO,
            DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
            DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
        ],
    )


def termina_dietas_especiais(usuario):
    for solicitacao in dietas_especiais_a_terminar():
        if solicitacao.tipo_solicitacao == TIPO_SOLICITACAO_DIETA.get("ALTERACAO_UE"):
            solicitacao.dieta_alterada.ativo = True
            solicitacao.dieta_alterada.save()
        solicitacao.termina(usuario)


def dietas_especiais_a_iniciar():
    return SolicitacaoDietaEspecial.objects.filter(
        data_inicio__lte=date.today(),
        ativo=False,
        status__in=[
            DietaEspecialWorkflow.CODAE_AUTORIZADO,
            DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
            DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
        ],
    )


def inicia_dietas_temporarias(usuario):
    for solicitacao in dietas_especiais_a_iniciar():
        if solicitacao.tipo_solicitacao == TIPO_SOLICITACAO_DIETA.get("ALTERACAO_UE"):
            solicitacao.dieta_alterada.ativo = False
            solicitacao.dieta_alterada.save()
            solicitacao.ativo = True
            solicitacao.save()


def aluno_pertence_a_escola_ou_esta_na_rede(
    cod_escola_no_eol, cod_escola_no_sigpae
) -> bool:
    return cod_escola_no_eol == cod_escola_no_sigpae


def gerar_log_dietas_ativas_canceladas_automaticamente(
    dieta, dados, fora_da_rede=False
):
    data = dict(
        dieta=dieta,
        codigo_eol_aluno=dados["codigo_eol_aluno"],
        nome_aluno=dados["nome_aluno"],
        codigo_eol_escola_destino=dados.get("codigo_eol_escola_origem"),
        nome_escola_destino=dados.get("nome_escola_origem"),
        codigo_eol_escola_origem=dados.get("codigo_eol_escola_destino"),
        nome_escola_origem=dados.get("nome_escola_destino"),
    )
    if fora_da_rede:
        data["codigo_eol_escola_origem"] = dados.get("codigo_eol_escola_origem")
        data["nome_escola_origem"] = dados.get("nome_escola_origem")
        data["codigo_eol_escola_destino"] = ""
        data["nome_escola_destino"] = ""
    LogDietasAtivasCanceladasAutomaticamente.objects.create(**data)


def _cancelar_dieta(dieta):
    usuario_admin = Usuario.objects.get(pk=1)
    dieta.cancelar_aluno_mudou_escola(user=usuario_admin)
    dieta.ativo = False
    dieta.save()


def _cancelar_dieta_aluno_fora_da_rede(dieta):
    usuario_admin = Usuario.objects.get(pk=1)
    dieta.cancelar_aluno_nao_pertence_rede(user=usuario_admin)
    dieta.ativo = False
    dieta.save()


def enviar_email_para_diretor_da_escola_origem(
    solicitacao_dieta, aluno, escola
):  # noqa C901
    assunto = (
        f"Cancelamento Automático de Dieta Especial Nº {solicitacao_dieta.id_externo}"
    )
    hoje = date.today().strftime("%d/%m/%Y")
    template = ("email/email_dieta_cancelada_automaticamente_escola_origem.html",)
    dados_template = {
        "nome_aluno": aluno.nome,
        "codigo_eol_aluno": aluno.codigo_eol,
        "dieta_numero": solicitacao_dieta.id_externo,
        "nome_escola": escola.nome,
        "hoje": hoje,
    }
    html = render_to_string(template, dados_template)
    terceirizada = escola.lote.terceirizada
    if terceirizada:
        emails = [contato.email for contato in terceirizada.contatos.all()]
        emails.append(escola.contato.email)
    else:
        emails = [escola.contato.email]

    for email in emails:
        envia_email_unico(
            assunto=assunto,
            corpo="",
            email=email,
            template=template,
            dados_template=dados_template,
            html=html,
        )


def enviar_email_para_escola_origem_eol(solicitacao_dieta, aluno, escola):
    assunto = "Alerta para Criar uma Nova Dieta Especial"

    email_escola_origem_eol = escola.escola_destino.contato.email

    html_string = relatorio_dieta_especial_conteudo(solicitacao_dieta)
    anexo = html_to_pdf_email_anexo(html_string)
    anexo_nome = f"dieta_especial_{aluno.codigo_eol}.pdf"
    html_to_pdf_email_anexo(html_string)

    corpo = render_to_string(
        template_name="email/email_dieta_cancelada_automaticamente_escola_destino.html",
        context={
            "nome_aluno": aluno.nome,
            "codigo_eol_aluno": aluno.codigo_eol,
            "nome_escola": escola.nome,
        },
    )

    envia_email_unico_com_anexo_inmemory(
        assunto=assunto,
        corpo=corpo,
        email=email_escola_origem_eol,
        anexo_nome=anexo_nome,
        mimetypes="application/pdf",
        anexo=anexo,
    )


def enviar_email_para_escola_destino_eol(solicitacao_dieta, aluno, escola):
    assunto = "Alerta para Criar uma Nova Dieta Especial"

    email_escola_destino_eol = escola.escola_destino.contato.email

    html_string = relatorio_dieta_especial_conteudo(solicitacao_dieta)
    anexo = html_to_pdf_email_anexo(html_string)
    anexo_nome = f"dieta_especial_{aluno.codigo_eol}.pdf"
    html_to_pdf_email_anexo(html_string)

    corpo = render_to_string(
        template_name="email/email_dieta_cancelada_automaticamente_escola_destino.html",
        context={
            "nome_aluno": aluno.nome,
            "codigo_eol_aluno": aluno.codigo_eol,
            "nome_escola": escola.nome,
        },
    )

    envia_email_unico_com_anexo_inmemory(
        assunto=assunto,
        corpo=corpo,
        email=email_escola_destino_eol,
        anexo_nome=anexo_nome,
        mimetypes="application/pdf",
        anexo=anexo,
    )


def enviar_email_para_diretor_da_escola_destino(solicitacao_dieta, aluno, escola):
    assunto = "Alerta para Criar uma Nova Dieta Especial"
    email = escola.contato.email
    html_string = relatorio_dieta_especial_conteudo(solicitacao_dieta)
    anexo = html_to_pdf_email_anexo(html_string)
    anexo_nome = f"dieta_especial_{aluno.codigo_eol}.pdf"
    html_to_pdf_email_anexo(html_string)

    corpo = render_to_string(
        template_name="email/email_dieta_cancelada_automaticamente_escola_destino.html",
        context={
            "nome_aluno": aluno.nome,
            "codigo_eol_aluno": aluno.codigo_eol,
            "nome_escola": escola.nome,
        },
    )

    envia_email_unico_com_anexo_inmemory(
        assunto=assunto,
        corpo=corpo,
        email=email,
        anexo_nome=anexo_nome,
        mimetypes="application/pdf",
        anexo=anexo,
    )


def enviar_email_para_adm_terceirizada_e_escola(
    solicitacao_dieta, aluno, escola, fora_da_rede=False
):
    assunto = (
        f"Cancelamento Automático de Dieta Especial Nº {solicitacao_dieta.id_externo}"
    )
    hoje = date.today().strftime("%d/%m/%Y")
    template = (
        "email/email_dieta_cancelada_automaticamente_terceirizada_escola_destino.html"
    )
    justificativa_cancelamento = "por não pertencer a unidade educacional"
    if fora_da_rede:
        justificativa_cancelamento = "por não estar matriculado"
    dados_template = {
        "nome_aluno": aluno.nome,
        "codigo_eol_aluno": aluno.codigo_eol,
        "dieta_numero": solicitacao_dieta.id_externo,
        "nome_escola": escola.nome,
        "hoje": hoje,
        "justificativa_cancelamento": justificativa_cancelamento,
    }
    html = render_to_string(template, dados_template)
    emails_terceirizada = solicitacao_dieta.rastro_terceirizada.emails_por_modulo(
        "Dieta Especial"
    )
    email_escola = [escola.contato.email]
    email_lista = emails_terceirizada + email_escola
    for email in email_lista:
        envia_email_unico(
            assunto=assunto,
            corpo="",
            email=email,
            template=template,
            dados_template=dados_template,
            html=html,
        )


def aluno_matriculado_em_outra_ue(aluno, solicitacao_dieta):
    if aluno.escola:
        return aluno.escola.codigo_eol != solicitacao_dieta.escola.codigo_eol
    return False


def cancela_dietas_ativas_automaticamente():  # noqa C901 D205 D400
    dietas_ativas_comuns = (
        SolicitacoesCODAE.get_autorizados_dieta_especial()
        .filter(tipo_solicitacao_dieta="COMUM")
        .order_by("pk")
        .distinct("pk")
    )
    for dieta in dietas_ativas_comuns:
        aluno = Aluno.objects.filter(codigo_eol=dieta.codigo_eol_aluno).first()
        solicitacao_dieta = SolicitacaoDietaEspecial.objects.filter(pk=dieta.pk).first()
        if aluno.nao_matriculado:
            dados = dict(
                codigo_eol_aluno=aluno.codigo_eol,
                nome_aluno=aluno.nome,
                codigo_eol_escola_origem=solicitacao_dieta.escola.codigo_eol,
                nome_escola_origem=solicitacao_dieta.escola.nome,
            )
            gerar_log_dietas_ativas_canceladas_automaticamente(
                solicitacao_dieta, dados, fora_da_rede=True
            )
            _cancelar_dieta_aluno_fora_da_rede(dieta=solicitacao_dieta)
            enviar_email_para_adm_terceirizada_e_escola(
                solicitacao_dieta,
                aluno,
                escola=solicitacao_dieta.escola,
                fora_da_rede=True,
            )
        elif aluno_matriculado_em_outra_ue(aluno, solicitacao_dieta):
            dados = dict(
                codigo_eol_aluno=aluno.codigo_eol,
                nome_aluno=aluno.nome,
                codigo_eol_escola_destino=aluno.escola.codigo_eol,
                nome_escola_destino=aluno.escola.nome,
                nome_escola_origem=solicitacao_dieta.escola.nome,
                codigo_eol_escola_origem=solicitacao_dieta.escola.codigo_eol,
            )
            gerar_log_dietas_ativas_canceladas_automaticamente(solicitacao_dieta, dados)
            _cancelar_dieta(solicitacao_dieta)
            enviar_email_para_adm_terceirizada_e_escola(
                solicitacao_dieta, aluno, escola=solicitacao_dieta.escola
            )
        else:
            continue


class RelatorioPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ProtocoloPadraoPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


def log_create(protocolo_padrao, user=None):
    import json
    from datetime import datetime

    historico = {}

    historico["created_at"] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    historico["user"] = (
        {
            "uuid": str(user.uuid),
            "email": user.email,
            "username": user.username,
            "nome": user.nome,
        }
        if user
        else user
    )
    historico["action"] = "CREATE"

    editais = []
    for edital in protocolo_padrao.editais.all():
        editais.append(edital.numero)

    substituicoes = []
    for substituicao in protocolo_padrao.substituicoes.all():
        alimentos_substitutos = [
            {"uuid": str(sub.uuid), "nome": sub.nome}
            for sub in substituicao.alimentos_substitutos.all()
        ]
        subs = [
            {"uuid": str(sub.uuid), "nome": sub.nome}
            for sub in substituicao.substitutos.all()
        ]

        substitutos = [*alimentos_substitutos, *subs]
        substituicoes.append(
            {
                "tipo": {"from": None, "to": substituicao.tipo},
                "alimento": {
                    "from": None,
                    "to": {
                        "id": substituicao.alimento.id,
                        "nome": substituicao.alimento.nome,
                    },
                },
                "substitutos": {"from": None, "to": substitutos},
            }
        )

    historico["changes"] = [
        {
            "field": "criado_em",
            "from": None,
            "to": protocolo_padrao.criado_em.strftime("%Y-%m-%d %H:%M:%S"),
        },
        {"field": "id", "from": None, "to": protocolo_padrao.id},
        {
            "field": "nome_protocolo",
            "from": None,
            "to": protocolo_padrao.nome_protocolo,
        },
        {
            "field": "orientacoes_gerais",
            "from": None,
            "to": protocolo_padrao.orientacoes_gerais,
        },
        {"field": "status", "from": None, "to": protocolo_padrao.status},
        {"field": "uuid", "from": None, "to": str(protocolo_padrao.uuid)},
        {"field": "substituicoes", "changes": substituicoes},
        {"field": "editais", "from": None, "to": editais},
    ]

    protocolo_padrao.historico = json.dumps([historico])
    protocolo_padrao.save()


def log_update(
    instance,
    validated_data,
    substituicoes_old,
    substituicoes_new,
    new_editais,
    old_editais,
    user=None,
):
    import json
    from datetime import datetime

    historico = {}
    changes = diff_protocolo_padrao(instance, validated_data, new_editais, old_editais)
    changes_subs = diff_substituicoes(substituicoes_old, substituicoes_new)

    if changes_subs:
        changes.append({"field": "substituicoes", "changes": changes_subs})

    if changes:
        historico["updated_at"] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        historico["user"] = (
            {
                "uuid": str(user.uuid),
                "email": user.email,
                "username": user.username,
                "nome": user.nome,
            }
            if user
            else user
        )
        historico["action"] = "UPDATE"
        historico["changes"] = changes

        hist = json.loads(instance.historico) if instance.historico else []
        hist.append(historico)

        instance.historico = json.dumps(hist)


def diff_protocolo_padrao(instance, validated_data, new_editais, old_editais):
    changes = []

    if instance.nome_protocolo != validated_data["nome_protocolo"]:
        changes.append(
            {
                "field": "nome_protocolo",
                "from": instance.nome_protocolo,
                "to": validated_data["nome_protocolo"],
            }
        )

    if instance.orientacoes_gerais != validated_data["orientacoes_gerais"]:
        changes.append(
            {
                "field": "orientacoes_gerais",
                "from": instance.orientacoes_gerais,
                "to": validated_data["orientacoes_gerais"],
            }
        )

    if instance.status != validated_data["status"]:
        changes.append(
            {"field": "status", "from": instance.status, "to": validated_data["status"]}
        )

    new_editais_list_ordered = set(
        new_editais.order_by("uuid").values_list("uuid", flat=True)
    )
    old_editais_list_ordered = set(
        old_editais.all().order_by("uuid").values_list("uuid", flat=True)
    )
    if new_editais_list_ordered != old_editais_list_ordered:
        changes.append(
            {
                "field": "editais",
                "from": [edital.numero for edital in old_editais.all()],
                "to": [edital.numero for edital in new_editais],
            }
        )

    return changes


def diff_substituicoes(substituicoes_old, substituicoes_new):  # noqa C901
    substituicoes = []

    # Tratando adição e edição de substituíções
    if substituicoes_old.all().count() <= len(substituicoes_new):
        for index, subs_new in enumerate(substituicoes_new):
            sub = {}

            try:
                subs = substituicoes_old.all().order_by("id")[index]
            except IndexError:
                subs = None

            if not subs or subs.alimento.id != subs_new["alimento"].id:
                sub["alimento"] = {
                    "from": {
                        "id": subs.alimento.id if subs else None,
                        "nome": subs.alimento.nome if subs else None,
                    },
                    "to": {
                        "id": subs_new["alimento"].id,
                        "nome": subs_new["alimento"].nome,
                    },
                }

            if not subs or subs.tipo != subs_new["tipo"]:
                sub["tipo"] = {
                    "from": subs.tipo if subs else None,
                    "to": subs_new["tipo"] if subs_new else None,
                }

            al_subs_ids = (
                subs.alimentos_substitutos.all()
                .order_by("id")
                .values_list("id", flat=True)
                if subs
                else []
            )
            subs_ids_old = (
                subs.substitutos.all().order_by("id").values_list("id", flat=True)
                if subs
                else []
            )

            ids_olds = [*al_subs_ids, *subs_ids_old]
            ids_news = sorted([s.id for s in subs_new["substitutos"]])

            from itertools import zip_longest

            if any(
                map(
                    lambda t: t[0] != t[1],
                    zip_longest(ids_olds, ids_news, fillvalue=False),
                )
            ):
                from_ = None

                if subs:
                    alimentos_substitutos = [
                        {"uuid": str(sub.uuid), "nome": sub.nome}
                        for sub in subs.alimentos_substitutos.all()
                    ]

                    substitutos_ = [
                        {"uuid": str(sub.uuid), "nome": sub.nome}
                        for sub in subs.substitutos.all()
                    ]

                    substitutos = [*alimentos_substitutos, *substitutos_]
                    from_ = (
                        [
                            {"uuid": sub["uuid"], "nome": sub["nome"]}
                            for sub in substitutos
                        ]
                        if substitutos
                        else None
                    )

                sub["substitutos"] = {
                    "from": from_,
                    "to": [
                        {"uuid": str(s.uuid), "nome": s.nome}
                        for s in subs_new["substitutos"]
                    ]
                    if subs_new["substitutos"]
                    else None,
                }

            if sub:
                substituicoes.append(sub)

    else:
        # trata a remoção de uma substituíção
        for index, subs in enumerate(substituicoes_old.all()):
            sub = {}
            try:
                subs_new = substituicoes_new[index]
            except IndexError:
                subs_new = None

            if not subs_new or subs.alimento.id != subs_new["alimento"].id:
                sub["alimento"] = {
                    "from": {"id": subs.alimento.id, "nome": subs.alimento.nome},
                    "to": {
                        "id": subs_new["alimento"].id if subs_new else None,
                        "nome": subs_new["alimento"].nome if subs_new else None,
                    },
                }

            if not subs_new or subs.tipo != subs_new["tipo"]:
                sub["tipo"] = {
                    "from": subs.tipo,
                    "to": subs_new["tipo"] if subs_new else None,
                }

            al_sub_ids = (
                subs.alimentos_substitutos.all()
                .order_by("id")
                .values_list("id", flat=True)
                if subs
                else []
            )
            subs_ids_old = (
                subs.substitutos.all().order_by("id").values_list("id", flat=True)
                if subs
                else []
            )

            ids_olds = [*al_sub_ids, *subs_ids_old]
            ids_news = (
                sorted([s.id for s in subs_new["substitutos"]]) if subs_new else []
            )

            from itertools import zip_longest

            if any(
                map(
                    lambda t: t[0] != t[1],
                    zip_longest(ids_olds, ids_news, fillvalue=False),
                )
            ):
                to_ = None
                if subs_new:
                    to_ = (
                        [
                            {"uuid": str(s.uuid), "nome": s.nome}
                            for s in subs_new["substitutos"]
                        ]
                        if subs_new["substitutos"]
                        else None
                    )

                alimentos_substitutos = [
                    {"uuid": str(sub.uuid), "nome": sub.nome}
                    for sub in subs.alimentos_substitutos.all()
                ]

                substitutos_ = [
                    {"uuid": str(sub.uuid), "nome": sub.nome}
                    for sub in subs.substitutos.all()
                ]

                substitutos = [*alimentos_substitutos, *substitutos_]

                sub["substitutos"] = {
                    "from": [
                        {"uuid": sub["uuid"], "nome": sub["nome"]}
                        for sub in substitutos
                    ]
                    if substitutos
                    else None,
                    "to": to_,
                }

            if sub:
                substituicoes.append(sub)

    return substituicoes


def is_alpha_numeric_and_has_single_space(descricao):
    return bool(re.match(r"[A-Za-z0-9\s]+$", descricao))


def verifica_se_existe_dieta_valida(aluno, queryset, status_dieta, escola):
    return [
        s
        for s in aluno.dietas_especiais.all()
        if s.rastro_escola == escola and s.status in status_dieta
    ]


def filtrar_alunos_com_dietas_nos_status_e_rastro_escola(
    queryset, status_dieta, escola
):
    uuids_alunos_para_excluir = []
    for aluno in queryset:
        if not verifica_se_existe_dieta_valida(aluno, queryset, status_dieta, escola):
            uuids_alunos_para_excluir.append(aluno.uuid)
    queryset = queryset.exclude(uuid__in=uuids_alunos_para_excluir)
    return queryset


def get_quantidade_nao_matriculados_entre_4_e_6_anos(dietas):
    return dietas.filter(
        tipo_solicitacao="ALUNO_NAO_MATRICULADO",
        aluno__data_nascimento__lte=date.today() - relativedelta(years=4),
        aluno__data_nascimento__gte=date.today() - relativedelta(years=6),
    ).count()


def get_quantidade_nao_matriculados_maior_6_anos(dietas):
    return dietas.filter(
        tipo_solicitacao="ALUNO_NAO_MATRICULADO",
        aluno__data_nascimento__lte=date.today() - relativedelta(years=6),
    ).count()


def get_quantidade_dietas_emebs(each, dietas):
    dietas_sem_alunos_nao_matriculados = dietas.exclude(
        tipo_solicitacao="ALUNO_NAO_MATRICULADO"
    )
    if each == "INFANTIL":
        quantidade = dietas_sem_alunos_nao_matriculados.filter(
            aluno__etapa=ETAPA_INFANTIL
        ).count()
        quantidade += get_quantidade_nao_matriculados_entre_4_e_6_anos(dietas)
    else:
        quantidade = dietas_sem_alunos_nao_matriculados.exclude(
            aluno__etapa=ETAPA_INFANTIL
        ).count()
        quantidade += get_quantidade_nao_matriculados_maior_6_anos(dietas)
    return quantidade


def logs_a_criar_sem_periodo_escolar(
    logs_a_criar, escola, dietas_filtradas, ontem, classificacao
):
    if escola.eh_emebs:
        for each in ["INFANTIL", "FUNDAMENTAL"]:
            quantidade = get_quantidade_dietas_emebs(each, dietas_filtradas)
            log = LogQuantidadeDietasAutorizadas(
                quantidade=quantidade,
                escola=escola,
                data=ontem,
                classificacao=classificacao,
                infantil_ou_fundamental=each,
            )
            logs_a_criar.append(log)
    else:
        log = LogQuantidadeDietasAutorizadas(
            quantidade=dietas_filtradas.count(),
            escola=escola,
            data=ontem,
            classificacao=classificacao,
        )
        logs_a_criar.append(log)
    return logs_a_criar


def gera_logs_dietas_escolas_comuns(escola, dietas_autorizadas, ontem):
    logs_a_criar = []
    dict_periodos = PeriodoEscolar.dict_periodos()
    for classificacao in ClassificacaoDieta.objects.all():
        dietas_filtradas = dietas_autorizadas.filter(
            classificacao=classificacao, escola_destino=escola
        )
        logs_a_criar = logs_a_criar_sem_periodo_escolar(
            logs_a_criar, escola, dietas_filtradas, ontem, classificacao
        )
        for periodo_escolar_nome in escola.periodos_escolares_com_alunos:
            dietas_filtradas_periodo = dietas_autorizadas.filter(
                classificacao=classificacao, escola_destino=escola
            ).filter(
                Q(aluno__periodo_escolar__nome=periodo_escolar_nome)
                | Q(tipo_solicitacao="ALUNO_NAO_MATRICULADO")
            )
            if escola.eh_cemei and periodo_escolar_nome == "INTEGRAL":
                logs_a_criar = logs_periodo_integral_cei_ou_emei_escola_cemei(
                    logs_a_criar,
                    dietas_autorizadas,
                    classificacao,
                    escola,
                    periodo_escolar_nome,
                    dict_periodos,
                    ontem,
                )
            if escola.eh_emebs:
                for each in ["INFANTIL", "FUNDAMENTAL"]:
                    quantidade = get_quantidade_dietas_emebs(
                        each, dietas_filtradas_periodo
                    )
                    log = LogQuantidadeDietasAutorizadas(
                        quantidade=quantidade,
                        escola=escola,
                        data=ontem,
                        periodo_escolar=dict_periodos[periodo_escolar_nome],
                        classificacao=classificacao,
                        infantil_ou_fundamental=each,
                    )
                    logs_a_criar.append(log)
            else:
                log = LogQuantidadeDietasAutorizadas(
                    quantidade=dietas_filtradas_periodo.count(),
                    escola=escola,
                    data=ontem,
                    periodo_escolar=dict_periodos[periodo_escolar_nome],
                    classificacao=classificacao,
                )
                logs_a_criar.append(log)
    return logs_a_criar


def logs_periodo_integral_cei_ou_emei_escola_cemei(
    logs_a_criar,
    dietas_autorizadas,
    classificacao,
    escola,
    periodo_escolar_nome,
    dict_periodos,
    ontem,
):
    dietas = dietas_autorizadas.filter(
        classificacao=classificacao, escola_destino=escola
    ).filter(
        Q(aluno__periodo_escolar__nome=periodo_escolar_nome)
        | Q(tipo_solicitacao="ALUNO_NAO_MATRICULADO")
    )
    series_cei = ["1", "2", "3", "4"]
    quantidade_cei = 0
    quantidade_emei = 0
    for dieta in dietas:
        if not dieta.aluno.serie:
            quantidade_cei += 1
            quantidade_emei += 1
        elif any(
            serie in dieta.aluno.serie for serie in series_cei if dieta.aluno.serie
        ):
            quantidade_cei += 1
        else:
            quantidade_emei += 1
    log_cei = LogQuantidadeDietasAutorizadas(
        quantidade=quantidade_cei,
        escola=escola,
        data=ontem,
        periodo_escolar=dict_periodos[periodo_escolar_nome],
        classificacao=classificacao,
        cei_ou_emei="CEI",
    )
    log_emei = LogQuantidadeDietasAutorizadas(
        quantidade=quantidade_emei,
        escola=escola,
        data=ontem,
        periodo_escolar=dict_periodos[periodo_escolar_nome],
        classificacao=classificacao,
        cei_ou_emei="EMEI",
    )
    return logs_a_criar + [log_cei] + [log_emei]


def gera_logs_dietas_escolas_cei(escola, dietas_autorizadas, ontem):
    try:
        return logs_a_criar_existe_solicitacao_medicao(
            escola, dietas_autorizadas, ontem
        )
    except ObjectDoesNotExist:
        return logs_a_criar_nao_existe_solicitacao_medicao(
            escola, dietas_autorizadas, ontem
        )


def logs_a_criar_existe_solicitacao_medicao(escola, dietas_autorizadas, ontem):
    solicitacao_medicao = SolicitacaoMedicaoInicial.objects.get(
        escola__codigo_eol=escola.codigo_eol,
        mes=f"{date.today().month:02d}",
        ano=date.today().year,
    )
    dict_periodos = PeriodoEscolar.dict_periodos()
    logs_a_criar = []
    periodos = escola.periodos_escolares_com_alunos
    periodos = append_periodo_parcial(periodos, solicitacao_medicao)
    periodos = list(set(periodos))
    for periodo in periodos:
        for classificacao in ClassificacaoDieta.objects.all():
            dietas = dietas_autorizadas.filter(
                classificacao=classificacao, escola_destino=escola
            )
            dietas_filtradas_periodo = dietas.filter(
                aluno__periodo_escolar__nome=periodo
            )
            dietas_nao_matriculados = dietas.filter(
                tipo_solicitacao="ALUNO_NAO_MATRICULADO"
            )
            faixas = []
            faixas += append_faixas_dietas(dietas_filtradas_periodo, escola)
            faixas += append_faixas_dietas(dietas_nao_matriculados, escola)
            if periodo == "INTEGRAL" and "PARCIAL" in periodos:
                logs_a_criar += criar_logs_integral_parcial(
                    True,
                    dietas,
                    solicitacao_medicao,
                    escola,
                    ontem,
                    classificacao,
                    periodo,
                    faixas,
                )
            elif periodo == "PARCIAL":
                logs_a_criar += criar_logs_integral_parcial(
                    False,
                    dietas,
                    solicitacao_medicao,
                    escola,
                    ontem,
                    classificacao,
                    periodo,
                    None,
                )
            else:
                for faixa, quantidade in Counter(faixas).items():
                    log = LogQuantidadeDietasAutorizadasCEI(
                        quantidade=quantidade,
                        escola=escola,
                        data=ontem,
                        classificacao=classificacao,
                        periodo_escolar=dict_periodos[periodo],
                        faixa_etaria=faixa,
                    )
                    logs_a_criar.append(log)
    logs_a_criar = append_logs_a_criar_de_quantidade_zero(
        logs_a_criar, periodos, escola, ontem
    )
    return logs_a_criar


def logs_a_criar_nao_existe_solicitacao_medicao(escola, dietas_autorizadas, ontem):
    logs_a_criar = []
    periodos = escola.periodos_escolares_com_alunos
    dict_periodos = PeriodoEscolar.dict_periodos()
    for periodo in periodos:
        for classificacao in ClassificacaoDieta.objects.all():
            dietas = dietas_autorizadas.filter(
                classificacao=classificacao, escola_destino=escola
            )
            dietas_filtradas_periodo = dietas.filter(
                aluno__periodo_escolar__nome=periodo
            )
            dietas_nao_matriculados = dietas.filter(
                tipo_solicitacao="ALUNO_NAO_MATRICULADO"
            )
            faixas = []
            faixas += append_faixas_dietas(dietas_filtradas_periodo, escola)
            faixas += append_faixas_dietas(dietas_nao_matriculados, escola)
            for faixa, quantidade in Counter(faixas).items():
                log = LogQuantidadeDietasAutorizadasCEI(
                    quantidade=quantidade,
                    escola=escola,
                    data=ontem,
                    classificacao=classificacao,
                    periodo_escolar=dict_periodos[periodo],
                    faixa_etaria=faixa,
                )
                logs_a_criar.append(log)
    logs_a_criar = append_logs_a_criar_de_quantidade_zero(
        logs_a_criar, periodos, escola, ontem
    )
    return logs_a_criar


def append_logs_a_criar_de_quantidade_zero(logs_a_criar, periodos, escola, ontem):
    dict_periodos = PeriodoEscolar.dict_periodos()
    for periodo in periodos:
        faixas = faixas_por_periodo_e_faixa_etaria(escola, periodo)
        for faixa, _ in faixas.items():
            if faixa in [
                str(f)
                for f in FaixaEtaria.objects.filter(ativo=True).values_list(
                    "uuid", flat=True
                )
            ]:
                for classificacao in ClassificacaoDieta.objects.all():
                    if not existe_log(
                        logs_a_criar, escola, ontem, classificacao, periodo, faixa
                    ):
                        log = LogQuantidadeDietasAutorizadasCEI(
                            quantidade=0,
                            escola=escola,
                            data=ontem,
                            classificacao=classificacao,
                            periodo_escolar=dict_periodos[periodo],
                            faixa_etaria=FaixaEtaria.objects.get(uuid=faixa),
                        )
                        logs_a_criar.append(log)
    return logs_a_criar


def faixas_por_periodo_e_faixa_etaria(escola, periodo):
    try:
        return escola.matriculados_por_periodo_e_faixa_etaria()[periodo]
    except KeyError:
        return escola.matriculados_por_periodo_e_faixa_etaria()["INTEGRAL"]


def existe_log(logs_a_criar, escola, ontem, classificacao, periodo, faixa):
    resultado = list(
        filter(
            lambda log: condicoes(log, escola, ontem, classificacao, periodo, faixa),
            logs_a_criar,
        )
    )
    return resultado


def condicoes(log, escola, ontem, classificacao, periodo, faixa):
    resultado = (
        log.escola == escola
        and log.data == ontem
        and log.classificacao == classificacao
        and log.periodo_escolar.nome == periodo
        and str(log.faixa_etaria.uuid) == faixa
    )
    return resultado


def append_periodo_parcial(periodos, solicitacao_medicao):
    if solicitacao_medicao.ue_possui_alunos_periodo_parcial:
        periodos.append("PARCIAL")
    return periodos


def quantidade_meses(d1, d2):
    delta = relativedelta(d1, d2)
    return (delta.years * 12) + delta.months


def append_faixas_dietas(dietas, escola):
    faixas = []
    series_cei = ["1", "2", "3", "4"]
    for dieta_periodo in dietas:
        data_nascimento = dieta_periodo.aluno.data_nascimento
        meses = quantidade_meses(date.today(), data_nascimento)
        ultima_faixa = FaixaEtaria.objects.filter(ativo=True).order_by("fim").last()
        if meses >= ultima_faixa.fim:
            faixa = ultima_faixa
        else:
            faixa = FaixaEtaria.objects.get(
                ativo=True, inicio__lte=meses, fim__gt=meses
            )
        if escola.eh_cemei and not any(
            serie in dieta_periodo.aluno.serie
            for serie in series_cei
            if dieta_periodo.aluno.serie
        ):
            continue
        faixas.append(faixa)
    return faixas


def criar_logs_integral_parcial(
    eh_integral,
    dietas,
    solicitacao_medicao,
    escola,
    ontem,
    classificacao,
    periodo,
    faixas,
):
    logs = []
    dict_periodos = PeriodoEscolar.dict_periodos()
    faixas_alunos_parciais = []
    for dieta in dietas:
        if dieta.aluno.nome in solicitacao_medicao.alunos_periodo_parcial.values_list(
            "aluno__nome", flat=True
        ):
            data_nascimento = dieta.aluno.data_nascimento
            meses = quantidade_meses(date.today(), data_nascimento)
            faixa = FaixaEtaria.objects.get(
                ativo=True, inicio__lte=meses, fim__gt=meses
            )
            faixas_alunos_parciais.append(faixa)
    faixas = faixas if eh_integral else faixas_alunos_parciais
    for faixa, quantidade in Counter(faixas).items():
        if eh_integral and faixa in Counter(faixas_alunos_parciais).keys():
            quantidade = quantidade - Counter(faixas_alunos_parciais).get(faixa)
        log = LogQuantidadeDietasAutorizadasCEI(
            quantidade=quantidade,
            escola=escola,
            data=ontem,
            classificacao=classificacao,
            periodo_escolar=dict_periodos[periodo],
            faixa_etaria=faixa,
        )
        logs.append(log)
    return logs


def trata_lotes_dict_duplicados(lotes_dict):
    lotes_ = []
    for lote_uuid in lotes_dict.values():
        try:
            lotes_.append(
                tuple([Lote.objects.get(uuid=lote_uuid).__str__(), lote_uuid])
            )
        except Lote.DoesNotExist:
            continue
    return dict(lotes_)


def gerar_filtros_relatorio_historico(query_params: dict) -> dict:
    """_
    Gera os filtros
    """
    map_filtros = {
        "escola__uuid__in": query_params.getlist(
            "unidades_educacionais_selecionadas[]", None
        ),
        "periodo_escolar__uuid__in": query_params.getlist(
            "periodos_escolares_selecionadas[]", None
        ),
        "classificacao__id__in": query_params.getlist(
            "classificacoes_selecionadas[]", None
        ),
    }

    formato = "%d/%m/%Y"
    data_dieta = query_params.get("data")
    if data_dieta:
        data = datetime.strptime(data_dieta, formato)
        map_filtros.update(
            {"data__day": data.day, "data__month": data.month, "data__year": data.year}
        )

    filtros = {
        key: value for key, value in map_filtros.items() if value not in [None, []]
    }
    return filtros


def dados_dietas_escolas_cei(filtros: dict) -> List[dict]:
    logs_dietas_escolas_cei = (
        LogQuantidadeDietasAutorizadasCEI.objects.filter(**filtros)
        .values(
            "escola__nome",
            "escola__tipo_unidade__iniciais",
            "escola__lote__nome",
            "classificacao__nome",
            "periodo_escolar__nome",
            "faixa_etaria__inicio",
            "faixa_etaria__fim",
            "escola__uuid",
        )
        .annotate(quantidade_total=Sum("quantidade"))
    )

    return list(logs_dietas_escolas_cei)


def dados_dietas_escolas_comuns(filtros: dict) -> List[dict]:
    logs_dietas_outras_escolas = (
        LogQuantidadeDietasAutorizadas.objects.filter(**filtros)
        .values(
            "escola__nome",
            "escola__tipo_unidade__iniciais",
            "escola__lote__nome",
            "classificacao__nome",
            "periodo_escolar__nome",
            "infantil_ou_fundamental",
            "cei_ou_emei",
            "escola__uuid",
        )
        .annotate(quantidade_total=Sum("quantidade"))
    )

    return list(logs_dietas_outras_escolas)


def gera_dicionario_historico_dietas(log_escolas_cei, log_escolas):
    logs_dietas = log_escolas + log_escolas_cei
    info = transform_data(logs_dietas)
    return info


def transform_data(data):
    from collections import defaultdict

    categorias = {
        "cei_ceucei_cci": ["CEI", "CEU CEI", "CCI"],
        "cemei": ["CEMEI"],
        "emebs": ["EMEBS"],
    }

    resultado = defaultdict(list)
    resultado["total_dietas"] = 0

    for item in data:
        resultado["total_dietas"] += item["quantidade_total"]
        tipo_unidade = item.get("escola__tipo_unidade__iniciais", "OUTRAS")
        chave_categoria = next(
            (k for k, v in categorias.items() if tipo_unidade in v), "outras"
        )
        unidade = next(
            (
                escola
                for escola in resultado[chave_categoria]
                if escola["unidade_educacional"] == item["escola__nome"]
            ),
            None,
        )
        if not unidade:
            unidade = {
                "lote": item["escola__lote__nome"],
                "unidade_educacional": item["escola__nome"],
                "tipo_unidade": tipo_unidade,
                "classificacao_dieta": [],
            }
            resultado[chave_categoria].append(unidade)

        classificacao = next(
            (
                c
                for c in unidade["classificacao_dieta"]
                if c["tipo"] == item["classificacao__nome"]
            ),
            None,
        )
        if not classificacao:
            classificacao = {
                "tipo": item["classificacao__nome"],
                "total": 0,
            }
            if tipo_unidade in ["EMEBS", "CEMEI"]:
                classificacao["periodos"] = {}
            elif tipo_unidade not in ["CEU GESTAO", "CMCT"]:
                classificacao["periodos"] = []

            unidade["classificacao_dieta"].append(classificacao)

        classificacao["total"] += item["quantidade_total"]
        periodo_nome = item["periodo_escolar__nome"] or "N/A"

        if tipo_unidade == "EMEBS":
            turma = (
                "fundamental"
                if item.get("infantil_ou_fundamental") == "FUNDAMENTAL"
                else "infantil"
            )
            if turma not in classificacao["periodos"]:
                classificacao["periodos"][turma] = []
            periodo = next(
                (
                    p
                    for p in classificacao["periodos"].get(turma, [])
                    if p["periodo"] == periodo_nome
                ),
                None,
            )
            if not periodo:
                periodo = {
                    "periodo": periodo_nome,
                    "autorizadas": item["quantidade_total"],
                }
                classificacao["periodos"][turma].append(periodo)
            else:
                periodo["autorizadas"] += item["quantidade_total"]

        elif tipo_unidade in ["CEU GESTAO", "CMCT"]:
            classificacao["total"] += item["quantidade_total"]

        elif tipo_unidade in ["CEMEI"]:
            if "faixa_etaria__inicio" in item and "faixa_etaria__fim" in item:
                turma = "por_idade"
                if turma not in classificacao["periodos"]:
                    classificacao["periodos"][turma] = []

                periodo = next(
                    (
                        p
                        for p in classificacao["periodos"].get(turma, [])
                        if p["periodo"] == periodo_nome
                    ),
                    None,
                )

                if not periodo:
                    periodo = {
                        "periodo": periodo_nome,
                        "faixa_etaria": [],
                    }
                    classificacao["periodos"][turma].append(periodo)

                faixa = (
                    f"{item['faixa_etaria__inicio']} a {item['faixa_etaria__fim']} anos"
                )
                faixa_etaria = next(
                    (f for f in periodo.get("faixa_etaria", []) if f["faixa"] == faixa),
                    None,
                )
                if not faixa_etaria:
                    faixa_etaria = {
                        "faixa": faixa,
                        "autorizadas": item["quantidade_total"],
                    }
                    periodo["faixa_etaria"].append(faixa_etaria)
                else:
                    faixa_etaria["autorizadas"] += item["quantidade_total"]

            else:
                turma = "turma_infantil"
                if turma not in classificacao["periodos"]:
                    classificacao["periodos"][turma] = []
                periodo = next(
                    (
                        p
                        for p in classificacao["periodos"].get(turma, [])
                        if p["periodo"] == periodo_nome
                    ),
                    None,
                )
                if not periodo:
                    periodo = {
                        "periodo": periodo_nome,
                        "autorizadas": item["quantidade_total"],
                    }
                    classificacao["periodos"][turma].append(periodo)
                else:
                    periodo["autorizadas"] += item["quantidade_total"]

        elif tipo_unidade in ["CEI", "CEU CEI", "CCI"]:
            periodo = next(
                (p for p in classificacao["periodos"] if p["periodo"] == periodo_nome),
                None,
            )
            if not periodo:
                periodo = {"periodo": periodo_nome, "faixa_etaria": []}
                classificacao["periodos"].append(periodo)

            if "faixa_etaria__inicio" in item and "faixa_etaria__fim" in item:
                faixa = (
                    f"{item['faixa_etaria__inicio']} a {item['faixa_etaria__fim']} anos"
                )
                faixa_etaria = next(
                    (f for f in periodo.get("faixa_etaria", []) if f["faixa"] == faixa),
                    None,
                )
                if not faixa_etaria:
                    faixa_etaria = {
                        "faixa": faixa,
                        "autorizadas": item["quantidade_total"],
                    }
                    periodo["faixa_etaria"].append(faixa_etaria)
                else:
                    faixa_etaria["autorizadas"] += item["quantidade_total"]
        else:
            try:
                periodo = next(
                    (
                        p
                        for p in classificacao["periodos"]
                        if p["periodo"] == periodo_nome
                    ),
                    None,
                )
            except KeyError:
                print(item["escola__nome"], item["escola__uuid"])
                continue

            if not periodo:
                periodo = {
                    "periodo": periodo_nome,
                    "autorizadas": item["quantidade_total"],
                }

                classificacao["periodos"].append(periodo)
            else:
                periodo["autorizadas"] += item["quantidade_total"]

    return resultado
