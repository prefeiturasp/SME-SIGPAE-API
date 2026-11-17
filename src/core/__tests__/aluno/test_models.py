import datetime
from collections import Counter

import pytest
from freezegun import freeze_time
from model_bakery import baker

from ....dados_comuns.constants import TIPOS_UNIDADE_ESCOLAR, FaixasEtarias
from ...models import FaixaEtaria

pytestmark = pytest.mark.django_db


def test_aluno(aluno):
    assert aluno.__str__() == "Fulano da Silva - 000001"


def test_aluno_retorna_periodo_escolar(aluno):
    aluno.nao_matriculado = False
    aluno.escola.tipo_unidade.iniciais = TIPOS_UNIDADE_ESCOLAR.EMEF.value
    assert aluno.periodo == aluno.periodo_escolar.nome


def test_aluno_nao_retorna_periodo_quando_nao_tem_codigo_eol(aluno):
    aluno.codigo_eol = None
    aluno.nao_matriculado = False
    aluno.escola.tipo_unidade.iniciais = TIPOS_UNIDADE_ESCOLAR.EMEF.value
    assert aluno.periodo is None


def test_aluno_nao_retorna_periodo_quando_nao_matriculado(aluno):
    aluno.nao_matriculado = True
    aluno.escola.tipo_unidade.iniciais = TIPOS_UNIDADE_ESCOLAR.EMEF.value
    assert aluno.periodo is None


def test_aluno_nao_retorna_periodo_para_tipo_unidade_cei(aluno):
    aluno.nao_matriculado = False
    aluno.escola.tipo_unidade.iniciais = TIPOS_UNIDADE_ESCOLAR.CEI.value
    assert aluno.periodo is None


def test_aluno_nao_retorna_periodo_para_cei_do_cemei(aluno, escola_cemei):
    aluno.nao_matriculado = False
    aluno.escola = escola_cemei
    aluno.ciclo = aluno.CICLO_ALUNO_CEI
    assert aluno.periodo is None


@freeze_time("2019-06-20")
def test_data_pertence_faixa_etaria_hoje(datas_e_faixas):
    data, faixa_etaria, eh_pertencente = datas_e_faixas
    assert (
        faixa_etaria.data_pertence_a_faixa(data, datetime.date.today())
        == eh_pertencente
    )


def test_faixa_etaria_respeita_29_de_fevereiro_em_ano_bissexto():
    faixa = baker.make("FaixaEtaria", inicio=0, fim=1, ativo=True)
    referencia = datetime.date(2024, 3, 29)
    assert faixa.data_pertence_a_faixa(datetime.date(2024, 2, 28), referencia) is False
    assert faixa.data_pertence_a_faixa(datetime.date(2024, 2, 29), referencia) is True


def test_faixa_etaria_fevereiro_de_ano_comum_termina_no_dia_28():
    faixa = baker.make("FaixaEtaria", inicio=0, fim=1, ativo=True)
    referencia = datetime.date(2023, 3, 29)
    assert faixa.data_pertence_a_faixa(datetime.date(2023, 2, 27), referencia) is False
    assert faixa.data_pertence_a_faixa(datetime.date(2023, 2, 28), referencia) is True


def test_faixa_etaria_seculo_nao_bissexto_nao_usa_29_de_fevereiro():
    faixa = baker.make("FaixaEtaria", inicio=0, fim=1, ativo=True)
    referencia = datetime.date(1900, 3, 30)
    assert faixa.data_pertence_a_faixa(datetime.date(1900, 2, 28), referencia) is True


def test_faixa_str():
    faixa = FaixaEtaria.objects.create(inicio=24, fim=48)
    assert str(faixa) == FaixasEtarias.DOIS_ANOS_A_TRES_ANOS_E_ONZE_MESES.value


@freeze_time("2023-08-28")
def test_alunos_por_periodo_e_faixa_etaria(
    escola, faixas_etarias, periodo_escolar, eolservicosgp_get_lista_alunos
):
    response = escola.alunos_por_periodo_e_faixa_etaria()
    assert len(response) == 1
    assert response["INTEGRAL"] == Counter(
        {
            f"{str([f for f in faixas_etarias if f.inicio == 48][0].uuid)}": 3,
        }
    )


@freeze_time("2023-08-28")
def test_alunos_periodo_parcial_e_faixa_etaria(
    escola_cei,
    faixas_etarias,
    alunos_periodo_parcial,
    periodo_escolar,
    eolservicosgp_get_lista_alunos,
):
    response = escola_cei.alunos_periodo_parcial_e_faixa_etaria()
    assert len(response) == 1
    assert response["PARCIAL"] == Counter(
        {
            f"{str([f for f in faixas_etarias if f.inicio == 48][0].uuid)}": 2,
        }
    )


@freeze_time("2023-08-28")
def test_alunos_por_periodo_e_faixa_etaria_objetos_alunos(
    escola_cei, faixas_etarias, alunos
):
    response = escola_cei.alunos_por_periodo_e_faixa_etaria_objetos_alunos()
    assert len(response) == 1
    assert response["INTEGRAL"] == Counter(
        {
            f"{str([f for f in faixas_etarias if f.inicio == 48][0].uuid)}": 3,
        }
    )


@freeze_time("2023-08-28")
def test_alunos_por_faixa_etaria(
    escola_cei, faixas_etarias, eolservicosgp_get_lista_alunos
):
    response = escola_cei.alunos_por_faixa_etaria()
    assert len(response.items()) == 1
    assert response == Counter(
        {
            f"{str([f for f in faixas_etarias if f.inicio == 48][0].uuid)}": 3,
        }
    )
