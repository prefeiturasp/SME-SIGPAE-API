Feature: Login

  Scenario Outline: Validar login com diferentes perfis
    Given que acesso o sistema
    When informo os dados do usuario "<perfil>" no dispositivo "<device>"
    And clico no botao acessar
    Then sistema apresenta "<mensagem>"

    Examples:
      | perfil                            | device | mensagem                   |
      | COORDENADOR_LOGISTICA             | web    | sucesso                    |
      | COORDENADOR_CODAE_DILOG_LOGISTICA | web    | sucesso                    |
      | COORDENADOR_SUPERVISAO_NUTRICAO   | web    | sucesso                    |
      | DILOG_CRONOGRAMA                  | web    | sucesso                    |
      | DILOG_QUALIDADE                   | web    | sucesso                    |
      | ABASTECIMENTO                     | web    | sucesso                    |
      | DIRETOR_UE                        | web    | sucesso                    |
      | CODAE                             | web    | sucesso                    |
      | GPCODAE                           | web    | sucesso                    |
      | DRE                               | web    | sucesso                    |
      | USUARIO_INVALIDO                  | web    | Usuário ou senha inválidos |
      | SENHA_INVALIDA                    | web    | Usuário ou senha inválidos |
      | USUARIO_INEXISTENTE               | web    | Usuário ou senha inválidos |
      | USUARIO_EM_BRANCO                 | web    | Campo obrigatório          |
      | SENHA_EM_BRANCO                   | web    | Campo obrigatório          |
