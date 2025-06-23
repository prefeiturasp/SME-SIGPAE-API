from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpResponse
from django_filters import rest_framework as filters
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_406_NOT_ACCEPTABLE,
)
from xworkflows.base import InvalidTransitionError

from sme_sigpae_api.dados_comuns.constants import ADMINISTRADOR_EMPRESA
from sme_sigpae_api.dados_comuns.fluxo_status import (
    CronogramaWorkflow,
    DocumentoDeRecebimentoWorkflow,
)
from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoParaAnalisarDilogAbastecimentoSolicitacaoAlteracaoCronograma,
    PermissaoParaAnalisarDilogSolicitacaoAlteracaoCronograma,
    PermissaoParaAnalisarFichaTecnica,
    PermissaoParaAssinarCronogramaUsuarioDilog,
    PermissaoParaAssinarCronogramaUsuarioFornecedor,
    PermissaoParaCadastrarLaboratorio,
    PermissaoParaCadastrarVisualizarEmbalagem,
    PermissaoParaCadastrarVisualizarUnidadesMedida,
    PermissaoParaCriarCronograma,
    PermissaoParaCriarSolicitacoesAlteracaoCronograma,
    PermissaoParaDarCienciaAlteracaoCronograma,
    PermissaoParaDashboardCronograma,
    PermissaoParaDashboardDocumentosDeRecebimento,
    PermissaoParaDashboardFichaTecnica,
    PermissaoParaDashboardLayoutEmbalagem,
    PermissaoParaListarDashboardSolicitacaoAlteracaoCronograma,
    PermissaoParaVisualizarCalendarioCronograma,
    PermissaoParaVisualizarCronograma,
    PermissaoParaVisualizarDocumentosDeRecebimento,
    PermissaoParaVisualizarFichaTecnica,
    PermissaoParaVisualizarLayoutDeEmbalagem,
    PermissaoParaVisualizarRelatorioCronograma,
    PermissaoParaVisualizarSolicitacoesAlteracaoCronograma,
    PermissaoParaVisualizarUnidadesMedida,
    UsuarioDilogAbastecimento,
    UsuarioEhDilogQualidade,
    UsuarioEhFornecedor,
    ViewSetActionPermissionMixin,
)
from sme_sigpae_api.pre_recebimento.api.filters import (
    CronogramaFilter,
    DocumentoDeRecebimentoFilter,
    FichaTecnicaFilter,
    LaboratorioFilter,
    LayoutDeEmbalagemFilter,
    SolicitacaoAlteracaoCronogramaFilter,
    TipoEmbalagemQldFilter,
    UnidadeMedidaFilter,
)
from sme_sigpae_api.pre_recebimento.api.helpers import totalizador_relatorio_cronograma
from sme_sigpae_api.pre_recebimento.api.paginations import (
    CronogramaPagination,
    LaboratorioPagination,
    TipoEmbalagemQldPagination,
)
from sme_sigpae_api.pre_recebimento.api.serializers.serializer_create import (
    AnaliseFichaTecnicaCreateSerializer,
    AnaliseFichaTecnicaRascunhoSerializer,
    CorrecaoFichaTecnicaSerializer,
    CronogramaCreateSerializer,
    DocumentoDeRecebimentoAnalisarRascunhoSerializer,
    DocumentoDeRecebimentoAnalisarSerializer,
    DocumentoDeRecebimentoAtualizacaoSerializer,
    DocumentoDeRecebimentoCorrecaoSerializer,
    DocumentoDeRecebimentoCreateSerializer,
    FichaTecnicaAtualizacaoSerializer,
    FichaTecnicaCreateSerializer,
    FichaTecnicaRascunhoSerializer,
    LaboratorioCreateSerializer,
    LayoutDeEmbalagemAnaliseSerializer,
    LayoutDeEmbalagemCorrecaoSerializer,
    LayoutDeEmbalagemCreateSerializer,
    SolicitacaoDeAlteracaoCronogramaCreateSerializer,
    TipoEmbalagemQldCreateSerializer,
    UnidadeMedidaCreateSerializer,
)
from sme_sigpae_api.pre_recebimento.api.serializers.serializers import (
    CronogramaComLogSerializer,
    CronogramaFichaDeRecebimentoSerializer,
    CronogramaRascunhosSerializer,
    CronogramaRelatorioSerializer,
    CronogramaSerializer,
    CronogramaSimplesSerializer,
    DocRecebimentoDetalharCodaeSerializer,
    DocRecebimentoDetalharSerializer,
    DocumentoDeRecebimentoSerializer,
    EtapasDoCronogramaCalendarioSerializer,
    FichaTecnicaComAnaliseDetalharSerializer,
    FichaTecnicaCronogramaSerializer,
    FichaTecnicaDetalharSerializer,
    FichaTecnicaListagemSerializer,
    FichaTecnicaSimplesSerializer,
    LaboratorioCredenciadoSimplesSerializer,
    LaboratorioSerializer,
    LaboratorioSimplesFiltroSerializer,
    LayoutDeEmbalagemDetalheSerializer,
    LayoutDeEmbalagemSerializer,
    PainelCronogramaSerializer,
    PainelDocumentoDeRecebimentoSerializer,
    PainelFichaTecnicaSerializer,
    PainelLayoutEmbalagemSerializer,
    PainelSolicitacaoAlteracaoCronogramaSerializer,
    SolicitacaoAlteracaoCronogramaCompletoSerializer,
    SolicitacaoAlteracaoCronogramaSerializer,
    TipoEmbalagemQldSerializer,
    UnidadeMedidaSerialzer,
    UnidadeMedidaSimplesSerializer,
)
from sme_sigpae_api.pre_recebimento.api.services import (
    ServiceDashboardDocumentosDeRecebimento,
    ServiceDashboardFichaTecnica,
    ServiceDashboardLayoutEmbalagem,
    ServiceDashboardSolicitacaoAlteracaoCronogramaProfiles,
    ServiceQuerysetAlteracaoCronograma,
)
from sme_sigpae_api.pre_recebimento.models import (
    Cronograma,
    DocumentoDeRecebimento,
    EtapasDoCronograma,
    Laboratorio,
    LayoutDeEmbalagem,
    SolicitacaoAlteracaoCronograma,
    TipoEmbalagemQld,
    UnidadeMedida,
)
from sme_sigpae_api.pre_recebimento.tasks import (
    gerar_relatorio_cronogramas_pdf_async,
    gerar_relatorio_cronogramas_xlsx_async,
)

