# language: pt
Funcionalidade: Validar downloads

  Cenario: Consultar downloads com sucesso
    Quando consulto os downloads com um usuario CODAE
    Entao a operacao de downloads retorna 200
    E a consulta de downloads retorna uma lista paginada valida

  Cenario: Consultar quantidade de downloads nao vistos
    Quando executo "GET" em downloads na rota "quantidade-nao-vistos" com acesso "autenticado"
    Entao a operacao de downloads retorna 200
    E downloads retorna uma quantidade de nao vistos valida

  Cenario: Consultar downloads com UUID inexistente
    Quando consulto downloads filtrando um UUID inexistente
    Entao a operacao de downloads retorna 200
    E a consulta de downloads retorna uma lista vazia

  Esquema do Cenario: Filtrar downloads por visualizacao
    Quando consulto downloads com visto "<visto>"
    Entao a operacao de downloads retorna 200
    E a consulta de downloads retorna uma lista paginada valida
    E os downloads correspondem ao filtro visto "<visto>"
    Exemplos:
      | visto |
      | true  |
      | false |

  Esquema do Cenario: Rejeitar UUID de download inexistente
    Quando executo "<metodo>" em downloads na rota "detalhe" com acesso "autenticado"
    Entao a operacao de downloads retorna 404
    Exemplos:
      | metodo |
      | GET    |
      | PUT    |
      | PATCH  |
      | DELETE |

  Esquema do Cenario: Rejeitar downloads sem autenticacao
    Quando executo "<metodo>" em downloads na rota "<rota>" com acesso "anonimo"
    Entao a operacao de downloads retorna 401
    Exemplos:
      | metodo | rota                 |
      | GET    | listagem             |
      | POST   | listagem             |
      | GET    | detalhe              |
      | PUT    | detalhe              |
      | PATCH  | detalhe              |
      | DELETE | detalhe              |
      | PUT    | marcar-visto         |
      | GET    | quantidade-nao-vistos |

  Cenario: Rejeitar cadastro de download sem status
    Quando executo "POST" em downloads na rota "listagem" com acesso "autenticado"
    Entao a operacao de downloads retorna 400
    E o cadastro de downloads informa o status obrigatorio

  Cenario: Rejeitar marcar visto sem campos obrigatorios
    Quando executo "PUT" em downloads na rota "marcar-visto" com acesso "autenticado"
    Entao a operacao de downloads retorna 400
    E downloads retorna uma mensagem de erro

  Cenario: Rejeitar marcar visto para UUID inexistente
    Quando marco como visto um download inexistente
    Entao a operacao de downloads retorna 400
    E downloads retorna uma mensagem de erro
