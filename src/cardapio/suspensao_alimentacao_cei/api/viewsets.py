from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from xworkflows import InvalidTransitionError

from src.cardapio.suspensao_alimentacao_cei.api.serializers import (
    SuspensaoAlimentacaoDaCEISerializer,
)
from src.cardapio.suspensao_alimentacao_cei.api.serializers_create import (
    SuspensaoAlimentacaodeCEICreateSerializer,
)
from src.cardapio.suspensao_alimentacao_cei.models import (
    SuspensaoAlimentacaoDaCEI,
)
from src.dados_comuns import constants
from src.dados_comuns.mixins.serializer_context import (
    DataSolicitacaoContextMixin,
)
from src.dados_comuns.permissions import (
    PermissaoParaRecuperarObjeto,
    UsuarioEscolaTercTotal,
)
from src.relatorios.relatorios import relatorio_suspensao_de_alimentacao_cei


class SuspensaoAlimentacaoDaCEIViewSet(
    DataSolicitacaoContextMixin, viewsets.ModelViewSet
):
    """ViewSet para gerenciamento de solicitações de suspensão de CEI.

    Gerencia o ciclo de vida completo das solicitações de suspensão de
    alimentação de CEI: criação, leitura, atualização, exclusão e ações do
    fluxo informativo partindo da escola.

    Actions de fluxo disponíveis:
        - ``informa_suspensao``: Escola informa a suspensão (RASCUNHO → INFORMADO).
        - ``cancela_suspensao_cei``: Escola cancela a suspensão (INFORMADO/TERCEIRIZADA_TOMOU_CIENCIA → ESCOLA_CANCELOU).
    """

    lookup_field = "uuid"
    queryset = SuspensaoAlimentacaoDaCEI.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = SuspensaoAlimentacaoDaCEISerializer

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
            self.permission_classes = (IsAuthenticated, PermissaoParaRecuperarObjeto)
        elif self.action in ["create", "destroy"]:
            self.permission_classes = (UsuarioEscolaTercTotal,)
        return super(SuspensaoAlimentacaoDaCEIViewSet, self).get_permissions()

    def get_serializer_class(self):
        """Retorna a classe de serializer adequada para a ação atual.

        - Para as ações ``create``, ``update`` e ``partial_update``: utiliza
          ``SuspensaoAlimentacaodeCEICreateSerializer``.
        - Para as demais ações: utiliza
          ``SuspensaoAlimentacaoDaCEISerializer``.

        Returns:
            type: Classe de serializer a ser utilizada na ação corrente.
        """
        if self.action in ["create", "update", "partial_update"]:
            return SuspensaoAlimentacaodeCEICreateSerializer
        return SuspensaoAlimentacaoDaCEISerializer

    @action(detail=False, methods=["GET"])
    def informadas(self, request):
        """Retorna as suspensões de CEI com status INFORMADO.
        - permissão: qualquer usuário autenticado.

        Os resultados são ordenados por ID decrescente.

        Args:
            request (Request): Objeto da requisição HTTP.

        Returns:
            Response: Lista serializada das suspensões de CEI informadas.
        """
        informados = SuspensaoAlimentacaoDaCEI.get_informados().order_by("-id")
        serializer = SuspensaoAlimentacaoDaCEISerializer(informados, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["GET"], permission_classes=(UsuarioEscolaTercTotal,))
    def meus_rascunhos(self, request):
        """Retorna as suspensões de CEI em rascunho do usuário logado.
        - permissão: Escola terceirizada.

        Os resultados são paginados.

        Args:
            request (Request): Objeto da requisição HTTP contendo o usuário
                autenticado.

        Returns:
            Response: Resposta paginada com a lista de rascunhos do usuário.
        """
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
        """Informa a suspensão de CEI, iniciando o fluxo pela escola.
        - sai do status RASCUNHO e passa para INFORMADO.
        - permissão: Escola terceirizada.

        Args:
            request (Request): Objeto da requisição HTTP contendo o usuário
                autenticado.
            uuid (str, optional): UUID da instância de
                ``SuspensaoAlimentacaoDaCEI``. Padrão: None.

        Returns:
            Response: Dados serializados da solicitação após a transição, ou
            erro 400 em caso de transição inválida.

        Raises:
            InvalidTransitionError: Quando a transição de estado não é
                permitida pelo workflow.
        """
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
        """Cancela a suspensão de CEI pela escola.

        Passa do status INFORMADO ou TERCEIRIZADA_TOMOU_CIENCIA para
        ESCOLA_CANCELOU.

        - permissão: Escola terceirizada.

        Args:
            request (Request): Objeto da requisição HTTP. Deve conter
                ``justificativa`` no body.
            uuid (str, optional): UUID da instância de
                ``SuspensaoAlimentacaoDaCEI``. Padrão: None.

        Returns:
            Response: Dados serializados da solicitação após o cancelamento,
            ou erro 400 em caso de transição inválida.

        Raises:
            InvalidTransitionError: Quando a transição de estado não é
                permitida pelo workflow.
        """
        suspensao_de_alimentacao = self.get_object()
        try:
            justificativa = request.data.get("justificativa", "")
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
        """Marca a suspensão de CEI como conferida pela empresa terceirizada.
        - ou seja, a empresa visualizou a solicitação e está ciente.
        - permissão: qualquer usuário autenticado.

        Args:
            request (Request): Objeto da requisição HTTP contendo o usuário
                autenticado.
            uuid (str, optional): UUID da instância de
                ``SuspensaoAlimentacaoDaCEI``. Padrão: None.

        Returns:
            Response: Dados serializados da solicitação após a marcação, ou
            erro 400 em caso de falha.
        """
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
        """Gera e retorna o relatório da suspensão de CEI em PDF.
        - permissão: qualquer usuário autenticado com acesso à solicitação.

        Args:
            request (Request): Objeto da requisição HTTP.
            uuid (str, optional): UUID da instância de
                ``SuspensaoAlimentacaoDaCEI``. Padrão: None.

        Returns:
            HttpResponse: Resposta contendo o PDF do relatório gerado.
        """
        return relatorio_suspensao_de_alimentacao_cei(
            request, solicitacao=self.get_object()
        )
