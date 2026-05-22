import datetime

import pytest
from model_bakery import baker

from src.medicao_inicial.models import ValorMedicao
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_cei_cci_cips import (
    _categoria_tem_logs_dieta_autorizada_cei,
    cria_valores_medicao_participantes_cei,
    cria_valores_medicao_participantes_dietas_autorizadas_cei,
    indexar_logs_dieta_autorizadas_por_data_e_faixa,
    retorna_valor_para_log_dieta_autorizada_cei,
    validate_lancamento_alimentacoes_medicao_recreio_cei,
    validate_lancamento_dietas_medicao_recreio_cei,
)
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_common import (
    agrupar_tipos_alimentacao_por_categoria,
)
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_emef_emei_ceu_gesto_cieja import (
    existe_colaborador,
)

pytestmark = pytest.mark.django_db


def test_validate_lancamento_alimentacoes_medicao_recreio_cei(solicitacao_recreio_cei):

    lista_erros = []
    lista_erros = validate_lancamento_alimentacoes_medicao_recreio_cei(
        solicitacao_recreio_cei, lista_erros
    )
    assert len(lista_erros) == 0


def test_validate_lancamento_alimentacoes_medicao_recreio_cei_dados_nao_lancados(
    solicitacao_recreio_cei, categoria_medicao
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        nome_campo="frequencia",
        dia="17",
        categoria_medicao=categoria_medicao,
    )
    assert valores.count() == 9
    valores.delete()
    lista_erros = []

    lista_erros = validate_lancamento_alimentacoes_medicao_recreio_cei(
        solicitacao_recreio_cei,
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


def test_validate_lancamento_dietas_medicao_recreio_cei(solicitacao_recreio_cei):
    lista_erros = []
    validate_lancamento_dietas_medicao_recreio_cei(solicitacao_recreio_cei, lista_erros)
    assert len(lista_erros) == 0


def test_validate_lancamento_dietas_medicao_recreio_cei_dados_nao_lancados(
    solicitacao_recreio_cei, categoria_medicao_dieta_a
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        nome_campo="frequencia",
        dia="17",
        categoria_medicao=categoria_medicao_dieta_a,
    )
    assert valores.count() == 8
    valores.delete()
    assert valores.count() == 0
    lista_erros = []
    validate_lancamento_dietas_medicao_recreio_cei(solicitacao_recreio_cei, lista_erros)
    assert len(lista_erros) == 1
    assert lista_erros == [
        {
            "erro": "Restam dias a serem lançados nas dietas.",
            "periodo_escolar": "Recreio nas Férias",
        }
    ]


def test_agrupar_tipos_alimentacao_por_categoria(solicitacao_recreio_cei):
    recreio = solicitacao_recreio_cei.recreio_nas_ferias
    participantes = recreio.unidades_participantes.first()

    tipos_alimentacao = participantes.tipos_alimentacao.filter(
        categoria__nome__in=["Inscritos", "Colaboradores"]
    )

    resultado = agrupar_tipos_alimentacao_por_categoria(tipos_alimentacao)

    assert "Colaboradores" in resultado
    colaboradores = ["Refeição", "Sobremesa"]
    for esperado in colaboradores:
        assert (
            esperado in resultado["Colaboradores"]
        ), f"Elemento {esperado} não encontrado"

    assert "Inscritos" in resultado
    inscritos = ["Refeição", "Sobremesa", "Lanche", "Lanche 4h", "Almoço"]
    for esperado in inscritos:
        assert esperado in resultado["Inscritos"], f"Elemento {esperado} não encontrado"


def test_retorna_valor_para_log_dieta_autorizada_cei(
    solicitacao_recreio_cei, categoria_medicao_dieta_a, faixas_etarias_ativas
):
    escola = solicitacao_recreio_cei.escola
    recreio = solicitacao_recreio_cei.recreio_nas_ferias
    inicio_recreio = recreio.data_inicio
    fim_recreio = recreio.data_fim

    logs_do_recreio = escola.logs_dietas_autorizadas_recreio_ferias_cei.filter(
        data__range=[inicio_recreio, fim_recreio],
    )
    logs_por_dia = indexar_logs_dieta_autorizadas_por_data_e_faixa(logs_do_recreio)
    data = datetime.date(2025, 12, 10)
    resultado = retorna_valor_para_log_dieta_autorizada_cei(
        categoria_medicao_dieta_a, logs_por_dia, data, faixas_etarias_ativas[1]
    )

    assert resultado == 3


def test_cria_valores_medicao_participantes_cei(
    solicitacao_recreio_cei,
):

    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        nome_campo="participantes",
    )
    assert valores.count() == 28
    valores.delete()
    assert valores.count() == 0

    quantidade_antes = ValorMedicao.objects.count()

    cria_valores_medicao_participantes_cei(solicitacao_recreio_cei)

    quantidade_depois = ValorMedicao.objects.count()

    assert quantidade_depois > quantidade_antes

    valores_depois = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        nome_campo="participantes",
    )

    assert valores_depois.count() == 42


def test_cria_valores_medicao_participantes_dietas_autorizadas_cei(
    solicitacao_recreio_cei,
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        nome_campo="dietas_autorizadas",
    )
    assert valores.count() == 112
    valores.delete()
    assert valores.count() == 0

    quantidade_antes = ValorMedicao.objects.count()

    cria_valores_medicao_participantes_dietas_autorizadas_cei(solicitacao_recreio_cei)
    quantidade_depois = ValorMedicao.objects.count()

    assert quantidade_depois > quantidade_antes

    valores_depois = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        nome_campo="dietas_autorizadas",
    )

    assert valores_depois.count() == 168


def test_validate_lancamento_alimentacoes_medicao_recreio_cei_erro_quando_existe_observacao_e_nao_existe_lancamento(
    solicitacao_recreio_cei, categoria_medicao
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        nome_campo="frequencia",
        dia="17",
    )

    assert valores.count() == 17

    valores.delete()

    medicoes = solicitacao_recreio_cei.medicoes.all()
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

    lista_erros = validate_lancamento_alimentacoes_medicao_recreio_cei(
        solicitacao_recreio_cei,
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


def test_validate_lancamento_alimentacoes_medicao_recreio_cei_gera_erro_sem_observacao(
    solicitacao_recreio_cei,
):
    ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        nome_campo="frequencia",
        dia="17",
    ).delete()

    ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        nome_campo="observacoes",
        dia="17",
    ).delete()

    lista_erros = []

    lista_erros = validate_lancamento_alimentacoes_medicao_recreio_cei(
        solicitacao_recreio_cei,
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


def test_validate_lancamento_alimentacoes_medicao_recreio_cei_sem_colaboradores(
    solicitacao_recreio_cei,
):
    participantes = (
        solicitacao_recreio_cei.recreio_nas_ferias.unidades_participantes.first()
    )

    participantes.num_colaboradores = 0
    participantes.save()

    ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        medicao__grupo__nome="Colaboradores",
    ).delete()

    lista_erros = []

    lista_erros = validate_lancamento_alimentacoes_medicao_recreio_cei(
        solicitacao_recreio_cei,
        lista_erros,
    )

    assert lista_erros == []


def test_cria_valores_medicao_participantes_cei_nao_duplica_registros(
    solicitacao_recreio_cei,
):
    quantidade_antes = ValorMedicao.objects.count()

    cria_valores_medicao_participantes_cei(solicitacao_recreio_cei)

    quantidade_depois_primeira_execucao = ValorMedicao.objects.count()

    cria_valores_medicao_participantes_cei(solicitacao_recreio_cei)

    quantidade_depois_segunda_execucao = ValorMedicao.objects.count()

    assert quantidade_depois_primeira_execucao == quantidade_depois_segunda_execucao

    assert quantidade_depois_segunda_execucao >= quantidade_antes


def test_cria_valores_dietas_cei_nao_cria_sem_logs(
    solicitacao_recreio_cei,
):
    escola = solicitacao_recreio_cei.escola

    escola.logs_dietas_autorizadas_recreio_ferias_cei.all().delete()

    ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        nome_campo="dietas_autorizadas",
    ).delete()

    cria_valores_medicao_participantes_dietas_autorizadas_cei(solicitacao_recreio_cei)

    assert not ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        nome_campo="dietas_autorizadas",
    ).exists()


def test_indexar_logs_dieta_autorizadas_por_data_e_faixa_soma_quantidades(
    solicitacao_recreio_cei, faixas_etarias_ativas
):
    escola = solicitacao_recreio_cei.escola
    recreio = solicitacao_recreio_cei.recreio_nas_ferias
    inicio_recreio = recreio.data_inicio
    fim_recreio = recreio.data_fim

    logs_do_recreio = escola.logs_dietas_autorizadas_recreio_ferias_cei.filter(
        data__range=[inicio_recreio, fim_recreio],
    )
    resultado = indexar_logs_dieta_autorizadas_por_data_e_faixa(logs_do_recreio)
    assert len(resultado[datetime.date(2025, 12, 10)]) == 8
    for faixa in faixas_etarias_ativas:
        assert resultado[datetime.date(2025, 12, 10)][faixa.id]["tipo a enteral"] == 3


