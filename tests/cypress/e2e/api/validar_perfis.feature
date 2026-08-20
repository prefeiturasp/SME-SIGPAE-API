# language: pt
Funcionalidade: Validar perfis
  Contexto:
    Dado que estou autenticado como CODAE para consultar perfis
  Cenario: Consultar lista de perfis
    Quando consulto a lista de perfis
    Entao a lista de perfis retorna status 200 e dados paginados
  Cenario: Consultar perfil por UUID valido
    Quando consulto um perfil existente por UUID
    Entao o perfil retorna status 200 e os dados esperados
  Cenario: Consultar perfil por UUID invalido
    Quando consulto um perfil por UUID invalido
    Entao o perfil retorna status 404
  Cenario: Consultar visoes dos perfis
    Quando consulto as visoes dos perfis
    Entao as visoes dos perfis retornam status 200 e uma lista valida
