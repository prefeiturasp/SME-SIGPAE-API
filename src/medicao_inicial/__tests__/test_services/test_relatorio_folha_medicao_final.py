import datetime
import io
from decimal import Decimal

import pytest
from django.template import Context
from django.template.loader import get_template
from django.template.loader_tags import ExtendsNode
from freezegun import freeze_time
from model_bakery import baker
from pypdf import PdfReader

from src.dados_comuns.constants import StringsParametrizacaoFinanceiraTabela
from src.escola.models import FaixaEtaria, GrupoUnidadeEscolar
from src.medicao_inicial.models import (
    DescontoFinanceiro,
    MedicaoFinal,
    ParametrizacaoFinanceiraTabelaValor,
)
from src.medicao_inicial.services.relatorio_ateste_financeiro import (
    montar_relatorio_calculado,
    obter_config_grupo,
)
from src.medicao_inicial.services.relatorio_folha_medicao_final import (
    montar_cabecalho_folha,
    montar_contexto_folha_medicao_final,
    montar_faturamento_final,
    nome_arquivo_folha_medicao_final,
    obter_dados_contratuais,
    titulo_coluna_faixa_ou_alimentacao,
)
from src.relatorios.relatorios import (
    gerar_relatorio_ateste_financeiro,
    gerar_relatorio_folha_medicao_final,
)
from src.relatorios.templatetags.index import (
    agrupador_milhar_com_decimal,
    numero_para_milhar,
    percentual_br,
)
from src.relatorios.utils import extrair_texto_de_pdf

pytestmark = pytest.mark.django_db

ALIMENTACOES = StringsParametrizacaoFinanceiraTabela.ALIMENTACOES.value


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


TEMPLATE_FOLHA = "relatorio_financeiro/relatorio_folha_medicao_final.html"


def _template_pai_da_folha(contexto):
    template = get_template(TEMPLATE_FOLHA).template
    extends = template.nodelist.get_nodes_by_type(ExtendsNode)[0]
    context = Context(contexto)
    context.template = template
    return extends.get_parent(context).origin.template_name


def test_template_da_folha_estende_o_base_sem_contexto():
    assert (
        _template_pai_da_folha({})
        == "relatorio_financeiro/relatorio_ateste_financeiro_base.html"
    )


@pytest.mark.parametrize(
    "grupo",
    [
        GrupoUnidadeEscolar.GRUPO_1,
        GrupoUnidadeEscolar.GRUPO_2,
        GrupoUnidadeEscolar.GRUPO_3,
        GrupoUnidadeEscolar.GRUPO_5,
    ],
)
def test_template_da_folha_estende_o_template_do_grupo(grupo):
    template_grupo = obter_config_grupo(grupo)["template"]

    assert _template_pai_da_folha({"template_ateste": template_grupo}) == (
        template_grupo
    )


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
        assert "TABELA DE DESCONTO" not in texto
        assert "TOTAL DE DESCONTOS DOS ITENS (D)" not in texto
        assert "DESCONTOSTOTAIS(D)" not in _sem_espacos(texto)
        assert "FATURAMENTOFINAL" not in _sem_espacos(texto)
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

    def test_responsaveis_na_pagina_do_consolidado_quando_cabem(
        self, relatorio_financeiro_cei, parametrizacao_financeira_cei
    ):
        _gera_medicao_final(relatorio_financeiro_cei)

        ultima = _paginas(
            gerar_relatorio_folha_medicao_final(
                relatorio_financeiro_cei, parametrizacao_financeira_cei
            )
        )[-1]

        assert "CONSOLIDADO TOTAL (A + B + C)" in ultima
        assert "Responsável pela Empresa Contratada" in ultima

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


def _sem_espacos(texto):
    return "".join(texto.split())


def _assert_em_ordem(texto, trechos):
    posicao = 0
    for trecho in trechos:
        posicao = texto.index(_sem_espacos(trecho), posicao)


