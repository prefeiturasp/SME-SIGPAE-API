from rest_framework import serializers

from ....dados_comuns.api.serializers import LogSolicitacoesUsuarioSerializer
from ....escola.api.serializers import (
    EscolaListagemSimplesSelializer,
    EscolaSimplesSerializer,
    FaixaEtariaSerializer,
    PeriodoEscolarSerializer,
    PeriodoEscolarSimplesSerializer,
    TipoUnidadeEscolarSerializer,
    TipoUnidadeEscolarSerializerSimples,
)
from ....escola.models import FaixaEtaria
from ....terceirizada.api.serializers.serializers import (
    EditalSerializer,
    TerceirizadaSimplesSerializer,
)
from ...alteracao_tipo_alimentacao.models import (
    AlteracaoCardapio,
    MotivoAlteracaoCardapio,
    SubstituicaoAlimentacaoNoPeriodoEscolar,
)
from ...alteracao_tipo_alimentacao_cei.models import (
    AlteracaoCardapioCEI,
    FaixaEtariaSubstituicaoAlimentacaoCEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEI,
)
from ...alteracao_tipo_alimentacao_cemei.models import (
    AlteracaoCardapioCEMEI,
    FaixaEtariaSubstituicaoAlimentacaoCEMEICEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI,
)
from ...base.models import (
    Cardapio,
    ComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
    MotivoDRENaoValida,
    SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from ...inversao_dia_cardapio.models import InversaoCardapio
from ...suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    MotivoSuspensao,
    QuantidadePorPeriodoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
    SuspensaoAlimentacaoNoPeriodoEscolar,
)
from ...suspensao_alimentacao_cei.models import SuspensaoAlimentacaoDaCEI
from .serializers_create import (
    DatasIntervaloAlteracaoCardapioCEMEICreateSerializer,
    DatasIntervaloAlteracaoCardapioSerializerCreateSerializer,
)


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


class InversaoCardapioSerializer(serializers.ModelSerializer):
    cardapio_de = CardapioSimplesSerializer()
    cardapio_para = CardapioSimplesSerializer()
    escola = EscolaSimplesSerializer()
    id_externo = serializers.CharField()
    prioridade = serializers.CharField()
    data = (
        serializers.DateField()
    )  # representa data do objeto, a menor entre data_de e data_para
    data_de = serializers.DateField()
    data_para = serializers.DateField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    rastro_terceirizada = TerceirizadaSimplesSerializer()
    tipos_alimentacao = TipoAlimentacaoSimplesSerializer(many=True)

    class Meta:
        model = InversaoCardapio
        exclude = ("id", "criado_por")


class InversaoCardapioSimpleserializer(serializers.ModelSerializer):
    id_externo = serializers.CharField()
    prioridade = serializers.CharField()
    escola = EscolaSimplesSerializer()
    data = serializers.DateField()

    class Meta:
        model = InversaoCardapio
        exclude = (
            "id",
            "criado_por",
            "cardapio_de",
            "cardapio_para",
        )


class MotivoSuspensaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotivoSuspensao
        exclude = ("id",)


class SuspensaoAlimentacaoDaCEISerializer(serializers.ModelSerializer):
    escola = EscolaSimplesSerializer()
    motivo = MotivoSuspensaoSerializer()
    periodos_escolares = PeriodoEscolarSimplesSerializer(many=True)
    id_externo = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = SuspensaoAlimentacaoDaCEI
        exclude = ("id",)


class SuspensaoAlimentacaoNoPeriodoEscolarSerializer(serializers.ModelSerializer):
    periodo_escolar = PeriodoEscolarSimplesSerializer()
    tipos_alimentacao = TipoAlimentacaoSerializer(many=True)

    class Meta:
        model = SuspensaoAlimentacaoNoPeriodoEscolar
        exclude = ("id", "suspensao_alimentacao")


class SuspensaoAlimentacaoSerializer(serializers.ModelSerializer):
    motivo = MotivoSuspensaoSerializer()

    class Meta:
        model = SuspensaoAlimentacao
        exclude = ("id", "grupo_suspensao")


class QuantidadePorPeriodoSuspensaoAlimentacaoSerializer(serializers.ModelSerializer):
    periodo_escolar = PeriodoEscolarSimplesSerializer()
    tipos_alimentacao = TipoAlimentacaoSerializer(many=True)

    class Meta:
        model = QuantidadePorPeriodoSuspensaoAlimentacao
        exclude = ("id", "grupo_suspensao")


class GrupoSuspensaoAlimentacaoSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = GrupoSuspensaoAlimentacao
        exclude = ("id", "criado_por", "escola")


class GrupoSupensaoAlimentacaoListagemSimplesSerializer(serializers.ModelSerializer):
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


class MotivoAlteracaoCardapioSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotivoAlteracaoCardapio
        exclude = ("id",)


class FaixaEtariaSubstituicaoAlimentacaoCEISerializer(serializers.ModelSerializer):
    faixa_etaria = FaixaEtariaSerializer()

    class Meta:
        model = FaixaEtariaSubstituicaoAlimentacaoCEI
        exclude = ("id",)


