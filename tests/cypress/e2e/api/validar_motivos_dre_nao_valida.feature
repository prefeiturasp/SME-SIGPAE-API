# language: pt
Funcionalidade: Validar motivos pelos quais a DRE nao valida
  Contexto:
    Dado que estou autenticado como CODAE para consultar motivos da DRE
  Cenario: Consultar motivos da DRE com sucesso
    Quando consulto a lista de motivos da DRE
    Entao a lista de motivos da DRE retorna status 200 e dados paginados
  Cenario: Consultar motivo da DRE por UUID valido
    Quando consulto um motivo existente da DRE por UUID
    Entao o motivo da DRE retorna status 200 e o UUID consultado
  Cenario: Consultar motivo da DRE por UUID invalido
    Quando consulto um motivo da DRE por UUID invalido
    Entao o motivo da DRE retorna status 404
