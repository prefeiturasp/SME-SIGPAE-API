import re
from collections import Counter, defaultdict
from datetime import date, datetime
from itertools import chain
from typing import List

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import CharField, F, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import QueryDict
from django.template.loader import render_to_string
from rest_framework.pagination import PageNumberPagination

from sme_sigpae_api.dieta_especial.models import (
    ClassificacaoDieta,
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
)
from sme_sigpae_api.escola.models import Lote
from sme_sigpae_api.escola.utils import faixa_to_string
from sme_sigpae_api.medicao_inicial.models import SolicitacaoMedicaoInicial
from sme_sigpae_api.perfil.models import Usuario
from sme_sigpae_api.relatorios.relatorios import relatorio_dieta_especial_conteudo
from sme_sigpae_api.relatorios.utils import html_to_pdf_email_anexo

from ..dados_comuns.constants import TIPO_SOLICITACAO_DIETA
from ..dados_comuns.fluxo_status import DietaEspecialWorkflow
from ..dados_comuns.utils import envia_email_unico, envia_email_unico_com_anexo_inmemory
from ..escola.models import Aluno, FaixaEtaria, PeriodoEscolar
from ..paineis_consolidados.models import SolicitacoesCODAE
from .constants import (
    ETAPA_INFANTIL,
    UNIDADES_CEI,
    UNIDADES_CEMEI,
    UNIDADES_EMEBS,
    UNIDADES_EMEI_EMEF_CIEJA,
    UNIDADES_SEM_PERIODOS,
)
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
    elif each == "FUNDAMENTAL":
        quantidade = dietas_sem_alunos_nao_matriculados.exclude(
            aluno__etapa=ETAPA_INFANTIL
        ).count()
        quantidade += get_quantidade_nao_matriculados_maior_6_anos(dietas)
    else:
        quantidade = dietas_sem_alunos_nao_matriculados.count()
        quantidade += get_quantidade_nao_matriculados_maior_6_anos(dietas)
        quantidade += get_quantidade_nao_matriculados_entre_4_e_6_anos(dietas)
    return quantidade


def logs_a_criar_sem_periodo_escolar(
    logs_a_criar, escola, dietas_filtradas, ontem, classificacao
):
    if escola.eh_emebs:
        for each in ["INFANTIL", "FUNDAMENTAL", "N/A"]:
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


def gerar_filtros_relatorio_historico(
    query_params: QueryDict, eh_exportacao=False
) -> tuple:
    map_filtros = {
        "escola__tipo_gestao__uuid": query_params.get("tipo_gestao", None),
        "escola__tipo_unidade__uuid__in": query_params.getlist(
            "tipos_unidades_selecionadas[]", None
        ),
        "escola__lote__uuid": query_params.get("lote", None),
        "escola__uuid__in": query_params.getlist(
            "unidades_educacionais_selecionadas[]", None
        ),
        "periodo_escolar__uuid__in": query_params.getlist(
            "periodos_escolares_selecionadas[]", None
        ),
        "classificacao__id__in": query_params.getlist(
            "classificacoes_selecionadas[]", None
        ),
        "quantidade__gt": 0,
    }

    if eh_exportacao:
        map_filtros["periodo_escolar__isnull"] = False

    data_dieta = query_params.get("data")
    if not data_dieta:
        raise ValidationError("`data` é um parâmetro obrigatório.")
    try:
        formato = "%d/%m/%Y"
        data = datetime.strptime(data_dieta, formato)
    except ValueError:
        raise ValidationError(
            f"A data {data_dieta} não corresponde ao formato esperado 'dd/mm/YYYY'."
        )

    map_filtros.update(
        {"data__day": data.day, "data__month": data.month, "data__year": data.year}
    )

    filtros = {
        key: value for key, value in map_filtros.items() if value not in [None, []]
    }
    return filtros, data_dieta


