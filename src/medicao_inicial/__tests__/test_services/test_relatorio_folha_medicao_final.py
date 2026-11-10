import datetime
import io
from decimal import Decimal

import pytest
from freezegun import freeze_time
from model_bakery import baker
from pypdf import PdfReader

from src.escola.models import FaixaEtaria
from src.medicao_inicial.models import MedicaoFinal, ParametrizacaoFinanceiraTabelaValor
from src.medicao_inicial.services.relatorio_ateste_financeiro import (
    montar_relatorio_calculado,
    obter_config_grupo,
)
from src.medicao_inicial.services.relatorio_folha_medicao_final import (
    montar_cabecalho_folha,
    montar_contexto_folha_medicao_final,
    nome_arquivo_folha_medicao_final,
    obter_dados_contratuais,
)
from src.relatorios.relatorios import (
    gerar_relatorio_ateste_financeiro,
    gerar_relatorio_folha_medicao_final,
)
from src.relatorios.templatetags.index import percentual_br
from src.relatorios.utils import extrair_texto_de_pdf

pytestmark = pytest.mark.django_db


def _gera_medicao_final(relatorio, nome="MARIA DA SILVA", rf="8785571"):
    return baker.make(
        MedicaoFinal,
        relatorio_financeiro=relatorio,
        gerado_por=baker.make("perfil.Usuario", nome=nome, registro_funcional=rf),
        nome_responsavel_conferencia="JOAO DE SOUZA",
        rf_responsavel_conferencia="1234567",
        numero_processo_pagamento="6016.2025/0001234-5",
    )


def _paginas(pdf_bytes):
    return [pagina.extract_text() for pagina in PdfReader(io.BytesIO(pdf_bytes)).pages]


class TestConsolidados:
    def test_extenso_dos_consolidados_tem_maiuscula_e_ponto(
        self, contexto_grupo_relatorio
    ):
        relatorio = contexto_grupo_relatorio["relatorio"]
        _gera_medicao_final(relatorio)

        contexto = montar_contexto_folha_medicao_final(
            relatorio, contexto_grupo_relatorio["parametrizacao"]
        )

        for consolidado in contexto["consolidados"]:
            extenso = consolidado["valor_extenso"]
            assert extenso[0].isupper()
            assert extenso.endswith(".")


class TestCabecalhoEArquivo:
    @pytest.fixture
    def relatorio(self):
        lote = baker.make(
            "Lote",
            nome="05",
            terceirizada=None,
            diretoria_regional=baker.make(
                "DiretoriaRegional",
                nome="DIRETORIA REGIONAL DE EDUCACAO FREGUESIA/BRASILANDIA",
            ),
        )
        grupo = baker.make(
            "GrupoUnidadeEscolar",
            nome="Grupo 2",
            tipos_unidades=[
                baker.make("TipoUnidadeEscolar", iniciais="CEU CEMEI"),
                baker.make("TipoUnidadeEscolar", iniciais="CEMEI"),
            ],
        )
        return baker.make(
            "RelatorioFinanceiro",
            lote=lote,
            grupo_unidade_escolar=grupo,
            mes="08",
            ano="2025",
        )

    def test_sem_contrato_e_sem_terceirizada_exibe_traco(self, relatorio):
        cabecalho = montar_cabecalho_folha(
            relatorio, {"data_referencia": "AGOSTO/2025"}
        )

        assert cabecalho["dre_lote"] == "DRE FREGUESIA/BRASILANDIA - LOTE 05"
        assert cabecalho["empresa_contratada"] == "-"
        assert cabecalho["numero_contrato"] == "-"
        assert cabecalho["numero_processo_administrativo"] == "-"
        assert cabecalho["grupo_unidade_escolar"] == "Grupo 2 (CEMEI, CEU CEMEI)"
        assert cabecalho["periodo_servico"] == "01/08/2025 À 31/08/2025"
        assert cabecalho["data_referencia"] == "AGOSTO/2025"

    def test_nao_duplica_prefixo_do_lote(self, relatorio):
        relatorio.lote.nome = "Lote 05"
        relatorio.lote.save()

        cabecalho = montar_cabecalho_folha(relatorio, {})

        assert cabecalho["dre_lote"] == "DRE FREGUESIA/BRASILANDIA - LOTE 05"

    def test_dados_contratuais_sem_contrato_e_sem_terceirizada(self, relatorio):
        dados = obter_dados_contratuais(relatorio)

        assert dados == {
            "empresa_contratada": None,
            "periodo_inicio": "01/08/2025",
            "periodo_fim": "31/08/2025",
            "lote": "05",
            "dre": "DIRETORIA REGIONAL DE EDUCACAO FREGUESIA/BRASILANDIA",
            "tipos_unidade": "CEMEI, CEU CEMEI",
            "numero_contrato": None,
            "numero_processo_administrativo": None,
        }

    def test_nome_do_arquivo_nao_tem_barra_e_cabe_no_campo(self, relatorio):
        nome = nome_arquivo_folha_medicao_final(relatorio)

        assert nome == (
            "Folha de Medição Final - DRE FREGUESIA-BRASILANDIA - Grupo 2 - 08_2025.pdf"
        )
        assert len(f"cental_downloads/{nome}") <= 100


