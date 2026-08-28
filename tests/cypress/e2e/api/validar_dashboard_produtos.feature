# language: pt
Funcionalidade: Validar dashboard de produtos
  Cenario: Consultar dashboard paginado com sucesso
    Quando consulto uma pagina do dashboard de produtos autenticado
    Entao o dashboard retorna status 200 e um produto valido
  Cenario: Consultar dashboard sem autenticacao
    Quando consulto o dashboard de produtos sem autenticacao
    Entao o dashboard retorna status 401
  Esquema do Cenario: Consultar filas do dashboard de produtos
    Quando consulto a fila "<fila>" do dashboard com o perfil "<perfil>"
    Entao a fila do dashboard retorna status permitido e dados validos
    Exemplos:
      | fila                                | perfil  |
      | aguardando_analise_reclamacao       | codae   |
      | nao_homologados                     | codae   |
      | questionamento_codae                | codae   |
      | suspensos                           | codae   |
      | homologados                         | codae   |
      | correcao_produtos                   | gpcodae |
      | aguardando_amostra_analise_sensorial| gpcodae |
      | pendente_homologacao                | gpcodae |