def dados_dietas_escolas_cei(filtros: dict) -> List[dict]:
    logs_dietas_escolas_cei = (
        LogQuantidadeDietasAutorizadasCEI.objects.filter(**filtros)
        .select_related(
            "escola",
            "periodo_escolar",
            "escola__tipo_unidade",
            "classificacao",
            "faixa_etaria",
        )
        .annotate(
            nome_escola=F("escola__nome"),
            nome_periodo_escolar=Coalesce(F("periodo_escolar__nome"), Value(None)),
            tipo_unidade=F("escola__tipo_unidade__iniciais"),
            lote=F("escola__lote__nome"),
            nome_classificacao=F("classificacao__nome"),
            quantidade_total=Sum("quantidade"),
            inicio=Coalesce(F("faixa_etaria__inicio"), Value(None)),
            fim=Coalesce(F("faixa_etaria__fim"), Value(None)),
            infantil_ou_fundamental=Value(None, output_field=CharField()),
            cei_ou_emei=Value(None, output_field=CharField()),
        )
        .values(
            "nome_escola",
            "tipo_unidade",
            "lote",
            "nome_classificacao",
            "nome_periodo_escolar",
            "infantil_ou_fundamental",
            "cei_ou_emei",
            "data",
            "quantidade_total",
            "inicio",
            "fim",
        )
        .order_by("nome_escola", "faixa_etaria__inicio")
    )

    return logs_dietas_escolas_cei


def dados_dietas_escolas_comuns(filtros: dict) -> List[dict]:
    filtro_por_tipo_unidade = Q(
        Q(
            escola__tipo_unidade__iniciais__in=UNIDADES_EMEBS,
            periodo_escolar__isnull=True,
            cei_ou_emei="N/A",
            infantil_ou_fundamental__in=["FUNDAMENTAL", "INFANTIL"],
        )
        | Q(
            escola__tipo_unidade__iniciais__in=UNIDADES_CEMEI,
            periodo_escolar__nome="INTEGRAL",
            cei_ou_emei__in=["CEI", "EMEI"],
        )
    )
    logs_dietas_outras_escolas = (
        LogQuantidadeDietasAutorizadas.objects.filter(**filtros)
        .exclude(filtro_por_tipo_unidade)
        .select_related(
            "escola", "periodo_escolar", "escola__tipo_unidade", "classificacao"
        )
        .annotate(
            nome_escola=F("escola__nome"),
            nome_periodo_escolar=Coalesce(F("periodo_escolar__nome"), Value(None)),
            tipo_unidade=F("escola__tipo_unidade__iniciais"),
            lote=F("escola__lote__nome"),
            nome_classificacao=F("classificacao__nome"),
            quantidade_total=Sum("quantidade"),
            inicio=Value(None, output_field=IntegerField()),
            fim=Value(None, output_field=IntegerField()),
        )
        .values(
            "nome_escola",
            "tipo_unidade",
            "lote",
            "nome_classificacao",
            "nome_periodo_escolar",
            "infantil_ou_fundamental",
            "cei_ou_emei",
            "data",
            "quantidade_total",
            "inicio",
            "fim",
        )
        .order_by("nome_escola")
    )

    return logs_dietas_outras_escolas


def get_logs_historico_dietas(filtros) -> list:
    log_escolas_cei = dados_dietas_escolas_cei(filtros)
    log_escolas = dados_dietas_escolas_comuns(filtros)
    log_dietas = sorted(
        chain(log_escolas_cei, log_escolas), key=lambda x: x["nome_escola"]
    )
    return log_dietas


def gera_dicionario_historico_dietas(filtros):
    log_dietas = get_logs_historico_dietas(filtros)
    periodo_escolar_selecionado = False
    if "periodo_escolar__uuid__in" in filtros:
        periodo_escolar_selecionado = True
    escolas, total_dietas = transformar_dados_escolas(
        log_dietas, periodo_escolar_selecionado
    )
    informacoes = formatar_informacoes_historioco_dietas(escolas, total_dietas)
    return informacoes


