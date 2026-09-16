# language: pt
Funcionalidade: Validar motivos de suspensao de cardapio
  Contexto:
    Dado que estou autenticado como CODAE para consultar catalogos
  Cenario: Consultar lista de motivos de suspensao
    Quando consulto a lista do catalogo "motivos_suspensao_cardapio"
    Entao o catalogo retorna status 200 e campos "nome,uuid"
  Cenario: Consultar motivo de suspensao por UUID valido
    Quando consulto um item existente do catalogo "motivos_suspensao_cardapio"
    Entao o item do catalogo retorna status 200 e campos "nome,uuid"
  Cenario: Consultar motivo de suspensao por UUID invalido
    Quando consulto o catalogo "motivos_suspensao_cardapio" por UUID invalido
    Entao o item do catalogo retorna status 404
