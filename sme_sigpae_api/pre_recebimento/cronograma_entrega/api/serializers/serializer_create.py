from datetime import date

from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated
from xworkflows.base import InvalidTransitionError

from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.dados_comuns.utils import (
    update_instance_from_dict,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import (
    Cronograma,
    EtapasDoCronograma,
    ProgramacaoDoRecebimentoDoCronograma,
    SolicitacaoAlteracaoCronograma,
)
from sme_sigpae_api.pre_recebimento.base.models import (
    UnidadeMedida,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto
from sme_sigpae_api.pre_recebimento.qualidade.models import TipoEmbalagemQld
from sme_sigpae_api.terceirizada.models import Contrato, Terceirizada

from ..helpers import (
    cria_etapas_de_cronograma,
    cria_programacao_de_cronograma,
)
from ..validators import (
    contrato_pertence_a_empresa,
)


class ProgramacaoDoRecebimentoDoCronogramaCreateSerializer(serializers.ModelSerializer):
    data_programada = serializers.CharField(required=False)
    tipo_carga = serializers.ChoiceField(
        choices=ProgramacaoDoRecebimentoDoCronograma.TIPO_CARGA_CHOICES,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = ProgramacaoDoRecebimentoDoCronograma
        exclude = ("id", "cronograma")


class EtapasDoCronogramaCreateSerializer(serializers.ModelSerializer):
    numero_empenho = serializers.CharField(required=False)
    etapa = serializers.IntegerField(required=False, allow_null=True)
    parte = serializers.CharField(required=False)
    data_programada = serializers.CharField(required=False)
    quantidade = serializers.FloatField(required=False)
    total_embalagens = serializers.FloatField(required=False)
    qtd_total_empenho = serializers.FloatField(required=False)

    class Meta:
        model = EtapasDoCronograma
        exclude = ("id", "cronograma")


class CronogramaCreateSerializer(serializers.ModelSerializer):
    armazem = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=Terceirizada.objects.filter(
            tipo_servico=Terceirizada.DISTRIBUIDOR_ARMAZEM
        ),
        allow_null=True,
    )
    empresa = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=Terceirizada.objects.filter(
            tipo_servico__in=[
                Terceirizada.FORNECEDOR,
                Terceirizada.FORNECEDOR_E_DISTRIBUIDOR,
            ]
        ),
    )
    contrato = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=Contrato.objects.all(),
        allow_null=True,
    )
    unidade_medida = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=UnidadeMedida.objects.all(),
        allow_null=True,
    )
    password = serializers.CharField(required=False)
    qtd_total_programada = serializers.FloatField(required=False)
    etapas = EtapasDoCronogramaCreateSerializer(many=True, required=False)
    programacoes_de_recebimento = ProgramacaoDoRecebimentoDoCronogramaCreateSerializer(
        many=True, required=False
    )
    cadastro_finalizado = serializers.BooleanField(required=False)
    ficha_tecnica = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=FichaTecnicaDoProduto.objects.all(),
        allow_null=True,
    )
    tipo_embalagem_secundaria = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=TipoEmbalagemQld.objects.all(),
        required=False,
        allow_null=True,
    )
    custo_unitario_produto = serializers.FloatField(required=False)

    def gera_proximo_numero_cronograma(self):
        ano = date.today().year
        ultimo_cronograma = Cronograma.objects.last()
        if ultimo_cronograma:
            return f"{str(int(ultimo_cronograma.numero[:3]) + 1).zfill(3)}/{ano}A"
        else:
            return f"001/{ano}A"

    def validate(self, attrs):
        user = self.context["request"].user
        cadastro_finalizado = attrs.get("cadastro_finalizado", None)
        if cadastro_finalizado and not user.verificar_autenticidade(
            attrs.pop("password", None)
        ):
            raise NotAuthenticated(
                "Assinatura do cronograma não foi validada. Verifique sua senha."
            )

        contrato = attrs.get("contrato", None)
        empresa = attrs.get("empresa", None)
        contrato_pertence_a_empresa(contrato, empresa)

        return super().validate(attrs)

    def create(self, validated_data):
        user = self.context["request"].user
        cadastro_finalizado = validated_data.pop("cadastro_finalizado", None)
        etapas = validated_data.pop("etapas", [])
        programacoes_de_recebimento = validated_data.pop(
            "programacoes_de_recebimento", []
        )
        numero_cronograma = self.gera_proximo_numero_cronograma()
        cronograma = Cronograma.objects.create(
            numero=numero_cronograma, **validated_data
        )
        cronograma.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CRONOGRAMA_CRIADO, usuario=user
        )

        cria_etapas_de_cronograma(etapas, cronograma)
        cria_programacao_de_cronograma(programacoes_de_recebimento, cronograma)

        if cadastro_finalizado:
            cronograma.inicia_fluxo(user=user)

        return cronograma

    def update(self, instance, validated_data):
        user = self.context["request"].user
        cadastro_finalizado = validated_data.pop("cadastro_finalizado", None)
        etapas = validated_data.pop("etapas", [])
        programacoes_de_recebimento = validated_data.pop(
            "programacoes_de_recebimento", []
        )

        instance.etapas.all().delete()
        instance.programacoes_de_recebimento.all().delete()

        update_instance_from_dict(instance, validated_data, save=True)

        cria_etapas_de_cronograma(etapas, instance)
        cria_programacao_de_cronograma(programacoes_de_recebimento, instance)

        if cadastro_finalizado:
            instance.inicia_fluxo(user=user)
        return instance

    class Meta:
        model = Cronograma
        exclude = ("id", "numero", "status")


