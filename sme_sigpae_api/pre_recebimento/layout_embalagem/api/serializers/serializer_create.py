from rest_framework import serializers
from xworkflows.base import InvalidTransitionError

from sme_sigpae_api.dados_comuns.utils import (
    convert_base64_to_contentfile,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto
from sme_sigpae_api.pre_recebimento.layout_embalagem.models import (
    ImagemDoTipoDeEmbalagem,
    LayoutDeEmbalagem,
    TipoDeEmbalagemDeLayout,
)

from ..helpers import (
    cria_tipos_de_embalagens,
)


class TipoDeEmbalagemDeLayoutCreateSerializer(serializers.ModelSerializer):
    tipo_embalagem = serializers.ChoiceField(
        choices=TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_CHOICES,
        required=True,
        allow_blank=True,
    )
    imagens_do_tipo_de_embalagem = serializers.JSONField(write_only=True)

    def validate(self, attrs):
        tipo_embalagem = attrs.get("tipo_embalagem", None)
        imagens = attrs.get("imagens_do_tipo_de_embalagem", None)
        tipos_obrigatorios = [
            TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_PRIMARIA,
            TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_SECUNDARIA,
        ]

        if tipo_embalagem in tipos_obrigatorios:
            for img in imagens:
                if not img["arquivo"] or not img["nome"]:
                    raise serializers.ValidationError(
                        {
                            f"Layout Embalagem {tipo_embalagem}": [
                                "Este campo é obrigatório."
                            ]
                        }
                    )
        return attrs

    class Meta:
        model = TipoDeEmbalagemDeLayout
        exclude = ("id", "layout_de_embalagem")


class LayoutDeEmbalagemCreateSerializer(serializers.ModelSerializer):
    ficha_tecnica = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=FichaTecnicaDoProduto.objects.all(),
        required=True,
    )
    tipos_de_embalagens = TipoDeEmbalagemDeLayoutCreateSerializer(
        many=True, required=False
    )
    observacoes = serializers.CharField(required=False)

    def validate_ficha_tecnica(self, value):
        if (
            value is not None
            and value.status == FichaTecnicaDoProduto.workflow_class.RASCUNHO
        ):
            raise serializers.ValidationError(
                "Não é possível vincular com Ficha Técnica em rascunho."
            )

        return value

    def create(self, validated_data):
        user = self.context["request"].user

        tipos_de_embalagens = validated_data.pop("tipos_de_embalagens", [])
        layout_de_embalagem = LayoutDeEmbalagem.objects.create(
            **validated_data,
        )
        cria_tipos_de_embalagens(tipos_de_embalagens, layout_de_embalagem)
        layout_de_embalagem.inicia_fluxo(user=user)

        return layout_de_embalagem

    def update(self, instance, validated_data):
        try:
            user = self.context["request"].user
            dados_correcao = validated_data.pop("tipos_de_embalagens", [])

            instance.tipos_de_embalagens.all().delete()
            cria_tipos_de_embalagens(dados_correcao, instance)

            instance.observacoes = validated_data.pop("observacoes", "")
            instance.fornecedor_atualiza(user=user)
            instance.save()

        except InvalidTransitionError as e:
            raise serializers.ValidationError(
                f"Erro de transição de estado. O status deste layout não permite correção: {e}"
            )

        return instance

    class Meta:
        model = LayoutDeEmbalagem
        exclude = ("id",)


class TipoDeEmbalagemDeLayoutAnaliseSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=False)

    def validate(self, attrs):
        uuid = attrs.get("uuid", None)
        tipo_embalagem = attrs.get("tipo_embalagem", None)
        status = attrs.get("status", None)

        if tipo_embalagem is TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_PRIMARIA:
            if not uuid or not status:
                raise serializers.ValidationError(
                    {
                        f"Layout Embalagem {tipo_embalagem}": [
                            "UUID obrigatório para o tipo de embalagem informado."
                        ]
                    }
                )
        return attrs

    class Meta:
        model = TipoDeEmbalagemDeLayout
        fields = ("uuid", "tipo_embalagem", "status", "complemento_do_status")
        extra_kwargs = {
            "tipo_embalagem": {"required": True},
            "status": {"required": False},
            "complemento_do_status": {"required": True},
        }


