# language: pt
Funcionalidade: Validar horario do combo tipo de alimentacao por unidade escolar

  Cenario: Consultar listagem paginada de horarios
    Quando consulto a listagem de horarios do combo por unidade escolar
    Entao horarios do combo retorna status 200
    E horarios do combo retorna uma lista paginada valida

  Cenario: Consultar detalhe de horario existente
    Quando consulto o detalhe de um horario do combo existente
    Entao horarios do combo retorna status 200
    E o detalhe do horario do combo corresponde ao registro consultado

  Cenario: Consultar horarios por escola existente
    Quando consulto horarios do combo por escola "existente"
    Entao horarios do combo retorna status 200
    E horarios do combo retorna uma lista paginada valida
    E os horarios do combo pertencem a escola consultada

  Cenario: Consultar horarios por escola inexistente
    Quando consulto horarios do combo por escola "inexistente"
    Entao horarios do combo retorna status 200
    E horarios do combo retorna uma lista paginada valida
    E horarios do combo retorna uma lista vazia

  Cenario: Validar campos obrigatorios no cadastro de horario
    Quando executo "POST" em horarios do combo na rota "principal" com acesso "autenticado"
    Entao horarios do combo retorna status 400
    E horarios do combo informa os campos obrigatorios

  Esquema do Cenario: Rejeitar operacoes em horario inexistente ou UUID malformado
    Quando executo "<metodo>" em horarios do combo na rota "<rota>" com acesso "autenticado"
    Entao horarios do combo retorna status 404
    Exemplos:
      | metodo | rota |
      | GET | 00000000-0000-0000-0000-000000000000/ |
      | GET | uuid-invalido/ |
      | PUT | 00000000-0000-0000-0000-000000000000/ |
      | PATCH | 00000000-0000-0000-0000-000000000000/ |
      | DELETE | 00000000-0000-0000-0000-000000000000/ |

  Esquema do Cenario: Exigir autenticacao nos metodos disponiveis
    Quando executo "<metodo>" em horarios do combo na rota "<rota>" com acesso "<acesso>"
    Entao horarios do combo retorna status 401
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
      | GET | escola/00000000-0000-0000-0000-000000000000/ | ausente |
      | GET | escola/00000000-0000-0000-0000-000000000000/ | invalido |
