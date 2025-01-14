import datetime

from django.core.exceptions import ValidationError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.viewsets import GenericViewSet
from xworkflows import InvalidTransitionError

from ...dados_comuns import constants, services
from ...dados_comuns.permissions import (
    PermissaoParaRecuperarObjeto,
    UsuarioCODAEGestaoAlimentacao,
    UsuarioDiretoriaRegional,
    UsuarioEscolaTercTotal,
    UsuarioTerceirizada,
)
from ...escola.api.viewsets import PeriodoEscolarViewSet
from ...escola.constants import PERIODOS_ESPECIAIS_CEMEI
from ...escola.models import Escola, PeriodoEscolar
from ...inclusao_alimentacao.api.viewsets import (
    CodaeAutoriza,
    CodaeQuestionaTerceirizadaResponde,
    DREValida,
    EscolaIniciaCancela,
    TerceirizadaTomaCiencia,
)
from ...inclusao_alimentacao.models import (
    InclusaoAlimentacaoNormal,
    QuantidadePorPeriodo,
)
from ...relatorios.relatorios import (
    relatorio_alteracao_alimentacao_cemei,
    relatorio_alteracao_cardapio,
    relatorio_alteracao_cardapio_cei,
    relatorio_inversao_dia_de_cardapio,
    relatorio_suspensao_de_alimentacao,
    relatorio_suspensao_de_alimentacao_cei,
)
from ..models import (
    AlteracaoCardapio,
    AlteracaoCardapioCEI,
    AlteracaoCardapioCEMEI,
    Cardapio,
    ComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    GrupoSuspensaoAlimentacao,
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
    InversaoCardapio,
    MotivoAlteracaoCardapio,
    MotivoDRENaoValida,
    MotivoSuspensao,
    SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    SuspensaoAlimentacaoDaCEI,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from .serializers.serializers import (
    AlteracaoCardapioCEISerializer,
    AlteracaoCardapioCEMEISerializer,
    AlteracaoCardapioSerializer,
    AlteracaoCardapioSimplesSerializer,
    CardapioSerializer,
    CombosVinculoTipoAlimentoSimplesSerializer,
    GrupoSupensaoAlimentacaoListagemSimplesSerializer,
    GrupoSuspensaoAlimentacaoSerializer,
    GrupoSuspensaoAlimentacaoSimplesSerializer,
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializer,
    InversaoCardapioSerializer,
    MotivoAlteracaoCardapioSerializer,
    MotivoDRENaoValidaSerializer,
    MotivoSuspensaoSerializer,
    SubstituicaoDoComboVinculoTipoAlimentoSimplesSerializer,
    SuspensaoAlimentacaoDaCEISerializer,
    TipoAlimentacaoSerializer,
    VinculoTipoAlimentoSimplesSerializer,
)
from .serializers.serializers_create import (
    AlteracaoCardapioCEISerializerCreate,
    AlteracaoCardapioCEMEISerializerCreate,
    AlteracaoCardapioSerializerCreate,
    CardapioCreateSerializer,
    ComboDoVinculoTipoAlimentoSimplesSerializerCreate,
    GrupoSuspensaoAlimentacaoCreateSerializer,
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializerCreate,
    InversaoCardapioSerializerCreate,
    SubstituicaoDoComboVinculoTipoAlimentoSimplesSerializerCreate,
    SuspensaoAlimentacaodeCEICreateSerializer,
    VinculoTipoAlimentoCreateSerializer,
)


class CardapioViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    serializer_class = CardapioSerializer
    queryset = Cardapio.objects.all().order_by("data")

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CardapioCreateSerializer
        return CardapioSerializer


class TipoAlimentacaoViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    serializer_class = TipoAlimentacaoSerializer
    queryset = TipoAlimentacao.objects.all()


class HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    serializer_class = HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializer
    queryset = HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar.objects.all()

    @action(detail=False, url_path="escola/(?P<escola_uuid>[^/.]+)")
    def filtro_por_escola(self, request, escola_uuid=None):
        combos = HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar.objects.filter(
            escola__uuid=escola_uuid
        )
        page = self.paginate_queryset(combos)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializerCreate
        return HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializer


class VinculoTipoAlimentacaoViewSet(
    viewsets.ModelViewSet,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    lookup_field = "uuid"
    serializer_class = VinculoTipoAlimentoSimplesSerializer
    queryset = (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
            ativo=True
        )
    )

    @action(
        detail=False,
        url_path="tipo_unidade_escolar/(?P<tipo_unidade_escolar_uuid>[^/.]+)",
    )
    def filtro_por_tipo_ue(self, request, tipo_unidade_escolar_uuid=None):
        vinculos = (
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                tipo_unidade_escolar__uuid=tipo_unidade_escolar_uuid, ativo=True
            ).order_by("periodo_escolar__posicao")
        )
        page = self.paginate_queryset(vinculos)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def get_vinculos_inclusoes_evento_especifico(
        self, mes, ano, tipo_solicitacao, escola
    ):
        gupos_uuids = (
            InclusaoAlimentacaoNormal.objects.filter(
                data__month=int(mes),
                data__year=int(ano),
                motivo__nome="Evento Específico",
                grupo_inclusao__escola=escola,
                grupo_inclusao__status="CODAE_AUTORIZADO",
            )
            .values_list("grupo_inclusao__uuid", flat=True)
            .distinct()
        )

        periodos_escolares_uuids = escola.periodos_escolares().values_list(
            "uuid", flat=True
        )

        quantidades_por_periodo = QuantidadePorPeriodo.objects.filter(
            grupo_inclusao_normal__uuid__in=gupos_uuids
        ).exclude(periodo_escolar__uuid__in=periodos_escolares_uuids)

        periodos_escolares_uuids = quantidades_por_periodo.values_list(
            "periodo_escolar__uuid"
        ).distinct()
        vinculos = (
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                tipo_unidade_escolar__iniciais=escola.tipo_unidade.iniciais,
                periodo_escolar__nome__in=constants.PERIODOS_INCLUSAO_MOTIVO_ESPECIFICO,
                periodo_escolar__uuid__in=periodos_escolares_uuids,
            )
        )
        return vinculos

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{constants.VINCULOS_INCLUSOES_EVENTO_ESPECIFICO_AUTORIZADAS}",
    )
    def vinculos_inclusoes_evento_especifico_autorizadas(self, request):
        escola_uuid = request.query_params.get("escola_uuid")
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")
        tipo_solicitacao = request.query_params.get("tipo_solicitacao")
        escola = Escola.objects.get(uuid=escola_uuid)
        vinculos = self.get_vinculos_inclusoes_evento_especifico(
            mes, ano, tipo_solicitacao, escola
        )
        serializer = self.get_serializer(vinculos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def trata_inclusao_continua_medicao_inicial(self, request, escola, ano):
        mes = request.query_params.get("mes", None)
        periodos_escolares_inclusao_continua = None
        if mes:
            periodoEscolarViewset = PeriodoEscolarViewSet()
            response = periodoEscolarViewset.inclusao_continua_por_mes(request)
            if response.data and response.data.get("periodos", None):
                periodos_escolares_inclusao_continua = PeriodoEscolar.objects.filter(
                    uuid__in=list(response.data["periodos"].values())
                )
        periodos_para_filtrar = escola.periodos_escolares(ano)
        if periodos_escolares_inclusao_continua:
            periodos_para_filtrar = (
                periodos_para_filtrar | periodos_escolares_inclusao_continua
            )
        return periodos_para_filtrar

    @action(detail=False, url_path="escola/(?P<escola_uuid>[^/.]+)")
    def filtro_por_escola(self, request, escola_uuid=None):
        escola = Escola.objects.get(uuid=escola_uuid)
        ano = request.query_params.get("ano", datetime.date.today().year)
        periodos_para_filtrar = self.trata_inclusao_continua_medicao_inicial(
            request, escola, ano
        )
        vinculos = (
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                periodo_escolar__in=periodos_para_filtrar, ativo=True
            ).order_by("periodo_escolar__posicao")
        )
        if escola.eh_cemei:
            vinculos = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                periodo_escolar__nome__in=PERIODOS_ESPECIAIS_CEMEI,
                tipo_unidade_escolar__iniciais__in=["CEI DIRET", "EMEI"],
            )
        else:
            vinculos = vinculos.filter(tipo_unidade_escolar=escola.tipo_unidade)
        page = self.paginate_queryset(vinculos)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,  # noqa C901
        url_path="atualizar_lista_de_vinculos",
        methods=["put"],
    )
    def atualizar_lista_de_vinculos(self, request):
        try:
            if "vinculos" not in request.data:
                raise AssertionError("vinculos é um parâmetro obrigatório")
            vinculos_from_request = request.data.get("vinculos", [])
            for vinculo in vinculos_from_request:
                vinculo_class = (
                    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar
                )
                instance = vinculo_class.objects.get(uuid=vinculo["uuid"])
                instance.tipos_alimentacao.set(
                    TipoAlimentacao.objects.filter(
                        uuid__in=vinculo["tipos_alimentacao"]
                    )
                )
                instance.save()
            vinculos_uuids = [vinculo["uuid"] for vinculo in vinculos_from_request]
            vinculos = vinculo_class.objects.filter(uuid__in=vinculos_uuids)
            page = self.paginate_queryset(vinculos)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        except AssertionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["GET"], url_path="motivo_inclusao_especifico")
    def motivo_inclusao_especifico(self, request):
        try:
            tipo_unidade_escolar_iniciais = request.query_params.get(
                "tipo_unidade_escolar_iniciais", ""
            )
            if tipo_unidade_escolar_iniciais:
                vinculos = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                    tipo_unidade_escolar__iniciais=tipo_unidade_escolar_iniciais,
                    periodo_escolar__nome__in=constants.PERIODOS_INCLUSAO_MOTIVO_ESPECIFICO,
                )
                serializer = self.get_serializer(vinculos, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                raise ValidationError(
                    "tipo_unidade_escolar_iniciais é obrigatório via query_params"
                )
        except ValidationError as e:
            return Response({"detail": e}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return VinculoTipoAlimentoCreateSerializer
        return VinculoTipoAlimentoSimplesSerializer


class CombosDoVinculoTipoAlimentacaoPeriodoTipoUEViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    lookup_field = "uuid"
    serializer_class = CombosVinculoTipoAlimentoSimplesSerializer
    queryset = ComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return ComboDoVinculoTipoAlimentoSimplesSerializerCreate
        return CombosVinculoTipoAlimentoSimplesSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.pode_excluir():
            return Response(
                data={
                    "detail": "Não pode excluir, o combo já tem movimentação no sistema"
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubstituicaoDoCombosDoVinculoTipoAlimentacaoPeriodoTipoUEViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    lookup_field = "uuid"
    serializer_class = SubstituicaoDoComboVinculoTipoAlimentoSimplesSerializer
    queryset = SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return SubstituicaoDoComboVinculoTipoAlimentoSimplesSerializerCreate
        return SubstituicaoDoComboVinculoTipoAlimentoSimplesSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.pode_excluir():
            return Response(
                data={
                    "detail": "Não pode excluir, o combo já tem movimentação no sistema"
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
        permission_classes=(UsuarioTerceirizada,),
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
                status=HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=(UsuarioTerceirizada,),
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
                status=HTTP_400_BAD_REQUEST,
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
                services.enviar_email_ue_cancelar_pedido_parcialmente(
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
            )  # noqa


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
        url_path="com-lanche-do-mes-corrente/(?P<escola_uuid>[^/.]+)",
        permission_classes=(UsuarioEscolaTercTotal,),
    )
    def minhas_solicitacoes_do_mes_com_lanches(self, request, escola_uuid):
        alteracoes_cardapio = AlteracaoCardapio.com_lanche_do_mes_corrente(escola_uuid)
        page = self.paginate_queryset(alteracoes_cardapio)
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

    @action(
        detail=False,
        url_path=f"{constants.PEDIDOS_TERCEIRIZADA}/{constants.FILTRO_PADRAO_PEDIDOS}",
        permission_classes=[UsuarioTerceirizada],
    )
    def solicitacoes_terceirizada(self, request, filtro_aplicado=constants.SEM_FILTRO):
        # TODO: colocar regras de Terceirizada aqui...
        usuario = request.user
        terceirizada = usuario.vinculo_atual.instituicao
        alteracoes_cardapio = terceirizada.alteracoes_cardapio_das_minhas(
            filtro_aplicado
        )

        page = self.paginate_queryset(alteracoes_cardapio)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=["GET"], url_path=f"{constants.RELATORIO}")
    def relatorio(self, request, uuid=None):
        return relatorio_alteracao_cardapio(request, solicitacao=self.get_object())

    #
    # IMPLEMENTAÇÃO DO FLUXO (PARTINDO DA ESCOLA)
    #

    @action(
        detail=True,
        permission_classes=[UsuarioEscolaTercTotal],  # noqa C901
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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
                status=HTTP_400_BAD_REQUEST,
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
                services.enviar_email_ue_cancelar_pedido_parcialmente(obj)
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
            )  # noqa


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
        page = self.paginate_queryset(alteracoes_cardapio)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

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
        page = self.paginate_queryset(alteracoes_cardapio)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        url_path=f"{constants.PEDIDOS_TERCEIRIZADA}/{constants.FILTRO_PADRAO_PEDIDOS}",
        permission_classes=[UsuarioTerceirizada],
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


class MotivosSuspensaoCardapioViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "uuid"
    queryset = MotivoSuspensao.objects.all()
    serializer_class = MotivoSuspensaoSerializer


class MotivosDRENaoValidaViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "uuid"
    queryset = MotivoDRENaoValida.objects.all()
    serializer_class = MotivoDRENaoValidaSerializer
