Feature: Validar API Token Auth da aplicacao SIGPAE

  Scenario Outline: Autenticar perfil com sucesso na API Token Auth
    When solicito um token para o perfil "<perfil>"
    Then deve retornar os tokens de acesso e renovacao

    Examples:
      | perfil                              |
      | coordenador_logistica               |
      | coordenador_codae_dilog_logistica   |
      | coordenador_supervisao_nutricao     |
      | dilog_cronograma                    |
      | dilog_qualidade                     |
      | abastecimento                       |
      | diretor_ue                          |
      | codae                               |
      | gpcodae                             |
      | dre                                 |
      | classificacoes_dieta                |

  Scenario: Rejeitar credenciais invalidas na API Token Auth
    When solicito um token com credenciais invalidas
    Then a API Token Auth deve retornar status 401
