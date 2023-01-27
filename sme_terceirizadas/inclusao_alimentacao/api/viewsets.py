from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from xworkflows import InvalidTransitionError

from ...cardapio.models import AlteracaoCardapioCEMEI
from ...dados_comuns import constants, services
from ...dados_comuns.permissions import (
    PermissaoParaRecuperarObjeto,
    UsuarioCODAEGestaoAlimentacao,
    UsuarioDiretoriaRegional,
    UsuarioEscola,
    UsuarioTerceirizada
)
from ...kit_lanche.models import SolicitacaoKitLancheCEMEI
from ...relatorios.relatorios import (
    relatorio_inclusao_alimentacao_cei,
    relatorio_inclusao_alimentacao_cemei,
    relatorio_inclusao_alimentacao_continua,
    relatorio_inclusao_alimentacao_normal
)
from ..models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
    InclusaoAlimentacaoDaCEI,
    InclusaoDeAlimentacaoCEMEI,
    MotivoInclusaoContinua,
    MotivoInclusaoNormal
)
from .serializers import serializers, serializers_create


# TODO: Mover as proximas classes para o devido lugar e injetar nos outros
# tipos de solicitação
class EscolaIniciaCancela():

    @action(detail=True,
            permission_classes=(UsuarioEscola,),
            methods=['patch'],
            url_path=constants.ESCOLA_INICIO_PEDIDO)
    def inicio_de_pedido(self, request, uuid=None):
        obj = self.get_object()
        try:
            obj.inicia_fluxo(user=request.user, )
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            permission_classes=(UsuarioEscola,),
            methods=['patch'],
            url_path=constants.ESCOLA_CANCELA)
    def escola_cancela_pedido(self, request, uuid=None):
        obj = self.get_object()
        datas = request.data.get('datas', [])
        justificativa = request.data.get('justificativa', '')
        try:
            if (type(obj) in [SolicitacaoKitLancheCEMEI, AlteracaoCardapioCEMEI] or
                    len(datas) + obj.inclusoes.filter(cancelado=True).count() == obj.inclusoes.count()):
                # ISSO OCORRE QUANDO O CANCELAMENTO É TOTAL
                obj.cancelar_pedido(user=request.user, justificativa=justificativa)
            else:
                services.enviar_email_ue_cancelar_pedido_parcialmente(obj)
                obj.inclusoes.filter(data__in=datas).update(cancelado=True, cancelado_justificativa=justificativa)
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=status.HTTP_400_BAD_REQUEST)


class DREValida():

    @action(detail=True,
            permission_classes=(UsuarioDiretoriaRegional,),
            methods=['patch'],
            url_path=constants.DRE_VALIDA_PEDIDO)
    def diretoria_regional_valida(self, request, uuid=None):
        obj = self.get_object()
        try:
            obj.dre_valida(user=request.user)
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            permission_classes=(UsuarioDiretoriaRegional,),
            methods=['patch'],
            url_path=constants.DRE_NAO_VALIDA_PEDIDO)
    def diretoria_regional_nao_valida_pedido(self, request, uuid=None):
        obj = self.get_object()
        justificativa = request.data.get('justificativa', '')
        try:
            obj.dre_nao_valida(user=request.user, justificativa=justificativa)
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=status.HTTP_400_BAD_REQUEST)


class CodaeAutoriza():

    @action(detail=True,
            permission_classes=(UsuarioCODAEGestaoAlimentacao,),
            methods=['patch'],
            url_path=constants.CODAE_NEGA_PEDIDO)
    def codae_nega_pedido(self, request, uuid=None):
        obj = self.get_object()
        justificativa = request.data.get('justificativa', '')
        try:
            if obj.status == obj.workflow_class.DRE_VALIDADO:
                obj.codae_nega(user=request.user, justificativa=justificativa)
            else:
                obj.codae_nega_questionamento(user=request.user, justificativa=justificativa)
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            permission_classes=(UsuarioCODAEGestaoAlimentacao,),
            methods=['patch'],
            url_path=constants.CODAE_AUTORIZA_PEDIDO)
    def codae_autoriza_pedido(self, request, uuid=None):
        obj = self.get_object()
        justificativa = request.data.get('justificativa', '')
        try:
            if obj.status == obj.workflow_class.DRE_VALIDADO:
                obj.codae_autoriza(user=request.user)
            else:
                obj.codae_autoriza_questionamento(
                    user=request.user, justificativa=justificativa)
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=status.HTTP_400_BAD_REQUEST)


