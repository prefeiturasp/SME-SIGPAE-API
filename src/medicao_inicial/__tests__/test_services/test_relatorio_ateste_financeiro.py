import calendar
import datetime
import re
from decimal import Decimal

import pytest
from model_bakery import baker
from rest_framework import status

from src.dados_comuns.constants import (
    DIETA_ESPECIAL_TIPO_A,
    DIETA_ESPECIAL_TIPO_B,
    StringsParametrizacaoFinanceiraTabela,
)
from src.escola.models import GrupoUnidadeEscolar
from src.medicao_inicial.models import (
    CategoriaMedicao,
    GrupoMedicao,
    ParametrizacaoFinanceiraTabelaValor,
    TipoValorParametrizacaoFinanceira,
)
from src.medicao_inicial.services.relatorio_ateste_financeiro import (
    arredonda_centavos,
    build_relatorio_financeiro_grupo_cei,
    build_relatorio_financeiro_grupo_cemei,
    build_relatorio_financeiro_grupo_emebs,
    build_relatorio_financeiro_grupo_emei,
    calcula_linha_alimentacao,
    calcula_linha_dieta,
    serializa_relatorio_calculado,
)
from src.medicao_inicial.utils import normalizar_nome_campo
from src.relatorios.relatorios import gerar_relatorio_ateste_financeiro
from src.relatorios.templatetags.index import decimal_br
from src.relatorios.utils import extrair_texto_de_pdf

TEMPLATE_HTML_CEI = "relatorio_financeiro/relatorio_ateste_financeiro_grupo_cei.html"
TEMPLATE_HTML_CEMEI = (
    "relatorio_financeiro/relatorio_ateste_financeiro_grupo_cemei.html"
)
TEMPLATE_HTML_EMEBS = (
    "relatorio_financeiro/relatorio_ateste_financeiro_grupo_emebs.html"
)
TEMPLATE_HTML_EMEI = "relatorio_financeiro/relatorio_ateste_financeiro_grupo_emei.html"


@pytest.mark.django_db
def test_build_relatorio_financeiro_grupo_cei(
    relatorio_financeiro_cei,
    parametrizacao_financeira_cei,
    faixas_etarias_ativas,
):
    totais_consumo = {
        "ALIMENTAÇÃO - INTEGRAL": {
            str(faixas_etarias_ativas[0]): 10,
        },
        "ALIMENTAÇÃO - PARCIAL": {
            str(faixas_etarias_ativas[0]): 5,
        },
        "DIETA ESPECIAL - TIPO A - INTEGRAL": {
            str(faixas_etarias_ativas[0]): 2,
        },
        "DIETA ESPECIAL - TIPO B - PARCIAL": {
            str(faixas_etarias_ativas[0]): 1,
        },
    }

    tabelas = parametrizacao_financeira_cei.tabelas.all()

    resultado = build_relatorio_financeiro_grupo_cei(
        relatorio_financeiro_cei,
        tabelas,
        totais_consumo,
    )

    assert resultado["alimentacao"]["total_atendimentos"] == 15
    assert resultado["dieta_a"]["total_consumo"] == 2
    assert resultado["dieta_b"]["total_consumo"] == 1
    assert resultado["consolidado"]["quantidade"] == 18

    assert resultado["cabecalho"]["data_referencia"] == "OUTUBRO/2025"


@pytest.mark.django_db
def test_relatorio_ateste_financeiro_grupo_cei_conteudo_pdf(
    relatorio_financeiro_cei,
    parametrizacao_financeira_cei,
):
    pdf_bytes = gerar_relatorio_ateste_financeiro(
        relatorio_financeiro=relatorio_financeiro_cei,
        parametrizacao=parametrizacao_financeira_cei,
        builder=build_relatorio_financeiro_grupo_cei,
        template=TEMPLATE_HTML_CEI,
        tipo_calculo="faixa_etaria",
    )

    texto = extrair_texto_de_pdf(pdf_bytes)

    assert "ATESTE FINANCEIRO - MEDIÇÃO INICIAL" in texto
    assert "SECRETARIA MUNICIPAL DE EDUCAÇÃO" in texto

    assert "REFERÊNCIA:" in texto
    assert "OUTUBRO/2025" in texto

    assert relatorio_financeiro_cei.lote.nome.upper() in texto
    assert relatorio_financeiro_cei.lote.diretoria_regional.nome in texto

    assert GrupoUnidadeEscolar.GRUPO_1 in texto

    assert "ALIMENTAÇÕES FAIXAS ETÁRIAS - SEM DIETAS" in texto
    assert DIETA_ESPECIAL_TIPO_A in texto
    assert DIETA_ESPECIAL_TIPO_B in texto

    assert "CONSOLIDADO TOTAL (A + B + C)" in texto
    assert "QUANTIDADE SERVIDA:" in texto
    assert "VALOR DO FATURAMENTO TOTAL:" in texto


@pytest.mark.django_db
def test_build_relatorio_financeiro_grupo_emei(
    relatorio_financeiro_emei,
    parametrizacao_financeira_emei,
    tipo_alimentacao_lanche,
    tipo_alimentacao_lanche_4h,
    tipo_alimentacao_refeicao,
    grupo_unidade_escolar_emei,
    vinculo_alimentacao_emei,
):
    TIPOS_ALIMENTACOES = [
        tipo_alimentacao_lanche,
        tipo_alimentacao_lanche_4h,
        tipo_alimentacao_refeicao,
    ]

    GRUPO_NOME = grupo_unidade_escolar_emei.nome

    valores_por_tipo = {
        CategoriaMedicao.ALIMENTACAO: [10, 20, 30],
        DIETA_ESPECIAL_TIPO_A: [2, 4, 6],
        DIETA_ESPECIAL_TIPO_B: [1, 2, 3],
    }

    totais_consumo = {
        chave: {
            (
                f"total_{normalizar_nome_campo(tipo.nome, GRUPO_NOME).lower()}"
                if chave == CategoriaMedicao.ALIMENTACAO
                else normalizar_nome_campo(tipo.nome, GRUPO_NOME).lower()
            ): valor
            for tipo, valor in zip(TIPOS_ALIMENTACOES, valores)
        }
        for chave, valores in valores_por_tipo.items()
    }

    tabelas = parametrizacao_financeira_emei.tabelas.all()

    resultado = build_relatorio_financeiro_grupo_emei(
        relatorio_financeiro_emei,
        tabelas,
        totais_consumo,
    )

    assert resultado["alimentacao"]["total_atendimentos"] == 60
    assert resultado["alimentacao"]["valor_total"] == Decimal("1680.00")

    assert resultado["dieta_a"]["total_consumo"] == 12
    assert resultado["dieta_b"]["total_consumo"] == 3

    assert resultado["consolidado"]["quantidade"] == 75
    assert resultado["consolidado"]["valor"] == Decimal("1717.88")
    assert (
        resultado["consolidado"]["valor_extenso"]
        == "mil, setecentos e dezessete reais e oitenta e oito centavos"
    )

    assert resultado["cabecalho"]["data_referencia"] == "NOVEMBRO/2025"


