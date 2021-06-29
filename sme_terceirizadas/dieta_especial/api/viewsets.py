from datetime import date

from django.db import transaction
from django.db.models import Case, CharField, Count, F, Q, Sum, Value, When
from django.forms import ValidationError
from django_filters import rest_framework as filters
from rest_framework import generics, mixins, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from xworkflows import InvalidTransitionError

from ...dados_comuns import constants
from ...dados_comuns.fluxo_status import DietaEspecialWorkflow
from ...dados_comuns.permissions import (
    PermissaoParaRecuperarDietaEspecial,
    UsuarioCODAEDietaEspecial,
    UsuarioEscola,
    UsuarioTerceirizada
)
from ...escola.models import Aluno, EscolaPeriodoEscolar
from ...paineis_consolidados.api.constants import FILTRO_CODIGO_EOL_ALUNO
from ...paineis_consolidados.models import SolicitacoesCODAE, SolicitacoesDRE, SolicitacoesEscola
from ...relatorios.relatorios import (
    relatorio_dieta_especial,
    relatorio_dieta_especial_protocolo,
    relatorio_geral_dieta_especial,
    relatorio_quantitativo_classificacao_dieta_especial,
    relatorio_quantitativo_diag_dieta_especial,
    relatorio_quantitativo_diag_dieta_especial_somente_dietas_ativas,
    relatorio_quantitativo_solic_dieta_especial
)
from ..forms import (
    NegaDietaEspecialForm,
    PanoramaForm,
    RelatorioDietaForm,
    RelatorioQuantitativoSolicDietaEspForm,
    SolicitacoesAtivasInativasPorAlunoForm
)
from ..models import (
    AlergiaIntolerancia,
    Alimento,
    ClassificacaoDieta,
    MotivoAlteracaoUE,
    MotivoNegacao,
    ProtocoloPadraoDietaEspecial,
    SolicitacaoDietaEspecial,
    TipoContagem
)
from ..utils import ProtocoloPadraoPagination, RelatorioPagination
from .filters import AlimentoFilter, DietaEspecialFilter
from .serializers import (
    AlergiaIntoleranciaSerializer,
    AlimentoSerializer,
    ClassificacaoDietaSerializer,
    MotivoAlteracaoUESerializer,
    MotivoNegacaoSerializer,
    PanoramaSerializer,
    ProtocoloPadraoDietaEspecialSerializer,
    ProtocoloPadraoDietaEspecialSimplesSerializer,
    RelatorioQuantitativoSolicDietaEspSerializer,
    SolicitacaoDietaEspecialAutorizarSerializer,
    SolicitacaoDietaEspecialSerializer,
    SolicitacaoDietaEspecialSimplesSerializer,
    SolicitacaoDietaEspecialUpdateSerializer,
    SolicitacoesAtivasInativasPorAlunoSerializer,
    TipoContagemSerializer
)
from .serializers_create import (
    AlteracaoUESerializer,
    ProtocoloPadraoDietaEspecialSerializerCreate,
    SolicitacaoDietaEspecialCreateSerializer
)