def transformar_dados_escolas(dados, periodo_escolar_selecionado=False):
    escolas = defaultdict(
        lambda: {
            "tipo_unidade": None,
            "lote": None,
            "classificacoes": defaultdict(
                lambda: {
                    "infantil": defaultdict(int),
                    "fundamental": defaultdict(int),
                    "periodos": defaultdict(int),
                    "por_idade": defaultdict(int),
                    "turma_infantil": defaultdict(int),
                    "faixa_etaria": defaultdict(int),
                    "total": 0,
                }
            ),
        }
    )

    tipos_unidades = {
        **{tipo: unidades_tipo_emebs for tipo in UNIDADES_EMEBS},
        **{tipo: unidades_tipos_emei_emef_cieja for tipo in UNIDADES_EMEI_EMEF_CIEJA},
        **{tipo: unidades_tipos_cmct_ceugestao for tipo in UNIDADES_SEM_PERIODOS},
        **{tipo: unidades_tipo_cemei for tipo in UNIDADES_CEMEI},
        **{tipo: unidades_tipo_cei for tipo in UNIDADES_CEI},
    }

    total_dietas = 0
    for item in dados:
        nome_escola = item["nome_escola"]
        tipo_unidade = item["tipo_unidade"]

        escolas[nome_escola]["tipo_unidade"] = tipo_unidade
        escolas[nome_escola]["lote"] = item["lote"]
        escolas[nome_escola]["data"] = item["data"]

        unidade = tipos_unidades.get(tipo_unidade, lambda e, i, p: 0)
        total_dietas += unidade(item, escolas, periodo_escolar_selecionado)

    return escolas, total_dietas


def formatar_informacoes_historioco_dietas(escolas, total_dietas):
    tipos_unidades = {
        **{tipo: formatar_periodos_emebs for tipo in UNIDADES_EMEBS},
        **{
            tipo: formatar_periodos_emei_emef_cieja for tipo in UNIDADES_EMEI_EMEF_CIEJA
        },
        **{tipo: formatar_periodos_cemei for tipo in UNIDADES_CEMEI},
        **{tipo: formatar_periodos_cei for tipo in UNIDADES_CEI},
    }

    resultado = []
    for escola_nome, dados_escola in escolas.items():
        for classificacao, dados_classificacao in dados_escola[
            "classificacoes"
        ].items():
            tipo_unidade = dados_escola["tipo_unidade"]
            informacao_escola_por_classificacao = {
                "data": dados_escola["data"],
                "lote": dados_escola["lote"],
                "unidade_educacional": escola_nome,
                "tipo_unidade": dados_escola["tipo_unidade"],
                "classificacao": classificacao,
                "total": dados_classificacao["total"],
            }
            unidade = tipos_unidades.get(tipo_unidade, lambda i, d: None)
            unidade(informacao_escola_por_classificacao, dados_classificacao)
            resultado.append(informacao_escola_por_classificacao)

    return {
        "total_dietas": total_dietas,
        "resultados": resultado,
    }


def unidades_tipo_emebs(item, escolas, periodo_escolar_selecionado=False):
    nome_escola = item["nome_escola"]
    classificacao = item["nome_classificacao"]
    periodo_escola = item["nome_periodo_escolar"]
    tipo_turma = item["infantil_ou_fundamental"]
    cei_emei = item["cei_ou_emei"]
    quantidade = item["quantidade_total"]

    total_dietas = 0
    if periodo_escola:
        escolas[nome_escola]["classificacoes"][classificacao][f"{tipo_turma}".lower()][
            periodo_escola
        ] += quantidade
        if periodo_escolar_selecionado:
            escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
            total_dietas = quantidade
    elif periodo_escola is None and tipo_turma == "N/A" and cei_emei == "N/A":
        escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
        total_dietas = quantidade
    return total_dietas


def unidades_tipos_emei_emef_cieja(item, escolas, periodo_escolar_selecionado=False):
    nome_escola = item["nome_escola"]
    classificacao = item["nome_classificacao"]
    periodo_escola = item["nome_periodo_escolar"]
    tipo_turma = item["infantil_ou_fundamental"]
    cei_emei = item["cei_ou_emei"]
    quantidade = item["quantidade_total"]

    total_dietas = 0
    if periodo_escola:
        escolas[nome_escola]["classificacoes"][classificacao]["periodos"][
            periodo_escola
        ] += quantidade
        if periodo_escolar_selecionado:
            escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
            total_dietas = quantidade
    elif periodo_escola is None and tipo_turma == "N/A" and cei_emei == "N/A":
        escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
        total_dietas = quantidade

    return total_dietas


def unidades_tipos_cmct_ceugestao(item, escolas, periodo_escolar_selecionado=False):
    nome_escola = item["nome_escola"]
    classificacao = item["nome_classificacao"]
    quantidade = item["quantidade_total"]

    escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
    return quantidade


