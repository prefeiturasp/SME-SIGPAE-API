from datetime import datetime
from itertools import chain

from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django_filters import rest_framework as filters
from rest_framework import mixins, pagination, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_400_BAD_REQUEST
from xworkflows import InvalidTransitionError

from ...dados_comuns import constants
from ...dados_comuns.fluxo_status import HomologacaoProdutoWorkflow, ReclamacaoProdutoWorkflow
from ...dados_comuns.models import LogSolicitacoesUsuario
from ...dados_comuns.permissions import PermissaoParaReclamarDeProduto, UsuarioCODAEGestaoProduto, UsuarioTerceirizada
from ...dados_comuns.utils import url_configs
from ...dieta_especial.models import Alimento
from ...relatorios.relatorios import (
    relatorio_marcas_por_produto_homologacao,
    relatorio_produto_analise_sensorial,
    relatorio_produto_analise_sensorial_recebimento,
    relatorio_produto_homologacao,
    relatorio_produtos_agrupado_terceirizada,
    relatorio_produtos_em_analise_sensorial,
    relatorio_produtos_situacao,
    relatorio_produtos_suspensos,
    relatorio_reclamacao
)
from ...terceirizada.api.serializers.serializers import TerceirizadaSimplesSerializer
from ..constants import (
    AVALIAR_RECLAMACAO_HOMOLOGACOES_STATUS,
    AVALIAR_RECLAMACAO_RECLAMACOES_STATUS,
    NOVA_RECLAMACAO_HOMOLOGACOES_STATUS,
    RESPONDER_RECLAMACAO_HOMOLOGACOES_STATUS,
    RESPONDER_RECLAMACAO_RECLAMACOES_STATUS
)
from ..forms import ProdutoJaExisteForm, ProdutoPorParametrosForm
from ..models import (
    Fabricante,
    HomologacaoDoProduto,
    ImagemDoProduto,
    InformacaoNutricional,
    Marca,
    NomeDeProdutoEdital,
    Produto,
    ProtocoloDeDietaEspecial,
    ReclamacaoDeProduto,
    RespostaAnaliseSensorial,
    SolicitacaoCadastroProdutoDieta
)
from ..utils import (
    StandardResultsSetPagination,
    agrupa_por_terceirizada,
    converte_para_datetime,
    cria_filtro_aditivos,
    cria_filtro_produto_por_parametros_form,
    get_filtros_data
)
from .filters import ProdutoFilter, filtros_produto_reclamacoes
from .serializers.serializers import (
    FabricanteSerializer,
    FabricanteSimplesSerializer,
    HomologacaoProdutoPainelGerencialSerializer,
    HomologacaoProdutoSerializer,
    ImagemDoProdutoSerializer,
    InformacaoNutricionalSerializer,
    MarcaSerializer,
    MarcaSimplesSerializer,
    NomeDeProdutoEditalSerializer,
    ProdutoHomologadosPorParametrosSerializer,
    ProdutoListagemSerializer,
    ProdutoReclamacaoSerializer,
    ProdutoRelatorioAnaliseSensorialSerializer,
    ProdutoRelatorioSituacaoSerializer,
    ProdutoSerializer,
    ProdutoSimplesSerializer,
    ProdutoSuspensoSerializer,
    ProtocoloDeDietaEspecialSerializer,
    ProtocoloSimplesSerializer,
    ReclamacaoDeProdutoSerializer,
    ReclamacaoDeProdutoSimplesSerializer,
    SolicitacaoCadastroProdutoDietaSerializer,
    SubstitutosSerializer
)
from .serializers.serializers_create import (
    ProdutoSerializerCreate,
    ReclamacaoDeProdutoSerializerCreate,
    RespostaAnaliseSensorialSearilzerCreate,
    SolicitacaoCadastroProdutoDietaSerializerCreate
)


class ListaNomesUnicos():
    @action(detail=False, methods=['GET'], url_path='lista-nomes-unicos')
    def lista_nomes_unicos(self, request):
        query_set = self.filter_queryset(self.get_queryset()).values('nome').distinct()
        nomes_unicos = [i['nome'] for i in query_set]
        return Response({
            'results': nomes_unicos,
            'count': len(nomes_unicos)
        })


class InformacaoNutricionalBaseViewSet(viewsets.ReadOnlyModelViewSet):

    def possui_tipo_nutricional_na_lista(self, infos_nutricionais, nome):
        tem_tipo_nutricional = False
        if len(infos_nutricionais) > 0:
            for info_nutricional in infos_nutricionais:
                if info_nutricional['nome'] == nome:
                    tem_tipo_nutricional = True
        return tem_tipo_nutricional

    def adiciona_informacao_em_tipo_nutricional(self, infos_nutricionais, objeto):
        tipo_nutricional = objeto.tipo_nutricional.nome
        for item in infos_nutricionais:
            if item['nome'] == tipo_nutricional:
                item['informacoes_nutricionais'].append({
                    'nome': objeto.nome,
                    'uuid': objeto.uuid,
                    'medida': objeto.medida
                })
        return infos_nutricionais

    def _agrupa_informacoes_por_tipo(self, query_set):
        infos_nutricionais = []
        for objeto in query_set:
            tipo_nutricional = objeto.tipo_nutricional.nome
            if self.possui_tipo_nutricional_na_lista(infos_nutricionais, tipo_nutricional):
                infos_nutricionais = self.adiciona_informacao_em_tipo_nutricional(
                    infos_nutricionais, objeto)
            else:
                info_nutricional = {
                    'nome': tipo_nutricional,
                    'informacoes_nutricionais': [{
                        'nome': objeto.nome,
                        'uuid': objeto.uuid,
                        'medida': objeto.medida
                    }]
                }
                infos_nutricionais.append(info_nutricional)
        return infos_nutricionais