from ...dados_comuns.api.paginations import DefaultPagination
from ...dados_comuns.models import LogSolicitacoesUsuario
from ...relatorios.relatorios import get_pdf_cronograma, get_pdf_ficha_tecnica
from ..models.cronograma import FichaTecnicaDoProduto
from .validators import valida_parametros_calendario


class CronogramaModelViewSet(ViewSetActionPermissionMixin, viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = Cronograma.objects.all()
    serializer_class = CronogramaSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CronogramaFilter
    pagination_class = CronogramaPagination
    permission_classes = (PermissaoParaVisualizarCronograma,)
    permission_action_classes = {
        "create": [PermissaoParaCriarCronograma],
        "delete": [PermissaoParaCriarCronograma],
    }

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return CronogramaSerializer
        else:
            return CronogramaCreateSerializer

    def get_queryset(self):
        return Cronograma.objects.all().order_by("-criado_em")

    def get_lista_status(self):
        lista_status = [
            Cronograma.workflow_class.ASSINADO_E_ENVIADO_AO_FORNECEDOR,
            Cronograma.workflow_class.ASSINADO_FORNECEDOR,
            Cronograma.workflow_class.ASSINADO_DILOG_ABASTECIMENTO,
            Cronograma.workflow_class.ASSINADO_CODAE,
        ]

        return lista_status

    def get_default_sql(self, workflow, query_set, use_raw):
        workflow = workflow if isinstance(workflow, list) else [workflow]
        if use_raw:
            data = {
                "logs": LogSolicitacoesUsuario._meta.db_table,
                "cronograma": Cronograma._meta.db_table,
                "status": workflow,
            }
            raw_sql = (
                "SELECT %(cronograma)s.* FROM %(cronograma)s "
                "JOIN (SELECT uuid_original, MAX(criado_em) AS log_criado_em FROM %(logs)s "
                "GROUP BY uuid_original) "
                "AS most_recent_log "
                "ON %(cronograma)s.uuid = most_recent_log.uuid_original "
                "WHERE %(cronograma)s.status = '%(status)s' "
            )
            raw_sql += "ORDER BY log_criado_em DESC"

            return query_set.raw(raw_sql % data)
        else:
            qs = sorted(
                query_set.filter(status__in=workflow).distinct().all(),
                key=lambda x: (
                    x.log_mais_recente.criado_em if x.log_mais_recente else "-criado_em"
                ),
                reverse=True,
            )
            return qs

    def dados_dashboard(self, request, query_set: QuerySet, use_raw) -> list:
        limit = int(request.query_params.get("limit", 10))
        offset = int(request.query_params.get("offset", 0))
        status = request.query_params.getlist("status", None)
        sumario = []
        if status:
            qs = self.get_default_sql(
                workflow=status, query_set=query_set, use_raw=use_raw
            )
            sumario.append(
                {
                    "status": status,
                    "total": len(qs),
                    "dados": PainelCronogramaSerializer(
                        qs[offset : limit + offset],
                        context={"request": self.request, "workflow": status},
                        many=True,
                    ).data,
                }
            )
        else:
            for workflow in self.get_lista_status():
                qs = self.get_default_sql(
                    workflow=workflow, query_set=query_set, use_raw=use_raw
                )
                sumario.append(
                    {
                        "status": workflow,
                        "dados": PainelCronogramaSerializer(
                            qs[:6],
                            context={"request": self.request, "workflow": workflow},
                            many=True,
                        ).data,
                    }
                )

        return sumario

    @action(
        detail=False,
        methods=["GET"],
        url_path="dashboard",
        permission_classes=(PermissaoParaDashboardCronograma,),
    )
    def dashboard(self, request):
        query_set = self.get_queryset()
        response = {
            "results": self.dados_dashboard(
                query_set=query_set, request=request, use_raw=False
            )
        }
        return Response(response)

    @action(
        detail=False,
        methods=["GET"],
        url_path="dashboard-com-filtro",
        permission_classes=(PermissaoParaDashboardCronograma,),
    )
    def dashboard_com_filtro(self, request):
        query_set = self.get_queryset()
        numero_cronograma = request.query_params.get("numero_cronograma", None)
        produto = request.query_params.get("nome_produto", None)
        fornecedor = request.query_params.get("nome_fornecedor", None)

        if numero_cronograma:
            query_set = query_set.filter(numero__icontains=numero_cronograma)
        if produto:
            query_set = query_set.filter(
                ficha_tecnica__produto__nome__icontains=produto
            )
        if fornecedor:
            query_set = query_set.filter(empresa__razao_social__icontains=fornecedor)

        response = {
            "results": self.dados_dashboard(
                query_set=query_set, request=request, use_raw=False
            )
        }
        return Response(response)

    def list(self, request, *args, **kwargs):
        vinculo = self.request.user.vinculo_atual
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.order_by("-alterado_em").distinct()

        if (
            vinculo.perfil.nome == ADMINISTRADOR_EMPRESA
            and vinculo.instituicao.eh_fornecedor
        ):
            queryset = queryset.filter(empresa=vinculo.instituicao)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        permission_classes=(PermissaoParaVisualizarRelatorioCronograma,),
        methods=["GET"],
        url_path="listagem-relatorio",
    )
    def lista_relatorio(self, request, *args, **kwargs):
        queryset = (
            self.filter_queryset(self.get_queryset())
            .order_by("-alterado_em")
            .distinct()
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CronogramaRelatorioSerializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data["totalizadores"] = totalizador_relatorio_cronograma(queryset)
            return response

        serializer = CronogramaRelatorioSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, url_path="opcoes-etapas")
    def etapas(self, _):
        return Response(EtapasDoCronograma.etapas_to_json())

    @action(detail=False, methods=["GET"], url_path="rascunhos")
    def rascunhos(self, _):
        queryset = self.get_queryset().filter(status__in=[CronogramaWorkflow.RASCUNHO])
        response = {"results": CronogramaRascunhosSerializer(queryset, many=True).data}
        return Response(response)

    @transaction.atomic
    @action(
        detail=True,
        permission_classes=(PermissaoParaAssinarCronogramaUsuarioFornecedor,),
        methods=["patch"],
        url_path="fornecedor-assina-cronograma",
    )
    def fornecedor_assina(self, request, uuid=None):
        usuario = request.user

        if not usuario.verificar_autenticidade(request.data.get("password")):
            return Response(
                dict(
                    detail="Assinatura do cronograma não foi validada. Verifique sua senha."
                ),
                status=HTTP_401_UNAUTHORIZED,
            )

        try:
            cronograma = Cronograma.objects.get(uuid=uuid)
            cronograma.fornecedor_assina(
                user=usuario,
            )
            serializer = CronogramaSerializer(cronograma)
            return Response(serializer.data)

        except ObjectDoesNotExist as e:
            return Response(
                dict(detail=f"Cronograma informado não é valido: {e}"),
                status=HTTP_406_NOT_ACCEPTABLE,
            )
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )

    @transaction.atomic
    @action(
        detail=True,
        permission_classes=(UsuarioDilogAbastecimento,),
        methods=["patch"],
        url_path="abastecimento-assina",
    )
    def abastecimento_assina(self, request, uuid):
        usuario = request.user

        if not usuario.verificar_autenticidade(request.data.get("password")):
            return Response(
                dict(
                    detail="Assinatura do cronograma não foi validada. Verifique sua senha."
                ),
                status=HTTP_401_UNAUTHORIZED,
            )

        try:
            cronograma = Cronograma.objects.get(uuid=uuid)
            cronograma.dilog_abastecimento_assina(user=usuario)
            serializer = CronogramaSerializer(cronograma)
            return Response(serializer.data)

        except ObjectDoesNotExist as e:
            return Response(
                dict(detail=f"Cronograma informado não é valido: {e}"),
                status=HTTP_406_NOT_ACCEPTABLE,
            )
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )

    @transaction.atomic
    @action(
        detail=True,
        permission_classes=(PermissaoParaAssinarCronogramaUsuarioDilog,),
        methods=["patch"],
        url_path="codae-assina",
    )
    def codae_assina(self, request, uuid):
        usuario = request.user

        if not usuario.verificar_autenticidade(request.data.get("password")):
            return Response(
                dict(
                    detail="Assinatura do cronograma não foi validada. Verifique sua senha."
                ),
                status=HTTP_401_UNAUTHORIZED,
            )

        try:
            cronograma = Cronograma.objects.get(uuid=uuid)
            cronograma.codae_assina(user=usuario)
            serializer = CronogramaSerializer(cronograma)
            return Response(serializer.data)

        except ObjectDoesNotExist as e:
            return Response(
                dict(detail=f"Cronograma informado não é valido: {e}"),
                status=HTTP_406_NOT_ACCEPTABLE,
            )
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["GET"], url_path="gerar-pdf-cronograma")
    def gerar_pdf_cronograma(self, request, uuid=None):
        cronograma = self.get_object()

        return get_pdf_cronograma(request, cronograma)

    @action(detail=True, methods=["GET"], url_path="detalhar-com-log")
    def detalhar_com_log(self, request, uuid=None):
        cronograma = self.get_object()
        response = CronogramaComLogSerializer(cronograma, many=False).data
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-cronogramas-cadastro")
    def lista_cronogramas_para_cadastro(self, request):
        user = self.request.user
        if user.eh_fornecedor:
            cronogramas = Cronograma.objects.filter(
                empresa=user.vinculo_atual.instituicao
            ).order_by("-criado_em")
        else:
            cronogramas = self.get_queryset()

        serializer = CronogramaSimplesSerializer(cronogramas, many=True).data
        response = {"results": serializer}
        return Response(response)

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-cronogramas-ficha-recebimento",
    )
    def lista_cronogramas_ficha_recebimento(self, request):
        qs = self.get_queryset().filter(status=CronogramaWorkflow.ASSINADO_CODAE)

        return Response({"results": CronogramaSimplesSerializer(qs, many=True).data})

    @action(
        detail=True,
        methods=["GET"],
        url_path="dados-cronograma-ficha-recebimento",
    )
    def dados_cronograma_ficha_recebimento(self, request, uuid):
        return Response(
            {"results": CronogramaFichaDeRecebimentoSerializer(self.get_object()).data}
        )

    @action(
        detail=False,
        permission_classes=(PermissaoParaVisualizarRelatorioCronograma,),
        methods=["GET"],
        url_path="gerar-relatorio-xlsx-async",
    )
    def gerar_relatorio_xlsx_async(self, request):
        ids_cronogramas = list(
            (
                self.filter_queryset(self.get_queryset())
                .order_by("-alterado_em")
                .distinct()
            ).values_list("id", flat=True)
        )

        gerar_relatorio_cronogramas_xlsx_async.delay(
            request.user.username,
            ids_cronogramas,
        )

        return Response(
            {"detail": "Solicitação de geração de arquivo recebida com sucesso."},
            status=HTTP_200_OK,
        )

    @action(
        detail=False,
        permission_classes=(PermissaoParaVisualizarRelatorioCronograma,),
        methods=["GET"],
        url_path="gerar-relatorio-pdf-async",
    )
    def gerar_relatorio_pdf_async(self, request):
        ids_cronogramas = list(
            (
                self.filter_queryset(self.get_queryset())
                .order_by("-alterado_em")
                .distinct()
            ).values_list("id", flat=True)
        )

        gerar_relatorio_cronogramas_pdf_async.delay(
            request.user.username,
            ids_cronogramas,
        )

        return Response(
            {"detail": "Solicitação de geração de arquivo recebida com sucesso."},
            status=HTTP_200_OK,
        )


