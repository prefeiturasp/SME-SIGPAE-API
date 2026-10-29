# language: pt
Funcionalidade: Validar painel de inclusao de alimentacao

  Esquema do Cenario: Consultar pedidos por perfil e periodo
    Quando consulto o painel de inclusao de alimentacao como "<perfil>" com filtro "<filtro>"
    Entao o painel de inclusao de alimentacao retorna status 200
    E o painel de inclusao de alimentacao retorna dados validos
    Exemplos:
      | perfil | filtro |
      | codae | sem_filtro |
      | dre | sem_filtro |

  Esquema do Cenario: Consultar pedidos por prazo
    Quando consulto o painel de inclusao de alimentacao como "<perfil>" com parametro "prazo" igual a "<prazo>"
    Entao o painel de inclusao de alimentacao retorna status 200
    E o painel de inclusao de alimentacao retorna dados validos
    Exemplos:
      | perfil | prazo |
      | codae | PRIORITARIO |
      | codae | LIMITE |
      | codae | REGULAR |
      | dre | PRIORITARIO |
      | dre | LIMITE |
      | dre | REGULAR |

  Esquema do Cenario: Consultar vinculos inexistentes
    Quando consulto o painel de inclusao de alimentacao como "<perfil>" com parametro "<parametro>" igual a "00000000-0000-0000-0000-000000000000"
    Entao o painel de inclusao de alimentacao retorna status 200
    E o painel de inclusao de alimentacao retorna dados validos
    E o painel de inclusao de alimentacao retorna lista vazia
    Exemplos:
      | perfil | parametro |
      | codae | lote |
      | codae | diretoria_regional |
      | dre | lote |
      | dre | diretoria_regional |

  Esquema do Cenario: Rejeitar pagina invalida
    Quando consulto o painel de inclusao de alimentacao como "<perfil>" com parametro "page" igual a "0"
    Entao o painel de inclusao de alimentacao retorna status 404
    Exemplos:
      | perfil |
      | codae |
      | dre |

  Esquema do Cenario: Negar acesso ao perfil escola
    Quando consulto o painel de inclusao de alimentacao de "<perfil>" com perfil escola
    Entao o painel de inclusao de alimentacao retorna status 403
    Exemplos:
      | perfil |
      | codae |
      | dre |

  Esquema do Cenario: Exigir autenticacao nas consultas
    Quando consulto o painel de inclusao de alimentacao na rota "<rota>" com acesso "<acesso>"
    Entao o painel de inclusao de alimentacao retorna status 401
    Exemplos:
      | rota | acesso |
      | pedidos-codae/sem_filtro/ | ausente |
      | pedidos-codae/sem_filtro/ | invalido |
      | pedidos-codae/daqui_a_7_dias/ | ausente |
      | pedidos-codae/daqui_a_7_dias/ | invalido |
      | pedidos-codae/daqui_a_30_dias/ | ausente |
      | pedidos-codae/daqui_a_30_dias/ | invalido |
      | pedidos-diretoria-regional/sem_filtro/ | ausente |
      | pedidos-diretoria-regional/sem_filtro/ | invalido |
      | pedidos-diretoria-regional/daqui_a_7_dias/ | ausente |
      | pedidos-diretoria-regional/daqui_a_7_dias/ | invalido |
      | pedidos-diretoria-regional/daqui_a_30_dias/ | ausente |
      | pedidos-diretoria-regional/daqui_a_30_dias/ | invalido |
