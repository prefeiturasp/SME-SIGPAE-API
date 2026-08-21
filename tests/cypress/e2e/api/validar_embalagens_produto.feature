# language: pt
Funcionalidade: Validar embalagens de produto

  Contexto:
    Dado que estou autenticado como CODAE para consultar embalagens de produto

  Cenario: Consultar todas as embalagens de produto
    Quando consulto todas as embalagens de produto
    Entao a consulta de embalagens de produto retorna status 200 e uma lista valida

  Cenario: Consultar embalagens de produto com paginacao
    Quando consulto embalagens de produto com limite 2 e deslocamento 2
    Entao a consulta paginada de embalagens de produto retorna status 200 e uma lista valida
