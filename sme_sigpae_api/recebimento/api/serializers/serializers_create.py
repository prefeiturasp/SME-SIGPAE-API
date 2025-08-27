from rest_framework import serializers

from sme_sigpae_api.dados_comuns.fluxo_status import DocumentoDeRecebimentoWorkflow
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import (
    EtapasDoCronograma,
)
from sme_sigpae_api.pre_recebimento.documento_recebimento.models import (
    DocumentoDeRecebimento,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto
from sme_sigpae_api.recebimento.api.helpers import atualizar_ficha, criar_ficha
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
        self.rascunho = kwargs.pop("rascunho", False)
        super().__init__(*args, **kwargs)

    class Meta:
        model = OcorrenciaFichaRecebimento
        exclude = ("id", "ficha_recebimento")

    def _validate_quantidade(self, tipo, quantidade):
        if tipo != OcorrenciaFichaRecebimento.TIPO_OUTROS and not quantidade:
            raise serializers.ValidationError(
                {"quantidade": "Este campo é obrigatório para o tipo selecionado."}
            )

    def _validate_falta(self, relacao):
        valid_relations = [
            OcorrenciaFichaRecebimento.RELACAO_CRONOGRAMA,
            OcorrenciaFichaRecebimento.RELACAO_NOTA_FISCAL,
        ]
        if not relacao or relacao not in valid_relations:
            raise serializers.ValidationError(
                {
                    "relacao": "Para o tipo FALTA, a relação deve ser CRONOGRAMA ou NOTA_FISCAL"
                }
            )

    def _validate_recusa(self, relacao, numero_nota):
        valid_relations = [
            OcorrenciaFichaRecebimento.RELACAO_TOTAL,
            OcorrenciaFichaRecebimento.RELACAO_PARCIAL,
        ]
        if not relacao or relacao not in valid_relations:
            raise serializers.ValidationError(
                {"relacao": "Para o tipo RECUSA, a relação deve ser TOTAL ou PARCIAL"}
            )
        if not numero_nota:
            raise serializers.ValidationError(
                {"numero_nota": "Para o tipo RECUSA, o número da nota é obrigatório"}
            )

    def validate(self, data):
        if getattr(self, "rascunho", False):
            return data

        tipo = data.get("tipo")
        relacao = data.get("relacao")
        numero_nota = data.get("numero_nota")
        quantidade = data.get("quantidade")

        self._validate_quantidade(tipo, quantidade)

        if tipo == OcorrenciaFichaRecebimento.TIPO_FALTA:
            self._validate_falta(relacao)
        elif tipo == OcorrenciaFichaRecebimento.TIPO_RECUSA:
            self._validate_recusa(relacao, numero_nota)
        else:  # OUTROS_MOTIVOS
            data["relacao"] = None
            data["numero_nota"] = None

        return data


class FichaDeRecebimentoCreateSerializer(serializers.ModelSerializer):
    etapa = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=EtapasDoCronograma.objects.all(),
    )
    data_entrega = serializers.DateField(required=True)
    documentos_recebimento = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=DocumentoDeRecebimento.objects.filter(
            status=DocumentoDeRecebimentoWorkflow.APROVADO
        ),
        many=True,
        required=True,
    )
    lote_fabricante_de_acordo = serializers.BooleanField(required=True)
    lote_fabricante_divergencia = serializers.CharField(
        required=False, allow_blank=True
    )
    data_fabricacao_de_acordo = serializers.BooleanField(required=True)
    data_fabricacao_divergencia = serializers.CharField(
        required=False, allow_blank=True
    )
    data_validade_de_acordo = serializers.BooleanField(required=True)
    data_validade_divergencia = serializers.CharField(required=False, allow_blank=True)
    numero_lote_armazenagem = serializers.CharField(required=True)
    numero_paletes = serializers.CharField(required=True)
    peso_embalagem_primaria_1 = serializers.CharField(required=True)
    peso_embalagem_primaria_2 = serializers.CharField(required=True)
    peso_embalagem_primaria_3 = serializers.CharField(required=True)
    peso_embalagem_primaria_4 = serializers.CharField(required=True)
    veiculos = serializers.ListField(child=serializers.DictField(), required=True)
    sistema_vedacao_embalagem_secundaria = serializers.CharField(required=True)
    observacao = serializers.CharField(required=False, allow_blank=True)
    arquivos = ArquivoFichaRecebimentoCreateSerializer(
        many=True,
        required=False,
    )
    questoes = QuestaoFichaRecebimentoCreateSerializer(
        many=True,
        required=True,
    )
    observacoes_conferencia = serializers.CharField(required=False, allow_blank=True)
    ocorrencias = OcorrenciaFichaRecebimentoCreateSerializer(
        many=True, required=False, rascunho=False
    )

    class Meta:
        model = FichaDeRecebimento
        fields = [
            "etapa",
            "data_entrega",
            "documentos_recebimento",
            "lote_fabricante_de_acordo",
            "lote_fabricante_divergencia",
            "data_fabricacao_de_acordo",
            "data_fabricacao_divergencia",
            "data_validade_de_acordo",
            "data_validade_divergencia",
            "numero_lote_armazenagem",
            "numero_paletes",
            "peso_embalagem_primaria_1",
            "peso_embalagem_primaria_2",
            "peso_embalagem_primaria_3",
            "peso_embalagem_primaria_4",
            "veiculos",
            "sistema_vedacao_embalagem_secundaria",
            "observacao",
            "arquivos",
            "questoes",
            "observacoes_conferencia",
            "ocorrencias",
        ]

    def validate(self, data):
        data = super().validate(data)

        self._validar_campos_divergencia(data)
        self._validar_veiculos(data)
        self._validar_questoes(data)

        return data

    def _validar_campos_divergencia(self, data):
        """Valida campos de divergência quando os respectivos 'de acordo' são False"""
        campos_divergencia = [
            (
                "lote_fabricante_de_acordo",
                "lote_fabricante_divergencia",
                "Campo obrigatório quando o lote do fabricante não está de acordo.",
            ),
            (
                "data_fabricacao_de_acordo",
                "data_fabricacao_divergencia",
                "Campo obrigatório quando a data de fabricação não está de acordo.",
            ),
            (
                "data_validade_de_acordo",
                "data_validade_divergencia",
                "Campo obrigatório quando a data de validade não está de acordo.",
            ),
        ]

        for campo_acordo, campo_divergencia, mensagem in campos_divergencia:
            if not data.get(campo_acordo) and not data.get(campo_divergencia):
                raise serializers.ValidationError({campo_divergencia: mensagem})

    def _validar_veiculos(self, data):
        """Valida se há pelo menos um veículo"""
        if not data.get("veiculos", []):
            raise serializers.ValidationError(
                {"veiculos": "É necessário informar pelo menos um veículo."}
            )

    def _validar_questoes(self, data):
        """Valida as questões obrigatórias associadas ao produto da ficha"""
        from django.db.models import Q

        questoes = data.get("questoes", [])
        if not questoes:
            raise serializers.ValidationError(
                {"questoes": "É necessário responder a todas as questões obrigatórias."}
            )

        ficha_tecnica = data["etapa"].cronograma.ficha_tecnica

        qp = QuestoesPorProduto.objects.get(ficha_tecnica=ficha_tecnica)

        questoes_respondidas = [
            q["questao_conferencia"].uuid
            for q in questoes
            if q.get("resposta") is not None and "questao_conferencia" in q
        ]

        questoes_obrigatorias = QuestaoConferencia.objects.filter(
            Q(questoes_primarias=qp) | Q(questoes_secundarias=qp),
            pergunta_obrigatoria=True,
        ).exclude(uuid__in=questoes_respondidas)

        if questoes_obrigatorias.exists():
            faltantes = list(questoes_obrigatorias.values_list("questao", flat=True))
            raise serializers.ValidationError(
                {
                    "questoes": f'Questões obrigatórias não respondidas: {", ".join(faltantes)}'
                }
            )

    def create(self, validated_data):
        ficha = criar_ficha(validated_data)
        user = self.context["request"].user
        ficha.inicia_fluxo(user=user)
        return ficha

    def update(self, instance, validated_data):
        eh_rascunho = (
            hasattr(instance, "status")
            and instance.status == instance.workflow_class.RASCUNHO
        )

        ficha_atualizada = atualizar_ficha(instance, validated_data)

        if eh_rascunho:
            user = self.context["request"].user
            ficha_atualizada.inicia_fluxo(user=user)

        return ficha_atualizada


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
        many=True, required=False, rascunho=True
    )

    def create(self, validated_data):
        return criar_ficha(validated_data)

    def update(self, instance, validated_data):
        return atualizar_ficha(instance, validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["ocorrencias"] = OcorrenciaFichaRecebimentoCreateSerializer(
            instance.ocorrencias.all(), many=True
        ).data
        return representation

    class Meta:
        model = FichaDeRecebimento
        exclude = ("id",)
