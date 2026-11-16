# language: pt
@inversoes_dia_cardapio
Funcionalidade: Validar inversoes de dia de cardapio por perfil

  @perfis_inversoes @perfil_coordenador_logistica
  Esquema do Cenario: Validar acesso de inversoes com usuario COORDENADOR_LOGISTICA
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "COORDENADOR_LOGISTICA"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 403 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_inversoes @perfil_coordenador_codae_dilog_logistica
  Esquema do Cenario: Validar acesso de inversoes com usuario COORDENADOR_CODAE_DILOG_LOGISTICA
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "COORDENADOR_CODAE_DILOG_LOGISTICA"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 403 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_inversoes @perfil_coordenador_supervisao_nutricao
  Esquema do Cenario: Validar acesso de inversoes com usuario COORDENADOR_SUPERVISAO_NUTRICAO
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "COORDENADOR_SUPERVISAO_NUTRICAO"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 403 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_inversoes @perfil_dilog_cronograma
  Esquema do Cenario: Validar acesso de inversoes com usuario DILOG_CRONOGRAMA
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "DILOG_CRONOGRAMA"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 403 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_inversoes @perfil_dilog_qualidade
  Esquema do Cenario: Validar acesso de inversoes com usuario DILOG_QUALIDADE
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "DILOG_QUALIDADE"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 403 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_inversoes @perfil_abastecimento
  Esquema do Cenario: Validar acesso de inversoes com usuario ABASTECIMENTO
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "ABASTECIMENTO"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 403 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_inversoes @perfil_diretor_ue
  Esquema do Cenario: Validar acesso de inversoes com usuario DIRETOR_UE
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "DIRETOR_UE"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 200 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 400 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_inversoes @perfil_codae
  Esquema do Cenario: Validar acesso de inversoes com usuario CODAE
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "CODAE"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 403 |
      | GET | pedidos-codae/sem_filtro/ | 200 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_inversoes @perfil_gpcodae
  Esquema do Cenario: Validar acesso de inversoes com usuario GPCODAE
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "GPCODAE"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 403 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_inversoes @perfil_dre
  Esquema do Cenario: Validar acesso de inversoes com usuario DRE
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "DRE"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 403 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 200 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_inversoes @perfil_classificacoes_dieta
  Esquema do Cenario: Validar acesso de inversoes com usuario CLASSIFICACOES_DIETA
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "CLASSIFICACOES_DIETA"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 403 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_inversoes @perfil_usuario_escola_cei_admin
  Esquema do Cenario: Validar acesso de inversoes com usuario USUARIO_ESCOLA_CEI_ADMIN
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "USUARIO_ESCOLA_CEI_ADMIN"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 200 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 400 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_inversoes @perfil_medicao
  Esquema do Cenario: Validar acesso de inversoes com usuario MEDICAO
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "MEDICAO"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 403 |
      | GET | pedidos-codae/sem_filtro/ | 200 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_inversoes @perfil_distribuidor
  Esquema do Cenario: Validar acesso de inversoes com usuario DISTRIBUIDOR
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "DISTRIBUIDOR"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 403 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 200 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_inversoes @perfil_emef
  Esquema do Cenario: Validar acesso de inversoes com usuario EMEF
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "EMEF"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 200 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 400 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_inversoes @perfil_cemei
  Esquema do Cenario: Validar acesso de inversoes com usuario CEMEI
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "CEMEI"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 200 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 400 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_inversoes @perfil_cei
  Esquema do Cenario: Validar acesso de inversoes com usuario CEI
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "CEI"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 200 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 400 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_inversoes @perfil_cci
  Esquema do Cenario: Validar acesso de inversoes com usuario CCI
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "CCI"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 200 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 400 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_inversoes @perfil_dilog_diretoria
  Esquema do Cenario: Validar acesso de inversoes com usuario DILOG_DIRETORIA
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "DILOG_DIRETORIA"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 403 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_inversoes @perfil_administrador_empresa
  Esquema do Cenario: Validar acesso de inversoes com usuario ADMINISTRADOR_EMPRESA
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "ADMINISTRADOR_EMPRESA"
    Entao inversoes de cardapio retorna status <status>
    E inversoes de cardapio valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | minhas-solicitacoes/ | 403 |
      | GET | pedidos-codae/sem_filtro/ | 403 |
      | GET | pedidos-diretoria-regional/sem_filtro/ | 403 |
      | GET | pedidos-terceirizadas/sem_filtro/ | 200 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @fluxo_inversoes
  Esquema do Cenario: Validar permissao das acoes do fluxo por perfil
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "<perfil>"
    Entao inversoes de cardapio retorna status <status>
    Exemplos:
      | metodo | rota | perfil | status |
      | PATCH | 00000000-0000-0000-0000-000000000000/inicio-pedido/ | DIRETOR_UE | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/inicio-pedido/ | CODAE | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/escola-cancela-pedido-48h-antes/ | DIRETOR_UE | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/escola-cancela-pedido-48h-antes/ | CODAE | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/diretoria-regional-valida-pedido/ | DRE | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/diretoria-regional-valida-pedido/ | DIRETOR_UE | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/diretoria-regional-nao-valida-pedido/ | DRE | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/diretoria-regional-nao-valida-pedido/ | DIRETOR_UE | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/codae-autoriza-pedido/ | CODAE | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/codae-autoriza-pedido/ | DIRETOR_UE | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/codae-questiona-pedido/ | CODAE | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/codae-questiona-pedido/ | DIRETOR_UE | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/codae-cancela-pedido/ | CODAE | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/codae-cancela-pedido/ | DIRETOR_UE | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/terceirizada-responde-questionamento/ | ADMINISTRADOR_EMPRESA | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/terceirizada-responde-questionamento/ | DIRETOR_UE | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/terceirizada-toma-ciencia/ | ADMINISTRADOR_EMPRESA | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/terceirizada-toma-ciencia/ | DIRETOR_UE | 403 |

  Esquema do Cenario: Rejeitar registro inexistente e UUID malformado
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com perfil "MEDICAO"
    Entao inversoes de cardapio retorna status 404
    Exemplos:
      | metodo | rota |
      | GET | 00000000-0000-0000-0000-000000000000/ |
      | GET | uuid-invalido/ |
      | GET | 00000000-0000-0000-0000-000000000000/relatorio/ |
      | PATCH | 00000000-0000-0000-0000-000000000000/marcar-conferida/ |
      | PUT | 00000000-0000-0000-0000-000000000000/ |
      | PATCH | 00000000-0000-0000-0000-000000000000/ |

  @perfil_medicao
  Cenario: Consultar listagem geral com perfil Medicao
    Quando executo "GET" em inversoes de cardapio na rota "principal" com perfil "MEDICAO"
    Entao inversoes de cardapio retorna status 200
    E inversoes de cardapio valida o retorno permitido para o perfil

  @perfil_medicao
  Cenario: Consultar detalhe com perfil Medicao
    Quando consulto inversao de cardapio existente para "detalhe" com perfil "MEDICAO"
    Entao inversoes de cardapio retorna status 200
    E o detalhe da inversao de cardapio corresponde ao registro consultado

  @perfil_medicao
  Cenario: Consultar PDF com perfil Medicao
    Quando consulto inversao de cardapio existente para "PDF" com perfil "MEDICAO"
    Entao inversoes de cardapio retorna status 200
    E o relatorio da inversao de cardapio retorna PDF valido

  @autenticacao_inversoes
  Esquema do Cenario: Exigir autenticacao em todas as rotas
    Quando executo "<metodo>" em inversoes de cardapio na rota "<rota>" com acesso "<acesso>"
    Entao inversoes de cardapio retorna status 401
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
      | GET | pedidos-codae/sem_filtro/ | ausente |
      | GET | pedidos-codae/sem_filtro/ | invalido |
      | GET | pedidos-diretoria-regional/sem_filtro/ | ausente |
      | GET | pedidos-diretoria-regional/sem_filtro/ | invalido |
      | GET | pedidos-terceirizadas/sem_filtro/ | ausente |
      | GET | pedidos-terceirizadas/sem_filtro/ | invalido |
