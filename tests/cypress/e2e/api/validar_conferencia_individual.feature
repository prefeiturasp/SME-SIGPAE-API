# language: pt
Funcionalidade: Validar conferencia individual
  # O GET autorizado permanece desabilitado porque a API retorna erro 500 no QA.

  Cenario: Consultar conferencia individual sem permissao
    Quando consulto a conferencia individual com usuario CODAE
    Entao a consulta de conferencia individual retorna status 403 e detalhe

  Esquema do Cenario: Bloquear metodos de conferencia individual para CODAE
    Quando acesso conferencia individual usando "<metodo>" como "codae" no caminho "<caminho>"
    Entao a operacao de conferencia individual retorna 403
    Exemplos:
      | metodo | caminho  |
      | POST   | listagem |
      | GET    | detalhe  |
      | PUT    | detalhe  |
      | PATCH  | detalhe  |
      | DELETE | detalhe  |

  Esquema do Cenario: Rejeitar UUID inexistente de conferencia individual
    Quando acesso conferencia individual usando "<metodo>" como "abastecimento" no caminho "detalhe"
    Entao a operacao de conferencia individual retorna 404
    Exemplos:
      | metodo |
      | GET    |
      | PUT    |
      | PATCH  |
      | DELETE |

  Esquema do Cenario: Exigir autenticacao em conferencia individual
    Quando acesso conferencia individual usando "<metodo>" como "anonimo" no caminho "<caminho>"
    Entao a operacao de conferencia individual retorna 401
    Exemplos:
      | metodo | caminho  |
      | GET    | listagem |
      | POST   | listagem |
      | GET    | detalhe  |
      | PUT    | detalhe  |
      | PATCH  | detalhe  |
      | DELETE | detalhe  |
