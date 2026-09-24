# language: pt
Funcionalidade: Validar dias de suspensao de atividades

  Cenario: Listar suspensoes com sucesso
    Dado que estou autenticado para dias de suspensao
    Quando consulto os dias de suspensao cadastrados
    Entao a operacao de suspensao retorna 200
    E a listagem de suspensoes possui estrutura valida

  Cenario: Consultar detalhe com sucesso
    Dado que estou autenticado para dias de suspensao
    Quando consulto o detalhe de uma suspensao existente
    Entao a operacao de suspensao retorna 200
    E o detalhe corresponde a suspensao consultada

  Cenario: Consultar lista de dias por escola com sucesso
    Dado que estou autenticado para dias de suspensao
    Quando consulto lista de dias de suspensao para uma escola existente
    Entao a operacao de suspensao retorna 200
    E a lista de dias de suspensao apresenta datas e editais

  Esquema do Cenario: Rejeitar suspensao inexistente
    Dado que estou autenticado para dias de suspensao
    Quando executo "<metodo>" em suspensao inexistente
    Entao a operacao de suspensao retorna 404
    Exemplos:
      | metodo |
      | GET    |
      | PUT    |
      | PATCH  |
      | DELETE |

  Esquema do Cenario: Rejeitar acesso sem autenticacao
    Quando executo "<metodo>" na rota de suspensao "<rota>" sem autenticacao
    Entao a operacao de suspensao retorna 401
    Exemplos:
      | metodo | rota       |
      | GET    | listagem   |
      | POST   | listagem   |
      | GET    | detalhe    |
      | PUT    | detalhe    |
      | PATCH  | detalhe    |
      | DELETE | detalhe    |
      | GET    | lista-dias |

  Cenario: Rejeitar cadastro sem campos obrigatorios
    Dado que estou autenticado para dias de suspensao
    Quando cadastro suspensao sem campos obrigatorios
    Entao a operacao de suspensao retorna 400
    E a suspensao informa campos obrigatorios

  Esquema do Cenario: Rejeitar consulta de lista de dias invalida
    Dado que estou autenticado para dias de suspensao
    Quando consulto lista de dias de suspensao com "<condicao>"
    Entao a operacao de suspensao retorna <status>
    Exemplos:
      | condicao            | status |
      | filtros ausentes    | 400    |
      | escola inexistente  | 404    |
