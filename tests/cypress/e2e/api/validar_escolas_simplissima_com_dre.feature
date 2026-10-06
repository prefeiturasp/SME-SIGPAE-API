# language: pt
Funcionalidade: Validar escolas simplissimas com DRE
  Contexto:
    Dado que estou autenticado como CODAE para consultar escolas simplissimas com DRE

  Cenario: Consultar lista de escolas simplissimas com DRE
    Quando consulto a lista de escolas simplissimas com DRE
    Entao a lista de escolas simplissimas com DRE retorna dados paginados

  Cenario: Consultar escola existente com DRE
    Quando consulto uma escola simplissima com DRE existente
    Entao a escola simplissima com DRE corresponde a escola consultada

  Esquema do Cenario: Rejeitar UUID inexistente ou malformado
    Quando consulto a escola simplissima com DRE pelo UUID "<uuid>"
    Entao a escola simplissima com DRE retorna status 404
    Exemplos:
      | uuid                                 |
      | 00000000-0000-0000-0000-000000000000 |
      | uuid-invalido                        |

  Esquema do Cenario: Limitar a quantidade de escolas retornadas
    Quando consulto escolas simplissimas com DRE com limite <limite>
    Entao a lista de escolas simplissimas com DRE retorna dados paginados
    E a listagem de escolas simplissimas com DRE respeita o limite
    Exemplos:
      | limite |
      | 1      |
      | 2      |

  Cenario: Consultar pagina com deslocamento
    Quando consulto escolas simplissimas com DRE com deslocamento
    Entao a listagem de escolas simplissimas com DRE retorna a segunda escola

  Cenario: Consultar pagina depois do total
    Quando consulto escolas simplissimas com DRE depois do total
    Entao a listagem de escolas simplissimas com DRE retorna vazia

  Esquema do Cenario: Rejeitar consulta sem autenticacao valida
    Quando consulto "<recurso>" de escolas simplissimas com DRE com autenticacao "<autenticacao>"
    Entao a escola simplissima com DRE retorna status 401
    E a resposta de escolas simplissimas com DRE apresenta mensagem de erro
    Exemplos:
      | recurso  | autenticacao |
      | listagem | ausente      |
      | detalhe  | ausente      |
      | listagem | invalida     |
      | detalhe  | invalida     |

  Esquema do Cenario: Rejeitar metodos de escrita
    Quando envio "<metodo>" para "<recurso>" de escolas simplissimas com DRE
    Entao a escola simplissima com DRE retorna status 405
    E a resposta de escolas simplissimas com DRE apresenta mensagem de erro
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
