# language: pt
Funcionalidade: Validar rotas de login da aplicacao SIGPAE

  Cenario: Validar login realizado com sucesso
    Quando realizo o login da API com o usuario coordenador de logistica
    Entao o login da API deve retornar status 200 e token de acesso
