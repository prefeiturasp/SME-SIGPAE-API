# language: pt
Funcionalidade: Validar escolas simplissimas com EOL
  Contexto:
    Dado que estou autenticado como CODAE para consultar escolas simplissimas com EOL

  Cenario: Consultar lista de escolas simplissimas com EOL
    Quando consulto a lista de escolas simplissimas com EOL
    Entao a lista de escolas simplissimas com EOL retorna dados paginados

  Cenario: Consultar escola existente com EOL
    Quando consulto uma escola simplissima com EOL existente
    Entao a escola simplissima com EOL corresponde a escola consultada

  Esquema do Cenario: Rejeitar UUID inexistente ou malformado
    Quando consulto a escola simplissima com EOL pelo UUID "<uuid>"
    Entao a escola simplissima com EOL retorna status 404
    Exemplos:
      | uuid                                 |
      | 00000000-0000-0000-0000-000000000000 |
      | uuid-invalido                        |

  Esquema do Cenario: Limitar a quantidade de escolas retornadas
    Quando consulto escolas simplissimas com EOL com limite <limite>
    Entao a lista de escolas simplissimas com EOL retorna dados paginados
    E a listagem de escolas simplissimas com EOL respeita o limite
    Exemplos:
      | limite |
      | 1      |
      | 2      |

  Cenario: Consultar pagina com deslocamento
    Quando consulto escolas simplissimas com EOL com deslocamento
    Entao a listagem de escolas simplissimas com EOL retorna a segunda escola

  Cenario: Consultar pagina depois do total
    Quando consulto escolas simplissimas com EOL depois do total
    Entao a listagem de escolas simplissimas com EOL retorna vazia

  Esquema do Cenario: Rejeitar consulta sem autenticacao valida
    Quando consulto "<recurso>" de escolas simplissimas com EOL com autenticacao "<autenticacao>"
    Entao a escola simplissima com EOL retorna status 401
    E a resposta de escolas simplissimas com EOL apresenta mensagem de erro
    Exemplos:
      | recurso  | autenticacao |
      | listagem | ausente      |
      | detalhe  | ausente      |
      | listagem | invalida     |
      | detalhe  | invalida     |

  Esquema do Cenario: Rejeitar metodos de escrita
    Quando envio "<metodo>" para "<recurso>" de escolas simplissimas com EOL
    Entao a escola simplissima com EOL retorna status 405
    E a resposta de escolas simplissimas com EOL apresenta mensagem de erro
    Exemplos:
      | metodo | recurso  |
      | POST   | listagem |
      | PUT    | listagem |
      | PATCH  | listagem |
      | DELETE | listagem |
      | POST   | detalhe  |
      | PUT    | detalhe  |
      | PATCH  | detalhe  |
      | DELETE | detalhe  |

  Esquema do Cenario: Consultar acoes POST de escolas com EOL
    Quando consulto a acao EOL "<acao>" com filtro "nenhum"
    Entao a acao EOL retorna uma lista de escolas
    Exemplos:
      | acao                |
      | escolas-com-cod-eol |
      | terc-total          |

  Esquema do Cenario: Consultar filtros sem correspondencia
    Quando consulto a acao EOL "escolas-com-cod-eol" com filtro "<filtro>"
    Entao a acao EOL informa ausencia de resultados
    Exemplos:
      | filtro                       |
      | lote                         |
      | lotes                        |
      | tipos_unidades               |
      | tipos_unidades_selecionadas   |

  Cenario: Consultar terceirizadas totais sem lote correspondente
    Quando consulto a acao EOL "terc-total" com filtro "lotes"
    Entao a acao EOL retorna uma lista vazia

  Esquema do Cenario: Rejeitar acesso invalido nas acoes POST de EOL
    Quando executo "POST" na acao EOL "<acao>" com acesso "<acesso>"
    Entao a escola simplissima com EOL retorna status 401
    Exemplos:
      | acao                | acesso   |
      | escolas-com-cod-eol | ausente  |
      | escolas-com-cod-eol | invalido |
      | terc-total          | ausente  |
      | terc-total          | invalido |

  Esquema do Cenario: Rejeitar metodos nao suportados nas acoes de EOL
    Quando executo "<metodo>" na acao EOL "<acao>" com acesso "valido"
    Entao a escola simplissima com EOL retorna status 405
    Exemplos:
      | acao                | metodo |
      | escolas-com-cod-eol | GET    |
      | escolas-com-cod-eol | PUT    |
      | escolas-com-cod-eol | PATCH  |
      | escolas-com-cod-eol | DELETE |
      | terc-total          | GET    |
      | terc-total          | PUT    |
      | terc-total          | PATCH  |
      | terc-total          | DELETE |