def novo_numero_solicitacao(objeto):
    # Nova regra para sequência de numeração.
    objeto.numero_solicitacao = f"{str(objeto.pk).zfill(8)}-ALT"
    objeto.save()


class SolicitacaoDeAlteracaoCronogramaCreateSerializer(serializers.ModelSerializer):
    cronograma = serializers.UUIDField()
    etapas = serializers.JSONField(write_only=True)
    programacoes_de_recebimento = serializers.JSONField(write_only=True, required=False)

    def validate_cronograma(self, value):
        cronograma = Cronograma.objects.filter(uuid=value)
        if not cronograma:
            raise serializers.ValidationError("Cronograma não existe")
        if not cronograma.first().status == Cronograma.workflow_class.ASSINADO_CODAE:
            raise serializers.ValidationError(
                "Não é possivel criar Solicitação de alteração neste momento!"
            )
        return value

    def valida_campo_etapa(self, etapa, campo):
        if not etapa[campo]:
            raise serializers.ValidationError({campo: ["Este campo é obrigatório."]})

    def validate(self, attrs):
        for etapa in attrs["etapas"]:
            self.valida_campo_etapa(etapa, "etapa")
            self.valida_campo_etapa(etapa, "data_programada")
            self.valida_campo_etapa(etapa, "quantidade")
            self.valida_campo_etapa(etapa, "total_embalagens")
        return super().validate(attrs)

    def _criar_etapas(self, etapas):
        etapas_created = []
        for etapa in etapas:
            etapas_created.append(EtapasDoCronograma.objects.create(**etapa))
        return etapas_created

    def create(self, validated_data):
        user = self.context["request"].user
        uuid_cronograma = validated_data.pop("cronograma", None)
        etapas = validated_data.pop("etapas", [])
        programacoes = validated_data.pop("programacoes_de_recebimento", [])
        cronograma = Cronograma.objects.get(uuid=uuid_cronograma)
        alteracao_cronograma = SolicitacaoAlteracaoCronograma.objects.create(
            usuario_solicitante=user,
            cronograma=cronograma,
            **validated_data,
        )
        alteracao_cronograma.etapas_antigas.set(cronograma.etapas.all())
        etapas_created = cria_etapas_de_cronograma(etapas)
        alteracao_cronograma.etapas_novas.set(etapas_created)
        programacoes_criadas = cria_programacao_de_cronograma(programacoes)
        alteracao_cronograma.programacoes_novas.set(programacoes_criadas)
        self._alterna_estado_cronograma(cronograma, user, alteracao_cronograma)
        self._alterna_estado_solicitacao_alteracao_cronograma(
            alteracao_cronograma, user, validated_data
        )
        return alteracao_cronograma

    def _alterna_estado_cronograma(self, cronograma, user, alteracao_cronograma):
        try:
            if user.eh_fornecedor:
                cronograma.fornecedor_solicita_alteracao(
                    user=user, justificativa=alteracao_cronograma.uuid
                )
            else:
                cronograma.codae_realiza_alteracao(
                    user=user, justificativa=alteracao_cronograma.uuid
                )
        except InvalidTransitionError as e:
            raise serializers.ValidationError(
                f"Erro de transição de estado do cronograma: {e}"
            )

    def _alterna_estado_solicitacao_alteracao_cronograma(
        self, alteracao_cronograma, user, validated_data
    ):
        try:
            if user.eh_fornecedor:
                alteracao_cronograma.inicia_fluxo(
                    user=user, justificativa=validated_data.get("justificativa", "")
                )
            else:
                alteracao_cronograma.inicia_fluxo_codae(
                    user=user, justificativa=validated_data.get("justificativa", "")
                )
        except InvalidTransitionError as e:
            raise serializers.ValidationError(
                f"Erro de transição de estado da alteração: {e}"
            )

    class Meta:
        model = SolicitacaoAlteracaoCronograma
        exclude = ("id", "usuario_solicitante", "etapas_antigas", "etapas_novas")
