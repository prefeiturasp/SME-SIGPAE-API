from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.validators import (
    precisa_pertencer_a_um_tipo_de_alimentacao,
    valida_duplicidade_solicitacoes_lanche_emergencial,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    AlteracaoCardapio,
    DataIntervaloAlteracaoCardapio,
    MotivoAlteracaoCardapio,
    SubstituicaoAlimentacaoNoPeriodoEscolar,
)
from sme_sigpae_api.cardapio.base.models import TipoAlimentacao
from sme_sigpae_api.dados_comuns.utils import update_instance_from_dict
from sme_sigpae_api.dados_comuns.validators import (
    deve_pedir_com_antecedencia,
    deve_ser_no_mesmo_ano_corrente,
    nao_pode_ser_no_passado,
    valida_datas_alteracao_cardapio,
    valida_duplicidade_solicitacoes,
)
from sme_sigpae_api.escola.models import DiaCalendario, Escola, PeriodoEscolar
from sme_sigpae_api.escola.utils import eh_dia_sem_atividade_escolar


class SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreateBase(
    serializers.ModelSerializer
):
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=PeriodoEscolar.objects.all()
    )

    tipos_alimentacao_de = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        many=True,
        queryset=TipoAlimentacao.objects.all(),
    )


class SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreate(
    SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreateBase
):
    alteracao_cardapio = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=AlteracaoCardapio.objects.all()
    )
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=PeriodoEscolar.objects.all()
    )

    tipos_alimentacao_para = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        many=True,
        queryset=TipoAlimentacao.objects.all(),
    )

    def create(self, validated_data):
        tipos_alimentacao_de = validated_data.pop("tipos_alimentacao_de")
        tipos_alimentacao_para = validated_data.pop("tipos_alimentacao_para")
        substituicao_alimentacao = (
            SubstituicaoAlimentacaoNoPeriodoEscolar.objects.create(**validated_data)
        )
        substituicao_alimentacao.tipos_alimentacao_de.set(tipos_alimentacao_de)
        substituicao_alimentacao.tipos_alimentacao_para.set(tipos_alimentacao_para)
        return substituicao_alimentacao

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolar
        exclude = ("id",)


class AlteracaoCardapioSerializerCreateBase(serializers.ModelSerializer):
    motivo = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=MotivoAlteracaoCardapio.objects.all()
    )
    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Escola.objects.all()
    )
    status_explicacao = serializers.CharField(
        source="status", required=False, read_only=True
    )

    def create(self, validated_data):
        substituicoes = validated_data.pop("substituicoes")
        validated_data["criado_por"] = self.context["request"].user

        substituicoes_lista = []
        for substituicao in substituicoes:
            substituicoes_object = self.Meta.serializer_substituicao().create(
                substituicao
            )
            substituicoes_lista.append(substituicoes_object)
        alteracao_cardapio = self.Meta.model.objects.create(**validated_data)
        alteracao_cardapio.substituicoes.set(substituicoes_lista)

        return alteracao_cardapio

    def update(self, instance, validated_data):
        substituicoes_json = validated_data.pop("substituicoes")
        instance.substituicoes.all().delete()

        substituicoes_lista = []
        for substituicao_json in substituicoes_json:
            substituicoes_object = self.Meta.serializer_substituicao().create(
                substituicao_json
            )
            substituicoes_lista.append(substituicoes_object)

        update_instance_from_dict(instance, validated_data)
        instance.substituicoes.set(substituicoes_lista)
        instance.save()

        return instance


class DatasIntervaloAlteracaoCardapioSerializerCreateSerializer(
    serializers.ModelSerializer
):
    alteracao_cardapio = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=AlteracaoCardapio.objects.all()
    )

    def create(self, validated_data):
        data_intervalo = DataIntervaloAlteracaoCardapio.objects.create(**validated_data)
        return data_intervalo

    class Meta:
        model = DataIntervaloAlteracaoCardapio
        exclude = ("id",)


