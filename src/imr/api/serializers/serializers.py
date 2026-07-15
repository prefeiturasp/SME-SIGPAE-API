import environ
from rest_framework import serializers

from src.escola.api.serializers import EscolaFormIMRSelializer
from src.imr.models import (
    AnexosFormularioBase,
    CategoriaOcorrencia,
    Equipamento,
    FormularioOcorrenciasBase,
    FormularioSupervisao,
    Insumo,
    Mobiliario,
    NotificacoesAssinadasFormularioBase,
    OcorrenciaNaoSeAplica,
    ParametrizacaoOcorrencia,
    PeriodoVisita,
    ReparoEAdaptacao,
    RespostaCampoNumerico,
    RespostaCampoTextoLongo,
    RespostaCampoTextoSimples,
    RespostaDatas,
    RespostaEquipamento,
    RespostaInsumo,
    RespostaMobiliario,
    RespostaReparoEAdaptacao,
    RespostaSimNao,
    RespostaTipoAlimentacao,
    RespostaUtensilioCozinha,
    RespostaUtensilioMesa,
    TipoAlimentacao,
    TipoOcorrencia,
    TipoPenalidade,
    TipoPerguntaParametrizacaoOcorrencia,
    UtensilioCozinha,
    UtensilioMesa,
)


class PeriodoVisitaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoVisita
        exclude = ("id",)


class FormularioSupervisaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormularioSupervisao
        exclude = ("id",)


class AnexosFormularioBaseSerializer(serializers.ModelSerializer):
    nome = serializers.CharField()
    anexo_url = serializers.SerializerMethodField()

    def get_anexo_url(self, instance):
        env = environ.Env()
        api_url = env.str("URL_ANEXO", default="http://localhost:8000")
        return f"{api_url}{instance.anexo.url}"

    class Meta:
        model = AnexosFormularioBase
        exclude = ("id",)


class NotificacoesAssinadasFormularioBaseSerializer(serializers.ModelSerializer):
    nome = serializers.CharField()
    anexo_url = serializers.SerializerMethodField()

    def get_anexo_url(self, instance):
        env = environ.Env()
        api_url = env.str("URL_ANEXO", default="http://localhost:8000")
        return f"{api_url}{instance.notificacao_assinada.url}"

    class Meta:
        model = NotificacoesAssinadasFormularioBase
        exclude = ("id",)


class FormularioSupervisaoRetrieveSerializer(serializers.ModelSerializer):
    diretoria_regional = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()
    escola = EscolaFormIMRSelializer()
    periodo_visita = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        allow_null=True,
        queryset=PeriodoVisita.objects.all(),
    )
    formulario_base = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        allow_null=True,
        queryset=FormularioOcorrenciasBase.objects.all(),
    )

    anexos = serializers.SerializerMethodField()
    notificacoes_assinadas = serializers.SerializerMethodField()

    def get_anexos(self, obj):
        return AnexosFormularioBaseSerializer(
            obj.formulario_base.anexos.all(), many=True
        ).data

    def get_notificacoes_assinadas(self, obj):
        return NotificacoesAssinadasFormularioBaseSerializer(
            obj.formulario_base.notificacoes_assinadas.all(), many=True
        ).data

    class Meta:
        model = FormularioSupervisao
        exclude = ("id",)

    @staticmethod
    def get_serializer_class_by_name(name):
        serializer_class = globals().get(name)
        if serializer_class is None:
            raise ValueError(f"Nenhum serializer encontrado com o nome '{name}'")
        return serializer_class

    def get_diretoria_regional(self, obj):
        return obj.escola.diretoria_regional.uuid

    def get_data(self, obj):
        return obj.formulario_base.data.strftime("%d/%m/%Y")


class FormularioSupervisaoSimplesSerializer(serializers.ModelSerializer):
    diretoria_regional = serializers.CharField(source="escola.diretoria_regional.nome")
    unidade_educacional = serializers.CharField(source="escola.nome")
    data = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")

    def get_data(self, obj):
        return obj.formulario_base.data.strftime("%d/%m/%Y")

    class Meta:
        model = FormularioSupervisao
        fields = (
            "uuid",
            "diretoria_regional",
            "unidade_educacional",
            "data",
            "status",
        )


class CategoriaOcorrenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaOcorrencia
        fields = (
            "uuid",
            "nome",
            "posicao",
            "gera_notificacao",
        )


class TipoPerguntaParametrizacaoOcorrenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoPerguntaParametrizacaoOcorrencia
        fields = (
            "uuid",
            "nome",
        )


class ParametrizacaoOcorrenciaSerializer(serializers.ModelSerializer):
    tipo_pergunta = TipoPerguntaParametrizacaoOcorrenciaSerializer()
    tipo_ocorrencia = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        allow_null=True,
        queryset=TipoOcorrencia.objects.all(),
    )

    class Meta:
        model = ParametrizacaoOcorrencia
        fields = ("uuid", "posicao", "titulo", "tipo_pergunta", "tipo_ocorrencia")


