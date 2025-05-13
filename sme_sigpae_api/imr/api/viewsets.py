from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from sme_sigpae_api.dados_comuns.api.paginations import DefaultPagination
from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoObjetoFormularioSupervisao,
    PermissaoParaVisualizarRelatorioFiscalizacaoNutri,
    UsuarioCODAENutriSupervisao,
    UsuarioEscolaTercTotal,
)
from sme_sigpae_api.terceirizada.models import Edital

from ...dados_comuns.constants import COORDENADOR_SUPERVISAO_NUTRICAO
from ...dados_comuns.fluxo_status import FormularioSupervisaoWorkflow
from ...escola.models import Escola
from ..models import (
    Equipamento,
    FormularioSupervisao,
    Insumo,
    Mobiliario,
    PeriodoVisita,
    ReparoEAdaptacao,
    TipoOcorrencia,
    UtensilioCozinha,
    UtensilioMesa,
)
from ..tasks import (
    gera_pdf_relatorio_formulario_supervisao_async,
    gerar_relatorio_notificacao_pdf_async,
)
from .filters import FormularioSupervisaoFilter
from .serializers.serializers import (
    EquipamentoSerializer,
    FormularioSupervisaoRetrieveSerializer,
    FormularioSupervisaoSerializer,
    FormularioSupervisaoSimplesSerializer,
    InsumoSerializer,
    MobiliarioSerializer,
    OcorrenciaNaoSeAplicaSerializer,
    PeriodoVisitaSerializer,
    ReparoEAdaptacaoSerializer,
    TipoOcorrenciaSerializer,
    TipoPerguntaParametrizacaoOcorrencia,
    UtensilioCozinhaSerializer,
    UtensilioMesaSerializer,
)
from .serializers.serializers_create import (
    FormularioDiretorManyCreateSerializer,
    FormularioSupervisaoCreateSerializer,
    FormularioSupervisaoRascunhoCreateSerializer,
)


class PeriodoVisitaModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    lookup_field = "uuid"
    queryset = PeriodoVisita.objects.all().order_by("-criado_em")
    permission_classes = (UsuarioCODAENutriSupervisao,)
    serializer_class = PeriodoVisitaSerializer
    pagination_class = DefaultPagination


class FormularioSupervisaoRascunhoModelViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
    mixins.DestroyModelMixin,
):
    lookup_field = "uuid"
    queryset = FormularioSupervisao.objects.all().order_by("-criado_em")
    permission_classes = (
        UsuarioCODAENutriSupervisao,
        PermissaoObjetoFormularioSupervisao,
    )
    serializer_class = FormularioSupervisaoRascunhoCreateSerializer
    pagination_class = DefaultPagination

    def update(self, request, *args, **kwargs):
        formulario_nutrisupervisao = self.get_object()
        if formulario_nutrisupervisao.em_preenchimento:
            return super(FormularioSupervisaoRascunhoModelViewSet, self).update(
                request, *args, **kwargs
            )
        else:
            return Response(
                {"detail": "Rascunho já foi enviado e não pode mais ser alterado."},
                status=status.HTTP_403_FORBIDDEN,
            )

    def destroy(self, request, *args, **kwargs):
        formulario_nutrisupervisao = self.get_object()
        if formulario_nutrisupervisao.em_preenchimento:
            return super().destroy(request, *args, **kwargs)
        else:
            return Response(
                dict(
                    detail="Você só pode excluir quando o status for EM PREENCHIMENTO."
                ),
                status=status.HTTP_403_FORBIDDEN,
            )


class FormularioSupervisaoModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
):
    lookup_field = "uuid"
    queryset = FormularioSupervisao.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaVisualizarRelatorioFiscalizacaoNutri,)
    serializer_class = FormularioSupervisaoSerializer
    pagination_class = DefaultPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = FormularioSupervisaoFilter
    permission_action_classes = {
        "create": [UsuarioCODAENutriSupervisao],
        "update": [UsuarioCODAENutriSupervisao],
        "delete": [UsuarioCODAENutriSupervisao],
    }

    def get_queryset(self):
        user = self.request.user
        if user.vinculo_atual.perfil.nome == COORDENADOR_SUPERVISAO_NUTRICAO:
            return FormularioSupervisao.objects.filter(
                formulario_base__usuario=user
            ).order_by("-criado_em")
        return FormularioSupervisao.objects.all().order_by("-criado_em")

    def get_serializer_class(self):
        return {
            "list": FormularioSupervisaoSimplesSerializer,
            "retrieve": FormularioSupervisaoRetrieveSerializer,
        }.get(self.action, FormularioSupervisaoCreateSerializer)

    def _get_categorias_nao_permitidas(self, tipo_escola):
        categorias_excluir = []

        if tipo_escola not in [
            "CEI",
            "CEI DIRET",
            "CEI CEU",
            "CEU CEI",
            "CCI/CIPS",
            "CCI",
            "CEMEI",
            "CEU CEMEI",
        ]:
            categorias_excluir.append("LACTÁRIO")
        if tipo_escola in ["CEI", "CEI DIRET", "CEI CEU", "CEU CEI", "CCI/CIPS", "CCI"]:
            categorias_excluir.append("RESÍDUO DE ÓLEO UTILIZADO NA FRITURA")

        return categorias_excluir

    @action(
        detail=False,
        url_path="tipos-ocorrencias",
    )
    def tipos_ocorrencias(self, request):
        edital_uuid = request.query_params.get("edital_uuid")
        escola_uuid = request.query_params.get("escola_uuid")

        try:
            edital = Edital.objects.get(uuid=edital_uuid)
            tipo_unidade = Escola.objects.get(uuid=escola_uuid).tipo_unidade.iniciais
        except Edital.DoesNotExist:
            return Response(
                {
                    "detail": "Edital do tipo IMR com o UUID informado não foi encontrado."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Escola.DoesNotExist:
            return Response(
                {"detail": "Escola com o UUID informado não foi encontrada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValidationError as error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

        queryset = TipoOcorrencia.para_nutrisupervisores.filter(edital=edital).exclude(
            categoria__nome__in=self._get_categorias_nao_permitidas(tipo_unidade)
        )

        serializer = TipoOcorrenciaSerializer(queryset, many=True)

        return Response(serializer.data)

    def get_lista_status(self) -> list[str]:
        lista_status = [
            state.name for state in list(FormularioSupervisaoWorkflow.states)
        ]
        lista_status += ["TODOS_OS_RELATORIOS"]
        return lista_status

    def get_label(self, workflow: str) -> str:
        try:
            return (
                "Aprovados"
                if workflow == FormularioSupervisaoWorkflow.APROVADO
                else FormularioSupervisaoWorkflow.states[workflow].title
            )
        except KeyError:
            return "Todos os Relatórios"

    def dados_dashboard(self, query_set: QuerySet) -> list:
        sumario = []

        for workflow in self.get_lista_status():
            todos_lancamentos = workflow == "TODOS_OS_RELATORIOS"
            qs = (
                query_set.filter(status=workflow)
                if not todos_lancamentos
                else query_set
            )
            sumario.append(
                {
                    "status": workflow,
                    "label": self.get_label(workflow),
                    "total": len(qs),
                }
            )
        return sumario

    @action(
        detail=False,
        methods=["GET"],
        url_path="dashboard",
    )
    def dashboard(self, request):
        query_set = self.get_queryset()
        response = {
            "results": self.dados_dashboard(
                query_set=query_set,
            )
        }
        return Response(response)

    @action(
        detail=True,
        url_path="respostas",
    )
    def respostas(self, request, uuid):
        formulario = self.get_object()

        respostas = []
        tipos_perguntas = TipoPerguntaParametrizacaoOcorrencia.objects.all()

        for tipo_pergunta in tipos_perguntas:
            modelo_reposta = tipo_pergunta.get_model_tipo_resposta()
            _respostas = modelo_reposta.objects.filter(
                formulario_base=formulario.formulario_base,
            )

            for _resposta in _respostas:
                resposta_serializer_name = f"{modelo_reposta.__name__}Serializer"
                get_resposta_serializer = (
                    FormularioSupervisaoRetrieveSerializer.get_serializer_class_by_name(
                        resposta_serializer_name
                    )
                )

                respostas.append(get_resposta_serializer(_resposta).data)

        return Response(respostas)

    @action(
        detail=True,
        url_path="respostas_nao_se_aplica",
    )
    def respostas_nao_se_aplica(self, request, uuid):
        formulario = self.get_object()

        serializer = OcorrenciaNaoSeAplicaSerializer(
            formulario.formulario_base.respostas_nao_se_aplica.all(), many=True
        )
        return Response(serializer.data)

    @action(detail=True, methods=["GET"], url_path="relatorio-pdf")
    def relatorio_pdf(self, request, uuid):
        try:
            user = request.user.get_username()
            formulario_supervisao = get_object_or_404(FormularioSupervisao, uuid=uuid)
            gera_pdf_relatorio_formulario_supervisao_async.delay(
                user=user,
                nome_arquivo=f"Relatório de Fiscalização - {formulario_supervisao.escola.nome}.pdf",
                uuid=uuid,
            )
            return Response(
                dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
                status=status.HTTP_200_OK,
            )
        except Http404:
            return Response(
                {
                    "detail": "FormularioSupervisao com o UUID informado não foi encontrado."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(
        detail=False,
        url_path="lista_nomes_nutricionistas",
    )
    def lista_nomes_nutricionistas(self, request):
        queryset = (
            FormularioSupervisao.objects.all()
            .values_list("formulario_base__usuario__nome", flat=True)
            .distinct()
        )
        response = {"results": queryset}
        return Response(response)

    @action(
        detail=True,
        url_path="gerar-relatorio-notificacoes",
    )
    def gerar_relatorio_notificacao(self, request, uuid):
        user = request.user.get_username()
        instance = self.get_object()

        gerar_relatorio_notificacao_pdf_async.delay(
            user=user,
            nome_arquivo=f"Relatório de Notificação - {instance.escola.nome}.pdf",
            formulario_supervisao_uuid=instance.uuid,
        )

        return Response(
            dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
            status=status.HTTP_200_OK,
        )


class FormularioDiretorModelViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    lookup_field = "uuid"
    queryset = FormularioSupervisao.objects.all().order_by("-criado_em")
    permission_classes = (UsuarioEscolaTercTotal,)
    serializer_class = FormularioSupervisaoSerializer
    pagination_class = DefaultPagination

    def get_serializer_class(self):
        return {
            "list": FormularioSupervisaoSerializer,
            "retrieve": FormularioSupervisaoSerializer,
        }.get(self.action, FormularioDiretorManyCreateSerializer)

    @action(
        detail=False,
        url_path="tipos-ocorrencias",
    )
    def tipos_ocorrencias(self, request):
        edital_uuid = request.query_params.get("edital_uuid")

        try:
            edital = Edital.objects.get(uuid=edital_uuid)
        except Edital.DoesNotExist:
            return Response(
                {
                    "detail": "Edital do tipo IMR com o UUID informado não foi encontrado."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValidationError as error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

        queryset = TipoOcorrencia.para_diretores.filter(edital=edital)

        serializer = TipoOcorrenciaSerializer(queryset, many=True)

        return Response(serializer.data)


class UtensilioCozinhaViewSet(viewsets.ModelViewSet):
    queryset = UtensilioCozinha.objects.all()
    serializer_class = UtensilioCozinhaSerializer
    http_method_names = ["get"]
    lookup_field = "uuid"

    def list(self, request, *args, **kwargs):
        self.queryset = UtensilioCozinha.ativos.all()

        edital_uuid = request.query_params.get("edital_uuid")

        if edital_uuid:
            self.queryset = self.queryset.filter(
                editalutensiliocozinha__edital__uuid=edital_uuid
            ).distinct("nome")

        serializer = self.get_serializer(self.queryset, many=True)
        return Response({"results": serializer.data})


class UtensilioMesaViewSet(viewsets.ModelViewSet):
    queryset = UtensilioMesa.objects.all()
    serializer_class = UtensilioMesaSerializer
    http_method_names = ["get"]
    lookup_field = "uuid"

    def list(self, request, *args, **kwargs):
        self.queryset = UtensilioMesa.ativos.all()

        edital_uuid = request.query_params.get("edital_uuid")

        if edital_uuid:
            self.queryset = self.queryset.filter(
                editalutensiliomesa__edital__uuid=edital_uuid
            ).distinct("nome")

        serializer = self.get_serializer(self.queryset, many=True)
        return Response({"results": serializer.data})


class EquipamentoViewSet(viewsets.ModelViewSet):
    queryset = Equipamento.objects.all()
    serializer_class = EquipamentoSerializer
    http_method_names = ["get"]
    lookup_field = "uuid"

    def list(self, request, *args, **kwargs):
        self.queryset = Equipamento.ativos.all()

        edital_uuid = request.query_params.get("edital_uuid")

        if edital_uuid:
            self.queryset = self.queryset.filter(
                editalequipamento__edital__uuid=edital_uuid
            ).distinct("nome")

        serializer = self.get_serializer(self.queryset, many=True)
        return Response({"results": serializer.data})


class MobiliarioViewSet(viewsets.ModelViewSet):
    queryset = Mobiliario.objects.all()
    serializer_class = MobiliarioSerializer
    http_method_names = ["get"]
    lookup_field = "uuid"

    def list(self, request, *args, **kwargs):
        self.queryset = Mobiliario.ativos.all()

        edital_uuid = request.query_params.get("edital_uuid")

        if edital_uuid:
            self.queryset = self.queryset.filter(
                editalmobiliario__edital__uuid=edital_uuid
            ).distinct("nome")

        serializer = self.get_serializer(self.queryset, many=True)
        return Response({"results": serializer.data})


class ReparoEAdaptacaoViewSet(viewsets.ModelViewSet):
    queryset = ReparoEAdaptacao.objects.all()
    serializer_class = ReparoEAdaptacaoSerializer
    http_method_names = ["get"]
    lookup_field = "uuid"

    def list(self, request, *args, **kwargs):
        self.queryset = ReparoEAdaptacao.ativos.all()

        edital_uuid = request.query_params.get("edital_uuid")

        if edital_uuid:
            self.queryset = self.queryset.filter(
                editalreparoeadaptacao__edital__uuid=edital_uuid
            ).distinct("nome")

        serializer = self.get_serializer(self.queryset, many=True)
        return Response({"results": serializer.data})


class InsumoViewSet(viewsets.ModelViewSet):
    queryset = Insumo.objects.all()
    serializer_class = InsumoSerializer
    http_method_names = ["get"]
    lookup_field = "uuid"

    def list(self, request, *args, **kwargs):
        self.queryset = Insumo.ativos.all()

        edital_uuid = request.query_params.get("edital_uuid")

        if edital_uuid:
            self.queryset = self.queryset.filter(
                editalinsumo__edital__uuid=edital_uuid
            ).distinct("nome")

        serializer = self.get_serializer(self.queryset, many=True)
        return Response({"results": serializer.data})