class LaboratorioModelViewSet(ViewSetActionPermissionMixin, viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = Laboratorio.objects.all().order_by("-criado_em")
    serializer_class = LaboratorioSerializer
    pagination_class = LaboratorioPagination
    filterset_class = LaboratorioFilter
    filter_backends = (filters.DjangoFilterBackend,)
    permission_classes = (PermissaoParaCadastrarLaboratorio,)
    permission_action_classes = {
        "create": [PermissaoParaCadastrarLaboratorio],
        "delete": [PermissaoParaCadastrarLaboratorio],
    }

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return LaboratorioSerializer
        else:
            return LaboratorioCreateSerializer

    @action(detail=False, methods=["GET"], url_path="lista-nomes-laboratorios")
    def lista_nomes_laboratorios(self, request):
        queryset = Laboratorio.objects.all()
        response = {"results": [q.nome for q in queryset]}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-laboratorios-credenciados")
    def lista_nomes_laboratorios_credenciados(self, request):
        laboratorios = self.get_queryset().filter(credenciado=True)
        serializer = LaboratorioCredenciadoSimplesSerializer(
            laboratorios, many=True
        ).data
        response = {"results": serializer}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-laboratorios")
    def lista_laboratorios_para_filtros(self, request):
        laboratorios = self.get_queryset()
        serializer = LaboratorioSimplesFiltroSerializer(laboratorios, many=True).data
        response = {"results": serializer}
        return Response(response)


class TipoEmbalagemQldModelViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = TipoEmbalagemQld.objects.all().order_by("-criado_em")
    serializer_class = TipoEmbalagemQldSerializer
    permission_classes = (PermissaoParaCadastrarVisualizarEmbalagem,)
    pagination_class = TipoEmbalagemQldPagination
    filterset_class = TipoEmbalagemQldFilter
    filter_backends = (filters.DjangoFilterBackend,)

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return TipoEmbalagemQldSerializer
        else:
            return TipoEmbalagemQldCreateSerializer

    @action(detail=False, methods=["GET"], url_path="lista-nomes-tipos-embalagens")
    def lista_nomes_tipos_embalagens(self, request):
        queryset = TipoEmbalagemQld.objects.all().values_list("nome", flat=True)
        response = {"results": queryset}
        return Response(response)

    @action(
        detail=False, methods=["GET"], url_path="lista-abreviacoes-tipos-embalagens"
    )
    def lista_abreviacoes_tipos_embalagens(self, request):
        queryset = TipoEmbalagemQld.objects.all().values_list("abreviacao", flat=True)
        response = {"results": queryset}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-tipos-embalagens")
    def lista_tipo_embalagem_completa(self, request):
        queryset = self.get_queryset()
        serializer = TipoEmbalagemQldSerializer(queryset, many=True).data
        response = {"results": serializer}
        return Response(response)


class SolicitacaoDeAlteracaoCronogramaViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    filter_backends = (filters.DjangoFilterBackend,)
    pagination_class = CronogramaPagination
    permission_classes = (IsAuthenticated,)
    filterset_class = SolicitacaoAlteracaoCronogramaFilter

    def get_queryset(self):
        user = self.request.user
        if user.eh_fornecedor:
            return SolicitacaoAlteracaoCronograma.objects.filter(
                cronograma__empresa=user.vinculo_atual.instituicao
            ).order_by("-criado_em")
        return SolicitacaoAlteracaoCronograma.objects.all().order_by("-criado_em")

    def get_serializer_class(self):
        serializer_classes_map = {
            "list": SolicitacaoAlteracaoCronogramaSerializer,
            "retrieve": SolicitacaoAlteracaoCronogramaCompletoSerializer,
        }
        return serializer_classes_map.get(
            self.action, SolicitacaoDeAlteracaoCronogramaCreateSerializer
        )

    def get_permissions(self):
        permission_classes_map = {
            "list": (PermissaoParaVisualizarSolicitacoesAlteracaoCronograma,),
            "retrieve": (PermissaoParaVisualizarSolicitacoesAlteracaoCronograma,),
            "create": (PermissaoParaCriarSolicitacoesAlteracaoCronograma,),
        }
        action_permissions = permission_classes_map.get(self.action, [])
        self.permission_classes = (*self.permission_classes, *action_permissions)
        return super(SolicitacaoDeAlteracaoCronogramaViewSet, self).get_permissions()

    def list(self, request, *args, **kwargs):
        queryset = ServiceQuerysetAlteracaoCronograma(
            request=self.request
        ).get_queryset(filter=self.filter_queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SolicitacaoAlteracaoCronogramaSerializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return response

        serializer = SolicitacaoAlteracaoCronogramaSerializer(queryset, many=True)
        return Response(serializer.data)

    def _dados_dashboard(self, request, filtros=None):
        limit = (
            int(request.query_params.get("limit", 10))
            if "limit" in request.query_params
            else 6
        )
        offset = (
            int(request.query_params.get("offset", 0))
            if "offset" in request.query_params
            else 0
        )
        status = request.query_params.getlist("status", None)
        dados_dashboard = []
        lista_status = (
            [status]
            if status
            else ServiceDashboardSolicitacaoAlteracaoCronogramaProfiles.get_dashboard_status(
                self.request.user
            )
        )
        dados_dashboard = [
            {
                "status": status,
                "dados": SolicitacaoAlteracaoCronograma.objects.filtrar_por_status(
                    status, filtros, offset, limit + offset
                ),
            }
            for status in lista_status
        ]

        if status:
            dados_dashboard[0]["total"] = (
                SolicitacaoAlteracaoCronograma.objects.filtrar_por_status(
                    status, filtros
                ).count()
            )

        return dados_dashboard

    @action(
        detail=False,
        methods=["GET"],
        url_path="dashboard",
        permission_classes=(
            PermissaoParaListarDashboardSolicitacaoAlteracaoCronograma,
        ),
    )
    def dashboard(self, request):
        serialized_data = PainelSolicitacaoAlteracaoCronogramaSerializer(
            self._dados_dashboard(request), many=True
        ).data
        return Response({"results": serialized_data})

    @action(
        detail=False,
        methods=["GET"],
        url_path="dashboard-com-filtro",
        permission_classes=(
            PermissaoParaListarDashboardSolicitacaoAlteracaoCronograma,
        ),
    )
    def dashboard_com_filtro(self, request):
        filtros = request.query_params
        serialized_data = PainelSolicitacaoAlteracaoCronogramaSerializer(
            self._dados_dashboard(request, filtros), many=True
        ).data
        return Response({"results": serialized_data})

    @transaction.atomic
    @action(
        detail=True,
        permission_classes=(PermissaoParaDarCienciaAlteracaoCronograma,),
        methods=["patch"],
        url_path="cronograma-ciente",
    )
    def cronograma_ciente(self, request, uuid):
        usuario = request.user
        justificativa = request.data.get("justificativa_cronograma")
        etapas = request.data.get("etapas", [])
        programacoes = request.data.get("programacoes_de_recebimento", [])
        try:
            solicitacao_alteracao = SolicitacaoAlteracaoCronograma.objects.get(
                uuid=uuid
            )
            solicitacao_alteracao.cronograma_confirma_ciencia(
                justificativa, usuario, etapas, programacoes
            )
            serializer = SolicitacaoAlteracaoCronogramaSerializer(solicitacao_alteracao)
            return Response(serializer.data)

        except ObjectDoesNotExist as e:
            return Response(
                dict(detail=f"Solicitação Cronograma informado não é valido: {e}"),
                status=HTTP_406_NOT_ACCEPTABLE,
            )
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )

    @transaction.atomic
    @action(
        detail=True,
        permission_classes=(
            PermissaoParaAnalisarDilogAbastecimentoSolicitacaoAlteracaoCronograma,
        ),
        methods=["patch"],
        url_path="analise-abastecimento",
    )
    def analise_abastecimento(self, request, uuid):
        usuario = request.user
        aprovado = request.data.get(("aprovado"), "aprovado")
        try:
            solicitacao_cronograma = SolicitacaoAlteracaoCronograma.objects.get(
                uuid=uuid
            )
            if aprovado is True:
                solicitacao_cronograma.dilog_abastecimento_aprova(user=usuario)
            elif aprovado is False:
                justificativa = request.data.get("justificativa_abastecimento")
                solicitacao_cronograma.dilog_abastecimento_reprova(
                    user=usuario, justificativa=justificativa
                )
            else:
                raise ValidationError("Parametro aprovado deve ser true ou false.")
            solicitacao_cronograma.save()
            serializer = SolicitacaoAlteracaoCronogramaSerializer(
                solicitacao_cronograma
            )
            return Response(serializer.data)

        except ObjectDoesNotExist as e:
            return Response(
                dict(detail=f"Solicitação Cronograma informado não é valido: {e}"),
                status=HTTP_406_NOT_ACCEPTABLE,
            )
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )

    @transaction.atomic
    @action(
        detail=True,
        permission_classes=(PermissaoParaAnalisarDilogSolicitacaoAlteracaoCronograma,),
        methods=["patch"],
        url_path="analise-dilog",
    )
    def analise_dilog(self, request, uuid):
        usuario = request.user
        aprovado = request.data.get(("aprovado"), "aprovado")
        try:
            solicitacao_cronograma = SolicitacaoAlteracaoCronograma.objects.get(
                uuid=uuid
            )
            if aprovado is True:
                solicitacao_cronograma.dilog_aprova(user=usuario)
                cronograma = solicitacao_cronograma.cronograma
                cronograma.etapas.set(solicitacao_cronograma.etapas_novas.all())
                cronograma.programacoes_de_recebimento.all().delete()
                cronograma.programacoes_de_recebimento.set(
                    solicitacao_cronograma.programacoes_novas.all()
                )
                cronograma.save()
            elif aprovado is False:
                justificativa = request.data.get("justificativa_dilog")
                solicitacao_cronograma.dilog_reprova(
                    user=usuario, justificativa=justificativa
                )
            else:
                raise ValidationError("Parametro aprovado deve ser true ou false.")
            solicitacao_cronograma.save()
            solicitacao_cronograma.cronograma.finaliza_solicitacao_alteracao(
                user=usuario
            )
            serializer = SolicitacaoAlteracaoCronogramaSerializer(
                solicitacao_cronograma
            )
            return Response(serializer.data)

        except ObjectDoesNotExist as e:
            return Response(
                dict(detail=f"Solicitação Cronograma informado não é valido: {e}"),
                status=HTTP_406_NOT_ACCEPTABLE,
            )
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )

    @transaction.atomic
    @action(
        detail=True,
        permission_classes=(PermissaoParaAssinarCronogramaUsuarioFornecedor,),
        methods=["patch"],
        url_path="fornecedor-ciente",
    )
    def fornecedor_ciente(self, request, uuid):
        usuario = request.user
        try:
            solicitacao_cronograma = SolicitacaoAlteracaoCronograma.objects.get(
                uuid=uuid
            )

            solicitacao_cronograma.fornecedor_ciente(user=usuario)
            cronograma = solicitacao_cronograma.cronograma
            cronograma.qtd_total_programada = (
                solicitacao_cronograma.qtd_total_programada
            )
            cronograma.etapas.set(solicitacao_cronograma.etapas_novas.all())
            cronograma.programacoes_de_recebimento.all().delete()
            cronograma.programacoes_de_recebimento.set(
                solicitacao_cronograma.programacoes_novas.all()
            )
            cronograma.save()

            solicitacao_cronograma.save()
            # Pega o usuario CODAE do penúltimo log, pois ele sempre será a assinatura da CODAE
            usuario_codae = cronograma.logs[len(cronograma.logs) - 2].usuario
            solicitacao_cronograma.cronograma.finaliza_solicitacao_alteracao(
                user=usuario_codae
            )
            serializer = SolicitacaoAlteracaoCronogramaSerializer(
                solicitacao_cronograma
            )
            return Response(serializer.data)

        except ObjectDoesNotExist as e:
            return Response(
                dict(detail=f"Solicitação Cronograma informado não é valido: {e}"),
                status=HTTP_406_NOT_ACCEPTABLE,
            )
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )


class UnidadeMedidaViewset(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = UnidadeMedida.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaCadastrarVisualizarUnidadesMedida,)
    pagination_class = DefaultPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UnidadeMedidaFilter

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return UnidadeMedidaSerialzer
        return UnidadeMedidaCreateSerializer

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-nomes-abreviacoes",
        permission_classes=(PermissaoParaVisualizarUnidadesMedida,),
    )
    def listar_nomes_abreviacoes(self, request):
        unidades_medida = self.get_queryset()
        serializer = UnidadeMedidaSimplesSerializer(unidades_medida, many=True)
        response = {"results": serializer.data}
        return Response(response)


class LayoutDeEmbalagemModelViewSet(
    ViewSetActionPermissionMixin, viewsets.ModelViewSet
):
    lookup_field = "uuid"
    serializer_class = LayoutDeEmbalagemSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = LayoutDeEmbalagemFilter
    pagination_class = DefaultPagination
    permission_classes = (PermissaoParaVisualizarLayoutDeEmbalagem,)
    permission_action_classes = {
        "create": [UsuarioEhFornecedor],
        "delete": [UsuarioEhFornecedor],
    }

    def get_queryset(self):
        user = self.request.user
        if user.eh_fornecedor:
            return LayoutDeEmbalagem.objects.filter(
                ficha_tecnica__empresa=user.vinculo_atual.instituicao
            ).order_by("-criado_em")
        return LayoutDeEmbalagem.objects.all().order_by("-criado_em")

    def get_serializer_class(self):
        serializer_classes_map = {
            "list": LayoutDeEmbalagemSerializer,
            "retrieve": LayoutDeEmbalagemDetalheSerializer,
        }
        return serializer_classes_map.get(
            self.action, LayoutDeEmbalagemCreateSerializer
        )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="codae-aprova-ou-solicita-correcao",
        permission_classes=(PermissaoParaDashboardLayoutEmbalagem,),
    )
    def codae_aprova_ou_solicita_correcao(self, request, uuid):
        serializer = LayoutDeEmbalagemAnaliseSerializer(
            instance=self.get_object(), data=request.data, context={"request": request}
        )

        if serializer.is_valid(raise_exception=True):
            layout_atualizado = serializer.save()
            return Response(LayoutDeEmbalagemDetalheSerializer(layout_atualizado).data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="dashboard",
        permission_classes=(PermissaoParaDashboardLayoutEmbalagem,),
    )
    def dashboard(self, request):
        dashboard_service = ServiceDashboardLayoutEmbalagem(
            self.get_queryset(),
            LayoutDeEmbalagemFilter,
            PainelLayoutEmbalagemSerializer,
            request,
        )

        return Response({"results": dashboard_service.get_dados_dashboard()})

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="fornecedor-realiza-correcao",
        permission_classes=(UsuarioEhFornecedor,),
    )
    def fornecedor_realiza_correcao(self, request, uuid):
        serializer = LayoutDeEmbalagemCorrecaoSerializer(
            instance=self.get_object(), data=request.data, context={"request": request}
        )

        if serializer.is_valid(raise_exception=True):
            layout_corrigido = serializer.save()
            return Response(LayoutDeEmbalagemDetalheSerializer(layout_corrigido).data)


