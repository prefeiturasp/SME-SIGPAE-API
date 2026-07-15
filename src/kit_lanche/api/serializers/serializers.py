import datetime

from rest_framework import serializers

from ....dados_comuns.api.serializers import LogSolicitacoesUsuarioSerializer
from ....dados_comuns.utils import update_instance_from_dict
from ....escola.api.serializers import (
    AlunoSerializer,
    AlunoSimplesSerializer,
    DiretoriaRegionalSimplissimaSerializer,
    EscolaSimplesSerializer,
    EscolaSimplissimaSerializer,
    FaixaEtariaSerializer,
    TipoUnidadeEscolarSimplesSerializer,
)
from ....escola.models import Escola, FaixaEtaria, TipoUnidadeEscolar
from ....perfil.api.serializers import UsuarioSerializer
from ....terceirizada.api.serializers.serializers import (
    EditalSerializer,
    TerceirizadaSimplesSerializer,
)
from ....terceirizada.models import Edital
from ...models import (
    EscolaQuantidade,
    FaixaEtariaSolicitacaoKitLancheCEIAvulsa,
    FaixasQuantidadesKitLancheCEIdaCEMEI,
    ItemKitLanche,
    KitLanche,
    SolicitacaoKitLanche,
    SolicitacaoKitLancheAvulsa,
    SolicitacaoKitLancheCEIAvulsa,
    SolicitacaoKitLancheCEIdaCEMEI,
    SolicitacaoKitLancheCEMEI,
    SolicitacaoKitLancheEMEIdaCEMEI,
    SolicitacaoKitLancheUnificada,
)


class ItemKitLancheSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemKitLanche
        exclude = ("id",)


class KitLancheSerializer(serializers.ModelSerializer):
    edital = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Edital.objects.all()
    )
    tipos_unidades = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=TipoUnidadeEscolar.objects.all(),
        many=True,
        allow_empty=False,
    )

    class Meta:
        model = KitLanche
        exclude = ("id",)

    def validate_nome_kit_lanche_create(self, validated_data):
        if KitLanche.objects.filter(
            nome=validated_data["nome"].upper(),
            edital__uuid=validated_data["edital"].uuid,
            tipos_unidades__in=validated_data["tipos_unidades"],
        ).exists():
            raise serializers.ValidationError(
                "Esse nome de kit lanche já existe para o edital e tipos de unidades selecionados"
            )
        validated_data["nome"] = validated_data["nome"].upper()
        return validated_data

    def validate_nome_kit_lanche_update(self, validated_data, instance):
        if (
            KitLanche.objects.filter(
                nome=validated_data["nome"].upper(),
                edital__uuid=validated_data["edital"].uuid,
                tipos_unidades__in=validated_data["tipos_unidades"],
            )
            .exclude(uuid=str(instance.uuid))
            .exists()
        ):
            serializers.ValidationError(
                "Esse nome de kit lanche já existe para o edital e tipos de unidades selecionados"
            )
        validated_data["nome"] = validated_data["nome"].upper()
        return validated_data

    def create(self, validated_data):
        self.validate_nome_kit_lanche_create(validated_data)
        tipos_unidades = validated_data.pop("tipos_unidades")
        kit_lanche = KitLanche.objects.create(**validated_data)
        kit_lanche.tipos_unidades.set(tipos_unidades)
        return kit_lanche

    def update(self, instance, validated_data):
        self.validate_nome_kit_lanche_update(validated_data, instance)
        tipos_unidades = validated_data.pop("tipos_unidades")
        update_instance_from_dict(instance, validated_data)
        instance.tipos_unidades.set(tipos_unidades)
        instance.save()
        return instance


class KitLancheSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = KitLanche
        exclude = ("id",)


class KitLancheConsultaSerializer(serializers.ModelSerializer):
    edital = EditalSerializer()
    tipos_unidades = TipoUnidadeEscolarSimplesSerializer(many=True)
    status = serializers.CharField(source="get_status_display")

    class Meta:
        model = KitLanche
        exclude = ("id",)


class SolicitacaoKitLancheSimplesSerializer(serializers.ModelSerializer):
    kits = KitLancheSimplesSerializer(many=True, required=False)
    tempo_passeio_explicacao = serializers.CharField(
        source="get_tempo_passeio_display", required=False, read_only=True
    )

    class Meta:
        model = SolicitacaoKitLanche
        exclude = ("id",)


