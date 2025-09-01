# app/schemas/importacao_planilha_usuario.py
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator

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
    def formata_documentos(cls, value: str) -> str:
        return value.replace(".", "").replace("-", "").strip()

    @classmethod
    def checa_vazio(cls, value: Optional[str], nome_parametro: str) -> None:
        if not value:
            raise ValueError(f"{nome_parametro} não pode ser vazio.")

    @field_validator("codigo_eol_escola")
    @classmethod
    def formata_codigo_eol(cls, value: str) -> str:
        cls.checa_vazio(value, "Codigo eol da escola")
        if len(value) == 5:
            value = f"0{value}"
        return f"{value:0>6}".strip()

    @field_validator("nome")
    @classmethod
    def formata_nome(cls, value: str) -> str:
        cls.checa_vazio(value, "Nome do usuário")
        return value.upper().strip()

    @field_validator("cargo")
    @classmethod
    def formata_cargo(cls, value: str) -> str:
        cls.checa_vazio(value, "Cargo do usuário")
        return value.upper().strip()

    @field_validator("email")
    @classmethod
    def formata_email(cls, value: str) -> str:
        cls.checa_vazio(value, "Email do usuário")
        return value.strip()

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, value: str) -> str:
        cls.checa_vazio(value, "CPF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_CPF:
            raise ValueError("CPF deve conter 11 dígitos.")
        return value

    @field_validator("telefone")
    @classmethod
    def formata_telefone(cls, value: str) -> str:
        cls.checa_vazio(value, "Telefone do usuário")
        return cls.formata_documentos(value)

    @field_validator("rf")
    @classmethod
    def formata_rf(cls, value: str) -> str:
        cls.checa_vazio(value, "RF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_RF:
            raise ValueError("RF deve ter 7 dígitos.")
        return value

    @field_validator("perfil")
    @classmethod
    def formata_perfil(cls, value: str) -> str:
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
    def formata_documentos(cls, value: str) -> str:
        return value.replace(".", "").replace("-", "").strip()

    @classmethod
    def checa_vazio(cls, value: Optional[str], nome_parametro: str) -> None:
        if not value:
            raise ValueError(f"{nome_parametro} não pode ser vazio.")

    @field_validator("nome")
    @classmethod
    def formata_nome(cls, value: str) -> str:
        cls.checa_vazio(value, "Nome do usuário")
        return value.upper().strip()

    @field_validator("cargo")
    @classmethod
    def formata_cargo(cls, value: str) -> str:
        cls.checa_vazio(value, "Cargo do usuário")
        return value.upper().strip()

    @field_validator("email")
    @classmethod
    def formata_email(cls, value: str) -> str:
        cls.checa_vazio(value, "Email do usuário")
        return value.strip()

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, value: str) -> str:
        cls.checa_vazio(value, "CPF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_CPF:
            raise ValueError("CPF deve conter 11 dígitos.")
        return value

    @field_validator("telefone")
    @classmethod
    def formata_telefone(cls, value: str) -> str:
        cls.checa_vazio(value, "Telefone do usuário")
        return cls.formata_documentos(value)

    @field_validator("rf")
    @classmethod
    def formata_rf(cls, value: str) -> str:
        cls.checa_vazio(value, "RF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_RF:
            raise ValueError("RF deve ter 7 dígitos.")
        return value

    @field_validator("perfil")
    @classmethod
    def formata_perfil(cls, value: str) -> str:
        cls.checa_vazio(value, "Perfil do usuário")
        return value.upper().strip()

    @field_validator("crn_numero")
    @classmethod
    def formata_crn_numero(cls, value: Optional[str]) -> Optional[str]:
        return cls.formata_documentos(value) if value else value


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
    def formata_documentos(cls, value: str) -> str:
        return value.replace(".", "").replace("-", "").strip()

    @classmethod
    def checa_vazio(cls, value: Optional[str], nome_parametro: str) -> None:
        if not value:
            raise ValueError(f"{nome_parametro} não pode ser vazio.")

    @field_validator("codigo_eol_dre")
    @classmethod
    def formata_codigo_eol_dre(cls, value: str) -> str:
        cls.checa_vazio(value, "Codigo eol da dre")
        if len(value) == 5:
            value = f"0{value}"
        return f"{value:0>6}".strip()

    @field_validator("nome")
    @classmethod
    def formata_nome(cls, value: str) -> str:
        cls.checa_vazio(value, "Nome do usuário")
        return value.upper().strip()

    @field_validator("cargo")
    @classmethod
    def formata_cargo(cls, value: str) -> str:
        cls.checa_vazio(value, "Cargo do usuário")
        return value.upper().strip()

    @field_validator("email")
    @classmethod
    def formata_email(cls, value: str) -> str:
        cls.checa_vazio(value, "Email do usuário")
        return value.strip()

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, value: str) -> str:
        cls.checa_vazio(value, "CPF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_CPF:
            raise ValueError("CPF deve conter 11 dígitos.")
        return value

    @field_validator("telefone")
    @classmethod
    def formata_telefone(cls, value: str) -> str:
        cls.checa_vazio(value, "Telefone do usuário")
        return cls.formata_documentos(value)

    @field_validator("rf")
    @classmethod
    def formata_rf(cls, value: str) -> str:
        cls.checa_vazio(value, "RF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_RF:
            raise ValueError("RF deve ter 7 dígitos.")
        return value

    @field_validator("perfil")
    @classmethod
    def formata_perfil(cls, value: str) -> str:
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
    def formata_documentos(cls, value: str) -> str:
        return value.replace(".", "").replace("-", "").strip()

    @classmethod
    def checa_vazio(cls, value: Optional[str], nome_parametro: str) -> None:
        if not value:
            raise ValueError(f"{nome_parametro} não pode ser vazio.")

    @field_validator("codigo_eol")
    @classmethod
    def formata_codigo_eol(cls, value: Optional[str]) -> Optional[str]:
        if value:
            if len(value) == 5:
                value = f"0{value}"
            return f"{value:0>6}".strip()
        return value

    @field_validator("nome")
    @classmethod
    def formata_nome(cls, value: str) -> str:
        cls.checa_vazio(value, "Nome do usuário")
        return value.upper().strip()

    @field_validator("cargo")
    @classmethod
    def formata_cargo(cls, value: str) -> str:
        cls.checa_vazio(value, "Cargo do usuário")
        return value.upper().strip()

    @field_validator("email")
    @classmethod
    def formata_email(cls, value: str) -> str:
        cls.checa_vazio(value, "Email do usuário")
        return value.strip()

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, value: str) -> str:
        cls.checa_vazio(value, "CPF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_CPF:
            raise ValueError("CPF deve conter 11 dígitos.")
        return value

    @field_validator("rf")
    @classmethod
    def formata_rf(cls, value: str) -> str:
        cls.checa_vazio(value, "RF do usuário")
        value = cls.formata_documentos(value)
        if len(value) not in (TAMANHO_RF, TAMANHO_CPF):
            raise ValueError("RF deve ter 7 ou 11 dígitos (PARCEIRA).")
        return value

    @field_validator("perfil")
    @classmethod
    def formata_perfil(cls, value: str) -> str:
        cls.checa_vazio(value, "Perfil do usuário")
        return value.upper().strip()

    @field_validator("tipo_perfil")
    @classmethod
    def formata_tipo_perfil(cls, value: str) -> str:
        cls.checa_vazio(value, "Tipo de Perfil do usuário")
        return value.upper().strip()

    @model_validator(mode="after")
    def validate_codigo_eol(self):
        if self.tipo_perfil and self.tipo_perfil.upper() != "CODAE":
            if not self.codigo_eol:
                raise ValueError("Codigo EOL obrigatório")
        else:
            if not self.codae:
                raise ValueError("CODAE obrigatório")
        return self


class ImportacaoPlanilhaUsuarioExternoCoreSSOSchema(BaseModel):
    nome: Optional[str]
    email: Optional[str]
    cpf: Optional[str]
    perfil: Optional[str]
    cnpj_terceirizada: Optional[str]

    @classmethod
    def formata_documentos(cls, value: str) -> str:
        return value.replace(".", "").replace("-", "").strip()

    @classmethod
    def checa_vazio(cls, value: Optional[str], nome_parametro: str) -> None:
        if not value:
            raise ValueError(f"{nome_parametro} não pode ser vazio.")

    @field_validator("nome")
    @classmethod
    def formata_nome(cls, value: str) -> str:
        cls.checa_vazio(value, "Nome do usuário")
        return value.upper().strip()

    @field_validator("email")
    @classmethod
    def formata_email(cls, value: str) -> str:
        cls.checa_vazio(value, "Email do usuário")
        return value.strip()

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, value: str) -> str:
        cls.checa_vazio(value, "CPF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_CPF:
            raise ValueError("CPF deve conter 11 dígitos.")
        return value

    @field_validator("perfil")
    @classmethod
    def formata_perfil(cls, value: str) -> str:
        cls.checa_vazio(value, "Perfil do usuário")
        return value.upper().strip()


class ImportacaoPlanilhaUsuarioUEParceiraCoreSSOSchema(BaseModel):
    codigo_eol: Optional[str]
    nome: Optional[str]
    cargo: Optional[str]
    email: Optional[str]
    cpf: Optional[str]
    perfil: Optional[str]

    @classmethod
    def formata_documentos(cls, value: str) -> str:
        return value.replace(".", "").replace("-", "").strip()

    @classmethod
    def checa_vazio(cls, value: Optional[str], nome_parametro: str) -> None:
        if not value:
            raise ValueError(f"{nome_parametro} não pode ser vazio.")

    @field_validator("codigo_eol")
    @classmethod
    def formata_codigo_eol(cls, value: Optional[str]) -> Optional[str]:
        if value:
            if len(value) == 5:
                value = f"0{value}"
            return f"{value:0>6}".strip()
        return value

    @field_validator("nome")
    @classmethod
    def formata_nome(cls, value: str) -> str:
        cls.checa_vazio(value, "Nome do usuário")
        return value.upper().strip()

    @field_validator("cargo")
    @classmethod
    def formata_cargo(cls, value: str) -> str:
        cls.checa_vazio(value, "Cargo do usuário")
        return value.upper().strip()

    @field_validator("email")
    @classmethod
    def formata_email(cls, value: str) -> str:
        cls.checa_vazio(value, "Email do usuário")
        return value.strip()

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, value: str) -> str:
        cls.checa_vazio(value, "CPF do usuário")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_CPF:
            raise ValueError("CPF deve conter 11 dígitos.")
        return value

    @field_validator("perfil")
    @classmethod
    def formata_perfil(cls, value: str) -> str:
        cls.checa_vazio(value, "Perfil do usuário")
        return value.upper().strip()

    @model_validator(mode="after")
    def validate_codigo_eol(self):
        if not self.codigo_eol:
            raise ValueError("Codigo EOL obrigatório")
        return self
