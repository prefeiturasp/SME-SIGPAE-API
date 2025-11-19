from datetime import datetime
from math import ceil

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import QuerySet
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

from sme_sigpae_api.dados_comuns.constants import ADMINISTRADOR_EMPRESA
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
from sme_sigpae_api.pre_recebimento.base.api.paginations import (
    PreRecebimentoPagination,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.filters import (
    CronogramaFilter,
    SolicitacaoAlteracaoCronogramaFilter,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.helpers import (
    totalizador_relatorio_cronograma,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.serializers.serializer_create import (
    CronogramaCreateSerializer,
    SolicitacaoDeAlteracaoCronogramaCreateSerializer,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.serializers.serializers import (
    CronogramaComLogSerializer,
    CronogramaFichaDeRecebimentoSerializer,
    CronogramaRascunhosSerializer,
    CronogramaRelatorioSerializer,
    CronogramaSerializer,
    CronogramaSimplesSerializer,
    EtapasDoCronogramaCalendarioSerializer,
    PainelCronogramaSerializer,
    PainelSolicitacaoAlteracaoCronogramaSerializer,
    SolicitacaoAlteracaoCronogramaCompletoSerializer,
    SolicitacaoAlteracaoCronogramaSerializer,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.services import (
    ServiceDashboardSolicitacaoAlteracaoCronogramaProfiles,
    ServiceQuerysetAlteracaoCronograma,
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
from sme_sigpae_api.relatorios.relatorios import get_pdf_cronograma

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

    def filtrar_etapas(self, serialized_data, request):
        data_inicial = request.query_params.get("data_inicial")
        data_final = request.query_params.get("data_final")
        situacoes = request.query_params.getlist("situacao", [])

        if not any([data_inicial, data_final, situacoes]) or len(situacoes) == 3:
            return serialized_data

        data_inicio_obj = self.parse_date(data_inicial) if data_inicial else None
        data_fim_obj = self.parse_date(data_final) if data_final else None
        tem_filtro_situacao = situacoes and len(situacoes) < 3

        for i in range(len(serialized_data) - 1, -1, -1):
            cronograma_data = serialized_data[i]
            etapas = cronograma_data.get("etapas", [])

            for j in range(len(etapas) - 1, -1, -1):
                etapa_data = etapas[j]
                deve_manter_etapa = self.aplicar_filtros_etapa(
                    etapa_data,
                    data_inicio_obj,
                    data_fim_obj,
                    situacoes,
                    tem_filtro_situacao,
                )

                if not deve_manter_etapa:
                    etapas.pop(j)

            if not etapas:
                serialized_data.pop(i)

        return serialized_data

    def parse_date(self, date_str):
        try:
            return datetime.strptime(date_str, "%d/%m/%Y").date()
        except (ValueError, AttributeError):
            return None

    def aplicar_filtros_etapa(
        self, etapa_data, data_inicio_obj, data_fim_obj, situacoes, tem_filtro_situacao
    ):
        if data_inicio_obj or data_fim_obj:
            if not self._passa_filtro_data_etapa(
                etapa_data, data_inicio_obj, data_fim_obj
            ):
                return False

        if tem_filtro_situacao:
            return self.passa_filtro_situacao(etapa_data, situacoes)

        return True

    def _passa_filtro_data_etapa(self, etapa_data, data_inicio_obj, data_fim_obj):
        """Helper para verificar se etapa passa no filtro de data"""
        data_programada = etapa_data.get("data_programada")
        if not data_programada:
            return False

        try:
            data_etapa = datetime.strptime(data_programada, "%d/%m/%Y").date()
            if data_inicio_obj and data_etapa < data_inicio_obj:
                return False
            if data_fim_obj and data_etapa > data_fim_obj:
                return False

            return True
        except (ValueError, AttributeError):
            return False

    def passa_filtro_situacao(self, etapa_data, situacoes):
        if not situacoes or len(situacoes) == 3:
            return True

        fichas_recebimento = etapa_data.get("fichas_recebimento", [])

        tem_fichas_com_ocorrencia = any(
            f.get("houve_ocorrencia") is True for f in fichas_recebimento
        )
        tem_fichas_sem_ocorrencia = any(
            f.get("houve_ocorrencia") in (None, False) for f in fichas_recebimento
        )

        incluir_etapa = False
        fichas_finais = []

        incluir_etapa, fichas_finais = self._processar_situacao_recebido(
            situacoes,
            tem_fichas_sem_ocorrencia,
            fichas_recebimento,
            incluir_etapa,
            fichas_finais,
        )

        incluir_etapa, fichas_finais = self._processar_situacao_ocorrencia(
            situacoes,
            tem_fichas_com_ocorrencia,
            tem_fichas_sem_ocorrencia,
            fichas_recebimento,
            incluir_etapa,
            fichas_finais,
        )

        incluir_etapa, fichas_finais = self._processar_situacao_a_receber(
            situacoes,
            fichas_recebimento,
            tem_fichas_com_ocorrencia,
            tem_fichas_sem_ocorrencia,
            incluir_etapa,
            fichas_finais,
        )

        if incluir_etapa:
            etapa_data["fichas_recebimento"] = fichas_finais

        return incluir_etapa

    def _processar_situacao_recebido(
        self,
        situacoes,
        tem_fichas_sem_ocorrencia,
        fichas_recebimento,
        incluir_etapa,
        fichas_finais,
    ):
        if "Recebido" in situacoes and tem_fichas_sem_ocorrencia:
            incluir_etapa = True
            fichas_finais = [
                f
                for f in fichas_recebimento
                if f.get("houve_ocorrencia") in (None, False)
            ]
        return incluir_etapa, fichas_finais

    def _processar_situacao_ocorrencia(
        self,
        situacoes,
        tem_fichas_com_ocorrencia,
        tem_fichas_sem_ocorrencia,
        fichas_recebimento,
        incluir_etapa,
        fichas_finais,
    ):
        if "Ocorrência" in situacoes and tem_fichas_com_ocorrencia:
            incluir_etapa = True
            fichas_com_ocorrencia = [
                f for f in fichas_recebimento if f.get("houve_ocorrencia") is True
            ]
            if "Recebido" in situacoes and tem_fichas_sem_ocorrencia:
                fichas_finais = fichas_finais + fichas_com_ocorrencia
            else:
                fichas_finais = fichas_com_ocorrencia
        return incluir_etapa, fichas_finais

    def _processar_situacao_a_receber(
        self,
        situacoes,
        fichas_recebimento,
        tem_fichas_com_ocorrencia,
        tem_fichas_sem_ocorrencia,
        incluir_etapa,
        fichas_finais,
    ):
        if "A Receber" in situacoes:
            if not fichas_recebimento or (
                tem_fichas_com_ocorrencia and not tem_fichas_sem_ocorrencia
            ):
                incluir_etapa = True
                if "Ocorrência" not in situacoes:
                    fichas_finais = []
        return incluir_etapa, fichas_finais

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

        situacoes = request.query_params.getlist("situacao", [])
        data_inicial = request.query_params.get("data_inicial")
        data_final = request.query_params.get("data_final")

        tem_filtro_pos_serializacao = (
            (bool(situacoes) and len(situacoes) < 3)
            or bool(data_inicial)
            or bool(data_final)
        )

        if tem_filtro_pos_serializacao:
            serializer = CronogramaRelatorioSerializer(queryset, many=True)

            dados_filtrados = self.filtrar_etapas(serializer.data, request)

            page_size = self.pagination_class().page_size
            page_number = int(request.query_params.get("page", 1))

            start_index = (page_number - 1) * page_size
            end_index = start_index + page_size
            dados_paginados = dados_filtrados[start_index:end_index]

            total_items = len(dados_filtrados)
            total_pages = ceil(total_items / page_size) if page_size > 0 else 1
            has_next = page_number < total_pages
            has_previous = page_number > 1

            response_data = {
                "count": total_items,
                "next": f"?page={page_number + 1}" if has_next else None,
                "previous": f"?page={page_number - 1}" if has_previous else None,
                "results": dados_paginados,
                "totalizadores": totalizador_relatorio_cronograma(queryset),
            }

            return Response(response_data)

        else:
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = CronogramaRelatorioSerializer(page, many=True)
                response = self.get_paginated_response(serializer.data)
                response.data["totalizadores"] = totalizador_relatorio_cronograma(
                    queryset
                )
                return response
            else:
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
