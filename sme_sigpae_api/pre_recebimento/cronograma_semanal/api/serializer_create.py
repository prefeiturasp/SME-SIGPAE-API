from django.db import transaction
from rest_framework import serializers

from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import Cronograma
from sme_sigpae_api.pre_recebimento.cronograma_semanal.models import (
    CronogramaSemanal,
    ProgramacaoEntregaSemanal,
)


class ProgramacaoEntregaSemanalCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de ProgramacaoEntregaSemanal"""

    mes_programado = serializers.CharField(required=True)
    data_inicio = serializers.DateField(required=True)
    data_fim = serializers.DateField(required=True)
    quantidade = serializers.FloatField(required=True)

    class Meta:
        model = ProgramacaoEntregaSemanal
        fields = (
            "mes_programado",
            "data_inicio",
            "data_fim",
            "quantidade",
        )

    def validate(self, data):
        if data.get("data_inicio") and data.get("data_fim"):
            if data["data_fim"] < data["data_inicio"]:
                raise serializers.ValidationError("Data fim deve ser posterior à data início.")
        return data


class CronogramaSemanalRascunhoSerializer(serializers.ModelSerializer):
    """
    Serializer para criação/atualização de Rascunho de CronogramaSemanal.
    Apenas o cronograma_mensal é obrigatório.
    """

    cronograma_mensal = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Cronograma.objects.all(),
        required=True,
        error_messages={
            "does_not_exist": "Cronograma mensal não encontrado.",
            "required": "Este campo é obrigatório.",
        },
    )
    observacoes = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    programacoes = ProgramacaoEntregaSemanalCreateSerializer(
        many=True,
        required=False,
    )

    class Meta:
        model = CronogramaSemanal
        fields = (
            "uuid",
            "cronograma_mensal",
            "observacoes",
            "programacoes",
        )

    def validate_cronograma_mensal(self, value):
        """Valida se o cronograma mensal é Ponto a Ponto e está assinado"""
        if not value.ponto_a_ponto:
            raise serializers.ValidationError(
                "O cronograma mensal deve ser do tipo Ponto a Ponto."
            )
        if value.status != "ASSINADO_CODAE":
            raise serializers.ValidationError(
                "O cronograma mensal deve estar com status ASSINADO_CODAE."
            )
        return value

    def create(self, validated_data):
        programacoes_data = validated_data.pop("programacoes", [])
        with transaction.atomic():
            cronograma_semanal = CronogramaSemanal.objects.create(**validated_data)
            for programacao_data in programacoes_data:
                ProgramacaoEntregaSemanal.objects.create(
                    cronograma_semanal=cronograma_semanal, **programacao_data
                )
        return cronograma_semanal

    def update(self, instance, validated_data):
        programacoes_data = validated_data.pop("programacoes", None)

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if programacoes_data is not None:
                instance.programacoes.all().delete()
                programacoes = [
                    ProgramacaoEntregaSemanal(cronograma_semanal=instance, **data)
                    for data in programacoes_data
                ]
                ProgramacaoEntregaSemanal.objects.bulk_create(programacoes)

        return instance


class CronogramaSemanalAssinarEEnviarSerializer(CronogramaSemanalRascunhoSerializer):
    """
    Serializer para assinar e enviar CronogramaSemanal.
    Todos os campos são obrigatórios e executa a transição inicia_fluxo.
    """

    programacoes = ProgramacaoEntregaSemanalCreateSerializer(
        many=True,
        required=True,
    )

    def validate_programacoes(self, value):
        """Valida se há pelo menos uma programação"""
        if not value or len(value) == 0:
            raise serializers.ValidationError(
                "É necessário adicionar pelo menos uma programação."
            )
        return value

    def create(self, validated_data):
        programacoes_data = validated_data.pop("programacoes", [])
        user = self.context["request"].user

        with transaction.atomic():
            cronograma_semanal = CronogramaSemanal.objects.create(**validated_data)
            for programacao_data in programacoes_data:
                ProgramacaoEntregaSemanal.objects.create(
                    cronograma_semanal=cronograma_semanal, **programacao_data
                )
            # Executa a transição do workflow
            cronograma_semanal.inicia_fluxo(user=user)

        return cronograma_semanal

    def update(self, instance, validated_data):
        programacoes_data = validated_data.pop("programacoes", None)
        user = self.context["request"].user

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if programacoes_data is not None:
                instance.programacoes.all().delete()
                programacoes = [
                    ProgramacaoEntregaSemanal(cronograma_semanal=instance, **data)
                    for data in programacoes_data
                ]
                ProgramacaoEntregaSemanal.objects.bulk_create(programacoes)

            # Executa a transição do workflow
            instance.inicia_fluxo(user=user)

        return instance