class AlteracaoCardapioSerializerCreate(AlteracaoCardapioSerializerCreateBase):
    substituicoes = SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreate(many=True)
    datas_intervalo = DatasIntervaloAlteracaoCardapioSerializerCreateSerializer(
        required=False, many=True
    )

    def validate(self, attrs):
        escola = attrs.get("escola")
        substituicoes = attrs.get("substituicoes")
        for substicuicao in substituicoes:
            tipos_alimentacao_de = substicuicao.get("tipos_alimentacao_de")
            tipo_alimentacao_para = substicuicao.get("tipo_alimentacao_para")
            periodo_escolar = substicuicao.get("periodo_escolar")
            precisa_pertencer_a_um_tipo_de_alimentacao(
                tipos_alimentacao_de,
                tipo_alimentacao_para,
                escola.tipo_unidade,
                periodo_escolar,
            )
        valida_datas_alteracao_cardapio(attrs)
        nao_pode_ser_no_passado(attrs["data_inicial"])
        if attrs["motivo"].nome != "Lanche Emergencial":
            deve_pedir_com_antecedencia(attrs["data_inicial"])
        if attrs["motivo"].nome == "RPL - Refeição por Lanche":
            valida_duplicidade_solicitacoes(attrs)
        deve_ser_no_mesmo_ano_corrente(attrs["data_inicial"])

        return attrs

    def datas_nos_meses_de_ferias(self, datas_intervalo):
        MESES_DE_FERIAS = [1, 7, 12]
        return (
            datas_intervalo[0]["data"].month in MESES_DE_FERIAS
            or datas_intervalo[-1]["data"].month in MESES_DE_FERIAS
        )

    def criar_datas_intervalo(self, datas_intervalo, instance):
        datas_intervalo = [
            dict(item, **{"alteracao_cardapio": instance}) for item in datas_intervalo
        ]
        if not instance.eh_alteracao_lanche_emergencial():
            for data_intervalo in datas_intervalo:
                DataIntervaloAlteracaoCardapio.objects.create(**data_intervalo)
        else:
            if not DiaCalendario.pelo_menos_um_dia_letivo(
                instance.escola,
                [data_intervalo["data"] for data_intervalo in datas_intervalo],
                instance,
            ) and not self.datas_nos_meses_de_ferias(datas_intervalo):
                raise ValidationError(
                    "Não é possível solicitar Lanche Emergencial para dia(s) não letivo(s)"
                )
            for data_intervalo in datas_intervalo:
                if eh_dia_sem_atividade_escolar(
                    instance.escola, data_intervalo["data"], instance
                ) and not self.datas_nos_meses_de_ferias(datas_intervalo):
                    continue
                DataIntervaloAlteracaoCardapio.objects.create(**data_intervalo)

    def criar_substituicoes(self, substituicoes, instance):
        substituicoes = [
            dict(item, **{"alteracao_cardapio": instance}) for item in substituicoes
        ]
        for substituicao in substituicoes:
            tipos_alimentacao_de = substituicao.pop("tipos_alimentacao_de")
            tipos_alimentacao_para = substituicao.pop("tipos_alimentacao_para")
            substituicao_alimentacao = (
                SubstituicaoAlimentacaoNoPeriodoEscolar.objects.create(**substituicao)
            )
            substituicao_alimentacao.tipos_alimentacao_de.set(tipos_alimentacao_de)
            substituicao_alimentacao.tipos_alimentacao_para.set(tipos_alimentacao_para)

    def create(self, validated_data):
        valida_duplicidade_solicitacoes_lanche_emergencial(validated_data)
        validated_data["criado_por"] = self.context["request"].user
        substituicoes = validated_data.pop("substituicoes")
        datas_intervalo = validated_data.pop("datas_intervalo", [])
        alteracao_cardapio = AlteracaoCardapio.objects.create(**validated_data)

        self.criar_substituicoes(substituicoes, alteracao_cardapio)
        self.criar_datas_intervalo(datas_intervalo, alteracao_cardapio)

        return alteracao_cardapio

    def update(self, instance, validated_data):
        valida_duplicidade_solicitacoes_lanche_emergencial(validated_data)
        instance.substituicoes.all().delete()
        instance.datas_intervalo.all().delete()

        validated_data["criado_por"] = self.context["request"].user
        substituicoes = validated_data.pop("substituicoes")
        datas_intervalo = validated_data.pop("datas_intervalo", [])
        update_instance_from_dict(instance, validated_data)
        instance.save()

        self.criar_substituicoes(substituicoes, instance)
        self.criar_datas_intervalo(datas_intervalo, instance)

        return instance

    class Meta:
        model = AlteracaoCardapio
        serializer_substituicao = (
            SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreate
        )
        exclude = ("id", "status")