class CodaeQuestionaTerceirizadaResponde():

    @action(detail=True,
            permission_classes=(UsuarioCODAEGestaoAlimentacao,),
            methods=['patch'],
            url_path=constants.CODAE_QUESTIONA_PEDIDO)
    def codae_questiona_pedido(self, request, uuid=None):
        obj = self.get_object()
        observacao_questionamento_codae = request.data.get(
            'observacao_questionamento_codae', '')
        try:
            obj.codae_questiona(
                user=request.user,
                justificativa=observacao_questionamento_codae
            )
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            permission_classes=(UsuarioTerceirizada,),
            methods=['patch'],
            url_path=constants.TERCEIRIZADA_RESPONDE_QUESTIONAMENTO)
    def terceirizada_responde_questionamento(self, request, uuid=None):
        obj = self.get_object()
        justificativa = request.data.get('justificativa', '')
        resposta_sim_nao = request.data.get('resposta_sim_nao', False)
        try:
            obj.terceirizada_responde_questionamento(user=request.user,
                                                     justificativa=justificativa,
                                                     resposta_sim_nao=resposta_sim_nao)
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=status.HTTP_400_BAD_REQUEST)


class TerceirizadaTomaCiencia():

    @action(detail=True,
            permission_classes=(UsuarioTerceirizada,),
            methods=['patch'],
            url_path=constants.TERCEIRIZADA_TOMOU_CIENCIA)
    def terceirizada_toma_ciencia(self, request, uuid=None):
        obj = self.get_object()
        try:
            obj.terceirizada_toma_ciencia(user=request.user, )
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['patch'],
            url_path=constants.MARCAR_CONFERIDA,
            permission_classes=(IsAuthenticated,))
    def terceirizada_marca_inclusao_como_conferida(self, request, uuid=None):
        inclusao_alimentacao_cei: InclusaoAlimentacaoDaCEI = self.get_object()
        try:
            inclusao_alimentacao_cei.terceirizada_conferiu_gestao = True
            inclusao_alimentacao_cei.save()
            serializer = self.get_serializer(inclusao_alimentacao_cei)
            return Response(serializer.data)
        except Exception as e:
            return Response(dict(detail=f'Erro ao marcar solicitação como conferida: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)  # noqa


class InclusaoAlimentacaoViewSetBase(ModelViewSet, EscolaIniciaCancela, DREValida, CodaeAutoriza,
                                     CodaeQuestionaTerceirizadaResponde, TerceirizadaTomaCiencia):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    funcao_relatorio = relatorio_inclusao_alimentacao_cei

    def get_permissions(self):
        if self.action in ['list']:
            self.permission_classes = (IsAdminUser,)
        elif self.action in ['retrieve', 'update']:
            self.permission_classes = (
                IsAuthenticated, PermissaoParaRecuperarObjeto)
        elif self.action in ['create', 'destroy']:
            self.permission_classes = (IsAuthenticated, UsuarioEscola)
        return super(InclusaoAlimentacaoViewSetBase, self).get_permissions()

    @action(detail=True,
            methods=['GET'],
            url_path=f'{constants.RELATORIO}',
            permission_classes=(IsAuthenticated,))
    def relatorio(self, request, uuid=None):
        return relatorio_inclusao_alimentacao_cei(request, solicitacao=self.get_object())


class InclusaoAlimentacaoDaCEIViewSet(InclusaoAlimentacaoViewSetBase):
    queryset = InclusaoAlimentacaoDaCEI.objects.all()
    serializer_class = serializers.InclusaoAlimentacaoDaCEISerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return serializers_create.InclusaoAlimentacaoDaCEICreateSerializer
        return serializers.InclusaoAlimentacaoDaCEISerializer

    @action(detail=False, url_path=constants.SOLICITACOES_DO_USUARIO, permission_classes=(UsuarioEscola,))
    def minhas_solicitacoes(self, request):
        usuario = request.user
        alimentacoes_normais = InclusaoAlimentacaoDaCEI.get_solicitacoes_rascunho(
            usuario)
        page = self.paginate_queryset(alimentacoes_normais)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_DRE}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioDiretoriaRegional,))
    def solicitacoes_diretoria_regional(self, request, filtro_aplicado=constants.SEM_FILTRO):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        inclusoes_alimentacao_cei = diretoria_regional.inclusoes_alimentacao_de_cei_das_minhas_escolas(
            filtro_aplicado
        )
        if request.query_params.get('lote'):
            lote_uuid = request.query_params.get('lote')
            inclusoes_alimentacao_cei = inclusoes_alimentacao_cei.filter(rastro_lote__uuid=lote_uuid)
        page = self.paginate_queryset(inclusoes_alimentacao_cei)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_CODAE}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioCODAEGestaoAlimentacao,))
    def solicitacoes_codae(self, request, filtro_aplicado=constants.SEM_FILTRO):
        # TODO: colocar regras de codae CODAE aqui...
        usuario = request.user
        codae = usuario.vinculo_atual.instituicao
        inclusoes_alimentacao_cei = codae.inclusoes_alimentacao_de_cei_das_minhas_escolas(
            filtro_aplicado
        )
        if request.query_params.get('diretoria_regional'):
            dre_uuid = request.query_params.get('diretoria_regional')
            inclusoes_alimentacao_cei = inclusoes_alimentacao_cei.filter(rastro_dre__uuid=dre_uuid)
        if request.query_params.get('lote'):
            lote_uuid = request.query_params.get('lote')
            inclusoes_alimentacao_cei = inclusoes_alimentacao_cei.filter(rastro_lote__uuid=lote_uuid)
        page = self.paginate_queryset(inclusoes_alimentacao_cei)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_TERCEIRIZADA}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioTerceirizada,))
    def solicitacoes_terceirizada(self, request, filtro_aplicado='sem_filtro'):
        # TODO: colocar regras de terceirizada aqui...
        usuario = request.user
        terceirizada = usuario.vinculo_atual.instituicao
        inclusoes_alimentacao_cei = terceirizada.inclusoes_alimentacao_de_cei_das_minhas_escolas(
            filtro_aplicado
        )
        page = self.paginate_queryset(inclusoes_alimentacao_cei)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=['patch'],
            url_path=constants.MARCAR_CONFERIDA,
            permission_classes=(IsAuthenticated,))
    def terceirizada_marca_inclusao_como_conferida(self, request, uuid=None):
        inclusao_alimentacao_cei: InclusaoAlimentacaoDaCEI = self.get_object()
        try:
            inclusao_alimentacao_cei.terceirizada_conferiu_gestao = True
            inclusao_alimentacao_cei.save()
            serializer = self.get_serializer(inclusao_alimentacao_cei)
            return Response(serializer.data)
        except Exception as e:
            return Response(dict(detail=f'Erro ao marcar solicitação como conferida: {e}'), status=status.HTTP_400_BAD_REQUEST)  # noqa


