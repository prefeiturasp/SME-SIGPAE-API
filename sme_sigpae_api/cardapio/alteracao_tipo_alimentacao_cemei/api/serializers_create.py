from rest_framework import serializers

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    MotivoAlteracaoCardapio,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.models import (
    AlteracaoCardapioCEMEI,
    DataIntervaloAlteracaoCardapioCEMEI,
    FaixaEtariaSubstituicaoAlimentacaoCEMEICEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI,
)
from sme_sigpae_api.cardapio.api.validators import (
    valida_duplicidade_solicitacoes_lanche_emergencial,
)
from sme_sigpae_api.cardapio.base.models import TipoAlimentacao
from sme_sigpae_api.dados_comuns.utils import update_instance_from_dict
from sme_sigpae_api.dados_comuns.validators import (
    deve_pedir_com_antecedencia,
    deve_ser_no_mesmo_ano_corrente,
    nao_pode_ser_no_passado,
    valida_duplicidade_solicitacoes_cemei,
)
from sme_sigpae_api.escola.models import Escola, FaixaEtaria, PeriodoEscolar


class FaixaEtariaSubstituicaoAlimentacaoCEMEICEICreateSerializer(
    serializers.ModelSerializer
):
    faixa_etaria = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=FaixaEtaria.objects.all()
    )
    substituicao_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI.objects.all(),
    )

    class Meta:
        model = FaixaEtariaSubstituicaoAlimentacaoCEMEICEI
        exclude = ("id",)


class SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEICreateSerializer(
    serializers.ModelSerializer
):
    alteracao_cardapio = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=AlteracaoCardapioCEMEI.objects.all()
    )
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=PeriodoEscolar.objects.all()
    )
    tipos_alimentacao_de = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        many=True,
        queryset=TipoAlimentacao.objects.all(),
    )
    tipos_alimentacao_para = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        many=True,
        queryset=TipoAlimentacao.objects.all(),
    )
    faixas_etarias = FaixaEtariaSubstituicaoAlimentacaoCEMEICEICreateSerializer(
        many=True
    )

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI
        exclude = ("id",)


class SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEICreateSerializer(
    serializers.ModelSerializer
):
    alteracao_cardapio = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=AlteracaoCardapioCEMEI.objects.all()
    )
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=PeriodoEscolar.objects.all()
    )
    tipos_alimentacao_de = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        many=True,
        queryset=TipoAlimentacao.objects.all(),
    )
    tipos_alimentacao_para = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        many=True,
        queryset=TipoAlimentacao.objects.all(),
    )

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI
        exclude = ("id",)


class DatasIntervaloAlteracaoCardapioCEMEICreateSerializer(serializers.ModelSerializer):
    alteracao_cardapio_cemei = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=AlteracaoCardapioCEMEI.objects.all()
    )

    def create(self, validated_data):
        data_intervalo = DataIntervaloAlteracaoCardapioCEMEI.objects.create(
            **validated_data
        )
        return data_intervalo

    class Meta:
        model = DataIntervaloAlteracaoCardapioCEMEI
        exclude = ("id",)


