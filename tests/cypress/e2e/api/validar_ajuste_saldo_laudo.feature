# language: pt
@ajuste_saldo_laudo
Funcionalidade: Validar ajuste de saldo do laudo

  Contexto:
    Dado que estou autenticado como DILOG qualidade para ajuste de saldo do laudo

  Cenario: Listar ajustes com paginacao
    Quando consulto os ajustes de saldo com pagina 1 e tamanho 2
    Entao a listagem de ajustes de saldo retorna dados paginados

  Cenario: Filtrar ajustes por cronograma
    Dado que criei um ajuste de saldo para o cenario
    Quando filtro os ajustes pelo cronograma do registro criado
    Entao todos os ajustes retornados pertencem ao cronograma informado

  Cenario: Consultar pagina inexistente
    Quando consulto os ajustes de saldo com pagina 999999999 e tamanho 2
    Entao a operacao de ajuste de saldo retorna status 404

  Cenario: Cadastrar ajuste de saldo
    Quando cadastro um ajuste de saldo valido
    Entao o ajuste e criado e pode ser consultado

  Esquema do Cenario: Rejeitar cadastro com campos invalidos
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
    Quando cadastro um ajuste com desconto maior que o saldo disponivel
    Entao o ajuste de saldo retorna erro no campo "quantidade_descontada"

  Cenario: Consultar ajuste por UUID
    Dado que criei um ajuste de saldo para o cenario
    Quando consulto o ajuste de saldo criado por UUID
    Entao o detalhe do ajuste de saldo corresponde ao registro criado

  Esquema do Cenario: Rejeitar UUID inexistente
    Quando executo "<metodo>" em um ajuste de saldo inexistente
    Entao a operacao de ajuste de saldo retorna status 404

    Exemplos:
      | metodo |
      | PUT    |
      | DELETE |

  Cenario: PUT preserva os campos somente de leitura do contrato atual
    Dado que criei um ajuste de saldo para o cenario
    Quando envio PUT com outra quantidade para o ajuste criado
    Entao o PUT retorna sucesso e preserva a quantidade somente de leitura

  Cenario: Atualizar quantidade por PATCH
    Dado que criei um ajuste de saldo para o cenario
    Quando atualizo a quantidade do ajuste criado por PATCH
    Entao a quantidade do ajuste e atualizada e persistida

  Esquema do Cenario: Rejeitar PATCH invalido
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
    Dado que criei um ajuste de saldo para o cenario
    Quando excluo o ajuste de saldo criado
    Entao o ajuste e excluido e uma segunda exclusao retorna 404

  Cenario: Listar cronogramas mensais com documentos
    Quando consulto os cronogramas mensais para ajuste de saldo
    Entao os cronogramas de ajuste de saldo possuem os campos esperados

  Cenario: Consultar documentos de um cronograma existente
    Quando consulto documentos de um cronograma disponivel para ajuste
    Entao os documentos do cronograma possuem os dados de saldo

  Cenario: Rejeitar consulta de documentos sem cronograma
    Quando consulto documentos de ajuste sem informar cronograma
    Entao a consulta de documentos de ajuste retorna 400 com mensagem "UUID do cronograma é obrigatório."

  Cenario: Consultar documentos de cronograma inexistente
    Quando consulto documentos de ajuste de cronograma inexistente
    Entao a operacao de ajuste de saldo retorna status 404

  Esquema do Cenario: Exigir autenticacao em todos os endpoints
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
    Quando consulto ajustes de saldo como diretor de escola
    Entao a operacao de ajuste de saldo retorna status 403
