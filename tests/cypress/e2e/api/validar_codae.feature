# language: pt
Funcionalidade: Validar rota CODAE

  Contexto:
    Dado que estou autenticado na API como CODAE para consultar a CODAE

  Cenario: Validar GET paginado com sucesso da CODAE
    Quando consulto a lista paginada da CODAE
    Entao a consulta da CODAE deve retornar status 200 e registros validos
