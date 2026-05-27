import pytest

from src.medicao_inicial.models import ValorMedicao
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_cemei import (
    buscar_alimentacoes_recreio_cemei,
    existe_colaborador_cemei,
    validate_lancamento_alimentacoes_medicao_recreio_cemei,
    validate_lancamento_dietas_medicao_recreio_cemei,
)
from utility.carga_dados.perfil.importa_dados import Q

pytestmark = pytest.mark.django_db
GRUPO_CEI = "Recreio nas Férias - de 0 a 3 anos e 11 meses"
GRUPO_EMEI = "Recreio nas Férias - 4 a 14 anos"
GRUPO_COLABORADORES = "Colaboradores"


def test_validate_lancamento_alimentacoes_medicao_recreio_cemei(
    solicitacao_recreio_cemei,
):

    lista_erros = []
    validate_lancamento_alimentacoes_medicao_recreio_cemei(
        solicitacao_recreio_cemei, lista_erros
    )
    assert len(lista_erros) == 0


def test_validate_lancamento_alimentacoes_medicao_recreio_cemei_dados_nao_lancados_emei(
    solicitacao_recreio_cemei,
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        nome_campo="sobremesa",
        dia="17",
    )
    assert valores.count() == 2
    valores.delete()
    assert valores.count() == 0
    lista_erros = []
    validate_lancamento_alimentacoes_medicao_recreio_cemei(
        solicitacao_recreio_cemei, lista_erros
    )
    assert len(lista_erros) == 2
    erros_esperados = [
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": "Colaboradores",
        },
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": "Recreio nas Férias - 4 a 14 anos",
        },
    ]

    for esperado in erros_esperados:
        assert esperado in lista_erros, f"Elemento {esperado} não encontrado"


def test_validate_lancamento_alimentacoes_medicao_recreio_cemei_dados_nao_lancados_cei(
    solicitacao_recreio_cemei, categoria_medicao
):
    valores = ValorMedicao.objects.filter(
        medicao__grupo__nome__in=[GRUPO_CEI, GRUPO_COLABORADORES],
        nome_campo="frequencia",
        dia="17",
        categoria_medicao=categoria_medicao,
    )
    assert valores.count() == 9
    valores.delete()
    lista_erros = []

    lista_erros = validate_lancamento_alimentacoes_medicao_recreio_cemei(
        solicitacao_recreio_cemei,
        lista_erros,
    )

    assert len(lista_erros) == 2
    erros_esperados = [
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": "Colaboradores",
        },
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": "Recreio nas Férias - de 0 a 3 anos e 11 meses",
        },
    ]

    for esperado in erros_esperados:
        assert esperado in lista_erros, f"Elemento {esperado} não encontrado"


def test_validate_lancamento_alimentacoes_medicao_recreio_cemei_dados_nao_lancados_geral(
    solicitacao_recreio_cemei, categoria_medicao
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        nome_campo="frequencia",
        dia="17",
        categoria_medicao=categoria_medicao,
    )
    assert valores.count() == 10
    valores.delete()
    lista_erros = []

    lista_erros = validate_lancamento_alimentacoes_medicao_recreio_cemei(
        solicitacao_recreio_cemei,
        lista_erros,
    )

    assert len(lista_erros) == 3
    erros_esperados = [
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": "Colaboradores",
        },
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": "Recreio nas Férias - de 0 a 3 anos e 11 meses",
        },
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": "Recreio nas Férias - 4 a 14 anos",
        },
    ]

    for esperado in erros_esperados:
        assert esperado in lista_erros, f"Elemento {esperado} não encontrado"


def test_validate_lancamento_dietas_medicao_recreio_cemei(solicitacao_recreio_cemei):
    lista_erros = []
    validate_lancamento_dietas_medicao_recreio_cemei(
        solicitacao_recreio_cemei, lista_erros
    )
    assert len(lista_erros) == 0


def test_validate_lancamento_dietas_medicao_recreio_cemei_dados_nao_lancados_emei(
    solicitacao_recreio_cemei, categoria_medicao_dieta_a_enteral_aminoacidos
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        nome_campo="refeicao",
        dia="17",
        categoria_medicao=categoria_medicao_dieta_a_enteral_aminoacidos,
    )
    assert valores.count() == 1
    valores.delete()
    assert valores.count() == 0
    lista_erros = []
    validate_lancamento_dietas_medicao_recreio_cemei(
        solicitacao_recreio_cemei, lista_erros
    )
    assert len(lista_erros) == 1
    assert lista_erros == [
        {
            "erro": "Restam dias a serem lançados nas dietas.",
            "periodo_escolar": "Recreio nas Férias - 4 a 14 anos",
        }
    ]


