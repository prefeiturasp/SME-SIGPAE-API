# language: pt
Funcionalidade: Validar informacoes nutricionais
  Contexto:
    Dado que estou autenticado como CODAE para consultar informacoes nutricionais
  Cenario: Consultar lista de informacoes nutricionais
    Quando consulto a lista de informacoes nutricionais
    Entao a lista de informacoes nutricionais retorna dados validos
  Cenario: Consultar informacao nutricional por UUID valido
    Quando consulto uma informacao nutricional existente por UUID
    Entao a informacao nutricional retorna os dados esperados
  Cenario: Consultar informacao nutricional por UUID invalido
    Quando consulto uma informacao nutricional por UUID invalido
    Entao a informacao nutricional retorna status 404
  Cenario: Consultar informacoes nutricionais agrupadas
    Quando consulto as informacoes nutricionais agrupadas
    Entao as informacoes agrupadas retornam dados validos
  Cenario: Consultar informacoes nutricionais ordenadas
    Quando consulto as informacoes nutricionais ordenadas
    Entao as informacoes ordenadas retornam dados validos