class LayoutDeEmbalagemAnaliseSerializer(serializers.ModelSerializer):
    tipos_de_embalagens = TipoDeEmbalagemDeLayoutAnaliseSerializer(many=True)

    def validate_tipos_de_embalagens(self, value):
        self._validar_primeira_analise(value)

        return value

    def _validar_primeira_analise(self, value):
        if self.instance.eh_primeira_analise:
            if len(value) < self.instance.tipos_de_embalagens.count():
                raise serializers.ValidationError(
                    "Quantidade de Tipos de Embalagem recebida para primeira análise "
                    + "é menor que quantidade presente no Layout de Embalagem."
                )

    def update(self, instance, validated_data):
        try:
            user = self.context["request"].user
            dados_tipos_de_embalagens = validated_data.pop("tipos_de_embalagens", [])

            for dados in dados_tipos_de_embalagens:
                if dados["tipo_embalagem"] in [
                    TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_SECUNDARIA,
                    TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_TERCIARIA,
                ] and not dados.get("uuid", None):
                    TipoDeEmbalagemDeLayout.objects.create(
                        layout_de_embalagem=instance, **dados
                    )

                else:
                    tipo_de_embalagem = instance.tipos_de_embalagens.get(
                        uuid=dados["uuid"]
                    )
                    tipo_de_embalagem.status = dados["status"]
                    tipo_de_embalagem.complemento_do_status = dados[
                        "complemento_do_status"
                    ]
                    tipo_de_embalagem.save()

            (
                instance.codae_aprova(user=user)
                if instance.aprovado
                else instance.codae_solicita_correcao(user=user)
            )

        except InvalidTransitionError as e:
            raise serializers.ValidationError(
                f"Erro de transição de estado. O status deste layout não permite analise: {e}"
            )

        return instance

    class Meta:
        model = LayoutDeEmbalagem
        fields = ("tipos_de_embalagens",)


class TipoDeEmbalagemDeLayoutCorrecaoSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField()
    tipo_embalagem = serializers.ChoiceField(
        choices=TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_CHOICES,
        required=True,
        allow_blank=True,
    )
    imagens_do_tipo_de_embalagem = serializers.JSONField(write_only=True, required=True)

    def validate(self, attrs):
        uuid = attrs.get("uuid", None)
        tipo = attrs.get("tipo_embalagem", None)
        imagens = attrs.get("imagens_do_tipo_de_embalagem", None)
        embalagem = TipoDeEmbalagemDeLayout.objects.filter(uuid=uuid).last()

        if not embalagem:
            raise serializers.ValidationError(
                {f"Layout Embalagem {tipo}": ["UUID do tipo informado não existe."]}
            )
        if embalagem.status != TipoDeEmbalagemDeLayout.STATUS_REPROVADO:
            raise serializers.ValidationError(
                {
                    f"Layout Embalagem {tipo}": [
                        "O Tipo/UUID informado não pode ser corrigido pois não está reprovado."
                    ]
                }
            )
        for img in imagens:
            if not img["arquivo"] or not img["nome"]:
                raise serializers.ValidationError(
                    {f"Layout Embalagem {tipo}": ["arquivo/nome é obrigatório."]}
                )
        return attrs

    class Meta:
        model = TipoDeEmbalagemDeLayout
        exclude = ("id", "layout_de_embalagem")


class LayoutDeEmbalagemCorrecaoSerializer(serializers.ModelSerializer):
    tipos_de_embalagens = TipoDeEmbalagemDeLayoutCorrecaoSerializer(
        many=True, required=True
    )
    observacoes = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        try:
            user = self.context["request"].user
            dados_correcao = validated_data.pop("tipos_de_embalagens", [])

            for embalagem in dados_correcao:
                tipo_embalagem = instance.tipos_de_embalagens.get(
                    uuid=embalagem["uuid"]
                )
                tipo_embalagem.status = TipoDeEmbalagemDeLayout.STATUS_EM_ANALISE
                tipo_embalagem.imagens.all().delete()
                tipo_embalagem.save()
                imagens = embalagem.pop("imagens_do_tipo_de_embalagem", [])
                for img in imagens:
                    data = convert_base64_to_contentfile(img.get("arquivo"))
                    ImagemDoTipoDeEmbalagem.objects.create(
                        tipo_de_embalagem=tipo_embalagem,
                        arquivo=data,
                        nome=img.get("nome", ""),
                    )

            instance.observacoes = validated_data.pop("observacoes", "")
            instance.fornecedor_realiza_correcao(user=user)
            instance.save()

        except InvalidTransitionError as e:
            raise serializers.ValidationError(
                f"Erro de transição de estado. O status deste layout não permite correção: {e}"
            )

        return instance

    class Meta:
        model = LayoutDeEmbalagem
        fields = ("tipos_de_embalagens", "observacoes")
