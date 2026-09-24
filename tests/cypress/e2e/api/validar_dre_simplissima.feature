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

  Cenario: Validar limite e deslocamento da paginacao
    Quando consulto duas paginas consecutivas de diretorias simplissimas
    Entao a paginacao de diretorias simplissimas respeita limite e deslocamento

  Cenario: Consultar pagina alem do total de diretorias
    Quando consulto diretorias simplissimas alem da ultima pagina
    Entao a pagina de diretorias simplissimas esta vazia

  Cenario: Rejeitar UUID malformado
    Quando consulto a diretoria simplissima pelo UUID "uuid-invalido"
    Entao a consulta da diretoria simplissima retorna status 404

  Esquema do Cenario: Consultar diretorias simplissimas sem autenticacao
    Quando consulto diretorias simplissimas na rota "<rota>" sem autenticacao
    Entao a consulta publica de diretorias simplissimas retorna dados validos
    Exemplos:
      | rota           |
      | listagem       |
      | detalhe        |
      | lista-completa |
