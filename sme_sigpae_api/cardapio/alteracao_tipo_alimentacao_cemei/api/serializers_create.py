from rest_framework import serializers

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.validators import (
    valida_duplicidade_solicitacoes_lanche_emergencial,
)
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
    """Serializer de escrita para ``FaixaEtariaSubstituicaoAlimentacaoCEMEICEI``.

    Aceita ``faixa_etaria`` por UUID e referencia a
    ``SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI`` de forma opcional.
    """

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
    """Serializer de escrita para ``SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI``.

    Aceita ``alteracao_cardapio``, ``periodo_escolar``,
    ``tipos_alimentacao_de``, ``tipos_alimentacao_para`` e ``faixas_etarias``
    por UUID. O campo ``faixas_etarias`` é aninhado e criado em cascata pelo
    método ``criar_substituicoes_cemei_cei`` do serializer pai.
    """

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
    """Serializer de escrita para ``SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI``.

    Aceita ``alteracao_cardapio``, ``periodo_escolar``,
    ``tipos_alimentacao_de`` e ``tipos_alimentacao_para`` por UUID. Diferente
    do lado CEI, não possui faixas etárias; a quantidade de alunos é
    informada diretamente no campo ``qtd_alunos`` do modelo.
    """

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
    """Serializer de escrita para ``DataIntervaloAlteracaoCardapioCEMEI``.

    Aceita ``alteracao_cardapio_cemei`` por UUID (campo opcional preenchido
    programaticamente no momento da criação) e implementa ``create`` para
    instanciar diretamente o modelo.
    """

    alteracao_cardapio_cemei = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=AlteracaoCardapioCEMEI.objects.all()
    )

    def create(self, validated_data):
        """Cria uma instância de ``DataIntervaloAlteracaoCardapioCEMEI``.

        Args:
            validated_data (dict): Dados validados pelo serializer.

        Returns:
            DataIntervaloAlteracaoCardapioCEMEI: Instância recém-criada.
        """
        data_intervalo = DataIntervaloAlteracaoCardapioCEMEI.objects.create(
            **validated_data
        )
        return data_intervalo

    class Meta:
        model = DataIntervaloAlteracaoCardapioCEMEI
        exclude = ("id",)


class AlteracaoCardapioCEMEISerializerCreate(serializers.ModelSerializer):
    """Serializer de escrita para ``AlteracaoCardapioCEMEI``.

    Utilizado pelo ``AlteracoesCardapioCEMEIViewSet`` nas actions de criação e
    atualização de solicitações. Coordena a persistência aninhada das
    substituições CEI, EMEI e datas de intervalo.
    """

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
        """Cria as faixas etárias CEI associadas a uma substituição.

        Args:
            faixas_etarias (list[dict]): Lista de dados das faixas etárias a
                serem criadas.
            substituicao (SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI):
                Instância já criada à qual as faixas serão vinculadas.

        Returns:
            None
        """
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
        """Cria as substituições de período escolar CEI da solicitação CEMEI.

        Para cada substituição, vincula ``alteracao_cardapio``, define os
        types M2M e cria as faixas etárias aninhadas.

        Args:
            substituicoes_cemei_cei_periodo_escolar (list[dict]): Lista de
                dados de substituições CEI.
            alteracao_cemei (AlteracaoCardapioCEMEI): Solicitação CEMEI à qual
                as substituições serão vinculadas.

        Returns:
            None
        """
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
        """Cria as substituições de período escolar EMEI da solicitação CEMEI.

        Para cada substituição, vincula ``alteracao_cardapio`` e define os
        types M2M. Diferente do lado CEI, não há faixas etárias aninhadas.

        Args:
            substituicoes_cemei_emei_periodo_escolar (list[dict]): Lista de
                dados de substituições EMEI.
            alteracao_cemei (AlteracaoCardapioCEMEI): Solicitação CEMEI à qual
                as substituições serão vinculadas.

        Returns:
            None
        """
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
        """Cria as datas do intervalo vinculadas à solicitação CEMEI.

        Args:
            datas_intervalo (list[dict]): Lista de dados de datas a serem
                criadas.
            instance (AlteracaoCardapioCEMEI): Solicitação CEMEI à qual as
                datas serão vinculadas.

        Returns:
            None
        """
        datas_intervalo = [
            dict(item, **{"alteracao_cardapio_cemei": instance})
            for item in datas_intervalo
        ]
        for data_intervalo in datas_intervalo:
            DataIntervaloAlteracaoCardapioCEMEI.objects.create(**data_intervalo)

    def validate_data(self, data):
        """Valida a data principal da solicitação CEMEI.

        Aplica as seguintes regras de negócio:
        - não pode ser uma data no passado;
        - deve ser solicitada com a antecedência mínima necessária;
        - deve estar dentro do ano corrente.

        Args:
            data (datetime.date): Data a ser validada.

        Returns:
            datetime.date: A mesma data, se válida.

        Raises:
            serializers.ValidationError: Se qualquer regra de validação
                for violada.
        """
        nao_pode_ser_no_passado(data)
        deve_pedir_com_antecedencia(data)
        deve_ser_no_mesmo_ano_corrente(data)
        return data

    def create(self, validated_data):
        """Cria uma ``AlteracaoCardapioCEMEI`` com todas as suas entidades aninhadas.

        Valida duplicidades de lanche emergencial e RPL; extrai e persiste
        separadamente as substituições CEI, EMEI e datas do intervalo.

        Args:
            validated_data (dict): Dados validados pelo serializer.

        Returns:
            AlteracaoCardapioCEMEI: Instância recém-criada.

        Raises:
            rest_framework.exceptions.ValidationError: Se houver duplicidade
                de solicitação de lanche emergencial ou RPL para o mesmo mês.
        """
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
        """Atualiza uma ``AlteracaoCardapioCEMEI`` recriando todas as entidades aninhadas.

        Remove todas as substituições e datas do intervalo existentes antes
        de recrear com os novos dados. Valida duplicidades de lanche
        emergencial.

        Args:
            instance (AlteracaoCardapioCEMEI): Instância a ser atualizada.
            validated_data (dict): Dados validados pelo serializer.

        Returns:
            AlteracaoCardapioCEMEI: Instância atualizada.

        Raises:
            rest_framework.exceptions.ValidationError: Se houver duplicidade
                de solicitação de lanche emergencial.
        """
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
