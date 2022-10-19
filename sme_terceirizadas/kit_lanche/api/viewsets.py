from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.viewsets import ModelViewSet
from xworkflows import InvalidTransitionError

from ...dados_comuns import constants
from ...dados_comuns.permissions import (
    PermissaoParaRecuperarObjeto,
    PermissaoParaRecuperarSolicitacaoUnificada,
    UsuarioCODAEGestaoAlimentacao,
    UsuarioDiretoriaRegional,
    UsuarioEscola,
    UsuarioTerceirizada
)
from ...inclusao_alimentacao.api.viewsets import (
    CodaeAutoriza,
    CodaeQuestionaTerceirizadaResponde,
    DREValida,
    EscolaIniciaCancela,
    TerceirizadaTomaCiencia
)
from ...relatorios.relatorios import (
    relatorio_kit_lanche_passeio,
    relatorio_kit_lanche_passeio_cei,
    relatorio_kit_lanche_unificado
)
from .. import models
from ..api.validators import nao_deve_ter_mais_solicitacoes_que_alunos
from ..filters import KitLancheFilter
from ..models import (
    SolicitacaoKitLancheAvulsa,
    SolicitacaoKitLancheCEIAvulsa,
    SolicitacaoKitLancheCEMEI,
    SolicitacaoKitLancheUnificada
)
from ..utils import KitLanchePagination
from .serializers import serializers, serializers_create, serializers_create_cei


class KitLancheViewSet(ModelViewSet):
    lookup_field = 'uuid'
    queryset = models.KitLanche.objects.all().order_by('nome')
    serializer_class = serializers.KitLancheSerializer
    pagination_class = KitLanchePagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = KitLancheFilter

    @action(detail=False, methods=['GET'], url_path='consulta-kits')
    def lista_kits_consulta(self, request):
        queryset = self.filter_queryset(self.get_queryset().order_by('id'))
        page = self.paginate_queryset(queryset)
        serializer = serializers.KitLancheConsultaSerializer(page, many=True)
        response = self.get_paginated_response(
            serializer.data
        )
        return response

    @action(detail=False, methods=['GET'], url_path='nome-existe')
    def valida_nome_kit_lanche(self, request):
        try:
            nome = request.query_params.get('nome').upper()
            edital = request.query_params.get('edital')
            uuid = request.query_params.get('uuid')
            kit_lanche = self.queryset.get(nome=nome, edital__uuid=edital)
            if (str(kit_lanche.uuid) != uuid):
                return Response(dict(
                    detail='Esse nome de kit lanche já existe para edital selecionado'),
                    status=HTTP_200_OK)
            else:
                return Response(dict(detail='Nome válido'), status=404)
        except models.KitLanche.DoesNotExist:
            return Response(dict(detail='Nome válido'), status=404)


