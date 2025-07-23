import datetime

from django.db.models.query import QuerySet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from ...dados_comuns.constants import FILTRO_PADRAO_PEDIDOS, SEM_FILTRO
from ...dados_comuns.permissions import (
    PermissaoParaRecuperarDietaEspecial,
    UsuarioCODAEDietaEspecial,
    UsuarioCODAEGabinete,
    UsuarioCODAERelatorios,
    UsuarioDinutreDiretoria,
    UsuarioDiretoriaRegional,
    UsuarioGticCODAE,
    UsuarioNutricionista,
    UsuarioTerceirizada,
)
from ...dieta_especial.models import SolicitacaoDietaEspecial
from ...paineis_consolidados.api.constants import (
    PESQUISA,
    TIPO_VISAO,
    TIPO_VISAO_LOTE,
    TIPO_VISAO_SOLICITACOES,
)
from ...paineis_consolidados.api.serializers import SolicitacoesSerializer
from ...relatorios.relatorios import (
    relatorio_filtro_periodo,
    relatorio_resumo_anual_e_mensal,
)
from ..api.constants import PENDENTES_VALIDACAO_DRE, RELATORIO_PERIODO
from ..models import (
    MoldeConsolidado,
    SolicitacoesCODAE,
    SolicitacoesDRE,
    SolicitacoesNutrimanifestacao,
    SolicitacoesNutrisupervisao,
    SolicitacoesTerceirizada,
)
from ..tasks import (
    gera_pdf_relatorio_solicitacoes_alimentacao_async,
    gera_xls_relatorio_solicitacoes_alimentacao_async,
)
from ..utils.datasets_graficos_relatorio_ga import (
    get_dataset_grafico_total_dre_lote,
    get_dataset_grafico_total_status,
    get_dataset_grafico_total_terceirizadas,
    get_dataset_grafico_total_tipo_solicitacao,
    get_dataset_grafico_total_tipo_unidade,
)
from ..utils.totalizadores_relatorio import (
    totalizador_cei_polo_recreio_ferias,
    totalizador_classificacao_dieta,
    totalizador_lote,
    totalizador_periodo,
    totalizador_rede_municipal,
    totalizador_relacao_diagnostico,
    totalizador_tipo_de_gestao,
    totalizador_tipo_solicitacao,
    totalizador_tipo_unidade,
    totalizador_total,
    totalizador_unidade_educacional,
)
from ..validators import FiltroValidator
from .constants import (
    AGUARDANDO_CODAE,
    AGUARDANDO_INICIO_VIGENCIA_DIETA_ESPECIAL,
    AUTORIZADAS_TEMPORARIAMENTE_DIETA_ESPECIAL,
    AUTORIZADOS,
    AUTORIZADOS_DIETA_ESPECIAL,
    CANCELADOS,
    CANCELADOS_DIETA_ESPECIAL,
    FILTRO_DRE_UUID,
    FILTRO_ESCOLA_UUID,
    FILTRO_TERCEIRIZADA_UUID,
    INATIVAS_DIETA_ESPECIAL,
    INATIVAS_TEMPORARIAMENTE_DIETA_ESPECIAL,
    NEGADOS,
    NEGADOS_DIETA_ESPECIAL,
    PENDENTES_AUTORIZACAO,
    PENDENTES_AUTORIZACAO_DIETA_ESPECIAL,
    PENDENTES_CIENCIA,
    QUESTIONAMENTOS,
    RELATORIO_RESUMO_MES_ANO,
    RESUMO_ANO,
    RESUMO_MES,
)


class SolicitacoesViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)

    @classmethod
    def count_query_set_sem_duplicados(cls, query_set):
        return len(set(query_set.values_list("uuid", flat=True)))

    @classmethod
    def remove_duplicados_do_query_set(cls, query_set):
        uuids_repetidos = set()
        return [
            solicitacao
            for solicitacao in query_set
            if solicitacao.uuid not in uuids_repetidos
            and not uuids_repetidos.add(solicitacao.uuid)
        ]

    def _retorno_base(self, query_set, sem_paginacao=None):
        sem_uuid_repetido = self.remove_duplicados_do_query_set(query_set)
        if sem_paginacao:
            serializer = self.get_serializer(sem_uuid_repetido, many=True)
            return Response({"results": serializer.data})
        page = self.paginate_queryset(sem_uuid_repetido)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def _agrupar_solicitacoes(self, tipo_visao: str, query_set: QuerySet):
        if tipo_visao == TIPO_VISAO_SOLICITACOES:
            descricao_prioridade = [
                (solicitacao.desc_doc, solicitacao.prioridade)
                for solicitacao in query_set
                if solicitacao.prioridade != "VENCIDO"
            ]
        elif tipo_visao == TIPO_VISAO_LOTE:
            descricao_prioridade = [
                (solicitacao.lote_nome, solicitacao.prioridade)
                for solicitacao in query_set
                if solicitacao.prioridade != "VENCIDO"
            ]
        else:
            descricao_prioridade = [
                (solicitacao.dre_nome, solicitacao.prioridade)
                for solicitacao in query_set
                if solicitacao.prioridade != "VENCIDO"
            ]
        return descricao_prioridade

    def _agrupa_por_tipo_visao(self, tipo_visao: str, query_set: QuerySet) -> dict:
        sumario = {}  # type: dict
        query_set = self.remove_duplicados_do_query_set(query_set)
        descricao_prioridade = self._agrupar_solicitacoes(tipo_visao, query_set)
        for nome_objeto, prioridade in descricao_prioridade:
            if nome_objeto == "Inclusão de Alimentação Contínua":
                nome_objeto = "Inclusão de Alimentação"
            if nome_objeto not in sumario:
                sumario[nome_objeto] = {
                    "TOTAL": 0,
                    "REGULAR": 0,
                    "PRIORITARIO": 0,
                    "LIMITE": 0,
                }
            sumario[nome_objeto][prioridade] += 1
            sumario[nome_objeto]["TOTAL"] += 1
        return sumario

    def _agrupa_por_mes_por_solicitacao(self, query_set: list) -> dict:
        # TODO: melhorar performance
        sumario = {
            "total": 0,
            "Inclusão de Alimentação": {
                "quantidades": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "total": 0,
            },
            "Alteração do tipo de Alimentação": {
                "quantidades": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "total": 0,
            },
            "Inversão de dia de Cardápio": {
                "quantidades": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "total": 0,
            },
            "Suspensão de Alimentação": {
                "quantidades": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "total": 0,
            },
            "Kit Lanche Passeio": {
                "quantidades": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "total": 0,
            },
            "Kit Lanche Unificado": {
                "quantidades": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "total": 0,
            },
            "Dieta Especial": {
                "quantidades": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "total": 0,
            },
        }  # type: dict
        for solicitacao in query_set:
            if solicitacao["desc_doc"] == "Inclusão de Alimentação Contínua":
                solicitacao["desc_doc"] = "Inclusão de Alimentação"
            sumario[solicitacao["desc_doc"]]["quantidades"][
                solicitacao["criado_em__month"] - 1
            ] += 1
            sumario[solicitacao["desc_doc"]]["total"] += 1
            sumario["total"] += 1
        return sumario

    @action(detail=False, methods=["GET"], url_path="solicitacoes-detalhadas")
    def solicitacoes_detalhadas(self, request):
        solicitacoes = request.query_params.getlist("solicitacoes[]", None)
        solicitacoes = MoldeConsolidado.solicitacoes_detalhadas(solicitacoes, request)
        return Response(dict(data=solicitacoes, status=HTTP_200_OK))

    def filtrar_solicitacoes_para_relatorio_cards_totalizadores(self, request, model):
        list_cards_totalizadores = []

        status = request.data.get("status", None)
        eh_relatorio_dietas_autorizadas = request.data.get(
            "relatorio_dietas_autorizadas", None
        )
        if eh_relatorio_dietas_autorizadas:
            status = "DIETAS_AUTORIZADAS"
        instituicao_uuid = request.user.vinculo_atual.instituicao.uuid
        queryset = model.map_queryset_por_status(
            status, instituicao_uuid=instituicao_uuid
        )

        list_cards_totalizadores = totalizador_rede_municipal(
            request, queryset, list_cards_totalizadores
        )
        if eh_relatorio_dietas_autorizadas:
            cei_polo = request.data.get("cei_polo", False)
            recreio_nas_ferias = request.data.get("recreio_nas_ferias", False)
            if cei_polo and recreio_nas_ferias:
                for string_polo_ou_recreio in ["polo", "recreio"]:
                    list_cards_totalizadores = totalizador_cei_polo_recreio_ferias(
                        request,
                        model,
                        queryset,
                        list_cards_totalizadores,
                        string_polo_ou_recreio,
                    )
                    list_cards_totalizadores = totalizador_lote(
                        request,
                        model,
                        queryset,
                        list_cards_totalizadores,
                        string_polo_ou_recreio,
                    )
                    list_cards_totalizadores = totalizador_unidade_educacional(
                        request,
                        model,
                        queryset,
                        list_cards_totalizadores,
                        string_polo_ou_recreio,
                    )
                    list_cards_totalizadores = totalizador_tipo_de_gestao(
                        request,
                        model,
                        queryset,
                        list_cards_totalizadores,
                        string_polo_ou_recreio,
                    )
                    list_cards_totalizadores = totalizador_tipo_unidade(
                        request,
                        model,
                        queryset,
                        list_cards_totalizadores,
                        string_polo_ou_recreio,
                    )
                    list_cards_totalizadores = totalizador_classificacao_dieta(
                        request,
                        model,
                        queryset,
                        list_cards_totalizadores,
                        string_polo_ou_recreio,
                    )
                    list_cards_totalizadores = totalizador_relacao_diagnostico(
                        request,
                        model,
                        queryset,
                        list_cards_totalizadores,
                        string_polo_ou_recreio,
                    )
            else:
                list_cards_totalizadores = totalizador_cei_polo_recreio_ferias(
                    request, model, queryset, list_cards_totalizadores
                )
                list_cards_totalizadores = totalizador_lote(
                    request, model, queryset, list_cards_totalizadores
                )
                list_cards_totalizadores = totalizador_unidade_educacional(
                    request, model, queryset, list_cards_totalizadores
                )
                list_cards_totalizadores = totalizador_tipo_de_gestao(
                    request, model, queryset, list_cards_totalizadores
                )
                list_cards_totalizadores = totalizador_tipo_unidade(
                    request, model, queryset, list_cards_totalizadores
                )
                list_cards_totalizadores = totalizador_classificacao_dieta(
                    request, model, queryset, list_cards_totalizadores
                )
                list_cards_totalizadores = totalizador_relacao_diagnostico(
                    request, model, queryset, list_cards_totalizadores
                )
        else:
            list_cards_totalizadores = totalizador_total(
                request, model, queryset, list_cards_totalizadores
            )
            list_cards_totalizadores = totalizador_periodo(
                request, model, queryset, list_cards_totalizadores
            )
            list_cards_totalizadores = totalizador_lote(
                request, model, queryset, list_cards_totalizadores
            )
            list_cards_totalizadores = totalizador_tipo_solicitacao(
                request, model, queryset, list_cards_totalizadores
            )
            list_cards_totalizadores = totalizador_tipo_unidade(
                request, model, queryset, list_cards_totalizadores
            )
            list_cards_totalizadores = totalizador_unidade_educacional(
                request, model, queryset, list_cards_totalizadores
            )

        return list_cards_totalizadores

    def filtrar_solicitacoes_para_relatorio_graficos(self, request, instituicao, model):
        status = request.data.get("status", None)
        eh_relatorio_dietas_autorizadas = request.data.get(
            "relatorio_dietas_autorizadas", None
        )
        if eh_relatorio_dietas_autorizadas:
            status = "DIETAS_AUTORIZADAS"
        instituicao_uuid = request.user.vinculo_atual.instituicao.uuid
        queryset = model.map_queryset_por_status(
            status, instituicao_uuid=instituicao_uuid
        )

        datasets = []

        if eh_relatorio_dietas_autorizadas:
            datasets = get_dataset_grafico_total_dre_lote(
                datasets,
                request,
                model,
                instituicao,
                queryset,
                eh_relatorio_dietas_autorizadas,
            )
        else:
            datasets = get_dataset_grafico_total_dre_lote(
                datasets, request, model, instituicao, queryset
            )
            datasets = get_dataset_grafico_total_tipo_solicitacao(
                datasets, request, model, queryset
            )
            datasets = get_dataset_grafico_total_status(
                datasets, request, model, instituicao
            )
            datasets = get_dataset_grafico_total_tipo_unidade(
                datasets, request, model, instituicao, queryset
            )
            datasets = get_dataset_grafico_total_terceirizadas(
                datasets, request, model, instituicao, queryset
            )

        return datasets

    def filtrar_solicitacoes_para_relatorio(self, request, model):
        status = request.data.get("status", None)
        instituicao_uuid = request.user.vinculo_atual.instituicao.uuid
        queryset = model.map_queryset_por_status(
            status, instituicao_uuid=instituicao_uuid
        )
        # filtra por datas
        periodo_datas = {
            "data_evento": request.data.get("de", None),
            "data_evento_fim": request.data.get("ate", None),
        }
        queryset = model.busca_periodo_de_datas(
            queryset,
            data_evento=periodo_datas["data_evento"],
            data_evento_fim=periodo_datas["data_evento_fim"],
        )
        tipo_doc = request.data.get("tipos_solicitacao", None)
        tipo_doc = model.map_queryset_por_tipo_doc(tipo_doc)
        # outros filtros
        map_filtros = {
            "lote_uuid__in": request.data.get("lotes", []),
            "escola_uuid__in": request.data.get("unidades_educacionais", []),
            "terceirizada_uuid": request.data.get("terceirizada", []),
            "tipo_doc__in": tipo_doc,
            "escola_tipo_unidade_uuid__in": request.data.get("tipos_unidade", []),
        }
        filtros = {
            key: value for key, value in map_filtros.items() if value not in [None, []]
        }
        queryset = queryset.filter(**filtros).order_by("escola_nome")
        queryset = self.remove_duplicados_do_query_set(queryset)
        return queryset

    @action(
        detail=False,
        methods=["POST"],
        url_path="filtrar-solicitacoes-ga",
        permission_classes=(IsAuthenticated,),
    )
    def filtrar_solicitacoes_ga(self, request):
        # queryset por status
        offset = request.data.get("offset", 0)
        limit = request.data.get("limit", 10)
        instituicao = request.user.vinculo_atual.instituicao
        queryset = self.filtrar_solicitacoes_para_relatorio(
            request, MoldeConsolidado.classe_por_tipo_usuario(instituicao.__class__)
        )
        return Response(
            data={
                "results": self.get_serializer(
                    queryset[offset : offset + limit], many=True
                ).data,
                "count": len(queryset),
            },
            status=HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["POST"],
        url_path="filtrar-solicitacoes-cards-totalizadores",
        permission_classes=(IsAuthenticated,),
    )
    def filtrar_solicitacoes_cards_totalizadores(self, request):
        # queryset por status
        instituicao = request.user.vinculo_atual.instituicao

        lista_cards_totalizadores = (
            self.filtrar_solicitacoes_para_relatorio_cards_totalizadores(
                request, MoldeConsolidado.classe_por_tipo_usuario(instituicao.__class__)
            )
        )
        return Response(
            data={"results": lista_cards_totalizadores},
            status=HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["POST"],
        url_path="filtrar-solicitacoes-graficos",
        permission_classes=(IsAuthenticated,),
    )
    def filtrar_solicitacoes_graficos(self, request):
        # queryset por status
        instituicao = request.user.vinculo_atual.instituicao
        dataset = self.filtrar_solicitacoes_para_relatorio_graficos(
            request,
            instituicao,
            MoldeConsolidado.classe_por_tipo_usuario(instituicao.__class__),
        )
        return Response(
            data=dataset,
            status=HTTP_200_OK,
        )

    @action(detail=False, methods=["POST"], url_path="exportar-xlsx")
    def exportar_xlsx(self, request):
        instituicao = request.user.vinculo_atual.instituicao
        queryset = self.filtrar_solicitacoes_para_relatorio(
            request, MoldeConsolidado.classe_por_tipo_usuario(instituicao.__class__)
        )
        uuids = [str(solicitacao.uuid) for solicitacao in queryset]
        lotes = request.data.get("lotes", [])
        tipos_solicitacao = request.data.get("tipos_solicitacao", [])
        tipos_unidade = request.data.get("tipos_unidade", [])
        unidades_educacionais = request.data.get("unidades_educacionais", [])

        user = request.user.get_username()
        gera_xls_relatorio_solicitacoes_alimentacao_async.delay(
            user=user,
            nome_arquivo="relatorio_solicitacoes_alimentacao.xlsx",
            data=request.data,
            uuids=uuids,
            lotes=lotes,
            tipos_solicitacao=tipos_solicitacao,
            tipos_unidade=tipos_unidade,
            unidades_educacionais=unidades_educacionais,
        )
        return Response(
            dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["POST"], url_path="exportar-pdf")
    def exportar_pdf(self, request):
        user = request.user.get_username()
        instituicao = request.user.vinculo_atual.instituicao
        queryset = self.filtrar_solicitacoes_para_relatorio(
            request, MoldeConsolidado.classe_por_tipo_usuario(instituicao.__class__)
        )
        uuids = [str(solicitacao.uuid) for solicitacao in queryset]
        gera_pdf_relatorio_solicitacoes_alimentacao_async.delay(
            user=user,
            nome_arquivo="relatorio_solicitacoes_alimentacao.pdf",
            data=request.data,
            uuids=uuids,
            status=request.data.get("status", None),
        )
        return Response(
            dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
            status=status.HTTP_200_OK,
        )


