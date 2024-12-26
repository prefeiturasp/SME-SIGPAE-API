import datetime
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from model_mommy import mommy
from rest_framework import status

from ..models import DiaSuspensaoAtividades, FaixaEtaria, MudancaFaixasEtarias
from ..services import NovoSGPServicoLogado
from .conftest import mocked_foto_aluno_novosgp, mocked_response, mocked_token_novosgp

ENDPOINT_ALUNOS_POR_PERIODO = "quantidade-alunos-por-periodo"
ENDPOINT_LOTES = "lotes"


def test_url_endpoint_quantidade_alunos_por_periodo(client_autenticado, escola):
    response = client_autenticado.get(
        f"/{ENDPOINT_ALUNOS_POR_PERIODO}/escola/{escola.uuid}/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_lotes(client_autenticado):
    response = client_autenticado.get(f"/{ENDPOINT_LOTES}/")
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_lotes_delete(client_autenticado, lote):
    response = client_autenticado.delete(f"/{ENDPOINT_LOTES}/{lote.uuid}/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


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
        "pegar_token_acesso",
        lambda p1, p2, p3: mocked_response(mocked_token_novosgp(), 200),
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
        "pegar_token_acesso",
        lambda p1, p2, p3: mocked_response(mocked_token_novosgp(), 200),
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
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "pegar_token_acesso",
        lambda p1, p2, p3: mocked_response(None, 204),
    )
    response = client_autenticado_da_escola.get(f"/alunos/{aluno.codigo_eol}/ver-foto/")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Não foi possível logar no sistema"


def test_url_endpoint_update_foto_aluno(
    client_autenticado_da_escola, aluno, monkeypatch
):
    foto = SimpleUploadedFile(
        "file.jpg", str.encode("file_content"), content_type="image/jpg"
    )
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "pegar_token_acesso",
        lambda p1, p2, p3: mocked_response(mocked_token_novosgp(), 200),
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
        "pegar_token_acesso",
        lambda p1, p2, p3: mocked_response(mocked_token_novosgp(), 200),
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
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "pegar_token_acesso",
        lambda p1, p2, p3: mocked_response(mocked_token_novosgp(), 204),
    )
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
        "pegar_token_acesso",
        lambda p1, p2, p3: mocked_response(mocked_token_novosgp(), 200),
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
        "pegar_token_acesso",
        lambda p1, p2, p3: mocked_response(mocked_token_novosgp(), 200),
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
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "pegar_token_acesso",
        lambda p1, p2, p3: mocked_response(None, 204),
    )
    response = client_autenticado_da_escola.delete(
        f"/alunos/{aluno.codigo_eol}/deletar-foto/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Não foi possível logar no sistema"


def test_escola_simplissima_dre_unpaginated(
    client_autenticado_da_dre, diretoria_regional
):
    assert diretoria_regional.escolas.count() == 3
    response = client_autenticado_da_dre.get(
        "/escolas-simplissima-com-dre-unpaginated/terc-total/?dre=d305add2-f070-4ad3-8c17-ba9664a7c655"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 3


def test_url_endpoint_escola_simplessima_actions(
    client_autenticado_da_escola, diretoria_regional
):
    client = client_autenticado_da_escola

    response = client.get(f"/escolas-simplissima/{diretoria_regional.uuid}/")
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_periodos_escolares_actions(client_autenticado_da_escola):
    client = client_autenticado_da_escola

    agora = datetime.datetime.now()
    mes = agora.month
    ano = agora.year

    response = client.get(
        f"/periodos-escolares/inclusao-continua-por-mes/?mes={mes}&ano={ano}"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_diretoria_regional_simplessima_actions(
    client_autenticado_da_dre, diretoria_regional
):
    client = client_autenticado_da_dre

    response = client.get("/diretorias-regionais-simplissima/lista-completa/")
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_subprefeitura_actions(client_autenticado_da_dre):
    client = client_autenticado_da_dre

    response = client.get("/subprefeituras/lista-completa/")
    assert response.status_code == status.HTTP_200_OK


def test_url_lotes_actions(client_autenticado_da_dre):
    client = client_autenticado_da_dre

    response = client.get("/lotes/meus-lotes-vinculados/")
    assert response.status_code == status.HTTP_200_OK


def test_url_aluno_actions(client_autenticado_da_dre, escola):
    aluno = mommy.make(
        "Aluno",
        nome="Fulano da Silva",
        codigo_eol="000001",
        data_nascimento=datetime.date(2000, 1, 1),
        escola=escola,
    )

    client = client_autenticado_da_dre
    response = client.get(f"/alunos/{aluno.codigo_eol}/aluno-pertence-a-escola/000546/")
    assert response.status_code == status.HTTP_200_OK


def test_url_relatorios_alunos_matriculados_actions(client_autenticado_da_dre):
    client = client_autenticado_da_dre

    response = client.get("/relatorio-alunos-matriculados/filtros/")
    assert response.status_code == status.HTTP_200_OK

    response = client.get("/relatorio-alunos-matriculados/filtrar/")
    assert response.status_code == status.HTTP_200_OK


def test_escolas_simplissimas_com_paginacao(client_autenticado_da_escola):
    response = client_autenticado_da_escola.get("/escolas-simplissima/?page=1")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 4
    assert "count" in response.json()


def test_escolas_simplissimas_sem_paginacao(client_autenticado_da_escola):
    response = client_autenticado_da_escola.get("/escolas-simplissima/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 4
    assert "count" not in response.json()


def test_url_log_alunos_matriculados_faixa_etaria_dia(
    client_autenticado_da_escola, escola, log_alunos_matriculados_faixa_etaria_dia
):
    response = client_autenticado_da_escola.get(
        f"/log-alunos-matriculados-faixa-etaria-dia/?escola_uuid={escola.uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["escola"] == escola.nome
    assert response.json()[0]["quantidade"] == 100


def test_url_endpoint_cria_dias_suspensao_atividades(
    client_autenticado_coordenador_codae,
):
    data = {
        "data": "2022-08-08",
        "tipo_unidades": [
            "1cc3253b-e297-42b3-8e57-ebfd115a1aba",
            "40ee89a7-dc70-4abb-ae21-369c67f2b9e3",
            "ac4858ff-1c11-41f3-b539-7a02696d6d1b",
        ],
    }
    response = client_autenticado_coordenador_codae.post(
        "/dias-suspensao-atividades/", content_type="application/json", data=data
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert DiaSuspensaoAtividades.objects.count() == 3
    response = client_autenticado_coordenador_codae.get(
        "/dias-suspensao-atividades/?mes=8&ano=2022", content_type="application/json"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 3
    response = client_autenticado_coordenador_codae.get(
        "/dias-suspensao-atividades/?mes=9&ano=2022", content_type="application/json"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 0
    data = {"data": "2022-08-08", "tipo_unidades": []}
    response = client_autenticado_coordenador_codae.post(
        "/dias-suspensao-atividades/", content_type="application/json", data=data
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert DiaSuspensaoAtividades.objects.count() == 0


def test_url_endpoint_matriculados_no_mes__quantidade_por_data(
    client_autenticado_coordenador_codae,
    escola_factory,
    log_alunos_matriculados_periodo_escola_factory,
):
    escola = escola_factory.create()

    data = datetime.date.today() - datetime.timedelta(days=5)

    log_1 = log_alunos_matriculados_periodo_escola_factory.create(
        escola=escola,
        quantidade_alunos=10,
        cei_ou_emei="N/A",
        infantil_ou_fundamental="N/A",
    )
    log_2 = log_alunos_matriculados_periodo_escola_factory.create(
        escola=escola,
        quantidade_alunos=15,
        cei_ou_emei="N/A",
        infantil_ou_fundamental="N/A",
    )

    log_1.criado_em = data
    log_1.save(update_fields=["criado_em"])

    log_2.criado_em = data
    log_2.save(update_fields=["criado_em"])

    data_formatted = data.strftime("%Y-%m-%d")

    response = client_autenticado_coordenador_codae.get(
        f"/matriculados-no-mes/quantidade-por-data/?data={data_formatted}&escola_uuid={escola.uuid}",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data == 25


def test_url_endpoint_matriculados_no_mes__quantidade_por_data_dia_atual(
    client_autenticado_coordenador_codae,
    escola_factory,
    log_alunos_matriculados_periodo_escola_factory,
):
    escola = escola_factory.create()

    data = datetime.date.today()
    dia_anterior = data - datetime.timedelta(days=1)

    log_1 = log_alunos_matriculados_periodo_escola_factory.create(
        escola=escola,
        quantidade_alunos=5,
        cei_ou_emei="N/A",
        infantil_ou_fundamental="N/A",
    )
    log_2 = log_alunos_matriculados_periodo_escola_factory.create(
        escola=escola,
        quantidade_alunos=15,
        cei_ou_emei="N/A",
        infantil_ou_fundamental="N/A",
    )

    log_1.criado_em = dia_anterior
    log_1.save(update_fields=["criado_em"])

    log_2.criado_em = dia_anterior
    log_2.save(update_fields=["criado_em"])

    data_formatted = data.strftime("%Y-%m-%d")

    response = client_autenticado_coordenador_codae.get(
        f"/matriculados-no-mes/quantidade-por-data/?data={data_formatted}&escola_uuid={escola.uuid}",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data == 20


def test_url_endpoint_meses_anos(client_autenticado_da_escola):
    response = client_autenticado_da_escola.get(
        "/relatorio-controle-frequencia/meses-anos/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 3


def test_url_endpoint_filtros(client_autenticado_da_escola):
    response = client_autenticado_da_escola.get(
        f"/relatorio-controle-frequencia/filtros/?mes=6&ano=2024"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["periodos"] == []
    assert response.data["data_inicial"] == datetime.date(2024, 6, 1)
    assert response.data["data_final"] == datetime.date(2024, 6, 30)


def test_url_endpoint_filtrar(
    client_autenticado_da_escola, periodo_escolar, periodo_escolar_parcial
):
    response = client_autenticado_da_escola.get(
        f"/relatorio-controle-frequencia/filtrar/?periodos={json.dumps([str(periodo_escolar.uuid)])}&data_inicial=2024-06-03&data_final=2024-06-25"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["periodos"].get("INTEGRAL") == 0
    assert response.data["total_matriculados"] == 0
