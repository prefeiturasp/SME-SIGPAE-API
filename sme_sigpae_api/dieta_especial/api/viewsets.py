import json
from collections import defaultdict
from datetime import datetime

from django.db.models import Q
from django.forms import ValidationError
from django_filters import rest_framework as filters
from rest_framework import generics, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from sme_sigpae_api.dieta_especial.solicitacao_dieta_especial.models import (
    MotivoAlteracaoUE,
    MotivoNegacao,
    SolicitacaoDietaEspecial,
)
from sme_sigpae_api.escola.models import Escola
from sme_sigpae_api.paineis_consolidados.models import SolicitacoesCODAE

from ...escola.models import Aluno
from ...terceirizada.models import Contrato, Edital
from ..forms import SolicitacoesAtivasInativasPorAlunoForm
from ..protocolo_padrao.models import (
    Alimento,
    ProtocoloPadraoDietaEspecial,
)
from ..solicitacao_dieta_especial.models import (
    AlergiaIntolerancia,
    ClassificacaoDieta,
)
from ..utils import (
    ProtocoloPadraoPagination,
    RelatorioPagination,
    filtrar_alunos_com_dietas_nos_status_e_rastro_escola,
)
from .filters import (
    AlimentoFilter,
    MotivoNegacaoFilter,
)
from .serializers import (
    AlergiaIntoleranciaSerializer,
    AlimentoSerializer,
    ClassificacaoDietaSerializer,
    MotivoAlteracaoUESerializer,
    MotivoNegacaoSerializer,
    ProtocoloPadraoDietaEspecialSerializer,
    ProtocoloPadraoDietaEspecialSimplesSerializer,
    SolicitacoesAtivasInativasPorAlunoSerializer,
)
from .serializers_create import ProtocoloPadraoDietaEspecialSerializerCreate

MSG_DRE_NAO_INFORMADA = "(DRE não informada)"


