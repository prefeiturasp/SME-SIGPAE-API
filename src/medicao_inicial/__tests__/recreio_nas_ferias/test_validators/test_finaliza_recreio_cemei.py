import pytest

from src.medicao_inicial.models import ValorMedicao
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_cemei import (
    buscar_alimentacoes_recreio_cemei,
    buscar_erro_por_periodo,
    cria_valores_medicao_participantes_cemei,
    cria_valores_medicao_participantes_dietas_autorizadas_cemei,
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
            "periodo_escolar": GRUPO_COLABORADORES,
        },
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": GRUPO_EMEI,
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
            "periodo_escolar": GRUPO_COLABORADORES,
        },
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": GRUPO_CEI,
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
            "periodo_escolar": GRUPO_COLABORADORES,
        },
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": GRUPO_CEI,
        },
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": GRUPO_EMEI,
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
            "periodo_escolar": GRUPO_EMEI,
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
            "periodo_escolar": GRUPO_CEI,
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
            "periodo_escolar": GRUPO_EMEI,
        },
        {
            "erro": "Restam dias a serem lançados nas dietas.",
            "periodo_escolar": GRUPO_CEI,
        },
    ]

    for esperado in erros_esperados:
        assert esperado in lista_erros, f"Elemento {esperado} não encontrado"


def test_buscar_alimentacoes_recreio_cemei(solicitacao_recreio_cemei):
    resultado = buscar_alimentacoes_recreio_cemei(solicitacao_recreio_cemei)
    assert len(resultado) == 3

    alimentacoes = ["Refeição", "Sobremesa"]
    assert GRUPO_COLABORADORES in resultado
    assert len(resultado[GRUPO_COLABORADORES]) == 2
    for esperado in alimentacoes:
        assert (
            esperado in resultado[GRUPO_COLABORADORES]
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
        participante.tipos_alimentacao.filter(
            categoria__nome=GRUPO_COLABORADORES
        ).delete()
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
        participante.tipos_alimentacao.filter(
            categoria__nome=GRUPO_COLABORADORES
        ).delete()
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
                categoria__nome=GRUPO_COLABORADORES
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
                categoria__nome=GRUPO_COLABORADORES
            ).delete()
        participantes[participante.cei_ou_emei] = participante

    participantes_cei = participantes.get("CEI")
    participantes_emei = participantes.get("EMEI")

    assert participantes_cei.num_colaboradores > 0
    assert participantes_emei.num_colaboradores > 0
    assert existe_colaborador_cemei(participantes_cei, participantes_emei) is True


def test_cria_valores_medicao_participantes_cemei(solicitacao_recreio_cemei):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        nome_campo="participantes",
    )
    assert valores.count() == 63
    valores.delete()
    assert valores.count() == 0

    quantidade_antes = ValorMedicao.objects.count()

    cria_valores_medicao_participantes_cemei(solicitacao_recreio_cemei)

    quantidade_depois = ValorMedicao.objects.count()

    assert quantidade_depois > quantidade_antes

    valores_depois = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        nome_campo="participantes",
    )

    assert valores_depois.count() == 63


def test_cria_valores_medicao_participantes_cemei_nao_duplica_registros(
    solicitacao_recreio_cemei,
):
    quantidade_antes = ValorMedicao.objects.count()

    cria_valores_medicao_participantes_cemei(solicitacao_recreio_cemei)
    quantidade_depois_primeira_execucao = ValorMedicao.objects.count()

    cria_valores_medicao_participantes_cemei(solicitacao_recreio_cemei)
    quantidade_depois_segunda_execucao = ValorMedicao.objects.count()

    assert quantidade_depois_primeira_execucao == quantidade_depois_segunda_execucao

    assert quantidade_depois_segunda_execucao >= quantidade_antes


def test_cria_medicao_quando_grupo_nao_existe(
    solicitacao_recreio_cemei,
):
    solicitacao_recreio_cemei.medicoes.all().delete()

    cria_valores_medicao_participantes_cemei(solicitacao_recreio_cemei)

    assert solicitacao_recreio_cemei.medicoes.exists()
    assert solicitacao_recreio_cemei.medicoes.count() == 3


def test_cria_valores_medicao_participantes_cemei_sem_tipo_alimentacao_colaboradores(
    solicitacao_recreio_cemei,
):
    participantes = dict()
    for (
        participante
    ) in solicitacao_recreio_cemei.recreio_nas_ferias.unidades_participantes.filter(
        unidade_educacional=solicitacao_recreio_cemei.escola
    ):

        participante.tipos_alimentacao.filter(
            categoria__nome=GRUPO_COLABORADORES
        ).delete()
        participantes[participante.cei_ou_emei] = participante

    participantes_cei = participantes.get("CEI")
    participantes_emei = participantes.get("EMEI")

    assert participantes_cei.num_colaboradores > 0
    assert participantes_emei.num_colaboradores > 0
    assert existe_colaborador_cemei(participantes_cei, participantes_emei) is False

    ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        nome_campo="participantes",
    ).delete()

    cria_valores_medicao_participantes_cemei(solicitacao_recreio_cemei)

    participantes_cei_valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        medicao__grupo__nome=GRUPO_CEI,
        nome_campo="participantes",
    )
    participantes_emei_valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        medicao__grupo__nome=GRUPO_EMEI,
        nome_campo="participantes",
    )
    colaboradores_valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        medicao__grupo__nome=GRUPO_COLABORADORES,
        nome_campo="participantes",
    )

    assert participantes_cei_valores.exists()
    assert participantes_emei_valores.exists()
    assert colaboradores_valores.count() == 0


