# language: pt
@lancamento_diario
Funcionalidade: Validar lancamento diario por perfil

  @perfis_lancamento_diario @perfil_coordenador_logistica
  Esquema do Cenario: Validar acesso de lancamento diario com perfil COORDENADOR_LOGISTICA
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "COORDENADOR_LOGISTICA"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_coordenador_codae_dilog_logistica
  Esquema do Cenario: Validar acesso de lancamento diario com perfil COORDENADOR_CODAE_DILOG_LOGISTICA
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "COORDENADOR_CODAE_DILOG_LOGISTICA"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_coordenador_supervisao_nutricao
  Esquema do Cenario: Validar acesso de lancamento diario com perfil COORDENADOR_SUPERVISAO_NUTRICAO
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "COORDENADOR_SUPERVISAO_NUTRICAO"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_dilog_cronograma
  Esquema do Cenario: Validar acesso de lancamento diario com perfil DILOG_CRONOGRAMA
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "DILOG_CRONOGRAMA"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_dilog_qualidade
  Esquema do Cenario: Validar acesso de lancamento diario com perfil DILOG_QUALIDADE
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "DILOG_QUALIDADE"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_abastecimento
  Esquema do Cenario: Validar acesso de lancamento diario com perfil ABASTECIMENTO
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "ABASTECIMENTO"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_diretor_ue
  Esquema do Cenario: Validar acesso de lancamento diario com perfil DIRETOR_UE
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "DIRETOR_UE"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_codae
  Esquema do Cenario: Validar acesso de lancamento diario com perfil CODAE
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "CODAE"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_gpcodae
  Esquema do Cenario: Validar acesso de lancamento diario com perfil GPCODAE
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "GPCODAE"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_dre
  Esquema do Cenario: Validar acesso de lancamento diario com perfil DRE
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "DRE"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_classificacoes_dieta
  Esquema do Cenario: Validar acesso de lancamento diario com perfil CLASSIFICACOES_DIETA
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "CLASSIFICACOES_DIETA"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_usuario_escola_cei_admin
  Esquema do Cenario: Validar acesso de lancamento diario com perfil USUARIO_ESCOLA_CEI_ADMIN
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "USUARIO_ESCOLA_CEI_ADMIN"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_medicao
  Esquema do Cenario: Validar acesso de lancamento diario com perfil MEDICAO
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "MEDICAO"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_distribuidor
  Esquema do Cenario: Validar acesso de lancamento diario com perfil DISTRIBUIDOR
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "DISTRIBUIDOR"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_emef
  Esquema do Cenario: Validar acesso de lancamento diario com perfil EMEF
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "EMEF"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_cemei
  Esquema do Cenario: Validar acesso de lancamento diario com perfil CEMEI
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "CEMEI"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_cei
  Esquema do Cenario: Validar acesso de lancamento diario com perfil CEI
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "CEI"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_cci
  Esquema do Cenario: Validar acesso de lancamento diario com perfil CCI
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "CCI"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_dilog_diretoria
  Esquema do Cenario: Validar acesso de lancamento diario com perfil DILOG_DIRETORIA
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "DILOG_DIRETORIA"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @perfis_lancamento_diario @perfil_administrador_empresa
  Esquema do Cenario: Validar acesso de lancamento diario com perfil ADMINISTRADOR_EMPRESA
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com perfil "ADMINISTRADOR_EMPRESA"
    Entao lancamento diario retorna status <status>
    E lancamento diario valida o retorno para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | POST | principal | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |
      | GET | por-mes/ | 200 |
      | GET | dados-dia-periodo/ | 200 |

  @autenticacao_lancamento_diario
  Esquema do Cenario: Exigir autenticacao nas rotas de lancamento diario
    Quando executo "<metodo>" em lancamento diario na rota "<rota>" com acesso "<acesso>"
    Entao lancamento diario retorna status 401
    Exemplos:
      | metodo | rota | acesso |
      | GET | principal | ausente |
      | POST | principal | ausente |
      | GET | 00000000-0000-0000-0000-000000000000/ | ausente |
      | PUT | 00000000-0000-0000-0000-000000000000/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | ausente |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | ausente |
      | GET | por-mes/ | ausente |
      | GET | dados-dia-periodo/ | ausente |
      | GET | principal | invalido |
      | POST | principal | invalido |
      | GET | 00000000-0000-0000-0000-000000000000/ | invalido |
      | PUT | 00000000-0000-0000-0000-000000000000/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | invalido |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | invalido |
      | GET | por-mes/ | invalido |
      | GET | dados-dia-periodo/ | invalido |
