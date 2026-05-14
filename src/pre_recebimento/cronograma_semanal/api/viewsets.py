from django_filters import rest_framework as filters
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from src.dados_comuns.constants import (
    ADMINISTRADOR_EMPRESA,
    USUARIO_EMPRESA,
)
from src.dados_comuns.permissions import (
    PermissaoParaCriarCronogramaSemanal,
    PermissaoParaDarCienciaCronogramaSemanal,
    PermissaoParaVisualizarCalendarioCronograma,
    PermissaoParaVisualizarCronogramaSemanal,
)
from src.pre_recebimento.base.api.paginations import (
    PreRecebimentoPagination,
)
from src.pre_recebimento.cronograma_entrega.api.serializers.serializers import (
    CronogramaMensalAssinadoSerializer,
)
from src.pre_recebimento.cronograma_entrega.models import Cronograma
from src.pre_recebimento.cronograma_semanal.api.filters import (
    CronogramaSemanalFilter,
)
from src.pre_recebimento.cronograma_semanal.api.serializers.serializer_create import (
    CronogramaSemanalAlterarSerializer,
    CronogramaSemanalAssinarEEnviarSerializer,
    CronogramaSemanalRascunhoSerializer,
)
from src.pre_recebimento.cronograma_semanal.api.serializers.serializers import (
    CronogramaSemanalCalendarioSerializer,
    CronogramaSemanalDetailSerializer,
    CronogramaSemanalListagemSerializer,
    CronogramaSemanalRascunhosSerializer,
)
from src.pre_recebimento.cronograma_semanal.models import CronogramaSemanal
from src.relatorios.relatorios import (
    get_pdf_cronograma_semanal,
)


class CronogramaSemanalViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para CRUD de Cronograma Semanal FLV.
    Apenas perfis DILOG_CRONOGRAMA e COORDENADOR_CODAE_DILOG_LOGISTICA têm acesso.

    Endpoints disponíveis:
    - GET /cronogramas-semanais/ - Lista cronogramas semanais (ordenado por data de alteração)
    - GET /cronogramas-semanais/{uuid}/ - Detalha cronograma semanal
    - POST /cronogramas-semanais/rascunho/ - Cria cronograma semanal como rascunho
    - PATCH /cronogramas-semanais/{uuid}/ - Atualiza cronograma semanal
    - PATCH /cronogramas-semanais/{uuid}/assinar-e-enviar/ - Assina e envia cronograma semanal
    - GET /cronogramas-semanais/cronogramas-mensal-assinados/ - Lista cronogramas mensal Ponto a Ponto assinados
    - GET /cronogramas-semanais/rascunhos/ - Lista cronogramas semanais com status RASCUNHO
    - GET /cronogramas-semanais/{uuid}/ - Detalha cronograma semanal
    - GET /cronogramas-semanais/calendario/
    """

    queryset = CronogramaSemanal.objects.all()
    serializer_class = CronogramaSemanalListagemSerializer
    permission_classes = [PermissaoParaVisualizarCronogramaSemanal]
    permission_action_classes = {
        "rascunho": [PermissaoParaCriarCronogramaSemanal],
        "create": [PermissaoParaCriarCronogramaSemanal],
        "update": [PermissaoParaCriarCronogramaSemanal],
        "partial_update": [PermissaoParaCriarCronogramaSemanal],
        "cronogramas_mensal_assinados": [PermissaoParaVisualizarCronogramaSemanal],
        "fornecedor_ciente": [PermissaoParaDarCienciaCronogramaSemanal],
        "rascunhos_listagem": [PermissaoParaCriarCronogramaSemanal],
        "alterar_cronograma": [PermissaoParaCriarCronogramaSemanal],
        "calendario": [PermissaoParaVisualizarCalendarioCronograma],
    }
    lookup_field = "uuid"
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CronogramaSemanalFilter
    pagination_class = PreRecebimentoPagination

    def get_permissions(self):
        permission_classes = self.permission_action_classes.get(
            self.action, self.permission_classes
        )
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Retorna queryset ordenado por data de alteração (mais recente primeiro)."""
        return (
            CronogramaSemanal.objects.select_related(
                "cronograma_mensal",
                "cronograma_mensal__ficha_tecnica",
                "cronograma_mensal__ficha_tecnica__produto",
                "cronograma_mensal__empresa",
            )
            .prefetch_related("programacoes")
            .order_by("-alterado_em")
        )

    def get_serializer_class(self):
        serializer_map = {
            "rascunho": CronogramaSemanalRascunhoSerializer,
            "update": CronogramaSemanalRascunhoSerializer,
            "partial_update": CronogramaSemanalRascunhoSerializer,
            "assinar_e_enviar": CronogramaSemanalAssinarEEnviarSerializer,
            "alterar_cronograma": CronogramaSemanalAlterarSerializer,
            "rascunhos_listagem": CronogramaSemanalRascunhosSerializer,
            "retrieve": CronogramaSemanalDetailSerializer,
            "fornecedor_ciente": CronogramaSemanalDetailSerializer,
            "list": CronogramaSemanalListagemSerializer,
            "calendario": CronogramaSemanalCalendarioSerializer,
        }
        return serializer_map.get(self.action, CronogramaSemanalListagemSerializer)

    def list(self, request, *args, **kwargs):
        """
        Endpoint: GET /cronogramas-semanais/

        Lista cronogramas semanais ordenados por data de alteração (mais recente primeiro).
        Suporta paginação através do PreRecebimentoPagination.
        """
        vinculo = self.request.user.vinculo_atual
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.order_by("-alterado_em").distinct()

        if (
            vinculo.perfil.nome == ADMINISTRADOR_EMPRESA
            or vinculo.perfil.nome == USUARIO_EMPRESA
        ) and vinculo.instituicao.eh_fornecedor:
            queryset = queryset.filter(
                cronograma_mensal__empresa=vinculo.instituicao
            ).exclude(status="RASCUNHO")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="calendario",
        url_name="calendario",
    )
    def calendario(self, request):
        """
        Lista cronogramas semanais para exibição no calendário.
        Filtra as programações pelo mês e ano informados via query params.
        """
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")
        status_filter = request.query_params.get("status")

        if not mes or not ano:
            return Response(
                {"detail": "Os parâmetros 'mes' e 'ano' são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            mes = int(mes)
            ano = int(ano)
        except ValueError:
            return Response(
                {"detail": "Os parâmetros 'mes' e 'ano' devem ser números inteiros."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = (
            CronogramaSemanal.objects.select_related(
                "cronograma_mensal",
                "cronograma_mensal__ficha_tecnica__produto",
                "cronograma_mensal__empresa",
                "cronograma_mensal__armazem",
                "cronograma_mensal__unidade_medida",
            )
            .prefetch_related("programacoes")
            .filter(
                programacoes__data_inicio__month=mes,
                programacoes__data_inicio__year=ano,
            )
            .exclude(status="RASCUNHO")
            .distinct()
        )

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        serializer = CronogramaSemanalCalendarioSerializer(
            queryset,
            many=True,
            context={"mes": mes, "ano": ano, "request": request},
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["post"],
        url_path="rascunho",
        url_name="rascunho",
    )
    def rascunho(self, request):
        """
        Endpoint: POST /cronogramas-semanais/rascunho/

        Cria um novo cronograma semanal como rascunho.
        Apenas o campo cronograma_mensal é obrigatório.
        """
        serializer = CronogramaSemanalRascunhoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        instance.salvar_log_cronograma_semanal_criado(usuario=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["get"],
        url_path="rascunhos",
        url_name="rascunhos_listagem",
    )
    def rascunhos_listagem(self, request):
        """
        Endpoint: GET /cronogramas-semanais/rascunhos/

        Lista cronogramas semanais com status RASCUNHO.
        Retorna uuid, numero e alterado_em de cada rascunho.
        """
        from src.dados_comuns.fluxo_status import CronogramaSemanalWorkflow

        queryset = self.get_queryset().filter(status=CronogramaSemanalWorkflow.RASCUNHO)
        serializer = CronogramaSemanalRascunhosSerializer(queryset, many=True)
        return Response({"results": serializer.data})

    @action(
        detail=False,
        methods=["get"],
        url_path="cronogramas-mensal-assinados",
        url_name="cronogramas_mensal_assinados",
    )
    def cronogramas_mensal_assinados(self, request):
        """
        Endpoint: GET /cronogramas-semanais/cronogramas-mensal-assinados/

        Retorna lista de cronogramas mensal do tipo Ponto a Ponto com status ASSINADO_CODAE.
        Usado no seletor de Cronograma Mensal no formulário de cadastro.
        """
        cronogramas = Cronograma.objects.filter(status="ASSINADO_CODAE").select_related(
            "empresa", "contrato", "ficha_tecnica__produto"
        )

        cronogramas_ponto_a_ponto = [c for c in cronogramas if c.ponto_a_ponto]

        serializer = CronogramaMensalAssinadoSerializer(
            cronogramas_ponto_a_ponto, many=True
        )
        return Response(serializer.data)

    def _validar_senha_e_executar_serializador(self, request, uuid):
        """
        Método auxiliar compartilhado entre assinar_e_enviar e alterar_cronograma.
        Valida a senha do usuário, obtém o objeto, executa o serializer e retorna a Response.
        O serializer (e portanto a transição do workflow) é determinado pela action atual.
        """
        usuario = request.user
        password = request.data.get("password")

        if not usuario.verificar_autenticidade(password):
            return Response(
                {"detail": "Assinatura do cronograma não foi validada."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            cronograma_semanal = self.get_object()
            serializer = self.get_serializer(cronograma_semanal, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["patch"],
        url_path="assinar-e-enviar",
        url_name="assinar_e_enviar",
    )
    def assinar_e_enviar(self, request, uuid):
        """
        Endpoint: PATCH /cronogramas-semanais/{uuid}/assinar-e-enviar/

        Assina digitalmente e envia o cronograma semanal para aprovação.
        Valida a senha do usuário e executa a transição inicia_fluxo do workflow
        (RASCUNHO -> ENVIADO_AO_FORNECEDOR).
        """
        return self._validar_senha_e_executar_serializador(request, uuid)

    @action(
        detail=True,
        methods=["patch"],
        url_path="alterar-cronograma",
        url_name="alterar_cronograma",
    )
    def alterar_cronograma(self, request, uuid):
        """
        Endpoint: PATCH /cronogramas-semanais/{uuid}/alterar-cronograma/

        Altera um cronograma semanal após o fornecedor ter dado ciência.
        Valida a senha do usuário e executa a transição alterar_cronograma do workflow
        (FORNECEDOR_CIENTE -> ENVIADO_AO_FORNECEDOR).
        """
        return self._validar_senha_e_executar_serializador(request, uuid)

    @action(
        detail=True,
        methods=["patch"],
        url_path="fornecedor-ciente",
        url_name="fornecedor_ciente",
    )
    def fornecedor_ciente(self, request, uuid):
        """
        Endpoint: PATCH /cronogramas-semanais/{uuid}/fornecedor-ciente/

        Registra a ciência do fornecedor sobre o cronograma semanal.
        Valida a senha do usuário e executa a transição fornecedor_ciente do workflow.
        """
        usuario = request.user

        try:
            cronograma_semanal = self.get_object()
            cronograma_semanal.fornecedor_ciente(user=usuario)
            serializer = self.get_serializer(cronograma_semanal)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["GET"], url_path="gerar-pdf-cronograma")
    def gerar_pdf_cronograma(self, request, uuid=None):
        cronograma = self.get_object()

        return get_pdf_cronograma_semanal(request, cronograma)