class MotivoInclusaoContinuaViewSet(ReadOnlyModelViewSet):
    lookup_field = 'uuid'
    queryset = MotivoInclusaoContinua.objects.all()
    serializer_class = serializers.MotivoInclusaoContinuaSerializer


class MotivoInclusaoNormalViewSet(ReadOnlyModelViewSet):
    lookup_field = 'uuid'
    queryset = MotivoInclusaoNormal.objects.all()
    serializer_class = serializers.MotivoInclusaoNormalSerializer


class GrupoInclusaoAlimentacaoNormalViewSet(InclusaoAlimentacaoViewSetBase):
    queryset = GrupoInclusaoAlimentacaoNormal.objects.all()
    serializer_class = serializers.GrupoInclusaoAlimentacaoNormalSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return serializers_create.GrupoInclusaoAlimentacaoNormalCreationSerializer
        return serializers.GrupoInclusaoAlimentacaoNormalSerializer

    def get_permissions(self):
        if self.action in ['list']:
            self.permission_classes = (IsAdminUser,)
        elif self.action in ['retrieve', 'update']:
            self.permission_classes = (
                IsAuthenticated, PermissaoParaRecuperarObjeto)
        elif self.action in ['create', 'destroy']:
            self.permission_classes = (UsuarioEscola,)
        return super(GrupoInclusaoAlimentacaoNormalViewSet, self).get_permissions()

    @action(detail=False, url_path=constants.SOLICITACOES_DO_USUARIO, permission_classes=(UsuarioEscola,))
    def minhas_solicitacoes(self, request):
        usuario = request.user
        alimentacoes_normais = GrupoInclusaoAlimentacaoNormal.get_solicitacoes_rascunho(
            usuario)
        page = self.paginate_queryset(alimentacoes_normais)
        serializer = serializers.GrupoInclusaoAlimentacaoNormalSerializer(
            page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_CODAE}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioCODAEGestaoAlimentacao,))
    def solicitacoes_codae(self, request, filtro_aplicado=constants.SEM_FILTRO):
        # TODO: colocar regras de codae CODAE aqui...
        usuario = request.user
        codae = usuario.vinculo_atual.instituicao
        inclusoes_continuas = codae.grupos_inclusoes_alimentacao_normal_das_minhas_escolas(
            filtro_aplicado
        )
        if request.query_params.get('diretoria_regional'):
            dre_uuid = request.query_params.get('diretoria_regional')
            inclusoes_continuas = inclusoes_continuas.filter(rastro_dre__uuid=dre_uuid)
        if request.query_params.get('lote'):
            lote_uuid = request.query_params.get('lote')
            inclusoes_continuas = inclusoes_continuas.filter(rastro_lote__uuid=lote_uuid)
        page = self.paginate_queryset(inclusoes_continuas)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_TERCEIRIZADA}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioTerceirizada,))
    def solicitacoes_terceirizada(self, request, filtro_aplicado=constants.SEM_FILTRO):
        # TODO: colocar regras de terceirizada aqui...
        usuario = request.user
        terceirizada = usuario.vinculo_atual.instituicao
        inclusoes_continuas = terceirizada.grupos_inclusoes_alimentacao_normal_das_minhas_escolas(
            filtro_aplicado
        )
        page = self.paginate_queryset(inclusoes_continuas)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    # TODO rever os demais endpoints. Essa action consolida em uma única
    # pesquisa as pesquisas por prioridade.
    @action(detail=False,
            url_path=f'{constants.PEDIDOS_DRE}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioDiretoriaRegional,))
    def solicitacoes_diretoria_regional(self, request, filtro_aplicado=constants.SEM_FILTRO):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        inclusoes_alimentacao_normal = diretoria_regional.grupos_inclusoes_alimentacao_normal_das_minhas_escolas(
            filtro_aplicado
        )
        if request.query_params.get('lote'):
            lote_uuid = request.query_params.get('lote')
            inclusoes_alimentacao_normal = inclusoes_alimentacao_normal.filter(rastro_lote__uuid=lote_uuid)
        page = self.paginate_queryset(inclusoes_alimentacao_normal)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=['GET'],
            url_path=f'{constants.RELATORIO}',
            permission_classes=(IsAuthenticated,))
    def relatorio(self, request, uuid=None):
        # TODO: essa função parece ser bem genérica, talvez possa ser incluida
        # por composição
        return relatorio_inclusao_alimentacao_normal(request, solicitacao=self.get_object())

    def destroy(self, request, *args, **kwargs):
        grupo_alimentacao_normal = self.get_object()
        if grupo_alimentacao_normal.pode_excluir:
            return super().destroy(request, *args, **kwargs)
        else:
            return Response(dict(detail='Você só pode excluir quando o status for RASCUNHO.'),
                            status=status.HTTP_403_FORBIDDEN)

    @action(detail=True,
            methods=['patch'],
            url_path=constants.MARCAR_CONFERIDA,
            permission_classes=(IsAuthenticated,))
    def terceirizada_marca_inclusao_como_conferida(self, request, uuid=None):
        inclusao_alimentacao_normal: GrupoInclusaoAlimentacaoNormal = self.get_object()
        try:
            inclusao_alimentacao_normal.terceirizada_conferiu_gestao = True
            inclusao_alimentacao_normal.save()
            serializer = self.get_serializer(inclusao_alimentacao_normal)
            return Response(serializer.data)
        except Exception as e:
            return Response(dict(detail=f'Erro ao marcar solicitação como conferida: {e}'), status=status.HTTP_400_BAD_REQUEST)  # noqa


