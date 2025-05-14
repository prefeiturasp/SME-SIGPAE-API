from rest_framework import serializers

from sme_sigpae_api.cardapio.base.api.validators import (
    escola_nao_pode_cadastrar_dois_combos_iguais,
    hora_inicio_nao_pode_ser_maior_que_hora_final,
)
from sme_sigpae_api.cardapio.base.models import (
    Cardapio,
    ComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
    SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from sme_sigpae_api.dados_comuns.utils import update_instance_from_dict
from sme_sigpae_api.dados_comuns.validators import (
    campo_nao_pode_ser_nulo,
    nao_pode_ser_feriado,
    nao_pode_ser_no_passado,
    objeto_nao_deve_ter_duplicidade,
)
from sme_sigpae_api.escola.models import Escola, PeriodoEscolar, TipoUnidadeEscolar
from sme_sigpae_api.terceirizada.models import Edital


class HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializerCreate(
    serializers.ModelSerializer
):
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
        hora_inicial = attrs["hora_inicial"]
        hora_final = attrs["hora_final"]
        hora_inicio_nao_pode_ser_maior_que_hora_final(hora_inicial, hora_final)
        return attrs

    def create(self, validated_data):
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


class CardapioCreateSerializer(serializers.ModelSerializer):
    tipos_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid",
        many=True,
        required=True,
        queryset=TipoAlimentacao.objects.all(),
    )
    edital = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Edital.objects.all()
    )

    def validate_data(self, data):
        nao_pode_ser_no_passado(data)
        nao_pode_ser_feriado(data)
        objeto_nao_deve_ter_duplicidade(
            Cardapio,
            mensagem="Já existe um cardápio cadastrado com esta data",
            data=data,
        )
        return data

    class Meta:
        model = Cardapio
        exclude = ("id",)


class VinculoTipoAlimentoCreateSerializer(serializers.ModelSerializer):
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
        tipos_alimentacao = validated_data.pop("tipos_alimentacao")
        update_instance_from_dict(instance, validated_data)
        instance.tipos_alimentacao.set(tipos_alimentacao)
        instance.save()
        return instance

    def validate_tipos_alimentacao(self, tipos_alimentacao):
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


class ComboDoVinculoTipoAlimentoSimplesSerializerCreate(serializers.ModelSerializer):
    tipos_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        many=True,
        queryset=TipoAlimentacao.objects.all(),
    )

    vinculo = serializers.SlugRelatedField(
        required=False,
        slug_field="uuid",
        queryset=VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.all(),
    )

    def validate_tipos_alimentacao(self, tipos_alimentacao):
        campo_nao_pode_ser_nulo(
            tipos_alimentacao,
            mensagem="tipos_alimentacao deve ter ao menos um elemento",
        )
        return tipos_alimentacao

    class Meta:
        model = ComboDoVinculoTipoAlimentacaoPeriodoTipoUE
        fields = ("uuid", "tipos_alimentacao", "vinculo")


class SubstituicaoDoComboVinculoTipoAlimentoSimplesSerializerCreate(
    serializers.ModelSerializer
):
    tipos_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        many=True,
        queryset=TipoAlimentacao.objects.all(),
    )

    combo = serializers.SlugRelatedField(
        required=False,
        slug_field="uuid",
        queryset=ComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.all(),
    )

    def validate_tipos_alimentacao(self, tipos_alimentacao):
        campo_nao_pode_ser_nulo(
            tipos_alimentacao,
            mensagem="tipos_alimentacao deve ter ao menos um elemento",
        )
        return tipos_alimentacao

    class Meta:
        model = SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE
        fields = ("uuid", "tipos_alimentacao", "combo")
