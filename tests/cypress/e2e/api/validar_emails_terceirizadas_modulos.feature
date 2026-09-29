# language: pt
@emails_modulos
Funcionalidade: Validar emails de terceirizadas por modulo

  Contexto:
    Dado que estou autenticado como CODAE para consultar emails de terceirizadas por modulo

  Cenario: Cadastrar email de terceirizada por modulo
    Quando cadastro um email de terceirizada por modulo
    Entao o email de terceirizada por modulo e cadastrado com sucesso

  Cenario: Atualizar email de terceirizada por modulo
    Quando atualizo um email de terceirizada por modulo
    Entao o email de terceirizada por modulo e atualizado com sucesso

  Cenario: Excluir email de terceirizada por modulo
    Quando cadastro um email de terceirizada por modulo
    Entao o email de terceirizada por modulo e cadastrado com sucesso
    Quando excluo o email de terceirizada por modulo criado
    Entao a operacao de emails de terceirizadas por modulo retorna 204

  Cenario: Rejeitar cadastro sem campos obrigatorios
    Quando envio cadastro de email de terceirizada por modulo sem campos obrigatorios
    Entao a operacao de emails de terceirizadas por modulo retorna 400
    E emails de terceirizadas por modulo informa erro no campo "email"
    E emails de terceirizadas por modulo informa erro no campo "terceirizada"
    E emails de terceirizadas por modulo informa erro no campo "modulo"

  Cenario: Rejeitar cadastro com email invalido
    Quando cadastro um email de terceirizada por modulo
    Entao o email de terceirizada por modulo e cadastrado com sucesso
    Quando cadastro email de terceirizada por modulo com email invalido
    Entao a operacao de emails de terceirizadas por modulo retorna 400
    E emails de terceirizadas por modulo informa erro no campo "email"

  Cenario: Rejeitar atualizacao com email invalido
    Quando cadastro um email de terceirizada por modulo
    Entao o email de terceirizada por modulo e cadastrado com sucesso
    Quando atualizo o email de terceirizada por modulo com email invalido
    Entao a operacao de emails de terceirizadas por modulo retorna 400
    E emails de terceirizadas por modulo informa erro no campo "email"

  Cenario: Rejeitar cadastro duplicado
    Quando cadastro um email de terceirizada por modulo
    Entao o email de terceirizada por modulo e cadastrado com sucesso
    Quando cadastro novamente o mesmo email de terceirizada por modulo
    Entao a operacao de emails de terceirizadas por modulo retorna 400
    E emails de terceirizadas por modulo informa erro no campo "non_field_errors"

  Esquema do Cenario: Rejeitar UUID inexistente
    Quando executo "<metodo>" em emails de terceirizadas por modulo na rota "detalhe" com acesso "autenticado"
    Entao a operacao de emails de terceirizadas por modulo retorna 404
    Exemplos:
      | metodo |
      | PATCH  |
      | DELETE |

  Esquema do Cenario: Rejeitar acesso sem autenticacao
    Quando executo "<metodo>" em emails de terceirizadas por modulo na rota "<rota>" com acesso "anonimo"
    Entao a operacao de emails de terceirizadas por modulo retorna 401
    Exemplos:
      | metodo | rota     |
      | POST   | listagem |
      | PATCH  | detalhe  |
      | DELETE | detalhe  |

  Esquema do Cenario: Rejeitar metodos nao permitidos
    Quando executo "<metodo>" em emails de terceirizadas por modulo na rota "<rota>" com acesso "autenticado"
    Entao a operacao de emails de terceirizadas por modulo retorna 405
    Exemplos:
      | metodo | rota     |
      | GET    | listagem |
      | GET    | detalhe  |
      | PUT    | detalhe  |
