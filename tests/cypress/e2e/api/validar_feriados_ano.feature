# language: pt
Funcionalidade: Validar feriados por ano

  Esquema do Cenario: Consultar feriados com e sem autenticacao
    Quando consulto feriados da rota "<rota>" com acesso "<acesso>"
    Entao os feriados possuem datas e anos corretos
    Exemplos:
      | rota            | acesso  |
      | atual           | valido  |
      | atual e proximo | valido  |
      | atual           | ausente |
      | atual e proximo | ausente |

  Esquema do Cenario: Rejeitar token invalido mesmo em rota publica
    Quando consulto feriados da rota "<rota>" com acesso "invalido"
    Entao a consulta de feriados retorna status 401
    Exemplos:
      | rota            |
      | atual           |
      | atual e proximo |

  Esquema do Cenario: Rejeitar metodos nao permitidos
    Quando envio "<metodo>" para a rota de feriados "<rota>"
    Entao a consulta de feriados retorna status 405
    Exemplos:
      | metodo | rota            |
      | POST   | atual           |
      | PUT    | atual           |
      | PATCH  | atual           |
      | DELETE | atual           |
      | POST   | atual e proximo |
      | PUT    | atual e proximo |
      | PATCH  | atual e proximo |
      | DELETE | atual e proximo |

  Cenario: Comparar feriados do ano atual entre as rotas
    Quando comparo as duas consultas de feriados
    Entao os feriados do ano atual coincidem nas duas rotas
