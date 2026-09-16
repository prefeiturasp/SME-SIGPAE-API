"""Serializers de criação do módulo de recebimento."""

from rest_framework import serializers

from src.dados_comuns.fluxo_status import DocumentoDeRecebimentoWorkflow
from src.pre_recebimento.cronograma_entrega.models import (
    EtapasDoCronograma,
)
from src.pre_recebimento.documento_recebimento.models import (
    DocumentoDeRecebimento,
)
from src.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto
from src.recebimento.api.helpers import atualizar_ficha, criar_ficha
from src.recebimento.models import (
    ArquivoFichaRecebimento,
    DocumentoFichaDeRecebimento,
    FichaDeRecebimento,
    OcorrenciaFichaRecebimento,
    QuestaoConferencia,
    QuestaoFichaRecebimento,
    QuestoesPorProduto,
    ReposicaoCronogramaFichaRecebimento,
    VeiculoFichaDeRecebimento,
)


class QuestoesPorProdutoCreateSerializer(serializers.ModelSerializer):
    """Serializer de criação/atualização das questões por produto.

    Recebe a ``ficha_tecnica`` (uuid) e as listas de questões primárias e
    secundárias (uuids). Na atualização, as questões anteriores são
    substituídas pelas novas.
    """

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
    """Serializer do veículo no rascunho da ficha de recebimento."""

    class Meta:
        model = VeiculoFichaDeRecebimento
        exclude = ("id", "ficha_recebimento")


class QuestaoFichaRecebimentoCreateSerializer(serializers.ModelSerializer):
    """Serializer de criação da resposta a uma questão na ficha.

    Recebe a ``questao_conferencia`` (uuid) e a ``resposta``.
    """

    questao_conferencia = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=QuestaoConferencia.objects.all(),
        many=False,
    )

    class Meta:
        model = QuestaoFichaRecebimento
        exclude = ("id", "ficha_recebimento")


class ArquivoFichaRecebimentoCreateSerializer(serializers.ModelSerializer):
    """Serializer de criação do arquivo da ficha de recebimento.

    Recebe o ``arquivo`` em base64 e o ``nome``.
    """

    arquivo = serializers.CharField()

    class Meta:
        model = ArquivoFichaRecebimento
        exclude = ("id", "ficha_recebimento")


class DocumentoFichaDeRecebimentoCreateSerializer(serializers.ModelSerializer):
    """Serializer do documento de recebimento na ficha.

    Vincula um documento de recebimento (apenas com status ``APROVADO``) à
    ficha, com a ``quantidade_recebida`` (obrigatória e maior que zero).
    """

    documento_recebimento = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=DocumentoDeRecebimento.objects.filter(
            status=DocumentoDeRecebimentoWorkflow.APROVADO
        ),
    )
    quantidade_recebida = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Quantidade recebida deve ser maior que zero",
    )

    class Meta:
        model = DocumentoFichaDeRecebimento
        fields = ("documento_recebimento", "quantidade_recebida")


