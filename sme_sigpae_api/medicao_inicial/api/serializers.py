import datetime
import json

import environ
from rest_framework import serializers

from sme_sigpae_api.dados_comuns.api.serializers import (
    LogSolicitacoesUsuarioComAnexosSerializer,
    LogSolicitacoesUsuarioSerializer,
)
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.dados_comuns.utils import converte_numero_em_mes
from sme_sigpae_api.escola.api.serializers import (
    AlunoPeriodoParcialSimplesSerializer,
    DiretoriaRegionalSimplissimaSerializer,
    EscolaSimplissimaSerializer,
    FaixaEtariaSerializer,
    GrupoUnidadeEscolarSerializer,
    LoteParaFiltroSerializer,
    PeriodoEscolarSerializer,
    TipoAlimentacaoSerializer,
    TipoUnidadeEscolarSerializer,
    TipoUnidadeEscolarSimplesSerializer,
)
from sme_sigpae_api.medicao_inicial.models import (
    AlimentacaoLancamentoEspecial,
    CategoriaMedicao,
    ClausulaDeDesconto,
    DiaParaCorrigir,
    DiaSobremesaDoce,
    Empenho,
    Medicao,
    OcorrenciaMedicaoInicial,
    ParametrizacaoFinanceira,
    ParametrizacaoFinanceiraTabela,
    ParametrizacaoFinanceiraTabelaValor,
    PermissaoLancamentoEspecial,
    RelatorioFinanceiro,
    Responsavel,
    SolicitacaoMedicaoInicial,
    TipoContagemAlimentacao,
    ValorMedicao,
)
from sme_sigpae_api.perfil.api.serializers import UsuarioSerializer
from sme_sigpae_api.terceirizada.api.serializers.serializers import (
    EditalSimplesSerializer,
    LoteSimplesSerializer,
)
from sme_sigpae_api.terceirizada.models import Edital


class DiaSobremesaDoceSerializer(serializers.ModelSerializer):
    tipo_unidade = TipoUnidadeEscolarSerializer()
    criado_por = UsuarioSerializer()
    edital = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Edital.objects.all()
    )
    edital_numero = serializers.CharField(source="edital.numero")

    class Meta:
        model = DiaSobremesaDoce
        exclude = ("id",)


class OcorrenciaMedicaoInicialSerializer(serializers.ModelSerializer):
    logs = LogSolicitacoesUsuarioComAnexosSerializer(many=True)
    ultimo_arquivo = serializers.SerializerMethodField()
    ultimo_arquivo_excel = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_ultimo_arquivo(self, obj):
        env = environ.Env()
        api_url = env.str("URL_ANEXO", default="http://localhost:8000")
        return f"{api_url}{obj.ultimo_arquivo.url}"

    def get_ultimo_arquivo_excel(self, obj):
        env = environ.Env()
        api_url = env.str("URL_ANEXO", default="http://localhost:8000")
        status = [
            LogSolicitacoesUsuario.MEDICAO_ENVIADA_PELA_UE,
            LogSolicitacoesUsuario.MEDICAO_CORRIGIDA_PELA_UE,
            LogSolicitacoesUsuario.MEDICAO_CORRIGIDA_PARA_CODAE,
        ]
        logs = obj.logs.filter(status_evento__in=status)
        if logs:
            anexo_excel = logs.last().anexos.filter(nome__icontains=".xls").first()
            if anexo_excel:
                return f"{api_url}{anexo_excel.arquivo.url}"
        return ""

    def get_status(self, obj):
        return obj.status.name

    class Meta:
        model = OcorrenciaMedicaoInicial
        exclude = ("id",)


class TipoContagemAlimentacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoContagemAlimentacao
        exclude = ("id",)


class ResponsavelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Responsavel
        exclude = (
            "id",
            "solicitacao_medicao_inicial",
        )


