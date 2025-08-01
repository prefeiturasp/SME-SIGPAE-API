from rest_framework import serializers

from sme_sigpae_api.dados_comuns.fluxo_status import DocumentoDeRecebimentoWorkflow
from sme_sigpae_api.dados_comuns.utils import (
    convert_base64_to_contentfile,
    update_instance_from_dict,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import (
    EtapasDoCronograma,
)
from sme_sigpae_api.pre_recebimento.documento_recebimento.models import (
    DocumentoDeRecebimento,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto
from sme_sigpae_api.recebimento.models import (
    ArquivoFichaRecebimento,
    FichaDeRecebimento,
    OcorrenciaFichaRecebimento,
    QuestaoConferencia,
    QuestaoFichaRecebimento,
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


class QuestaoFichaRecebimentoCreateSerializer(serializers.ModelSerializer):
    questao_conferencia = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=QuestaoConferencia.objects.all(),
        many=False,
    )

    class Meta:
        model = QuestaoFichaRecebimento
        exclude = ("id", "ficha_recebimento")


class ArquivoFichaRecebimentoCreateSerializer(serializers.ModelSerializer):
    arquivo = serializers.CharField()

    class Meta:
        model = ArquivoFichaRecebimento
        exclude = ("id", "ficha_recebimento")


class OcorrenciaFichaRecebimentoCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        self.rascunho = kwargs.pop('rascunho', False)
        super().__init__(*args, **kwargs)

    class Meta:
        model = OcorrenciaFichaRecebimento
        exclude = ("id", "ficha_recebimento")

    def _validate_quantidade(self, tipo, quantidade):
        if tipo != OcorrenciaFichaRecebimento.TIPO_OUTROS and not quantidade:
            raise serializers.ValidationError({
                'quantidade': 'Este campo é obrigatório para o tipo selecionado.'
            })

    def _validate_falta(self, relacao):
        valid_relations = [
            OcorrenciaFichaRecebimento.RELACAO_CRONOGRAMA,
            OcorrenciaFichaRecebimento.RELACAO_NOTA_FISCAL
        ]
        if not relacao or relacao not in valid_relations:
            raise serializers.ValidationError({
                'relacao': 'Para o tipo FALTA, a relação deve ser CRONOGRAMA ou NOTA_FISCAL'
            })

    def _validate_recusa(self, relacao, numero_nota):
        valid_relations = [
            OcorrenciaFichaRecebimento.RELACAO_TOTAL,
            OcorrenciaFichaRecebimento.RELACAO_PARCIAL
        ]
        if not relacao or relacao not in valid_relations:
            raise serializers.ValidationError({
                'relacao': 'Para o tipo RECUSA, a relação deve ser TOTAL ou PARCIAL'
            })
        if not numero_nota:
            raise serializers.ValidationError({
                'numero_nota': 'Para o tipo RECUSA, o número da nota é obrigatório'
            })

    def validate(self, data):
        if getattr(self, 'rascunho', False):
            return data

        tipo = data.get('tipo')
        relacao = data.get('relacao')
        numero_nota = data.get('numero_nota')
        quantidade = data.get('quantidade')

        self._validate_quantidade(tipo, quantidade)

        if tipo == OcorrenciaFichaRecebimento.TIPO_FALTA:
            self._validate_falta(relacao)
        elif tipo == OcorrenciaFichaRecebimento.TIPO_RECUSA:
            self._validate_recusa(relacao, numero_nota)
        else:  # OUTROS_MOTIVOS
            data['relacao'] = None
            data['numero_nota'] = None

        return data


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
    questoes = QuestaoFichaRecebimentoCreateSerializer(
        many=True,
        required=False,
    )
    ocorrencias = OcorrenciaFichaRecebimentoCreateSerializer(
        many=True,
        required=False,
        rascunho=True
    )

    def create(self, validated_data):
        dados_veiculos = validated_data.pop("veiculos", [])
        documentos_recebimento = validated_data.pop("documentos_recebimento", [])
        dados_arquivos = validated_data.pop("arquivos", [])
        dados_questoes = validated_data.pop("questoes", [])
        dados_ocorrencias = validated_data.pop("ocorrencias", [])

        instance = FichaDeRecebimento.objects.create(**validated_data)

        instance.documentos_recebimento.set(documentos_recebimento)
        self._criar_veiculos(instance, dados_veiculos)
        self._criar_arquivos(instance, dados_arquivos)
        self._criar_questoes(instance, dados_questoes)
        self._criar_ocorrencias(instance, dados_ocorrencias)
        return instance

    def update(self, instance, validated_data):
        instance.veiculos.all().delete()
        instance.documentos_recebimento.clear()
        instance.arquivos.all().delete()
        instance.questoes_conferencia.through.objects.filter(
            ficha_recebimento=instance
        ).delete()
        instance.ocorrencias.all().delete()

        dados_veiculos = validated_data.pop("veiculos", [])
        documentos_recebimento = validated_data.pop("documentos_recebimento", [])
        dados_arquivos = validated_data.pop("arquivos", [])
        dados_questoes = validated_data.pop("questoes", [])
        dados_ocorrencias = validated_data.pop("ocorrencias", [])

        instance = update_instance_from_dict(instance, validated_data, save=True)

        instance.documentos_recebimento.set(documentos_recebimento)
        self._criar_veiculos(instance, dados_veiculos)
        self._criar_arquivos(instance, dados_arquivos)
        self._criar_questoes(instance, dados_questoes)
        self._criar_ocorrencias(instance, dados_ocorrencias)
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

    def _criar_questoes(self, instance, dados_questoes):
        for dados_questao in dados_questoes:
            QuestaoFichaRecebimento.objects.create(
                ficha_recebimento=instance,
                **dados_questao,
            )

    def _criar_ocorrencias(self, instance, dados_ocorrencias):
        recusa_count = sum(
            1 for ocorrencia in dados_ocorrencias
            if ocorrencia.get('tipo') == OcorrenciaFichaRecebimento.TIPO_RECUSA
        )

        if recusa_count > 1:
            raise serializers.ValidationError({
                'ocorrencias': 'Apenas uma ocorrência do tipo RECUSA é permitida por ficha de recebimento.'
            })

        for dados_ocorrencia in dados_ocorrencias:
            OcorrenciaFichaRecebimento.objects.create(
                ficha_recebimento=instance,
                **dados_ocorrencia,
            )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['ocorrencias'] = OcorrenciaFichaRecebimentoCreateSerializer(
            instance.ocorrencias.all(), many=True
        ).data
        return representation

    class Meta:
        model = FichaDeRecebimento
        exclude = ("id",)
