from rest_framework import serializers

from sme_sigpae_api.cardapio.base.models import (
    Cardapio,
    ComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
    MotivoDRENaoValida,
    SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from sme_sigpae_api.escola.api.serializers import (
    EscolaListagemSimplesSelializer,
    PeriodoEscolarSimplesSerializer,
    TipoUnidadeEscolarSerializer,
    TipoUnidadeEscolarSerializerSimples,
)
from sme_sigpae_api.terceirizada.api.serializers.serializers import EditalSerializer


class TipoAlimentacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAlimentacao
        exclude = ("id",)


class TipoAlimentacaoSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAlimentacao
        fields = (
            "uuid",
            "nome",
        )


class SubstituicaoDoComboVinculoTipoAlimentoSimplesSerializer(
    serializers.ModelSerializer
):
    tipos_alimentacao = TipoAlimentacaoSimplesSerializer(many=True)
    combo = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=ComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.all(),
    )

    class Meta:
        model = SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE
        fields = (
            "uuid",
            "tipos_alimentacao",
            "combo",
            "label",
        )


class CombosVinculoTipoAlimentoSimplesSerializer(serializers.ModelSerializer):
    tipos_alimentacao = TipoAlimentacaoSimplesSerializer(many=True)
    substituicoes = SubstituicaoDoComboVinculoTipoAlimentoSimplesSerializer(many=True)
    vinculo = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.all(),
    )
    label = serializers.SerializerMethodField()

    def get_label(self, obj):
        label = ""
        for tipo_alimentacao in obj.tipos_alimentacao.all():
            if len(label) == 0:
                label += tipo_alimentacao.nome
            else:
                label += f" e {tipo_alimentacao.nome}"
        return label

    class Meta:
        model = ComboDoVinculoTipoAlimentacaoPeriodoTipoUE
        fields = (
            "uuid",
            "tipos_alimentacao",
            "vinculo",
            "substituicoes",
            "label",
        )


class CombosVinculoTipoAlimentoSimplissimaSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    def get_label(self, obj):
        label = ""
        for tipo_alimentacao in obj.tipos_alimentacao.all():
            if len(label) == 0:
                label += tipo_alimentacao.nome
            else:
                label += f" e {tipo_alimentacao.nome}"
        return label

    class Meta:
        model = ComboDoVinculoTipoAlimentacaoPeriodoTipoUE
        fields = (
            "uuid",
            "label",
        )


class HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializer(
    serializers.ModelSerializer
):
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
    nome = serializers.SerializerMethodField()
    tipos_alimentacao = TipoAlimentacaoSerializer(many=True, read_only=True)

    def get_nome(self, obj):
        return obj.periodo_escolar.nome

    class Meta:
        model = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar
        fields = (
            "nome",
            "tipos_alimentacao",
        )


class CardapioSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cardapio
        exclude = ("id",)


class CardapioSerializer(serializers.ModelSerializer):
    tipos_alimentacao = TipoAlimentacaoSerializer(many=True, read_only=True)
    tipos_unidade_escolar = TipoUnidadeEscolarSerializer(many=True, read_only=True)
    edital = EditalSerializer()

    class Meta:
        model = Cardapio
        exclude = ("id",)


class MotivoDRENaoValidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotivoDRENaoValida
        exclude = ("id",)


class TipoUnidadeEscolarAgrupadoSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()
    iniciais = serializers.CharField()
    ativo = serializers.BooleanField()
    tem_somente_integral_e_parcial = serializers.BooleanField()
    pertence_relatorio_solicitacoes_alimentacao = serializers.BooleanField()
    periodos_escolares = serializers.SerializerMethodField()

    def get_periodos_escolares(self, obj):
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
