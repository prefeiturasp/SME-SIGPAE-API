from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Count, F, FloatField, Max, Q, Sum
from django.db.utils import DataError
from django.http.response import HttpResponse
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_406_NOT_ACCEPTABLE
)
from xworkflows.base import InvalidTransitionError

from sme_terceirizadas.dados_comuns.fluxo_status import GuiaRemessaWorkFlow, SolicitacaoRemessaWorkFlow
from sme_terceirizadas.dados_comuns.models import LogSolicitacoesUsuario
from sme_terceirizadas.dados_comuns.parser_xml import ListXMLParser
from sme_terceirizadas.dados_comuns.permissions import (
    UsuarioDilogCodae,
    UsuarioDistribuidor,
    UsuarioEscolaAbastecimento
)
from sme_terceirizadas.logistica.api.serializers.serializer_create import (
    ConferenciaComOcorrenciaCreateSerializer,
    ConferenciaDaGuiaCreateSerializer,
    ConferenciaIndividualPorAlimentoCreateSerializer,
    InsucessoDeEntregaGuiaCreateSerializer,
    SolicitacaoDeAlteracaoRequisicaoCreateSerializer,
    SolicitacaoRemessaCreateSerializer
)
from sme_terceirizadas.logistica.api.serializers.serializers import (
    AlimentoDaGuiaDaRemessaSerializer,
    AlimentoDaGuiaDaRemessaSimplesSerializer,
    ConferenciaComOcorrenciaSerializer,
    ConferenciaDaGuiaSerializer,
    ConferenciaIndividualPorAlimentoSerializer,
    GuiaDaRemessaComDistribuidorSerializer,
    GuiaDaRemessaSerializer,
    GuiaDaRemessaSimplesSerializer,
    InfoUnidadesSimplesDaGuiaSerializer,
    InsucessoDeEntregaGuiaSerializer,
    SolicitacaoDeAlteracaoSerializer,
    SolicitacaoDeAlteracaoSimplesSerializer,
    SolicitacaoRemessaContagemGuiasSerializer,
    SolicitacaoRemessaLookUpSerializer,
    SolicitacaoRemessaSerializer,
    SolicitacaoRemessaSimplesSerializer,
    XmlParserSolicitacaoSerializer
)
from sme_terceirizadas.logistica.api.services.exporta_para_excel import RequisicoesExcelService
from sme_terceirizadas.logistica.models import Alimento, ConferenciaGuia, Embalagem
from sme_terceirizadas.logistica.models import Guia as GuiasDasRequisicoes
from sme_terceirizadas.logistica.models import SolicitacaoDeAlteracaoRequisicao, SolicitacaoRemessa
from sme_terceirizadas.logistica.services import confirma_guias

from ...escola.models import Escola
from ...relatorios.relatorios import get_pdf_guia_distribuidor
from ..models.guia import InsucessoEntregaGuia
from ..utils import GuiaPagination, RequisicaoPagination, SolicitacaoAlteracaoPagination
from .filters import GuiaFilter, SolicitacaoAlteracaoFilter, SolicitacaoFilter
from .helpers import (
    retorna_dados_normalizados_excel_entregas_distribuidor,
    retorna_dados_normalizados_excel_visao_dilog,
    retorna_dados_normalizados_excel_visao_distribuidor,
    valida_guia_conferencia,
    valida_guia_insucesso
)

STR_XML_BODY = '{http://schemas.xmlsoap.org/soap/envelope/}Body'
STR_ARQUIVO_SOLICITACAO = 'ArqSolicitacaoMOD'
STR_ARQUIVO_CANCELAMENTO = 'ArqCancelamento'


class SolicitacaoEnvioEmMassaModelViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    http_method_names = ['post']
    queryset = SolicitacaoRemessa.objects.all()
    serializer_class = SolicitacaoRemessaCreateSerializer
    permission_classes = [UsuarioDilogCodae]
    pagination_class = None

    @action(detail=False, permission_classes=(UsuarioDilogCodae,),
            methods=['post'], url_path='envia-grade')
    def inicia_fluxo_solicitacoes_em_massa(self, request):
        usuario = request.user
        solicitacoes = request.data.get('solicitacoes', [])
        solicitacoes = SolicitacaoRemessa.objects.filter(uuid__in=solicitacoes,
                                                         status=SolicitacaoRemessaWorkFlow.AGUARDANDO_ENVIO)
        for solicitacao in solicitacoes:
            try:
                solicitacao.inicia_fluxo(user=usuario)
            except InvalidTransitionError as e:
                return Response(dict(detail=f'Erro de transição de estado: {e}', status=HTTP_400_BAD_REQUEST))
        serializer = SolicitacaoRemessaSerializer(solicitacoes, many=True)
        return Response(serializer.data)


class SolicitacaoCancelamentoModelViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    http_method_names = ['post', ]
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
            guias_payload = [x['StrNumGui'] for x in guias]
        else:
            guias_payload = [x['StrNumGui'] for x in guias.values()]

        solicitacao = SolicitacaoRemessa.objects.get(numero_solicitacao=num_solicitacao)
        solicitacao.guias.filter(numero_guia__in=guias_payload).update(status=GuiaRemessaWorkFlow.CANCELADA)

        guias_existentes = list(solicitacao.guias.values_list('numero_guia', flat=True))
        existe_guia_nao_cancelada = solicitacao.guias.exclude(status=GuiaRemessaWorkFlow.CANCELADA).exists()

        if set(guias_existentes) == set(guias_payload) or not existe_guia_nao_cancelada:
            solicitacao.cancela_solicitacao(user=usuario)
        else:
            solicitacao.salvar_log_transicao(status_evento=LogSolicitacoesUsuario.PAPA_CANCELA_SOLICITACAO,
                                             usuario=usuario,
                                             justificativa=f'Guias canceladas: {guias_payload}')

    def create(self, request, *args, **kwargs):  # noqa: C901
        remove_dirt = request.data.get(f'{STR_XML_BODY}')
        json_cancelamento = remove_dirt.get(f'{STR_ARQUIVO_CANCELAMENTO}')
        usuario = request.user

        if json_cancelamento:
            try:
                num_solicitacao = json_cancelamento['StrNumSol']
                guias = json_cancelamento['guias']
                self.cancela_guias(num_solicitacao, guias, usuario)

                return Response(dict(detail=f'Cancelamento realizado com sucesso', status=True),
                                status=HTTP_200_OK)
            except InvalidTransitionError as e:
                return Response(dict(detail=f'Erro de transição de estado: {e}', status=False),
                                status=HTTP_406_NOT_ACCEPTABLE)
            except ObjectDoesNotExist as e:
                return Response(dict(detail=f'Erro de transição de estado: {e}', status=False),
                                status=HTTP_406_NOT_ACCEPTABLE)


class SolicitacaoModelViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    http_method_names = ['get', 'post', 'patch']
    serializer_class = SolicitacaoRemessaCreateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (ListXMLParser,)
    pagination_class = RequisicaoPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = SolicitacaoFilter

    def get_serializer_class(self):
        if self.action == 'create':
            return XmlParserSolicitacaoSerializer
        if self.action == 'list':
            return SolicitacaoRemessaLookUpSerializer
        return SolicitacaoRemessaSerializer

    def get_permissions(self):
        if self.action in ['list']:
            self.permission_classes = [UsuarioDilogCodae | UsuarioDistribuidor]
        return super(SolicitacaoModelViewSet, self).get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.vinculo_atual.perfil.nome in ['ADMINISTRADOR_DISTRIBUIDORA']:
            return SolicitacaoRemessa.objects.filter(distribuidor=user.vinculo_atual.instituicao)
        return SolicitacaoRemessa.objects.all()

    def get_paginated_response(self, data, num_enviadas=None, num_confirmadas=None):
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data, num_enviadas, num_confirmadas)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.order_by('-guias__data_entrega').distinct()

        num_enviadas = queryset.filter(status=SolicitacaoRemessaWorkFlow.DILOG_ENVIA).count()
        num_confirmadas = queryset.filter(status=SolicitacaoRemessaWorkFlow.DISTRIBUIDOR_CONFIRMA).count()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(
                serializer.data,
                num_enviadas=num_enviadas,
                num_confirmadas=num_confirmadas
            )
            return response

        serializer = self.get_serializer(queryset, many=True)
        serializer.data['teste'] = 1
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        remove_dirt = request.data.get(f'{STR_XML_BODY}')
        json_data = remove_dirt.get(f'{STR_ARQUIVO_SOLICITACAO}')
        usuario = request.user

        if json_data:
            try:
                instance = SolicitacaoRemessaCreateSerializer().create(validated_data=json_data)
                instance.salvar_log_transicao(
                    status_evento=LogSolicitacoesUsuario.INICIO_FLUXO_SOLICITACAO,
                    usuario=usuario
                )

                return Response(dict(detail=f'Criado com sucesso', status=True),
                                status=HTTP_201_CREATED)
            except DataError as e:
                return Response(dict(detail=f'Erro de transição de estado: {e}', status=False),
                                status=HTTP_406_NOT_ACCEPTABLE)

    @action(detail=False, methods=['GET'], url_path='lista-numeros')
    def lista_numeros(self, request):
        queryset = self.get_queryset().filter(status__in=[SolicitacaoRemessaWorkFlow.AGUARDANDO_ENVIO])
        response = {'results': SolicitacaoRemessaSimplesSerializer(queryset, many=True).data}
        return Response(response)

    @action(detail=False, permission_classes=(UsuarioDilogCodae,),  # noqa C901
            methods=['GET'], url_path='lista-requisicoes-para-envio')
    def lista_requisicoes_para_envio(self, request):
        queryset = self.get_queryset().filter(status=SolicitacaoRemessaWorkFlow.AGUARDANDO_ENVIO)
        numero_requisicao = request.query_params.get('numero_requisicao', None)
        nome_distribuidor = request.query_params.get('nome_distribuidor', None)
        data_inicio = request.query_params.get('data_inicio', None)
        data_fim = request.query_params.get('data_fim', None)

        if numero_requisicao:
            queryset = queryset.filter(numero_solicitacao=numero_requisicao)
        if nome_distribuidor:
            queryset = queryset.filter(distribuidor__nome_fantasia__icontains=nome_distribuidor)
        if data_inicio and data_fim:
            queryset = queryset.filter(guias__data_entrega__range=[data_inicio, data_fim]).distinct()
        if data_inicio and not data_fim:
            queryset = queryset.filter(guias__data_entrega__gte=data_inicio).distinct()
        if data_fim and not data_inicio:
            queryset = queryset.filter(guias__data_entrega__lte=data_fim).distinct()

        response = {'results': SolicitacaoRemessaLookUpSerializer(queryset, many=True).data}
        return Response(response)

    @action(detail=False, permission_classes=[UsuarioDilogCodae | UsuarioDistribuidor],
            methods=['GET'], url_path='lista-requisicoes-confirmadas')
    def lista_requisicoes_confirmadas(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(status=SolicitacaoRemessaWorkFlow.DISTRIBUIDOR_CONFIRMA))

        if(self.request.user.vinculo_atual.perfil.nome == 'ADMINISTRADOR_DISTRIBUIDORA'):
            queryset = queryset.filter(distribuidor=self.request.user.vinculo_atual.instituicao)

        queryset = queryset.annotate(
            qtd_guias=Count('guias', distinct=True),
            distribuidor_nome=F('distribuidor__razao_social'),
            data_entrega=Max('guias__data_entrega'),
            guias_pendentes=Count(
                'guias__status', filter=Q(guias__status=GuiaRemessaWorkFlow.PENDENTE_DE_CONFERENCIA), distinct=True),
            guias_insucesso=Count(
                'guias__status',
                filter=Q(guias__status=GuiaRemessaWorkFlow.DISTRIBUIDOR_REGISTRA_INSUCESSO),
                distinct=True),
            guias_recebidas=Count('guias__status', filter=Q(guias__status=GuiaRemessaWorkFlow.RECEBIDA), distinct=True),
            guias_parciais=Count(
                'guias__status', filter=Q(guias__status=GuiaRemessaWorkFlow.RECEBIMENTO_PARCIAL), distinct=True),
            guias_nao_recebidas=Count(
                'guias__status', filter=Q(guias__status=GuiaRemessaWorkFlow.NAO_RECEBIDA), distinct=True),
            guias_reposicao_parcial=Count('guias__status', filter=Q(
                guias__status=GuiaRemessaWorkFlow.REPOSICAO_PARCIAL
            ), distinct=True),
            guias_reposicao_total=Count(
                'guias__status', filter=Q(guias__status=GuiaRemessaWorkFlow.REPOSICAO_TOTAL), distinct=True),
        ).order_by('guias__data_entrega').distinct()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SolicitacaoRemessaContagemGuiasSerializer(page, many=True)
            response = self.get_paginated_response(
                serializer.data,
                num_enviadas=0,
                num_confirmadas=queryset.count()
            )
            return response

        response = {'results': SolicitacaoRemessaContagemGuiasSerializer(queryset, many=True).data}
        return Response(response)

    @action(detail=True, permission_classes=(UsuarioDilogCodae,),
            methods=['patch'], url_path='envia-solicitacao')
    def incia_fluxo_solicitacao(self, request, uuid=None):
        solicitacao = SolicitacaoRemessa.objects.get(uuid=uuid,
                                                     status=SolicitacaoRemessaWorkFlow.AGUARDANDO_ENVIO)
        usuario = request.user

        try:
            solicitacao.inicia_fluxo(user=usuario, )
            serializer = SolicitacaoRemessaSerializer(solicitacao)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True, permission_classes=(UsuarioDistribuidor,),
            methods=['patch'], url_path='distribuidor-confirma')
    def distribuidor_confirma(self, request, uuid=None):
        solicitacao = SolicitacaoRemessa.objects.get(uuid=uuid)
        usuario = request.user

        try:
            confirma_guias(solicitacao=solicitacao, user=usuario)
            solicitacao.empresa_atende(user=usuario, )
            serializer = SolicitacaoRemessaSerializer(solicitacao)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=False, permission_classes=(UsuarioDistribuidor,),
            methods=['patch'], url_path='distribuidor-confirma-todos')
    def distribuidor_confirma_todos(self, request):
        queryset = self.get_queryset()
        solicitacoes = queryset.filter(status=SolicitacaoRemessaWorkFlow.DILOG_ENVIA)
        usuario = request.user

        try:
            for solicitacao in solicitacoes:
                confirma_guias(solicitacao, usuario)
                solicitacao.empresa_atende(user=usuario, )
            return Response(status=HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True, permission_classes=[UsuarioDistribuidor | UsuarioDilogCodae],
            methods=['get'], url_path='consolidado-alimentos')
    def consolidado_alimentos(self, request, uuid=None):
        solicitacao = self.get_queryset().filter(uuid=uuid).first()
        queryset = Embalagem.objects.filter(alimento__guia__solicitacao=solicitacao)

        if solicitacao is None:
            return Response('Solicitação inexistente.', status=HTTP_400_BAD_REQUEST)

        response_data = []

        capacidade_total_alimentos = queryset.values(
            nome_alimento=F('alimento__nome_alimento')
        ).annotate(
            peso_total=Sum(F('capacidade_embalagem') * F('qtd_volume'), output_field=FloatField())
        ).order_by()

        capacidade_total_embalagens = queryset.values(
            'descricao_embalagem',
            'unidade_medida',
            'capacidade_embalagem',
            'tipo_embalagem',
            nome_alimento=F('alimento__nome_alimento')
        ).annotate(
            peso_total_embalagem=Sum(F('capacidade_embalagem') * F('qtd_volume'), output_field=FloatField()),
            qtd_volume=Sum('qtd_volume')
        ).order_by()

        for data in capacidade_total_alimentos:
            data['total_embalagens'] = []
            response_data.append(data)

        for data in capacidade_total_embalagens:
            nome_alimento = data.pop('nome_alimento')
            index = next((index for (index, item) in enumerate(response_data) if item['nome_alimento'] == nome_alimento)) # noqa E501
            response_data[index]['total_embalagens'].append(data)

        return Response(response_data, status=HTTP_200_OK)

    @action(detail=True, methods=['GET'], url_path='gerar-pdf-distribuidor', permission_classes=[UsuarioDistribuidor])
    def gerar_pdf_distribuidor(self, request, uuid=None):
        solicitacao = self.get_object()
        guias = solicitacao.guias.all()
        return get_pdf_guia_distribuidor(data=guias)

    @action(
        detail=False, methods=['GET'],
        url_path='gerar-pdf-distribuidor-geral',
        permission_classes=[UsuarioDistribuidor])
    def gerar_pdf_distribuidor_geral(self, request, uuid=None):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(status='DISTRIBUIDOR_CONFIRMA')
        guias = GuiasDasRequisicoes.objects.filter(solicitacao__in=queryset).order_by('-data_entrega').distinct()
        return get_pdf_guia_distribuidor(data=guias)

    @action(
        detail=False, methods=['GET'],
        url_path='exporta-excel-visao-analitica',
        permission_classes=[UsuarioDilogCodae | UsuarioDistribuidor])
    def gerar_excel(self, request):
        user = self.request.user
        queryset = self.filter_queryset(self.get_queryset())
        if user.vinculo_atual.perfil.nome in ['ADMINISTRADOR_DISTRIBUIDORA']:
            requisicoes = retorna_dados_normalizados_excel_visao_distribuidor(queryset)
            result = RequisicoesExcelService.exportar_visao_distribuidor(requisicoes)
        else:
            requisicoes = retorna_dados_normalizados_excel_visao_dilog(queryset)
            result = RequisicoesExcelService.exportar_visao_dilog(requisicoes)

        response = HttpResponse(
            result['arquivo'],
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % result['filename']
        return response

    @action(
        detail=False, methods=['GET'],
        url_path='exporta-excel-visao-entregas',
        permission_classes=[UsuarioDilogCodae | UsuarioDistribuidor])
    def gerar_excel_entregas(self, request):
        uuid = request.query_params.get('uuid', None)
        queryset = self.get_queryset().filter(uuid=uuid)
        requisicoes = retorna_dados_normalizados_excel_entregas_distribuidor(queryset)

        if self.request.user.vinculo_atual.perfil.nome in ['ADMINISTRADOR_DISTRIBUIDORA']:
            result = RequisicoesExcelService.exportar_entregas_distribuidor(requisicoes)
        else:
            result = RequisicoesExcelService.exportar_entregas_dilog(requisicoes)

        response = HttpResponse(
            result['arquivo'],
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % result['filename']

        return response


class GuiaDaRequisicaoModelViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    queryset = GuiasDasRequisicoes.objects.all()
    serializer_class = GuiaDaRemessaSerializer
    permission_classes = [UsuarioDilogCodae | UsuarioDistribuidor]
    pagination_class = GuiaPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = GuiaFilter

    def get_serializer_class(self):
        if self.action == 'nomes_unidades':
            return InfoUnidadesSimplesDaGuiaSerializer
        return GuiaDaRemessaSerializer

    def get_permissions(self):
        if self.action in ['nomes_unidades']:
            self.permission_classes = [UsuarioDilogCodae | UsuarioDistribuidor]
        return super(GuiaDaRequisicaoModelViewSet, self).get_permissions()

    @action(detail=False, methods=['GET'], url_path='lista-numeros')
    def lista_numeros(self, request):
        response = {'results': GuiaDaRemessaSimplesSerializer(self.get_queryset(), many=True).data}
        return Response(response)

    @action(detail=False, methods=['GET'], url_path='inconsistencias', permission_classes=(UsuarioDilogCodae,))
    def lista_guias_inconsistencias(self, request):
        response = {'results': GuiaDaRemessaSerializer(self.get_queryset().filter(escola=None), many=True).data}
        return Response(response)

    @action(detail=False, methods=['GET'], url_path='guias-escola', permission_classes=(UsuarioEscolaAbastecimento,))
    def lista_guias_escola(self, request):
        escola = request.user.vinculo_atual.instituicao
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.annotate(
            nome_distribuidor=F('solicitacao__distribuidor__nome_fantasia')
        ).filter(escola=escola).exclude(status__in=(
            GuiaRemessaWorkFlow.CANCELADA,
            GuiaRemessaWorkFlow.AGUARDANDO_ENVIO,
            GuiaRemessaWorkFlow.AGUARDANDO_CONFIRMACAO
        )).order_by('data_entrega').distinct()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = GuiaDaRemessaComDistribuidorSerializer(page, many=True)
            response = self.get_paginated_response(
                serializer.data
            )
            return response

        serializer = GuiaDaRemessaComDistribuidorSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'],
            url_path='guia-para-conferencia', permission_classes=(UsuarioEscolaAbastecimento,))
    def lista_guia_para_conferencia(self, request):
        escola = request.user.vinculo_atual.instituicao
        try:
            uuid = request.query_params.get('uuid', None)
            queryset = self.get_queryset().filter(uuid=uuid)
            return valida_guia_conferencia(queryset, escola)
        except ValidationError as e:
            return Response(dict(detail=f'Erro: {e}', status=False),
                            status=HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['PATCH'], url_path='vincula-guias')
    def vincula_guias_com_escolas(self, request):
        guias_desvinculadas = self.get_queryset().filter(escola=None)
        contagem = 0

        for guia in guias_desvinculadas:
            escola = Escola.objects.filter(codigo_codae=guia.codigo_unidade).first()
            if escola is not None:
                guia.escola = escola
                guia.save()
                contagem += 1

        response = {'message': str(contagem) + ' guia(s) vinculada(s)'}
        return Response(response)

    @action(detail=False, methods=['GET'], url_path='unidades-escolares')
    def nomes_unidades(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        response = {'results': serializer.data}
        return Response(response)

    @action(detail=True, methods=['GET'], url_path='gerar-pdf-distribuidor', permission_classes=[UsuarioDistribuidor])
    def gerar_pdf_distribuidor(self, request, uuid=None):
        guia = self.get_object()
        return get_pdf_guia_distribuidor(data=[guia])

    @action(detail=False,
            methods=['GET'],
            url_path='lista-guias-para-insucesso',
            permission_classes=[UsuarioDistribuidor])
    def lista_guias_para_insucesso(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.annotate(
            numero_requisicao=F('solicitacao__numero_solicitacao')
        ).exclude(status__in=(
            GuiaRemessaWorkFlow.CANCELADA,
            GuiaRemessaWorkFlow.AGUARDANDO_ENVIO,
            GuiaRemessaWorkFlow.AGUARDANDO_CONFIRMACAO
        )).order_by('data_entrega').distinct()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(
                serializer.data
            )
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'],
            url_path='guia-para-insucesso', permission_classes=(UsuarioDistribuidor,))
    def guia_para_insucesso(self, request):
        try:
            uuid = request.query_params.get('uuid', None)
            queryset = self.get_queryset().filter(uuid=uuid).annotate(
                numero_requisicao=F('solicitacao__numero_solicitacao'))
            return valida_guia_insucesso(queryset)
        except ValidationError as e:
            return Response(dict(detail=f'Erro: {e}', status=False),
                            status=HTTP_404_NOT_FOUND)


class AlimentoDaGuiaModelViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    queryset = Alimento.objects.all()
    serializer_class = AlimentoDaGuiaDaRemessaSerializer
    permission_classes = [UsuarioDilogCodae]

    @action(detail=False, methods=['GET'], url_path='lista-nomes')
    def lista_nomes(self, request):
        response = {'results': AlimentoDaGuiaDaRemessaSimplesSerializer(self.get_queryset(), many=True).data}
        return Response(response)


class SolicitacaoDeAlteracaoDeRequisicaoViewset(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    queryset = SolicitacaoDeAlteracaoRequisicao.objects.all()
    serializer_class = SolicitacaoDeAlteracaoSerializer
    permission_classes = [UsuarioDistribuidor]
    pagination_class = SolicitacaoAlteracaoPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = SolicitacaoAlteracaoFilter

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.annotate(
            qtd_guias=Count('requisicao__guias'),
            nome_distribuidor=F('requisicao__distribuidor__razao_social'),
            data_entrega=Max('requisicao__guias__data_entrega')
        ).order_by('requisicao__guias__data_entrega').distinct()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(
                serializer.data
            )
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        user = self.request.user
        if user.vinculo_atual.perfil.nome in ['ADMINISTRADOR_DISTRIBUIDORA']:
            return SolicitacaoDeAlteracaoRequisicao.objects.filter(
                requisicao__distribuidor=user.vinculo_atual.instituicao
            )
        return SolicitacaoDeAlteracaoRequisicao.objects.all()

    def get_permissions(self):
        if self.action in ['retrieve', 'list']:
            self.permission_classes = [UsuarioDilogCodae | UsuarioDistribuidor]
        return super(SolicitacaoDeAlteracaoDeRequisicaoViewset, self).get_permissions()

    def get_serializer_class(self):
        if self.action in ['retrieve', 'list']:
            return SolicitacaoDeAlteracaoSerializer
        else:
            return SolicitacaoDeAlteracaoRequisicaoCreateSerializer

    @action(detail=True, permission_classes=(UsuarioDilogCodae,),
            methods=['patch'], url_path='dilog-aceita-alteracao')
    def dilog_aceita_alteracao(self, request, uuid=None):
        usuario = request.user
        justificativa_aceite = request.data.get('justificativa_aceite', '')

        try:
            solicitacao_alteracao = SolicitacaoDeAlteracaoRequisicao.objects.get(uuid=uuid)
            requisicao = SolicitacaoRemessa.objects.get(id=solicitacao_alteracao.requisicao.id)

            requisicao.dilog_aceita_alteracao(user=usuario, justificativa=justificativa_aceite)
            solicitacao_alteracao.dilog_aceita(user=usuario, justificativa=justificativa_aceite)

            solicitacao_alteracao.justificativa_aceite = justificativa_aceite
            solicitacao_alteracao.save()
            serializer = SolicitacaoDeAlteracaoSimplesSerializer(solicitacao_alteracao)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True, permission_classes=(UsuarioDilogCodae,),
            methods=['patch'], url_path='dilog-nega-alteracao')
    def dilog_nega_alteracao(self, request, uuid=None):
        usuario = request.user
        justificativa_negacao = request.data.get('justificativa_negacao', '')

        try:
            solicitacao_alteracao = SolicitacaoDeAlteracaoRequisicao.objects.get(uuid=uuid)
            requisicao = SolicitacaoRemessa.objects.get(id=solicitacao_alteracao.requisicao.id)

            requisicao.dilog_nega_alteracao(user=usuario, justificativa=justificativa_negacao)
            solicitacao_alteracao.dilog_nega(user=usuario, justificativa=justificativa_negacao)

            solicitacao_alteracao.justificativa_negacao = justificativa_negacao
            solicitacao_alteracao.save()
            serializer = SolicitacaoDeAlteracaoSimplesSerializer(solicitacao_alteracao)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)


class ConferenciaDaGuiaModelViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    queryset = ConferenciaGuia.objects.all()
    serializer_class = ConferenciaDaGuiaSerializer
    permission_classes = [UsuarioEscolaAbastecimento]

    def get_serializer_class(self):
        if self.action in ['retrieve', 'list']:
            return ConferenciaDaGuiaSerializer
        else:
            return ConferenciaDaGuiaCreateSerializer


class ConferenciaDaGuiaComOcorrenciaModelViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    queryset = ConferenciaGuia.objects.all()
    serializer_class = ConferenciaComOcorrenciaSerializer
    permission_classes = [UsuarioEscolaAbastecimento]

    def get_serializer_class(self):
        if self.action in ['retrieve', 'list']:
            return ConferenciaComOcorrenciaSerializer
        else:
            return ConferenciaComOcorrenciaCreateSerializer


class InsucessoDeEntregaGuiaModelViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    queryset = InsucessoEntregaGuia.objects.all()
    serializer_class = InsucessoDeEntregaGuiaSerializer
    permission_classes = [UsuarioDistribuidor]

    def get_serializer_class(self):
        if self.action in ['retrieve', 'list']:
            return InsucessoDeEntregaGuiaSerializer
        else:
            return InsucessoDeEntregaGuiaCreateSerializer


class ConferenciaindividualModelViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    queryset = ConferenciaGuia.objects.all()
    serializer_class = ConferenciaIndividualPorAlimentoSerializer
    permission_classes = [UsuarioEscolaAbastecimento]

    def get_serializer_class(self):
        if self.action in ['retrieve', 'list']:
            return ConferenciaIndividualPorAlimentoSerializer
        else:
            return ConferenciaIndividualPorAlimentoCreateSerializer