@pytest.mark.django_db
def test_relatorio_ateste_financeiro_grupo_emei_conteudo_pdf(
    relatorio_financeiro_emei,
    parametrizacao_financeira_emei,
):
    pdf_bytes = gerar_relatorio_ateste_financeiro(
        relatorio_financeiro=relatorio_financeiro_emei,
        parametrizacao=parametrizacao_financeira_emei,
        builder=build_relatorio_financeiro_grupo_emei,
        template=TEMPLATE_HTML_EMEI,
        tipo_calculo="tipo_alimentacao",
    )

    texto = extrair_texto_de_pdf(pdf_bytes)

    assert "ATESTE FINANCEIRO - MEDIÇÃO INICIAL" in texto

    assert "REFERÊNCIA:" in texto
    assert "NOVEMBRO/2025" in texto

    assert relatorio_financeiro_emei.lote.nome.upper() in texto
    assert relatorio_financeiro_emei.lote.diretoria_regional.nome in texto

    assert GrupoUnidadeEscolar.GRUPO_3 in texto
    assert "(CEU EMEI, EMEI)" in texto

    assert "TIPOS DE ALIMENTAÇÕES - SEM DIETAS" in texto
    assert "DIETA ESPECIAL - TIPO A, A ENTERAL E RESTRIÇÃO DE AMINOÁCIDOS" in texto
    assert DIETA_ESPECIAL_TIPO_B in texto

    assert "CONSOLIDADO TOTAL (A + B + C)" in texto


@pytest.mark.django_db
def test_build_relatorio_financeiro_grupo_cieja(
    relatorio_financeiro_cieja,
    parametrizacao_financeira_cieja,
    tipo_alimentacao_lanche_4h,
    tipo_alimentacao_refeicao,
    grupo_unidade_escolar_cieja,
    vinculo_alimentacao_cieja,
):
    TIPOS_ALIMENTACOES = [
        tipo_alimentacao_lanche_4h,
        tipo_alimentacao_refeicao,
    ]

    GRUPO_NOME = grupo_unidade_escolar_cieja.nome

    valores_por_tipo = {
        CategoriaMedicao.ALIMENTACAO: [30, 60, 90],
        DIETA_ESPECIAL_TIPO_A: [20, 40, 60],
        DIETA_ESPECIAL_TIPO_B: [11, 22, 33],
    }

    totais_consumo = {
        chave: {
            (
                f"total_{normalizar_nome_campo(tipo.nome, GRUPO_NOME).lower()}"
                if chave == CategoriaMedicao.ALIMENTACAO
                else normalizar_nome_campo(tipo.nome, GRUPO_NOME).lower()
            ): valor
            for tipo, valor in zip(TIPOS_ALIMENTACOES, valores)
        }
        for chave, valores in valores_por_tipo.items()
    }

    tabelas = parametrizacao_financeira_cieja.tabelas.all()

    resultado = build_relatorio_financeiro_grupo_emei(
        relatorio_financeiro_cieja,
        tabelas,
        totais_consumo,
    )

    assert resultado["alimentacao"]["linhas"][0]["tipo"] == "REFEIÇÃO CIEJA E CMCT"

    assert len(resultado["dieta_a"]["linhas"]) == 2
    assert len(resultado["dieta_b"]["linhas"]) == 1

    assert resultado["consolidado"]["quantidade"] == 161

    assert resultado["cabecalho"]["data_referencia"] == "MARÇO/2026"


@pytest.mark.django_db
def test_relatorio_ateste_financeiro_grupo_cieja_conteudo_pdf(
    relatorio_financeiro_cieja,
    parametrizacao_financeira_cieja,
    vinculo_alimentacao_cieja,
):
    pdf_bytes = gerar_relatorio_ateste_financeiro(
        relatorio_financeiro=relatorio_financeiro_cieja,
        parametrizacao=parametrizacao_financeira_cieja,
        builder=build_relatorio_financeiro_grupo_emei,
        template=TEMPLATE_HTML_EMEI,
        tipo_calculo="tipo_alimentacao",
    )

    texto = extrair_texto_de_pdf(pdf_bytes)

    assert "MARÇO/2026" in texto

    assert relatorio_financeiro_cieja.lote.nome.upper() in texto
    assert relatorio_financeiro_cieja.lote.diretoria_regional.nome in texto

    assert GrupoUnidadeEscolar.GRUPO_6 in texto
    assert "(CIEJA, CMCT)" in texto

    assert texto.count("REFEIÇÃO CIEJA E CMCT") == 2
    assert texto.count("LANCHE 4H") == 3
    assert "KIT LANCHE" in texto

    assert "Página 1/1" in texto
    assert "Documento gerado em " in texto


@pytest.mark.django_db
def test_build_relatorio_financeiro_grupo_cemei(
    relatorio_financeiro_cemei,
    parametrizacao_financeira_cemei,
    faixas_etarias_ativas,
    tipo_alimentacao_lanche,
    tipo_alimentacao_lanche_4h,
    tipo_alimentacao_refeicao,
    grupo_unidade_escolar_cemei,
    vinculo_alimentacao_cemei,
):
    TIPOS_ALIMENTACOES = [
        tipo_alimentacao_lanche,
        tipo_alimentacao_lanche_4h,
        tipo_alimentacao_refeicao,
    ]

    GRUPO_NOME = grupo_unidade_escolar_cemei.nome

    totais_consumo_faixa = {
        chave: {str(faixa): 10 for faixa in faixas_etarias_ativas}
        for chave in [
            "ALIMENTAÇÃO - INTEGRAL",
            "ALIMENTAÇÃO - PARCIAL",
            "DIETA ESPECIAL - TIPO A - INTEGRAL",
            "DIETA ESPECIAL - TIPO B - PARCIAL",
        ]
    }

    valores_por_tipo = {
        CategoriaMedicao.ALIMENTACAO: [55, 66, 77],
        DIETA_ESPECIAL_TIPO_A: [11, 22, 33],
        DIETA_ESPECIAL_TIPO_B: [44, 55, 88],
    }

    totais_consumo_tipo = {
        chave: {
            (
                f"total_{normalizar_nome_campo(tipo.nome, GRUPO_NOME).lower()}"
                if chave == CategoriaMedicao.ALIMENTACAO
                else normalizar_nome_campo(tipo.nome, GRUPO_NOME).lower()
            ): valor
            for tipo, valor in zip(TIPOS_ALIMENTACOES, valores)
        }
        for chave, valores in valores_por_tipo.items()
    }

    totais_consumo = {
        "FAIXA": totais_consumo_faixa,
        "TIPO": totais_consumo_tipo,
    }

    tabelas = parametrizacao_financeira_cemei.tabelas.all()

    resultado = build_relatorio_financeiro_grupo_cemei(
        relatorio_financeiro_cemei,
        tabelas,
        totais_consumo,
    )

    numero_faixas = len(faixas_etarias_ativas) * 2

    assert len(resultado["cei"]["alimentacao"]["linhas"]) == numero_faixas
    assert len(resultado["cei"]["dieta_a"]["linhas"]) == numero_faixas
    assert len(resultado["cei"]["dieta_b"]["linhas"]) == numero_faixas

    assert len(resultado["emei"]["dieta_a"]["linhas"]) == 3
    assert len(resultado["emei"]["dieta_b"]["linhas"]) == 2

    assert resultado["emei"]["consolidado"]["quantidade"] == 363
    assert resultado["cei"]["consolidado"]["quantidade"] == 320

    assert resultado["cabecalho"]["data_referencia"] == "ABRIL/2026"


