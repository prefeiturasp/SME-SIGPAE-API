from datetime import date

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from ....dados_comuns.utils import update_instance_from_dict
from ....dados_comuns.validators import (
    campo_nao_pode_ser_nulo,
    deve_pedir_com_antecedencia,
    deve_ser_dia_letivo_e_dia_da_semana,
    deve_ser_no_mesmo_ano_corrente,
    nao_pode_ser_feriado,
    nao_pode_ser_no_passado,
    objeto_nao_deve_ter_duplicidade,
    valida_datas_alteracao_cardapio,
    valida_duplicidade_solicitacoes,
    valida_duplicidade_solicitacoes_cei,
    valida_duplicidade_solicitacoes_cemei,
    valida_duplicidade_solicitacoes_lanche_emergencial_cemei
)
from ....escola.models import (
    DiaCalendario,
    Escola,
    FaixaEtaria,
    PeriodoEscolar,
    TipoUnidadeEscolar,
)
from ....escola.utils import eh_dia_sem_atividade_escolar
from ....terceirizada.models import Edital
from ...api.validators import (
    escola_nao_pode_cadastrar_dois_combos_iguais,
    hora_inicio_nao_pode_ser_maior_que_hora_final,
    nao_pode_existir_solicitacao_igual_para_mesma_escola,
    nao_pode_ter_mais_que_60_dias_diferenca,
    precisa_pertencer_a_um_tipo_de_alimentacao,
    valida_duplicidade_solicitacoes_lanche_emergencial,
)
from ...models import (
    AlteracaoCardapio,
    AlteracaoCardapioCEI,
    AlteracaoCardapioCEMEI,
    Cardapio,
    ComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    DataIntervaloAlteracaoCardapio,
    DataIntervaloAlteracaoCardapioCEMEI,
    FaixaEtariaSubstituicaoAlimentacaoCEI,
    FaixaEtariaSubstituicaoAlimentacaoCEMEICEI,
    GrupoSuspensaoAlimentacao,
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
    InversaoCardapio,
    MotivoAlteracaoCardapio,
    MotivoSuspensao,
    QuantidadePorPeriodoSuspensaoAlimentacao,
    SubstituicaoAlimentacaoNoPeriodoEscolar,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI,
    SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    SuspensaoAlimentacao,
    SuspensaoAlimentacaoDaCEI,
    SuspensaoAlimentacaoNoPeriodoEscolar,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)


class HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializerCreate(
    serializers.ModelSerializer
):
    hora_inicial = serializers.TimeField()
    hora_final = serializers.TimeField()

    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Escola.objects.all()
    )

    tipo_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=TipoAlimentacao.objects.all()
    )

    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=PeriodoEscolar.objects.all()
    )

    def validate(self, attrs):
        hora_inicial = attrs["hora_inicial"]
        hora_final = attrs["hora_final"]
        hora_inicio_nao_pode_ser_maior_que_hora_final(hora_inicial, hora_final)
        return attrs

    def create(self, validated_data):
        escola = validated_data.get("escola")
        tipo_alimentacao = validated_data.get("tipo_alimentacao")
        periodo_escolar = validated_data.get("periodo_escolar")
        escola_nao_pode_cadastrar_dois_combos_iguais(
            escola, tipo_alimentacao, periodo_escolar
        )
        horario_do_combo = (
            HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar.objects.create(
                **validated_data
            )
        )
        return horario_do_combo

    def update(self, instance, validated_data):
        update_instance_from_dict(instance, validated_data)
        instance.save()
        return instance

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

        if data_de.month != 12 and date.today().year + 1 not in [
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


class CardapioCreateSerializer(serializers.ModelSerializer):
    tipos_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid",
        many=True,
        required=True,
        queryset=TipoAlimentacao.objects.all(),
    )
    edital = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Edital.objects.all()
    )

    def validate_data(self, data):
        nao_pode_ser_no_passado(data)
        nao_pode_ser_feriado(data)
        objeto_nao_deve_ter_duplicidade(
            Cardapio,
            mensagem="Já existe um cardápio cadastrado com esta data",
            data=data,
        )
        return data

    class Meta:
        model = Cardapio
        exclude = ("id",)


