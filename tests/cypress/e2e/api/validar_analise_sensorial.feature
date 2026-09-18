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

  Scenario: Consultar analise sensorial existente por UUID
    When consulto uma analise sensorial existente por UUID
    Then deve retornar a analise sensorial solicitada

  @ciclo_analise_sensorial
  Scenario: Cadastrar consultar atualizar e excluir analise sensorial de teste
    When cadastro uma analise sensorial de teste
    Then a analise sensorial de teste deve ser criada e consultavel
    When tento atualizar a analise sensorial de teste com data invalida usando "PUT"
    Then a analise sensorial deve retornar erro 400 no campo "data"
    When tento atualizar a analise sensorial de teste com data invalida usando "PATCH"
    Then a analise sensorial deve retornar erro 400 no campo "data"
    When atualizo a analise sensorial de teste usando "PUT"
    Then a alteracao da analise sensorial deve estar persistida
    When atualizo a analise sensorial de teste usando "PATCH"
    Then a alteracao da analise sensorial deve estar persistida
    When excluo a analise sensorial de teste
    Then a analise sensorial excluida nao deve ser encontrada

  Scenario Outline: Rejeitar cadastro de analise sensorial invalida
    When cadastro analise sensorial invalida no campo "<campo>"
    Then a analise sensorial deve retornar erro 400 no campo "<campo>"

    Examples:
      | campo                |
      | homologacao_produto  |
      | data                 |
      | hora                 |
      | responsavel_produto  |
      | registro_funcional   |

  Scenario Outline: Rejeitar UUID inexistente de analise sensorial
    When executo "<metodo>" para analise sensorial inexistente
    Then a operacao de analise sensorial deve retornar 404

    Examples:
      | metodo |
      | GET    |
      | PUT    |
      | PATCH  |
      | DELETE |

  Scenario Outline: Rejeitar operacoes de analise sensorial sem autenticacao
    When executo "<metodo>" no caminho sensorial "<caminho>" sem autenticacao
    Then a operacao de analise sensorial deve retornar 401

    Examples:
      | metodo | caminho                                        |
      | GET    |                                                |
      | POST   |                                                |
      | GET    | 00000000-0000-0000-0000-000000000000/          |
      | PUT    | 00000000-0000-0000-0000-000000000000/          |
      | PATCH  | 00000000-0000-0000-0000-000000000000/          |
      | DELETE | 00000000-0000-0000-0000-000000000000/          |
      | POST   | terceirizada-responde-analise-sensorial/          |

  Scenario: Bloquear resposta de terceirizada pelo perfil CODAE
    When respondo analise sensorial com perfil CODAE
    Then a operacao de analise sensorial deve retornar 403
