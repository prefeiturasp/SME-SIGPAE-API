import re

from rest_framework import serializers

from src.dados_comuns.constants import DILOG_QUALIDADE
from src.perfil.models import Usuario
from src.pre_recebimento.cronograma_entrega.models import Cronograma
from src.terceirizada.models import Contrato, Terceirizada

from ...models import TermoRecebimentoDefinitivo
from ..services import TermoRecebimentoDefinitivoService


class CronogramaTermoRecebimentoDefinitivoCreateSerializer(serializers.Serializer):
    """Item de cronograma do Termo de Recebimento Definitivo.

    Cada cronograma possui seu próprio valor de contrato e quantidade
    total recebida.
    """

    cronograma = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Cronograma.objects.all(),
        error_messages={"does_not_exist": "Cronograma não encontrado."},
    )
    valor_contrato = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    quantidade_total_recebida = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
    )


class TermoRecebimentoDefinitivoCreateSerializer(serializers.ModelSerializer):
    """Serializador de criação do Termo de Recebimento Definitivo.

    Recebe os uuids de empresa, contrato, cronogramas (cada um com seu
    valor de contrato e quantidade recebida) e fiscais, e valida as
    regras de negócio:

    - todos os campos obrigatórios;
    - empresa com ao menos uma ficha de recebimento "Assinado CODAE";
    - contrato vinculado à empresa selecionada;
    - cronogramas vinculados ao contrato/empresa selecionados;
    - fiscais com perfil DILOG_QUALIDADE;
    - valor do contrato e quantidade total recebida maiores que zero.
    """

    empresa = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Terceirizada.objects.all(),
        error_messages={"does_not_exist": "Empresa não encontrada."},
    )
    contrato = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Contrato.objects.all(),
        error_messages={"does_not_exist": "Contrato não encontrado."},
    )
    cronogramas = CronogramaTermoRecebimentoDefinitivoCreateSerializer(
        many=True,
        allow_empty=False,
    )
    fiscal_1 = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Usuario.objects.all(),
        error_messages={"does_not_exist": "Fiscal 1 não encontrado."},
    )
    fiscal_2 = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Usuario.objects.all(),
        error_messages={"does_not_exist": "Fiscal 2 não encontrado."},
    )
    fiscal_3 = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Usuario.objects.all(),
        error_messages={"does_not_exist": "Fiscal 3 não encontrado."},
    )

    class Meta:
        model = TermoRecebimentoDefinitivo
        fields = (
            "empresa",
            "contrato",
            "cronogramas",
            "fiscal_1",
            "fiscal_2",
            "fiscal_3",
            "texto_termo",
        )

    def _valida_empresa_com_ficha_assinada(self, empresa):
        """Empresa deve possuir ao menos uma ficha de recebimento
        'Assinado CODAE' (FichaDeRecebimentoWorkflow.ASSINADA)."""
        if not TermoRecebimentoDefinitivoService.empresa_tem_ficha_assinada(empresa):
            raise serializers.ValidationError(
                "A empresa deve possuir ao menos uma ficha de recebimento "
                "assinada pela CODAE."
            )

    def _valida_contrato_da_empresa(self, empresa, contrato):
        """O contrato informado deve pertencer à empresa selecionada."""
        if contrato.terceirizada_id != empresa.id:
            raise serializers.ValidationError(
                "O contrato informado não pertence à empresa selecionada."
            )

    def _valida_cronogramas(self, empresa, contrato, cronogramas):
        """Cronogramas não podem se repetir no payload e devem pertencer
        ao contrato e à empresa selecionados."""
        uuids_informados = []
        for item in cronogramas:
            cronograma = item["cronograma"]
            if cronograma.uuid in uuids_informados:
                raise serializers.ValidationError(
                    f"O cronograma {cronograma.numero} foi informado mais de "
                    "uma vez."
                )
            uuids_informados.append(cronograma.uuid)
            if cronograma.contrato_id != contrato.id:
                raise serializers.ValidationError(
                    f"O cronograma {cronograma.numero} não pertence ao "
                    "contrato selecionado."
                )
            if cronograma.empresa_id != empresa.id:
                raise serializers.ValidationError(
                    f"O cronograma {cronograma.numero} não pertence à "
                    "empresa selecionada."
                )

    def _valida_fiscais(self, fiscais):
        """Cada fiscal deve possuir vínculo ativo com o perfil
        DILOG_QUALIDADE."""
        for campo, fiscal in fiscais:
            if not fiscal.vinculos.filter(
                perfil__nome=DILOG_QUALIDADE, ativo=True
            ).exists():
                raise serializers.ValidationError(
                    {campo: "O usuário informado não possui o perfil DILOG_QUALIDADE."}
                )

    def validate(self, attrs):
        empresa = attrs.get("empresa")
        contrato = attrs.get("contrato")
        cronogramas = attrs.get("cronogramas")

        self._valida_empresa_com_ficha_assinada(empresa)
        self._valida_contrato_da_empresa(empresa, contrato)
        self._valida_cronogramas(empresa, contrato, cronogramas)
        self._valida_fiscais(
            [
                ("fiscal_1", attrs.get("fiscal_1")),
                ("fiscal_2", attrs.get("fiscal_2")),
                ("fiscal_3", attrs.get("fiscal_3")),
            ]
        )

        errors = {}
        for index, item in enumerate(cronogramas):
            if item["valor_contrato"] is not None and item["valor_contrato"] <= 0:
                errors[f"cronogramas[{index}].valor_contrato"] = (
                    "O valor do contrato deve ser maior que zero."
                )
            if (
                item["quantidade_total_recebida"] is not None
                and item["quantidade_total_recebida"] <= 0
            ):
                errors[f"cronogramas[{index}].quantidade_total_recebida"] = (
                    "A quantidade total recebida deve ser maior que zero."
                )
        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def validate_texto_termo(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("O texto do termo é obrigatório.")
        texto_limpo = re.sub(r"<[^>]*>", "", value).strip()
        if not texto_limpo:
            raise serializers.ValidationError(
                "O texto do termo é obrigatório e deve conter conteúdo."
            )
        return value
