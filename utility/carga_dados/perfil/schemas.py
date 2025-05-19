from typing import Optional

from pydantic import BaseModel, root_validator, validator

TAMANHO_CPF = 11
TAMANHO_RF = 7


class ImportacaoPlanilhaUsuarioPerfilEscolaSchema(BaseModel):
    codigo_eol_escola: Optional[str]
    nome: Optional[str]
    cargo: Optional[str]
    email: Optional[str]
    cpf: Optional[str]
    telefone: Optional[str]
    rf: Optional[str]
    perfil: Optional[str]

    @classmethod
    def formata_documentos(cls, value):
        return value.replace(".", "").replace("-", "").strip()

    @classmethod
    def checa_vazio(cls, value, nome_parametro):
        if not value:
            raise Exception(f"{nome_parametro} não pode ser vazio.")

    @validator("codigo_eol_escola")
    def formata_codigo_eol(cls, value):
        cls.checa_vazio(value, "Codigo eol da escola")
        if len(value) == 5:
            value = f"0{value}"
        return f"{value:0>6}".strip()

    @validator("nome")
    def formata_nome(cls, value):
        cls.checa_vazio(value, "Nome do usuário")
        return value.upper().strip()

    @validator("cargo")
    def formata_cargo(cls, value):
        cls.checa_vazio(value, "Cargo do usuário")
        return value.upper().strip()

    @validator("email")
    def formata_email(cls, value):
        cls.checa_vazio(value, "Email do usuário")
        return value.strip()

    @validator("cpf")
    def validate_cpf(cls, value):
        cls.checa_vazio(value, "CPF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_CPF:
            raise ValueError("CPF deve conter 11 dígitos.")
        return value

    @validator("telefone")
    def formata_telefone(cls, value):
        cls.checa_vazio(value, "Telefone do usuário")
        return cls.formata_documentos(value)

    @validator("rf")
    def formata_rf(cls, value):
        cls.checa_vazio(value, "RF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_RF:
            raise ValueError("RF deve ter 7 dígitos.")
        return value

    @validator("perfil")
    def formata_perfil(cls, value):
        cls.checa_vazio(value, "Perfil do usuário")
        return value.upper().strip()


class ImportacaoPlanilhaUsuarioPerfilCodaeSchema(BaseModel):
    nome: Optional[str]
    cargo: Optional[str]
    email: Optional[str]
    cpf: Optional[str]
    telefone: Optional[str]
    rf: Optional[str]
    perfil: Optional[str]
    crn_numero: Optional[str]

    @classmethod
    def formata_documentos(cls, value):
        return value.replace(".", "").replace("-", "").strip()

    @classmethod
    def checa_vazio(cls, value, nome_parametro):
        if not value:
            raise Exception(f"{nome_parametro} não pode ser vazio.")

    @validator("nome")
    def formata_nome(cls, value):
        cls.checa_vazio(value, "Nome do usuário")
        return value.upper().strip()

    @validator("cargo")
    def formata_cargo(cls, value):
        cls.checa_vazio(value, "Cargo do usuário")
        return value.upper().strip()

    @validator("email")
    def formata_email(cls, value):
        cls.checa_vazio(value, "Email do usuário")
        return value.strip()

    @validator("cpf")
    def validate_cpf(cls, value):
        cls.checa_vazio(value, "CPF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_CPF:
            raise ValueError("CPF deve conter 11 dígitos.")
        return value

    @validator("telefone")
    def formata_telefone(cls, value):
        cls.checa_vazio(value, "Telefone do usuário")
        return cls.formata_documentos(value)

    @validator("rf")
    def formata_rf(cls, value):
        cls.checa_vazio(value, "RF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_RF:
            raise ValueError("RF deve ter 7 dígitos.")
        return value

    @validator("perfil")
    def formata_perfil(cls, value):
        cls.checa_vazio(value, "Perfil do usuário")
        return value.upper().strip()

    @validator("crn_numero")
    def formata_crn_numero(cls, value):
        if value:
            return cls.formata_documentos(value)
        return value


class ImportacaoPlanilhaUsuarioPerfilDreSchema(BaseModel):
    codigo_eol_dre: Optional[str]
    nome: Optional[str]
    cargo: Optional[str]
    email: Optional[str]
    cpf: Optional[str]
    telefone: Optional[str]
    rf: Optional[str]
    perfil: Optional[str]

    @classmethod
    def formata_documentos(cls, value):
        return value.replace(".", "").replace("-", "").strip()

    @classmethod
    def checa_vazio(cls, value, nome_parametro):
        if not value:
            raise Exception(f"{nome_parametro} não pode ser vazio.")

    @validator("codigo_eol_dre")
    def formata_codigo_eol_dre(cls, value):
        cls.checa_vazio(value, "Codigo eol da dre")
        if len(value) == 5:
            value = f"0{value}"
        return f"{value:0>6}".strip()

    @validator("nome")
    def formata_nome(cls, value):
        cls.checa_vazio(value, "Nome do usuário")
        return value.upper().strip()

    @validator("cargo")
    def formata_cargo(cls, value):
        cls.checa_vazio(value, "Cargo do usuário")
        return value.upper().strip()

    @validator("email")
    def formata_email(cls, value):
        cls.checa_vazio(value, "Email do usuário")
        return value.strip()

    @validator("cpf")
    def validate_cpf(cls, value):
        cls.checa_vazio(value, "CPF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_CPF:
            raise ValueError("CPF deve conter 11 dígitos.")
        return value

    @validator("telefone")
    def formata_telefone(cls, value):
        cls.checa_vazio(value, "Telefone do usuário")
        return cls.formata_documentos(value)

    @validator("rf")
    def formata_rf(cls, value):
        cls.checa_vazio(value, "RF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_RF:
            raise ValueError("RF deve ter 7 dígitos.")
        return value

    @validator("perfil")
    def formata_perfil(cls, value):
        cls.checa_vazio(value, "Perfil do usuário")
        return value.upper().strip()


class ImportacaoPlanilhaUsuarioServidorCoreSSOSchema(BaseModel):
    codigo_eol: Optional[str]
    nome: Optional[str]
    cargo: Optional[str]
    email: Optional[str]
    cpf: Optional[str]
    rf: Optional[str]
    tipo_perfil: Optional[str]
    perfil: Optional[str]
    codae: Optional[str]

    @classmethod
    def formata_documentos(cls, value):
        return value.replace(".", "").replace("-", "").strip()

    @classmethod
    def checa_vazio(cls, value, nome_parametro):
        if not value:
            raise Exception(f"{nome_parametro} não pode ser vazio.")

    @validator("codigo_eol")
    def formata_codigo_eol(cls, value):
        if value:
            if len(value) == 5:
                value = f"0{value}"
            return f"{value:0>6}".strip()

    @validator("nome")
    def formata_nome(cls, value):
        cls.checa_vazio(value, "Nome do usuário")
        return value.upper().strip()

    @validator("cargo")
    def formata_cargo(cls, value):
        cls.checa_vazio(value, "Cargo do usuário")
        return value.upper().strip()

    @validator("email")
    def formata_email(cls, value):
        cls.checa_vazio(value, "Email do usuário")
        return value.strip()

    @validator("cpf")
    def validate_cpf(cls, value):
        cls.checa_vazio(value, "CPF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_CPF:
            raise ValueError("CPF deve conter 11 dígitos.")
        return value

    @validator("rf")
    def formata_rf(cls, value):
        cls.checa_vazio(value, "RF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_RF:
            raise ValueError("RF deve ter 7 dígitos.")
        return value

    @validator("perfil")
    def formata_perfil(cls, value):
        cls.checa_vazio(value, "Perfil do usuário")
        value = value.upper().strip()
        return value

    @validator("tipo_perfil")
    def formata_tipo_perfil(cls, value):
        cls.checa_vazio(value, "Tipo de Perfil do usuário")
        value = value.upper().strip()
        return value

    @root_validator
    def validate_codigo_eol(cls, values):
        if values["tipo_perfil"].upper() != "CODAE":
            if not values["codigo_eol"]:
                raise ValueError("Codigo EOL obrigatório")
        else:
            if not values["codae"]:
                raise ValueError("CODAE obrigatório")
        return values


class ImportacaoPlanilhaUsuarioExternoCoreSSOSchema(BaseModel):
    nome: Optional[str]
    email: Optional[str]
    cpf: Optional[str]
    perfil: Optional[str]
    cnpj_terceirizada: Optional[str]

    @classmethod
    def formata_documentos(cls, value):
        return value.replace(".", "").replace("-", "").strip()

    @classmethod
    def checa_vazio(cls, value, nome_parametro):
        if not value:
            raise Exception(f"{nome_parametro} não pode ser vazio.")

    @validator("nome")
    def formata_nome(cls, value):
        cls.checa_vazio(value, "Nome do usuário")
        return value.upper().strip()

    @validator("email")
    def formata_email(cls, value):
        cls.checa_vazio(value, "Email do usuário")
        return value.strip()

    @validator("cpf")
    def validate_cpf(cls, value):
        cls.checa_vazio(value, "CPF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_CPF:
            raise ValueError("CPF deve conter 11 dígitos.")
        return value

    @validator("perfil")
    def formata_perfil(cls, value):
        cls.checa_vazio(value, "Perfil do usuário")
        value = value.upper().strip()
        return value


class ImportacaoPlanilhaUsuarioUEParceiraCoreSSOSchema(BaseModel):
    codigo_eol: Optional[str]
    nome: Optional[str]
    cargo: Optional[str]
    email: Optional[str]
    cpf: Optional[str]
    perfil: Optional[str]

    @classmethod
    def formata_documentos(cls, value):
        return value.replace(".", "").replace("-", "").strip()

    @classmethod
    def checa_vazio(cls, value, nome_parametro):
        if not value:
            raise Exception(f"{nome_parametro} não pode ser vazio.")

    @validator("codigo_eol")
    def formata_codigo_eol(cls, value):
        if value:
            if len(value) == 5:
                value = f"0{value}"
            return f"{value:0>6}".strip()

    @validator("nome")
    def formata_nome(cls, value):
        cls.checa_vazio(value, "Nome do usuário")
        return value.upper().strip()

    @validator("cargo")
    def formata_cargo(cls, value):
        cls.checa_vazio(value, "Cargo do usuário")
        return value.upper().strip()

    @validator("email")
    def formata_email(cls, value):
        cls.checa_vazio(value, "Email do usuário")
        return value.strip()

    @validator("cpf")
    def validate_cpf(cls, value):
        cls.checa_vazio(value, "CPF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_CPF:
            raise ValueError("CPF deve conter 11 dígitos.")
        return value

    @validator("perfil")
    def formata_perfil(cls, value):
        cls.checa_vazio(value, "Perfil do usuário")
        value = value.upper().strip()
        return value

    @root_validator
    def validate_codigo_eol(cls, values):
        if not values["codigo_eol"]:
            raise ValueError("Codigo EOL obrigatório")
        return values
