from django.core.exceptions import ValidationError
from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from src.dados_comuns.constants import StringsValidationErrors

from ...aluno.api.filters import AlunoFilter
from ...api.permissions import PodeEditarFotoAlunoNoSGP, PodeVerFotoAlunoNoSGP
from ...api.serializers import AlunoSerializer, AlunoSimplesSerializer
from ...api.serializers_create import (
    FaixaEtariaSerializer,
    MudancaFaixasEtariasCreateSerializer,
)
from ...models import Aluno, Escola, FaixaEtaria
from ...services import NovoSGPServicoLogado, NovoSGPServicoLogadoException


class AlunoViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    lookup_field = "codigo_eol"
    queryset = Aluno.objects.all()
    serializer_class = AlunoSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = AlunoFilter

    @property
    def pagination_class(self):
        self._pagination_class = super(AlunoViewSet, self).pagination_class
        if self.request.query_params.get("sem_paginacao") == "true":
            self._pagination_class = None
        return self._pagination_class

    def get_serializer_class(self):
        if self.action == "list":
            return AlunoSimplesSerializer
        return self.serializer_class

    def get_queryset(self):
        if self.action == "retrieve":
            return self.queryset.select_related("escola__diretoria_regional")
        return self.queryset

    @action(
        detail=True,
        methods=["GET"],
        url_path="aluno-pertence-a-escola/(?P<escola_codigo_eol>[^/.]+)",
    )
    def aluno_pertence_a_escola(self, request, codigo_eol, escola_codigo_eol):
        escola = Escola.objects.filter(codigo_eol=escola_codigo_eol).first()
        aluno = Aluno.objects.filter(codigo_eol=codigo_eol).first()

        resposta = True if aluno and aluno.escola == escola else False
        return Response({"pertence_a_escola": resposta})

    @action(
        detail=True,
        methods=["GET"],
        url_path="ver-foto",
        permission_classes=(PodeVerFotoAlunoNoSGP,),
    )
    def ver_foto(self, request, codigo_eol):
        try:
            codigo_eol_ = self.get_object().codigo_eol
            novosgpservicologado = NovoSGPServicoLogado()
            response = novosgpservicologado.pegar_foto_aluno(codigo_eol_)
            if response.status_code == status.HTTP_200_OK:
                return Response({"data": response.json()}, status=response.status_code)
            return Response(status=response.status_code)
        except NovoSGPServicoLogadoException as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["POST"],
        url_path="atualizar-foto",
        permission_classes=(PodeEditarFotoAlunoNoSGP,),
    )
    def atualizar_foto(self, request, codigo_eol):
        try:
            codigo_eol_ = self.get_object().codigo_eol
            novosgpservicologado = NovoSGPServicoLogado()
            response = novosgpservicologado.atualizar_foto_aluno(
                codigo_eol_, request.FILES["file"]
            )
            if response.status_code == status.HTTP_200_OK:
                return Response({"data": response.json()}, status=response.status_code)
            return Response(status=response.status_code)
        except NovoSGPServicoLogadoException as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["DELETE"],
        url_path="deletar-foto",
        permission_classes=(PodeEditarFotoAlunoNoSGP,),
    )
    def deletar_foto(self, request, codigo_eol):
        try:
            codigo_eol_ = self.get_object().codigo_eol
            novosgpservicologado = NovoSGPServicoLogado()
            response = novosgpservicologado.deletar_foto_aluno(codigo_eol_)
            if response.status_code == status.HTTP_200_OK:
                return Response({"data": response.json()}, status=response.status_code)
            return Response(status=response.status_code)
        except NovoSGPServicoLogadoException as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=("GET",),
        url_path="quantidade-cemei-por-cei-emei",  # noqa C901
        permission_classes=(IsAuthenticated,),
    )
    def quantidade_cemei_por_cei_emei(self, request):
        try:
            codigo_eol_escola = request.query_params.get("codigo_eol_escola", None)
            manha_e_tarde_sempre = request.query_params.get(
                "manha_e_tarde_sempre", False
            )
            if not codigo_eol_escola:
                raise ValidationError(
                    StringsValidationErrors.CODIGO_EOL_ESCOLA_OBRIGATORIO.value
                )
            escola = Escola.objects.get(codigo_eol=codigo_eol_escola)
            if not escola.eh_cemei:
                raise ValidationError("escola não é CEMEI")
            return Response(
                escola.quantidade_alunos_por_cei_emei(manha_e_tarde_sempre == "true"),
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(e, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=("GET",),
        url_path="quantidade-alunos-por-periodo-cei-emei",  # noqa C901
        permission_classes=(IsAuthenticated,),
    )
    def quantidade_alunos_por_periodo_cei_emei(self, request):
        try:
            codigo_eol_escola = request.query_params.get("codigo_eol_escola", None)
            if not codigo_eol_escola:
                raise ValidationError(
                    StringsValidationErrors.CODIGO_EOL_ESCOLA_OBRIGATORIO.value
                )
            escola = Escola.objects.get(codigo_eol=codigo_eol_escola)
            if not escola.eh_cemei:
                raise ValidationError("escola não é CEMEI")
            return Response(
                escola.quantidade_alunos_por_periodo_cei_emei, status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response(e, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=("GET",),
        url_path="dados-aluno-nao-matriculado-detalhes-dieta",
        permission_classes=(IsAuthenticated,),
    )
    def dados_aluno_nao_matriculado_detalhes_dieta(self, request):
        try:
            codigo_eol_escola = request.query_params.get("codigo_eol_escola", None)
            nome_aluno = request.query_params.get("nome_aluno", False)
            if not codigo_eol_escola:
                raise ValidationError(
                    StringsValidationErrors.CODIGO_EOL_ESCOLA_OBRIGATORIO.value
                )
            if not nome_aluno:
                raise ValidationError("`nome_aluno` como query_param é obrigatório")
            aluno = Aluno.objects.filter(
                nao_matriculado=True,
                dietas_especiais__escola_destino__codigo_eol=codigo_eol_escola,
                nome=nome_aluno,
            ).first()
            return Response(self.get_serializer(aluno).data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(e, status=status.HTTP_400_BAD_REQUEST)


class FaixaEtariaViewSet(CreateModelMixin, ListModelMixin, GenericViewSet):
    """
    Lista faixas etárias ativas.
    """

    queryset = FaixaEtaria.objects.filter(ativo=True)

    def get_serializer_class(self):
        if self.action == "create":
            return MudancaFaixasEtariasCreateSerializer
        return FaixaEtariaSerializer
