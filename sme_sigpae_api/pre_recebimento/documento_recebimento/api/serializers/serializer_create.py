from rest_framework import serializers
from xworkflows.base import InvalidTransitionError

from sme_sigpae_api.dados_comuns.api.serializers import (
    CamposObrigatoriosMixin
)
from sme_sigpae_api.dados_comuns.utils import (
    update_instance_from_dict,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import Cronograma
from sme_sigpae_api.pre_recebimento.documento_recebimento.models import (
    DataDeFabricaoEPrazo,
    DocumentoDeRecebimento,
    TipoDeDocumentoDeRecebimento,
)
from sme_sigpae_api.pre_recebimento.base.models import (
    UnidadeMedida,
)
from sme_sigpae_api.pre_recebimento.qualidade.models import (
    Laboratorio,
)
from ..helpers import (
    cria_datas_e_prazos_doc_recebimento,
    cria_tipos_de_documentos,
)


class TipoDeDocumentoDeRecebimentoCreateSerializer(serializers.ModelSerializer):
    tipo_documento = serializers.ChoiceField(
        choices=TipoDeDocumentoDeRecebimento.TIPO_DOC_CHOICES,
        required=True,
        allow_blank=False,
    )
    arquivos_do_tipo_de_documento = serializers.JSONField(write_only=True)
    descricao_documento = serializers.CharField(required=False)

    def validate(self, attrs):
        tipo_documento = attrs.get("tipo_documento", None)
        arquivos = attrs.get("arquivos_do_tipo_de_documento", None)
        tipos_obrigatorios = [
            TipoDeDocumentoDeRecebimento.TIPO_DOC_LAUDO,
        ]

        if tipo_documento in tipos_obrigatorios:
            for doc in arquivos:
                if not doc["arquivo"] or not doc["nome"]:
                    raise serializers.ValidationError(
                        {f"{tipo_documento}": ["Este campo é obrigatório."]}
                    )
        return attrs

    class Meta:
        model = TipoDeDocumentoDeRecebimento
        exclude = ("id", "documento_recebimento")


class DocumentoDeRecebimentoCreateSerializer(serializers.ModelSerializer):
    cronograma = serializers.UUIDField(required=True)
    tipos_de_documentos = TipoDeDocumentoDeRecebimentoCreateSerializer(
        many=True, required=False
    )
    numero_laudo = serializers.CharField(required=True)

    def validate_cronograma(self, value):
        cronograma = Cronograma.objects.filter(uuid=value)
        if not cronograma:
            raise serializers.ValidationError("Cronograma não existe")
        return value

    def create(self, validated_data):
        user = self.context["request"].user

        uuid_cronograma = validated_data.pop("cronograma", None)
        tipos_de_documentos = validated_data.pop("tipos_de_documentos", [])
        cronograma = Cronograma.objects.get(uuid=uuid_cronograma)
        documento_de_recebimento = DocumentoDeRecebimento.objects.create(
            cronograma=cronograma,
            **validated_data,
        )
        cria_tipos_de_documentos(tipos_de_documentos, documento_de_recebimento)
        documento_de_recebimento.inicia_fluxo(user=user)

        return documento_de_recebimento

    class Meta:
        model = DocumentoDeRecebimento
        exclude = ("id",)


class DataDeFabricaoEPrazoAnalisarRascunhoSerializer(serializers.ModelSerializer):
    data_fabricacao = serializers.DateField(required=False, allow_null=True)
    data_validade = serializers.DateField(required=False, allow_null=True)
    prazo_maximo_recebimento = serializers.ChoiceField(
        choices=DataDeFabricaoEPrazo.PRAZO_CHOICES, required=False, allow_blank=True
    )
    justificativa = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = DataDeFabricaoEPrazo
        fields = (
            "data_fabricacao",
            "data_validade",
            "prazo_maximo_recebimento",
            "justificativa",
        )


class DataDeFabricaoEPrazoAnalisarSerializer(
    DataDeFabricaoEPrazoAnalisarRascunhoSerializer
):
    def validate(self, attrs):
        prazo_maximo = attrs.get("prazo_maximo_recebimento", None)
        justificativa = attrs.get("justificativa", None)
        if prazo_maximo == DataDeFabricaoEPrazo.PRAZO_OUTRO and not justificativa:
            raise serializers.ValidationError(
                {
                    "justificativa": [
                        "Este campo é obrigatório quando o prazo maximo de recebimento é OUTRO."
                    ]
                }
            )
        return attrs

    class Meta(DataDeFabricaoEPrazoAnalisarRascunhoSerializer.Meta):
        extra_kwargs = {
            "data_fabricacao": {"required": True, "allow_null": False},
            "data_validade": {"required": True, "allow_null": False},
            "prazo_maximo_recebimento": {"required": True, "allow_blank": False},
        }


class DocumentoDeRecebimentoAnalisarRascunhoSerializer(serializers.ModelSerializer):
    laboratorio = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=Laboratorio.objects.all(),
        allow_null=True,
    )
    unidade_medida = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=UnidadeMedida.objects.all(),
        allow_null=True,
    )
    quantidade_laudo = serializers.FloatField(required=False, allow_null=True)
    saldo_laudo = serializers.FloatField(required=False, allow_null=True)
    numero_lote_laudo = serializers.CharField(required=False, allow_null=True)
    data_final_lote = serializers.DateField(required=False, allow_null=True)
    datas_fabricacao_e_prazos = DataDeFabricaoEPrazoAnalisarRascunhoSerializer(
        many=True, required=False
    )

    def update(self, instance, validated_data):
        datas_fabricacao_e_prazos = validated_data.pop("datas_fabricacao_e_prazos", [])
        update_instance_from_dict(instance, validated_data, save=True)
        instance.datas_fabricacao_e_prazos.all().delete()
        cria_datas_e_prazos_doc_recebimento(datas_fabricacao_e_prazos, instance)
        instance.save()
        return instance

    class Meta:
        model = DocumentoDeRecebimento
        fields = (
            "laboratorio",
            "quantidade_laudo",
            "unidade_medida",
            "numero_lote_laudo",
            "data_final_lote",
            "saldo_laudo",
            "datas_fabricacao_e_prazos",
        )


