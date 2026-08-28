# language: pt
Funcionalidade: Validar rotas de IMR
  Contexto:
    Dado que estou autenticado como CODAE para consultar IMR

  Esquema do Cenario: Consultar catalogos de IMR
    Quando consulto o catalogo IMR "<catalogo>" com identificador "<identificador>"
    Entao o catalogo IMR retorna "<resultado>"
    Exemplos:
      | catalogo             | identificador | resultado         |
      | equipamentos         | lista         | lista ou permissao|
      | equipamentos         | valido        | detalhe ou permissao|
      | equipamentos         | invalido      | nao encontrado    |
      | insumos              | lista         | lista ou permissao|
      | insumos              | valido        | detalhe ou permissao|
      | insumos              | invalido      | nao encontrado    |
      | mobiliarios          | lista         | lista ou permissao|
      | mobiliarios          | valido        | detalhe ou permissao|
      | mobiliarios          | invalido      | nao encontrado    |
      | periodos visita      | lista         | lista ou permissao|
      | periodos visita      | valido        | detalhe ou permissao|
      | periodos visita      | invalido      | nao encontrado    |
      | reparos adaptacoes   | lista         | lista ou permissao|
      | reparos adaptacoes   | valido        | detalhe ou permissao|
      | reparos adaptacoes   | invalido      | nao encontrado    |
      | utensilios cozinha   | lista         | lista ou permissao|
      | utensilios cozinha   | valido        | detalhe ou permissao|
      | utensilios cozinha   | invalido      | nao encontrado    |
      | utensilios mesa      | lista         | lista ou permissao|
      | utensilios mesa      | valido        | detalhe ou permissao|
      | utensilios mesa      | invalido      | nao encontrado    |

  Esquema do Cenario: Consultar formularios IMR por status
    Quando consulto formularios IMR com status "<status>"
    Entao a lista de formularios IMR retorna dados ou permissao negada
    Exemplos:
      | status                        |
      | EM_PREENCHIMENTO              |
      | NUTRIMANIFESTACAO_A_VALIDAR   |
      | APROVADO                      |
      | COM_COMENTARIOS_DE_CODAE      |
      | VALIDADO_POR_CODAE            |

  Cenario: Consultar formularios IMR com status invalido
    Quando consulto formularios IMR com status "STATUS_INVALIDO"
    Entao a consulta de formulario IMR retorna erro de status ou permissao negada

  Esquema do Cenario: Consultar recursos de formulario IMR por UUID
    Quando consulto o recurso de formulario IMR "<recurso>" com UUID "<identificador>"
    Entao o recurso de formulario IMR retorna "<resultado>"
    Exemplos:
      | recurso            | identificador | resultado          |
      | formulario         | valido        | detalhe ou permissao|
      | formulario         | invalido      | nao encontrado     |
      | respostas          | valido        | detalhe ou permissao|
      | respostas          | invalido      | nao encontrado     |
      | nao se aplica      | valido        | detalhe ou permissao|
      | nao se aplica      | invalido      | nao encontrado     |

  Cenario: Consultar dashboard de formularios IMR
    Quando consulto a consulta auxiliar IMR "dashboard"
    Entao a consulta auxiliar IMR retorna lista ou permissao negada

  Cenario: Consultar nomes de nutricionistas do IMR
    Quando consulto a consulta auxiliar IMR "nutricionistas"
    Entao a consulta auxiliar IMR retorna lista ou permissao negada
