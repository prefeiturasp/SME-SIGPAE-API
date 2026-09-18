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

  Scenario: Filtrar alunos pelo codigo EOL com sucesso
    When filtro alunos por um codigo EOL existente
    Then a listagem deve conter somente o aluno solicitado

  Scenario: Filtrar alunos por codigo EOL inexistente
    When filtro alunos pelo codigo EOL inexistente
    Then a listagem de alunos deve estar vazia

  Scenario: Paginar alunos com limite e deslocamento
    When consulto duas paginas consecutivas de alunos
    Then as paginas devem respeitar o limite sem repetir o primeiro aluno

  Scenario: Verificar pertencimento de aluno inexistente
    When verifico se o aluno 0 pertence a escola "019769"
    Then o resultado de pertencimento deve ser "false"

  Scenario Outline: Rejeitar operacao de foto para aluno inexistente
    When executo "<acao>" para foto de aluno inexistente
    Then a operacao de foto do aluno deve retornar 404

    Examples:
      | acao           |
      | ver-foto       |
      | atualizar-foto |
      | deletar-foto   |

  Scenario Outline: Rejeitar operacao de foto sem autenticacao
    When executo "<acao>" para foto de aluno sem autenticacao
    Then a operacao de foto do aluno deve retornar 401

    Examples:
      | acao           |
      | ver-foto       |
      | atualizar-foto |
      | deletar-foto   |