class DocumentoDeRecebimentoModelViewSet(
    ViewSetActionPermissionMixin, viewsets.ModelViewSet
):
    lookup_field = "uuid"
    serializer_class = DocumentoDeRecebimentoSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = DocumentoDeRecebimentoFilter
    pagination_class = DefaultPagination
    permission_classes = (PermissaoParaVisualizarDocumentosDeRecebimento,)
    permission_action_classes = {
        "create": [UsuarioEhFornecedor],
        "delete": [UsuarioEhFornecedor],
    }

    def get_queryset(self):
        user = self.request.user
        if user.eh_fornecedor:
            return DocumentoDeRecebimento.objects.filter(
                cronograma__empresa=user.vinculo_atual.instituicao
            ).order_by("-criado_em")
        return DocumentoDeRecebimento.objects.all().order_by("-criado_em")

    def get_serializer_class(self):
        user = self.request.user
        retrieve = (
            DocRecebimentoDetalharSerializer
            if user.eh_fornecedor
            else DocRecebimentoDetalharCodaeSerializer
        )
        serializer_classes_map = {
            "list": DocumentoDeRecebimentoSerializer,
            "retrieve": retrieve,
        }
        return serializer_classes_map.get(
            self.action, DocumentoDeRecebimentoCreateSerializer
        )

    @action(
        detail=False,
        methods=["GET"],
        url_path="dashboard",
        permission_classes=(PermissaoParaDashboardDocumentosDeRecebimento,),
    )
    def dashboard(self, request):
        dashboard_service = ServiceDashboardDocumentosDeRecebimento(
            self.get_queryset().order_by("-alterado_em"),
            DocumentoDeRecebimentoFilter,
            PainelDocumentoDeRecebimentoSerializer,
            request,
        )

        return Response({"results": dashboard_service.get_dados_dashboard()})

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="analise-documentos-rascunho",
        permission_classes=(UsuarioEhDilogQualidade,),
    )
    def codae_analisa_documentos_rascunho(self, request, uuid):
        serializer = DocumentoDeRecebimentoAnalisarRascunhoSerializer(
            instance=self.get_object(), data=request.data, context={"request": request}
        )

        if serializer.is_valid(raise_exception=True):
            documento_recebimento_atualizado = serializer.save()
            return Response(
                DocRecebimentoDetalharCodaeSerializer(
                    documento_recebimento_atualizado
                ).data
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="analise-documentos",
        permission_classes=(UsuarioEhDilogQualidade,),
    )
    def codae_analisa_documentos(self, request, uuid):
        serializer = DocumentoDeRecebimentoAnalisarSerializer(
            instance=self.get_object(), data=request.data, context={"request": request}
        )

        if serializer.is_valid(raise_exception=True):
            documento_recebimento_atualizado = serializer.save()
            return Response(
                DocRecebimentoDetalharCodaeSerializer(
                    documento_recebimento_atualizado
                ).data
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="corrigir-documentos",
        permission_classes=(UsuarioEhFornecedor,),
    )
    def fornecedor_realiza_correcao(self, request, uuid):
        serializer = DocumentoDeRecebimentoCorrecaoSerializer(
            instance=self.get_object(), data=request.data, context={"request": request}
        )

        if serializer.is_valid(raise_exception=True):
            documentos_corrigidos = serializer.save()
            return Response(
                DocRecebimentoDetalharSerializer(documentos_corrigidos).data
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="atualizar-documentos",
        permission_classes=(UsuarioEhFornecedor,),
    )
    def fornecedor_realiza_atualizacao(self, request, uuid):
        serializer = DocumentoDeRecebimentoAtualizacaoSerializer(
            instance=self.get_object(), data=request.data, context={"request": request}
        )

        if serializer.is_valid(raise_exception=True):
            documentos_atualizados = serializer.save()
            return Response(
                DocRecebimentoDetalharSerializer(documentos_atualizados).data
            )

    @action(
        detail=True,
        methods=["GET"],
        url_path="download-laudo-assinado",
        permission_classes=(PermissaoParaVisualizarDocumentosDeRecebimento,),
    )
    def download_laudo_assinado(self, request, uuid):
        doc_recebimento = self.get_object()
        if doc_recebimento.status != DocumentoDeRecebimentoWorkflow.APROVADO:
            return HttpResponse(
                "Não é possível fazer download do Laudo assinado de um Documento não Aprovado.",
                status=HTTP_401_UNAUTHORIZED,
            )

        return HttpResponse(
            doc_recebimento.arquivo_laudo_assinado,
            content_type="application/pdf",
        )


