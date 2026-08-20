# language: pt
Funcionalidade: Validar modalidades
  Contexto:
    Dado que estou autenticado como CODAE para consultar modalidades
  Cenario: Consultar modalidades com sucesso
    Quando consulto a lista de modalidades
    Entao a lista de modalidades retorna status 200 e dados paginados
  Cenario: Consultar modalidade por UUID valido
    Quando consulto uma modalidade existente por UUID
    Entao a modalidade retorna status 200 e o UUID consultado
  Cenario: Consultar modalidade por UUID invalido
    Quando consulto uma modalidade por UUID invalido
    Entao a modalidade retorna status 404