@pytest.mark.parametrize(
    "valor, esperado",
    [
        (Decimal("3.00"), "3%"),
        (Decimal("0"), "0%"),
        (Decimal("10.00"), "10%"),
        (Decimal("100.00"), "100%"),
        (Decimal("12.50"), "12,5%"),
        (Decimal("33.33"), "33,33%"),
    ],
)
def test_percentual_br_sem_zeros_decimais(valor, esperado):
    assert percentual_br(valor) == esperado


@pytest.mark.usefixtures("pdf_com_estilos")
class TestAssinatura:
    def test_preserva_a_data_da_geracao_ao_regerar_o_pdf(
        self, relatorio_financeiro_cei, parametrizacao_financeira_cei
    ):
        with freeze_time("2026-10-02 14:30:00"):
            _gera_medicao_final(relatorio_financeiro_cei)

        with freeze_time("2026-11-15 09:05:00"):
            texto = extrair_texto_de_pdf(
                gerar_relatorio_folha_medicao_final(
                    relatorio_financeiro_cei, parametrizacao_financeira_cei
                )
            )

        assert "RF: 8785571, em 02/10/2026, às 14:30." in texto
        assert "em 15/11/2026, às" not in texto
        assert "Documento gerado em 15/11/2026 às 09:05" in texto

    def test_usuario_sem_rf_exibe_traco(self, relatorio_financeiro_cei):
        medicao_final = _gera_medicao_final(relatorio_financeiro_cei, rf=None)

        assert " - RF: -, em " in medicao_final.assinatura_eletronica

    def test_escapa_o_nome_do_usuario(self, relatorio_financeiro_cei):
        medicao_final = _gera_medicao_final(
            relatorio_financeiro_cei, nome="<b>MARIA</b>"
        )

        assert "&lt;b&gt;MARIA&lt;/b&gt;" in medicao_final.assinatura_eletronica


@pytest.mark.usefixtures("pdf_com_estilos")
class TestConteudoFolha:
    def test_conteudo_em_todos_os_grupos(self, contexto_grupo_relatorio):
        relatorio = contexto_grupo_relatorio["relatorio"]
        parametrizacao = contexto_grupo_relatorio["parametrizacao"]
        _gera_medicao_final(relatorio)

        texto = extrair_texto_de_pdf(
            gerar_relatorio_folha_medicao_final(relatorio, parametrizacao)
        )

        for trecho in (
            "FOLHA DE MEDIÇÃO FINAL",
            "DRE E LOTE",
            "EMPRESA CONTRATADA",
            "Nº PROCESSO ADMINISTRATIVO",
            "PERÍODO DE REALIZAÇÃO DO SERVIÇO",
            "MÊS DE REFERÊNCIA DA MEDIÇÃO",
            "NÚMERO DE ATEND.",
            "QUANTIDADE SERVIDA",
            "VALOR DO FATURAMENTO TOTAL",
            "Responsável pela conferência das medições iniciais:",
            "JOAO DE SOUZA - RF 1234567",
            "Servidor responsável pela consolidação das Medições Iniciais",
            "Diretor de Divisão Técnica SME/CODAE/DINUTRE",
            "Coordenador SME/CODAE",
            "Responsável pela Empresa Contratada",
        ):
            assert trecho in texto
        assert "DESCONTO" not in texto.upper()
        assert "FATURAMENTO FINAL" not in texto
        assert "ATESTE FINANCEIRO" not in texto

    def test_numeros_iguais_aos_da_api_e_do_ateste(self, contexto_grupo_relatorio):
        relatorio = contexto_grupo_relatorio["relatorio"]
        parametrizacao = contexto_grupo_relatorio["parametrizacao"]
        _gera_medicao_final(relatorio)
        config = obter_config_grupo(relatorio.grupo_unidade_escolar.nome)

        folha = extrair_texto_de_pdf(
            gerar_relatorio_folha_medicao_final(relatorio, parametrizacao)
        )
        ateste = extrair_texto_de_pdf(
            gerar_relatorio_ateste_financeiro(
                relatorio,
                parametrizacao,
                config["builder"],
                config["template"],
                config["tipo_calculo"],
            )
        )
        calculos = montar_relatorio_calculado(relatorio, parametrizacao)

        for valor in _valores_monetarios(calculos):
            assert f"R$ {valor}" in folha
            assert f"R$ {valor}" in ateste

    def test_sem_reajuste_oculta_as_colunas(
        self, relatorio_financeiro_cei, parametrizacao_financeira_cei
    ):
        _gera_medicao_final(relatorio_financeiro_cei)
        ParametrizacaoFinanceiraTabelaValor.objects.filter(
            tabela__parametrizacao_financeira=parametrizacao_financeira_cei,
            tipo_valor__nome="REAJUSTE",
        ).update(valor="0")

        texto = extrair_texto_de_pdf(
            gerar_relatorio_folha_medicao_final(
                relatorio_financeiro_cei, parametrizacao_financeira_cei
            )
        ).replace(" ", "")

        assert "VALORTOTALUNITÁRIO" in texto
        assert "VALORDOREAJUSTE" not in texto
        assert "VALORUNIT.REAJUSTADO" not in texto


