# language: pt
@ajuste_saldo_laudo
Funcionalidade: Validar ajuste de saldo do laudo

  Cenario: Listar ajustes com paginacao
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Quando consulto os ajustes de saldo com pagina 1 e tamanho 2
    Entao a listagem de ajustes de saldo retorna dados paginados

  Cenario: Filtrar ajustes por cronograma
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Dado que criei um ajuste de saldo para o cenario
    Quando filtro os ajustes pelo cronograma do registro criado
    Entao todos os ajustes retornados pertencem ao cronograma informado

  Cenario: Consultar pagina inexistente
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Quando consulto os ajustes de saldo com pagina 999999999 e tamanho 2
    Entao a operacao de ajuste de saldo retorna status 404

  Cenario: Cadastrar ajuste de saldo
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Quando cadastro um ajuste de saldo valido
    Entao o ajuste e criado e pode ser consultado

  Esquema do Cenario: Rejeitar cadastro com campos invalidos
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Quando cadastro um ajuste de saldo com "<caso>"
    Entao o ajuste de saldo retorna erro no campo "<campo>"

    Exemplos:
      | caso                 | campo                  |
      | documento ausente    | documento_recebimento  |
      | documento invalido   | documento_recebimento  |
      | quantidade ausente   | quantidade_descontada  |
      | quantidade invalida  | quantidade_descontada  |
      | casas decimais       | quantidade_descontada  |

  Cenario: Rejeitar desconto maior que o saldo no cadastro
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Quando cadastro um ajuste com desconto maior que o saldo disponivel
    Entao o ajuste de saldo retorna erro no campo "quantidade_descontada"

  Cenario: Consultar ajuste por UUID
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Dado que criei um ajuste de saldo para o cenario
    Quando consulto o ajuste de saldo criado por UUID
    Entao o detalhe do ajuste de saldo corresponde ao registro criado

  Esquema do Cenario: Rejeitar UUID inexistente
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Quando executo "<metodo>" em um ajuste de saldo inexistente
    Entao a operacao de ajuste de saldo retorna status 404

    Exemplos:
      | metodo |
      | PUT    |
      | DELETE |

  Cenario: PUT preserva os campos somente de leitura do contrato atual
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Dado que criei um ajuste de saldo para o cenario
    Quando envio PUT com outra quantidade para o ajuste criado
    Entao o PUT retorna sucesso e preserva a quantidade somente de leitura

  Cenario: Atualizar quantidade por PATCH
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Dado que criei um ajuste de saldo para o cenario
    Quando atualizo a quantidade do ajuste criado por PATCH
    Entao a quantidade do ajuste e atualizada e persistida

  Esquema do Cenario: Rejeitar PATCH invalido
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Dado que criei um ajuste de saldo para o cenario
    Quando envio PATCH de ajuste de saldo com "<caso>"
    Entao o ajuste de saldo retorna erro no campo "quantidade_descontada"
    E a quantidade original do ajuste permanece inalterada

    Exemplos:
      | caso                |
      | quantidade ausente  |
      | quantidade invalida |
      | saldo insuficiente  |

  Cenario: Excluir ajuste criado pelo teste
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Dado que criei um ajuste de saldo para o cenario
    Quando excluo o ajuste de saldo criado
    Entao o ajuste e excluido e uma segunda exclusao retorna 404

  Cenario: Listar cronogramas mensais com documentos
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Quando consulto os cronogramas mensais para ajuste de saldo
    Entao os cronogramas de ajuste de saldo possuem os campos esperados

  Cenario: Consultar documentos de um cronograma existente
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Quando consulto documentos de um cronograma disponivel para ajuste
    Entao os documentos do cronograma possuem os dados de saldo

  Cenario: Rejeitar consulta de documentos sem cronograma
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Quando consulto documentos de ajuste sem informar cronograma
    Entao a consulta de documentos de ajuste retorna 400 com mensagem "UUID do cronograma é obrigatório."

  Cenario: Consultar documentos de cronograma inexistente
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Quando consulto documentos de ajuste de cronograma inexistente
    Entao a operacao de ajuste de saldo retorna status 404

  Esquema do Cenario: Exigir autenticacao em todos os endpoints
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Quando acesso "<rota>" de ajuste de saldo sem autenticacao
    Entao a operacao de ajuste de saldo retorna status 401

    Exemplos:
      | rota        |
      | listar      |
      | cadastrar   |
      | detalhar    |
      | atualizar   |
      | parcial     |
      | excluir     |
      | cronogramas |
      | documentos  |

  Cenario: Impedir acesso de perfil sem permissao
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo
    Quando consulto ajustes de saldo como diretor de escola
    Entao a operacao de ajuste de saldo retorna status 403

  @perfis_ajuste_saldo @perfil_coordenador_logistica
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario COORDENADOR_LOGISTICA
    Quando acesso "<operacao>" de ajuste de saldo com perfil "COORDENADOR_LOGISTICA"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_coordenador_codae_dilog_logistica
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario COORDENADOR_CODAE_DILOG_LOGISTICA
    Quando acesso "<operacao>" de ajuste de saldo com perfil "COORDENADOR_CODAE_DILOG_LOGISTICA"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_coordenador_supervisao_nutricao
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario COORDENADOR_SUPERVISAO_NUTRICAO
    Quando acesso "<operacao>" de ajuste de saldo com perfil "COORDENADOR_SUPERVISAO_NUTRICAO"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_dilog_cronograma
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario DILOG_CRONOGRAMA
    Quando acesso "<operacao>" de ajuste de saldo com perfil "DILOG_CRONOGRAMA"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_dilog_qualidade
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario DILOG_QUALIDADE
    Quando acesso "<operacao>" de ajuste de saldo com perfil "DILOG_QUALIDADE"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 200 |
      | cadastrar | 400 |
      | detalhar | 200 |
      | atualizar | 404 |
      | parcial | 400 |
      | excluir | 404 |
      | cronogramas | 200 |
      | documentos | 400 |

  @perfis_ajuste_saldo @perfil_abastecimento
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario ABASTECIMENTO
    Quando acesso "<operacao>" de ajuste de saldo com perfil "ABASTECIMENTO"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_diretor_ue
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario DIRETOR_UE
    Quando acesso "<operacao>" de ajuste de saldo com perfil "DIRETOR_UE"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_codae
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario CODAE
    Quando acesso "<operacao>" de ajuste de saldo com perfil "CODAE"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_gpcodae
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario GPCODAE
    Quando acesso "<operacao>" de ajuste de saldo com perfil "GPCODAE"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_dre
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario DRE
    Quando acesso "<operacao>" de ajuste de saldo com perfil "DRE"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_classificacoes_dieta
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario CLASSIFICACOES_DIETA
    Quando acesso "<operacao>" de ajuste de saldo com perfil "CLASSIFICACOES_DIETA"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_usuario_escola_cei_admin
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario USUARIO_ESCOLA_CEI_ADMIN
    Quando acesso "<operacao>" de ajuste de saldo com perfil "USUARIO_ESCOLA_CEI_ADMIN"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_medicao
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario MEDICAO
    Quando acesso "<operacao>" de ajuste de saldo com perfil "MEDICAO"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_distribuidor
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario DISTRIBUIDOR
    Quando acesso "<operacao>" de ajuste de saldo com perfil "DISTRIBUIDOR"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_emef
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario EMEF
    Quando acesso "<operacao>" de ajuste de saldo com perfil "EMEF"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_cemei
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario CEMEI
    Quando acesso "<operacao>" de ajuste de saldo com perfil "CEMEI"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_cei
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario CEI
    Quando acesso "<operacao>" de ajuste de saldo com perfil "CEI"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_cci
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario CCI
    Quando acesso "<operacao>" de ajuste de saldo com perfil "CCI"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_dilog_diretoria
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario DILOG_DIRETORIA
    Quando acesso "<operacao>" de ajuste de saldo com perfil "DILOG_DIRETORIA"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |

  @perfis_ajuste_saldo @perfil_administrador_empresa
  Esquema do Cenario: Validar acesso de ajuste de saldo com usuario ADMINISTRADOR_EMPRESA
    Quando acesso "<operacao>" de ajuste de saldo com perfil "ADMINISTRADOR_EMPRESA"
    Entao a operacao de ajuste de saldo retorna status <status>
    E o retorno de ajuste de saldo respeita o acesso do perfil
    Exemplos:
      | operacao | status |
      | listar | 403 |
      | cadastrar | 403 |
      | detalhar | 403 |
      | atualizar | 403 |
      | parcial | 403 |
      | excluir | 403 |
      | cronogramas | 403 |
      | documentos | 403 |