class SolicitacaoKitLancheAvulsaViewSet(ModelViewSet):
    lookup_field = 'uuid'
    queryset = SolicitacaoKitLancheAvulsa.objects.all()
    serializer_class = serializers.SolicitacaoKitLancheAvulsaSerializer

    def get_permissions(self):
        if self.action in ['list', 'update']:
            self.permission_classes = (IsAdminUser,)
        elif self.action == 'retrieve':
            self.permission_classes = (IsAuthenticated, PermissaoParaRecuperarObjeto)
        elif self.action in ['create', 'destroy']:
            self.permission_classes = (UsuarioEscola,)
        return super(SolicitacaoKitLancheAvulsaViewSet, self).get_permissions()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return serializers_create.SolicitacaoKitLancheAvulsaCreationSerializer
        return serializers.SolicitacaoKitLancheAvulsaSerializer

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_DRE}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioDiretoriaRegional,))
    def solicitacoes_diretoria_regional(self, request, filtro_aplicado='sem_filtro'):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        kit_lanches_avulso = diretoria_regional.solicitacoes_kit_lanche_das_minhas_escolas_a_validar(
            filtro_aplicado
        )
        page = self.paginate_queryset(kit_lanches_avulso)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_CODAE}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioCODAEGestaoAlimentacao,))
    def solicitacoes_codae(self, request, filtro_aplicado='sem_filtro'):
        usuario = request.user
        codae = usuario.vinculo_atual.instituicao
        kit_lanches_avulso = codae.solicitacoes_kit_lanche_das_minhas_escolas_a_validar(
            filtro_aplicado
        )
        page = self.paginate_queryset(kit_lanches_avulso)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_TERCEIRIZADA}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioTerceirizada,))
    def solicitacoes_terceirizadas(self, request, filtro_aplicado='sem_filtro'):
        usuario = request.user
        terceirizadas = usuario.vinculo_atual.instituicao
        kit_lanches_avulso = terceirizadas.solicitacoes_kit_lanche_das_minhas_escolas_a_validar(
            filtro_aplicado
        )
        page = self.paginate_queryset(kit_lanches_avulso)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, url_path=constants.SOLICITACOES_DO_USUARIO,
            permission_classes=(UsuarioEscola,))
    def minhas_solicitacoes(self, request):
        usuario = request.user
        solicitacoes_unificadas = self.get_queryset().filter(
            criado_por=usuario,
            status=SolicitacaoKitLancheAvulsa.workflow_class.RASCUNHO
        )
        page = self.paginate_queryset(solicitacoes_unificadas)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    #
    # IMPLEMENTAÇÃO DO FLUXO (PARTINDO DA ESCOLA)
    #

    @action(detail=True,
            methods=['patch'], url_path=constants.ESCOLA_INICIO_PEDIDO,
            permission_classes=(UsuarioEscola,))
    def inicio_de_solicitacao(self, request, uuid=None):
        solicitacao_kit_lanche_avulsa = self.get_object()
        try:
            nao_deve_ter_mais_solicitacoes_que_alunos(solicitacao_kit_lanche_avulsa)

            solicitacao_kit_lanche_avulsa.inicia_fluxo(user=request.user, )
            serializer = self.get_serializer(solicitacao_kit_lanche_avulsa)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response(dict(detail=f'{str(e.detail[0])}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['patch'], url_path=constants.DRE_VALIDA_PEDIDO,
            permission_classes=(UsuarioDiretoriaRegional,))
    def diretoria_regional_valida_solicitacao(self, request, uuid=None):
        solicitacao_kit_lanche_avulsa = self.get_object()
        try:
            solicitacao_kit_lanche_avulsa.dre_valida(user=request.user, )
            serializer = self.get_serializer(solicitacao_kit_lanche_avulsa)
            return Response(serializer.data, status=HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['patch'], url_path=constants.DRE_NAO_VALIDA_PEDIDO,
            permission_classes=(UsuarioDiretoriaRegional,))
    def diretoria_regional_nao_valida(self, request, uuid=None):
        solicitacao_kit_lanche_avulsa = self.get_object()
        justificativa = request.data.get('justificativa', '')
        try:
            solicitacao_kit_lanche_avulsa.dre_nao_valida(user=request.user, justificativa=justificativa)
            serializer = self.get_serializer(solicitacao_kit_lanche_avulsa)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['patch'], url_path=constants.CODAE_QUESTIONA_PEDIDO,
            permission_classes=(UsuarioCODAEGestaoAlimentacao,))
    def codae_questiona_solicitacao(self, request, uuid=None):
        solicitacao_kit_lanche_avulsa = self.get_object()
        observacao_questionamento_codae = request.data.get('observacao_questionamento_codae', '')
        try:
            solicitacao_kit_lanche_avulsa.codae_questiona(
                user=request.user,
                justificativa=observacao_questionamento_codae
            )
            serializer = self.get_serializer(solicitacao_kit_lanche_avulsa)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['patch'], url_path=constants.CODAE_AUTORIZA_PEDIDO,
            permission_classes=(UsuarioCODAEGestaoAlimentacao,))
    def codae_autoriza_solicitacao(self, request, uuid=None):
        solicitacao_kit_lanche_avulsa = self.get_object()
        justificativa = request.data.get('justificativa', '')
        try:
            if solicitacao_kit_lanche_avulsa.status == solicitacao_kit_lanche_avulsa.workflow_class.DRE_VALIDADO:
                solicitacao_kit_lanche_avulsa.codae_autoriza(user=request.user)
            else:
                solicitacao_kit_lanche_avulsa.codae_autoriza_questionamento(user=request.user,
                                                                            justificativa=justificativa)
            serializer = self.get_serializer(solicitacao_kit_lanche_avulsa)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['patch'], url_path=constants.CODAE_NEGA_PEDIDO,
            permission_classes=(UsuarioCODAEGestaoAlimentacao,))
    def codae_nega_solicitacao(self, request, uuid=None):
        solicitacao_kit_lanche_avulsa = self.get_object()
        justificativa = request.data.get('justificativa', '')
        try:
            if solicitacao_kit_lanche_avulsa.status == solicitacao_kit_lanche_avulsa.workflow_class.DRE_VALIDADO:
                solicitacao_kit_lanche_avulsa.codae_nega(user=request.user, justificativa=justificativa)
            else:
                solicitacao_kit_lanche_avulsa.codae_nega_questionamento(user=request.user, justificativa=justificativa)
            serializer = self.get_serializer(solicitacao_kit_lanche_avulsa)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['patch'], url_path=constants.TERCEIRIZADA_RESPONDE_QUESTIONAMENTO,
            permission_classes=(UsuarioTerceirizada,))
    def terceirizada_responde_questionamento(self, request, uuid=None):
        solicitacao_kit_lanche_avulsa = self.get_object()
        justificativa = request.data.get('justificativa', '')
        resposta_sim_nao = request.data.get('resposta_sim_nao', False)
        try:
            solicitacao_kit_lanche_avulsa.terceirizada_responde_questionamento(user=request.user,
                                                                               justificativa=justificativa,
                                                                               resposta_sim_nao=resposta_sim_nao)
            serializer = self.get_serializer(solicitacao_kit_lanche_avulsa)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['patch'], url_path=constants.TERCEIRIZADA_TOMOU_CIENCIA,
            permission_classes=(UsuarioTerceirizada,))
    def terceirizada_toma_ciencia(self, request, uuid=None):
        solicitacao_kit_lanche_avulsa = self.get_object()
        try:
            solicitacao_kit_lanche_avulsa.terceirizada_toma_ciencia(user=request.user, )
            serializer = self.get_serializer(solicitacao_kit_lanche_avulsa)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['patch'], url_path=constants.ESCOLA_CANCELA,
            permission_classes=(UsuarioEscola,))
    def escola_cancela_solicitacao(self, request, uuid=None):
        justificativa = request.data.get('justificativa', '')
        solicitacao_kit_lanche_avulsa = self.get_object()
        try:
            solicitacao_kit_lanche_avulsa.cancelar_pedido(user=request.user,
                                                          justificativa=justificativa)
            serializer = self.get_serializer(solicitacao_kit_lanche_avulsa)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        solicitacao_kit_lanche_avulsa = self.get_object()
        if solicitacao_kit_lanche_avulsa.pode_excluir:
            return super().destroy(request, *args, **kwargs)
        else:
            return Response(dict(detail='Você só pode excluir quando o status for RASCUNHO.'),
                            status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, url_path=constants.RELATORIO,
            methods=['get'])
    def relatorio(self, request, uuid=None):
        return relatorio_kit_lanche_passeio(request, solicitacao=self.get_object())

    @action(detail=True,
            methods=['patch'],
            url_path=constants.MARCAR_CONFERIDA,
            permission_classes=(IsAuthenticated,))
    def terceirizada_marca_inclusao_como_conferida(self, request, uuid=None):
        solicitacao_kit_lanche_avulsa: SolicitacaoKitLancheAvulsa = self.get_object()
        try:
            solicitacao_kit_lanche_avulsa.terceirizada_conferiu_gestao = True
            solicitacao_kit_lanche_avulsa.save()
            serializer = self.get_serializer(solicitacao_kit_lanche_avulsa)
            return Response(serializer.data)
        except Exception as e:
            return Response(dict(detail=f'Erro ao marcar solicitação como conferida: {e}'), status=status.HTTP_400_BAD_REQUEST)  # noqa


