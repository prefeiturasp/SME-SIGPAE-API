Feature: Validar API Version da aplicacao SIGPAE

  Scenario: Consultar a versao da API com sucesso
    When consulto a versao da API
    Then a API deve retornar status 200
    And deve informar a versao atual da API
