import datetime

import pytest
from model_bakery import baker

from src.medicao_inicial.models import ValorMedicao
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_common import (
    agrupar_tipos_alimentacao_por_categoria,
    existe_colaborador,
    get_classificacoes_dietas_recreio,
)
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_emef_emei_ceu_gesto_cieja import (
    _categoria_tem_logs_dieta_autorizada,
    cria_valores_medicao_participantes_dietas_autorizadas_emef_emei_cieja_ceugestao,
    cria_valores_medicao_participantes_emef_emei_cieja_ceugestao,
    get_linhas_da_tabela_dieta_recreio,
    indexar_logs_dieta_autorizadas_por_data,
    retorna_valor_para_log_dieta_autorizada,
    validate_lancamento_alimentacoes_medicao_recreio,
    validate_lancamento_dietas_medicao_recreio,
)

pytestmark = pytest.mark.django_db


def test_validate_lancamento_alimentacoes_medicao_recreio(solicitacao_recreio_emef):

    lista_erros = []
    validate_lancamento_alimentacoes_medicao_recreio(
        solicitacao_recreio_emef, lista_erros
    )
    assert len(lista_erros) == 0


def test_validate_lancamento_alimentacoes_medicao_recreio_dados_nao_lancados(
    solicitacao_recreio_emef,
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        nome_campo="sobremesa",
        dia="17",
    )
    assert valores.count() == 2
    valores.delete()
    assert valores.count() == 0
    lista_erros = []
    validate_lancamento_alimentacoes_medicao_recreio(
        solicitacao_recreio_emef, lista_erros
    )
    assert len(lista_erros) == 2
    erros_esperados = [
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": "Colaboradores",
        },
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": "Recreio nas Férias",
        },
    ]

    for esperado in erros_esperados:
        assert esperado in lista_erros, f"Elemento {esperado} não encontrado"


def test_validate_lancamento_dietas_medicao_recreio(solicitacao_recreio_emef):
    lista_erros = []
    validate_lancamento_dietas_medicao_recreio(solicitacao_recreio_emef, lista_erros)
    assert len(lista_erros) == 0


def test_validate_lancamento_dietas_medicao_recreio_dados_nao_lancados(
    solicitacao_recreio_emef, categoria_medicao_dieta_a_enteral_aminoacidos
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        nome_campo="refeicao",
        dia="17",
        categoria_medicao=categoria_medicao_dieta_a_enteral_aminoacidos,
    )
    assert valores.count() == 1
    valores.delete()
    assert valores.count() == 0
    lista_erros = []
    validate_lancamento_dietas_medicao_recreio(solicitacao_recreio_emef, lista_erros)
    assert len(lista_erros) == 1
    assert lista_erros == [
        {
            "erro": "Restam dias a serem lançados nas dietas.",
            "periodo_escolar": "Recreio nas Férias",
        }
    ]


def test_agrupar_tipos_alimentacao_por_categoria(solicitacao_recreio_emef):
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


def test_retorna_valor_para_log_dieta_autorizada_enteral(
    solicitacao_recreio_emef,
    categoria_medicao_dieta_a_enteral_aminoacidos,
):

    escola = solicitacao_recreio_emef.escola
    recreio = solicitacao_recreio_emef.recreio_nas_ferias
    inicio_recreio = recreio.data_inicio
    fim_recreio = recreio.data_fim

    logs_do_recreio = escola.logs_dietas_autorizadas_recreio_ferias.filter(
        data__range=[inicio_recreio, fim_recreio],
    )
    logs_por_dia = indexar_logs_dieta_autorizadas_por_data(logs_do_recreio)
    data = datetime.date(2025, 12, 10)
    resultado = retorna_valor_para_log_dieta_autorizada(
        categoria_medicao_dieta_a_enteral_aminoacidos, logs_por_dia, data
    )

    assert resultado == 3


def test_retorna_valor_para_log_dieta_autorizada_categoria_comum(
    solicitacao_recreio_emef, categoria_medicao_dieta_b
):
    escola = solicitacao_recreio_emef.escola
    recreio = solicitacao_recreio_emef.recreio_nas_ferias
    inicio_recreio = recreio.data_inicio
    fim_recreio = recreio.data_fim

    logs_do_recreio = escola.logs_dietas_autorizadas_recreio_ferias.filter(
        data__range=[inicio_recreio, fim_recreio],
    )
    logs_por_dia = indexar_logs_dieta_autorizadas_por_data(logs_do_recreio)
    data = datetime.date(2025, 12, 10)
    resultado = retorna_valor_para_log_dieta_autorizada(
        categoria_medicao_dieta_b, logs_por_dia, data
    )

    assert resultado == 0