class SolicitacaoKitLancheUnificadaViewSet(ModelViewSet):
    lookup_field = 'uuid'
    queryset = SolicitacaoKitLancheUnificada.objects.all()
    serializer_class = serializers.SolicitacaoKitLancheUnificadaSerializer

    def get_permissions(self):
        if self.action in ['list']:
            self.permission_classes = (IsAdminUser,)
        elif self.action in ['retrieve', 'update']:
            self.permission_classes = (IsAuthenticated, PermissaoParaRecuperarSolicitacaoUnificada)
        elif self.action in ['create', 'destroy']:
            self.permission_classes = (UsuarioDiretoriaRegional,)
        return super(SolicitacaoKitLancheUnificadaViewSet, self).get_permissions()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return serializers_create.SolicitacaoKitLancheUnificadaCreationSerializer
        return serializers.SolicitacaoKitLancheUnificadaSerializer

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_CODAE}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioCODAEGestaoAlimentacao,))
    def solicitacoes_codae(self, request, filtro_aplicado=constants.SEM_FILTRO):
        # TODO: colocar regras de codae CODAE aqui...
        usuario = request.user
        codae = usuario.vinculo_atual.instituicao
        solicitacoes_unificadas = codae.solicitacoes_unificadas(
            filtro_aplicado
        )
        page = self.paginate_queryset(solicitacoes_unificadas)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_TERCEIRIZADA}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioTerceirizada,))
    def solicitacoes_terceirizada(self, request, filtro_aplicado=constants.SEM_FILTRO):
        # TODO: colocar regras de Terceirizada aqui...
        usuario = request.user
        terceirizada = usuario.vinculo_atual.instituicao
        solicitacoes_unificadas = terceirizada.solicitacoes_unificadas_das_minhas_escolas(
            filtro_aplicado
        )
        page = self.paginate_queryset(solicitacoes_unificadas)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, url_path=constants.SOLICITACOES_DO_USUARIO,
            permission_classes=(UsuarioDiretoriaRegional,))
    def minhas_solicitacoes(self, request):
        usuario = request.user
        solicitacoes_unificadas = SolicitacaoKitLancheUnificada.get_pedidos_rascunho(usuario)
        page = self.paginate_queryset(solicitacoes_unificadas)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, url_path=constants.RELATORIO,
            methods=['get'])
    def relatorio(self, request, uuid=None):
        return relatorio_kit_lanche_unificado(request, solicitacao=self.get_object())

    #
    # IMPLEMENTAÇÃO DO FLUXO (PARTINDO DA DRE)
    #

    @action(detail=True, url_path=constants.DRE_INICIO_PEDIDO, methods=['patch'],
            permission_classes=(UsuarioDiretoriaRegional,))
    def inicio_de_solicitacao(self, request, uuid=None):
        solicitacao_unificada = self.get_object()
        try:
            solicitacoes_unificadas = solicitacao_unificada.dividir_por_lote()
            for solicitacao_unificada in solicitacoes_unificadas:
                solicitacao_unificada.inicia_fluxo(user=request.user)
            serializer = self.get_serializer(solicitacoes_unificadas, many=True)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True, url_path=constants.CODAE_AUTORIZA_PEDIDO, methods=['patch'],
            permission_classes=(UsuarioCODAEGestaoAlimentacao,))
    def codae_autoriza(self, request, uuid=None):
        solicitacao_unificada = self.get_object()
        justificativa = request.data.get('justificativa', '')
        try:
            if solicitacao_unificada.status == solicitacao_unificada.workflow_class.CODAE_A_AUTORIZAR:
                solicitacao_unificada.codae_autoriza(user=request.user)
            else:
                solicitacao_unificada.codae_autoriza_questionamento(user=request.user, justificativa=justificativa)
            serializer = self.get_serializer(solicitacao_unificada)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True, url_path=constants.CODAE_NEGA_PEDIDO, methods=['patch'],
            permission_classes=(UsuarioCODAEGestaoAlimentacao,))
    def codae_nega_solicitacao(self, request, uuid=None):
        solicitacao_unificada = self.get_object()
        justificativa = request.data.get('justificativa', '')
        try:
            if solicitacao_unificada.status == solicitacao_unificada.workflow_class.CODAE_A_AUTORIZAR:
                solicitacao_unificada.codae_nega(user=request.user, justificativa=justificativa)
            else:
                solicitacao_unificada.codae_nega_questionamento(user=request.user, justificativa=justificativa)
            serializer = self.get_serializer(solicitacao_unificada)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path=constants.CODAE_QUESTIONA_PEDIDO,
            permission_classes=(UsuarioCODAEGestaoAlimentacao,))
    def codae_questiona_solicitacao(self, request, uuid=None):
        solicitacao_unificada = self.get_object()
        observacao_questionamento_codae = request.data.get('observacao_questionamento_codae', '')
        try:
            solicitacao_unificada.codae_questiona(
                user=request.user,
                justificativa=observacao_questionamento_codae
            )
            serializer = self.get_serializer(solicitacao_unificada)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True, url_path=constants.TERCEIRIZADA_TOMOU_CIENCIA, methods=['patch'],
            permission_classes=(UsuarioTerceirizada,))
    def terceirizada_toma_ciencia(self, request, uuid=None):
        solicitacao_unificada = self.get_object()
        try:
            solicitacao_unificada.terceirizada_toma_ciencia(user=request.user, )
            serializer = self.get_serializer(solicitacao_unificada)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path=constants.TERCEIRIZADA_RESPONDE_QUESTIONAMENTO,
            permission_classes=(UsuarioTerceirizada,))
    def terceirizada_responde_questionamento(self, request, uuid=None):
        solicitacao_unificada = self.get_object()
        justificativa = request.data.get('justificativa', '')
        resposta_sim_nao = request.data.get('resposta_sim_nao', False)
        try:
            solicitacao_unificada.terceirizada_responde_questionamento(user=request.user,
                                                                       justificativa=justificativa,
                                                                       resposta_sim_nao=resposta_sim_nao)
            serializer = self.get_serializer(solicitacao_unificada)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    @action(detail=True, url_path=constants.DRE_CANCELA, methods=['patch'],
            permission_classes=(UsuarioDiretoriaRegional,))
    def diretoria_regional_cancela(self, request, uuid=None):
        justificativa = request.data.get('justificativa', '')
        solicitacao_unificada = self.get_object()
        try:
            solicitacao_unificada.cancelar_pedido(user=request.user, justificativa=justificativa)
            serializer = self.get_serializer(solicitacao_unificada)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        solicitacao_kit_lanche_unificada = self.get_object()
        if solicitacao_kit_lanche_unificada.pode_excluir:
            return super().destroy(request, *args, **kwargs)
        else:
            return Response(dict(detail='Você só pode excluir quando o status for RASCUNHO.'),
                            status=status.HTTP_403_FORBIDDEN)

    @action(detail=True,
            methods=['patch'],
            url_path=constants.MARCAR_CONFERIDA,
            permission_classes=(IsAuthenticated,))
    def terceirizada_marca_inclusao_como_conferida(self, request, uuid=None):
        solicitacao_kit_lanche_unificado: SolicitacaoKitLancheUnificada = self.get_object()
        try:
            solicitacao_kit_lanche_unificado.terceirizada_conferiu_gestao = True
            solicitacao_kit_lanche_unificado.save()
            serializer = self.get_serializer(solicitacao_kit_lanche_unificado)
            return Response(serializer.data)
        except Exception as e:
            return Response(dict(detail=f'Erro ao marcar solicitação como conferida: {e}'), status=status.HTTP_400_BAD_REQUEST)  # noqa


