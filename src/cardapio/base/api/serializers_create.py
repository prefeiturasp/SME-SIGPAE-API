"""Serializers de escrita da subapp base do modulo de cardapio.

Centraliza a criacao e atualizacao de horarios por escola e de vinculos entre
tipo de unidade escolar, periodo escolar e tipos de alimentacao.
"""

from rest_framework import serializers

from src.cardapio.base.api.validators import (
    escola_nao_pode_cadastrar_dois_combos_iguais,
    hora_inicio_nao_pode_ser_maior_que_hora_final,
)
from src.cardapio.base.models import (
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from src.dados_comuns.utils import update_instance_from_dict
from src.dados_comuns.validators import (
    campo_nao_pode_ser_nulo,
)
from src.escola.models import Escola, PeriodoEscolar, TipoUnidadeEscolar


class HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializerCreate(
    serializers.ModelSerializer
):
    """Serializa a escrita de horarios de tipos de alimentacao por escola.

    Resolve os relacionamentos por UUID, valida a consistencia da faixa de
    horario e impede a criacao de combinacoes duplicadas para a mesma escola,
    tipo de alimentacao e periodo escolar.

    Viewsets que utilizam este serializer:
        - ``HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarViewSet``:
          retornado por ``get_serializer_class()`` nas acoes ``create``,
          ``update`` e ``partial_update``.
    """

    hora_inicial = serializers.TimeField()
    hora_final = serializers.TimeField()

    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Escola.objects.all()
    )

    tipo_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=TipoAlimentacao.objects.all()
    )

    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=PeriodoEscolar.objects.all()
    )

    def validate(self, attrs):
        """Valida a ordem cronologica da faixa de horario informada.

        Args:
            attrs (dict): Dados normalizados pelo serializer antes da
                persistencia.

        Returns:
            dict: Os atributos recebidos apos a validacao.

        Raises:
            ValidationError: Quando ``hora_inicial`` e maior ou igual a
                ``hora_final``.
        """
        hora_inicial = attrs["hora_inicial"]
        hora_final = attrs["hora_final"]
        hora_inicio_nao_pode_ser_maior_que_hora_final(hora_inicial, hora_final)
        return attrs

    def create(self, validated_data):
        """Cria um horario validando duplicidade por escola e periodo.

        Args:
            validated_data (dict): Dados validados da configuracao de horario.

        Returns:
            HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar: Instancia
            criada.

        Raises:
            ValidationError: Quando ja existe um horario para a mesma
                combinacao de escola, tipo de alimentacao e periodo escolar.
        """
        escola = validated_data.get("escola")
        tipo_alimentacao = validated_data.get("tipo_alimentacao")
        periodo_escolar = validated_data.get("periodo_escolar")
        escola_nao_pode_cadastrar_dois_combos_iguais(
            escola, tipo_alimentacao, periodo_escolar
        )
        horario_do_combo = (
            HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar.objects.create(
                **validated_data
            )
        )
        return horario_do_combo

    def update(self, instance, validated_data):
        """Atualiza um horario existente com os dados recebidos.

        Args:
            instance (HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar):
                Instancia a ser atualizada.
            validated_data (dict): Dados validados da requisicao.

        Returns:
            HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar: Instancia
            atualizada e salva.
        """
        update_instance_from_dict(instance, validated_data)
        instance.save()
        return instance

    class Meta:
        model = HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar
        fields = (
            "uuid",
            "hora_inicial",
            "hora_final",
            "escola",
            "tipo_alimentacao",
            "periodo_escolar",
        )


class VinculoTipoAlimentoCreateSerializer(serializers.ModelSerializer):
    """Serializa a escrita de vinculos entre periodo, tipo de U.E. e alimentacoes.

    Resolve por UUID o tipo de unidade escolar, o periodo escolar e a lista de
    tipos de alimentacao autorizados para a combinacao editada.

    Viewsets que utilizam este serializer:
        - ``VinculoTipoAlimentacaoViewSet``: retornado por
          ``get_serializer_class()`` nas acoes ``create``, ``update`` e
          ``partial_update``.
    """

    tipo_unidade_escolar = serializers.SlugRelatedField(
        slug_field="uuid", queryset=TipoUnidadeEscolar.objects.all()
    )
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", queryset=PeriodoEscolar.objects.all()
    )

    tipos_alimentacao = serializers.SlugRelatedField(
        many=True, slug_field="uuid", queryset=TipoAlimentacao.objects.all()
    )

    def update(self, instance, validated_data):
        """Atualiza um vinculo e substitui seus tipos de alimentacao.

        Args:
            instance (VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar):
                Instancia a ser atualizada.
            validated_data (dict): Dados validados contendo os campos do
                vinculo e a lista ``tipos_alimentacao``.

        Returns:
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar:
            Instancia atualizada e salva.
        """
        tipos_alimentacao = validated_data.pop("tipos_alimentacao")
        update_instance_from_dict(instance, validated_data)
        instance.tipos_alimentacao.set(tipos_alimentacao)
        instance.save()
        return instance

    def validate_tipos_alimentacao(self, tipos_alimentacao):
        """Garante que a lista de tipos de alimentacao nao seja nula.

        Args:
            tipos_alimentacao (list[TipoAlimentacao]): Tipos de alimentacao
                resolvidos pelo campo ``SlugRelatedField``.

        Returns:
            list[TipoAlimentacao]: A mesma lista validada.

        Raises:
            ValidationError: Quando o campo e informado como nulo.
        """
        campo_nao_pode_ser_nulo(tipos_alimentacao)
        return tipos_alimentacao

    class Meta:
        model = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar
        fields = (
            "uuid",
            "tipos_alimentacao",
            "tipo_unidade_escolar",
            "periodo_escolar",
        )