class NutrisupervisaoSolicitacoesViewSet(SolicitacoesViewSet):
    lookup_field = "uuid"
    permission_classes = (IsAuthenticated,)
    queryset = SolicitacoesNutrisupervisao.objects.all()
    serializer_class = SolicitacoesSerializer

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[
            UsuarioCODAEDietaEspecial | UsuarioGticCODAE | UsuarioCODAERelatorios
        ],
        url_name="anos-com-dietas",
        url_path="anos-com-dietas",
    )
    def anos_com_dietas(self, request):
        queryset = SolicitacaoDietaEspecial.objects.all().exclude(
            status=SolicitacaoDietaEspecial.workflow_class.RASCUNHO
        )

        anos = [c.date().year for c in queryset.values_list("criado_em", flat=True)]
        anos_unicos = list(set(anos))
        anos_unicos_ordenados = sorted(anos_unicos, reverse=True)

        return Response(data=anos_unicos_ordenados, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[
            UsuarioCODAEDietaEspecial | UsuarioGticCODAE | UsuarioCODAERelatorios
        ],
        url_name="totais-gerencial-dietas",
        url_path="totais-gerencial-dietas",
    )
    def totais_gerencial_dietas(self, request):
        queryset = (
            SolicitacaoDietaEspecial.objects.all()
            .exclude(status=SolicitacaoDietaEspecial.workflow_class.RASCUNHO)
            .order_by()
        )

        dia = request.query_params.get("dia")
        if dia:
            data = datetime.datetime.strptime(dia, "%d/%m/%Y").date()
            queryset = queryset.filter(criado_em__date=data)
        else:
            anos = request.query_params.get("anos")
            if anos:
                queryset = queryset.filter(criado_em__date__year__in=anos.split(","))

            meses = request.query_params.get("meses")
            if meses:
                queryset = queryset.filter(criado_em__date__month__in=meses.split(","))

        totais = SolicitacaoDietaEspecial.get_totais_gerencial_dietas(queryset)

        return Response(
            data=totais,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{PENDENTES_AUTORIZACAO}/{FILTRO_PADRAO_PEDIDOS}",
        permission_classes=(UsuarioNutricionista,),
    )
    def pendentes_autorizacao(self, request, filtro_aplicado=SEM_FILTRO):
        query_set = SolicitacoesNutrisupervisao.get_pendentes_autorizacao(
            filtro=filtro_aplicado
        )
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=AUTORIZADOS,
        permission_classes=(UsuarioNutricionista,),
    )
    def autorizados(self, request):
        query_set = SolicitacoesNutrisupervisao.get_autorizados()
        query_set = SolicitacoesNutrisupervisao.busca_filtro(
            query_set, request.query_params
        )
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=NEGADOS,
        permission_classes=(UsuarioNutricionista,),
    )
    def negados(self, request):
        query_set = SolicitacoesNutrisupervisao.get_negados()
        query_set = SolicitacoesNutrisupervisao.busca_filtro(
            query_set, request.query_params
        )
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=CANCELADOS,
        permission_classes=(UsuarioNutricionista,),
    )
    def cancelados(self, request):
        query_set = SolicitacoesNutrisupervisao.get_cancelados()
        query_set = SolicitacoesNutrisupervisao.busca_filtro(
            query_set, request.query_params
        )
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{PENDENTES_AUTORIZACAO}/{FILTRO_PADRAO_PEDIDOS}/{TIPO_VISAO}",
    )
    def pendentes_autorizacao_secao_pendencias(
        self, request, filtro_aplicado=SEM_FILTRO, tipo_visao=TIPO_VISAO_SOLICITACOES
    ):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        query_set = SolicitacoesCODAE.get_pendentes_autorizacao(
            dre_uuid=diretoria_regional.uuid, filtro=filtro_aplicado
        )
        response = {
            "results": self._agrupa_por_tipo_visao(
                tipo_visao=tipo_visao, query_set=query_set
            )
        }

        return Response(response)

    @action(detail=False, methods=["GET"], url_path=f"{PENDENTES_AUTORIZACAO}")
    def pendentes_autorizacao_sem_filtro(self, request):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        query_set = SolicitacoesCODAE.get_pendentes_autorizacao(
            dre_uuid=diretoria_regional.uuid
        )
        query_set = SolicitacoesNutrisupervisao.busca_filtro(
            query_set, request.query_params
        )
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=QUESTIONAMENTOS,
        permission_classes=(UsuarioNutricionista,),
    )
    def questionamentos(self, request):
        query_set = SolicitacoesCODAE.get_questionamentos()
        query_set = SolicitacoesNutrisupervisao.busca_filtro(
            query_set, request.query_params
        )
        return self._retorno_base(query_set)


