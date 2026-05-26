import pytest

from src.medicao_inicial.models import ValorMedicao
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_common import (
    agrupar_tipos_alimentacao_por_categoria,
    existe_colaborador,
    get_classificacoes_dietas_recreio,
    get_linhas_da_tabela_alimentacoes_recreio,
    get_tipos_alimentacao_recreio,
    valida_campo_participantes,
)

pytestmark = pytest.mark.django_db


def test_agrupar_tipos_alimentacao_por_categoria_recreio_emef(solicitacao_recreio_emef):
    recreio = solicitacao_recreio_emef.recreio_nas_ferias
    participantes = recreio.unidades_participantes.first()

    tipos_alimentacao = participantes.tipos_alimentacao.filter(
        categoria__nome__in=["Inscritos", "Colaboradores"]
    )

    resultado = agrupar_tipos_alimentacao_por_categoria(tipos_alimentacao)

    alimentacoes = ["Refeição", "Sobremesa"]
    assert "Colaboradores" in resultado
    for esperado in alimentacoes:
        assert (
            esperado in resultado["Colaboradores"]
        ), f"Elemento {esperado} não encontrado"

    assert "Inscritos" in resultado
    for esperado in alimentacoes:
        assert esperado in resultado["Inscritos"], f"Elemento {esperado} não encontrado"


def test_valida_campo_participantes_recreio_emef(solicitacao_recreio_emef):

    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        nome_campo="participantes",
    )
    assert valores.count() == 42
    valores.delete()
    assert valores.count() == 0

    quantidade_antes = ValorMedicao.objects.count()

    participantes = (
        solicitacao_recreio_emef.recreio_nas_ferias.unidades_participantes.filter(
            unidade_educacional=solicitacao_recreio_emef.escola
        ).first()
    )
    informacoes_participantes = informacoes_participantes = {
        "Recreio nas Férias": participantes.num_inscritos,
        "Colaboradores": participantes.num_colaboradores,
    }
    valida_campo_participantes(solicitacao_recreio_emef, informacoes_participantes)

    quantidade_depois = ValorMedicao.objects.count()

    assert quantidade_depois > quantidade_antes

    valores_depois = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        nome_campo="participantes",
    )

    assert valores_depois.count() == 42


def test_existe_colaborador_recreio_emef(
    solicitacao_recreio_emef,
):
    participante = (
        solicitacao_recreio_emef.recreio_nas_ferias.unidades_participantes.first()
    )
    assert existe_colaborador(participante) is True


def test_get_tipos_alimentacao_recreio_emef(solicitacao_recreio_emef):

    resultado = get_tipos_alimentacao_recreio(solicitacao_recreio_emef)
    alimentacoes = ["Refeição", "Sobremesa"]

    assert len(resultado) == 2
    for esperado in alimentacoes:
        assert esperado in resultado, f"Elemento {esperado} não encontrado"


def test_agrupar_tipos_alimentacao_por_categoria_recreio_cei(solicitacao_recreio_cei):
    recreio = solicitacao_recreio_cei.recreio_nas_ferias
    participantes = recreio.unidades_participantes.first()

    tipos_alimentacao = participantes.tipos_alimentacao.filter(
        categoria__nome__in=["Inscritos", "Colaboradores"]
    )

    resultado = agrupar_tipos_alimentacao_por_categoria(tipos_alimentacao)

    assert "Colaboradores" in resultado
    colaboradores = ["Refeição", "Sobremesa"]
    assert len(resultado["Colaboradores"]) == 2
    for esperado in colaboradores:
        assert (
            esperado in resultado["Colaboradores"]
        ), f"Elemento {esperado} não encontrado"

    assert "Inscritos" in resultado
    inscritos = ["Refeição", "Sobremesa", "Lanche", "Lanche 4h", "Almoço"]
    assert len(resultado["Inscritos"]) == 5
    for esperado in inscritos:
        assert esperado in resultado["Inscritos"], f"Elemento {esperado} não encontrado"