def unidades_tipo_cei(item, escolas, periodo_escolar_selecionado=False):
    nome_escola = item["nome_escola"]
    classificacao = item["nome_classificacao"]
    periodo_escola = item["nome_periodo_escolar"]
    quantidade = item["quantidade_total"]
    inicio = item["inicio"]
    fim = item["fim"]

    total_dietas = 0
    if inicio is not None and fim is not None:
        faixa_etaria_infantil = faixa_to_string(item["inicio"], item["fim"])
        if (
            escolas[nome_escola]["classificacoes"][classificacao]["periodos"][
                periodo_escola
            ]
            == 0
        ):
            escolas[nome_escola]["classificacoes"][classificacao]["periodos"][
                periodo_escola
            ] = []

        escolas[nome_escola]["classificacoes"][classificacao]["periodos"][
            periodo_escola
        ].append({"faixa": faixa_etaria_infantil, "autorizadas": quantidade})
    else:
        escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
        total_dietas = quantidade

    return total_dietas


def unidades_tipo_cemei(item, escolas, periodo_escolar_selecionado=False):  # noqa
    nome_escola = item["nome_escola"]
    classificacao = item["nome_classificacao"]
    periodo_escola = item["nome_periodo_escolar"]
    tipo_turma = item["infantil_ou_fundamental"]
    cei_emei = item["cei_ou_emei"]
    quantidade = item["quantidade_total"]
    inicio = item["inicio"]
    fim = item["fim"]

    total_dietas = 0
    if inicio is not None and fim is not None:
        faixa_etaria_infantil = faixa_to_string(item["inicio"], item["fim"])
        if (
            escolas[nome_escola]["classificacoes"][classificacao]["por_idade"][
                periodo_escola
            ]
            == 0
        ):
            escolas[nome_escola]["classificacoes"][classificacao]["por_idade"][
                periodo_escola
            ] = []
        escolas[nome_escola]["classificacoes"][classificacao]["por_idade"][
            periodo_escola
        ].append({"faixa": faixa_etaria_infantil, "autorizadas": quantidade})
    elif inicio is None and fim is None and tipo_turma is None and cei_emei is None:
        escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
        total_dietas = quantidade
    elif periodo_escola:
        escolas[nome_escola]["classificacoes"][classificacao]["turma_infantil"][
            periodo_escola
        ] = quantidade
        if periodo_escolar_selecionado:
            escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
            total_dietas = quantidade
    elif periodo_escola is None and tipo_turma == "N/A" and cei_emei == "N/A":
        escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
        total_dietas = quantidade

    return total_dietas


def formatar_periodos_emebs(informacao_escola_por_classificacao, dados_classificacao):
    informacao_escola_por_classificacao["periodos"] = {}
    infantil = dados_classificacao["infantil"]
    if len(infantil) > 0:
        informacao_escola_por_classificacao["periodos"]["infantil"] = [
            {"periodo": p, "autorizadas": q} for p, q in infantil.items()
        ]
    fundamental = dados_classificacao["fundamental"]
    if len(fundamental) > 0:
        informacao_escola_por_classificacao["periodos"]["fundamental"] = [
            {"periodo": p, "autorizadas": q} for p, q in fundamental.items()
        ]


def formatar_periodos_emei_emef_cieja(
    informacao_escola_por_classificacao, dados_classificacao
):
    informacao_escola_por_classificacao["periodos"] = [
        {"periodo": p, "autorizadas": q}
        for p, q in dados_classificacao["periodos"].items()
    ]


def formatar_periodos_cemei(informacao_escola_por_classificacao, dados_classificacao):
    informacao_escola_por_classificacao["periodos"] = {}
    turma_infantil = dados_classificacao["turma_infantil"]
    if len(turma_infantil) > 0:
        informacao_escola_por_classificacao["periodos"]["turma_infantil"] = [
            {"periodo": p, "autorizadas": q} for p, q in turma_infantil.items()
        ]
    por_idade = dados_classificacao["por_idade"]
    if len(por_idade) > 0:
        informacao_escola_por_classificacao["periodos"]["por_idade"] = [
            {"periodo": p, "faixa_etaria": q} for p, q in por_idade.items()
        ]


def formatar_periodos_cei(informacao_escola_por_classificacao, dados_classificacao):
    informacao_escola_por_classificacao["periodos"] = [
        {"periodo": p, "faixa_etaria": q}
        for p, q in dados_classificacao["periodos"].items()
    ]
