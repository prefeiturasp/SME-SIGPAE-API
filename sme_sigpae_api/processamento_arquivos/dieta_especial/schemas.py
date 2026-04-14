from typing import Optional

from pydantic import BaseModel, field_validator

TAMANHO_CODIGO_EOL_ALUNO = 7


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
