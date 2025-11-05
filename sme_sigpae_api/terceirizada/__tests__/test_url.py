import json

from rest_framework import status

from sme_sigpae_api.terceirizada.models import Contrato, Terceirizada


def test_url_terceirizadas_autenticado(client_autenticado_terceiro):
    client = client_autenticado_terceiro
    response = client.get("/terceirizadas/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 1
    item = data["results"][0]

    assert isinstance(item, dict)
    assert len(item["contatos"]) == 1
    assert len(item["contratos"]) == 1


def test_url_endpoint_editais_autenticado(client_autenticado_terceiro):
    client = client_autenticado_terceiro
    response = client.get("/editais/")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["count"] == 1
    item = data["results"][0]

    assert isinstance(item, dict)


def test_url_endpoint_editais_numeros_autenticado(client_autenticado_terceiro):
    client = client_autenticado_terceiro
    response = client.get("/editais/lista-numeros/")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 1
    item = data["results"][0]

    assert isinstance(item, dict)


def test_url_endpoint_editais_contratos_autenticado(client_autenticado_terceiro):
    client = client_autenticado_terceiro
    response = client.get("/editais-contratos/")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["count"] == 1
    item = data["results"][0]

    assert isinstance(item, dict)
    assert len(item["contratos"]) == 1


def test_cadastro_empresa(users_codae_gestao_alimentacao):
    client, email, password, rf, cpf, user = users_codae_gestao_alimentacao
    data = {
        "nutricionistas": [
            {
                "nome": "Yolanda",
                "crn_numero": "0987654",
                "super_admin_terceirizadas": True,
                "contatos": [
                    {"telefone": "12 32131 2312", "email": "yolanda@empresa.teste.com"}
                ],
            }
        ],
        "super_admin": {
            "username": "97596447031",
            "email": "empresa@empresa.teste.com",
            "nome": "Empresa LTDA",
            "cpf": "97596447031",
            "cargo": "militante",
            "contatos": [
                {"email": "empresa@empresa2.teste.com", "telefone": "12 32131 2315"}
            ],
        },
        "nome_fantasia": "Empresa Empresada",
        "razao_social": "Empresa LTDA",
        "cnpj": "58833199000119",
        "representante_legal": "Seu Carlos",
        "representante_telefone": "12 12212 1121",
        "representante_email": "carlos@empresa.teste.com",
        "endereco": "Rua dos Coqueiros 123",
        "cep": "09123456",
        "contatos": [
            {"telefone": "12 12121 2121", "email": "empresa@empresa.teste.com"}
        ],
        "lotes": ["42d3887a-517b-4a72-be78-95d96d857236"],
    }
    response = client.post(
        "/terceirizadas/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_201_CREATED
    terceirizada_uuid = response.json()["uuid"]
    data_update = {
        "nutricionistas": [
            {
                "nome": "Yolanda",
                "crn_numero": "0987654",
                "super_admin_terceirizadas": False,
                "contatos": [
                    {"telefone": "12 32131 2312", "email": "yolanda@empresa2.teste.com"}
                ],
            },
            {
                "nome": "Yago",
                "crn_numero": "7654321",
                "super_admin_terceirizadas": True,
                "contatos": [
                    {"telefone": "11 32334 2212", "email": "yago@empresa3.teste.com"}
                ],
            },
        ],
        "super_admin": {
            "username": "97596447027",
            "email": "empresa@empresa2.teste.com",
            "nome": "Empresa LTDA2",
            "cpf": "97596447027",
            "cargo": "vagal",
            "contatos": [
                {"email": "empresa@empresa2.teste.com", "telefone": "12 32131 2315"}
            ],
        },
        "nome_fantasia": "Empresa Empresada",
        "razao_social": "Empresa LTDA",
        "cnpj": "58833199000119",
        "representante_legal": "Seu Carlos",
        "representante_telefone": "12 12212 1121",
        "representante_email": "carlos@empresa.teste.com",
        "endereco": "Rua dos Coqueiros 123",
        "cep": "09123456",
        "contatos": [
            {"telefone": "12 12121 2121", "email": "empresa@empresa.teste.com"}
        ],
        "lotes": [
            "143c2550-8bf0-46b4-b001-27965cfcd107",
            "42d3887a-517b-4a72-be78-95d96d857236",
        ],
    }
    response = client.put(
        f"/terceirizadas/{terceirizada_uuid}/",
        content_type="application/json",
        data=json.dumps(data_update),
    )
    assert response.status_code == status.HTTP_200_OK
    terceirizada = Terceirizada.objects.get(uuid="66c1bdd1-9cec-4f1f-a2f6-008f27713e53")
    assert terceirizada.ativo is False
    assert (
        terceirizada.inclusao_alimentacao_inclusaoalimentacaocontinua_rastro_terceirizada.count()
        == 1
    )
    assert (
        terceirizada.dieta_especial_solicitacaodietaespecial_rastro_terceirizada.count()
        == 2
    )
    assert (
        terceirizada.dieta_especial_solicitacaodietaespecial_rastro_terceirizada.get(
            rastro_lote__uuid="42d3887a-517b-4a72-be78-95d96d857236"
        ).conferido
        is False
    )
    terceirizada_criada = Terceirizada.objects.get(uuid=terceirizada_uuid)
    assert (
        terceirizada_criada.inclusao_alimentacao_inclusaoalimentacaocontinua_rastro_terceirizada.count()
        == 1
    )
    assert (
        terceirizada_criada.dieta_especial_solicitacaodietaespecial_rastro_terceirizada.count()
        == 0
    )


def test_cadastro_empresa_remove_lote_erro(users_codae_gestao_alimentacao):
    client, email, password, rf, cpf, user = users_codae_gestao_alimentacao
    data = {
        "nutricionistas": [
            {
                "nome": "Yolanda",
                "crn_numero": "0987654",
                "super_admin_terceirizadas": True,
                "contatos": [
                    {"telefone": "12 32131 2312", "email": "yolanda@empresa.teste.com"}
                ],
            }
        ],
        "super_admin": {
            "username": "97596447031",
            "email": "empresa@empresa.teste.com",
            "nome": "Empresa LTDA",
            "cpf": "97596447031",
            "cargo": "militante",
            "contatos": [
                {"email": "empresa@empresa2.teste.com", "telefone": "12 32131 2315"}
            ],
        },
        "nome_fantasia": "Empresa Empresada",
        "razao_social": "Empresa LTDA",
        "cnpj": "58833199000119",
        "representante_legal": "Seu Carlos",
        "representante_telefone": "12 12212 1121",
        "representante_email": "carlos@empresa.teste.com",
        "endereco": "Rua dos Coqueiros 123",
        "cep": "09123456",
        "contatos": [
            {"telefone": "12 12121 2121", "email": "empresa@empresa.teste.com"}
        ],
        "lotes": ["143c2550-8bf0-46b4-b001-27965cfcd107"],
    }
    response = client.post(
        "/terceirizadas/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_201_CREATED
    terceirizada_uuid = response.json()["uuid"]
    data_update = {
        "nutricionistas": [
            {
                "nome": "Yolanda",
                "crn_numero": "0987654",
                "super_admin_terceirizadas": False,
                "contatos": [
                    {"telefone": "12 32131 2312", "email": "yolanda@empresa2.teste.com"}
                ],
            },
            {
                "nome": "Yago",
                "crn_numero": "7654321",
                "super_admin_terceirizadas": True,
                "contatos": [
                    {"telefone": "11 32334 2212", "email": "yago@empresa3.teste.com"}
                ],
            },
        ],
        "nome_fantasia": "Empresa Empresada",
        "razao_social": "Empresa LTDA",
        "cnpj": "58833199000119",
        "representante_legal": "Seu Carlos",
        "representante_telefone": "12 12212 1121",
        "representante_email": "carlos@empresa.teste.com",
        "endereco": "Rua dos Coqueiros 123",
        "cep": "09123456",
        "contatos": [
            {"telefone": "12 12121 2121", "email": "empresa@empresa.teste.com"}
        ],
        "lotes": ["42d3887a-517b-4a72-be78-95d96d857236"],
    }
    response = client.put(
        f"/terceirizadas/{terceirizada_uuid}/",
        content_type="application/json",
        data=json.dumps(data_update),
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()[0]
        == "Não pode remover um lote de uma empresa. É preciso atribuí-lo a outra empresa."
    )


def test_url_authorized_emails_terceirizadas(client_autenticado_terceiro):
    client = client_autenticado_terceiro
    response = client.get("/terceirizadas/emails-por-modulo/")
    assert response.status_code == status.HTTP_200_OK


def test_url_authorized_emails_terceirizadas_por_modulo(client_autenticado_terceiro):
    client = client_autenticado_terceiro
    response = client.get("/emails-terceirizadas-modulos/")
    assert response.status_code == status.HTTP_200_OK


def test_encerrar_contrato(client_autenticado_terceiro):
    response = client_autenticado_terceiro.patch(
        "/contratos/44d51e10-8999-48bb-889a-1540c9e8c895/encerrar-contrato/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["encerrado"] is True
    assert "data_hora_encerramento" in response.json()


def test_encerrar_contrato_integrity_error(client_autenticado_terceiro):
    Contrato.objects.filter(uuid="44d51e10-8999-48bb-889a-1540c9e8c895").update(
        encerrado=True
    )
    response = client_autenticado_terceiro.patch(
        "/contratos/44d51e10-8999-48bb-889a-1540c9e8c895/encerrar-contrato/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Contrato já encerrado. Não é possivel encerrar novamente!"
    }


def test_cria_edital_contrato(users_codae_gestao_alimentacao):
    client_, email, password, rf, cpf, user = users_codae_gestao_alimentacao
    data = {
        "contratos": [
            {
                "vigencias": [
                    {
                        "uuid": "c4b17252-4c3e-462b-a744-da797eb41fa8",
                        "data_inicial": "28/11/2020",
                        "data_final": "05/12/2020",
                        "status": "vencido",
                    }
                ],
                "lotes": ["143c2550-8bf0-46b4-b001-27965cfcd107"],
                "terceirizada": "66c1bdd1-9cec-4f1f-a2f6-008f27713e53",
                "diretorias_regionais": ["9db1e5d8-dba3-4245-b937-a94c4ea44411"],
                "numero": "4552",
                "processo": "0840983028080",
                "data_proposta": "28/11/2020",
                "encerrado": False,
                "data_hora_encerramento": None,
                "ata": "",
                "modalidade": "",
                "numero_pregao": "",
                "numero_chamada_publica": "",
                "programa": "LEVE_LEITE",
            }
        ],
        "numero": "938373",
        "tipo_contratacao": "TESTE",
        "processo": "848477",
        "objeto": "TESTE",
    }
    response = client_.post(
        "/editais-contratos/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert "contratos" in response.json()
    assert len(response.json()["contratos"][0]["lotes"]) == 1
    assert len(response.json()["contratos"][0]["vigencias"]) == 1
    assert len(response.json()["contratos"][0]["diretorias_regionais"]) == 1

    data["uuid"] = response.json()["uuid"]
    data["contratos"][0]["uuid"] = response.json()["contratos"][0]["uuid"]

    response = client_.put(
        f"/editais-contratos/{str(response.json()['uuid'])}/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_200_OK
    assert "contratos" in response.json()
    assert len(response.json()["contratos"][0]["lotes"]) == 1
    assert len(response.json()["contratos"][0]["vigencias"]) == 1
    assert len(response.json()["contratos"][0]["diretorias_regionais"]) == 1
