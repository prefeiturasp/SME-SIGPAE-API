# language: pt
Funcionalidade: Validar grupos de inclusao de alimentacao normal

  Esquema do Cenario: Consultar pedidos com perfil correspondente
    Quando consulto grupos de inclusao normal na rota "<rota>" com perfil "<perfil>"
    Entao a consulta de grupos de inclusao normal retorna uma lista
    Exemplos:
      | rota | perfil |
      | minhas-solicitacoes/ | escola |

  Cenario: Consultar listagem com usuario configurado
    Quando consulto grupos de inclusao normal na rota "principal" com perfil "escola"
    Entao a consulta de grupos de inclusao normal retorna uma lista

  Cenario: Consultar grupo inexistente
    Quando consulto grupo de inclusao normal inexistente
    Entao grupos de inclusao normal retorna status 404

  Esquema do Cenario: Exigir autenticacao nos metodos disponiveis
    Quando executo "<metodo>" em grupos de inclusao normal na rota "<rota>" com acesso "<acesso>"
    Entao grupos de inclusao normal retorna status 401
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
      | PATCH | 00000000-0000-0000-0000-000000000000/codae-autoriza-pedido/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/codae-autoriza-pedido/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/codae-cancela-pedido/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/codae-cancela-pedido/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/codae-questiona-pedido/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/codae-questiona-pedido/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/diretoria-regional-nao-valida-pedido/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/diretoria-regional-nao-valida-pedido/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/diretoria-regional-valida-pedido/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/diretoria-regional-valida-pedido/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/escola-cancela-pedido-48h-antes/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/escola-cancela-pedido-48h-antes/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/inicio-pedido/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/inicio-pedido/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/marcar-conferida/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/marcar-conferida/ | invalido |
      | GET | 00000000-0000-0000-0000-000000000000/relatorio/ | ausente |
      | GET | 00000000-0000-0000-0000-000000000000/relatorio/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/terceirizada-responde-questionamento/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/terceirizada-responde-questionamento/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/terceirizada-toma-ciencia/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/terceirizada-toma-ciencia/ | invalido |
      | GET | minhas-solicitacoes/ | ausente |
      | GET | minhas-solicitacoes/ | invalido |

  Cenario: Consultar detalhe de grupo existente
    Quando consulto um grupo de inclusao normal existente para "detalhe"
    Entao o detalhe do grupo corresponde ao registro consultado

  Cenario: Gerar relatorio PDF de grupo existente
    Quando consulto um grupo de inclusao normal existente para "PDF"
    Entao o relatorio do grupo retorna um PDF