def test_cria_valores_medicao_participantes_emef_emei_cieja_ceugestao(
    solicitacao_recreio_emef,
):

    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        nome_campo="participantes",
    )
    assert valores.count() == 42
    valores.delete()
    assert valores.count() == 0

    quantidade_antes = ValorMedicao.objects.count()

    cria_valores_medicao_participantes_emef_emei_cieja_ceugestao(
        solicitacao_recreio_emef
    )

    quantidade_depois = ValorMedicao.objects.count()

    assert quantidade_depois > quantidade_antes

    valores_depois = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        nome_campo="participantes",
    )

    assert valores_depois.count() == 42


def test_cria_valores_medicao_participantes_dietas_autorizadas_emef_emei_cieja_ceugestao(
    solicitacao_recreio_emef,
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        nome_campo="dietas_autorizadas",
    )
    assert valores.count() == 14
    valores.delete()
    assert valores.count() == 0

    quantidade_antes = ValorMedicao.objects.count()

    cria_valores_medicao_participantes_dietas_autorizadas_emef_emei_cieja_ceugestao(
        solicitacao_recreio_emef
    )
    quantidade_depois = ValorMedicao.objects.count()

    assert quantidade_depois > quantidade_antes

    valores_depois = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        nome_campo="dietas_autorizadas",
    )

    assert valores_depois.count() == 21


def test_validate_lancamento_alimentacoes_medicao_recreio_erro_quando_existe_observacao_e_nao_existe_lancamento(
    solicitacao_recreio_emef, categoria_medicao
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        nome_campo="sobremesa",
        dia="17",
    )

    assert valores.count() == 2

    valores.delete()

    medicoes = solicitacao_recreio_emef.medicoes.all()

    for medicao in medicoes:
        baker.make(
            "ValorMedicao",
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            nome_campo="observacoes",
            dia="17",
            valor="Sem atendimento na unidade",
        )

    lista_erros = []

    validate_lancamento_alimentacoes_medicao_recreio(
        solicitacao_recreio_emef,
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
            "periodo_escolar": "Recreio nas Férias",
        },
    ]

    for esperado in erros_esperados:
        assert esperado in lista_erros, f"Elemento {esperado} não encontrado"


def test_validate_lancamento_alimentacoes_medicao_recreio_gera_erro_sem_observacao(
    solicitacao_recreio_emef,
):
    ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        nome_campo="refeicao",
        dia="17",
    ).delete()

    ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        nome_campo="observacoes",
        dia="17",
    ).delete()

    lista_erros = []

    validate_lancamento_alimentacoes_medicao_recreio(
        solicitacao_recreio_emef,
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
            "periodo_escolar": "Recreio nas Férias",
        },
    ]

    for esperado in erros_esperados:
        assert esperado in lista_erros, f"Elemento {esperado} não encontrado"


def test_validate_lancamento_alimentacoes_medicao_recreio_sem_colaboradores(
    solicitacao_recreio_emef,
):
    participantes = (
        solicitacao_recreio_emef.recreio_nas_ferias.unidades_participantes.first()
    )

    participantes.num_colaboradores = 0
    participantes.save()

    ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        medicao__grupo__nome="Colaboradores",
    ).delete()

    lista_erros = []

    validate_lancamento_alimentacoes_medicao_recreio(
        solicitacao_recreio_emef,
        lista_erros,
    )

    assert lista_erros == []


def test_cria_valores_medicao_participantes_nao_duplica_registros(
    solicitacao_recreio_emef,
):
    quantidade_antes = ValorMedicao.objects.count()

    cria_valores_medicao_participantes_emef_emei_cieja_ceugestao(
        solicitacao_recreio_emef
    )

    quantidade_depois_primeira_execucao = ValorMedicao.objects.count()

    cria_valores_medicao_participantes_emef_emei_cieja_ceugestao(
        solicitacao_recreio_emef
    )

    quantidade_depois_segunda_execucao = ValorMedicao.objects.count()

    assert quantidade_depois_primeira_execucao == quantidade_depois_segunda_execucao

    assert quantidade_depois_segunda_execucao >= quantidade_antes


def test_cria_valores_dietas_nao_cria_sem_logs(
    solicitacao_recreio_emef,
):
    escola = solicitacao_recreio_emef.escola

    escola.logs_dietas_autorizadas_recreio_ferias.all().delete()

    ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        nome_campo="dietas_autorizadas",
    ).delete()

    cria_valores_medicao_participantes_dietas_autorizadas_emef_emei_cieja_ceugestao(
        solicitacao_recreio_emef
    )

    assert not ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        nome_campo="dietas_autorizadas",
    ).exists()


def test_indexar_logs_dieta_autorizadas_por_data_soma_quantidades(
    solicitacao_recreio_emef,
):
    escola = solicitacao_recreio_emef.escola
    recreio = solicitacao_recreio_emef.recreio_nas_ferias
    inicio_recreio = recreio.data_inicio
    fim_recreio = recreio.data_fim

    logs_do_recreio = escola.logs_dietas_autorizadas_recreio_ferias.filter(
        data__range=[inicio_recreio, fim_recreio],
    )

    resultado = indexar_logs_dieta_autorizadas_por_data(logs_do_recreio)

    assert resultado[datetime.date(2025, 12, 10)]["tipo a enteral"] == 3