@pytest.mark.django_db
def test_relatorio_ateste_financeiro_grupo_cemei_conteudo_pdf(
    relatorio_financeiro_cemei,
    parametrizacao_financeira_cemei,
    faixas_etarias_ativas,
    vinculo_alimentacao_cemei,
):
    pdf_bytes = gerar_relatorio_ateste_financeiro(
        relatorio_financeiro=relatorio_financeiro_cemei,
        parametrizacao=parametrizacao_financeira_cemei,
        builder=build_relatorio_financeiro_grupo_cemei,
        template=TEMPLATE_HTML_CEMEI,
        tipo_calculo=None,
    )

    texto = extrair_texto_de_pdf(pdf_bytes)

    assert "ABRIL/2026" in texto

    assert relatorio_financeiro_cemei.lote.nome.upper() in texto
    assert relatorio_financeiro_cemei.lote.diretoria_regional.nome in texto

    assert GrupoUnidadeEscolar.GRUPO_2 in texto
    assert "(CEMEI, CEU CEMEI)" in texto

    for faixa in faixas_etarias_ativas:
        assert str(faixa) in texto

    assert "REFEIÇÃO" in texto
    assert "LANCHE" in texto
    assert "LANCHE 4H" in texto


@pytest.mark.django_db
def test_build_relatorio_financeiro_grupo_emef(
    relatorio_financeiro_emef,
    parametrizacao_financeira_emef,
    tipo_alimentacao_lanche,
    tipo_alimentacao_lanche_4h,
    tipo_alimentacao_refeicao,
    grupo_unidade_escolar_emef,
    vinculo_alimentacao_emef,
):
    TIPOS_ALIMENTACOES = [
        tipo_alimentacao_lanche.nome,
        tipo_alimentacao_lanche_4h.nome,
        tipo_alimentacao_refeicao.nome,
        "Refeição EJA",
    ]

    GRUPO_NOME = grupo_unidade_escolar_emef.nome

    valores_por_tipo = {
        CategoriaMedicao.ALIMENTACAO: [68, 78, 88, 98],
        DIETA_ESPECIAL_TIPO_A: [65, 75, 85, 95],
        DIETA_ESPECIAL_TIPO_B: [69, 79, 89, 99],
    }

    totais_consumo = {
        chave: {
            (
                f"total_{normalizar_nome_campo(tipo, GRUPO_NOME).lower()}"
                if chave == CategoriaMedicao.ALIMENTACAO
                else normalizar_nome_campo(tipo, GRUPO_NOME).lower()
            ): valor
            for tipo, valor in zip(TIPOS_ALIMENTACOES, valores)
        }
        for chave, valores in valores_por_tipo.items()
    }

    tabelas = parametrizacao_financeira_emef.tabelas.all()

    resultado = build_relatorio_financeiro_grupo_emei(
        relatorio_financeiro_emef,
        tabelas,
        totais_consumo,
    )

    for tipo in ["REFEIÇÃO - EJA", "KIT LANCHE"]:
        assert any(
            linha.get("tipo") == tipo for linha in resultado["alimentacao"]["linhas"]
        )

    assert (
        resultado["cabecalho"]["grupo_unidade_escolar"]
        == "Grupo 4 (CEU EMEF, CEU GESTAO, EMEF, EMEFM)"
    )
    assert resultado["cabecalho"]["data_referencia"] == "OUTUBRO/2025"


@pytest.mark.django_db
def test_relatorio_ateste_financeiro_grupo_emef_conteudo_pdf(
    relatorio_financeiro_emef,
    parametrizacao_financeira_emef,
    vinculo_alimentacao_emef,
):
    pdf_bytes = gerar_relatorio_ateste_financeiro(
        relatorio_financeiro=relatorio_financeiro_emef,
        parametrizacao=parametrizacao_financeira_emef,
        builder=build_relatorio_financeiro_grupo_emei,
        template=TEMPLATE_HTML_EMEI,
        tipo_calculo="tipo_alimentacao",
    )

    texto = extrair_texto_de_pdf(pdf_bytes)

    assert "ATESTE FINANCEIRO - MEDIÇÃO INICIAL" in texto
    assert "OUTUBRO/2025" in texto

    assert relatorio_financeiro_emef.lote.nome.upper() in texto
    assert relatorio_financeiro_emef.lote.diretoria_regional.nome in texto

    assert GrupoUnidadeEscolar.GRUPO_4 in texto
    assert "(CEU EMEF, CEU GESTAO, EMEF, EMEFM)" in texto

    assert "REFEIÇÃO" in texto
    assert "REFEIÇÃO - EJA" in texto


@pytest.mark.django_db
def test_build_relatorio_financeiro_grupo_emebs(
    relatorio_financeiro_emebs,
    parametrizacao_financeira_emebs,
    tipo_alimentacao_lanche,
    tipo_alimentacao_lanche_4h,
    tipo_alimentacao_refeicao,
    grupo_unidade_escolar_emebs,
    vinculo_alimentacao_emebs,
):
    TIPOS_ALIMENTACOES = [
        tipo_alimentacao_lanche.nome,
        tipo_alimentacao_lanche_4h.nome,
        tipo_alimentacao_refeicao.nome,
    ]

    GRUPO_NOME = grupo_unidade_escolar_emebs.nome

    valores_por_tipo = {
        "INFANTIL": {
            CategoriaMedicao.ALIMENTACAO: [68, 78, 88, 98],
            DIETA_ESPECIAL_TIPO_A: [65, 75, 85, 95],
            DIETA_ESPECIAL_TIPO_B: [69, 79, 89, 99],
        },
        "FUNDAMENTAL": {
            CategoriaMedicao.ALIMENTACAO: [10, 20, 30, 40],
            DIETA_ESPECIAL_TIPO_A: [11, 21, 31, 41],
            DIETA_ESPECIAL_TIPO_B: [12, 22, 32, 42],
        },
    }

    totais_consumo = {
        etapa: {
            chave: {
                (
                    f"total_{normalizar_nome_campo(tipo, GRUPO_NOME).lower()}"
                    if chave == CategoriaMedicao.ALIMENTACAO
                    else normalizar_nome_campo(tipo, GRUPO_NOME).lower()
                ): valor
                for tipo, valor in zip(TIPOS_ALIMENTACOES, valores)
            }
            for chave, valores in tipos.items()
        }
        for etapa, tipos in valores_por_tipo.items()
    }

    tabelas = parametrizacao_financeira_emebs.tabelas.all()

    resultado = build_relatorio_financeiro_grupo_emebs(
        relatorio_financeiro_emebs,
        tabelas,
        totais_consumo,
    )

    assert "infantil" in resultado
    assert "fundamental" in resultado

    assert resultado["cabecalho"]["grupo_unidade_escolar"] == "Grupo 5 (EMEBS)"
    assert resultado["cabecalho"]["data_referencia"] == "MAIO/2025"


