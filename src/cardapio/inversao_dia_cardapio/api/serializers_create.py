"""Serializer de escrita da API de inversao de dia de cardapio."""

import datetime

from rest_framework import serializers

from src.cardapio.base.models import TipoAlimentacao
from src.cardapio.inversao_dia_cardapio.api.validators import (
    nao_pode_existir_solicitacao_igual_para_mesma_escola,
    nao_pode_ter_mais_que_60_dias_diferenca,
)
from src.cardapio.inversao_dia_cardapio.models import InversaoCardapio
from src.dados_comuns.utils import update_instance_from_dict
from src.dados_comuns.validators import (
    deve_ser_dia_letivo_e_dia_da_semana,
    deve_ser_no_mesmo_ano_corrente,
    nao_pode_ser_no_passado,
)
from src.escola.models import Escola


class InversaoCardapioSerializerCreate(serializers.ModelSerializer):
    """Serializa a criação e a atualização de ``InversaoCardapio``.

    Recebe as datas expostas pela API, aplica validações de negócio e converte
    os campos para a estrutura persistida no modelo.
    """

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
        """Valida se a data inicial da primeira inversão não está no passado.

        Args:
            data_de (datetime.date): Data inicial informada na solicitação.

        Returns:
            datetime.date: A mesma data validada.
        """
        nao_pode_ser_no_passado(data_de)
        return data_de

    def validate_data_para(self, data_para):
        """Valida se a data final da primeira inversão não está no passado.

        Args:
            data_para (datetime.date): Data final informada na solicitação.

        Returns:
            datetime.date: A mesma data validada.
        """
        nao_pode_ser_no_passado(data_para)
        return data_para

    def validate_data_de_2(self, data_de_2):
        """Valida a segunda data inicial quando uma segunda inversão é enviada; não pode ser no passado.

        Args:
            data_de_2 (datetime.date | None): Segunda data inicial da
                solicitação.

        Returns:
            datetime.date | None: A data validada ou ``None`` quando ausente.
        """
        if data_de_2 is not None:
            nao_pode_ser_no_passado(data_de_2)
        return data_de_2

    def validate_data_para_2(self, data_para_2):
        """Valida a segunda data final quando uma segunda inversão é enviada; não pode ser no passado.

        Args:
            data_para_2 (datetime.date | None): Segunda data final da
                solicitação.

        Returns:
            datetime.date | None: A data validada ou ``None`` quando ausente.
        """
        if data_para_2 is not None:
            nao_pode_ser_no_passado(data_para_2)
        return data_para_2

    def validate(self, attrs):
        """Aplica as validações de negócio da solicitação de inversão.

        - as datas devem ser do mesmo ano corrente ou do próximo ano quando a solicitação for feita no mês de dezembro;
        - não pode existir outra solicitação de inversão para a mesma escola, tipos de alimentação e datas, que esteja em aberto;
        - a diferença entre as datas de origem e destino da inversão não pode ser superior a 60 dias;
        - as datas informadas devem ser dias letivos e dias da semana válidos para a escola.

        Args:
            attrs (dict): Dados normalizados pelo serializer antes da
                persistência.

        Returns:
            dict: O dicionário de atributos validado.
        """
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
        """Cria uma ``InversaoCardapio`` a partir dos campos expostos pela API.

        Args:
            validated_data (dict): Dados da solicitação após as validações do
                serializer.

        Returns:
            InversaoCardapio: Instância criada com os tipos de alimentação
            associados.
        """
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
        """Atualiza uma ``InversaoCardapio`` convertendo os campos da API.

        Args:
            instance (InversaoCardapio): Instância persistida a ser atualizada.
            validated_data (dict): Dados validados enviados na requisição.

        Returns:
            InversaoCardapio: Instância atualizada.
        """
        data_de = validated_data.pop("data_de")
        data_para = validated_data.pop("data_para")
        data_de_2 = validated_data.pop("data_de_2", None)
        data_para_2 = validated_data.pop("data_para_2", None)
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
