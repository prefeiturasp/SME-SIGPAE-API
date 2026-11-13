import datetime
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from model_bakery import baker
from rest_framework import status

from src.dados_comuns.constants import TIPOS_UNIDADE_ESCOLAR

from ...models import FaixaEtaria, MudancaFaixasEtarias
from ...services import NovoSGPServicoLogado, NovoSGPServicoLogadoException
from ..conftest import mocked_foto_aluno_novosgp, mocked_response

ENDPOINT_ALUNOS_POR_PERIODO = "quantidade-alunos-por-periodo"


ENDPOINT_LOTES = "lotes"


ENDPOINT_LISTA_DIAS = "dias-suspensao-atividades/lista-dias"


def _mock_obter_token_erro(monkeypatch):
    def _raise_login_error(self):
        raise NovoSGPServicoLogadoException("Não foi possível logar no sistema")

    monkeypatch.setattr(NovoSGPServicoLogado, "_obter_token", _raise_login_error)


ENDPOINT_LOTES_SIMPLES = "lotes-simples"


def test_url_endpoint_alunos_por_faixa_etaria_data_invalida(
    client_autenticado, escola_periodo_escolar
):
    url = f"/quantidade-alunos-por-periodo/{escola_periodo_escolar.uuid}/alunos-por-faixa-etaria/2020-15-40/"
    response = client_autenticado.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert "data_referencia" in json
    assert json["data_referencia"][0] == "Informe uma data válida."


def test_url_endpoint_alunos_por_faixa_etaria_faixas_nao_cadastradas(
    client_autenticado, escola_periodo_escolar
):
    url = f"/quantidade-alunos-por-periodo/{escola_periodo_escolar.uuid}/alunos-por-faixa-etaria/2020-10-20/"
    response = client_autenticado.get(url)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert (
        response.json()["detail"]
        == "Não há faixas etárias cadastradas. Contate a coordenadoria CODAE."
    )


def test_url_endpoint_alunos_por_faixa_etaria_periodo_invalido(
    client_autenticado, escola_periodo_escolar, faixas_etarias
):
    url = "/quantidade-alunos-por-periodo/sou-um-uuid-invalido/alunos-por-faixa-etaria/2020-10-20/"
    response = client_autenticado.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_url_endpoint_alunos_por_faixa_etaria(
    client_autenticado,
    escola_periodo_escolar,
    eolservicosgp_get_lista_alunos,
    faixas_etarias,
):
    url = f"/quantidade-alunos-por-periodo/{escola_periodo_escolar.uuid}/alunos-por-faixa-etaria/2020-10-20/"
    response = client_autenticado.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()

    assert json["count"] == 2
    result0 = json["results"][0]
    assert result0["faixa_etaria"]["inicio"] == 12
    assert result0["faixa_etaria"]["fim"] == 24
    assert result0["count"] == 1
    result1 = json["results"][1]
    assert result1["faixa_etaria"]["inicio"] == 24
    assert result1["faixa_etaria"]["fim"] == 48
    assert result1["count"] == 2


def test_url_endpoint_cria_mudanca_faixa_etaria(client_autenticado_coordenador_codae):
    data = {
        "faixas_etarias_ativadas": [
            {"inicio": 1, "fim": 4},
            {"inicio": 4, "fim": 8},
            {"inicio": 8, "fim": 12},
            {"inicio": 12, "fim": 17},
        ],
        "justificativa": "Primeiro cadastro",
    }
    response = client_autenticado_coordenador_codae.post(
        "/faixas-etarias/", content_type="application/json", data=data
    )
    assert response.status_code == status.HTTP_201_CREATED

    assert MudancaFaixasEtarias.objects.count() == 1
    assert FaixaEtaria.objects.count() == 4

    mfe = MudancaFaixasEtarias.objects.first()

    assert mfe.justificativa == data["justificativa"]

    faixas_etarias = FaixaEtaria.objects.filter(ativo=True).order_by("inicio")
    for expected, actual in zip(data["faixas_etarias_ativadas"], faixas_etarias):
        assert expected["inicio"] == actual.inicio
        assert expected["fim"] == actual.fim


