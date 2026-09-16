Feature: Validar alergias e intolerancias da aplicacao SIGPAE

  Background:
    Given que estou autenticado para consultar alergias e intolerancias

  Scenario: Consultar todas as alergias e intolerancias com sucesso
    When consulto todas as alergias e intolerancias
    Then a consulta de alergias e intolerancias deve retornar status 200
    And deve retornar a alergia ARGININEMIA com id 127 na lista

  Scenario: Consultar uma alergia ou intolerancia por id com sucesso
    When consulto a alergia ou intolerancia de id 127
    Then a consulta de alergias e intolerancias deve retornar status 200
    And deve retornar a alergia ARGININEMIA com id 127

  Scenario: Consultar id sem barra final
    When consulto alergias e intolerancias pelo caminho "1"
    Then a API deve redirecionar a consulta para o caminho com barra final

  Scenario: Consultar id em texto sem barra final
    When consulto alergias e intolerancias pelo caminho "ace"
    Then a API deve redirecionar a consulta para o caminho com barra final
