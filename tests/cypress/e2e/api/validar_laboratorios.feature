# language: pt
Funcionalidade: Validar laboratorios
  @funcionais_laboratorios @perfil_dilog_qualidade
  Cenario: Consultar laboratorios
    Quando consulto todos os laboratorios
    Entao a consulta de laboratorios retorna status permitido e lista valida
  @funcionais_laboratorios @perfil_dilog_qualidade
  Esquema do Cenario: Filtrar laboratorios por valor existente
    Quando filtro laboratorios pelo campo existente "<campo>"
    Entao o filtro valido de laboratorios retorna dados coerentes
    Exemplos:
      | campo |
      | nome  |
      | cnpj  |
      | uuid  |
  @funcionais_laboratorios @perfil_dilog_qualidade
  Esquema do Cenario: Filtrar laboratorios por valor inexistente
    Quando filtro laboratorios pelo campo inexistente "<campo>"
    Entao o filtro inexistente retorna lista vazia ou permissao negada
    Exemplos:
      | campo |
      | nome  |
      | cnpj  |
      | uuid  |
  @funcionais_laboratorios @perfil_dilog_qualidade
  Cenario: Consultar laboratorio por UUID existente
    Quando consulto um laboratorio existente por UUID
    Entao o laboratorio por UUID retorna dados coerentes
  @funcionais_laboratorios @perfil_dilog_qualidade
  Cenario: Consultar laboratorio por UUID invalido
    Quando consulto um laboratorio por UUID invalido
    Entao a operacao de laboratorio retorna status de erro permitido
  @funcionais_laboratorios @perfil_dilog_qualidade
  Esquema do Cenario: Consultar listagens de laboratorios
    Quando consulto a listagem de laboratorios "<lista>"
    Entao a listagem de laboratorios retorna status permitido e dados validos
    Exemplos:
      | lista        |
      | completa     |
      | credenciados |
      | nomes        |
  @funcionais_laboratorios @perfil_dilog_qualidade
  Cenario: Cadastrar laboratorio valido
    Quando cadastro um laboratorio com dados "validos"
    Entao o cadastro valido retorna sucesso ou permissao negada e realiza limpeza
  @funcionais_laboratorios @perfil_dilog_qualidade
  Esquema do Cenario: Cadastrar laboratorio invalido
    Quando cadastro um laboratorio com dados "<tipo>"
    Entao o cadastro invalido retorna validacao ou permissao negada
    Exemplos:
      | tipo             |
      | booleanos_invalidos |
      | campos_em_branco |
      | campos_ausentes  |
  @funcionais_laboratorios @perfil_dilog_qualidade
  Cenario: Excluir laboratorio valido
    Quando cadastro e excluo um laboratorio valido
    Entao a exclusao valida retorna status permitido
  @funcionais_laboratorios @perfil_dilog_qualidade
  Cenario: Excluir laboratorio inexistente
    Quando excluo um laboratorio por UUID invalido
    Entao a operacao de laboratorio retorna status de erro permitido
  @funcionais_laboratorios @perfil_dilog_qualidade
  Cenario: Atualizar laboratorio valido por PUT
    Quando atualizo por PUT um laboratorio com dados "validos"
    Entao a atualizacao valida retorna sucesso ou permissao negada e realiza limpeza
  @funcionais_laboratorios @perfil_dilog_qualidade
  Esquema do Cenario: Atualizar laboratorio invalido por PUT
    Quando atualizo por PUT um laboratorio com dados "<tipo>"
    Entao a atualizacao invalida retorna validacao ou permissao negada e realiza limpeza
    Exemplos:
      | tipo                |
      | booleanos_invalidos |
      | campos_ausentes     |
      | campos_em_branco    |
  @funcionais_laboratorios @perfil_dilog_qualidade
  Cenario: Atualizar laboratorio inexistente por PUT
    Quando atualizo por PUT um laboratorio com UUID invalido
    Entao a operacao de laboratorio retorna status de erro permitido
  @funcionais_laboratorios @perfil_dilog_qualidade
  Cenario: Atualizar laboratorio valido por PATCH
    Quando atualizo por PATCH um laboratorio com dados "validos"
    Entao a atualizacao valida retorna sucesso ou permissao negada e realiza limpeza
  @funcionais_laboratorios @perfil_dilog_qualidade
  Esquema do Cenario: Atualizar laboratorio invalido por PATCH
    Quando atualizo por PATCH um laboratorio com dados "<tipo>"
    Entao a atualizacao invalida retorna validacao ou permissao negada e realiza limpeza
    Exemplos:
      | tipo                |
      | booleanos_invalidos |
      | campos_em_branco    |
  @funcionais_laboratorios @perfil_dilog_qualidade
  Cenario: Atualizar laboratorio inexistente por PATCH
    Quando atualizo por PATCH um laboratorio com UUID invalido
    Entao a operacao de laboratorio retorna status de erro permitido

  @perfis_laboratorios @perfil_coordenador_logistica
  Esquema do Cenario: Validar acesso de laboratorios com perfil COORDENADOR_LOGISTICA
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "COORDENADOR_LOGISTICA"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_coordenador_codae_dilog_logistica
  Esquema do Cenario: Validar acesso de laboratorios com perfil COORDENADOR_CODAE_DILOG_LOGISTICA
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "COORDENADOR_CODAE_DILOG_LOGISTICA"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-laboratorios/ | 200 |
      | GET | lista-laboratorios-credenciados/ | 200 |
      | GET | lista-nomes-laboratorios/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_laboratorios @perfil_coordenador_supervisao_nutricao
  Esquema do Cenario: Validar acesso de laboratorios com perfil COORDENADOR_SUPERVISAO_NUTRICAO
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "COORDENADOR_SUPERVISAO_NUTRICAO"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_dilog_cronograma
  Esquema do Cenario: Validar acesso de laboratorios com perfil DILOG_CRONOGRAMA
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "DILOG_CRONOGRAMA"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_dilog_qualidade
  Esquema do Cenario: Validar acesso de laboratorios com perfil DILOG_QUALIDADE
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "DILOG_QUALIDADE"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-laboratorios/ | 200 |
      | GET | lista-laboratorios-credenciados/ | 200 |
      | GET | lista-nomes-laboratorios/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_laboratorios @perfil_abastecimento
  Esquema do Cenario: Validar acesso de laboratorios com perfil ABASTECIMENTO
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "ABASTECIMENTO"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_diretor_ue
  Esquema do Cenario: Validar acesso de laboratorios com perfil DIRETOR_UE
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "DIRETOR_UE"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_codae
  Esquema do Cenario: Validar acesso de laboratorios com perfil CODAE
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "CODAE"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_gpcodae
  Esquema do Cenario: Validar acesso de laboratorios com perfil GPCODAE
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "GPCODAE"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_dre
  Esquema do Cenario: Validar acesso de laboratorios com perfil DRE
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "DRE"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_classificacoes_dieta
  Esquema do Cenario: Validar acesso de laboratorios com perfil CLASSIFICACOES_DIETA
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "CLASSIFICACOES_DIETA"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_usuario_escola_cei_admin
  Esquema do Cenario: Validar acesso de laboratorios com perfil USUARIO_ESCOLA_CEI_ADMIN
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "USUARIO_ESCOLA_CEI_ADMIN"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_medicao
  Esquema do Cenario: Validar acesso de laboratorios com perfil MEDICAO
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "MEDICAO"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_distribuidor
  Esquema do Cenario: Validar acesso de laboratorios com perfil DISTRIBUIDOR
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "DISTRIBUIDOR"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_emef
  Esquema do Cenario: Validar acesso de laboratorios com perfil EMEF
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "EMEF"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_cemei
  Esquema do Cenario: Validar acesso de laboratorios com perfil CEMEI
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "CEMEI"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_cei
  Esquema do Cenario: Validar acesso de laboratorios com perfil CEI
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "CEI"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_cci
  Esquema do Cenario: Validar acesso de laboratorios com perfil CCI
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "CCI"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_dilog_diretoria
  Esquema do Cenario: Validar acesso de laboratorios com perfil DILOG_DIRETORIA
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "DILOG_DIRETORIA"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @perfis_laboratorios @perfil_administrador_empresa
  Esquema do Cenario: Validar acesso de laboratorios com perfil ADMINISTRADOR_EMPRESA
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com perfil "ADMINISTRADOR_EMPRESA"
    Entao laboratorios retorna status <status>
    E laboratorios valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 403 |
      | GET | lista-laboratorios/ | 403 |
      | GET | lista-laboratorios-credenciados/ | 403 |
      | GET | lista-nomes-laboratorios/ | 403 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 403 |
      | POST | principal | 403 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 403 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 403 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 403 |

  @autenticacao_laboratorios
  Esquema do Cenario: Exigir autenticacao por rota de laboratorios
    Quando executo "<metodo>" em laboratorios na rota "<rota>" com acesso "<acesso>"
    Entao laboratorios retorna status 401
    Exemplos:
      | metodo | rota | acesso |
      | GET | principal | ausente |
      | GET | lista-laboratorios/ | ausente |
      | GET | lista-laboratorios-credenciados/ | ausente |
      | GET | lista-nomes-laboratorios/ | ausente |
      | GET | 00000000-0000-0000-0000-000000000000/ | ausente |
      | POST | principal | ausente |
      | PUT | 00000000-0000-0000-0000-000000000000/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | ausente |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | ausente |
      | GET | principal | invalido |
      | GET | lista-laboratorios/ | invalido |
      | GET | lista-laboratorios-credenciados/ | invalido |
      | GET | lista-nomes-laboratorios/ | invalido |
      | GET | 00000000-0000-0000-0000-000000000000/ | invalido |
      | POST | principal | invalido |
      | PUT | 00000000-0000-0000-0000-000000000000/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | invalido |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | invalido |