class OcorrenciaFichaRecebimentoCreateSerializer(serializers.ModelSerializer):
    """Serializer de criação da ocorrência da ficha de recebimento.

    Quando ``rascunho`` é ``True``, as validações de tipo/relação são
    ignoradas. Caso contrário, valida: (1) ``quantidade`` obrigatória para
    os tipos diferentes de ``OUTROS_MOTIVOS``; (2) tipo ``FALTA`` com
    relação obrigatória ``CRONOGRAMA`` ou ``NOTA_FISCAL``; (3) tipo
    ``RECUSA`` com relação obrigatória ``TOTAL`` ou ``PARCIAL`` e número da
    nota obrigatório; (4) tipo ``OUTROS_MOTIVOS`` zera ``relacao`` e
    ``numero_nota``.
    """

    def __init__(self, *args, **kwargs):
        """Inicializa o serializer recebendo a flag ``rascunho``."""
        self.rascunho = kwargs.pop("rascunho", False)
        super().__init__(*args, **kwargs)

    class Meta:
        model = OcorrenciaFichaRecebimento
        exclude = ("id", "ficha_recebimento")

    def _validate_quantidade(self, tipo, quantidade):
        """Valida a quantidade para tipos diferentes de OUTROS_MOTIVOS."""
        if tipo != OcorrenciaFichaRecebimento.TIPO_OUTROS and not quantidade:
            raise serializers.ValidationError(
                {"quantidade": "Este campo é obrigatório para o tipo selecionado."}
            )

    def _validate_falta(self, relacao):
        """Valida a relação para o tipo FALTA."""
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
        """Valida a relação e o número da nota para o tipo RECUSA."""
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
        """Aplica as validações por tipo de ocorrência (fora do rascunho)."""
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
    """Serializer de criação/atualização da ficha de recebimento.

    Exige a ``etapa`` (uuid), a ``data_entrega``, os ``documentos_recebimento``
    (apenas ``APROVADO``), os indicadores de conformidade, os pesos das
    embalagens primárias, os ``veiculos``, o ``sistema_vedacao_embalagem_secundaria``
    e as ``questoes`` obrigatórias. Na criação e na atualização de fichas em
    ``RASCUNHO``, executa ``inicia_fluxo`` (RASCUNHO → ASSINADA). Os campos
    de peso são normalizados de texto (``1.234,56`` → ``1234.56``).
    """

    etapa = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=EtapasDoCronograma.objects.all(),
    )
    data_entrega = serializers.DateField(required=True)
    documentos_recebimento = DocumentoFichaDeRecebimentoCreateSerializer(
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
    numero_paletes = serializers.IntegerField(required=True)
    peso_embalagem_primaria_1 = serializers.FloatField(required=True)
    peso_embalagem_primaria_2 = serializers.FloatField(required=True)
    peso_embalagem_primaria_3 = serializers.FloatField(required=True)
    peso_embalagem_primaria_4 = serializers.FloatField(required=True)
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
    houve_ocorrencia = serializers.BooleanField(required=True)
    observacoes_conferencia = serializers.CharField(required=False, allow_blank=True)
    ocorrencias = OcorrenciaFichaRecebimentoCreateSerializer(
        many=True, required=False, rascunho=False
    )
    reposicao_cronograma = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=ReposicaoCronogramaFichaRecebimento.objects.all(),
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
            "houve_ocorrencia",
            "ocorrencias",
            "reposicao_cronograma",
        ]

    def validate(self, data):
        """Aplica as validações de divergência, veículos e questões."""
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
        """Cria a ficha de recebimento e inicia o fluxo (ASSINADA)."""
        ficha = criar_ficha(validated_data)
        user = self.context["request"].user
        ficha.inicia_fluxo(user=user)
        return ficha

    def update(self, instance, validated_data):
        """Atualiza a ficha, iniciando o fluxo quando ela está em rascunho."""
        eh_rascunho = (
            hasattr(instance, "status")
            and instance.status == instance.workflow_class.RASCUNHO
        )

        ficha_atualizada = atualizar_ficha(instance, validated_data)

        if eh_rascunho:
            user = self.context["request"].user
            ficha_atualizada.inicia_fluxo(user=user)

        return ficha_atualizada

    def to_internal_value(self, data):
        """Normaliza os campos de peso de texto (vírgula) para decimal."""
        peso_fields = [
            "numero_paletes",
            "peso_embalagem_primaria_1",
            "peso_embalagem_primaria_2",
            "peso_embalagem_primaria_3",
            "peso_embalagem_primaria_4",
        ]

        for field in peso_fields:
            if field in data and isinstance(data[field], str):
                data[field] = data[field].replace(".", "").replace(",", ".")

        return super().to_internal_value(data)


class FichaDeRecebimentoCreateSerializerSaldoZero(FichaDeRecebimentoCreateSerializer):
    """
    Serializer para criação de Ficha de Recebimento que ignora os campos
    que no frontend são validados com requiredSaldoTotalZero.
    Herda de FichaDeRecebimentoCreateSerializer mas remove os campos específicos.
    """

    class Meta:
        model = FichaDeRecebimento
        fields = [
            "etapa",
            "data_entrega",
            "documentos_recebimento",
            "observacao",
            "arquivos",
            "observacoes_conferencia",
            "houve_ocorrencia",
            "ocorrencias",
            "reposicao_cronograma",
        ]

    def to_internal_value(self, data):
        """Limpa os campos de saldo total zero na atualização."""
        result = super().to_internal_value(data)

        if self.instance is not None:
            campos_para_limpar = [
                "lote_fabricante_de_acordo",
                "data_fabricacao_de_acordo",
                "data_validade_de_acordo",
                "numero_lote_armazenagem",
                "numero_paletes",
                "peso_embalagem_primaria_1",
                "peso_embalagem_primaria_2",
                "peso_embalagem_primaria_3",
                "peso_embalagem_primaria_4",
                "sistema_vedacao_embalagem_secundaria",
            ]

            for campo in campos_para_limpar:
                if campo not in result:
                    result[campo] = None

        return result

    def validate(self, data):
        """Valida os dados sem as regras de saldo total zero."""
        data = super(FichaDeRecebimentoCreateSerializer, self).validate(data)

        return data


