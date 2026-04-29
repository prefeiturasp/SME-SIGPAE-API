from rest_framework import serializers

from sme_sigpae_api.dados_comuns.utils import (
    remove_multiplos_espacos,
    update_instance_from_dict,
)
from sme_sigpae_api.dieta_especial.protocolo_padrao.api.validators import (
    edital_ja_existe_protocolo,
)
from sme_sigpae_api.dieta_especial.protocolo_padrao.models import (
    Alimento,
    AlimentoSubstituto,
    ProtocoloPadraoDietaEspecial,
    SubstituicaoAlimento,
    SubstituicaoAlimentoProtocoloPadrao,
)
from sme_sigpae_api.dieta_especial.utils import log_create, log_update
from sme_sigpae_api.produto.api.serializers import serializers as ser
from sme_sigpae_api.produto.models import Produto
from sme_sigpae_api.terceirizada.models import Edital


class SubstituicaoCreateSerializer(serializers.ModelSerializer):
    substitutos = ser.SubstitutosSerializer(many=True)

    class Meta:
        model = SubstituicaoAlimento
        fields = "__all__"


class SubstituicaoProtocoloPadraoCreateSerializer(serializers.ModelSerializer):
    substitutos = ser.SubstitutosSerializer(many=True)

    class Meta:
        model = SubstituicaoAlimentoProtocoloPadrao
        exclude = ("protocolo_padrao",)


class SubstituicaoAutorizarSerializer(serializers.ModelSerializer):
    substitutos = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=Produto.objects.all(), many=True
    )
    alimentos_substitutos = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=Alimento.objects.all(), many=True
    )

    class Meta:
        model = SubstituicaoAlimento
        fields = "__all__"


class ProtocoloPadraoDietaEspecialSerializerCreate(serializers.ModelSerializer):
    substituicoes = SubstituicaoProtocoloPadraoCreateSerializer(many=True)
    editais = serializers.ListField(child=serializers.CharField(), write_only=True)

    def create(self, validated_data):  # noqa C901
        substituicoes = validated_data.pop("substituicoes")
        editais = validated_data.pop("editais")
        nome_protocolo = remove_multiplos_espacos(
            validated_data["nome_protocolo"]
        ).upper()
        protocolos = Edital.objects.check_editais_already_has_nome_protocolo(
            editais, nome_protocolo
        )
        if protocolos:
            edital_ja_existe_protocolo(protocolos, len(editais))
        validated_data["nome_protocolo"] = nome_protocolo.upper()
        protocolo_padrao = ProtocoloPadraoDietaEspecial.objects.create(**validated_data)
        if editais and len(editais):
            protocolo_padrao.editais.set(Edital.objects.filter(uuid__in=editais))
        for substituicao in substituicoes:
            substitutos = substituicao.pop("substitutos", None)
            substituicao["protocolo_padrao"] = protocolo_padrao
            subst_obj = SubstituicaoAlimentoProtocoloPadrao.objects.create(
                **substituicao
            )
            if substitutos:
                for substituto in substitutos:
                    if isinstance(substituto, Alimento):
                        AlimentoSubstituto.objects.create(
                            substituicao_alimento_protocolo_padrao=subst_obj,
                            alimento=substituto,
                        )
                    if isinstance(substituto, Produto):
                        subst_obj.substitutos.add(substituto)

        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        log_create(protocolo_padrao, user=user)

        return protocolo_padrao

    def update(self, instance, validated_data):  # noqa C901
        new_editais = validated_data.get("editais")
        new_editais = Edital.objects.filter(uuid__in=new_editais)
        editais = validated_data.pop("editais")
        nome_protocolo = validated_data["nome_protocolo"]
        protocolos = Edital.objects.check_editais_already_has_nome_protocolo(
            editais, nome_protocolo
        )
        if nome_protocolo == self.instance.nome_protocolo:
            protocolos = protocolos.exclude(
                uuid__in=list(instance.editais.values_list("uuid", flat=True))
            )
        if protocolos:
            edital_ja_existe_protocolo(protocolos, len(editais))

        substituicoes = validated_data.pop("substituicoes")

        validated_data["nome_protocolo"] = nome_protocolo.upper()
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user

        log_update(
            instance,
            validated_data,
            instance.substituicoes,
            substituicoes,
            new_editais,
            instance.editais,
            user,
        )

        instance.editais.clear()
        if editais and len(editais):
            instance.editais.set(Edital.objects.filter(uuid__in=editais))

        instance.substituicoes.all().delete()
        update_instance_from_dict(instance, validated_data, save=True)

        for substituicao in substituicoes:
            substitutos = substituicao.pop("substitutos", None)
            substituicao["protocolo_padrao"] = instance
            subst_obj = SubstituicaoAlimentoProtocoloPadrao.objects.create(
                **substituicao
            )
            if substitutos:
                for substituto in substitutos:
                    if isinstance(substituto, Alimento):
                        AlimentoSubstituto.objects.create(
                            substituicao_alimento_protocolo_padrao=subst_obj,
                            alimento=substituto,
                        )
                    if isinstance(substituto, Produto):
                        subst_obj.substitutos.add(substituto)
        return instance

    class Meta:
        model = ProtocoloPadraoDietaEspecial
        fields = (
            "uuid",
            "nome_protocolo",
            "status",
            "orientacoes_gerais",
            "criado_em",
            "substituicoes",
            "editais",
        )
