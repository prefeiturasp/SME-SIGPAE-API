"""Serializers da subapp base do modulo de cardapio.

Reune serializers de leitura usados para expor tipos de alimentacao,
configuracoes de horario por escola, vinculos de periodo/tipo de unidade e
motivos de nao validacao da DRE.
"""

from rest_framework import serializers

from src.cardapio.base.models import (
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
    MotivoDRENaoValida,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from src.escola.api.serializers import (
    EscolaListagemSimplesSelializer,
    PeriodoEscolarSimplesSerializer,
    TipoUnidadeEscolarSerializerSimples,
)


class TipoAlimentacaoSerializer(serializers.ModelSerializer):
    """Serializa tipos de alimentacao com sua representacao completa de leitura.

    Expoe os campos publicos de ``TipoAlimentacao`` usados na API base e em
    serializers aninhados que retornam os tipos de alimentacao permitidos para
    horarios e vinculos.

    Viewsets que utilizam este serializer:
            - ``TipoAlimentacaoViewSet``: uso direto como ``serializer_class`` nas
                acoes padrao do ``ModelViewSet``.
            - ``HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarViewSet``: uso
                indireto, aninhado em
                ``HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializer``.
            - ``VinculoTipoAlimentacaoViewSet``: uso indireto, aninhado em
                ``VinculoTipoAlimentoSimplesSerializer`` e
                ``VinculoTipoAlimentoPeriodoSerializer``.
    """

    class Meta:
        model = TipoAlimentacao
        exclude = ("id",)


class TipoAlimentacaoSimplesSerializer(serializers.ModelSerializer):
    """Serializa uma visao resumida dos tipos de alimentacao.

    Retorna apenas UUID e nome, sendo usado quando o payload precisa listar os
    tipos de alimentacao vinculados a um periodo escolar sem incluir todos os
    campos do modelo.

    Viewsets que utilizam este serializer:
        - Nenhum diretamente.
        - Uso indireto em ``VinculosPorTipoUnidadeEscolarViewSet``, por meio de
          ``TipoUnidadeEscolarAgrupadoSerializer``.
    """

    class Meta:
        model = TipoAlimentacao
        fields = (
            "uuid",
            "nome",
        )


class HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializer(
    serializers.ModelSerializer
):
    """Serializa horarios configurados para tipos de alimentacao por escola.

    Retorna a faixa de horario com os relacionamentos de escola, tipo de
    alimentacao e periodo escolar ja expandidos por serializers simples.

    Viewsets que utilizam este serializer:
        - ``HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarViewSet``:
          retornado por ``get_serializer_class()`` nas acoes de leitura.
    """

    escola = EscolaListagemSimplesSelializer()
    tipo_alimentacao = TipoAlimentacaoSerializer()
    periodo_escolar = PeriodoEscolarSimplesSerializer()

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


class VinculoTipoAlimentoSimplesSerializer(serializers.ModelSerializer):
    """Serializa um vinculo ativo entre periodo, tipo de U.E. e alimentacoes.

    Retorna o tipo de unidade escolar, o periodo escolar e a colecao de tipos
    de alimentacao autorizados para aquela combinacao.

    Viewsets que utilizam este serializer:
        - ``VinculoTipoAlimentacaoViewSet``: uso direto como
          ``serializer_class`` nas acoes de leitura.
    """

    tipo_unidade_escolar = TipoUnidadeEscolarSerializerSimples()
    periodo_escolar = PeriodoEscolarSimplesSerializer()
    tipos_alimentacao = TipoAlimentacaoSerializer(many=True, read_only=True)

    class Meta:
        model = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar
        fields = (
            "uuid",
            "tipo_unidade_escolar",
            "periodo_escolar",
            "tipos_alimentacao",
        )


class VinculoTipoAlimentoPeriodoSerializer(serializers.ModelSerializer):
    """Serializa vinculos agrupando o periodo pelo nome exibivel.

    Converte o periodo escolar em um campo textual ``nome`` e retorna os tipos
    de alimentacao relacionados para compor respostas resumidas por periodo.

    Viewsets que utilizam este serializer:
        - Nenhum diretamente no modulo.
        - Pode ser reutilizado por endpoints que precisem expor vinculos por
          periodo escolar em formato resumido.
    """

    nome = serializers.SerializerMethodField()
    tipos_alimentacao = TipoAlimentacaoSerializer(many=True, read_only=True)

    def get_nome(self, obj):
        """Retorna o nome do periodo escolar associado ao vinculo.

        Args:
            obj (VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar):
                Vinculo serializado.

        Returns:
            str: Nome do periodo escolar relacionado ao vinculo.
        """
        return obj.periodo_escolar.nome

    class Meta:
        model = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar
        fields = (
            "nome",
            "tipos_alimentacao",
        )


class MotivoDRENaoValidaSerializer(serializers.ModelSerializer):
    """Serializa os motivos usados pela DRE para nao validar solicitacoes.

    Expoe os campos publicos de ``MotivoDRENaoValida`` para consumo em listas e
    seletores da API.

    Viewsets que utilizam este serializer:
        - ``MotivosDRENaoValidaViewSet``: uso direto como ``serializer_class``
          nas acoes de listagem e detalhamento.
    """

    class Meta:
        model = MotivoDRENaoValida
        exclude = ("id",)


class TipoUnidadeEscolarAgrupadoSerializer(serializers.Serializer):
    """Serializa tipos de unidade escolar agrupados com seus vinculos.

    Recebe uma estrutura agregada em memoria contendo o tipo de unidade e os
    vinculos associados e monta a resposta final com periodos escolares e tipos
    de alimentacao permitidos.

    Viewsets que utilizam este serializer:
        - ``VinculosPorTipoUnidadeEscolarViewSet``: uso direto na action
          ``list``.
    """

    uuid = serializers.UUIDField()
    iniciais = serializers.CharField()
    ativo = serializers.BooleanField()
    tem_somente_integral_e_parcial = serializers.BooleanField()
    pertence_relatorio_solicitacoes_alimentacao = serializers.BooleanField()
    periodos_escolares = serializers.SerializerMethodField()

    def get_periodos_escolares(self, obj):
        """Monta os periodos escolares agrupados para um tipo de unidade.

        Args:
            obj (dict): Dicionario agregado contendo a chave ``vinculos`` com
                os vinculos do tipo de unidade escolar.

        Returns:
            list[dict]: Lista de periodos escolares com UUID, nome e tipos de
            alimentacao serializados.
        """
        vinculos = obj.get("vinculos", [])
        periodos_data = []

        for vinculo in vinculos:
            periodo_data = {
                "uuid": vinculo.periodo_escolar.uuid,
                "nome": vinculo.periodo_escolar.nome,
                "tipos_alimentacao": TipoAlimentacaoSimplesSerializer(
                    vinculo.tipos_alimentacao.all(), many=True
                ).data,
            }
            periodos_data.append(periodo_data)

        return periodos_data

    @staticmethod
    def agrupar_vinculos_por_tipo_ue(vinculos):
        """Agrupa vinculos ativos pelo UUID do tipo de unidade escolar.

        Args:
            vinculos (Iterable[VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar]):
                Vinculos a serem agrupados.

        Returns:
            list[dict]: Lista ordenada por iniciais contendo os dados do tipo
            de unidade escolar e a colecao de vinculos correspondente.
        """
        from collections import defaultdict

        agrupados = defaultdict(list)

        for vinculo in vinculos:
            if vinculo.tipo_unidade_escolar:
                key = vinculo.tipo_unidade_escolar.uuid
                agrupados[key].append(vinculo)

        resultado = []
        for _, vinculos_do_tipo in agrupados.items():
            tipo_ue = vinculos_do_tipo[0].tipo_unidade_escolar

            dados_tipo_ue = {
                "uuid": tipo_ue.uuid,
                "iniciais": tipo_ue.iniciais,
                "ativo": tipo_ue.ativo,
                "tem_somente_integral_e_parcial": tipo_ue.tem_somente_integral_e_parcial,
                "pertence_relatorio_solicitacoes_alimentacao": tipo_ue.pertence_relatorio_solicitacoes_alimentacao,
                "vinculos": vinculos_do_tipo,
            }
            resultado.append(dados_tipo_ue)

        return sorted(resultado, key=lambda x: x["iniciais"])
