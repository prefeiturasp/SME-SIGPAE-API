# language: pt
Funcionalidade: Validar itens de cadastros
  @funcionais_itens @perfil_codae
  Cenario: Consultar itens de cadastros
    Quando consulto todos os itens de cadastros
    Entao a lista de itens de cadastros retorna dados validos
  @funcionais_itens @perfil_codae
  Esquema do Cenario: Filtrar itens de cadastros por valores validos
    Quando filtro itens de cadastros pelos campos "<campos>" existentes
    Entao o filtro de itens retorna dados validos
    Exemplos:
      | campos    |
      | nome      |
      | tipo      |
      | nome,tipo |
  @funcionais_itens @perfil_codae
  Esquema do Cenario: Filtrar itens de cadastros por valor invalido
    Quando filtro itens de cadastros pelo campo "<campo>" invalido
    Entao o filtro de itens retorna lista vazia
    Exemplos:
      | campo |
      | nome  |
      | tipo  |
  @funcionais_itens @perfil_codae
  Cenario: Consultar item de cadastro por UUID valido
    Quando consulto um item de cadastro existente por UUID
    Entao o item de cadastro retorna dados validos
  @funcionais_itens @perfil_codae
  Cenario: Consultar item de cadastro por UUID invalido
    Quando consulto um item de cadastro por UUID invalido
    Entao a operacao de item de cadastro retorna status 404
  @funcionais_itens @perfil_codae
  Cenario: Consultar lista de nomes dos itens
    Quando consulto a lista de nomes dos itens de cadastros
    Entao a lista de nomes retorna status 200 e resultados
  @funcionais_itens @perfil_codae
  Cenario: Consultar tipos dos itens
    Quando consulto os tipos de itens de cadastros
    Entao os tipos de itens retornam dados validos
  @funcionais_itens @perfil_codae
  Cenario: Cadastrar item de cadastro valido
    Quando cadastro um item de cadastro valido
    Entao o item de cadastro e criado e removido com sucesso
  @funcionais_itens @perfil_codae
  Cenario: Cadastrar item duplicado
    Quando cadastro duas vezes o mesmo item de cadastro
    Entao o segundo cadastro retorna status 400 e o item e removido
  @funcionais_itens @perfil_codae
  Esquema do Cenario: Cadastrar item invalido
    Quando cadastro um item de cadastro com dados "<tipo>"
    Entao o cadastro invalido do item retorna status 400
    Exemplos:
      | tipo          |
      | tipo_invalido |
      | campos_vazios |
      | campos_ausentes |
  @funcionais_itens @perfil_codae
  Cenario: Excluir item de cadastro valido
    Quando cadastro e excluo um item de cadastro
    Entao a exclusao do item retorna status 204
  @funcionais_itens @perfil_codae
  Cenario: Excluir item de cadastro inexistente
    Quando excluo um item de cadastro por UUID invalido
    Entao a operacao de item de cadastro retorna status 404
  @funcionais_itens @perfil_codae
  Cenario: Atualizar item por PUT
    Quando atualizo um item de cadastro por PUT com dados "validos"
    Entao a atualizacao valida do item retorna status 200 e realiza limpeza
  @funcionais_itens @perfil_codae
  Esquema do Cenario: Atualizar item invalido por PUT
    Quando atualizo um item de cadastro por PUT com dados "<tipo>"
    Entao a atualizacao invalida do item retorna erro e realiza limpeza quando necessario
    Exemplos:
      | tipo          |
      | tipo_invalido |
      | duplicado     |
      | campos_vazios |
      | campos_ausentes |
  @funcionais_itens @perfil_codae
  Cenario: Atualizar item por PATCH
    Quando atualizo um item de cadastro por PATCH com dados "validos"
    Entao a atualizacao valida do item retorna status 200 e realiza limpeza
  @funcionais_itens @perfil_codae
  Esquema do Cenario: Atualizar item invalido por PATCH
    Quando atualizo um item de cadastro por PATCH com dados "<tipo>"
    Entao a atualizacao invalida do item retorna erro e realiza limpeza quando necessario
    Exemplos:
      | tipo          |
      | tipo_invalido |
      | duplicado     |
      | campos_vazios |

  @perfis_itens @perfil_coordenador_logistica
  Esquema do Cenario: Validar acesso de itens com usuario COORDENADOR_LOGISTICA
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "COORDENADOR_LOGISTICA"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_coordenador_codae_dilog_logistica
  Esquema do Cenario: Validar acesso de itens com usuario COORDENADOR_CODAE_DILOG_LOGISTICA
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "COORDENADOR_CODAE_DILOG_LOGISTICA"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_coordenador_supervisao_nutricao
  Esquema do Cenario: Validar acesso de itens com usuario COORDENADOR_SUPERVISAO_NUTRICAO
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "COORDENADOR_SUPERVISAO_NUTRICAO"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_dilog_cronograma
  Esquema do Cenario: Validar acesso de itens com usuario DILOG_CRONOGRAMA
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "DILOG_CRONOGRAMA"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_dilog_qualidade
  Esquema do Cenario: Validar acesso de itens com usuario DILOG_QUALIDADE
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "DILOG_QUALIDADE"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_abastecimento
  Esquema do Cenario: Validar acesso de itens com usuario ABASTECIMENTO
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "ABASTECIMENTO"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_diretor_ue
  Esquema do Cenario: Validar acesso de itens com usuario DIRETOR_UE
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "DIRETOR_UE"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_codae
  Esquema do Cenario: Validar acesso de itens com usuario CODAE
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "CODAE"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_gpcodae
  Esquema do Cenario: Validar acesso de itens com usuario GPCODAE
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "GPCODAE"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_dre
  Esquema do Cenario: Validar acesso de itens com usuario DRE
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "DRE"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_classificacoes_dieta
  Esquema do Cenario: Validar acesso de itens com usuario CLASSIFICACOES_DIETA
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "CLASSIFICACOES_DIETA"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_usuario_escola_cei_admin
  Esquema do Cenario: Validar acesso de itens com usuario USUARIO_ESCOLA_CEI_ADMIN
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "USUARIO_ESCOLA_CEI_ADMIN"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_medicao
  Esquema do Cenario: Validar acesso de itens com usuario MEDICAO
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "MEDICAO"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_distribuidor
  Esquema do Cenario: Validar acesso de itens com usuario DISTRIBUIDOR
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "DISTRIBUIDOR"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_emef
  Esquema do Cenario: Validar acesso de itens com usuario EMEF
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "EMEF"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_cemei
  Esquema do Cenario: Validar acesso de itens com usuario CEMEI
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "CEMEI"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_cei
  Esquema do Cenario: Validar acesso de itens com usuario CEI
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "CEI"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_cci
  Esquema do Cenario: Validar acesso de itens com usuario CCI
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "CCI"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_dilog_diretoria
  Esquema do Cenario: Validar acesso de itens com usuario DILOG_DIRETORIA
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "DILOG_DIRETORIA"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @perfis_itens @perfil_administrador_empresa
  Esquema do Cenario: Validar acesso de itens com usuario ADMINISTRADOR_EMPRESA
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com perfil "ADMINISTRADOR_EMPRESA"
    Entao itens de cadastros retorna status <status>
    E itens de cadastros valida o retorno permitido para o perfil
    Exemplos:
      | metodo | rota | status |
      | GET | principal | 200 |
      | GET | lista-nomes/ | 200 |
      | GET | tipos/ | 200 |
      | GET | 00000000-0000-0000-0000-000000000000/ | 404 |
      | POST | principal | 400 |
      | PUT | 00000000-0000-0000-0000-000000000000/ | 404 |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | 404 |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | 404 |

  @autenticacao_itens
  Esquema do Cenario: Exigir autenticacao por rota de itens de cadastros
    Quando executo "<metodo>" em itens de cadastros na rota "<rota>" com acesso "<acesso>"
    Entao itens de cadastros retorna status 401
    Exemplos:
      | metodo | rota | acesso |
      | GET | principal | ausente |
      | GET | principal | invalido |
      | GET | lista-nomes/ | ausente |
      | GET | lista-nomes/ | invalido |
      | GET | tipos/ | ausente |
      | GET | tipos/ | invalido |
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