class TipoPenalidadeSerializer(serializers.ModelSerializer):
    obrigacoes = serializers.SerializerMethodField()

    class Meta:
        model = TipoPenalidade
        fields = (
            "uuid",
            "numero_clausula",
            "descricao",
            "obrigacoes",
        )

    def get_obrigacoes(self, obj):
        obrigacoes = obj.obrigacoes.all()
        return [obrigacao.descricao for obrigacao in obrigacoes]


class TipoOcorrenciaSerializer(serializers.ModelSerializer):
    categoria = CategoriaOcorrenciaSerializer()
    parametrizacoes = ParametrizacaoOcorrenciaSerializer(many=True)
    penalidade = TipoPenalidadeSerializer()

    class Meta:
        model = TipoOcorrencia
        fields = (
            "uuid",
            "titulo",
            "descricao",
            "posicao",
            "categoria",
            "parametrizacoes",
            "penalidade",
            "aceita_multiplas_respostas",
        )


class UtensilioCozinhaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UtensilioCozinha
        exclude = ("id",)


class UtensilioMesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UtensilioMesa
        exclude = ("id",)


class EquipamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipamento
        exclude = ("id",)


class MobiliarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mobiliario
        exclude = ("id",)


class ReparoEAdaptacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReparoEAdaptacao
        exclude = ("id",)


class InsumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insumo
        exclude = ("id",)


class RespostaDatasSerializer(serializers.ModelSerializer):
    parametrizacao = ParametrizacaoOcorrenciaSerializer()

    class Meta:
        model = RespostaDatas
        exclude = ("id",)


class RespostaCampoTextoLongoSerializer(serializers.ModelSerializer):
    parametrizacao = ParametrizacaoOcorrenciaSerializer()

    class Meta:
        model = RespostaCampoTextoLongo
        exclude = ("id",)


class RespostaCampoTextoSimplesSerializer(serializers.ModelSerializer):
    parametrizacao = ParametrizacaoOcorrenciaSerializer()

    class Meta:
        model = RespostaCampoTextoSimples
        exclude = ("id",)


class RespostaCampoNumericoSerializer(serializers.ModelSerializer):
    parametrizacao = ParametrizacaoOcorrenciaSerializer()

    class Meta:
        model = RespostaCampoNumerico
        exclude = ("id",)


class RespostaSimNaoSerializer(serializers.ModelSerializer):
    parametrizacao = ParametrizacaoOcorrenciaSerializer()

    class Meta:
        model = RespostaSimNao
        exclude = ("id",)


class RespostaTipoAlimentacaoSerializer(serializers.ModelSerializer):
    parametrizacao = ParametrizacaoOcorrenciaSerializer()
    resposta = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        allow_null=True,
        queryset=TipoAlimentacao.objects.all(),
    )

    class Meta:
        model = RespostaTipoAlimentacao
        exclude = ("id",)


class RespostaEquipamentoSerializer(serializers.ModelSerializer):
    parametrizacao = ParametrizacaoOcorrenciaSerializer()
    resposta = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        allow_null=True,
        queryset=Equipamento.objects.all(),
    )

    class Meta:
        model = RespostaEquipamento
        exclude = ("id",)


class RespostaInsumoSerializer(serializers.ModelSerializer):
    parametrizacao = ParametrizacaoOcorrenciaSerializer()
    resposta = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        allow_null=True,
        queryset=Insumo.objects.all(),
    )

    class Meta:
        model = RespostaInsumo
        exclude = ("id",)


class RespostaMobiliarioSerializer(serializers.ModelSerializer):
    parametrizacao = ParametrizacaoOcorrenciaSerializer()
    resposta = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        allow_null=True,
        queryset=Mobiliario.objects.all(),
    )

    class Meta:
        model = RespostaMobiliario
        exclude = ("id",)


class RespostaReparoEAdaptacaoSerializer(serializers.ModelSerializer):
    parametrizacao = ParametrizacaoOcorrenciaSerializer()
    resposta = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        allow_null=True,
        queryset=ReparoEAdaptacao.objects.all(),
    )

    class Meta:
        model = RespostaReparoEAdaptacao
        exclude = ("id",)


class RespostaUtensilioCozinhaSerializer(serializers.ModelSerializer):
    parametrizacao = ParametrizacaoOcorrenciaSerializer()
    resposta = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        allow_null=True,
        queryset=UtensilioCozinha.objects.all(),
    )

    class Meta:
        model = RespostaUtensilioCozinha
        exclude = ("id",)


class RespostaUtensilioMesaSerializer(serializers.ModelSerializer):
    parametrizacao = ParametrizacaoOcorrenciaSerializer()
    resposta = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        allow_null=True,
        queryset=UtensilioMesa.objects.all(),
    )

    class Meta:
        model = RespostaUtensilioMesa
        exclude = ("id",)


class OcorrenciaNaoSeAplicaSerializer(serializers.ModelSerializer):
    tipo_ocorrencia = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        allow_null=True,
        queryset=TipoOcorrencia.objects.all(),
    )

    class Meta:
        model = OcorrenciaNaoSeAplica
        exclude = ("id",)
