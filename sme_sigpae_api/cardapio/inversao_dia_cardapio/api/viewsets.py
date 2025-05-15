from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from xworkflows import InvalidTransitionError

from sme_sigpae_api.cardapio.inversao_dia_cardapio.api.serializers import (
    InversaoCardapioSerializer,
)
from sme_sigpae_api.cardapio.inversao_dia_cardapio.api.serializers_create import (
    InversaoCardapioSerializerCreate,
)
from sme_sigpae_api.cardapio.inversao_dia_cardapio.models import InversaoCardapio
from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoParaRecuperarObjeto,
    UsuarioCODAEGestaoAlimentacao,
    UsuarioDiretoriaRegional,
    UsuarioEscolaTercTotal,
    UsuarioTerceirizada,
)
from sme_sigpae_api.relatorios.relatorios import relatorio_inversao_dia_de_cardapio


class InversaoCardapioViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    serializer_class = InversaoCardapioSerializer
    permission_classes = (IsAuthenticated,)
    queryset = InversaoCardapio.objects.all()

    def get_permissions(self):
        if self.action in ["list"]:
            self.permission_classes = (IsAdminUser,)
        elif self.action in ["retrieve", "update"]:
            self.permission_classes = (IsAuthenticated, PermissaoParaRecuperarObjeto)
        elif self.action in ["create", "destroy"]:
            self.permission_classes = (UsuarioEscolaTercTotal,)
        return super(InversaoCardapioViewSet, self).get_permissions()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return InversaoCardapioSerializerCreate
        return InversaoCardapioSerializer

    @action(
        detail=False,
        url_path=f"{constants.PEDIDOS_DRE}/{constants.FILTRO_PADRAO_PEDIDOS}",
        permission_classes=(UsuarioDiretoriaRegional,),
    )
    def solicitacoes_diretoria_regional(
        self, request, filtro_aplicado=constants.SEM_FILTRO
    ):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        inversoes_cardapio = diretoria_regional.inversoes_cardapio_das_minhas_escolas(
            filtro_aplicado
        )
        if request.query_params.get("lote"):
            lote_uuid = request.query_params.get("lote")
            inversoes_cardapio = inversoes_cardapio.filter(rastro_lote__uuid=lote_uuid)
        page = self.paginate_queryset(inversoes_cardapio)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        url_path=f"{constants.PEDIDOS_CODAE}/{constants.FILTRO_PADRAO_PEDIDOS}",
        permission_classes=(UsuarioCODAEGestaoAlimentacao,),
    )
    def solicitacoes_codae(self, request, filtro_aplicado=constants.SEM_FILTRO):
        # TODO: colocar regras de codae CODAE aqui...
        usuario = request.user
        codae = usuario.vinculo_atual.instituicao
        inversoes_cardapio = codae.inversoes_cardapio_das_minhas_escolas(
            filtro_aplicado
        )
        if request.query_params.get("diretoria_regional"):
            dre_uuid = request.query_params.get("diretoria_regional")
            inversoes_cardapio = inversoes_cardapio.filter(rastro_dre__uuid=dre_uuid)
        if request.query_params.get("lote"):
            lote_uuid = request.query_params.get("lote")
            inversoes_cardapio = inversoes_cardapio.filter(rastro_lote__uuid=lote_uuid)
        page = self.paginate_queryset(inversoes_cardapio)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        url_path=f"{constants.PEDIDOS_TERCEIRIZADA}/{constants.FILTRO_PADRAO_PEDIDOS}",
        permission_classes=(UsuarioTerceirizada,),
    )
    def solicitacoes_terceirizada(self, request, filtro_aplicado=constants.SEM_FILTRO):
        # TODO: colocar regras de Terceirizada aqui...
        usuario = request.user
        terceirizada = usuario.vinculo_atual.instituicao
        inversoes_cardapio = terceirizada.inversoes_cardapio_das_minhas_escolas(
            filtro_aplicado
        )
        page = self.paginate_queryset(inversoes_cardapio)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        url_path=constants.SOLICITACOES_DO_USUARIO,
        permission_classes=(UsuarioEscolaTercTotal,),
    )
    def minhas_solicitacoes(self, request):
        usuario = request.user
        inversoes_rascunho = InversaoCardapio.get_solicitacoes_rascunho(usuario)
        page = self.paginate_queryset(inversoes_rascunho)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    #
    # IMPLEMENTAÇÃO DO FLUXO (PARTINDO DA ESCOLA)
    #

    @action(
        detail=True,
        permission_classes=(UsuarioEscolaTercTotal,),
        methods=["patch"],
        url_path=constants.ESCOLA_INICIO_PEDIDO,
    )
    def inicio_de_solicitacao(self, request, uuid=None):
        inversao_cardapio = self.get_object()
        try:
            inversao_cardapio.inicia_fluxo(
                user=request.user,
            )
            serializer = self.get_serializer(inversao_cardapio)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=(UsuarioDiretoriaRegional,),
        methods=["patch"],
        url_path=constants.DRE_VALIDA_PEDIDO,
    )
    def diretoria_regional_valida_solicitacao(self, request, uuid=None):
        inversao_cardapio = self.get_object()
        try:
            inversao_cardapio.dre_valida(
                user=request.user,
            )
            serializer = self.get_serializer(inversao_cardapio)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=(UsuarioDiretoriaRegional,),
        methods=["patch"],
        url_path=constants.DRE_NAO_VALIDA_PEDIDO,
    )
    def diretoria_regional_nao_valida_solicitacao(self, request, uuid=None):
        inversao_cardapio = self.get_object()
        justificativa = request.data.get("justificativa", "")
        try:
            inversao_cardapio.dre_nao_valida(
                user=request.user, justificativa=justificativa
            )
            serializer = self.get_serializer(inversao_cardapio)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=(UsuarioCODAEGestaoAlimentacao,),
        methods=["patch"],
        url_path=constants.CODAE_AUTORIZA_PEDIDO,
    )
    def codae_autoriza_solicitacao(self, request, uuid=None):
        inversao_cardapio = self.get_object()
        justificativa = request.data.get("justificativa", "")
        try:
            user = request.user
            if (
                inversao_cardapio.status
                == inversao_cardapio.workflow_class.DRE_VALIDADO
            ):
                inversao_cardapio.codae_autoriza(user=user, justificativa=justificativa)
            else:
                inversao_cardapio.codae_autoriza_questionamento(
                    user=user, justificativa=justificativa
                )
            serializer = self.get_serializer(inversao_cardapio)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=(UsuarioCODAEGestaoAlimentacao,),
        methods=["patch"],
        url_path=constants.CODAE_QUESTIONA_PEDIDO,
    )
    def codae_questiona(self, request, uuid=None):
        inversao_cardapio = self.get_object()
        justificativa = request.data.get("observacao_questionamento_codae", "")
        try:
            inversao_cardapio.codae_questiona(
                user=request.user, justificativa=justificativa
            )
            serializer = self.get_serializer(inversao_cardapio)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=(UsuarioCODAEGestaoAlimentacao,),
        methods=["patch"],
        url_path=constants.CODAE_NEGA_PEDIDO,
    )
    def codae_nega_solicitacao(self, request, uuid=None):
        inversao_cardapio = self.get_object()
        justificativa = request.data.get("justificativa", "")
        try:
            user = request.user
            if (
                inversao_cardapio.status
                == inversao_cardapio.workflow_class.DRE_VALIDADO
            ):
                inversao_cardapio.codae_nega(user=user, justificativa=justificativa)
            else:
                inversao_cardapio.codae_nega_questionamento(
                    user=user, justificativa=justificativa
                )
            serializer = self.get_serializer(inversao_cardapio)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=(UsuarioTerceirizada,),
        methods=["patch"],
        url_path=constants.TERCEIRIZADA_RESPONDE_QUESTIONAMENTO,
    )
    def terceirizada_responde_questionamento(self, request, uuid=None):
        inversao_cardapio = self.get_object()
        justificativa = request.data.get("justificativa", "")
        resposta_sim_nao = request.data.get("resposta_sim_nao", False)
        try:
            inversao_cardapio.terceirizada_responde_questionamento(
                user=request.user,
                justificativa=justificativa,
                resposta_sim_nao=resposta_sim_nao,
            )
            serializer = self.get_serializer(inversao_cardapio)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=(UsuarioTerceirizada,),
        methods=["patch"],
        url_path=constants.TERCEIRIZADA_TOMOU_CIENCIA,
    )
    def terceirizada_toma_ciencia(self, request, uuid=None):
        inversao_cardapio = self.get_object()
        try:
            inversao_cardapio.terceirizada_toma_ciencia(
                user=request.user,
            )
            serializer = self.get_serializer(inversao_cardapio)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=(UsuarioEscolaTercTotal,),
        methods=["patch"],
        url_path=constants.ESCOLA_CANCELA,
    )
    def escola_cancela_solicitacao(self, request, uuid=None):
        inversao_cardapio = self.get_object()
        justificativa = request.data.get("justificativa", "")
        try:
            inversao_cardapio.cancelar_pedido(
                user=request.user, justificativa=justificativa
            )
            serializer = self.get_serializer(inversao_cardapio)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    def destroy(self, request, *args, **kwargs):
        inversao_cardapio = self.get_object()
        if inversao_cardapio.pode_excluir:
            return super().destroy(request, *args, **kwargs)
        else:
            return Response(
                dict(detail="Você só pode excluir quando o status for RASCUNHO."),
                status=status.HTTP_403_FORBIDDEN,
            )

    @action(
        detail=True,
        url_path=constants.RELATORIO,
        methods=["get"],
        permission_classes=(IsAuthenticated,),
    )
    def relatorio(self, request, uuid=None):
        return relatorio_inversao_dia_de_cardapio(
            request, solicitacao=self.get_object()
        )

    @action(
        detail=True,
        methods=["patch"],
        url_path=constants.MARCAR_CONFERIDA,
        permission_classes=(IsAuthenticated,),
    )
    def terceirizada_marca_inclusao_como_conferida(self, request, uuid=None):
        inversao_cardapio: InversaoCardapio = self.get_object()
        try:
            inversao_cardapio.terceirizada_conferiu_gestao = True
            inversao_cardapio.save()
            serializer = self.get_serializer(inversao_cardapio)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                dict(detail=f"Erro ao marcar solicitação como conferida: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )
