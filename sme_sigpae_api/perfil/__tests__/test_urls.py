import json
import uuid
from unittest.mock import patch

import pytest
from rest_framework import status

from ..api.helpers import ofuscar_email
from ..api.viewsets import UsuarioUpdateViewSet
from ..models import (
    ImportacaoPlanilhaUsuarioExternoCoreSSO,
    ImportacaoPlanilhaUsuarioServidorCoreSSO,
    Perfil,
    Usuario,
)

pytestmark = pytest.mark.django_db


def test_get_usuarios(client_autenticado):
    response = client_autenticado.get("/usuarios/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), dict)
    json = response.json()
    assert json["count"] == 1
    assert json["results"][0]["email"] == "test@test.com"


def test_atualizar_email(users_admin_escola):
    client, email, password, rf, user = users_admin_escola
    data = {"email": "novoemail@email.com"}
    response = client.patch(
        "/usuarios/atualizar-email/", content_type="application/json", data=data
    )
    assert response.status_code == status.HTTP_200_OK
    user = Usuario.objects.get(registro_funcional=rf)
    assert user.email == "novoemail@email.com"


def test_atualizar_senha_logado(users_admin_escola):
    client, email, password, rf, user = users_admin_escola
    data = {
        "senha_atual": password,
        "senha": "adminadmin123",
        "confirmar_senha": "adminadmin123",
    }
    api_redefine_senha = "sme_sigpae_api.eol_servico.utils.EOLServicoSGP.redefine_senha"
    with patch(api_redefine_senha):
        response = client.patch(
            "/usuarios/atualizar-senha/", content_type="application/json", data=data
        )
    assert response.status_code == status.HTTP_200_OK
    user = Usuario.objects.get(registro_funcional=rf)
    assert user.check_password("adminadmin123") is True


def test_atualizar_senha_logado_senha_atual_incorreta(users_admin_escola):
    client, email, password, rf, user = users_admin_escola
    data = {
        "senha_atual": "senhaincorreta",
        "senha": "adminadmin123",
        "confirmar_senha": "adminadmin123",
    }
    response = client.patch(
        "/usuarios/atualizar-senha/", content_type="application/json", data=data
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Senha atual incorreta"}


def test_atualizar_senha_logado_senha_e_confirmar_senha_divergem(users_admin_escola):
    client, email, password, rf, user = users_admin_escola
    data = {
        "senha_atual": password,
        "senha": "adminadmin123",
        "confirmar_senha": "senhadiferente",
    }
    response = client.patch(
        "/usuarios/atualizar-senha/", content_type="application/json", data=data
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == ["Senha e confirmar senha divergem"]


def test_get_meus_dados_admin_escola(users_admin_escola):
    client, email, password, rf, user = users_admin_escola
    response = client.get("/usuarios/meus-dados/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), dict)
    json = response.json()
    keys = [
        "uuid",
        "nome",
        "email",
        "registro_funcional",
        "date_joined",
        "vinculo_atual",
        "tipo_usuario",
    ]
    for key in keys:
        assert key in json.keys()
    assert json["email"] == email
    response.json().get("vinculo_atual").pop("uuid")
    assert json["registro_funcional"] == rf
    assert json["tipo_usuario"] == "escola"
    assert json["vinculo_atual"]["instituicao"]["nome"] == "EMEI NOE AZEVEDO, PROF"
    assert (
        json["vinculo_atual"]["instituicao"]["uuid"]
        == "b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd"
    )
    assert json["vinculo_atual"]["instituicao"]["codigo_eol"] == "256341"
    assert json["vinculo_atual"]["ativo"] is True
    assert json["vinculo_atual"]["perfil"]["nome"] == "Admin"
    assert (
        json["vinculo_atual"]["perfil"]["uuid"]
        == "d6fd15cc-52c6-4db4-b604-018d22eeb3dd"
    )


def test_get_meus_dados_diretor_escola(users_diretor_escola):
    client, email, password, rf, cpf, user = users_diretor_escola
    response = client.get("/usuarios/meus-dados/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), dict)
    json = response.json()
    keys = [
        "uuid",
        "nome",
        "email",
        "registro_funcional",
        "date_joined",
        "vinculo_atual",
        "tipo_usuario",
    ]
    for key in keys:
        assert key in json.keys()
    response.json().get("vinculo_atual").pop("uuid")
    assert json["email"] == email
    assert json["registro_funcional"] == rf
    assert json["tipo_usuario"] == "escola"
    assert json["vinculo_atual"]["instituicao"]["nome"] == "EMEI NOE AZEVEDO, PROF"
    assert (
        json["vinculo_atual"]["instituicao"]["uuid"]
        == "b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd"
    )
    assert json["vinculo_atual"]["instituicao"]["codigo_eol"] == "256341"
    assert json["vinculo_atual"]["ativo"] is True
    assert json["vinculo_atual"]["perfil"]["nome"] == "DIRETOR_UE"
    assert (
        json["vinculo_atual"]["perfil"]["uuid"]
        == "41c20c8b-7e57-41ed-9433-ccb92e8afaf1"
    )


def test_cadastro_erro(client):
    response = client.post(
        "/cadastro/",
        data={
            "email": "string",
            "registro_funcional": "string",
            "password": "string",
            "confirmar_password": "string",
            "cpf": "string",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert isinstance(response.json(), dict)
    assert response.json() == {"detail": "RF não cadastrado no sistema"}


def test_cadastro_diretor(client, users_diretor_escola, monkeypatch):
    _, email, password, rf, cpf, user = users_diretor_escola
    data = {
        "email": email,
        "registro_funcional": rf,
        "password": password,
        "confirmar_password": password,
        "cpf": cpf,
    }
    assert user.registro_funcional == rf

    monkeypatch.setattr(
        UsuarioUpdateViewSet, "_get_usuario", lambda p1, p2: user
    )  # noqa
    monkeypatch.setattr(Usuario, "pode_efetuar_cadastro", lambda: True)
    response = client.post(
        "/cadastro/", content_type="application/json", data=json.dumps(data)
    )  # noqa
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    keys = [
        "uuid",
        "nome",
        "email",
        "registro_funcional",
        "date_joined",
        "vinculo_atual",
        "tipo_usuario",
    ]
    for key in keys:
        assert key in response_json.keys()
    assert response_json["email"] == email
    assert response_json["registro_funcional"] == rf
    response.json().get("vinculo_atual").pop("uuid")
    response.json().get("vinculo_atual").get("instituicao").pop("periodos_escolares")
    assert response_json["tipo_usuario"] == "escola"
    assert response_json["vinculo_atual"] == {
        "instituicao": {
            "nome": "EMEI NOE AZEVEDO, PROF",
            "uuid": "b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd",
            "codigo_eol": "256341",
            "quantidade_alunos": 450,
            "lotes": [],
            "eh_cei": False,
            "eh_cemei": False,
            "eh_emebs": False,
            "acesso_modulo_medicao_inicial": False,
            "possui_alunos_regulares": True,
            "modulo_gestao": "TERCEIRIZADA",
            "diretoria_regional": {
                "uuid": "7da9acec-48e1-430c-8a5c-1f1efc666fad",
                "nome": "DIRETORIA REGIONAL IPIRANGA",
                "codigo_eol": "987656",
                "iniciais": "IP",
                "acesso_modulo_medicao_inicial": False,
            },
            "tipo_unidade_escolar": "56725de5-89d3-4edf-8633-3e0b5c99e9d4",
            "tipo_unidade_escolar_iniciais": "EMEF",
            "tipo_gestao": "TERC TOTAL",
            "tipos_contagem": [],
            "endereco": {
                "logradouro": "",
                "numero": None,
                "complemento": "",
                "bairro": "",
                "cep": None,
            },
            "contato": {
                "nome": "",
                "telefone": "",
                "telefone2": "",
                "celular": "",
                "email": "",
                "eh_nutricionista": False,
                "crn_numero": "",
            },
        },
        "perfil": {
            "nome": "DIRETOR_UE",
            "uuid": "41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
            "visao": None,
        },
        "ativo": True,
    }


def test_post_usuarios(client_autenticado):
    response = client_autenticado.post("/usuarios/")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    response = client_autenticado.put("/usuarios/")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_confirmar_email(client, usuarios_pendentes_confirmacao):
    usuario = usuarios_pendentes_confirmacao
    assert usuario.is_active is False  # deve estar inativo no sistema
    assert usuario.is_confirmed is False  # deve estar com email nao confirmado
    # ativacao endpoint
    response = client.get(
        f"/confirmar_email/{usuario.uuid}/{usuario.confirmation_key}/"
    )  # noqa

    usuario_apos_ativacao = Usuario.objects.get(id=usuario.id)
    # apos a ativacao pelo link confirma email
    assert usuario_apos_ativacao.is_confirmed is True
    # # apos a ativacao pelo link ativa no sistema
    assert usuario_apos_ativacao.is_active is True

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    keys = [
        "uuid",
        "cpf",
        "nome",
        "email",
        "tipo_email",
        "registro_funcional",
        "tipo_usuario",
        "date_joined",
        "vinculo_atual",
        "crn_numero",
        "cargo",
        "aceitou_termos",
    ]
    for key in keys:
        assert key in json.keys()
    assert len(json.keys()) == len(keys)
    json.pop("date_joined")
    json.get("vinculo_atual").pop("uuid")
    result = {
        "uuid": "d36fa08e-e91e-4acb-9d54-b88115147e8e",
        "cpf": None,
        "nome": "Bruno da Conceição",
        "email": "GrVdXIhxqb@example.com",
        "tipo_email": None,
        "registro_funcional": "1234567",
        "tipo_usuario": "escola",
        "vinculo_atual": {
            "instituicao": {
                "nome": "EMEI NOE AZEVEDO, PROF",
                "uuid": "b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd",
                "codigo_eol": "256341",
                "quantidade_alunos": 0,
                "lotes": [],
                "periodos_escolares": [],
                "diretoria_regional": {
                    "uuid": "7da9acec-48e1-430c-8a5c-1f1efc666fad",
                    "nome": "DIRETORIA REGIONAL IPIRANGA",
                    "codigo_eol": "987656",
                    "iniciais": "IP",
                    "acesso_modulo_medicao_inicial": False,
                },
                "eh_cei": False,
                "eh_cemei": False,
                "eh_emebs": False,
                "possui_alunos_regulares": False,
                "acesso_modulo_medicao_inicial": False,
                "modulo_gestao": "TERCEIRIZADA",
                "tipo_unidade_escolar": "56725de5-89d3-4edf-8633-3e0b5c99e9d4",
                "tipo_unidade_escolar_iniciais": "EMEF",
                "tipo_gestao": "TERC TOTAL",
                "tipos_contagem": [],
                "endereco": {
                    "logradouro": "",
                    "numero": None,
                    "complemento": "",
                    "bairro": "",
                    "cep": None,
                },
                "contato": {
                    "nome": "",
                    "telefone": "",
                    "telefone2": "",
                    "celular": "",
                    "email": "",
                    "eh_nutricionista": False,
                    "crn_numero": "",
                },
            },
            "perfil": {
                "nome": "título do perfil",
                "uuid": "d38e10da-c5e3-4dd5-9916-010fc250595a",
                "visao": None,
            },
            "ativo": True,
        },
        "crn_numero": None,
        "cargo": "",
        "aceitou_termos": False,
    }
    assert json == result


def test_confirmar_error(client, usuarios_pendentes_confirmacao):
    usuario = usuarios_pendentes_confirmacao
    respo = client.get(
        f"/confirmar_email/{uuid.uuid4()}/{usuario.confirmation_key}/"
    )  # chave email correta uuid errado
    assert respo.status_code == status.HTTP_400_BAD_REQUEST
    assert respo.json() == {"detail": "Erro ao confirmar email"}


def test_recuperar_senha(client, usuarios_pendentes_confirmacao):
    usuario = usuarios_pendentes_confirmacao
    response = client.get(f"/cadastro/recuperar-senha/{usuario.registro_funcional}/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"email": ofuscar_email(usuario.email)}


def test_recuperar_senha_invalido(client, usuarios_pendentes_confirmacao):
    response = client.get("/cadastro/recuperar-senha/NAO-EXISTE/")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Não existe usuário com este CPF ou RF"}


def test_busca_sem_vinculos_ativos(
    client_autenticado_representante_codae, users_terceirizada
):
    """Teste para verificar se não retorna o usuário logado no vínculo."""
    response = client_autenticado_representante_codae.get("/vinculos/vinculos-ativos/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 0


def test_busca_vinculos_ativos_dre(client_autenticado_diretoria_regional):
    """Teste para verificar se o perfil DRE tem acesso aos vinculos ativos."""
    response = client_autenticado_diretoria_regional.get("/vinculos/vinculos-ativos/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 0


def test_busca_vinculos_ativos_com_filtro(
    client_autenticado_codae_dilog, users_terceirizada
):
    response = client_autenticado_codae_dilog.get(
        "/vinculos/vinculos-ativos/?perfil=ADMINISTRADOR_EMPRESA"
    )
    assert response.status_code == status.HTTP_200_OK
    for resultado in response.json()["results"]:
        assert resultado.get("nome_perfil") == "ADMINISTRADOR_EMPRESA"


def test_url_visoes(client_autenticado):
    response = client_autenticado.get("/perfis/visoes/")
    assert response.status_code == status.HTTP_200_OK
    json_data = json.loads(response.content)
    assert json_data == Perfil.visoes_to_json()


def test_criar_usuario_nao_servidor_coresso(
    client_autenticado, terceirizada, perfil_distribuidor
):
    payload = {
        "username": "52898325139",
        "email": "teste_silva@teste.com",
        "nome": "Teste da Silva",
        "visao": "EMPRESA",
        "perfil": perfil_distribuidor.nome,
        "instituicao": terceirizada.cnpj,
        "cpf": "52898325139",
        "eh_servidor": "N",
    }

    api_cria_ou_atualiza_usuario_core_sso = "sme_sigpae_api.perfil.services.usuario_coresso_service.EOLUsuarioCoreSSO.cria_ou_atualiza_usuario_core_sso"  # noqa
    with patch(api_cria_ou_atualiza_usuario_core_sso):
        response = client_autenticado.post(
            "/cadastro-com-coresso/",
            data=json.dumps(payload),
            content_type="application/json",
        )
    result = response.json()

    u = Usuario.objects.filter(username="52898325139").first()
    esperado = {
        "uuid": str(u.uuid),
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert result == esperado


def test_criar_usuario_servidor_coresso(client_autenticado, escola, perfil_escola):
    payload = {
        "username": "1234567",
        "email": "teste_servidor@teste.com",
        "nome": "Servidor da Silva",
        "visao": "ESCOLA",
        "perfil": perfil_escola.nome,
        "instituicao": escola.codigo_eol,
        "cpf": "52898325139",
        "cargo": "Diretor",
        "eh_servidor": "S",
    }

    api_cria_ou_atualiza_usuario_core_sso = "sme_sigpae_api.perfil.services.usuario_coresso_service.EOLUsuarioCoreSSO.cria_ou_atualiza_usuario_core_sso"  # noqa
    with patch(api_cria_ou_atualiza_usuario_core_sso):
        response = client_autenticado.post(
            "/cadastro-com-coresso/",
            data=json.dumps(payload),
            content_type="application/json",
        )
    result = response.json()

    u = Usuario.objects.filter(username="1234567").first()
    esperado = {
        "uuid": str(u.uuid),
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert result == esperado


def test_finaliza_vinculo(client_autenticado_codae_dilog, usuario_3):
    username = usuario_3.username
    response = client_autenticado_codae_dilog.post(
        f"/cadastro-com-coresso/{username}/finalizar-vinculo/",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK


def test_edicao_email(client_autenticado_codae_dilog, usuario_3):
    username = usuario_3.username
    payload = {"username": username, "email": "teste_servidor_novo_email@teste.com"}
    api_redefine_email = "sme_sigpae_api.eol_servico.utils.EOLServicoSGP.redefine_email"
    with patch(api_redefine_email):
        response = client_autenticado_codae_dilog.patch(
            f"/cadastro-com-coresso/{username}/alterar-email/",
            data=json.dumps(payload),
            content_type="application/json",
        )

    result = response.json()
    u = Usuario.objects.filter(username=username).first()

    assert response.status_code == status.HTTP_200_OK
    assert result["email"] == "teste_servidor_novo_email@teste.com"
    assert u.email == "teste_servidor_novo_email@teste.com"


def test_create_planilha_externo_coresso(
    client_autenticado_codae_dilog, arquivo_xls, arquivo_pdf
):
    payload = {"conteudo": arquivo_xls}
    payload_extensao_invalida = {"conteudo": arquivo_pdf}
    response = client_autenticado_codae_dilog.post(
        "/planilha-coresso-externo/", data=payload, format="multipart"
    )
    response_erro_forcado = client_autenticado_codae_dilog.post(
        "/planilha-coresso-externo/", data=payload_extensao_invalida, format="multipart"
    )
    result = json.loads(response.content)

    assert response.status_code == status.HTTP_201_CREATED
    assert ImportacaoPlanilhaUsuarioExternoCoreSSO.objects.filter(
        uuid=result["uuid"]
    ).exists()
    planilha = ImportacaoPlanilhaUsuarioExternoCoreSSO.objects.get(uuid=result["uuid"])
    assert planilha.conteudo.name.split(".")[-1] == arquivo_xls.name.split(".")[-1]
    assert response_erro_forcado.status_code == status.HTTP_400_BAD_REQUEST


def test_processar_planilha_externo_coresso(
    client_autenticado_codae_dilog, planilha_usuario_externo, arquivo_xls
):
    assert (
        ImportacaoPlanilhaUsuarioExternoCoreSSO.objects.get(
            uuid=planilha_usuario_externo.uuid
        ).status
        == "PENDENTE"
    )
    api_cria_ou_atualiza_usuario_core_sso = "sme_sigpae_api.perfil.services.usuario_coresso_service.EOLUsuarioCoreSSO.cria_ou_atualiza_usuario_core_sso"  # noqa
    with patch(api_cria_ou_atualiza_usuario_core_sso):
        response = client_autenticado_codae_dilog.post(
            f"/planilha-coresso-externo/{planilha_usuario_externo.uuid}/processar-importacao/"
        )
        response2 = client_autenticado_codae_dilog.post(
            "/planilha-coresso-externo/F38e10da-c5e3-4dd5-9916-010fc250595a/processar-importacao/"
        )

    assert response.status_code == status.HTTP_200_OK
    assert response2.status_code == status.HTTP_404_NOT_FOUND


def test_remover_planilha_externo_coresso(
    client_autenticado_codae_dilog, planilha_usuario_externo, arquivo_xls
):
    response = client_autenticado_codae_dilog.patch(
        f"/planilha-coresso-externo/{planilha_usuario_externo.uuid}/remover/"
    )
    response2 = client_autenticado_codae_dilog.patch(
        "/planilha-coresso-externo/F38e10da-c5e3-4dd5-9916-010fc250595a/remover/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response2.status_code == status.HTTP_404_NOT_FOUND


def test_busca_planilha_coresso_externo(
    client_autenticado_codae_dilog, planilha_usuario_externo
):
    response = client_autenticado_codae_dilog.get("/planilha-coresso-externo/")
    assert response.status_code == status.HTTP_200_OK


def test_download_planilha_modelo_coresso_externo(client_autenticado_codae_dilog):
    response = client_autenticado_codae_dilog.get(
        "/planilha-coresso-externo/download-planilha-nao-servidor/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_create_planilha_servidor_coresso(
    client_autenticado_codae_dilog, arquivo_xls, arquivo_pdf
):
    payload = {"conteudo": arquivo_xls}
    payload_extensao_invalida = {"conteudo": arquivo_pdf}
    response = client_autenticado_codae_dilog.post(
        "/planilha-coresso-servidor/", data=payload, format="multipart"
    )
    response_erro_forcado = client_autenticado_codae_dilog.post(
        "/planilha-coresso-servidor/",
        data=payload_extensao_invalida,
        format="multipart",
    )
    result = json.loads(response.content)

    assert response.status_code == status.HTTP_201_CREATED
    assert ImportacaoPlanilhaUsuarioServidorCoreSSO.objects.filter(
        uuid=result["uuid"]
    ).exists()
    planilha = ImportacaoPlanilhaUsuarioServidorCoreSSO.objects.get(uuid=result["uuid"])
    assert planilha.conteudo.name.split(".")[-1] == arquivo_xls.name.split(".")[-1]
    assert response_erro_forcado.status_code == status.HTTP_400_BAD_REQUEST


def test_processar_planilha_servidor_coresso(
    client_autenticado_codae_dilog, planilha_usuario_servidor, arquivo_xls
):
    assert (
        ImportacaoPlanilhaUsuarioServidorCoreSSO.objects.get(
            uuid=planilha_usuario_servidor.uuid
        ).status
        == "PENDENTE"
    )
    api_cria_ou_atualiza_usuario_core_sso = "sme_sigpae_api.perfil.services.usuario_coresso_service.EOLUsuarioCoreSSO.cria_ou_atualiza_usuario_core_sso"  # noqa
    with patch(api_cria_ou_atualiza_usuario_core_sso):
        response = client_autenticado_codae_dilog.post(
            f"/planilha-coresso-servidor/{planilha_usuario_servidor.uuid}/processar-importacao/"
        )
        response2 = client_autenticado_codae_dilog.post(
            "/planilha-coresso-servidor/F38e10da-c5e3-4dd5-9916-010fc250595a/processar-importacao/"
        )

    assert response.status_code == status.HTTP_200_OK
    assert response2.status_code == status.HTTP_404_NOT_FOUND


def test_remover_planilha_servidor_coresso(
    client_autenticado_codae_dilog, planilha_usuario_servidor, arquivo_xls
):
    response = client_autenticado_codae_dilog.patch(
        f"/planilha-coresso-servidor/{planilha_usuario_servidor.uuid}/remover/"
    )
    response2 = client_autenticado_codae_dilog.patch(
        "/planilha-coresso-servidor/F38e10da-c5e3-4dd5-9916-010fc250595a/remover/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response2.status_code == status.HTTP_404_NOT_FOUND


def test_busca_planilha_coresso_servidor(
    client_autenticado_codae_dilog, planilha_usuario_servidor
):
    response = client_autenticado_codae_dilog.get("/planilha-coresso-servidor/")
    assert response.status_code == status.HTTP_200_OK


def test_get_perfis_vinculados(client_autenticado_codae_dilog, perfis_vinculados):
    response = client_autenticado_codae_dilog.get("/perfis-vinculados/")
    assert response.status_code == status.HTTP_200_OK


def test_get_perfis_vinculados_subordinados(
    client_autenticado_codae_dilog, perfis_vinculados
):
    response = client_autenticado_codae_dilog.get(
        "/perfis-vinculados/ADMINISTRADOR_EMPRESA/perfis-subordinados/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_aceitar_termos(client_autenticado_codae_dilog, django_user_model):
    usuario = django_user_model.objects.get(
        pk=client_autenticado_codae_dilog.session["_auth_user_id"]
    )

    response = client_autenticado_codae_dilog.patch(
        f"/usuarios/{usuario.uuid}/aceitar-termos/"
    )

    usuario.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert usuario.aceitou_termos is True
