# language: pt
Funcionalidade: Validar rota CODAE

  Contexto:
    Dado que estou autenticado na API como CODAE para consultar a CODAE

  Cenario: Validar GET paginado com sucesso da CODAE
    Quando consulto a lista paginada da CODAE
    Entao a consulta da CODAE deve retornar status 200 e registros validos

  Cenario: Consultar CODAE por UUID com sucesso
    Quando consulto uma CODAE existente por UUID
    Entao o detalhe da CODAE corresponde ao registro solicitado

  Cenario: Consultar CODAE com limite de paginacao
    Quando consulto CODAE com pagina de um registro
    Entao a paginacao CODAE respeita o limite solicitado

  Cenario: Rejeitar cadastro sem quantidade de alunos
    Quando envio cadastro CODAE sem quantidade de alunos
    Entao a CODAE retorna erro no campo "quantidade_alunos"

  Esquema do Cenario: Rejeitar cadastro CODAE invalido
    Quando envio cadastro CODAE com "<campo>" invalido
    Entao a CODAE retorna erro no campo "<campo>"
    Exemplos:
      | campo             |
      | quantidade_alunos |
      | nome              |

  Esquema do Cenario: Rejeitar atualizacao CODAE com nome acima do limite
    Quando envio atualizacao CODAE invalida usando "<metodo>"
    Entao a CODAE retorna erro no campo "nome"
    Exemplos:
      | metodo |
      | PUT    |
      | PATCH  |

  Esquema do Cenario: Rejeitar UUID inexistente CODAE
    Quando acesso CODAE inexistente usando "<metodo>"
    Entao a operacao CODAE retorna status 404
    Exemplos:
      | metodo |
      | GET    |
      | PUT    |
      | PATCH  |
      | DELETE |

  Esquema do Cenario: Exigir autenticacao nas operacoes CODAE
    Quando acesso "<metodo>" da CODAE sem autenticacao no caminho "<caminho>"
    Entao a operacao CODAE retorna status 401
    Exemplos:
      | metodo | caminho  |
      | GET    | listagem |
      | POST   | listagem |
      | GET    | detalhe  |
      | PUT    | detalhe  |
      | PATCH  | detalhe  |
      | DELETE | detalhe  |