class DocumentoDeRecebimentoAnalisarSerializer(
    CamposObrigatoriosMixin, DocumentoDeRecebimentoAnalisarRascunhoSerializer
):
    def __init__(self, *args, **kwargs):
        """Exceção ao demais campos, correcao_solicitada não é obrigatório."""
        super().__init__(*args, **kwargs)
        self.fields["correcao_solicitada"] = serializers.CharField(required=False)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        datas_fabricacao_e_prazos = validated_data.pop("datas_fabricacao_e_prazos", [])
        tem_solicitacao_correcao = validated_data.get("correcao_solicitada", None)
        update_instance_from_dict(instance, validated_data, save=True)
        instance.datas_fabricacao_e_prazos.all().delete()
        cria_datas_e_prazos_doc_recebimento(datas_fabricacao_e_prazos, instance)
        try:
            if tem_solicitacao_correcao:
                instance.qualidade_solicita_correcao(
                    user=user, justificativa=tem_solicitacao_correcao
                )
            else:
                instance.qualidade_aprova_analise(user=user)
        except InvalidTransitionError as e:
            raise serializers.ValidationError(
                f"Erro de transição de estado. O status atual não permite análise: {e}"
            )
        instance.save()
        return instance

    class Meta(DocumentoDeRecebimentoAnalisarRascunhoSerializer.Meta):
        fields = DocumentoDeRecebimentoAnalisarRascunhoSerializer.Meta.fields + (
            "correcao_solicitada",
        )


