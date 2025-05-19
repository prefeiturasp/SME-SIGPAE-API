import datetime

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from xworkflows import InvalidTransitionError

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.serializers import (
    AlteracaoCardapioSerializer,
    AlteracaoCardapioSimplesSerializer,
    MotivoAlteracaoCardapioSerializer,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.serializers_create import (
    AlteracaoCardapioSerializerCreate,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    AlteracaoCardapio,
    MotivoAlteracaoCardapio,
)
from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoParaRecuperarObjeto,
    UsuarioCODAEGestaoAlimentacao,
    UsuarioDiretoriaRegional,
    UsuarioEscolaTercTotal,
    UsuarioTerceirizada,
)
from sme_sigpae_api.dados_comuns.services import (
    enviar_email_ue_cancelar_pedido_parcialmente,
)
from sme_sigpae_api.escola.models import Escola
from sme_sigpae_api.relatorios.relatorios import relatorio_alteracao_cardapio


class AlteracoesCardapioViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    permission_classes = (IsAuthenticated,)
    queryset = AlteracaoCardapio.objects.all()

    def get_permissions(self):
        if self.action in ["list"]:
            self.permission_classes = (UsuarioEscolaTercTotal,)
        elif self.action in ["retrieve", "update"]:
            self.permission_classes = (IsAuthenticated, PermissaoParaRecuperarObjeto)
        elif self.action in ["create", "destroy"]:
            self.permission_classes = (UsuarioEscolaTercTotal,)
        return super(AlteracoesCardapioViewSet, self).get_permissions()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return AlteracaoCardapioSerializerCreate
        return AlteracaoCardapioSerializer

    #
    # Pedidos
    #

    @action(
        detail=False,
        url_path=constants.SOLICITACOES_DO_USUARIO,
        permission_classes=(UsuarioEscolaTercTotal,),
    )
    def minhas_solicitacoes(self, request):
        usuario = request.user
        alteracoes_cardapio_rascunho = AlteracaoCardapio.get_rascunhos_do_usuario(
            usuario
        )
        page = self.paginate_queryset(alteracoes_cardapio_rascunho)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        url_path=f"{constants.PEDIDOS_CODAE}/{constants.FILTRO_PADRAO_PEDIDOS}",
        permission_classes=[UsuarioCODAEGestaoAlimentacao],
    )
    def solicitacoes_codae(self, request, filtro_aplicado=constants.SEM_FILTRO):
        # TODO: colocar regras de codae CODAE aqui...
        usuario = request.user
        codae = usuario.vinculo_atual.instituicao
        alteracoes_cardapio = codae.alteracoes_cardapio_das_minhas(filtro_aplicado)
        if request.query_params.get("diretoria_regional"):
            dre_uuid = request.query_params.get("diretoria_regional")
            alteracoes_cardapio = alteracoes_cardapio.filter(rastro_dre__uuid=dre_uuid)
        if request.query_params.get("lote"):
            lote_uuid = request.query_params.get("lote")
            alteracoes_cardapio = alteracoes_cardapio.filter(
                rastro_lote__uuid=lote_uuid
            )
        page = self.paginate_queryset(alteracoes_cardapio)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        url_path=f"{constants.PEDIDOS_DRE}/{constants.FILTRO_PADRAO_PEDIDOS}",
        permission_classes=[UsuarioDiretoriaRegional],
    )
    def solicitacoes_dre(self, request, filtro_aplicado=constants.SEM_FILTRO):
        # TODO: colocar regras de DRE aqui...
        usuario = request.user
        dre = usuario.vinculo_atual.instituicao
        alteracoes_cardapio = dre.alteracoes_cardapio_das_minhas_escolas_a_validar(
            filtro_aplicado
        )

        page = self.paginate_queryset(alteracoes_cardapio)
        serializer = AlteracaoCardapioSimplesSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=["GET"], url_path=f"{constants.RELATORIO}")
    def relatorio(self, request, uuid=None):
        return relatorio_alteracao_cardapio(request, solicitacao=self.get_object())

    #
    # IMPLEMENTAÇÃO DO FLUXO (PARTINDO DA ESCOLA)
    #

    @action(
        detail=True,
        permission_classes=[UsuarioEscolaTercTotal],
        methods=["patch"],
        url_path=constants.ESCOLA_INICIO_PEDIDO,
    )
    def inicio_de_solicitacao(self, request, uuid=None):
        alteracao_cardapio = self.get_object()
        try:
            alteracao_cardapio.inicia_fluxo(
                user=request.user,
            )
            serializer = self.get_serializer(alteracao_cardapio)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=[UsuarioDiretoriaRegional],
        methods=["patch"],
        url_path=constants.DRE_VALIDA_PEDIDO,
    )
    def diretoria_regional_valida(self, request, uuid=None):
        alteracao_cardapio = self.get_object()
        try:
            alteracao_cardapio.dre_valida(
                user=request.user,
            )
            serializer = self.get_serializer(alteracao_cardapio)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=[UsuarioDiretoriaRegional],
        methods=["patch"],
        url_path=constants.DRE_NAO_VALIDA_PEDIDO,
    )
    def dre_nao_valida_solicitacao(self, request, uuid=None):
        alteracao_cardapio = self.get_object()
        justificativa = request.data.get("justificativa", "")
        try:
            alteracao_cardapio.dre_nao_valida(
                user=request.user, justificativa=justificativa
            )
            serializer = self.get_serializer(alteracao_cardapio)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=[UsuarioCODAEGestaoAlimentacao],
        methods=["patch"],
        url_path=constants.CODAE_NEGA_PEDIDO,
    )
    def codae_nega_solicitacao(self, request, uuid=None):
        alteracao_cardapio = self.get_object()
        justificativa = request.data.get("justificativa", "")
        try:
            if (
                alteracao_cardapio.status
                == alteracao_cardapio.workflow_class.DRE_VALIDADO
            ):
                alteracao_cardapio.codae_nega(
                    user=request.user, justificativa=justificativa
                )
            else:
                alteracao_cardapio.codae_nega_questionamento(
                    user=request.user, justificativa=justificativa
                )
            serializer = self.get_serializer(alteracao_cardapio)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=[UsuarioCODAEGestaoAlimentacao],
        methods=["patch"],
        url_path=constants.CODAE_AUTORIZA_PEDIDO,
    )
    def codae_autoriza(self, request, uuid=None):
        alteracao_cardapio = self.get_object()
        justificativa = request.data.get("justificativa", "")
        try:
            if (
                alteracao_cardapio.status
                == alteracao_cardapio.workflow_class.DRE_VALIDADO
            ):
                alteracao_cardapio.codae_autoriza(
                    user=request.user, justificativa=justificativa
                )
            else:
                alteracao_cardapio.codae_autoriza_questionamento(
                    user=request.user, justificativa=justificativa
                )
            serializer = self.get_serializer(alteracao_cardapio)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=[UsuarioCODAEGestaoAlimentacao],
        methods=["patch"],
        url_path=constants.CODAE_QUESTIONA_PEDIDO,
    )
    def codae_questiona_pedido(self, request, uuid=None):
        alteracao_cardapio = self.get_object()
        observacao_questionamento_codae = request.data.get(
            "observacao_questionamento_codae", ""
        )
        try:
            alteracao_cardapio.codae_questiona(
                user=request.user, justificativa=observacao_questionamento_codae
            )
            serializer = self.get_serializer(alteracao_cardapio)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=[UsuarioTerceirizada],
        methods=["patch"],
        url_path=constants.TERCEIRIZADA_TOMOU_CIENCIA,
    )
    def terceirizada_toma_ciencia(self, request, uuid=None):
        alteracao_cardapio = self.get_object()
        try:
            alteracao_cardapio.terceirizada_toma_ciencia(
                user=request.user,
            )
            serializer = self.get_serializer(alteracao_cardapio)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=[UsuarioTerceirizada],
        methods=["patch"],
        url_path=constants.TERCEIRIZADA_RESPONDE_QUESTIONAMENTO,
    )
    def terceirizada_responde_questionamento(self, request, uuid=None):
        alteracao_cardapio = self.get_object()
        justificativa = request.data.get("justificativa", "")
        resposta_sim_nao = request.data.get("resposta_sim_nao", False)
        try:
            alteracao_cardapio.terceirizada_responde_questionamento(
                user=request.user,
                justificativa=justificativa,
                resposta_sim_nao=resposta_sim_nao,
            )
            serializer = self.get_serializer(alteracao_cardapio)
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
        permission_classes=[UsuarioEscolaTercTotal],
        methods=["patch"],
        url_path=constants.ESCOLA_CANCELA,
    )
    def escola_cancela_pedido(self, request, uuid=None):
        obj = self.get_object()
        datas = request.data.get("datas", [])
        justificativa = request.data.get("justificativa", "")
        try:
            assert (  # nosec
                obj.status != obj.workflow_class.ESCOLA_CANCELOU
            ), "Solicitação já está cancelada"
            self.valida_datas(obj, datas)
            if (
                not hasattr(obj, "datas_intervalo")
                or obj.data_inicial == obj.data_final
                or len(datas) + obj.datas_intervalo.filter(cancelado=True).count()
                == obj.datas_intervalo.count()
            ):
                obj.cancelar_pedido(user=request.user, justificativa=justificativa)
            else:
                enviar_email_ue_cancelar_pedido_parcialmente(obj)
            if hasattr(obj, "datas_intervalo") and obj.datas_intervalo.exists():
                obj.datas_intervalo.filter(data__in=datas).update(
                    cancelado_justificativa=justificativa, cancelado=True
                )
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        except (InvalidTransitionError, AssertionError) as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    # TODO rever os demais endpoints. Essa action consolida em uma única
    # pesquisa as pesquisas por prioridade.
    @action(
        detail=False,
        url_path=f"{constants.PEDIDOS_DRE}/{constants.FILTRO_PADRAO_PEDIDOS}",
        permission_classes=[UsuarioDiretoriaRegional],
    )
    def solicitacoes_diretoria_regional(self, request, filtro_aplicado="sem_filtro"):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        alteracoes_cardapio = (
            diretoria_regional.alteracoes_cardapio_das_minhas_escolas_a_validar(
                filtro_aplicado
            )
        )
        if request.query_params.get("lote"):
            lote_uuid = request.query_params.get("lote")
            alteracoes_cardapio = alteracoes_cardapio.filter(
                rastro_lote__uuid=lote_uuid
            )
        page = self.paginate_queryset(alteracoes_cardapio)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        alteracao_cardapio = self.get_object()
        if alteracao_cardapio.pode_excluir:
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
        alteracao_cardapio: AlteracaoCardapio = self.get_object()
        try:
            alteracao_cardapio.terceirizada_conferiu_gestao = True
            alteracao_cardapio.save()
            serializer = self.get_serializer(alteracao_cardapio)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                dict(detail=f"Erro ao marcar solicitação como conferida: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )


class MotivosAlteracaoCardapioViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "uuid"
    queryset = MotivoAlteracaoCardapio.objects.filter(ativo=True)
    serializer_class = MotivoAlteracaoCardapioSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = MotivoAlteracaoCardapio.objects.filter(ativo=True)
        if (
            isinstance(user.vinculo_atual.instituicao, Escola)
            and user.vinculo_atual.instituicao.eh_cei
        ):
            return queryset.exclude(nome__icontains="Lanche Emergencial")
        return queryset
