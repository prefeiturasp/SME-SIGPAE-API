import datetime
from typing import Iterable

import environ
from django.template.loader import render_to_string

from ..perfil.models import Usuario
from .models import LogSolicitacoesUsuario, Notificacao
from .tasks import envia_email_em_massa_task

env = environ.Env()
base_url = f'{env("REACT_APP_URL")}'


def _partes_interessadas_ue_cancela(obj):
    email_query_set_terceirizada = (
        obj.escola.lote.terceirizada.emails_terceirizadas.filter(
            modulo__nome="Gestão de Alimentação"
        ).values_list("email", flat=True)
    )
    return list(email_query_set_terceirizada)


def _preenche_template_e_envia_email_ue_cancela_parcialmente(
    obj, assunto, titulo, id_externo, criado_em, partes_interessadas
):
    url = f'{env("REACT_APP_URL")}/{obj.path}'
    template = "fluxo_ue_cancela_parcialmente.html"
    dados_template = {
        "titulo": titulo,
        "tipo_solicitacao": obj.DESCRICAO,
        "id_externo": id_externo,
        "criado_em": criado_em,
        "nome_ue": obj.escola.nome,
        "url": url,
        "nome_dre": obj.escola.diretoria_regional.nome,
        "nome_lote": obj.escola.lote.nome,
    }
    html = render_to_string(template, dados_template)
    envia_email_em_massa_task.delay(
        assunto=assunto,
        corpo="",
        emails=partes_interessadas,
        template="fluxo_ue_cancela.html",
        dados_template=dados_template,
        html=html,
    )


def enviar_email_ue_cancelar_pedido_parcialmente(obj):
    # envia email para partes interessadas
    id_externo = "#" + obj.id_externo
    assunto = "[SIGPAE] Status de solicitação - " + id_externo
    titulo = f"Solicitação de {obj.tipo} Parcialmente Cancelada"
    momento_cancelamento = datetime.datetime.now()
    criado_em = momento_cancelamento.strftime("%d/%m/%Y - %H:%M")
    _preenche_template_e_envia_email_ue_cancela_parcialmente(
        obj,
        assunto,
        titulo,
        id_externo,
        criado_em,
        _partes_interessadas_ue_cancela(obj),
    )


def _partes_interessadas_codae_atualiza_protocolo(obj):
    email_query_set_terceirizada = (
        obj.aluno.escola.lote.terceirizada.emails_terceirizadas.filter(
            modulo__nome="Dieta Especial"
        ).values_list("email", flat=True)
    )
    email_contato_ecola = obj.aluno.escola.contato.email
    return list(email_query_set_terceirizada) + [email_contato_ecola]


def _preenche_template_e_envia_email_codae_atualiza_protocolo(
    obj, assunto, titulo, criado_em, partes_interessadas
):
    url = f'{env("REACT_APP_URL")}/dieta-especial/relatorio?uuid={obj.uuid}'
    template = "fluxo_codae_atualiza_dieta_autorizada.html"
    dados_template = {
        "titulo": titulo,
        "criado_em": criado_em,
        "nome_aluno": obj.aluno.nome,
        "url": url,
    }
    html = render_to_string(template, dados_template)
    envia_email_em_massa_task.delay(
        assunto=assunto,
        corpo="",
        emails=partes_interessadas,
        template="fluxo_codae_atualiza_dieta_autorizada.html",
        dados_template=dados_template,
        html=html,
    )


def enviar_email_codae_atualiza_protocolo(obj):
    assunto = "Protocolo Padrão de Dieta Atualizado"
    titulo = "Protocolo Padrão de Dieta Atualizado"
    momento_atualização = datetime.datetime.now()
    criado_em = momento_atualização.strftime("%d/%m/%Y - %H:%M")
    _preenche_template_e_envia_email_codae_atualiza_protocolo(
        obj,
        assunto,
        titulo,
        criado_em,
        _partes_interessadas_codae_atualiza_protocolo(obj),
    )


class PartesInteressadasService:
    @staticmethod
    def usuarios_por_perfis(nomes_perfis, somente_email=False):
        if isinstance(nomes_perfis, str):
            nomes_perfis = [nomes_perfis]

        queryset = Usuario.objects.filter(
            vinculos__perfil__nome__in=nomes_perfis,
            vinculos__ativo=True,
            vinculos__data_inicial__isnull=False,
            vinculos__data_final__isnull=True,
        )

        if somente_email:
            return [usuario.email for usuario in queryset]

        return [usuario for usuario in queryset]

    @staticmethod
    def usuarios_vinculados_a_empresa_do_objeto(objeto, somente_email=False):
        if objeto.empresa:
            vinculos = objeto.empresa.vinculos.filter(ativo=True)

            if somente_email:
                return [vinculo.usuario.email for vinculo in vinculos]

            return [vinculo.usuario for vinculo in vinculos]

        return []


class EmailENotificacaoService:
    @staticmethod
    def enviar_email(
        titulo: str,
        assunto: str,
        template: str,
        contexto_template: "dict[str, any]",
        destinatarios: "list[str]",
        esconder_email_tarja_inferior: bool = False,
    ):
        contexto = {
            **contexto_template,
            "titulo": titulo,
            "hidden_email": esconder_email_tarja_inferior,
        }

        html_email = render_to_string(template_name=template, context=contexto)

        envia_email_em_massa_task.delay(
            assunto=assunto, emails=destinatarios, corpo="", html=html_email
        )

    @staticmethod
    def enviar_notificacao(
        template: str,
        contexto_template: "dict[str, any]",
        titulo_notificacao: str,
        tipo_notificacao: str,
        categoria_notificacao: str,
        link_acesse_aqui: str,
        usuarios: Iterable[Usuario],
        requisicao=None,
        solicitacao_alteracao=None,
        guia=None,
        cronograma=None,
    ):
        descricao_notificacao = render_to_string(
            template_name=template,
            context=contexto_template,
        )

        if usuarios:
            for usuario in usuarios:
                Notificacao.notificar(
                    tipo=tipo_notificacao,
                    categoria=categoria_notificacao,
                    titulo=titulo_notificacao,
                    descricao=descricao_notificacao,
                    usuario=usuario,
                    link=link_acesse_aqui,
                    requisicao=requisicao,
                    solicitacao_alteracao=solicitacao_alteracao,
                    guia=guia,
                    cronograma=cronograma,
                )


class ServiceMapeamentoLogsLinhaDoTempo:
    STATUS_POR_TIPO_SOLICITACAO = {
        LogSolicitacoesUsuario.DOCUMENTO_DE_RECEBIMENTO: {
            "Documento enviado para análise": "Enviado para Análise",
            "Documento correção realizada": "Enviado para Análise",
            "Documento enviado para correção": "Enviado para Correção",
            "Documento aprovado": "Aprovado",
        },
        LogSolicitacoesUsuario.LAYOUT_DE_EMBALAGEM: {
            "Layout enviado para análise": "Enviado para Análise",
            "Layout solicitado correção": "Solicitado Correção",
            "Layout correção realizada": "Enviado para Análise",
            "Layout atualizado": "Enviado para Análise",
            "Layout aprovado": "Aprovado",
        },
    }

    @classmethod
    def get_status_map(cls, tipo_solicitacao):
        return cls.STATUS_POR_TIPO_SOLICITACAO.get(tipo_solicitacao, {})
