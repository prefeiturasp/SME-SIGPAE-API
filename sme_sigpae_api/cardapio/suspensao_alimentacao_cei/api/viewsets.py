from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from xworkflows import InvalidTransitionError

from sme_sigpae_api.cardapio.suspensao_alimentacao_cei.api.serializers import (
    SuspensaoAlimentacaoDaCEISerializer,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao_cei.api.serializers_create import (
    SuspensaoAlimentacaodeCEICreateSerializer,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao_cei.models import (
    SuspensaoAlimentacaoDaCEI,
)
from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoParaRecuperarObjeto,
    UsuarioEscolaTercTotal,
)
from sme_sigpae_api.relatorios.relatorios import relatorio_suspensao_de_alimentacao_cei


class SuspensaoAlimentacaoDaCEIViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = SuspensaoAlimentacaoDaCEI.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = SuspensaoAlimentacaoDaCEISerializer

    def get_permissions(self):
        if self.action in ["list"]:
            self.permission_classes = (IsAdminUser,)
        elif self.action in ["retrieve", "update"]:
            self.permission_classes = (IsAuthenticated, PermissaoParaRecuperarObjeto)
        elif self.action in ["create", "destroy"]:
            self.permission_classes = (UsuarioEscolaTercTotal,)
        return super(SuspensaoAlimentacaoDaCEIViewSet, self).get_permissions()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SuspensaoAlimentacaodeCEICreateSerializer
        return SuspensaoAlimentacaoDaCEISerializer

    @action(detail=False, methods=["GET"])
    def informadas(self, request):
        informados = SuspensaoAlimentacaoDaCEI.get_informados().order_by("-id")
        serializer = SuspensaoAlimentacaoDaCEISerializer(informados, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["GET"], permission_classes=(UsuarioEscolaTercTotal,))
    def meus_rascunhos(self, request):
        usuario = request.user
        suspensoes = SuspensaoAlimentacaoDaCEI.get_rascunhos_do_usuario(usuario)
        page = self.paginate_queryset(suspensoes)
        serializer = SuspensaoAlimentacaoDaCEISerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        permission_classes=(UsuarioEscolaTercTotal,),
        methods=["patch"],
        url_path=constants.ESCOLA_INFORMA_SUSPENSAO,
    )
    def informa_suspensao(self, request, uuid=None):
        suspensao_de_alimentacao = self.get_object()
        try:
            suspensao_de_alimentacao.informa(
                user=request.user,
            )
            serializer = self.get_serializer(suspensao_de_alimentacao)
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
        url_path=constants.CANCELA_SUSPENSAO_CEI,
    )
    def cancela_suspensao_cei(self, request, uuid=None):
        suspensao_de_alimentacao = self.get_object()
        try:
            justificativa = request.data.get("justificativa")
            suspensao_de_alimentacao.escola_cancela(
                user=request.user, justificativa=justificativa
            )
            serializer = self.get_serializer(suspensao_de_alimentacao)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    def destroy(self, request, *args, **kwargs):
        suspensao_de_alimentacao = self.get_object()
        if suspensao_de_alimentacao.pode_excluir:
            return super().destroy(request, *args, **kwargs)
        else:
            return Response(
                dict(detail="Você só pode excluir quando o status for RASCUNHO."),
                status=status.HTTP_403_FORBIDDEN,
            )

    @action(
        detail=True,
        methods=["patch"],
        url_path=constants.MARCAR_CONFERIDA,
        permission_classes=(IsAuthenticated,),
    )
    def terceirizada_marca_inclusao_como_conferida(self, request, uuid=None):
        suspensao_alimentacao_cei: SuspensaoAlimentacaoDaCEI = self.get_object()
        try:
            suspensao_alimentacao_cei.terceirizada_conferiu_gestao = True
            suspensao_alimentacao_cei.save()
            serializer = self.get_serializer(suspensao_alimentacao_cei)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                dict(detail=f"Erro ao marcar solicitação como conferida: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        url_path=constants.RELATORIO,
        methods=["get"],
        permission_classes=(IsAuthenticated,),
    )
    def relatorio(self, request, uuid=None):
        return relatorio_suspensao_de_alimentacao_cei(
            request, solicitacao=self.get_object()
        )