class SolicitacaoKitLancheAvulsaSimilarSerializer(serializers.ModelSerializer):
    solicitacao_kit_lanche = SolicitacaoKitLancheSimplesSerializer()
    id_externo = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    data = serializers.DateField()

    class Meta:
        model = SolicitacaoKitLancheAvulsa
        exclude = ("id",)


class SolicitacaoKitLancheAvulsaSerializer(serializers.ModelSerializer):
    solicitacao_kit_lanche = SolicitacaoKitLancheSimplesSerializer()
    escola = EscolaSimplesSerializer(read_only=True, required=False)
    prioridade = serializers.CharField()
    id_externo = serializers.CharField()
    alunos_com_dieta_especial_participantes = AlunoSerializer(many=True)
    foi_solicitado_fora_do_prazo = serializers.BooleanField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    quantidade_alimentacoes = serializers.IntegerField()
    data = serializers.DateField()
    rastro_terceirizada = TerceirizadaSimplesSerializer()
    solicitacoes_similares = SolicitacaoKitLancheAvulsaSimilarSerializer(many=True)

    class Meta:
        model = SolicitacaoKitLancheAvulsa
        exclude = ("id",)


class SolicitacaoKitLancheAvulsaSimplesSerializer(serializers.ModelSerializer):
    prioridade = serializers.CharField()
    id_externo = serializers.CharField()

    class Meta:
        model = SolicitacaoKitLancheAvulsa
        exclude = ("id", "solicitacao_kit_lanche", "escola", "criado_por")


class EscolaQuantidadeSerializerSimples(serializers.ModelSerializer):
    kits = KitLancheSimplesSerializer(many=True, required=False)
    escola = EscolaSimplesSerializer()
    solicitacao_unificada = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=SolicitacaoKitLancheUnificada.objects.all(),
    )
    tempo_passeio_explicacao = serializers.CharField(
        source="get_tempo_passeio_display", required=False, read_only=True
    )
    cancelado_por = UsuarioSerializer()
    cancelado_em = serializers.SerializerMethodField()
    cancelado_em_com_hora = serializers.SerializerMethodField()

    def get_cancelado_em(self, obj):
        if obj.cancelado:
            if obj.cancelado_em and obj.cancelado_em.date() == datetime.date.today():
                return obj.cancelado_em.strftime("%d/%m/%Y %H:%M:%S")
            return obj.cancelado_em.strftime("%d/%m/%Y")
        return None

    def get_cancelado_em_com_hora(self, obj):
        if obj.cancelado:
            return obj.cancelado_em.strftime("%d/%m/%Y %H:%M:%S")
        return None

    class Meta:
        model = EscolaQuantidade
        exclude = ("id",)


class EscolaQuantidadeSerializerRelatorioSolicitacoesAlimentacaoSimples(
    EscolaQuantidadeSerializerSimples
):
    escola = EscolaSimplissimaSerializer()


class SolicitacaoKitLancheUnificadaSimilarSerializer(serializers.ModelSerializer):
    solicitacao_kit_lanche = SolicitacaoKitLancheSimplesSerializer()
    escolas_quantidades = EscolaQuantidadeSerializerSimples(many=True)
    id_externo = serializers.CharField()
    # TODO: remover total_kit_lanche ou quantidade_alimentacoes. estao duplicados
    total_kit_lanche = serializers.IntegerField()
    lote_nome = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    data = serializers.DateField()
    quantidade_alimentacoes = serializers.IntegerField()

    class Meta:
        model = SolicitacaoKitLancheUnificada
        exclude = ("id",)


class SolicitacaoKitLancheUnificadaSerializer(serializers.ModelSerializer):
    diretoria_regional = DiretoriaRegionalSimplissimaSerializer()
    solicitacao_kit_lanche = SolicitacaoKitLancheSimplesSerializer()
    escolas_quantidades = EscolaQuantidadeSerializerSimples(many=True)
    id_externo = serializers.CharField()
    # TODO: remover total_kit_lanche ou quantidade_alimentacoes. estao duplicados
    total_kit_lanche = serializers.IntegerField()
    lote_nome = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    prioridade = serializers.CharField()
    data = serializers.DateField()
    quantidade_alimentacoes = serializers.IntegerField()
    rastro_terceirizada = TerceirizadaSimplesSerializer()
    solicitacoes_similares = SolicitacaoKitLancheUnificadaSimilarSerializer(many=True)
    tipo = serializers.SerializerMethodField()

    def get_tipo(self, obj):
        return obj.tipo

    class Meta:
        model = SolicitacaoKitLancheUnificada
        exclude = ("id",)