class NutrimanifestacaoSolicitacoesViewSet(SolicitacoesViewSet):
    lookup_field = "uuid"
    permission_classes = (IsAuthenticated,)
    queryset = SolicitacoesNutrimanifestacao.objects.all()
    serializer_class = SolicitacoesSerializer

    @action(
        detail=False,
        methods=["GET"],
        url_path=AUTORIZADOS,
        permission_classes=[
            UsuarioNutricionista | UsuarioCODAEGabinete | UsuarioDinutreDiretoria
        ],
    )
    def autorizados(self, request):
        query_set = SolicitacoesNutrimanifestacao.get_autorizados()
        query_set = SolicitacoesNutrimanifestacao.busca_filtro(
            query_set, request.query_params
        )
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=NEGADOS,
        permission_classes=[
            UsuarioNutricionista | UsuarioCODAEGabinete | UsuarioDinutreDiretoria
        ],
    )
    def negados(self, request):
        query_set = SolicitacoesNutrimanifestacao.get_negados()
        query_set = SolicitacoesNutrimanifestacao.busca_filtro(
            query_set, request.query_params
        )
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=CANCELADOS,
        permission_classes=[
            UsuarioNutricionista | UsuarioCODAEGabinete | UsuarioDinutreDiretoria
        ],
    )
    def cancelados(self, request):
        query_set = SolicitacoesNutrimanifestacao.get_cancelados()
        query_set = SolicitacoesNutrimanifestacao.busca_filtro(
            query_set, request.query_params
        )
        return self._retorno_base(query_set)


