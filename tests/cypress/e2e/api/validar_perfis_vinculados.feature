# language: pt
Funcionalidade: Validar perfis vinculados
  Contexto:
    Dado que estou autenticado como CODAE para consultar perfis vinculados
  Cenario: Consultar lista de perfis vinculados
    Quando consulto a lista de perfis vinculados
    Entao a lista de perfis vinculados retorna dados validos
  Esquema do Cenario: Consultar perfis vinculados por perfil master
    Quando consulto perfis vinculados pelo perfil master <perfil>
    Entao a consulta por perfil master retorna status <status>
    E quando encontrada apresenta os perfis vinculados
    Exemplos:
      | perfil | status |
      | 7      | 200    |
      | 0      | 404    |
  Cenario: Consultar perfis subordinados por perfil master existente
    Quando consulto os subordinados de um perfil master existente
    Entao a API retorna o perfil subordinado esperado
  Cenario: Consultar perfis subordinados por perfil master inexistente
    Quando consulto subordinados pelo perfil master "ABC"
    Entao a consulta de subordinados retorna status 400 e detalhe