class SolicitacaoDietaEspecialViewSet(
        mixins.RetrieveModelMixin,
        mixins.ListModelMixin,
        mixins.CreateModelMixin,
        mixins.UpdateModelMixin,
        GenericViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    queryset = SolicitacaoDietaEspecial.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = DietaEspecialFilter

    def get_queryset(self):
        if self.action in ['relatorio_dieta_especial', 'imprime_relatorio_dieta_especial']:  # noqa
            return self.queryset.select_related('rastro_escola__diretoria_regional').order_by('criado_em')  # noqa
        return super().get_queryset()

    def get_permissions(self):  # noqa C901
        if self.action == 'list':
            self.permission_classes = (
                IsAuthenticated, PermissaoParaRecuperarDietaEspecial)
        elif self.action == 'update':
            self.permission_classes = (IsAdminUser, UsuarioCODAEDietaEspecial)
        elif self.action == 'retrieve':
            self.permission_classes = (
                IsAuthenticated, PermissaoParaRecuperarDietaEspecial)
        elif self.action == 'create':
            self.permission_classes = (UsuarioEscola,)
        elif self.action in [
            'imprime_relatorio_dieta_especial',
            'relatorio_dieta_especial'
        ]:
            self.permission_classes = (
                IsAuthenticated, PermissaoParaRecuperarDietaEspecial)
        return super(SolicitacaoDietaEspecialViewSet, self).get_permissions()

    def get_serializer_class(self):  # noqa C901
        if self.action == 'create':
            return SolicitacaoDietaEspecialCreateSerializer
        elif self.action == 'autorizar':
            return SolicitacaoDietaEspecialAutorizarSerializer
        elif self.action in ['update', 'partial_update']:
            return SolicitacaoDietaEspecialUpdateSerializer
        elif self.action in [
            'relatorio_quantitativo_solic_dieta_esp',
            'relatorio_quantitativo_diag_dieta_esp',
            'relatorio_quantitativo_classificacao_dieta_esp',
        ]:
            return RelatorioQuantitativoSolicDietaEspSerializer
        elif self.action == 'relatorio_dieta_especial':
            return SolicitacaoDietaEspecialSimplesSerializer
        elif self.action == 'panorama_escola':
            return PanoramaSerializer
        elif self.action == 'alteracao_ue':
            return AlteracaoUESerializer
        return SolicitacaoDietaEspecialSerializer

    @action(
        detail=False,
        methods=['get'],
        url_path=f'solicitacoes-aluno/{FILTRO_CODIGO_EOL_ALUNO}'
    )
    def solicitacoes_vigentes(self, request, codigo_eol_aluno=None):
        solicitacoes = SolicitacaoDietaEspecial.objects.filter(
            aluno__codigo_eol=codigo_eol_aluno
        ).exclude(
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_A_AUTORIZAR
        )
        page = self.paginate_queryset(solicitacoes)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @transaction.atomic  # noqa C901
    @action(detail=True, methods=['patch'], permission_classes=(UsuarioCODAEDietaEspecial,))  # noqa: C901
    def autorizar(self, request, uuid=None):
        solicitacao = self.get_object()
        if solicitacao.aluno.possui_dieta_especial_ativa and solicitacao.tipo_solicitacao == 'COMUM':
            solicitacao.aluno.inativar_dieta_especial()
        serializer = self.get_serializer()
        try:
            if solicitacao.tipo_solicitacao != 'ALTERACAO_UE':
                serializer.update(solicitacao, request.data)
                solicitacao.ativo = True
            solicitacao.codae_autoriza(user=request.user)
            return Response({'detail': 'Autorização de dieta especial realizada com sucesso'})  # noqa
        except InvalidTransitionError as e:
            return Response({'detail': f'Erro na transição de estado {e}'}, status=HTTP_400_BAD_REQUEST)  # noqa
        except serializers.ValidationError as e:
            return Response({'detail': f'Dados inválidos {e}'}, status=HTTP_400_BAD_REQUEST)  # noqa

    @action(detail=True,
            methods=['patch'],
            url_path=constants.ESCOLA_SOLICITA_INATIVACAO,
            permission_classes=(UsuarioEscola,))
    def escola_solicita_inativacao(self, request, uuid=None):
        solicitacao_dieta_especial = self.get_object()
        justificativa = request.data.get('justificativa', '')
        try:
            solicitacao_dieta_especial.cria_anexos_inativacao(
                request.data.get('anexos'))
            solicitacao_dieta_especial.inicia_fluxo_inativacao(
                user=request.user, justificativa=justificativa)
            serializer = self.get_serializer(solicitacao_dieta_especial)
            return Response(serializer.data)
        except AssertionError as e:
            return Response(dict(detail=str(e)), status=HTTP_400_BAD_REQUEST)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)  # noqa

    @action(detail=True,
            methods=['patch'],
            url_path=constants.CODAE_AUTORIZA_INATIVACAO,
            permission_classes=(UsuarioCODAEDietaEspecial,))
    def codae_autoriza_inativacao(self, request, uuid=None):
        solicitacao_dieta_especial = self.get_object()
        try:
            solicitacao_dieta_especial.codae_autoriza_inativacao(
                user=request.user)
            solicitacao_dieta_especial.ativo = False
            solicitacao_dieta_especial.save()
            if solicitacao_dieta_especial.tipo_solicitacao == 'ALTERACAO_UE':
                solicitacao_dieta_especial.dieta_alterada.ativo = True
                solicitacao_dieta_especial.dieta_alterada.save()
            serializer = self.get_serializer(solicitacao_dieta_especial)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)  # noqa

    @action(detail=True,
            methods=['patch'],
            url_path=constants.CODAE_NEGA_INATIVACAO,
            permission_classes=(UsuarioCODAEDietaEspecial,))
    def codae_nega_inativacao(self, request, uuid=None):
        solicitacao_dieta_especial = self.get_object()
        justificativa = request.data.get('justificativa_negacao', '')
        try:
            solicitacao_dieta_especial.codae_nega_inativacao(
                user=request.user, justificativa=justificativa)
            serializer = self.get_serializer(solicitacao_dieta_especial)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)  # noqa

    @action(detail=True,
            methods=['patch'],
            url_path=constants.TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
            permission_classes=(UsuarioTerceirizada,))
    def terceirizada_toma_ciencia_inativacao(self, request, uuid=None):
        solicitacao_dieta_especial = self.get_object()
        try:
            solicitacao_dieta_especial.terceirizada_toma_ciencia_inativacao(
                user=request.user)
            serializer = self.get_serializer(solicitacao_dieta_especial)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)  # noqa

    @action(detail=True, methods=['post'], permission_classes=(UsuarioCODAEDietaEspecial,))
    def negar(self, request, uuid=None):
        solicitacao = self.get_object()
        form = NegaDietaEspecialForm(request.data, instance=solicitacao)

        if not form.is_valid():
            return Response(form.errors)

        solicitacao.codae_nega(user=request.user)

        return Response({'mensagem': 'Solicitação de Dieta Especial Negada'})

    @action(detail=True, methods=['post'], permission_classes=(UsuarioTerceirizada,))
    def tomar_ciencia(self, request, uuid=None):
        solicitacao = self.get_object()
        try:
            solicitacao.terceirizada_toma_ciencia(user=request.user)
            return Response({'mensagem': 'Ciente da solicitação de dieta especial'})  # noqa
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)  # noqa

    @action(detail=True, url_path=constants.RELATORIO,
            methods=['get'], permission_classes=(IsAuthenticated,))
    def relatorio(self, request, uuid=None):
        return relatorio_dieta_especial(request, solicitacao=self.get_object())

    @action(detail=True, url_path=constants.PROTOCOLO,
            methods=['get'], permission_classes=(IsAuthenticated,))
    def protocolo(self, request, uuid=None):
        return relatorio_dieta_especial_protocolo(request, solicitacao=self.get_object())  # noqa

    @action(
        detail=True,
        methods=['post'],
        url_path=constants.ESCOLA_CANCELA_DIETA_ESPECIAL
    )
    def escola_cancela_solicitacao(self, request, uuid=None):
        justificativa = request.data.get('justificativa', '')
        solicitacao = self.get_object()
        try:
            solicitacao.cancelar_pedido(
                user=request.user, justificativa=justificativa)
            solicitacao.ativo = False
            solicitacao.save()
            if solicitacao.tipo_solicitacao == 'ALTERACAO_UE':
                solicitacao.dieta_alterada.ativo = True
                solicitacao.dieta_alterada.save()
            serializer = self.get_serializer(solicitacao)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(dict(detail=f'Erro de transição de estado: {e}'), status=HTTP_400_BAD_REQUEST)  # noqa

    def get_queryset_relatorio_quantitativo_solic_dieta_esp(self, form, campos):  # noqa C901
        user = self.request.user
        qs = self.get_queryset()

        if user.tipo_usuario == 'escola':
            qs = qs.filter(aluno__escola=user.vinculo_atual.instituicao)
        elif form.cleaned_data['escola']:
            qs = qs.filter(aluno__escola__in=form.cleaned_data['escola'])
        elif user.tipo_usuario == 'diretoriaregional':
            qs = qs.filter(aluno__escola__diretoria_regional=user.vinculo_atual.instituicao)  # noqa
        elif form.cleaned_data['dre']:
            qs = qs.filter(aluno__escola__diretoria_regional__in=form.cleaned_data['dre'])  # noqa

        if form.cleaned_data['data_inicial']:
            qs = qs.filter(criado_em__date__gte=form.cleaned_data['data_inicial'])  # noqa
        if form.cleaned_data['data_final']:
            qs = qs.filter(criado_em__date__lte=form.cleaned_data['data_final'])  # noqa
        if form.cleaned_data['diagnostico']:
            qs = qs.filter(alergias_intolerancias__in=form.cleaned_data['diagnostico'])  # noqa
        if form.cleaned_data['classificacao']:
            qs = qs.filter(classificacao__in=form.cleaned_data['classificacao'])  # noqa

        STATUS_PENDENTE = ['CODAE_A_AUTORIZAR']
        STATUS_ATIVA = [
            'CODAE_AUTORIZADO',
            'TERCEIRIZADA_TOMOU_CIENCIA',
            'ESCOLA_SOLICITOU_INATIVACAO',
            'CODAE_NEGOU_INATIVACAO'
        ]
        STATUS_INATIVA = [
            'CODAE_AUTORIZOU_INATIVACAO',
            'TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO',
            'TERMINADA_AUTOMATICAMENTE_SISTEMA'
        ]

        when_data = {
            'ativas': When(status__in=STATUS_ATIVA, then=Value('Ativa')),
            'inativas': When(status__in=STATUS_INATIVA, then=Value('Inativa')),
            'pendentes': When(status__in=STATUS_PENDENTE, then=Value('Pendente'))
        }

        if form.cleaned_data['status'] == '':
            whens = when_data.values()
        else:
            whens = [when_data[form.cleaned_data['status']]]

        qs = qs.annotate(
            status_simples=Case(
                *whens,
                default=Value('Outros'),
                output_field=CharField()
            )
        ).exclude(status_simples='Outros').values(*campos).annotate(
            qtde_ativas=Count('status_simples', filter=Q(status_simples='Ativa')),  # noqa
            qtde_inativas=Count('status_simples', filter=Q(status_simples='Inativa')),  # noqa
            qtde_pendentes=Count(
                'status_simples', filter=Q(status_simples='Pendente'))
        ).order_by(*campos)

        return qs

    def get_campos_relatorio_quantitativo_solic_dieta_esp(self, filtros):
        campos = ['aluno__escola__diretoria_regional__nome']
        if len(filtros['escola']) > 0:
            campos.append('aluno__escola__nome')
        return campos

    def get_campos_relatorio_quantitativo_diag_dieta_esp(self, filtros):
        user = self.request.user
        campos = []
        if user.tipo_usuario != 'diretoriaregional' and len(filtros['escola']) == 0:  # noqa
            campos.append('aluno__escola__diretoria_regional__nome')
        else:
            if user.tipo_usuario != 'diretoriaregional':
                campos.append('aluno__escola__diretoria_regional__nome')
        if len(filtros['escola']) > 0:
            campos.append('aluno__escola__nome')
        campos.append('alergias_intolerancias__descricao')
        campos.append('aluno__data_nascimento__year')

        return campos

    def get_campos_relatorio_quantitativo_classificacao_dieta_esp(self, filtros):
        user = self.request.user
        campos = []
        if user.tipo_usuario != 'diretoriaregional' and len(filtros['escola']) == 0:  # noqa
            campos.append('aluno__escola__diretoria_regional__nome')
        else:
            if user.tipo_usuario != 'diretoriaregional':
                campos.append('aluno__escola__diretoria_regional__nome')
        if len(filtros['escola']) > 0:
            campos.append('aluno__escola__nome')
        campos.append('classificacao__nome')

        return campos

    @action(detail=False, methods=['POST'], url_path='relatorio-quantitativo-solic-dieta-esp')
    def relatorio_quantitativo_solic_dieta_esp(self, request):
        form = RelatorioQuantitativoSolicDietaEspForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        campos = self.get_campos_relatorio_quantitativo_solic_dieta_esp(
            form.cleaned_data)
        qs = self.get_queryset_relatorio_quantitativo_solic_dieta_esp(
            form, campos)

        self.pagination_class = RelatorioPagination
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(
            page if page is not None else qs, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['POST'],
        url_path='relatorio-quantitativo-diag-dieta-esp'
    )
    def relatorio_quantitativo_diag_dieta_esp(self, request):
        form = RelatorioQuantitativoSolicDietaEspForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        if self.request.data.get('somente_dietas_ativas'):
            campos = ['alergias_intolerancias__descricao']
        else:
            campos = self.get_campos_relatorio_quantitativo_diag_dieta_esp(form.cleaned_data)  # noqa
        qs = self.get_queryset_relatorio_quantitativo_solic_dieta_esp(form, campos)  # noqa

        self.pagination_class = RelatorioPagination
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(
            page if page is not None else qs, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['POST'],
        url_path='relatorio-quantitativo-classificacao-dieta-esp'
    )
    def relatorio_quantitativo_classificacao_dieta_esp(self, request):
        form = RelatorioQuantitativoSolicDietaEspForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        campos = self.get_campos_relatorio_quantitativo_classificacao_dieta_esp(form.cleaned_data)  # noqa
        qs = self.get_queryset_relatorio_quantitativo_solic_dieta_esp(form, campos)  # noqa

        self.pagination_class = RelatorioPagination
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(
            page if page is not None else qs, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['POST'],
        url_path='imprime-relatorio-quantitativo-solic-dieta-esp'
    )
    def imprime_relatorio_quantitativo_solic_dieta_esp(self, request):
        form = RelatorioQuantitativoSolicDietaEspForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        campos = self.get_campos_relatorio_quantitativo_solic_dieta_esp(
            form.cleaned_data)
        qs = self.get_queryset_relatorio_quantitativo_solic_dieta_esp(
            form, campos)
        user = self.request.user

        return relatorio_quantitativo_solic_dieta_especial(campos, form, qs, user)

    @action(
        detail=False,
        methods=['POST'],
        url_path='imprime-relatorio-quantitativo-classificacao-dieta-esp'
    )
    def imprime_relatorio_quantitativo_classificacao_dieta_esp(self, request):
        form = RelatorioQuantitativoSolicDietaEspForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        campos = self.get_campos_relatorio_quantitativo_classificacao_dieta_esp(
            form.cleaned_data)
        qs = self.get_queryset_relatorio_quantitativo_solic_dieta_esp(
            form, campos)
        user = self.request.user

        return relatorio_quantitativo_classificacao_dieta_especial(campos, form, qs, user)

    @action(
        detail=False,
        methods=['POST'],
        url_path='imprime-relatorio-quantitativo-diag-dieta-esp'
    )
    def imprime_relatorio_quantitativo_diag_dieta_esp(self, request):
        form = RelatorioQuantitativoSolicDietaEspForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        campos = self.get_campos_relatorio_quantitativo_diag_dieta_esp(form.cleaned_data)  # noqa
        qs = self.get_queryset_relatorio_quantitativo_solic_dieta_esp(form, campos)  # noqa
        user = self.request.user
        return relatorio_quantitativo_diag_dieta_especial(campos, form, qs, user)

    @action(
        detail=False,
        methods=['POST'],
        url_path='imprime-relatorio-quantitativo-diag-dieta-esp/somente-dietas-ativas'
    )
    def imprime_relatorio_quantitativo_diag_dieta_esp_somente_dietas_ativas(self, request):  # noqa
        form = RelatorioQuantitativoSolicDietaEspForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        if self.request.data.get('somente_dietas_ativas'):
            campos = ['alergias_intolerancias__descricao']
        else:
            campos = self.get_campos_relatorio_quantitativo_diag_dieta_esp(form.cleaned_data)  # noqa
        qs = self.get_queryset_relatorio_quantitativo_solic_dieta_esp(form, campos)  # noqa
        user = self.request.user
        return relatorio_quantitativo_diag_dieta_especial_somente_dietas_ativas(campos, form, qs, user)  # noqa

    @action(detail=False, methods=['POST'], url_path='relatorio-dieta-especial')  # noqa C901
    def relatorio_dieta_especial(self, request):
        self.pagination_class = RelatorioPagination
        form = RelatorioDietaForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        queryset = self.filter_queryset(self.get_queryset())
        data = form.cleaned_data
        filtros = {}
        if data['escola']:
            filtros['rastro_escola__uuid__in'] = [
                escola.uuid for escola in data['escola']]
        if data['diagnostico']:
            filtros['alergias_intolerancias__id__in'] = [
                disgnostico.id for disgnostico in data['diagnostico']]
        page = self.paginate_queryset(queryset.filter(**filtros))
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['POST'], url_path='imprime-relatorio-dieta-especial')  # noqa C901
    def imprime_relatorio_dieta_especial(self, request):
        form = RelatorioDietaForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)
        queryset = self.filter_queryset(self.get_queryset())
        data = form.cleaned_data
        filtros = {}
        if data['escola']:
            filtros['rastro_escola__uuid__in'] = [
                escola.uuid for escola in data['escola']]
        if data['diagnostico']:
            filtros['alergias_intolerancias__id__in'] = [
                disgnostico.id for disgnostico in data['diagnostico']]

        user = self.request.user
        return relatorio_geral_dieta_especial(form, queryset.filter(**filtros), user)  # noqa

    @action(detail=False, methods=['POST'], url_path='panorama-escola')
    def panorama_escola(self, request):
        # TODO: Mover essa rotina para o viewset escola simples, evitando esse
        # form
        form = PanoramaForm(self.request.data)
        if not form.is_valid():
            raise ValidationError(form.errors)

        hoje = date.today()

        filtros_gerais = Q(
            escola__aluno__periodo_escolar=F('periodo_escolar'),
            escola__aluno__escola=form.cleaned_data['escola'],
            escola__aluno__dietas_especiais__ativo=True,
            escola__aluno__dietas_especiais__status__in=[
                DietaEspecialWorkflow.CODAE_AUTORIZADO,
                DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
                DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO
            ],
        )
        filtros_data_dieta = (
            (
                Q(escola__aluno__dietas_especiais__data_termino__isnull=True) |
                Q(escola__aluno__dietas_especiais__data_termino__gte=hoje)
            )
            &
            (
                Q(escola__aluno__dietas_especiais__data_inicio__isnull=True)
                &
                Q(escola__aluno__dietas_especiais__criado_em__date__lte=hoje)
                |
                Q(escola__aluno__dietas_especiais__data_inicio__isnull=False)
                &
                Q(escola__aluno__dietas_especiais__data_inicio__lte=hoje)
            )
        )

        q_params = filtros_gerais & filtros_data_dieta

        campos = [
            'periodo_escolar__nome',
            'horas_atendimento',
            'quantidade_alunos',
            'uuid',
        ]
        qs = EscolaPeriodoEscolar.objects.filter(
            escola=form.cleaned_data['escola'], quantidade_alunos__gt=0
        ).values(*campos).annotate(
            qtde_tipo_a=(Count('id', filter=Q(
                escola__aluno__dietas_especiais__classificacao__nome='Tipo A'
            ) & q_params)),
            qtde_enteral=(Count('id', filter=Q(
                escola__aluno__dietas_especiais__classificacao__nome='Tipo A Enteral'
            ) & q_params)),
            qtde_tipo_b=(Count('id', filter=Q(
                escola__aluno__dietas_especiais__classificacao__nome='Tipo B'
            ) & q_params)),
        ).order_by(*campos)

        serializer = self.get_serializer(qs, many=True)

        return Response(serializer.data)

    @action(detail=False, methods=['POST'], url_path='alteracao-ue')
    def alteracao_ue(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class SolicitacoesAtivasInativasPorAlunoView(generics.ListAPIView):
    serializer_class = SolicitacoesAtivasInativasPorAlunoSerializer
    pagination_class = RelatorioPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        total_ativas = queryset.aggregate(Sum('ativas'))
        total_inativas = queryset.aggregate(Sum('inativas'))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'total_ativas': total_ativas['ativas__sum'],
                'total_inativas': total_inativas['inativas__sum'],
                'solicitacoes': serializer.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'total_ativas': total_ativas['ativas__sum'],
            'total_inativas': total_inativas['inativas__sum'],
            'solicitacoes': serializer.data
        })

    def get_queryset(self):  # noqa C901
        form = SolicitacoesAtivasInativasPorAlunoForm(self.request.GET)
        if not form.is_valid():
            raise ValidationError(form.errors)

        user = self.request.user

        instituicao = user.vinculo_atual.instituicao
        if user.tipo_usuario == 'escola':
            dietas_autorizadas = SolicitacoesEscola.get_autorizados_dieta_especial(escola_uuid=instituicao.uuid)
            dietas_inativas = SolicitacoesEscola.get_inativas_dieta_especial(escola_uuid=instituicao.uuid)
        elif user.tipo_usuario == 'diretoriaregional':
            dietas_autorizadas = SolicitacoesDRE.get_autorizados_dieta_especial(dre_uuid=instituicao.uuid)
            dietas_inativas = SolicitacoesDRE.get_inativas_dieta_especial(dre_uuid=instituicao.uuid)
        else:
            dietas_autorizadas = SolicitacoesCODAE.get_autorizados_dieta_especial()
            dietas_inativas = SolicitacoesCODAE.get_inativas_dieta_especial()

        # Retorna somente Dietas Autorizadas
        ids_dietas_autorizadas = dietas_autorizadas.values_list('id', flat=True)

        # Retorna somente Dietas Inativas.
        ids_dietas_inativas = dietas_inativas.values_list('id', flat=True)

        INATIVOS_STATUS_DIETA_ESPECIAL = [
            'CODAE_AUTORIZADO',
            'CODAE_AUTORIZOU_INATIVACAO',
            'TERMINADA_AUTOMATICAMENTE_SISTEMA'
        ]

        # Retorna somente Dietas Autorizadas e Inativas.
        qs = Aluno.objects.filter(
            dietas_especiais__status__in=INATIVOS_STATUS_DIETA_ESPECIAL).annotate(
            ativas=Count('dietas_especiais', filter=Q(dietas_especiais__id__in=ids_dietas_autorizadas)),
            inativas=Count('dietas_especiais', filter=Q(dietas_especiais__id__in=ids_dietas_inativas)),
        ).filter(Q(ativas__gt=0) | Q(inativas__gt=0))

        if user.tipo_usuario == 'escola':
            qs = qs.filter(escola=user.vinculo_atual.instituicao)
        elif form.cleaned_data['escola']:
            qs = qs.filter(escola=form.cleaned_data['escola'])
        elif user.tipo_usuario == 'diretoriaregional':
            qs = qs.filter(escola__diretoria_regional=user.vinculo_atual.instituicao)
        elif form.cleaned_data['dre']:
            qs = qs.filter(escola__diretoria_regional=form.cleaned_data['dre'])

        if form.cleaned_data['codigo_eol']:
            codigo_eol = f"{int(form.cleaned_data['codigo_eol']):06d}"
            qs = qs.filter(codigo_eol=codigo_eol)
        elif form.cleaned_data['nome_aluno']:
            qs = qs.filter(nome__icontains=form.cleaned_data['nome_aluno'])

        if self.request.user.tipo_usuario == 'dieta_especial':
            return qs.order_by(
                'escola__diretoria_regional__nome',
                'escola__nome',
                'nome'
            )
        elif self.request.user.tipo_usuario == 'diretoriaregional':
            return qs.order_by('escola__nome', 'nome')
        return qs.order_by('nome')