@pytest.mark.django_db
def test_relatorio_ateste_financeiro_grupo_emebs_conteudo_pdf(
    relatorio_financeiro_emebs,
    parametrizacao_financeira_emebs,
    vinculo_alimentacao_emebs,
):
    pdf_bytes = gerar_relatorio_ateste_financeiro(
        relatorio_financeiro=relatorio_financeiro_emebs,
        parametrizacao=parametrizacao_financeira_emebs,
        builder=build_relatorio_financeiro_grupo_emebs,
        template=TEMPLATE_HTML_EMEBS,
        tipo_calculo="tipo_alimentacao",
    )

    texto = extrair_texto_de_pdf(pdf_bytes)

    assert "ATESTE FINANCEIRO - MEDIÇÃO INICIAL" in texto
    assert "MAIO/2025" in texto

    assert GrupoUnidadeEscolar.GRUPO_5 in texto
    assert "(EMEBS)" in texto

    assert "TURMA INFANTIL" in texto
    assert "TURMA FUNDAMENTAL" in texto


@pytest.mark.django_db
class TestRelatorioAtesteFinanceiroEmeiLancheEmergencialExtraordinarias:
    """
    O relatório de ateste financeiro obtém o consumo via
    `calcula_totais_consumo_por_grupo` (mesmo cálculo do endpoint
    `totais-atendimento-consumo`), que não filtra medições por grupo.

    Por isso o `lanche_emergencial` lançado nas medições de
    `SOLICITACOES_DE_ALIMENTACAO_EXTRAORDINARIAS` entra na linha
    "LANCHE EMERGENCIAL" da tabela de alimentações, somado ao das
    `SOLICITACOES_DE_ALIMENTACAO`.
    """

    LINHA_LANCHE_EMERGENCIAL = "LANCHE EMERGENCIAL"
    VALOR_UNITARIO = Decimal("4.00")
    VALOR_REAJUSTE = Decimal("1.00")
    QUANTIDADE_SOLICITACOES = 3
    QUANTIDADE_EXTRAORDINARIAS = 5

    @pytest.fixture
    def cenario(
        self,
        relatorio_financeiro_emei,
        parametrizacao_financeira_emei,
        tipo_unidade_escolar_emei,
        tipo_alimentacao_lanche_emergencial,
    ):
        escola = baker.make(
            "Escola",
            lote=relatorio_financeiro_emei.lote,
            tipo_unidade=tipo_unidade_escolar_emei,
        )
        solicitacao = baker.make(
            "SolicitacaoMedicaoInicial",
            escola=escola,
            mes=relatorio_financeiro_emei.mes,
            ano=relatorio_financeiro_emei.ano,
            status="MEDICAO_APROVADA_PELA_CODAE",
        )

        vinculo = baker.make(
            "VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
            tipo_unidade_escolar=tipo_unidade_escolar_emei,
        )
        vinculo.tipos_alimentacao.add(tipo_alimentacao_lanche_emergencial)

        tabela_alimentacoes = next(
            tabela
            for tabela in parametrizacao_financeira_emei.tabelas.all()
            if "Preço das Alimentações" in tabela.nome
        )
        for nome_tipo_valor, valor in (
            ("UNITARIO", self.VALOR_UNITARIO),
            ("REAJUSTE", self.VALOR_REAJUSTE),
        ):
            baker.make(
                "ParametrizacaoFinanceiraTabelaValor",
                tabela=tabela_alimentacoes,
                nome_campo="lanche_emergencial",
                faixa_etaria=None,
                tipo_alimentacao=tipo_alimentacao_lanche_emergencial,
                tipo_valor=TipoValorParametrizacaoFinanceira.objects.get(
                    nome=nome_tipo_valor
                ),
                valor=str(valor),
            )

        return {
            "relatorio_financeiro": relatorio_financeiro_emei,
            "parametrizacao": parametrizacao_financeira_emei,
            "solicitacao": solicitacao,
            "categoria_solicitacoes": baker.make(
                "CategoriaMedicao", nome=CategoriaMedicao.SOLICITACOES_DE_ALIMENTACAO
            ),
        }

    @staticmethod
    def _lanca_lanche_emergencial(cenario, nome_grupo, quantidade):
        grupo, _ = GrupoMedicao.objects.get_or_create(nome=nome_grupo)
        medicao = baker.make(
            "Medicao",
            solicitacao_medicao_inicial=cenario["solicitacao"],
            periodo_escolar=None,
            grupo=grupo,
        )
        baker.make(
            "ValorMedicao",
            medicao=medicao,
            categoria_medicao=cenario["categoria_solicitacoes"],
            nome_campo="lanche_emergencial",
            valor=str(quantidade),
            dia="01",
            semana="1",
        )

    @staticmethod
    def _gera_relatorio(cenario):
        """Gera o relatório pelo fluxo real e devolve (dados do builder, texto do PDF)."""
        capturado = {}

        def builder(*args, **kwargs):
            capturado["relatorio"] = build_relatorio_financeiro_grupo_emei(
                *args, **kwargs
            )
            return capturado["relatorio"]

        pdf_bytes = gerar_relatorio_ateste_financeiro(
            relatorio_financeiro=cenario["relatorio_financeiro"],
            parametrizacao=cenario["parametrizacao"],
            builder=builder,
            template=TEMPLATE_HTML_EMEI,
            tipo_calculo="tipo_alimentacao",
        )
        return capturado["relatorio"], extrair_texto_de_pdf(pdf_bytes)

    @classmethod
    def _linha_lanche_emergencial(cls, relatorio):
        return next(
            linha
            for linha in relatorio["alimentacao"]["linhas"]
            if linha["tipo"] == cls.LINHA_LANCHE_EMERGENCIAL
        )

    def test_relatorio_considera_medicao_extraordinaria(self, cenario):
        self._lanca_lanche_emergencial(
            cenario,
            GrupoMedicao.SOLICITACOES_DE_ALIMENTACAO_EXTRAORDINARIAS,
            self.QUANTIDADE_EXTRAORDINARIAS,
        )

        relatorio, texto = self._gera_relatorio(cenario)

        linha = self._linha_lanche_emergencial(relatorio)
        assert linha["numero_atendimentos"] == self.QUANTIDADE_EXTRAORDINARIAS
        assert linha["total_unitario"] == self.VALOR_UNITARIO + self.VALOR_REAJUSTE
        assert linha["valor_total"] == Decimal("25.00")
        assert self.LINHA_LANCHE_EMERGENCIAL in texto

    def test_relatorio_soma_solicitacoes_e_extraordinarias(self, cenario):
        self._lanca_lanche_emergencial(
            cenario,
            GrupoMedicao.SOLICITACOES_DE_ALIMENTACAO,
            self.QUANTIDADE_SOLICITACOES,
        )
        self._lanca_lanche_emergencial(
            cenario,
            GrupoMedicao.SOLICITACOES_DE_ALIMENTACAO_EXTRAORDINARIAS,
            self.QUANTIDADE_EXTRAORDINARIAS,
        )

        relatorio, _ = self._gera_relatorio(cenario)

        total = self.QUANTIDADE_SOLICITACOES + self.QUANTIDADE_EXTRAORDINARIAS
        linha = self._linha_lanche_emergencial(relatorio)
        assert linha["numero_atendimentos"] == total
        assert linha["valor_total"] == Decimal("40.00")
        assert relatorio["alimentacao"]["total_atendimentos"] == total
        assert relatorio["alimentacao"]["valor_total"] == Decimal("40.00")
        assert relatorio["consolidado"]["quantidade"] == total
        assert relatorio["consolidado"]["valor"] == Decimal("40.00")

    def test_adicionar_extraordinaria_aumenta_o_valor_do_relatorio(self, cenario):
        self._lanca_lanche_emergencial(
            cenario,
            GrupoMedicao.SOLICITACOES_DE_ALIMENTACAO,
            self.QUANTIDADE_SOLICITACOES,
        )
        relatorio_antes, _ = self._gera_relatorio(cenario)

        self._lanca_lanche_emergencial(
            cenario,
            GrupoMedicao.SOLICITACOES_DE_ALIMENTACAO_EXTRAORDINARIAS,
            self.QUANTIDADE_EXTRAORDINARIAS,
        )
        relatorio_depois, _ = self._gera_relatorio(cenario)

        antes = self._linha_lanche_emergencial(relatorio_antes)
        depois = self._linha_lanche_emergencial(relatorio_depois)
        assert antes["numero_atendimentos"] == self.QUANTIDADE_SOLICITACOES
        assert (
            depois["numero_atendimentos"] - antes["numero_atendimentos"]
            == self.QUANTIDADE_EXTRAORDINARIAS
        )
        assert depois["valor_total"] - antes["valor_total"] == Decimal("25.00")