class SuspensaoAlimentacaoNoPeriodoEscolarCreateSerializer(serializers.ModelSerializer):
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", queryset=PeriodoEscolar.objects.all()
    )
    tipos_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid", many=True, queryset=TipoAlimentacao.objects.all()
    )

    class Meta:
        model = SuspensaoAlimentacaoNoPeriodoEscolar
        exclude = ("id", "suspensao_alimentacao")


class SuspensaoAlimentacaoCreateSerializer(serializers.ModelSerializer):
    motivo = serializers.SlugRelatedField(
        slug_field="uuid", queryset=MotivoSuspensao.objects.all()
    )

    def validate_data(self, data):
        nao_pode_ser_no_passado(data)
        deve_ser_no_mesmo_ano_corrente(data)
        return data

    class Meta:
        model = SuspensaoAlimentacao
        exclude = ("id",)


class SuspensaoAlimentacaodeCEICreateSerializer(serializers.ModelSerializer):
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
        data = attrs["data"]
        nao_pode_ser_no_passado(data)
        deve_pedir_com_antecedencia(data)
        deve_ser_no_mesmo_ano_corrente(data)
        return attrs

    def create(self, validated_data):
        periodos_escolares = validated_data.pop("periodos_escolares", "")
        validated_data["criado_por"] = self.context["request"].user
        suspensao_alimentacao = SuspensaoAlimentacaoDaCEI.objects.create(
            **validated_data
        )
        suspensao_alimentacao.periodos_escolares.set(periodos_escolares)
        suspensao_alimentacao.save()
        return suspensao_alimentacao

    def update(self, instance, validated_data):
        periodos_escolares = validated_data.pop("periodos_escolares", "")
        update_instance_from_dict(instance, validated_data)
        instance.periodos_escolares.set([])
        instance.periodos_escolares.set(periodos_escolares)
        instance.save()
        return instance

    class Meta:
        model = SuspensaoAlimentacaoDaCEI
        exclude = ("id", "status", "criado_por")


class FaixaEtariaSubstituicaoAlimentacaoCEISerializerCreate(
    serializers.ModelSerializer
):
    substituicao_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=SubstituicaoAlimentacaoNoPeriodoEscolarCEI.objects.all(),
    )

    faixa_etaria = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=FaixaEtaria.objects.all()
    )

    class Meta:
        model = FaixaEtariaSubstituicaoAlimentacaoCEI
        exclude = ("id",)


class SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreateBase(
    serializers.ModelSerializer
):
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=PeriodoEscolar.objects.all()
    )

    tipos_alimentacao_de = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        many=True,
        queryset=TipoAlimentacao.objects.all(),
    )


class SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreate(
    SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreateBase
):  # noqa E501
    alteracao_cardapio = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=AlteracaoCardapio.objects.all()
    )
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=PeriodoEscolar.objects.all()
    )

    tipos_alimentacao_para = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        many=True,
        queryset=TipoAlimentacao.objects.all(),
    )

    def create(self, validated_data):
        tipos_alimentacao_de = validated_data.pop("tipos_alimentacao_de")
        tipos_alimentacao_para = validated_data.pop("tipos_alimentacao_para")
        substituicao_alimentacao = (
            SubstituicaoAlimentacaoNoPeriodoEscolar.objects.create(**validated_data)
        )
        substituicao_alimentacao.tipos_alimentacao_de.set(tipos_alimentacao_de)
        substituicao_alimentacao.tipos_alimentacao_para.set(tipos_alimentacao_para)
        return substituicao_alimentacao

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolar
        exclude = ("id",)


