# language: pt
Funcionalidade: Validar fichas de recebimento

  Cenario: Consultar listagem
    Quando consulto ficha de recebimento na listagem "principal"
    Entao a listagem de fichas de recebimento retorna resultados

  Cenario: Consultar detalhe existente
    Quando consulto detalhe de ficha de recebimento existente
    Entao o detalhe corresponde a ficha de recebimento consultada

  Esquema do Cenario: Validar paginacao
    Quando consulto ficha de recebimento com tamanho de pagina <tamanho>
    Entao a ficha de recebimento respeita o tamanho da pagina
    Exemplos:
      | tamanho |
      | 1 |
      | 2 |

  Esquema do Cenario: Consultar filtros sem resultados
    Quando consulto ficha de recebimento com filtro "<campo>" igual a "CYPRESS-INEXISTENTE-000000"
    Entao a lista de fichas de recebimento esta vazia
    Exemplos:
      | campo |
      | nome_produto |
      | numero_cronograma |
      | nome_empresa |

  Esquema do Cenario: Rejeitar filtros invalidos
    Quando consulto ficha de recebimento com filtro "<campo>" igual a "invalido"
    Entao a ficha de recebimento retorna status 400
    Exemplos:
      | campo |
      | data_inicial |
      | data_final |
      | status |

  Esquema do Cenario: Consultar ficha inexistente
    Quando consulto ficha de recebimento inexistente na acao "<acao>"
    Entao a ficha de recebimento retorna status 404
    Exemplos:
      | acao |
      | detalhe |
      | gerar-pdf-ficha |

  Cenario: Rejeitar exclusao da colecao
    Quando envio DELETE para a colecao de fichas de recebimento
    Entao a ficha de recebimento retorna status 405

  Esquema do Cenario: Exigir autenticacao nos metodos documentados
    Quando executo "<metodo>" na rota de ficha de recebimento "<rota>" com acesso "<acesso>"
    Entao a ficha de recebimento retorna status 401
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
      | PUT | 00000000-0000-0000-0000-000000000000/atualizar-saldo-zero/ | ausente |
      | PUT | 00000000-0000-0000-0000-000000000000/atualizar-saldo-zero/ | invalido |
      | GET | 00000000-0000-0000-0000-000000000000/gerar-pdf-ficha/ | ausente |
      | GET | 00000000-0000-0000-0000-000000000000/gerar-pdf-ficha/ | invalido |
      | POST | cadastrar-saldo-zero/ | ausente |
      | POST | cadastrar-saldo-zero/ | invalido |

  Cenario: Gerar PDF de ficha de recebimento com sucesso
    Quando gero o PDF de uma ficha de recebimento assinada existente
    Entao a ficha de recebimento retorna um arquivo PDF valido

  Cenario: Validar permissao de cadastro do usuario configurado
    Quando valido a permissao de cadastro de recebimento do usuario de qualidade
    Entao o usuario de qualidade pode acessar a validacao de cadastro