class TipoDeDocumentoDeRecebimentoCorrecaoSerializer(serializers.ModelSerializer):
    tipo_documento = serializers.ChoiceField(
        choices=TipoDeDocumentoDeRecebimento.TIPO_DOC_CHOICES,
        required=True,
        allow_blank=True,
    )

    arquivos_do_tipo_de_documento = serializers.JSONField(
        write_only=True, required=True
    )

    def validate(self, attrs):
        tipo = attrs.get("tipo_documento")
        arquivos_do_tipo_de_documento = attrs.get("arquivos_do_tipo_de_documento")
        descricao_documento = attrs.get("descricao_documento")

        if tipo == TipoDeDocumentoDeRecebimento.TIPO_DOC_OUTROS:
            if not descricao_documento:
                raise serializers.ValidationError(
                    {
                        "tipo_documento": [
                            "O campo descricao_documento é obrigatório para documentos do tipo Outros."
                        ]
                    }
                )

        for arquivo in arquivos_do_tipo_de_documento:
            if not arquivo.get("arquivo") or not arquivo.get("nome"):
                raise serializers.ValidationError(
                    {
                        "arquivos_do_tipo_de_documento": [
                            "Os campos arquivo e nome são obrigatórios."
                        ]
                    }
                )

        return attrs

    class Meta:
        model = TipoDeDocumentoDeRecebimento
        fields = (
            "tipo_documento",
            "descricao_documento",
            "arquivos_do_tipo_de_documento",
        )


class DocumentoDeRecebimentoCorrecaoSerializer(serializers.ModelSerializer):
    tipos_de_documentos = TipoDeDocumentoDeRecebimentoCorrecaoSerializer(
        many=True, required=True
    )

    def validate(self, attrs):
        tipos_documentos_recebidos = [
            dados["tipo_documento"] for dados in attrs["tipos_de_documentos"]
        ]
        if (
            TipoDeDocumentoDeRecebimento.TIPO_DOC_LAUDO
            not in tipos_documentos_recebidos
        ):
            raise serializers.ValidationError(
                {
                    "tipos_de_documentos": "É obrigatório pelo menos um documento do tipo Laudo."
                }
            )

        choices_tipos_documentos = set(
            [choice[0] for choice in TipoDeDocumentoDeRecebimento.TIPO_DOC_CHOICES]
        )
        if len(choices_tipos_documentos.intersection(tipos_documentos_recebidos)) < 2:
            raise serializers.ValidationError(
                {
                    "tipos_de_documentos": (
                        "É obrigatório pelo menos um documento do tipo Laudo"
                        + " e um documento de algum dos tipos"
                        + f' {", ".join(choices_tipos_documentos)}.'
                    )
                }
            )

        return attrs

    def update(self, instance, validated_data):
        try:
            user = self.context["request"].user

            dados_tipos_documentos_corrigidos = validated_data.pop(
                "tipos_de_documentos", []
            )

            for tipo_documento_antigo in instance.tipos_de_documentos.all():
                tipo_documento_antigo.arquivos.all().delete()
                tipo_documento_antigo.delete()

            cria_tipos_de_documentos(dados_tipos_documentos_corrigidos, instance)

            instance.fornecedor_realiza_correcao(user=user)
            instance.save()

            return instance

        except InvalidTransitionError as e:
            raise serializers.ValidationError(
                f"Erro de transição de estado. O status deste documento de recebimento não permite correção: {e}"
            )

    class Meta:
        model = DocumentoDeRecebimento
        fields = ("tipos_de_documentos",)


class DocumentoDeRecebimentoAtualizacaoSerializer(serializers.ModelSerializer):
    tipos_de_documentos = TipoDeDocumentoDeRecebimentoCorrecaoSerializer(
        many=True, required=True
    )

    def update(self, instance, validated_data):
        try:
            user = self.context["request"].user

            dados_tipos_documentos_corrigidos = validated_data.pop(
                "tipos_de_documentos", []
            )

            for tipo_documento_antigo in instance.tipos_de_documentos.exclude(
                tipo_documento=TipoDeDocumentoDeRecebimento.TIPO_DOC_LAUDO
            ):
                tipo_documento_antigo.arquivos.all().delete()
                tipo_documento_antigo.delete()

            cria_tipos_de_documentos(dados_tipos_documentos_corrigidos, instance)

            instance.fornecedor_atualiza(user=user)
            instance.save()

            return instance

        except InvalidTransitionError as e:
            raise serializers.ValidationError(
                f"Erro de transição de estado. O status deste documento de recebimento não permite atualização: {e}"
            )

    class Meta:
        model = DocumentoDeRecebimento
        fields = ("tipos_de_documentos",)
