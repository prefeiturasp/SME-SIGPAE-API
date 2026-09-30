Feature: Validar alteracoes de cardapio CEMEI da aplicacao SIGPAE

  Scenario: Consultar alteracoes de cardapio CEMEI com sucesso
    When consulto as alteracoes de cardapio CEMEI
    Then deve retornar a listagem paginada de alteracoes CEMEI

  Scenario Outline: Consultar solicitacoes CEMEI por perfil
    When consulto "<operacao>" de cardapio CEMEI como "<perfil>"
    Then a consulta CEMEI retorna uma lista de solicitacoes

    Examples:
      | operacao      | perfil |
      | pedidos_codae | codae  |
      | pedidos_dre   | dre    |

  Scenario: Consultar detalhe CEMEI por UUID
    When consulto "detalhar" de uma solicitacao CEMEI existente
    Then o detalhe CEMEI corresponde ao UUID solicitado

  Scenario: Emitir relatorio CEMEI
    When consulto "relatorio" de uma solicitacao CEMEI existente
    Then o relatorio CEMEI e um PDF valido

  Scenario: Rejeitar cadastro CEMEI sem campos obrigatorios
    When cadastro alteracao CEMEI sem campos obrigatorios
    Then o cadastro CEMEI informa os campos obrigatorios

  Scenario Outline: Rejeitar UUID inexistente CEMEI
    When acesso "<operacao>" CEMEI inexistente como "<perfil>"
    Then a operacao CEMEI retorna status 404

    Examples:
      | operacao        | perfil |
      | detalhar        | codae  |
      | atualizar       | codae  |
      | parcial         | escola |
      | excluir         | escola |
      | relatorio       | escola |
      | iniciar         | escola |
      | cancelar_escola | escola |
      | autorizar       | codae  |
      | cancelar_codae  | codae  |
      | questionar      | codae  |
      | validar_dre     | dre    |
      | nao_validar_dre | dre    |
      | conferir        | escola |

  Scenario Outline: Bloquear escola em operacoes CEMEI de outros perfis
    When acesso "<operacao>" CEMEI inexistente como "escola"
    Then a operacao CEMEI retorna status 403

    Examples:
      | operacao        |
      | autorizar       |
      | cancelar_codae  |
      | questionar      |
      | validar_dre     |
      | nao_validar_dre |
      | responder       |
      | tomar_ciencia   |
      | pedidos_codae   |
      | pedidos_dre     |

  Scenario Outline: Exigir autenticacao nas operacoes CEMEI
    When acesso "<operacao>" CEMEI sem autenticacao
    Then a operacao CEMEI retorna status 401

    Examples:
      | operacao        |
      | listar          |
      | cadastrar       |
      | detalhar        |
      | atualizar       |
      | parcial         |
      | excluir         |
      | autorizar       |
      | cancelar_codae  |
      | questionar      |
      | nao_validar_dre |
      | validar_dre     |
      | cancelar_escola |
      | iniciar         |
      | conferir        |
      | relatorio       |
      | responder       |
      | tomar_ciencia   |
      | minhas          |
      | pedidos_codae   |
      | pedidos_dre     |
