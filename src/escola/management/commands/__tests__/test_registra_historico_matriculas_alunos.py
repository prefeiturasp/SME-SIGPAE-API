from datetime import datetime
from unittest import mock

import pytest
from django.core.management import call_command

from src.escola.management.commands.registra_historico_matriculas_alunos import (
    Command,
)
from src.escola.models import HistoricoMatriculaAluno

from .data import HISTORICO_LORENA, HISTORICO_SHEILA


def sgp_mock_sheila_4_escolas_ativas(*args, **kwargs):
    return HISTORICO_SHEILA


def sgp_mock_lorena_2_escolas_ativas_1_concluida(*args, **kwargs):
    return HISTORICO_LORENA


def test_agrupamento_das_matriculas_por_escola():
    data = Command()._agrupa_matriculas_por_escola(sgp_mock_sheila_4_escolas_ativas())

    assert data == {
        "094595": [
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2022-11-03T19:49:01.807",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2022-11-03T19:49:01.807",
                "numeroAlunoChamada": "0",
                "codigoTurma": 2523972,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "094595",
                "codigoTipoTurma": 1,
            },
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2022-11-03T19:49:01.807",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2022-12-14T14:56:58.12",
                "numeroAlunoChamada": "0",
                "codigoTurma": 2523972,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "094595",
                "codigoTipoTurma": 1,
            },
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2022-12-14T16:15:54.233",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2022-12-14T16:15:54.233",
                "numeroAlunoChamada": "0",
                "codigoTurma": 2523972,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "094595",
                "codigoTipoTurma": 1,
            },
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2023-01-27T12:18:04.147",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2022-12-14T16:15:54.233",
                "numeroAlunoChamada": "0",
                "codigoTurma": 2605231,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "094595",
                "codigoTipoTurma": 1,
            },
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2023-01-27T12:21:02.407",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2022-12-14T16:15:54.233",
                "numeroAlunoChamada": "021",
                "codigoTurma": 2523972,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "094595",
                "codigoTipoTurma": 1,
            },
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2022-12-14T16:15:54.233",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2023-08-07T11:37:06.47",
                "numeroAlunoChamada": "0",
                "codigoTurma": 2523972,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "094595",
                "codigoTipoTurma": 1,
            },
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2023-01-27T12:18:04.147",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2023-08-07T11:37:06.47",
                "numeroAlunoChamada": "0",
                "codigoTurma": 2605231,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "094595",
                "codigoTipoTurma": 1,
            },
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2023-01-27T12:21:02.407",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2023-08-07T11:37:06.47",
                "numeroAlunoChamada": "021",
                "codigoTurma": 2523972,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "094595",
                "codigoTipoTurma": 1,
            },
        ],
        "094641": [
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2023-08-11T10:43:15.697",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2023-08-16T10:31:30.36",
                "numeroAlunoChamada": "0",
                "codigoTurma": 2645165,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "094641",
                "codigoTipoTurma": 1,
            },
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2023-08-16T10:31:30.423",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2023-08-16T10:31:30.36",
                "numeroAlunoChamada": "0",
                "codigoTurma": 2645165,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "094641",
                "codigoTipoTurma": 1,
            },
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2023-08-11T10:43:15.697",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2023-08-16T10:31:57.8",
                "numeroAlunoChamada": "0",
                "codigoTurma": 2645165,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "094641",
                "codigoTipoTurma": 1,
            },
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2023-08-16T10:31:30.423",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2023-08-16T10:31:57.8",
                "numeroAlunoChamada": "0",
                "codigoTurma": 2645165,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "094641",
                "codigoTipoTurma": 1,
            },
        ],
        "094633": [
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2023-08-17T13:19:36.69",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2023-08-17T13:19:36.563",
                "numeroAlunoChamada": "0",
                "codigoTurma": 2644960,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "094633",
                "codigoTipoTurma": 1,
            },
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2023-08-17T13:19:36.69",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2023-08-17T13:20:55.113",
                "numeroAlunoChamada": "0",
                "codigoTurma": 2644960,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "094633",
                "codigoTipoTurma": 1,
            },
        ],
        "200069": [
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2023-08-17T13:25:18.753",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2023-08-17T13:25:18.707",
                "numeroAlunoChamada": "027",
                "codigoTurma": 2502112,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "200069",
                "codigoTipoTurma": 1,
            },
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2023-08-17T13:25:18.753",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2023-11-09T19:47:32.76",
                "numeroAlunoChamada": "027",
                "codigoTurma": 2502112,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "200069",
                "codigoTipoTurma": 1,
            },
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2023-12-01T10:29:04.48",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2023-12-01T10:29:04.387",
                "numeroAlunoChamada": "035",
                "codigoTurma": 2502112,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "200069",
                "codigoTipoTurma": 1,
            },
            {
                "codigoAluno": 584782,
                "anoLetivo": 2023,
                "nomeAluno": "SHEILA DUARTE AMORIM",
                "nomeSocialAluno": "SHEILA DUARTE AMORIM",
                "codigoSituacaoMatricula": 1,
                "situacaoMatricula": "Ativo",
                "dataSituacao": "2023-12-01T10:29:04.48",
                "dataNascimento": "1983-12-25T00:00:00",
                "dataMatricula": "2023-12-01T10:31:47.18",
                "numeroAlunoChamada": "035",
                "codigoTurma": 2502112,
                "nomeResponsavel": "SHEILA DUARTE AMORIM",
                "tipoResponsavel": "4",
                "celularResponsavel": "11939588844",
                "dataAtualizacaoContato": "2022-09-02T15:14:52.56",
                "codigoEscola": "200069",
                "codigoTipoTurma": 1,
            },
        ],
    }