class SolicitacaoKitLancheUnificadaRelatorioSolicitacoesAlimentacaoSerializer(
    SolicitacaoKitLancheUnificadaSerializer
):
    escolas_quantidades = serializers.SerializerMethodField()
    total_kit_lanche = serializers.SerializerMethodField()
    solicitacoes_similares = None

    def get_escolas_quantidades(self, obj):
        instituicao = self.context["request"].user.vinculo_atual.instituicao
        escolas_quantidades = obj.escolas_quantidades.all()
        if isinstance(instituicao, Escola):
            escolas_quantidades = escolas_quantidades.filter(escola=instituicao)
        return EscolaQuantidadeSerializerRelatorioSolicitacoesAlimentacaoSimples(
            escolas_quantidades, context=self.context, many=True
        ).data

    def get_total_kit_lanche(self, obj):
        instituicao = self.context["request"].user.vinculo_atual.instituicao
        if isinstance(instituicao, Escola):
            return obj.total_kit_lanche_escola(instituicao.uuid)
        return obj.total_kit_lanche


class SolicitacaoKitLancheUnificadaSimplesSerializer(serializers.ModelSerializer):
    prioridade = serializers.CharField()

    class Meta:
        model = SolicitacaoKitLancheUnificada
        exclude = ("id",)


class EscolaQuantidadeSerializer(serializers.ModelSerializer):
    kits = KitLancheSimplesSerializer(many=True, required=False)
    escola = EscolaSimplesSerializer()

    class Meta:
        model = EscolaQuantidade
        exclude = ("id",)


class FaixaEtariaSolicitacaoKitLancheCEIAvulsaSerializer(serializers.ModelSerializer):
    faixa_etaria = FaixaEtariaSerializer()

    class Meta:
        model = FaixaEtariaSolicitacaoKitLancheCEIAvulsa
        exclude = ("id", "solicitacao_kit_lanche_avulsa")


class SolicitacaoKitLancheCEISimilarSerializer(serializers.ModelSerializer):
    solicitacao_kit_lanche = SolicitacaoKitLancheSimplesSerializer()
    faixas_etarias = FaixaEtariaSolicitacaoKitLancheCEIAvulsaSerializer(many=True)
    quantidade_alunos = serializers.IntegerField()
    id_externo = serializers.CharField()
    alunos_com_dieta_especial_participantes = AlunoSerializer(many=True)
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    escola = EscolaSimplesSerializer()

    def to_representation(self, instance):
        retorno = super().to_representation(instance)

        # Inclui o total de alunos nas faixas etárias
        faixas_etarias_da_solicitacao = FaixaEtaria.objects.filter(
            uuid__in=[f.faixa_etaria.uuid for f in instance.faixas_etarias.all()]
        )

        qtde_alunos = instance.escola.alunos_por_faixa_etaria(
            instance.data, faixas_etarias_da_solicitacao
        )
        for faixa_etaria in retorno["faixas_etarias"]:
            uuid_faixa_etaria = faixa_etaria["faixa_etaria"]["uuid"]
            faixa_etaria["total_alunos_no_periodo"] = qtde_alunos[uuid_faixa_etaria]

        return retorno

    class Meta:
        model = SolicitacaoKitLancheCEIAvulsa
        exclude = ("id", "criado_por")


class SolicitacaoKitLancheCEIAvulsaSerializer(serializers.ModelSerializer):
    solicitacao_kit_lanche = SolicitacaoKitLancheSimplesSerializer()
    faixas_etarias = FaixaEtariaSolicitacaoKitLancheCEIAvulsaSerializer(many=True)
    quantidade_alunos = serializers.IntegerField()
    id_externo = serializers.CharField()
    alunos_com_dieta_especial_participantes = AlunoSerializer(many=True)
    prioridade = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    escola = EscolaSimplesSerializer()
    rastro_terceirizada = TerceirizadaSimplesSerializer()
    solicitacoes_similares = SolicitacaoKitLancheCEISimilarSerializer(many=True)

    def to_representation(self, instance):
        retorno = super().to_representation(instance)

        # Inclui o total de alunos nas faixas etárias
        faixas_etarias_da_solicitacao = FaixaEtaria.objects.filter(
            uuid__in=[f.faixa_etaria.uuid for f in instance.faixas_etarias.all()]
        )

        qtde_alunos = instance.escola.alunos_por_faixa_etaria(
            instance.data, faixas_etarias_da_solicitacao
        )
        for faixa_etaria in retorno["faixas_etarias"]:
            uuid_faixa_etaria = faixa_etaria["faixa_etaria"]["uuid"]
            faixa_etaria["total_alunos_no_periodo"] = qtde_alunos[uuid_faixa_etaria]

        return retorno

    class Meta:
        model = SolicitacaoKitLancheCEIAvulsa
        exclude = ("id", "criado_por")