def test_valida_campo_participantes_recreio_cei(solicitacao_recreio_cei):

    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        nome_campo="participantes",
    )
    assert valores.count() == 28
    valores.delete()
    assert valores.count() == 0

    quantidade_antes = ValorMedicao.objects.count()

    participantes = (
        solicitacao_recreio_cei.recreio_nas_ferias.unidades_participantes.filter(
            unidade_educacional=solicitacao_recreio_cei.escola
        ).first()
    )
    informacoes_participantes = informacoes_participantes = {
        "Recreio nas Férias": participantes.num_inscritos,
        "Colaboradores": participantes.num_colaboradores,
    }
    valida_campo_participantes(solicitacao_recreio_cei, informacoes_participantes)

    quantidade_depois = ValorMedicao.objects.count()

    assert quantidade_depois > quantidade_antes

    valores_depois = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        nome_campo="participantes",
    )

    assert valores_depois.count() == 42


def test_existe_colaborador_recreio_cei(
    solicitacao_recreio_cei,
):
    participante = (
        solicitacao_recreio_cei.recreio_nas_ferias.unidades_participantes.first()
    )
    assert existe_colaborador(participante) is True


def test_get_tipos_alimentacao_recreio_cei(solicitacao_recreio_cei):

    resultado = get_tipos_alimentacao_recreio(solicitacao_recreio_cei)
    alimentacoes = ["Refeição", "Sobremesa", "Lanche", "Lanche 4h", "Almoço"]

    assert len(resultado) == 5
    for esperado in alimentacoes:
        assert esperado in resultado, f"Elemento {esperado} não encontrado"


def test_get_linhas_da_tabela_alimentacoes_recreio():
    resultado = get_linhas_da_tabela_alimentacoes_recreio(
        ["Refeição", "Sobremesa", "Lanche"]
    )

    alimentacoes = [
        "participantes",
        "frequencia",
        "refeicao",
        "repeticao_refeicao",
        "sobremesa",
        "repeticao_sobremesa",
        "lanche",
    ]
    assert len(resultado) == 7
    for esperado in alimentacoes:
        assert esperado in resultado, f"Elemento {esperado} não encontrado"


def test_get_linhas_sem_refeicao_nao_adiciona_repeticao():
    resultado = get_linhas_da_tabela_alimentacoes_recreio(["Lanche"])

    campos = [
        "participantes",
        "frequencia",
        "lanche",
    ]
    assert len(resultado) == 3
    for esperado in campos:
        assert esperado in resultado, f"Elemento {esperado} não encontrado"


def test_get_linhas_adiciona_repeticao_sobremesa():
    resultado = get_linhas_da_tabela_alimentacoes_recreio(["Sobremesa"])

    campos = [
        "participantes",
        "frequencia",
        "sobremesa",
        "repeticao_sobremesa",
    ]
    assert len(resultado) == 4
    for esperado in campos:
        assert esperado in resultado, f"Elemento {esperado} não encontrado"


def test_get_classificacoes_dietas_recreio(
    categoria_medicao_dieta_a_enteral_aminoacidos,
    categoria_medicao_dieta_b,
    categoria_medicao_dieta_a,
):
    categorias = [
        categoria_medicao_dieta_a_enteral_aminoacidos,
        categoria_medicao_dieta_b,
        categoria_medicao_dieta_a,
    ]

    resultado = get_classificacoes_dietas_recreio(
        categorias,
        ["Lanche", "Refeição"],
    )

    assert categoria_medicao_dieta_a_enteral_aminoacidos in resultado
    assert categoria_medicao_dieta_b in resultado
    assert categoria_medicao_dieta_a in resultado


def test_get_classificacoes_dietas_recreio_sem_lanche(
    categoria_medicao_dieta_a_enteral_aminoacidos,
    categoria_medicao_dieta_b,
    categoria_medicao_dieta_a,
):
    categorias = [
        categoria_medicao_dieta_a_enteral_aminoacidos,
        categoria_medicao_dieta_b,
        categoria_medicao_dieta_a,
    ]

    resultado = get_classificacoes_dietas_recreio(
        categorias,
        ["Refeição"],
    )

    assert categoria_medicao_dieta_a_enteral_aminoacidos in resultado
    assert categoria_medicao_dieta_b not in resultado
    assert categoria_medicao_dieta_a not in resultado