class AlergiaIntoleranciaViewSet(
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        GenericViewSet):
    queryset = AlergiaIntolerancia.objects.all()
    serializer_class = AlergiaIntoleranciaSerializer
    pagination_class = None


class ClassificacaoDietaViewSet(
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        GenericViewSet):
    queryset = ClassificacaoDieta.objects.order_by('nome')
    serializer_class = ClassificacaoDietaSerializer
    pagination_class = None


class MotivoNegacaoViewSet(
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        GenericViewSet):
    queryset = MotivoNegacao.objects.all()
    serializer_class = MotivoNegacaoSerializer
    pagination_class = None


class AlimentoViewSet(
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        GenericViewSet):
    queryset = Alimento.objects.all().order_by('nome')
    serializer_class = AlimentoSerializer
    pagination_class = None
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = AlimentoFilter


class TipoContagemViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = TipoContagem.objects.all().order_by('nome')
    serializer_class = TipoContagemSerializer
    pagination_class = None
    verbose_name = 'Tipo de Contagem'
    verbose_name_plural = 'Tipos de Contagem'


class MotivoAlteracaoUEViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = MotivoAlteracaoUE.objects.order_by('nome')
    serializer_class = MotivoAlteracaoUESerializer


class ProtocoloPadraoDietaEspecialViewSet(ModelViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    queryset = ProtocoloPadraoDietaEspecial.objects.all().order_by('nome_protocolo')
    serializer_class = ProtocoloPadraoDietaEspecialSerializer
    pagination_class = ProtocoloPadraoPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('nome_protocolo', 'status')

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return ProtocoloPadraoDietaEspecialSerializerCreate
        else:
            return ProtocoloPadraoDietaEspecialSerializer

    @action(detail=False, methods=['GET'], url_path='lista-status')
    def lista_status(self, request):
        list_status = ProtocoloPadraoDietaEspecial.STATUS_NOMES.keys()

        return Response({'results': list_status})

    @action(detail=False, methods=['GET'], url_path='nomes')
    def nomes(self, request):
        nomes = self.queryset.values_list('nome_protocolo', flat=True).distinct()

        return Response({'results': nomes})

    @action(detail=False, methods=['GET'], url_path='lista-protocolos-liberados')
    def lista_protocolos_liberados(self, request):
        protocolos_liberados = self.get_queryset().filter(status=ProtocoloPadraoDietaEspecial.STATUS_LIBERADO)
        response = {'results': ProtocoloPadraoDietaEspecialSimplesSerializer(protocolos_liberados, many=True).data}
        return Response(response)
