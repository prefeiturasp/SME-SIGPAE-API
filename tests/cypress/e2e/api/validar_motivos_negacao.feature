# language: pt
Funcionalidade: Validar motivos de negacao
  Contexto:
    Dado que estou autenticado como CODAE para consultar motivos de negacao
  Cenario: Consultar todos os motivos de negacao
    Quando consulto todos os motivos de negacao
    Entao a API retorna uma lista valida de motivos de negacao
  Esquema do Cenario: Consultar motivos por processo valido
    Quando consulto motivos de negacao pelo processo "<processo>"
    Entao a API retorna motivos do processo "<processo>"
    Exemplos:
      | processo |
      | INCLUSAO |
  Cenario: Consultar motivos por processo invalido
    Quando consulto motivos de negacao pelo processo "NomeInvalidoParaoTeste"
    Entao a API retorna status 400 e erro no processo
  Cenario: Consultar motivo de negacao por ID valido
    Quando consulto um motivo de negacao existente por ID
    Entao a API retorna o motivo de negacao consultado
  Cenario: Consultar motivo de negacao por ID invalido
    Quando consulto um motivo de negacao pelo ID invalido
    Entao a consulta do motivo de negacao retorna status 404
