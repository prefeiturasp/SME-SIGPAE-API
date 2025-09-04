from typing import Optional

from pydantic import BaseModel, field_validator

TAMANHO_CODIGO_EOL_ALUNO = 7
TAMANHO_CPF = 11
TAMANHO_RF = 7


class ArquivoCargaDietaEspecialSchema(BaseModel):
    dre: Optional[str]
    tipo_gestao: Optional[str]
    tipo_unidade: Optional[str]
    codigo_escola: Optional[str]
    nome_unidade: Optional[str]
    codigo_eol_aluno: str
    nome_aluno: Optional[str]
    data_nascimento: Optional[str]
    data_ocorrencia: Optional[str]
    codigo_diagnostico: str
    protocolo_dieta: str
    codigo_categoria_dieta: str

    @field_validator("codigo_eol_aluno")
    def codigo_eol_aluno_deve_ter_7_digitos(cls, value):
        if len(value) != TAMANHO_CODIGO_EOL_ALUNO:
            raise ValueError("Codigo eol do aluno deve ter 7 dígitos.")
        return value


class ArquivoCargaAlimentosSchema(BaseModel):
    nome: str


class ArquivoCargaUsuariosDiretorSchema(BaseModel):
    dre: Optional[str]
    unidade_escola: Optional[str]
    codigo_eol_escola: str
    nome_diretor: Optional[str]
    rg_diretor: Optional[str]
    rf_diretor: str
    cpf_diretor: str
    email_diretor: str
    telefone_diretor: Optional[str]
    nome_assistente: Optional[str]
    rg_assistente: Optional[str]
    rf_assistente: str
    cpf_assistente: str
    email_assistente: str
    telefone_assistente: Optional[str]

    @field_validator(
        "codigo_eol_escola",
        "rf_diretor",
        "telefone_diretor",
        "telefone_assistente",
        mode="before",
    )
    def converte_para_str(cls, v):
        return str(v).strip() if v is not None else None

    @classmethod
    def formata_nome(cls, value):
        return value.upper()

    @classmethod
    def formata_documentos(cls, value):
        return value.replace(".", "").replace("-", "").strip()

    @classmethod
    def validate_cpf(cls, value):
        value = cls.formata_documentos(value)

        if len(value) != TAMANHO_CPF:
            raise ValueError("CPF deve conter 11 dígitos.")
        return value

    @field_validator("codigo_eol_escola")
    def formata_codigo_eol(cls, value):
        if not value:
            raise ValueError("Codigo eol da escola não pode ser vazio.")
        return f"{value:0>6}".strip()

    @field_validator("nome_diretor")
    def formata_nome_diretor(cls, value):
        if not value:
            raise ValueError("Nome do diretor não pode ser vazio.")
        return cls.formata_nome(value)

    @field_validator("rg_diretor")
    def formata_rg_diretor(cls, value):
        if not value:
            raise ValueError("RG do diretor não pode ser vazio.")
        return cls.formata_documentos(value)

    @field_validator("rf_diretor")
    def formata_rf_diretor(cls, value):
        if not value:
            raise ValueError("RF do diretor não pode ser vazio.")
        value = cls.formata_documentos(value)
        if len(value) != TAMANHO_RF:
            raise ValueError("RF deve ter 7 dígitos.")
        return value

    @field_validator("cpf_diretor")
    def validate_cpf_diretor(cls, value):
        if not value:
            raise ValueError("Cpf do diretor não pode ser vazio.")
        return cls.validate_cpf(value)

    @field_validator("nome_assistente")
    def formata_nome_assistente(cls, value):
        if not value:
            raise ValueError("Nome do assistente não pode ser vazio.")
        return cls.formata_nome(value)

    @field_validator("rg_assistente")
    def formata_rg_assistente(cls, value):
        if not value:
            raise ValueError("RG do assistente não pode ser vazio.")
        return cls.formata_documentos(value)

    @field_validator("rf_assistente")
    def formata_rf_assistente(cls, value):
        if not value:
            raise ValueError("RF do assistente não pode ser vazio.")
        value = cls.formata_documentos(value)

        if len(value) != TAMANHO_RF:
            raise ValueError("RF deve ter 7 dígitos.")
        return value

    @field_validator("cpf_assistente")
    def validate_cpf_assistente(cls, value):
        if not value:
            raise ValueError("CPF do assistente não pode ser vazio.")
        return cls.validate_cpf(value)