class InclusaoAlimentacaoContinuaViewSet(ModelViewSet, DREValida, CodaeAutoriza,
                                         CodaeQuestionaTerceirizadaResponde, TerceirizadaTomaCiencia):
    lookup_field = 'uuid'
    queryset = InclusaoAlimentacaoContinua.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.InclusaoAlimentacaoContinuaSerializer
    funcao_relatorio = relatorio_inclusao_alimentacao_continua

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return serializers_create.InclusaoAlimentacaoContinuaCreationSerializer
        return serializers.InclusaoAlimentacaoContinuaSerializer

    def get_permissions(self):
        if self.action in ['list']:
            self.permission_classes = (IsAdminUser,)
        elif self.action in ['retrieve', 'update']:
            self.permission_classes = (
                IsAuthenticated, PermissaoParaRecuperarObjeto)
        elif self.action in ['create', 'destroy']:
            self.permission_classes = (UsuarioEscola,)
        return super(InclusaoAlimentacaoContinuaViewSet, self).get_permissions()

    @action(detail=True,
            permission_classes=(UsuarioEscola,),
            methods=['patch'],
            url_path=constants.ESCOLA_INICIO_PEDIDO)
    def inicio_de_pedido(self, request, uuid=None):
        obj = self.get_object()
        try:
            obj.inicia_fluxo(user=request.user, )
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            permission_classes=(UsuarioEscola,),
            methods=['patch'],
            url_path=constants.ESCOLA_CANCELA)
    def escola_cancela_pedido(self, request, uuid=None):
        obj = self.get_object()
        quantidades_periodo = request.data.get('quantidades_periodo', [])
        justificativa = request.data.get('justificativa', '')
        try:
            uuids_a_cancelar = [qtd_periodo['uuid'] for qtd_periodo in quantidades_periodo if qtd_periodo['cancelado']]
            if len(uuids_a_cancelar) == obj.quantidades_periodo.count():
                obj.cancelar_pedido(user=request.user, justificativa=justificativa)
            else:
                services.enviar_email_ue_cancelar_pedido_parcialmente(obj)
                obj.quantidades_periodo.filter(uuid__in=uuids_a_cancelar).exclude(cancelado=True).update(
                    cancelado=True, cancelado_justificativa=justificativa)
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, url_path=constants.SOLICITACOES_DO_USUARIO, permission_classes=(UsuarioEscola,))
    def minhas_solicitacoes(self, request):
        usuario = request.user
        inclusoes_continuas = InclusaoAlimentacaoContinua.get_solicitacoes_rascunho(
            usuario)
        page = self.paginate_queryset(inclusoes_continuas)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_CODAE}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioCODAEGestaoAlimentacao,))
    def solicitacoes_codae(self, request, filtro_aplicado=constants.SEM_FILTRO):
        # TODO: colocar regras de codae CODAE aqui...
        usuario = request.user
        codae = usuario.vinculo_atual.instituicao
        inclusoes_continuas = codae.inclusoes_alimentacao_continua_das_minhas_escolas(
            filtro_aplicado
        )
        if request.query_params.get('diretoria_regional'):
            dre_uuid = request.query_params.get('diretoria_regional')
            inclusoes_continuas = inclusoes_continuas.filter(rastro_dre__uuid=dre_uuid)
        if request.query_params.get('lote'):
            lote_uuid = request.query_params.get('lote')
            inclusoes_continuas = inclusoes_continuas.filter(rastro_lote__uuid=lote_uuid)
        page = self.paginate_queryset(inclusoes_continuas)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_TERCEIRIZADA}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioTerceirizada,))
    def solicitacoes_terceirizada(self, request, filtro_aplicado=constants.SEM_FILTRO):
        # TODO: colocar regras de terceirizada aqui...
        usuario = request.user
        terceirizada = usuario.vinculo_atual.instituicao
        inclusoes_continuas = terceirizada.inclusoes_alimentacao_continua_das_minhas_escolas(
            filtro_aplicado
        )
        page = self.paginate_queryset(inclusoes_continuas)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_DRE}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioDiretoriaRegional,))
    def solicitacoes_diretoria_regional(self, request, filtro_aplicado=constants.SEM_FILTRO):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        inclusoes_alimentacao_continua = diretoria_regional.inclusoes_alimentacao_continua_das_minhas_escolas(
            filtro_aplicado
        )
        if request.query_params.get('lote'):
            lote_uuid = request.query_params.get('lote')
            inclusoes_alimentacao_continua = inclusoes_alimentacao_continua.filter(rastro_lote__uuid=lote_uuid)
        page = self.paginate_queryset(inclusoes_alimentacao_continua)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=['GET'],
            url_path=f'{constants.RELATORIO}',
            permission_classes=(IsAuthenticated,))
    def relatorio(self, request, uuid=None):
        return relatorio_inclusao_alimentacao_continua(request, solicitacao=self.get_object())

    def destroy(self, request, *args, **kwargs):
        grupo_alimentacao_normal = self.get_object()
        if grupo_alimentacao_normal.pode_excluir:
            return super().destroy(request, *args, **kwargs)
        else:
            return Response(dict(detail='Você só pode excluir quando o status for RASCUNHO.'),
                            status=status.HTTP_403_FORBIDDEN)

    @action(detail=True,
            methods=['patch'],
            url_path=constants.MARCAR_CONFERIDA,
            permission_classes=(IsAuthenticated,))
    def terceirizada_marca_inclusao_como_conferida(self, request, uuid=None):
        inclusao_alimentacao_continua: InclusaoAlimentacaoContinua = self.get_object()
        try:
            if inclusao_alimentacao_continua.status != inclusao_alimentacao_continua.workflow_class.CODAE_AUTORIZADO:
                raise AssertionError('inclusão não está no status AUTORIZADO')
            inclusao_alimentacao_continua.terceirizada_conferiu_gestao = True
            inclusao_alimentacao_continua.save()
            serializer = self.get_serializer(inclusao_alimentacao_continua)
            return Response(serializer.data)
        except AssertionError as e:
            return Response(dict(detail=f'Erro ao marcar solicitação como conferida: {e}'),
                            status=status.HTTP_400_BAD_REQUEST)


