# language: pt
Funcionalidade: Validar motivos de inclusao normal
  Contexto:
    Dado que estou autenticado como CODAE para consultar catalogos
  Cenario: Consultar lista de motivos de inclusao normal
    Quando consulto a lista do catalogo "motivos_inclusao_normal"
    Entao o catalogo retorna status 200 e campos "nome,uuid"
  Cenario: Consultar motivo de inclusao normal por UUID valido
    Quando consulto um item existente do catalogo "motivos_inclusao_normal"
    Entao o item do catalogo retorna status 200 e campos "nome,uuid"
  Cenario: Consultar motivo de inclusao normal por UUID invalido
    Quando consulto o catalogo "motivos_inclusao_normal" por UUID invalido
    Entao o item do catalogo retorna status 404