def test_retorna_valor_para_log_dieta_autorizada_enteral_sem_logs(
    categoria_medicao_dieta_a_enteral_aminoacidos,
):
    resultado = retorna_valor_para_log_dieta_autorizada(
        categoria_medicao_dieta_a_enteral_aminoacidos,
        {},
        datetime.date(2025, 12, 10),
    )

    assert resultado == 0


def test_cria_medicao_quando_grupo_nao_existe(
    solicitacao_recreio_emef,
):
    solicitacao_recreio_emef.medicoes.all().delete()

    cria_valores_medicao_participantes_emef_emei_cieja_ceugestao(
        solicitacao_recreio_emef
    )

    assert solicitacao_recreio_emef.medicoes.exists()


def test_get_linhas_da_tabela_dieta_recreio_com_todas_alimentacoes(
    categoria_medicao_dieta_a_enteral_aminoacidos,
):
    resultado = get_linhas_da_tabela_dieta_recreio(
        ["Lanche", "Lanche 4h", "Refeição"],
        categoria_medicao_dieta_a_enteral_aminoacidos,
    )

    campos = [
        "frequencia",
        "lanche",
        "lanche_4h",
        "refeicao",
    ]
    for esperado in campos:
        assert esperado in resultado, f"Elemento {esperado} não encontrado"


def test_categoria_tem_logs_dieta_autorizada_categoria_comum_retorna_true(
    categoria_medicao_dieta_b,
):
    logs_por_dia = {
        datetime.date(2025, 12, 10): {
            "tipo b": 4,
        }
    }
    resultado = _categoria_tem_logs_dieta_autorizada(
        categoria_medicao_dieta_b,
        logs_por_dia,
    )

    assert resultado is True


def test_get_classificacoes_dietas_recreio_remove_enteral_sem_lanche_e_sem_refeicao(
    categoria_medicao_dieta_a_enteral_aminoacidos,
    categoria_medicao_dieta_b,
):
    categorias = [
        categoria_medicao_dieta_a_enteral_aminoacidos,
        categoria_medicao_dieta_b,
    ]

    resultado = get_classificacoes_dietas_recreio(
        categorias,
        [],
    )

    assert categoria_medicao_dieta_a_enteral_aminoacidos not in resultado
    assert categoria_medicao_dieta_b not in resultado


def test_existe_colaborador_retorna_false_quando_nao_tem_colaboradores(
    solicitacao_recreio_emef,
):
    participante = (
        solicitacao_recreio_emef.recreio_nas_ferias.unidades_participantes.first()
    )

    participante.num_colaboradores = 0
    participante.save()

    assert existe_colaborador(participante) is False


def test_existe_colaborador_retorna_false_quando_nao_tem_tipos_alimentacao_com_colaboradores(
    solicitacao_recreio_emef,
):
    participante = (
        solicitacao_recreio_emef.recreio_nas_ferias.unidades_participantes.first()
    )

    participante.tipos_alimentacao.filter(categoria__nome="Colaboradores").delete()

    assert participante.num_colaboradores > 0
    assert existe_colaborador(participante) is False


def test_cria_valores_medicao_participantes_emef_emei_cieja_ceugestao_sem_tipo_alimentacao_colaboradores(
    solicitacao_recreio_emef,
):
    participante = (
        solicitacao_recreio_emef.recreio_nas_ferias.unidades_participantes.first()
    )

    participante.tipos_alimentacao.filter(categoria__nome="Colaboradores").delete()

    assert participante.num_colaboradores > 0
    assert existe_colaborador(participante) is False

    ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        medicao__grupo__nome="Recreio nas Férias",
        nome_campo="participantes",
    ).delete()
    ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        medicao__grupo__nome="Colaboradores",
        nome_campo="participantes",
    ).delete()

    cria_valores_medicao_participantes_emef_emei_cieja_ceugestao(
        solicitacao_recreio_emef
    )

    participantes_valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        medicao__grupo__nome="Recreio nas Férias",
        nome_campo="participantes",
    )
    colaboradores_valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        medicao__grupo__nome="Colaboradores",
        nome_campo="participantes",
    )

    assert participantes_valores.exists()
    assert colaboradores_valores.count() == 0


def test_validate_lancamento_alimentacoes_medicao_recreio_ignora_colaboradores_sem_tipo_alimentacao(
    solicitacao_recreio_emef,
):
    participante = (
        solicitacao_recreio_emef.recreio_nas_ferias.unidades_participantes.first()
    )

    participante.tipos_alimentacao.filter(categoria__nome="Colaboradores").delete()

    assert participante.num_colaboradores > 0
    assert existe_colaborador(participante) is False

    lista_erros = []

    validate_lancamento_alimentacoes_medicao_recreio(
        solicitacao_recreio_emef,
        lista_erros,
    )

    assert lista_erros == []
