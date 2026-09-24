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

  @complemento_dashboard
  Cenario: Consultar detalhe de produto pelo UUID com sucesso
    Quando consulto um produto existente pelo UUID no dashboard
    Entao o detalhe do dashboard corresponde ao produto consultado

  @complemento_dashboard
  Esquema do Cenario: Rejeitar UUID inexistente no dashboard
    Quando executo "<metodo>" no dashboard com UUID inexistente
    Entao a operacao do dashboard retorna 404
    Exemplos:
      | metodo |
      | GET    |
      | PUT    |
      | PATCH  |
      | DELETE |

  @complemento_dashboard
  Esquema do Cenario: Rejeitar operacao no dashboard sem autenticacao
    Quando executo "<metodo>" no dashboard sem autenticacao
    Entao a operacao do dashboard retorna 401
    Exemplos:
      | metodo |
      | POST   |
      | GET    |
      | PUT    |
      | PATCH  |
      | DELETE |

  @complemento_dashboard
  Cenario: Rejeitar cadastro no dashboard com status invalido
    Quando cadastro no dashboard um status invalido
    Entao a operacao do dashboard retorna 400
    E o dashboard informa erro no campo status
