# language: pt
Funcionalidade: Validar dias letivos

  Cenario: Validar GET de dias letivos com sucesso
    Quando consulto os dias letivos com um usuario CODAE
    Entao a consulta de dias letivos retorna status 200 e uma lista valida

  Cenario: Validar GET de dias letivos sem permissao
    Quando consulto os dias letivos com um usuario diretor de UE
    Entao a consulta de dias letivos retorna status 403 e mensagem de permissao

  Cenario: Consultar detalhe de dia letivo com sucesso
    Quando consulto o detalhe de um dia letivo existente
    Entao a operacao de dias letivos retorna 200
    E o detalhe de dias letivos corresponde ao UUID consultado

  Cenario: Consultar calendario com sucesso
    Quando executo "GET" em dias letivos na rota "calendario" com acesso "autenticado"
    Entao a operacao de dias letivos retorna 200
    E o calendario de dias letivos retorna uma lista

  Esquema do Cenario: Rejeitar UUID de dia letivo inexistente
    Quando executo "<metodo>" em dias letivos na rota "detalhe" com acesso "autenticado"
    Entao a operacao de dias letivos retorna 404
    Exemplos:
      | metodo |
      | GET    |
      | PUT    |
      | PATCH  |
      | DELETE |

  Esquema do Cenario: Rejeitar dias letivos sem autenticacao
    Quando executo "<metodo>" em dias letivos na rota "<rota>" com acesso "anonimo"
    Entao a operacao de dias letivos retorna 401
    Exemplos:
      | metodo | rota       |
      | GET    | listagem   |
      | POST   | listagem   |
      | GET    | detalhe    |
      | PUT    | detalhe    |
      | PATCH  | detalhe    |
      | DELETE | detalhe    |
      | GET    | calendario |

  Cenario: Rejeitar cadastro sem campos obrigatorios
    Quando executo "POST" em dias letivos na rota "listagem" com acesso "autenticado"
    Entao a operacao de dias letivos retorna 400
    E o cadastro de dias letivos informa campos obrigatorios

  Esquema do Cenario: Rejeitar consulta sem mes e ano
    Quando consulto "<rota>" de dias letivos sem filtros obrigatorios
    Entao a operacao de dias letivos retorna 400
    E dias letivos informa os filtros obrigatorios
    Exemplos:
      | rota       |
      | listagem   |
      | calendario |
