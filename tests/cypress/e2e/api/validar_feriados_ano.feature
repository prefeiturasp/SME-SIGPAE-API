# language: pt
Funcionalidade: Validar feriados por ano

  Contexto:
    Dado que estou autenticado como CODAE para consultar feriados

  Cenario: Validar GET com sucesso de feriados por ano
    Quando consulto os feriados por ano
    Entao a consulta de feriados deve retornar status 200 e uma lista

  Cenario: Validar GET com sucesso de feriados do ano atual e proximo
    Quando consulto os feriados do ano atual e do proximo
    Entao a consulta de feriados deve retornar status 200 e uma lista
