from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Count, F, FloatField, Max, Q, Sum
from django.db.utils import DataError
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_406_NOT_ACCEPTABLE,
)
from xworkflows.base import InvalidTransitionError

from sme_sigpae_api.dados_comuns.fluxo_status import (
    GuiaRemessaWorkFlow,
    NotificacaoOcorrenciaWorkflow,
    SolicitacaoRemessaWorkFlow,
)
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.dados_comuns.parser_xml import ListXMLParser
from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoParaCriarNotificacaoDeGuiasComOcorrencias,
    PermissaoParaListarEntregas,
    PermissaoParaVisualizarGuiasComOcorrencias,
    UsuarioCodaeDilog,
    UsuarioCODAEGabinete,
    UsuarioDilog,
    UsuarioDilogOuDistribuidor,
    UsuarioDilogOuDistribuidorOuEscolaAbastecimento,
    UsuarioDistribuidor,
    UsuarioEscolaAbastecimento,
    ViewSetActionPermissionMixin,
)
from sme_sigpae_api.eol_servico.utils import EOLPapaService
from sme_sigpae_api.logistica.api.serializers.serializer_create import (
    ConferenciaComOcorrenciaCreateSerializer,
    ConferenciaDaGuiaCreateSerializer,
    InsucessoDeEntregaGuiaCreateSerializer,
    NotificacaoOcorrenciasCreateSerializer,
    NotificacaoOcorrenciasUpdateRascunhoSerializer,
    NotificacaoOcorrenciasUpdateSerializer,
    PrevisoesContratuaisDaNotificacaoUpdateSerializer,
    SolicitacaoDeAlteracaoRequisicaoCreateSerializer,
    SolicitacaoRemessaCreateSerializer,
)
from sme_sigpae_api.logistica.api.serializers.serializers import (  # noqa
    AlimentoDaGuiaDaRemessaSerializer,
    AlimentoDaGuiaDaRemessaSimplesSerializer,
    ConferenciaComOcorrenciaSerializer,
    ConferenciaDaGuiaSerializer,
    ConferenciaIndividualPorAlimentoSerializer,
    GuiaDaRemessaComDistribuidorSerializer,
    GuiaDaRemessaComOcorrenciasSerializer,
    GuiaDaRemessaCompletaSerializer,
    GuiaDaRemessaComStatusRequisicaoSerializer,
    GuiaDaRemessaLookUpSerializer,
    GuiaDaRemessaSerializer,
    GuiaDaRemessaSimplesSerializer,
    InfoUnidadesSimplesDaGuiaSerializer,
    InsucessoDeEntregaGuiaSerializer,
    NotificacaoOcorrenciasGuiaDetalheSerializer,
    NotificacaoOcorrenciasGuiaSerializer,
    NotificacaoOcorrenciasGuiaSimplesSerializer,
    SolicitacaoDeAlteracaoSerializer,
    SolicitacaoDeAlteracaoSimplesSerializer,
    SolicitacaoRemessaContagemGuiasSerializer,
    SolicitacaoRemessaLookUpSerializer,
    SolicitacaoRemessaSerializer,
    SolicitacaoRemessaSimplesSerializer,
    XmlParserSolicitacaoSerializer,
)
from sme_sigpae_api.logistica.models import (
    Alimento,
    ConferenciaGuia,
    Embalagem,
)
from sme_sigpae_api.logistica.models import Guia as GuiasDasRequisicoes
from sme_sigpae_api.logistica.models import (
    NotificacaoOcorrenciasGuia,
    SolicitacaoDeAlteracaoRequisicao,
    SolicitacaoRemessa,
)
from sme_sigpae_api.logistica.services import (
    arquiva_guias,
    confirma_cancelamento,
    confirma_guias,
    desarquiva_guias,
    envia_email_e_notificacao_confirmacao_guias,
)

from ...dados_comuns.constants import COGESTOR_DRE
from ...escola.models import DiretoriaRegional, Escola
from ...relatorios.relatorios import relatorio_guia_de_remessa
from ..models.guia import InsucessoEntregaGuia
from ..tasks import gera_pdf_async, gera_xlsx_async, gera_xlsx_entregas_async
from ..utils import GuiaPagination, RequisicaoPagination, SolicitacaoAlteracaoPagination
from .filters import (
    GuiaFilter,
    NotificacaoFilter,
    SolicitacaoAlteracaoFilter,
    SolicitacaoFilter,
)
from .helpers import valida_guia_conferencia, valida_guia_insucesso
from .validators import eh_true_ou_false

STR_XML_BODY = "{http://schemas.xmlsoap.org/soap/envelope/}Body"
STR_ARQUIVO_SOLICITACAO = "ArqSolicitacaoMOD"
STR_ARQUIVO_CANCELAMENTO = "ArqCancelamento"


class SolicitacaoEnvioEmMassaModelViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    http_method_names = ["post"]
    queryset = SolicitacaoRemessa.objects.all()
    serializer_class = SolicitacaoRemessaCreateSerializer
    permission_classes = [UsuarioDilog]
    pagination_class = None

    @action(
        detail=False,
        permission_classes=(UsuarioDilog,),
        methods=["post"],
        url_path="envia-grade",
    )
    def inicia_fluxo_solicitacoes_em_massa(self, request):
        usuario = request.user
        solicitacoes = request.data.get("solicitacoes", [])
        solicitacoes = SolicitacaoRemessa.objects.filter(
            uuid__in=solicitacoes, status=SolicitacaoRemessaWorkFlow.AGUARDANDO_ENVIO
        )
        for solicitacao in solicitacoes:
            try:
                solicitacao.inicia_fluxo(user=usuario)
            except InvalidTransitionError as e:
                return Response(
                    dict(detail=f"Erro de transição de estado: {e}"),
                    status=HTTP_400_BAD_REQUEST,
                )
        serializer = SolicitacaoRemessaSerializer(solicitacoes, many=True)
        return Response(serializer.data)


class SolicitacaoCancelamentoModelViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    http_method_names = [
        "post",
    ]
    queryset = SolicitacaoRemessa.objects.all()
    serializer_class = XmlParserSolicitacaoSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (ListXMLParser,)
    pagination_class = None

    def cancela_guias(self, num_solicitacao, guias, usuario):
        # Cancela as guias recebidas no cancelamento;
        # Se as guias da solicitação forem todas as guias recebidas, cancela também a solicitação;
        # E se todas as guias de uma solicitação encontram se canceladas, cancela também a solicitação;

        if isinstance(guias, list):
            guias_payload = [x["StrNumGui"] for x in guias]
        else:
            guias_payload = [x["StrNumGui"] for x in guias.values()]

        solicitacao = SolicitacaoRemessa.objects.get(numero_solicitacao=num_solicitacao)
        solicitacao.guias.filter(numero_guia__in=guias_payload).update(
            status=GuiaRemessaWorkFlow.CANCELADA
        )

        guias_existentes = list(solicitacao.guias.values_list("numero_guia", flat=True))
        existe_guia_nao_cancelada = solicitacao.guias.exclude(
            status=GuiaRemessaWorkFlow.CANCELADA
        ).exists()

        if set(guias_existentes) == set(guias_payload) or not existe_guia_nao_cancelada:
            solicitacao.cancela_solicitacao(user=usuario)
        else:
            solicitacao.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.PAPA_CANCELA_SOLICITACAO,
                usuario=usuario,
                justificativa=f"Guias canceladas: {guias_payload}",
            )

    def create(self, request, *args, **kwargs):  # noqa: C901
        remove_dirt = request.data.get(f"{STR_XML_BODY}")
        json_cancelamento = remove_dirt.get(f"{STR_ARQUIVO_CANCELAMENTO}")
        usuario = request.user

        if json_cancelamento:
            try:
                num_solicitacao = json_cancelamento["StrNumSol"]
                guias = json_cancelamento["guias"]
                self.cancela_guias(num_solicitacao, guias, usuario)

                return Response(
                    dict(detail="Cancelamento realizado com sucesso", status=True),
                    status=HTTP_200_OK,
                )
            except InvalidTransitionError as e:
                return Response(
                    dict(detail=f"Erro de transição de estado: {e}", status=False),
                    status=HTTP_406_NOT_ACCEPTABLE,
                )
            except ObjectDoesNotExist as e:
                return Response(
                    dict(detail=f"Erro de transição de estado: {e}", status=False),
                    status=HTTP_406_NOT_ACCEPTABLE,
                )


class SolicitacaoModelViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    http_method_names = ["get", "post", "patch"]
    serializer_class = SolicitacaoRemessaCreateSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = RequisicaoPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = SolicitacaoFilter

    def get_serializer_class(self):
        if self.action == "create":
            return SolicitacaoRemessaCreateSerializer
        if self.action == "list":
            return SolicitacaoRemessaLookUpSerializer
        return SolicitacaoRemessaSerializer

    def get_permissions(self):
        if self.action in ["list"]:
            self.permission_classes = [
                UsuarioDilogOuDistribuidor | UsuarioCODAEGabinete
            ]
        return super(SolicitacaoModelViewSet, self).get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.eh_distribuidor:
            return SolicitacaoRemessa.objects.filter(
                distribuidor=user.vinculo_atual.instituicao
            )
        return SolicitacaoRemessa.objects.all()

    def get_paginated_response(self, data, num_enviadas=None, num_confirmadas=None):
        assert self.paginator is not None  # nosec
        return self.paginator.get_paginated_response(
            data, num_enviadas, num_confirmadas
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.order_by("-guias__data_entrega").distinct()

        num_enviadas = queryset.filter(
            status=SolicitacaoRemessaWorkFlow.DILOG_ENVIA
        ).count()
        num_confirmadas = queryset.filter(
            status=SolicitacaoRemessaWorkFlow.DISTRIBUIDOR_CONFIRMA
        ).count()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(
                serializer.data,
                num_enviadas=num_enviadas,
                num_confirmadas=num_confirmadas,
            )
            return response

        serializer = self.get_serializer(queryset, many=True)
        serializer.data["teste"] = 1
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        remove_dirt = request.data.get(f"{STR_XML_BODY}")
        json_data = remove_dirt.get(f"{STR_ARQUIVO_SOLICITACAO}")
        usuario = request.user

        if json_data:
            try:
                instance = SolicitacaoRemessaCreateSerializer().create(
                    validated_data=json_data
                )
                instance.salvar_log_transicao(
                    status_evento=LogSolicitacoesUsuario.INICIO_FLUXO_SOLICITACAO,
                    usuario=usuario,
                )

                return Response(
                    dict(detail="Criado com sucesso", status=True),
                    status=HTTP_201_CREATED,
                )
            except DataError as e:
                return Response(
                    dict(detail=f"Erro de transição de estado: {e}", status=False),
                    status=HTTP_406_NOT_ACCEPTABLE,
                )

    @action(
        detail=False,
        permission_classes=(UsuarioDistribuidor,),
        methods=["post"],
        url_path="confirmar-cancelamento",
    )
    def confirma_cancelamento_guias_e_requisicoes(self, request):
        numero_requisicao = request.data.get("numero_requisicao", "")
        guias = request.data.get("guias", [])

        if not numero_requisicao:
            return Response(
                "É necessario informar o número da requisição ao qual a(s) guia(s) pertece(m).",
                status=HTTP_406_NOT_ACCEPTABLE,
            )
        if not guias:
            return Response(
                "É necessario informar o número das guias para confirmação do cancelamento.",
                status=HTTP_406_NOT_ACCEPTABLE,
            )

        confirma_cancelamento(
            numero_requisicao=numero_requisicao, guias=guias, user=self.request.user
        )

        return Response("Cancelamento realizado com sucesso.", status=HTTP_200_OK)

    @action(
        detail=False,
        permission_classes=(UsuarioDilog,),
        methods=["post"],
        url_path="arquivar",
    )
    def arquiva_guias_e_requisicoes(self, request):
        numero_requisicao = request.data.get("numero_requisicao", "")
        guias = request.data.get("guias", [])

        if not numero_requisicao:
            return Response(
                "É necessario informar o número da requisição ao qual a(s) guia(s) pertece(m).",
                status=HTTP_406_NOT_ACCEPTABLE,
            )
        if not guias:
            return Response(
                "É necessario informar o número das guias para arquivamento.",
                status=HTTP_406_NOT_ACCEPTABLE,
            )

        arquiva_guias(numero_requisicao=numero_requisicao, guias=guias)

        return Response("Arquivamento realizado com sucesso.", status=HTTP_200_OK)

    @action(
        detail=False,
        permission_classes=(UsuarioDilog,),
        methods=["post"],
        url_path="desarquivar",
    )
    def desarquiva_guias_e_requisicoes(self, request):
        numero_requisicao = request.data.get("numero_requisicao", "")
        guias = request.data.get("guias", [])

        if not numero_requisicao:
            return Response(
                "É necessario informar o número da requisição ao qual a(s) guia(s) pertece(m).",
                status=HTTP_406_NOT_ACCEPTABLE,
            )
        if not guias:
            return Response(
                "É necessario informar o número das guias para desarquivamento.",
                status=HTTP_406_NOT_ACCEPTABLE,
            )

        desarquiva_guias(numero_requisicao=numero_requisicao, guias=guias)

        return Response("Desarquivamento realizado com sucesso.", status=HTTP_200_OK)

    @action(detail=False, methods=["GET"], url_path="lista-numeros")
    def lista_numeros(self, request):
        queryset = self.get_queryset().filter(
            status__in=[SolicitacaoRemessaWorkFlow.AGUARDANDO_ENVIO]
        )
        response = {
            "results": SolicitacaoRemessaSimplesSerializer(queryset, many=True).data
        }
        return Response(response)

    @action(
        detail=False,
        permission_classes=(UsuarioDilog,),  # noqa C901
        methods=["GET"],
        url_path="lista-requisicoes-para-envio",
    )
    def lista_requisicoes_para_envio(self, request):
        queryset = self.get_queryset().filter(
            status=SolicitacaoRemessaWorkFlow.AGUARDANDO_ENVIO
        )
        numero_requisicao = request.query_params.get("numero_requisicao", None)
        nome_distribuidor = request.query_params.get("nome_distribuidor", None)
        data_inicio = request.query_params.get("data_inicio", None)
        data_fim = request.query_params.get("data_fim", None)

        if numero_requisicao:
            queryset = queryset.filter(numero_solicitacao=numero_requisicao)
        if nome_distribuidor:
            queryset = queryset.filter(
                distribuidor__nome_fantasia__icontains=nome_distribuidor
            )
        if data_inicio and data_fim:
            queryset = queryset.filter(
                guias__data_entrega__range=[data_inicio, data_fim]
            ).distinct()
        if data_inicio and not data_fim:
            queryset = queryset.filter(guias__data_entrega__gte=data_inicio).distinct()
        if data_fim and not data_inicio:
            queryset = queryset.filter(guias__data_entrega__lte=data_fim).distinct()

        response = {
            "results": SolicitacaoRemessaLookUpSerializer(queryset, many=True).data
        }
        return Response(response)

    @action(
        detail=False,
        permission_classes=[PermissaoParaListarEntregas],
        methods=["GET"],
        url_path="lista-requisicoes-confirmadas",
    )
    def lista_requisicoes_confirmadas(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(
                status=SolicitacaoRemessaWorkFlow.DISTRIBUIDOR_CONFIRMA
            )
        )

        if self.request.user.eh_distribuidor:
            queryset = queryset.filter(
                distribuidor=self.request.user.vinculo_atual.instituicao
            )

        if isinstance(self.request.user.vinculo_atual.instituicao, DiretoriaRegional):
            lista_ids_escolas = (
                self.request.user.vinculo_atual.instituicao.escolas.values_list(
                    "id", flat="True"
                )
            )
            queryset = queryset.filter(
                guias__escola__id__in=lista_ids_escolas
            ).distinct()

        queryset = (
            queryset.annotate(
                qtd_guias=Count("guias"),
                distribuidor_nome=F("distribuidor__razao_social"),
                data_entrega=Max("guias__data_entrega"),
                guias_pendentes=Count(
                    "guias__status",
                    filter=Q(guias__status=GuiaRemessaWorkFlow.PENDENTE_DE_CONFERENCIA),
                ),
                guias_insucesso=Count(
                    "guias__status",
                    filter=Q(
                        guias__status=GuiaRemessaWorkFlow.DISTRIBUIDOR_REGISTRA_INSUCESSO
                    ),
                    distinct=True,
                ),
                guias_recebidas=Count(
                    "guias__status",
                    filter=Q(guias__status=GuiaRemessaWorkFlow.RECEBIDA),
                ),
                guias_parciais=Count(
                    "guias__status",
                    filter=Q(guias__status=GuiaRemessaWorkFlow.RECEBIMENTO_PARCIAL),
                ),
                guias_nao_recebidas=Count(
                    "guias__status",
                    filter=Q(guias__status=GuiaRemessaWorkFlow.NAO_RECEBIDA),
                ),
                guias_reposicao_parcial=Count(
                    "guias__status",
                    filter=Q(guias__status=GuiaRemessaWorkFlow.REPOSICAO_PARCIAL),
                ),
                guias_reposicao_total=Count(
                    "guias__status",
                    filter=Q(guias__status=GuiaRemessaWorkFlow.REPOSICAO_TOTAL),
                ),
            )
            .order_by("guias__data_entrega")
            .distinct()
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SolicitacaoRemessaContagemGuiasSerializer(page, many=True)
            response = self.get_paginated_response(
                serializer.data, num_enviadas=0, num_confirmadas=queryset.count()
            )
            return response

        response = {
            "results": SolicitacaoRemessaContagemGuiasSerializer(
                queryset, many=True
            ).data
        }
        return Response(response)

    @action(
        detail=True,
        permission_classes=(UsuarioDilog,),
        methods=["patch"],
        url_path="envia-solicitacao",
    )
    def incia_fluxo_solicitacao(self, request, uuid=None):
        solicitacao = SolicitacaoRemessa.objects.get(
            uuid=uuid, status=SolicitacaoRemessaWorkFlow.AGUARDANDO_ENVIO
        )
        usuario = request.user

        try:
            solicitacao.inicia_fluxo(
                user=usuario,
            )
            serializer = SolicitacaoRemessaSerializer(solicitacao)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )

    @transaction.atomic
    @action(
        detail=True,
        permission_classes=(UsuarioDistribuidor,),
        methods=["patch"],
        url_path="distribuidor-confirma",
    )
    def distribuidor_confirma(self, request, uuid=None):
        solicitacao = SolicitacaoRemessa.objects.get(uuid=uuid)
        usuario = request.user

        try:
            confirma_guias(solicitacao=solicitacao, user=usuario)
            solicitacao.empresa_atende(
                user=usuario,
            )
            serializer = SolicitacaoRemessaSerializer(solicitacao)
            if settings.DEBUG is not True:
                EOLPapaService.confirmacao_de_envio(
                    cnpj=solicitacao.cnpj,
                    numero_solicitacao=solicitacao.numero_solicitacao,
                    sequencia_envio=solicitacao.sequencia_envio,
                )
                envia_email_e_notificacao_confirmacao_guias(solicitacao)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )

    @transaction.atomic  # noqa: C901
    @action(
        detail=False,
        permission_classes=(UsuarioDistribuidor,),
        methods=["patch"],
        url_path="distribuidor-confirma-todos",
    )
    def distribuidor_confirma_todos(self, request):
        queryset = self.get_queryset()
        solicitacoes = queryset.filter(status=SolicitacaoRemessaWorkFlow.DILOG_ENVIA)
        usuario = request.user

        try:
            for solicitacao in solicitacoes:
                confirma_guias(solicitacao, usuario)
                solicitacao.empresa_atende(
                    user=usuario,
                )
                if settings.DEBUG is not True:
                    EOLPapaService.confirmacao_de_envio(
                        cnpj=solicitacao.cnpj,
                        numero_solicitacao=solicitacao.numero_solicitacao,
                        sequencia_envio=solicitacao.sequencia_envio,
                    )
                    envia_email_e_notificacao_confirmacao_guias(solicitacao)
            return Response(status=HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=[UsuarioDilogOuDistribuidor],
        methods=["get"],
        url_path="consolidado-alimentos",
    )
    def consolidado_alimentos(self, request, uuid=None):
        solicitacao = self.get_queryset().filter(uuid=uuid).first()
        queryset = Embalagem.objects.filter(alimento__guia__solicitacao=solicitacao)

        if solicitacao is None:
            return Response("Solicitação inexistente.", status=HTTP_400_BAD_REQUEST)

        response_data = []

        capacidade_total_alimentos = (
            queryset.values(nome_alimento=F("alimento__nome_alimento"))
            .annotate(
                peso_total=Sum(
                    F("capacidade_embalagem") * F("qtd_volume"),
                    output_field=FloatField(),
                )
            )
            .order_by()
        )

        capacidade_total_embalagens = (
            queryset.values(
                "descricao_embalagem",
                "unidade_medida",
                "capacidade_embalagem",
                "tipo_embalagem",
                nome_alimento=F("alimento__nome_alimento"),
            )
            .annotate(
                peso_total_embalagem=Sum(
                    F("capacidade_embalagem") * F("qtd_volume"),
                    output_field=FloatField(),
                ),
                qtd_volume=Sum("qtd_volume"),
            )
            .order_by()
        )

        for data in capacidade_total_alimentos:
            data["total_embalagens"] = []
            response_data.append(data)

        for data in capacidade_total_embalagens:
            nome_alimento = data.pop("nome_alimento")
            index = next(
                (
                    index
                    for (index, item) in enumerate(response_data)
                    if item["nome_alimento"] == nome_alimento
                )
            )  # noqa E501
            response_data[index]["total_embalagens"].append(data)

        return Response(response_data, status=HTTP_200_OK)

    @action(
        detail=True,
        methods=["GET"],
        url_path="gerar-pdf-distribuidor",
        permission_classes=[UsuarioDistribuidor],
    )
    def gerar_pdf_distribuidor(self, request, uuid=None):
        user = request.user.get_username()
        solicitacao = self.get_object()
        guias = list(solicitacao.guias.all().values_list("id", flat=True))
        gera_pdf_async.delay(
            user=user,
            nome_arquivo=f"requisicao_{solicitacao.numero_solicitacao}.pdf",
            list_guias=guias,
        )
        return Response(
            dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
            status=HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["GET"],
        url_path="gerar-pdf-distribuidor-geral",
        permission_classes=[UsuarioDistribuidor],
    )
    def gerar_pdf_distribuidor_geral(self, request, uuid=None):
        user = request.user.get_username()
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(status="DISTRIBUIDOR_CONFIRMA")
        guias = (
            GuiasDasRequisicoes.objects.filter(solicitacao__in=queryset)
            .order_by("-data_entrega")
            .distinct()
        )
        lista_id_guias = list(guias.values_list("id", flat=True))
        gera_pdf_async.delay(
            user=user,
            nome_arquivo="requisicoes-confirmadas.pdf",
            list_guias=lista_id_guias,
        )
        return Response(
            dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
            status=HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["GET"],
        url_path="relatorio-guias-da-requisicao",
        permission_classes=[PermissaoParaListarEntregas],
    )
    def gerar_relaorio_guias_da_requisicao(self, request, uuid=None):
        user = request.user.get_username()
        solicitacao = SolicitacaoRemessa.objects.get(uuid=uuid)
        nome_arquivo = request.query_params.get("nome_arquivo", "requisicao")
        tem_conferencia = request.query_params.get("tem_conferencia", "false")
        tem_insucesso = request.query_params.get("tem_insucesso", "false")
        tem_conferencia = eh_true_ou_false(tem_conferencia, "tem_conferencia")
        tem_insucesso = eh_true_ou_false(tem_insucesso, "tem_insucesso")
        status_guia = request.query_params.getlist("status_guia", None)
        tem_pendencia_conferencia = (
            True
            if GuiaRemessaWorkFlow.PENDENTE_DE_CONFERENCIA in status_guia
            else False
        )

        guias = solicitacao.guias.all()
        list_guias = list(
            guias.filter(status__in=status_guia).values_list("id", flat=True)
        )

        if tem_insucesso:
            guias_filter = list(
                guias.filter(
                    status=GuiaRemessaWorkFlow.DISTRIBUIDOR_REGISTRA_INSUCESSO
                ).values_list("id", flat=True)
            )
            list_guias.extend(guias_filter)

        if not tem_conferencia and not tem_pendencia_conferencia and not tem_insucesso:
            list_guias = list(guias.values_list("id", flat=True))

        gera_pdf_async.delay(
            user=user,
            nome_arquivo=f"{nome_arquivo}_{solicitacao.numero_solicitacao}.pdf",
            list_guias=list_guias,
        )
        return Response(
            dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
            status=HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["GET"],
        url_path="exporta-excel-visao-analitica",
        permission_classes=[UsuarioDilogOuDistribuidor | UsuarioCODAEGabinete],
    )
    def gerar_excel(self, request):
        user = self.request.user
        username = user.get_username()
        numero_requisicao = request.query_params.get("numero_requisicao", False)
        ids_requisicoes = list(
            self.filter_queryset(self.get_queryset().values_list("id", flat=True))
        )

        filename = (
            f"requisicao_{numero_requisicao}.xlsx"
            if numero_requisicao
            else "requisicoes-de-entrega.xlsx"
        )

        gera_xlsx_async.delay(
            username=username,
            nome_arquivo=filename,
            ids_requisicoes=ids_requisicoes,
            eh_distribuidor=user.eh_distribuidor,
        )

        return Response(
            dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
            status=HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["GET"],
        url_path="exporta-excel-visao-entregas",
        permission_classes=[PermissaoParaListarEntregas],
    )
    def gerar_excel_entregas(self, request):
        user = self.request.user
        username = user.get_username()
        uuid = request.query_params.get("uuid", None)
        tem_conferencia = request.query_params.get("tem_conferencia", None)
        tem_insucesso = request.query_params.get("tem_insucesso", None)
        tem_conferencia = eh_true_ou_false(tem_conferencia, "tem_conferencia")
        tem_insucesso = eh_true_ou_false(tem_insucesso, "tem_insucesso")
        eh_dre = True if user.vinculo_atual.perfil.nome == COGESTOR_DRE else False
        status_guia = request.query_params.getlist("status_guia", None)
        gera_xlsx_entregas_async.delay(
            uuid=uuid,
            username=username,
            tem_conferencia=tem_conferencia,
            tem_insucesso=tem_insucesso,
            eh_distribuidor=user.eh_distribuidor,
            eh_dre=eh_dre,
            status_guia=status_guia,
        )
        return Response(
            dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
            status=HTTP_200_OK,
        )


class GuiaDaRequisicaoModelViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = GuiasDasRequisicoes.objects.all()
    serializer_class = GuiaDaRemessaSerializer
    permission_classes = [UsuarioDilogOuDistribuidor]
    pagination_class = GuiaPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = GuiaFilter

    def get_serializer_class(self):
        if self.action == "nomes_unidades":
            return InfoUnidadesSimplesDaGuiaSerializer
        return GuiaDaRemessaSerializer

    def get_permissions(self):
        if self.action in ["nomes_unidades"]:
            self.permission_classes = [UsuarioDilogOuDistribuidor]
        return super(GuiaDaRequisicaoModelViewSet, self).get_permissions()

    @action(detail=False, methods=["GET"], url_path="lista-numeros")
    def lista_numeros(self, request):
        response = {
            "results": GuiaDaRemessaSimplesSerializer(
                self.get_queryset(), many=True
            ).data
        }
        return Response(response)

    @action(
        detail=False,
        methods=["GET"],
        url_path="inconsistencias",
        permission_classes=(UsuarioCodaeDilog,),
    )
    def lista_guias_inconsistencias(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(escola=None).order_by("-id")
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = GuiaDaRemessaLookUpSerializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return response
        response = GuiaDaRemessaLookUpSerializer(queryset, many=True).data
        return Response(response)

    @action(
        detail=False,
        methods=["GET"],
        url_path="guias-escola",
        permission_classes=(UsuarioEscolaAbastecimento,),
    )
    def lista_guias_escola(self, request):
        escola = request.user.vinculo_atual.instituicao
        queryset = self.filter_queryset(self.get_queryset())
        queryset = (
            queryset.annotate(
                nome_distribuidor=F("solicitacao__distribuidor__nome_fantasia")
            )
            .filter(escola=escola)
            .exclude(
                status__in=(
                    GuiaRemessaWorkFlow.AGUARDANDO_ENVIO,
                    GuiaRemessaWorkFlow.AGUARDANDO_CONFIRMACAO,
                )
            )
            .order_by("data_entrega")
            .distinct()
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = GuiaDaRemessaComDistribuidorSerializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return response

        serializer = GuiaDaRemessaComDistribuidorSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="guia-para-conferencia",
        permission_classes=(UsuarioEscolaAbastecimento,),
    )
    def lista_guia_para_conferencia(self, request):
        escola = request.user.vinculo_atual.instituicao
        try:
            uuid = request.query_params.get("uuid", None)
            queryset = self.get_queryset().filter(uuid=uuid)
            return valida_guia_conferencia(queryset, escola)
        except ValidationError as e:
            return Response(
                dict(detail=f"Erro: {e}", status=False), status=HTTP_404_NOT_FOUND
            )

    @action(
        detail=False,
        methods=["GET"],
        url_path="guias-com-ocorrencias-sem-notificacao",
        permission_classes=(PermissaoParaVisualizarGuiasComOcorrencias,),
    )
    def lista_guias_com_ocorrencias_sem_notificacao(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = (
            queryset.annotate(
                nome_distribuidor=F("solicitacao__distribuidor__nome_fantasia")
            )
            .filter(
                conferencias__conferencia_dos_alimentos__tem_ocorrencia=True,
                notificacao__isnull=True,
            )
            .exclude(
                status__in=(
                    GuiaRemessaWorkFlow.AGUARDANDO_ENVIO,
                    GuiaRemessaWorkFlow.AGUARDANDO_CONFIRMACAO,
                    GuiaRemessaWorkFlow.PENDENTE_DE_CONFERENCIA,
                    GuiaRemessaWorkFlow.CANCELADA,
                )
            )
            .order_by("-data_entrega")
            .distinct()
        )
        if request.query_params.get("notificacao_uuid"):
            queryset_guias_do_numero = GuiasDasRequisicoes.objects.filter(
                notificacao__uuid=request.query_params.get("notificacao_uuid")
            ).distinct()
            queryset = queryset | queryset_guias_do_numero
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = GuiaDaRemessaComOcorrenciasSerializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return response

        serializer = GuiaDaRemessaComOcorrenciasSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["PATCH"],
        url_path="vincula-guias",
        permission_classes=(UsuarioCodaeDilog,),
    )
    def vincula_guias_com_escolas(self, request):
        guias_desvinculadas = self.get_queryset().filter(escola=None)
        contagem = 0

        for guia in guias_desvinculadas:
            escola = Escola.objects.filter(codigo_codae=guia.codigo_unidade).first()
            if escola is not None:
                guia.escola = escola
                guia.save()
                contagem += 1

        response = {"message": str(contagem) + " guia(s) vinculada(s)"}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="unidades-escolares")
    def nomes_unidades(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        response = {"results": serializer.data}
        return Response(response)

    @action(
        detail=True,
        methods=["GET"],
        url_path="gerar-pdf-distribuidor",
        permission_classes=[UsuarioDistribuidor],
    )
    def gerar_pdf_distribuidor(self, request, uuid=None):
        user = request.user.get_username()
        guia = self.get_object()
        gera_pdf_async.delay(
            user=user, nome_arquivo="guias_da_requisicao.pdf", list_guias=[guia.id]
        )
        return Response(
            dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
            status=HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-guias-para-insucesso",
        permission_classes=[UsuarioDistribuidor],
    )
    def lista_guias_para_insucesso(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = (
            queryset.annotate(
                numero_requisicao=F("solicitacao__numero_solicitacao"),
                status_requisicao=F("solicitacao__status"),
            )
            .exclude(
                status__in=(
                    GuiaRemessaWorkFlow.CANCELADA,
                    GuiaRemessaWorkFlow.AGUARDANDO_ENVIO,
                    GuiaRemessaWorkFlow.AGUARDANDO_CONFIRMACAO,
                )
            )
            .order_by("data_entrega")
            .distinct()
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = GuiaDaRemessaComStatusRequisicaoSerializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="guia-para-insucesso",
        permission_classes=(UsuarioDistribuidor,),
    )
    def guia_para_insucesso(self, request):
        try:
            uuid = request.query_params.get("uuid", None)
            queryset = (
                self.get_queryset()
                .filter(uuid=uuid)
                .annotate(numero_requisicao=F("solicitacao__numero_solicitacao"))
            )
            return valida_guia_insucesso(queryset)
        except ValidationError as e:
            return Response(
                dict(detail=f"Erro: {e}", status=False), status=HTTP_404_NOT_FOUND
            )

    @action(
        detail=True,
        methods=["GET"],
        url_path="relatorio-guia-remessa",
        permission_classes=[
            UsuarioDilogOuDistribuidorOuEscolaAbastecimento | UsuarioCODAEGabinete
        ],
    )
    def relatorio_guia_de_remessa(self, request, uuid=None):
        guia = self.get_object()
        guias = [guia]
        return relatorio_guia_de_remessa(guias)

    @action(
        detail=True,
        methods=["GET"],
        url_path="detalhe-guia-de-remessa",
        permission_classes=[UsuarioDilogOuDistribuidorOuEscolaAbastecimento],
    )
    def detalhe_guia_de_remessa(self, request, uuid=None):
        guia = self.get_object()
        serializer = GuiaDaRemessaCompletaSerializer(guia)
        return Response(serializer.data)


class AlimentoDaGuiaModelViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = Alimento.objects.all()
    serializer_class = AlimentoDaGuiaDaRemessaSerializer
    permission_classes = [UsuarioDilog]

    @action(detail=False, methods=["GET"], url_path="lista-nomes")
    def lista_nomes(self, request):
        response = {
            "results": AlimentoDaGuiaDaRemessaSimplesSerializer(
                self.get_queryset(), many=True
            ).data
        }
        return Response(response)


class SolicitacaoDeAlteracaoDeRequisicaoViewset(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = SolicitacaoDeAlteracaoRequisicao.objects.all()
    serializer_class = SolicitacaoDeAlteracaoSerializer
    permission_classes = [UsuarioDistribuidor]
    pagination_class = SolicitacaoAlteracaoPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = SolicitacaoAlteracaoFilter

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = (
            queryset.annotate(
                qtd_guias=Count("requisicao__guias"),
                nome_distribuidor=F("requisicao__distribuidor__razao_social"),
                data_entrega=Max("requisicao__guias__data_entrega"),
            )
            .order_by("requisicao__guias__data_entrega")
            .distinct()
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        user = self.request.user
        if user.eh_distribuidor:
            return SolicitacaoDeAlteracaoRequisicao.objects.filter(
                requisicao__distribuidor=user.vinculo_atual.instituicao
            )
        return SolicitacaoDeAlteracaoRequisicao.objects.all()

    def get_permissions(self):
        if self.action in ["retrieve", "list"]:
            self.permission_classes = [UsuarioDilogOuDistribuidor]
        return super(SolicitacaoDeAlteracaoDeRequisicaoViewset, self).get_permissions()

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return SolicitacaoDeAlteracaoSerializer
        else:
            return SolicitacaoDeAlteracaoRequisicaoCreateSerializer

    @action(
        detail=True,
        permission_classes=(UsuarioDilog,),
        methods=["patch"],
        url_path="dilog-aceita-alteracao",
    )
    def dilog_aceita_alteracao(self, request, uuid=None):
        usuario = request.user
        justificativa_aceite = request.data.get("justificativa_aceite", "")

        try:
            solicitacao_alteracao = SolicitacaoDeAlteracaoRequisicao.objects.get(
                uuid=uuid
            )
            requisicao = SolicitacaoRemessa.objects.get(
                id=solicitacao_alteracao.requisicao.id
            )

            requisicao.dilog_aceita_alteracao(
                user=usuario, justificativa=justificativa_aceite
            )
            solicitacao_alteracao.dilog_aceita(
                user=usuario, justificativa=justificativa_aceite
            )

            solicitacao_alteracao.justificativa_aceite = justificativa_aceite
            solicitacao_alteracao.save()
            serializer = SolicitacaoDeAlteracaoSimplesSerializer(solicitacao_alteracao)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=(UsuarioDilog,),
        methods=["patch"],
        url_path="dilog-nega-alteracao",
    )
    def dilog_nega_alteracao(self, request, uuid=None):
        usuario = request.user
        justificativa_negacao = request.data.get("justificativa_negacao", "")

        try:
            solicitacao_alteracao = SolicitacaoDeAlteracaoRequisicao.objects.get(
                uuid=uuid
            )
            requisicao = SolicitacaoRemessa.objects.get(
                id=solicitacao_alteracao.requisicao.id
            )

            requisicao.dilog_nega_alteracao(
                user=usuario, justificativa=justificativa_negacao
            )
            solicitacao_alteracao.dilog_nega(
                user=usuario, justificativa=justificativa_negacao
            )

            solicitacao_alteracao.justificativa_negacao = justificativa_negacao
            solicitacao_alteracao.save()
            serializer = SolicitacaoDeAlteracaoSimplesSerializer(solicitacao_alteracao)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )


class ConferenciaDaGuiaModelViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = ConferenciaGuia.objects.all()
    serializer_class = ConferenciaDaGuiaSerializer
    permission_classes = [UsuarioEscolaAbastecimento]

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return ConferenciaDaGuiaSerializer
        else:
            return ConferenciaDaGuiaCreateSerializer


class ConferenciaDaGuiaComOcorrenciaModelViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = ConferenciaGuia.objects.all()
    serializer_class = ConferenciaComOcorrenciaSerializer
    permission_classes = [UsuarioEscolaAbastecimento]

    def get_serializer_class(self):
        if self.action in ["create", "update"]:
            return ConferenciaComOcorrenciaCreateSerializer
        else:
            return ConferenciaComOcorrenciaSerializer

    @action(
        detail=False,
        methods=["GET"],
        url_path="get-ultima-conferencia",
        permission_classes=[UsuarioEscolaAbastecimento],
    )
    def get_ultima_conferencia(self, request):
        uuid = request.query_params.get("uuid", None)
        conferencia = (
            self.get_queryset().filter(guia__uuid=uuid, eh_reposicao=False).last()
        )

        if not conferencia:
            return Response(
                dict(
                    detail="Erro: Não existe conferência para edição na guia informada."
                ),
                status=HTTP_404_NOT_FOUND,
            )

        response = {
            "results": ConferenciaComOcorrenciaSerializer(conferencia, many=False).data
        }
        return Response(response)

    @action(
        detail=False,
        methods=["GET"],
        url_path="get-ultima-reposicao",
        permission_classes=[UsuarioEscolaAbastecimento],
    )
    def get_ultima_reposicao(self, request):
        uuid = request.query_params.get("uuid", None)
        reposicao = (
            self.get_queryset().filter(guia__uuid=uuid, eh_reposicao=True).last()
        )

        if not reposicao:
            return Response(
                dict(
                    detail="Erro: Não existe reposição para edição na guia informada."
                ),
                status=HTTP_404_NOT_FOUND,
            )

        response = {
            "results": ConferenciaComOcorrenciaSerializer(reposicao, many=False).data
        }
        return Response(response)


class InsucessoDeEntregaGuiaModelViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = InsucessoEntregaGuia.objects.all()
    serializer_class = InsucessoDeEntregaGuiaSerializer
    permission_classes = [UsuarioDistribuidor]

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return InsucessoDeEntregaGuiaSerializer
        else:
            return InsucessoDeEntregaGuiaCreateSerializer


class ConferenciaindividualModelViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = ConferenciaGuia.objects.all()
    serializer_class = ConferenciaIndividualPorAlimentoSerializer
    permission_classes = [UsuarioEscolaAbastecimento]

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return ConferenciaIndividualPorAlimentoSerializer


class NotificacaoOcorrenciaGuiaModelViewSet(
    ViewSetActionPermissionMixin, viewsets.ModelViewSet
):
    lookup_field = "uuid"
    queryset = NotificacaoOcorrenciasGuia.objects.all().order_by("-criado_em")
    serializer_class = NotificacaoOcorrenciasGuiaSerializer
    permission_classes = (PermissaoParaVisualizarGuiasComOcorrencias,)
    permission_action_classes = {
        "create": [PermissaoParaCriarNotificacaoDeGuiasComOcorrencias]
    }
    pagination_class = GuiaPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = NotificacaoFilter

    def get_serializer_class(self):
        if self.action in ["list"]:
            return NotificacaoOcorrenciasGuiaSerializer
        elif self.action in ["retrieve"]:
            return NotificacaoOcorrenciasGuiaDetalheSerializer
        else:
            return NotificacaoOcorrenciasCreateSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.annotate(
            nome_empresa=F("empresa__nome_fantasia")
        ).distinct()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = NotificacaoOcorrenciasGuiaSimplesSerializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return response

        serializer = NotificacaoOcorrenciasGuiaSimplesSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["PUT"], url_path="edicao-rascunho")
    def edicao_rascunho(self, request, uuid):
        instance = self.get_object()
        if instance.status == NotificacaoOcorrenciaWorkflow.RASCUNHO:
            serializer = NotificacaoOcorrenciasUpdateRascunhoSerializer()
            validated_data = serializer.validate(request.data, instance)
            res = serializer.update(instance, validated_data)
            return Response(NotificacaoOcorrenciasGuiaSerializer(res).data)
        else:
            return Response(
                dict(
                    detail="Erro de transição de estado: Status da Notificação não é RASCUNHO"
                ),
                status=HTTP_400_BAD_REQUEST,
            )

    def atualiza_notificacao(self, instance, request):
        serializer = NotificacaoOcorrenciasUpdateSerializer()
        validated_data = serializer.validate(request.data)
        res = serializer.update(instance, validated_data)
        return res

    @action(detail=True, methods=["PATCH"], url_path="criar-notificacao")
    def criar_notificacao(self, request, uuid):
        usuario = request.user
        instance = self.get_object()
        serializer = NotificacaoOcorrenciasUpdateSerializer()
        res = serializer.update(instance, request.data)
        if instance.status == NotificacaoOcorrenciaWorkflow.RASCUNHO:
            instance.cria_notificacao(user=usuario)
        return Response(NotificacaoOcorrenciasGuiaSerializer(res).data)

    @action(detail=True, methods=["PATCH"], url_path="enviar-notificacao")
    def enviar_notificacao(self, request, uuid):
        usuario = request.user
        instance = self.get_object()
        if instance.status == NotificacaoOcorrenciaWorkflow.RASCUNHO:
            res = self.atualiza_notificacao(instance, request)
            instance.cria_notificacao(user=usuario)
            instance.envia_fiscal(user=usuario)
        elif instance.status == NotificacaoOcorrenciaWorkflow.NOTIFICACAO_CRIADA:
            res = self.atualiza_notificacao(instance, request)
            instance.envia_fiscal(user=usuario)
        else:
            return Response(
                dict(
                    detail="""Erro de transição de estado:
                                          Status da Notificação não é RASCUNHO ou NOTIFICACAO_CRIADA"""
                ),
                status=HTTP_400_BAD_REQUEST,
            )
        return Response(NotificacaoOcorrenciasGuiaSerializer(res).data)

    @action(detail=True, methods=["PATCH"], url_path="solicitar-alteracao")
    def solicitar_alteracao(self, request, uuid):
        usuario = request.user
        instance = self.get_object()

        if instance.status == NotificacaoOcorrenciaWorkflow.NOTIFICACAO_ENVIADA_FISCAL:
            previsoes = instance.previsoes_contratuais.all()
            serializer = PrevisoesContratuaisDaNotificacaoUpdateSerializer(
                previsoes, data=request.data["previsoes"], many=True
            )

            if serializer.is_valid(raise_exception=True):
                serializer.save()
                instance.solicita_alteracao(user=usuario)
                return Response(NotificacaoOcorrenciasGuiaSerializer(instance).data)

        return Response(
            {
                "detail": "Erro de transição de estado: Status da Notificação não é NOTIFICACAO_ENVIADA_FISCAL"
            },
            status=HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["PATCH"], url_path="assinar")
    def assinar(self, request, uuid):
        usuario = request.user
        instance = self.get_object()

        password = request.data.pop("password", None)
        if not usuario.verificar_autenticidade(password):
            return Response(
                dict(
                    detail="Assinatura da notificação não foi validada. Verifique sua senha."
                ),
                status=HTTP_401_UNAUTHORIZED,
            )

        if instance.status == NotificacaoOcorrenciaWorkflow.NOTIFICACAO_ENVIADA_FISCAL:
            previsoes = instance.previsoes_contratuais.all()
            serializer = PrevisoesContratuaisDaNotificacaoUpdateSerializer(
                previsoes, data=request.data["previsoes"], many=True
            )

            if serializer.is_valid(raise_exception=True):
                serializer.save()
                instance.assina_fiscal(user=usuario)
                return Response(NotificacaoOcorrenciasGuiaSerializer(instance).data)

        return Response(
            {
                "detail": "Erro de transição de estado: Status da Notificação não é NOTIFICACAO_ENVIADA_FISCAL"
            },
            status=HTTP_400_BAD_REQUEST,
        )
