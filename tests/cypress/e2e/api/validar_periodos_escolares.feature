# language: pt
Funcionalidade: Validar periodos escolares
  Contexto:
    Dado que estou autenticado como CODAE para consultar periodos escolares
  Cenario: Consultar periodos escolares
    Quando consulto todos os periodos escolares
    Entao a lista de periodos escolares retorna dados validos
  Cenario: Consultar periodos escolares por nome valido
    Quando consulto periodos escolares por um nome existente
    Entao a consulta por nome retorna o periodo esperado
  Cenario: Consultar periodos escolares por nome invalido
    Quando consulto periodos escolares pelo nome invalido
    Entao a consulta por nome invalido retorna uma lista vazia
  Cenario: Consultar periodo escolar por UUID valido
    Quando consulto um periodo escolar por UUID existente
    Entao a consulta por UUID retorna o periodo esperado
  Cenario: Consultar periodo escolar por UUID invalido
    Quando consulto um periodo escolar por UUID invalido
    Entao a consulta do periodo invalido retorna status 400 ou 404
  Cenario: Consultar alunos por faixa etaria e data
    Quando consulto alunos por faixa etaria com data valida
    Entao a consulta por faixa etaria retorna status suportado e dados coerentes
  Cenario: Consultar alunos por faixa etaria com data invalida
    Quando consulto alunos por faixa etaria com data invalida
    Entao a consulta por data invalida retorna o erro esperado
  Cenario: Consultar alunos por faixa etaria com UUID invalido
    Quando consulto alunos por faixa etaria com UUID invalido
    Entao a consulta por UUID invalido retorna status 400 ou 404
  Cenario: Consultar inclusao continua por mes
    Quando consulto inclusao continua por mes como diretor de UE
    Entao a inclusao continua retorna status permitido e dados coerentes
