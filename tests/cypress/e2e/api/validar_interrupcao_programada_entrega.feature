# language: pt
Funcionalidade: Validar interrupcao programada de entrega

  Cenario: Consultar listagem paginada
    Quando consulto interrupcao programada de entrega na rota "principal"
    Entao interrupcao programada retorna status 200
    E interrupcao programada retorna lista paginada valida

  Cenario: Consultar motivos disponiveis
    Quando consulto interrupcao programada de entrega na rota "motivos/"
    Entao interrupcao programada retorna status 200
    E interrupcao programada retorna motivos sem feriado

  Cenario: Consultar datas bloqueadas armazenaveis
    Quando consulto interrupcao programada de entrega na rota "datas-bloqueadas-armazenavel/"
    Entao interrupcao programada retorna status 200
    E interrupcao programada retorna datas bloqueadas validas

  Esquema do Cenario: Filtrar listagem por motivo e calendario
    Quando filtro interrupcoes programadas por "<campo>" igual a "<valor>"
    Entao interrupcao programada retorna status 200
    E interrupcao programada retorna lista paginada valida
    E as interrupcoes correspondem ao filtro consultado
    Exemplos:
      | campo | valor |
      | motivo | REUNIAO |
      | motivo | INVENTARIO |
      | motivo | OUTROS |
      | tipo_calendario | ARMAZENAVEL |
      | tipo_calendario | PONTO_A_PONTO |

  Esquema do Cenario: Validar campos no cadastro
    Quando cadastro interrupcao programada com dados "<caso>"
    Entao interrupcao programada retorna status 400
    E interrupcao programada informa erro no campo "<campo>"
    Exemplos:
      | caso | campo |
      | vazios | data |
      | vazios | motivo |
      | data invalida | data |
      | motivo invalido | motivo |
      | calendario invalido | tipo_calendario |
      | outros sem descricao | descricao_motivo |

  Esquema do Cenario: Rejeitar exclusao de registro inexistente ou UUID malformado
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com acesso "cronograma"
    Entao interrupcao programada retorna status 404
    Exemplos:
      | metodo | rota |
      | DELETE | 00000000-0000-0000-0000-000000000000/ |
      | DELETE | uuid-invalido/ |

  Esquema do Cenario: Rejeitar metodos indisponiveis no detalhe
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com acesso "cronograma"
    Entao interrupcao programada retorna status 405
    Exemplos:
      | metodo | rota |
      | GET | 00000000-0000-0000-0000-000000000000/ |
      | PUT | 00000000-0000-0000-0000-000000000000/ |
      | PATCH | 00000000-0000-0000-0000-000000000000/ |

  Esquema do Cenario: Exigir autenticacao nas operacoes disponiveis
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com acesso "<acesso>"
    Entao interrupcao programada retorna status 401
    Exemplos:
      | metodo | rota | acesso |
      | GET | principal | ausente |
      | GET | principal | invalido |
      | POST | principal | ausente |
      | POST | principal | invalido |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | ausente |s
      | DELETE | 00000000-0000-0000-0000-000000000000/ | invalido |
      | GET | motivos/ | ausente |
      | GET | motivos/ | invalido |
      | GET | datas-bloqueadas-armazenavel/ | ausente |
      | GET | datas-bloqueadas-armazenavel/ | invalido |

  @perfis @perfil_coordenador_logistica
  # Vinculo: COORDENADOR_LOGISTICA
  Esquema do Cenario: Validar acesso do usuario COORDENADOR_LOGISTICA
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com perfil "COORDENADOR_LOGISTICA"
    Entao interrupcao programada retorna status <status>
    E interrupcao programada valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | motivos/ | 403 |
      | GET | datas-bloqueadas-armazenavel/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis @perfil_coordenador_codae_dilog_logistica
  # Vinculo: COORDENADOR_CODAE_DILOG_LOGISTICA
  Esquema do Cenario: Validar acesso do usuario COORDENADOR_CODAE_DILOG_LOGISTICA
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com perfil "COORDENADOR_CODAE_DILOG_LOGISTICA"
    Entao interrupcao programada retorna status <status>
    E interrupcao programada valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | motivos/ | 200 |
      | GET | datas-bloqueadas-armazenavel/ | 200 |
      | POST | principal | 400 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis @perfil_coordenador_supervisao_nutricao
  # Vinculo: ADMINISTRADOR_SUPERVISAO_NUTRICAO
  Esquema do Cenario: Validar acesso do usuario COORDENADOR_SUPERVISAO_NUTRICAO
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com perfil "COORDENADOR_SUPERVISAO_NUTRICAO"
    Entao interrupcao programada retorna status <status>
    E interrupcao programada valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | motivos/ | 403 |
      | GET | datas-bloqueadas-armazenavel/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis @perfil_dilog_cronograma
  # Vinculo: DILOG_CRONOGRAMA
  Esquema do Cenario: Validar acesso do usuario DILOG_CRONOGRAMA
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com perfil "DILOG_CRONOGRAMA"
    Entao interrupcao programada retorna status <status>
    E interrupcao programada valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | motivos/ | 200 |
      | GET | datas-bloqueadas-armazenavel/ | 200 |
      | POST | principal | 400 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis @perfil_dilog_qualidade
  # Vinculo: DILOG_QUALIDADE
  Esquema do Cenario: Validar acesso do usuario DILOG_QUALIDADE
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com perfil "DILOG_QUALIDADE"
    Entao interrupcao programada retorna status <status>
    E interrupcao programada valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | motivos/ | 200 |
      | GET | datas-bloqueadas-armazenavel/ | 200 |
      | POST | principal | 400 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis @perfil_abastecimento
  # Vinculo: ADMINISTRADOR_UE
  Esquema do Cenario: Validar acesso do usuario ABASTECIMENTO
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com perfil "ABASTECIMENTO"
    Entao interrupcao programada retorna status <status>
    E interrupcao programada valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | motivos/ | 403 |
      | GET | datas-bloqueadas-armazenavel/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis @perfil_diretor_ue
  # Vinculo: DIRETOR_UE
  Esquema do Cenario: Validar acesso do usuario DIRETOR_UE
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com perfil "DIRETOR_UE"
    Entao interrupcao programada retorna status <status>
    E interrupcao programada valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | motivos/ | 403 |
      | GET | datas-bloqueadas-armazenavel/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis @perfil_codae
  # Vinculo: COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA
  Esquema do Cenario: Validar acesso do usuario CODAE
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com perfil "CODAE"
    Entao interrupcao programada retorna status <status>
    E interrupcao programada valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | motivos/ | 403 |
      | GET | datas-bloqueadas-armazenavel/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis @perfil_gpcodae
  # Vinculo: COORDENADOR_GESTAO_PRODUTO
  Esquema do Cenario: Validar acesso do usuario GPCODAE
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com perfil "GPCODAE"
    Entao interrupcao programada retorna status <status>
    E interrupcao programada valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | motivos/ | 403 |
      | GET | datas-bloqueadas-armazenavel/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis @perfil_dre
  # Vinculo: COGESTOR_DRE
  Esquema do Cenario: Validar acesso do usuario DRE
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com perfil "DRE"
    Entao interrupcao programada retorna status <status>
    E interrupcao programada valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | motivos/ | 403 |
      | GET | datas-bloqueadas-armazenavel/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis @perfil_classificacoes_dieta
  # Vinculo: COORDENADOR_DIETA_ESPECIAL
  Esquema do Cenario: Validar acesso do usuario CLASSIFICACOES_DIETA
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com perfil "CLASSIFICACOES_DIETA"
    Entao interrupcao programada retorna status <status>
    E interrupcao programada valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | motivos/ | 403 |
      | GET | datas-bloqueadas-armazenavel/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis @perfil_usuario_escola_cei_admin
  # Vinculo: DIRETOR_UE
  Esquema do Cenario: Validar acesso do usuario USUARIO_ESCOLA_CEI_ADMIN
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com perfil "USUARIO_ESCOLA_CEI_ADMIN"
    Entao interrupcao programada retorna status <status>
    E interrupcao programada valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | motivos/ | 403 |
      | GET | datas-bloqueadas-armazenavel/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis @perfil_medicao
  # Vinculo: ADMINISTRADOR_MEDICAO
  Esquema do Cenario: Validar acesso do usuario MEDICAO
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com perfil "MEDICAO"
    Entao interrupcao programada retorna status <status>
    E interrupcao programada valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | motivos/ | 403 |
      | GET | datas-bloqueadas-armazenavel/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis @perfil_distribuidor
  # Vinculo: ADMINISTRADOR_EMPRESA
  Esquema do Cenario: Validar acesso do usuario DISTRIBUIDOR
    Quando executo "<metodo>" em interrupcao programada na rota "<rota>" com perfil "DISTRIBUIDOR"
    Entao interrupcao programada retorna status <status>
    E interrupcao programada valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | motivos/ | 403 |
      | GET | datas-bloqueadas-armazenavel/ | 403 |
      | POST | principal | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |
