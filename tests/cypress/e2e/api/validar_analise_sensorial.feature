Feature: Validar analise sensorial da aplicacao SIGPAE

  Background:
    Given que estou autenticado para consultar analises sensoriais

  Scenario: Consultar analises sensoriais com sucesso
    When consulto todas as analises sensoriais
    Then deve retornar a lista paginada de analises sensoriais

  Scenario: Consultar analises sensoriais com limite
    When consulto analises sensoriais com filtro "?limit=1"
    Then deve retornar no maximo 1 analise sensorial paginada

  Scenario: Consultar analises sensoriais com limite e offset
    When consulto analises sensoriais com filtro "?limit=1&offset=0"
    Then deve retornar no maximo 1 analise sensorial paginada
