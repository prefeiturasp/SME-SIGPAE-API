# app/schemas/importacao_planilha.py
from typing import Optional, Union

from pydantic import BaseModel, field_validator


class ImportacaoPlanilhaTipoPenalidadeSchema(BaseModel):
    edital: Optional[str]
    numero_clausula: Optional[str]
    gravidade: Optional[str]
    obrigacoes: Optional[str]
    descricao_clausula: Optional[str]
    status: Optional[str]

    @classmethod
    def checa_vazio(cls, value: Optional[str], nome_parametro: str) -> None:
        if not value:
            raise ValueError(f"{nome_parametro} não pode ser vazio.")

    @field_validator("edital")
    @classmethod
    def valida_edital(cls, value: str) -> str:
        cls.checa_vazio(value, "Edital")
        return value.strip()

    @field_validator("numero_clausula")
    @classmethod
    def valida_numero_clausula(cls, value: str) -> str:
        cls.checa_vazio(value, "Número da Cláusula/Item")
        return value.strip()

    @field_validator("gravidade")
    @classmethod
    def valida_gravidade(cls, value: str) -> str:
        cls.checa_vazio(value, "Gravidade")
        return value.strip()

    @field_validator("obrigacoes")
    @classmethod
    def valida_obrigacoes(cls, value: str) -> str:
        cls.checa_vazio(value, "Obrigações")
        return value.strip()

    @field_validator("descricao_clausula")
    @classmethod
    def valida_descricao_clausula(cls, value: str) -> str:
        cls.checa_vazio(value, "Descrição da Cláusula/Item")
        return value.strip()

    @field_validator("status")
    @classmethod
    def valida_status(cls, value: str) -> str:
        cls.checa_vazio(value, "Status")
        return value.strip()


class ImportacaoPlanilhaTipoOcorrenciaSchema(BaseModel):
    posicao: Optional[Union[str, int]]
    perfis: Optional[str]
    edital: Optional[str]
    categoria_ocorrencia: Optional[str]
    titulo: Optional[str]
    descricao: Optional[str]
    penalidade: Optional[str]
    eh_imr: Optional[str]
    pontuacao: Optional[Union[str, int]]
    tolerancia: Optional[Union[str, int]]
    porcentagem_desconto: Optional[Union[str, int]]
    status: Optional[str]
    aceita_multiplas_respostas: Optional[str]

    @field_validator(
        "posicao", "pontuacao", "tolerancia", "porcentagem_desconto", mode="before"
    )
    def converte_para_str(cls, v):
        return str(v).strip() if v is not None else None

    @classmethod
    def checa_vazio(cls, value: Optional[str], nome_parametro: str) -> None:
        if not value:
            raise ValueError(f"{nome_parametro} não pode ser vazio.")

    @classmethod
    def eh_inteiro(cls, value: Optional[str], nome_parametro: str) -> None:
        if value and not value.isdigit():
            raise ValueError(f"{nome_parametro} deve ser um número inteiro positivo.")

    @field_validator("posicao")
    @classmethod
    def valida_posicao(cls, value: str) -> str:
        cls.checa_vazio(value, "Posição")
        cls.eh_inteiro(value, "Posição")
        return value.strip()

    @field_validator("perfis")
    @classmethod
    def valida_perfis(cls, value: str) -> str:
        cls.checa_vazio(value, "Perfis")
        return value.strip()

    @field_validator("edital")
    @classmethod
    def valida_edital(cls, value: str) -> str:
        cls.checa_vazio(value, "Edital")
        return value.strip()

    @field_validator("categoria_ocorrencia")
    @classmethod
    def valida_categoria_ocorrencia(cls, value: str) -> str:
        cls.checa_vazio(value, "Categoria da Ocorrência")
        return value.strip()

    @field_validator("titulo")
    @classmethod
    def valida_titulo(cls, value: str) -> str:
        cls.checa_vazio(value, "Titulo")
        return value.strip()

    @field_validator("descricao")
    @classmethod
    def valida_descricao(cls, value: str) -> str:
        cls.checa_vazio(value, "Descrição")
        return value.strip()

    @field_validator("penalidade")
    @classmethod
    def valida_penalidade(cls, value: str) -> str:
        cls.checa_vazio(value, "Penalidade")
        return value.strip()

    @field_validator("eh_imr")
    @classmethod
    def valida_eh_imr(cls, value: str) -> str:
        cls.checa_vazio(value, "É IMR?")
        return value.strip()

    @field_validator("pontuacao")
    @classmethod
    def valida_pontuacao(cls, value: Optional[str], info) -> Optional[str]:
        eh_imr = info.data.get("eh_imr")
        if eh_imr == "NÃO" and value:
            raise ValueError("Pontuação não deve ser preenchida se é IMR.")
        if eh_imr == "SIM" and not value:
            raise ValueError("Pontuação deve ser preenchida se é IMR.")
        cls.eh_inteiro(value, "Pontuação (IMR)")
        return value.strip() if value else None

    @field_validator("tolerancia")
    @classmethod
    def valida_tolerancia(cls, value: Optional[str], info) -> Optional[str]:
        eh_imr = info.data.get("eh_imr")
        if eh_imr == "NÃO" and value:
            raise ValueError("Tolerância não deve ser preenchida se é IMR.")
        if eh_imr == "SIM" and not value:
            raise ValueError("Tolerância deve ser preenchida se é IMR.")
        cls.eh_inteiro(value, "Tolerância")
        return value.strip() if value else None

    @field_validator("porcentagem_desconto")
    @classmethod
    def valida_porcentagem_desconto(cls, value: str) -> str:
        cls.checa_vazio(value, "% de Desconto")
        return value.strip()

    @field_validator("status")
    @classmethod
    def valida_status(cls, value: str) -> str:
        cls.checa_vazio(value, "Status")
        return value.strip()

    @field_validator("aceita_multiplas_respostas")
    @classmethod
    def valida_aceita_multiplas_respostas(cls, value: str) -> str:
        cls.checa_vazio(value, "Aceita múltiplas respostas")
        return value.strip()
