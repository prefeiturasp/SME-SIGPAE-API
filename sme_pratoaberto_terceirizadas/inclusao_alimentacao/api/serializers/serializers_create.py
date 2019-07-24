from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from sme_pratoaberto_terceirizadas.cardapio.models import TipoAlimentacao
from sme_pratoaberto_terceirizadas.dados_comuns.utils import update_instance_from_dict
from sme_pratoaberto_terceirizadas.dados_comuns.validators import nao_pode_ser_no_passado
from sme_pratoaberto_terceirizadas.escola.models import PeriodoEscolar, Escola
from ...models import (
    MotivoInclusaoContinua, MotivoInclusaoNormal,
    InclusaoAlimentacaoNormal, QuantidadePorPeriodo,
    InclusaoAlimentacaoContinua, GrupoInclusaoAlimentacaoNormal
)


class MotivoInclusaoContinuaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotivoInclusaoContinua
        exclude = ('id',)


class MotivoInclusaoNormalSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotivoInclusaoNormal
        exclude = ('id',)


class QuantidadePorPeriodoCreationSerializer(serializers.ModelSerializer):
    periodo_escolar = serializers.SlugRelatedField(
        slug_field='uuid',
        required=True,
        queryset=PeriodoEscolar.objects.all())

    tipos_alimentacao = serializers.SlugRelatedField(
        slug_field='uuid',
        many=True,
        required=True,
        queryset=TipoAlimentacao.objects.all())

    grupo_inclusao_normal = serializers.SlugRelatedField(
        slug_field='uuid',
        required=False,
        queryset=GrupoInclusaoAlimentacaoNormal.objects.all())

    inclusao_alimentacao_continua = serializers.SlugRelatedField(
        slug_field='uuid',
        required=False,
        queryset=InclusaoAlimentacaoContinua.objects.all())

    def create(self, validated_data):
        tipos_alimentacao = validated_data.pop('tipos_alimentacao', [])
        quantidade_periodo = QuantidadePorPeriodo.objects.create(**validated_data)
        quantidade_periodo.tipos_alimentacao.set(tipos_alimentacao)
        return quantidade_periodo

    def update(self, instance, validated_data):
        tipos_alimentacao = validated_data.pop('tipos_alimentacao', [])
        if tipos_alimentacao:
            instance.tipos_alimentacao.set(tipos_alimentacao)
        update_instance_from_dict(instance, validated_data)
        instance.save()
        return instance

    class Meta:
        model = QuantidadePorPeriodo
        exclude = ('id',)


class InclusaoAlimentacaoNormalCreationSerializer(serializers.ModelSerializer):
    motivo = serializers.SlugRelatedField(
        slug_field='uuid',
        required=True,
        queryset=MotivoInclusaoNormal.objects.all())

    def validate_data(self, data):
        nao_pode_ser_no_passado(data)
        return data

    def update(self, instance, validated_data):
        update_instance_from_dict(instance, validated_data)
        instance.save()
        return instance

    class Meta:
        model = InclusaoAlimentacaoNormal
        exclude = ('id',)


class GrupoInclusaoAlimentacaoNormalCreationSerializer(serializers.ModelSerializer):
    inclusoes = InclusaoAlimentacaoNormalCreationSerializer(
        many=True,
        required=True
    )
    escola = serializers.SlugRelatedField(
        slug_field='uuid',
        required=True,
        queryset=Escola.objects.all()
    )
    quantidades_periodo = QuantidadePorPeriodoCreationSerializer(
        many=True,
        required=True
    )

    def create(self, validated_data):
        inclusoes_json = validated_data.pop('inclusoes')
        quantidades_periodo_json = validated_data.pop('quantidades_periodo')

        grupo_inclusao_alimentacao_normal = GrupoInclusaoAlimentacaoNormal.objects.create(**validated_data)

        for inclusao_json in inclusoes_json:
            inc = InclusaoAlimentacaoNormalCreationSerializer().create(
                validated_data=inclusao_json)
            grupo_inclusao_alimentacao_normal.adiciona_inclusao_normal(inc)

        for quantidade_periodo_json in quantidades_periodo_json:
            qtd = QuantidadePorPeriodoCreationSerializer().create(
                validated_data=quantidade_periodo_json)
            grupo_inclusao_alimentacao_normal.adiciona_quantidade_periodo(qtd)

        return grupo_inclusao_alimentacao_normal

    def update(self, instance, validated_data):
        # TODO: ajustar esse para os ajustes do modelo..
        inclusoes_dict = validated_data.pop('inclusoes')
        inclusoes = instance.inclusoes.all()
        assert len(inclusoes) == len(inclusoes_dict)
        for index in range(len(inclusoes_dict)):
            InclusaoAlimentacaoNormalCreationSerializer(
            ).update(instance=inclusoes[index], validated_data=inclusoes_dict[index])
        update_instance_from_dict(instance, validated_data)
        instance.save()
        return instance

    class Meta:
        model = GrupoInclusaoAlimentacaoNormal
        exclude = ('id',)


class InclusaoAlimentacaoContinuaCreationSerializer(serializers.ModelSerializer):
    motivo = serializers.SlugRelatedField(
        slug_field='uuid',
        required=True,
        queryset=MotivoInclusaoContinua.objects.all())
    escola = serializers.SlugRelatedField(
        slug_field='uuid',
        required=True,
        queryset=Escola.objects.all()
    )
    quantidades_periodo = QuantidadePorPeriodoCreationSerializer(many=True)
    dias_semana_explicacao = serializers.CharField(
        source='dias_semana_display',
        required=False,
        read_only=True
    )

    def validate_data_inicial(self, data):
        nao_pode_ser_no_passado(data)
        return data

    def validate_data_final(self, data):
        nao_pode_ser_no_passado(data)
        return data

    def validate(self, attrs):
        data_inicial = attrs.get('data_inicial', None)
        data_final = attrs.get('data_final', None)
        if data_inicial > data_final:
            raise ValidationError('data inicial não pode ser maior que data final')
        return attrs

    def create(self, validated_data):
        quantidades_periodo_array = validated_data.pop('quantidades_periodo')
        lista_escola_quantidade = self._gera_lista_escola_quantidade(quantidades_periodo_array)
        inclusao_alimentacao_continua = InclusaoAlimentacaoContinua.objects.create(
            **validated_data)
        inclusao_alimentacao_continua.quantidades_periodo.set(lista_escola_quantidade)

        return inclusao_alimentacao_continua

    def update(self, instance, validated_data):
        quantidades_periodo_array = validated_data.pop('quantidades_periodo')
        quantidades_periodo = instance.quantidades_periodo.all()

        assert len(quantidades_periodo) == len(quantidades_periodo_array)
        for index in range(len(quantidades_periodo_array)):
            QuantidadePorPeriodoCreationSerializer(
            ).update(instance=quantidades_periodo[index],
                     validated_data=quantidades_periodo_array[index]
                     )
        update_instance_from_dict(instance, validated_data)
        instance.save()
        return instance

    def _gera_lista_escola_quantidade(self, quantidades_periodo_array):
        escola_qtd_lista = []
        for quantidade_periodo_json in quantidades_periodo_array:
            quantidade_periodo = QuantidadePorPeriodoCreationSerializer(
            ).create(quantidade_periodo_json)
            escola_qtd_lista.append(quantidade_periodo)
        return escola_qtd_lista

    class Meta:
        model = InclusaoAlimentacaoContinua
        exclude = ('id',)