class FichaTecnicaRascunhoViewSet(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    lookup_field = "uuid"
    serializer_class = FichaTecnicaRascunhoSerializer
    queryset = FichaTecnicaDoProduto.objects.all().order_by("-criado_em")
    permission_classes = (UsuarioEhFornecedor,)


class FichaTecnicaModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    lookup_field = "uuid"
    serializer_class = FichaTecnicaRascunhoSerializer
    queryset = FichaTecnicaDoProduto.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaVisualizarFichaTecnica,)
    pagination_class = DefaultPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = FichaTecnicaFilter

    def get_queryset(self):
        user = self.request.user
        if user.eh_fornecedor:
            return FichaTecnicaDoProduto.objects.filter(
                empresa=user.vinculo_atual.instituicao
            ).order_by("-criado_em")

        return FichaTecnicaDoProduto.objects.all().order_by("-criado_em")

    def get_serializer_class(self):
        serializer_classes_map = {
            "list": FichaTecnicaListagemSerializer,
            "retrieve": FichaTecnicaDetalharSerializer,
            "create": FichaTecnicaCreateSerializer,
            "update": FichaTecnicaCreateSerializer,
        }

        return serializer_classes_map.get(self.action, FichaTecnicaRascunhoSerializer)

    def create(self, request, *args, **kwargs):
        return self._verificar_autenticidade_usuario(
            request, *args, **kwargs
        ) or super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return self._verificar_autenticidade_usuario(
            request, *args, **kwargs
        ) or super().update(request, *args, **kwargs)

    @action(
        detail=False,
        methods=["GET"],
        url_path="dashboard",
        permission_classes=(PermissaoParaDashboardFichaTecnica,),
    )
    def dashboard(self, request):
        qs = FichaTecnicaDoProduto.objects.order_by("-alterado_em")
        dashboard_service = ServiceDashboardFichaTecnica(
            qs,
            FichaTecnicaFilter,
            PainelFichaTecnicaSerializer,
            request,
        )

        return Response({"results": dashboard_service.get_dados_dashboard()})

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-simples",
        permission_classes=(PermissaoParaVisualizarFichaTecnica,),
    )
    def lista_simples(self, request, **kwargs):
        usuario = self.request.user

        qs = (
            self.get_queryset().filter(empresa=usuario.vinculo_atual.instituicao)
            if usuario.eh_empresa
            else self.get_queryset()
        )

        qs = qs.exclude(status=FichaTecnicaDoProduto.workflow_class.RASCUNHO)

        return Response({"results": FichaTecnicaSimplesSerializer(qs, many=True).data})

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-simples-aprovadas",
        permission_classes=(PermissaoParaVisualizarFichaTecnica,),
    )
    def lista_simples_aprovadas(self, request, **kwargs):
        usuario = self.request.user

        qs = (
            self.get_queryset().filter(empresa=usuario.vinculo_atual.instituicao)
            if usuario.eh_empresa
            else self.get_queryset()
        )

        qs = qs.filter(status=FichaTecnicaDoProduto.workflow_class.APROVADA)

        return Response({"results": FichaTecnicaSimplesSerializer(qs, many=True).data})

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-simples-sem-cronograma",
        permission_classes=(PermissaoParaVisualizarFichaTecnica,),
    )
    def lista_simples_sem_cronograma(self, request, **kwargs):
        qs = (
            self.get_queryset()
            .exclude(status=FichaTecnicaDoProduto.workflow_class.RASCUNHO)
            .exclude(cronograma__isnull=False)
        )

        return Response({"results": FichaTecnicaSimplesSerializer(qs, many=True).data})

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-simples-sem-layout-embalagem",
        permission_classes=(PermissaoParaVisualizarFichaTecnica,),
    )
    def lista_simples_sem_layout_embalagem(self, request, **kwargs):
        usuario = self.request.user

        qs = (
            self.get_queryset().filter(empresa=usuario.vinculo_atual.instituicao)
            if usuario.eh_empresa
            else self.get_queryset()
        )

        qs = qs.exclude(status=FichaTecnicaDoProduto.workflow_class.RASCUNHO).exclude(
            layout_embalagem__isnull=False
        )

        return Response({"results": FichaTecnicaSimplesSerializer(qs, many=True).data})

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-simples-sem-questoes-conferencia",
        permission_classes=(PermissaoParaVisualizarFichaTecnica,),
    )
    def lista_simples_sem_questoes_conferencia(self, request, **kwargs):
        usuario = self.request.user

        qs = (
            self.get_queryset().filter(empresa=usuario.vinculo_atual.instituicao)
            if usuario.eh_empresa
            else self.get_queryset()
        )

        qs = qs.exclude(status=FichaTecnicaDoProduto.workflow_class.RASCUNHO).exclude(
            questoes_conferencia__isnull=False
        )

        return Response({"results": FichaTecnicaSimplesSerializer(qs, many=True).data})

    @action(
        detail=True,
        methods=["GET"],
        url_path="dados-cronograma",
        permission_classes=(PermissaoParaVisualizarCronograma,),
    )
    def dados_cronograma(self, request, **kwargs):
        return Response(FichaTecnicaCronogramaSerializer(self.get_object()).data)

    @action(
        detail=True,
        methods=["GET"],
        url_path="detalhar-com-analise",
        permission_classes=(PermissaoParaVisualizarFichaTecnica,),
    )
    def detalhar_com_analise(self, request, **kwargs):
        return Response(
            FichaTecnicaComAnaliseDetalharSerializer(
                self.get_object(),
                context=self.get_serializer_context(),
            ).data
        )

    @action(
        detail=True,
        methods=["POST", "PUT"],
        url_path="rascunho-analise-gpcodae",
        permission_classes=(PermissaoParaAnalisarFichaTecnica,),
    )
    def rascunho_analise_gpcodae(self, request, *args, **kwargs):
        ficha_tecnica = self.get_object()
        analise = ficha_tecnica.analises.last()
        criado_por = self.request.user

        serializer = AnaliseFichaTecnicaRascunhoSerializer(
            instance=analise,
            data=request.data,
            context={
                "ficha_tecnica": ficha_tecnica,
                "criado_por": criado_por,
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=HTTP_201_CREATED if analise is None else HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["POST", "PUT"],
        url_path="analise-gpcodae",
        permission_classes=(PermissaoParaAnalisarFichaTecnica,),
    )
    def analise_gpcodae(self, request, *args, **kwargs):
        ficha_tecnica = self.get_object()
        analise = ficha_tecnica.analises.last()
        criado_por = self.request.user

        serializer = AnaliseFichaTecnicaCreateSerializer(
            instance=analise,
            data=request.data,
            context={
                "ficha_tecnica": ficha_tecnica,
                "criado_por": criado_por,
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=HTTP_201_CREATED if analise is None else HTTP_200_OK)

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="correcao-fornecedor",
        permission_classes=(UsuarioEhFornecedor,),
    )
    def correcao_fornecedor(self, request, *args, **kwargs):
        return self._verificar_autenticidade_usuario(
            request, *args, **kwargs
        ) or self._processa_correcao(request, *args, **kwargs)

    def _processa_correcao(self, request, *args, **kwargs):
        serializer = CorrecaoFichaTecnicaSerializer(
            instance=self.get_object(),
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(HTTP_200_OK)

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="atualizacao-fornecedor",
        permission_classes=(UsuarioEhFornecedor,),
    )
    def atualizacao_fornecedor(self, request, *args, **kwargs):
        return self._verificar_autenticidade_usuario(
            request, *args, **kwargs
        ) or self._processa_atualizacao(request, *args, **kwargs)

    def _processa_atualizacao(self, request, *args, **kwargs):
        serializer = FichaTecnicaAtualizacaoSerializer(
            instance=self.get_object(),
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(HTTP_200_OK)

    def _verificar_autenticidade_usuario(self, request, *args, **kwargs):
        usuario = request.user
        password = request.data.pop("password", "")

        if not usuario.verificar_autenticidade(password):
            return Response(
                {
                    "Senha inválida": "em caso de esquecimento de senha, solicite a recuperação e tente novamente."
                },
                status=HTTP_401_UNAUTHORIZED,
            )

    @action(detail=True, methods=["GET"], url_path="gerar-pdf-ficha")
    def gerar_pdf_ficha(self, request, uuid=None):
        ficha = self.get_object()
        return get_pdf_ficha_tecnica(request, ficha)


class CalendarioCronogramaViewset(viewsets.ReadOnlyModelViewSet):
    queryset = EtapasDoCronograma.objects.filter(cronograma__isnull=False).order_by(
        "-criado_em"
    )
    serializer_class = EtapasDoCronogramaCalendarioSerializer
    permission_classes = (PermissaoParaVisualizarCalendarioCronograma,)

    def get_queryset(self):
        mes = self.request.query_params.get("mes", None)
        ano = self.request.query_params.get("ano", None)

        valida_parametros_calendario(mes, ano)

        status_necessarios_cronogramas = [
            CronogramaWorkflow.ASSINADO_CODAE,
            CronogramaWorkflow.ALTERACAO_CODAE,
            CronogramaWorkflow.SOLICITADO_ALTERACAO,
        ]

        queryset = EtapasDoCronograma.objects.filter(
            cronograma__isnull=False,
            cronograma__status__in=status_necessarios_cronogramas,
            data_programada__month=mes,
            data_programada__year=ano,
        ).order_by("-criado_em")

        return queryset
