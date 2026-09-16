Feature: Validar alimentos da aplicacao SIGPAE

  Background:
    Given que estou autenticado para consultar alimentos

  Scenario Outline: Consultar alimentos por tipo com sucesso
    When consulto os alimentos do tipo "<tipo>"
    Then a consulta de alimentos deve retornar status 200
    And o primeiro alimento deve ser "<nome>"

    Examples:
      | tipo | nome    |
      | E    | ABACATE |
      | P    | Alga    |

  Scenario: Consultar todos os alimentos com sucesso
    When consulto todos os alimentos
    Then a consulta de alimentos deve retornar status 200
    And o primeiro alimento deve ser "ABACATE"

  Scenario: Consultar alimentos com tipo invalido
    When consulto os alimentos do tipo "batata"
    Then a consulta deve rejeitar o tipo de alimento invalido

  Scenario: Consultar alimento por id com sucesso
    When consulto o alimento de id 489
    Then deve retornar os dados completos do alimento ABACATE

  Scenario: Consultar alimento por id sem barra final
    When consulto o alimento pelo caminho "54"
    Then a API de alimentos deve redirecionar para o caminho com barra final