class FaixasQuantidadesKitLancheCEIdaCEMEISerializer(serializers.ModelSerializer):
    faixa_etaria = FaixaEtariaSerializer()

    class Meta:
        model = FaixasQuantidadesKitLancheCEIdaCEMEI
        exclude = ("id",)


class SolicitacaoKitLancheCEIdaCEMEISerializer(serializers.ModelSerializer):
    kits = serializers.SlugRelatedField(many=True, read_only=True, slug_field="uuid")
    alunos_com_dieta_especial_participantes = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="uuid"
    )
    faixas_quantidades = FaixasQuantidadesKitLancheCEIdaCEMEISerializer(many=True)
    tempo_passeio = serializers.CharField()

    class Meta:
        model = SolicitacaoKitLancheCEIdaCEMEI
        exclude = ("id",)


class SolicitacaoKitLancheEMEIdaCEMEISerializer(serializers.ModelSerializer):
    kits = serializers.SlugRelatedField(many=True, read_only=True, slug_field="uuid")
    alunos_com_dieta_especial_participantes = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="uuid"
    )
    tempo_passeio = serializers.CharField()

    class Meta:
        model = SolicitacaoKitLancheEMEIdaCEMEI
        exclude = ("id",)


class SolicitacaoKitLancheCEMEISerializer(serializers.ModelSerializer):
    solicitacao_cei = SolicitacaoKitLancheCEIdaCEMEISerializer()
    solicitacao_emei = SolicitacaoKitLancheEMEIdaCEMEISerializer()
    id_externo = serializers.CharField()
    escola = serializers.UUIDField(source="escola.uuid")

    class Meta:
        model = SolicitacaoKitLancheCEMEI
        exclude = ("id",)


class KitLancheNomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = KitLanche
        fields = ("nome",)


class SolicitacaoKitLancheEMEIdaCEMEIRetrieveSerializer(serializers.ModelSerializer):
    alunos_com_dieta_especial_participantes = AlunoSimplesSerializer(many=True)
    kits = KitLancheNomeSerializer(many=True)
    tempo_passeio = serializers.CharField()
    tempo_passeio_explicacao = serializers.CharField(
        source="get_tempo_passeio_display", required=False, read_only=True
    )

    class Meta:
        model = SolicitacaoKitLancheEMEIdaCEMEI
        exclude = ("id",)


class SolicitacaoKitLancheCEIdaCEMEIRetrieveSerializer(serializers.ModelSerializer):
    alunos_com_dieta_especial_participantes = AlunoSimplesSerializer(many=True)
    kits = KitLancheNomeSerializer(many=True)
    faixas_quantidades = FaixasQuantidadesKitLancheCEIdaCEMEISerializer(many=True)
    tempo_passeio = serializers.CharField()
    tempo_passeio_explicacao = serializers.CharField(
        source="get_tempo_passeio_display", required=False, read_only=True
    )

    class Meta:
        model = SolicitacaoKitLancheCEIdaCEMEI
        exclude = ("id",)


class SolicitacaoKitLancheCEMEISimilarSerializer(serializers.ModelSerializer):
    solicitacao_cei = SolicitacaoKitLancheCEIdaCEMEIRetrieveSerializer()
    solicitacao_emei = SolicitacaoKitLancheEMEIdaCEMEIRetrieveSerializer()
    id_externo = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    data = serializers.DateField()

    class Meta:
        model = SolicitacaoKitLancheCEMEI
        exclude = ("id",)


class SolicitacaoKitLancheCEMEIRetrieveSerializer(serializers.ModelSerializer):
    solicitacao_cei = SolicitacaoKitLancheCEIdaCEMEIRetrieveSerializer()
    solicitacao_emei = SolicitacaoKitLancheEMEIdaCEMEIRetrieveSerializer()
    solicitacoes_similares = SolicitacaoKitLancheCEMEISimilarSerializer(many=True)
    id_externo = serializers.CharField()
    escola = EscolaSimplesSerializer()
    rastro_terceirizada = TerceirizadaSimplesSerializer()
    prioridade = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    data = serializers.DateField()

    class Meta:
        model = SolicitacaoKitLancheCEMEI
        exclude = ("id",)