class SubstituicoesAlimentacaoNoPeriodoEscolarCEISerializerCreate(
    SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreateBase
):  # noqa E501
    alteracao_cardapio = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=AlteracaoCardapioCEI.objects.all()
    )

    tipo_alimentacao_para = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=TipoAlimentacao.objects.all()
    )

    faixas_etarias = FaixaEtariaSubstituicaoAlimentacaoCEISerializerCreate(many=True)

    def create(self, validated_data):
        faixas_etarias = validated_data.pop("faixas_etarias", "")
        tipos_alimentacao_de = validated_data.pop("tipos_alimentacao_de")
        substituicao_alimentacao = (
            SubstituicaoAlimentacaoNoPeriodoEscolarCEI.objects.create(**validated_data)
        )
        substituicao_alimentacao.tipos_alimentacao_de.set(tipos_alimentacao_de)
        substituicao_alimentacao.save()
        for faixa_etaria_dados in faixas_etarias:
            FaixaEtariaSubstituicaoAlimentacaoCEI.objects.create(
                substituicao_alimentacao=substituicao_alimentacao, **faixa_etaria_dados
            )
        return substituicao_alimentacao

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolarCEI
        exclude = ("id",)


class AlteracaoCardapioSerializerCreateBase(serializers.ModelSerializer):
    motivo = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=MotivoAlteracaoCardapio.objects.all()
    )
    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Escola.objects.all()
    )
    status_explicacao = serializers.CharField(
        source="status", required=False, read_only=True
    )

    def create(self, validated_data):
        substituicoes = validated_data.pop("substituicoes")
        validated_data["criado_por"] = self.context["request"].user

        substituicoes_lista = []
        for substituicao in substituicoes:
            substituicoes_object = self.Meta.serializer_substituicao().create(
                substituicao
            )
            substituicoes_lista.append(substituicoes_object)
        alteracao_cardapio = self.Meta.model.objects.create(**validated_data)
        alteracao_cardapio.substituicoes.set(substituicoes_lista)

        return alteracao_cardapio

    def update(self, instance, validated_data):
        substituicoes_json = validated_data.pop("substituicoes")
        instance.substituicoes.all().delete()

        substituicoes_lista = []
        for substituicao_json in substituicoes_json:
            substituicoes_object = self.Meta.serializer_substituicao().create(
                substituicao_json
            )
            substituicoes_lista.append(substituicoes_object)

        update_instance_from_dict(instance, validated_data)
        instance.substituicoes.set(substituicoes_lista)
        instance.save()

        return instance


class DatasIntervaloAlteracaoCardapioSerializerCreateSerializer(
    serializers.ModelSerializer
):
    alteracao_cardapio = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=AlteracaoCardapio.objects.all()
    )

    def create(self, validated_data):
        data_intervalo = DataIntervaloAlteracaoCardapio.objects.create(**validated_data)
        return data_intervalo

    class Meta:
        model = DataIntervaloAlteracaoCardapio
        exclude = ("id",)


