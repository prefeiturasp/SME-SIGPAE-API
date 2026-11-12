import logging

from django.template.loader import render_to_string

from src.dados_comuns.constants import StringsVerboseNameModels
from src.dados_comuns.fluxo_status import FichaDeRecebimentoWorkflow
from src.dados_comuns.services import base_url
from src.dados_comuns.tasks import envia_email_unico_task
from src.terceirizada.models import Terceirizada

logger = logging.getLogger(__name__)


class EmailAssinaturaTermoRecebimentoService:
    """Envio do e-mail de assinatura de um Termo de Recebimento aos Fiscais
    do Contrato.

    O nome do termo é parametrizado para que o mesmo template e fluxo de
    envio atendam a outros tipos de termo de recebimento.
    """

    @staticmethod
    def _fiscais_destinatarios(termo):
        """Fiscais distintos do termo, preservando a ordem do cadastro."""
        fiscais = {}
        for fiscal in (termo.fiscal_1, termo.fiscal_2, termo.fiscal_3):
            fiscais.setdefault(fiscal.pk, fiscal)
        return list(fiscais.values())

    @staticmethod
    def _url_frontend(caminho=""):
        """URL absoluta do frontend, garantindo o protocolo para que os
        clientes de e-mail reconheçam o link."""
        if base_url.startswith("http"):
            return f"{base_url}{caminho}"
        protocolo = "http://" if ":" in base_url else "https://"
        return f"{protocolo}{base_url}{caminho}"

    @classmethod
    def enviar(cls, termo, nome_termo):
        """Agenda um e-mail individual para cada fiscal distinto com e-mail
        cadastrado. Fiscais sem e-mail são registrados em log e ignorados."""
        assunto = f"Assinatura do {nome_termo}"
        url_sigpae = cls._url_frontend()
        url_termo = cls._url_frontend(
            f"/pos-recebimento/detalhar-termo-recebimento-provisorio?uuid={termo.uuid}"
        )

        for fiscal in cls._fiscais_destinatarios(termo):
            if not fiscal.email:
                logger.warning(
                    "Fiscal %s sem e-mail cadastrado: e-mail de assinatura do "
                    "termo %s não enviado.",
                    fiscal.uuid,
                    termo.uuid,
                )
                continue

            html = render_to_string(
                template_name="pos_recebimento_email_assinatura_termo_recebimento.html",
                context={
                    "titulo": nome_termo,
                    "nome_termo": nome_termo,
                    "nome_destinatario": fiscal.nome,
                    "url_sigpae": url_sigpae,
                    "url_termo": url_termo,
                },
            )
            envia_email_unico_task.delay(
                assunto=assunto, corpo="", email=fiscal.email, html=html
            )


class TermoRecebimentoProvisorioService:
    """Regra de negócio do Pós-Recebimento referente ao modelo novo.

    As listagens de empresas, contratos, cronogramas e fiscais foram
    movidas para os services/viewsets dos seus respectivos módulos
    (terceirizada, pre_recebimento e perfil). Aqui permanece apenas a
    regra utilizada na criação do Termo de Recebimento Provisório.
    """

    @staticmethod
    def empresa_tem_ficha_assinada(empresa):
        """Verifica se uma empresa possui ficha de recebimento assinada pela CODAE."""
        return Terceirizada.objects.filter(
            pk=empresa.pk,
            cronograma__etapas__ficha_recebimento__status=(
                FichaDeRecebimentoWorkflow.ASSINADA
            ),
        ).exists()

    @staticmethod
    def envia_email_assinatura_fiscais(termo):
        """Envia aos Fiscais do Contrato o e-mail de assinatura do termo."""
        EmailAssinaturaTermoRecebimentoService.enviar(
            termo,
            StringsVerboseNameModels.TERMO_DE_RECEBIMENTO_PROVISORIO.value,
        )
