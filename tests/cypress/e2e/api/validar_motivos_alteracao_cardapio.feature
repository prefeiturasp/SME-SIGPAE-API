# language: pt
Funcionalidade: Validar motivos de alteracao de cardapio
  Contexto:
    Dado que estou autenticado como CODAE para consultar catalogos
  Cenario: Consultar lista de motivos de alteracao
    Quando consulto a lista do catalogo "motivos_alteracao_cardapio"
    Entao o catalogo retorna status 200 e campos "nome,ativo,uuid"
  Cenario: Consultar motivo de alteracao por UUID valido
    Quando consulto um item existente do catalogo "motivos_alteracao_cardapio"
    Entao o item do catalogo retorna status 200 e campos "nome,ativo,uuid"
  Cenario: Consultar motivo de alteracao por UUID invalido
    Quando consulto o catalogo "motivos_alteracao_cardapio" por UUID invalido
    Entao o item do catalogo retorna status 404
