import datetime

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from xworkflows import InvalidTransitionError

from src.cardapio.suspensao_alimentacao.api.serializers import (
    GrupoSupensaoAlimentacaoListagemSimplesSerializer,
    GrupoSuspensaoAlimentacaoSerializer,
    GrupoSuspensaoAlimentacaoSimplesSerializer,
    MotivoSuspensaoSerializer,
)
from src.cardapio.suspensao_alimentacao.api.serializers_create import (
    GrupoSuspensaoAlimentacaoCreateSerializer,
)
from src.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    MotivoSuspensao,
)
from src.dados_comuns import constants
from src.dados_comuns.mixins.serializer_context import (
    DataSolicitacaoContextMixin,
)
from src.dados_comuns.permissions import (
    PermissaoParaRecuperarObjeto,
    UsuarioCODAEGestaoAlimentacao,
    UsuarioEmpresaGenerico,
    UsuarioEscolaTercTotal,
)
from src.dados_comuns.services import (
    enviar_email_ue_cancelar_pedido_parcialmente,
)
from src.relatorios.relatorios import relatorio_suspensao_de_alimentacao


class GrupoSuspensaoAlimentacaoSerializerViewSet(
    DataSolicitacaoContextMixin, viewsets.ModelViewSet
):
    """Viewset para gerenciamento de solicitações de suspensão de alimentação.

    Gerencia o ciclo de vida completo das solicitações de suspensão de
    alimentação: criação, leitura, atualização, exclusão e ações do fluxo
    informativo partindo da escola.

    Actions de fluxo disponíveis:
        - ``informa_suspensao``: Escola informa a suspensão (RASCUNHO → INFORMADO).
        - ``terceirizada_toma_ciencia``: Terceirizada toma ciência (INFORMADO → TERCEIRIZADA_TOMOU_CIENCIA).
        - ``escola_cancela``: Escola cancela total ou parcialmente.
    """

    lookup_field = "uuid"
    queryset = GrupoSuspensaoAlimentacao.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = GrupoSuspensaoAlimentacaoSerializer

    def get_permissions(self):
        """Retorna a lista de permissões necessárias para a ação atual.

        - Para a ação ``list``: requer ``IsAdminUser``.
        - Para as ações ``retrieve`` e ``update``: requer autenticação e
          ``PermissaoParaRecuperarObjeto``.
        - Para as ações ``create`` e ``destroy``: requer
          ``UsuarioEscolaTercTotal``.

        Returns:
            list: Lista de instâncias de classes de permissão configuradas
            para a ação atual.
        """
        if self.action in ["list"]:
            self.permission_classes = (IsAdminUser,)
        elif self.action in ["retrieve", "update"]:
            self.permission_classes = (PermissaoParaRecuperarObjeto,)
        elif self.action in ["create", "destroy"]:
            self.permission_classes = (UsuarioEscolaTercTotal,)
        return super(GrupoSuspensaoAlimentacaoSerializerViewSet, self).get_permissions()

    def get_serializer_class(self):
        """Retorna a classe de serializer adequada para a ação atual.

        - Para as ações ``create``, ``update`` e ``partial_update``: utiliza
          ``GrupoSuspensaoAlimentacaoCreateSerializer``.
        - Para as demais ações: utiliza ``GrupoSuspensaoAlimentacaoSerializer``.

        Returns:
            type: Classe de serializer a ser utilizada na ação corrente.
        """
        if self.action in ["create", "update", "partial_update"]:
            return GrupoSuspensaoAlimentacaoCreateSerializer
        return GrupoSuspensaoAlimentacaoSerializer

    @action(
        detail=False,
        url_path=f"{constants.PEDIDOS_CODAE}/{constants.FILTRO_PADRAO_PEDIDOS}",
        permission_classes=(UsuarioCODAEGestaoAlimentacao,),
    )
    def solicitacoes_codae(self, request, filtro_aplicado=constants.SEM_FILTRO):
        """Retorna as solicitações de suspensão para a CODAE Gestão de Alimentação.
        - permissão: CODAE Gestão de Alimentação.

        Args:
            request (Request): Objeto da requisição HTTP contendo o usuário
                autenticado.
            filtro_aplicado (str): Filtro de status aplicado às solicitações.
                Padrão: ``constants.SEM_FILTRO``.

        Returns:
            Response: Resposta paginada com a lista serializada das
            solicitações encontradas.
        """
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
        """Retorna as solicitações de suspensão com status INFORMADO.
        - permissão: qualquer usuário autenticado.

        Args:
            request (Request): Objeto da requisição HTTP.

        Returns:
            Response: Resposta paginada com a lista de solicitações informadas.
        """
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
        """Retorna as solicitações de suspensão para a empresa terceirizada.
        - permissão: Empresa terceirizada.

        Args:
            request (Request): Objeto da requisição HTTP contendo o usuário
                autenticado.
            filtro_aplicado (str): Filtro de status aplicado às solicitações.
                Padrão: ``"sem_filtro"``.

        Returns:
            Response: Resposta paginada com a lista serializada das
            solicitações da terceirizada.
        """
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
        """Retorna as solicitações de suspensão com status TERCEIRIZADA_TOMOU_CIENCIA.
        - permissão: qualquer usuário autenticado.

        Args:
            request (Request): Objeto da requisição HTTP.

        Returns:
            Response: Resposta paginada com a lista de solicitações das quais
            a terceirizada tomou ciência.
        """
        grupo_informados = GrupoSuspensaoAlimentacao.get_tomados_ciencia()
        page = self.paginate_queryset(grupo_informados)
        serializer = GrupoSuspensaoAlimentacaoSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["GET"], permission_classes=(UsuarioEscolaTercTotal,))
    def meus_rascunhos(self, request):
        """Retorna as solicitações de suspensão em rascunho do usuário logado.
        - permissão: Escola terceirizada.

        Args:
            request (Request): Objeto da requisição HTTP contendo o usuário
                autenticado.

        Returns:
            Response: Resposta paginada com a lista de rascunhos do usuário.
        """
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
        """Informa a suspensão de alimentação, iniciando o fluxo pela escola.
        - sai do status RASCUNHO e passa para INFORMADO.
        - permissão: Escola terceirizada.

        Args:
            request (Request): Objeto da requisição HTTP contendo o usuário
                autenticado.
            uuid (str, optional): UUID da instância de
                ``GrupoSuspensaoAlimentacao``. Padrão: None.

        Returns:
            Response: Dados serializados da solicitação após a transição, ou
            erro 400 em caso de transição inválida.

        Raises:
            InvalidTransitionError: Quando a transição de estado não é
                permitida pelo workflow.
        """
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
        """Registra a ciência da terceirizada sobre a suspensão de alimentação.
        - passa do status INFORMADO para TERCEIRIZADA_TOMOU_CIENCIA.
        - permissão: Empresa terceirizada.

        Args:
            request (Request): Objeto da requisição HTTP contendo o usuário
                autenticado.
            uuid (str, optional): UUID da instância de
                ``GrupoSuspensaoAlimentacao``. Padrão: None.

        Returns:
            Response: Dados serializados da solicitação após a transição, ou
            erro 400 em caso de transição inválida.

        Raises:
            InvalidTransitionError: Quando a transição de estado não é
                permitida pelo workflow.
        """
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
        """Valida cada data para verificar se pode ser cancelada.

        Args:
            obj (GrupoSuspensaoAlimentacao): Instância da solicitação a ser
                validada.
            datas (list[str]): Lista de datas no formato ``"%Y-%m-%d"`` a
                serem verificadas.

        Raises:
            InvalidTransitionError: Quando alguma data não permite
                cancelamento conforme a regra de negócio.
        """
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
        """Cancela total ou parcialmente a solicitação pela escola.
        - cancela totalmente quando todas as datas são canceladas.
        - cancela parcialmente quando apenas algumas datas são canceladas,
          enviando notificação por e-mail.
        - permissão: Escola terceirizada.

        Args:
            request (Request): Objeto da requisição HTTP. Deve conter
                ``datas`` (list[str]) e ``justificativa`` no body.
            uuid (str, optional): UUID da instância de
                ``GrupoSuspensaoAlimentacao``. Padrão: None.

        Returns:
            Response: Dados serializados da solicitação após o cancelamento,
            ou erro 400 em caso de transição inválida ou solicitação já
            cancelada.

        Raises:
            InvalidTransitionError: Quando a transição de estado não é
                permitida pelo workflow.
            AssertionError: Quando a solicitação já está cancelada.
        """
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
        """Remove a solicitação se o status permitir exclusão.
        - somente solicitações com status RASCUNHO podem ser excluídas.
        - permissão: Escola terceirizada.

        Args:
            request (Request): Objeto da requisição HTTP.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais, incluindo ``uuid`` do
                objeto.

        Returns:
            Response: Resposta vazia com status 204 em caso de sucesso, ou
            erro 403 quando o status não permite exclusão.
        """
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
        """Gera e retorna o relatório da suspensão de alimentação em PDF.
        - permissão: qualquer usuário autenticado com acesso à solicitação.

        Args:
            request (Request): Objeto da requisição HTTP.
            uuid (str, optional): UUID da instância de
                ``GrupoSuspensaoAlimentacao``. Padrão: None.

        Returns:
            HttpResponse: Resposta contendo o PDF do relatório gerado.
        """
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
        """Marca a suspensão como conferida pela empresa terceirizada.
        - ou seja, a empresa visualizou a solicitação e está ciente.
        - permissão: qualquer usuário autenticado.

        Args:
            request (Request): Objeto da requisição HTTP contendo o usuário
                autenticado.
            uuid (str, optional): UUID da instância de
                ``GrupoSuspensaoAlimentacao``. Padrão: None.

        Returns:
            Response: Dados serializados da solicitação após a marcação, ou
            erro 400 em caso de falha.
        """
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
    """Viewset para listagem dos motivos de suspensão de alimentação.

    Fornece acesso somente-leitura aos motivos cadastrados, utilizados
    como opções na criação de solicitações de suspensão.

    Actions disponíveis:
        - ``list``: Lista todos os motivos de suspensão.
        - ``retrieve``: Retorna um motivo específico por UUID.
    """

    lookup_field = "uuid"
    queryset = MotivoSuspensao.objects.all()
    serializer_class = MotivoSuspensaoSerializer
