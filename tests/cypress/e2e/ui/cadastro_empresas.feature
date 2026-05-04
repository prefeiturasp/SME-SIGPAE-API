Feature: Cadastro de Empresas
  Como usuario Codae ou Cronograma
  Preciso realizar o cadastro de empresas
  Para que fiquem disponiveis no sistema

  Background:
    Given que acesso o sistema

  Scenario: Cadastro de empresa com sucesso
    When acesso o menu Cadastros > Empresas
    And preencho os campos obrigatorios de cadastro da empresa
    And clico no botao Salvar
    And confirmo a acao no modal de confirmacao
    Then devo visualizar a mensagem "Empresa cadastrada com sucesso"
    #teste
    