class AlteracaoCardapioCEMEISerializerCreate(serializers.ModelSerializer):
    motivo = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=MotivoAlteracaoCardapio.objects.all()
    )
    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Escola.objects.all()
    )

    substituicoes_cemei_cei_periodo_escolar = (
        SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEICreateSerializer(
            required=False, many=True
        )
    )
    substituicoes_cemei_emei_periodo_escolar = (
        SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEICreateSerializer(
            required=False, many=True
        )
    )
    datas_intervalo = DatasIntervaloAlteracaoCardapioCEMEICreateSerializer(
        required=False, many=True
    )

    def criar_faixas_etarias_cemei(self, faixas_etarias, substituicao):
        if not faixas_etarias:
            return
        faixas_etarias = [
            dict(item, **{"substituicao_alimentacao": substituicao})
            for item in faixas_etarias
        ]

        for faixa_etaria in faixas_etarias:
            FaixaEtariaSubstituicaoAlimentacaoCEMEICEI.objects.create(**faixa_etaria)

    def criar_substituicoes_cemei_cei(
        self, substituicoes_cemei_cei_periodo_escolar, alteracao_cemei
    ):
        if not substituicoes_cemei_cei_periodo_escolar:
            return
        substituicoes_cemei_cei_periodo_escolar = [
            dict(item, **{"alteracao_cardapio": alteracao_cemei})
            for item in substituicoes_cemei_cei_periodo_escolar
        ]

        for substituicao in substituicoes_cemei_cei_periodo_escolar:
            tipos_alimentacao_de = substituicao.pop("tipos_alimentacao_de", [])
            tipos_alimentacao_para = substituicao.pop("tipos_alimentacao_para", [])
            faixas_etarias = substituicao.pop("faixas_etarias", [])
            subs = SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI.objects.create(
                **substituicao
            )
            subs.tipos_alimentacao_de.set(tipos_alimentacao_de)
            subs.tipos_alimentacao_para.set(tipos_alimentacao_para)
            self.criar_faixas_etarias_cemei(faixas_etarias, subs)

    def criar_substituicoes_cemei_emei(
        self, substituicoes_cemei_emei_periodo_escolar, alteracao_cemei
    ):
        if not substituicoes_cemei_emei_periodo_escolar:
            return
        substituicoes_cemei_emei_periodo_escolar = [
            dict(item, **{"alteracao_cardapio": alteracao_cemei})
            for item in substituicoes_cemei_emei_periodo_escolar
        ]
        for substituicao in substituicoes_cemei_emei_periodo_escolar:
            tipos_alimentacao_de = substituicao.pop("tipos_alimentacao_de", [])
            tipos_alimentacao_para = substituicao.pop("tipos_alimentacao_para", [])
            subs = SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI.objects.create(
                **substituicao
            )
            subs.tipos_alimentacao_de.set(tipos_alimentacao_de)
            subs.tipos_alimentacao_para.set(tipos_alimentacao_para)

    def criar_datas_intervalo(self, datas_intervalo, instance):
        datas_intervalo = [
            dict(item, **{"alteracao_cardapio_cemei": instance})
            for item in datas_intervalo
        ]
        for data_intervalo in datas_intervalo:
            DataIntervaloAlteracaoCardapioCEMEI.objects.create(**data_intervalo)

    def validate_data(self, data):
        nao_pode_ser_no_passado(data)
        deve_pedir_com_antecedencia(data)
        deve_ser_no_mesmo_ano_corrente(data)
        return data

    def create(self, validated_data):
        valida_duplicidade_solicitacoes_lanche_emergencial(
            validated_data, eh_cemei=True
        )
        motivo = validated_data.get("motivo", None)
        if motivo and motivo.nome == "RPL - Refeição por Lanche":
            valida_duplicidade_solicitacoes_cemei(validated_data)
        substituicoes_cemei_cei_periodo_escolar = validated_data.pop(
            "substituicoes_cemei_cei_periodo_escolar", []
        )
        substituicoes_cemei_emei_periodo_escolar = validated_data.pop(
            "substituicoes_cemei_emei_periodo_escolar", []
        )
        datas_intervalo = validated_data.pop("datas_intervalo", [])
        alteracao_cemei = AlteracaoCardapioCEMEI.objects.create(**validated_data)
        self.criar_substituicoes_cemei_cei(
            substituicoes_cemei_cei_periodo_escolar, alteracao_cemei
        )
        self.criar_substituicoes_cemei_emei(
            substituicoes_cemei_emei_periodo_escolar, alteracao_cemei
        )
        self.criar_datas_intervalo(datas_intervalo, alteracao_cemei)
        return alteracao_cemei

    def update(self, instance, validated_data):
        valida_duplicidade_solicitacoes_lanche_emergencial(
            validated_data, eh_cemei=True
        )
        instance.substituicoes_cemei_cei_periodo_escolar.all().delete()
        instance.substituicoes_cemei_emei_periodo_escolar.all().delete()
        instance.datas_intervalo.all().delete()
        substituicoes_cemei_cei_periodo_escolar = validated_data.pop(
            "substituicoes_cemei_cei_periodo_escolar", []
        )
        substituicoes_cemei_emei_periodo_escolar = validated_data.pop(
            "substituicoes_cemei_emei_periodo_escolar", []
        )
        datas_intervalo = validated_data.pop("datas_intervalo", [])
        self.criar_substituicoes_cemei_cei(
            substituicoes_cemei_cei_periodo_escolar, instance
        )
        self.criar_substituicoes_cemei_emei(
            substituicoes_cemei_emei_periodo_escolar, instance
        )
        self.criar_datas_intervalo(datas_intervalo, instance)
        update_instance_from_dict(instance, validated_data)
        instance.save()
        return instance

    class Meta:
        model = AlteracaoCardapioCEMEI
        exclude = ("id",)