@pytest.mark.usefixtures("pdf_com_estilos")
@pytest.mark.parametrize(
    "contexto_grupo_relatorio", ["grupo_1_cei", "grupo_2_cemei"], indirect=True
)
class TestGruposPorFaixaEtaria:
    @pytest.fixture
    def folha(self, contexto_grupo_relatorio):
        relatorio = contexto_grupo_relatorio["relatorio"]
        parametrizacao = contexto_grupo_relatorio["parametrizacao"]
        _gera_medicao_final(relatorio)
        contexto = montar_contexto_folha_medicao_final(relatorio, parametrizacao)
        texto = extrair_texto_de_pdf(
            gerar_relatorio_folha_medicao_final(relatorio, parametrizacao)
        )
        return contexto.get("cei", contexto), _sem_espacos(texto)

    def test_tabelas_na_ordem_com_os_totais(self, folha):
        tabelas, texto = folha

        _assert_em_ordem(
            texto,
            [
                "ALIMENTAÇÕES FAIXAS ETÁRIAS - SEM DIETAS",
                "TOTAL (A)",
                "DIETA ESPECIAL - TIPO A",
                "TOTAL (B)",
                "DIETA ESPECIAL - TIPO B",
                "TOTAL (C)",
            ],
        )
        totais = (
            ("A", tabelas["alimentacao"]["total_atendimentos"], "alimentacao"),
            ("B", tabelas["dieta_a"]["total_consumo"], "dieta_a"),
            ("C", tabelas["dieta_b"]["total_consumo"], "dieta_b"),
        )
        for ordem, quantidade, tabela in totais:
            valor = agrupador_milhar_com_decimal(tabelas[tabela]["valor_total"])
            assert f"TOTAL({ordem}){numero_para_milhar(quantidade)}R${valor}" in texto

    def test_linhas_exibem_periodo_e_faixa_com_os_valores(self, folha):
        tabelas, texto = folha
        linhas = [
            (linha, linha["numero_atendimentos"])
            for linha in tabelas["alimentacao"]["linhas"]
        ] + [
            (linha, linha["numero_consumo"])
            for tabela in ("dieta_a", "dieta_b")
            for linha in tabelas[tabela]["linhas"]
        ]

        assert linhas
        for linha, quantidade in linhas:
            rotulo = _sem_espacos(f"{linha['periodo']} - {linha['faixa']}")
            valor_unitario = agrupador_milhar_com_decimal(linha["valor_unitario"])
            assert (
                f"{rotulo}{numero_para_milhar(quantidade)}R${valor_unitario}" in texto
            )


@pytest.mark.usefixtures("pdf_com_estilos")
@pytest.mark.parametrize("contexto_grupo_relatorio", ["grupo_2_cemei"], indirect=True)
def test_cemei_exibe_turma_infantil_e_os_tres_consolidados(contexto_grupo_relatorio):
    relatorio = contexto_grupo_relatorio["relatorio"]
    parametrizacao = contexto_grupo_relatorio["parametrizacao"]
    _gera_medicao_final(relatorio)
    consolidados = montar_contexto_folha_medicao_final(relatorio, parametrizacao)[
        "consolidados"
    ]

    texto = _sem_espacos(
        extrair_texto_de_pdf(
            gerar_relatorio_folha_medicao_final(relatorio, parametrizacao)
        )
    )

    _assert_em_ordem(
        texto,
        [
            "TOTAL (C)",
            "Alimentações TURMA INFANTIL da CEMEI",
            "TOTAL (INF. A)",
            "TOTAL (INF. B)",
            "TOTAL (INF. C)",
            "CONSOLIDADO CEI (A + B + C)",
            "CONSOLIDADO INFANTIL - EMEI (INF. A + INF. B + INF. C)",
            "CONSOLIDADO TOTAL (A + B + C + INF. A + INF. B + INF. C)",
        ],
    )
    for consolidado in consolidados:
        bloco = texto.split(_sem_espacos(consolidado["titulo"]), 1)[1]
        bloco = bloco.split("CONSOLIDADO", 1)[0]
        quantidade = numero_para_milhar(consolidado["quantidade"])
        valor = agrupador_milhar_com_decimal(consolidado["valor"])
        assert f"{quantidade}ALIMENTAÇÕES" in bloco
        assert f"R${valor}" in bloco


