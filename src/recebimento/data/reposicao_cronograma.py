"""Seed data dos tipos de reposição de cronograma da ficha de recebimento.

Lista consumida pela carga de dados
(``utility.carga_dados.recebimento.importa_dados``) para popular os tipos
de reposição disponíveis: repor os produtos faltantes/recusados ou fazer
carta de crédito do valor pago.
"""

data_reposicao_cronograma = [
    {"tipo": "Repor", "descricao": "REPOR OS PRODUTOS FALTANTES/RECUSADOS"},
    {"tipo": "Credito", "descricao": "FAZER UMA CARTA DE CRÉDITO DO VALOR PAGO"},
]
