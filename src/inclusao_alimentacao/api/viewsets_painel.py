import datetime

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from src.dados_comuns import constants
from src.dados_comuns.permissions import (
    UsuarioCODAEGestaoAlimentacao,
    UsuarioDiretoriaRegional,
)
from src.dados_comuns.utils import (
    eh_dia_util,
    obter_dias_uteis_apos,
    queryset_por_data,
)
from src.escola.models import DiaSuspensaoAtividades
from src.inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
    InclusaoAlimentacaoDaCEI,
    InclusaoDeAlimentacaoCEMEI,
)
from src.kit_lanche.utils import KitLanchePagination, filtra_solicitacoes_por_busca

from .serializers import serializers


class InclusaoAlimentacaoPainelViewSet(viewsets.GenericViewSet):
    lookup_field = "uuid"
    permission_classes = (IsAuthenticated,)
    pagination_class = KitLanchePagination

    MODELOS = [
        GrupoInclusaoAlimentacaoNormal,
        InclusaoAlimentacaoDaCEI,
        InclusaoAlimentacaoContinua,
        InclusaoDeAlimentacaoCEMEI,
    ]

    def get_permissions(self):
        if self.action == "solicitacoes_diretoria_regional":
            self.permission_classes = (UsuarioDiretoriaRegional,)
        elif self.action == "solicitacoes_codae":
            self.permission_classes = (UsuarioCODAEGestaoAlimentacao,)
        return super().get_permissions()

    @action(
        detail=False,
        url_path=f"{constants.PEDIDOS_DRE}/{constants.FILTRO_PADRAO_PEDIDOS}",
    )
    def solicitacoes_diretoria_regional(self, request, filtro_aplicado="sem_filtro"):
        return self._processar_painel(request, filtro_aplicado, visao="dre")

    @action(
        detail=False,
        url_path=f"{constants.PEDIDOS_CODAE}/{constants.FILTRO_PADRAO_PEDIDOS}",
    )
    def solicitacoes_codae(self, request, filtro_aplicado="sem_filtro"):
        return self._processar_painel(request, filtro_aplicado, visao="codae")

    def _processar_painel(self, request, filtro_aplicado, visao):
        prazo = request.query_params.get("prazo", "").upper()
        instituicao = request.user.vinculo_atual.instituicao
        querysets = self._base_querysets(filtro_aplicado, instituicao, visao)
        querysets = self._aplicar_filtros(querysets, request)
        objetos, escolas, totais = self._classificar_por_prioridade(querysets, prazo)
        objetos = sorted(objetos, key=lambda obj: (obj.data, str(obj.uuid)))
        page = self.paginate_queryset(objetos)
        uuids = [obj.uuid for obj in page]
        resultados = self._serializar_pagina(uuids, request)
        response = self.get_paginated_response(resultados)
        if prazo in escolas:
            escolas_solicitantes = len(escolas[prazo])
        else:
            escolas_solicitantes = len(set().union(*escolas.values()))
        response.data["escolas_solicitantes"] = escolas_solicitantes
        response.data["totais"] = totais
        return response

    def _base_querysets(self, filtro_aplicado, instituicao, visao):
        querysets = []
        for modelo in self.MODELOS:
            queryset = queryset_por_data(filtro_aplicado, modelo)
            if visao == "dre":
                queryset = queryset.filter(
                    escola__in=instituicao.escolas.all(),
                    status=modelo.workflow_class.DRE_A_VALIDAR,
                )
            else:
                queryset = queryset.filter(
                    status__in=[
                        modelo.workflow_class.DRE_VALIDADO,
                        modelo.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
                    ]
                )
            querysets.append(queryset)
        return querysets

    def _aplicar_filtros(self, querysets, request):
        query_params = request.query_params
        if query_params.get("lote"):
            lote_uuid = query_params.get("lote")
            querysets = [qs.filter(rastro_lote__uuid=lote_uuid) for qs in querysets]
        if query_params.get("diretoria_regional"):
            dre_uuid = query_params.get("diretoria_regional")
            querysets = [qs.filter(rastro_dre__uuid=dre_uuid) for qs in querysets]
        if query_params.get("busca"):
            busca = query_params.get("busca")
            querysets = [filtra_solicitacoes_por_busca(qs, busca) for qs in querysets]
        return querysets

    def _classificar_por_prioridade(self, querysets, prazo):
        objetos = []
        escolas = {"PRIORITARIO": set(), "LIMITE": set(), "REGULAR": set()}
        totais = {"PRIORITARIO": 0, "LIMITE": 0, "REGULAR": 0}
        cache_dias = {}
        for queryset in querysets:
            queryset = queryset.select_related("escola", "escola__tipo_unidade")
            for obj in queryset.iterator():
                escola = obj.escola
                if escola.id not in cache_dias:
                    cache_dias[escola.id] = (
                        DiaSuspensaoAtividades.get_dias_com_suspensao_escola(
                            escola, constants.PRIORITARIO
                        ),
                        DiaSuspensaoAtividades.get_dias_com_suspensao_escola(
                            escola, constants.LIMITE_INFERIOR
                        ),
                        DiaSuspensaoAtividades.get_dias_com_suspensao_escola(
                            escola, constants.LIMITE_SUPERIOR
                        ),
                    )
                prioridade = self._calcular_prioridade(obj.data, cache_dias[escola.id])
                if prioridade in totais:
                    escolas[prioridade].add(escola.id)
                    totais[prioridade] += 1
                    if not prazo or prioridade == prazo:
                        objetos.append(obj)
        return objetos, escolas, totais

    def _serializar_pagina(self, uuids, request):
        grupos = [
            (
                GrupoInclusaoAlimentacaoNormal,
                serializers.GrupoInclusaoAlimentacaoNormalSerializer,
            ),
            (
                InclusaoAlimentacaoDaCEI,
                serializers.InclusaoAlimentacaoDaCEISerializer,
            ),
            (
                InclusaoAlimentacaoContinua,
                serializers.InclusaoAlimentacaoContinuaSerializer,
            ),
            (
                InclusaoDeAlimentacaoCEMEI,
                serializers.InclusaoDeAlimentacaoCEMEISerializer,
            ),
        ]
        objetos = {}
        for modelo, _ in grupos:
            for obj in modelo.objects.filter(uuid__in=uuids):
                objetos[obj.uuid] = obj
        resultados_por_uuid = {}
        for modelo, serializer_class in grupos:
            objs_modelo = [objetos[u] for u in uuids if isinstance(objetos[u], modelo)]
            if objs_modelo:
                data = serializer_class(
                    objs_modelo, many=True, context={"request": request}
                ).data
                for obj, item in zip(objs_modelo, data):
                    resultados_por_uuid[obj.uuid] = item
        return [resultados_por_uuid[u] for u in uuids]

    def _calcular_prioridade(self, data_pedido, dias_suspensao):
        if data_pedido is None:
            return "VENCIDO"
        hoje = datetime.date.today()
        dias_prioritario, dias_inferior, dias_superior = dias_suspensao
        minimo_dias_para_pedido = obter_dias_uteis_apos(
            hoje, constants.PRIORITARIO + dias_prioritario
        )
        dias_uteis_limite_inferior = obter_dias_uteis_apos(
            hoje, constants.LIMITE_INFERIOR + dias_inferior
        )
        dias_uteis_limite_superior = obter_dias_uteis_apos(
            hoje, constants.LIMITE_SUPERIOR + dias_superior
        )
        ultimo_dia_util = self._ultimo_dia_util(data_pedido)
        if ultimo_dia_util and minimo_dias_para_pedido >= ultimo_dia_util >= hoje:
            return "PRIORITARIO"
        if (
            ultimo_dia_util
            and dias_uteis_limite_superior >= data_pedido >= dias_uteis_limite_inferior
        ):
            return "LIMITE"
        if ultimo_dia_util and ultimo_dia_util >= dias_uteis_limite_superior:
            return "REGULAR"
        return "VENCIDO"

    def _ultimo_dia_util(self, data):
        data_retorno = data
        if data_retorno:
            while not eh_dia_util(data_retorno):
                data_retorno -= datetime.timedelta(days=1)
            if isinstance(data_retorno, datetime.datetime):
                return data_retorno.date()
        return data_retorno
