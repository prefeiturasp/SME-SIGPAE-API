# language: pt
Funcionalidade: Validar informacoes nutricionais
  Cenario: Consultar lista de informacoes nutricionais
    Dado que estou autenticado como CODAE para consultar informacoes nutricionais
    Quando consulto a lista de informacoes nutricionais
    Entao a lista de informacoes nutricionais retorna dados validos
  Cenario: Consultar informacao nutricional por UUID valido
    Dado que estou autenticado como CODAE para consultar informacoes nutricionais
    Quando consulto uma informacao nutricional existente por UUID
    Entao a informacao nutricional retorna os dados esperados
  Cenario: Consultar informacao nutricional por UUID invalido
    Dado que estou autenticado como CODAE para consultar informacoes nutricionais
    Quando consulto uma informacao nutricional por UUID invalido
    Entao a informacao nutricional retorna status 404
  Cenario: Consultar informacoes nutricionais agrupadas
    Dado que estou autenticado como CODAE para consultar informacoes nutricionais
    Quando consulto as informacoes nutricionais agrupadas
    Entao as informacoes agrupadas retornam dados validos
  Cenario: Consultar informacoes nutricionais ordenadas
    Dado que estou autenticado como CODAE para consultar informacoes nutricionais
    Quando consulto as informacoes nutricionais ordenadas
    Entao as informacoes ordenadas retornam dados validos

  Cenario: Consultar UUID valido inexistente
    Quando executo "GET" em informacoes nutricionais na rota "00000000-0000-0000-0000-000000000000/" com acesso "autenticado"
    Entao informacoes nutricionais retorna status 404

  Esquema do Cenario: Filtrar informacoes por situacao
    Quando consulto informacoes nutricionais na rota "<rota>" com ativo "<ativo>"
    Entao informacoes nutricionais retorna status 200
    E as informacoes nutricionais correspondem ao filtro ativo
    Exemplos:
      | rota | ativo |
      | principal | true |
      | principal | false |
      | ordenadas/ | true |
      | ordenadas/ | false |

  Esquema do Cenario: Filtrar informacoes agrupadas por situacao
    Quando consulto informacoes nutricionais na rota "agrupadas/" com ativo "<ativo>"
    Entao informacoes nutricionais retorna status 200
    E as informacoes agrupadas correspondem ao filtro ativo
    Exemplos:
      | ativo |
      | true |
      | false |

  Esquema do Cenario: Validar paginacao
    Quando consulto informacoes nutricionais com limite 2 e deslocamento <offset>
    Entao informacoes nutricionais retorna status 200
    E a paginacao de informacoes nutricionais respeita o limite
    Exemplos:
      | offset |
      | 0 |
      | 2 |

  Esquema do Cenario: Rejeitar metodos de escrita
    Quando executo "<metodo>" em informacoes nutricionais na rota "<rota>" com acesso "autenticado"
    Entao informacoes nutricionais retorna status 405
    Exemplos:
      | metodo | rota |
      | POST | principal |
      | PUT | 00000000-0000-0000-0000-000000000000/ |
      | PATCH | 00000000-0000-0000-0000-000000000000/ |
      | DELETE | 00000000-0000-0000-0000-000000000000/ |
      | POST | agrupadas/ |
      | POST | ordenadas/ |

  Esquema do Cenario: Exigir autenticacao nas quatro rotas
    Quando executo "GET" em informacoes nutricionais na rota "<rota>" com acesso "<acesso>"
    Entao informacoes nutricionais retorna status 401
    Exemplos:
      | rota | acesso |
      | principal | ausente |
      | principal | invalido |
      | 00000000-0000-0000-0000-000000000000/ | ausente |
      | 00000000-0000-0000-0000-000000000000/ | invalido |
      | agrupadas/ | ausente |
      | agrupadas/ | invalido |
      | ordenadas/ | ausente |
      | ordenadas/ | invalido |
