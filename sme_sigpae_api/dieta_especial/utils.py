import re
from collections import defaultdict
from datetime import date, datetime
from itertools import chain
from typing import List

from django.core.exceptions import ValidationError
from django.db.models import CharField, F, IntegerField, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce
from django.http import QueryDict
from django.template.loader import render_to_string
from rest_framework.pagination import PageNumberPagination

from sme_sigpae_api.dieta_especial.models import (
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
)
from sme_sigpae_api.escola.models import Lote
from sme_sigpae_api.escola.utils import faixa_to_string
from sme_sigpae_api.perfil.models import Usuario
from sme_sigpae_api.relatorios.relatorios import relatorio_dieta_especial_conteudo
from sme_sigpae_api.relatorios.utils import html_to_pdf_email_anexo

from ..dados_comuns.constants import TIPO_SOLICITACAO_DIETA
from ..dados_comuns.fluxo_status import DietaEspecialWorkflow
from ..dados_comuns.utils import envia_email_unico, envia_email_unico_com_anexo_inmemory
from ..escola.models import Aluno
from ..paineis_consolidados.models import SolicitacoesCODAE
from .constants import (
    UNIDADES_CEI,
    UNIDADES_CEMEI,
    UNIDADES_EMEBS,
    UNIDADES_EMEI_EMEF_CIEJA,
    UNIDADES_SEM_PERIODOS,
)
from .models import (
    AlergiaIntolerancia,
    ClassificacaoDieta,
    LogDietasAtivasCanceladasAutomaticamente,
    SolicitacaoDietaEspecial,
)


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
    dieta.save()


def _cancelar_dieta_aluno_fora_da_rede(dieta):
    usuario_admin = Usuario.objects.get(pk=1)
    dieta.cancelar_aluno_nao_pertence_rede(user=usuario_admin)
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
                    "to": (
                        [
                            {"uuid": str(s.uuid), "nome": s.nome}
                            for s in subs_new["substitutos"]
                        ]
                        if subs_new["substitutos"]
                        else None
                    ),
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
                    "from": (
                        [
                            {"uuid": sub["uuid"], "nome": sub["nome"]}
                            for sub in substitutos
                        ]
                        if substitutos
                        else None
                    ),
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


def gerar_filtros_relatorio_historico(query_params: QueryDict) -> tuple:
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