class TestCalculosLinhaAtesteFinanceiro:
    def test_alimentacao_exemplo_manual(self):
        resultado = calcula_linha_alimentacao(Decimal("9.54"), Decimal("0.16"), 5)

        assert resultado == {
            "valor_total_unitario": Decimal("47.70"),
            "valor_total_reajuste": Decimal("0.80"),
            "valor_unitario_reajustado": Decimal("9.70"),
            "valor_total": Decimal("48.50"),
        }

    def test_alimentacao_sem_reajuste_e_sem_atendimentos(self):
        resultado = calcula_linha_alimentacao(Decimal("9.54"), Decimal("0"), 0)

        assert resultado["valor_total_unitario"] == Decimal("0.00")
        assert resultado["valor_total_reajuste"] == Decimal("0.00")
        assert resultado["valor_unitario_reajustado"] == Decimal("9.54")
        assert resultado["valor_total"] == Decimal("0.00")

    def test_alimentacao_aceita_quantidade_float_inteira(self):
        resultado = calcula_linha_alimentacao(Decimal("9.54"), Decimal("0.16"), 2237.0)

        assert resultado["valor_total"] == Decimal("21698.90")

    def test_dieta_exemplo_manual(self):
        resultado = calcula_linha_dieta(Decimal("10.00"), Decimal("12.5"), 4)

        assert resultado == {
            "valor_unitario_total": Decimal("11.25"),
            "valor_total": Decimal("45.00"),
        }

    def test_dieta_sem_acrescimo(self):
        resultado = calcula_linha_dieta(Decimal("9.54"), Decimal("0"), 5)

        assert resultado["valor_unitario_total"] == Decimal("9.54")
        assert resultado["valor_total"] == Decimal("47.70")

    def test_dieta_nao_arredonda_valor_intermediario(self):
        resultado = calcula_linha_dieta(Decimal("9.54"), Decimal("12.5"), 5)

        assert resultado["valor_unitario_total"] == Decimal("10.73")
        assert resultado["valor_total"] == Decimal("53.66")

    @pytest.mark.parametrize(
        "valor,esperado",
        [
            (Decimal("0.125"), Decimal("0.13")),
            (Decimal("0.135"), Decimal("0.14")),
            (Decimal("2.675"), Decimal("2.68")),
            (Decimal("1.004"), Decimal("1.00")),
            (Decimal("1.005"), Decimal("1.01")),
        ],
    )
    def test_arredonda_centavos_half_up(self, valor, esperado):
        assert arredonda_centavos(valor) == esperado

    @pytest.mark.parametrize(
        "valor,esperado",
        [
            (Decimal("0"), "0,00"),
            (Decimal("9.54"), "9,54"),
            (Decimal("47.7"), "47,70"),
            (Decimal("1234.56"), "1.234,56"),
            (Decimal("2000"), "2.000,00"),
            (Decimal("1234567.891"), "1.234.567,89"),
            (Decimal("0.125"), "0,13"),
        ],
    )
    def test_decimal_br_apos_arredondar(self, valor, esperado):
        assert decimal_br(arredonda_centavos(valor)) == esperado

    def test_serializa_relatorio_calculado_mescla_calculo_e_formata_pt_br(self):
        relatorio = {
            "cabecalho": {"data_geracao": "01/01/2026"},
            "alimentacao": {
                "linhas": [
                    {
                        "tipo": "LANCHE",
                        "valor_unitario": Decimal("9.54"),
                        "valor_total": Decimal("48.5000"),
                        "numero_atendimentos": 5,
                        "calculo": {"valor_total": Decimal("48.50")},
                    }
                ],
                "total_atendimentos": 5,
                "valor_total": Decimal("1234.5"),
            },
        }

        resultado = serializa_relatorio_calculado(relatorio)

        assert "cabecalho" not in resultado
        linha = resultado["alimentacao"]["linhas"][0]
        assert "calculo" not in linha
        assert linha == {
            "tipo": "LANCHE",
            "valor_unitario": "9,54",
            "valor_total": "48,50",
            "numero_atendimentos": 5,
        }
        assert resultado["alimentacao"]["total_atendimentos"] == 5
        assert resultado["alimentacao"]["valor_total"] == "1.234,50"


