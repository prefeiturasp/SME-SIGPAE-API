import calendar
import datetime
import json

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, IntegerField, Q, QuerySet
from django.db.models.functions import Cast
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ViewSet
from workalendar.america import BrazilSaoPauloCity
from xworkflows import InvalidTransitionError

from sme_sigpae_api.cardapio.utils import ordem_periodos
from sme_sigpae_api.medicao_inicial.services.relatorio_adesao import (
    obtem_resultados,
    valida_parametros_periodo_lancamento,
)
from sme_sigpae_api.medicao_inicial.utils import process_anexos_from_request

from ...cardapio.base.models import TipoAlimentacao
from ...dados_comuns import constants
from ...dados_comuns.api.serializers import LogSolicitacoesUsuarioSerializer
from ...dados_comuns.constants import TRADUCOES_FERIADOS
from ...dados_comuns.models import LogSolicitacoesUsuario
from ...dados_comuns.permissions import (
    UsuarioAdministradorEmpresaTerceirizada,
    UsuarioCODAEGabinete,
    UsuarioCODAEGestaoAlimentacao,
    UsuarioCODAENutriManifestacao,
    UsuarioDinutreDiretoria,
    UsuarioDiretorEscolaTercTotal,
    UsuarioDiretoriaRegional,
    UsuarioEmpresaTerceirizada,
    UsuarioEscolaTercTotal,
    UsuarioEscolaTercTotalSemAlunosRegulares,
    UsuarioMedicao,
    UsuarioSupervisaoNutricao,
    ViewSetActionPermissionMixin,
)
from ...dados_comuns.utils import get_ultimo_dia_mes
from ...escola.api.permissions import (
    PodeCriarAdministradoresDaCODAEGestaoAlimentacaoTerceirizada,
)
from ...escola.models import (
    DiretoriaRegional,
    Escola,
    FaixaEtaria,
    GrupoUnidadeEscolar,
    LogAlunosMatriculadosPeriodoEscola,
    Lote,
    TipoTurma,
)
from ..models import (
    AlimentacaoLancamentoEspecial,
    CategoriaMedicao,
    ClausulaDeDesconto,
    DiaParaCorrigir,
    DiaSobremesaDoce,
    Empenho,
    Medicao,
    OcorrenciaMedicaoInicial,
    ParametrizacaoFinanceira,
    PermissaoLancamentoEspecial,
    RelatorioFinanceiro,
    SolicitacaoMedicaoInicial,
    TipoContagemAlimentacao,
    ValorMedicao,
)
from ..tasks import (
    exporta_relatorio_adesao_para_pdf,
    exporta_relatorio_adesao_para_xlsx,
    exporta_relatorio_consolidado_xlsx,
    gera_pdf_relatorio_solicitacao_medicao_por_escola_async,
    gera_pdf_relatorio_unificado_async,
)
from ..utils import (
    atualizar_anexos_ocorrencia,
    criar_log_aprovar_periodos_corrigidos,
    criar_log_solicitar_correcao_periodos,
    get_campos_a_desconsiderar,
    get_dict_alimentacoes_lancamentos_especiais,
    get_valor_total,
    log_alteracoes_escola_corrige_periodo,
    tratar_valores,
)
from .constants import (
    ORDEM_NAME_LANCAMENTOS_ESPECIAIS,
    STATUS_RELACAO_DRE,
    STATUS_RELACAO_DRE_CODAE,
    STATUS_RELACAO_DRE_MEDICAO,
    STATUS_RELACAO_DRE_UE,
    USUARIOS_VISAO_CODAE,
)
from .filters import (
    ClausulaDeDescontoFilter,
    DiaParaCorrecaoFilter,
    EmpenhoFilter,
    ParametrizacaoFinanceiraFilter,
    RelatorioFinanceiroFilter,
)
from .permissions import EhAdministradorMedicaoInicialOuGestaoAlimentacao
from .serializers import (
    AlimentacaoLancamentoEspecialSerializer,
    CategoriaMedicaoSerializer,
    ClausulaDeDescontoSerializer,
    DadosParametrizacaoFinanceiraSerializer,
    DiaParaCorrigirSerializer,
    DiaSobremesaDoceSerializer,
    EmpenhoSerializer,
    MedicaoSerializer,
    OcorrenciaMedicaoInicialSerializer,
    ParametrizacaoFinanceiraSerializer,
    PermissaoLancamentoEspecialSerializer,
    RelatorioFinanceiroSerializer,
    SolicitacaoMedicaoInicialDashboardSerializer,
    SolicitacaoMedicaoInicialLancadaSerializer,
    SolicitacaoMedicaoInicialSerializer,
    TipoContagemAlimentacaoSerializer,
    ValorMedicaoSerializer,
)
from .serializers_create import (
    ClausulaDeDescontoCreateUpdateSerializer,
    DiaSobremesaDoceCreateManySerializer,
    EmpenhoCreateUpdateSerializer,
    InformacoesBasicasMedicaoInicialUpdateSerializer,
    MedicaoCreateUpdateSerializer,
    ParametrizacaoFinanceiraWriteModelSerializer,
    PermissaoLancamentoEspecialCreateUpdateSerializer,
    SolicitacaoMedicaoInicialCreateSerializer,
)

calendario = BrazilSaoPauloCity()


DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10


class CustomPagination(PageNumberPagination):
    page = DEFAULT_PAGE
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        return Response(
            {
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "count": self.page.paginator.count,
                "page_size": int(self.request.GET.get("page_size", self.page_size)),
                "results": data,
            }
        )