def test_validate_lancamento_dietas_medicao_recreio_cemei_dados_nao_lancados_cei(
    solicitacao_recreio_cemei, categoria_medicao_dieta_a
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        nome_campo="frequencia",
        dia="17",
        categoria_medicao=categoria_medicao_dieta_a,
    )
    assert valores.count() == 8
    valores.delete()
    assert valores.count() == 0
    lista_erros = []
    validate_lancamento_dietas_medicao_recreio_cemei(
        solicitacao_recreio_cemei, lista_erros
    )
    assert len(lista_erros) == 1
    assert lista_erros == [
        {
            "erro": "Restam dias a serem lançados nas dietas.",
            "periodo_escolar": "Recreio nas Férias - de 0 a 3 anos e 11 meses",
        }
    ]


def test_validate_lancamento_dietas_medicao_recreio_cemei_dados_nao_lancados_geral(
    solicitacao_recreio_cemei,
    categoria_medicao_dieta_a,
    categoria_medicao_dieta_a_enteral_aminoacidos,
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        dia="17",
        nome_campo__in=["frequencia", "refeicao"],
        categoria_medicao__in=[
            categoria_medicao_dieta_a,
            categoria_medicao_dieta_a_enteral_aminoacidos,
        ],
    )
    assert valores.count() == 10
    valores.delete()
    assert valores.count() == 0
    lista_erros = []
    lista_erros = validate_lancamento_dietas_medicao_recreio_cemei(
        solicitacao_recreio_cemei, lista_erros
    )
    assert len(lista_erros) == 2
    erros_esperados = [
        {
            "erro": "Restam dias a serem lançados nas dietas.",
            "periodo_escolar": "Recreio nas Férias - 4 a 14 anos",
        },
        {
            "erro": "Restam dias a serem lançados nas dietas.",
            "periodo_escolar": "Recreio nas Férias - de 0 a 3 anos e 11 meses",
        },
    ]

    for esperado in erros_esperados:
        assert esperado in lista_erros, f"Elemento {esperado} não encontrado"


def test_buscar_alimentacoes_recreio_cemei(solicitacao_recreio_cemei):
    resultado = buscar_alimentacoes_recreio_cemei(solicitacao_recreio_cemei)
    assert len(resultado) == 3

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

    alimentacoes_inscritos = ["Refeição", "Sobremesa", "Lanche", "Almoço"]
    assert "Inscritos" in resultado
    assert len(resultado["Inscritos"]) == 4
    for esperado in alimentacoes_inscritos:
        assert esperado in resultado["Inscritos"], f"Elemento {esperado} não encontrado"


def test_existe_colaborador_cemei(solicitacao_recreio_cemei):
    participantes = dict()
    for (
        participante
    ) in solicitacao_recreio_cemei.recreio_nas_ferias.unidades_participantes.filter(
        unidade_educacional=solicitacao_recreio_cemei.escola
    ):
        participantes[participante.cei_ou_emei] = participante

    participantes_cei = participantes.get("CEI")
    participantes_emei = participantes.get("EMEI")
    assert existe_colaborador_cemei(participantes_cei, participantes_emei) is True


def test_existe_colaborador_cemei_retorna_false_quando_nao_tem_colaboradores(
    solicitacao_recreio_cemei,
):
    participantes = dict()
    for (
        participante
    ) in solicitacao_recreio_cemei.recreio_nas_ferias.unidades_participantes.filter(
        unidade_educacional=solicitacao_recreio_cemei.escola
    ):
        participante.num_colaboradores = 0
        participante.save()
        participantes[participante.cei_ou_emei] = participante

    participantes_cei = participantes.get("CEI")
    participantes_emei = participantes.get("EMEI")
    assert existe_colaborador_cemei(participantes_cei, participantes_emei) is False


def test_existe_colaborador_cemei_retorna_true_quando_so_tem_colaboradores_cei(
    solicitacao_recreio_cemei,
):
    participantes = dict()
    for (
        participante
    ) in solicitacao_recreio_cemei.recreio_nas_ferias.unidades_participantes.filter(
        unidade_educacional=solicitacao_recreio_cemei.escola
    ):
        if participante.cei_ou_emei == "EMEI":
            participante.num_colaboradores = 0
            participante.save()
        participantes[participante.cei_ou_emei] = participante

    participantes_cei = participantes.get("CEI")
    participantes_emei = participantes.get("EMEI")
    assert existe_colaborador_cemei(participantes_cei, participantes_emei) is True


