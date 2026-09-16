# language: pt
Funcionalidade: Validar diretorias regionais simplissimas
  Contexto:
    Dado que estou autenticado como DRE para consultar diretorias simplissimas
  Cenario: Consultar lista paginada de diretorias simplissimas
    Quando consulto a lista paginada de diretorias simplissimas
    Entao a lista de diretorias simplissimas retorna status 200 e dados validos
  Esquema do Cenario: Consultar diretoria simplissima por UUID
    Quando consulto a diretoria simplissima pelo UUID "<uuid>"
    Entao a consulta da diretoria simplissima retorna status <status>
    E quando encontrada apresenta os campos esperados da diretoria
    Exemplos:
      | uuid                                 | status |
      | 8f1da4a7-11b6-4a09-9eaa-6633d066f26b | 200    |
      | 3fa85f64-5717-4562-b3fc-2c963f66afa6 | 404    |
  Cenario: Consultar lista completa de diretorias simplissimas
    Quando consulto a lista completa de diretorias simplissimas
    Entao a lista completa de diretorias simplissimas retorna dados validos