class SolicitacaoKitLancheCEIAvulsaViewSet(SolicitacaoKitLancheAvulsaViewSet):
    lookup_field = 'uuid'
    queryset = SolicitacaoKitLancheCEIAvulsa.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return serializers_create_cei.SolicitacaoKitLancheCEIAvulsaCreationSerializer
        return serializers.SolicitacaoKitLancheCEIAvulsaSerializer

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_DRE}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioDiretoriaRegional,))
    def solicitacoes_diretoria_regional(self, request, filtro_aplicado='sem_filtro'):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        kit_lanches_avulso = diretoria_regional.solicitacoes_kit_lanche_cei_das_minhas_escolas_a_validar(
            filtro_aplicado
        )
        page = self.paginate_queryset(kit_lanches_avulso)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_CODAE}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioCODAEGestaoAlimentacao,))
    def solicitacoes_codae(self, request, filtro_aplicado='sem_filtro'):
        usuario = request.user
        codae = usuario.vinculo_atual.instituicao
        kit_lanches_avulso = codae.solicitacoes_kit_lanche_cei_das_minhas_escolas_a_validar(
            filtro_aplicado
        )
        page = self.paginate_queryset(kit_lanches_avulso)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_TERCEIRIZADA}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioTerceirizada,))
    def solicitacoes_terceirizadas(self, request, filtro_aplicado='sem_filtro'):
        usuario = request.user
        terceirizadas = usuario.vinculo_atual.instituicao
        kit_lanches_avulso = terceirizadas.solicitacoes_kit_lanche_cei_das_minhas_escolas_a_validar(
            filtro_aplicado
        )
        page = self.paginate_queryset(kit_lanches_avulso)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, url_path=constants.SOLICITACOES_DO_USUARIO,
            permission_classes=(UsuarioEscola,))
    def minhas_solicitacoes(self, request):
        usuario = request.user
        solicitacoes_unificadas = self.get_queryset().filter(
            criado_por=usuario,
            status=SolicitacaoKitLancheAvulsa.workflow_class.RASCUNHO
        )
        page = self.paginate_queryset(solicitacoes_unificadas)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, url_path=constants.RELATORIO,
            methods=['get'])
    def relatorio(self, request, uuid=None):
        return relatorio_kit_lanche_passeio_cei(request, solicitacao=self.get_object())

    @action(detail=True,
            methods=['patch'],
            url_path=constants.MARCAR_CONFERIDA,
            permission_classes=(IsAuthenticated,))
    def terceirizada_marca_inclusao_como_conferida(self, request, uuid=None):
        solicitacao_kit_lanche_cei_avulsa: SolicitacaoKitLancheCEIAvulsa = self.get_object()
        try:
            solicitacao_kit_lanche_cei_avulsa.terceirizada_conferiu_gestao = True
            solicitacao_kit_lanche_cei_avulsa.save()
            serializer = self.get_serializer(solicitacao_kit_lanche_cei_avulsa)
            return Response(serializer.data)
        except Exception as e:
            return Response(dict(detail=f'Erro ao marcar solicitação como conferida: {e}'), status=status.HTTP_400_BAD_REQUEST)  # noqa


