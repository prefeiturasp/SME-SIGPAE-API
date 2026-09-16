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
