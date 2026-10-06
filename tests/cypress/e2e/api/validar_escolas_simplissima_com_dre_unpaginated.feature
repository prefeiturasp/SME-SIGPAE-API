# language: pt
Funcionalidade: Validar escolas simplissimas com DRE sem paginacao
  Contexto:
    Dado que estou autenticado como CODAE para consultar escolas com DRE sem paginacao

  Esquema do Cenario: Listar escolas sem paginacao
    Quando consulto escolas com DRE sem paginacao na rota "<rota>"
    Entao a resposta sem paginacao contem uma lista de escolas
    Exemplos:
      | rota       |
      | lista      |
      | terc-total |

  Cenario: Consultar detalhe existente sem paginacao
    Quando consulto detalhe sem paginacao com UUID "existente"
    Entao o detalhe sem paginacao corresponde a escola consultada

  Esquema do Cenario: Rejeitar UUID sem paginacao inexistente ou malformado
    Quando consulto detalhe sem paginacao com UUID "<uuid>"
    Entao a escola simplissima com DRE sem paginacao retorna status 404
    Exemplos:
      | uuid                                 |
      | 00000000-0000-0000-0000-000000000000 |
      | uuid-invalido                        |

  Esquema do Cenario: Rejeitar acesso sem autenticacao valida nas rotas sem paginacao
    Quando executo "GET" na rota sem paginacao "<rota>" com acesso "<acesso>"
    Entao a escola simplissima com DRE sem paginacao retorna status 401
    Exemplos:
      | rota       | acesso   |
      | lista      | ausente  |
      | lista      | invalido |
      | detalhe    | ausente  |
      | detalhe    | invalido |
      | terc-total | ausente  |
      | terc-total | invalido |

  Esquema do Cenario: Rejeitar escrita nas rotas sem paginacao
    Quando executo "<metodo>" na rota sem paginacao "<rota>" com acesso "valido"
    Entao a escola simplissima com DRE sem paginacao retorna status 405
    Exemplos:
      | metodo | rota       |
      | POST   | lista      |
      | PUT    | lista      |
      | PATCH  | lista      |
      | DELETE | lista      |
      | POST   | detalhe    |
      | PUT    | detalhe    |
      | PATCH  | detalhe    |
      | DELETE | detalhe    |
      | POST   | terc-total |
      | PUT    | terc-total |
      | PATCH  | terc-total |
      | DELETE | terc-total |

  Cenario: Filtrar terc-total por escola existente
    Quando filtro terc-total por escola existente
    Entao terc-total retorna somente a escola filtrada

  Esquema do Cenario: Filtrar terc-total sem correspondencias
    Quando filtro terc-total pelo campo "<campo>" inexistente
    Entao terc-total retorna lista vazia
    Exemplos:
      | campo        |
      | escola       |
      | dre          |
      | tipo_unidade |
      | terceirizada |
      | nome_edital  |