def dados_dietas_escolas_cei(filtros: dict, eh_exportacao: bool = False) -> List[dict]:
    queryset = LogQuantidadeDietasAutorizadasCEI.objects.filter(**filtros)
    if eh_exportacao:
        queryset = queryset.filter(faixa_etaria__isnull=False)

    logs_dietas_escolas_cei = (
        queryset.select_related(
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
            dre=F("escola__lote__diretoria_regional__iniciais"),
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
            "dre",
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


def dados_dietas_escolas_comuns(filtros: dict) -> QuerySet[dict]:
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
            dre=F("escola__lote__diretoria_regional__iniciais"),
            nome_classificacao=F("classificacao__nome"),
            quantidade_total=Sum("quantidade"),
            inicio=Value(None, output_field=IntegerField()),
            fim=Value(None, output_field=IntegerField()),
        )
        .values(
            "nome_escola",
            "tipo_unidade",
            "lote",
            "dre",
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


def get_logs_historico_dietas(filtros, eh_exportacao=False) -> list:
    log_escolas_cei = dados_dietas_escolas_cei(filtros, eh_exportacao)
    log_escolas = dados_dietas_escolas_comuns(filtros)
    if eh_exportacao:
        log_escolas = [
            log
            for log in log_escolas
            if log.get("nome_periodo_escolar") is not None
            or log.get("tipo_unidade") in {"CEU GESTAO", "CMCT"}
        ]
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
        if periodo_escola in ["MANHA", "TARDE"]:
            total_dietas = quantidade
            escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
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


def filtra_relatorio_recreio_nas_ferias(query_params: QueryDict) -> QuerySet:
    """
    Retorna um queryset unificado com alunos matriculados e não matriculados que atendem aos critérios do Recreio nas Férias.

    Args:
        query_params (QueryDict): Parâmetros de filtro da requisição.
    Returns:
        QuerySet: Conjunto de solicitações filtradas e ordenadas por escola de destino.
    """
    filtros = gera_filtros_relatorio_recreio_nas_ferias(query_params)

    padrao = filtros.get("padrao", {})
    matriculado = filtros.get("matriculado", {})
    nao_matriculado = filtros.get("nao_matriculado", {})

    filtro_matriculados = Q(
        status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
        tipo_solicitacao="ALTERACAO_UE",
        motivo_alteracao_ue__nome__icontains="recreio",
        **padrao,
        **matriculado,
    )

    filtro_nao_matriculados = Q(
        status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
        tipo_solicitacao="COMUM",
        dieta_para_recreio_ferias=True,
        **padrao,
        **nao_matriculado,
    )

    queryset = SolicitacaoDietaEspecial.objects.filter(
        filtro_matriculados | filtro_nao_matriculados
    ).order_by("escola_destino__nome")

    return queryset


def gera_filtros_relatorio_recreio_nas_ferias(query_params: QueryDict) -> dict:
    """
    Gera os dicionários de filtros com base nos parâmetros da requisição.

    Args:
        query_params (QueryDict): Parâmetros enviados na requisição HTTP.
    Returns:
        dict:  Dicionário com filtros para padrao, matriculado e nao_matriculado.
    """
    filtros = {
        "padrao": {
            "escola_destino__lote__uuid": query_params.get("lote", None),
            "escola_destino__uuid__in": query_params.getlist(
                "unidades_educacionais_selecionadas[]", None
            ),
            "classificacao__id__in": query_params.getlist(
                "classificacoes_selecionadas[]", None
            ),
            "alergias_intolerancias__id__in": query_params.getlist(
                "alergias_intolerancias_selecionadas[]", None
            ),
        },
        "matriculado": {},
        "nao_matriculado": {},
    }

    data_inicio = query_params.get("data_inicio")
    data_fim = query_params.get("data_fim")
    if data_inicio and data_fim:
        data_ini = _parse_data(data_inicio, "data_inicio")
        data_fim = _parse_data(data_fim, "data_fim")
        filtros["matriculado"]["data_inicio__gte"] = data_ini
        filtros["matriculado"]["data_termino__lte"] = data_fim
        filtros["nao_matriculado"]["periodo_recreio_inicio__gte"] = data_ini
        filtros["nao_matriculado"]["periodo_recreio_fim__lte"] = data_fim

    filtros["padrao"] = {
        key: value
        for key, value in filtros["padrao"].items()
        if value not in [None, []]
    }
    return filtros


def _parse_data(valor: str, campo: str) -> datetime:
    """
    Converte string de data no formato 'dd/mm/yyyy' para objeto date
    Args:
        valor (str): string contendo a data.
        campo (str): nome do campo para mensagens de erro.
    Raises:
        ValidationError: se o formato da data for inválido.
    Returns:
        datetime:  objeto date convertido.
    """
    try:
        return datetime.strptime(valor, "%d/%m/%Y").date()
    except ValueError:
        raise ValidationError(
            f"Formato de data inválido para '{campo}'. Use o formato dd/mm/yyyy"
        )


def atualiza_log_protocolo(instance, dados_protocolo_novo):
    alteracoes = {}
    texto_html = ""
    dados_protocolo_atual = {
        "alergias_intolerancias": list(
            instance.alergias_intolerancias.values_list("id", flat=True)
        ),
        "classificacao": instance.classificacao.id,
    }

    alteracoes["Relação por Diagnóstico"] = _compara_alergias(
        atuais=dados_protocolo_atual["alergias_intolerancias"],
        novas=dados_protocolo_novo.get("alergias_intolerancias"),
    )
    alteracoes["Classificação da Dieta"] = _compara_classificacao(
        atual=dados_protocolo_atual["classificacao"],
        nova=dados_protocolo_novo.get("classificacao"),
    )

    if alteracoes:
        texto_html = _registrar_log_alteracoes(alteracoes)
    return texto_html


def update_de_teste(instance, dados_request):
    dados_instancia = {
        "alergias_intolerancias": list(
            instance.alergias_intolerancias.values_list("id", flat=True)
        ),
        "classificacao": (
            int(instance.classificacao.id) if instance.classificacao else None
        ),
        "protocolo_padrao": (
            str(instance.protocolo_padrao.uuid) if instance.protocolo_padrao else None
        ),
        "orientacoes_gerais": instance.orientacoes_gerais,
        "informacoes_adicionais": instance.informacoes_adicionais,
        "registro_funcional_nutricionista": instance.registro_funcional_nutricionista,
        "nome_protocolo": instance.nome_protocolo,
        "substituicoes": list(
            instance.substituicaoalimento_set.values(
                "alimento", "tipo", "alimentos_substitutos__uuid"
            )
        ),
    }

    dados_request["classificacao"] = int(dados_request["classificacao"])
    alteracoes = {}
    texto = ""
    campos_para_comparar = [
        "classificacao",
        "protocolo_padrao",
        "orientacoes_gerais",
        "informacoes_adicionais",
        "registro_funcional_nutricionista",
        "nome_protocolo",
    ]

    for campo in campos_para_comparar:
        valor_atual = dados_instancia.get(campo)
        valor_novo = dados_request.get(campo)

        if valor_atual != valor_novo:
            alteracoes[campo] = {"de": valor_atual, "para": valor_novo}

    alergias_atuais = set(dados_instancia["alergias_intolerancias"])
    alergias_novas = set(map(int, dados_request["alergias_intolerancias"]))
    alteracoes["alergias_intolerancias"] = _compara_alergias(
        alergias_atuais, alergias_novas
    )

    alteracoes["substituicoes"] = _comparar_substituicoes(
        dados_instancia["substituicoes"], dados_request["substituicoes"]
    )

    if alteracoes:
        texto = _registrar_log_alteracoes(alteracoes)

    return texto


def _compara_alergias(atuais, novas):
    if novas:
        ids_alergias_atuais = set(atuais)
        ids_alergias_novas = set(map(int, novas))
        if ids_alergias_atuais != ids_alergias_novas:
            nome_atuais = (
                AlergiaIntolerancia.objects.filter(id__in=list(ids_alergias_atuais))
                .values_list("descricao", flat=True)
                .order_by("descricao")
            )
            nome_novas = (
                AlergiaIntolerancia.objects.filter(id__in=list(ids_alergias_novas))
                .values_list("descricao", flat=True)
                .order_by("descricao")
            )
            return {"de": ", ".join(nome_atuais), "para": ", ".join(nome_novas)}
    return None


def _compara_classificacao(atual, nova):
    if nova:
        id_classificacao_atual = int(atual)
        id_classificacao_nova = int(nova)
        if id_classificacao_atual != id_classificacao_nova:
            classificacao_atual = ClassificacaoDieta.objects.get(
                id=id_classificacao_atual
            )
            classificacao_nova = ClassificacaoDieta.objects.get(
                id=id_classificacao_nova
            )
            return {"de": classificacao_atual.nome, "para": classificacao_nova.nome}
    return None


def normalizar_substituicao(sub):
    if "alimentos_substitutos__uuid" in sub:
        substituto = str(sub["alimentos_substitutos__uuid"])
    elif "substitutos" in sub:
        substituto = sub["substitutos"][0]

    return {
        "alimento": str(sub["alimento"]),
        "tipo": sub["tipo"],
        "substitutos": substituto,
    }


def _comparar_substituicoes(substituicoes_atuais, substituicoes_novas):
    atuais_normalizadas = [normalizar_substituicao(s) for s in substituicoes_atuais]
    novas_normalizadas = [normalizar_substituicao(s) for s in substituicoes_novas]

    alteracoes = []

    for sub in atuais_normalizadas:
        if sub not in novas_normalizadas:
            alteracoes.append({"tipo": "ITEM EXCLUÍDO", "dados": sub})

    for sub in novas_normalizadas:
        if sub not in atuais_normalizadas:
            alteracoes.append({"tipo": "ITEM INCLUÍDO", "dados": sub})

    for sub_atual in atuais_normalizadas:
        for sub_novo in novas_normalizadas:
            if sub_atual["alimento"] == sub_novo["alimento"] and sub_atual != sub_novo:
                alteracoes.append({"tipo": "ITEM ALTERADO DE", "dados": sub_atual})
                alteracoes.append({"tipo": "ITEM ALTERADO PARA", "dados": sub_novo})

    return alteracoes if alteracoes else None


def _registrar_log_alteracoes(alteracoes):
    processed_data = {}

    for campo, mudanca in alteracoes.items():
        if campo != "substituicoes":
            processed_data[campo] = {"de": mudanca["de"], "para": mudanca["para"]}

    if "substituicoes" in alteracoes:
        processed_data["substituicoes"] = [
            {
                "tipo": sub["tipo"],
                "dados": {
                    "alimento": sub["dados"]["alimento"],
                    "tipo": sub["dados"]["tipo"],
                    "substitutos": sub["dados"]["substitutos"],
                },
            }
            for sub in alteracoes["substituicoes"]
        ]

    html_content = render_to_string(
        "dieta_especial/historico_atualizacao_dieta.html",
        {"alteracoes": processed_data},
    )
    with open(
        "/home/priscyla/spassu/pmsp/repositorios/SME-SIGPAE-API/log_protocolo.html",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(html_content)
    return