class SubstituicoesAlimentacaoNoPeriodoEscolarSerializerBase(
    serializers.ModelSerializer
):
    periodo_escolar = PeriodoEscolarSerializer()
    alteracao_cardapio = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=AlteracaoCardapio.objects.all()
    )
    tipos_alimentacao_de = TipoAlimentacaoSerializer(many=True)


class SubstituicoesAlimentacaoNoPeriodoEscolarSerializer(
    SubstituicoesAlimentacaoNoPeriodoEscolarSerializerBase
):
    tipos_alimentacao_para = TipoAlimentacaoSerializer(many=True)

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolar
        exclude = ("id",)


class SubstituicoesAlimentacaoNoPeriodoEscolarCEISerializer(
    SubstituicoesAlimentacaoNoPeriodoEscolarSerializerBase
):
    tipo_alimentacao_para = TipoAlimentacaoSerializer()

    faixas_etarias = FaixaEtariaSubstituicaoAlimentacaoCEISerializer(many=True)

    def to_representation(self, instance):
        retorno = super().to_representation(instance)

        faixas_etarias_da_solicitacao = FaixaEtaria.objects.filter(
            uuid__in=[f.faixa_etaria.uuid for f in instance.faixas_etarias.all()]
        )

        # Inclui o total de alunos nas faixas etárias num período
        qtde_alunos = (
            instance.alteracao_cardapio.escola.alunos_por_periodo_e_faixa_etaria(
                instance.alteracao_cardapio.data, faixas_etarias_da_solicitacao
            )
        )

        nome_periodo_correcoes = {
            "PARCIAL": "INTEGRAL",
            "MANHA": "MANHÃ",
        }
        nome_periodo = nome_periodo_correcoes.get(
            instance.periodo_escolar.nome, instance.periodo_escolar.nome
        )

        for faixa_etaria in retorno["faixas_etarias"]:
            try:
                uuid_faixa_etaria = faixa_etaria["faixa_etaria"]["uuid"]
                faixa_etaria["total_alunos_no_periodo"] = qtde_alunos[nome_periodo][
                    uuid_faixa_etaria
                ]
            except KeyError:
                continue

        return retorno

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolarCEI
        exclude = ("id",)


class AlteracaoCardapioSerializerBase(serializers.ModelSerializer):
    escola = EscolaSimplesSerializer()
    motivo = MotivoAlteracaoCardapioSerializer()
    foi_solicitado_fora_do_prazo = serializers.BooleanField()
    eh_alteracao_com_lanche_repetida = serializers.BooleanField()
    id_externo = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    prioridade = serializers.CharField()


class AlteracaoCardapioSerializer(AlteracaoCardapioSerializerBase):
    substituicoes = SubstituicoesAlimentacaoNoPeriodoEscolarSerializer(many=True)
    datas_intervalo = DatasIntervaloAlteracaoCardapioSerializerCreateSerializer(
        many=True
    )
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = AlteracaoCardapio
        exclude = ("id",)


class AlteracaoCardapioCEISerializer(AlteracaoCardapioSerializerBase):
    substituicoes = SubstituicoesAlimentacaoNoPeriodoEscolarCEISerializer(many=True)
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = AlteracaoCardapioCEI
        exclude = ("id",)


class FaixaEtariaSubstituicaoAlimentacaoCEMEICEISerializer(serializers.ModelSerializer):
    faixa_etaria = FaixaEtariaSerializer()

    class Meta:
        model = FaixaEtariaSubstituicaoAlimentacaoCEMEICEI
        exclude = ("id",)


class SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEISerializer(
    serializers.ModelSerializer
):
    periodo_escolar = PeriodoEscolarSerializer()
    faixas_etarias = FaixaEtariaSubstituicaoAlimentacaoCEMEICEISerializer(many=True)
    tipos_alimentacao_de = TipoAlimentacaoSerializer(many=True)
    tipos_alimentacao_para = TipoAlimentacaoSerializer(many=True)

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI
        exclude = ("id",)


class SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEISerializer(
    serializers.ModelSerializer
):
    periodo_escolar = PeriodoEscolarSerializer()
    tipos_alimentacao_de = TipoAlimentacaoSerializer(many=True)
    tipos_alimentacao_para = TipoAlimentacaoSerializer(many=True)

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI
        exclude = ("id",)


class AlteracaoCardapioCEMEISerializer(serializers.ModelSerializer):
    escola = EscolaSimplesSerializer()
    motivo = MotivoAlteracaoCardapioSerializer()
    foi_solicitado_fora_do_prazo = serializers.BooleanField()
    id_externo = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    prioridade = serializers.CharField()
    substituicoes_cemei_cei_periodo_escolar = (
        SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEISerializer(many=True)
    )
    substituicoes_cemei_emei_periodo_escolar = (
        SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEISerializer(many=True)
    )
    datas_intervalo = DatasIntervaloAlteracaoCardapioCEMEICreateSerializer(many=True)

    class Meta:
        model = AlteracaoCardapioCEMEI
        exclude = ("id",)


class AlteracaoCardapioSimplesSerializer(serializers.ModelSerializer):
    prioridade = serializers.CharField()

    class Meta:
        model = AlteracaoCardapio
        exclude = ("id", "criado_por", "escola", "motivo")


class MotivoDRENaoValidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotivoDRENaoValida
        exclude = ("id",)
