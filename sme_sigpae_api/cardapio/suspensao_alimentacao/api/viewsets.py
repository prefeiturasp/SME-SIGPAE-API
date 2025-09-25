import datetime

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from xworkflows import InvalidTransitionError

from sme_sigpae_api.cardapio.suspensao_alimentacao.api.serializers import (
    GrupoSupensaoAlimentacaoListagemSimplesSerializer,
    GrupoSuspensaoAlimentacaoSerializer,
    GrupoSuspensaoAlimentacaoSimplesSerializer,
    MotivoSuspensaoSerializer,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao.api.serializers_create import (
    GrupoSuspensaoAlimentacaoCreateSerializer,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    MotivoSuspensao,
)
from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoParaRecuperarObjeto,
    UsuarioCODAEGestaoAlimentacao,
    UsuarioEmpresaGenerico,
    UsuarioEscolaTercTotal,
)
from sme_sigpae_api.dados_comuns.services import (
    enviar_email_ue_cancelar_pedido_parcialmente,
)
from sme_sigpae_api.relatorios.relatorios import relatorio_suspensao_de_alimentacao


class GrupoSuspensaoAlimentacaoSerializerViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = GrupoSuspensaoAlimentacao.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = GrupoSuspensaoAlimentacaoSerializer

    def get_permissions(self):
        if self.action in ["list"]:
            self.permission_classes = (IsAdminUser,)
        elif self.action in ["retrieve", "update"]:
            self.permission_classes = (PermissaoParaRecuperarObjeto,)
        elif self.action in ["create", "destroy"]:
            self.permission_classes = (UsuarioEscolaTercTotal,)
        return super(GrupoSuspensaoAlimentacaoSerializerViewSet, self).get_permissions()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return GrupoSuspensaoAlimentacaoCreateSerializer
        return GrupoSuspensaoAlimentacaoSerializer

    @action(
        detail=False,
        url_path=f"{constants.PEDIDOS_CODAE}/{constants.FILTRO_PADRAO_PEDIDOS}",
        permission_classes=(UsuarioCODAEGestaoAlimentacao,),
    )
    def solicitacoes_codae(self, request, filtro_aplicado=constants.SEM_FILTRO):
        # TODO: colocar regras de codae CODAE aqui...
        usuario = request.user
        codae = usuario.vinculo_atual.instituicao
        alteracoes_cardapio = codae.suspensoes_cardapio_das_minhas_escolas(
            filtro_aplicado
        )

        page = self.paginate_queryset(alteracoes_cardapio)
        serializer = GrupoSuspensaoAlimentacaoSimplesSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["GET"])
    def informadas(self, request):
        grupo_informados = GrupoSuspensaoAlimentacao.get_informados().order_by("-id")
        serializer = GrupoSupensaoAlimentacaoListagemSimplesSerializer(
            grupo_informados, many=True
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{constants.PEDIDOS_TERCEIRIZADA}/{constants.FILTRO_PADRAO_PEDIDOS}",
        permission_classes=(UsuarioEmpresaGenerico,),
    )
    def solicitacoes_terceirizada(self, request, filtro_aplicado="sem_filtro"):
        # TODO: colocar regras de Terceirizada aqui...
        usuario = request.user
        terceirizada = usuario.vinculo_atual.instituicao
        suspensoes_cardapio = terceirizada.suspensoes_alimentacao_das_minhas_escolas(
            filtro_aplicado
        )

        page = self.paginate_queryset(suspensoes_cardapio)
        serializer = GrupoSupensaoAlimentacaoListagemSimplesSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, url_path="tomados-ciencia", methods=["GET"])
    def tomados_ciencia(self, request):
        grupo_informados = GrupoSuspensaoAlimentacao.get_tomados_ciencia()
        page = self.paginate_queryset(grupo_informados)
        serializer = GrupoSuspensaoAlimentacaoSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["GET"], permission_classes=(UsuarioEscolaTercTotal,))
    def meus_rascunhos(self, request):
        usuario = request.user
        grupos_suspensao = GrupoSuspensaoAlimentacao.get_rascunhos_do_usuario(usuario)
        page = self.paginate_queryset(grupos_suspensao)
        serializer = GrupoSuspensaoAlimentacaoSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    #
    # IMPLEMENTAÇÃO DO FLUXO (INFORMATIVO PARTINDO DA ESCOLA)
    #

    @action(
        detail=True,
        permission_classes=(UsuarioEscolaTercTotal,),
        methods=["patch"],
        url_path=constants.ESCOLA_INFORMA_SUSPENSAO,
    )
    def informa_suspensao(self, request, uuid=None):
        grupo_suspensao_de_alimentacao = self.get_object()
        try:
            grupo_suspensao_de_alimentacao.informa(
                user=request.user,
            )
            serializer = self.get_serializer(grupo_suspensao_de_alimentacao)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=(UsuarioEmpresaGenerico,),
        methods=["patch"],
        url_path=constants.TERCEIRIZADA_TOMOU_CIENCIA,
    )
    def terceirizada_toma_ciencia(self, request, uuid=None):
        grupo_suspensao_de_alimentacao = self.get_object()
        try:
            grupo_suspensao_de_alimentacao.terceirizada_toma_ciencia(
                user=request.user,
            )
            serializer = self.get_serializer(grupo_suspensao_de_alimentacao)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    def valida_datas(self, obj, datas):
        if datas:
            for data in datas:
                data_obj = datetime.datetime.strptime(data, "%Y-%m-%d").date()
                obj.checa_se_pode_cancelar(data_obj)

    @action(
        detail=True,
        permission_classes=(UsuarioEscolaTercTotal,),
        methods=["patch"],
        url_path="escola-cancela",
    )
    def escola_cancela(self, request, uuid=None):
        grupo_suspensao_de_alimentacao: GrupoSuspensaoAlimentacao = self.get_object()
        datas = request.data.get("datas", [])
        justificativa = request.data.get("justificativa", "")
        try:
            assert (  # nosec
                grupo_suspensao_de_alimentacao.status
                != grupo_suspensao_de_alimentacao.workflow_class.ESCOLA_CANCELOU
            ), "Solicitação já está cancelada"
            self.valida_datas(grupo_suspensao_de_alimentacao, datas)
            if (
                not hasattr(grupo_suspensao_de_alimentacao, "suspensoes_alimentacao")
                or len(datas)
                + grupo_suspensao_de_alimentacao.suspensoes_alimentacao.filter(
                    cancelado=True
                ).count()
                == grupo_suspensao_de_alimentacao.suspensoes_alimentacao.count()
            ):
                grupo_suspensao_de_alimentacao.cancelar_pedido(
                    user=request.user, justificativa=justificativa
                )
            else:
                enviar_email_ue_cancelar_pedido_parcialmente(
                    grupo_suspensao_de_alimentacao
                )
            if hasattr(grupo_suspensao_de_alimentacao, "suspensoes_alimentacao"):
                grupo_suspensao_de_alimentacao.suspensoes_alimentacao.filter(
                    data__in=datas
                ).update(cancelado_justificativa=justificativa, cancelado=True)
            serializer = self.get_serializer(grupo_suspensao_de_alimentacao)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    def destroy(self, request, *args, **kwargs):
        grupo_suspensao_de_alimentacao = self.get_object()
        if grupo_suspensao_de_alimentacao.pode_excluir:
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
        return relatorio_suspensao_de_alimentacao(
            request, solicitacao=self.get_object()
        )

    @action(
        detail=True,
        methods=["patch"],
        url_path=constants.MARCAR_CONFERIDA,
        permission_classes=(IsAuthenticated,),
    )
    def terceirizada_marca_inclusao_como_conferida(self, request, uuid=None):
        grupo_suspensao_alimentacao: GrupoSuspensaoAlimentacao = self.get_object()
        try:
            grupo_suspensao_alimentacao.terceirizada_conferiu_gestao = True
            grupo_suspensao_alimentacao.save()
            serializer = self.get_serializer(grupo_suspensao_alimentacao)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                dict(detail=f"Erro ao marcar solicitação como conferida: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )


class MotivosSuspensaoCardapioViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "uuid"
    queryset = MotivoSuspensao.objects.all()
    serializer_class = MotivoSuspensaoSerializer
