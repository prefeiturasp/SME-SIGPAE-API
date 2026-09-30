# language: pt
@empresas_nao_terceirizadas
Funcionalidade: Validar empresas nao terceirizadas

  Contexto:
    Dado que estou autenticado como CODAE para empresas nao terceirizadas

  Cenario: Cadastrar empresa nao terceirizada
    Quando cadastro uma empresa nao terceirizada
    Entao a operacao de empresas nao terceirizadas retorna 201
    E a empresa nao terceirizada corresponde aos dados enviados

  Esquema do Cenario: Atualizar empresa nao terceirizada
    Dado que cadastrei uma empresa nao terceirizada para o cenario
    Quando atualizo a empresa nao terceirizada usando "<metodo>"
    Entao a operacao de empresas nao terceirizadas retorna 200
    E a empresa nao terceirizada corresponde aos dados enviados
    Exemplos:
      | metodo |
      | PUT    |
      | PATCH  |

  Cenario: Excluir empresa nao terceirizada
    Dado que cadastrei uma empresa nao terceirizada para o cenario
    Quando excluo a empresa nao terceirizada criada
    Entao a operacao de empresas nao terceirizadas retorna 204
    E a empresa nao terceirizada nao pode ser excluida novamente

  Esquema do Cenario: Rejeitar acesso sem autenticacao
    Quando executo "<metodo>" em empresas nao terceirizadas na rota "<rota>" com acesso "anonimo"
    Entao a operacao de empresas nao terceirizadas retorna 401
    Exemplos:
      | metodo | rota     |
      | POST   | cadastro |
      | PUT    | detalhe  |
      | PATCH  | detalhe  |
      | DELETE | detalhe  |

  Esquema do Cenario: Rejeitar UUID inexistente
    Quando executo "<metodo>" em empresas nao terceirizadas na rota "detalhe" com acesso "autenticado"
    Entao a operacao de empresas nao terceirizadas retorna 404
    Exemplos:
      | metodo |
      | PUT    |
      | PATCH  |
      | DELETE |

  Esquema do Cenario: Rejeitar consulta GET nao disponivel
    Quando executo "GET" em empresas nao terceirizadas na rota "<rota>" com acesso "autenticado"
    Entao a operacao de empresas nao terceirizadas retorna 405
    Exemplos:
      | rota     |
      | cadastro |
      | detalhe  |

  Cenario: Rejeitar cadastro sem CNPJ
    Quando cadastro uma empresa nao terceirizada sem CNPJ
    Entao a operacao de empresas nao terceirizadas retorna 400
    E empresas nao terceirizadas informa erro no campo "cnpj"

  Cenario: Rejeitar cadastro com CNPJ curto
    Quando cadastro uma empresa nao terceirizada com CNPJ curto
    Entao a operacao de empresas nao terceirizadas retorna 400
    E empresas nao terceirizadas informa erro no campo "cnpj"

  Cenario: Rejeitar cadastro com CNPJ longo
    Quando cadastro uma empresa nao terceirizada com CNPJ longo
    Entao a operacao de empresas nao terceirizadas retorna 400
    E empresas nao terceirizadas informa erro no campo "cnpj"

  Esquema do Cenario: Rejeitar atualizacao com nome acima do limite
    Dado que cadastrei uma empresa nao terceirizada para o cenario
    Quando atualizo a empresa nao terceirizada usando "<metodo>" com nome de 161 caracteres
    Entao a operacao de empresas nao terceirizadas retorna 400
    E empresas nao terceirizadas informa erro no campo "nome_fantasia"
    Exemplos:
      | metodo |
      | PUT    |
      | PATCH  |