class SolicitacoesAtivasInativasPorAlunoView(generics.ListAPIView):
    serializer_class = SolicitacoesAtivasInativasPorAlunoSerializer

    def _qs_ativas_view(self):
        return (
            SolicitacoesCODAE.get_autorizados_dieta_especial()
            | SolicitacoesCODAE.get_autorizadas_temporariamente_dieta_especial()
        ).distinct()

    def _qs_inativas_view(self):
        return (
            SolicitacoesCODAE.get_cancelados_dieta_especial()
            | SolicitacoesCODAE.get_inativas_dieta_especial()
            | SolicitacoesCODAE.get_inativas_temporariamente_dieta_especial()
        ).distinct()

    def aplicar_filtros_escola_view(
        self,
        qs,
        escola_filtrada=None,
        codigo_eol_escola=None,
        dre_filtrada=None,
        user=None,
    ):
        if escola_filtrada:
            return self._filtrar_por_escola(qs, escola_filtrada)

        if codigo_eol_escola:
            escola_uuid = (
                Escola.objects.filter(codigo_eol=codigo_eol_escola)
                .values_list("uuid", flat=True)
                .first()
            )

            if escola_uuid:
                escola_uuid_str = str(escola_uuid)
                return qs.filter(
                    Q(escola_uuid=escola_uuid_str)
                    | Q(escola_destino_uuid=escola_uuid_str)
                )
            return qs.none()

        if user:
            return self._filtrar_por_usuario(qs, user)

        if dre_filtrada:
            return self._filtrar_por_dre(qs, dre_filtrada)

        return qs

    def _filtrar_por_escola(self, qs, escola):
        escola_uuid = getattr(escola, "uuid", escola)
        return qs.filter(escola_uuid=escola_uuid)

    def _filtrar_por_dre(self, qs, dre):
        dre_uuid = getattr(dre, "uuid", dre)
        return qs.filter(dre_uuid=dre_uuid)

    def _filtrar_por_usuario(self, qs, user):
        tipo_usuario = getattr(user, "tipo_usuario", None)
        if tipo_usuario == "escola":
            return self._filtrar_por_escola_usuario(qs, user)
        if tipo_usuario == "diretoriaregional":
            return self._filtrar_por_dre_usuario(qs, user)
        return qs

    def _filtrar_por_escola_usuario(self, qs, user):
        instituicao = getattr(user.vinculo_atual, "instituicao", None)
        escola_uuid = getattr(instituicao, "uuid", None)
        if escola_uuid:
            return qs.filter(escola_uuid=escola_uuid)
        return qs

    def _filtrar_por_dre_usuario(self, qs, user):
        instituicao = getattr(user.vinculo_atual, "instituicao", None)
        dre_uuid = getattr(instituicao, "uuid", None)
        if dre_uuid:
            return qs.filter(dre_uuid=dre_uuid)
        return qs

    def calcular_totais(self, alunos_qs, **filtros):
        codigos_eol = alunos_qs.values_list("codigo_eol", flat=True).distinct()
        nomes_alunos = alunos_qs.values_list("nome", flat=True).distinct()

        ativas_qs = self._qs_ativas_view().filter(
            Q(codigo_eol_aluno__in=codigos_eol)
            | Q(nome_aluno__in=nomes_alunos, codigo_eol_aluno__isnull=True)
        )
        ativas_qs = self.aplicar_filtros_escola_view(ativas_qs, **filtros)
        total_ativas = ativas_qs.values("uuid").distinct().count()

        inativas_qs = self._qs_inativas_view().filter(
            Q(codigo_eol_aluno__in=codigos_eol)
            | Q(nome_aluno__in=nomes_alunos, codigo_eol_aluno__isnull=True)
        )
        inativas_qs = self.aplicar_filtros_escola_view(inativas_qs, **filtros)
        total_inativas = inativas_qs.values("uuid").distinct().count()

        return total_ativas, total_inativas

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        alunos_ids = queryset.values_list("id", flat=True).distinct()
        alunos_qs = Aluno.objects.filter(id__in=alunos_ids)

        filtros = self._obter_filtros(request)
        total_ativas, total_inativas = self.calcular_totais(alunos_qs, **filtros)

        escolas_por_aluno = self._obter_escolas_por_aluno(alunos_qs, filtros)
        alunos_por_escola = self._criar_alunos_por_escola(alunos_qs, escolas_por_aluno)

        return self._criar_resposta(
            request, alunos_por_escola, total_ativas, total_inativas
        )

    def _obter_filtros(self, request):
        form = SolicitacoesAtivasInativasPorAlunoForm(request.GET)
        form.is_valid()

        return {
            "escola_filtrada": form.cleaned_data.get("escola"),
            "dre_filtrada": form.cleaned_data.get("dre"),
            "codigo_eol_escola": request.query_params.get("codigo_eol_escola"),
            "user": request.user,
        }

    def _obter_escolas_por_aluno(self, alunos_qs, filtros):
        codigos_eol = alunos_qs.values_list("codigo_eol", flat=True).distinct()
        nomes_alunos = alunos_qs.values_list("nome", flat=True).distinct()

        dietas_relevantes = (self._qs_ativas_view() | self._qs_inativas_view()).filter(
            Q(codigo_eol_aluno__in=codigos_eol)
            | Q(nome_aluno__in=nomes_alunos, codigo_eol_aluno__isnull=True)
        )

        dietas_relevantes = self.aplicar_filtros_escola_view(
            dietas_relevantes, **filtros
        )

        dietas_data = list(
            dietas_relevantes.values(
                "codigo_eol_aluno",
                "nome_aluno",
                "escola_uuid",
                "escola_nome",
                "dre_nome",
                "tipo_solicitacao_dieta",
                "escola_destino_uuid",
            ).distinct()
        )

        escolas_map = self._criar_mapa_escolas(dietas_data)
        return self._agrupar_escolas_por_aluno(dietas_data, escolas_map)

    def _criar_mapa_escolas(self, dietas_data):
        todas_escolas_uuids = set()

        for row in dietas_data:
            escola_uuid = row.get("escola_uuid")
            if escola_uuid:
                todas_escolas_uuids.add(str(escola_uuid))

            destino_uuid = row.get("escola_destino_uuid")
            if destino_uuid:
                todas_escolas_uuids.add(str(destino_uuid))

        escolas_map = {}
        if todas_escolas_uuids:
            escolas = Escola.objects.filter(
                uuid__in=todas_escolas_uuids
            ).select_related("diretoria_regional")

            for escola in escolas:
                escolas_map[str(escola.uuid)] = {
                    "nome": escola.nome,
                    "dre": (
                        escola.diretoria_regional.nome
                        if escola.diretoria_regional
                        else MSG_DRE_NAO_INFORMADA
                    ),
                    "codigo_eol": escola.codigo_eol,
                }

        return escolas_map

    def _agrupar_escolas_por_aluno(self, dietas_data, escolas_map):
        escolas_por_aluno = defaultdict(set)

        for row in dietas_data:
            eol = row.get("codigo_eol_aluno")
            nome_aluno = row.get("nome_aluno")

            chave_aluno = eol if eol else f"nome_{nome_aluno}"

            if not chave_aluno:
                continue

            self._adicionar_escola_origem(
                escolas_por_aluno, row, escolas_map, chave_aluno
            )
            self._adicionar_escola_destino(
                escolas_por_aluno, row, escolas_map, chave_aluno
            )

        return escolas_por_aluno

    def _adicionar_escola_origem(self, escolas_por_aluno, row, escolas_map, eol):
        escola_uuid = row.get("escola_uuid")
        if not escola_uuid:
            return

        escola_uuid_str = str(escola_uuid)
        escola_info = escolas_map.get(
            escola_uuid_str,
            {
                "nome": row.get("escola_nome") or "(Escola não encontrada)",
                "dre": row.get("dre_nome") or MSG_DRE_NAO_INFORMADA,
                "codigo_eol": None,
            },
        )

        escolas_por_aluno[eol].add(
            (
                escola_uuid_str,
                escola_info["nome"],
                escola_info["dre"],
                escola_info["codigo_eol"],
            )
        )

    def _adicionar_escola_destino(self, escolas_por_aluno, row, escolas_map, eol):
        if row.get("tipo_solicitacao_dieta") != "ALTERACAO_UE":
            return

        escola_destino_uuid = row.get("escola_destino_uuid")
        if not escola_destino_uuid:
            return

        escola_destino_uuid_str = str(escola_destino_uuid)
        escola_info = escolas_map.get(
            escola_destino_uuid_str,
            {
                "nome": "(Escola não encontrada)",
                "dre": MSG_DRE_NAO_INFORMADA,
                "codigo_eol": None,
            },
        )

        escolas_por_aluno[eol].add(
            (
                escola_destino_uuid_str,
                escola_info["nome"],
                escola_info["dre"],
                escola_info["codigo_eol"],
            )
        )

    def _criar_alunos_por_escola(self, alunos_qs, escolas_por_aluno):
        alunos_por_escola = []
        for aluno in alunos_qs:
            chave_aluno = aluno.codigo_eol if aluno.codigo_eol else f"nome_{aluno.nome}"
            escolas_aluno = escolas_por_aluno.get(chave_aluno, set())

            if not escolas_aluno:
                alunos_por_escola.append(self._criar_copia_aluno_sem_escola(aluno))
            else:
                for escola_uuid, escola_nome, dre_nome, codigo_eol in escolas_aluno:
                    alunos_por_escola.append(
                        self._criar_copia_aluno_com_escola(
                            aluno, escola_uuid, escola_nome, dre_nome, codigo_eol
                        )
                    )

        alunos_por_escola.sort(
            key=lambda x: ((x._escola_nome or "").upper(), x.nome.upper())
        )
        return alunos_por_escola

    def _criar_copia_aluno_sem_escola(self, aluno):
        from copy import copy

        copia = copy(aluno)
        copia._escola_contexto_id = None
        copia._escola_nome = "(Sem escola vinculada)"
        copia._escola_dre = MSG_DRE_NAO_INFORMADA
        copia._escola_codigo_eol = None
        return copia

    def _criar_copia_aluno_com_escola(
        self, aluno, escola_uuid, escola_nome, dre_nome, codigo_eol
    ):
        from copy import copy

        copia = copy(aluno)
        copia._escola_contexto_id = escola_uuid
        copia._escola_nome = escola_nome
        copia._escola_dre = dre_nome
        copia._escola_codigo_eol = codigo_eol
        return copia

    def _criar_resposta(self, request, alunos_por_escola, total_ativas, total_inativas):
        paginar = request.GET.get("page", False)

        if paginar:
            return self._criar_resposta_paginada(
                request, alunos_por_escola, total_ativas, total_inativas
            )

        serializer = self.get_serializer(alunos_por_escola, many=True)
        return Response(
            {
                "total_ativas": total_ativas,
                "total_inativas": total_inativas,
                "solicitacoes": serializer.data,
            }
        )

    def _criar_resposta_paginada(
        self, request, alunos_por_escola, total_ativas, total_inativas
    ):
        self.pagination_class = RelatorioPagination
        page = self.paginate_queryset(alunos_por_escola)
        serializer = self.get_serializer(page, many=True, context={"request": request})

        return self.get_paginated_response(
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
            "ESCOLA_CANCELOU",
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
        else:
            if form.cleaned_data["escola"]:
                if incluir_alteracao_ue:
                    qs = qs.filter(
                        Q(
                            dietas_especiais__rastro_escola=form.cleaned_data["escola"],
                            dietas_especiais__status__in=["CODAE_AUTORIZADO"],
                            dietas_especiais__ativo=True,
                            dietas_especiais__tipo_solicitacao="COMUM",
                        )
                        | Q(
                            dietas_especiais__escola_destino=form.cleaned_data[
                                "escola"
                            ],
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

            else:
                codigo_eol_escola = self.request.query_params.get("codigo_eol_escola")
                if codigo_eol_escola:
                    if incluir_alteracao_ue:
                        qs = qs.filter(
                            Q(
                                dietas_especiais__rastro_escola__codigo_eol=codigo_eol_escola,
                                dietas_especiais__status__in=["CODAE_AUTORIZADO"],
                                dietas_especiais__ativo=True,
                                dietas_especiais__tipo_solicitacao="COMUM",
                            )
                            | Q(
                                dietas_especiais__escola_destino__codigo_eol=codigo_eol_escola,
                                dietas_especiais__status__in=["CODAE_AUTORIZADO"],
                                dietas_especiais__ativo=True,
                                dietas_especiais__tipo_solicitacao="ALTERACAO_UE",
                            )
                        )
                    else:
                        qs = qs.filter(
                            dietas_especiais__rastro_escola__codigo_eol=codigo_eol_escola
                        )

        if form.cleaned_data["codigo_eol"]:
            codigo_eol = f"{int(form.cleaned_data['codigo_eol']):06d}"
            qs = qs.filter(codigo_eol=codigo_eol)
        elif form.cleaned_data["nome_aluno"]:
            qs = qs.filter(nome__icontains=form.cleaned_data["nome_aluno"])

        series = self.request.query_params.getlist("serie")
        if series:
            qs = qs.filter(Q(*[Q(serie__icontains=s) for s in series], _connector=Q.OR))
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


class MotivoAlteracaoUEViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = MotivoAlteracaoUE.objects.filter(ativo=True).order_by("nome")
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
