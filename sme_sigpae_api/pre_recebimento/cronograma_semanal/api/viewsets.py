from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoParaCriarCronogramaSemanal,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.serializers.serializers import (
    CronogramaMensalAssinadoSerializer,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import Cronograma
from sme_sigpae_api.pre_recebimento.cronograma_semanal.api.serializer_create import (
    CronogramaSemanalAssinarEEnviarSerializer,
    CronogramaSemanalRascunhoSerializer,
)
from sme_sigpae_api.pre_recebimento.cronograma_semanal.models import CronogramaSemanal


class CronogramaSemanalViewSet(
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para CRUD de Cronograma Semanal FLV.
    Apenas perfis DILOG_CRONOGRAMA e COORDENADOR_CODAE_DILOG_LOGISTICA têm acesso.

    Endpoints disponíveis:
    - POST /cronogramas-semanais/rascunho/ - Cria cronograma semanal como rascunho
    - PATCH /cronogramas-semanais/{uuid}/ - Atualiza cronograma semanal
    - PATCH /cronogramas-semanais/{uuid}/assinar-e-enviar/ - Assina e envia cronograma semanal
    - GET /cronogramas-semanais/cronogramas-mensal-assinados/ - Lista cronogramas mensal Ponto a Ponto assinados
    """

    queryset = CronogramaSemanal.objects.all()
    permission_classes = [PermissaoParaCriarCronogramaSemanal]
    lookup_field = "uuid"

    def get_serializer_class(self):
        if self.action == "rascunho":
            return CronogramaSemanalRascunhoSerializer
        if self.action in ["update", "partial_update"]:
            return CronogramaSemanalRascunhoSerializer
        if self.action == "assinar_e_enviar":
            return CronogramaSemanalAssinarEEnviarSerializer
        return CronogramaSemanalRascunhoSerializer

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
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
        cronogramas = Cronograma.objects.filter(
            status="ASSINADO_CODAE"
        ).select_related("empresa", "contrato", "ficha_tecnica__produto")

        cronogramas_ponto_a_ponto = [
            c for c in cronogramas if c.ponto_a_ponto
        ]

        serializer = CronogramaMensalAssinadoSerializer(
            cronogramas_ponto_a_ponto, many=True
        )
        return Response(serializer.data)

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
        Valida a senha do usuário e executa a transição inicia_fluxo do workflow.
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
            serializer = self.get_serializer(
                cronograma_semanal,
                data=request.data,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Exception as e:
            # Se a transição do workflow falhar (ex: status não é RASCUNHO),
            # retorna erro 400
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