@pytest.mark.django_db
@mock.patch.object(Command, "_obtem_matriculas_aluno", sgp_mock_sheila_4_escolas_ativas)
def test_registro_do_historico_sheila_4_escolas_ativas(
    aluno_com_codigo_eol,
    escola_sheila_1,
    escola_sheila_2,
    escola_sheila_3,
    escola_sheila_4,
):
    call_command("registra_historico_matriculas_alunos")

    assert HistoricoMatriculaAluno.objects.count() == 4

    historico_1 = HistoricoMatriculaAluno.objects.get(
        aluno=aluno_com_codigo_eol, escola=escola_sheila_1
    )
    assert historico_1.data_inicio == datetime(2022, 11, 3).date()
    assert historico_1.data_fim is None
    assert historico_1.situacao == "ATIVO"

    historico_2 = HistoricoMatriculaAluno.objects.get(
        aluno=aluno_com_codigo_eol, escola=escola_sheila_2
    )
    assert historico_2.data_inicio == datetime(2023, 8, 11).date()
    assert historico_2.data_fim is None
    assert historico_2.situacao == "ATIVO"

    historico_3 = HistoricoMatriculaAluno.objects.get(
        aluno=aluno_com_codigo_eol, escola=escola_sheila_3
    )
    assert historico_3.data_inicio == datetime(2023, 8, 17).date()
    assert historico_3.data_fim is None
    assert historico_3.situacao == "ATIVO"

    historico_4 = HistoricoMatriculaAluno.objects.get(
        aluno=aluno_com_codigo_eol, escola=escola_sheila_4
    )
    assert historico_4.data_inicio == datetime(2023, 8, 17).date()
    assert historico_4.data_fim is None
    assert historico_4.situacao == "ATIVO"


@pytest.mark.django_db
@mock.patch.object(
    Command, "_obtem_matriculas_aluno", sgp_mock_lorena_2_escolas_ativas_1_concluida
)
def test_registro_do_historico_lorena_2_escolas_ativas_1_concluida(
    aluno_com_codigo_eol,
    escola_lorena_1,
    escola_lorena_2,
    escola_lorena_3,
):
    call_command("registra_historico_matriculas_alunos")

    assert HistoricoMatriculaAluno.objects.count() == 3

    historico_1 = HistoricoMatriculaAluno.objects.get(
        aluno=aluno_com_codigo_eol, escola=escola_lorena_1
    )
    assert historico_1.data_inicio == datetime(2022, 10, 31).date()
    assert historico_1.data_fim is None
    assert historico_1.situacao == "ATIVO"

    historico_2 = HistoricoMatriculaAluno.objects.get(
        aluno=aluno_com_codigo_eol, escola=escola_lorena_2
    )
    assert historico_2.data_inicio == datetime(2023, 4, 24).date()
    assert historico_2.data_fim is None
    assert historico_2.situacao == "ATIVO"

    historico_3 = HistoricoMatriculaAluno.objects.get(
        aluno=aluno_com_codigo_eol, escola=escola_lorena_3
    )
    assert historico_3.data_inicio == datetime(2023, 6, 14).date()
    assert historico_3.data_fim == datetime(2023, 12, 29).date()
    assert historico_3.situacao == "CONCLUÍDO"


@pytest.mark.django_db
@mock.patch.object(Command, "_get_ano_atual", lambda *args: 2030)
def test_argumento_ano_letivo_padrao():
    patcher = mock.patch.object(Command, "_gera_historico_matriculas_alunos")

    mocked = patcher.start()

    call_command("registra_historico_matriculas_alunos")

    mocked.assert_called_once_with(2030)

    patcher.stop()


@pytest.mark.django_db
def test_argumento_ano_letivo():
    patcher = mock.patch.object(Command, "_gera_historico_matriculas_alunos")

    mocked = patcher.start()

    call_command("registra_historico_matriculas_alunos", "--ano=2023")

    mocked.assert_called_once_with(2023)

    patcher.stop()