class FichaDeRecebimentoRascunhoSerializer(serializers.ModelSerializer):
    """Serializer de criação/atualização do rascunho da ficha de recebimento.

    Diferente do serializer de criação assinada, não exige os campos de
    conferência (documentos, veículos, questões e ocorrências são
    opcionais) e não inicia o fluxo: a ficha permanece em ``RASCUNHO``. Ao
    atualizar uma ficha ``ASSINADA``, executa ``volta_para_rascunho``.
    """

    etapa = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=EtapasDoCronograma.objects.all(),
    )
    documentos_recebimento = DocumentoFichaDeRecebimentoCreateSerializer(
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
    reposicao_cronograma = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=ReposicaoCronogramaFichaRecebimento.objects.all(),
    )

    def create(self, validated_data):
        """Cria a ficha de recebimento rascunho."""
        return criar_ficha(validated_data)

    def update(self, instance, validated_data):
        """Atualiza a ficha, voltando para rascunho quando está assinada."""
        ficha_atualizada = atualizar_ficha(instance, validated_data)

        if (
            hasattr(instance, "status")
            and instance.status == instance.workflow_class.ASSINADA
        ):
            user = self.context["request"].user
            ficha_atualizada.volta_para_rascunho(user=user)

        return ficha_atualizada

    def to_internal_value(self, data):
        """Normaliza os campos de peso de texto (vírgula) para decimal."""
        peso_fields = [
            "numero_paletes",
            "peso_embalagem_primaria_1",
            "peso_embalagem_primaria_2",
            "peso_embalagem_primaria_3",
            "peso_embalagem_primaria_4",
        ]

        for field in peso_fields:
            if field in data and isinstance(data[field], str):
                data[field] = data[field].replace(".", "").replace(",", ".")

        return super().to_internal_value(data)

    class Meta:
        model = FichaDeRecebimento
        exclude = ("id",)


class FichaDeRecebimentoReposicaoSerializer(serializers.ModelSerializer):
    """Serializer de criação/atualização da ficha no fluxo de reposição.

    Exige ``etapa``, ``data_entrega``, ``observacao`` e
    ``reposicao_cronograma`` (uuid). Os ``documentos_recebimento`` são
    filtrados para o status ``APROVADO``. Na criação e na atualização de
    fichas em ``RASCUNHO``, executa ``inicia_fluxo`` (RASCUNHO → ASSINADA).
    """

    etapa = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=EtapasDoCronograma.objects.all(),
    )
    data_entrega = serializers.DateField(required=True)
    ocorrencias = OcorrenciaFichaRecebimentoCreateSerializer(
        many=True, required=False, rascunho=True
    )
    observacao = serializers.CharField(required=True, allow_blank=True)
    arquivos = ArquivoFichaRecebimentoCreateSerializer(
        many=True,
        required=False,
    )
    reposicao_cronograma = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=ReposicaoCronogramaFichaRecebimento.objects.all(),
    )
    documentos_recebimento = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=DocumentoDeRecebimento.objects.filter(
            status=DocumentoDeRecebimentoWorkflow.APROVADO
        ),
        many=True,
        required=False,
    )

    def create(self, validated_data):
        """Cria a ficha de reposição e inicia o fluxo (ASSINADA)."""
        ficha = criar_ficha(validated_data)
        user = self.context["request"].user
        ficha.inicia_fluxo(user=user)
        return ficha

    def update(self, instance, validated_data):
        """Atualiza a ficha de reposição, iniciando o fluxo em rascunho."""
        eh_rascunho = (
            hasattr(instance, "status")
            and instance.status == instance.workflow_class.RASCUNHO
        )

        ficha_atualizada = atualizar_ficha(instance, validated_data)

        if eh_rascunho:
            user = self.context["request"].user
            ficha_atualizada.inicia_fluxo(user=user)

        return ficha_atualizada

    def to_representation(self, instance):
        """Retorna a representação padrão do serializer."""
        representation = super().to_representation(instance)
        return representation

    def to_internal_value(self, data):
        """Normaliza os campos de peso de texto (vírgula) para decimal."""
        peso_fields = [
            "numero_paletes",
            "peso_embalagem_primaria_1",
            "peso_embalagem_primaria_2",
            "peso_embalagem_primaria_3",
            "peso_embalagem_primaria_4",
        ]

        for field in peso_fields:
            if field in data and isinstance(data[field], str):
                data[field] = data[field].replace(".", "").replace(",", ".")

        return super().to_internal_value(data)

    class Meta:
        model = FichaDeRecebimento
        exclude = ("id",)
