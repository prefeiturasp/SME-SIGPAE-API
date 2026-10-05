# language: pt
Funcionalidade: Validar escolas simplissimas
  Contexto:
    Dado que estou autenticado como CODAE para consultar escolas simplissimas
  Cenario: Consultar lista de escolas simplissimas
    Quando consulto a lista de escolas simplissimas
    Entao a lista de escolas simplissimas retorna dados paginados
  Cenario: Consultar escolas simplissimas por UUID da DRE
    Quando consulto escolas simplissimas pelo UUID da DRE
    Entao a consulta por UUID retorna escolas simplissimas validas
  Cenario: Consultar escolas simplissimas pelo filtro de DRE
    Quando filtro escolas simplissimas pela DRE
    Entao a consulta filtrada retorna escolas vinculadas a DRE

  Cenario: Consultar lista sem paginacao
    Quando consulto escolas simplissimas sem paginacao
    Entao a operacao de escolas simplissimas retorna 200
    E escolas simplissimas retorna lista sem paginacao

  Esquema do Cenario: Aplicar filtros individuais e combinados
    Quando consulto escolas simplissimas usando o filtro "<filtro>"
    Entao a operacao de escolas simplissimas retorna 200
    E escolas simplissimas respeita o filtro aplicado
    Exemplos:
      | filtro     |
      | codigo_eol |
      | nome       |
      | dre        |
      | combinados |

  Esquema do Cenario: Consultar filtros sem resultados
    Quando consulto escolas simplissimas com parametro "<campo>" e valor "<valor>"
    Entao a operacao de escolas simplissimas retorna 200
    E escolas simplissimas retorna lista vazia
    Exemplos:
      | campo                   | valor                                |
      | codigo_eol              | 000000000000                         |
      | nome                    | ESCOLA_INEXISTENTE_CYPRESS_000000     |
      | diretoria_regional__uuid | 00000000-0000-0000-0000-000000000000 |

  Cenario: Rejeitar filtro de DRE com UUID invalido
    Quando consulto escolas simplissimas com parametro "diretoria_regional__uuid" e valor "uuid-invalido"
    Entao a operacao de escolas simplissimas retorna 400
    E escolas simplissimas informa UUID de filtro invalido

  Cenario: Validar tamanho e pagina consecutiva
    Quando consulto paginas consecutivas de escolas simplissimas
    Entao a operacao de escolas simplissimas retorna 200
    E escolas simplissimas respeita tamanho e pagina

  Cenario: Rejeitar pagina alem do total
    Quando consulto pagina alem do total de escolas simplissimas
    Entao a operacao de escolas simplissimas retorna 404

  Esquema do Cenario: Rejeitar numero de pagina invalido
    Quando consulto escolas simplissimas com parametro "page" e valor "<valor>"
    Entao a operacao de escolas simplissimas retorna 404
    Exemplos:
      | valor |
      | 0     |
      | abc   |

  Cenario: Consultar agrupamento de DRE inexistente
    Quando consulto escolas simplissimas pela DRE "00000000-0000-0000-0000-000000000000"
    Entao a operacao de escolas simplissimas retorna 200
    E escolas simplissimas retorna agrupamento vazio

  Esquema do Cenario: Rejeitar acesso sem token valido
    Quando executo "GET" em escolas simplissimas na rota "<rota>" com acesso "<acesso>"
    Entao a operacao de escolas simplissimas retorna 401
    Exemplos:
      | rota     | acesso         |
      | listagem | anonimo        |
      | dre      | anonimo        |
      | listagem | token invalido |
      | dre      | token invalido |

  Esquema do Cenario: Rejeitar metodos nao permitidos
    Quando executo "<metodo>" em escolas simplissimas na rota "<rota>" com acesso "autenticado"
    Entao a operacao de escolas simplissimas retorna 405
    Exemplos:
      | metodo | rota     |
      | POST   | listagem |
      | PUT    | listagem |
      | PATCH  | listagem |
      | DELETE | listagem |
      | POST   | dre      |
      | PUT    | dre      |
      | PATCH  | dre      |
      | DELETE | dre      |
