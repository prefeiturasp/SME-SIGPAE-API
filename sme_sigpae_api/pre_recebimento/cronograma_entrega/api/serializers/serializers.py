import datetime
from collections import OrderedDict

from rest_framework import serializers

from sme_sigpae_api.dados_comuns.fluxo_status import DocumentoDeRecebimentoWorkflow
from sme_sigpae_api.dados_comuns.utils import numero_com_agrupador_de_milhar_e_decimal
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import (
    Cronograma,
    EtapasDoCronograma,
    ProgramacaoDoRecebimentoDoCronograma,
    SolicitacaoAlteracaoCronograma,
    UnidadeMedida,
)
from sme_sigpae_api.pre_recebimento.documento_recebimento.api.serializers.serializers import (
    DocRecebimentoFichaDeRecebimentoSerializer,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.serializers.serializers import (
    FichaTecnicaCronogramaSerializer,
)
from sme_sigpae_api.pre_recebimento.qualidade.models import (
    TipoEmbalagemQld,
)
from sme_sigpae_api.terceirizada.api.serializers.serializers import (
    ContratoSimplesSerializer,
    DistribuidorComEnderecoSimplesSerializer,
    DistribuidorSimplesSerializer,
    TerceirizadaLookUpSerializer,
)

from .....dados_comuns.api.serializers import (
    LogSolicitacoesUsuarioSerializer,
)


class ProgramacaoDoRecebimentoDoCronogramaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramacaoDoRecebimentoDoCronograma
        fields = (
            "uuid",
            "data_programada",
            "tipo_carga",
        )


class EtapasDoCronogramaSerializer(serializers.ModelSerializer):
    data_programada = serializers.SerializerMethodField()
    etapa = serializers.SerializerMethodField()

    def get_data_programada(self, obj):
        return obj.data_programada.strftime("%d/%m/%Y") if obj.data_programada else None

    def get_etapa(self, obj):
        return f"Etapa {obj.etapa}" if obj.etapa is not None else None

    class Meta:
        model = EtapasDoCronograma
        fields = (
            "uuid",
            "numero_empenho",
            "qtd_total_empenho",
            "etapa",
            "parte",
            "data_programada",
            "quantidade",
            "total_embalagens",
        )


class EtapasDoCronogramaCalendarioSerializer(serializers.ModelSerializer):
    nome_produto = serializers.SerializerMethodField()
    uuid_cronograma = serializers.SerializerMethodField()
    numero_cronograma = serializers.SerializerMethodField()
    nome_fornecedor = serializers.SerializerMethodField()
    data_programada = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    unidade_medida = serializers.SerializerMethodField()
    etapa = serializers.SerializerMethodField()

    def get_etapa(self, obj):
        return f"Etapa {obj.etapa}" if obj.etapa is not None else None

    def get_nome_produto(self, obj):
        try:
            return obj.cronograma.ficha_tecnica.produto.nome
        except AttributeError:
            return None

    def get_uuid_cronograma(self, obj):
        return obj.cronograma.uuid if obj.cronograma else None

    def get_numero_cronograma(self, obj):
        return str(obj.cronograma.numero) if obj.cronograma else None

    def get_nome_fornecedor(self, obj):
        return obj.cronograma.empresa.nome_fantasia if obj.cronograma.empresa else None

    def get_data_programada(self, obj):
        return obj.data_programada.strftime("%d/%m/%Y") if obj.data_programada else None

    def get_status(self, obj):
        return obj.cronograma.get_status_display() if obj.cronograma else None

    def get_unidade_medida(self, obj):
        return obj.cronograma.unidade_medida.abreviacao if obj.cronograma else None

    class Meta:
        model = EtapasDoCronograma
        fields = (
            "uuid",
            "nome_produto",
            "uuid_cronograma",
            "numero_cronograma",
            "nome_fornecedor",
            "data_programada",
            "numero_empenho",
            "etapa",
            "parte",
            "quantidade",
            "status",
            "unidade_medida",
        )


class SolicitacaoAlteracaoCronogramaSerializer(serializers.ModelSerializer):
    fornecedor = serializers.CharField(source="cronograma.empresa")
    cronograma = serializers.CharField(source="cronograma.numero")
    status = serializers.CharField(source="get_status_display")

    class Meta:
        model = SolicitacaoAlteracaoCronograma
        fields = (
            "uuid",
            "numero_solicitacao",
            "fornecedor",
            "status",
            "criado_em",
            "cronograma",
        )


class TipoEmbalagemQldSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEmbalagemQld
        exclude = ("id",)


class TipoEmbalagemQldSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEmbalagemQld
        fields = ("uuid", "nome", "abreviacao")


class UnidadeMedidaSerialzer(serializers.ModelSerializer):
    class Meta:
        model = UnidadeMedida
        fields = ("uuid", "nome", "abreviacao", "criado_em")
        read_only_fields = ("uuid", "nome", "abreviacao", "criado_em")


class CronogramaSerializer(serializers.ModelSerializer):
    etapas = EtapasDoCronogramaSerializer(many=True)
    programacoes_de_recebimento = ProgramacaoDoRecebimentoDoCronogramaSerializer(
        many=True
    )
    armazem = DistribuidorSimplesSerializer()
    status = serializers.CharField(source="get_status_display")
    empresa = TerceirizadaLookUpSerializer()
    contrato = ContratoSimplesSerializer()
    unidade_medida = UnidadeMedidaSerialzer()
    ficha_tecnica = FichaTecnicaCronogramaSerializer()
    tipo_embalagem_secundaria = TipoEmbalagemQldSimplesSerializer()

    class Meta:
        model = Cronograma
        fields = (
            "uuid",
            "numero",
            "status",
            "criado_em",
            "alterado_em",
            "contrato",
            "empresa",
            "qtd_total_programada",
            "unidade_medida",
            "armazem",
            "etapas",
            "programacoes_de_recebimento",
            "ficha_tecnica",
            "tipo_embalagem_secundaria",
            "custo_unitario_produto",
            "observacoes",
        )


class CronogramaComLogSerializer(serializers.ModelSerializer):
    etapas = EtapasDoCronogramaSerializer(many=True)
    programacoes_de_recebimento = ProgramacaoDoRecebimentoDoCronogramaSerializer(
        many=True
    )
    armazem = DistribuidorComEnderecoSimplesSerializer()
    status = serializers.CharField(source="get_status_display")
    empresa = TerceirizadaLookUpSerializer()
    contrato = ContratoSimplesSerializer()
    unidade_medida = UnidadeMedidaSerialzer()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    ficha_tecnica = FichaTecnicaCronogramaSerializer()
    tipo_embalagem_secundaria = TipoEmbalagemQldSimplesSerializer()

    class Meta:
        model = Cronograma
        fields = (
            "uuid",
            "numero",
            "status",
            "criado_em",
            "alterado_em",
            "contrato",
            "empresa",
            "qtd_total_programada",
            "unidade_medida",
            "armazem",
            "etapas",
            "programacoes_de_recebimento",
            "ficha_tecnica",
            "tipo_embalagem_secundaria",
            "custo_unitario_produto",
            "logs",
            "observacoes",
        )


class SolicitacaoAlteracaoCronogramaCompletoSerializer(serializers.ModelSerializer):
    fornecedor = serializers.CharField(source="cronograma.empresa")
    cronograma = CronogramaSerializer()
    status = serializers.CharField(source="get_status_display")
    etapas_antigas = EtapasDoCronogramaSerializer(many=True)
    etapas_novas = EtapasDoCronogramaSerializer(many=True)
    logs = LogSolicitacoesUsuarioSerializer(many=True)

    class Meta:
        model = SolicitacaoAlteracaoCronograma
        fields = (
            "uuid",
            "numero_solicitacao",
            "fornecedor",
            "status",
            "criado_em",
            "cronograma",
            "etapas_antigas",
            "etapas_novas",
            "justificativa",
            "logs",
        )


class CronogramaRascunhosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cronograma
        fields = ("uuid", "numero", "alterado_em")


class CronogramaSimplesSerializer(serializers.ModelSerializer):
    pregao_chamada_publica = serializers.SerializerMethodField()
    nome_produto = serializers.SerializerMethodField()

    def get_pregao_chamada_publica(self, obj):
        return obj.contrato.pregao_chamada_publica if obj.contrato else None

    def get_nome_produto(self, obj):
        return obj.ficha_tecnica.produto.nome if obj.ficha_tecnica else None

    class Meta:
        model = Cronograma
        fields = ("uuid", "numero", "pregao_chamada_publica", "nome_produto")


class EtapasDoCronogramaFichaDeRecebimentoSerializer(serializers.ModelSerializer):
    qtd_total_empenho = serializers.SerializerMethodField()
    data_programada = serializers.SerializerMethodField()
    quantidade = serializers.SerializerMethodField()
    total_embalagens = serializers.SerializerMethodField()
    desvinculada_recebimento = serializers.SerializerMethodField()
    etapa = serializers.SerializerMethodField()

    def get_etapa(self, obj):
        return f"Etapa {obj.etapa}" if obj.etapa is not None else None

    def get_qtd_total_empenho(self, obj):
        try:
            valor = numero_com_agrupador_de_milhar_e_decimal(obj.qtd_total_empenho)
            return f"{valor} {obj.cronograma.unidade_medida.abreviacao}"

        except AttributeError:
            return valor

    def get_quantidade(self, obj):
        try:
            valor = numero_com_agrupador_de_milhar_e_decimal(obj.quantidade)
            return f"{valor} {obj.cronograma.unidade_medida.abreviacao}"

        except AttributeError:
            return valor

    def get_total_embalagens(self, obj):
        try:
            valor = numero_com_agrupador_de_milhar_e_decimal(obj.total_embalagens)
            return f"{valor} {obj.cronograma.tipo_embalagem_secundaria.abreviacao}"

        except AttributeError:
            return valor

    def get_data_programada(self, obj):
        return obj.data_programada.strftime("%d/%m/%Y") if obj.data_programada else None

    def get_desvinculada_recebimento(self, obj):
        return not obj.ficha_recebimento.exists()

    class Meta:
        model = EtapasDoCronograma
        fields = (
            "uuid",
            "numero_empenho",
            "qtd_total_empenho",
            "etapa",
            "parte",
            "data_programada",
            "quantidade",
            "total_embalagens",
            "desvinculada_recebimento",
        )


class CronogramaFichaDeRecebimentoSerializer(serializers.ModelSerializer):
    fornecedor = serializers.SerializerMethodField()
    contrato = serializers.SerializerMethodField()
    pregao_chamada_publica = serializers.SerializerMethodField()
    ata = serializers.SerializerMethodField()
    produto = serializers.SerializerMethodField()
    marca = serializers.SerializerMethodField()
    qtd_total_programada = serializers.SerializerMethodField()
    peso_liquido_embalagem_primaria = serializers.SerializerMethodField()
    peso_liquido_embalagem_secundaria = serializers.SerializerMethodField()
    embalagem_primaria = serializers.SerializerMethodField()
    embalagem_secundaria = serializers.SerializerMethodField()
    categoria = serializers.SerializerMethodField()
    etapas = EtapasDoCronogramaFichaDeRecebimentoSerializer(many=True)
    documentos_de_recebimento = serializers.SerializerMethodField()
    sistema_vedacao_embalagem_secundaria = serializers.SerializerMethodField()

    def get_fornecedor(self, obj):
        return obj.empresa.nome_fantasia if obj.empresa else None

    def get_contrato(self, obj):
        return obj.contrato.numero if obj.contrato else None

    def get_pregao_chamada_publica(self, obj):
        return obj.contrato.pregao_chamada_publica if obj.contrato else None

    def get_ata(self, obj):
        return obj.contrato.ata if obj.contrato else None

    def get_produto(self, obj):
        try:
            return obj.ficha_tecnica.produto.nome
        except AttributeError:
            return None

    def get_marca(self, obj):
        try:
            return obj.ficha_tecnica.marca.nome if obj.ficha_tecnica else None
        except AttributeError:
            return None

    def get_qtd_total_programada(self, obj):
        valor = numero_com_agrupador_de_milhar_e_decimal(obj.qtd_total_programada)

        return (
            f"{valor} {obj.unidade_medida.abreviacao}" if obj.unidade_medida else valor
        )

    def get_peso_liquido_embalagem_primaria(self, obj):
        try:
            return f"{obj.ficha_tecnica.peso_liquido_embalagem_primaria} {obj.ficha_tecnica.unidade_medida_primaria.abreviacao}"
        except AttributeError:
            return None

    def get_peso_liquido_embalagem_secundaria(self, obj):
        try:
            return f"{obj.ficha_tecnica.peso_liquido_embalagem_secundaria} {obj.ficha_tecnica.unidade_medida_secundaria.abreviacao}"
        except AttributeError:
            return None

    def get_embalagem_primaria(self, obj):
        return obj.ficha_tecnica.embalagem_primaria if obj.ficha_tecnica else None

    def get_embalagem_secundaria(self, obj):
        return obj.ficha_tecnica.embalagem_secundaria if obj.ficha_tecnica else None

    def get_categoria(self, obj):
        return obj.ficha_tecnica.categoria if obj.ficha_tecnica else None

    def get_documentos_de_recebimento(self, obj):
        return DocRecebimentoFichaDeRecebimentoSerializer(
            obj.documentos_de_recebimento.filter(
                status=DocumentoDeRecebimentoWorkflow.APROVADO
            ),
            many=True,
        ).data

    def get_sistema_vedacao_embalagem_secundaria(self, obj):
        return (
            obj.ficha_tecnica.sistema_vedacao_embalagem_secundaria
            if obj.ficha_tecnica
            else None
        )

    class Meta:
        model = Cronograma
        fields = (
            "uuid",
            "fornecedor",
            "contrato",
            "pregao_chamada_publica",
            "ata",
            "produto",
            "marca",
            "qtd_total_programada",
            "peso_liquido_embalagem_primaria",
            "peso_liquido_embalagem_secundaria",
            "embalagem_primaria",
            "embalagem_secundaria",
            "categoria",
            "etapas",
            "documentos_de_recebimento",
            "sistema_vedacao_embalagem_secundaria",
        )


class EtapaCronogramaRelatorioSerializer(serializers.ModelSerializer):
    numero_cronograma = serializers.SerializerMethodField()
    produto = serializers.SerializerMethodField()
    empresa = serializers.SerializerMethodField()
    marca = serializers.SerializerMethodField()
    qtd_total_programada = serializers.SerializerMethodField()
    unidade_medida = serializers.SerializerMethodField()
    custo_unitario_produto = serializers.SerializerMethodField()
    armazem = serializers.SerializerMethodField()
    status_cronograma = serializers.SerializerMethodField()
    total_embalagens = serializers.SerializerMethodField()
    situacao = serializers.SerializerMethodField()
    etapa = serializers.SerializerMethodField()

    def get_etapa(self, obj):
        return f"Etapa {obj.etapa}" if obj.etapa is not None else None

    def get_numero_cronograma(self, obj):
        try:
            return obj.cronograma.numero
        except AttributeError:
            return "-"

    def get_produto(self, obj):
        try:
            return obj.cronograma.ficha_tecnica.produto.nome
        except AttributeError:
            return "-"

    def get_empresa(self, obj):
        try:
            return obj.cronograma.empresa.nome_fantasia
        except AttributeError:
            return "-"

    def get_marca(self, obj):
        try:
            return obj.cronograma.ficha_tecnica.marca.nome
        except AttributeError:
            return "-"

    def get_qtd_total_programada(self, obj):
        try:
            return obj.cronograma.qtd_total_programada
        except AttributeError:
            return "-"

    def get_unidade_medida(self, obj):
        try:
            return obj.cronograma.unidade_medida.abreviacao
        except AttributeError:
            return "-"

    def get_custo_unitario_produto(self, obj):
        return (
            f"R$ {numero_com_agrupador_de_milhar_e_decimal(obj.cronograma.custo_unitario_produto)}"
            if obj.cronograma.custo_unitario_produto
            else "-"
        )

    def get_armazem(self, obj):
        try:
            return obj.cronograma.armazem.nome_fantasia
        except AttributeError:
            return "-"

    def get_status_cronograma(self, obj):
        try:
            return obj.cronograma.get_status_display()
        except AttributeError:
            return "-"

    def get_total_embalagens(self, obj):
        try:
            return f"{obj.total_embalagens} {obj.cronograma.tipo_embalagem_secundaria.abreviacao}"

        except AttributeError:
            return "-"

    def get_situacao(self, obj):
        return "-"

    class Meta:
        model = EtapasDoCronograma
        fields = (
            "numero_cronograma",
            "produto",
            "empresa",
            "marca",
            "qtd_total_programada",
            "unidade_medida",
            "custo_unitario_produto",
            "armazem",
            "status_cronograma",
            "etapa",
            "parte",
            "data_programada",
            "quantidade",
            "total_embalagens",
            "situacao",
        )


class CronogramaRelatorioSerializer(serializers.ModelSerializer):
    etapas = EtapasDoCronogramaFichaDeRecebimentoSerializer(many=True)
    produto = serializers.SerializerMethodField()
    empresa = serializers.SerializerMethodField()
    armazem = serializers.SerializerMethodField()
    marca = serializers.SerializerMethodField()
    custo_unitario_produto = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")

    def get_produto(self, obj):
        try:
            return obj.ficha_tecnica.produto.nome
        except AttributeError:
            return None

    def get_empresa(self, obj):
        try:
            return obj.empresa.nome_fantasia
        except AttributeError:
            return None

    def get_armazem(self, obj):
        try:
            return obj.armazem.nome_fantasia
        except AttributeError:
            return None

    def get_marca(self, obj):
        try:
            return obj.ficha_tecnica.marca.nome if obj.ficha_tecnica else None
        except AttributeError:
            return None

    def get_custo_unitario_produto(self, obj):
        return (
            f"R$ {numero_com_agrupador_de_milhar_e_decimal(obj.custo_unitario_produto)}"
            if obj.custo_unitario_produto
            else None
        )

    class Meta:
        model = Cronograma
        fields = (
            "uuid",
            "numero",
            "produto",
            "empresa",
            "qtd_total_programada",
            "armazem",
            "status",
            "marca",
            "custo_unitario_produto",
            "etapas",
        )


class PainelCronogramaSerializer(serializers.ModelSerializer):
    produto = serializers.SerializerMethodField()
    empresa = serializers.SerializerMethodField()
    log_mais_recente = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")

    def get_produto(self, obj):
        try:
            return obj.ficha_tecnica.produto.nome
        except AttributeError:
            return None

    def get_empresa(self, obj):
        return obj.empresa.nome_fantasia if obj.empresa else None

    def get_log_mais_recente(self, obj):
        if obj.log_mais_recente:
            if obj.log_mais_recente.criado_em.date() == datetime.date.today():
                return datetime.datetime.strftime(
                    obj.log_mais_recente.criado_em, "%d/%m/%Y %H:%M"
                )
            return datetime.datetime.strftime(
                obj.log_mais_recente.criado_em, "%d/%m/%Y"
            )
        else:
            return datetime.datetime.strftime(obj.criado_em, "%d/%m/%Y")

    class Meta:
        model = Cronograma
        fields = ("uuid", "numero", "status", "empresa", "produto", "log_mais_recente")


class PainelSolicitacaoAlteracaoCronogramaSerializerItem(serializers.ModelSerializer):
    empresa = serializers.CharField(source="cronograma.empresa")
    cronograma = serializers.CharField(source="cronograma.numero")
    produto = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")
    log_mais_recente = serializers.SerializerMethodField()

    def get_produto(self, obj):
        try:
            return obj.cronograma.ficha_tecnica.produto.nome
        except AttributeError:
            return None

    def get_log_mais_recente(self, obj):
        if obj.log_criado_em:
            if obj.log_criado_em.date() == datetime.date.today():
                return datetime.datetime.strftime(obj.log_criado_em, "%d/%m/%Y %H:%M")
            return datetime.datetime.strftime(obj.log_criado_em, "%d/%m/%Y")
        else:
            return datetime.datetime.strftime(obj.log_criado_em, "%d/%m/%Y")

    class Meta:
        model = SolicitacaoAlteracaoCronograma
        fields = (
            "uuid",
            "numero_solicitacao",
            "empresa",
            "status",
            "cronograma",
            "produto",
            "log_mais_recente",
        )


class PainelSolicitacaoAlteracaoCronogramaSerializer(serializers.Serializer):
    status = serializers.CharField()
    dados = serializers.SerializerMethodField()
    total = serializers.IntegerField(allow_null=True)

    def get_dados(self, obj):
        return PainelSolicitacaoAlteracaoCronogramaSerializerItem(
            obj["dados"], many=True
        ).data

    class Meta:
        model = SolicitacaoAlteracaoCronograma
        fields = ("uuid", "status", "total", "dados")

    def to_representation(self, instance):
        result = super(
            PainelSolicitacaoAlteracaoCronogramaSerializer, self
        ).to_representation(instance)
        return OrderedDict(
            [(key, result[key]) for key in result if result[key] is not None]
        )
