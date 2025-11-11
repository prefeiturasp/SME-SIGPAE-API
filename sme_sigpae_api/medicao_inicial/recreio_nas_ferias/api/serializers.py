from rest_framework import serializers
from sme_sigpae_api.medicao_inicial.recreio_nas_ferias.models import (
    RecreioNasFerias,
    RecreioNasFeriasUnidadeParticipante,
    RecreioNasFeriasUnidadeTipoAlimentacao,
    CategoriaAlimentacao
)
from sme_sigpae_api.cardapio.base.models import TipoAlimentacao
from sme_sigpae_api.escola.models import Lote, Escola


class RecreioNasFeriasUnidadeParticipanteSerializer(serializers.ModelSerializer):
    lote = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Lote.objects.all()
    )
    unidade_educacional = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Escola.objects.all()
    )
    tipos_alimentacao_inscritos = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=TipoAlimentacao.objects.all(),
        many=True,
        required=True,
        write_only=True
    )
    tipos_alimentacao_colaboradores = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=TipoAlimentacao.objects.all(),
        many=True,
        required=False,
        allow_empty=True,
        write_only=True
    )
    tipos_alimentacao_infantil = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=TipoAlimentacao.objects.all(),
        many=True,
        required=False,
        allow_empty=True,
        write_only=True
    )

    class Meta:
        model = RecreioNasFeriasUnidadeParticipante
        fields = [
            'id',
            'uuid',
            'lote',
            'unidade_educacional',
            'num_inscritos',
            'num_colaboradores',
            'liberar_medicao',
            'cei_ou_emei',  # ← ADICIONAR AQUI
            'tipos_alimentacao_inscritos',
            'tipos_alimentacao_colaboradores',
            'tipos_alimentacao_infantil'
        ]
        read_only_fields = ['id', 'uuid']


class RecreioNasFeriasSerializer(serializers.ModelSerializer):
    unidades_participantes = RecreioNasFeriasUnidadeParticipanteSerializer(
        many=True,
        required=True
    )

    class Meta:
        model = RecreioNasFerias
        fields = [
            'uuid',
            'id',
            'titulo',
            'data_inicio',
            'data_fim',
            'unidades_participantes',
            'criado_em',
            'alterado_em'
        ]
        read_only_fields = ['id', 'uuid', 'criado_em', 'alterado_em']

    def create(self, validated_data):
        unidades_data = validated_data.pop('unidades_participantes')

        recreio = RecreioNasFerias.objects.create(**validated_data)

        try:
            cat_inscritos = CategoriaAlimentacao.objects.get(nome='Inscritos')
            cat_colaboradores = CategoriaAlimentacao.objects.get(nome='Colaboradores')
            cat_infantil = CategoriaAlimentacao.objects.get(nome='Infantil')
        except CategoriaAlimentacao.DoesNotExist:
            raise serializers.ValidationError(
                "Categorias de alimentação não encontradas. Execute as migrations."
            )

        for unidade_data in unidades_data:
            tipos_inscritos = unidade_data.pop('tipos_alimentacao_inscritos', [])
            tipos_colaboradores = unidade_data.pop('tipos_alimentacao_colaboradores', [])
            tipos_infantil = unidade_data.pop('tipos_alimentacao_infantil', [])

            unidade = RecreioNasFeriasUnidadeParticipante.objects.create(
                recreio_nas_ferias=recreio,
                **unidade_data
            )

            for tipo in tipos_inscritos:
                RecreioNasFeriasUnidadeTipoAlimentacao.objects.create(
                    recreio_ferias_unidade=unidade,
                    tipo_alimentacao=tipo,
                    categoria=cat_inscritos
                )

            for tipo in tipos_colaboradores:
                RecreioNasFeriasUnidadeTipoAlimentacao.objects.create(
                    recreio_ferias_unidade=unidade,
                    tipo_alimentacao=tipo,
                    categoria=cat_colaboradores
                )

            for tipo in tipos_infantil:
                RecreioNasFeriasUnidadeTipoAlimentacao.objects.create(
                    recreio_ferias_unidade=unidade,
                    tipo_alimentacao=tipo,
                    categoria=cat_infantil
                )

        return recreio
