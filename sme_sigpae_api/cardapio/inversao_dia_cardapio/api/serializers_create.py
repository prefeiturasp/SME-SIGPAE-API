import datetime

from rest_framework import serializers

from sme_sigpae_api.cardapio.base.models import TipoAlimentacao
from sme_sigpae_api.cardapio.inversao_dia_cardapio.api.validators import (
    nao_pode_existir_solicitacao_igual_para_mesma_escola,
    nao_pode_ter_mais_que_60_dias_diferenca,
)
from sme_sigpae_api.cardapio.inversao_dia_cardapio.models import InversaoCardapio
from sme_sigpae_api.dados_comuns.utils import update_instance_from_dict
from sme_sigpae_api.dados_comuns.validators import (
    deve_ser_dia_letivo_e_dia_da_semana,
    deve_ser_no_mesmo_ano_corrente,
    nao_pode_ser_no_passado,
)
from sme_sigpae_api.escola.models import Escola


class InversaoCardapioSerializerCreate(serializers.ModelSerializer):
    data_de = serializers.DateField()
    data_para = serializers.DateField()
    data_de_2 = serializers.DateField(required=False, allow_null=True)
    data_para_2 = serializers.DateField(required=False, allow_null=True)
    tipos_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid", many=True, queryset=TipoAlimentacao.objects.all()
    )

    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Escola.objects.all()
    )

    status_explicacao = serializers.CharField(
        source="status", required=False, read_only=True
    )

    def validate_data_de(self, data_de):
        nao_pode_ser_no_passado(data_de)
        return data_de

    def validate_data_para(self, data_para):
        nao_pode_ser_no_passado(data_para)
        return data_para

    def validate_data_de_2(self, data_de_2):
        if data_de_2 is not None:
            nao_pode_ser_no_passado(data_de_2)
        return data_de_2

    def validate_data_para_2(self, data_para_2):
        if data_para_2 is not None:
            nao_pode_ser_no_passado(data_para_2)
        return data_para_2

    def validate(self, attrs):
        data_de = attrs["data_de"]
        data_para = attrs["data_para"]
        escola = attrs["escola"]
        tipos_alimentacao = attrs["tipos_alimentacao"]

        if data_de.month != 12 and datetime.date.today().year + 1 not in [
            data_de.year,
            data_para.year,
        ]:
            deve_ser_no_mesmo_ano_corrente(data_de)
            deve_ser_no_mesmo_ano_corrente(data_para)

        nao_pode_existir_solicitacao_igual_para_mesma_escola(
            data_de, data_para, escola, tipos_alimentacao
        )
        nao_pode_ter_mais_que_60_dias_diferenca(data_de, data_para)
        deve_ser_dia_letivo_e_dia_da_semana(escola, data_de)
        deve_ser_dia_letivo_e_dia_da_semana(escola, data_para)
        if "data_de_2" in attrs and attrs["data_de_2"] is not None:
            data_de_2 = attrs["data_de_2"]
            data_para_2 = attrs["data_para_2"]
            nao_pode_existir_solicitacao_igual_para_mesma_escola(
                data_de_2, data_para_2, escola, tipos_alimentacao
            )
            nao_pode_ter_mais_que_60_dias_diferenca(data_de_2, data_para_2)
            deve_ser_dia_letivo_e_dia_da_semana(escola, data_de_2)
            deve_ser_dia_letivo_e_dia_da_semana(escola, data_para_2)

        return attrs

    def create(self, validated_data):
        data_de = validated_data.pop("data_de")
        data_para = validated_data.pop("data_para")
        data_de_2 = validated_data.pop("data_de_2", None)
        data_para_2 = validated_data.pop("data_para_2", None)

        validated_data["data_de_inversao"] = data_de
        validated_data["data_para_inversao"] = data_para
        validated_data["data_de_inversao_2"] = data_de_2
        validated_data["data_para_inversao_2"] = data_para_2
        validated_data["criado_por"] = self.context["request"].user
        tipos_alimentacao = validated_data.pop("tipos_alimentacao", None)
        inversao_cardapio = InversaoCardapio.objects.create(**validated_data)
        if tipos_alimentacao:
            inversao_cardapio.tipos_alimentacao.set(tipos_alimentacao)

        return inversao_cardapio

    def update(self, instance, validated_data):
        data_de = validated_data.pop("data_de")
        data_para = validated_data.pop("data_para")
        data_de_2 = validated_data.pop("data_de_2", None)
        data_para_2 = validated_data.pop("data_para_2", None)
        if instance.cardapio_de or instance.cardapio_para:
            instance.cardapio_de = None
            instance.cardapio_para = None
            instance.save()
        validated_data["data_de_inversao"] = data_de
        validated_data["data_para_inversao"] = data_para
        validated_data["data_de_inversao_2"] = data_de_2
        validated_data["data_para_inversao_2"] = data_para_2
        tipos_alimentacao = validated_data.pop("tipos_alimentacao", None)
        update_instance_from_dict(instance, validated_data)
        instance.save()
        if tipos_alimentacao:
            instance.tipos_alimentacao.set(tipos_alimentacao)
        return instance

    class Meta:
        model = InversaoCardapio
        fields = (
            "uuid",
            "motivo",
            "observacao",
            "data_de",
            "data_para",
            "tipos_alimentacao",
            "data_de_2",
            "data_para_2",
            "escola",
            "status_explicacao",
            "alunos_da_cemei",
            "alunos_da_cemei_2",
        )
