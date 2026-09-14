from rest_framework import serializers

from ....escola.models import Escola
from ...models import (
    SolicitacaoKitLancheAvulsa,
    SolicitacaoKitLancheCEIAvulsa,
    SolicitacaoKitLancheCEMEI,
)
from .serializers import (
    SolicitacaoKitLancheAvulsaSimilarSerializer,
    SolicitacaoKitLancheCEISimilarSerializer,
    SolicitacaoKitLancheCEMEISimilarSerializer,
)

CAMPOS_LISTAGEM = (
    "uuid",
    "id_externo",
    "escola",
    "data",
    "prioridade",
    "solicitacoes_similares",
)


class SolicitacaoKitLancheEscolaNomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escola
        fields = ("uuid", "nome")


class PrioridadeRequestCacheMixin:
    def get_prioridade(self, obj):
        request = self.context.get("request")
        cache = (
            getattr(request, "_kit_lanche_prioridade_cache", None) if request else None
        )
        if cache is None:
            valor = obj.prioridade
            if request is not None:
                setattr(
                    request,
                    "_kit_lanche_prioridade_cache",
                    {(obj.escola_id, obj.data): valor},
                )
            return valor
        chave = (obj.escola_id, obj.data)
        if chave not in cache:
            cache[chave] = obj.prioridade
        return cache[chave]


class SolicitacaoKitLancheListagemBase(
    PrioridadeRequestCacheMixin, serializers.ModelSerializer
):
    escola = SolicitacaoKitLancheEscolaNomeSerializer()
    data = serializers.DateField()
    prioridade = serializers.SerializerMethodField()
    id_externo = serializers.CharField()
    solicitacoes_similares = serializers.SerializerMethodField()

    similar_serializer_class = None

    def get_solicitacoes_similares(self, obj):
        similares = getattr(obj, "_prefetched_solicitacoes_similares", None)
        if similares is None:
            similares = obj.solicitacoes_similares
        return self.similar_serializer_class(
            similares, many=True, context=self.context
        ).data

    class Meta:
        fields = CAMPOS_LISTAGEM


class SolicitacaoKitLancheAvulsaListagemSerializer(SolicitacaoKitLancheListagemBase):
    similar_serializer_class = SolicitacaoKitLancheAvulsaSimilarSerializer

    class Meta(SolicitacaoKitLancheListagemBase.Meta):
        model = SolicitacaoKitLancheAvulsa


class SolicitacaoKitLancheCEIAvulsaListagemSerializer(SolicitacaoKitLancheListagemBase):
    similar_serializer_class = SolicitacaoKitLancheCEISimilarSerializer

    class Meta(SolicitacaoKitLancheListagemBase.Meta):
        model = SolicitacaoKitLancheCEIAvulsa


class SolicitacaoKitLancheCEMEIListagemSerializer(SolicitacaoKitLancheListagemBase):
    similar_serializer_class = SolicitacaoKitLancheCEMEISimilarSerializer

    class Meta(SolicitacaoKitLancheListagemBase.Meta):
        model = SolicitacaoKitLancheCEMEI
