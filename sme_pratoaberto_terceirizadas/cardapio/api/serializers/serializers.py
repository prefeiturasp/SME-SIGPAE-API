from rest_framework import serializers

from sme_pratoaberto_terceirizadas.escola.api.serializers import (
    EscolaSimplesSerializer, PeriodoEscolarSerializer,
    TipoUnidadeEscolarSerializer,
    PeriodoEscolarSimplesSerializer)
from sme_pratoaberto_terceirizadas.terceirizada.api.serializers import EditalSerializer
from ...models import (
    TipoAlimentacao, Cardapio, InversaoCardapio,
    SuspensaoAlimentacao, AlteracaoCardapio, MotivoAlteracaoCardapio,
    SubstituicoesAlimentacaoNoPeriodoEscolar,
    SuspensaoAlimentacaoNoPeriodoEscolar)


class TipoAlimentacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAlimentacao
        exclude = ('id',)


class CardapioSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cardapio
        exclude = ('id',)


class CardapioSerializer(serializers.ModelSerializer):
    tipos_alimentacao = TipoAlimentacaoSerializer(many=True, read_only=True)
    tipos_unidade_escolar = TipoUnidadeEscolarSerializer(many=True, read_only=True)
    edital = EditalSerializer()

    class Meta:
        model = Cardapio
        exclude = ('id',)


class InversaoCardapioSerializer(serializers.ModelSerializer):
    cardapio_de = CardapioSimplesSerializer()
    cardapio_para = CardapioSimplesSerializer()
    escola = EscolaSimplesSerializer()
    status = serializers.SerializerMethodField()
    id_externo = serializers.CharField()

    def get_status(self, obj):
        return obj.get_status_display()

    class Meta:
        model = InversaoCardapio
        exclude = ('id',)


class SuspensaoAlimentacaoNoPeriodoEscolarSerializer(serializers.ModelSerializer):
    periodo_escolar = PeriodoEscolarSimplesSerializer()
    tipos_alimentacao = TipoAlimentacaoSerializer(many=True)

    class Meta:
        model = SuspensaoAlimentacaoNoPeriodoEscolar
        exclude = ('id', 'suspensao_alimentacao')


class SuspensaoAlimentacaoSerializer(serializers.ModelSerializer):
    escola = EscolaSimplesSerializer()
    suspensoes_periodo_escolar = SuspensaoAlimentacaoNoPeriodoEscolarSerializer(many=True)

    class Meta:
        model = SuspensaoAlimentacao
        exclude = ('id',)


class MotivoAlteracaoCardapioSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotivoAlteracaoCardapio
        exclude = ('id',)


class SubstituicoesAlimentacaoNoPeriodoEscolarSerializer(serializers.ModelSerializer):
    periodo_escolar = PeriodoEscolarSerializer()
    alteracao_cardapio = serializers.SlugRelatedField(
        slug_field='uuid',
        required=False,
        queryset=AlteracaoCardapio.objects.all()
    )
    tipos_alimentacao = TipoAlimentacaoSerializer(many=True)

    class Meta:
        model = SubstituicoesAlimentacaoNoPeriodoEscolar
        exclude = ('id',)


class AlteracaoCardapioSerializer(serializers.ModelSerializer):
    escola = EscolaSimplesSerializer()
    motivo = MotivoAlteracaoCardapioSerializer()
    substituicoes = SubstituicoesAlimentacaoNoPeriodoEscolarSerializer(many=True)

    class Meta:
        model = AlteracaoCardapio
        exclude = ('id',)