def test_url_endpoint_cria_mudanca_faixa_etaria_erro_fim_menor_igual_inicio(
    client_autenticado_coordenador_codae,
):
    faixas_etarias = [{"inicio": 10, "fim": 5}]
    response = client_autenticado_coordenador_codae.post(
        "/faixas-etarias/",
        content_type="application/json",
        data={
            "faixas_etarias_ativadas": faixas_etarias,
            "justificativa": "Primeiro cadastro",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        str(response.data["faixas_etarias_ativadas"][0]["non_field_errors"][0])
        == "A faixa etária tem que terminar depois do início: inicio=10;fim=5"
    )


def test_url_endpoint_cria_mudanca_faixa_etaria_erro_inicio_menor_zero(
    client_autenticado_coordenador_codae,
):
    faixas_etarias = [{"inicio": -10, "fim": 5}]
    response = client_autenticado_coordenador_codae.post(
        "/faixas-etarias/",
        content_type="application/json",
        data={
            "faixas_etarias_ativadas": faixas_etarias,
            "justificativa": "Primeiro cadastro",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert (
        str(response.data["faixas_etarias_ativadas"][0]["inicio"][0])
        == "Certifque-se de que este valor seja maior ou igual a 0."
    )


def test_url_endpoint_lista_faixas_etarias(
    client_autenticado_coordenador_codae, faixas_etarias
):
    response = client_autenticado_coordenador_codae.get("/faixas-etarias/")
    assert response.status_code == status.HTTP_200_OK
    json = response.json()

    ativas = FaixaEtaria.objects.filter(ativo=True)

    assert json["count"] == len(ativas)

    for expected, actual in zip(ativas, json["results"]):
        assert actual["inicio"] == expected.inicio
        assert actual["fim"] == expected.fim


def test_url_endpoint_get_foto_aluno(client_autenticado_da_escola, aluno, monkeypatch):
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "_obter_token",
        lambda self: "Bearer abc123",
    )
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "pegar_foto_aluno",
        lambda p1, p2: mocked_response(mocked_foto_aluno_novosgp(), 200),
    )
    response = client_autenticado_da_escola.get(f"/alunos/{aluno.codigo_eol}/ver-foto/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] == mocked_foto_aluno_novosgp()


def test_url_endpoint_get_foto_aluno_204(
    client_autenticado_da_escola, aluno, monkeypatch
):
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "_obter_token",
        lambda self: "Bearer abc123",
    )
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "pegar_foto_aluno",
        lambda p1, p2: mocked_response(mocked_foto_aluno_novosgp(), 204),
    )
    response = client_autenticado_da_escola.get(f"/alunos/{aluno.codigo_eol}/ver-foto/")
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_url_endpoint_get_foto_aluno_token_invalido(
    client_autenticado_da_escola, aluno, monkeypatch
):
    _mock_obter_token_erro(monkeypatch)
    response = client_autenticado_da_escola.get(f"/alunos/{aluno.codigo_eol}/ver-foto/")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Não foi possível logar no sistema"


def test_url_endpoint_get_foto_aluno_codae(
    client_autenticado_coordenador_codae, aluno, monkeypatch
):
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "_obter_token",
        lambda self: "Bearer abc123",
    )
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "pegar_foto_aluno",
        lambda p1, p2: mocked_response(mocked_foto_aluno_novosgp(), 200),
    )
    response = client_autenticado_coordenador_codae.get(
        f"/alunos/{aluno.codigo_eol}/ver-foto/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] == mocked_foto_aluno_novosgp()


def test_url_endpoint_update_foto_aluno(
    client_autenticado_da_escola, aluno, monkeypatch
):
    foto = SimpleUploadedFile(
        "file.jpg", str.encode("file_content"), content_type="image/jpg"
    )
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "_obter_token",
        lambda self: "Bearer abc123",
    )
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "atualizar_foto_aluno",
        lambda p1, p2, p3: mocked_response("c8c564b6-ea7f-4549-9474-6234e2406881", 200),
    )
    response = client_autenticado_da_escola.post(
        f"/alunos/{aluno.codigo_eol}/atualizar-foto/", {"file": foto}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] == "c8c564b6-ea7f-4549-9474-6234e2406881"


