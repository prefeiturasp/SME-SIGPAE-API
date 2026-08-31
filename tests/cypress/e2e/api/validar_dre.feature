# language: pt
Funcionalidade: Validar diretorias regionais

  Contexto:
    Dado que estou autenticado como DRE para consultar diretorias regionais

  Cenario: Validar GET de diretoria regional com UUID valido
    Quando consulto uma diretoria regional com UUID valido
    Entao a diretoria regional deve retornar status 200 e os dados esperados

  Cenario: Validar GET de diretoria regional com UUID invalido
    Quando consulto uma diretoria regional com UUID invalido
    Entao a diretoria regional deve retornar status 404
