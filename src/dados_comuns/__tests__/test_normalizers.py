from ..normalizers import normalizar_nome_categoria


def test_normalizar_nome_categoria_remove_acentos():
    resultado = normalizar_nome_categoria("Alimentação")

    assert resultado == "alimentacao"


def test_normalizar_nome_categoria_remove_espacos_das_extremidades():
    resultado = normalizar_nome_categoria("  categoria de produtos  ")

    assert resultado == "categoria de produtos"


def test_normalizar_nome_categoria_ignora_maiusculas_e_minusculas():
    resultado = normalizar_nome_categoria("CADASTRO DE PRODUTOS")

    assert resultado == "cadastro de produtos"

def test_normalizar_nome_categoria_remove_acentos_e_cedilha():
    resultado = normalizar_nome_categoria(
        "Alimentação, Nutrição e Educação"
    )

    assert resultado == "alimentacao, nutricao e educacao"


def test_normalizar_nome_categoria_remove_espacos_das_extremidades():
    resultado = normalizar_nome_categoria(
        "  Gestão de Produção e Distribuição  "
    )

    assert resultado == "gestao de producao e distribuicao"


def test_normalizar_nome_categoria_ignora_maiusculas_e_minusculas():
    resultado = normalizar_nome_categoria(
        "DúViDaS FrEqUeNtEs SoBrE ReFeIçÕeS"
    )

    assert resultado == "duvidas frequentes sobre refeicoes"