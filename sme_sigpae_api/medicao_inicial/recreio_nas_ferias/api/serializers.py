from rest_framework import serializers
from django.db import transaction

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
            'cei_ou_emei',
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

    def validate(self, attrs):
        data_inicio = attrs.get('data_inicio')
        data_fim = attrs.get('data_fim')

        if data_inicio and data_fim and data_fim < data_inicio:
            raise serializers.ValidationError({
                'data_fim': 'A data de fim não pode ser anterior à data de início.'
            })

        return attrs

    def _fetch_categorias(self):
        """
        Busca as categorias necessárias e retorna um dict com chaves:
        'inscritos', 'colaboradores', 'infantil'.
        """
        required = {
            'Inscritos': 'inscritos',
            'Colaboradores': 'colaboradores',
            'Infantil': 'infantil'
        }
        categorias = CategoriaAlimentacao.objects.filter(nome__in=required.keys())
        if categorias.count() != len(required):
            found = {c.nome for c in categorias}
            missing = [name for name in required.keys() if name not in found]
            raise serializers.ValidationError(
                f"Categorias de alimentação não encontradas: {', '.join(missing)}. "
                "Execute as migrations."
            )
        return {required[c.nome]: c for c in categorias}

    def _build_unidade_tipos_instances(self, unidade, tipos_por_categoria, categorias_map):
        instances = []
        if tipos_por_categoria.get('inscritos'):
            instances.extend(
                RecreioNasFeriasUnidadeTipoAlimentacao(
                    recreio_ferias_unidade=unidade,
                    tipo_alimentacao=tipo,
                    categoria=categorias_map['inscritos']
                ) for tipo in tipos_por_categoria['inscritos']
            )
        if tipos_por_categoria.get('colaboradores'):
            instances.extend(
                RecreioNasFeriasUnidadeTipoAlimentacao(
                    recreio_ferias_unidade=unidade,
                    tipo_alimentacao=tipo,
                    categoria=categorias_map['colaboradores']
                ) for tipo in tipos_por_categoria['colaboradores']
            )
        if tipos_por_categoria.get('infantil'):
            instances.extend(
                RecreioNasFeriasUnidadeTipoAlimentacao(
                    recreio_ferias_unidade=unidade,
                    tipo_alimentacao=tipo,
                    categoria=categorias_map['infantil']
                ) for tipo in tipos_por_categoria['infantil']
            )
        return instances

    @transaction.atomic
    def create(self, validated_data):
        unidades_data = validated_data.pop('unidades_participantes', [])

        recreio = RecreioNasFerias.objects.create(**validated_data)

        categorias_map = self._fetch_categorias()

        tipo_alimentacao_instances_to_create = []
        for unidade_data in unidades_data:
            tipos_inscritos = unidade_data.pop('tipos_alimentacao_inscritos', []) or []
            tipos_colaboradores = unidade_data.pop('tipos_alimentacao_colaboradores', []) or []
            tipos_infantil = unidade_data.pop('tipos_alimentacao_infantil', []) or []

            unidade = RecreioNasFeriasUnidadeParticipante.objects.create(
                recreio_nas_ferias=recreio,
                **unidade_data
            )

            tipos_por_categoria = {
                'inscritos': tipos_inscritos,
                'colaboradores': tipos_colaboradores,
                'infantil': tipos_infantil
            }

            tipo_alimentacao_instances_to_create.extend(
                self._build_unidade_tipos_instances(unidade, tipos_por_categoria, categorias_map)
            )

        if tipo_alimentacao_instances_to_create:
            RecreioNasFeriasUnidadeTipoAlimentacao.objects.bulk_create(tipo_alimentacao_instances_to_create)

        return recreio
