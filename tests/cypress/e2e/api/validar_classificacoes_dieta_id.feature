# language: pt
Funcionalidade: Validar classificacoes de dieta por ID

  Contexto:
    Dado que estou autenticado para consultar classificacoes de dieta por ID

  Esquema do Cenario: Consultar classificacao existente
    Quando consulto a classificacao de dieta pelo ID <id>
    Entao a classificacao retorna status 200, ID <id> e nome "<nome>"

    Exemplos:
      | id | nome                            |
      | 1  | Tipo A                          |
      | 5  | Tipo A ENTERAL                  |
      | 7  | Tipo A RESTRICAO DE AMINOACIDOS |
      | 2  | Tipo B                          |
      | 6  | Tipo C                          |

  Esquema do Cenario: Consultar classificacao inexistente
    Quando consulto a classificacao de dieta pelo ID <id>
    Entao a classificacao retorna status 404

    Exemplos:
      | id |
      | 3  |
      | 4  |
