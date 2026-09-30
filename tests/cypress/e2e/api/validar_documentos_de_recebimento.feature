# language: pt
Funcionalidade: Validar documentos de recebimento
  Cenario: Consultar documentos de recebimento com sucesso
    Quando consulto documentos de recebimento com usuario autorizado
    Entao a consulta de documentos retorna status 200 e dados paginados validos
  Cenario: Consultar documentos de recebimento sem permissao
    Quando consulto documentos de recebimento com usuario CODAE
    Entao a consulta de documentos retorna status 403 e mensagem de permissao

  # O POST com sucesso permanece desabilitado porque nenhum usuario do .env possui permissao.

  Cenario: Gerar documentos de recebimento sem permissao
    Quando tento gerar documentos de recebimento com usuario CODAE
    Entao a geracao de documentos retorna status 403 e mensagem de permissao

  @complemento_documentos
  Esquema do Cenario: Consultar detalhe e paineis de documentos com sucesso
    Quando consulto documentos de recebimento pela operacao "<operacao>"
    Entao a consulta complementar de documentos retorna dados validos
    Exemplos:
      | operacao           |
      | detalhe            |
      | dashboard          |
      | listagem-relatorio |

  @complemento_documentos
  Esquema do Cenario: Exigir autenticacao nas operacoes de documentos
    Quando executo "<metodo>" em documentos na rota "<rota>" com perfil "anonimo"
    Entao a operacao complementar de documentos retorna 401
    Exemplos:
      | metodo | rota                        |
      | GET    | listagem                    |
      | POST   | listagem                    |
      | GET    | detalhe                     |
      | PUT    | detalhe                     |
      | PATCH  | detalhe                     |
      | DELETE | detalhe                     |
      | PATCH  | analise-documentos          |
      | PATCH  | analise-documentos-rascunho |
      | PATCH  | atualizar-documentos        |
      | PATCH  | corrigir-documentos         |
      | GET    | download-laudo-assinado      |
      | GET    | dashboard                   |
      | GET    | exportar-excel              |
      | GET    | listagem-relatorio          |

  @complemento_documentos
  Esquema do Cenario: Rejeitar documento inexistente
    Quando executo "<metodo>" em documentos na rota "<rota>" com perfil "<perfil>"
    Entao a operacao complementar de documentos retorna 404
    Exemplos:
      | metodo | rota                        | perfil     |
      | GET    | detalhe                     | autorizado |
      | PUT    | detalhe                     | autorizado |
      | PATCH  | detalhe                     | autorizado |
      | DELETE | detalhe                     | autorizado |
      | GET    | download-laudo-assinado      | autorizado |
      | PATCH  | analise-documentos          | qualidade  |
      | PATCH  | analise-documentos-rascunho | qualidade  |

  @complemento_documentos
  Esquema do Cenario: Bloquear operacoes exclusivas para perfil CODAE sem permissao
    Quando executo "<metodo>" em documentos na rota "<rota>" com perfil "codae"
    Entao a operacao complementar de documentos retorna 403
    Exemplos:
      | metodo | rota                 |
      | PATCH  | atualizar-documentos |
      | PATCH  | corrigir-documentos  |
      | GET    | exportar-excel       |