def _clausula(edital, porcentagem="50.00", numero="7.2.2", item="item a"):
    return baker.make(
        "ClausulaDeDesconto",
        edital=edital,
        numero_clausula=numero,
        item_clausula=item,
        porcentagem_desconto=Decimal(porcentagem),
    )


def _cria_desconto(relatorio, clausula, quantidade, unidades=("EMEF TESTE",), **kw):
    return baker.make(
        DescontoFinanceiro,
        relatorio_financeiro=relatorio,
        clausula_desconto=clausula,
        quantidade=quantidade,
        unidades_educacionais=[baker.make("Escola", nome=nome) for nome in unidades],
        **kw,
    )


def _altera_unitario(parametrizacao, valor, nome_tabela=ALIMENTACOES, **filtros):
    atualizados = ParametrizacaoFinanceiraTabelaValor.objects.filter(
        tabela__parametrizacao_financeira=parametrizacao,
        tabela__nome__startswith=nome_tabela,
        tipo_valor__nome="UNITARIO",
        **filtros,
    ).update(valor=valor)
    assert atualizados


def _descontos(relatorio, parametrizacao):
    _gera_medicao_final(relatorio)
    return montar_contexto_folha_medicao_final(relatorio, parametrizacao)["descontos"]


class TestTabelaDescontos:
    def test_cei_por_faixa_etaria_segue_a_regra_do_modal(
        self,
        edital,
        relatorio_financeiro_cei,
        parametrizacao_financeira_cei,
        periodo_escolar_integral,
    ):
        faixa = FaixaEtaria.objects.filter(ativo=True).first()
        _altera_unitario(
            parametrizacao_financeira_cei,
            "9.70",
            tabela__periodo_escolar=periodo_escolar_integral,
            faixa_etaria=faixa,
        )
        _cria_desconto(
            relatorio_financeiro_cei,
            _clausula(edital),
            3,
            unidades=("CEI DIRET JARDIM SANTA TEREZA",),
            tipo_lancamento="ALIMENTACOES",
            faixa_etaria=faixa,
            periodo_escolar=periodo_escolar_integral,
        )

        descontos = _descontos(relatorio_financeiro_cei, parametrizacao_financeira_cei)

        assert descontos["linhas"] == [
            {
                "unidades": ["CEI DIRET JARDIM SANTA TEREZA"],
                "tipo_lancamento": "ALIMENTAÇÃO",
                "faixa_ou_alimentacao": f"Integral - {faixa}",
                "clausula": "7.2.2. item a - (50%)",
                "quantidade": 3,
                "valor_unitario": Decimal("9.70"),
                "total": Decimal("14.55"),
            }
        ]
        assert descontos["total"] == Decimal("14.55")

    def test_cei_dieta_usa_o_unitario_sem_acrescimo(
        self,
        edital,
        relatorio_financeiro_cei,
        parametrizacao_financeira_cei,
        periodo_escolar_parcial,
    ):
        faixa = FaixaEtaria.objects.filter(ativo=True).last()
        _altera_unitario(
            parametrizacao_financeira_cei,
            "12.00",
            nome_tabela=StringsParametrizacaoFinanceiraTabela.DIETA_B.value,
            tabela__periodo_escolar=periodo_escolar_parcial,
            faixa_etaria=faixa,
        )
        _cria_desconto(
            relatorio_financeiro_cei,
            _clausula(edital, porcentagem="10.00"),
            2,
            tipo_lancamento="DIETAS_TIPO_B",
            faixa_etaria=faixa,
            periodo_escolar=periodo_escolar_parcial,
        )

        [linha] = _descontos(relatorio_financeiro_cei, parametrizacao_financeira_cei)[
            "linhas"
        ]

        assert linha["tipo_lancamento"] == "DIETA ESPECIAL TIPO B"
        assert linha["faixa_ou_alimentacao"] == f"Parcial - {faixa}"
        assert linha["valor_unitario"] == Decimal("12.00")
        assert linha["total"] == Decimal("2.40")

    def test_emef_diferencia_refeicao_e_refeicao_eja(
        self,
        edital,
        vinculo_alimentacao_emef,
        relatorio_financeiro_emef,
        parametrizacao_financeira_emef,
        tipo_alimentacao_refeicao,
        periodo_escolar_noite,
    ):
        clausula = _clausula(edital, porcentagem="100.00", item="item c")
        _cria_desconto(
            relatorio_financeiro_emef,
            clausula,
            5,
            tipo_lancamento="ALIMENTACOES",
            tipo_alimentacao=tipo_alimentacao_refeicao,
        )
        _cria_desconto(
            relatorio_financeiro_emef,
            clausula,
            2,
            tipo_lancamento="ALIMENTACOES",
            tipo_alimentacao=tipo_alimentacao_refeicao,
            periodo_escolar=periodo_escolar_noite,
        )

        descontos = _descontos(
            relatorio_financeiro_emef, parametrizacao_financeira_emef
        )

        assert [
            (linha["faixa_ou_alimentacao"], linha["valor_unitario"], linha["total"])
            for linha in descontos["linhas"]
        ] == [
            ("REFEIÇÃO", Decimal("21.00"), Decimal("105.00")),
            ("REFEIÇÃO - EJA", Decimal("25.00"), Decimal("50.00")),
        ]
        assert descontos["linhas"][0]["clausula"] == "7.2.2. item c - (100%)"
        assert descontos["total"] == Decimal("155.00")

    def test_cemei_busca_o_valor_na_turma_do_desconto(
        self,
        edital,
        vinculo_alimentacao_cemei,
        relatorio_financeiro_cemei,
        parametrizacao_financeira_cemei,
        tipo_alimentacao_refeicao,
        periodo_escolar_integral,
    ):
        faixa = FaixaEtaria.objects.filter(ativo=True).first()
        _altera_unitario(
            parametrizacao_financeira_cemei,
            "9.70",
            tabela__periodo_escolar=periodo_escolar_integral,
            faixa_etaria=faixa,
        )
        clausula = _clausula(edital)
        _cria_desconto(
            relatorio_financeiro_cemei,
            clausula,
            3,
            tipo_lancamento="ALIMENTACOES",
            cei_ou_emei="CEI",
            faixa_etaria=faixa,
            periodo_escolar=periodo_escolar_integral,
        )
        _cria_desconto(
            relatorio_financeiro_cemei,
            clausula,
            4,
            tipo_lancamento="ALIMENTACOES",
            cei_ou_emei="EMEI",
            tipo_alimentacao=tipo_alimentacao_refeicao,
        )
        _cria_desconto(
            relatorio_financeiro_cemei,
            clausula,
            1,
            tipo_lancamento="ALIMENTACOES",
            cei_ou_emei="EMEI",
        )

        descontos = _descontos(
            relatorio_financeiro_cemei, parametrizacao_financeira_cemei
        )

        assert [
            (
                linha["tipo_lancamento"],
                linha["faixa_ou_alimentacao"],
                linha["valor_unitario"],
                linha["total"],
            )
            for linha in descontos["linhas"]
        ] == [
            (
                "ALIMENTAÇÃO - CEI",
                f"Integral - {faixa}",
                Decimal("9.70"),
                Decimal("14.55"),
            ),
            ("ALIMENTAÇÃO - EMEI", "REFEIÇÃO", Decimal("10.00"), Decimal("20.00")),
            ("ALIMENTAÇÃO - EMEI", "KIT LANCHE", Decimal("6.88"), Decimal("3.44")),
        ]
        assert descontos["total"] == Decimal("37.99")

    def test_emebs_busca_o_valor_na_turma_do_desconto(
        self,
        edital,
        vinculo_alimentacao_emebs,
        relatorio_financeiro_emebs,
        parametrizacao_financeira_emebs,
        tipo_alimentacao_refeicao,
    ):
        _altera_unitario(
            parametrizacao_financeira_emebs,
            "15.00",
            tabela__nome__endswith="Fundamental",
            tipo_alimentacao=tipo_alimentacao_refeicao,
        )
        clausula = _clausula(edital, porcentagem="100.00")
        for turma in ("INFANTIL", "FUNDAMENTAL"):
            _cria_desconto(
                relatorio_financeiro_emebs,
                clausula,
                1,
                tipo_lancamento="ALIMENTACOES",
                infantil_ou_fundamental=turma,
                tipo_alimentacao=tipo_alimentacao_refeicao,
            )

        linhas = _descontos(
            relatorio_financeiro_emebs, parametrizacao_financeira_emebs
        )["linhas"]

        assert [
            (linha["tipo_lancamento"], linha["valor_unitario"]) for linha in linhas
        ] == [
            ("ALIMENTAÇÃO - INFANTIL", Decimal("10.00")),
            ("ALIMENTAÇÃO - FUNDAMENTAL", Decimal("15.00")),
        ]

    def test_cieja_usa_a_linha_de_refeicao_cieja_e_cmct(
        self,
        edital,
        vinculo_alimentacao_cieja,
        relatorio_financeiro_cieja,
        parametrizacao_financeira_cieja,
        tipo_alimentacao_refeicao,
    ):
        _cria_desconto(
            relatorio_financeiro_cieja,
            _clausula(edital, porcentagem="100.00"),
            1,
            tipo_lancamento="DIETAS_TIPO_A",
            tipo_alimentacao=tipo_alimentacao_refeicao,
        )

        [linha] = _descontos(
            relatorio_financeiro_cieja, parametrizacao_financeira_cieja
        )["linhas"]

        assert linha["faixa_ou_alimentacao"] == "REFEIÇÃO CIEJA E CMCT"
        assert linha["valor_unitario"] == Decimal("11.22")

    def test_varias_unidades_geram_uma_linha_sem_multiplicar_o_total(
        self,
        edital,
        vinculo_alimentacao_emef,
        relatorio_financeiro_emef,
        parametrizacao_financeira_emef,
        tipo_alimentacao_refeicao,
    ):
        _cria_desconto(
            relatorio_financeiro_emef,
            _clausula(edital, porcentagem="100.00"),
            1,
            unidades=("EMEF ZETA", "EMEF ALFA"),
            tipo_lancamento="ALIMENTACOES",
            tipo_alimentacao=tipo_alimentacao_refeicao,
        )

        descontos = _descontos(
            relatorio_financeiro_emef, parametrizacao_financeira_emef
        )

        assert len(descontos["linhas"]) == 1
        assert descontos["linhas"][0]["unidades"] == ["EMEF ALFA", "EMEF ZETA"]
        assert descontos["total"] == Decimal("21.00")

    def test_total_d_soma_as_linhas_arredondadas(
        self,
        edital,
        vinculo_alimentacao_emef,
        relatorio_financeiro_emef,
        parametrizacao_financeira_emef,
        tipo_alimentacao_lanche_4h,
    ):
        clausula = _clausula(edital, porcentagem="1.00")
        for _ in range(2):
            _cria_desconto(
                relatorio_financeiro_emef,
                clausula,
                1,
                tipo_lancamento="ALIMENTACOES",
                tipo_alimentacao=tipo_alimentacao_lanche_4h,
            )

        descontos = _descontos(
            relatorio_financeiro_emef, parametrizacao_financeira_emef
        )

        assert [linha["total"] for linha in descontos["linhas"]] == [
            Decimal("0.05"),
            Decimal("0.05"),
        ]
        assert descontos["total"] == Decimal("0.10")

    def test_ordena_pela_data_de_registro(
        self,
        edital,
        vinculo_alimentacao_emef,
        relatorio_financeiro_emef,
        parametrizacao_financeira_emef,
    ):
        clausula = _clausula(edital)
        with freeze_time("2026-10-02 10:00:00"):
            _cria_desconto(
                relatorio_financeiro_emef,
                clausula,
                1,
                unidades=("EMEF SEGUNDA",),
                tipo_lancamento="ALIMENTACOES",
            )
        with freeze_time("2026-10-01 10:00:00"):
            _cria_desconto(
                relatorio_financeiro_emef,
                clausula,
                1,
                unidades=("EMEF PRIMEIRA",),
                tipo_lancamento="ALIMENTACOES",
            )

        linhas = _descontos(relatorio_financeiro_emef, parametrizacao_financeira_emef)[
            "linhas"
        ]

        assert [linha["unidades"] for linha in linhas] == [
            ["EMEF PRIMEIRA"],
            ["EMEF SEGUNDA"],
        ]

    def test_sem_descontos_retorna_tabela_vazia(
        self, relatorio_financeiro_cei, parametrizacao_financeira_cei
    ):
        assert _descontos(relatorio_financeiro_cei, parametrizacao_financeira_cei) == {
            "titulo_faixa_ou_alimentacao": "FAIXA ETÁRIA",
            "linhas": [],
            "total": Decimal("0"),
        }


