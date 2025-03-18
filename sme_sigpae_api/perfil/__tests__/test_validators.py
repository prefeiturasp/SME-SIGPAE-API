from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from rest_framework.exceptions import ValidationError

from sme_sigpae_api.eol_servico.utils import EOLException
from sme_sigpae_api.perfil.models.perfil import Perfil
from sme_sigpae_api.perfil.models.usuario import Usuario

from ..api.validators import (
    checa_senha,
    deve_ser_email_sme_ou_prefeitura,
    deve_ter_mesmo_cpf,
    registro_funcional_e_cpf_sao_da_mesma_pessoa,
    senha_deve_ser_igual_confirmar_senha,
    terceirizada_tem_esse_cnpj,
    usuario_com_coresso_validation,
    usuario_e_das_terceirizadas,
    usuario_e_vinculado_a_aquela_instituicao,
    usuario_nao_possui_vinculo_valido,
    usuario_pode_efetuar_cadastro,
)

pytestmark = pytest.mark.django_db


def test_senha_deve_ser_igual_confirmar_senha():
    assert senha_deve_ser_igual_confirmar_senha("1", "1") is True
    assert senha_deve_ser_igual_confirmar_senha("134", "134") is True
    assert senha_deve_ser_igual_confirmar_senha("!@#$%", "!@#$%") is True
    with pytest.raises(ValidationError, match="Senha e confirmar senha divergem"):
        senha_deve_ser_igual_confirmar_senha("134", "1343")
        senha_deve_ser_igual_confirmar_senha("senha", "senha1")


def test_registro_funcional_e_cpf_sao_da_mesma_pessoa(usuario):
    assert (
        registro_funcional_e_cpf_sao_da_mesma_pessoa(
            usuario, registro_funcional="1234567", cpf="52347255100"
        )
        is True
    )
    with pytest.raises(ValidationError, match="Erro ao cadastrar usuário"):
        registro_funcional_e_cpf_sao_da_mesma_pessoa(
            usuario, registro_funcional="1234567", cpf="52347255101"
        )
        registro_funcional_e_cpf_sao_da_mesma_pessoa(
            usuario, registro_funcional="1234568", cpf="52347255100"
        )


def test_deve_ser_email_sme_ou_prefeitura(email_list):
    email, _ = email_list
    assert deve_ser_email_sme_ou_prefeitura(email) is True


def test_deve_ser_email_sme_ou_prefeitura_invalidos(email_list_invalidos):
    email, _ = email_list_invalidos
    with pytest.raises(ValidationError, match="Deve ser email da SME"):
        deve_ser_email_sme_ou_prefeitura(email)


def test_terceirizada_tem_esse_cnpj_valido(terceirizada):
    assert terceirizada_tem_esse_cnpj(terceirizada, terceirizada.cnpj)


def test_terceirizada_tem_esse_cnpj_invalido(terceirizada):
    with pytest.raises(ValidationError, match="CNPJ da Empresa inválido"):
        terceirizada_tem_esse_cnpj(terceirizada, "123456789")


def test_usuario_e_das_terceirizadas_usuarios_validos(users_terceirizada):
    _, _, _, _, _, usuario = users_terceirizada
    assert usuario_e_das_terceirizadas(usuario)


def test_usuario_e_das_terceirizadas_usuarios_invalidos(users_codae_gestao_alimentacao):
    _, _, _, _, _, usuario = users_codae_gestao_alimentacao

    with pytest.raises(
        ValidationError, match="Usuario já existe e não é Perfil Terceirizadas"
    ):
        usuario_e_das_terceirizadas(usuario)


def test_usuario_e_das_terceirizadas_usuario_sem_vinculo(usuario):
    with pytest.raises(
        ValidationError, match="Usuario não possui vinculo com instituição"
    ):
        usuario_e_das_terceirizadas(usuario)


def test_deve_ter_mesmo_cpf_valido(usuario):
    assert deve_ter_mesmo_cpf(usuario.cpf, usuario.cpf)


def test_deve_ter_mesmo_cpf_invalido(usuario, usuario_2):
    with pytest.raises(ValidationError, match="CPF incorreto"):
        deve_ter_mesmo_cpf(usuario.cpf, usuario_2.cpf)


def test_usuario_pode_efetuar_cadastro_retorna_true(usuario):
    with patch.object(
        Usuario, "pode_efetuar_cadastro", new_callable=PropertyMock, return_value=True
    ):
        assert usuario_pode_efetuar_cadastro(usuario) is True


def test_usuario_pode_efetuar_cadastro_erro(usuario):
    with patch.object(
        Usuario, "pode_efetuar_cadastro", new_callable=PropertyMock, return_value=False
    ):
        with pytest.raises(ValidationError, match="Erro ao cadastrar usuário"):
            usuario_pode_efetuar_cadastro(usuario)


def test_usuario_pode_efetuar_cadastro_erro_eol(usuario):
    with patch.object(
        Usuario,
        "pode_efetuar_cadastro",
        new_callable=PropertyMock,
        side_effect=EOLException("Erro no EOL"),
    ):
        with pytest.raises(ValidationError, match="Erro no EOL"):
            usuario_pode_efetuar_cadastro(usuario)


def test_usuario_e_vinculado_a_aquela_instituicao():
    response_mock = MagicMock()
    response_mock.json.return_value = {
        "cargos": [{"descricaoUnidade": "ESCOLA EMF de responsabilidade da CODAE"}]
    }
    descricao_instituicao = "ESCOLA EMF - CODAE"
    assert usuario_e_vinculado_a_aquela_instituicao(
        descricao_instituicao, response_mock
    )


def test_usuario_e_vinculado_a_aquela_instituicao_erro():
    response_mock = MagicMock()
    response_mock.json.return_value = {
        "cargos": [{"descricaoUnidade": "ESCOLA EMF de responsabilidade da CODAE"}]
    }
    descricao_instituicao = "ESCOLA EMEF do estado"
    with pytest.raises(ValidationError, match="Instituições devem ser a mesma"):
        usuario_e_vinculado_a_aquela_instituicao(descricao_instituicao, response_mock)


def test_usuario_nao_possui_vinculo_valido_sem_vinculo(usuario):
    assert usuario_nao_possui_vinculo_valido(usuario)


def test_usuario_nao_possui_vinculo_valido_vinculo_encontrado(usuario_3):
    with pytest.raises(ValidationError, match="Usuário já possui vínculo válido"):
        usuario_nao_possui_vinculo_valido(usuario_3)


def test_usuario_com_coresso_validation():
    assert usuario_com_coresso_validation(Perfil.CODAE, "escola") is None
    assert usuario_com_coresso_validation(Perfil.ESCOLA, None) is None
    assert usuario_com_coresso_validation(Perfil.DRE, None) is None
    assert usuario_com_coresso_validation(Perfil.EMPRESA, None) is None


def test_usuario_com_coresso_validation_erro():
    with pytest.raises(
        ValidationError,
        match=f"É necessário Informar a subdivisão da visão {Perfil.CODAE}",
    ):
        usuario_com_coresso_validation(Perfil.CODAE, None) is None


def test_checa_senha(users_admin_escola):
    _, _, senha, _, usuario = users_admin_escola
    assert checa_senha(usuario, senha) is None


def test_checa_senha_incorreta(users_admin_escola):
    _, _, _, _, usuario = users_admin_escola
    with pytest.raises(ValidationError, match=f"Senha atual incorreta"):
        checa_senha(usuario, usuario.password)
