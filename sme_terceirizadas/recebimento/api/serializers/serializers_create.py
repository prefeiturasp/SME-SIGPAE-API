from rest_framework import serializers

from sme_terceirizadas.dados_comuns.fluxo_status import DocumentoDeRecebimentoWorkflow
from sme_terceirizadas.dados_comuns.utils import (
    convert_base64_to_contentfile,
    update_instance_from_dict,
)
from sme_terceirizadas.pre_recebimento.models import FichaTecnicaDoProduto
from sme_terceirizadas.pre_recebimento.models.cronograma import (
    DocumentoDeRecebimento,
    EtapasDoCronograma,
)
from sme_terceirizadas.recebimento.models import (
    ArquivoFichaRecebimento,
    FichaDeRecebimento,
    QuestaoConferencia,
    QuestoesPorProduto,
    VeiculoFichaDeRecebimento,
)


class QuestoesPorProdutoCreateSerializer(serializers.ModelSerializer):
    ficha_tecnica = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=FichaTecnicaDoProduto.objects.all(),
    )
    questoes_primarias = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=QuestaoConferencia.objects.all(),
        many=True,
    )
    questoes_secundarias = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=QuestaoConferencia.objects.all(),
        many=True,
    )

    def create(self, validated_data):
        questoes_primarias = validated_data.pop("questoes_primarias", [])
        questoes_secundarias = validated_data.pop("questoes_secundarias", [])

        instance = super().create(validated_data)
        instance.questoes_primarias.set(questoes_primarias)
        instance.questoes_secundarias.set(questoes_secundarias)

        return instance

    def update(self, instance, validated_data):
        instance.questoes_primarias.clear()
        instance.questoes_secundarias.clear()

        instance.questoes_primarias.set(validated_data.pop("questoes_primarias", []))
        instance.questoes_secundarias.set(
            validated_data.pop("questoes_secundarias", [])
        )

        return instance

    class Meta:
        model = QuestoesPorProduto
        fields = ("ficha_tecnica", "questoes_primarias", "questoes_secundarias")


class VeiculoFichaDeRecebimentoRascunhoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VeiculoFichaDeRecebimento
        exclude = ("id", "ficha_recebimento")


class ArquivoFichaRecebimentoCreateSerializer(serializers.ModelSerializer):
    arquivo = serializers.CharField()

    class Meta:
        model = ArquivoFichaRecebimento
        exclude = ("id", "ficha_recebimento")


class FichaDeRecebimentoRascunhoSerializer(serializers.ModelSerializer):
    etapa = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=EtapasDoCronograma.objects.all(),
    )
    documentos_recebimento = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=DocumentoDeRecebimento.objects.filter(
            status=DocumentoDeRecebimentoWorkflow.APROVADO
        ),
        many=True,
        required=False,
    )
    veiculos = VeiculoFichaDeRecebimentoRascunhoSerializer(
        many=True,
        required=False,
    )
    arquivos = ArquivoFichaRecebimentoCreateSerializer(
        many=True,
        required=False,
    )

    def create(self, validated_data):
        dados_veiculos = validated_data.pop("veiculos", [])
        documentos_recebimento = validated_data.pop("documentos_recebimento", [])
        dados_arquivos = validated_data.pop("arquivos", [])

        instance = FichaDeRecebimento.objects.create(**validated_data)

        instance.documentos_recebimento.set(documentos_recebimento)
        self._criar_veiculos(instance, dados_veiculos)
        self._criar_arquivos(instance, dados_arquivos)

        return instance

    def update(self, instance, validated_data):
        instance.veiculos.all().delete()
        instance.documentos_recebimento.clear()
        instance.arquivos.all().delete()

        dados_veiculos = validated_data.pop("veiculos", [])
        documentos_recebimento = validated_data.pop("documentos_recebimento", [])
        dados_arquivos = validated_data.pop("arquivos", [])

        instance = update_instance_from_dict(instance, validated_data, save=True)

        instance.documentos_recebimento.set(documentos_recebimento)
        self._criar_veiculos(instance, dados_veiculos)
        self._criar_arquivos(instance, dados_arquivos)

        return instance

    def _criar_veiculos(self, instance, dados_veiculos):
        for dados_veiculo in dados_veiculos:
            VeiculoFichaDeRecebimento.objects.create(
                ficha_recebimento=instance,
                **dados_veiculo,
            )

    def _criar_arquivos(self, instance, dados_arquivos):
        for dados_arquivo in dados_arquivos:
            contentfile = convert_base64_to_contentfile(dados_arquivo.get("arquivo"))
            ArquivoFichaRecebimento.objects.create(
                ficha_recebimento=instance,
                arquivo=contentfile,
                nome=dados_arquivo.get("nome"),
            )

    class Meta:
        model = FichaDeRecebimento
        exclude = ("id",)
