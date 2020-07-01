from datetime import timedelta

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from xworkflows import InvalidTransitionError

from ...dados_comuns import constants
from ...dados_comuns.fluxo_status import HomologacaoProdutoWorkflow
from ...dados_comuns.permissions import PermissaoParaReclamarDeProduto, UsuarioCODAEGestaoProduto, UsuarioTerceirizada
from ...relatorios.relatorios import (
    relatorio_produto_analise_sensorial,
    relatorio_produto_analise_sensorial_recebimento,
    relatorio_produto_homologacao,
    relatorio_produtos_agrupado_terceirizada
)
from ...terceirizada.api.serializers.serializers import TerceirizadaSimplesSerializer
from ..forms import ProdutoPorParametrosForm
from ..models import (
    Fabricante,
    HomologacaoDoProduto,
    ImagemDoProduto,
    InformacaoNutricional,
    Marca,
    Produto,
    ProtocoloDeDietaEspecial,
    RespostaAnaliseSensorial
)
from ..utils import agrupa_por_terceirizada
from .serializers.serializers import (
    FabricanteSerializer,
    FabricanteSimplesSerializer,
    HomologacaoProdutoPainelGerencialSerializer,
    HomologacaoProdutoSerializer,
    ImagemDoProdutoSerializer,
    InformacaoNutricionalSerializer,
    MarcaSerializer,
    MarcaSimplesSerializer,
    ProdutoSerializer,
    ProdutoSimplesSerializer,
    ProtocoloDeDietaEspecialSerializer,
    ProtocoloSimplesSerializer,
    ReclamacaoDeProdutoSimplesSerializer
)
from .serializers.serializers_create import (
    ProdutoSerializerCreate,
    ReclamacaoDeProdutoSerializerCreate,
    RespostaAnaliseSensorialSearilzerCreate
)


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
            HomologacaoDoProduto.workflow_class.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
            HomologacaoDoProduto.workflow_class.CODAE_PEDIU_ANALISE_RECLAMACAO,
            HomologacaoDoProduto.workflow_class.CODAE_SUSPENDEU,
            HomologacaoDoProduto.workflow_class.CODAE_HOMOLOGADO,
            HomologacaoDoProduto.workflow_class.CODAE_NAO_HOMOLOGADO,
            HomologacaoDoProduto.workflow_class.CODAE_AUTORIZOU_RECLAMACAO
        ]

        if self.request.user.tipo_usuario in [constants.TIPO_USUARIO_TERCEIRIZADA,
                                              constants.TIPO_USUARIO_GESTAO_PRODUTO]:
            lista_status.append(HomologacaoDoProduto.workflow_class.CODAE_QUESTIONADO)
            lista_status.append(HomologacaoDoProduto.workflow_class.TERCEIRIZADA_RESPONDEU_RECLAMACAO)
            lista_status.append(HomologacaoDoProduto.workflow_class.CODAE_PEDIU_ANALISE_SENSORIAL)
            lista_status.append(HomologacaoDoProduto.workflow_class.CODAE_PENDENTE_HOMOLOGACAO)

        return lista_status

    def dados_dashboard(self, query_set: list) -> dict:
        sumario = []
        for workflow_status in self.get_lista_status():
            sumario.append({
                'status': workflow_status,
                'dados': self.get_serializer(query_set.filter(status=workflow_status),
                                             context={'request': self.request}, many=True).data
            })

        return sumario

    def get_queryset_dashboard(self):
        query_set = self.get_queryset()
        user = self.request.user
        if user.tipo_usuario == constants.TIPO_USUARIO_TERCEIRIZADA:
            query_set = query_set.filter(rastro_terceirizada=user.vinculo_atual.instituicao)
        return query_set

    @action(detail=False, methods=['GET'], url_path='dashboard')
    def dashboard(self, request):
        query_set = self.get_queryset_dashboard()
        response = {'results': self.dados_dashboard(query_set=query_set)}
        return Response(response)

    @action(detail=False,
            methods=['GET'],
            url_path=f'filtro-por-status/{constants.FILTRO_STATUS_HOMOLOGACAO}')
    def solicitacoes_homologacao_por_status(self, request, filtro_aplicado=constants.RASCUNHO):
        query_set = self.get_queryset_dashboard()
        if filtro_aplicado:
            if filtro_aplicado == 'codae_pediu_analise_reclamacao':
                query_set = query_set.filter(status__in=['ESCOLA_OU_NUTRICIONISTA_RECLAMOU',
                                                         'CODAE_PEDIU_ANALISE_RECLAMACAO',
                                                         'TERCEIRIZADA_RESPONDEU_RECLAMACAO'])
            else:
                query_set = query_set.filter(status=filtro_aplicado.upper())
        serializer = self.get_serializer if filtro_aplicado != constants.RASCUNHO else HomologacaoProdutoSerializer
        response = {'results': serializer(query_set, context={'request': request}, many=True).data}
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
        try:
            homologacao_produto.codae_homologa(
                user=request.user,
                link_pdf=reverse(
                    'Produtos-relatorio',
                    args=[homologacao_produto.produto.uuid],
                    request=request
                ))
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
        try:
            justificativa = request.data.get('justificativa', '')
            homologacao_produto.codae_nao_homologa(
                user=request.user,
                justificativa=justificativa,
                link_pdf=reverse(
                    'Produtos-relatorio',
                    args=[homologacao_produto.produto.uuid],
                    request=request
                )
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
        try:
            justificativa = request.data.get('justificativa', '')
            homologacao_produto.codae_questiona(
                user=request.user,
                justificativa=justificativa,
                link_pdf=reverse(
                    'Produtos-relatorio',
                    args=[homologacao_produto.produto.uuid],
                    request=request
                ))
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
        try:
            justificativa = request.data.get('justificativa', '')
            homologacao_produto.codae_pede_analise_sensorial(
                user=request.user, justificativa=justificativa,
                link_pdf=reverse(
                    'Produtos-relatorio',
                    args=[homologacao_produto.produto.uuid],
                    request=request
                ))
            homologacao_produto.gera_protocolo_analise_sensorial()
            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            permission_classes=[PermissaoParaReclamarDeProduto],
            methods=['patch'],
            url_path=constants.ESCOLA_OU_NUTRI_RECLAMA)
    def escola_ou_nutricodae_reclama(self, request, uuid=None):
        homologacao_produto = self.get_object()
        data = request.data.copy()
        data['homologacao_de_produto'] = homologacao_produto.id
        data['vinculo'] = request.user.vinculo_atual.id
        data['criado_por'] = request.user
        try:
            serializer_reclamacao = ReclamacaoDeProdutoSerializerCreate(data=data)
            if not serializer_reclamacao.is_valid():
                return Response(serializer_reclamacao.errors)
            serializer_reclamacao.save()
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
            homologacao_produto.terceirizada_responde_reclamacao(request=request)
            return Response('Reclamação respondida')
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['GET'], url_path='reclamacao')
    def reclamacao_homologao(self, request, uuid=None):
        homologacao_produto = self.get_object()
        reclamacao = homologacao_produto.reclamacoes.last()
        serializer = ReclamacaoDeProdutoSimplesSerializer(reclamacao)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='numero_protocolo')
    def numero_relatorio_analise_sensorial(self, request):
        homologacao = HomologacaoDoProduto()
        protocolo = homologacao.retorna_numero_do_protocolo()
        return Response(protocolo)

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

    def destroy(self, request, *args, **kwargs):
        homologacao_produto = self.get_object()
        if homologacao_produto.pode_excluir:
            return super().destroy(request, *args, **kwargs)
        else:
            return Response(dict(detail='Você só pode excluir quando o status for RASCUNHO.'),
                            status=status.HTTP_403_FORBIDDEN)


class ProdutoViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = ProdutoSerializer
    queryset = Produto.objects.all()

    def paginated_response(self, queryset):
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, context={'request': self.request}, many=True)
        return self.get_paginated_response(serializer.data)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProdutoSerializerCreate
        return ProdutoSerializer

    @action(detail=False, methods=['GET'], url_path='lista-nomes')
    def lista_produtos(self, request):
        query_set = Produto.objects.filter(ativo=True)
        filtrar_por = request.query_params.get('filtrar_por', None)
        if filtrar_por == 'reclamacoes/':
            query_set = query_set.filter(homologacoes__reclamacoes__isnull=False,
                                         homologacoes__status__in=['CODAE_PEDIU_ANALISE_RECLAMACAO',
                                                                   'TERCEIRIZADA_RESPONDEU_RECLAMACAO',
                                                                   'ESCOLA_OU_NUTRICIONISTA_RECLAMOU'])
        response = {'results': ProdutoSimplesSerializer(query_set, many=True).data}
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

    @action(detail=True, url_path=constants.RELATORIO_ANALISE,
            methods=['get'], permission_classes=(AllowAny,))
    def relatorio_analise_sensorial(self, request, uuid=None):
        return relatorio_produto_analise_sensorial(request, produto=self.get_object())

    @action(detail=True, url_path=constants.RELATORIO_RECEBIMENTO,
            methods=['get'], permission_classes=(AllowAny,))
    def relatorio_analise_sensorial_recebimento(self, request, uuid=None):
        return relatorio_produto_analise_sensorial_recebimento(request, produto=self.get_object())

    def get_queryset_filtrado(self, cleaned_data, request):  # noqa C901
        campos_a_pesquisar = {}
        for (chave, valor) in cleaned_data.items():
            if valor != '' and valor is not None:
                if chave == 'nome_fabricante':
                    campos_a_pesquisar['fabricante__nome__icontains'] = valor
                elif chave == 'nome_marca':
                    campos_a_pesquisar['marca__nome__icontains'] = valor
                elif chave == 'nome_produto':
                    campos_a_pesquisar['nome__icontains'] = valor
                elif chave == 'nome_terceirizada':
                    campos_a_pesquisar['homologacoes__rastro_terceirizada__nome_fantasia__icontains'] = valor
                elif chave == 'data_inicial':
                    campos_a_pesquisar['homologacoes__criado_em__gte'] = valor
                elif chave == 'data_final':
                    campos_a_pesquisar['homologacoes__criado_em__lt'] = valor + timedelta(days=1)
                elif chave == 'status' and len(valor) > 0:
                    campos_a_pesquisar['homologacoes__status__in'] = valor

        return self.get_queryset().filter(**campos_a_pesquisar)

    @action(detail=False,
            methods=['POST'],
            url_path='filtro-por-parametros')
    def filtro_por_parametros(self, request):
        form = ProdutoPorParametrosForm(request.data)

        if not form.is_valid():
            return Response(form.errors)

        queryset = self.get_queryset_filtrado(form.cleaned_data, request)
        return self.paginated_response(queryset)

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

        queryset = self.get_queryset_filtrado(form_data, request)
        queryset.order_by('criado_por')

        dados_agrupados = agrupa_por_terceirizada(queryset)

        return Response(self.serializa_agrupamento(dados_agrupados))

    @action(detail=False,
            methods=['GET'],
            url_path='relatorio-por-parametros-agrupado-terceirizada',
            permission_classes=(AllowAny,))
    def relatorio_por_parametros_agrupado_terceirizada(self, request):
        form = ProdutoPorParametrosForm(request.GET)

        if not form.is_valid():
            return Response(form.errors)

        form_data = form.cleaned_data.copy()
        form_data['status'] = [
            HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO,
            HomologacaoProdutoWorkflow.ESCOLA_OU_NUTRICIONISTA_RECLAMOU
        ]

        queryset = self.get_queryset_filtrado(form_data, request)

        dados_agrupados = agrupa_por_terceirizada(queryset)

        return relatorio_produtos_agrupado_terceirizada(
            request, dados_agrupados, form_data)

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
            HomologacaoProdutoWorkflow.ESCOLA_OU_NUTRICIONISTA_RECLAMOU
        ]

        queryset = self.get_queryset_filtrado(form_data, request)
        return self.paginated_response(queryset)


class ProtocoloDeDietaEspecialViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = ProtocoloDeDietaEspecialSerializer
    queryset = ProtocoloDeDietaEspecial.objects.all()

    @action(detail=False, methods=['GET'], url_path='lista-nomes')
    def lista_protocolos(self, request):
        query_set = ProtocoloDeDietaEspecial.objects.filter(ativo=True)
        response = {'results': ProtocoloSimplesSerializer(query_set, many=True).data}
        return Response(response)


class FabricanteViewSet(viewsets.ModelViewSet):
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
        response = {'results': FabricanteSimplesSerializer(query_set, many=True).data}
        return Response(response)


class MarcaViewSet(viewsets.ModelViewSet):
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
        response = {'results': MarcaSimplesSerializer(query_set, many=True).data}
        return Response(response)


class InformacaoNutricionalViewSet(InformacaoNutricionalBaseViewSet):
    lookup_field = 'uuid'
    serializer_class = InformacaoNutricionalSerializer
    queryset = InformacaoNutricional.objects.all()

    @action(detail=False, methods=['GET'], url_path=f'agrupadas')
    def informacoes_nutricionais_agrupadas(self, request):
        query_set = InformacaoNutricional.objects.all()
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
