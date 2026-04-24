import datetime

from django.db.models import QuerySet
from django.http import HttpResponse
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
from sme_sigpae_api.dados_comuns.mixins.serializer_context import (
    DataSolicitacaoContextMixin,
)
from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoParaRecuperarObjeto,
    UsuarioCODAEGestaoAlimentacao,
    UsuarioDiretoriaRegional,
    UsuarioEmpresaGenerico,
    UsuarioEscolaTercTotal,
)
from sme_sigpae_api.dados_comuns.services import (
    enviar_email_ue_cancelar_pedido_parcialmente,
)
from sme_sigpae_api.escola.models import Escola
from sme_sigpae_api.relatorios.relatorios import relatorio_alteracao_cardapio


class AlteracoesCardapioViewSet(DataSolicitacaoContextMixin, viewsets.ModelViewSet):
    lookup_field = "uuid"
    permission_classes = (IsAuthenticated,)
    queryset = AlteracaoCardapio.objects.all()

    def get_permissions(self) -> list:
        """Retorna a lista de permissões necessárias para a ação atual.

        - Para a ação ``list``: requer ``UsuarioEscolaTercTotal``.
        - Para as ações ``retrieve`` e ``update``: requer autenticação e ``PermissaoParaRecuperarObjeto``.
        - Para as ações ``create`` e ``destroy``: requer ``UsuarioEscolaTercTotal``.

        Returns:
            list: Lista de instâncias de classes de permissão configuradas para a ação atual.
        """
        if self.action in ["list"]:
            self.permission_classes = (UsuarioEscolaTercTotal,)
        elif self.action in ["retrieve", "update"]:
            self.permission_classes = (IsAuthenticated, PermissaoParaRecuperarObjeto)
        elif self.action in ["create", "destroy"]:
            self.permission_classes = (UsuarioEscolaTercTotal,)
        return super(AlteracoesCardapioViewSet, self).get_permissions()

    def get_serializer_class(self) -> type:
        """Retorna a classe de serializer adequada para a ação atual.

        - Para as ações ``create``, ``update`` e ``partial_update``: utiliza ``AlteracaoCardapioSerializerCreate``.
        - Para as demais ações: utiliza ``AlteracaoCardapioSerializer``.

        Returns:
            type: Classe de serializer a ser utilizada na ação corrente.
        """
        if self.action in ["create", "update", "partial_update"]:
            return AlteracaoCardapioSerializerCreate
        return AlteracaoCardapioSerializer

    @action(
        detail=False,
        url_path=constants.SOLICITACOES_DO_USUARIO,
        permission_classes=(UsuarioEscolaTercTotal,),
    )
    def minhas_solicitacoes(self, request) -> Response:
        """Retorna as solicitações de Alteração de Tipo de Alimentação do usuário logado que estão em RASCUNHO.
          - permissão: Escola terceirizada.

        Os resultados são paginados.

        Args:
            request (Request): Objeto da requisição HTTP contendo o usuário autenticado.

        Returns:
            Response: Resposta paginada com a lista de alterações de cardápio em rascunho do usuário.
        """
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
    def solicitacoes_codae(
        self, request, filtro_aplicado=constants.SEM_FILTRO
    ) -> Response:
        """Retorna as todas solicitações de Alteração de Tipo de Alimentação:
          - com status DRE_VALIDADO, para a CODAE autorizar, negar ou pedir questionamento à empresa do lote;
          - utilizado em tela para dividir as solicitações por prioridade (próximas ao vencimento, prazo limite, prazo regular).
          - permissão: CODAE Gestão de Alimentação.

        Filtra opcionalmente por diretoria regional e/ou lote via query params.

        Args:
            request (Request): Objeto da requisição HTTP. Aceita ``diretoria_regional`` e
                ``lote`` como query params opcionais.
            filtro_aplicado (str): Filtro de status aplicado às solicitações.
                Padrão: ``constants.SEM_FILTRO``.

        Returns:
            Response: Lista serializada das alterações de cardápio encontradas.
        """
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
        serializer = self.get_serializer(alteracoes_cardapio, many=True)
        return Response({"results": serializer.data})

    @action(
        detail=False,
        url_path=f"{constants.PEDIDOS_DRE}/{constants.FILTRO_PADRAO_PEDIDOS}",
        permission_classes=[UsuarioDiretoriaRegional],
    )
    def solicitacoes_dre(
        self, request, filtro_aplicado=constants.SEM_FILTRO
    ) -> Response:
        """Retorna as solicitações de Alteração do Tipo de Alimentação das escolas vinculadas à DRE do usuário:
          - com status DRE_A_VALIDAR, para a DRE validar ou não validar;
          - utilizado em tela para dividir as solicitações por prioridade (próximas ao vencimento, prazo limite, prazo regular).
          - permissão: Diretoria Regional.

        Filtra opcionalmente por lote via query param.

        Args:
            request (Request): Objeto da requisição HTTP contendo o usuário autenticado.
            filtro_aplicado (str): Filtro de status aplicado às solicitações.
                Padrão: ``constants.SEM_FILTRO``.

        Returns:
            Response: Lista serializada das alterações de cardápio encontradas para a DRE.
        """
        usuario = request.user
        dre = usuario.vinculo_atual.instituicao
        alteracoes_cardapio = dre.alteracoes_cardapio_das_minhas_escolas_a_validar(
            filtro_aplicado
        )
        serializer = AlteracaoCardapioSimplesSerializer(alteracoes_cardapio, many=True)
        return Response({"results": serializer.data})

    @action(detail=True, methods=["GET"], url_path=f"{constants.RELATORIO}")
    def relatorio(self, request, uuid=None) -> HttpResponse:
        """Gera e retorna o relatório da Alteração do Tipo de Alimentação em formato PDF.
        - permissão: qualquer usuário autenticado com acesso à solicitação.

        Args:
            request (Request): Objeto da requisição HTTP.
            uuid (str, optional): UUID da instância de ``AlteracaoCardapio``. Padrão: None.

        Returns:
            HttpResponse: Resposta contendo o PDF do relatório gerado.
        """
        return relatorio_alteracao_cardapio(request, solicitacao=self.get_object())

    @action(
        detail=True,
        permission_classes=[UsuarioEscolaTercTotal],
        methods=["patch"],
        url_path=constants.ESCOLA_INICIO_PEDIDO,
    )
    def inicio_de_solicitacao(self, request, uuid=None) -> Response:
        """Inicia o fluxo de uma solicitação de Alteração do Tipo de Alimentação pela escola:
          - sai do status RASCUNHO e passa para DRE_A_VALIDAR, ficando disponível para validação da DRE.
          - somente é permitido iniciar o fluxo se a solicitação estiver em RASCUNHO.
          - permissão: Escola terceirizada.

        Args:
            request (Request): Objeto da requisição HTTP contendo o usuário autenticado.
            uuid (str, optional): UUID da instância de ``AlteracaoCardapio``. Padrão: None.

        Returns:
            Response: Dados serializados da alteração após a transição de estado, ou erro 400
                em caso de transição inválida.

        Raises:
            InvalidTransitionError: Quando a transição de estado não é permitida pelo workflow.
        """
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
    def diretoria_regional_valida(self, request, uuid=None) -> Response:
        """Valida a solicitação de Alteração do Tipo de Alimentação pela Diretoria Regional com status DRE_A_VALIDAR:
            - passa para o status DRE_VALIDADO, ficando disponível para a CODAE autorizar, negar ou pedir questionamento à empresa do lote.
            - permissão: Diretoria Regional.

        Args:
            request (Request): Objeto da requisição HTTP contendo o usuário autenticado.
            uuid (str, optional): UUID da instância de ``AlteracaoCardapio``. Padrão: None.

        Returns:
            Response: Dados serializados da alteração após a validação, ou erro 400
                em caso de transição inválida.

        Raises:
            InvalidTransitionError: Quando a transição de estado não é permitida pelo workflow.
        """
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
    def dre_nao_valida_solicitacao(self, request, uuid=None) -> Response:
        """Registra a não validação da solicitação de Alteração de Tipo de Alimentação pela DRE com status DRE_A_VALIDAR:
            - passa para o status DRE_NAO_VALIDOU_PEDIDO_ESCOLA, não validando o pedido da Escola; fim de fluxo.
            - permissão: Diretoria Regional.


        Args:
            request (Request): Objeto da requisição HTTP. Deve conter ``justificativa`` no body.
            uuid (str, optional): UUID da instância de ``AlteracaoCardapio``. Padrão: None.

        Returns:
            Response: Dados serializados da alteração após a transição, ou erro 400
                em caso de transição inválida.

        Raises:
            InvalidTransitionError: Quando a transição de estado não é permitida pelo workflow.
        """
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
    def codae_nega_solicitacao(self, request, uuid=None) -> Response:
        """Registra a negação da solicitação de Alteração de Tipo de Alimentação pela CODAE, quando está com status DRE_VALIDADO:
            - passa para o status CODAE_NEGOU_PEDIDO, negando o pedido da Escola; fim de fluxo.
            - permissão: CODAE Gestão de Alimentação.

        Se o status atual for ``DRE_VALIDADO``, aplica ``codae_nega``; caso contrário (ex: após questionamento à empresa),
        aplica ``codae_nega_questionamento``.

        Args:
            request (Request): Objeto da requisição HTTP. Deve conter ``justificativa`` no body.
            uuid (str, optional): UUID da instância de ``AlteracaoCardapio``. Padrão: None.

        Returns:
            Response: Dados serializados da alteração após a transição, ou erro 400
                em caso de transição inválida.

        Raises:
            InvalidTransitionError: Quando a transição de estado não é permitida pelo workflow.
        """
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
    def codae_autoriza(self, request, uuid=None) -> Response:
        """Autoriza a solicitação de Alteração de Tipo de Alimentação pela CODAE.
            - caso a solicitação estiver dentro do prazo de 5 dias úteis, pode ser autorizada diretamente após DRE validar.
            - caso contrário (data < 5 dias úteis), é autorizada após confirmação do atendimento pela empresa.
            - permissão: CODAE Gestão de Alimentação.

        Args:
            request (Request): Objeto da requisição HTTP. Pode conter ``justificativa`` no body.
            uuid (str, optional): UUID da instância de ``AlteracaoCardapio``. Padrão: None.

        Returns:
            Response: Dados serializados da alteração após a autorização, ou erro 400
                em caso de transição inválida.

        Raises:
            InvalidTransitionError: Quando a transição de estado não é permitida pelo workflow.
        """
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
    def codae_questiona_pedido(self, request, uuid=None) -> Response:
        """Registra o questionamento da CODAE sobre a solicitação de Alteração de Tipo de Alimentação.
           - a solicitação é questionada se chegar na CODAE entre 2 e 5 dias úteis antes do atendimento.
           - a solicitação deve estar com status DRE_VALIDADO para ser questionada.
           - passa para o status CODAE_QUESTIONADO, ficando pendente da resposta da empresa
           - permissão: CODAE Gestão de Alimentação.


        Args:
            request (Request): Objeto da requisição HTTP. Deve conter
                ``observacao_questionamento_codae`` no body.
            uuid (str, optional): UUID da instância de ``AlteracaoCardapio``. Padrão: None.

        Returns:
            Response: Dados serializados da alteração após o questionamento, ou erro 400
                em caso de transição inválida.

        Raises:
            InvalidTransitionError: Quando a transição de estado não é permitida pelo workflow.
        """
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
        permission_classes=[UsuarioEmpresaGenerico],
        methods=["patch"],
        url_path=constants.TERCEIRIZADA_TOMOU_CIENCIA,
    )
    def terceirizada_toma_ciencia(self, request, uuid=None) -> Response:
        """Registra que a terceirizada tomou ciência da Alteração de Tipo de Alimentação.

        Args:
            request (Request): Objeto da requisição HTTP contendo o usuário autenticado.
            uuid (str, optional): UUID da instância de ``AlteracaoCardapio``. Padrão: None.

        Returns:
            Response: Dados serializados da alteração após o registro de ciência, ou erro 400
                em caso de transição inválida.

        Raises:
            InvalidTransitionError: Quando a transição de estado não é permitida pelo workflow.
        """
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
        permission_classes=[UsuarioEmpresaGenerico],
        methods=["patch"],
        url_path=constants.TERCEIRIZADA_RESPONDE_QUESTIONAMENTO,
    )
    def terceirizada_responde_questionamento(self, request, uuid=None) -> Response:
        """Registra a resposta da terceirizada ao questionamento da CODAE, da solicitação com status CODAE_QUESTIONADO.
            - a solicitação vai para o status TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO;
            - a resposta pode ser sim ou não, e deve conter uma justificativa.
              - caso a resposta seja sim, CODAE pode autorizar a solicitação normalmente.
              - caso a resposta seja não, CODAE deve negar a solicitação, passando para o status CODAE_NEGOU_PEDIDO.
            - permissão: Empresa terceirizada.

        Args:
            request (Request): Objeto da requisição HTTP. Deve conter ``justificativa`` e
                ``resposta_sim_nao`` no body.
            uuid (str, optional): UUID da instância de ``AlteracaoCardapio``. Padrão: None.

        Returns:
            Response: Dados serializados da alteração após a resposta, ou erro 400
                em caso de transição inválida.

        Raises:
            InvalidTransitionError: Quando a transição de estado não é permitida pelo workflow.
        """
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

    def valida_datas(self, obj, datas) -> None:
        """Valida cada data individualmente, verificando se esta pode ser cancelada (se está dentro do intervalo de 48 úteis após hoje).
            - função auxiliar para o cancelamento parcial da solicitação pela escola.

        Args:
            obj (AlteracaoCardapio): Instância da alteração do tipo de alimentação a ser validada.
            datas (list[str]): Lista de datas no formato ``"%Y-%m-%d"`` a serem verificadas.

        Raises:
            Exception: Quando alguma data não permite cancelamento conforme a regra de negócio.
        """
        if datas:
            for data in datas:
                data_obj = datetime.datetime.strptime(data, "%Y-%m-%d").date()
                obj.checa_se_pode_cancelar(data_obj)

    def _validar_cancelamento(self, obj, datas) -> None:
        """Valida se a solicitação pode ser cancelada, levantando exceção em caso negativo.

        Verifica se a solicitação já está cancelada e se as datas informadas permitem
        cancelamento conforme a regra de negócio.

        Args:
            obj (AlteracaoCardapio): Instância da alteração do tipo de alimentação a ser validada.
            datas (list[str]): Lista de datas no formato ``"%Y-%m-%d"`` a serem verificadas.

        Raises:
            InvalidTransitionError: Quando a solicitação já está com status ``ESCOLA_CANCELOU``.
            Exception: Quando alguma data não permite cancelamento conforme a regra de negócio.
        """
        if obj.status == obj.workflow_class.ESCOLA_CANCELOU:
            raise InvalidTransitionError("Solicitação já está cancelada")

        self.valida_datas(obj, datas)

    def _deve_cancelar_totalmente(self, obj, datas) -> bool:
        """Determina se a solicitação deve ser cancelada totalmente ou apenas parcialmente.

        Retorna ``True`` quando:
        - o objeto não possui ``datas_intervalo``;
        - ``data_inicial == data_final`` (solicitação de dia único);
        - o número de datas a cancelar somado às já canceladas equivale ao total do intervalo.

        Args:
            obj (AlteracaoCardapio): Instância da alteração do tipo de alimentação.
            datas (list[str]): Lista de datas selecionadas para cancelamento.

        Returns:
            bool: ``True`` se a solicitação deve ser cancelada totalmente; ``False`` se parcialmente.
        """
        datas_intervalo = getattr(obj, "datas_intervalo", None)

        if not datas_intervalo:
            return True

        if obj.data_inicial == obj.data_final:
            return True

        total = datas_intervalo.count()
        cancelados = datas_intervalo.filter(cancelado=True).count()

        return len(datas) + cancelados == total

    def _atualizar_datas_canceladas(self, obj, datas, justificativa) -> None:
        """Marca as datas informadas como canceladas no intervalo da solicitação.

        Atualiza os campos ``cancelado`` e ``cancelado_justificativa`` nas instâncias de
        ``datas_intervalo`` cujas datas estejam na lista fornecida. Não faz nada se o objeto
        não possuir ``datas_intervalo``.

        Args:
            obj (AlteracaoCardapio): Instância da alteração do tipo de alimentação.
            datas (list[str]): Lista de datas no formato ``"%Y-%m-%d"`` a serem marcadas como canceladas.
            justificativa (str): Justificativa para o cancelamento das datas.
        """
        datas_intervalo = getattr(obj, "datas_intervalo", None)

        if not datas_intervalo:
            return

        datas_intervalo.filter(data__in=datas).update(
            cancelado=True,
            cancelado_justificativa=justificativa,
        )

    @action(
        detail=True,
        permission_classes=[UsuarioEscolaTercTotal],
        methods=["patch"],
        url_path=constants.ESCOLA_CANCELA,
    )
    def escola_cancela_pedido(self, request, uuid=None) -> Response:
        """Cancela total ou parcialmente a solicitação de Alteração do Tipo de Alimentação pela escola.
            - permissão: Escola terceirizada.

        Cancela totalmente quando não há datas de intervalo, quando ``data_inicial == data_final``,
        ou quando todas as datas do intervalo serão canceladas. Caso contrário, realiza cancelamento
        parcial e envia notificação por e-mail.

        Args:
            request (Request): Objeto da requisição HTTP. Deve conter ``datas`` (list[str]) e
                ``justificativa`` no body.
            uuid (str, optional): UUID da instância de ``AlteracaoCardapio``. Padrão: None.

        Returns:
            Response: Dados serializados da alteração após o cancelamento, ou erro 400
                em caso de transição inválida ou solicitação já cancelada.

        Raises:
            InvalidTransitionError: Quando a transição de estado não é permitida pelo workflow.
            AssertionError: Quando a solicitação já está cancelada.
        """
        obj = self.get_object()
        datas = request.data.get("datas", [])
        justificativa = request.data.get("justificativa", "")
        try:
            self._validar_cancelamento(obj, datas)

            if self._deve_cancelar_totalmente(obj, datas):
                obj.cancelar_pedido(user=request.user, justificativa=justificativa)
            else:
                enviar_email_ue_cancelar_pedido_parcialmente(obj)

            self._atualizar_datas_canceladas(obj, datas, justificativa)

            return Response(self.get_serializer(obj).data)

        except (InvalidTransitionError, AssertionError) as e:
            return Response(
                {"detail": f"Erro de transição de estado: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False,
        url_path=f"{constants.PEDIDOS_DRE}/{constants.FILTRO_PADRAO_PEDIDOS}",
        permission_classes=[UsuarioDiretoriaRegional],
    )
    def solicitacoes_diretoria_regional(
        self, request, filtro_aplicado="sem_filtro"
    ) -> Response:
        """Retorna as solicitações de Alteração do Tipo de Alimentação das escolas da diretoria regional.
            - consolida em uma única pesquisa as buscas por prioridade.
            - filtra opcionalmente por lote via query param.
            - permissão: Diretoria Regional.

        Args:
            request (Request): Objeto da requisição HTTP. Aceita ``lote`` como query param opcional.
            filtro_aplicado (str): Filtro de status aplicado às solicitações. Padrão: ``"sem_filtro"``.

        Returns:
            Response: Lista serializada das alterações de cardápio encontradas para a diretoria regional.
        """
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
        serializer = self.get_serializer(alteracoes_cardapio, many=True)
        return Response({"results": serializer.data})

    def destroy(self, request, *args, **kwargs) -> Response:
        """Remove a Alteração do Tipo de Alimentação se o status permitir exclusão.
            - somente solicitações com status RASCUNHO podem ser excluídas.
            - permissão: Escola terceirizada.

        Args:
            request (Request): Objeto da requisição HTTP.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais, incluindo ``uuid`` do objeto.

        Returns:
            Response: Resposta vazia com status 204 em caso de sucesso, ou erro 403
                quando o status não permite exclusão.
        """
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
        permission_classes=(UsuarioEmpresaGenerico,),
    )
    def terceirizada_marca_inclusao_como_conferida(
        self, request, uuid=None
    ) -> Response:
        """Marca a Alteração do Tipo de Alimentação como conferida pela empresa terceirizada.
            - ou seja, a empresa visualizou a solicitação e está ciente da alteração solicitada.
            - permissão: Empresa terceirizada.

        Args:
            request (Request): Objeto da requisição HTTP contendo o usuário autenticado.
            uuid (str, optional): UUID da instância de ``AlteracaoTipoAlimentacao``. Padrão: None.

        Returns:
            Response: Dados serializados da alteração após a marcação, ou erro 400 em caso de falha.
        """
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

    def get_queryset(self) -> QuerySet[MotivoAlteracaoCardapio]:
        """Retorna o queryset de ``MotivoAlteracaoCardapio`` que estão ativos.
            - exclui o motivo "Lanche Emergencial" para usuários vinculados a escolas do tipo CEI.
            - permissão: qualquer usuário autenticado.

        Returns:
            QuerySet: QuerySet de ``MotivoAlteracaoCardapio`` ativos, ajustado conforme o perfil
                da instituição do usuário.
        """
        user = self.request.user
        queryset = MotivoAlteracaoCardapio.objects.filter(ativo=True)
        if (
            isinstance(user.vinculo_atual.instituicao, Escola)
            and user.vinculo_atual.instituicao.eh_cei
        ):
            return queryset.exclude(nome__icontains="Lanche Emergencial")
        return queryset
