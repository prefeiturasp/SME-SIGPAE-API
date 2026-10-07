# language: pt
Funcionalidade: Validar fichas tecnicas

  Esquema do Cenario: Consultar listagens de fichas tecnicas
    Quando consulto ficha tecnica na listagem "<rota>"
    Entao a listagem de fichas tecnicas retorna resultados
    Exemplos:
      | rota |
      | principal |
      | lista-simples |
      | lista-simples-aprovadas |
      | lista-simples-sem-cronograma |
      | lista-simples-sem-layout-embalagem |
      | lista-simples-sem-questoes-conferencia |
      | listagem-relatorio |

  Cenario: Consultar detalhe existente
    Quando consulto detalhe de ficha tecnica existente
    Entao o detalhe corresponde a ficha tecnica consultada

  Esquema do Cenario: Validar paginacao
    Quando consulto ficha tecnica com tamanho de pagina <tamanho>
    Entao a ficha tecnica respeita o tamanho da pagina
    Exemplos:
      | tamanho |
      | 1 |
      | 2 |

  Esquema do Cenario: Consultar filtros sem resultados
    Quando consulto ficha tecnica com filtro "<campo>" igual a "CYPRESS-INEXISTENTE-000000"
    Entao a lista de fichas tecnicas esta vazia
    Exemplos:
      | campo |
      | nome_produto |
      | numero_ficha |
      | nome_empresa |

  Esquema do Cenario: Rejeitar filtros invalidos
    Quando consulto ficha tecnica com filtro "<campo>" igual a "invalido"
    Entao a ficha tecnica retorna status 400
    Exemplos:
      | campo |
      | data_cadastro |
      | empresa |
      | status |

  Esquema do Cenario: Consultar ficha inexistente
    Quando consulto ficha tecnica inexistente na acao "<acao>"
    Entao a ficha tecnica retorna status 404
    Exemplos:
      | acao |
      | detalhe |
      | detalhar-com-analise |
      | dados-cronograma |
      | gerar-pdf-ficha |

  Cenario: Rejeitar exclusao da colecao
    Quando envio DELETE para a colecao de fichas tecnicas
    Entao a ficha tecnica retorna status 405

  Esquema do Cenario: Exigir autenticacao em todos os metodos documentados
    Quando executo "<metodo>" na rota de ficha tecnica "<rota>" com acesso "<acesso>"
    Entao a ficha tecnica retorna status 401
    Exemplos:
      | metodo | rota | acesso |
      | GET | principal | ausente |
      | GET | principal | invalido |
      | POST | principal | ausente |
      | POST | principal | invalido |
      | GET | 00000000-0000-0000-0000-000000000000/ | ausente |
      | GET | 00000000-0000-0000-0000-000000000000/ | invalido |
      | PUT | 00000000-0000-0000-0000-000000000000/ | ausente |
      | PUT | 00000000-0000-0000-0000-000000000000/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | invalido |
      | POST | 00000000-0000-0000-0000-000000000000/analise-gpcodae/ | ausente |
      | POST | 00000000-0000-0000-0000-000000000000/analise-gpcodae/ | invalido |
      | PUT | 00000000-0000-0000-0000-000000000000/analise-gpcodae/ | ausente |
      | PUT | 00000000-0000-0000-0000-000000000000/analise-gpcodae/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/atualizacao-fornecedor/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/atualizacao-fornecedor/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/correcao-fornecedor/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/correcao-fornecedor/ | invalido |
      | GET | 00000000-0000-0000-0000-000000000000/dados-cronograma/ | ausente |
      | GET | 00000000-0000-0000-0000-000000000000/dados-cronograma/ | invalido |
      | GET | 00000000-0000-0000-0000-000000000000/detalhar-com-analise/ | ausente |
      | GET | 00000000-0000-0000-0000-000000000000/detalhar-com-analise/ | invalido |
      | GET | 00000000-0000-0000-0000-000000000000/gerar-pdf-ficha/ | ausente |
      | GET | 00000000-0000-0000-0000-000000000000/gerar-pdf-ficha/ | invalido |
      | POST | 00000000-0000-0000-0000-000000000000/rascunho-analise-gpcodae/ | ausente |
      | POST | 00000000-0000-0000-0000-000000000000/rascunho-analise-gpcodae/ | invalido |
      | PUT | 00000000-0000-0000-0000-000000000000/rascunho-analise-gpcodae/ | ausente |
      | PUT | 00000000-0000-0000-0000-000000000000/rascunho-analise-gpcodae/ | invalido |
      | GET | dashboard/ | ausente |
      | GET | dashboard/ | invalido |
      | GET | exportar-excel/ | ausente |
      | GET | exportar-excel/ | invalido |
      | GET | lista-simples/ | ausente |
      | GET | lista-simples/ | invalido |
      | GET | lista-simples-aprovadas/ | ausente |
      | GET | lista-simples-aprovadas/ | invalido |
      | GET | lista-simples-sem-cronograma/ | ausente |
      | GET | lista-simples-sem-cronograma/ | invalido |
      | GET | lista-simples-sem-layout-embalagem/ | ausente |
      | GET | lista-simples-sem-layout-embalagem/ | invalido |
      | GET | lista-simples-sem-questoes-conferencia/ | ausente |
      | GET | lista-simples-sem-questoes-conferencia/ | invalido |
      | GET | listagem-relatorio/ | ausente |
      | GET | listagem-relatorio/ | invalido |
