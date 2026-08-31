# language: pt
Funcionalidade: Validar atualizacao de senha do cadastro

  Cenario: Atualizar senha sem dados obrigatorios
    Quando solicito a atualizacao de senha sem os dados obrigatorios
    Entao a atualizacao de senha deve retornar status 400 e um corpo de resposta

  Cenario: Atualizar senha com usuario e token invalidos
    Quando solicito a atualizacao de senha com usuario e token invalidos
    Entao a atualizacao de senha deve retornar erro de validacao ou recurso nao encontrado
