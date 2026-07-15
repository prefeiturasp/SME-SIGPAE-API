from rest_framework import serializers

from src.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    MotivoSuspensao,
    QuantidadePorPeriodoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
)
from src.cardapio.suspensao_alimentacao_cei.models import (
    SuspensaoAlimentacaoDaCEI,
)
from src.dados_comuns.api.serializers import LogSolicitacoesUsuarioSerializer
from src.escola.api.serializers import (
    EscolaListagemSimplesSelializer,
    EscolaSimplesSerializer,
    PeriodoEscolarSimplesSerializer,
    TipoAlimentacaoSerializer,
)
from src.terceirizada.api.serializers.serializers import (
    TerceirizadaSimplesSerializer,
)


class MotivoSuspensaoSerializer(serializers.ModelSerializer):
    """Serializa os motivos de suspensão de alimentação.

    Expoe os campos públicos de ``MotivoSuspensao`` usados para listar e
    embutir o motivo selecionado em respostas de solicitações.

    Viewsets que utilizam este serializer:
        - ``MotivosSuspensaoCardapioViewSet``: uso direto como
          ``serializer_class`` nas ações ``list`` e ``retrieve``.
        - ``GrupoSuspensaoAlimentacaoSerializerViewSet``: uso indireto,
          aninhado nos serializers de leitura e criação.
    """

    class Meta:
        model = MotivoSuspensao
        exclude = ("id",)


class SuspensaoAlimentacaoDaCEISerializer(serializers.ModelSerializer):
    """Serializa a representação completa de uma suspensão de CEI.

    Inclui escola, motivo, períodos escolares, logs e rastro da terceirizada
    usados nas respostas detalhadas da API de suspensão de alimentação CEI.

    Viewsets que utilizam este serializer:
        - ``SuspensaoAlimentacaoDaCEIViewSet``: uso direto nas respostas de
          leitura da API de suspensão de alimentação CEI.
    """

    escola = EscolaSimplesSerializer()
    motivo = MotivoSuspensaoSerializer()
    periodos_escolares = PeriodoEscolarSimplesSerializer(many=True)
    id_externo = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = SuspensaoAlimentacaoDaCEI
        exclude = ("id",)


class SuspensaoAlimentacaoSerializer(serializers.ModelSerializer):
    """Serializa uma data de suspensão de alimentação.

    Inclui o motivo aninhado para representar cada item da lista
    ``suspensoes_alimentacao`` da solicitação.

    Viewsets que utilizam este serializer:
        - ``GrupoSuspensaoAlimentacaoSerializerViewSet``: uso indireto,
          aninhado em ``GrupoSuspensaoAlimentacaoSerializer`` nas respostas
          de leitura.
    """

    motivo = MotivoSuspensaoSerializer()

    class Meta:
        model = SuspensaoAlimentacao
        exclude = ("id", "grupo_suspensao")


class QuantidadePorPeriodoSuspensaoAlimentacaoSerializer(serializers.ModelSerializer):
    """Serializa a quantidade de alunos por período escolar.

    Inclui o período escolar e os tipos de alimentação aninhados para
    representar cada item da lista ``quantidades_por_periodo`` da suspensão.

    Viewsets que utilizam este serializer:
        - ``GrupoSuspensaoAlimentacaoSerializerViewSet``: uso indireto,
          aninhado em ``GrupoSuspensaoAlimentacaoSerializer`` nas respostas
          de leitura.
    """

    periodo_escolar = PeriodoEscolarSimplesSerializer()
    tipos_alimentacao = TipoAlimentacaoSerializer(many=True)

    class Meta:
        model = QuantidadePorPeriodoSuspensaoAlimentacao
        exclude = ("id", "grupo_suspensao")


class GrupoSuspensaoAlimentacaoSerializer(serializers.ModelSerializer):
    """Serializa a representação detalhada de uma suspensão de alimentação.

    Inclui escola, quantidades por período, datas de suspensão, logs e
    rastro da terceirizada usados nas respostas completas da API.

    Viewsets que utilizam este serializer:
        - ``GrupoSuspensaoAlimentacaoSerializerViewSet``: retornado por
          ``get_serializer_class()`` em todas as ações de leitura e nas
          actions customizadas que respondem com o objeto serializado, exceto
          ``create``, ``update`` e ``partial_update``.
    """

    escola = EscolaSimplesSerializer()
    quantidades_por_periodo = QuantidadePorPeriodoSuspensaoAlimentacaoSerializer(
        many=True
    )
    suspensoes_alimentacao = SuspensaoAlimentacaoSerializer(many=True)
    id_externo = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = GrupoSuspensaoAlimentacao
        exclude = ("id",)


class GrupoSuspensaoAlimentacaoSimplesSerializer(serializers.ModelSerializer):
    """Serializa uma visão resumida da suspensão de alimentação.

    Remove campos mais pesados e relacionamentos aninhados para atender
    listagens que precisam de um payload menor.

    Viewsets que utilizam este serializer:
        - ``GrupoSuspensaoAlimentacaoSerializerViewSet``: uso direto nas
          actions ``solicitacoes_codae`` e ``solicitacoes_terceirizada``.
    """

    class Meta:
        model = GrupoSuspensaoAlimentacao
        exclude = ("id", "criado_por", "escola")


class GrupoSupensaoAlimentacaoListagemSimplesSerializer(serializers.ModelSerializer):
    """Serializa uma visão enxuta da suspensão para listagens.

    Retorna apenas os campos essenciais para listagens de solicitações
    informadas e rascunhos, incluindo UUID, id externo, status, prioridade
    e escola.

    Viewsets que utilizam este serializer:
        - ``GrupoSuspensaoAlimentacaoSerializerViewSet``: uso direto nas
          actions ``informadas``.
    """

    escola = EscolaListagemSimplesSelializer()
    prioridade = serializers.CharField()

    class Meta:
        model = GrupoSuspensaoAlimentacao
        fields = (
            "uuid",
            "id_externo",
            "status",
            "prioridade",
            "criado_em",
            "escola",
        )
