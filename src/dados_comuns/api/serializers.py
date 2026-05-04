from datetime import datetime

import environ
from des.models import DynamicEmailConfiguration
from rest_framework import serializers

from ...perfil.api.serializers import UsuarioSerializer, UsuarioSimplesSerializer
from ..models import (
    AnexoLogSolicitacoesUsuario,
    CategoriaPerguntaFrequente,
    CentralDeDownload,
    Contato,
    Endereco,
    LogSolicitacoesUsuario,
    Notificacao,
    PerguntaFrequente,
    SolicitacaoAberta,
    TemplateMensagem,
)
from ..services import ServiceMapeamentoLogsLinhaDoTempo


class CamposObrigatoriosMixin:
    def __init__(self, *args, **kwargs):
        """Define campos obrigatórios, para ser usado quando extender um serializer com campos não obrigatórios."""
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True
            field.allow_null = False
            field.allow_blank = False


class AnexoLogSolicitacoesUsuarioSerializer(serializers.ModelSerializer):
    nome = serializers.CharField()
    arquivo_url = serializers.SerializerMethodField()

    def get_arquivo_url(self, instance):
        env = environ.Env()
        api_url = env.str("URL_ANEXO", default="http://localhost:8000")
        return f"{api_url}{instance.arquivo.url}"

    class Meta:
        model = AnexoLogSolicitacoesUsuario
        fields = ("nome", "arquivo", "arquivo_url")


class LogSolicitacoesUsuarioComAnexosSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer()
    anexos = serializers.SerializerMethodField()
    status_evento_explicacao = serializers.CharField(
        source="get_status_evento_display", required=False, read_only=True
    )
    tipo_solicitacao_explicacao = serializers.CharField(
        source="get_solicitacao_tipo_display", required=False, read_only=True
    )

    def get_anexos(self, obj):
        return AnexoLogSolicitacoesUsuarioSerializer(
            AnexoLogSolicitacoesUsuario.objects.filter(log=obj), many=True
        ).data

    class Meta:
        model = LogSolicitacoesUsuario
        fields = (
            "anexos",
            "status_evento_explicacao",
            "usuario",
            "criado_em",
            "descricao",
            "justificativa",
            "resposta_sim_nao",
            "tipo_solicitacao_explicacao",
        )


class LogSolicitacoesUsuarioSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer()
    status_evento_explicacao = serializers.CharField(
        source="get_status_evento_display", required=False, read_only=True
    )

    class Meta:
        model = LogSolicitacoesUsuario
        fields = (
            "status_evento_explicacao",
            "usuario",
            "criado_em",
            "descricao",
            "justificativa",
            "resposta_sim_nao",
        )


class LogSolicitacoesUsuarioSimplesSerializer(serializers.ModelSerializer):
    usuario = UsuarioSimplesSerializer()
    status_evento_explicacao = serializers.SerializerMethodField()

    def get_status_evento_explicacao(self, obj):
        status_map = ServiceMapeamentoLogsLinhaDoTempo.get_status_map(
            obj.solicitacao_tipo
        )

        return status_map.get(
            obj.status_evento_explicacao, obj.status_evento_explicacao
        )

    class Meta:
        model = LogSolicitacoesUsuario
        fields = (
            "status_evento_explicacao",
            "usuario",
            "criado_em",
            "justificativa",
        )


class LogSolicitacoesSerializer(serializers.ModelSerializer):
    status_evento_explicacao = serializers.CharField(
        source="get_status_evento_display", required=False, read_only=True
    )

    anexos = serializers.SerializerMethodField()

    def get_anexos(self, obj):
        return AnexoLogSolicitacoesUsuarioSerializer(
            AnexoLogSolicitacoesUsuario.objects.filter(log=obj), many=True
        ).data

    class Meta:
        model = LogSolicitacoesUsuario
        fields = (
            "status_evento_explicacao",
            "criado_em",
            "descricao",
            "justificativa",
            "resposta_sim_nao",
            "anexos",
        )


