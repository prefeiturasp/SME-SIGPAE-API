"""Viewsets da API base do modulo de cardapio.

Expoe endpoints para consulta e manutencao de tipos de alimentacao, horarios
por escola, vinculos de periodo/tipo de unidade escolar e motivos de nao
validacao usados pela DRE.
"""

import datetime

from django.core.exceptions import ValidationError
from django.db.models import Case, IntegerField, Value, When
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from src.cardapio.base.api.serializers import (
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializer,
    MotivoDRENaoValidaSerializer,
    TipoAlimentacaoSerializer,
    TipoUnidadeEscolarAgrupadoSerializer,
    VinculoTipoAlimentoSimplesSerializer,
)
from src.cardapio.base.api.serializers_create import (
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializerCreate,
    VinculoTipoAlimentoCreateSerializer,
)
from src.cardapio.base.models import (
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
    MotivoDRENaoValida,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from src.cardapio.utils import ordem_periodos
from src.dados_comuns import constants
from src.escola.api.viewsets import PeriodoEscolarViewSet
from src.escola.constants import PERIODOS_ESPECIAIS_CEMEI
from src.escola.models import Escola, PeriodoEscolar
from src.inclusao_alimentacao.models import (
    InclusaoAlimentacaoNormal,
    InclusaoDeAlimentacaoCEMEI,
    QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI,
    QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEI,
    QuantidadePorPeriodo,
)


class TipoAlimentacaoViewSet(viewsets.ModelViewSet):
    """Expoe o CRUD de tipos de alimentacao da base de cardapio.

    Utiliza ``TipoAlimentacaoSerializer`` em todas as acoes padrao do
    ``ModelViewSet`` e identifica instancias pelo campo ``uuid``.
    """

    lookup_field = "uuid"
    serializer_class = TipoAlimentacaoSerializer
    queryset = TipoAlimentacao.objects.all()


class HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarViewSet(viewsets.ModelViewSet):
    """Gerencia horarios de tipos de alimentacao configurados por escola.

    Disponibiliza leitura, criacao, atualizacao e uma action customizada para
    listar os horarios associados a uma escola especifica.
    """

    lookup_field = "uuid"
    serializer_class = HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializer
    queryset = HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar.objects.all()

    @action(detail=False, url_path="escola/(?P<escola_uuid>[^/.]+)")
    def filtro_por_escola(self, request, escola_uuid=None):
        """Lista horarios cadastrados para a escola informada.

        Args:
            request (Request): Requisicao HTTP recebida pela action.
            escola_uuid (str | None): UUID da escola usado como filtro.

        Returns:
            Response: Resposta paginada com os horarios encontrados para a
            escola.
        """
        combos = HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar.objects.filter(
            escola__uuid=escola_uuid
        )
        page = self.paginate_queryset(combos)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def get_serializer_class(self):
        """Seleciona o serializer de leitura ou escrita conforme a acao.

        Returns:
            type: ``HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializerCreate``
            nas acoes de escrita; caso contrario,
            ``HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializer``.
        """
        if self.action in ["create", "update", "partial_update"]:
            return HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializerCreate
        return HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializer


class VinculoTipoAlimentacaoViewSet(
    viewsets.ModelViewSet,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Gerencia vinculos ativos entre tipo de U.E., periodo e alimentacoes.

    Alem das acoes padrao de leitura e escrita, expoe endpoints customizados
    para filtrar vinculos por escola, por tipo de unidade e por cenarios
    especificos de inclusao de alimentacao.
    """

    lookup_field = "uuid"
    serializer_class = VinculoTipoAlimentoSimplesSerializer
    queryset = (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
            ativo=True
        )
    )

    @action(
        detail=False,
        url_path="tipo_unidade_escolar/(?P<tipo_unidade_escolar_uuid>[^/.]+)",
    )
    def filtro_por_tipo_ue(self, request, tipo_unidade_escolar_uuid=None):
        """Lista vinculos ativos de um tipo especifico de unidade escolar.

        Args:
            request (Request): Requisicao HTTP recebida pela action.
            tipo_unidade_escolar_uuid (str | None): UUID do tipo de unidade
                escolar filtrado.

        Returns:
            Response: Resposta paginada com os vinculos encontrados.
        """
        vinculos = (
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                tipo_unidade_escolar__uuid=tipo_unidade_escolar_uuid, ativo=True
            ).order_by("periodo_escolar__posicao")
        )
        page = self.paginate_queryset(vinculos)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def get_vinculos_inclusoes_evento_especifico(
        self, mes, ano, tipo_solicitacao, escola
    ):
        """Busca vinculos necessarios para inclusoes de Evento Especifico.

        Considera inclusoes normais autorizadas por Evento Especifico e cruza
        os periodos obtidos com os vinculos da escola para montar o conjunto de
        vinculos elegiveis.

        Args:
            mes (str | int): Mes de referencia da consulta.
            ano (str | int): Ano de referencia da consulta.
            tipo_solicitacao (str | None): Parametro mantido por compatibilidade
                com a assinatura da chamada.
            escola (Escola): Escola utilizada na filtragem dos grupos e
                vinculos.

        Returns:
            QuerySet[VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar]:
            Vinculos compativeis com o cenario consultado.
        """
        mes_int = int(mes)
        ano_int = int(ano)

        gupos_uuids = (
            InclusaoAlimentacaoNormal.objects.filter(
                data__month=mes_int,
                data__year=ano_int,
                motivo__nome="Evento Específico",
                grupo_inclusao__escola=escola,
                grupo_inclusao__status="CODAE_AUTORIZADO",
            )
            .values_list("grupo_inclusao__uuid", flat=True)
            .distinct()
        )

        periodos_escolares_uuids = escola.periodos_escolares().values_list(
            "uuid", flat=True
        )

        quantidades_por_periodo = QuantidadePorPeriodo.objects.filter(
            grupo_inclusao_normal__uuid__in=gupos_uuids
        ).exclude(periodo_escolar__uuid__in=periodos_escolares_uuids)

        periodos_escolares_uuids_set = set(
            quantidades_por_periodo.values_list("periodo_escolar__uuid", flat=True)
        )

        cemei_qs = InclusaoDeAlimentacaoCEMEI.objects.filter(
            escola=escola,
            status="CODAE_AUTORIZADO",
            dias_motivos_da_inclusao_cemei__data__month=mes_int,
            dias_motivos_da_inclusao_cemei__data__year=ano_int,
            dias_motivos_da_inclusao_cemei__motivo__nome="Evento Específico",
        ).distinct()

        if cemei_qs.exists():
            cemei_uuids = cemei_qs.values_list("uuid", flat=True)
            cemei_periodos = (
                QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI.objects.filter(
                    inclusao_alimentacao_cemei__uuid__in=cemei_uuids
                ).values_list("periodo_escolar__uuid", flat=True)
            )
            periodos_escolares_uuids_set.update(cemei_periodos)
            cemei_cei_periodos = QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEI.objects.filter(
                inclusao_alimentacao_cemei__uuid__in=cemei_uuids
            ).values_list(
                "periodo_escolar__uuid", flat=True
            )
            periodos_escolares_uuids_set.update(cemei_cei_periodos)

        tipo_unidade = "EMEI" if escola.eh_cemei else escola.tipo_unidade.iniciais

        vinculos = (
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                tipo_unidade_escolar__iniciais=tipo_unidade,
                periodo_escolar__nome__in=constants.PERIODOS_INCLUSAO_MOTIVO_ESPECIFICO,
                periodo_escolar__uuid__in=periodos_escolares_uuids_set,
            )
        )
        return vinculos

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{constants.VINCULOS_INCLUSOES_EVENTO_ESPECIFICO_AUTORIZADAS}",
    )
    def vinculos_inclusoes_evento_especifico_autorizadas(self, request):
        """Retorna vinculos usados em inclusoes autorizadas de Evento Especifico.

        Args:
            request (Request): Requisicao HTTP com ``escola_uuid``, ``mes``,
                ``ano`` e ``tipo_solicitacao`` em ``query_params``.

        Returns:
            Response: Lista serializada dos vinculos encontrados.
        """
        escola_uuid = request.query_params.get("escola_uuid")
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")
        tipo_solicitacao = request.query_params.get("tipo_solicitacao")
        escola = Escola.objects.get(uuid=escola_uuid)
        vinculos = self.get_vinculos_inclusoes_evento_especifico(
            mes, ano, tipo_solicitacao, escola
        )
        serializer = self.get_serializer(vinculos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def trata_inclusao_continua_medicao_inicial(
        self, request, escola, ano, pega_atualmente
    ):
        """Calcula os periodos escolares a considerar na inclusao continua.

        Combina os periodos escolares da escola com os periodos extras
        retornados pelo endpoint de inclusao continua, quando o mes e enviado
        na requisicao.

        Args:
            request (Request): Requisicao HTTP com os filtros atuais.
            escola (Escola): Escola cujos periodos serao avaliados.
            ano (str | int): Ano de referencia para consulta dos periodos.
            pega_atualmente (bool | str): Indicador usado pelo metodo
                ``periodos_escolares`` da escola.

        Returns:
            QuerySet[PeriodoEscolar]: Periodos resultantes da combinacao entre
            o calendario regular da escola e a inclusao continua, quando houver.
        """
        mes = request.query_params.get("mes_inclusao_continua", None)
        periodos_escolares_inclusao_continua = None
        if mes:
            periodoEscolarViewset = PeriodoEscolarViewSet()
            response = periodoEscolarViewset.inclusao_continua_por_mes(request)
            if response.data and response.data.get("periodos", None):
                periodos_escolares_inclusao_continua = PeriodoEscolar.objects.filter(
                    uuid__in=list(response.data["periodos"].values())
                )
        periodos_para_filtrar = escola.periodos_escolares(ano, mes, pega_atualmente)

        if periodos_escolares_inclusao_continua:
            periodos_para_filtrar = (
                periodos_para_filtrar | periodos_escolares_inclusao_continua
            )
        return periodos_para_filtrar

    @action(detail=False, url_path="escola/(?P<escola_uuid>[^/.]+)")
    def filtro_por_escola(self, request, escola_uuid=None):
        """Lista vinculos aplicaveis a uma escola em uma data de referencia.

        Para escolas CEMEI, monta uma ordenacao especial por unidade e periodo.
        Nos demais casos, filtra pelos periodos da escola e pela unidade
        historica valida na data consultada.

        Args:
            request (Request): Requisicao HTTP com filtros opcionais como
                ``mes``, ``ano`` e ``pega_atualmente``.
            escola_uuid (str | None): UUID da escola consultada.

        Returns:
            Response: Resposta paginada com os vinculos ordenados para a escola.
        """
        escola = Escola.objects.get(uuid=escola_uuid)
        mes = request.query_params.get("mes", datetime.date.today().month)
        ano = request.query_params.get("ano", datetime.date.today().year)
        data_referencia = datetime.date(int(ano), int(mes), 1)
        pega_atualmente = request.query_params.get("pega_atualmente", False)
        periodos_para_filtrar = self.trata_inclusao_continua_medicao_inicial(
            request, escola, ano, pega_atualmente
        )

        ordem_personalizada = ordem_periodos(escola, data_referencia)

        if escola.eh_cemei_data(data_referencia):
            ordem_das_unidades = {"CEI DIRET": 1, "EMEI": 2}
            unidades = [
                When(tipo_unidade_escolar__iniciais=key, then=Value(val))
                for key, val in ordem_das_unidades.items()
            ]

            periodo_cases = []
            for unidade, periodos in ordem_personalizada.items():
                for periodo, ordem in periodos.items():
                    periodo_cases.append(
                        When(
                            tipo_unidade_escolar__iniciais=unidade,
                            periodo_escolar__nome=periodo,
                            then=Value(ordem),
                        )
                    )
            vinculos = (
                VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                    periodo_escolar__nome__in=PERIODOS_ESPECIAIS_CEMEI,
                    tipo_unidade_escolar__iniciais__in=ordem_das_unidades.keys(),
                )
                .annotate(
                    unidade_order=Case(
                        *unidades, default=Value(99), output_field=IntegerField()
                    ),
                    periodo_order=Case(
                        *periodo_cases, default=Value(99), output_field=IntegerField()
                    ),
                )
                .order_by("unidade_order", "periodo_order")
            )

        else:
            condicoes_ordenacao = [
                When(periodo_escolar__nome=nome, then=Value(prioridade))
                for nome, prioridade in ordem_personalizada.items()
            ]
            vinculos = (
                VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                    periodo_escolar__in=periodos_para_filtrar, ativo=True
                )
                .annotate(
                    ordem_personalizada=Case(
                        *condicoes_ordenacao,
                        default=Value(99),  # Valor alto para períodos não listados
                        output_field=IntegerField(),
                    )
                )
                .order_by("ordem_personalizada")
            )
            vinculos = vinculos.filter(
                tipo_unidade_escolar=escola.tipo_unidade_historico(data_referencia)
            )
        page = self.paginate_queryset(vinculos)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        url_path="atualizar_lista_de_vinculos",
        methods=["put"],
    )
    def atualizar_lista_de_vinculos(self, request):
        """Atualiza em lote os tipos de alimentacao de uma lista de vinculos.

        Args:
            request (Request): Requisicao HTTP cujo corpo deve conter a chave
                ``vinculos`` com UUIDs e listas de ``tipos_alimentacao``.

        Returns:
            Response: Resposta paginada com os vinculos atualizados, ou erro 400
            quando o payload obrigatorio nao e informado.
        """
        try:
            if "vinculos" not in request.data:
                raise AssertionError("vinculos é um parâmetro obrigatório")
            vinculos_from_request = request.data.get("vinculos", [])
            for vinculo in vinculos_from_request:
                vinculo_class = (
                    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar
                )
                instance = vinculo_class.objects.get(uuid=vinculo["uuid"])
                instance.tipos_alimentacao.set(
                    TipoAlimentacao.objects.filter(
                        uuid__in=vinculo["tipos_alimentacao"]
                    )
                )
                instance.save()
            vinculos_uuids = [vinculo["uuid"] for vinculo in vinculos_from_request]
            vinculos = vinculo_class.objects.filter(uuid__in=vinculos_uuids)
            page = self.paginate_queryset(vinculos)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        except AssertionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["GET"], url_path="motivo_inclusao_especifico")
    def motivo_inclusao_especifico(self, request):
        """Lista vinculos permitidos para o motivo de inclusao especifico.

        Args:
            request (Request): Requisicao HTTP que deve informar
                ``tipo_unidade_escolar_iniciais`` em ``query_params``.

        Returns:
            Response: Lista serializada dos vinculos filtrados ou erro 400
            quando o parametro obrigatorio nao e enviado.
        """
        try:
            tipo_unidade_escolar_iniciais = request.query_params.get(
                "tipo_unidade_escolar_iniciais", ""
            )
            if tipo_unidade_escolar_iniciais:
                vinculos = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                    tipo_unidade_escolar__iniciais=tipo_unidade_escolar_iniciais,
                    periodo_escolar__nome__in=constants.PERIODOS_INCLUSAO_MOTIVO_ESPECIFICO,
                )
                serializer = self.get_serializer(vinculos, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                raise ValidationError(
                    "tipo_unidade_escolar_iniciais é obrigatório via query_params"
                )
        except ValidationError as e:
            return Response({"detail": e}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        """Seleciona o serializer de escrita ou leitura conforme a acao.

        Returns:
            type: ``VinculoTipoAlimentoCreateSerializer`` nas acoes de escrita;
            caso contrario, ``VinculoTipoAlimentoSimplesSerializer``.
        """
        if self.action in ["create", "update", "partial_update"]:
            return VinculoTipoAlimentoCreateSerializer
        return VinculoTipoAlimentoSimplesSerializer


class MotivosDRENaoValidaViewSet(viewsets.ReadOnlyModelViewSet):
    """Expoe consulta somente leitura dos motivos de nao validacao da DRE."""

    lookup_field = "uuid"
    queryset = MotivoDRENaoValida.objects.all()
    serializer_class = MotivoDRENaoValidaSerializer


class VinculosPorTipoUnidadeEscolarViewSet(mixins.ListModelMixin, GenericViewSet):
    """Lista vinculos ativos agrupados por tipo de unidade escolar.

    Usa um serializer agregador para montar a resposta final a partir dos
    vinculos e seus relacionamentos pre-carregados.
    """

    def list(self, request):
        """Lista todos os tipos de U.E. com seus periodos e alimentacoes.

        Args:
            request (Request): Requisicao HTTP recebida pela action ``list``.

        Returns:
            Response: Resposta no formato ``{"results": [...]}`` contendo os
            tipos de unidade escolar agrupados com seus periodos e tipos de
            alimentacao.
        """
        vinculos = (
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                ativo=True, tipo_unidade_escolar__ativo=True
            )
            .select_related("tipo_unidade_escolar", "periodo_escolar")
            .prefetch_related("tipos_alimentacao")
        )

        dados_agrupados = (
            TipoUnidadeEscolarAgrupadoSerializer.agrupar_vinculos_por_tipo_ue(vinculos)
        )
        serializer = TipoUnidadeEscolarAgrupadoSerializer(dados_agrupados, many=True)

        return Response({"results": serializer.data})
