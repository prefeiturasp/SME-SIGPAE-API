from rest_framework.decorators import action
from rest_framework.response import Response

from src.cardapio.alteracao_tipo_alimentacao.api.viewsets import (
    AlteracoesCardapioViewSet,
)
from src.cardapio.alteracao_tipo_alimentacao_cei.api.serializers import (
    AlteracaoCardapioCEISerializer,
)
from src.cardapio.alteracao_tipo_alimentacao_cei.api.serializers_create import (
    AlteracaoCardapioCEISerializerCreate,
)
from src.cardapio.alteracao_tipo_alimentacao_cei.models import (
    AlteracaoCardapioCEI,
)
from src.dados_comuns import constants
from src.dados_comuns.permissions import (
    UsuarioCODAEGestaoAlimentacao,
    UsuarioDiretoriaRegional,
    UsuarioEmpresaGenerico,
    UsuarioEscolaTercTotal,
)
from src.relatorios.relatorios import relatorio_alteracao_cardapio_cei


class AlteracoesCardapioCEIViewSet(AlteracoesCardapioViewSet):
    """ViewSet para gerenciar solicitacoes de Alteracao do Tipo de Alimentacao CEI.

    Herda todas as actions de fluxo de ``AlteracoesCardapioViewSet`` (inicio de
    pedido, validacao DRE, autorizacao CODAE, cancelamento, etc.) e sobrescreve
    o queryset, os serializers e as actions de listagem por perfil para operar
    sobre ``AlteracaoCardapioCEI``.

    Tipos de unidade contemplados:
        - CEI DIRET
        - CEU CEI
        - CCI/CIPS
    """

    queryset = AlteracaoCardapioCEI.objects.all()

    def get_serializer_class(self) -> type:
        """Retorna a classe de serializer adequada para a acao atual.

        - Para as acoes ``create``, ``update`` e ``partial_update``: utiliza
          ``AlteracaoCardapioCEISerializerCreate``.
        - Para as demais acoes: utiliza ``AlteracaoCardapioCEISerializer``.

        Returns:
            type: Classe de serializer a ser utilizada na acao corrente.
        """
        if self.action in ["create", "update", "partial_update"]:
            return AlteracaoCardapioCEISerializerCreate
        return AlteracaoCardapioCEISerializer

    @action(
        detail=False,
        url_path=constants.SOLICITACOES_DO_USUARIO,
        permission_classes=(UsuarioEscolaTercTotal,),
    )
    def minhas_solicitacoes(self, request) -> Response:
        """Retorna as solicitacoes de Alteracao de Tipo de Alimentacao CEI do usuario logado que estao em RASCUNHO.
          - permissao: Escola terceirizada.

        Os resultados sao paginados.

        Args:
            request (Request): Objeto da requisicao HTTP contendo o usuario autenticado.

        Returns:
            Response: Resposta paginada com a lista de alteracoes de cardapio CEI em rascunho do usuario.
        """
        usuario = request.user
        alteracoes_cardapio_rascunho = AlteracaoCardapioCEI.get_rascunhos_do_usuario(
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
        """Retorna todas as solicitacoes de Alteracao de Tipo de Alimentacao CEI para a CODAE:
          - com status DRE_VALIDADO, para a CODAE autorizar, negar ou pedir questionamento a empresa do lote;
          - utilizado em tela para dividir as solicitacoes por prioridade (proximas ao vencimento, prazo limite, prazo regular).
          - permissao: CODAE Gestao de Alimentacao.

        Filtra opcionalmente por diretoria regional e/ou lote via query params.

        Args:
            request (Request): Objeto da requisicao HTTP. Aceita ``diretoria_regional`` e
                ``lote`` como query params opcionais.
            filtro_aplicado (str): Filtro de status aplicado as solicitacoes.
                Padrao: ``constants.SEM_FILTRO``.

        Returns:
            Response: Lista serializada das alteracoes de cardapio CEI encontradas.
        """
        usuario = request.user
        codae = usuario.vinculo_atual.instituicao
        alteracoes_cardapio = codae.alteracoes_cardapio_cei_das_minhas(filtro_aplicado)
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
    def solicitacoes_diretoria_regional(
        self, request, filtro_aplicado=constants.SEM_FILTRO
    ) -> Response:
        """Retorna as solicitacoes de Alteracao do Tipo de Alimentacao CEI das escolas vinculadas a DRE do usuario:
          - com status DRE_A_VALIDAR, para a DRE validar ou nao validar;
          - utilizado em tela para dividir as solicitacoes por prioridade (proximas ao vencimento, prazo limite, prazo regular).
          - permissao: Diretoria Regional.

        Filtra opcionalmente por lote via query param.

        Args:
            request (Request): Objeto da requisicao HTTP contendo o usuario autenticado.
                Aceita ``lote`` como query param opcional.
            filtro_aplicado (str): Filtro de status aplicado as solicitacoes.
                Padrao: ``constants.SEM_FILTRO``.

        Returns:
            Response: Lista serializada das alteracoes de cardapio CEI encontradas para a DRE.
        """
        usuario = request.user
        dre = usuario.vinculo_atual.instituicao
        alteracoes_cardapio = dre.alteracoes_cardapio_cei_das_minhas_escolas(
            filtro_aplicado
        )
        if request.query_params.get("lote"):
            lote_uuid = request.query_params.get("lote")
            alteracoes_cardapio = alteracoes_cardapio.filter(
                rastro_lote__uuid=lote_uuid
            )
        serializer = self.get_serializer(alteracoes_cardapio, many=True)
        return Response({"results": serializer.data})

    @action(
        detail=False,
        url_path=f"{constants.PEDIDOS_TERCEIRIZADA}/{constants.FILTRO_PADRAO_PEDIDOS}",
        permission_classes=[UsuarioEmpresaGenerico],
    )
    def solicitacoes_terceirizada(
        self, request, filtro_aplicado=constants.SEM_FILTRO
    ) -> Response:
        """Retorna as solicitacoes de Alteracao do Tipo de Alimentacao CEI da terceirizada do usuario.
          - permissao: empresa terceirizada.

        Os resultados sao paginados.

        Args:
            request (Request): Objeto da requisicao HTTP contendo o usuario autenticado.
            filtro_aplicado (str): Filtro de status aplicado as solicitacoes.
                Padrao: ``constants.SEM_FILTRO``.

        Returns:
            Response: Resposta paginada com a lista de alteracoes de cardapio CEI da terceirizada.
        """
        usuario = request.user
        terceirizada = usuario.vinculo_atual.instituicao
        alteracoes_cardapio = terceirizada.alteracoes_cardapio_cei_das_minhas(
            filtro_aplicado
        )

        page = self.paginate_queryset(alteracoes_cardapio)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=["GET"], url_path=f"{constants.RELATORIO}")
    def relatorio(self, request, uuid=None) -> Response:
        """Gera e retorna o relatorio da Alteracao do Tipo de Alimentacao CEI em formato PDF.
          - permissao: qualquer usuario autenticado com acesso a solicitacao.

        Args:
            request (Request): Objeto da requisicao HTTP.
            uuid (str, optional): UUID da instancia de ``AlteracaoCardapioCEI``. Padrao: None.

        Returns:
            HttpResponse: Resposta contendo o PDF do relatorio gerado.
        """
        return relatorio_alteracao_cardapio_cei(request, solicitacao=self.get_object())