def test_cria_medicao_quando_grupo_nao_existe(
    solicitacao_recreio_cei,
):
    solicitacao_recreio_cei.medicoes.all().delete()

    cria_valores_medicao_participantes_cei(solicitacao_recreio_cei)

    assert solicitacao_recreio_cei.medicoes.exists()


def test_categoria_tem_logs_dieta_autorizada_cei_retorna_true(
    categoria_medicao_dieta_a, faixas_etarias_ativas
):
    logs_por_dia = {
        datetime.date(2025, 12, 10): {
            faixas_etarias_ativas[2].id: {
                "tipo a enteral": 4,
            }
        }
    }
    resultado = _categoria_tem_logs_dieta_autorizada_cei(
        categoria_medicao_dieta_a,
        logs_por_dia,
    )

    assert resultado is True


def test_categoria_tem_logs_dieta_autorizada_cei_retorna_false(
    categoria_medicao_dieta_a, faixas_etarias_ativas
):
    logs_por_dia = {
        datetime.date(2025, 12, 10): {
            faixas_etarias_ativas[2].id: {
                "tipo b": 4,
            }
        }
    }
    resultado = _categoria_tem_logs_dieta_autorizada_cei(
        categoria_medicao_dieta_a,
        logs_por_dia,
    )

    assert resultado is False


def test_existe_colaborador_retorna_false_quando_nao_tem_colaboradores(
    solicitacao_recreio_cei,
):
    participante = (
        solicitacao_recreio_cei.recreio_nas_ferias.unidades_participantes.first()
    )

    participante.num_colaboradores = 0
    participante.save()

    assert existe_colaborador(participante) is False


def test_existe_colaborador_retorna_false_quando_nao_tem_tipos_alimentacao_com_colaboradores(
    solicitacao_recreio_cei,
):
    participante = (
        solicitacao_recreio_cei.recreio_nas_ferias.unidades_participantes.first()
    )

    participante.tipos_alimentacao.filter(categoria__nome="Colaboradores").delete()

    assert participante.num_colaboradores > 0
    assert existe_colaborador(participante) is False


def test_cria_valores_medicao_participantes_cei_sem_tipo_alimentacao_colaboradores(
    solicitacao_recreio_cei,
):
    participante = (
        solicitacao_recreio_cei.recreio_nas_ferias.unidades_participantes.first()
    )

    participante.tipos_alimentacao.filter(categoria__nome="Colaboradores").delete()

    assert participante.num_colaboradores > 0
    assert existe_colaborador(participante) is False

    ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        medicao__grupo__nome="Recreio nas Férias",
        nome_campo="participantes",
    ).delete()
    ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        medicao__grupo__nome="Colaboradores",
        nome_campo="participantes",
    ).delete()

    cria_valores_medicao_participantes_cei(solicitacao_recreio_cei)

    participantes_valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        medicao__grupo__nome="Recreio nas Férias",
        nome_campo="participantes",
    )
    colaboradores_valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        medicao__grupo__nome="Colaboradores",
        nome_campo="participantes",
    )

    assert participantes_valores.exists()
    assert colaboradores_valores.count() == 0


def test_validate_lancamento_alimentacoes_medicao_recreio_ignora_colaboradores_sem_tipo_alimentacao(
    solicitacao_recreio_cei,
):
    participante = (
        solicitacao_recreio_cei.recreio_nas_ferias.unidades_participantes.first()
    )

    participante.tipos_alimentacao.filter(categoria__nome="Colaboradores").delete()

    assert participante.num_colaboradores > 0
    assert existe_colaborador(participante) is False

    lista_erros = []

    lista_erros = validate_lancamento_alimentacoes_medicao_recreio_cei(
        solicitacao_recreio_cei,
        lista_erros,
    )

    assert lista_erros == []


def test_retorna_valor_para_log_dieta_autorizada_cei_quando_nao_existe(
    solicitacao_recreio_cei, categoria_medicao_dieta_b, faixas_etarias_ativas
):
    escola = solicitacao_recreio_cei.escola
    recreio = solicitacao_recreio_cei.recreio_nas_ferias
    inicio_recreio = recreio.data_inicio
    fim_recreio = recreio.data_fim

    logs_do_recreio = escola.logs_dietas_autorizadas_recreio_ferias_cei.filter(
        data__range=[inicio_recreio, fim_recreio],
    )
    logs_por_dia = indexar_logs_dieta_autorizadas_por_data_e_faixa(logs_do_recreio)
    data = datetime.date(2025, 12, 10)
    resultado = retorna_valor_para_log_dieta_autorizada_cei(
        categoria_medicao_dieta_b, logs_por_dia, data, faixas_etarias_ativas[1]
    )

    assert resultado == 0