@pytest.mark.parametrize(
    "grupo_nome, titulo",
    [
        (GrupoUnidadeEscolar.GRUPO_1, "FAIXA ETÁRIA"),
        (GrupoUnidadeEscolar.GRUPO_2, "FAIXA ETÁRIA OU ALIMENTAÇÃO"),
        (GrupoUnidadeEscolar.GRUPO_3, "ALIMENTAÇÃO"),
        (GrupoUnidadeEscolar.GRUPO_4, "ALIMENTAÇÃO"),
        (GrupoUnidadeEscolar.GRUPO_5, "ALIMENTAÇÃO"),
        (GrupoUnidadeEscolar.GRUPO_6, "ALIMENTAÇÃO"),
    ],
)
def test_titulo_coluna_faixa_ou_alimentacao_por_grupo(grupo_nome, titulo):
    assert titulo_coluna_faixa_ou_alimentacao(grupo_nome) == titulo


class TestFaturamentoFinal:
    @pytest.mark.parametrize(
        "titulo, rotulo",
        [
            ("CONSOLIDADO TOTAL (A + B + C)", "(A + B + C - D)"),
            (
                "CONSOLIDADO TOTAL (A + B + C + INF. A + INF. B + INF. C)",
                "(A + B + C + INF. A + INF. B + INF. C - D)",
            ),
            (
                "CONSOLIDADO TOTAL (INF. A + INF. B + INF. C + FUND. A + FUND. B "
                "+ FUND. C)",
                "(INF. A + INF. B + INF. C + FUND. A + FUND. B + FUND. C - D)",
            ),
        ],
    )
    def test_subtrai_os_descontos_do_consolidado_geral(self, titulo, rotulo):
        faturamento = montar_faturamento_final(
            {"titulo": titulo, "valor": Decimal("100.00")}, Decimal("12.34")
        )

        assert faturamento == {
            "titulo_valor": f"VALOR DO FATURAMENTO FINAL {rotulo}:",
            "valor": Decimal("87.66"),
            "valor_extenso": "Oitenta e sete reais e sessenta e seis centavos.",
        }

    def test_contexto_usa_o_ultimo_consolidado(self, contexto_grupo_relatorio, edital):
        relatorio = contexto_grupo_relatorio["relatorio"]
        _cria_desconto(
            relatorio,
            _clausula(edital),
            1,
            tipo_lancamento="ALIMENTACOES",
        )
        _gera_medicao_final(relatorio)

        contexto = montar_contexto_folha_medicao_final(
            relatorio, contexto_grupo_relatorio["parametrizacao"]
        )

        assert contexto["faturamento_final"]["valor"] == (
            contexto["consolidados"][-1]["valor"] - contexto["descontos"]["total"]
        )


