# language: pt
Funcionalidade: Validar emails de terceirizadas por modulo

  Contexto:
    Dado que estou autenticado como CODAE para consultar emails de terceirizadas por modulo

  Cenario: Cadastrar email de terceirizada por modulo
    Quando cadastro um email de terceirizada por modulo
    Entao o email de terceirizada por modulo e cadastrado com sucesso

  Cenario: Atualizar email de terceirizada por modulo
    Quando atualizo um email de terceirizada por modulo
    Entao o email de terceirizada por modulo e atualizado com sucesso
