# language: pt
@kit_lanches
Funcionalidade: Validar kit lanches por perfil

    @perfis_kit_lanches @perfil_coordenador_logistica
  Esquema do Cenario: Validar acesso de kit lanches com usuario COORDENADOR_LOGISTICA
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "COORDENADOR_LOGISTICA"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_coordenador_codae_dilog_logistica
  Esquema do Cenario: Validar acesso de kit lanches com usuario COORDENADOR_CODAE_DILOG_LOGISTICA
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "COORDENADOR_CODAE_DILOG_LOGISTICA"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_coordenador_supervisao_nutricao
  Esquema do Cenario: Validar acesso de kit lanches com usuario COORDENADOR_SUPERVISAO_NUTRICAO
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "COORDENADOR_SUPERVISAO_NUTRICAO"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_dilog_cronograma
  Esquema do Cenario: Validar acesso de kit lanches com usuario DILOG_CRONOGRAMA
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "DILOG_CRONOGRAMA"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_dilog_qualidade
  Esquema do Cenario: Validar acesso de kit lanches com usuario DILOG_QUALIDADE
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "DILOG_QUALIDADE"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_abastecimento
  Esquema do Cenario: Validar acesso de kit lanches com usuario ABASTECIMENTO
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "ABASTECIMENTO"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_diretor_ue
  Esquema do Cenario: Validar acesso de kit lanches com usuario DIRETOR_UE
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "DIRETOR_UE"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_codae
  Esquema do Cenario: Validar acesso de kit lanches com usuario CODAE
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "CODAE"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_gpcodae
  Esquema do Cenario: Validar acesso de kit lanches com usuario GPCODAE
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "GPCODAE"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_dre
  Esquema do Cenario: Validar acesso de kit lanches com usuario DRE
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "DRE"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_classificacoes_dieta
  Esquema do Cenario: Validar acesso de kit lanches com usuario CLASSIFICACOES_DIETA
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "CLASSIFICACOES_DIETA"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_usuario_escola_cei_admin
  Esquema do Cenario: Validar acesso de kit lanches com usuario USUARIO_ESCOLA_CEI_ADMIN
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "USUARIO_ESCOLA_CEI_ADMIN"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_medicao
  Esquema do Cenario: Validar acesso de kit lanches com usuario MEDICAO
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "MEDICAO"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_distribuidor
  Esquema do Cenario: Validar acesso de kit lanches com usuario DISTRIBUIDOR
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "DISTRIBUIDOR"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_emef
  Esquema do Cenario: Validar acesso de kit lanches com usuario EMEF
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "EMEF"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_cemei
  Esquema do Cenario: Validar acesso de kit lanches com usuario CEMEI
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "CEMEI"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_cei
  Esquema do Cenario: Validar acesso de kit lanches com usuario CEI
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "CEI"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_cci
  Esquema do Cenario: Validar acesso de kit lanches com usuario CCI
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "CCI"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_dilog_diretoria
  Esquema do Cenario: Validar acesso de kit lanches com usuario DILOG_DIRETORIA
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "DILOG_DIRETORIA"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_kit_lanches @perfil_administrador_empresa
  Esquema do Cenario: Validar acesso de kit lanches com usuario ADMINISTRADOR_EMPRESA
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com perfil "ADMINISTRADOR_EMPRESA"
    Entao kit lanches retorna status <status>
    E kit lanches valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | consulta-kits/ | 200 |
      | GET | nome-existe/ | 404 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfil_codae
  Cenario: Consultar detalhe de kit lanche existente
    Quando consulto detalhe de kit lanche existente com perfil "CODAE"
    Entao kit lanches retorna status 200
    E o detalhe do kit lanche corresponde ao registro consultado

  @perfil_codae
  Esquema do Cenario: Filtrar kits por status com perfil CODAE
    Quando filtro kit lanches na rota "<rota>" por "status" igual a "<status>" com perfil "CODAE"
    Entao kit lanches retorna status 200
    E os kits correspondem ao filtro informado
    Exemplos:
      | rota | status |
      | principal | ATIVO |
      | principal | INATIVO |
      | consulta-kits/ | ATIVO |
      | consulta-kits/ | INATIVO |

  @perfil_codae
  Esquema do Cenario: Consultar filtros sem resultados com perfil CODAE
    Quando filtro kit lanches na rota "<rota>" por "<campo>" igual a "<valor>" com perfil "CODAE"
    Entao kit lanches retorna status 200
    E os kits correspondem ao filtro informado
    Exemplos:
      | rota | campo | valor |
      | principal | uuid | 00000000-0000-0000-0000-000000000000 |
      | principal | numero_edital | EDITAL_INEXISTENTE_CYPRESS |
      | consulta-kits/ | uuid | 00000000-0000-0000-0000-000000000000 |
      | consulta-kits/ | numero_edital | EDITAL_INEXISTENTE_CYPRESS |

  @perfil_codae
  Esquema do Cenario: Validar nome existente e edicao do proprio kit com perfil CODAE
    Quando consulto nome de kit lanche "<caso>" com perfil "CODAE"
    Entao kit lanches retorna status <status>
    E kit lanches informa nome "<resultado>"
    Exemplos:
      | caso | status | resultado |
      | existente | 200 | existente |
      | do proprio registro | 404 | valido |

  @autenticacao_kit_lanches
  Esquema do Cenario: Exigir autenticacao em todas as operacoes de kit lanches
    Quando executo "<metodo>" em kit lanches na rota "<rota>" com acesso "<acesso>"
    Entao kit lanches retorna status 401
    Exemplos:
      | metodo | rota | acesso |
      | GET | principal | ausente |
      | GET | principal | invalido |
      | GET | consulta-kits/ | ausente |
      | GET | consulta-kits/ | invalido |
      | GET | nome-existe/ | ausente |
      | GET | nome-existe/ | invalido |
      | GET | 00000000-0000-0000-0000-000000000000/ | ausente |
      | GET | 00000000-0000-0000-0000-000000000000/ | invalido |
      | POST | principal | ausente |
      | POST | principal | invalido |
      | PUT | 00000000-0000-0000-0000-000000000000/ | ausente |
      | PUT | 00000000-0000-0000-0000-000000000000/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | invalido |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | ausente |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | invalido |