class AlteracaoCardapioSerializerCreate(AlteracaoCardapioSerializerCreateBase):
    substituicoes = SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreate(many=True)
    datas_intervalo = DatasIntervaloAlteracaoCardapioSerializerCreateSerializer(
        required=False, many=True
    )

    def validate(self, attrs):
        escola = attrs.get("escola")
        substituicoes = attrs.get("substituicoes")
        for substicuicao in substituicoes:
            tipos_alimentacao_de = substicuicao.get("tipos_alimentacao_de")
            tipo_alimentacao_para = substicuicao.get("tipo_alimentacao_para")
            periodo_escolar = substicuicao.get("periodo_escolar")
            precisa_pertencer_a_um_tipo_de_alimentacao(
                tipos_alimentacao_de,
                tipo_alimentacao_para,
                escola.tipo_unidade,
                periodo_escolar,
            )
        valida_datas_alteracao_cardapio(attrs)
        nao_pode_ser_no_passado(attrs["data_inicial"])
        if attrs["motivo"].nome != "Lanche Emergencial":
            deve_pedir_com_antecedencia(attrs["data_inicial"])
        if attrs["motivo"].nome == "RPL - Refeição por Lanche":
            valida_duplicidade_solicitacoes(attrs)
        deve_ser_no_mesmo_ano_corrente(attrs["data_inicial"])

        return attrs

    def datas_nos_meses_de_ferias(self, datas_intervalo):
        MESES_DE_FERIAS = [1, 7, 12]
        return (
            datas_intervalo[0]["data"].month in MESES_DE_FERIAS
            or datas_intervalo[-1]["data"].month in MESES_DE_FERIAS
        )

    def criar_datas_intervalo(self, datas_intervalo, instance):
        datas_intervalo = [
            dict(item, **{"alteracao_cardapio": instance}) for item in datas_intervalo
        ]
        if not instance.eh_alteracao_lanche_emergencial():
            for data_intervalo in datas_intervalo:
                DataIntervaloAlteracaoCardapio.objects.create(**data_intervalo)
        else:
            if not DiaCalendario.pelo_menos_um_dia_letivo(
                instance.escola,
                [data_intervalo["data"] for data_intervalo in datas_intervalo],
                instance,
            ) and not self.datas_nos_meses_de_ferias(datas_intervalo):
                raise ValidationError(
                    "Não é possível solicitar Lanche Emergencial para dia(s) não letivo(s)"
                )
            for data_intervalo in datas_intervalo:
                if eh_dia_sem_atividade_escolar(
                    instance.escola, data_intervalo["data"], instance
                ) and not self.datas_nos_meses_de_ferias(datas_intervalo):
                    continue
                DataIntervaloAlteracaoCardapio.objects.create(**data_intervalo)

    def criar_substituicoes(self, substituicoes, instance):
        substituicoes = [
            dict(item, **{"alteracao_cardapio": instance}) for item in substituicoes
        ]
        for substituicao in substituicoes:
            tipos_alimentacao_de = substituicao.pop("tipos_alimentacao_de")
            tipos_alimentacao_para = substituicao.pop("tipos_alimentacao_para")
            substituicao_alimentacao = (
                SubstituicaoAlimentacaoNoPeriodoEscolar.objects.create(**substituicao)
            )
            substituicao_alimentacao.tipos_alimentacao_de.set(tipos_alimentacao_de)
            substituicao_alimentacao.tipos_alimentacao_para.set(tipos_alimentacao_para)

    def create(self, validated_data):
        valida_duplicidade_solicitacoes_lanche_emergencial(validated_data)
        validated_data["criado_por"] = self.context["request"].user
        substituicoes = validated_data.pop("substituicoes")
        datas_intervalo = validated_data.pop("datas_intervalo", [])
        alteracao_cardapio = AlteracaoCardapio.objects.create(**validated_data)

        self.criar_substituicoes(substituicoes, alteracao_cardapio)
        self.criar_datas_intervalo(datas_intervalo, alteracao_cardapio)

        return alteracao_cardapio

    def update(self, instance, validated_data):
        instance.substituicoes.all().delete()
        instance.datas_intervalo.all().delete()

        validated_data["criado_por"] = self.context["request"].user
        substituicoes = validated_data.pop("substituicoes")
        datas_intervalo = validated_data.pop("datas_intervalo", [])
        update_instance_from_dict(instance, validated_data)
        instance.save()

        self.criar_substituicoes(substituicoes, instance)
        self.criar_datas_intervalo(datas_intervalo, instance)

        return instance

    class Meta:
        model = AlteracaoCardapio
        serializer_substituicao = (
            SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreate
        )
        exclude = ("id", "status")