def _valores_monetarios(dados):
    """Percorre os valores em Reais do relatório calculado pela API."""
    chaves = {"valor_total", "valor"}
    if isinstance(dados, dict):
        for chave, valor in dados.items():
            if chave in chaves and isinstance(valor, str):
                yield valor
            else:
                yield from _valores_monetarios(valor)
    elif isinstance(dados, list):
        for item in dados:
            yield from _valores_monetarios(item)


@pytest.mark.usefixtures("pdf_com_estilos")
class TestPaginacao:
    @pytest.fixture
    def documento_longo(
        self, relatorio_financeiro_cemei, parametrizacao_financeira_cemei
    ):
        _gera_medicao_final(relatorio_financeiro_cemei)
        for mes in range(40):
            baker.make("FaixaEtaria", inicio=100 + mes, fim=101 + mes, ativo=True)

        with freeze_time(datetime.datetime(2026, 11, 6, 10, 15)):
            return _paginas(
                gerar_relatorio_folha_medicao_final(
                    relatorio_financeiro_cemei, parametrizacao_financeira_cemei
                )
            )

    def test_cabecalho_numeracao_e_rodape_em_todas_as_paginas(self, documento_longo):
        total = len(documento_longo)

        assert total > 3
        for numero, pagina in enumerate(documento_longo, start=1):
            assert pagina.count("FOLHA DE MEDIÇÃO FINAL") == 1
            assert f"Página {numero}/{total}" in pagina
            assert "Documento gerado em 06/11/2026 às 10:15" in pagina

    def test_responsaveis_somente_na_ultima_pagina(self, documento_longo):
        *anteriores, ultima = documento_longo

        assert "Diretor de Divisão Técnica SME/CODAE/DINUTRE" in ultima
        assert "Responsável pela Empresa Contratada" in ultima
        for pagina in anteriores:
            assert "Diretor de Divisão Técnica" not in pagina
            assert "Responsável pela Empresa Contratada" not in pagina

    def test_nenhuma_linha_de_faixa_etaria_e_perdida(self, documento_longo):
        texto = "\n".join(documento_longo)
        faixas_ativas = FaixaEtaria.objects.filter(ativo=True).count()

        for periodo in ("Período Integral", "Período Parcial"):
            assert texto.count(periodo) == 3 * faixas_ativas

    def test_thead_repete_na_continuacao_das_tabelas(self, documento_longo):
        paginas_com_linhas = [
            pagina for pagina in documento_longo if "Período Integral" in pagina
        ]

        assert len(paginas_com_linhas) > 1
        for pagina in paginas_com_linhas:
            assert "NÚMERO DE" in pagina

    def test_cabecalho_em_todas_as_paginas_nos_seis_grupos(
        self, contexto_grupo_relatorio
    ):
        relatorio = contexto_grupo_relatorio["relatorio"]
        _gera_medicao_final(relatorio)

        paginas = _paginas(
            gerar_relatorio_folha_medicao_final(
                relatorio, contexto_grupo_relatorio["parametrizacao"]
            )
        )

        assert len(paginas) >= 2
        for numero, pagina in enumerate(paginas, start=1):
            assert pagina.count("FOLHA DE MEDIÇÃO FINAL") == 1
            assert f"Página {numero}/{len(paginas)}" in pagina
        assert "Coordenador SME/CODAE" in paginas[-1]
