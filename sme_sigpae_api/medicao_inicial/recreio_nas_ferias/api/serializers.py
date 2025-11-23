from rest_framework import serializers
from django.db import transaction

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


class EscolaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escola
        fields = ('uuid', 'nome', 'codigo_eol')


class LoteSerializer(serializers.ModelSerializer):
    nome_exibicao = serializers.SerializerMethodField()

    class Meta:
        model = Lote
        fields = ('uuid', 'nome', 'nome_exibicao')

    def get_nome_exibicao(self, obj):
        dre = getattr(obj, 'diretoria_regional', None)
        iniciais = getattr(dre, 'iniciais', None)
        if iniciais:
            return f"{obj.nome} - {iniciais}"
        return obj.nome


class RecreioNasFeriasUnidadeParticipanteSerializer(serializers.ModelSerializer):
    lote = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Lote.objects.all(),
        write_only=True
    )
    unidade_educacional = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Escola.objects.all(),
        write_only=True
    )

    lote_obj = LoteSerializer(source='lote', read_only=True)
    unidade_educacional_obj = EscolaSerializer(source='unidade_educacional', read_only=True)

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

    tipos_alimentacao = serializers.SerializerMethodField()

    class Meta:
        model = RecreioNasFeriasUnidadeParticipante
        fields = [
            'id',
            'uuid',
            'lote',
            'unidade_educacional',
            'lote_obj',
            'unidade_educacional_obj',
            'num_inscritos',
            'num_colaboradores',
            'liberar_medicao',
            'cei_ou_emei',
            'tipos_alimentacao_inscritos',
            'tipos_alimentacao_colaboradores',
            'tipos_alimentacao_infantil',
            'tipos_alimentacao',
        ]
        read_only_fields = ['id', 'uuid']

    def get_tipos_alimentacao(self, obj):
        categorias = {}
        qs = obj.tipos_alimentacao.select_related('tipo_alimentacao', 'categoria')
        for ta in qs:
            nome_cat = (ta.categoria.nome if ta.categoria and ta.categoria.nome else 'outros').lower()
            categorias.setdefault(nome_cat, []).append({
                'uuid': getattr(ta.tipo_alimentacao, 'uuid', None),
                'nome': str(ta.tipo_alimentacao)
            })
        return categorias

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        unidade_obj = rep.pop('unidade_educacional_obj', None)
        if unidade_obj is not None:
            rep['unidade_educacional'] = unidade_obj
        lote_obj = rep.pop('lote_obj', None)
        if lote_obj is not None:
            rep['lote'] = lote_obj

        return rep


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

    @transaction.atomic
    def update(self, instance, validated_data):
            unidades_data = validated_data.pop('unidades_participantes', None)

            instance.titulo = validated_data.get('titulo', instance.titulo)
            instance.data_inicio = validated_data.get('data_inicio', instance.data_inicio)
            instance.data_fim = validated_data.get('data_fim', instance.data_fim)
            instance.save()

            if unidades_data is not None:
                categorias_map = self._fetch_categorias()

                # Remove todas as unidades existentes e seus tipos de alimentação
                instance.unidades_participantes.all().delete()

                # Cria as novas unidades
                tipo_alimentacao_instances_to_create = []
                for unidade_data in unidades_data:
                    tipos_inscritos = unidade_data.pop('tipos_alimentacao_inscritos', []) or []
                    tipos_colaboradores = unidade_data.pop('tipos_alimentacao_colaboradores', []) or []
                    tipos_infantil = unidade_data.pop('tipos_alimentacao_infantil', []) or []

                    unidade = RecreioNasFeriasUnidadeParticipante.objects.create(
                        recreio_nas_ferias=instance,
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

            return instance