def test_cria_valores_medicao_participantes_dietas_autorizadas_cemei(
    solicitacao_recreio_cemei,
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        nome_campo="dietas_autorizadas",
    )
    assert valores.count() == 126
    valores.delete()
    assert valores.count() == 0

    quantidade_antes = ValorMedicao.objects.count()

    cria_valores_medicao_participantes_dietas_autorizadas_cemei(
        solicitacao_recreio_cemei
    )
    quantidade_depois = ValorMedicao.objects.count()

    assert quantidade_depois > quantidade_antes

    valores_depois = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        nome_campo="dietas_autorizadas",
    )

    assert valores_depois.count() == 189


def test_cria_valores_dietas_nao_cria_sem_logs(
    solicitacao_recreio_cemei,
):
    escola = solicitacao_recreio_cemei.escola

    escola.logs_dietas_autorizadas_recreio_ferias.all().delete()
    escola.logs_dietas_autorizadas_recreio_ferias_cei.all().delete()

    ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        nome_campo="dietas_autorizadas",
    ).delete()

    cria_valores_medicao_participantes_dietas_autorizadas_cemei(
        solicitacao_recreio_cemei
    )

    assert not ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cemei,
        nome_campo="dietas_autorizadas",
    ).exists()


def test_buscar_erro_por_periodo_deve_encontrar_erro_pelo_tipo_erro(
    solicitacao_recreio_cemei,
):

    medicao = solicitacao_recreio_cemei.medicoes.filter(grupo__nome=GRUPO_CEI).first()

    lista_erros = [
        {
            "periodo_escolar": GRUPO_CEI,
            "erro": "Restam dias a serem lançados nas dietas.",
        }
    ]

    resultado = buscar_erro_por_periodo(
        lista_erros=lista_erros,
        medicao=medicao,
        tipo_erro="dietas",
    )

    assert resultado == {
        "erro": "Restam dias a serem lançados nas dietas.",
        "periodo_escolar": GRUPO_CEI,
    }


def test_buscar_erro_por_periodo_deve_usar_grupo(solicitacao_recreio_cemei):
    medicao = solicitacao_recreio_cemei.medicoes.filter(grupo__nome=GRUPO_CEI).first()

    lista_erros = [
        {
            "periodo_escolar": GRUPO_EMEI,
            "erro": "Restam dias a serem lançados nas dietas.",
        }
    ]

    resultado = buscar_erro_por_periodo(
        lista_erros=lista_erros,
        medicao=medicao,
        tipo_erro="dietas",
    )

    assert resultado is None


def test_buscar_erro_por_periodo_deve_retornar_none_quando_nao_existir_periodo_correspondente(
    solicitacao_recreio_cemei,
):
    medicao = solicitacao_recreio_cemei.medicoes.filter(grupo__nome=GRUPO_CEI).first()

    lista_erros = [
        {
            "periodo_escolar": GRUPO_COLABORADORES,
            "erro": "Restam dias a serem lançados nas dietas.",
        }
    ]

    resultado = buscar_erro_por_periodo(
        lista_erros=lista_erros,
        medicao=medicao,
        tipo_erro="dietas",
    )

    assert resultado is None


def test_buscar_erro_por_periodo_deve_retornar_none_quando_tipo_erro_nao_corresponder(
    solicitacao_recreio_cemei,
):
    medicao = solicitacao_recreio_cemei.medicoes.filter(grupo__nome=GRUPO_EMEI).first()

    lista_erros = [
        {
            "periodo_escolar": GRUPO_EMEI,
            "erro": "Restam dias a serem lançados nas dietas.",
        }
    ]

    resultado = buscar_erro_por_periodo(
        lista_erros=lista_erros,
        medicao=medicao,
        tipo_erro="alimentação",
    )

    assert resultado is None


def test_buscar_erro_por_periodo_deve_retornar_apenas_primeiro_erro_encontrado(
    solicitacao_recreio_cemei,
):
    medicao = solicitacao_recreio_cemei.medicoes.filter(grupo__nome=GRUPO_EMEI).first()

    primeiro = {
        "periodo_escolar": GRUPO_EMEI,
        "erro": "Restam dias a serem lançados nas dietas.",
    }

    segundo = {
        "periodo_escolar": GRUPO_EMEI,
        "erro": "Restam dias a serem lançados nas dietas.",
    }

    resultado = buscar_erro_por_periodo(
        lista_erros=[primeiro, segundo],
        medicao=medicao,
        tipo_erro="dietas",
    )

    assert resultado == primeiro
