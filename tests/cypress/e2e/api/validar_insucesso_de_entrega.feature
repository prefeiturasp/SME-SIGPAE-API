# language: pt
Funcionalidade: Validar insucesso de entrega

  Cenario: Consultar listagem paginada
    Quando consulto a listagem de insucesso de entrega
    Entao insucesso de entrega retorna status 200
    E insucesso de entrega retorna lista paginada valida

  Cenario: Consultar detalhe de insucesso existente
    Quando consulto o detalhe de um insucesso de entrega existente
    Entao insucesso de entrega retorna status 200
    E o detalhe do insucesso de entrega corresponde ao registro consultado

  Cenario: Exigir campos obrigatorios no cadastro
    Quando executo "POST" em insucesso de entrega na rota "principal" com acesso "distribuidor"
    Entao insucesso de entrega retorna status 400
    E insucesso de entrega informa os campos obrigatorios

  Esquema do Cenario: Rejeitar registro inexistente ou UUID malformado
    Quando executo "<metodo>" em insucesso de entrega na rota "<rota>" com acesso "distribuidor"
    Entao insucesso de entrega retorna status 404
    Exemplos:
      | metodo | rota |
      | GET | 00000000-0000-0000-0000-000000000000/ |
      | GET | uuid-invalido/ |
      | PUT | 00000000-0000-0000-0000-000000000000/ |
      | PATCH | 00000000-0000-0000-0000-000000000000/ |
      | DELETE | 00000000-0000-0000-0000-000000000000/ |

  Esquema do Cenario: Negar operacoes ao perfil escola
    Quando executo "<metodo>" em insucesso de entrega na rota "<rota>" com acesso "escola"
    Entao insucesso de entrega retorna status 403
    Exemplos:
      | metodo | rota |
      | GET | principal |
      | POST | principal |
      | GET | 00000000-0000-0000-0000-000000000000/ |
      | PUT | 00000000-0000-0000-0000-000000000000/ |
      | PATCH | 00000000-0000-0000-0000-000000000000/ |
      | DELETE | 00000000-0000-0000-0000-000000000000/ |

  Esquema do Cenario: Exigir autenticacao nos metodos disponiveis
    Quando executo "<metodo>" em insucesso de entrega na rota "<rota>" com acesso "<acesso>"
    Entao insucesso de entrega retorna status 401
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
