# language: pt
Funcionalidade: Validar escolas para filtros

  Cenario: Consultar escolas sem paginacao
    Quando consulto escolas para filtros com sucesso
    Entao a operacao de escolas para filtros retorna 200
    E escolas para filtros retorna uma lista valida

  Esquema do Cenario: Consultar dados da escola
    Quando consulto "<rota>" de uma escola para filtros existente
    Entao a operacao de escolas para filtros retorna 200
    E escolas para filtros retorna periodos ou tipos de alimentacao validos
    Exemplos:
      | rota               |
      | periodos-escolares |
      | tipos-alimentacao  |

  Esquema do Cenario: Filtrar escolas por vinculos
    Quando consulto escolas para filtros usando "<filtro>"
    Entao a operacao de escolas para filtros retorna 200
    E escolas para filtros retorna uma lista valida
    E escolas para filtros corresponde ao filtro aplicado
    Exemplos:
      | filtro         |
      | dre            |
      | lote           |
      | tipo           |
      | multiplos      |
      | combinados     |
      | tipos em lista |
      | lotes em lista |
      | excluir tipo   |

  Cenario: Filtrar escolas por tipo de gestao
    Quando consulto escolas para filtros pelo tipo de gestao
    Entao a operacao de escolas para filtros retorna 200
    E escolas para filtros retorna uma lista valida
    E escolas para filtros respeita o tipo de gestao

  Esquema do Cenario: Consultar filtros sem resultados
    Quando consulto escolas para filtros com parametro "<campo>" e valor "<valor>"
    Entao a operacao de escolas para filtros retorna 200
    E escolas para filtros retorna uma lista vazia
    Exemplos:
      | campo                    | valor                      |
      | diretoria_regional__uuid | inexistente                |
      | lote__uuid               | inexistente                |
      | tipo_unidade__uuid__in   | inexistente                |
      | tipo_gestao__nome        | GESTAO_INEXISTENTE_CYPRESS |

  Esquema do Cenario: Rejeitar UUID invalido nos filtros
    Quando consulto escolas para filtros com parametro "<campo>" e valor "uuid-invalido"
    Entao a operacao de escolas para filtros retorna 400
    E escolas para filtros informa parametro invalido
    Exemplos:
      | campo                    |
      | diretoria_regional__uuid |
      | lote__uuid               |
      | tipo_unidade__uuid__in   |

  Esquema do Cenario: Rejeitar escola inexistente ou UUID malformado
    Quando consulto "<rota>" de escolas para filtros com UUID "<uuid>"
    Entao a operacao de escolas para filtros retorna 404
    Exemplos:
      | rota               | uuid          |
      | periodos-escolares | inexistente   |
      | tipos-alimentacao  | inexistente   |
      | periodos-escolares | uuid-invalido |
      | tipos-alimentacao  | uuid-invalido |

  Esquema do Cenario: Rejeitar acesso sem token valido
    Quando consulto escolas para filtros na rota "<rota>" com acesso "<acesso>"
    Entao a operacao de escolas para filtros retorna 401
    Exemplos:
      | rota               | acesso         |
      | listagem           | anonimo        |
      | periodos-escolares | anonimo        |
      | tipos-alimentacao  | anonimo        |
      | listagem           | token invalido |
      | periodos-escolares | token invalido |
      | tipos-alimentacao  | token invalido |

  Esquema do Cenario: Rejeitar metodos nao permitidos
    Quando executo "<metodo>" em escolas para filtros na rota "<rota>"
    Entao a operacao de escolas para filtros retorna 405
    Exemplos:
      | metodo | rota               |
      | POST   | listagem           |
      | PUT    | listagem           |
      | PATCH  | listagem           |
      | DELETE | listagem           |
      | POST   | periodos-escolares |
      | PUT    | periodos-escolares |
      | PATCH  | periodos-escolares |
      | DELETE | periodos-escolares |
      | POST   | tipos-alimentacao  |
      | PUT    | tipos-alimentacao  |
      | PATCH  | tipos-alimentacao  |
      | DELETE | tipos-alimentacao  |