class ImagensViewset(mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    lookup_field = 'uuid'
    queryset = ImagemDoProduto.objects.all()
    serializer_class = ImagemDoProdutoSerializer


class HomologacaoProdutoPainelGerencialViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = HomologacaoProdutoPainelGerencialSerializer
    queryset = HomologacaoDoProduto.objects.all()

    def get_lista_status(self):
        lista_status = [
            HomologacaoDoProduto.workflow_class.TERCEIRIZADA_RESPONDEU_RECLAMACAO,
            HomologacaoDoProduto.workflow_class.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
            HomologacaoDoProduto.workflow_class.CODAE_PEDIU_ANALISE_RECLAMACAO,
            HomologacaoDoProduto.workflow_class.CODAE_AUTORIZOU_RECLAMACAO,
            HomologacaoDoProduto.workflow_class.CODAE_SUSPENDEU,
            HomologacaoDoProduto.workflow_class.CODAE_HOMOLOGADO,
            HomologacaoDoProduto.workflow_class.CODAE_NAO_HOMOLOGADO,
            HomologacaoDoProduto.workflow_class.TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO]

        if self.request.user.tipo_usuario in [constants.TIPO_USUARIO_TERCEIRIZADA,
                                              constants.TIPO_USUARIO_GESTAO_PRODUTO]:
            lista_status.append(
                HomologacaoDoProduto.workflow_class.CODAE_QUESTIONADO)

            lista_status.append(
                HomologacaoDoProduto.workflow_class.CODAE_PEDIU_ANALISE_SENSORIAL)

            lista_status.append(
                HomologacaoDoProduto.workflow_class.CODAE_PENDENTE_HOMOLOGACAO)

        return lista_status

    def dados_dashboard(self, query_set: list) -> dict:
        # TODO: é preciso fazer um refactor dessa parte do dashboard de P&D
        sumario = []

        query = self.get_queryset()

        for workflow in self.get_lista_status():
            q = query_set

            if (workflow in [
                HomologacaoDoProduto.workflow_class.TERCEIRIZADA_RESPONDEU_RECLAMACAO,
                HomologacaoDoProduto.workflow_class.CODAE_QUESTIONADO] and
                    self.request.user.tipo_usuario == constants.TIPO_USUARIO_TERCEIRIZADA):

                q = query_set.filter(rastro_terceirizada=self.request.user.vinculo_atual.instituicao)

            # Para o card aguardando reclamação quando o usuário é uma escola
            if (workflow in [
                HomologacaoDoProduto.workflow_class.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
                HomologacaoDoProduto.workflow_class.TERCEIRIZADA_RESPONDEU_RECLAMACAO,
                HomologacaoDoProduto.workflow_class.CODAE_PEDIU_ANALISE_RECLAMACAO] and
                    self.request.user.tipo_usuario == constants.TIPO_USUARIO_ESCOLA):

                q = query.filter(reclamacoes__escola=self.request.user.vinculo_atual.instituicao)

            sumario.append({
                'status': workflow,
                'dados': self.get_serializer(
                    q.filter(status=workflow).distinct().all(),
                    context={'request': self.request}, many=True).data
            })

        return sumario

    @action(detail=False, methods=['GET'], url_path='dashboard')
    def dashboard(self, request):
        query_set = self.get_queryset()
        response = {'results': self.dados_dashboard(query_set=query_set)}
        return Response(response)

    @action(detail=False,  # noqa C901
            methods=['GET'],
            url_path=f'filtro-por-status/{constants.FILTRO_STATUS_HOMOLOGACAO}')
    def solicitacoes_homologacao_por_status(self, request, filtro_aplicado=constants.RASCUNHO):
        filtros = {}
        user = self.request.user
        if filtro_aplicado:
            if filtro_aplicado == 'codae_pediu_analise_reclamacao':
                status__in = ['ESCOLA_OU_NUTRICIONISTA_RECLAMOU',
                              'CODAE_PEDIU_ANALISE_RECLAMACAO']
                if request.user.vinculo_atual.perfil.nome in [constants.COORDENADOR_GESTAO_PRODUTO,
                                                              constants.ADMINISTRADOR_GESTAO_PRODUTO]:
                    status__in.append('TERCEIRIZADA_RESPONDEU_RECLAMACAO')
                filtros['status__in'] = status__in

                if request.user.tipo_usuario == constants.TIPO_USUARIO_ESCOLA:
                    filtros['reclamacoes__escola'] = request.user.vinculo_atual.instituicao
                    if 'TERCEIRIZADA_RESPONDEU_RECLAMACAO' not in status__in:
                        status__in.append('TERCEIRIZADA_RESPONDEU_RECLAMACAO')

            elif filtro_aplicado == 'codae_homologado':

                if user.tipo_usuario == constants.TIPO_USUARIO_TERCEIRIZADA:
                    filtros['status__in'] = ['ESCOLA_OU_NUTRICIONISTA_RECLAMOU',
                                             'TERCEIRIZADA_RESPONDEU_RECLAMACAO',
                                             filtro_aplicado.upper()]

                elif user.tipo_usuario == constants.TIPO_USUARIO_GESTAO_PRODUTO:
                    filtros['status'] = filtro_aplicado.upper()

                else:
                    filtros['status__in'] = ['ESCOLA_OU_NUTRICIONISTA_RECLAMOU',
                                             'CODAE_PEDIU_ANALISE_RECLAMACAO',
                                             'TERCEIRIZADA_RESPONDEU_RECLAMACAO',
                                             filtro_aplicado.upper()]
            elif filtro_aplicado == 'codae_nao_homologado':
                status__in = ['CODAE_NAO_HOMOLOGADO',
                              'TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO']
                filtros['status__in'] = status__in
            else:
                filtros['status'] = filtro_aplicado.upper()
        query_set = self.get_queryset().filter(**filtros).distinct()
        serializer = self.get_serializer if filtro_aplicado != constants.RASCUNHO else HomologacaoProdutoSerializer
        response = {'results': serializer(
            query_set, context={'request': request}, many=True).data}
        return Response(response)


class HomologacaoProdutoViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = HomologacaoProdutoSerializer
    queryset = HomologacaoDoProduto.objects.all()

    @action(detail=True,
            permission_classes=(UsuarioCODAEGestaoProduto,),
            methods=['patch'],
            url_path=constants.CODAE_HOMOLOGA)
    def codae_homologa(self, request, uuid=None):
        homologacao_produto = self.get_object()
        uri = reverse(
            'Produtos-relatorio',
            args=[homologacao_produto.produto.uuid]
        )
        try:
            homologacao_produto.codae_homologa(
                user=request.user,
                link_pdf=url_configs('API', {'uri': uri}))
            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            permission_classes=(UsuarioCODAEGestaoProduto,),
            methods=['patch'],
            url_path=constants.CODAE_NAO_HOMOLOGA)
    def codae_nao_homologa(self, request, uuid=None):
        homologacao_produto = self.get_object()
        uri = reverse(
            'Produtos-relatorio',
            args=[homologacao_produto.produto.uuid]
        )
        try:
            justificativa = request.data.get('justificativa', '')
            homologacao_produto.codae_nao_homologa(
                user=request.user,
                justificativa=justificativa,
                link_pdf=url_configs('API', {'uri': uri})
            )
            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            permission_classes=(UsuarioCODAEGestaoProduto,),
            methods=['patch'],
            url_path=constants.CODAE_QUESTIONA_PEDIDO)
    def codae_questiona(self, request, uuid=None):
        homologacao_produto = self.get_object()
        uri = reverse(
            'Produtos-relatorio',
            args=[homologacao_produto.produto.uuid]
        )
        try:
            justificativa = request.data.get('justificativa', '')
            homologacao_produto.codae_questiona(
                user=request.user,
                justificativa=justificativa,
                link_pdf=url_configs('API', {'uri': uri})
            )
            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            permission_classes=(UsuarioCODAEGestaoProduto,),
            methods=['patch'],
            url_path=constants.CODAE_PEDE_ANALISE_SENSORIAL)
    def codae_pede_analise_sensorial(self, request, uuid=None):
        homologacao_produto = self.get_object()
        uri = reverse(
            'Produtos-relatorio',
            args=[homologacao_produto.produto.uuid]
        )
        try:
            justificativa = request.data.get('justificativa', '')
            homologacao_produto.gera_protocolo_analise_sensorial()
            homologacao_produto.codae_pede_analise_sensorial(
                user=request.user, justificativa=justificativa,
                link_pdf=url_configs('API', {'uri': uri})
            )
            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,  # noqa C901
            permission_classes=[PermissaoParaReclamarDeProduto],
            methods=['patch'],
            url_path=constants.ESCOLA_OU_NUTRI_RECLAMA)
    def escola_ou_nutricodae_reclama(self, request, uuid=None):
        homologacao_produto = self.get_object()
        data = request.data.copy()
        data['homologacao_de_produto'] = homologacao_produto.id
        data['criado_por'] = request.user.id
        try:
            serializer_reclamacao = ReclamacaoDeProdutoSerializerCreate(
                data=data)
            if not serializer_reclamacao.is_valid():
                return Response(serializer_reclamacao.errors)
            serializer_reclamacao.save()
            if homologacao_produto.status == HomologacaoDoProduto.workflow_class.CODAE_HOMOLOGADO:
                homologacao_produto.escola_ou_nutricionista_reclamou(
                    user=request.user,
                    reclamacao=serializer_reclamacao.data)
            return Response(serializer_reclamacao.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            permission_classes=[UsuarioCODAEGestaoProduto],
            methods=['patch'],
            url_path=constants.CODAE_PEDE_ANALISE_RECLAMACAO)
    def codae_pede_analise_reclamacao(self, request, uuid=None):
        anexos = request.data.get('anexos', [])
        justificativa = request.data.get('justificativa', '')
        homologacao_produto = self.get_object()
        try:
            homologacao_produto.codae_pediu_analise_reclamacao(
                user=request.user,
                anexos=anexos,
                justificativa=justificativa
            )
            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            permission_classes=[UsuarioCODAEGestaoProduto],
            methods=['patch'],
            url_path=constants.CODAE_ACEITA_RECLAMACAO)
    def codae_aceita_reclamacao(self, request, uuid=None):
        anexos = request.data.get('anexos', [])
        justificativa = request.data.get('justificativa', '')
        homologacao_produto = self.get_object()
        try:
            homologacao_produto.codae_autorizou_reclamacao(
                user=request.user,
                anexos=anexos,
                justificativa=justificativa,
                nao_enviar_email=True
            )
            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            permission_classes=[UsuarioCODAEGestaoProduto],
            methods=['patch'],
            url_path=constants.CODAE_RECUSA_RECLAMACAO)
    def codae_recusa_reclamacao(self, request, uuid=None):
        anexos = request.data.get('anexos', [])
        justificativa = request.data.get('justificativa', '')
        homologacao_produto = self.get_object()
        try:
            homologacao_produto.codae_homologa(
                user=request.user,
                anexos=anexos,
                justificativa=justificativa,
                nao_enviar_email=True
            )
            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            permission_classes=[UsuarioCODAEGestaoProduto],
            methods=['patch'],
            url_path=constants.SUSPENDER_PRODUTO)
    def suspender(self, request, uuid=None):
        homologacao_produto = self.get_object()
        try:
            homologacao_produto.codae_suspende(request=request)
            return Response('Homologação suspensa')
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            permission_classes=[UsuarioCODAEGestaoProduto],
            methods=['patch'],
            url_path=constants.ATIVAR_PRODUTO)
    def ativar(self, request, uuid=None):
        homologacao_produto = self.get_object()
        try:
            homologacao_produto.codae_ativa(request=request)
            return Response('Homologação ativada')
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            permission_classes=[UsuarioTerceirizada],
            methods=['patch'],
            url_path=constants.TERCEIRIZADA_RESPONDE_RECLAMACAO)
    def terceirizada_responde_reclamacao(self, request, uuid=None):
        homologacao_produto = self.get_object()
        try:
            homologacao_produto.terceirizada_responde_reclamacao(
                request=request)
            return Response('Reclamação respondida')
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['GET'], url_path='reclamacao')
    def reclamacao_homologao(self, request, uuid=None):
        homologacao_produto = self.get_object()
        reclamacao = homologacao_produto.reclamacoes.filter(
            status=ReclamacaoProdutoWorkflow.CODAE_ACEITOU).first()
        serializer = ReclamacaoDeProdutoSimplesSerializer(reclamacao)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='numero_protocolo')
    def numero_relatorio_analise_sensorial(self, request):
        homologacao = HomologacaoDoProduto()
        protocolo = homologacao.retorna_numero_do_protocolo()
        return Response(protocolo)

    def retorna_datetime(self, data):
        data = datetime.strptime(data, '%d/%m/%Y')
        return data

    @action(detail=True,
            permission_classes=[UsuarioTerceirizada],
            methods=['post'],
            url_path=constants.GERAR_PDF)
    def gerar_pdf_homologacao(self, request, uuid=None):
        homologacao_produto = self.get_object()
        homologacao_produto.pdf_gerado = True
        homologacao_produto.save()
        return Response('PDF Homologação gerado')

    @action(detail=False,
            permission_classes=[UsuarioTerceirizada],
            methods=['get'],
            url_path=constants.AGUARDANDO_ANALISE_SENSORIAL)
    def homolocoes_aguardando_analise_sensorial(self, request):
        homologacoes = HomologacaoDoProduto.objects.filter(
            status=HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_SENSORIAL
        )
        serializer = self.get_serializer(homologacoes, many=True)
        return Response(serializer.data)

    @action(detail=True,
            permission_classes=[UsuarioTerceirizada],
            methods=['patch'],
            url_path=constants.TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO)
    def terceirizada_cancelou_solicitacao_homologacao(self, request, uuid=None):
        homologacao_produto = self.get_object()
        justificativa = request.data.get('justificativa', '')
        try:
            homologacao_produto.terceirizada_cancelou_solicitacao_homologacao(
                user=request.user, justificativa=justificativa)
            return Response('Cancelamento de solicitação de homologação realizada com sucesso!')
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        homologacao_produto = self.get_object()
        if homologacao_produto.pode_excluir:
            homologacao_produto.produto.delete()
            homologacao_produto.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(dict(detail='Você só pode excluir quando o status for RASCUNHO.'),
                            status=status.HTTP_403_FORBIDDEN)


class ProdutoViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = ProdutoSerializer
    queryset = Produto.objects.all()
    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ProdutoFilter

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).select_related(
            'marca', 'fabricante').order_by('criado_em')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProdutoListagemSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ProdutoListagemSerializer(queryset, many=True)
        return Response(serializer.data)

    def paginated_response(self, queryset):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, context={'request': self.request}, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_paginated_response(
            queryset, context={'request': self.request}, many=True)
        return Response(serializer.data)

    def get_serializer_class(self):  # noqa C901
        if self.action in ['create', 'update', 'partial_update']:
            return ProdutoSerializerCreate
        if self.action == 'filtro_relatorio_em_analise_sensorial':
            return ProdutoRelatorioAnaliseSensorialSerializer
        if self.action == 'filtro_relatorio_situacao_produto':
            return ProdutoRelatorioSituacaoSerializer
        if self.action == 'filtro_homologados_por_parametros':
            return ProdutoHomologadosPorParametrosSerializer
        if self.action == 'filtro_relatorio_produto_suspenso':
            return ProdutoSuspensoSerializer
        if self.action in ['filtro_reclamacoes', 'filtro_reclamacoes_terceirizada',
                           'filtro_avaliar_reclamacoes']:
            return ProdutoReclamacaoSerializer
        return ProdutoSerializer

    @action(detail=False, methods=['GET'], url_path='lista-nomes')
    def lista_produtos(self, request):
        query_set = Produto.objects.filter(ativo=True)
        filtrar_por = request.query_params.get('filtrar_por', None)
        if filtrar_por == 'reclamacoes/':
            query_set = query_set.filter(
                homologacoes__reclamacoes__isnull=False,
                homologacoes__status__in=[
                    'CODAE_PEDIU_ANALISE_RECLAMACAO',
                    'TERCEIRIZADA_RESPONDEU_RECLAMACAO',
                    'ESCOLA_OU_NUTRICIONISTA_RECLAMOU'
                ]
            )
        response = {'results': ProdutoSimplesSerializer(
            query_set, many=True).data}
        return Response(response)

    @action(detail=False, methods=['GET'], url_path='lista-nomes-unicos')
    def lista_nomes_unicos(self, request):
        query_set = self.filter_queryset(self.get_queryset()).filter(ativo=True).values('nome').distinct()
        nomes_unicos = [p['nome'] for p in query_set]
        return Response({
            'results': nomes_unicos,
            'count': len(nomes_unicos)
        })

    @action(detail=False, methods=['GET'], url_path='lista-nomes-nova-reclamacao')
    def lista_produtos_nova_reclamacao(self, request):
        query_set = Produto.objects.filter(
            ativo=True,
            homologacoes__status__in=NOVA_RECLAMACAO_HOMOLOGACOES_STATUS
        ).only('nome').values('nome').order_by('nome').distinct()
        response = {'results': [{'uuid': 'uuid', 'nome': r['nome']} for r in query_set]}
        return Response(response)

    @action(detail=False, methods=['GET'], url_path='lista-nomes-avaliar-reclamacao')
    def lista_produtos_avaliar_reclamacao(self, request):
        query_set = Produto.objects.filter(
            ativo=True,
            homologacoes__status__in=AVALIAR_RECLAMACAO_HOMOLOGACOES_STATUS,
            homologacoes__reclamacoes__status__in=AVALIAR_RECLAMACAO_RECLAMACOES_STATUS
        ).only('nome').values('nome').order_by('nome').distinct()
        response = {'results': [{'uuid': 'uuid', 'nome': r['nome']} for r in query_set]}
        return Response(response)

    @action(detail=False, methods=['GET'], url_path='lista-nomes-responder-reclamacao')
    def lista_produtos_responder_reclamacao(self, request):
        user = request.user
        query_set = Produto.objects.filter(
            ativo=True,
            homologacoes__status__in=RESPONDER_RECLAMACAO_HOMOLOGACOES_STATUS,
            homologacoes__reclamacoes__status__in=RESPONDER_RECLAMACAO_RECLAMACOES_STATUS,
            homologacoes__rastro_terceirizada=user.vinculo_atual.instituicao
        ).only('nome').values('nome').order_by('nome').distinct()
        response = {'results': [{'uuid': 'uuid', 'nome': r['nome']} for r in query_set]}
        return Response(response)

    @action(detail=False, methods=['GET'], url_path='lista-nomes-homologados')
    def lista_produtos_homologados(self, request):
        status = 'CODAE_HOMOLOGADO'
        query_set = Produto.objects.filter(
            ativo=True,
            homologacoes__status=status
        )
        response = {
            'results': ProdutoSimplesSerializer(query_set, many=True).data
        }
        return Response(response)

    @action(detail=False, methods=['GET'], url_path='lista-substitutos')
    def lista_substitutos(self, request):
        # Retorna todos os alimentos + os produtos homologados.
        status = 'CODAE_HOMOLOGADO'
        alimentos = Alimento.objects.filter(tipo='E')
        produtos = Produto.objects.filter(ativo=True, homologacoes__status=status)
        alimentos.model = Produto
        query_set = list(chain(alimentos, produtos))
        response = {
            'results': SubstitutosSerializer(query_set, many=True).data
        }
        return Response(response)

    @action(detail=False,
            methods=['GET'],
            url_path='filtro-por-nome/(?P<produto_nome>[^/.]+)')
    def filtro_por_nome(self, request, produto_nome=None):
        query_set = Produto.filtrar_por_nome(nome=produto_nome)
        page = self.paginate_queryset(query_set)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            methods=['GET'],
            url_path='filtro-por-fabricante/(?P<fabricante_nome>[^/.]+)')
    def filtro_por_fabricante(self, request, fabricante_nome=None):
        query_set = Produto.filtrar_por_fabricante(nome=fabricante_nome)
        page = self.paginate_queryset(query_set)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            methods=['GET'],
            url_path='filtro-por-marca/(?P<marca_nome>[^/.]+)')
    def filtro_por_marca(self, request, marca_nome=None):
        query_set = Produto.filtrar_por_marca(nome=marca_nome)
        page = self.paginate_queryset(query_set)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            methods=['GET'],
            url_path='todos-produtos')
    def filtro_consolidado(self, request):
        query_set = Produto.objects.all()
        response = {'results': self.get_serializer(query_set, many=True).data}
        return Response(response)

    @action(detail=True, url_path=constants.RELATORIO,
            methods=['get'], permission_classes=(AllowAny,))
    def relatorio(self, request, uuid=None):
        return relatorio_produto_homologacao(request, produto=self.get_object())

    @action(detail=False,
            methods=['GET'],
            permission_classes=(AllowAny,),
            url_path='marcas-por-produto')
    def relatorio_marcas_por_produto(self, request):
        form = ProdutoPorParametrosForm(request.GET)

        if not form.is_valid():
            return Response(form.errors)

        return relatorio_marcas_por_produto_homologacao(
            request,
            produtos=self.get_queryset_filtrado_agrupado(request, form),
            filtros=form.cleaned_data
        )

    @action(detail=True, url_path=constants.RELATORIO_ANALISE,
            methods=['get'], permission_classes=(IsAuthenticated,))
    def relatorio_analise_sensorial(self, request, uuid=None):
        return relatorio_produto_analise_sensorial(request, produto=self.get_object())

    @action(detail=True, url_path=constants.RELATORIO_RECEBIMENTO,
            methods=['get'], permission_classes=(IsAuthenticated,))
    def relatorio_analise_sensorial_recebimento(self, request, uuid=None):
        return relatorio_produto_analise_sensorial_recebimento(request, produto=self.get_object())

    def get_queryset_filtrado(self, cleaned_data):
        campos_a_pesquisar = cria_filtro_produto_por_parametros_form(cleaned_data)
        if 'aditivos' in cleaned_data:
            filtro_aditivos = cria_filtro_aditivos(cleaned_data['aditivos'])
            return self.get_queryset().filter(**campos_a_pesquisar).filter(filtro_aditivos)
        else:
            return self.get_queryset().filter(**campos_a_pesquisar)

    @action(detail=False,
            methods=['POST'],
            url_path='filtro-por-parametros')
    def filtro_por_parametros(self, request):
        form = ProdutoPorParametrosForm(request.data)

        if not form.is_valid():
            return Response(form.errors)

        queryset = self.get_queryset_filtrado(form.cleaned_data)
        return self.paginated_response(queryset.order_by('criado_em'))

    def serializa_agrupamento(self, agrupamento):
        serializado = []

        for grupo in agrupamento['results']:
            serializado.append({
                'terceirizada': TerceirizadaSimplesSerializer(grupo['terceirizada']).data,
                'produtos': [
                    self.get_serializer(prod, context={'request': self.request}).data for prod in grupo['produtos']
                ]
            })

        return serializado

    @action(detail=False,
            methods=['POST'],
            url_path='filtro-por-parametros-agrupado-terceirizada')
    def filtro_por_parametros_agrupado_terceirizada(self, request):
        form = ProdutoPorParametrosForm(request.data)

        if not form.is_valid():
            return Response(form.errors)

        form_data = form.cleaned_data.copy()
        form_data['status'] = [
            HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO,
            HomologacaoProdutoWorkflow.ESCOLA_OU_NUTRICIONISTA_RECLAMOU
        ]

        queryset = self.get_queryset_filtrado(form_data)
        queryset.order_by('criado_por')

        dados_agrupados = agrupa_por_terceirizada(queryset)

        return Response(self.serializa_agrupamento(dados_agrupados))

    def get_queryset_filtrado_agrupado(self, request, form):
        form_data = form.cleaned_data.copy()
        form_data['status'] = [
            HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO,
            HomologacaoProdutoWorkflow.ESCOLA_OU_NUTRICIONISTA_RECLAMOU
        ]

        queryset = self.get_queryset_filtrado(form_data)
        queryset.order_by('criado_por')

        produtos = queryset.values_list('nome', 'marca__nome').order_by('nome', 'marca__nome')
        produtos_e_marcas = {}
        for key, value in produtos:
            produtos_e_marcas[key] = produtos_e_marcas.get(key, [])  # caso a chave não exista, criar a lista vazia
            produtos_e_marcas[key].append(value)
        return produtos_e_marcas

    @action(detail=False,
            methods=['POST'],
            url_path='filtro-por-parametros-agrupado-nome-marcas')
    def filtro_por_parametros_agrupado_nome_marcas(self, request):
        form = ProdutoPorParametrosForm(request.data)

        if not form.is_valid():
            return Response(form.errors)

        produtos_e_marcas = self.get_queryset_filtrado_agrupado(request, form)
        return Response(produtos_e_marcas)

    @action(detail=False,
            methods=['GET'],
            url_path='relatorio-por-parametros-agrupado-terceirizada')
    def relatorio_por_parametros_agrupado_terceirizada(self, request):
        form = ProdutoPorParametrosForm(request.GET)

        if not form.is_valid():
            return Response(form.errors)

        form_data = form.cleaned_data.copy()
        form_data['status'] = [
            HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO,
            HomologacaoProdutoWorkflow.ESCOLA_OU_NUTRICIONISTA_RECLAMOU
        ]

        queryset = self.get_queryset_filtrado(form_data)

        dados_agrupados = agrupa_por_terceirizada(queryset)

        return relatorio_produtos_agrupado_terceirizada(request, dados_agrupados, form_data)

    @action(detail=False,
            methods=['GET'],
            url_path='filtro-relatorio-situacao-produto')
    def filtro_relatorio_situacao_produto(self, request):
        queryset = self.filter_queryset(self.get_queryset()).distinct()
        return self.paginated_response(queryset.order_by('criado_em'))

    @action(detail=False,
            methods=['GET'],
            url_path='relatorio-situacao-produto')
    def relatorio_situacao_produto(self, request):
        queryset = self.filter_queryset(self.get_queryset()).distinct()
        filtros = self.request.query_params.dict()
        return relatorio_produtos_situacao(
            request, queryset.order_by('criado_em'), filtros)

    # TODO: Remover esse endpoint legado refatorando o frontend
    @action(detail=False,
            methods=['POST'],
            url_path='filtro-homologados-por-parametros')
    def filtro_homologados_por_parametros(self, request):
        form = ProdutoPorParametrosForm(request.data)

        if not form.is_valid():
            return Response(form.errors)

        form_data = form.cleaned_data.copy()
        form_data['status'] = [
            HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO,
            HomologacaoProdutoWorkflow.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
            HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_RECLAMACAO,
            HomologacaoProdutoWorkflow.TERCEIRIZADA_RESPONDEU_RECLAMACAO
        ]

        queryset = self.get_queryset_filtrado(form_data)
        return self.paginated_response(queryset.order_by('criado_em'))

    @action(detail=False,
            methods=['GET'],
            url_path='filtro-reclamacoes-terceirizada',
            permission_classes=[UsuarioTerceirizada])
    def filtro_reclamacoes_terceirizada(self, request):
        filtro_homologacao = {'homologacoes__reclamacoes__status':
                              ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_TERCEIRIZADA}
        filtro_reclamacao = {'status__in': [ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_TERCEIRIZADA,
                                            ReclamacaoProdutoWorkflow.RESPONDIDO_TERCEIRIZADA
                                            ]}
        qtde_questionamentos = Count('homologacoes__reclamacoes', filter=Q(
            homologacoes__reclamacoes__status=ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_TERCEIRIZADA))

        queryset = self.filter_queryset(self.get_queryset()).filter(
            **filtro_homologacao).prefetch_related(
                Prefetch('homologacoes__reclamacoes', queryset=ReclamacaoDeProduto.objects.filter(
                    **filtro_reclamacao))).annotate(
                        qtde_questionamentos=qtde_questionamentos).order_by('criado_em').distinct()

        return self.paginated_response(queryset)

    def filtra_produtos_em_analise_sensorial(self, request, queryset):
        data_analise_inicial = converte_para_datetime(
            request.query_params.get('data_analise_inicial', None))
        data_analise_final = converte_para_datetime(
            request.query_params.get('data_analise_final', None))
        para_excluir = []
        if data_analise_inicial or data_analise_final:
            filtros_data = get_filtros_data(
                data_analise_inicial, data_analise_final)
            for produto in queryset:
                ultima_homologacao = produto.ultima_homologacao
                ultima_resposta = ultima_homologacao.respostas_analise.last()
                log_analise = ultima_homologacao.logs.filter(
                    status_evento=LogSolicitacoesUsuario.CODAE_PEDIU_ANALISE_SENSORIAL,
                    **filtros_data
                ).filter(criado_em__lte=ultima_resposta.criado_em).order_by('criado_em').last()

                if log_analise is None:
                    para_excluir.append(produto.id)
        return queryset.exclude(id__in=para_excluir).order_by('nome',
                                                              'homologacoes__rastro_terceirizada__nome_fantasia')

    def filtra_produtos_suspensos_por_data(self, request, queryset):
        data_suspensao_inicial = converte_para_datetime(
            request.query_params.get('data_suspensao_inicial', None))
        data_suspensao_final = converte_para_datetime(
            request.query_params.get('data_suspensao_final', None))
        para_excluir = []
        if data_suspensao_inicial or data_suspensao_final:
            filtros_data = get_filtros_data(
                data_suspensao_inicial, data_suspensao_final)
            for produto in queryset:
                ultima_homologacao = produto.ultima_homologacao
                ultimo_log = ultima_homologacao.ultimo_log
                log_suspensao = ultima_homologacao.logs.filter(
                    id=ultimo_log.id,
                    status_evento=LogSolicitacoesUsuario.CODAE_SUSPENDEU,
                    **filtros_data
                ).first()
                if log_suspensao is None:
                    para_excluir.append(produto.id)
        return queryset.exclude(id__in=para_excluir)

    @action(detail=False,
            methods=['GET'],
            url_path='filtro-relatorio-produto-suspenso')
    def filtro_relatorio_produto_suspenso(self, request):
        queryset = self.filter_queryset(self.get_queryset()).select_related(
            'marca', 'fabricante').order_by('nome')
        queryset = self.filtra_produtos_suspensos_por_data(request, queryset)
        return self.paginated_response(queryset)

    @action(detail=False, url_path='relatorio-produto-suspenso',
            methods=['GET'])
    def relatorio_produto_suspenso(self, request):
        queryset = self.filter_queryset(self.get_queryset()).select_related(
            'marca', 'fabricante').order_by('nome')
        queryset = self.filtra_produtos_suspensos_por_data(request, queryset)
        filtros = self.request.query_params.dict()
        return relatorio_produtos_suspensos(queryset, filtros)

    @action(detail=False,
            methods=['GET'],
            url_path='filtro-relatorio-em-analise-sensorial',
            permission_classes=[UsuarioTerceirizada | UsuarioCODAEGestaoProduto])
    def filtro_relatorio_em_analise_sensorial(self, request):
        queryset = self.filter_queryset(
            self.get_queryset()).filter(homologacoes__respostas_analise__isnull=False).prefetch_related(
                Prefetch('homologacoes', queryset=HomologacaoDoProduto.objects.all().exclude(
                    respostas_analise__exact=None))).distinct()
        queryset = self.filtra_produtos_em_analise_sensorial(
            request, queryset).select_related('marca', 'fabricante')
        return self.paginated_response(queryset)

    @action(detail=False,
            methods=['GET'],
            url_path='relatorio-em-analise-sensorial',
            permission_classes=[UsuarioTerceirizada | UsuarioCODAEGestaoProduto])
    def relatorio_em_analise_sensorial(self, request):
        queryset = self.filter_queryset(
            self.get_queryset()).filter(homologacoes__respostas_analise__isnull=False).prefetch_related(
                Prefetch('homologacoes', queryset=HomologacaoDoProduto.objects.all().exclude(
                    respostas_analise__exact=None))).distinct()
        queryset = self.filtra_produtos_em_analise_sensorial(
            request, queryset).select_related('marca', 'fabricante')
        filtros = self.request.query_params.dict()
        produtos = ProdutoRelatorioAnaliseSensorialSerializer(
            queryset, many=True).data
        return relatorio_produtos_em_analise_sensorial(produtos, filtros)

    @action(detail=False,
            methods=['GET'],
            url_path='filtro-reclamacoes')
    def filtro_reclamacoes(self, request):
        filtro_reclamacao, filtro_homologacao = filtros_produto_reclamacoes(
            request)
        queryset = self.filter_queryset(
            self.get_queryset()).filter(**filtro_homologacao).prefetch_related(
                Prefetch('homologacoes__reclamacoes', queryset=ReclamacaoDeProduto.objects.filter(
                    **filtro_reclamacao))).order_by(
                        'nome').select_related('marca', 'fabricante').distinct()
        return self.paginated_response(queryset)

    @action(detail=False,
            methods=['GET'],
            url_path='filtro-avaliar-reclamacoes',
            permission_classes=[UsuarioCODAEGestaoProduto])
    def filtro_avaliar_reclamacoes(self, request):
        status_reclamacao = self.request.query_params.getlist(
            'status_reclamacao')
        queryset = self.filter_queryset(self.get_queryset()).prefetch_related('homologacoes__reclamacoes').filter(
            homologacoes__reclamacoes__status__in=status_reclamacao).order_by('nome').select_related(
                'marca', 'fabricante').distinct()
        return self.paginated_response(queryset)

    @action(detail=False,
            methods=['GET'],
            url_path='relatorio-reclamacao')
    def relatorio_reclamacao(self, request):
        filtro_reclamacao, filtro_homologacao = filtros_produto_reclamacoes(
            request)
        queryset = self.filter_queryset(
            self.get_queryset()).filter(**filtro_homologacao).prefetch_related(
                Prefetch('homologacoes__reclamacoes', queryset=ReclamacaoDeProduto.objects.filter(
                    **filtro_reclamacao))).order_by(
                        'nome').distinct()
        filtros = self.request.query_params.dict()
        return relatorio_reclamacao(queryset, filtros)

    @action(detail=False, methods=['GET'], url_path='ja-existe')
    def ja_existe(self, request):
        form = ProdutoJaExisteForm(request.GET)

        if not form.is_valid():
            return Response(form.errors)

        queryset = self.get_queryset().filter(
            **form.cleaned_data).exclude(
                homologacoes__status=HomologacaoProdutoWorkflow.RASCUNHO)

        return Response({
            'produto_existe': queryset.count() > 0
        })

    @action(detail=False, methods=['GET'], url_path='autocomplete-nomes')
    def autocomplete_nomes(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        return Response({
            'count': queryset.count(),
            'results': [value[0] for value in queryset.values_list('nome')]
        })


class CustomPagination(pagination.PageNumberPagination):
    page_size = 300


class NomeDeProdutoEditalViewSet(viewsets.ModelViewSet):
    serializer_class = NomeDeProdutoEditalSerializer
    queryset = NomeDeProdutoEdital.objects.filter(ativo=True)
    pagination_class = CustomPagination


class ProtocoloDeDietaEspecialViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = ProtocoloDeDietaEspecialSerializer
    queryset = ProtocoloDeDietaEspecial.objects.all()

    @action(detail=False, methods=['GET'], url_path='lista-nomes')
    def lista_protocolos(self, request):
        query_set = ProtocoloDeDietaEspecial.objects.filter(ativo=True)
        response = {'results': ProtocoloSimplesSerializer(
            query_set, many=True).data}
        return Response(response)


class FabricanteViewSet(viewsets.ModelViewSet, ListaNomesUnicos):
    lookup_field = 'uuid'
    serializer_class = FabricanteSerializer
    queryset = Fabricante.objects.all()

    @action(detail=False, methods=['GET'], url_path='lista-nomes')
    def lista_fabricantes(self, request):
        query_set = Fabricante.objects.all()
        filtrar_por = request.query_params.get('filtrar_por', None)
        if filtrar_por == 'reclamacoes/':
            query_set = query_set.filter(produto__homologacoes__reclamacoes__isnull=False,
                                         produto__homologacoes__status__in=['CODAE_PEDIU_ANALISE_RECLAMACAO',
                                                                            'TERCEIRIZADA_RESPONDEU_RECLAMACAO',
                                                                            'ESCOLA_OU_NUTRICIONISTA_RECLAMOU'])
        response = {'results': FabricanteSimplesSerializer(
            query_set, many=True).data}
        return Response(response)

    @action(detail=False, methods=['GET'], url_path='lista-nomes-nova-reclamacao')
    def lista_fabricantes_nova_reclamacao(self, request):
        query_set = Fabricante.objects.filter(
            produto__ativo=True,
            produto__homologacoes__status__in=NOVA_RECLAMACAO_HOMOLOGACOES_STATUS
        ).distinct('nome')
        response = {'results': FabricanteSimplesSerializer(query_set, many=True).data}
        return Response(response)

    @action(detail=False, methods=['GET'], url_path='lista-nomes-avaliar-reclamacao')
    def lista_fabricantes_avaliar_reclamacao(self, request):
        query_set = Fabricante.objects.filter(
            produto__homologacoes__status__in=AVALIAR_RECLAMACAO_HOMOLOGACOES_STATUS,
            produto__homologacoes__reclamacoes__status__in=AVALIAR_RECLAMACAO_RECLAMACOES_STATUS
        ).distinct()
        response = {'results': FabricanteSimplesSerializer(query_set, many=True).data}
        return Response(response)

    @action(detail=False, methods=['GET'], url_path='lista-nomes-responder-reclamacao')
    def lista_fabricantes_responder_reclamacao(self, request):
        user = request.user
        query_set = Fabricante.objects.filter(
            produto__homologacoes__status__in=RESPONDER_RECLAMACAO_HOMOLOGACOES_STATUS,
            produto__homologacoes__reclamacoes__status__in=RESPONDER_RECLAMACAO_RECLAMACOES_STATUS,
            produto__homologacoes__rastro_terceirizada=user.vinculo_atual.instituicao
        ).distinct()
        if user.tipo_usuario == 'terceirizada':
            query_set = query_set.filter(produto__homologacoes__rastro_terceirizada=user.vinculo_atual.instituicao)
        response = {'results': FabricanteSimplesSerializer(query_set, many=True).data}
        return Response(response)


class MarcaViewSet(viewsets.ModelViewSet, ListaNomesUnicos):
    lookup_field = 'uuid'
    serializer_class = MarcaSerializer
    queryset = Marca.objects.all()

    @action(detail=False, methods=['GET'], url_path='lista-nomes')
    def lista_marcas(self, request):
        query_set = Marca.objects.all()
        filtrar_por = request.query_params.get('filtrar_por', None)
        if filtrar_por == 'reclamacoes/':
            query_set = query_set.filter(produto__homologacoes__reclamacoes__isnull=False,
                                         produto__homologacoes__status__in=['CODAE_PEDIU_ANALISE_RECLAMACAO',
                                                                            'TERCEIRIZADA_RESPONDEU_RECLAMACAO',
                                                                            'ESCOLA_OU_NUTRICIONISTA_RECLAMOU'])
        response = {'results': MarcaSimplesSerializer(
            query_set, many=True).data}
        return Response(response)

    @action(detail=False, methods=['GET'], url_path='lista-nomes-nova-reclamacao')
    def lista_marcas_nova_reclamacao(self, request):
        query_set = Marca.objects.filter(
            produto__ativo=True,
            produto__homologacoes__status__in=NOVA_RECLAMACAO_HOMOLOGACOES_STATUS
        ).distinct('nome')
        response = {'results': MarcaSimplesSerializer(query_set, many=True).data}
        return Response(response)

    @action(detail=False, methods=['GET'], url_path='lista-nomes-avaliar-reclamacao')
    def lista_marcas_avaliar_reclamacao(self, request):
        query_set = Marca.objects.filter(
            produto__homologacoes__status__in=AVALIAR_RECLAMACAO_HOMOLOGACOES_STATUS,
            produto__homologacoes__reclamacoes__status__in=AVALIAR_RECLAMACAO_RECLAMACOES_STATUS
        ).distinct()
        response = {'results': MarcaSimplesSerializer(query_set, many=True).data}
        return Response(response)

    @action(detail=False, methods=['GET'], url_path='lista-nomes-responder-reclamacao')
    def lista_marcas_responder_reclamacao(self, request):
        user = request.user
        query_set = Marca.objects.filter(
            produto__homologacoes__status__in=RESPONDER_RECLAMACAO_HOMOLOGACOES_STATUS,
            produto__homologacoes__reclamacoes__status__in=RESPONDER_RECLAMACAO_RECLAMACOES_STATUS,
            produto__homologacoes__rastro_terceirizada=user.vinculo_atual.instituicao
        ).distinct()
        response = {'results': MarcaSimplesSerializer(query_set, many=True).data}
        return Response(response)


class InformacaoNutricionalViewSet(InformacaoNutricionalBaseViewSet):
    lookup_field = 'uuid'
    serializer_class = InformacaoNutricionalSerializer
    queryset = InformacaoNutricional.objects.all()

    @action(detail=False, methods=['GET'], url_path=f'agrupadas')
    def informacoes_nutricionais_agrupadas(self, request):
        query_set = InformacaoNutricional.objects.all().order_by('id')
        response = {'results': self._agrupa_informacoes_por_tipo(query_set)}
        return Response(response)


class RespostaAnaliseSensorialViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = RespostaAnaliseSensorialSearilzerCreate
    queryset = RespostaAnaliseSensorial.objects.all()

    @action(detail=False,
            permission_classes=[UsuarioTerceirizada],
            methods=['post'],
            url_path=constants.TERCEIRIZADA_RESPONDE_ANALISE_SENSORIAL)
    def terceirizada_responde(self, request):
        data = request.data.copy()
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors)

        uuid_homologacao = data.get('homologacao_de_produto', None)
        homologacao = HomologacaoDoProduto.objects.get(uuid=uuid_homologacao)
        data['homologacao_de_produto'] = homologacao
        try:
            serializer.create(data)
            justificativa = request.data.get('justificativa', '')
            homologacao.terceirizada_responde_analise_sensorial(
                user=request.user, justificativa=justificativa
            )
            serializer.save()
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)


class ReclamacaoProdutoViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    lookup_field = 'uuid'
    serializer_class = ReclamacaoDeProdutoSerializer
    queryset = ReclamacaoDeProduto.objects.all()

    def muda_status_com_justificativa_e_anexo(self, request, metodo_transicao):
        anexos = request.data.get('anexos', [])
        justificativa = request.data.get('justificativa', '')
        try:
            metodo_transicao(
                user=request.user,
                anexos=anexos,
                justificativa=justificativa
            )
            serializer = self.get_serializer(self.get_object())
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            permission_classes=[UsuarioCODAEGestaoProduto],
            methods=['patch'],
            url_path=constants.CODAE_ACEITA)
    def codae_aceita(self, request, uuid=None):
        reclamacao_produto = self.get_object()
        anexos = request.data.get('anexos', [])
        justificativa = request.data.get('justificativa', '')
        reclamacao_produto.homologacao_de_produto.codae_autorizou_reclamacao(
            user=request.user,
            anexos=anexos,
            justificativa=justificativa
        )
        return self.muda_status_com_justificativa_e_anexo(
            request,
            reclamacao_produto.codae_aceita)

    @action(detail=True,
            permission_classes=[UsuarioCODAEGestaoProduto],
            methods=['patch'],
            url_path=constants.CODAE_RECUSA)
    def codae_recusa(self, request, uuid=None):
        reclamacao_produto = self.get_object()
        resposta = self.muda_status_com_justificativa_e_anexo(
            request,
            reclamacao_produto.codae_recusa)
        reclamacoes_ativas = reclamacao_produto.homologacao_de_produto.reclamacoes.filter(
            status__in=[
                ReclamacaoProdutoWorkflow.AGUARDANDO_AVALIACAO,
                ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_TERCEIRIZADA,
                ReclamacaoProdutoWorkflow.RESPONDIDO_TERCEIRIZADA
            ]
        )
        if reclamacoes_ativas.count() == 0:
            reclamacao_produto.homologacao_de_produto.codae_recusou_reclamacao(
                user=request.user,
                justificativa='Recusa automática por não haver mais reclamações'
            )
        return resposta

    @action(detail=True,
            permission_classes=[UsuarioCODAEGestaoProduto],
            methods=['patch'],
            url_path=constants.CODAE_QUESTIONA)
    def codae_questiona(self, request, uuid=None):
        reclamacao_produto = self.get_object()
        homologacao_de_produto = reclamacao_produto.homologacao_de_produto
        anexos = request.data.get('anexos', [])
        justificativa = request.data.get('justificativa', '')
        status_homologacao = homologacao_de_produto.status
        if status_homologacao != HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_RECLAMACAO:
            homologacao_de_produto.codae_pediu_analise_reclamacao(
                user=request.user,
                anexos=anexos,
                justificativa=justificativa
            )
            homologacao_de_produto.rastro_terceirizada = reclamacao_produto.escola.lote.terceirizada
            homologacao_de_produto.save()
        return self.muda_status_com_justificativa_e_anexo(
            request,
            reclamacao_produto.codae_questiona)

    @action(detail=True,
            permission_classes=[UsuarioCODAEGestaoProduto],
            methods=['patch'],
            url_path=constants.CODAE_RESPONDE)
    def codae_responde(self, request, uuid=None):
        reclamacao_produto = self.get_object()
        return self.muda_status_com_justificativa_e_anexo(
            request,
            reclamacao_produto.codae_responde)

    @action(detail=True,
            methods=['patch'],
            url_path=constants.TERCEIRIZADA_RESPONDE)
    def terceirizada_responde(self, request, uuid=None):
        reclamacao_produto = self.get_object()
        anexos = request.data.get('anexos', [])
        justificativa = request.data.get('justificativa', '')
        resposta = self.muda_status_com_justificativa_e_anexo(
            request,
            reclamacao_produto.terceirizada_responde)
        questionamentos_ativas = reclamacao_produto.homologacao_de_produto.reclamacoes.filter(
            status__in=[
                ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_TERCEIRIZADA,
            ]
        )
        if questionamentos_ativas.count() == 0:
            reclamacao_produto.homologacao_de_produto.terceirizada_responde_reclamacao(
                user=request.user,
                anexos=anexos,
                justificativa=justificativa,
                request=request
            )
        return resposta


