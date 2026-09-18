Feature: Validar cadastro de usuarios com CoreSSO

  Scenario Outline: Rejeitar operacoes CoreSSO sem autenticacao
    When acesso "<operacao>" do cadastro CoreSSO sem autenticacao
    Then o cadastro CoreSSO retorna status 401

    Examples:
      | operacao          |
      | cadastrar         |
      | alterar_email     |

  Scenario: Rejeitar cadastro CoreSSO sem campos obrigatorios
    Given que estou autenticado como escola para cadastro CoreSSO
    When cadastro usuario CoreSSO sem dados
    Then o cadastro CoreSSO informa os campos obrigatorios

  Scenario Outline: Rejeitar campos invalidos no cadastro CoreSSO
    Given que estou autenticado como escola para cadastro CoreSSO
    When cadastro usuario CoreSSO com "<campo>" invalido
    Then o cadastro CoreSSO retorna erro no campo "<campo>"

    Examples:
      | campo      |
      | email      |
      | subdivisao |

  Scenario Outline: Impedir escola de alterar dados administrativos CoreSSO
    Given que estou autenticado como escola para cadastro CoreSSO
    When acesso "<operacao>" do cadastro CoreSSO como escola
    Then o cadastro CoreSSO retorna status 403

    Examples:
      | operacao        |
      | alterar_email   |
      | alterar_vinculo |

  Scenario: Rejeitar finalizacao de vinculo de usuario inexistente
    Given que estou autenticado como escola para cadastro CoreSSO
    When acesso "finalizar_vinculo" do cadastro CoreSSO como escola
    Then o cadastro CoreSSO informa usuario inexistente
