# language: pt
@cardapio_cei
Funcionalidade: Validar alteracoes de cardapio CEI

  Contexto:
    Dado que estou autenticado como escola para cardapio CEI

  Esquema do Cenario: Consultar listagens com o perfil permitido
    Quando consulto "<operacao>" de cardapio CEI como "<perfil>"
    Entao a listagem de cardapio CEI retorna status 200 e resultados

    Exemplos:
      | operacao      | perfil  |
      | listar        | escola  |
      | minhas        | escola  |
      | pedidos_codae | codae   |
      | pedidos_dre   | dre     |

  Cenario: Paginar listagem CEI
    Quando consulto a segunda pagina de cardapio CEI com limite 2
    Entao a pagina de cardapio CEI respeita o limite informado

  Cenario: Cadastrar rascunho CEI com substituicoes e faixas etarias
    Dado que criei um rascunho de cardapio CEI
    Entao o rascunho CEI foi criado com os dados enviados

  Cenario: Consultar detalhe CEI
    Dado que criei um rascunho de cardapio CEI
    Quando consulto o detalhe do rascunho CEI como CODAE
    Entao o detalhe CEI corresponde ao rascunho criado

  Esquema do Cenario: Atualizar rascunho CEI
    Dado que criei um rascunho de cardapio CEI
    Quando altero a observacao do rascunho CEI usando "<operacao>"
    Entao a alteracao CEI e persistida

    Exemplos:
      | operacao  |
      | atualizar |
      | parcial   |

  Cenario: Excluir rascunho CEI
    Dado que criei um rascunho de cardapio CEI
    Quando excluo o rascunho de cardapio CEI
    Entao a exclusao CEI retorna 204 e o registro deixa de existir

  Cenario: Gerar relatorio PDF CEI
    Quando solicito o relatorio de uma solicitacao CEI existente
    Entao o relatorio CEI retorna um PDF

  Esquema do Cenario: Rejeitar cadastro CEI invalido
    Quando cadastro cardapio CEI com "<caso>"
    Entao o cadastro CEI retorna 400 no campo "<campo>"

    Exemplos:
      | caso                   | campo         |
      | escola ausente         | escola        |
      | motivo invalido        | motivo        |
      | escola invalida        | escola        |
      | data ausente           | data          |
      | data invalida          | data          |
      | data passada           | data          |
      | substituicoes ausentes | substituicoes |

  Esquema do Cenario: Rejeitar atualizacao CEI com data invalida
    Dado que criei um rascunho de cardapio CEI
    Quando atualizo cardapio CEI com data invalida usando "<operacao>"
    Entao o cadastro CEI retorna 400 no campo "data"

    Exemplos:
      | operacao  |
      | atualizar |
      | parcial   |

  Esquema do Cenario: Rejeitar UUID inexistente no CRUD e relatorio CEI
    Quando acesso "<operacao>" de cardapio CEI com UUID inexistente como "<perfil>"
    Entao a operacao de cardapio CEI retorna status 404

    Exemplos:
      | operacao  | perfil |
      | detalhar  | codae  |
      | atualizar | codae  |
      | parcial   | escola |
      | excluir   | escola |
      | relatorio | escola |

  Esquema do Cenario: Rejeitar UUID inexistente nas acoes de fluxo CEI
    Quando acesso "<operacao>" de cardapio CEI com UUID inexistente como "<perfil>"
    Entao a operacao de cardapio CEI retorna status 404

    Exemplos:
      | operacao        | perfil |
      | iniciar         | escola |
      | cancelar_escola | escola |
      | autorizar       | codae  |
      | cancelar_codae  | codae  |
      | questionar      | codae  |
      | validar_dre     | dre    |
      | nao_validar_dre | dre    |

  Esquema do Cenario: Rejeitar transicao antecipada de rascunho CEI
    Dado que criei um rascunho de cardapio CEI
    Quando tento "<operacao>" no rascunho CEI como "<perfil>"
    Entao a transicao CEI retorna 400 e preserva o rascunho

    Exemplos:
      | operacao    | perfil |
      | autorizar   | codae  |
      | questionar  | codae  |
      | validar_dre | dre    |

  Esquema do Cenario: Bloquear escola nas operacoes exclusivas de outro perfil
    Quando acesso "<operacao>" de cardapio CEI como escola sem permissao
    Entao a operacao de cardapio CEI retorna status 403

    Exemplos:
      | operacao             |
      | autorizar            |
      | cancelar_codae       |
      | questionar           |
      | validar_dre          |
      | nao_validar_dre      |
      | conferir             |
      | responder            |
      | pedidos_terceirizada |

  Esquema do Cenario: Exigir autenticacao em todas as operacoes CEI
    Quando acesso "<operacao>" de cardapio CEI sem autenticacao
    Entao a operacao de cardapio CEI retorna status 401

    Exemplos:
      | operacao             |
      | listar               |
      | cadastrar            |
      | detalhar             |
      | atualizar            |
      | parcial              |
      | excluir              |
      | autorizar            |
      | cancelar_codae       |
      | questionar           |
      | nao_validar_dre      |
      | validar_dre          |
      | cancelar_escola      |
      | iniciar              |
      | conferir             |
      | relatorio            |
      | responder            |
      | minhas               |
      | pedidos_codae        |
      | pedidos_dre          |
      | pedidos_terceirizada |
