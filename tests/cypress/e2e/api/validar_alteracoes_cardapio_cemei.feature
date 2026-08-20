Feature: Validar alteracoes de cardapio CEMEI da aplicacao SIGPAE

  Scenario: Consultar alteracoes de cardapio CEMEI com sucesso
    When consulto as alteracoes de cardapio CEMEI
    Then deve retornar a listagem paginada de alteracoes CEMEI