class DiaSobremesaDoceViewSet(ViewSetActionPermissionMixin, ModelViewSet):
    permission_action_classes = {
        "list": [EhAdministradorMedicaoInicialOuGestaoAlimentacao],
        "create": [PodeCriarAdministradoresDaCODAEGestaoAlimentacaoTerceirizada],
        "delete": [PodeCriarAdministradoresDaCODAEGestaoAlimentacaoTerceirizada],
    }
    queryset = (
        DiaSobremesaDoce.objects.select_related("tipo_unidade", "criado_por", "edital")
        .annotate(edital_numero=F("edital__numero"))
        .all()
    )
    lookup_field = "uuid"
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return DiaSobremesaDoceCreateManySerializer
        return DiaSobremesaDoceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if "mes" in self.request.query_params and "ano" in self.request.query_params:
            queryset = queryset.filter(
                data__month=self.request.query_params.get("mes"),
                data__year=self.request.query_params.get("ano"),
            )
        if "escola_uuid" in self.request.query_params:
            escola = Escola.objects.get(
                uuid=self.request.query_params.get("escola_uuid")
            )
            queryset = queryset.filter(
                tipo_unidade=escola.tipo_unidade,
                edital__uuid__in=escola.editais,
            )
        return queryset

    def create(self, request, *args, **kwargs):
        try:
            return super(DiaSobremesaDoceViewSet, self).create(request, *args, **kwargs)
        except AssertionError as error:
            if str(error) == "`create()` did not return an object instance.":
                return Response(status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        DiaSobremesaDoce.objects.filter(
            data=instance.data, tipo_unidade=instance.tipo_unidade
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["GET"], url_path="lista-dias")
    def lista_dias(self, request):
        try:
            lista_dias = self.get_queryset().values_list("data", flat=True).distinct()
            return Response(lista_dias, status=status.HTTP_200_OK)
        except Escola.DoesNotExist as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SolicitacaoMedicaoInicialViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    lookup_field = "uuid"
    permission_classes = [
        UsuarioEscolaTercTotal
        | UsuarioDiretoriaRegional
        | UsuarioCODAEGestaoAlimentacao
        | UsuarioCODAENutriManifestacao
        | UsuarioCODAEGabinete
        | UsuarioDinutreDiretoria
        | UsuarioEmpresaTerceirizada
        | UsuarioSupervisaoNutricao
    ]
    queryset = SolicitacaoMedicaoInicial.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SolicitacaoMedicaoInicialCreateSerializer
        return SolicitacaoMedicaoInicialSerializer

    def update(self, request, *args, **kwargs):
        try:
            return super(SolicitacaoMedicaoInicialViewSet, self).update(
                request, *args, **kwargs
            )
        except ValidationError as lista_erros:
            list_response = []
            for indice, erro in enumerate(lista_erros):
                param = "erro" if "Restam dias" in erro else "periodo_escolar"
                if indice % 2 == 0:
                    obj = {param: erro}
                else:
                    obj[param] = erro
                    list_response.append(obj)
            return Response(list_response, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        escola_uuid = request.query_params.get("escola")
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")

        queryset = queryset.filter(escola__uuid=escola_uuid, mes=mes, ano=ano)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def _get_lista_status(self):
        usuario = self.request.user

        if usuario.tipo_usuario == "medicao":
            return STATUS_RELACAO_DRE_MEDICAO + ["TODOS_OS_LANCAMENTOS"]
        elif usuario.tipo_usuario == "diretoriaregional":
            return STATUS_RELACAO_DRE + ["TODOS_OS_LANCAMENTOS"]
        elif usuario.tipo_usuario in USUARIOS_VISAO_CODAE + [
            "terceirizada",
            "supervisao_nutricao",
        ]:
            return STATUS_RELACAO_DRE_CODAE + ["TODOS_OS_LANCAMENTOS"]
        else:
            return (
                STATUS_RELACAO_DRE_UE
                + STATUS_RELACAO_DRE_CODAE
                + ["TODOS_OS_LANCAMENTOS"]
            )

    def _condicao_por_usuario(self, queryset):
        usuario = self.request.user

        if usuario.tipo_usuario in USUARIOS_VISAO_CODAE + [
            "terceirizada",
            "supervisao_nutricao",
        ]:
            return queryset.filter(status__in=STATUS_RELACAO_DRE_CODAE)
        if not (
            usuario.tipo_usuario == "diretoriaregional"
            or usuario.tipo_usuario == "medicao"
        ):
            queryset = queryset.exclude(
                status="MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE"
            )
        if usuario.tipo_usuario == "diretoriaregional":
            return queryset.filter(
                escola__diretoria_regional=usuario.vinculo_atual.instituicao
            )
        elif usuario.tipo_usuario == "escola":
            return queryset.filter(escola=usuario.vinculo_atual.instituicao)
        elif usuario.tipo_usuario == "medicao":
            return queryset.filter(status__in=STATUS_RELACAO_DRE_MEDICAO)
        return queryset

    def _get_label(self, workflow: str) -> str:
        try:
            return SolicitacaoMedicaoInicial.workflow_class.states[workflow].title
        except (ValidationError, KeyError):
            return "TODOS_OS_LANCAMENTOS"

    def _get_totalizadores(self, query_set: QuerySet, kwargs: dict) -> list:
        sumario = []

        for workflow in self._get_lista_status():
            todos_lancamentos = workflow == "TODOS_OS_LANCAMENTOS"
            qs = (
                query_set.filter(status=workflow)
                if not todos_lancamentos
                else query_set
            )
            qs = self._condicao_por_usuario(qs)
            qs = qs.filter(**kwargs)
            sumario.append(
                {
                    "status": workflow,
                    "label": self._get_label(workflow),
                    "total": len(qs),
                }
            )
        return sumario

    def _get_resultados(
        self, request: Request, query_set: QuerySet, kwargs: dict
    ) -> dict:
        limit = int(request.query_params.get("limit", 10))
        offset = int(request.query_params.get("offset", 0))
        workflow = request.query_params.get("status")
        qs = self._condicao_por_usuario(query_set)
        qs = qs.filter(**kwargs)

        logs_map = {}
        for log in LogSolicitacoesUsuario.objects.filter(
            uuid_original__in=qs.values_list("uuid", flat=True)
        ).order_by("uuid_original", "-criado_em"):
            logs_map.setdefault(log.uuid_original, []).append(log)

        def log_mais_recente(obj):
            return logs_map[obj.uuid][0] if logs_map[obj.uuid] else None

        qs_ordenado = sorted(
            qs,
            key=lambda obj: (
                log_mais_recente(obj).criado_em
                if log_mais_recente(obj)
                else datetime.min
            ),
        )
        total = len(qs_ordenado)
        paginated = qs_ordenado[offset : offset + limit]
        return {
            "total": total,
            "dados": SolicitacaoMedicaoInicialDashboardSerializer(
                paginated,
                context={"request": self.request, "workflow": workflow},
                many=True,
            ).data,
        }

    def _formatar_filtros(self, query_params):
        kwargs = {}

        mapping = {
            "tipo_unidade": lambda params: {
                "escola__tipo_unidade__uuid": params.get("tipo_unidade")
            },
            "dre": lambda params: {
                "escola__diretoria_regional__uuid": params.get("dre")
            },
            "ocorrencias": lambda params: {
                "com_ocorrencias": params.get("ocorrencias").lower() == "true"
            },
            "mes_ano": lambda params: dict(
                zip(["mes", "ano"], params["mes_ano"].split("_"))
            ),
            "lotes_selecionados[]": lambda params: {
                "escola__lote__uuid__in": params.getlist("lotes_selecionados[]")
            },
            "escola": lambda params: {
                "escola__codigo_eol": params.get("escola").split(" - ")[0]
            },
        }

        if query_params.get("status") != "TODOS_OS_LANCAMENTOS":
            mapping["status"] = lambda params: {"status": params.get("status")}

        for param, parser in mapping.items():
            if query_params.get(param) or query_params.getlist(param):
                kwargs.update(parser(query_params))

        return kwargs

    @action(
        detail=False,
        methods=["GET"],
        url_path="dashboard-totalizadores",
        permission_classes=[
            UsuarioEscolaTercTotal
            | UsuarioDiretoriaRegional
            | UsuarioCODAEGestaoAlimentacao
            | UsuarioCODAENutriManifestacao
            | UsuarioCODAEGabinete
            | UsuarioDinutreDiretoria
            | UsuarioEmpresaTerceirizada
            | UsuarioSupervisaoNutricao
        ],
    )
    def dashboard_totalizadores(self, request):
        query_set = self.get_queryset()
        kwargs = self._formatar_filtros(request.query_params)
        response = {
            "results": self._get_totalizadores(query_set=query_set, kwargs=kwargs)
        }
        return Response(response)

    @action(
        detail=False,
        methods=["GET"],
        url_path="dashboard-resultados",
        permission_classes=[
            UsuarioEscolaTercTotal
            | UsuarioDiretoriaRegional
            | UsuarioCODAEGestaoAlimentacao
            | UsuarioCODAENutriManifestacao
            | UsuarioCODAEGabinete
            | UsuarioDinutreDiretoria
            | UsuarioEmpresaTerceirizada
            | UsuarioSupervisaoNutricao
        ],
    )
    def dashboard_resultados(self, request):
        query_set = self.get_queryset()
        kwargs = self._formatar_filtros(request.query_params)
        response = {
            "results": self._get_resultados(
                request=request, query_set=query_set, kwargs=kwargs
            )
        }
        return Response(response)

    @action(
        detail=False,
        methods=["GET"],
        url_path="meses-anos",
        permission_classes=[
            UsuarioEscolaTercTotal
            | UsuarioDiretoriaRegional
            | UsuarioCODAEGestaoAlimentacao
            | UsuarioCODAENutriManifestacao
            | UsuarioCODAEGabinete
            | UsuarioDinutreDiretoria
            | UsuarioEmpresaTerceirizada
            | UsuarioSupervisaoNutricao
        ],
    )
    def meses_anos(self, request):
        qs_solicitacao_medicao = SolicitacaoMedicaoInicial.objects.all()
        query_set = self._condicao_por_usuario(self.get_queryset())

        if (
            isinstance(request.user.vinculo_atual.instituicao, DiretoriaRegional)
            or request.user.tipo_usuario
            in USUARIOS_VISAO_CODAE + ["terceirizada", "supervisao_nutricao"]
            or (
                request.query_params.get("eh_relatorio_adesao")
                and request.user.tipo_usuario == constants.TIPO_USUARIO_ESCOLA
            )
        ):
            qs_solicitacao_medicao = query_set

        filtros = {}

        if request.query_params.get("status"):
            filtros["status"] = request.query_params.get("status")

        if request.query_params.get("dre"):
            filtros["escola__diretoria_regional__uuid"] = request.query_params.get(
                "dre"
            )

        if filtros:
            qs_solicitacao_medicao = qs_solicitacao_medicao.filter(**filtros)

        meses_anos = qs_solicitacao_medicao.values_list("mes", "ano").distinct()
        meses_anos_unicos = []

        for mes_ano in meses_anos:
            status_ = (
                qs_solicitacao_medicao.filter(mes=mes_ano[0], ano=mes_ano[1])
                .values_list("status", flat=True)
                .distinct()
            )
            mes_ano_obj = {"mes": mes_ano[0], "ano": mes_ano[1], "status": status_}
            meses_anos_unicos.append(mes_ano_obj)
        return Response(
            {
                "results": sorted(
                    meses_anos_unicos, key=lambda k: (k["ano"], k["mes"]), reverse=True
                )
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["GET"], url_path="relatorio-pdf")
    def relatorio_pdf(self, request):
        user = request.user.get_username()
        uuid_sol_medicao = request.query_params["uuid"]
        solicitacao = SolicitacaoMedicaoInicial.objects.get(uuid=uuid_sol_medicao)
        gera_pdf_relatorio_solicitacao_medicao_por_escola_async.delay(
            user=user,
            nome_arquivo=f"Relatório Medição Inicial - {solicitacao.escola.nome} - "
            f"{solicitacao.mes}/{solicitacao.ano}.pdf",
            uuid_sol_medicao=uuid_sol_medicao,
        )
        return Response(
            dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["GET"], url_path="relatorio-unificado")
    def relatorio_unificado(self, request):
        user = request.user.get_username()
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")
        if not mes and not ano:
            return Response(
                data="É necessário informar o mês/ano de referência",
                status=status.HTTP_400_BAD_REQUEST,
            )

        uuid_grupo_escolar = request.query_params.get("grupo_escolar")
        status_solicitacao = request.query_params.get("status")
        uuid_dre = request.query_params.get("dre")

        diretoria_regional = DiretoriaRegional.objects.get(uuid=uuid_dre)
        grupo_unidade_escolar = GrupoUnidadeEscolar.objects.get(uuid=uuid_grupo_escolar)
        query_set = SolicitacaoMedicaoInicial.objects.filter(
            mes=mes,
            ano=ano,
            status=status_solicitacao,
            escola__diretoria_regional__uuid=uuid_dre,
        )
        tipos_de_unidade_do_grupo = [
            tipo_unidade.iniciais
            for tipo_unidade in grupo_unidade_escolar.tipos_unidades.all()
        ]

        if query_set.exists():
            solicitacoes = []
            for solicitacao in query_set:
                id_tipo_unidade = solicitacao.escola.tipo_unidade.id
                if grupo_unidade_escolar.tipos_unidades.filter(
                    id=id_tipo_unidade
                ).exists():
                    solicitacoes.append(solicitacao.uuid)
            if solicitacoes:
                nome_arquivo = f"Relatório Unificado das Medições Inicias - {diretoria_regional.nome} - {grupo_unidade_escolar.nome} - {mes}/{ano}.pdf"
                gera_pdf_relatorio_unificado_async.delay(
                    user=user,
                    nome_arquivo=nome_arquivo,
                    ids_solicitacoes=solicitacoes,
                    tipos_de_unidade=tipos_de_unidade_do_grupo,
                )
                return Response(
                    dict(
                        detail="Solicitação de geração de arquivo recebida com sucesso."
                    ),
                    status=status.HTTP_200_OK,
                )
        return Response(
            data={
                "erro": "Não foram encontradas Medições Iniciais para o grupo e mês de referência selecionados"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=False,
        methods=["GET"],
        url_name="relatorio-consolidado_exportar-xlsx",
        url_path="relatorio-consolidado/exportar-xlsx",
        permission_classes=[
            UsuarioMedicao
            | UsuarioDiretoriaRegional
            | UsuarioCODAEGestaoAlimentacao
            | UsuarioAdministradorEmpresaTerceirizada
            | UsuarioCODAENutriManifestacao
            | UsuarioDinutreDiretoria
            | UsuarioCODAEGabinete
        ],
    )
    def relatorio_consolidado_exportar_xlsx(self, request: Request):
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")
        if not mes and not ano:
            return Response(
                data="É necessário informar o mês/ano de referência",
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            uuid_grupo_escolar = request.query_params.get("grupo_escolar")
            status_solicitacao = request.query_params.get("status")
            uuid_dre = request.query_params.get("dre")
            uuid_lotes = request.query_params.getlist("lotes[]", None)

            query_params = request.query_params.dict()

            filtros = {
                "mes": mes,
                "ano": ano,
                "status": status_solicitacao,
            }

            if uuid_lotes:
                lotes = Lote.objects.filter(uuid__in=uuid_lotes)
                filtros["escola__lote__in"] = lotes
                query_params["lotes"] = request.query_params.getlist("lotes[]")

            diretoria_regional = DiretoriaRegional.objects.get(uuid=uuid_dre)
            filtros["escola__diretoria_regional"] = diretoria_regional

            grupo_unidade_escolar = GrupoUnidadeEscolar.objects.get(
                uuid=uuid_grupo_escolar
            )
            tipos_unidades = grupo_unidade_escolar.tipos_unidades.all()
            filtros["escola__tipo_unidade__in"] = tipos_unidades

            solicitacoes_com_filtro = SolicitacaoMedicaoInicial.objects.filter(
                **filtros
            ).values_list("uuid", flat=True)
            if solicitacoes_com_filtro.exists():
                solicitacoes = list(solicitacoes_com_filtro)

                tipos_de_unidade_do_grupo = list(
                    tipos_unidades.values_list("iniciais", flat=True)
                )

                nome_arquivo = f"Relatório Consolidado das Medições Inicias - {diretoria_regional.nome} - {grupo_unidade_escolar.nome} - {mes}/{ano}.xlsx"

                exporta_relatorio_consolidado_xlsx.delay(
                    user=request.user.get_username(),
                    nome_arquivo=nome_arquivo,
                    solicitacoes=solicitacoes,
                    tipos_de_unidade=tipos_de_unidade_do_grupo,
                    query_params=query_params,
                )

                return Response(
                    data={
                        "detail": "Solicitação de geração de arquivo recebida com sucesso."
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                data={
                    "erro": "Não foram encontradas Medições Iniciais. Verifique os parâmetros e tente novamente"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                data={"erro": "Verifique os parâmetros e tente novamente"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False,
        methods=["GET"],
        url_path="periodos-grupos-medicao",
        permission_classes=[
            UsuarioDiretoriaRegional
            | UsuarioEscolaTercTotal
            | UsuarioCODAEGestaoAlimentacao
            | UsuarioCODAENutriManifestacao
            | UsuarioCODAEGabinete
            | UsuarioDinutreDiretoria
            | UsuarioEmpresaTerceirizada
            | UsuarioSupervisaoNutricao
        ],
    )
    def periodos_grupos_medicao(self, request):
        uuid = request.query_params.get("uuid_solicitacao")
        solicitacao = SolicitacaoMedicaoInicial.objects.get(uuid=uuid)
        retorno = []
        for medicao in solicitacao.medicoes.all():
            nome = None
            if medicao.grupo and medicao.periodo_escolar:
                nome = f"{medicao.grupo.nome} - {medicao.periodo_escolar.nome}"
            elif medicao.grupo and not medicao.periodo_escolar:
                nome = f"{medicao.grupo.nome}"
            elif medicao.periodo_escolar:
                nome = medicao.periodo_escolar.nome
            retorno.append(
                {
                    "uuid_medicao_periodo_grupo": medicao.uuid,
                    "nome_periodo_grupo": nome,
                    "periodo_escolar": (
                        medicao.periodo_escolar.nome
                        if medicao.periodo_escolar
                        else None
                    ),
                    "grupo": medicao.grupo.nome if medicao.grupo else None,
                    "status": medicao.status.name,
                    "logs": LogSolicitacoesUsuarioSerializer(
                        medicao.logs.all(), many=True
                    ).data,
                }
            )
        ordem = (
            constants.ORDEM_PERIODOS_GRUPOS_CEI
            if solicitacao.escola.eh_cei
            else (
                constants.ORDEM_PERIODOS_GRUPOS_CEMEI
                if solicitacao.escola.eh_cemei
                else constants.ORDEM_PERIODOS_GRUPOS
            )
        )

        return Response(
            {"results": sorted(retorno, key=lambda k: ordem[k["nome_periodo_grupo"]])},
            status=status.HTTP_200_OK,
        )

    def get_justificativa(self, medicao: Medicao) -> str:
        if medicao.status == medicao.workflow_class.MEDICAO_CORRIGIDA_PELA_UE:
            return (
                medicao.logs.filter(
                    status_evento=LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA
                )
                .last()
                .justificativa
            )
        elif medicao.status == medicao.workflow_class.MEDICAO_CORRIGIDA_PARA_CODAE:
            return (
                medicao.logs.filter(
                    status_evento=LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA_CODAE
                )
                .last()
                .justificativa
            )
        return medicao.logs.last().justificativa if medicao.logs.last() else None

    @action(
        detail=False,
        methods=["GET"],
        url_path="quantidades-alimentacoes-lancadas-periodo-grupo",
        permission_classes=[UsuarioEscolaTercTotal],
    )
    def quantidades_alimentacoes_lancadas_periodo_grupo(self, request):
        usuario = self.request.user
        escola = usuario.vinculo_atual.instituicao
        uuid = request.query_params.get("uuid_solicitacao")
        solicitacao = SolicitacaoMedicaoInicial.objects.get(uuid=uuid)
        retorno = []
        for medicao in solicitacao.medicoes.all():
            campos_a_desconsiderar = get_campos_a_desconsiderar(escola, medicao)
            total_por_nome_campo = {}
            for valor_medicao in medicao.valores_medicao.exclude(
                categoria_medicao__nome__icontains="DIETA"
            ):
                if valor_medicao.nome_campo not in campos_a_desconsiderar:
                    total_por_nome_campo[valor_medicao.nome_campo] = (
                        total_por_nome_campo.get(valor_medicao.nome_campo, 0)
                        + int(valor_medicao.valor)
                    )
            total_por_nome_campo = tratar_valores(escola, total_por_nome_campo)
            valor_total = get_valor_total(escola, total_por_nome_campo, medicao)
            valores = [
                {"nome_campo": nome_campo, "valor": valor}
                for nome_campo, valor in total_por_nome_campo.items()
            ]
            dict_retorno = {
                "nome_periodo_grupo": medicao.nome_periodo_grupo,
                "status": medicao.status.name,
                "justificativa": self.get_justificativa(medicao),
                "valores": valores,
                "valor_total": valor_total,
            }
            if escola.eh_cei or (
                escola.eh_cemei
                and ("Infantil" not in medicao.nome_periodo_grupo)
                and ("Solicitações" not in medicao.nome_periodo_grupo)
            ):
                dict_retorno["quantidade_alunos"] = sum(v["valor"] for v in valores)
            retorno.append(dict_retorno)
        return Response({"results": retorno}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
        url_path="periodos-escola-cemei-com-alunos-emei",
        permission_classes=[UsuarioEscolaTercTotal],
    )
    def periodos_escola_cemei_com_alunos_emei(self, request):
        usuario = self.request.user
        escola = usuario.vinculo_atual.instituicao
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")
        retorno = []
        if escola.eh_cemei:
            logs = LogAlunosMatriculadosPeriodoEscola.objects.filter(
                escola=escola,
                criado_em__year=ano,
                criado_em__month=mes,
                tipo_turma=TipoTurma.REGULAR.name,
                quantidade_alunos__gt=0,
            )
            existe_emei = logs.filter(
                cei_ou_emei="EMEI", periodo_escolar__nome="INTEGRAL"
            ).exists()
            lista_periodos = list(
                set(logs.values_list("periodo_escolar__nome", flat=True))
            )
            if not existe_emei and "INTEGRAL" in lista_periodos:
                lista_periodos.remove("INTEGRAL")
            lista_periodos = sorted(f"Infantil {periodo}" for periodo in lista_periodos)

            ordem_personalizada = ordem_periodos(escola).get("EMEI", {})
            retorno = sorted(
                lista_periodos,
                key=lambda p: ordem_personalizada.get(p.replace("Infantil ", ""), 99),
            )
        return Response({"results": retorno}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="dre-aprova-solicitacao-medicao",
        permission_classes=[UsuarioDiretoriaRegional],
    )
    def dre_aprova_solicitacao_medicao(self, request, uuid=None):
        solicitacao_medicao_inicial = self.get_object()
        try:
            medicoes = solicitacao_medicao_inicial.medicoes.all()
            if medicoes.exclude(
                status=OcorrenciaMedicaoInicial.workflow_class.MEDICAO_APROVADA_PELA_DRE
            ).exists() or (
                solicitacao_medicao_inicial.tem_ocorrencia
                and solicitacao_medicao_inicial.ocorrencia.status
                not in [
                    OcorrenciaMedicaoInicial.workflow_class.MEDICAO_APROVADA_PELA_DRE,
                    OcorrenciaMedicaoInicial.workflow_class.OCORRENCIA_EXCLUIDA_PELA_ESCOLA,
                ]
            ):
                mensagem = "Erro: existe(m) pendência(s) de análise"
                return Response(
                    dict(detail=mensagem), status=status.HTTP_400_BAD_REQUEST
                )
            solicitacao_medicao_inicial.dre_aprova(user=request.user)
            acao = solicitacao_medicao_inicial.workflow_class.MEDICAO_APROVADA_PELA_DRE
            log = criar_log_aprovar_periodos_corrigidos(
                request.user, solicitacao_medicao_inicial, acao
            )
            if log:
                if not solicitacao_medicao_inicial.historico:
                    historico = [log]
                else:
                    historico = json.loads(solicitacao_medicao_inicial.historico)
                    historico.append(log)
                solicitacao_medicao_inicial.historico = json.dumps(historico)
                solicitacao_medicao_inicial.save()
            serializer = self.get_serializer(solicitacao_medicao_inicial)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="dre-solicita-correcao-medicao",
        permission_classes=[UsuarioDiretoriaRegional],
    )
    def dre_solicita_correcao_medicao(self, request, uuid=None):
        solicitacao_medicao_inicial = self.get_object()
        try:
            solicitacao_medicao_inicial.dre_pede_correcao(user=request.user)
            acao = (
                solicitacao_medicao_inicial.workflow_class.MEDICAO_CORRECAO_SOLICITADA
            )
            log = criar_log_solicitar_correcao_periodos(
                request.user, solicitacao_medicao_inicial, acao
            )
            if log:
                if not solicitacao_medicao_inicial.historico:
                    historico = [log]
                else:
                    historico = json.loads(solicitacao_medicao_inicial.historico)
                    historico.append(log)
                solicitacao_medicao_inicial.historico = json.dumps(historico)
                solicitacao_medicao_inicial.save()
            serializer = self.get_serializer(solicitacao_medicao_inicial)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="codae-aprova-solicitacao-medicao",
        permission_classes=[UsuarioCODAEGestaoAlimentacao],
    )
    def codae_aprova_solicitacao_medicao(self, request, uuid=None):
        solicitacao_medicao_inicial = self.get_object()
        try:
            medicoes = solicitacao_medicao_inicial.medicoes.all()
            if medicoes.exclude(
                status=OcorrenciaMedicaoInicial.workflow_class.MEDICAO_APROVADA_PELA_CODAE
            ).exists() or (
                solicitacao_medicao_inicial.tem_ocorrencia
                and solicitacao_medicao_inicial.ocorrencia.status
                not in [
                    OcorrenciaMedicaoInicial.workflow_class.MEDICAO_APROVADA_PELA_CODAE,
                    OcorrenciaMedicaoInicial.workflow_class.OCORRENCIA_EXCLUIDA_PELA_ESCOLA,
                ]
            ):
                mensagem = "Erro: existe(m) pendência(s) de análise"
                return Response(
                    dict(detail=mensagem), status=status.HTTP_400_BAD_REQUEST
                )
            solicitacao_medicao_inicial.codae_aprova_medicao(user=request.user)
            acao = (
                solicitacao_medicao_inicial.workflow_class.MEDICAO_APROVADA_PELA_CODAE
            )
            log = criar_log_aprovar_periodos_corrigidos(
                request.user, solicitacao_medicao_inicial, acao
            )
            if log:
                if not solicitacao_medicao_inicial.historico:
                    historico = [log]
                else:
                    historico = json.loads(solicitacao_medicao_inicial.historico)
                    historico.append(log)
                solicitacao_medicao_inicial.historico = json.dumps(historico)
                solicitacao_medicao_inicial.save()
            serializer = self.get_serializer(solicitacao_medicao_inicial)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="codae-solicita-correcao-medicao",
        permission_classes=[UsuarioCODAEGestaoAlimentacao],
    )
    def codae_solicita_correcao_medicao(self, request, uuid=None):
        solicitacao_medicao_inicial = self.get_object()
        try:
            solicitacao_medicao_inicial.codae_pede_correcao_medicao(user=request.user)
            acao = (
                solicitacao_medicao_inicial.workflow_class.MEDICAO_CORRECAO_SOLICITADA_CODAE
            )
            log = criar_log_solicitar_correcao_periodos(
                request.user, solicitacao_medicao_inicial, acao
            )
            if log:
                if not solicitacao_medicao_inicial.historico:
                    historico = [log]
                else:
                    historico = json.loads(solicitacao_medicao_inicial.historico)
                    historico.append(log)
                solicitacao_medicao_inicial.historico = json.dumps(historico)
                solicitacao_medicao_inicial.save()
            serializer = self.get_serializer(solicitacao_medicao_inicial)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="escola-corrige-medicao-para-dre",
        permission_classes=[
            UsuarioDiretorEscolaTercTotal | UsuarioEscolaTercTotalSemAlunosRegulares
        ],
    )
    def escola_corrige_medicao_para_dre(self, request, uuid=None):
        solicitacao_medicao_inicial = self.get_object()
        try:
            if (
                solicitacao_medicao_inicial.status
                == SolicitacaoMedicaoInicial.workflow_class.MEDICAO_CORRIGIDA_PELA_UE
            ):
                raise InvalidTransitionError(
                    "solicitação já está no status Corrigido para DRE"
                )
            solicitacao_medicao_inicial.ue_corrige(user=request.user)
            ValorMedicao.objects.filter(
                medicao__solicitacao_medicao_inicial=solicitacao_medicao_inicial
            ).update(habilitado_correcao=False)
            DiaParaCorrigir.objects.filter(
                medicao__solicitacao_medicao_inicial=solicitacao_medicao_inicial
            ).update(habilitado_correcao=False)
            serializer = self.get_serializer(solicitacao_medicao_inicial)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="escola-corrige-medicao-para-codae",
        permission_classes=[
            UsuarioDiretorEscolaTercTotal | UsuarioEscolaTercTotalSemAlunosRegulares
        ],
    )
    def escola_corrige_medicao_para_codae(self, request, uuid=None):
        solicitacao_medicao_inicial = self.get_object()
        try:
            status_medicao_corrigida_codae = (
                SolicitacaoMedicaoInicial.workflow_class.MEDICAO_CORRIGIDA_PARA_CODAE
            )
            if solicitacao_medicao_inicial.status == status_medicao_corrigida_codae:
                raise InvalidTransitionError(
                    "solicitação já está no status Corrigido para CODAE"
                )
            solicitacao_medicao_inicial.ue_corrige_medicao_para_codae(user=request.user)
            ValorMedicao.objects.filter(
                medicao__solicitacao_medicao_inicial=solicitacao_medicao_inicial
            ).update(habilitado_correcao=False)
            DiaParaCorrigir.objects.filter(
                medicao__solicitacao_medicao_inicial=solicitacao_medicao_inicial
            ).update(habilitado_correcao=False)
            serializer = self.get_serializer(solicitacao_medicao_inicial)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="ue-atualiza-ocorrencia",
        permission_classes=[
            UsuarioDiretorEscolaTercTotal | UsuarioEscolaTercTotalSemAlunosRegulares
        ],
    )
    def ue_atualiza_ocorrencia(self, request, uuid=None):
        solicitacao_medicao_inicial = self.get_object()
        status_ocorrencia = solicitacao_medicao_inicial.status
        status_correcao_solicitada_codae = (
            SolicitacaoMedicaoInicial.workflow_class.MEDICAO_CORRECAO_SOLICITADA_CODAE
        )
        try:
            anexos_processados = process_anexos_from_request(request)
            com_ocorrencias = request.data.get("com_ocorrencias", None)
            justificativa = request.data.get("justificativa", "")
            if com_ocorrencias == "true" and anexos_processados:
                solicitacao_medicao_inicial.com_ocorrencias = True
                atualizar_anexos_ocorrencia(
                    anexos_processados, solicitacao_medicao_inicial
                )
                if status_ocorrencia == status_correcao_solicitada_codae:
                    solicitacao_medicao_inicial.ocorrencia.ue_corrige_ocorrencia_para_codae(
                        user=request.user,
                        anexos=anexos_processados,
                        justificativa=justificativa,
                    )
                else:
                    solicitacao_medicao_inicial.ocorrencia.ue_corrige(
                        user=request.user,
                        anexos=anexos_processados,
                        justificativa=justificativa,
                    )
            else:
                solicitacao_medicao_inicial.com_ocorrencias = False
                solicitacao_medicao_inicial.ocorrencia.escola_exclui_ocorrencia(
                    user=request.user, justificativa=justificativa
                )
            solicitacao_medicao_inicial.save()
            serializer = self.get_serializer(solicitacao_medicao_inicial)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False,
        methods=["GET"],
        url_path="solicitacoes-lancadas",
        permission_classes=[UsuarioEscolaTercTotal],
    )
    def solicitacoes_lancadas(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        escola_uuid = request.query_params.get("escola")
        data_ano_anterior = datetime.date.today() - relativedelta(years=1)
        medicao_em_preenchimento = (
            SolicitacaoMedicaoInicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        )

        queryset = (
            queryset.filter(escola__uuid=escola_uuid)
            .annotate(
                mes_int=Cast("mes", output_field=IntegerField()),
                ano_int=Cast("ano", output_field=IntegerField()),
            )
            .filter(
                Q(ano=datetime.date.today().year)
                | Q(
                    ano_int=data_ano_anterior.year, mes_int__gte=data_ano_anterior.month
                )
            )
            .exclude(status=medicao_em_preenchimento)
        )

        serializer = SolicitacaoMedicaoInicialLancadaSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["GET"],
        url_path="ceu-gestao-frequencias-dietas",
        permission_classes=[UsuarioEscolaTercTotal],
    )
    def ceu_gestao_frequencias_dietas(self, request, uuid=None):
        solicitacao_medicao = self.get_object()
        valores_medicao = ValorMedicao.objects.filter(
            medicao__solicitacao_medicao_inicial=solicitacao_medicao,
            categoria_medicao__nome__icontains="DIETA ESPECIAL",
            nome_campo="frequencia",
        )
        return Response(
            ValorMedicaoSerializer(valores_medicao, many=True).data,
            status=status.HTTP_200_OK,
        )

    def _valida_sem_lancamentos(self, solicitacao):
        """
        Se a Solicitação de Medição Inicial não é sem lançamentos, não pode seguir este fluxo.
        """
        if not solicitacao.sem_lancamentos:
            raise ValidationError(
                "Solicitação Medição Inicial não pode voltar para ser preenchida novamente, pois possui lançamentos."
            )

    def _solicita_correcao_em_solicitacao(self, solicitacao, user, justificativa):
        """
        Altera o status da Solicitação de Medição Inicial sem lançamentos para ser preenchida novamente.
        """
        solicitacao.codae_pede_correcao_sem_lancamentos(
            user=user, justificativa=justificativa
        )

    def _solicita_correcao_em_medicoes(self, solicitacao, user, justificativa):
        """
        Altera os status das medições da Solicitação de Medição Inicial sem lançamentos para serem preenchidas novamente.
        """
        for medicao in solicitacao.medicoes.all():
            medicao.codae_pede_correcao_sem_lancamentos(
                user=user, justificativa=justificativa
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="codae-solicita-correcao-sem-lancamentos",
        permission_classes=[UsuarioMedicao],
    )
    def codae_solicita_correcao_sem_lancamentos(self, request, uuid=None):
        """
        CODAE (Medição) solicita correção de uma Solicitação de Medição Inicial sem lançamentos.
        A Solicitação será preenchida novamente.
        """
        try:
            solicitacao_medicao_inicial = self.get_object()
            self._valida_sem_lancamentos(solicitacao_medicao_inicial)
            justificativa = request.data.get("justificativa", "")
            self._solicita_correcao_em_solicitacao(
                solicitacao_medicao_inicial, request.user, justificativa
            )
            self._solicita_correcao_em_medicoes(
                solicitacao_medicao_inicial, request.user, justificativa
            )
            serializer = self.get_serializer(solicitacao_medicao_inicial)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SolicitacaoMedicaoInicial.DoesNotExist:
            return Response(
                {
                    "detail": "Solicitação Medição Inicial com o UUID informado não foi encontrado."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except (ValidationError, InvalidTransitionError) as e:
            return Response(
                dict(detail=str(e)),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="informacoes-basicas",
        permission_classes=[UsuarioEscolaTercTotal],
    )
    def atualiza_informacoes_basicas(self, request, uuid=None):
        solicitacao_medicao_inicial = self.get_object()
        try:
            serializer = InformacoesBasicasMedicaoInicialUpdateSerializer(
                solicitacao_medicao_inicial,
                data=request.data,
                context={"request": request},
                partial=True,
            )

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except (ValidationError, InvalidTransitionError) as e:
            return Response(
                dict(detail=str(e)),
                status=status.HTTP_400_BAD_REQUEST,
            )


class TipoContagemAlimentacaoViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = TipoContagemAlimentacao.objects.filter(ativo=True)
    serializer_class = TipoContagemAlimentacaoSerializer
    pagination_class = None


class CategoriaMedicaoViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = CategoriaMedicao.objects.filter(ativo=True)
    serializer_class = CategoriaMedicaoSerializer
    pagination_class = None


class ValorMedicaoViewSet(
    mixins.ListModelMixin, mixins.DestroyModelMixin, GenericViewSet
):
    lookup_field = "uuid"
    queryset = ValorMedicao.objects.all()
    serializer_class = ValorMedicaoSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = ValorMedicao.objects.all()
        nome_periodo_escolar = self.request.query_params.get(
            "nome_periodo_escolar", None
        )
        uuid_solicitacao_medicao = self.request.query_params.get(
            "uuid_solicitacao_medicao", None
        )
        nome_grupo = self.request.query_params.get("nome_grupo", None)
        uuid_medicao_periodo_grupo = self.request.query_params.get(
            "uuid_medicao_periodo_grupo", None
        )
        if nome_periodo_escolar:
            queryset = queryset.filter(
                medicao__periodo_escolar__nome=nome_periodo_escolar
            )
        if nome_grupo:
            queryset = queryset.filter(medicao__grupo__nome=nome_grupo)
        elif not uuid_medicao_periodo_grupo:
            queryset = queryset.filter(medicao__grupo__isnull=True)
        if uuid_solicitacao_medicao:
            queryset = queryset.filter(
                medicao__solicitacao_medicao_inicial__uuid=uuid_solicitacao_medicao
            )
        if uuid_medicao_periodo_grupo:
            queryset = queryset.filter(medicao__uuid=uuid_medicao_periodo_grupo)
        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = ValorMedicao.objects.get(uuid=kwargs.get("uuid"))
        medicao = instance.medicao
        self.perform_destroy(instance)
        if not medicao.valores_medicao.all().exists():
            medicao.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MedicaoViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    lookup_field = "uuid"
    queryset = Medicao.objects.all()

    def get_serializer_class(self):
        if self.action == "dre_aprova_medicao":
            return MedicaoSerializer
        return MedicaoCreateUpdateSerializer

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="dre-aprova-medicao",
        permission_classes=[UsuarioDiretoriaRegional],
    )
    def dre_aprova_medicao(self, request, uuid=None):
        medicao = self.get_object()
        try:
            medicao.dre_aprova(user=request.user)
            serializer = self.get_serializer(medicao)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="dre-pede-correcao-medicao",
        permission_classes=[UsuarioDiretoriaRegional],
    )
    def dre_pede_correcao_medicao(self, request, uuid=None):
        medicao = self.get_object()
        justificativa = request.data.get("justificativa", "")
        uuids_valores_medicao_para_correcao = request.data.get(
            "uuids_valores_medicao_para_correcao", []
        )
        dias_para_corrigir = request.data.get("dias_para_corrigir", [])
        try:
            medicao.valores_medicao.filter(
                uuid__in=uuids_valores_medicao_para_correcao
            ).update(habilitado_correcao=True)
            medicao.valores_medicao.exclude(
                uuid__in=uuids_valores_medicao_para_correcao
            ).update(habilitado_correcao=False)
            DiaParaCorrigir.cria_dias_para_corrigir(
                medicao, self.request.user, dias_para_corrigir
            )
            medicao.dre_pede_correcao(user=request.user, justificativa=justificativa)
            serializer = self.get_serializer(medicao)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="codae-aprova-periodo",
        permission_classes=[UsuarioCODAEGestaoAlimentacao],
    )
    def codae_aprova_periodo(self, request, uuid=None):
        medicao = self.get_object()
        try:
            medicao.codae_aprova_periodo(user=request.user)
            serializer = self.get_serializer(medicao)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="codae-pede-correcao-periodo",
        permission_classes=[UsuarioCODAEGestaoAlimentacao],
    )
    def codae_pede_correcao_periodo(self, request, uuid=None):
        medicao = self.get_object()
        justificativa = request.data.get("justificativa", "")
        uuids_valores_medicao_para_correcao = request.data.get(
            "uuids_valores_medicao_para_correcao", None
        )
        dias_para_corrigir = request.data.get("dias_para_corrigir", [])
        try:
            ValorMedicao.objects.filter(
                uuid__in=uuids_valores_medicao_para_correcao
            ).update(habilitado_correcao=True)
            DiaParaCorrigir.cria_dias_para_corrigir(
                medicao, self.request.user, dias_para_corrigir
            )
            medicao.codae_pede_correcao_periodo(
                user=request.user, justificativa=justificativa
            )
            serializer = self.get_serializer(medicao)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get_tipo_alimentacao(self, valor_medicao):
        tipo_alimentacao = None
        tipo_alimentacao_uuid = valor_medicao.get("tipo_alimentacao", None)
        if tipo_alimentacao_uuid:
            tipo_alimentacao = TipoAlimentacao.objects.get(uuid=tipo_alimentacao_uuid)
        return tipo_alimentacao

    def get_faixa_etaria(self, valor_medicao):
        faixa_etaria = None
        faixa_etaria_uuid = valor_medicao.get("faixa_etaria", None)
        if faixa_etaria_uuid:
            faixa_etaria = FaixaEtaria.objects.get(uuid=faixa_etaria_uuid)
        return faixa_etaria

    def get_nome_acao(self, medicao, status_codae):
        if medicao.status in status_codae:
            return (
                medicao.solicitacao_medicao_inicial.workflow_class.MEDICAO_CORRIGIDA_PARA_CODAE
            )
        else:
            return (
                medicao.solicitacao_medicao_inicial.workflow_class.MEDICAO_CORRIGIDA_PELA_UE
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="escola-corrige-medicao",
        permission_classes=[
            UsuarioDiretorEscolaTercTotal | UsuarioEscolaTercTotalSemAlunosRegulares
        ],
    )
    def escola_corrige_medicao(self, request, uuid=None):
        medicao = self.get_object()
        status_correcao_solicitada_codae = (
            SolicitacaoMedicaoInicial.workflow_class.MEDICAO_CORRECAO_SOLICITADA_CODAE
        )
        status_medicao_corrigida_para_codae = (
            SolicitacaoMedicaoInicial.workflow_class.MEDICAO_CORRIGIDA_PARA_CODAE
        )
        status_codae = [
            status_correcao_solicitada_codae,
            status_medicao_corrigida_para_codae,
        ]
        try:
            acao = self.get_nome_acao(medicao, status_codae)
            log_alteracoes_escola_corrige_periodo(
                request.user, medicao, acao, request.data
            )
            for valor_medicao in request.data:
                if not valor_medicao:
                    continue
                dia = int(valor_medicao.get("dia", ""))
                mes = int(medicao.solicitacao_medicao_inicial.mes)
                ano = int(medicao.solicitacao_medicao_inicial.ano)
                semana = ValorMedicao.get_week_of_month(ano, mes, dia)
                categoria_medicao_qs = CategoriaMedicao.objects.filter(
                    id=valor_medicao.get("categoria_medicao", None)
                )
                tipo_alimentacao = self.get_tipo_alimentacao(valor_medicao)
                faixa_etaria = self.get_faixa_etaria(valor_medicao)
                infantil_ou_fundamental = valor_medicao.get(
                    "infantil_ou_fundamental", "N/A"
                )
                ValorMedicao.objects.update_or_create(
                    medicao=medicao,
                    dia=valor_medicao.get("dia", ""),
                    semana=semana,
                    nome_campo=valor_medicao.get("nome_campo", ""),
                    categoria_medicao=categoria_medicao_qs.first(),
                    tipo_alimentacao=tipo_alimentacao,
                    faixa_etaria=faixa_etaria,
                    infantil_ou_fundamental=infantil_ou_fundamental,
                    defaults={
                        "medicao": medicao,
                        "dia": valor_medicao.get("dia", ""),
                        "semana": semana,
                        "valor": valor_medicao.get("valor", ""),
                        "nome_campo": valor_medicao.get("nome_campo", ""),
                        "categoria_medicao": categoria_medicao_qs.first(),
                        "tipo_alimentacao": tipo_alimentacao,
                        "faixa_etaria": faixa_etaria,
                        "habilitado_correcao": True,
                        "infantil_ou_fundamental": infantil_ou_fundamental,
                    },
                )
            medicao.valores_medicao.filter(valor=-1).delete()
            if medicao.status in status_codae:
                medicao.ue_corrige_periodo_grupo_para_codae(user=request.user)
            else:
                medicao.ue_corrige(user=request.user)
            serializer = self.get_serializer(medicao)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get_day_from_date(self, data):
        return datetime.date.strftime(data, "%d")

    @action(
        detail=False,
        methods=["GET"],
        url_path="feriados-no-mes",
        permission_classes=[
            UsuarioEscolaTercTotal
            | UsuarioDiretoriaRegional
            | UsuarioCODAEGestaoAlimentacao
        ],
    )
    def feriados_no_mes(self, request, uuid=None):
        mes = request.query_params.get("mes", "")
        ano = request.query_params.get("ano", "")

        retorno = [
            self.get_day_from_date(h[0])
            for h in calendario.holidays(int(ano))
            if h[0].month == int(mes) and h[0].year == int(ano)
        ]
        return Response({"results": retorno}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
        url_path="feriados-no-mes-com-nome",
        permission_classes=[
            UsuarioEscolaTercTotal
            | UsuarioDiretoriaRegional
            | UsuarioCODAEGestaoAlimentacao
            | UsuarioCODAENutriManifestacao
            | UsuarioCODAEGabinete
            | UsuarioDinutreDiretoria
            | UsuarioEmpresaTerceirizada
            | UsuarioSupervisaoNutricao
        ],
    )
    def feriados_no_mes_com_nome(self, request, uuid=None):
        mes = request.query_params.get("mes", "")
        ano = request.query_params.get("ano", "")

        lista_feriados = []
        for h in calendario.holidays(int(ano)):
            if h[0].month == int(mes) and h[0].year == int(ano):
                try:
                    lista_feriados.append(
                        {
                            "dia": self.get_day_from_date(h[0]),
                            "feriado": TRADUCOES_FERIADOS[h[1]],
                        }
                    )
                except KeyError:
                    lista_feriados.append(
                        {"dia": self.get_day_from_date(h[0]), "feriado": h[1]}
                    )

        return Response({"results": lista_feriados}, status=status.HTTP_200_OK)


class OcorrenciaViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    lookup_field = "uuid"
    queryset = OcorrenciaMedicaoInicial.objects.all()

    def get_serializer_class(self):
        return OcorrenciaMedicaoInicialSerializer

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="dre-pede-correcao-ocorrencia",
    )
    def dre_pede_correcao_ocorrencia(self, request, uuid=None):
        object = self.get_object()
        ocorrencia = object.solicitacao_medicao_inicial.ocorrencia
        justificativa = request.data.get("justificativa", "")
        try:
            ocorrencia.dre_pede_correcao(user=request.user, justificativa=justificativa)
            serializer = self.get_serializer(
                ocorrencia.solicitacao_medicao_inicial.ocorrencia
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="codae-pede-correcao-ocorrencia",
    )
    def codae_pede_correcao_ocorrencia(self, request, uuid=None):
        object = self.get_object()
        ocorrencia = object.solicitacao_medicao_inicial.ocorrencia
        justificativa = request.data.get("justificativa", "")
        try:
            ocorrencia.codae_pede_correcao_ocorrencia(
                user=request.user, justificativa=justificativa
            )
            serializer = self.get_serializer(
                ocorrencia.solicitacao_medicao_inicial.ocorrencia
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="dre-aprova-ocorrencia",
    )
    def dre_aprova_ocorrencia(self, request, uuid=None):
        object = self.get_object()
        ocorrencia = object.solicitacao_medicao_inicial.ocorrencia
        try:
            ocorrencia.dre_aprova(user=request.user)
            serializer = self.get_serializer(
                ocorrencia.solicitacao_medicao_inicial.ocorrencia
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="codae-aprova-ocorrencia",
        permission_classes=[UsuarioCODAEGestaoAlimentacao],
    )
    def codae_aprova_ocorrencia(self, request, uuid=None):
        object = self.get_object()
        ocorrencia = object.solicitacao_medicao_inicial.ocorrencia
        try:
            ocorrencia.codae_aprova_ocorrencia(user=request.user)
            serializer = self.get_serializer(
                ocorrencia.solicitacao_medicao_inicial.ocorrencia
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False,
        methods=["POST"],
        url_path="gera-ocorrencia-para-correcao",
        permission_classes=[
            UsuarioDiretoriaRegional
            | UsuarioCODAEGestaoAlimentacao
            | UsuarioCODAENutriManifestacao
            | UsuarioCODAEGabinete
            | UsuarioDinutreDiretoria
            | UsuarioEmpresaTerceirizada
            | UsuarioSupervisaoNutricao
        ],
    )
    @transaction.atomic
    def gera_ocorrencia_para_correcao(self, request):
        solicitacao_uuid = request.data.get("solicitacao_medicao_uuid")

        try:
            solicitacao_medicao_inicial = SolicitacaoMedicaoInicial.objects.get(
                uuid=solicitacao_uuid
            )

            ocorrencia = getattr(solicitacao_medicao_inicial, "ocorrencia", None)
            if ocorrencia:
                return Response(
                    {"medicao": "Já possui ocorrência associada"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ocorrencia = OcorrenciaMedicaoInicial.objects.create(
                solicitacao_medicao_inicial=solicitacao_medicao_inicial
            )

            usuario = request.user
            justificativa = request.data.get("justificativa", "")

            if usuario.tipo_usuario == "diretoriaregional":
                ocorrencia.dre_pede_correcao(user=usuario, justificativa=justificativa)
            else:
                ocorrencia.codae_pede_correcao_ocorrencia(
                    user=usuario, justificativa=justificativa
                )

        except SolicitacaoMedicaoInicial.DoesNotExist:
            return Response(
                {"solicitacao_medicao_uuid": "Medição não encontrada"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except InvalidTransitionError as e:
            return Response(
                {"detail": f"Erro de transição de estado: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(ocorrencia)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AlimentacaoLancamentoEspecialViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = AlimentacaoLancamentoEspecial.objects.filter(ativo=True)
    serializer_class = AlimentacaoLancamentoEspecialSerializer
    pagination_class = None


class PermissaoLancamentoEspecialViewSet(ModelViewSet):
    lookup_field = "uuid"
    permission_classes = [UsuarioCODAEGestaoAlimentacao]
    queryset = PermissaoLancamentoEspecial.objects.all()
    serializer_class = PermissaoLancamentoEspecialSerializer
    pagination_class = CustomPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ["escola__uuid"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PermissaoLancamentoEspecialCreateUpdateSerializer
        return PermissaoLancamentoEspecialSerializer

    @action(
        detail=False,
        methods=["GET"],
        url_path="escolas-permissoes-lancamentos-especiais",
    )
    def escolas_permissoes_lancamentos_especiais(self, request):
        try:
            escolas = []
            for permissao in PermissaoLancamentoEspecial.objects.order_by().distinct(
                "escola"
            ):
                escolas.append(
                    {"nome": permissao.escola.nome, "uuid": permissao.escola.uuid}
                )

            return Response(
                {"results": sorted(escolas, key=lambda e: e["nome"])},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                dict(detail=f"Erro: {e}"), status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=["GET"],
        url_path="permissoes-lancamentos-especiais-mes-ano-por-periodo",
        permission_classes=[
            UsuarioEscolaTercTotal
            | UsuarioDiretoriaRegional
            | UsuarioCODAENutriManifestacao
            | UsuarioCODAEGestaoAlimentacao
            | UsuarioCODAEGabinete
            | UsuarioDinutreDiretoria
            | UsuarioEmpresaTerceirizada
            | UsuarioSupervisaoNutricao
        ],
    )
    def permissoes_lancamentos_especiais_mes_ano_por_periodo(self, request):
        escola_uuid = request.query_params.get("escola_uuid")
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")
        nome_periodo_escolar = request.query_params.get("nome_periodo_escolar")
        primeiro_dia_mes = datetime.date(int(ano), int(mes), 1)
        ultimo_dia_mes = get_ultimo_dia_mes(primeiro_dia_mes)

        query_set = PermissaoLancamentoEspecial.objects.filter(
            escola__uuid=escola_uuid,
            periodo_escolar__nome=nome_periodo_escolar,
            data_inicial__lte=ultimo_dia_mes,
        ).filter(Q(data_final__gte=primeiro_dia_mes) | Q(data_final=None))

        permissoes_por_dia = []
        alimentacoes_lancamentos_especiais_names = []
        for permissao in query_set:
            dia_inicial = 1
            dia_final = calendar.monthrange(int(ano), int(mes))[1]
            if permissao.data_inicial.month == int(mes):
                dia_inicial = permissao.data_inicial.day
            if permissao.data_final and permissao.data_final.month == int(mes):
                dia_final = permissao.data_final.day
            nome_periodo_escolar = permissao.periodo_escolar.nome
            permissao_id_externo = permissao.id_externo
            alimentacoes = [
                alimentacao.name
                for alimentacao in permissao.alimentacoes_lancamento_especial.all()
            ]
            alimentacoes_lancamentos_especiais_names += alimentacoes
            for dia in range(dia_inicial, dia_final + 1):
                permissoes_por_dia.append(
                    {
                        "dia": f"{dia:02d}",
                        "periodo": nome_periodo_escolar,
                        "alimentacoes": alimentacoes,
                        "permissao_id_externo": permissao_id_externo,
                    }
                )
        alimentacoes_lancamentos_especiais = (
            get_dict_alimentacoes_lancamentos_especiais(
                alimentacoes_lancamentos_especiais_names
            )
        )
        data = {
            "results": {
                "alimentacoes_lancamentos_especiais": sorted(
                    alimentacoes_lancamentos_especiais,
                    key=lambda k: ORDEM_NAME_LANCAMENTOS_ESPECIAIS[k["name"]],
                ),
                "permissoes_por_dia": permissoes_por_dia,
                "data_inicio_permissoes": (
                    f'{min([permissao["dia"] for permissao in permissoes_por_dia])}/{mes}/{ano}'
                    if permissoes_por_dia
                    else None
                ),
            }
        }

        return Response(data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="periodos-permissoes-lancamentos-especiais-mes-ano",
        permission_classes=[UsuarioEscolaTercTotal],
    )
    def periodos_permissoes_lancamentos_especiais_mes_ano(self, request):
        escola_uuid = request.query_params.get("escola_uuid")
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")

        query_set = PermissaoLancamentoEspecial.objects.filter(
            escola__uuid=escola_uuid,
            data_inicial__month__lte=mes,
            data_inicial__year=ano,
        )
        periodos = list(set(query_set.values_list("periodo_escolar__nome", flat=True)))
        alimentacoes_por_periodo = []
        for periodo in periodos:
            permissoes = query_set.filter(periodo_escolar__nome=periodo)
            listas_alimentacoes = [
                list(
                    set(
                        permissao.alimentacoes_lancamento_especial.values_list(
                            "nome", flat=True
                        )
                    )
                )
                for permissao in permissoes
            ]
            alimentacoes = list(
                set(
                    [
                        alimentacao
                        for lista in listas_alimentacoes
                        for alimentacao in lista
                    ]
                )
            )
            alimentacoes_por_periodo.append(
                {
                    "periodo": periodo,
                    "alimentacoes": alimentacoes,
                }
            )
        data = {"results": alimentacoes_por_periodo}

        return Response(data)


class DiasParaCorrigirViewSet(mixins.ListModelMixin, GenericViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = DiaParaCorrigir.objects.filter(habilitado_correcao=True)
    serializer_class = DiaParaCorrigirSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = DiaParaCorrecaoFilter
    pagination_class = None


class EmpenhoViewSet(ModelViewSet):
    lookup_field = "uuid"
    permission_classes = [UsuarioCODAEGestaoAlimentacao]
    queryset = Empenho.objects.all()
    serializer_class = EmpenhoSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = EmpenhoFilter
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return EmpenhoCreateUpdateSerializer
        return EmpenhoSerializer


class RelatoriosViewSet(ViewSet):
    permission_classes = [
        UsuarioEscolaTercTotal
        | UsuarioDiretoriaRegional
        | UsuarioCODAEGestaoAlimentacao
        | UsuarioCODAENutriManifestacao
        | UsuarioCODAEGabinete
        | UsuarioDinutreDiretoria
        | UsuarioEmpresaTerceirizada
        | UsuarioSupervisaoNutricao
    ]

    @action(detail=False, url_name="relatorio-adesao", url_path="relatorio-adesao")
    def relatorio_adesao(self, request: Request):
        query_params = request.query_params
        try:
            valida_parametros_periodo_lancamento(query_params)
            resultados = obtem_resultados(query_params)

            return Response(data=resultados, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                dict(detail=e.messages[0]), status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return Response(
                data={"detail": "Verifique os parâmetros e tente novamente"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False,
        url_name="relatorio-adesao_exportar-xlsx",
        url_path="relatorio-adesao/exportar-xlsx",
    )
    def relatorio_adesao_exportar_xlsx(self, request: Request):
        query_params = request.query_params
        try:
            valida_parametros_periodo_lancamento(query_params)
            resultados = obtem_resultados(query_params)

            query_params_dict = query_params.dict()

            if query_params.get("lotes[]"):
                query_params_dict["lotes"] = query_params.getlist("lotes[]")

            exporta_relatorio_adesao_para_xlsx.delay(
                user=request.user.get_username(),
                nome_arquivo="relatorio-adesao.xlsx",
                resultados=resultados,
                query_params=query_params_dict,
            )

            return Response(
                data={
                    "detail": "Solicitação de geração de arquivo recebida com sucesso."
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                dict(detail=e.messages[0]), status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return Response(
                data={"detail": "Verifique os parâmetros e tente novamente"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False,
        url_name="relatorio-adesao_exportar-pdf",
        url_path="relatorio-adesao/exportar-pdf",
    )
    def relatorio_adesao_exportar_pdf(self, request: Request):
        query_params = request.query_params
        try:
            valida_parametros_periodo_lancamento(query_params)
            resultados = obtem_resultados(query_params)
            query_params_dict = query_params.dict()

            if query_params.get("lotes[]"):
                query_params_dict["lotes"] = query_params.getlist("lotes[]")

            exporta_relatorio_adesao_para_pdf.delay(
                user=request.user.get_username(),
                nome_arquivo="relatorio-adesao.pdf",
                resultados=resultados,
                query_params=query_params_dict,
            )

            return Response(
                data={
                    "detail": "Solicitação de geração de arquivo recebida com sucesso."
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                dict(detail=e.messages[0]), status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return Response(
                data={"detail": "Verifique os parâmetros e tente novamente"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ClausulaDeDescontoViewSet(ModelViewSet):
    lookup_field = "uuid"
    permission_classes = [UsuarioCODAEGestaoAlimentacao]
    queryset = ClausulaDeDesconto.objects.all()
    serializer_class = ClausulaDeDescontoSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ClausulaDeDescontoFilter
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ClausulaDeDescontoCreateUpdateSerializer
        return ClausulaDeDescontoSerializer


class ParametrizacaoFinanceiraViewSet(ModelViewSet):
    lookup_field = "uuid"
    permission_classes = [UsuarioMedicao]
    queryset = ParametrizacaoFinanceira.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ParametrizacaoFinanceiraFilter
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ParametrizacaoFinanceiraWriteModelSerializer
        return ParametrizacaoFinanceiraSerializer

    @action(
        detail=False,
        methods=["GET"],
        url_path="dados-parametrizacao-financeira/(?P<uuid_parametrizacao_financeira>[^/.]+)",
        permission_classes=[UsuarioMedicao],
    )
    def dados_parametrizacao(self, request, uuid_parametrizacao_financeira):
        parametrizacao = get_object_or_404(
            ParametrizacaoFinanceira, uuid=uuid_parametrizacao_financeira
        )
        serializer = DadosParametrizacaoFinanceiraSerializer(parametrizacao)
        return Response(serializer.data)


class RelatorioFinanceiroViewSet(ModelViewSet):
    lookup_field = "uuid"
    permission_classes = [UsuarioMedicao]
    queryset = RelatorioFinanceiro.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RelatorioFinanceiroFilter
    pagination_class = CustomPagination
    serializer_class = RelatorioFinanceiroSerializer

    @action(
        detail=False,
        methods=["GET"],
        url_path="relatorio-consolidado/(?P<uuid_relatorio_financeiro>[^/.]+)",
        permission_classes=[UsuarioMedicao],
    )
    def relatorio_consolidado(self, _, uuid_relatorio_financeiro):
        try:
            relatorio_financeiro = RelatorioFinanceiro.objects.get(
                uuid=uuid_relatorio_financeiro
            )
            parametrizacao = ParametrizacaoFinanceira.objects.filter(
                lote=relatorio_financeiro.lote,
                tipos_unidades__in=relatorio_financeiro.grupo_unidade_escolar.tipos_unidades.all(),
            ).first()
            if not parametrizacao:
                return Response(
                    {
                        "Erro": "Não foi encontrada parametrização financeira para o tipo de unidade e lote do relatório financeiro."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            response = {
                **ParametrizacaoFinanceiraSerializer(parametrizacao).data,
                "lote": parametrizacao.lote.uuid,
                "grupo_unidade_escolar": relatorio_financeiro.grupo_unidade_escolar.uuid,
                "mes_ano": f"{relatorio_financeiro.mes}_{relatorio_financeiro.ano}",
            }
            return Response(
                data=response,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"Erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)