URL_RELATORIO_CONSOLIDADO = (
    "/medicao-inicial/relatorio-financeiro/relatorio-consolidado/{uuid}/"
)
URL_TOTAIS_CONSUMO = (
    "/medicao-inicial/solicitacao-medicao-inicial/totais-atendimento-consumo/"
)

REGEX_VALOR_PT_BR = re.compile(r"^\d{1,3}(\.\d{3})*,\d{2}$")

UNITARIO = "9,54"
REAJUSTE = "0,16"
ACRESCIMO = "12,50"

CHAVES_RESPOSTA_ATUAL = {
    "uuid",
    "edital",
    "lote",
    "grupo_unidade_escolar",
    "data_inicial",
    "data_final",
    "legenda",
    "tabelas",
    "mes_ano",
    "possui_reajuste",
}

GRUPOS = {
    "grupo_1_cei": dict(
        relatorio="relatorio_financeiro_cei",
        parametrizacao="parametrizacao_financeira_cei",
        consumo="relatorio_consolidado_xlsx_cei",
        tipo_calculo="faixa_etaria",
        fixtures_extras=["faixas_etarias_ativas"],
    ),
    "grupo_2_cemei": dict(
        relatorio="relatorio_financeiro_cemei",
        parametrizacao="parametrizacao_financeira_cemei",
        consumo="relatorio_consolidado_xlsx_cemei",
        tipo_calculo=None,
        fixtures_extras=["faixas_etarias_ativas", "vinculo_alimentacao_cemei"],
    ),
    "grupo_3_emei": dict(
        relatorio="relatorio_financeiro_emei",
        parametrizacao="parametrizacao_financeira_emei",
        consumo="relatorio_consolidado_xlsx_emei",
        tipo_calculo="tipo_alimentacao",
        fixtures_extras=["vinculo_alimentacao_emei"],
    ),
    "grupo_4_emef": dict(
        relatorio="relatorio_financeiro_emef",
        parametrizacao="parametrizacao_financeira_emef",
        consumo="relatorio_consolidado_xlsx_emef",
        tipo_calculo="tipo_alimentacao",
        fixtures_extras=["vinculo_alimentacao_emef"],
    ),
    "grupo_5_emebs": dict(
        relatorio="relatorio_financeiro_emebs",
        parametrizacao="parametrizacao_financeira_emebs",
        consumo="relatorio_consolidado_xlsx_emebs",
        tipo_calculo="tipo_alimentacao",
        fixtures_extras=["vinculo_alimentacao_emebs"],
    ),
    "grupo_6_cieja_cmct": dict(
        relatorio="relatorio_financeiro_cieja",
        parametrizacao="parametrizacao_financeira_cieja",
        consumo="relatorio_consolidado_xlsx_cieja",
        tipo_calculo="tipo_alimentacao",
        fixtures_extras=["vinculo_alimentacao_cieja"],
    ),
}


def _alinha_relatorio_a_solicitacao(relatorio, parametrizacao, solicitacao):
    relatorio.mes = solicitacao.mes
    relatorio.ano = solicitacao.ano

    escola = solicitacao.escola
    if escola.lote.diretoria_regional_id is None:
        escola.lote = relatorio.lote
    tipos_do_grupo = relatorio.grupo_unidade_escolar.tipos_unidades
    if not tipos_do_grupo.filter(pk=escola.tipo_unidade_id).exists():
        escola.tipo_unidade = tipos_do_grupo.get(iniciais=escola.tipo_unidade.iniciais)
    escola.save()

    relatorio.lote = escola.lote
    relatorio.save()

    ano = int(solicitacao.ano)
    mes = int(solicitacao.mes)
    parametrizacao.lote = solicitacao.escola.lote
    parametrizacao.data_inicial = datetime.date(ano, mes, 1)
    parametrizacao.data_final = datetime.date(
        ano, mes, calendar.monthrange(ano, mes)[1]
    )
    parametrizacao.save()


@pytest.fixture(params=list(GRUPOS))
def contexto_grupo(request):
    spec = GRUPOS[request.param]
    for nome_fixture in spec["fixtures_extras"]:
        request.getfixturevalue(nome_fixture)

    relatorio = request.getfixturevalue(spec["relatorio"])
    parametrizacao = request.getfixturevalue(spec["parametrizacao"])
    solicitacao = request.getfixturevalue(spec["consumo"])
    _alinha_relatorio_a_solicitacao(relatorio, parametrizacao, solicitacao)

    return {
        "nome": request.param,
        "spec": spec,
        "relatorio": relatorio,
        "parametrizacao": parametrizacao,
    }


def _aplica_valores_pt_br(parametrizacao):
    valores = ParametrizacaoFinanceiraTabelaValor.objects.filter(
        tabela__parametrizacao_financeira=parametrizacao
    )
    valores.filter(tipo_valor__nome="UNITARIO").update(valor=UNITARIO)
    valores.filter(tipo_valor__nome="REAJUSTE").update(valor=REAJUSTE)
    valores.filter(tipo_valor__nome="ACRESCIMO").update(valor=ACRESCIMO)


def _tipos_valor_por_tabela(tabelas):
    alimentacoes, dietas = [], []
    for tabela in tabelas:
        tipos = {valor["tipo_valor"] for valor in tabela["valores"]}
        if tabela["nome"].startswith(
            StringsParametrizacaoFinanceiraTabela.ALIMENTACOES.value
        ):
            alimentacoes.append(tipos)
        else:
            dietas.append(tipos)
    return alimentacoes, dietas


def _get_consolidado(client, relatorio, **params):
    return client.get(
        URL_RELATORIO_CONSOLIDADO.format(uuid=relatorio.uuid),
        data=params,
        content_type="application/json",
    )


def _get_totais(client, contexto):
    relatorio = contexto["relatorio"]
    params = {
        "mes": relatorio.mes,
        "ano": relatorio.ano,
        "grupo_unidade_escolar": relatorio.grupo_unidade_escolar.uuid,
        "lote": relatorio.lote.uuid,
    }
    if contexto["spec"]["tipo_calculo"]:
        params["tipo_calculo"] = contexto["spec"]["tipo_calculo"]
    return client.get(URL_TOTAIS_CONSUMO, data=params, format="json")


def _numeros_folha(dados):
    if isinstance(dados, dict):
        for valor in dados.values():
            yield from _numeros_folha(valor)
    elif isinstance(dados, list):
        for valor in dados:
            yield from _numeros_folha(valor)
    elif isinstance(dados, (int, float)) and not isinstance(dados, bool):
        yield dados


