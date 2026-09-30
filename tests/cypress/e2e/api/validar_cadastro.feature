# language: pt
Funcionalidade: Validar cadastro da aplicacao SIGPAE

  Cenario: Atualizar senha sem dados obrigatorios
    Quando solicito a atualizacao de senha sem os dados obrigatorios
    Entao a atualizacao de senha deve retornar status 400 e um corpo de resposta

  Cenario: Atualizar senha com usuario e token invalidos
    Quando solicito a atualizacao de senha com usuario e token invalidos
    Entao a atualizacao de senha deve retornar erro de validacao ou recurso nao encontrado

  Esquema do Cenario: Recuperar senha com identificador inexistente
    Quando solicito recuperacao de senha para o identificador "<identificador>"
    Entao o cadastro informa que nao existe usuario com esse CPF ou RF

    Exemplos:
      | identificador |
      | 00000000000   |
      | 0000000       |
