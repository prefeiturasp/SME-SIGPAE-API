from rest_framework import serializers, status
from rest_framework.response import Response

from ...eol_servico.utils import EOLException
from ...terceirizada.models import Terceirizada
from ..models import Perfil, Usuario


def senha_deve_ser_igual_confirmar_senha(senha: str, confirmar_senha: str):
    if senha != confirmar_senha:
        raise serializers.ValidationError("Senha e confirmar senha divergem")
    return True


def registro_funcional_e_cpf_sao_da_mesma_pessoa(
    usuario: Usuario, registro_funcional: str, cpf: str
):
    if usuario.cpf != cpf or usuario.registro_funcional != registro_funcional:
        raise serializers.ValidationError("Erro ao cadastrar usuário")
    return True


def terceirizada_tem_esse_cnpj(terceirizada: Terceirizada, cnpj: str):
    if terceirizada.cnpj != cnpj:
        raise serializers.ValidationError("CNPJ da Empresa inválido")
    return True


def usuario_e_das_terceirizadas(usuario: Usuario):
    if usuario.vinculo_atual is None:
        raise serializers.ValidationError("Usuario não possui vinculo com instituição")
    if not isinstance(usuario.vinculo_atual.instituicao, Terceirizada):
        raise serializers.ValidationError(
            "Usuario já existe e não é Perfil Terceirizadas"
        )
    return True


def deve_ter_mesmo_cpf(cpf_request: str, cpf_instance: str):
    if cpf_request != cpf_instance:
        raise serializers.ValidationError("CPF incorreto")
    return True


def usuario_pode_efetuar_cadastro(usuario: Usuario):
    try:
        if not usuario.pode_efetuar_cadastro:
            raise serializers.ValidationError("Erro ao cadastrar usuário")
    except EOLException as e:
        raise serializers.ValidationError(f"{e}")
    return True


def deve_ser_email_sme_ou_prefeitura(email):
    if (
        "@sme.prefeitura.sp.gov.br" not in email
        and "@prefeitura.sp.gov.br" not in email
    ):
        raise serializers.ValidationError("Deve ser email da SME")
    return True


def usuario_e_vinculado_a_aquela_instituicao(
    descricao_instituicao: str, response: Response
):
    dados = response.json()
    instituicao = dados.get("cargos")[0].get("descricaoUnidade").replace(" - ", " ")
    pertencem_mesma_divisao = (
        instituicao in descricao_instituicao or descricao_instituicao in instituicao
    )
    pertencem_a_codae = (
        "codae" in instituicao.lower() and "codae" in descricao_instituicao.lower()
    )
    if pertencem_mesma_divisao or pertencem_a_codae:
        return True
    raise serializers.ValidationError("Instituições devem ser a mesma")


def usuario_nao_possui_vinculo_valido(usuario: Usuario):
    if usuario.vinculo_atual is not None:
        raise serializers.ValidationError(
            "Usuário já possui vínculo válido", code=status.HTTP_400_BAD_REQUEST
        )
    return True


def usuario_com_coresso_validation(visao, subdivisao):
    if visao == Perfil.CODAE:
        if not subdivisao:
            raise serializers.ValidationError(
                {
                    "detail": f"É necessário Informar a subdivisão da visão {Perfil.CODAE}"
                }
            )


def checa_senha(usuario, senha):
    if not usuario.check_password(senha):
        raise serializers.ValidationError({"detail": "Senha atual incorreta"})
