# language: pt
Funcionalidade: Validar rotas de IMR
  Esquema do Cenario: Consultar catalogos de IMR
    Dado que estou autenticado como CODAE para consultar IMR
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
    Dado que estou autenticado como CODAE para consultar IMR
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
    Dado que estou autenticado como CODAE para consultar IMR
    Quando consulto formularios IMR com status "STATUS_INVALIDO"
    Entao a consulta de formulario IMR retorna erro de status ou permissao negada

  Esquema do Cenario: Consultar recursos de formulario IMR por UUID
    Dado que estou autenticado como CODAE para consultar IMR
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
    Dado que estou autenticado como CODAE para consultar IMR
    Quando consulto a consulta auxiliar IMR "dashboard"
    Entao a consulta auxiliar IMR retorna lista ou permissao negada

  Cenario: Consultar nomes de nutricionistas do IMR
    Dado que estou autenticado como CODAE para consultar IMR
    Quando consulto a consulta auxiliar IMR "nutricionistas"
    Entao a consulta auxiliar IMR retorna lista ou permissao negada

  Esquema do Cenario: Validar parametros de tipos de ocorrencias com perfil autorizado
    Quando consulto IMR na rota "<rota>" com parametro "edital_uuid" igual a "<edital>"
    Entao IMR retorna status 400
    Exemplos:
      | rota | edital |
      | formulario-supervisao/tipos-ocorrencias/ | 00000000-0000-0000-0000-000000000000 |
      | formulario-supervisao/tipos-ocorrencias/ | uuid-invalido |
      | formulario-diretor/tipos-ocorrencias/ | 00000000-0000-0000-0000-000000000000 |
      | formulario-diretor/tipos-ocorrencias/ | uuid-invalido |

  Esquema do Cenario: Exigir campos obrigatorios nos formularios
    Quando executo "POST" em IMR na rota "<rota>" com acesso "autenticado"
    Entao IMR retorna status 400
    E IMR informa erro no campo "<campo>"
    Exemplos:
      | rota | campo |
      | formulario-supervisao/ | escola |
      | rascunho-formulario-supervisao/ | escola |
      | formulario-diretor/ | datas |

  Esquema do Cenario: Validar filtros de formularios com perfil autorizado
    Quando consulto IMR na rota "formulario-supervisao/" com parametro "<parametro>" igual a "<valor>"
    Entao IMR retorna status 400
    E IMR informa erro no campo "<parametro>"
    Exemplos:
      | parametro | valor |
      | status | STATUS_INVALIDO |
      | data_inicial | data-invalida |
      | data_final | data-invalida |

  Esquema do Cenario: Consultar catalogos por edital sem vinculos
    Quando consulto IMR na rota "<rota>" com parametro "edital_uuid" igual a "00000000-0000-0000-0000-000000000000"
    Entao IMR retorna status 200
    E IMR retorna resultados vazios
    Exemplos:
      | rota |
      | equipamentos/ |
      | insumos/ |
      | mobiliarios/ |
      | reparos-e-adaptacoes/ |
      | utensilios-cozinha/ |
      | utensilios-mesa/ |

  Esquema do Cenario: Consultar relatorios inexistentes com perfil autorizado
    Quando executo "GET" em IMR na rota "formulario-supervisao/00000000-0000-0000-0000-000000000000/<recurso>/" com acesso "autenticado"
    Entao IMR retorna status 404
    Exemplos:
      | recurso |
      | relatorio-pdf |
      | gerar-relatorio-notificacoes |

  Esquema do Cenario: Consultar formularios inexistentes com perfil autorizado
    Quando executo "GET" em IMR na rota "formulario-supervisao/00000000-0000-0000-0000-000000000000/<recurso>" com acesso "autenticado"
    Entao IMR retorna status 404
    Exemplos:
      | recurso |
      | |
      | respostas/ |
      | respostas_nao_se_aplica/ |

  Esquema do Cenario: Rejeitar escrita em catalogos somente leitura
    Quando executo "POST" em IMR na rota "<rota>" com acesso "autenticado"
    Entao IMR retorna status 405
    Exemplos:
      | rota |
      | equipamentos/ |
      | insumos/ |
      | mobiliarios/ |
      | periodos-de-visita/ |
      | reparos-e-adaptacoes/ |
      | utensilios-cozinha/ |
      | utensilios-mesa/ |

  Esquema do Cenario: Rejeitar alteracao de rascunho inexistente
    Quando executo "<metodo>" em IMR na rota "rascunho-formulario-supervisao/00000000-0000-0000-0000-000000000000/" com acesso "autenticado"
    Entao IMR retorna status 404
    Exemplos:
      | metodo |
      | PUT |
      | PATCH |
      | DELETE |

  Esquema do Cenario: Exigir autenticacao em todas as operacoes documentadas de IMR
    Quando executo "<metodo>" em IMR na rota "<rota>" com acesso "<acesso>"
    Entao IMR retorna status 401
    Exemplos:
      | metodo | rota | acesso |
      | GET | equipamentos/ | ausente |
      | GET | equipamentos/ | invalido |
      | GET | equipamentos/00000000-0000-0000-0000-000000000000/ | ausente |
      | GET | equipamentos/00000000-0000-0000-0000-000000000000/ | invalido |
      | POST | formulario-diretor/ | ausente |
      | POST | formulario-diretor/ | invalido |
      | PUT | formulario-diretor/00000000-0000-0000-0000-000000000000/ | ausente |
      | PUT | formulario-diretor/00000000-0000-0000-0000-000000000000/ | invalido |
      | PATCH | formulario-diretor/00000000-0000-0000-0000-000000000000/ | ausente |
      | PATCH | formulario-diretor/00000000-0000-0000-0000-000000000000/ | invalido |
      | GET | formulario-diretor/tipos-ocorrencias/ | ausente |
      | GET | formulario-diretor/tipos-ocorrencias/ | invalido |
      | GET | formulario-supervisao/ | ausente |
      | GET | formulario-supervisao/ | invalido |
      | POST | formulario-supervisao/ | ausente |
      | POST | formulario-supervisao/ | invalido |
      | GET | formulario-supervisao/00000000-0000-0000-0000-000000000000/ | ausente |
      | GET | formulario-supervisao/00000000-0000-0000-0000-000000000000/ | invalido |
      | PUT | formulario-supervisao/00000000-0000-0000-0000-000000000000/ | ausente |
      | PUT | formulario-supervisao/00000000-0000-0000-0000-000000000000/ | invalido |
      | PATCH | formulario-supervisao/00000000-0000-0000-0000-000000000000/ | ausente |
      | PATCH | formulario-supervisao/00000000-0000-0000-0000-000000000000/ | invalido |
      | GET | formulario-supervisao/00000000-0000-0000-0000-000000000000/gerar-relatorio-notificacoes/ | ausente |
      | GET | formulario-supervisao/00000000-0000-0000-0000-000000000000/gerar-relatorio-notificacoes/ | invalido |
      | GET | formulario-supervisao/00000000-0000-0000-0000-000000000000/relatorio-pdf/ | ausente |
      | GET | formulario-supervisao/00000000-0000-0000-0000-000000000000/relatorio-pdf/ | invalido |
      | GET | formulario-supervisao/00000000-0000-0000-0000-000000000000/respostas/ | ausente |
      | GET | formulario-supervisao/00000000-0000-0000-0000-000000000000/respostas/ | invalido |
      | GET | formulario-supervisao/00000000-0000-0000-0000-000000000000/respostas_nao_se_aplica/ | ausente |
      | GET | formulario-supervisao/00000000-0000-0000-0000-000000000000/respostas_nao_se_aplica/ | invalido |
      | GET | formulario-supervisao/dashboard/ | ausente |
      | GET | formulario-supervisao/dashboard/ | invalido |
      | GET | formulario-supervisao/lista_nomes_nutricionistas/ | ausente |
      | GET | formulario-supervisao/lista_nomes_nutricionistas/ | invalido |
      | GET | formulario-supervisao/tipos-ocorrencias/ | ausente |
      | GET | formulario-supervisao/tipos-ocorrencias/ | invalido |
      | GET | insumos/ | ausente |
      | GET | insumos/ | invalido |
      | GET | insumos/00000000-0000-0000-0000-000000000000/ | ausente |
      | GET | insumos/00000000-0000-0000-0000-000000000000/ | invalido |
      | GET | mobiliarios/ | ausente |
      | GET | mobiliarios/ | invalido |
      | GET | mobiliarios/00000000-0000-0000-0000-000000000000/ | ausente |
      | GET | mobiliarios/00000000-0000-0000-0000-000000000000/ | invalido |
      | GET | periodos-de-visita/ | ausente |
      | GET | periodos-de-visita/ | invalido |
      | GET | periodos-de-visita/00000000-0000-0000-0000-000000000000/ | ausente |
      | GET | periodos-de-visita/00000000-0000-0000-0000-000000000000/ | invalido |
      | POST | rascunho-formulario-supervisao/ | ausente |
      | POST | rascunho-formulario-supervisao/ | invalido |
      | PUT | rascunho-formulario-supervisao/00000000-0000-0000-0000-000000000000/ | ausente |
      | PUT | rascunho-formulario-supervisao/00000000-0000-0000-0000-000000000000/ | invalido |
      | PATCH | rascunho-formulario-supervisao/00000000-0000-0000-0000-000000000000/ | ausente |
      | PATCH | rascunho-formulario-supervisao/00000000-0000-0000-0000-000000000000/ | invalido |
      | DELETE | rascunho-formulario-supervisao/00000000-0000-0000-0000-000000000000/ | ausente |
      | DELETE | rascunho-formulario-supervisao/00000000-0000-0000-0000-000000000000/ | invalido |
      | GET | reparos-e-adaptacoes/ | ausente |
      | GET | reparos-e-adaptacoes/ | invalido |
      | GET | reparos-e-adaptacoes/00000000-0000-0000-0000-000000000000/ | ausente |
      | GET | reparos-e-adaptacoes/00000000-0000-0000-0000-000000000000/ | invalido |
      | GET | utensilios-cozinha/ | ausente |
      | GET | utensilios-cozinha/ | invalido |
      | GET | utensilios-cozinha/00000000-0000-0000-0000-000000000000/ | ausente |
      | GET | utensilios-cozinha/00000000-0000-0000-0000-000000000000/ | invalido |
      | GET | utensilios-mesa/ | ausente |
      | GET | utensilios-mesa/ | invalido |
      | GET | utensilios-mesa/00000000-0000-0000-0000-000000000000/ | ausente |
      | GET | utensilios-mesa/00000000-0000-0000-0000-000000000000/ | invalido |
