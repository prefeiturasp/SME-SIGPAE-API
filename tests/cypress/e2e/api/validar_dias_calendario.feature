# language: pt
Funcionalidade: Validar dias do calendario

  Cenario: Consultar dias de uma escola com sucesso
    Dado que estou autenticado para consultar dias do calendario
    Quando consulto dias do calendario de uma escola existente
    Entao a operacao de dias do calendario retorna 200
    E a listagem de dias do calendario possui estrutura valida

  Cenario: Retornar lista vazia para escola inexistente
    Dado que estou autenticado para consultar dias do calendario
    Quando consulto dias do calendario de uma escola inexistente
    Entao a operacao de dias do calendario retorna 200
    E a listagem de dias do calendario esta vazia

  Esquema do Cenario: Rejeitar dia inexistente
    Dado que estou autenticado para consultar dias do calendario
    Quando executo "<metodo>" em dia do calendario inexistente
    Entao a operacao de dias do calendario retorna 404
    Exemplos:
      | metodo |
      | GET    |
      | PUT    |
      | PATCH  |
      | DELETE |

  Esquema do Cenario: Rejeitar acesso sem autenticacao
    Quando executo "<metodo>" em dias do calendario na rota "<rota>" sem autenticacao
    Entao a operacao de dias do calendario retorna 401
    Exemplos:
      | metodo | rota     |
      | GET    | listagem |
      | POST   | listagem |
      | GET    | detalhe  |
      | PUT    | detalhe  |
      | PATCH  | detalhe  |
      | DELETE | detalhe  |

  Cenario: Rejeitar cadastro sem campos obrigatorios
    Dado que estou autenticado para consultar dias do calendario
    Quando cadastro dia do calendario sem campos obrigatorios
    Entao a operacao de dias do calendario retorna 400
    E dias do calendario informa os campos obrigatorios
