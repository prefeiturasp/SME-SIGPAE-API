# language: pt
Funcionalidade: Validar nome de produtos do edital

  Contexto:
    Dado que estou autenticado na API como CODAE para consultar nomes de produtos

  Cenario: Validar GET com sucesso de nome de produtos do edital
    Quando consulto os nomes de produtos do edital
    Entao a consulta de nomes de produtos deve retornar status 200 e uma lista valida
