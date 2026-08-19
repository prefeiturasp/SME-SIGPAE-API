# language: pt
Funcionalidade: Validar configuracao de email
  Cenario: Consultar configuracoes de email com sucesso
    Quando consulto as configuracoes de email autenticado
    Entao a lista de configuracoes de email retorna dados validos
  Cenario: Consultar configuracoes de email sem autenticacao
    Quando consulto as configuracoes de email sem autenticacao
    Entao a consulta de email retorna status 401

  # O POST de sucesso permanece desabilitado porque altera a configuracao SMTP do QA.

  Cenario: Cadastrar configuracao de email com dados invalidos
    Quando cadastro uma configuracao de email invalida
    Entao o cadastro de email retorna status 400
  Cenario: Cadastrar configuracao de email sem autenticacao
    Quando cadastro uma configuracao de email sem autenticacao
    Entao o cadastro de email retorna status 401