class DRESolicitacoesViewSet(SolicitacoesViewSet):
    lookup_field = "uuid"
    queryset = SolicitacoesDRE.objects.all()
    permission_classes = (UsuarioDiretoriaRegional,)
    serializer_class = SolicitacoesSerializer

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{PENDENTES_VALIDACAO_DRE}/{FILTRO_PADRAO_PEDIDOS}/{TIPO_VISAO}",
    )
    def pendentes_validacao(
        self, request, filtro_aplicado=SEM_FILTRO, tipo_visao=TIPO_VISAO_SOLICITACOES
    ):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        query_set = SolicitacoesDRE.get_pendentes_validacao(
            dre_uuid=diretoria_regional.uuid, filtro=filtro_aplicado
        )
        query_set = SolicitacoesDRE.busca_filtro(query_set, request.query_params)
        response = {
            "results": self._agrupa_por_tipo_visao(
                tipo_visao=tipo_visao, query_set=query_set
            )
        }
        return Response(response)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{PENDENTES_AUTORIZACAO_DIETA_ESPECIAL}/{FILTRO_DRE_UUID}",
    )
    def pendentes_autorizacao_dieta_especial(self, request, dre_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesDRE.get_pendentes_dieta_especial(dre_uuid=dre_uuid)
        query_set = SolicitacoesDRE.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{AUTORIZADOS_DIETA_ESPECIAL}/{FILTRO_DRE_UUID}",
    )
    def autorizados_dieta_especial(self, request, dre_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesDRE.get_autorizados_dieta_especial(dre_uuid=dre_uuid)
        query_set = SolicitacoesDRE.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{NEGADOS_DIETA_ESPECIAL}/{FILTRO_DRE_UUID}",
    )
    def negados_dieta_especial(self, request, dre_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesDRE.get_negados_dieta_especial(dre_uuid=dre_uuid)
        query_set = SolicitacoesDRE.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{CANCELADOS_DIETA_ESPECIAL}/{FILTRO_DRE_UUID}",
    )
    def cancelados_dieta_especial(self, request, dre_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesDRE.get_cancelados_dieta_especial(dre_uuid=dre_uuid)
        query_set = SolicitacoesDRE.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{AUTORIZADAS_TEMPORARIAMENTE_DIETA_ESPECIAL}/{FILTRO_DRE_UUID}",
    )
    def autorizadas_temporariamente_dieta_especial(self, request, dre_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesDRE.get_autorizadas_temporariamente_dieta_especial(
            dre_uuid=dre_uuid
        )
        query_set = SolicitacoesDRE.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{INATIVAS_TEMPORARIAMENTE_DIETA_ESPECIAL}/{FILTRO_DRE_UUID}",
    )
    def inativas_temporariamente_dieta_especial(self, request, dre_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesDRE.get_inativas_temporariamente_dieta_especial(
            dre_uuid=dre_uuid
        )
        query_set = SolicitacoesDRE.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{INATIVAS_DIETA_ESPECIAL}/{FILTRO_DRE_UUID}",
        permission_classes=(
            IsAuthenticated,
            PermissaoParaRecuperarDietaEspecial,
        ),
    )
    def inativas_dieta_especial(self, request, dre_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesDRE.get_inativas_dieta_especial(dre_uuid=dre_uuid)
        query_set = SolicitacoesDRE.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(detail=False, methods=["GET"], url_path=f"{PENDENTES_AUTORIZACAO}")
    def pendentes_autorizacao(self, request, dre_uuid=None):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        query_set = SolicitacoesDRE.get_pendentes_validacao(
            dre_uuid=diretoria_regional.uuid
        )
        query_set = SolicitacoesCODAE.busca_filtro(query_set, request.query_params)
        return self._retorno_base(query_set)

    @action(detail=False, methods=["GET"], url_path=f"{AUTORIZADOS}")
    def autorizados(self, request, dre_uuid=None):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        query_set = SolicitacoesDRE.get_autorizados(dre_uuid=diretoria_regional.uuid)
        query_set = SolicitacoesCODAE.busca_filtro(query_set, request.query_params)
        return self._retorno_base(query_set)

    @action(detail=False, methods=["GET"], url_path=f"{AGUARDANDO_CODAE}")
    def aguardando_codae(self, request, dre_uuid=None):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        query_set = SolicitacoesDRE.get_aguardando_codae(
            dre_uuid=diretoria_regional.uuid
        )
        query_set = SolicitacoesDRE.busca_filtro(query_set, request.query_params)
        return self._retorno_base(query_set)

    @action(detail=False, methods=["GET"], url_path=f"{NEGADOS}")
    def negados(self, request, dre_uuid=None):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        query_set = SolicitacoesDRE.get_negados(dre_uuid=diretoria_regional.uuid)
        query_set = SolicitacoesCODAE.busca_filtro(query_set, request.query_params)
        return self._retorno_base(query_set)

    @action(detail=False, methods=["GET"], url_path=f"{CANCELADOS}")
    def cancelados(self, request, dre_uuid=None):
        usuario = request.user
        diretoria_regional = usuario.vinculo_atual.instituicao
        query_set = SolicitacoesDRE.get_cancelados(dre_uuid=diretoria_regional.uuid)
        query_set = SolicitacoesCODAE.busca_filtro(query_set, request.query_params)
        return self._retorno_base(query_set)

    @action(detail=False, methods=["GET"], url_path=f"{RESUMO_MES}")
    def resumo_mes(self, request):
        usuario = request.user
        dre_uuid = usuario.vinculo_atual.instituicao.uuid
        totais_dict = SolicitacoesDRE.resumo_totais_mes(
            dre_uuid=dre_uuid,
        )
        return Response(totais_dict)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{RELATORIO_RESUMO_MES_ANO}",
    )
    def relatorio_resumo_anual_e_mensal(self, request):
        usuario = request.user
        dre_uuid = usuario.vinculo_atual.instituicao.uuid

        query_set = SolicitacoesDRE.get_solicitacoes_ano_corrente(dre_uuid=dre_uuid)
        resumo_do_ano = self._agrupa_por_mes_por_solicitacao(query_set=query_set)
        resumo_do_mes = SolicitacoesDRE.resumo_totais_mes(
            dre_uuid=dre_uuid,
        )
        return relatorio_resumo_anual_e_mensal(request, resumo_do_mes, resumo_do_ano)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{RELATORIO_PERIODO}/{FILTRO_ESCOLA_UUID}",
    )
    def relatorio_filtro_periodo(self, request, escola_uuid=None):
        usuario = request.user
        dre = usuario.vinculo_atual.instituicao
        form = FiltroValidator(request.GET)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            query_set = SolicitacoesDRE.filtros_dre(
                escola_uuid=escola_uuid,
                dre_uuid=dre.uuid,
                data_inicial=cleaned_data.get("data_inicial"),
                data_final=cleaned_data.get("data_final"),
                tipo_solicitacao=cleaned_data.get("tipo_solicitacao"),
                status_solicitacao=cleaned_data.get("status_solicitacao"),
            )
            query_set = self.remove_duplicados_do_query_set(query_set)

            return relatorio_filtro_periodo(request, query_set, dre.nome, escola_uuid)
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["GET"], url_path=f"{RESUMO_ANO}")
    def evolucao_solicitacoes(self, request):
        usuario = request.user
        dre_uuid = usuario.vinculo_atual.instituicao.uuid
        query_set = SolicitacoesDRE.get_solicitacoes_ano_corrente(dre_uuid=dre_uuid)
        response = {
            "results": self._agrupa_por_mes_por_solicitacao(query_set=query_set)
        }
        return Response(response)

    @action(detail=False, methods=["GET"], url_path=f"{PESQUISA}/{FILTRO_ESCOLA_UUID}")
    def filtro_periodo_tipo_solicitacao(self, request, escola_uuid=None):
        """Filtro de todas as solicitações da dre.

        ---
        tipo_solicitacao -- ALT_CARDAPIO|INV_CARDAPIO|INC_ALIMENTA|INC_ALIMENTA_CONTINUA|
        KIT_LANCHE_AVULSA|SUSP_ALIMENTACAO|KIT_LANCHE_UNIFICADA|TODOS
        status_solicitacao -- AUTORIZADOS|NEGADOS|CANCELADOS|RECEBIDAS|TODOS
        data_inicial -- dd-mm-yyyy
        data_final -- dd-mm-yyyy
        """
        usuario = request.user
        dre_uuid = usuario.vinculo_atual.instituicao.uuid
        form = FiltroValidator(request.GET)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            query_set = SolicitacoesDRE.filtros_dre(
                escola_uuid=escola_uuid,
                dre_uuid=dre_uuid,
                data_inicial=cleaned_data.get("data_inicial"),
                data_final=cleaned_data.get("data_final"),
                tipo_solicitacao=cleaned_data.get("tipo_solicitacao"),
                status_solicitacao=cleaned_data.get("status_solicitacao"),
            )
            return self._retorno_base(query_set)
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


