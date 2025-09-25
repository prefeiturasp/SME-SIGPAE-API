import json
import uuid as uuid_generator
from copy import deepcopy
from datetime import date, datetime

from django.core.exceptions import ValidationError as coreValidation
from django.db import transaction
from django.db.models import Case, CharField, Count, F, Q, Value, When
from django.forms import ValidationError
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from xworkflows import InvalidTransitionError

from sme_sigpae_api.dados_comuns.api.paginations import HistoricoDietasPagination
from sme_sigpae_api.dieta_especial.gera_historico_protocolo import (
    atualiza_historico_protocolo,
)

from ...dados_comuns import constants
from ...dados_comuns.fluxo_status import DietaEspecialWorkflow
from ...dados_comuns.models import LogSolicitacoesUsuario
from ...dados_comuns.permissions import (
    PermissaoHistoricoDietasEspeciais,
    PermissaoParaRecuperarDietaEspecial,
    PermissaoRelatorioDietasEspeciais,
    PermissaoRelatorioRecreioNasFerias,
    UsuarioCODAEDietaEspecial,
    UsuarioEmpresaGenerico,
    UsuarioEscolaDiretaParceira,
    UsuarioEscolaTercTotal,
)
from ...dados_comuns.services import enviar_email_codae_atualiza_protocolo
from ...dieta_especial.tasks import gera_pdf_relatorio_dieta_especial_async
from ...escola.models import (
    Aluno,
    DiretoriaRegional,
    EscolaPeriodoEscolar,
    Lote,
    TipoGestao,
)
from ...escola.services import NovoSGPServicoLogado
from ...paineis_consolidados.api.constants import FILTRO_CODIGO_EOL_ALUNO
from ...relatorios.relatorios import (
    relatorio_dieta_especial,
    relatorio_dieta_especial_protocolo,
    relatorio_quantitativo_classificacao_dieta_especial,
    relatorio_quantitativo_diag_dieta_especial,
    relatorio_quantitativo_diag_dieta_especial_somente_dietas_ativas,
    relatorio_quantitativo_solic_dieta_especial,
)
from ...terceirizada.models import Contrato, Edital
from ..forms import (
    NegaDietaEspecialForm,
    PanoramaForm,
    RelatorioDietaForm,
    RelatorioQuantitativoSolicDietaEspForm,
    SolicitacoesAtivasInativasPorAlunoForm,
)
from ..models import (
    AlergiaIntolerancia,
    Alimento,
    Anexo,
    ClassificacaoDieta,
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
    MotivoAlteracaoUE,
    MotivoNegacao,
    ProtocoloPadraoDietaEspecial,
    SolicitacaoDietaEspecial,
    SubstituicaoAlimento,
    TipoContagem,
)
from ..tasks import (
    gera_pdf_relatorio_dietas_especiais_terceirizadas_async,
    gera_pdf_relatorio_historico_dietas_especiais_async,
    gera_pdf_relatorio_recreio_nas_ferias_async,
    gera_xlsx_relatorio_dietas_especiais_terceirizadas_async,
    gera_xlsx_relatorio_historico_dietas_especiais_async,
    gera_xlsx_relatorio_recreio_nas_ferias_async,
)
from ..utils import (
    ProtocoloPadraoPagination,
    RelatorioPagination,
    filtra_relatorio_recreio_nas_ferias,
    filtrar_alunos_com_dietas_nos_status_e_rastro_escola,
    gera_dicionario_historico_dietas,
    gerar_filtros_relatorio_historico,
    trata_lotes_dict_duplicados,
)
from .filters import (
    AlimentoFilter,
    DietaEspecialFilter,
    LogQuantidadeDietasEspeciaisFilter,
    MotivoNegacaoFilter,
)
from .serializers import (
    AlergiaIntoleranciaSerializer,
    AlimentoSerializer,
    ClassificacaoDietaSerializer,
    LogQuantidadeDietasAutorizadasCEISerializer,
    LogQuantidadeDietasAutorizadasSerializer,
    MotivoAlteracaoUESerializer,
    MotivoNegacaoSerializer,
    PanoramaSerializer,
    ProtocoloPadraoDietaEspecialSerializer,
    ProtocoloPadraoDietaEspecialSimplesSerializer,
    RelatorioQuantitativoSolicDietaEspSerializer,
    SolicitacaoDietaEspecialAutorizarSerializer,
    SolicitacaoDietaEspecialRecreioNasFeriasSerializer,
    SolicitacaoDietaEspecialRelatorioTercSerializer,
    SolicitacaoDietaEspecialSerializer,
    SolicitacaoDietaEspecialSimplesSerializer,
    SolicitacaoDietaEspecialUpdateSerializer,
    SolicitacoesAtivasInativasPorAlunoSerializer,
    TipoContagemSerializer,
    UnidadeEducacionalSerializer,
)
from .serializers_create import (
    AlteracaoUESerializer,
    ProtocoloPadraoDietaEspecialSerializerCreate,
    SolicitacaoDietaEspecialCreateSerializer,
)


class SolicitacaoDietaEspecialViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    lookup_field = "uuid"
    permission_classes = (IsAuthenticated,)
    queryset = SolicitacaoDietaEspecial.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = DietaEspecialFilter

    def get_queryset(self):
        if self.action in [
            "relatorio_dieta_especial",
            "imprime_relatorio_dieta_especial",
        ]:
            return self.queryset.select_related(
                "rastro_escola__diretoria_regional"
            ).order_by("criado_em")
        if self.action in ["relatorio_dieta_especial_terceirizada"]:
            return self.queryset.select_related("rastro_terceirizada").order_by(
                "-criado_em"
            )
        return super().get_queryset()

    def get_permissions(self):  # noqa C901
        if self.action == "list":
            self.permission_classes = (
                IsAuthenticated,
                PermissaoParaRecuperarDietaEspecial,
            )
        elif self.action == "update":
            self.permission_classes = (IsAdminUser, UsuarioCODAEDietaEspecial)
        elif self.action == "retrieve":
            self.permission_classes = (
                IsAuthenticated,
                PermissaoParaRecuperarDietaEspecial,
            )
        elif self.action == "create":
            self.permission_classes = [
                UsuarioEscolaTercTotal | UsuarioEscolaDiretaParceira
            ]
        elif self.action in [
            "imprime_relatorio_dieta_especial",
        ]:
            self.permission_classes = (
                IsAuthenticated,
                PermissaoParaRecuperarDietaEspecial,
            )
        elif self.action == "relatorio_dieta_especial_terceirizada":
            self.permission_classes = (
                IsAuthenticated,
                PermissaoRelatorioDietasEspeciais,
            )
        return super(SolicitacaoDietaEspecialViewSet, self).get_permissions()

    def get_serializer_class(self):  # noqa C901
        if self.action == "create":
            return SolicitacaoDietaEspecialCreateSerializer
        elif self.action in ["autorizar", "atualiza_protocolo"]:
            return SolicitacaoDietaEspecialAutorizarSerializer
        elif self.action in ["update", "partial_update"]:
            return SolicitacaoDietaEspecialUpdateSerializer
        elif self.action in [
            "relatorio_quantitativo_solic_dieta_esp",
            "relatorio_quantitativo_diag_dieta_esp",
            "relatorio_quantitativo_classificacao_dieta_esp",
        ]:
            return RelatorioQuantitativoSolicDietaEspSerializer
        elif self.action == "relatorio_dieta_especial":
            return SolicitacaoDietaEspecialSimplesSerializer
        elif self.action == "relatorio_dieta_especial_terceirizada":
            return SolicitacaoDietaEspecialRelatorioTercSerializer
        elif self.action == "panorama_escola":
            return PanoramaSerializer
        elif self.action == "alteracao_ue":
            return AlteracaoUESerializer
        elif self.action == "relatorio-historico-dieta-especial":
            return UnidadeEducacionalSerializer
        elif self.action == "relatorio_recreio_nas_ferias":
            return SolicitacaoDietaEspecialRecreioNasFeriasSerializer
        return SolicitacaoDietaEspecialSerializer

    def atualiza_solicitacao(self, solicitacao, request):
        texto_html = atualiza_historico_protocolo(solicitacao, request.data)
        if (
            solicitacao.aluno.possui_dieta_especial_ativa
            and not solicitacao.tipo_solicitacao == "ALTERACAO_UE"
        ):
            solicitacao.aluno.inativar_dieta_especial()
        if not solicitacao.tipo_solicitacao == "ALTERACAO_UE":
            serializer = self.get_serializer()
            serializer.update(solicitacao, request.data)
            solicitacao.ativo = True
        self.salva_log_transicao(solicitacao, request.user, texto_html)
        if solicitacao.aluno.escola:
            enviar_email_codae_atualiza_protocolo(solicitacao)
        if not solicitacao.data_inicio:
            solicitacao.data_inicio = datetime.now().strftime("%Y-%m-%d")
            solicitacao.save()

    def salva_log_transicao(self, solicitacao, user, justificativa):
        solicitacao.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_ATUALIZOU_PROTOCOLO,
            usuario=user,
            justificativa=justificativa,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path=f"solicitacoes-aluno/{FILTRO_CODIGO_EOL_ALUNO}",
    )
    def solicitacoes_vigentes(self, request, codigo_eol_aluno=None):
        solicitacoes = (
            SolicitacaoDietaEspecial.objects.filter(aluno__codigo_eol=codigo_eol_aluno)
            .exclude(status=SolicitacaoDietaEspecial.workflow_class.CODAE_A_AUTORIZAR)
            .order_by("-criado_em")
        )
        page = self.paginate_queryset(solicitacoes)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=("GET",),
        url_path="solicitacoes-aluno-nao-matriculado",
    )
    def solicitacoes_vigentes_aluno_nao_matriculado(self, request):
        try:
            codigo_eol_escola = request.query_params.get("codigo_eol_escola", None)
            nome_aluno = request.query_params.get("nome_aluno", False)
            if not codigo_eol_escola:
                raise ValidationError(
                    "`codigo_eol_escola` como query_param é obrigatório"
                )
            if not nome_aluno:
                raise ValidationError("`nome_aluno` como query_param é obrigatório")
            solicitacoes = (
                SolicitacaoDietaEspecial.objects.filter(
                    aluno__nao_matriculado=True,
                    escola_destino__codigo_eol=codigo_eol_escola,
                    aluno__nome=nome_aluno,
                )
                .exclude(
                    status=SolicitacaoDietaEspecial.workflow_class.CODAE_A_AUTORIZAR
                )
                .order_by("-criado_em")
            )
            page = self.paginate_queryset(solicitacoes)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        except ValidationError as e:
            return Response(e, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    @action(
        detail=True, methods=["patch"], permission_classes=(UsuarioCODAEDietaEspecial,)
    )
    def autorizar(self, request, uuid=None):  # noqa C901
        solicitacao = self.get_object()
        if (
            solicitacao.aluno.possui_dieta_especial_ativa
            and solicitacao.tipo_solicitacao == "COMUM"
        ):
            solicitacao.aluno.inativar_dieta_especial()
        serializer = self.get_serializer()
        try:
            if solicitacao.tipo_solicitacao != "ALTERACAO_UE":
                serializer.update(solicitacao, request.data)
                solicitacao.ativo = True
            solicitacao.codae_autoriza(user=request.user)
            if not solicitacao.data_inicio:
                solicitacao.data_inicio = datetime.now().strftime("%Y-%m-%d")
                solicitacao.save()
            return Response(
                {"detail": "Autorização de Dieta Especial realizada com sucesso!"}
            )
        except InvalidTransitionError as e:
            return Response(
                {"detail": f"Erro na transição de estado {e}"},
                status=HTTP_400_BAD_REQUEST,
            )
        except serializers.ValidationError as e:
            return Response(
                {"detail": f"Dados inválidos {e}"}, status=HTTP_400_BAD_REQUEST
            )

    @transaction.atomic
    @action(
        detail=True,
        methods=["patch"],
        url_path=constants.CODAE_ATUALIZA_PROTOCOLO,
        permission_classes=(UsuarioCODAEDietaEspecial,),
    )
    def atualiza_protocolo(self, request, uuid=None):
        solicitacao = self.get_object()
        try:
            self.atualiza_solicitacao(solicitacao, request)
            return Response({"detail": "Edição realizada com sucesso!"})
        except serializers.ValidationError as e:
            return Response(
                {"detail": f"Dados inválidos {e}"}, status=HTTP_400_BAD_REQUEST
            )
        except coreValidation as e:
            return Response(
                dict(detail=e.messages[0]), status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=["POST"],
        url_path=constants.ESCOLA_SOLICITA_INATIVACAO,
        permission_classes=[UsuarioEscolaTercTotal | UsuarioEscolaDiretaParceira],
    )
    def escola_solicita_inativacao(self, request, uuid=None):
        # TODO: colocar essa lógica dentro de um serializer
        dieta_cancelada = self.get_object()
        solicitacoes_de_cancelamento = SolicitacaoDietaEspecial.objects.filter(
            tipo_solicitacao="CANCELAMENTO_DIETA",
            dieta_alterada=dieta_cancelada,
            status=SolicitacaoDietaEspecial.workflow_class.ESCOLA_SOLICITOU_INATIVACAO,
        )
        if solicitacoes_de_cancelamento:
            return Response(
                dict(
                    detail="Já existe uma solicitação de cancelamento para essa dieta"
                ),
                status=HTTP_400_BAD_REQUEST,
            )
        justificativa = request.data.get("justificativa", "")
        substituicoes = SubstituicaoAlimento.objects.filter(
            solicitacao_dieta_especial=dieta_cancelada
        )
        anexos = Anexo.objects.filter(solicitacao_dieta_especial=dieta_cancelada)
        solicitacao_cancelamento = deepcopy(dieta_cancelada)
        solicitacao_cancelamento.id = None
        solicitacao_cancelamento.status = None
        solicitacao_cancelamento.ativo = False
        solicitacao_cancelamento.uuid = uuid_generator.uuid4()
        solicitacao_cancelamento.tipo_solicitacao = "CANCELAMENTO_DIETA"
        solicitacao_cancelamento.dieta_alterada = dieta_cancelada
        solicitacao_cancelamento.save()
        solicitacao_cancelamento.alergias_intolerancias.add(
            *dieta_cancelada.alergias_intolerancias.all()
        )
        solicitacao_cancelamento.cria_anexos_inativacao(request.data.get("anexos"))
        solicitacao_cancelamento.inicia_fluxo_inativacao(
            user=request.user, justificativa=justificativa
        )
        for substituicao in substituicoes:
            substituicao_cancelamento = deepcopy(substituicao)
            substituicao_cancelamento.id = None
            substituicao_cancelamento.solicitacao_dieta_especial = (
                solicitacao_cancelamento
            )
            substituicao_cancelamento.save()
            substituicao_cancelamento.substitutos.add(*substituicao.substitutos.all())
            substituicao_cancelamento.alimentos_substitutos.add(
                *substituicao.alimentos_substitutos.all()
            )
        for anexo in anexos:
            anexo_cancelamento = deepcopy(anexo)
            anexo_cancelamento.id = None
            anexo_cancelamento.solicitacao_dieta_especial = solicitacao_cancelamento
            anexo_cancelamento.save()
        serializer = self.get_serializer(solicitacao_cancelamento)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["patch"],
        url_path=constants.CODAE_AUTORIZA_INATIVACAO,
        permission_classes=(UsuarioCODAEDietaEspecial,),
    )
    def codae_autoriza_inativacao(self, request, uuid=None):
        solicitacao_dieta_especial = self.get_object()
        try:
            solicitacao_dieta_especial.codae_autoriza_inativacao(user=request.user)
            solicitacao_dieta_especial.ativo = False
            solicitacao_dieta_especial.save()
            if solicitacao_dieta_especial.tipo_solicitacao == "ALTERACAO_UE":
                solicitacao_dieta_especial.dieta_alterada.ativo = True
                solicitacao_dieta_especial.dieta_alterada.save()
            serializer = self.get_serializer(solicitacao_dieta_especial)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["patch"],
        url_path=constants.CODAE_NEGA_INATIVACAO,
        permission_classes=(UsuarioCODAEDietaEspecial,),
    )
    def codae_nega_inativacao(self, request, uuid=None):
        solicitacao_dieta_especial = self.get_object()
        justificativa = request.data.get("justificativa_negacao", "")
        try:
            solicitacao_dieta_especial.codae_nega_inativacao(
                user=request.user, justificativa=justificativa
            )
            serializer = self.get_serializer(solicitacao_dieta_especial)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["patch"],
        url_path=constants.TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
        permission_classes=(UsuarioEmpresaGenerico,),
    )
    def terceirizada_toma_ciencia_inativacao(self, request, uuid=None):
        solicitacao_dieta_especial = self.get_object()
        try:
            solicitacao_dieta_especial.terceirizada_toma_ciencia_inativacao(
                user=request.user
            )
            serializer = self.get_serializer(solicitacao_dieta_especial)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True, methods=["post"], permission_classes=(UsuarioCODAEDietaEspecial,)
    )
    def negar(self, request, uuid=None):
        solicitacao = self.get_object()
        form = NegaDietaEspecialForm(request.data, instance=solicitacao)

        if not form.is_valid():
            return Response(form.errors)

        solicitacao.codae_nega(user=request.user)

        return Response({"mensagem": "Solicitação de Dieta Especial Negada"})

    @action(detail=True, methods=["post"], permission_classes=(UsuarioEmpresaGenerico,))
    def tomar_ciencia(self, request, uuid=None):
        solicitacao = self.get_object()
        try:
            solicitacao.terceirizada_toma_ciencia(user=request.user)
            return Response({"mensagem": "Ciente da solicitação de dieta especial"})
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )  # noqa

    @action(
        detail=True,
        url_path=constants.RELATORIO,
        methods=["get"],
        permission_classes=(IsAuthenticated,),
    )
    def relatorio(self, request, uuid=None):
        return relatorio_dieta_especial(request, solicitacao=self.get_object())

    @action(
        detail=True,
        url_path=constants.PROTOCOLO,
        methods=["get"],
        permission_classes=(IsAuthenticated,),
    )
    def protocolo(self, request, uuid=None):
        return relatorio_dieta_especial_protocolo(
            request, solicitacao=self.get_object()
        )

    @action(
        detail=True, methods=["post"], url_path=constants.ESCOLA_CANCELA_DIETA_ESPECIAL
    )  # noqa C901
    def escola_cancela_solicitacao(self, request, uuid=None):
        justificativa = request.data.get("justificativa", "")
        solicitacao = self.get_object()
        try:
            solicitacao.cancelar_pedido(
                user=request.user, justificativa=justificativa, alta_medica=True
            )
            solicitacao.ativo = False
            solicitacao.save()
            if solicitacao.tipo_solicitacao == "CANCELAMENTO_DIETA":
                if request.user.tipo_usuario == "escola":
                    solicitacao.dieta_alterada.ativo = True
                else:
                    solicitacao.dieta_alterada.ativo = False
                    solicitacao.dieta_alterada.cancelar_pedido(
                        user=request.user,
                        justificativa=solicitacao.logs.first().justificativa,
                        alta_medica=True,
                    )
                solicitacao.dieta_alterada.save()
            if solicitacao.tipo_solicitacao == "ALTERACAO_UE":
                solicitacao.dieta_alterada.ativo = True
                solicitacao.dieta_alterada.save()
            serializer = self.get_serializer(solicitacao)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )  # noqa

    @action(
        detail=True, methods=["post"], url_path=constants.CODAE_NEGA_CANCELAMENTO_DIETA
    )
    def codae_nega_cancelamento(self, request, uuid=None):
        justificativa = request.data.get("justificativa", "")
        motivo_negacao = request.data.get("motivo_negacao", "")
        solicitacao = self.get_object()
        try:
            solicitacao.negar_cancelamento_pedido(
                user=request.user, justificativa=justificativa
            )
            solicitacao.motivo_negacao = MotivoNegacao.objects.get(id=motivo_negacao)
            solicitacao.save()
            serializer = self.get_serializer(solicitacao)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["patch"],
        url_path=constants.MARCAR_CONFERIDA,
        permission_classes=(UsuarioEmpresaGenerico,),
    )
    def terceirizada_marca_solicitacao_como_conferida(self, request, uuid=None):
        solicitacao_dieta_especial: SolicitacaoDietaEspecial = self.get_object()
        try:
            solicitacao_dieta_especial.conferido = True
            solicitacao_dieta_especial.save()
            serializer = self.get_serializer(solicitacao_dieta_especial)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                dict(detail=f"Erro ao marcar solicitação como conferida: {e}"),
                status=HTTP_400_BAD_REQUEST,
            )  # noqa

    def get_queryset_relatorio_quantitativo_solic_dieta_esp(  # noqa: C901
        self, form, campos
    ):
        user = self.request.user
        qs = self.get_queryset()

        if user.tipo_usuario == "escola":
            qs = qs.filter(aluno__escola=user.vinculo_atual.instituicao)
        elif form.cleaned_data["escola"]:
            qs = qs.filter(aluno__escola__in=form.cleaned_data["escola"])
        elif user.tipo_usuario == "diretoriaregional":
            qs = qs.filter(
                aluno__escola__diretoria_regional=user.vinculo_atual.instituicao
            )  # noqa
        elif form.cleaned_data["dre"]:
            qs = qs.filter(
                aluno__escola__diretoria_regional__in=form.cleaned_data["dre"]
            )  # noqa

        if form.cleaned_data["data_inicial"]:
            qs = qs.filter(
                criado_em__date__gte=form.cleaned_data["data_inicial"]
            )  # noqa
        if form.cleaned_data["data_final"]:
            qs = qs.filter(criado_em__date__lte=form.cleaned_data["data_final"])  # noqa
        if form.cleaned_data["diagnostico"]:
            qs = qs.filter(
                alergias_intolerancias__in=form.cleaned_data["diagnostico"]
            )  # noqa
        if form.cleaned_data["classificacao"]:
            qs = qs.filter(classificacao__in=form.cleaned_data["classificacao"])  # noqa

        STATUS_PENDENTE = ["CODAE_A_AUTORIZAR"]
        STATUS_ATIVA = [
            "CODAE_AUTORIZADO",
            "TERCEIRIZADA_TOMOU_CIENCIA",
            "ESCOLA_SOLICITOU_INATIVACAO",
            "CODAE_NEGOU_INATIVACAO",
        ]
        STATUS_INATIVA = [
            "CODAE_AUTORIZOU_INATIVACAO",
            "TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO",
            "TERMINADA_AUTOMATICAMENTE_SISTEMA",
            "CANCELADO_ALUNO_NAO_PERTENCE_REDE",
        ]

        when_data = {
            "ativas": When(status__in=STATUS_ATIVA, then=Value("Ativa")),
            "inativas": When(status__in=STATUS_INATIVA, then=Value("Inativa")),
            "pendentes": When(status__in=STATUS_PENDENTE, then=Value("Pendente")),
        }

        if form.cleaned_data["status"] == "":
            whens = when_data.values()
        else:
            whens = [when_data[form.cleaned_data["status"]]]

        qs = (
            qs.annotate(
                status_simples=Case(
                    *whens, default=Value("Outros"), output_field=CharField()
                )
            )
            .exclude(status_simples="Outros")
            .values(*campos)
            .annotate(
                qtde_ativas=Count(
                    "status_simples", filter=Q(status_simples="Ativa")
                ),  # noqa
                qtde_inativas=Count(
                    "status_simples", filter=Q(status_simples="Inativa")
                ),  # noqa
                qtde_pendentes=Count(
                    "status_simples", filter=Q(status_simples="Pendente")
                ),
            )
            .order_by(*campos)
        )

        return qs

    def get_campos_relatorio_quantitativo_solic_dieta_esp(self, filtros):
        campos = ["aluno__escola__diretoria_regional__nome"]
        if len(filtros["escola"]) > 0:
            campos.append("aluno__escola__nome")
        return campos

    def get_campos_relatorio_quantitativo_diag_dieta_esp(self, filtros):
        user = self.request.user
        campos = []
        if (
            user.tipo_usuario != "diretoriaregional" and len(filtros["escola"]) == 0
        ):  # noqa
            campos.append("aluno__escola__diretoria_regional__nome")
        else:
            if user.tipo_usuario != "diretoriaregional":
                campos.append("aluno__escola__diretoria_regional__nome")
        if len(filtros["escola"]) > 0:
            campos.append("aluno__escola__nome")
        campos.append("alergias_intolerancias__descricao")
        campos.append("aluno__data_nascimento__year")

        return campos

    def get_campos_relatorio_quantitativo_classificacao_dieta_esp(self, filtros):
        user = self.request.user
        campos = []
        if (
            user.tipo_usuario != "diretoriaregional" and len(filtros["escola"]) == 0
        ):  # noqa
            campos.append("aluno__escola__diretoria_regional__nome")
        else:
            if user.tipo_usuario != "diretoriaregional":
                campos.append("aluno__escola__diretoria_regional__nome")
        if len(filtros["escola"]) > 0:
            campos.append("aluno__escola__nome")
        campos.append("classificacao__nome")

        return campos

    @action(
        detail=False,
        methods=["POST"],
        url_path="relatorio-quantitativo-solic-dieta-esp",
    )
    def relatorio_quantitativo_solic_dieta_esp(self, request):
        form = RelatorioQuantitativoSolicDietaEspForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        campos = self.get_campos_relatorio_quantitativo_solic_dieta_esp(
            form.cleaned_data
        )
        qs = self.get_queryset_relatorio_quantitativo_solic_dieta_esp(form, campos)

        self.pagination_class = RelatorioPagination
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False, methods=["POST"], url_path="relatorio-quantitativo-diag-dieta-esp"
    )
    def relatorio_quantitativo_diag_dieta_esp(self, request):
        form = RelatorioQuantitativoSolicDietaEspForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        if self.request.data.get("somente_dietas_ativas"):
            campos = ["alergias_intolerancias__descricao"]
        else:
            campos = self.get_campos_relatorio_quantitativo_diag_dieta_esp(
                form.cleaned_data
            )  # noqa
        qs = self.get_queryset_relatorio_quantitativo_solic_dieta_esp(
            form, campos
        )  # noqa

        self.pagination_class = RelatorioPagination
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["POST"],
        url_path="relatorio-quantitativo-classificacao-dieta-esp",
    )
    def relatorio_quantitativo_classificacao_dieta_esp(self, request):
        form = RelatorioQuantitativoSolicDietaEspForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        campos = self.get_campos_relatorio_quantitativo_classificacao_dieta_esp(
            form.cleaned_data
        )  # noqa
        qs = self.get_queryset_relatorio_quantitativo_solic_dieta_esp(
            form, campos
        )  # noqa

        self.pagination_class = RelatorioPagination
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["POST"],
        url_path="imprime-relatorio-quantitativo-solic-dieta-esp",
    )
    def imprime_relatorio_quantitativo_solic_dieta_esp(self, request):
        form = RelatorioQuantitativoSolicDietaEspForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        campos = self.get_campos_relatorio_quantitativo_solic_dieta_esp(
            form.cleaned_data
        )
        qs = self.get_queryset_relatorio_quantitativo_solic_dieta_esp(form, campos)
        user = self.request.user

        return relatorio_quantitativo_solic_dieta_especial(campos, form, qs, user)

    @action(
        detail=False,
        methods=["POST"],
        url_path="imprime-relatorio-quantitativo-classificacao-dieta-esp",
    )
    def imprime_relatorio_quantitativo_classificacao_dieta_esp(self, request):
        form = RelatorioQuantitativoSolicDietaEspForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        campos = self.get_campos_relatorio_quantitativo_classificacao_dieta_esp(
            form.cleaned_data
        )
        qs = self.get_queryset_relatorio_quantitativo_solic_dieta_esp(form, campos)
        user = self.request.user

        return relatorio_quantitativo_classificacao_dieta_especial(
            campos, form, qs, user
        )

    @action(
        detail=False,
        methods=["POST"],
        url_path="imprime-relatorio-quantitativo-diag-dieta-esp",
    )
    def imprime_relatorio_quantitativo_diag_dieta_esp(self, request):
        form = RelatorioQuantitativoSolicDietaEspForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        campos = self.get_campos_relatorio_quantitativo_diag_dieta_esp(
            form.cleaned_data
        )  # noqa
        qs = self.get_queryset_relatorio_quantitativo_solic_dieta_esp(
            form, campos
        )  # noqa
        user = self.request.user
        return relatorio_quantitativo_diag_dieta_especial(campos, form, qs, user)

    @action(
        detail=False,
        methods=["POST"],
        url_path="imprime-relatorio-quantitativo-diag-dieta-esp/somente-dietas-ativas",
    )
    def imprime_relatorio_quantitativo_diag_dieta_esp_somente_dietas_ativas(
        self, request
    ):  # noqa
        form = RelatorioQuantitativoSolicDietaEspForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        if self.request.data.get("somente_dietas_ativas"):
            campos = ["alergias_intolerancias__descricao"]
        else:
            campos = self.get_campos_relatorio_quantitativo_diag_dieta_esp(
                form.cleaned_data
            )  # noqa
        qs = self.get_queryset_relatorio_quantitativo_solic_dieta_esp(
            form, campos
        )  # noqa
        user = self.request.user
        return relatorio_quantitativo_diag_dieta_especial_somente_dietas_ativas(
            campos, form, qs, user
        )  # noqa

    @action(
        detail=False, methods=["POST"], url_path="relatorio-dieta-especial"
    )  # noqa C901
    def relatorio_dieta_especial(self, request):
        self.pagination_class = RelatorioPagination
        form = RelatorioDietaForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        queryset = self.filter_queryset(self.get_queryset())
        data = form.cleaned_data
        filtros = {}
        if data["escola"]:
            filtros["rastro_escola__uuid__in"] = [
                escola.uuid for escola in data["escola"]
            ]
        if data["diagnostico"]:
            filtros["alergias_intolerancias__id__in"] = [
                disgnostico.id for disgnostico in data["diagnostico"]
            ]
        page = self.paginate_queryset(queryset.filter(**filtros))
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False, methods=["POST"], url_path="imprime-relatorio-dieta-especial"
    )  # noqa C901
    def imprime_relatorio_dieta_especial(self, request):
        try:
            form = RelatorioDietaForm(self.request.data)
            if not form.is_valid():
                raise ValidationError(form.errors)
            queryset = self.filter_queryset(self.get_queryset())
            data = form.cleaned_data
            filtros = {}
            if data["escola"]:
                filtros["rastro_escola__uuid__in"] = [
                    escola.uuid for escola in data["escola"]
                ]
            if data["diagnostico"]:
                filtros["alergias_intolerancias__id__in"] = [
                    disgnostico.id for disgnostico in data["diagnostico"]
                ]

            user = request.user.get_username()
            ids_dietas = list(queryset.filter(**filtros).values_list("id", flat=True))
            gera_pdf_relatorio_dieta_especial_async.delay(
                user=user,
                nome_arquivo="relatorio_dieta_especial.pdf",
                data=self.request.data,
                ids_dietas=ids_dietas,
            )
            return Response(
                dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
                status=status.HTTP_200_OK,
            )
        except ValidationError as error:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

    def filtrar_queryset_polo_recreio_ferias(self, query_set, query_params):
        if query_params.get("cei_polo") == "true" and (
            query_params.get("recreio_nas_ferias") == "false"
            or not query_params.get("recreio_nas_ferias")
        ):
            query_set = query_set.filter(
                motivo_alteracao_ue__nome__icontains="polo",
            )
        if query_params.get("recreio_nas_ferias") == "true" and (
            query_params.get("cei_polo") == "false" or not query_params.get("cei_polo")
        ):
            query_set = query_set.filter(
                motivo_alteracao_ue__nome__icontains="recreio",
            )
        if (
            query_params.get("cei_polo") == "true"
            and query_params.get("recreio_nas_ferias") == "true"
        ):
            query_set = query_set.filter(
                Q(motivo_alteracao_ue__nome__icontains="polo")
                | Q(motivo_alteracao_ue__nome__icontains="recreio"),
            )
        return query_set.order_by("motivo_alteracao_ue__nome")

    def filtrar_queryset_relatorio_dieta_especial(self, request, eh_relatorio=False):
        query_set = self.filter_queryset(self.get_queryset())

        lotes_filtro = request.query_params.getlist("lotes_selecionados[]", None)
        instituicao = request.user.vinculo_atual.instituicao
        if not lotes_filtro:
            if isinstance(instituicao, DiretoriaRegional):
                lotes_list = list(instituicao.lotes.all().values_list("uuid"))
                lotes_filtro = [str(u[0]) for u in lotes_list]
        campo_escola_destino = (
            "escola_destino__uuid__in"
            if eh_relatorio
            else "escola_destino__codigo_eol__in"
        )
        map_filtros = {
            "protocolo_padrao__uuid__in": request.query_params.getlist(
                "protocolos_padrao_selecionados[]", None
            ),
            "alergias_intolerancias__id__in": request.query_params.getlist(
                "alergias_intolerancias_selecionadas[]", None
            ),
            "classificacao__id__in": request.query_params.getlist(
                "classificacoes_selecionadas[]", None
            ),
            "escola_destino__lote__uuid__in": lotes_filtro,
            campo_escola_destino: request.query_params.getlist(
                "unidades_educacionais_selecionadas[]", None
            ),
            "escola_destino__tipo_unidade__uuid__in": request.query_params.getlist(
                "tipos_unidades_selecionadas[]", None
            ),
        }
        if isinstance(instituicao, DiretoriaRegional):
            map_filtros["escola_destino__diretoria_regional__uuid"] = instituicao.uuid
        filtros = {
            key: value for key, value in map_filtros.items() if value not in [None, []]
        }
        query_set = query_set.filter(**filtros)
        data = request.query_params
        query_set = self.filtrar_queryset_polo_recreio_ferias(query_set, data)
        if data.get("status_selecionado") == "AUTORIZADAS":
            query_set = query_set.filter(
                status=SolicitacaoDietaEspecial.workflow_class.states.CODAE_AUTORIZADO,
                ativo=True,
            )
        elif data.get("status_selecionado") == "CANCELADAS":
            data_inicial_str = data.get("data_cancelamento_inicial")
            data_final_str = data.get("data_cancelamento_final")
            formato = "%d/%m/%Y"

            data_inicial = (
                datetime.strptime(data_inicial_str, formato)
                if data_inicial_str
                else None
            )
            data_final = (
                datetime.strptime(data_final_str, formato) if data_final_str else None
            )

            params = {
                "criado_em__gte": data_inicial,
                "criado_em__lte": data_final,
                "status_evento__in": [
                    LogSolicitacoesUsuario.ESCOLA_CANCELOU,
                    LogSolicitacoesUsuario.CODAE_AUTORIZOU_INATIVACAO,
                    LogSolicitacoesUsuario.CANCELADO_ALUNO_MUDOU_ESCOLA,
                    LogSolicitacoesUsuario.CANCELADO_ALUNO_NAO_PERTENCE_REDE,
                    LogSolicitacoesUsuario.TERMINADA_AUTOMATICAMENTE_SISTEMA,
                ],
            }

            log_filtros = {
                key: value for key, value in params.items() if value is not None
            }

            logs = LogSolicitacoesUsuario.objects.filter(**log_filtros)

            solicitacoes_uuids = [log.uuid_original for log in logs]
            query_set = query_set.filter(uuid__in=solicitacoes_uuids)

        return query_set

    @action(detail=False, methods=("get",), url_path="filtros-relatorio-dieta-especial")
    def filtros_relatorio_dieta_especial(self, request):
        query_set = self.filtrar_queryset_relatorio_dieta_especial(request)
        instituicao = request.user.vinculo_atual.instituicao
        lotes_dres = []
        if isinstance(instituicao, DiretoriaRegional):
            for lote in instituicao.lotes.all().values_list("nome", "uuid"):
                lotes_dres.append(tuple([f"{lote[0]} - {instituicao.nome}", lote[1]]))
            lotes_dict = dict(lotes_dres)
        else:
            for s in query_set.values_list(
                "escola_destino__lote__nome",
                "escola_destino__lote__uuid",
                "escola_destino__diretoria_regional__nome",
            ):
                lotes_dres.append(tuple([f"{s[0]} - {s[2]}", s[1]]))
            lotes_dict = dict(lotes_dres)
        lotes_dict = trata_lotes_dict_duplicados(lotes_dict)
        lotes = sorted(
            [
                {"nome": key, "uuid": lotes_dict[key]}
                for key in lotes_dict.keys()
                if key
            ],
            key=lambda lote: lote["nome"],
        )

        classificacoes_dict = dict(
            set(query_set.values_list("classificacao__nome", "classificacao__id"))
        )
        classificacoes = sorted(
            [
                {"nome": key, "id": classificacoes_dict[key]}
                for key in classificacoes_dict.keys()
                if key
            ],
            key=lambda classificacao: classificacao["nome"],
        )

        protocolos_padrao_dict = dict(
            set(
                query_set.values_list(
                    "protocolo_padrao__nome_protocolo", "protocolo_padrao__uuid"
                )
            )
        )
        protocolos_padrao = sorted(
            [
                {"nome": key, "uuid": protocolos_padrao_dict[key]}
                for key in protocolos_padrao_dict.keys()
                if key
            ],
            key=lambda protocolo_padrao: protocolo_padrao["nome"],
        )

        alergias_intolerancias_dict = dict(
            set(
                query_set.values_list(
                    "alergias_intolerancias__descricao", "alergias_intolerancias__id"
                )
            )
        )
        alergias_intolerancias = sorted(
            [
                {"nome": key, "id": alergias_intolerancias_dict[key]}
                for key in alergias_intolerancias_dict.keys()
                if key
            ],
            key=lambda alergia_intolerancia: alergia_intolerancia["nome"],
        )
        tipos_gestao_dict = dict(
            set(
                TipoGestao.objects.exclude(nome__in=["DIRETA", "MISTA"]).values_list(
                    "nome", "uuid"
                )
            )
        )
        tipos_gestao = [
            {"nome": key, "uuid": tipos_gestao_dict[key]}
            for key in tipos_gestao_dict.keys()
            if key
        ]

        tipos_unidades_dict = dict(
            set(
                query_set.values_list(
                    "escola_destino__tipo_unidade__iniciais",
                    "escola_destino__tipo_unidade__uuid",
                )
            )
        )
        tipos_unidades = [
            {"nome": key, "uuid": tipos_unidades_dict[key]}
            for key in tipos_unidades_dict.keys()
            if key
        ]
        return Response(
            {
                "alergias_intolerancias": alergias_intolerancias,
                "classificacoes": classificacoes,
                "lotes": lotes,
                "protocolos_padrao": protocolos_padrao,
                "tipos_gestao": tipos_gestao,
                "tipos_unidades": tipos_unidades,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False, methods=("get",), url_path="relatorio-dieta-especial-terceirizada"
    )
    def relatorio_dieta_especial_terceirizada(self, request):  # noqa C901
        query_set = self.filtrar_queryset_relatorio_dieta_especial(
            request, True
        ).distinct()
        page = self.paginate_queryset(query_set)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["POST"], url_path="panorama-escola")
    def panorama_escola(self, request):
        # TODO: Mover essa rotina para o viewset escola simples, evitando esse
        # form
        form = PanoramaForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        hoje = date.today()

        filtros_gerais = Q(
            escola__aluno__periodo_escolar=F("periodo_escolar"),
            escola__aluno__escola=form.cleaned_data["escola"],
            escola__aluno__dietas_especiais__ativo=True,
            escola__aluno__dietas_especiais__status__in=[
                DietaEspecialWorkflow.CODAE_AUTORIZADO,
                DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
                DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
            ],
        )
        filtros_data_dieta = (
            Q(escola__aluno__dietas_especiais__data_termino__isnull=True)
            | Q(escola__aluno__dietas_especiais__data_termino__gte=hoje)
        ) & (
            Q(escola__aluno__dietas_especiais__data_inicio__isnull=True)
            & Q(escola__aluno__dietas_especiais__criado_em__date__lte=hoje)
            | Q(escola__aluno__dietas_especiais__data_inicio__isnull=False)
            & Q(escola__aluno__dietas_especiais__data_inicio__lte=hoje)
        )

        q_params = filtros_gerais & filtros_data_dieta

        campos = [
            "periodo_escolar__nome",
            "horas_atendimento",
            "quantidade_alunos",
            "uuid",
        ]
        qs = (
            EscolaPeriodoEscolar.objects.filter(
                escola=form.cleaned_data["escola"], quantidade_alunos__gt=0
            )
            .values(*campos)
            .annotate(
                qtde_tipo_a=(
                    Count(
                        "id",
                        filter=Q(
                            escola__aluno__dietas_especiais__classificacao__nome="Tipo A"
                        )
                        & q_params,
                    )
                ),
                qtde_enteral=(
                    Count(
                        "id",
                        filter=Q(
                            escola__aluno__dietas_especiais__classificacao__nome="Tipo A Enteral"
                        )
                        & q_params,
                    )
                ),
                qtde_tipo_b=(
                    Count(
                        "id",
                        filter=Q(
                            escola__aluno__dietas_especiais__classificacao__nome="Tipo B"
                        )
                        & q_params,
                    )
                ),
            )
            .order_by(*campos)
        )

        serializer = self.get_serializer(qs, many=True)

        return Response(serializer.data)

    @action(detail=False, methods=["POST"], url_path="alteracao-ue")
    def alteracao_ue(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["GET"], url_path="exportar-xlsx")
    def exportar_xlsx(self, request):
        """TODO: ver porque nao pode importar o pandas via pytest."""
        query_set = self.filtrar_queryset_relatorio_dieta_especial(request, True)
        data = request.query_params
        user = request.user.get_username()
        ids_dietas = list(query_set.values_list("id", flat=True))
        lotes = data.getlist("lotes_selecionados[]", None)
        classificacoes = data.getlist("classificacoes_selecionadas[]", None)
        protocolos_padrao = data.getlist("protocolos_padrao_selecionados[]", None)
        gera_xlsx_relatorio_dietas_especiais_terceirizadas_async.delay(
            user=user,
            nome_arquivo="relatorio_dietas_especiais.xlsx",
            ids_dietas=ids_dietas,
            data=request.query_params,
            lotes=lotes,
            classificacoes=classificacoes,
            protocolos_padrao=protocolos_padrao,
        )
        return Response(
            dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
            status=status.HTTP_200_OK,
        )

    def build_texto(  # noqa: C901
        self,
        lotes,
        classificacoes,
        protocolos,
        alergias_intolerancias,
        data_inicial,
        data_final,
    ):
        filtros = ""
        if lotes:
            nomes_lotes = ", ".join(
                [lote.nome for lote in Lote.objects.filter(uuid__in=lotes)]
            )
            if len(filtros) == 0:
                filtros += f"{nomes_lotes}"
            else:
                filtros += f" | {nomes_lotes}"

        if classificacoes:
            nomes_classificacoes = ", ".join(
                [
                    classificacao.nome
                    for classificacao in ClassificacaoDieta.objects.filter(
                        id__in=classificacoes
                    )
                ]
            )
            if len(filtros) == 0:
                filtros += f"Classificação(ões) da dieta: {nomes_classificacoes}"
            else:
                filtros += f" | Classificação(ões) da dieta: {nomes_classificacoes}"

        if protocolos:
            nomes_protocolos = ", ".join(
                [
                    protocolo.nome_protocolo
                    for protocolo in ProtocoloPadraoDietaEspecial.objects.filter(
                        uuid__in=protocolos
                    )
                ]
            )
            if len(filtros) == 0:
                filtros += f"Protocolo(s) padrão(ões): {nomes_protocolos}"
            else:
                filtros += f" | Protocolo(s) padrão(ões): {nomes_protocolos}"

        if alergias_intolerancias:
            nomes_alergias_intolerancias = ", ".join(
                [
                    alergia_intolerancia.descricao
                    for alergia_intolerancia in AlergiaIntolerancia.objects.filter(
                        id__in=alergias_intolerancias
                    )
                ]
            )
            if len(filtros) == 0:
                filtros += f"Diagnóstico(s) da dieta: {nomes_alergias_intolerancias}"
            else:
                filtros += f" | Diagnóstico(s) da dieta: {nomes_alergias_intolerancias}"

        if data_inicial:
            if len(filtros) == 0:
                filtros += f"Data inicial: {data_inicial}"
            else:
                filtros += f" | Data inicial: {data_inicial}"

        if data_final:
            if len(filtros) == 0:
                filtros += f"Data final: {data_final}"
            else:
                filtros += f" | Data final: {data_final}"

        return filtros

    @action(detail=False, methods=["GET"], url_path="exportar-pdf")
    def exportar_pdf(self, request):
        user = request.user.get_username()
        query_set = self.filtrar_queryset_relatorio_dieta_especial(request, True)
        ids_dietas = list(query_set.values_list("id", flat=True))
        filtros = self.build_texto(
            request.query_params.getlist("lotes_selecionados[]", None),
            request.query_params.getlist("classificacoes_selecionadas[]", None),
            request.query_params.getlist("protocolos_padrao_selecionados[]", None),
            request.query_params.getlist("alergias_intolerancias_selecionadas[]", None),
            request.query_params.get("data_cancelamento_inicial", None),
            request.query_params.get("data_cancelamento_final", None),
        )
        gera_pdf_relatorio_dietas_especiais_terceirizadas_async.delay(
            user=user,
            data=request.query_params,
            nome_arquivo="relatorio_dietas_especiais.pdf",
            ids_dietas=ids_dietas,
            filtros=filtros,
        )
        return Response(
            dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["GET"],
        url_path="relatorio-historico-dieta-especial",
        permission_classes=(PermissaoHistoricoDietasEspeciais,),
    )
    def relatorio_historico_dieta_especial(self, request):
        try:
            filtros, data_dieta = gerar_filtros_relatorio_historico(
                request.query_params
            )
            dietas = gera_dicionario_historico_dietas(filtros)
            paginator = HistoricoDietasPagination()
            page = paginator.paginate_queryset(dietas["resultados"], request)
            serializer = UnidadeEducacionalSerializer(page, many=True)
            return paginator.get_paginated_response(
                serializer.data, dietas["total_dietas"], data_dieta
            )
        except ValidationError as e:
            return Response(dict(detail=e.messages[0]), status=HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["GET"],
        url_path="relatorio-historico-dieta-especial/exportar-pdf",
        permission_classes=(PermissaoHistoricoDietasEspeciais,),
    )
    def relatorio_historico_dieta_especial_exportar_pdf(self, request):
        try:
            query_dict = request.query_params
            data = {
                key: query_dict.getlist(key) if "[]" in key else query_dict.get(key)
                for key in query_dict.keys()
            }
            data_str = data.get("data").replace("/", "_")
            user = request.user.get_username()
            gera_pdf_relatorio_historico_dietas_especiais_async.delay(
                user=user,
                nome_arquivo=f"relatorio_historico_dietas_especiais_{data_str}.pdf",
                data=json.dumps(data),
            )
            return Response(
                dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(dict(detail=e.messages[0]), status=HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["GET"],
        url_path="relatorio-historico-dieta-especial/exportar-excel",
        permission_classes=(PermissaoHistoricoDietasEspeciais,),
    )
    def relatorio_historico_dieta_especial_exportar_excel(self, request):
        try:
            query_dict = request.query_params
            data = {
                key: query_dict.getlist(key) if "[]" in key else query_dict.get(key)
                for key in query_dict.keys()
            }
            data_str = data.get("data").replace("/", "_")
            user = request.user.get_username()
            gera_xlsx_relatorio_historico_dietas_especiais_async.delay(
                user=user,
                nome_arquivo=f"relatorio_historico_dietas_especiais_{data_str}.xlsx",
                data=json.dumps(data),
            )
            return Response(
                dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(dict(detail=e.messages[0]), status=HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["GET"],
        url_path="relatorio-recreio-nas-ferias",
        permission_classes=(PermissaoRelatorioRecreioNasFerias,),
    )
    def relatorio_recreio_nas_ferias(self, request):
        self.pagination_class = RelatorioPagination
        try:
            queryset = filtra_relatorio_recreio_nas_ferias(request.query_params)
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except ValidationError as e:
            return Response(dict(detail=e.messages[0]), status=HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["GET"],
        url_path="relatorio-recreio-nas-ferias/exportar-pdf",
        permission_classes=(PermissaoRelatorioRecreioNasFerias,),
    )
    def relatorio_recreio_nas_ferias_exportar_pdf(self, request):
        try:
            user = request.user.get_username()
            gera_pdf_relatorio_recreio_nas_ferias_async.delay(
                user=user,
                nome_arquivo="relatorio_recreio_nas_ferias.pdf",
                params=request.query_params,
            )
            return Response(
                dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(dict(detail=e.messages[0]), status=HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["GET"],
        url_path="relatorio-recreio-nas-ferias/exportar-excel",
        permission_classes=(PermissaoRelatorioRecreioNasFerias,),
    )
    def relatorio_recreio_nas_ferias_exportar_xlsx(self, request):
        try:
            user = request.user.get_username()
            gera_xlsx_relatorio_recreio_nas_ferias_async.delay(
                user=user,
                nome_arquivo="relatorio_recreio_nas_ferias.xlsx",
                params=request.query_params,
            )
            return Response(
                dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(dict(detail=e.messages[0]), status=HTTP_400_BAD_REQUEST)


class SolicitacoesAtivasInativasPorAlunoView(generics.ListAPIView):
    serializer_class = SolicitacoesAtivasInativasPorAlunoSerializer

    @staticmethod
    def calcular_totais(queryset):
        status_dietas = [
            "CODAE_AUTORIZADO",
            "CODAE_AUTORIZOU_INATIVACAO",
            "TERMINADA_AUTOMATICAMENTE_SISTEMA",
            "CANCELADO_ALUNO_NAO_PERTENCE_REDE",
        ]
        total_ativas = (
            SolicitacaoDietaEspecial.objects.filter(
                aluno__in=queryset, status__in=["CODAE_AUTORIZADO"], ativo=True
            )
            .distinct()
            .count()
        )
        total_inativas = (
            SolicitacaoDietaEspecial.objects.filter(
                aluno__in=queryset, status__in=status_dietas, ativo=False
            )
            .distinct()
            .count()
        )
        return total_ativas, total_inativas

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        total_ativas, total_inativas = self.calcular_totais(queryset)

        tem_parametro_page = request.GET.get("page", False)

        if tem_parametro_page:
            novo_sgp_service = NovoSGPServicoLogado()
            self.pagination_class = RelatorioPagination
            page = self.paginate_queryset(queryset)
            serializer = SolicitacoesAtivasInativasPorAlunoSerializer(
                page, context={"novo_sgp_service": novo_sgp_service}, many=True
            )

            return self.get_paginated_response(
                {
                    "total_ativas": total_ativas,
                    "total_inativas": total_inativas,
                    "solicitacoes": serializer.data,
                }
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "total_ativas": total_ativas,
                "total_inativas": total_inativas,
                "solicitacoes": serializer.data,
            }
        )

    def get_queryset(self):  # noqa C901
        form = SolicitacoesAtivasInativasPorAlunoForm(self.request.GET)
        if not form.is_valid():
            raise ValidationError(form.errors)

        user = self.request.user

        STATUS_DIETA_ESPECIAL = [
            "CODAE_AUTORIZADO",
            "CODAE_AUTORIZOU_INATIVACAO",
            "TERMINADA_AUTOMATICAMENTE_SISTEMA",
            "CANCELADO_ALUNO_NAO_PERTENCE_REDE",
        ]

        qs = Aluno.objects.filter(dietas_especiais__status__in=STATUS_DIETA_ESPECIAL)
        incluir_alteracao_ue = (
            self.request.query_params.get("incluir_alteracao_ue", None) == "true"
        )
        if user.tipo_usuario == "escola":
            if incluir_alteracao_ue:
                qs = qs.filter(
                    Q(
                        dietas_especiais__rastro_escola=user.vinculo_atual.instituicao,
                        dietas_especiais__status__in=["CODAE_AUTORIZADO"],
                        dietas_especiais__ativo=True,
                        dietas_especiais__tipo_solicitacao="COMUM",
                    )
                    | Q(
                        dietas_especiais__escola_destino=user.vinculo_atual.instituicao,
                        dietas_especiais__status__in=["CODAE_AUTORIZADO"],
                        dietas_especiais__ativo=True,
                        dietas_especiais__tipo_solicitacao="ALTERACAO_UE",
                    )
                )
            else:
                qs = qs.filter(
                    dietas_especiais__rastro_escola=user.vinculo_atual.instituicao
                )
        elif form.cleaned_data["escola"]:
            if incluir_alteracao_ue:
                qs = qs.filter(
                    Q(
                        dietas_especiais__rastro_escola=form.cleaned_data["escola"],
                        dietas_especiais__status__in=["CODAE_AUTORIZADO"],
                        dietas_especiais__ativo=True,
                        dietas_especiais__tipo_solicitacao="COMUM",
                    )
                    | Q(
                        dietas_especiais__escola_destino=form.cleaned_data["escola"],
                        dietas_especiais__status__in=["CODAE_AUTORIZADO"],
                        dietas_especiais__ativo=True,
                        dietas_especiais__tipo_solicitacao="ALTERACAO_UE",
                    )
                )
            else:
                qs = qs.filter(
                    dietas_especiais__rastro_escola=form.cleaned_data["escola"]
                )
                qs = filtrar_alunos_com_dietas_nos_status_e_rastro_escola(
                    qs, STATUS_DIETA_ESPECIAL, form.cleaned_data["escola"]
                )
        elif user.tipo_usuario == "diretoriaregional":
            if incluir_alteracao_ue:
                qs = qs.filter(
                    Q(
                        dietas_especiais__rastro_escola__diretoria_regional=user.vinculo_atual.instituicao,
                        dietas_especiais__status__in=["CODAE_AUTORIZADO"],
                        dietas_especiais__ativo=True,
                        dietas_especiais__tipo_solicitacao="COMUM",
                    )
                    | Q(
                        dietas_especiais__escola_destino__diretoria_regional=user.vinculo_atual.instituicao,
                        dietas_especiais__status__in=["CODAE_AUTORIZADO"],
                        dietas_especiais__ativo=True,
                        dietas_especiais__tipo_solicitacao="ALTERACAO_UE",
                    )
                )
            else:
                qs = qs.filter(
                    dietas_especiais__rastro_escola__diretoria_regional=user.vinculo_atual.instituicao
                )

        elif form.cleaned_data["dre"]:
            if incluir_alteracao_ue:
                qs = qs.filter(
                    Q(
                        dietas_especiais__rastro_escola__diretoria_regional=form.cleaned_data[
                            "dre"
                        ],
                        dietas_especiais__status__in=["CODAE_AUTORIZADO"],
                        dietas_especiais__ativo=True,
                        dietas_especiais__tipo_solicitacao="COMUM",
                    )
                    | Q(
                        dietas_especiais__escola_destino__diretoria_regional=form.cleaned_data[
                            "dre"
                        ],
                        dietas_especiais__status__in=["CODAE_AUTORIZADO"],
                        dietas_especiais__ativo=True,
                        dietas_especiais__tipo_solicitacao="ALTERACAO_UE",
                    )
                )
            else:
                qs = qs.filter(
                    dietas_especiais__rastro_escola__diretoria_regional=form.cleaned_data[
                        "dre"
                    ]
                )

        if form.cleaned_data["codigo_eol"]:
            codigo_eol = f"{int(form.cleaned_data['codigo_eol']):06d}"
            qs = qs.filter(codigo_eol=codigo_eol)
        elif form.cleaned_data["nome_aluno"]:
            qs = qs.filter(nome__icontains=form.cleaned_data["nome_aluno"])

        if self.request.user.tipo_usuario == "dieta_especial":
            return qs.distinct().order_by(
                "escola__diretoria_regional__nome", "escola__nome", "nome"
            )
        elif self.request.user.tipo_usuario == "diretoriaregional":
            return qs.distinct().order_by("escola__nome", "nome")

        return qs.distinct().order_by("nome")


class AlergiaIntoleranciaViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet
):
    queryset = AlergiaIntolerancia.objects.all()
    serializer_class = AlergiaIntoleranciaSerializer
    pagination_class = None


class ClassificacaoDietaViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet
):
    queryset = ClassificacaoDieta.objects.order_by("nome")
    serializer_class = ClassificacaoDietaSerializer
    pagination_class = None


class MotivoNegacaoViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet
):
    queryset = MotivoNegacao.objects.all()
    serializer_class = MotivoNegacaoSerializer
    pagination_class = None
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = MotivoNegacaoFilter


class AlimentoViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    queryset = Alimento.objects.all().order_by("nome")
    serializer_class = AlimentoSerializer
    pagination_class = None
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = AlimentoFilter


class TipoContagemViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = TipoContagem.objects.all().order_by("nome")
    serializer_class = TipoContagemSerializer
    pagination_class = None
    verbose_name = "Tipo de Contagem"
    verbose_name_plural = "Tipos de Contagem"


class MotivoAlteracaoUEViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = MotivoAlteracaoUE.objects.order_by("nome")
    serializer_class = MotivoAlteracaoUESerializer


class ProtocoloPadraoDietaEspecialViewSet(ModelViewSet):
    lookup_field = "uuid"
    permission_classes = (IsAuthenticated,)
    queryset = ProtocoloPadraoDietaEspecial.objects.filter(ativo=True).order_by(
        "nome_protocolo"
    )
    serializer_class = ProtocoloPadraoDietaEspecialSerializer
    pagination_class = ProtocoloPadraoPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ("nome_protocolo", "status")

    def get_serializer_class(self):
        if self.action in ["create", "update"]:
            return ProtocoloPadraoDietaEspecialSerializerCreate
        return ProtocoloPadraoDietaEspecialSerializer

    def get_queryset(self):
        queryset = ProtocoloPadraoDietaEspecial.objects.filter(ativo=True)
        if "editais[]" in self.request.query_params:
            queryset = queryset.filter(
                editais__uuid__in=self.request.query_params.getlist("editais[]")
            ).distinct()
        return queryset.order_by("nome_protocolo")

    @action(detail=False, methods=["GET"], url_path="lista-status")
    def lista_status(self, request):
        list_status = ProtocoloPadraoDietaEspecial.STATUS_NOMES.keys()

        return Response({"results": list_status})

    @action(detail=False, methods=["GET"], url_path="nomes")
    def nomes(self, request):
        nomes = self.queryset.values_list("nome_protocolo", flat=True).distinct()

        return Response({"results": nomes})

    @action(detail=False, methods=["GET"], url_path="lista-protocolos-liberados")
    def lista_protocolos_liberados(self, request):
        dieta_uuid = request.query_params.get("dieta_especial_uuid", None)
        solicitacao = SolicitacaoDietaEspecial.objects.get(uuid=dieta_uuid)
        escola = solicitacao.escola
        if escola.eh_parceira:
            editais_uuid = Edital.objects.filter(numero__iexact="PARCEIRA").values_list(
                "uuid", flat=True
            )
        else:
            editais_uuid = Contrato.objects.filter(lotes__in=[escola.lote]).values_list(
                "edital__uuid", flat=True
            )
        protocolos_liberados = (
            self.get_queryset()
            .filter(
                status=ProtocoloPadraoDietaEspecial.STATUS_LIBERADO,
                editais__uuid__in=editais_uuid,
            )
            .distinct()
        )
        response = {
            "results": ProtocoloPadraoDietaEspecialSimplesSerializer(
                protocolos_liberados, many=True
            ).data
        }
        return Response(response)

    @action(
        detail=False, methods=["GET"], url_path="lista-protocolos-liberados-por-edital"
    )
    def lista_protocolos_liberados_por_edital(self, request):
        edital_uuid = request.query_params.get("edital_uuid", None)
        protocolos_liberados = self.get_queryset().filter(
            status=ProtocoloPadraoDietaEspecial.STATUS_LIBERADO,
            editais__uuid__in=[edital_uuid],
        )
        response = {
            "results": ProtocoloPadraoDietaEspecialSimplesSerializer(
                protocolos_liberados, many=True
            ).data
        }
        return Response(response)

    def criar_historico_editais(self, protocolo, validated_data):
        historico = {}
        changes = []

        outras_informacoes = validated_data.get("outras_informacoes")

        editais_antes = protocolo.editais.all()
        editais_depois = Edital.objects.filter(
            uuid__in=validated_data.get("editais_destino", [])
        )
        soma_todos_editais = editais_antes | editais_depois
        diferenca = soma_todos_editais.distinct().difference(editais_antes)

        if diferenca and diferenca.count() > 0:
            changes.append(
                {
                    "field": "editais",
                    "from": [
                        edital.numero for edital in editais_antes.order_by("numero")
                    ],
                    "to": [
                        edital.numero
                        for edital in soma_todos_editais.distinct().order_by("numero")
                    ],
                }
            )

        if (protocolo.outras_informacoes != outras_informacoes) and (
            outras_informacoes != ""
        ):
            changes.append(
                {
                    "field": "outras informacoes",
                    "from": protocolo.outras_informacoes,
                    "to": outras_informacoes,
                }
            )

        if changes and len(changes) > 0:
            historico["updated_at"] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            historico["user"] = {
                "uuid": str(self.request.user.uuid),
                "email": self.request.user.email,
                "nome": self.request.user.nome,
                "username": self.request.user.username,
            }
            historico["action"] = "UPDATE_VINCULOS"
            historico["changes"] = changes
        return historico

    @action(detail=False, methods=["PUT"], url_path="atualizar-editais")
    def atualizar_editais(self, request):
        protocolos_padrao = request.data.get("protocolos_padrao", None)
        editais_destino = request.data.get("editais_destino", None)
        outras_informacoes = request.data.get("outras_informacoes", "")

        validated_data = {
            "editais_destino": editais_destino,
            "outras_informacoes": outras_informacoes,
        }

        if protocolos_padrao and editais_destino:
            editais = Edital.objects.filter(uuid__in=editais_destino)
            protocolos = self.get_queryset().filter(uuid__in=protocolos_padrao)
            for protocolo in protocolos:
                historico = self.criar_historico_editais(protocolo, validated_data)
                if len(historico) > 0:
                    hist = (
                        json.loads(protocolo.historico) if protocolo.historico else []
                    )
                    hist.append(historico)
                    protocolo.historico = json.dumps(hist)

                protocolo.outras_informacoes = outras_informacoes
                protocolo.editais.add(*editais)
                protocolo.save()
            return Response(
                {"results": "Protacolos relacionados com sucesso."},
                status=status.HTTP_200_OK,
            )
        if not protocolos_padrao:
            return Response(
                {"results": "É necessário selecionar um Protocolo Padrão."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not editais_destino:
            return Response(
                {"results": "É necessário selecionar um Edital."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LogQuantidadeDietasAutorizadasViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = LogQuantidadeDietasAutorizadasSerializer
    queryset = LogQuantidadeDietasAutorizadas.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = LogQuantidadeDietasEspeciaisFilter
    pagination_class = None


class LogQuantidadeDietasAutorizadasCEIViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = LogQuantidadeDietasAutorizadasCEISerializer
    queryset = LogQuantidadeDietasAutorizadasCEI.objects.filter(
        faixa_etaria__isnull=False
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = LogQuantidadeDietasEspeciaisFilter
    pagination_class = None