def _linhas(calculos, tabela):
    blocos = [calculos]
    if "cei" in calculos:
        blocos = [calculos["cei"], calculos["emei"]]
    elif "infantil" in calculos:
        blocos = [calculos["infantil"], calculos["fundamental"]]
    return [linha for bloco in blocos for linha in bloco[tabela]["linhas"]]


def _quantidade(linha):
    return linha.get("numero_atendimentos", linha.get("numero_consumo"))


def _pt_br(valor: Decimal) -> str:
    return decimal_br(arredonda_centavos(valor))


@pytest.mark.django_db
class TestContratoRelatorioConsolidado:
    def test_retorna_unitario_reajuste_acrescimo_como_string_pt_br(
        self, client_autenticado_codae_medicao, contexto_grupo
    ):
        _aplica_valores_pt_br(contexto_grupo["parametrizacao"])

        response = _get_consolidado(
            client_autenticado_codae_medicao, contexto_grupo["relatorio"]
        )

        assert response.status_code == status.HTTP_200_OK, response.json()
        dados = response.json()
        assert set(dados.keys()) == CHAVES_RESPOSTA_ATUAL

        alimentacoes, dietas = _tipos_valor_por_tabela(dados["tabelas"])
        assert alimentacoes and dietas
        assert all({"UNITARIO", "REAJUSTE"} <= tipos for tipos in alimentacoes)
        assert all({"UNITARIO", "ACRESCIMO"} <= tipos for tipos in dietas)

        esperado_por_tipo = {
            "UNITARIO": UNITARIO,
            "REAJUSTE": REAJUSTE,
            "ACRESCIMO": ACRESCIMO,
        }
        for tabela in dados["tabelas"]:
            for valor in tabela["valores"]:
                assert isinstance(valor["valor"], str)
                assert REGEX_VALOR_PT_BR.match(valor["valor"])
                assert valor["valor"] == esperado_por_tipo[valor["tipo_valor"]]

    def test_nao_altera_formato_de_milhar_pt_br(
        self, client_autenticado_codae_medicao, contexto_grupo
    ):
        ParametrizacaoFinanceiraTabelaValor.objects.filter(
            tabela__parametrizacao_financeira=contexto_grupo["parametrizacao"],
            tipo_valor__nome="UNITARIO",
        ).update(valor="2.000,00")

        response = _get_consolidado(
            client_autenticado_codae_medicao, contexto_grupo["relatorio"]
        )

        assert response.status_code == status.HTTP_200_OK, response.json()
        valores = {
            valor["valor"]
            for tabela in response.json()["tabelas"]
            for valor in tabela["valores"]
            if valor["tipo_valor"] == "UNITARIO"
        }
        assert valores == {"2.000,00"}

    def test_sem_incluir_calculos_nao_tem_chave_calculos(
        self, client_autenticado_codae_medicao, contexto_grupo
    ):
        for valor in ("", "false", "0"):
            params = {"incluir_calculos": valor} if valor else {}
            response = _get_consolidado(
                client_autenticado_codae_medicao, contexto_grupo["relatorio"], **params
            )

            assert response.status_code == status.HTTP_200_OK, response.json()
            assert "calculos" not in response.json()


@pytest.mark.django_db
class TestContratoTotaisAtendimentoConsumo:
    def test_retorna_quantitativos_inteiros_por_grupo(
        self, client_autenticado_codae_medicao, contexto_grupo
    ):
        response = _get_totais(client_autenticado_codae_medicao, contexto_grupo)

        assert response.status_code == status.HTTP_200_OK, response.json()
        dados = response.json()

        quantidades = list(_numeros_folha(dados))
        assert quantidades
        assert all(float(q).is_integer() for q in quantidades), dados

        nome = contexto_grupo["nome"]
        if nome == "grupo_1_cei":
            assert dados["ALIMENTAÇÃO - INTEGRAL"]
            assert dados["ALIMENTAÇÃO - PARCIAL"]
            assert dados["DIETA ESPECIAL - TIPO A - INTEGRAL"]
            assert dados["DIETA ESPECIAL - TIPO B - PARCIAL"]
        elif nome == "grupo_2_cemei":
            assert set(dados) == {"TIPO", "FAIXA"}
            assert dados["FAIXA"]["ALIMENTAÇÃO - INTEGRAL"]
            assert dados["FAIXA"]["DIETA ESPECIAL - TIPO A - PARCIAL"]
            assert dados["TIPO"][CategoriaMedicao.ALIMENTACAO]["total_lanche_4h"] > 0
            assert dados["TIPO"][DIETA_ESPECIAL_TIPO_A]["lanche_4h"] > 0
            assert dados["TIPO"][DIETA_ESPECIAL_TIPO_B]["lanche_4h"] > 0
        elif nome == "grupo_5_emebs":
            for turma in ("INFANTIL", "FUNDAMENTAL"):
                bloco = dados[turma]
                assert bloco[CategoriaMedicao.ALIMENTACAO]["total_lanche_4h"] > 0
                assert bloco[DIETA_ESPECIAL_TIPO_A]["lanche_4h"] > 0
                assert bloco[DIETA_ESPECIAL_TIPO_B]["lanche_4h"] > 0
        else:
            assert dados[CategoriaMedicao.ALIMENTACAO]["total_lanche_4h"] > 0
            assert dados[DIETA_ESPECIAL_TIPO_A]["lanche_4h"] > 0
            assert dados[DIETA_ESPECIAL_TIPO_B]["lanche_4h"] > 0


