# language: pt
Funcionalidade: Validar confirmacao de email

  Cenario: Rejeitar confirmacao de email de usuario inexistente
    Quando solicito confirmacao de email para usuario inexistente
    Entao a confirmacao de email retorna erro de usuario inexistente
