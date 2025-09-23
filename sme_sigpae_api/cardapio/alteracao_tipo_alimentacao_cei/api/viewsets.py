from rest_framework.decorators import action
from rest_framework.response import Response

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.viewsets import (
    AlteracoesCardapioViewSet,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cei.api.serializers import (
    AlteracaoCardapioCEISerializer,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cei.api.serializers_create import (
    AlteracaoCardapioCEISerializerCreate,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cei.models import (
    AlteracaoCardapioCEI,
)
from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.permissions import (
    UsuarioCODAEGestaoAlimentacao,
    UsuarioDiretoriaRegional,
    UsuarioEscolaTercTotal,
    UsuarioEmpresaGenerico,
)
from sme_sigpae_api.relatorios.relatorios import relatorio_alteracao_cardapio_cei


class AlteracoesCardapioCEIViewSet(AlteracoesCardapioViewSet):
    queryset = AlteracaoCardapioCEI.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return AlteracaoCardapioCEISerializerCreate
        return AlteracaoCardapioCEISerializer

    @action(
        detail=False,
        url_path=constants.SOLICITACOES_DO_USUARIO,
        permission_classes=(UsuarioEscolaTercTotal,),
    )
    def minhas_solicitacoes(self, request):
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
    def solicitacoes_codae(self, request, filtro_aplicado=constants.SEM_FILTRO):
        # TODO: colocar regras de codae CODAE aqui...
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
    ):
        # TODO: colocar regras de DRE aqui...
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
    def solicitacoes_terceirizada(self, request, filtro_aplicado=constants.SEM_FILTRO):
        # TODO: colocar regras de Terceirizada aqui...
        usuario = request.user
        terceirizada = usuario.vinculo_atual.instituicao
        alteracoes_cardapio = terceirizada.alteracoes_cardapio_cei_das_minhas(
            filtro_aplicado
        )

        page = self.paginate_queryset(alteracoes_cardapio)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=["GET"], url_path=f"{constants.RELATORIO}")
    def relatorio(self, request, uuid=None):
        return relatorio_alteracao_cardapio_cei(request, solicitacao=self.get_object())