class TerceirizadaSolicitacoesViewSet(SolicitacoesViewSet):
    lookup_field = "uuid"
    queryset = SolicitacoesTerceirizada.objects.all()
    permission_classes = (UsuarioTerceirizada,)
    serializer_class = SolicitacoesSerializer

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{PENDENTES_AUTORIZACAO_DIETA_ESPECIAL}/{FILTRO_TERCEIRIZADA_UUID}",
    )
    def pendentes_autorizacao_dieta_especial(self, request, terceirizada_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesTerceirizada.get_pendentes_dieta_especial(
            terceirizada_uuid=terceirizada_uuid
        )
        query_set = SolicitacoesTerceirizada.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{AUTORIZADOS_DIETA_ESPECIAL}/{FILTRO_TERCEIRIZADA_UUID}",
    )
    def autorizados_dieta_especial(self, request, terceirizada_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesTerceirizada.get_autorizados_dieta_especial(
            terceirizada_uuid=terceirizada_uuid
        )
        query_set = SolicitacoesTerceirizada.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{NEGADOS_DIETA_ESPECIAL}/{FILTRO_TERCEIRIZADA_UUID}",
    )
    def negados_dieta_especial(self, request, terceirizada_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesTerceirizada.get_negados_dieta_especial(
            terceirizada_uuid=terceirizada_uuid
        )
        query_set = SolicitacoesTerceirizada.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{CANCELADOS_DIETA_ESPECIAL}/{FILTRO_TERCEIRIZADA_UUID}",
    )
    def cancelados_dieta_especial(self, request, terceirizada_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesTerceirizada.get_cancelados_dieta_especial(
            terceirizada_uuid=terceirizada_uuid
        )
        query_set = SolicitacoesTerceirizada.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{AUTORIZADAS_TEMPORARIAMENTE_DIETA_ESPECIAL}/{FILTRO_TERCEIRIZADA_UUID}",
    )
    def autorizadas_temporariamente_dieta_especial(
        self, request, terceirizada_uuid=None
    ):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = (
            SolicitacoesTerceirizada.get_autorizadas_temporariamente_dieta_especial(
                terceirizada_uuid=terceirizada_uuid
            )
        )
        query_set = SolicitacoesTerceirizada.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{AGUARDANDO_INICIO_VIGENCIA_DIETA_ESPECIAL}/{FILTRO_TERCEIRIZADA_UUID}",
    )
    def aguardando_inicio_vigencia_dieta_especial(
        self, request, terceirizada_uuid=None
    ):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesTerceirizada.get_aguardando_vigencia_dieta_especial(
            terceirizada_uuid=terceirizada_uuid
        )
        query_set = SolicitacoesTerceirizada.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{INATIVAS_TEMPORARIAMENTE_DIETA_ESPECIAL}/{FILTRO_TERCEIRIZADA_UUID}",
    )
    def inativas_temporariamente_dieta_especial(self, request, terceirizada_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = (
            SolicitacoesTerceirizada.get_inativas_temporariamente_dieta_especial(
                terceirizada_uuid=terceirizada_uuid
            )
        )
        query_set = SolicitacoesTerceirizada.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{INATIVAS_DIETA_ESPECIAL}/{FILTRO_TERCEIRIZADA_UUID}",
    )
    def inativas_dieta_especial(self, request, terceirizada_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesTerceirizada.get_inativas_dieta_especial(
            terceirizada_uuid=terceirizada_uuid
        )
        query_set = SolicitacoesTerceirizada.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(detail=False, methods=["GET"], url_path=f"{QUESTIONAMENTOS}")
    def questionamentos(self, request):
        terceirizada_uuid = request.user.vinculo_atual.instituicao.uuid
        query_set = SolicitacoesTerceirizada.get_questionamentos(
            terceirizada_uuid=terceirizada_uuid
        )
        query_set = SolicitacoesTerceirizada.busca_filtro(
            query_set, request.query_params
        )
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{PENDENTES_AUTORIZACAO}/{FILTRO_TERCEIRIZADA_UUID}",
    )
    def pendentes_autorizacao(self, request, terceirizada_uuid=None):
        query_set = SolicitacoesTerceirizada.get_pendentes_autorizacao(
            terceirizada_uuid=terceirizada_uuid
        )
        return self._retorno_base(query_set)

    @action(detail=False, methods=["GET"], url_path=f"{AUTORIZADOS}")
    def autorizados(self, request):
        terceirizada_uuid = request.user.vinculo_atual.instituicao.uuid
        query_set = SolicitacoesTerceirizada.get_autorizados(
            terceirizada_uuid=terceirizada_uuid
        )
        query_set = SolicitacoesTerceirizada.busca_filtro(
            query_set, request.query_params
        )
        return self._retorno_base(query_set)

    @action(detail=False, methods=["GET"], url_path=f"{NEGADOS}")
    def negados(self, request):
        terceirizada_uuid = request.user.vinculo_atual.instituicao.uuid
        query_set = SolicitacoesTerceirizada.get_negados(
            terceirizada_uuid=terceirizada_uuid
        )
        query_set = SolicitacoesTerceirizada.busca_filtro(
            query_set, request.query_params
        )
        return self._retorno_base(query_set)

    @action(detail=False, methods=["GET"], url_path=f"{CANCELADOS}")
    def cancelados(self, request):
        terceirizada_uuid = request.user.vinculo_atual.instituicao.uuid
        query_set = SolicitacoesTerceirizada.get_cancelados(
            terceirizada_uuid=terceirizada_uuid
        )
        query_set = SolicitacoesTerceirizada.busca_filtro(
            query_set, request.query_params
        )
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{PENDENTES_CIENCIA}/{FILTRO_TERCEIRIZADA_UUID}/{FILTRO_PADRAO_PEDIDOS}/{TIPO_VISAO}",
    )
    def pendentes_ciencia(
        self,
        request,
        terceirizada_uuid=None,
        filtro_aplicado=SEM_FILTRO,
        tipo_visao=TIPO_VISAO_SOLICITACOES,
    ):
        query_set = SolicitacoesTerceirizada.get_pendentes_ciencia(
            terceirizada_uuid=terceirizada_uuid, filtro=filtro_aplicado
        )
        response = {
            "results": self._agrupa_por_tipo_visao(
                tipo_visao=tipo_visao, query_set=query_set
            )
        }
        return Response(response)
