# language: pt
Funcionalidade: Validar inclusoes de alimentacao continua

  Esquema do Cenario: Consultar inclusoes continuas
    Quando consulto inclusoes de alimentacao continua na rota "<rota>"
    Entao inclusoes de alimentacao continua retorna status 200
    E inclusoes de alimentacao continua retorna lista paginada valida
    Exemplos:
      | rota |
      | principal |
      | minhas-solicitacoes/ |

  Cenario: Consultar detalhe de inclusao continua existente
    Quando consulto uma inclusao de alimentacao continua existente para "detalhe"
    Entao inclusoes de alimentacao continua retorna status 200
    E o detalhe da inclusao continua corresponde ao registro consultado

  Cenario: Consultar relatorio de inclusao continua existente
    Quando consulto uma inclusao de alimentacao continua existente para "PDF"
    Entao inclusoes de alimentacao continua retorna status 200
    E o relatorio da inclusao continua retorna PDF valido

  Cenario: Exigir campos obrigatorios no cadastro
    Quando executo "POST" em inclusoes de alimentacao continua na rota "principal" com acesso "autenticado"
    Entao inclusoes de alimentacao continua retorna status 400
    E inclusoes de alimentacao continua informa campos obrigatorios

  Esquema do Cenario: Rejeitar operacoes em inclusao inexistente ou UUID malformado
    Quando executo "<metodo>" em inclusoes de alimentacao continua na rota "<rota>" com acesso "autenticado"
    Entao inclusoes de alimentacao continua retorna status 404
    Exemplos:
      | metodo | rota |
      | GET | 00000000-0000-0000-0000-000000000000/ |
      | GET | uuid-invalido/ |
      | GET | 00000000-0000-0000-0000-000000000000/relatorio/ |
      | PUT | 00000000-0000-0000-0000-000000000000/ |
      | PATCH | 00000000-0000-0000-0000-000000000000/ |
      | DELETE | 00000000-0000-0000-0000-000000000000/ |

  Esquema do Cenario: Exigir autenticacao nas operacoes disponiveis
    Quando executo "<metodo>" em inclusoes de alimentacao continua na rota "<rota>" com acesso "<acesso>"
    Entao inclusoes de alimentacao continua retorna status 401
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
