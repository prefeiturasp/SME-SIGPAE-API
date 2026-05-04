import logging
import os

import environ
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import exceptions, viewsets
from rest_framework.permissions import AllowAny, DjangoModelPermissionsOrAnonReadOnly
from spyne.application import Application
from spyne.decorator import rpc
from spyne.protocol.soap import Soap11
from spyne.server.django import DjangoApplication
from spyne.service import ServiceBase

from src.eol_servico.utils import EOLException

from ....dados_comuns.models import LogSolicitacoesUsuario
from ...models import SolicitacaoRemessa
from .models import ArqCancelamento, ArqSolicitacaoMOD, SoapResponse, oWsAcessoModel
from .token_auth import TokenAuthentication

logger = logging.getLogger("sigpae.integracao_papa")
env = environ.Env()

API_URL = env.str("API_URL", default=None)
NS = f'{env("DJANGO_XMLNS")}'


class SolicitacaoService(ServiceBase):
    @rpc(oWsAcessoModel, ArqSolicitacaoMOD, _returns=SoapResponse)
    def Solicitacao(ctx, oWsAcessoModel, ArqSolicitacaoMOD):  # noqa C901
        logger.info("Inicia integração envio de solicitação PAPA x SIGPAE:")
        logger.info(str(ArqSolicitacaoMOD))

        try:
            user, token = TokenAuthentication().authenticate(oWsAcessoModel)

        except exceptions.AuthenticationFailed as e:
            logger.info(str(e))
            return SoapResponse(str_status="false", str_menssagem=str(e))

        try:
            solicitacao = ArqSolicitacaoMOD.create()
            solicitacao.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.INICIO_FLUXO_SOLICITACAO,
                usuario=user,
            )
        except ObjectDoesNotExist as e:
            logger.info(str(e))
            return SoapResponse(str_status="false", str_menssagem=str(e))

        except IntegrityError as e:
            logger.info(str(e))
            return SoapResponse(str_status="false", str_menssagem=str(e))

        except Exception as e:
            msg = f"Houve um erro ao salvar a solicitação: {str(e)}"
            logger.info(msg)
            return SoapResponse(str_status="false", str_menssagem=msg)

        logger.info(f"Solicitação {solicitacao.numero_solicitacao} criada com sucesso.")
        return SoapResponse(
            str_status="true", str_menssagem="Solicitação criada com sucesso."
        )

    @rpc(oWsAcessoModel, ArqCancelamento, _returns=SoapResponse)
    def Cancelamento(ctx, oWsAcessoModel, ArqCancelamento):  # noqa C901
        logger.info("Inicia integração envio de cancelamento PAPA x SIGPAE:")
        logger.info(str(ArqCancelamento))

        try:
            user, token = TokenAuthentication().authenticate(oWsAcessoModel)

        except exceptions.AuthenticationFailed as e:
            logger.info(str(e))
            return SoapResponse(str_status="false", str_menssagem=str(e))

        try:
            confirma_cancelamento = ArqCancelamento.cancel(user)
            if confirma_cancelamento:
                status = "canc"
                msg = "Cancelamento realizado com sucesso"
            else:
                status = "pend"
                msg = "Solicitação de cancelamento recebida com sucesso. Pendente de confirmação do distribuidor"
            return SoapResponse(str_status=status, str_menssagem=msg)
        except ObjectDoesNotExist as e:
            logger.info(str(e))
            return SoapResponse(str_status="false", str_menssagem=str(e))

        except IntegrityError as e:
            logger.info(str(e))
            return SoapResponse(str_status="false", str_menssagem=str(e))

        except EOLException as e:
            logger.info(str(e))
            return SoapResponse(str_status="false", str_menssagem=str(e))

        except Exception as e:
            msg = f"Houve um erro ao receber a solicitação de cancelamento: {str(e)}"
            logger.info(msg)
            return SoapResponse(str_status="false", str_menssagem=msg)


def _method_return_string(ctx):
    ctx.out_string[0] = ctx.out_string[0].replace(b"tns:", b"")
    ctx.out_string[0] = ctx.out_string[0].replace(b"soap11env", b"soap")


SolicitacaoService.event_manager.add_listener(
    "method_return_string", _method_return_string
)


soap_app = Application(
    [SolicitacaoService],
    tns=NS,
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

django_soap_application = DjangoApplication(soap_app)
if API_URL:
    django_soap_application.doc.wsdl11.build_interface_document(
        API_URL + "/webserver/solicitacao-remessa/"
    )
    django_soap_application.max_content_length = 50 * 1024 * 1024

solicitacao_application = csrf_exempt(django_soap_application)


class WSDLSolicitacaoServiceViewSet(viewsets.ModelViewSet):
    http_method_names = ["get"]
    permission_classes = [AllowAny, DjangoModelPermissionsOrAnonReadOnly]
    queryset = SolicitacaoRemessa.objects.all()

    def list(self, request, *args, **kwargs):
        CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

        return HttpResponse(
            open(f"{CURRENT_DIR}/wsdl.xml").read(), content_type="text/xml"
        )
