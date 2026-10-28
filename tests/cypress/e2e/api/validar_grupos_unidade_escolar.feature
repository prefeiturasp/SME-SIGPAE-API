# language: pt
Funcionalidade: Validar grupos de unidade escolar

  Cenario: Consultar listagem paginada
    Quando consulto a listagem de grupos de unidade escolar
    Entao grupos de unidade escolar retorna status 200
    E grupos de unidade escolar retorna uma lista paginada valida

  Cenario: Consultar detalhe de grupo existente
    Quando consulto o detalhe de um grupo de unidade escolar existente
    Entao grupos de unidade escolar retorna status 200
    E o detalhe de unidade escolar corresponde ao grupo consultado

  Cenario: Consultar grupos por DRE existente
    Quando consulto grupos de unidade escolar por DRE "existente"
    Entao grupos de unidade escolar retorna status 200
    E a consulta de grupos por DRE retorna habilitacao dos grupos

  Esquema do Cenario: Validar parametro DRE
    Quando consulto grupos de unidade escolar por DRE "<dre>"
    Entao grupos de unidade escolar retorna status <status>
    Exemplos:
      | dre | status |
      | ausente | 400 |
      | inexistente | 404 |

  Esquema do Cenario: Consultar grupo inexistente ou UUID malformado
    Quando executo "GET" em grupos de unidade escolar na rota "<rota>" com acesso "autenticado"
    Entao grupos de unidade escolar retorna status 404
    Exemplos:
      | rota |
      | 00000000-0000-0000-0000-000000000000/ |
      | uuid-invalido/ |

  Esquema do Cenario: Exigir autenticacao nos metodos disponiveis
    Quando executo "<metodo>" em grupos de unidade escolar na rota "<rota>" com acesso "<acesso>"
    Entao grupos de unidade escolar retorna status 401
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
      | DELETE | 00000000-0000-0000-0000-000000000000/ | ausente |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | invalido |
      | GET | por-dre/ | ausente |
      | GET | por-dre/ | invalido |
