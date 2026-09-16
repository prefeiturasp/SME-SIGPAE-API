# language: pt
Funcionalidade: Validar faixas etarias

  Contexto:
    Dado que estou autenticado na API como CODAE para consultar faixas etarias

  Cenario: Validar GET com sucesso de faixas etarias
    Quando consulto as faixas etarias
    Entao a consulta de faixas etarias deve retornar status 200 e dados paginados validos