class InclusaoAlimentacaoCEMEIViewSet(ModelViewSet, EscolaIniciaCancela, DREValida, CodaeAutoriza,
                                      CodaeQuestionaTerceirizadaResponde, TerceirizadaTomaCiencia):
    lookup_field = 'uuid'
    queryset = InclusaoDeAlimentacaoCEMEI.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return serializers_create.InclusaoDeAlimentacaoCEMEICreateSerializer
        elif self.action == 'retrieve':
            return serializers.InclusaoDeAlimentacaoCEMEIRetrieveSerializer
        return serializers.InclusaoDeAlimentacaoCEMEISerializer

    def get_permissions(self):
        if self.action in ['list']:
            self.permission_classes = (IsAuthenticated,)
        elif self.action in ['retrieve', 'update', 'destroy']:
            self.permission_classes = (
                IsAuthenticated, PermissaoParaRecuperarObjeto)
        elif self.action in ['create']:
            self.permission_classes = (UsuarioEscola,)
        return super(InclusaoAlimentacaoCEMEIViewSet, self).get_permissions()

    def get_queryset(self): # noqa C901
        queryset = InclusaoDeAlimentacaoCEMEI.objects.all()
        user = self.request.user
        if user.tipo_usuario == 'escola':
            queryset = queryset.filter(escola=user.vinculo_atual.instituicao)
        elif user.tipo_usuario == 'diretoriaregional':
            queryset = queryset.filter(rastro_dre=user.vinculo_atual.instituicao)
        elif user.tipo_usuario == 'terceirizada':
            queryset = queryset.filter(rastro_terceirizada=user.vinculo_atual.instituicao)
        if 'status' in self.request.query_params:
            queryset = queryset.filter(status=self.request.query_params.get('status').upper())
        return queryset

    def destroy(self, request, *args, **kwargs):
        inclusao_alimentacao_cemei = self.get_object()
        if inclusao_alimentacao_cemei.pode_excluir:
            return super().destroy(request, *args, **kwargs)
        else:
            return Response(dict(detail='Você só pode excluir quando o status for RASCUNHO.'),
                            status=status.HTTP_403_FORBIDDEN)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_DRE}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioDiretoriaRegional,))
    def solicitacoes_diretoria_regional(self, request, filtro_aplicado=constants.SEM_FILTRO):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        inclusoes_alimentacao = diretoria_regional.inclusoes_alimentacao_cemei_das_minhas_escolas(
            filtro_aplicado
        )
        if request.query_params.get('lote'):
            lote_uuid = request.query_params.get('lote')
            inclusoes_alimentacao = inclusoes_alimentacao.filter(rastro_lote__uuid=lote_uuid)
        page = self.paginate_queryset(inclusoes_alimentacao)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            url_path=f'{constants.PEDIDOS_CODAE}/{constants.FILTRO_PADRAO_PEDIDOS}',
            permission_classes=(UsuarioCODAEGestaoAlimentacao,))
    def solicitacoes_codae(self, request, filtro_aplicado=constants.SEM_FILTRO):
        usuario = request.user
        codae = usuario.vinculo_atual.instituicao
        inclusoes_alimentacao = codae.inclusoes_alimentacao_cemei_das_minhas_escolas(
            filtro_aplicado
        )
        if request.query_params.get('diretoria_regional'):
            dre_uuid = request.query_params.get('diretoria_regional')
            inclusoes_alimentacao = inclusoes_alimentacao.filter(rastro_dre__uuid=dre_uuid)
        if request.query_params.get('lote'):
            lote_uuid = request.query_params.get('lote')
            inclusoes_alimentacao = inclusoes_alimentacao.filter(rastro_lote__uuid=lote_uuid)
        page = self.paginate_queryset(inclusoes_alimentacao)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=['GET'],
            url_path=f'{constants.RELATORIO}',
            permission_classes=(IsAuthenticated,))
    def relatorio(self, request, uuid=None):
        return relatorio_inclusao_alimentacao_cemei(request, solicitacao=self.get_object())