def test_url_endpoint_update_foto_aluno_error(
    client_autenticado_da_escola, aluno, monkeypatch
):
    foto = SimpleUploadedFile(
        "file.jpg", str.encode("file_content"), content_type="image/jpg"
    )
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "_obter_token",
        lambda self: "Bearer abc123",
    )
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "atualizar_foto_aluno",
        lambda p1, p2, p3: mocked_response(None, 400),
    )
    response = client_autenticado_da_escola.post(
        f"/alunos/{aluno.codigo_eol}/atualizar-foto/", {"file": foto}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_endpoint_update_foto_aluno_token_invalido(
    client_autenticado_da_escola, aluno, monkeypatch
):
    foto = SimpleUploadedFile(
        "file.jpg", str.encode("file_content"), content_type="image/jpg"
    )
    _mock_obter_token_erro(monkeypatch)
    response = client_autenticado_da_escola.post(
        f"/alunos/{aluno.codigo_eol}/atualizar-foto/", {"file": foto}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Não foi possível logar no sistema"


def test_url_endpoint_deletar_foto_aluno(
    client_autenticado_da_escola, aluno, monkeypatch
):
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "_obter_token",
        lambda self: "Bearer abc123",
    )
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "deletar_foto_aluno",
        lambda p1, p2: mocked_response(None, 200),
    )
    response = client_autenticado_da_escola.delete(
        f"/alunos/{aluno.codigo_eol}/deletar-foto/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_deletar_foto_aluno_204(
    client_autenticado_da_escola, aluno, monkeypatch
):
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "_obter_token",
        lambda self: "Bearer abc123",
    )
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "deletar_foto_aluno",
        lambda p1, p2: mocked_response(None, 204),
    )
    response = client_autenticado_da_escola.delete(
        f"/alunos/{aluno.codigo_eol}/deletar-foto/"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_url_endpoint_deletar_foto_aluno_token_invalido(
    client_autenticado_da_escola, aluno, monkeypatch
):
    _mock_obter_token_erro(monkeypatch)
    response = client_autenticado_da_escola.delete(
        f"/alunos/{aluno.codigo_eol}/deletar-foto/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Não foi possível logar no sistema"


def test_url_aluno_actions(client_autenticado_da_dre, escola):
    aluno = baker.make(
        "Aluno",
        nome="Fulano da Silva",
        codigo_eol="000001",
        data_nascimento=datetime.date(2000, 1, 1),
        escola=escola,
    )

    client = client_autenticado_da_dre
    response = client.get(f"/alunos/{aluno.codigo_eol}/aluno-pertence-a-escola/000546/")
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_filtrar_sem_duplicacao_faixa_etaria(
    client_autenticado_da_escola,
    escola,
    periodo_escolar,
    periodo_escolar_parcial,
    faixas_etarias_ativas,
):
    # Forçar a escola a ser CEI para testar a lógica específica
    tipo_unidade_cei = baker.make(
        "TipoUnidadeEscolar", iniciais=TIPOS_UNIDADE_ESCOLAR.CEI.value
    )
    escola.tipo_unidade = tipo_unidade_cei
    escola.save()

    aluno = baker.make(
        "Aluno",
        nome="Criança Teste",
        codigo_eol="999999",
        escola=escola,
        periodo_escolar=periodo_escolar,
    )

    data_teste = datetime.date(2024, 6, 15)

    # Log 1: Faixa Etária 1
    log1 = baker.make(
        "LogAlunosMatriculadosFaixaEtariaDia",
        escola=escola,
        periodo_escolar=periodo_escolar,
        faixa_etaria=faixas_etarias_ativas[0],
        quantidade=1,
        data=data_teste,
    )
    baker.make("LogAlunoPorDia", log_alunos_matriculados_faixa_dia=log1, aluno=aluno)

    # Log 2: Faixa Etária 2 (mesmo aluno, mesmo dia, mesmo período)
    log2 = baker.make(
        "LogAlunosMatriculadosFaixaEtariaDia",
        escola=escola,
        periodo_escolar=periodo_escolar,
        faixa_etaria=faixas_etarias_ativas[1],
        quantidade=1,
        data=data_teste,
    )
    baker.make("LogAlunoPorDia", log_alunos_matriculados_faixa_dia=log2, aluno=aluno)

    url = (
        f"/relatorio-controle-frequencia/filtrar/?"
        f"periodos={json.dumps([str(periodo_escolar.uuid)])}&"
        f"data_inicial=2024-06-15&data_final=2024-06-15&"
        f"mes_ano=06_2024"
    )

    response = client_autenticado_da_escola.get(url)

    assert response.status_code == status.HTTP_200_OK
    # Deve ser 1, não 2, pois o aluno é o mesmo e usamos Count(distinct=True)
    assert response.data["total_matriculados"] == 1
    assert response.data["periodos"]["INTEGRAL"] == 1
