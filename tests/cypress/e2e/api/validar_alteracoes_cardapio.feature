Feature: Validar alteracoes de cardapio da aplicacao SIGPAE

  Background:
    Given que estou autenticado como diretor para alteracoes de cardapio

  Scenario: Consultar alteracoes de cardapio com sucesso
    When consulto todas as alteracoes de cardapio como supervisao de nutricao
    Then deve retornar a listagem de alteracoes de cardapio permitida ao perfil

  Scenario: Cadastrar alteracao de cardapio com sucesso
    When cadastro uma alteracao de cardapio com dados validos
    Then a alteracao de cardapio deve ser cadastrada com sucesso

  Scenario Outline: Rejeitar cadastro de alteracao de cardapio com dados invalidos
    When tento cadastrar uma alteracao de cardapio com "<caso>" invalido
    Then o cadastro da alteracao deve ser rejeitado por "<caso>" invalido

    Examples:
      | caso                              |
      | motivo_branco                     |
      | motivo_uuid_invalido              |
      | escola_branco                     |
      | escola_uuid_invalido              |
      | periodo_escolar_branco            |
      | periodo_escolar_uuid_invalido     |
      | tipo_alimentacao_de_branco        |
      | tipo_alimentacao_de_uuid_invalido |
      | alteracao_cardapio_branco         |
      | alteracao_cardapio_uuid_invalido  |
      | tipo_alimentacao_para_branco      |
      | tipo_alimentacao_para_uuid_invalido |
      | quantidade_alunos_negativa        |
      | quantidade_alunos_branco          |
      | cancelado_branco                  |
      | cancelado_em_texto                |
      | cancelado_em_formato_invalido     |
      | cancelado_em_branco               |
      | cancelado_por_texto               |
      | cancelado_por_formato_invalido    |
      | fora_prazo_branco                 |
      | terceirizada_conferiu_branco      |
      | data_branco                       |
      | data_passado                      |
      | data_nao_letivo                   |
      | data_formato_invalido             |

  Scenario: Consultar alteracao por id com perfil sem permissao
    When consulto uma alteracao de cardapio como diretor
    Then a consulta deve retornar o registro ou permissao negada

  Scenario: Consultar alteracao de cardapio por id inexistente
    When consulto uma alteracao de cardapio por id inexistente
    Then a consulta da alteracao deve retornar status 404

  Scenario: Consultar alteracao de cardapio por id sem barra final
    When consulto uma alteracao de cardapio por id sem barra final
    Then a consulta da alteracao deve redirecionar para a barra final

  Scenario: Consultar alteracao de cardapio por id conforme permissao do perfil
    When consulto uma alteracao de cardapio existente
    Then deve retornar os dados completos da alteracao ou permissao negada

  Scenario: Excluir alteracao de cardapio com sucesso
    When cadastro e excluo uma alteracao de cardapio
    Then a operacao de exclusao deve ser aceita pelo perfil

  Scenario: Excluir alteracao de cardapio com id invalido
    When excluo uma alteracao de cardapio com id invalido
    Then a exclusao invalida deve retornar status 403 ou 404

  Scenario: Consultar relatorio de alteracao de cardapio com sucesso
    When consulto o relatorio de uma alteracao de cardapio existente
    Then deve retornar o relatorio PDF da alteracao

  Scenario: Consultar relatorio com id inexistente
    When consulto o relatorio de uma alteracao de cardapio inexistente
    Then a consulta do relatorio deve retornar status 404

  Scenario: Consultar minhas solicitacoes de alteracao de cardapio
    When consulto minhas solicitacoes de alteracao de cardapio
    Then deve retornar a listagem das minhas solicitacoes
