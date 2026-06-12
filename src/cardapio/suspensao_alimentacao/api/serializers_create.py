from rest_framework import serializers

from src.cardapio.base.models import TipoAlimentacao
from src.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    MotivoSuspensao,
    QuantidadePorPeriodoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
)
from src.dados_comuns.utils import update_instance_from_dict
from src.dados_comuns.validators import (
    deve_ser_no_mesmo_ano_corrente,
    nao_pode_ser_no_passado,
)
from src.escola.models import Escola, PeriodoEscolar


class SuspensaoAlimentacaoCreateSerializer(serializers.ModelSerializer):
    """Serializa a criação de uma data de suspensão de alimentação.

    Recebe a referência do motivo por UUID e valida que a data não seja
    no passado e pertença ao ano corrente.

    Viewsets que utilizam este serializer:
        - ``GrupoSuspensaoAlimentacaoSerializerViewSet``: uso indireto,
          aninhado em ``GrupoSuspensaoAlimentacaoCreateSerializer`` nas
          actions ``create``, ``update`` e ``partial_update``.
    """

    motivo = serializers.SlugRelatedField(
        slug_field="uuid", queryset=MotivoSuspensao.objects.all()
    )

    def validate_data(self, data):
        """Valida que a data da suspensão atende às regras de negócio.

        A data não pode ser no passado e deve pertencer ao ano corrente.

        Args:
            data (datetime.date): Data da suspensão a ser validada.

        Returns:
            datetime.date: A mesma data, após passar pelas validações.
        """
        nao_pode_ser_no_passado(data)
        deve_ser_no_mesmo_ano_corrente(data)
        return data

    class Meta:
        model = SuspensaoAlimentacao
        exclude = ("id",)


class QuantidadePorPeriodoSuspensaoAlimentacaoCreateSerializer(
    serializers.ModelSerializer
):
    """Serializa a criação de uma quantidade de alunos por período escolar.

    Recebe referências por UUID para o período escolar e tipos de
    alimentação associados.

    Viewsets que utilizam este serializer:
        - ``GrupoSuspensaoAlimentacaoSerializerViewSet``: uso indireto,
          aninhado em ``GrupoSuspensaoAlimentacaoCreateSerializer`` nas
          actions ``create``, ``update`` e ``partial_update``.
    """

    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", queryset=PeriodoEscolar.objects.all()
    )
    tipos_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid", many=True, queryset=TipoAlimentacao.objects.all()
    )
    alunos_cei_ou_emei = serializers.CharField(required=False)

    class Meta:
        model = QuantidadePorPeriodoSuspensaoAlimentacao
        exclude = ("id", "grupo_suspensao")


class GrupoSuspensaoAlimentacaoCreateSerializer(serializers.ModelSerializer):
    """Serializa a criação e atualização de suspensões de alimentação.

    Resolve referências por UUID para a escola e recebe listas aninhadas
    de ``quantidades_por_periodo`` e ``suspensoes_alimentacao``. No
    ``create``, persiste o grupo e seus relacionamentos; no ``update``,
    remove e recria os itens vinculados.

    Viewsets que utilizam este serializer:
        - ``GrupoSuspensaoAlimentacaoSerializerViewSet``: retornado por
          ``get_serializer_class()`` nas actions ``create``, ``update`` e
          ``partial_update``.
    """

    escola = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Escola.objects.all()
    )
    quantidades_por_periodo = QuantidadePorPeriodoSuspensaoAlimentacaoCreateSerializer(
        many=True
    )
    suspensoes_alimentacao = SuspensaoAlimentacaoCreateSerializer(many=True)

    def create(self, validated_data):
        """Cria uma solicitação de suspensão com quantidades e datas.

        Args:
            validated_data (dict): Dados validados da solicitação, incluindo
                listas aninhadas de ``quantidades_por_periodo`` e
                ``suspensoes_alimentacao``.

        Returns:
            GrupoSuspensaoAlimentacao: Instância criada com seus
            relacionamentos vinculados.
        """
        quantidades_por_periodo_array = validated_data.pop("quantidades_por_periodo")
        suspensoes_alimentacao_array = validated_data.pop("suspensoes_alimentacao")
        validated_data["criado_por"] = self.context["request"].user

        quantidades = []
        for quantidade_json in quantidades_por_periodo_array:
            quantidade = (
                QuantidadePorPeriodoSuspensaoAlimentacaoCreateSerializer().create(
                    quantidade_json
                )
            )
            quantidades.append(quantidade)

        suspensoes = []
        for suspensao_json in suspensoes_alimentacao_array:
            suspensao = SuspensaoAlimentacaoCreateSerializer().create(suspensao_json)
            suspensoes.append(suspensao)

        grupo = GrupoSuspensaoAlimentacao.objects.create(**validated_data)
        grupo.quantidades_por_periodo.set(quantidades)
        grupo.suspensoes_alimentacao.set(suspensoes)
        return grupo

    def update(self, instance, validated_data):
        """Atualiza uma solicitação de suspensão recriando seus itens.

        Args:
            instance (GrupoSuspensaoAlimentacao): Instância existente a ser
                atualizada.
            validated_data (dict): Dados validados da requisição.

        Returns:
            GrupoSuspensaoAlimentacao: Instância atualizada com seus
            relacionamentos recriados.
        """
        quantidades_por_periodo_array = validated_data.pop("quantidades_por_periodo")
        suspensoes_alimentacao_array = validated_data.pop("suspensoes_alimentacao")

        instance.quantidades_por_periodo.all().delete()
        instance.suspensoes_alimentacao.all().delete()

        quantidades = []
        for quantidade_json in quantidades_por_periodo_array:
            quantidade = (
                QuantidadePorPeriodoSuspensaoAlimentacaoCreateSerializer().create(
                    quantidade_json
                )
            )
            quantidades.append(quantidade)

        suspensoes = []
        for suspensao_json in suspensoes_alimentacao_array:
            suspensao = SuspensaoAlimentacaoCreateSerializer().create(suspensao_json)
            suspensoes.append(suspensao)

        update_instance_from_dict(instance, validated_data, save=True)
        instance.quantidades_por_periodo.set(quantidades)
        instance.suspensoes_alimentacao.set(suspensoes)

        return instance

    class Meta:
        model = GrupoSuspensaoAlimentacao
        exclude = ("id",)
