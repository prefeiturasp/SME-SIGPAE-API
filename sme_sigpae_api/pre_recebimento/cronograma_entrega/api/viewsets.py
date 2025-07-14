from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_406_NOT_ACCEPTABLE,
)
from xworkflows.base import InvalidTransitionError

from sme_sigpae_api.dados_comuns.fluxo_status import (
    CronogramaWorkflow,
)
from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoParaAnalisarDilogAbastecimentoSolicitacaoAlteracaoCronograma,
    PermissaoParaAnalisarDilogSolicitacaoAlteracaoCronograma,
    PermissaoParaAssinarCronogramaUsuarioDilog,
    PermissaoParaAssinarCronogramaUsuarioFornecedor,
    PermissaoParaCriarCronograma,
    PermissaoParaCriarSolicitacoesAlteracaoCronograma,
    PermissaoParaDarCienciaAlteracaoCronograma,
    PermissaoParaDashboardCronograma,
    PermissaoParaListarDashboardSolicitacaoAlteracaoCronograma,
    PermissaoParaVisualizarCalendarioCronograma,
    PermissaoParaVisualizarCronograma,
    PermissaoParaVisualizarRelatorioCronograma,
    PermissaoParaVisualizarSolicitacoesAlteracaoCronograma,
    UsuarioDilogAbastecimento,
    ViewSetActionPermissionMixin,
    
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.filters import (
    SolicitacaoAlteracaoCronogramaFilter,
)
from sme_sigpae_api.pre_recebimento.base.api.paginations import (
    PreRecebimentoPagination,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.serializers.serializer_create import (
    SolicitacaoDeAlteracaoCronogramaCreateSerializer,
)

from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.services import (

    ServiceDashboardSolicitacaoAlteracaoCronogramaProfiles,
    ServiceQuerysetAlteracaoCronograma,
)

from django.db.models import QuerySet

from sme_sigpae_api.relatorios.relatorios import get_pdf_cronograma

from sme_sigpae_api.dados_comuns.constants import ADMINISTRADOR_EMPRESA
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.filters import (
    CronogramaFilter,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.helpers import totalizador_relatorio_cronograma

from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.serializers.serializer_create import (
    CronogramaCreateSerializer,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.serializers.serializers import (
    CronogramaComLogSerializer,
    CronogramaFichaDeRecebimentoSerializer,
    CronogramaRascunhosSerializer,
    CronogramaRelatorioSerializer,
    CronogramaSerializer,
    CronogramaSimplesSerializer,
    EtapasDoCronogramaCalendarioSerializer,
    PainelSolicitacaoAlteracaoCronogramaSerializer,
    SolicitacaoAlteracaoCronogramaCompletoSerializer,
    SolicitacaoAlteracaoCronogramaSerializer,
    PainelCronogramaSerializer,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import (
    Cronograma,
    EtapasDoCronograma,
    SolicitacaoAlteracaoCronograma,
)

from sme_sigpae_api.pre_recebimento.tasks import (
    gerar_relatorio_cronogramas_pdf_async,
    gerar_relatorio_cronogramas_xlsx_async,
)

from ....dados_comuns.models import LogSolicitacoesUsuario


from .validators import valida_parametros_calendario


class CronogramaModelViewSet(ViewSetActionPermissionMixin, viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = Cronograma.objects.all()
    serializer_class = CronogramaSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CronogramaFilter
    pagination_class = PreRecebimentoPagination
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


class SolicitacaoDeAlteracaoCronogramaViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    filter_backends = (filters.DjangoFilterBackend,)
    pagination_class = PreRecebimentoPagination
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