class LogSolicitacoesUsuarioComVinculoSerializer(LogSolicitacoesUsuarioSerializer):
    nome_instituicao = serializers.SerializerMethodField()

    def get_nome_instituicao(self, obj):
        return (
            obj.usuario.vinculo_atual.instituicao.nome
            if obj.usuario and obj.usuario.vinculo_atual
            else None
        )

    class Meta:
        model = LogSolicitacoesUsuario
        fields = (
            "status_evento_explicacao",
            "usuario",
            "criado_em",
            "descricao",
            "justificativa",
            "resposta_sim_nao",
            "nome_instituicao",
        )


class ConfiguracaoEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicEmailConfiguration
        fields = (
            "host",
            "port",
            "username",
            "password",
            "from_email",
            "use_tls",
            "use_ssl",
            "timeout",
        )


class ConfiguracaoMensagemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateMensagem
        exclude = ("id", "tipo")


class ContatoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contato
        exclude = ("id",)


class ContatoSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contato
        fields = ("nome", "telefone", "email")


class CategoriaPerguntaFrequenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaPerguntaFrequente
        exclude = ("id",)


class PerguntaFrequenteCreateSerializer(serializers.ModelSerializer):
    categoria = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=CategoriaPerguntaFrequente.objects.all(),
    )

    class Meta:
        model = PerguntaFrequente
        exclude = ("id", "criado_em")


class PerguntaFrequenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerguntaFrequente
        exclude = ("id", "categoria", "criado_em")


class ConsultaPerguntasFrequentesSerializer(serializers.ModelSerializer):
    perguntas = PerguntaFrequenteSerializer(
        many=True, source="perguntafrequente_set", read_only=True
    )

    class Meta:
        model = CategoriaPerguntaFrequente
        exclude = ("id",)


class EnderecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endereco
        exclude = ("id",)


class NotificacaoSerializer(serializers.ModelSerializer):
    tipo = serializers.CharField(source="get_tipo_display")
    categoria = serializers.CharField(source="get_categoria_display")
    hora = serializers.SerializerMethodField()
    criado_em = serializers.SerializerMethodField()

    def get_hora(self, obj):
        return obj.hora.strftime("%H:%M")

    def get_criado_em(self, obj):
        return obj.criado_em.strftime("%d/%m/%Y")

    class Meta:
        model = Notificacao
        fields = [
            "uuid",
            "titulo",
            "descricao",
            "criado_em",
            "hora",
            "tipo",
            "categoria",
            "link",
            "lido",
            "resolvido",
        ]


class CentralDeDownloadSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="get_status_display")
    data_criacao = serializers.SerializerMethodField()

    def get_data_criacao(self, obj):
        return obj.criado_em.strftime("%d/%m/%Y ás %H:%M")

    class Meta:
        model = CentralDeDownload
        fields = [
            "uuid",
            "identificador",
            "arquivo",
            "status",
            "data_criacao",
            "msg_erro",
            "visto",
        ]


class SolicitacaoAbertaSerializer(serializers.ModelSerializer):
    uuid_solicitacao = serializers.CharField()
    usuario = UsuarioSerializer(required=False)
    datetime_ultimo_acesso = serializers.CharField(required=False)

    def create(self, validated_data):
        user = self.context["request"].user
        datetime_ultimo_acesso = datetime.now()
        return SolicitacaoAberta.objects.create(
            usuario=user,
            datetime_ultimo_acesso=datetime_ultimo_acesso,
            **validated_data,
        )

    def update(self, instance, validated_data):
        datetime_ultimo_acesso = datetime.now()
        instance.datetime_ultimo_acesso = datetime_ultimo_acesso
        instance.save()

        return instance

    class Meta:
        model = SolicitacaoAberta
        fields = ("id", "uuid_solicitacao", "usuario", "datetime_ultimo_acesso")