class SolicitacaoMedicaoInicialSerializer(serializers.ModelSerializer):
    escola = serializers.CharField(source="escola.nome")
    escola_uuid = serializers.CharField(source="escola.uuid")
    tipos_contagem_alimentacao = TipoContagemAlimentacaoSerializer(many=True)
    responsaveis = ResponsavelSerializer(many=True)
    ocorrencia = OcorrenciaMedicaoInicialSerializer()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    alunos_periodo_parcial = AlunoPeriodoParcialSimplesSerializer(many=True)
    historico = serializers.SerializerMethodField()
    escola_eh_emebs = serializers.SerializerMethodField()
    escola_cei_com_inclusao_parcial_autorizada = serializers.BooleanField()
    sem_lancamentos = serializers.BooleanField()
    justificativa_sem_lancamentos = serializers.CharField()
    justificativa_codae_correcao_sem_lancamentos = serializers.CharField()

    def get_historico(self, obj):
        if not obj.historico:
            return None
        return json.loads(obj.historico)

    def get_escola_eh_emebs(self, obj):
        return obj.escola.eh_emebs

    class Meta:
        model = SolicitacaoMedicaoInicial
        exclude = (
            "id",
            "criado_por",
        )


class SolicitacaoMedicaoInicialLancadaSerializer(serializers.ModelSerializer):
    escola = serializers.CharField(source="escola.nome")
    escola_uuid = serializers.CharField(source="escola.uuid")

    class Meta:
        model = SolicitacaoMedicaoInicial
        fields = (
            "uuid",
            "mes",
            "ano",
            "escola",
            "escola_uuid",
            "escola_cei_com_inclusao_parcial_autorizada",
        )


class SolicitacaoMedicaoInicialDashboardSerializer(serializers.ModelSerializer):
    escola = serializers.CharField(source="escola.nome")
    escola_uuid = serializers.CharField(source="escola.uuid")
    status = serializers.CharField(source="get_status_display")
    tipo_unidade = serializers.CharField(source="escola.tipo_unidade")
    log_mais_recente = serializers.SerializerMethodField()
    mes_ano = serializers.SerializerMethodField()
    sem_lancamentos = serializers.BooleanField()

    def get_log_mais_recente(self, obj):
        return (
            datetime.datetime.strftime(obj.log_mais_recente.criado_em, "%d/%m/%Y %H:%M")
            if obj.log_mais_recente
            else None
        )

    def get_mes_ano(self, obj):
        return f"{converte_numero_em_mes(int(obj.mes))} {obj.ano}"

    class Meta:
        model = SolicitacaoMedicaoInicial
        fields = (
            "uuid",
            "escola",
            "escola_uuid",
            "mes",
            "ano",
            "mes_ano",
            "tipo_unidade",
            "status",
            "log_mais_recente",
            "dre_ciencia_correcao_data",
            "todas_medicoes_e_ocorrencia_aprovados_por_medicao",
            "escola_cei_com_inclusao_parcial_autorizada",
            "sem_lancamentos",
        )


class ValorMedicaoSerializer(serializers.ModelSerializer):
    medicao_uuid = serializers.SerializerMethodField()
    medicao_alterado_em = serializers.SerializerMethodField()
    faixa_etaria = serializers.SerializerMethodField()
    faixa_etaria_str = serializers.SerializerMethodField()
    faixa_etaria_inicio = serializers.SerializerMethodField()
    infantil_ou_fundamental = serializers.CharField()

    def get_medicao_uuid(self, obj):
        return obj.medicao.uuid

    def get_faixa_etaria(self, obj):
        return obj.faixa_etaria.uuid if obj.faixa_etaria else None

    def get_faixa_etaria_str(self, obj):
        return obj.faixa_etaria.__str__() if obj.faixa_etaria else None

    def get_faixa_etaria_inicio(self, obj):
        return obj.faixa_etaria.inicio if obj.faixa_etaria else None

    def get_medicao_alterado_em(self, obj):
        if obj.medicao.alterado_em:
            return datetime.datetime.strftime(
                obj.medicao.alterado_em, "%d/%m/%Y, às %H:%M:%S"
            )

    class Meta:
        model = ValorMedicao
        fields = (
            "categoria_medicao",
            "nome_campo",
            "valor",
            "dia",
            "medicao_uuid",
            "faixa_etaria",
            "faixa_etaria_str",
            "faixa_etaria_inicio",
            "uuid",
            "medicao_alterado_em",
            "habilitado_correcao",
            "infantil_ou_fundamental",
        )


class CategoriaMedicaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaMedicao
        fields = "__all__"


class MedicaoSerializer(serializers.ModelSerializer):
    solicitacao_medicao_inicial = SolicitacaoMedicaoInicialSerializer()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return obj.status.name

    class Meta:
        model = Medicao
        fields = ("uuid", "solicitacao_medicao_inicial", "status", "logs")


class AlimentacaoLancamentoEspecialSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlimentacaoLancamentoEspecial
        fields = "__all__"


class PermissaoLancamentoEspecialSerializer(serializers.ModelSerializer):
    escola = EscolaSimplissimaSerializer()
    diretoria_regional = DiretoriaRegionalSimplissimaSerializer()
    periodo_escolar = PeriodoEscolarSerializer()
    alimentacoes_lancamento_especial = AlimentacaoLancamentoEspecialSerializer(
        many=True
    )
    alterado_em = serializers.SerializerMethodField()
    ativo = serializers.SerializerMethodField()

    def get_alterado_em(self, obj):
        return datetime.datetime.strftime(obj.alterado_em, "%d/%m/%Y")

    def get_ativo(self, obj):
        return obj.ativo

    class Meta:
        model = PermissaoLancamentoEspecial
        fields = "__all__"


class DiaParaCorrigirSerializer(serializers.ModelSerializer):
    medicao = serializers.CharField(source="medicao.uuid")

    class Meta:
        model = DiaParaCorrigir
        exclude = ("id", "criado_por")


class EmpenhoSerializer(serializers.ModelSerializer):
    contrato = serializers.CharField(source="contrato.numero")
    edital = serializers.CharField(source="edital.numero")

    class Meta:
        model = Empenho
        exclude = ("id", "criado_em", "alterado_em")


class ClausulaDeDescontoSerializer(serializers.ModelSerializer):
    edital = EditalSimplesSerializer()

    class Meta:
        model = ClausulaDeDesconto
        exclude = ("id", "criado_em", "alterado_em")


class ParametrizacaoFinanceiraTabelaValorSerializer(serializers.ModelSerializer):
    faixa_etaria = FaixaEtariaSerializer()
    tipo_alimentacao = TipoAlimentacaoSerializer()

    class Meta:
        model = ParametrizacaoFinanceiraTabelaValor
        fields = ["faixa_etaria", "tipo_alimentacao", "grupo", "valor_colunas"]


class ParametrizacaoFinanceiraTabelaSerializer(serializers.ModelSerializer):
    valores = ParametrizacaoFinanceiraTabelaValorSerializer(many=True)

    class Meta:
        model = ParametrizacaoFinanceiraTabela
        fields = ["nome", "valores"]


class ParametrizacaoFinanceiraSerializer(serializers.ModelSerializer):
    edital = EditalSimplesSerializer()
    dre = serializers.CharField(source="lote.diretoria_regional.nome")
    lote = LoteSimplesSerializer()
    tipos_unidades = TipoUnidadeEscolarSimplesSerializer(many=True)
    tabelas = ParametrizacaoFinanceiraTabelaSerializer(many=True)

    class Meta:
        model = ParametrizacaoFinanceira
        exclude = ("id", "criado_em", "alterado_em")


class RelatorioFinanceiroSerializer(serializers.ModelSerializer):
    lote = LoteParaFiltroSerializer()
    grupo_unidade_escolar = GrupoUnidadeEscolarSerializer()

    class Meta:
        model = RelatorioFinanceiro
        exclude = ("id", "criado_em", "alterado_em")
