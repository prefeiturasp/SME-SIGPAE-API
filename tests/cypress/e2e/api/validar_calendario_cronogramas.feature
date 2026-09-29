# language: pt
Funcionalidade: Validar calendario de cronogramas

  Cenario: Consultar calendario do mes atual com sucesso e paginacao
    Dado que estou autenticado para consultar o calendario de cronogramas
    Quando consulto o calendario de cronogramas do mes atual
    Entao o calendario retorna uma lista paginada com limite de dois itens

  Esquema do Cenario: Rejeitar parametros ausentes ou invalidos no calendario
    Dado que estou autenticado para consultar o calendario de cronogramas
    Quando consulto o calendario de cronogramas com parametros "<parametros>"
    Entao o calendario retorna erro de validacao contendo "<mensagem>"
    Exemplos:
      | parametros           | mensagem               |
      |                      | obrigatorios           |
      | ?mes=3               | obrigatorios           |
      | ?ano=2025            | obrigatorios           |
      | ?mes=0&ano=2025      | entre 1 e 12           |
      | ?mes=13&ano=2025     | entre 1 e 12           |
      | ?mes=abc&ano=2025    | numeros inteiros       |
      | ?mes=3&ano=abc       | numeros inteiros       |
      | ?mes=3&ano=202       | 4 digitos              |
      | ?mes=3&ano=20255     | 4 digitos              |

  Cenario: Consultar etapa de calendario inexistente
    Dado que estou autenticado para consultar o calendario de cronogramas
    Quando consulto a etapa de calendario com ID inexistente
    Entao o calendario de cronogramas retorna status 404 e detalhe

  Cenario: Rejeitar detalhe do calendario sem mes e ano
    Dado que estou autenticado para consultar o calendario de cronogramas
    Quando consulto a etapa de calendario sem parametros
    Entao o calendario retorna erro de validacao contendo "obrigatorios"

  Cenario: Bloquear listagem do calendario para escola
    Dado que estou autenticado como escola para consultar calendario
    Quando consulto o calendario de cronogramas com parametros "?mes=3&ano=2025"
    Entao o calendario de cronogramas retorna status 403 e detalhe

  Cenario: Bloquear detalhe do calendario para escola
    Dado que estou autenticado como escola para consultar calendario
    Quando consulto a etapa de calendario com ID inexistente
    Entao o calendario de cronogramas retorna status 403 e detalhe

  Esquema do Cenario: Exigir autenticacao no calendario
    Quando consulto "<operacao>" do calendario sem autenticacao
    Entao o calendario de cronogramas retorna status 401 e detalhe
    Exemplos:
      | operacao |
      | listagem |
      | detalhe  |
