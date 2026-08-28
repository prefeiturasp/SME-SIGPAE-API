# language: pt
Funcionalidade: Validar emails de terceirizadas por modulo

  Contexto:
    Dado que estou autenticado como CODAE para consultar emails de terceirizadas por modulo

  Cenario: Consultar emails de terceirizadas por modulo
    Quando consulto os emails de terceirizadas por modulo
    Entao a consulta retorna status 200 e uma lista paginada valida

  Cenario: Consultar email de terceirizada por UUID
    Quando consulto um email de terceirizada por UUID existente
    Entao a consulta por UUID retorna status 200 e os dados do email

  Cenario: Filtrar emails de terceirizadas por modulo com paginacao
    Quando consulto os emails de terceirizadas com limite 10 modulo "1" e deslocamento 10
    Entao a consulta filtrada retorna status 200 e respeita o limite informado

  Cenario: Impedir consulta sem autenticacao
    Quando consulto os emails de terceirizadas por modulo sem autenticacao
    Entao a consulta de emails de terceirizadas retorna status 401

  Cenario: Cadastrar email de terceirizada por modulo
    Quando cadastro um email de terceirizada usando os dados da consulta
    Entao o email de terceirizada por modulo e cadastrado com sucesso