class AlteracaoCardapioCEISerializerCreate(AlteracaoCardapioSerializerCreateBase):
    substituicoes = SubstituicoesAlimentacaoNoPeriodoEscolarCEISerializerCreate(
        many=True
    )

    def validate_data(self, data):
        nao_pode_ser_no_passado(data)
        deve_pedir_com_antecedencia(data)
        deve_ser_no_mesmo_ano_corrente(data)
        attrs = self.context["request"].data
        motivo = MotivoAlteracaoCardapio.objects.filter(uuid=attrs["motivo"]).first()
        if motivo and motivo.nome == "RPL - Refeição por Lanche":
            valida_duplicidade_solicitacoes_cei(attrs, data)
        return data

    class Meta:
        model = AlteracaoCardapioCEI
        serializer_substituicao = (
            SubstituicoesAlimentacaoNoPeriodoEscolarCEISerializerCreate
        )
        exclude = ("id", "status")


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
        valida_duplicidade_solicitacoes_lanche_emergencial_cemei(validated_data)
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


class QuantidadePorPeriodoSuspensaoAlimentacaoCreateSerializer(
    serializers.ModelSerializer
):
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
    escola = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Escola.objects.all()
    )
    quantidades_por_periodo = QuantidadePorPeriodoSuspensaoAlimentacaoCreateSerializer(
        many=True
    )
    suspensoes_alimentacao = SuspensaoAlimentacaoCreateSerializer(many=True)

    def create(self, validated_data):
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


class VinculoTipoAlimentoCreateSerializer(serializers.ModelSerializer):
    tipo_unidade_escolar = serializers.SlugRelatedField(
        slug_field="uuid", queryset=TipoUnidadeEscolar.objects.all()
    )
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", queryset=PeriodoEscolar.objects.all()
    )

    tipos_alimentacao = serializers.SlugRelatedField(
        many=True, slug_field="uuid", queryset=TipoAlimentacao.objects.all()
    )

    def update(self, instance, validated_data):
        tipos_alimentacao = validated_data.pop("tipos_alimentacao")
        update_instance_from_dict(instance, validated_data)
        instance.tipos_alimentacao.set(tipos_alimentacao)
        instance.save()
        return instance

    def validate_tipos_alimentacao(self, tipos_alimentacao):
        campo_nao_pode_ser_nulo(tipos_alimentacao)
        return tipos_alimentacao

    class Meta:
        model = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar
        fields = (
            "uuid",
            "tipos_alimentacao",
            "tipo_unidade_escolar",
            "periodo_escolar",
        )


class ComboDoVinculoTipoAlimentoSimplesSerializerCreate(serializers.ModelSerializer):
    tipos_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        many=True,
        queryset=TipoAlimentacao.objects.all(),
    )

    vinculo = serializers.SlugRelatedField(
        required=False,
        slug_field="uuid",
        queryset=VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.all(),
    )

    def validate_tipos_alimentacao(self, tipos_alimentacao):
        campo_nao_pode_ser_nulo(
            tipos_alimentacao,
            mensagem="tipos_alimentacao deve ter ao menos um elemento",
        )
        return tipos_alimentacao

    class Meta:
        model = ComboDoVinculoTipoAlimentacaoPeriodoTipoUE
        fields = ("uuid", "tipos_alimentacao", "vinculo")


class SubstituicaoDoComboVinculoTipoAlimentoSimplesSerializerCreate(
    serializers.ModelSerializer
):
    tipos_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        many=True,
        queryset=TipoAlimentacao.objects.all(),
    )

    combo = serializers.SlugRelatedField(
        required=False,
        slug_field="uuid",
        queryset=ComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.all(),
    )

    def validate_tipos_alimentacao(self, tipos_alimentacao):
        campo_nao_pode_ser_nulo(
            tipos_alimentacao,
            mensagem="tipos_alimentacao deve ter ao menos um elemento",
        )
        return tipos_alimentacao

    class Meta:
        model = SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE
        fields = ("uuid", "tipos_alimentacao", "combo")
