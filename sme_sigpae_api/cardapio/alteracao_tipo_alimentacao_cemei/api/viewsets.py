from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.viewsets import (
    AlteracoesCardapioViewSet,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.api.serializers import (
    AlteracaoCardapioCEMEISerializer,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.api.serializers_create import (
    AlteracaoCardapioCEMEISerializerCreate,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.models import (
    AlteracaoCardapioCEMEI,
)
from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.permissions import (
    UsuarioCODAEGestaoAlimentacao,
    UsuarioDiretoriaRegional,
)
from sme_sigpae_api.inclusao_alimentacao.api.viewsets import (
    CodaeAutoriza,
    CodaeQuestionaTerceirizadaResponde,
    DREValida,
    EscolaIniciaCancela,
    TerceirizadaTomaCiencia,
)
from sme_sigpae_api.relatorios.relatorios import relatorio_alteracao_alimentacao_cemei


class AlteracoesCardapioCEMEIViewSet(
    AlteracoesCardapioViewSet,
    EscolaIniciaCancela,
    DREValida,
    CodaeAutoriza,
    CodaeQuestionaTerceirizadaResponde,
    TerceirizadaTomaCiencia,
):
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return AlteracaoCardapioCEMEISerializerCreate
        return AlteracaoCardapioCEMEISerializer

    def get_queryset(self):
        queryset = AlteracaoCardapioCEMEI.objects.all()
        user = self.request.user
        if user.tipo_usuario == "escola":
            queryset = queryset.filter(escola=user.vinculo_atual.instituicao)
        if user.tipo_usuario == "diretoriaregional":
            queryset = queryset.filter(rastro_dre=user.vinculo_atual.instituicao)
        if user.tipo_usuario == "terceirizada":
            queryset = queryset.filter(
                rastro_terceirizada=user.vinculo_atual.instituicao
            )
        if "status" in self.request.query_params:
            queryset = queryset.filter(
                status=self.request.query_params.get("status").upper()
            )
        return queryset

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
        alteracoes_cardapio = (
            diretoria_regional.alteracoes_cardapio_cemei_das_minhas_escolas(
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

    @action(
        detail=False,
        url_path=f"{constants.PEDIDOS_CODAE}/{constants.FILTRO_PADRAO_PEDIDOS}",
        permission_classes=(UsuarioCODAEGestaoAlimentacao,),
    )
    def solicitacoes_codae(self, request, filtro_aplicado=constants.SEM_FILTRO):
        usuario = request.user
        codae = usuario.vinculo_atual.instituicao
        alteracoes_cardapio = codae.alteracoes_cardapio_cemei_das_minhas_escolas(
            filtro_aplicado
        )
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
        detail=True,
        methods=["GET"],
        url_path=f"{constants.RELATORIO}",
        permission_classes=(IsAuthenticated,),
    )
    def relatorio(self, request, uuid=None):
        return relatorio_alteracao_alimentacao_cemei(request, self.get_object())
