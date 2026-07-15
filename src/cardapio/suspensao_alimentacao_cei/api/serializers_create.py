from rest_framework import serializers

from src.cardapio.suspensao_alimentacao.models import MotivoSuspensao
from src.cardapio.suspensao_alimentacao_cei.models import (
    SuspensaoAlimentacaoDaCEI,
)
from src.dados_comuns.utils import update_instance_from_dict
from src.dados_comuns.validators import (
    deve_pedir_com_antecedencia,
    deve_ser_no_mesmo_ano_corrente,
    nao_pode_ser_no_passado,
)
from src.escola.models import Escola, PeriodoEscolar


class SuspensaoAlimentacaodeCEICreateSerializer(serializers.ModelSerializer):
    """Serializa a criação e atualização de suspensões de alimentação de CEI.

    Resolve referências por UUID para a escola, motivo e períodos escolares.
    Valida datas e regras de negócio e persiste os relacionamentos M2M de
    períodos escolares.

    Viewsets que utilizam este serializer:
        - ``SuspensaoAlimentacaoDaCEIViewSet``: retornado por
          ``get_serializer_class()`` nas actions ``create``, ``update`` e
          ``partial_update``.
    """

    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Escola.objects.all()
    )

    motivo = serializers.SlugRelatedField(
        slug_field="uuid", queryset=MotivoSuspensao.objects.all()
    )

    outro_motivo = serializers.CharField(required=False)

    periodos_escolares = serializers.SlugRelatedField(
        slug_field="uuid", many=True, queryset=PeriodoEscolar.objects.all()
    )

    def validate(self, attrs):
        """Valida as regras de negócio para a data da solicitação CEI.

        A data não pode ser no passado, deve pedir com antecedência e deve
        pertencer ao ano corrente.

        Args:
            attrs (dict): Atributos validados contendo a chave ``data``.

        Returns:
            dict: Atributos validados após a aplicação das regras de
            negócio.
        """
        data = attrs["data"]
        nao_pode_ser_no_passado(data)
        deve_pedir_com_antecedencia(data)
        deve_ser_no_mesmo_ano_corrente(data)
        return attrs

    def create(self, validated_data):
        """Cria uma solicitação de suspensão de CEI com os períodos escolares.

        Args:
            validated_data (dict): Dados validados da solicitação, incluindo
                a lista ``periodos_escolares``.

        Returns:
            SuspensaoAlimentacaoDaCEI: Instância criada com os períodos
            escolares vinculados.
        """
        periodos_escolares = validated_data.pop("periodos_escolares", "")
        validated_data["criado_por"] = self.context["request"].user
        suspensao_alimentacao = SuspensaoAlimentacaoDaCEI.objects.create(
            **validated_data
        )
        suspensao_alimentacao.periodos_escolares.set(periodos_escolares)
        suspensao_alimentacao.save()
        return suspensao_alimentacao

    def update(self, instance, validated_data):
        """Atualiza uma solicitação de suspensão de CEI recriando seus períodos.

        Remove os períodos escolares existentes e define os novos a partir
        dos dados validados.

        Args:
            instance (SuspensaoAlimentacaoDaCEI): Instância existente a ser
                atualizada.
            validated_data (dict): Dados validados da requisição.

        Returns:
            SuspensaoAlimentacaoDaCEI: Instância atualizada com os novos
            períodos escolares.
        """
        periodos_escolares = validated_data.pop("periodos_escolares", "")
        update_instance_from_dict(instance, validated_data)
        instance.periodos_escolares.set([])
        instance.periodos_escolares.set(periodos_escolares)
        instance.save()
        return instance

    class Meta:
        model = SuspensaoAlimentacaoDaCEI
        exclude = ("id", "status", "criado_por")
