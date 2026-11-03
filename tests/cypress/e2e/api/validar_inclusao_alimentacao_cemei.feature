# language: pt
Funcionalidade: Validar inclusao de alimentacao CEMEI

  Esquema do Cenario: Consultar listagem por perfil
    Quando consulto inclusoes de alimentacao CEMEI com perfil "<perfil>"
    Entao inclusao de alimentacao CEMEI retorna status 200
    E inclusao de alimentacao CEMEI retorna lista paginada valida
    Exemplos:
      | perfil |
      | escola |
      | codae |
      | dre |

  Esquema do Cenario: Filtrar inclusoes por status
    Quando consulto inclusoes de alimentacao CEMEI com status "<status>"
    Entao inclusao de alimentacao CEMEI retorna status 200
    E inclusao de alimentacao CEMEI retorna lista paginada valida
    E as inclusoes CEMEI correspondem ao status consultado
    Exemplos:
      | status |
      | DRE_A_VALIDAR |
      | dre_a_validar |

  Cenario: Consultar detalhe de inclusao existente
    Quando consulto uma inclusao de alimentacao CEMEI existente para "detalhe"
    Entao inclusao de alimentacao CEMEI retorna status 200
    E o detalhe da inclusao CEMEI corresponde ao registro consultado

  Cenario: Consultar relatorio de inclusao existente
    Quando consulto uma inclusao de alimentacao CEMEI existente para "PDF"
    Entao inclusao de alimentacao CEMEI retorna status 200
    E o relatorio da inclusao CEMEI retorna um PDF

  Cenario: Exigir campos obrigatorios no cadastro
    Quando executo "POST" em inclusao de alimentacao CEMEI na rota "principal" com acesso "autenticado"
    Entao inclusao de alimentacao CEMEI retorna status 400
    E inclusao de alimentacao CEMEI informa os campos obrigatorios

  Esquema do Cenario: Consultar inclusao inexistente ou UUID malformado
    Quando executo "GET" em inclusao de alimentacao CEMEI na rota "<rota>" com acesso "autenticado"
    Entao inclusao de alimentacao CEMEI retorna status 404
    Exemplos:
      | rota |
      | 00000000-0000-0000-0000-000000000000/ |
      | uuid-invalido/ |
      | 00000000-0000-0000-0000-000000000000/relatorio/ |

  Esquema do Cenario: Exigir autenticacao nas operacoes documentadas
    Quando executo "<metodo>" em inclusao de alimentacao CEMEI na rota "<rota>" com acesso "<acesso>"
    Entao inclusao de alimentacao CEMEI retorna status 401
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