class SolicitacaoCadastroProdutoDietaFilter(filters.FilterSet):
    nome_produto = filters.CharFilter(
        field_name='nome_produto', lookup_expr='icontains')
    data_inicial = filters.DateFilter(
        field_name='criado_em', lookup_expr='date__gte')
    data_final = filters.DateFilter(
        field_name='criado_em', lookup_expr='date__lte')
    status = filters.CharFilter(field_name='status')

    class Meta:
        model = SolicitacaoCadastroProdutoDieta
        fields = ['nome_produto', 'data_inicial', 'data_final', 'status']


class SolicitacaoCadastroProdutoDietaViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    queryset = SolicitacaoCadastroProdutoDieta.objects.all().order_by('-criado_em')
    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = SolicitacaoCadastroProdutoDietaFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SolicitacaoCadastroProdutoDietaSerializerCreate
        return SolicitacaoCadastroProdutoDietaSerializer

    @action(detail=False, methods=['GET'], url_path='nomes-produtos')
    def nomes_produtos(self, request):
        return Response([s.nome_produto for s in SolicitacaoCadastroProdutoDieta.objects.only('nome_produto')])

    @transaction.atomic
    @action(detail=True, methods=['patch'], url_path='confirma-previsao')
    def confirma_previsao(self, request, uuid=None):
        solicitacao = self.get_object()
        serializer = self.get_serializer()
        try:
            serializer.update(solicitacao, request.data)
            solicitacao.terceirizada_atende_solicitacao(user=request.user)
            return Response({'detail': 'Confirmação de previsão de cadastro realizada com sucesso'})
        except InvalidTransitionError as e:
            return Response({'detail': f'Erro na transição de estado {e}'}, status=HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as e:
            return Response({'detail': f'Dados inválidos {e}'}, status=HTTP_400_BAD_REQUEST)
