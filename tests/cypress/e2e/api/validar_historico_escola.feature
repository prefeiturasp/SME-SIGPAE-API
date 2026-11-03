# language: pt
Funcionalidade: Validar historico da escola

  Esquema do Cenario: Consultar historico de escola existente
    Quando consulto o historico de uma escola existente no mes <mes> e ano <ano>
    Entao historico escolar retorna status 200
    E o historico escolar retorna nome e tipo de unidade
    Exemplos:
      | mes | ano |
      | 1 | 2024 |
      | 12 | 2024 |

  Esquema do Cenario: Validar parametros obrigatorios e formato
    Quando consulto historico escolar com mes "<mes>" e ano "<ano>"
    Entao historico escolar retorna status 400
    E historico escolar informa erro de "<erro>"
    Exemplos:
      | mes | ano | erro |
      | ausente | ausente | obrigatorios |
      | ausente | 2024 | obrigatorios |
      | 1 | ausente | obrigatorios |
      | texto | 2024 | inteiros |
      | 1 | texto | inteiros |
      | 1.5 | 2024 | inteiros |
      | 1 | 2024.5 | inteiros |
      | 0 | 2024 | intervalo |
      | 13 | 2024 | intervalo |
      | -1 | 2024 | intervalo |

  Cenario: Consultar escola inexistente
    Quando executo "GET" em historico escolar com acesso "autenticado"
    Entao historico escolar retorna status 404

  Esquema do Cenario: Exigir autenticacao
    Quando executo "GET" em historico escolar com acesso "<acesso>"
    Entao historico escolar retorna status 401
    Exemplos:
      | acesso |
      | ausente |
      | invalido |

  Esquema do Cenario: Rejeitar metodos nao permitidos
    Quando executo "<metodo>" em historico escolar com acesso "autenticado"
    Entao historico escolar retorna status 405
    Exemplos:
      | metodo |
      | POST |
      | PUT |
      | PATCH |
      | DELETE |