class SolicitacaoKitLancheCEMEIViewSet(ModelViewSet, CodaeAutoriza, CodaeQuestionaTerceirizadaResponde, DREValida,
                                       EscolaIniciaCancela, TerceirizadaTomaCiencia):
    lookup_field = 'uuid'
    queryset = SolicitacaoKitLancheCEMEI.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return serializers_create.SolicitacaoKitLancheCEMEICreateSerializer
        if self.action == 'retrieve':
            return serializers.SolicitacaoKitLancheCEMEIRetrieveSerializer
        return serializers.SolicitacaoKitLancheCEMEISerializer

    def get_permissions(self):
        if self.action in ['list']:
            self.permission_classes = (UsuarioEscola,)
        elif self.action in ['retrieve', 'update']:
            self.permission_classes = (
                IsAuthenticated, PermissaoParaRecuperarObjeto)
        elif self.action in ['create', 'destroy']:
            self.permission_classes = (UsuarioEscola,)
        return super(SolicitacaoKitLancheCEMEIViewSet, self).get_permissions()

    def get_queryset(self):
        queryset = SolicitacaoKitLancheCEMEI.objects.all()
        user = self.request.user
        if user.tipo_usuario == 'escola':
            queryset = queryset.filter(escola=user.vinculo_atual.instituicao)
        if user.tipo_usuario == 'diretoriaregional':
            queryset = queryset.filter(rastro_dre=user.vinculo_atual.instituicao)
        if 'status' in self.request.query_params:
            queryset = queryset.filter(status=self.request.query_params.get('status').upper())
        return queryset

    def destroy(self, request, *args, **kwargs):
        solicitacao_kit_lanche_cemei = self.get_object()
        if not solicitacao_kit_lanche_cemei.pode_excluir:
            return Response(dict(detail='Você só pode excluir quando o status for RASCUNHO.'),
                            status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_DRE}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioDiretoriaRegional,))
    def solicitacoes_diretoria_regional(self, request, filtro_aplicado='sem_filtro'):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        kit_lanches_cemei = diretoria_regional.solicitacoes_kit_lanche_cemei_das_minhas_escolas_a_validar(
            filtro_aplicado
        )
        page = self.paginate_queryset(kit_lanches_cemei)
        serializer = serializers.SolicitacaoKitLancheCEMEIRetrieveSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_CODAE}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioCODAEGestaoAlimentacao,))
    def solicitacoes_codae(self, request, filtro_aplicado='sem_filtro'):
        usuario = request.user
        codae = usuario.vinculo_atual.instituicao
        kit_lanches_cemei = codae.solicitacoes_kit_lanche_cemei_das_minhas_escolas_a_validar(
            filtro_aplicado
        )
        page = self.paginate_queryset(kit_lanches_cemei)
        serializer = serializers.SolicitacaoKitLancheCEMEIRetrieveSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)