@pytest.mark.usefixtures("pdf_com_estilos")
class TestDescontosNoPdf:
    @pytest.fixture
    def folha_cei(
        self,
        edital,
        relatorio_financeiro_cei,
        parametrizacao_financeira_cei,
        periodo_escolar_integral,
    ):
        faixa = FaixaEtaria.objects.filter(ativo=True).first()
        _altera_unitario(
            parametrizacao_financeira_cei,
            "9.70",
            tabela__periodo_escolar=periodo_escolar_integral,
            faixa_etaria=faixa,
        )
        _cria_desconto(
            relatorio_financeiro_cei,
            _clausula(edital),
            3,
            unidades=("CEI DIRET JARDIM SANTA TEREZA",),
            tipo_lancamento="ALIMENTACOES",
            faixa_etaria=faixa,
            periodo_escolar=periodo_escolar_integral,
        )
        _gera_medicao_final(relatorio_financeiro_cei)
        contexto = montar_contexto_folha_medicao_final(
            relatorio_financeiro_cei, parametrizacao_financeira_cei
        )
        texto = extrair_texto_de_pdf(
            gerar_relatorio_folha_medicao_final(
                relatorio_financeiro_cei, parametrizacao_financeira_cei
            )
        )
        return contexto, faixa, _sem_espacos(texto)

    def test_tabela_entre_as_tabelas_do_grupo_e_os_consolidados(self, folha_cei):
        _, _, texto = folha_cei

        _assert_em_ordem(
            texto,
            [
                "TOTAL (C)",
                "TABELA DE DESCONTO",
                "NOME DA UNIDADE",
                "TIPO DE LANÇAMENTO",
                "FAIXA ETÁRIA",
                "CLÁUSULA DO DESCONTO",
                "QUANTIDADE",
                "VALOR UNITÁRIO",
                "TOTAL DO DESCONTO",
                "TOTAL DE DESCONTOS DOS ITENS (D)",
                "CONSOLIDADO TOTAL (A + B + C)",
                "DESCONTOS TOTAIS (D)",
                "VALOR DO FATURAMENTO FINAL (A + B + C - D):",
                "Responsável pela conferência das medições iniciais:",
            ],
        )

    def test_linha_e_totais_com_os_valores_do_contexto(self, folha_cei):
        contexto, faixa, texto = folha_cei
        final = contexto["faturamento_final"]

        assert (
            _sem_espacos(
                "CEI DIRET JARDIM SANTA TEREZA ALIMENTAÇÃO "
                f"Integral - {faixa} 7.2.2. item a - (50%) 3 R$ 9,70 R$ 14,55"
            )
            in texto
        )
        assert "TOTALDEDESCONTOSDOSITENS(D)R$14,55" in texto
        assert "FAIXAETÁRIAOUALIMENTAÇÃO" not in texto
        assert "DESCONTOSTOTAIS(D)R$14,55CONFORMEITENSNASTABELAS" in texto
        assert (
            f"R${agrupador_milhar_com_decimal(final['valor'])}"
            f"({_sem_espacos(final['valor_extenso'])})"
        ) in texto

    def test_muitos_descontos_quebram_paginas_sem_perder_linhas(
        self, edital, relatorio_financeiro_emef, parametrizacao_financeira_emef
    ):
        clausula = _clausula(edital)
        for indice in range(45):
            _cria_desconto(
                relatorio_financeiro_emef,
                clausula,
                1,
                unidades=(f"EMEF UNIDADE {indice:02d}",),
                tipo_lancamento="ALIMENTACOES",
            )
        _gera_medicao_final(relatorio_financeiro_emef)

        paginas = _paginas(
            gerar_relatorio_folha_medicao_final(
                relatorio_financeiro_emef, parametrizacao_financeira_emef
            )
        )
        texto = "\n".join(paginas)

        assert len(paginas) > 2
        for indice in range(45):
            assert texto.count(f"EMEF UNIDADE {indice:02d}") == 1
        for numero, pagina in enumerate(paginas, start=1):
            assert pagina.count("FOLHA DE MEDIÇÃO FINAL") == 1
            assert f"Página {numero}/{len(paginas)}" in pagina
        assert "Responsável pela Empresa Contratada" in paginas[-1]
