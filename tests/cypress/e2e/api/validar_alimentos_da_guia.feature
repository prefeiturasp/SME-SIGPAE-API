Feature: Validar alimentos da guia da aplicacao SIGPAE

  Background:
    Given que estou autenticado para gerenciar alimentos da guia

  Scenario: Consultar todos os alimentos da guia com sucesso
    When consulto todos os alimentos da guia
    Then a consulta de alimentos da guia deve retornar uma lista paginada

  Scenario: Consultar alimentos da guia com paginacao
    When consulto alimentos da guia com limit 4 e offset 5
    Then a consulta de alimentos da guia deve retornar uma lista paginada

  Scenario: Consultar alimentos da guia com caminho invalido
    When consulto alimentos da guia pelo caminho invalido "dgaugsusausay"
    Then a API de alimentos da guia deve redirecionar para o caminho com barra final

  Scenario: Impedir consulta por usuario sem permissao
    When um diretor de UE consulta todos os alimentos da guia
    Then a consulta de alimentos da guia deve retornar permissao negada

  Scenario: Consultar alimento da guia por UUID com sucesso
    When consulto o alimento da guia de UUID "b9a97cc1-f4dc-469d-be34-f63eb96bdbf4"
    Then deve retornar os dados do alimento da guia com status 200

  Scenario: Consultar alimento da guia sem barra final
    When consulto alimentos da guia pelo caminho invalido "b9a97cc1-f4dc-469d-be34-f63eb96bdbf4"
    Then a API de alimentos da guia deve redirecionar para o caminho com barra final

  Scenario: Consultar alimento da guia com UUID invalido
    When consulto alimentos da guia pelo caminho invalido "b9adscc1-fddc-46sd-b534-f63ebdsbdbf4"
    Then a API de alimentos da guia deve redirecionar para o caminho com barra final

  Scenario: Cadastrar alimento da guia com sucesso
    When cadastro um alimento da guia com dados validos
    Then o alimento da guia deve ser cadastrado com sucesso

  Scenario Outline: Rejeitar cadastro de alimento da guia com dados invalidos
    When tento cadastrar um alimento da guia com "<caso>" invalido
    Then o cadastro deve ser rejeitado por "<caso>" invalido

    Examples:
      | caso                        |
      | codigo_suprimento_extenso  |
      | codigo_papa_extenso        |
      | nome_alimento_extenso      |
      | guia_texto                 |
      | guia_inexistente           |

  Scenario: Excluir alimento da guia com sucesso
    When cadastro e excluo um alimento da guia
    Then a exclusao do alimento da guia deve retornar status 204

  Scenario: Excluir alimento da guia sem informar UUID
    When excluo um alimento da guia sem informar UUID
    Then a exclusao do alimento da guia deve retornar status 405

  Scenario: Excluir alimento da guia com UUID inexistente
    When excluo o alimento da guia de UUID inexistente
    Then a exclusao do alimento da guia deve retornar status 404

  Scenario: Alterar alimento da guia via PUT com sucesso
    Given que existe um alimento da guia para alteracao
    When altero o alimento da guia via PUT com dados validos
    Then o alimento da guia deve ser alterado via PUT com sucesso

  Scenario Outline: Rejeitar alteracao via PUT com dados invalidos
    Given que existe um alimento da guia para alteracao
    When tento alterar o alimento da guia via PUT com "<caso>" invalido
    Then a alteracao deve ser rejeitada por "<caso>" invalido

    Examples:
      | caso                        |
      | codigo_suprimento_extenso  |
      | codigo_papa_extenso        |
      | nome_alimento_extenso      |
      | guia_texto                 |
      | guia_inexistente           |

  Scenario: Alterar alimento da guia via PATCH com sucesso
    Given que existe um alimento da guia para alteracao
    When altero o alimento da guia via PATCH com dados validos
    Then o alimento da guia deve ser alterado via PATCH com sucesso

  Scenario Outline: Rejeitar alteracao via PATCH com dados invalidos
    Given que existe um alimento da guia para alteracao
    When tento alterar o alimento da guia via PATCH com "<caso>" invalido
    Then a alteracao deve ser rejeitada por "<caso>" invalido

    Examples:
      | caso                        |
      | codigo_suprimento_extenso  |
      | codigo_papa_extenso        |
      | nome_alimento_extenso      |
      | guia_texto                 |
      | guia_inexistente           |

  Scenario: Consultar lista de nomes dos alimentos da guia
    When consulto a lista de nomes dos alimentos da guia
    Then deve retornar os nomes e UUIDs dos alimentos da guia