@pytest.mark.django_db
class TestCalculosRelatorioConsolidado:
    def test_alimentacao_bate_com_calculo_manual(
        self, client_autenticado_codae_medicao, contexto_grupo
    ):
        _aplica_valores_pt_br(contexto_grupo["parametrizacao"])

        response = _get_consolidado(
            client_autenticado_codae_medicao,
            contexto_grupo["relatorio"],
            incluir_calculos="true",
        )

        assert response.status_code == status.HTTP_200_OK, response.json()
        dados = response.json()
        assert CHAVES_RESPOSTA_ATUAL <= set(dados)
        assert "cabecalho" not in dados["calculos"]

        linhas = _linhas(dados["calculos"], "alimentacao")
        com_consumo = [linha for linha in linhas if _quantidade(linha) > 0]
        assert com_consumo

        unitario, reajuste = Decimal("9.54"), Decimal("0.16")
        linhas_verificadas = 0
        for linha in com_consumo:
            if linha["valor_unitario"] != "9,54":
                continue
            atendimentos = Decimal(_quantidade(linha))
            assert linha["valor_reajuste"] == "0,16"
            assert linha["valor_total_unitario"] == _pt_br(atendimentos * unitario)
            assert linha["valor_total_reajuste"] == _pt_br(atendimentos * reajuste)
            assert linha["valor_unitario_reajustado"] == "9,70"
            assert linha["valor_total"] == _pt_br(atendimentos * (unitario + reajuste))
            linhas_verificadas += 1
        assert linhas_verificadas > 0

    def test_dieta_bate_com_calculo_manual(
        self, client_autenticado_codae_medicao, contexto_grupo
    ):
        _aplica_valores_pt_br(contexto_grupo["parametrizacao"])

        response = _get_consolidado(
            client_autenticado_codae_medicao,
            contexto_grupo["relatorio"],
            incluir_calculos="true",
        )

        assert response.status_code == status.HTTP_200_OK, response.json()
        calculos = response.json()["calculos"]

        unitario = Decimal("9.54")
        unitario_total = unitario * (1 + Decimal("12.5") / 100)
        linhas_verificadas = 0
        for tabela in ("dieta_a", "dieta_b"):
            linhas = _linhas(calculos, tabela)
            assert linhas
            for linha in linhas:
                if linha["valor_unitario"] != "9,54":
                    assert linha["valor_total"] == "0,00"
                    continue
                atendimentos = Decimal(_quantidade(linha))
                assert linha["valor_acrescimo"] == "12,50"
                assert linha["valor_unitario_total"] == _pt_br(unitario_total)
                assert linha["valor_total"] == _pt_br(atendimentos * unitario_total)
                linhas_verificadas += 1

        assert linhas_verificadas > 0

    def test_nao_altera_demais_campos(
        self, client_autenticado_codae_medicao, contexto_grupo
    ):
        relatorio = contexto_grupo["relatorio"]

        sem_calculos = _get_consolidado(client_autenticado_codae_medicao, relatorio)
        com_calculos = _get_consolidado(
            client_autenticado_codae_medicao, relatorio, incluir_calculos="true"
        )

        assert sem_calculos.status_code == status.HTTP_200_OK
        assert com_calculos.status_code == status.HTTP_200_OK
        dados = com_calculos.json()
        dados.pop("calculos")
        assert dados == sem_calculos.json()


def _reajustes(parametrizacao):
    return ParametrizacaoFinanceiraTabelaValor.objects.filter(
        tabela__parametrizacao_financeira=parametrizacao,
        tipo_valor__nome="REAJUSTE",
    )


@pytest.mark.django_db
class TestPossuiReajuste:
    def test_false_sem_reajustes_cadastrados(
        self,
        client_autenticado_codae_medicao,
        relatorio_financeiro_emei,
        parametrizacao_financeira_emei,
    ):
        _reajustes(parametrizacao_financeira_emei).delete()

        response = _get_consolidado(
            client_autenticado_codae_medicao, relatorio_financeiro_emei
        )

        assert response.status_code == status.HTTP_200_OK, response.json()
        assert response.json()["possui_reajuste"] is False

    @pytest.mark.parametrize("valor", ["0", "0,00", "0.00", ""])
    def test_false_quando_reajustes_sao_zero(
        self,
        client_autenticado_codae_medicao,
        relatorio_financeiro_emei,
        parametrizacao_financeira_emei,
        valor,
    ):
        _reajustes(parametrizacao_financeira_emei).update(valor=valor)

        response = _get_consolidado(
            client_autenticado_codae_medicao, relatorio_financeiro_emei
        )

        assert response.status_code == status.HTTP_200_OK, response.json()
        assert response.json()["possui_reajuste"] is False

    def test_false_com_nulos_e_zeros_combinados(
        self,
        client_autenticado_codae_medicao,
        relatorio_financeiro_emei,
        parametrizacao_financeira_emei,
    ):
        reajustes = list(_reajustes(parametrizacao_financeira_emei))
        for reajuste, valor in zip(reajustes, ["", "0", "0,00", "0.00"]):
            reajuste.valor = valor
            reajuste.save()

        response = _get_consolidado(
            client_autenticado_codae_medicao, relatorio_financeiro_emei
        )

        assert response.json()["possui_reajuste"] is False

    def test_true_quando_um_reajuste_e_diferente_de_zero(
        self,
        client_autenticado_codae_medicao,
        relatorio_financeiro_emei,
        parametrizacao_financeira_emei,
    ):
        reajustes = list(_reajustes(parametrizacao_financeira_emei))
        for reajuste in reajustes:
            reajuste.valor = "0"
            reajuste.save()
        reajustes[0].valor = "0,16"
        reajustes[0].save()

        response = _get_consolidado(
            client_autenticado_codae_medicao, relatorio_financeiro_emei
        )

        dados = response.json()
        assert dados["possui_reajuste"] is True
        assert isinstance(dados["possui_reajuste"], bool)
        assert CHAVES_RESPOSTA_ATUAL <= set(dados)
        assert any(
            valor["valor"] == "0,16"
            for tabela in dados["tabelas"]
            for valor in tabela["valores"]
            if valor["tipo_valor"] == "REAJUSTE"
        )

    def test_true_quando_reajuste_e_negativo(
        self,
        client_autenticado_codae_medicao,
        relatorio_financeiro_emei,
        parametrizacao_financeira_emei,
    ):
        _reajustes(parametrizacao_financeira_emei).update(valor="0")
        reajuste = _reajustes(parametrizacao_financeira_emei).first()
        reajuste.valor = "-0,16"
        reajuste.save()

        response = _get_consolidado(
            client_autenticado_codae_medicao, relatorio_financeiro_emei
        )

        assert response.json()["possui_reajuste"] is True

    def test_ignora_unitario_e_acrescimo(
        self,
        client_autenticado_codae_medicao,
        relatorio_financeiro_emei,
        parametrizacao_financeira_emei,
    ):
        _reajustes(parametrizacao_financeira_emei).update(valor="0")
        ParametrizacaoFinanceiraTabelaValor.objects.filter(
            tabela__parametrizacao_financeira=parametrizacao_financeira_emei,
            tipo_valor__nome__in=["UNITARIO", "ACRESCIMO"],
        ).update(valor="12,50")

        response = _get_consolidado(
            client_autenticado_codae_medicao, relatorio_financeiro_emei
        )

        assert response.json()["possui_reajuste"] is False

    def test_ignora_reajuste_de_outro_lote_e_grupo(
        self,
        client_autenticado_codae_medicao,
        relatorio_financeiro_emei,
        parametrizacao_financeira_emei,
        parametrizacao_financeira_cei,
    ):
        _reajustes(parametrizacao_financeira_emei).update(valor="0")
        _reajustes(parametrizacao_financeira_cei).update(valor="9,54")

        response = _get_consolidado(
            client_autenticado_codae_medicao, relatorio_financeiro_emei
        )

        assert response.status_code == status.HTTP_200_OK, response.json()
        assert response.json()["possui_reajuste"] is False
