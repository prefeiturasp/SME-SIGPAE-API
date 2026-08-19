# language: pt
Funcionalidade: Validar motivos de alteracao da UE

  Contexto:
    Dado que estou autenticado na API como CODAE para consultar motivos de alteracao da UE

  Cenario: Validar GET com sucesso de motivo de alteracao da UE
    Quando consulto os motivos de alteracao da UE
    Entao a consulta de motivos da UE deve retornar status 200 e dados paginados validos
