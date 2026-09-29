# language: pt
Funcionalidade: Validar cronogramas
  Contexto:
    Dado que estou autenticado para consultar cronogramas

  Esquema do Cenario: Consultar cronogramas por status
    Quando consulto cronogramas com status "<status>"
    Entao a consulta de cronogramas retorna dados ou permissao negada
    Exemplos:
      | status                             |
      | sem filtro                         |
      | RASCUNHO                           |
      | ASSINADO_E_ENVIADO_AO_FORNECEDOR  |
      | ALTERACAO_CODAE                    |
      | ASSINADO_CODAE                     |
      | ASSINADO_FORNECEDOR                |
      | SOLICITADO_ALTERACAO               |
      | ASSINADO_DILOG_ABASTECIMENTO       |

  Esquema do Cenario: Consultar cronogramas por campo
    Quando consulto cronogramas pelo campo "<campo>" com valor "<valor>"
    Entao a consulta de cronogramas retorna "<resultado>" ou permissao negada
    Exemplos:
      | campo        | valor          | resultado |
      | nome_empresa | JP Alimentos   | dados     |
      | nome_empresa | testes testes  | vazio     |
      | nome_produto | ARROZ TIPO I   | dados     |
      | nome_produto | testes-testes  | vazio     |
      | numero       | 172/2024A      | dados     |
      | numero       | testeteste     | vazio     |

  Cenario: Consultar cronograma por parametro UUID valido
    Quando consulto cronograma por parametro UUID existente
    Entao a consulta de cronogramas retorna dados ou permissao negada

  Cenario: Consultar cronograma por parametro UUID invalido
    Quando consulto cronogramas pelo campo "uuid" com valor "53886ad8-cb8b-4175-853e-deaaaaaaaaaa"
    Entao a consulta de cronogramas retorna "vazio" ou permissao negada

  Esquema do Cenario: Consultar detalhe de cronograma por UUID
    Quando consulto o detalhe "<detalhe>" de cronograma com UUID "<tipo>"
    Entao o detalhe de cronograma retorna "<resultado>"
    Exemplos:
      | detalhe          | tipo     | resultado              |
      | cronograma       | valido   | dados ou permissao      |
      | cronograma       | invalido | nao encontrado          |
      | ficha recebimento| valido   | dados ou permissao      |
      | ficha recebimento| invalido | nao encontrado          |
      | log              | valido   | dados ou permissao      |
      | log              | invalido | nao encontrado          |

  Esquema do Cenario: Consultar dashboard de cronogramas
    Quando consulto a dashboard de cronogramas com filtro "<filtro>"
    Entao a dashboard de cronogramas retorna "<resultado>" ou permissao negada
    Exemplos:
      | filtro                    | resultado |
      | sem parametros            | dados     |
      | filtros vazios            | dados     |
      | filtros preenchidos       | dados     |
      | produto existente         | dados     |
      | produto inexistente       | vazio     |
      | numero existente          | dados     |
      | numero inexistente        | vazio     |

  Esquema do Cenario: Consultar listas auxiliares de cronogramas
    Quando consulto a lista auxiliar de cronogramas "<lista>"
    Entao a lista auxiliar de cronogramas retorna dados ou permissao negada
    Exemplos:
      | lista               |
      | ficha recebimento   |
      | cadastro            |
      | relatorio           |
      | opcoes etapas       |
      | rascunhos           |

  Cenario: Cadastrar cronograma e limpar massa
    Quando cadastro um cronograma para teste
    Entao o cronograma e criado e removido ou retorna permissao negada

  Cenario: Excluir cronograma existente
    Quando cadastro e excluo um cronograma para teste
    Entao o cronograma e excluido ou retorna permissao negada

  Cenario: Excluir cronograma com UUID invalido
    Quando excluo um cronograma com UUID invalido
    Entao a exclusao de cronograma retorna nao encontrado ou permissao negada

  @complemento_cronogramas
  Cenario: Consultar dados de cronograma para pos recebimento
    Quando consulto complemento de cronogramas "dados_pos_recebimento" com registro existente
    Entao os dados de pos recebimento do cronograma sao validos

  @complemento_cronogramas
  Cenario: Listar cronogramas do contrato e empresa
    Quando consulto complemento de cronogramas "lista_pos_recebimento" com registro existente
    Entao a lista de pos recebimento inclui o cronograma selecionado

  @complemento_cronogramas
  Cenario: Gerar PDF individual de cronograma
    Quando consulto complemento de cronogramas "pdf_cronograma" com registro existente
    Entao o PDF individual de cronograma e valido

  @complemento_cronogramas
  Esquema do Cenario: Solicitar exportacao assincrona de cronogramas
    Quando solicito exportacao de cronogramas "<operacao>"
    Entao a exportacao de cronogramas confirma o recebimento
    Exemplos:
      | operacao       |
      | relatorio_pdf  |
      | relatorio_xlsx |

  @complemento_cronogramas
  Cenario: Consultar pos recebimento sem filtros obrigatorios
    Quando consulto pos recebimento de cronogramas sem filtros
    Entao a lista de pos recebimento de cronogramas esta vazia

  @complemento_cronogramas
  Esquema do Cenario: Rejeitar consultas complementares por UUID inexistente
    Quando consulto complemento de cronogramas "<operacao>" com UUID inexistente
    Entao o complemento de cronogramas retorna status 404
    Exemplos:
      | operacao              |
      | dados_pos_recebimento |
      | pdf_cronograma        |

  @complemento_cronogramas
  Esquema do Cenario: Bloquear escola nas alteracoes e assinaturas de cronogramas
    Quando tento alterar cronogramas com "<operacao>" como escola
    Entao o complemento de cronogramas retorna status 403
    Exemplos:
      | operacao             |
      | atualizar            |
      | parcial              |
      | assinar_abastecimento |
      | assinar_codae        |
      | assinar_fornecedor   |

  @complemento_cronogramas
  Esquema do Cenario: Exigir autenticacao nos metodos complementares de cronogramas
    Quando acesso complemento de cronogramas "<operacao>" sem autenticacao
    Entao o complemento de cronogramas retorna status 401
    Exemplos:
      | operacao              |
      | atualizar             |
      | parcial               |
      | assinar_abastecimento |
      | assinar_codae         |
      | assinar_fornecedor    |
      | dados_pos_recebimento |
      | pdf_cronograma        |
      | relatorio_pdf         |
      | relatorio_xlsx        |
      | lista_pos_recebimento |
