# language: pt
@embalagens_produto
Funcionalidade: Validar embalagens de produto

  Contexto:
    Dado que estou autenticado como CODAE para consultar embalagens de produto

  Cenario: Consultar todas as embalagens de produto
    Quando consulto todas as embalagens de produto
    Entao a consulta de embalagens de produto retorna status 200 e uma lista valida

  Cenario: Consultar embalagens de produto com paginacao
    Quando consulto embalagens de produto com limite 2 e deslocamento 2
    Entao a consulta paginada de embalagens de produto retorna status 200 e uma lista valida

  Cenario: Cadastrar embalagem de produto
    Quando cadastro uma embalagem de produto
    Entao a operacao de embalagens de produto retorna 201
    E a embalagem de produto corresponde aos dados enviados

  Cenario: Consultar embalagem de produto por UUID
    Dado que cadastrei uma embalagem de produto para o cenario
    Quando consulto a embalagem de produto criada por UUID
    Entao a operacao de embalagens de produto retorna 200
    E a embalagem de produto corresponde aos dados enviados

  Esquema do Cenario: Atualizar embalagem de produto
    Dado que cadastrei uma embalagem de produto para o cenario
    Quando atualizo a embalagem de produto criada usando "<metodo>"
    Entao a operacao de embalagens de produto retorna 200
    E a embalagem de produto corresponde aos dados enviados
    E a alteracao da embalagem de produto foi persistida
    Exemplos:
      | metodo |
      | PUT    |
      | PATCH  |

  Cenario: Excluir embalagem de produto
    Dado que cadastrei uma embalagem de produto para o cenario
    Quando excluo a embalagem de produto criada
    Entao a operacao de embalagens de produto retorna 204
    E a embalagem de produto excluida nao pode ser consultada

  Esquema do Cenario: Rejeitar acesso a embalagens de produto sem autenticacao
    Quando executo "<metodo>" em embalagens de produto na rota "<rota>" sem autenticacao
    Entao a operacao de embalagens de produto retorna 401
    E embalagens de produto informa erro de autenticacao
    Exemplos:
      | metodo | rota     |
      | GET    | listagem |
      | POST   | listagem |
      | GET    | detalhe  |
      | PUT    | detalhe  |
      | PATCH  | detalhe  |
      | DELETE | detalhe  |

  Esquema do Cenario: Rejeitar UUID de embalagem de produto inexistente
    Quando executo "<metodo>" em uma embalagem de produto inexistente
    Entao a operacao de embalagens de produto retorna 404
    Exemplos:
      | metodo |
      | GET    |
      | PUT    |
      | PATCH  |
      | DELETE |

  Cenario: Rejeitar cadastro de embalagem com nome acima do limite
    Quando cadastro uma embalagem de produto com nome de 101 caracteres
    Entao a operacao de embalagens de produto retorna 400
    E embalagens de produto informa erro no nome

  Esquema do Cenario: Rejeitar atualizacao de embalagem com nome acima do limite
    Dado que cadastrei uma embalagem de produto para o cenario
    Quando atualizo a embalagem de produto usando "<metodo>" com nome de 101 caracteres
    Entao a operacao de embalagens de produto retorna 400
    E embalagens de produto informa erro no nome
    E o nome original da embalagem de produto foi preservado
    Exemplos:
      | metodo |
      | PUT    |
      | PATCH  |
