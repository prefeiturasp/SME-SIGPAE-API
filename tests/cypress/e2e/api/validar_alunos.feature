Feature: Validar alunos da aplicacao SIGPAE

  Background:
    Given que estou autenticado como diretor para consultar alunos

  Scenario: Consultar todos os alunos com sucesso
    When consulto todos os alunos
    Then deve retornar uma lista paginada de alunos

  Scenario: Consultar aluno por codigo EOL com sucesso
    When consulto o aluno de codigo EOL 6577549
    Then deve retornar os dados do aluno com status 200

  Scenario: Consultar aluno com codigo EOL inexistente
    When consulto o aluno de codigo EOL 0
    Then a consulta do aluno deve retornar status 404

  Scenario Outline: Verificar se aluno pertence a escola
    When verifico se o aluno 6577549 pertence a escola "<escola>"
    Then o resultado de pertencimento deve ser "<resultado>"

    Examples:
      | escola | resultado |
      | 019769 | true      |
      | 017981 | false     |

  Scenario: Consultar detalhes de dieta de aluno nao matriculado
    When consulto detalhes de dieta com escola 200018 e nome "Teste"
    Then a consulta de detalhes de dieta deve retornar status 200

  Scenario: Consultar detalhes de dieta sem codigo da escola
    When consulto detalhes de dieta sem parametros
    Then deve informar que codigo_eol_escola e obrigatorio

  Scenario: Consultar detalhes de dieta sem nome do aluno
    When consulto detalhes de dieta apenas com escola 200018
    Then deve informar que nome_aluno e obrigatorio

  Scenario: Consultar quantidade por periodo sem codigo da escola
    When consulto quantidade de alunos por periodo sem codigo da escola
    Then deve informar que codigo_eol_escola e obrigatorio

  Scenario: Consultar quantidade por periodo para escola que nao e CEMEI
    When consulto quantidade de alunos por periodo da escola "000566"
    Then deve informar que a escola nao e CEMEI

  Scenario: Consultar quantidade de alunos por periodo CEMEI com sucesso
    When consulto quantidade de alunos por periodo da escola "019432"
    Then deve retornar quantidades CEI e EMEI por periodo

  Scenario: Consultar quantidade CEMEI por CEI e EMEI com sucesso
    When consulto quantidade CEMEI por CEI e EMEI da escola "019432"
    Then deve retornar quantidades CEMEI para CEI e EMEI

  Scenario: Consultar quantidade CEMEI para escola que nao e CEMEI
    When consulto quantidade CEMEI por CEI e EMEI da escola "000566"
    Then deve informar que a escola nao e CEMEI

  Scenario: Consultar quantidade CEMEI sem codigo da escola
    When consulto quantidade CEMEI por CEI e EMEI sem codigo da escola
    Then deve informar que codigo_eol_escola e obrigatorio
