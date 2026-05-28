import pytest
from rest_framework.serializers import ValidationError

from src.cardapio.base.models import TipoAlimentacao
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
GRUPO_CEI = "Recreio nas Férias - de 0 a 3 anos e 11 meses"
GRUPO_EMEI = "Recreio nas Férias - 4 a 14 anos"
GRUPO_COLABORADORES = "Colaboradores"


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


def test_agrupar_tipos_alimentacao_por_categoria_recreio_cemei(
    solicitacao_recreio_cemei,
):
    recreio = solicitacao_recreio_cemei.recreio_nas_ferias
    participantes = dict()
    tipos_alimentacao = TipoAlimentacao.objects.none()
    for participante in recreio.unidades_participantes.filter(
        unidade_educacional=solicitacao_recreio_cemei.escola
    ):
        alimentacoes = participante.tipos_alimentacao.filter(
            categoria__nome__in=["Infantil", "Inscritos", "Colaboradores"]
        )
        tipos_alimentacao = tipos_alimentacao | alimentacoes
        participantes[participante.cei_ou_emei] = participante

    resultado = agrupar_tipos_alimentacao_por_categoria(tipos_alimentacao)

    alimentacoes = ["Refeição", "Sobremesa"]
    assert "Colaboradores" in resultado
    assert len(resultado["Colaboradores"]) == 2
    for esperado in alimentacoes:
        assert (
            esperado in resultado["Colaboradores"]
        ), f"Elemento {esperado} não encontrado"

    assert "Infantil" in resultado
    assert len(resultado["Infantil"]) == 2
    for esperado in alimentacoes:
        assert esperado in resultado["Infantil"], f"Elemento {esperado} não encontrado"

    assert "Inscritos" in resultado
    inscritos = ["Refeição", "Sobremesa", "Lanche", "Almoço"]
    assert len(resultado["Inscritos"]) == 4
    for esperado in inscritos:
        assert esperado in resultado["Inscritos"], f"Elemento {esperado} não encontrado"


def test_valida_campo_participantes_recreio_cemei(solicitacao_recreio_cemei):

    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        nome_campo="participantes",
    )
    assert valores.count() == 63
    valores.delete()
    assert valores.count() == 0

    quantidade_antes = ValorMedicao.objects.count()

    participantes = dict()
    for (
        participante
    ) in solicitacao_recreio_cemei.recreio_nas_ferias.unidades_participantes.filter(
        unidade_educacional=solicitacao_recreio_cemei.escola
    ):
        participantes[participante.cei_ou_emei] = participante

    participantes_cei = participantes.get("CEI")
    participantes_emei = participantes.get("EMEI")
    informacoes_participantes = informacoes_participantes = {
        GRUPO_CEI: participantes_cei.num_inscritos,
        GRUPO_EMEI: participantes_emei.num_colaboradores,
        GRUPO_COLABORADORES: participantes_cei.num_colaboradores
        + participantes_emei.num_colaboradores,
    }
    valida_campo_participantes(solicitacao_recreio_cemei, informacoes_participantes)

    quantidade_depois = ValorMedicao.objects.count()

    assert quantidade_depois > quantidade_antes

    valores_depois = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        nome_campo="participantes",
    )

    assert valores_depois.count() == 63


def test_existe_colaborador_recreio_cemei(
    solicitacao_recreio_cemei,
):
    participante = (
        solicitacao_recreio_cemei.recreio_nas_ferias.unidades_participantes.first()
    )
    with pytest.raises(
        ValidationError,
        match="Método incorreto para validar colaboradores de unidades CEMEI.",
    ):
        existe_colaborador(participante)


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