def test_existe_colaborador_cemei_retorna_true_quando_so_tem_colaboradores_emei(
    solicitacao_recreio_cemei,
):
    participantes = dict()
    for (
        participante
    ) in solicitacao_recreio_cemei.recreio_nas_ferias.unidades_participantes.filter(
        unidade_educacional=solicitacao_recreio_cemei.escola
    ):
        if participante.cei_ou_emei == "CEI":
            participante.num_colaboradores = 0
            participante.save()
        participantes[participante.cei_ou_emei] = participante

    participantes_cei = participantes.get("CEI")
    participantes_emei = participantes.get("EMEI")
    assert existe_colaborador_cemei(participantes_cei, participantes_emei) is True


def test_existe_colaborador_cemei_retorna_false_quando_nao_tem_tipos_alimentacao_com_colaboradores(
    solicitacao_recreio_cemei,
):
    participantes = dict()
    for (
        participante
    ) in solicitacao_recreio_cemei.recreio_nas_ferias.unidades_participantes.filter(
        unidade_educacional=solicitacao_recreio_cemei.escola
    ):
        participante.tipos_alimentacao.filter(categoria__nome="Colaboradores").delete()
        participantes[participante.cei_ou_emei] = participante

    participantes_cei = participantes.get("CEI")
    participantes_emei = participantes.get("EMEI")

    assert participantes_cei.num_colaboradores > 0
    assert participantes_emei.num_colaboradores > 0
    assert existe_colaborador_cemei(participantes_cei, participantes_emei) is False


def test_existe_colaborador_cemei_retorna_false_quando_nao_tem_tipos_alimentacao_com_colaboradores(
    solicitacao_recreio_cemei,
):
    participantes = dict()
    for (
        participante
    ) in solicitacao_recreio_cemei.recreio_nas_ferias.unidades_participantes.filter(
        unidade_educacional=solicitacao_recreio_cemei.escola
    ):
        participante.tipos_alimentacao.filter(categoria__nome="Colaboradores").delete()
        participantes[participante.cei_ou_emei] = participante

    participantes_cei = participantes.get("CEI")
    participantes_emei = participantes.get("EMEI")

    assert participantes_cei.num_colaboradores > 0
    assert participantes_emei.num_colaboradores > 0
    assert existe_colaborador_cemei(participantes_cei, participantes_emei) is False


def test_existe_colaborador_cemei_retorna_true_quando_so_tem_tipos_alimentacao_com_colaboradores_cei(
    solicitacao_recreio_cemei,
):
    participantes = dict()
    for (
        participante
    ) in solicitacao_recreio_cemei.recreio_nas_ferias.unidades_participantes.filter(
        unidade_educacional=solicitacao_recreio_cemei.escola
    ):
        if participante.cei_ou_emei == "EMEI":
            participante.tipos_alimentacao.filter(
                categoria__nome="Colaboradores"
            ).delete()
        participantes[participante.cei_ou_emei] = participante

    participantes_cei = participantes.get("CEI")
    participantes_emei = participantes.get("EMEI")

    assert participantes_cei.num_colaboradores > 0
    assert participantes_emei.num_colaboradores > 0
    assert existe_colaborador_cemei(participantes_cei, participantes_emei) is True


def test_existe_colaborador_cemei_retorna_true_quando_so_tem_tipos_alimentacao_com_colaboradores_emei(
    solicitacao_recreio_cemei,
):
    participantes = dict()
    for (
        participante
    ) in solicitacao_recreio_cemei.recreio_nas_ferias.unidades_participantes.filter(
        unidade_educacional=solicitacao_recreio_cemei.escola
    ):
        if participante.cei_ou_emei == "CEI":
            participante.tipos_alimentacao.filter(
                categoria__nome="Colaboradores"
            ).delete()
        participantes[participante.cei_ou_emei] = participante

    participantes_cei = participantes.get("CEI")
    participantes_emei = participantes.get("EMEI")

    assert participantes_cei.num_colaboradores > 0
    assert participantes_emei.num_colaboradores > 0
    assert existe_colaborador_cemei(participantes_cei, participantes_emei) is True
