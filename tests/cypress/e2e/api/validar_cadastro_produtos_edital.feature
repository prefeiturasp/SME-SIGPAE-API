# language: pt
Funcionalidade: Validar cadastro de produtos do edital
  Contexto:
    Dado que estou autenticado para gerenciar produtos do edital

  Esquema do Cenario: Consultar produtos do edital por filtro valido
    Quando consulto produtos do edital pelo filtro "<filtro>"
    Entao a consulta de produtos do edital retorna uma lista valida
    Exemplos:
      | filtro                              |
      | sem filtro                          |
      | nome existente                      |
      | data de cadastro                    |
      | status                              |

  Cenario: Consultar produto inexistente por nome
    Quando consulto produtos do edital pelo filtro "nome inexistente"
    Entao a consulta de produtos do edital retorna uma lista vazia

  Cenario: Consultar produtos por data invalida
    Quando consulto produtos do edital pelo filtro "data invalida"
    Entao a consulta de produtos do edital retorna erro de data invalida

  Cenario: Cadastrar produto do edital valido
    Quando cadastro um produto valido do edital
    Entao o produto do edital e criado e removido com sucesso

  Cenario: Cadastrar produto do edital duplicado
    Quando cadastro duas vezes o mesmo produto do edital
    Entao o segundo cadastro do produto retorna item ja cadastrado

  Esquema do Cenario: Cadastrar produto do edital com dados invalidos
    Quando cadastro produto do edital com erro "<erro>"
    Entao o cadastro invalido do produto retorna erro no campo "<campo>"
    Exemplos:
      | erro                  | campo        |
      | tipo invalido         | tipo_produto |
      | sem nome              | nome         |
      | nome em branco        | nome         |
      | sem ativo             | ativo        |
      | ativo em branco       | ativo        |

  Cenario: Consultar produto do edital por UUID valido
    Quando consulto produto do edital por UUID "valido"
    Entao o produto do edital retorna dados validos

  Cenario: Consultar produto do edital por UUID invalido
    Quando consulto produto do edital por UUID "invalido"
    Entao a operacao de produto do edital retorna status 404

  Esquema do Cenario: Consultar listas auxiliares de produtos do edital
    Quando consulto a lista auxiliar de produtos "<lista>"
    Entao a lista auxiliar de produtos retorna resultados validos
    Exemplos:
      | lista                       |
      | completa logistica          |
      | nomes                       |
      | nomes logistica             |
      | todos produtos logistica    |

  Cenario: Atualizar produto do edital por PUT
    Quando atualizo um produto do edital por PUT com dados validos
    Entao o produto e atualizado e restaurado por PUT

  Cenario: Atualizar produto do edital por PUT com nome duplicado
    Quando atualizo produto do edital por PUT com nome duplicado
    Entao a atualizacao do produto retorna item ja cadastrado

  Esquema do Cenario: Atualizar produto do edital por PUT com dados invalidos
    Quando atualizo produto do edital por PUT com erro "<erro>"
    Entao a atualizacao invalida do produto retorna erro no campo "<campo>"
    Exemplos:
      | erro            | campo        |
      | tipo invalido   | tipo_produto |
      | sem nome        | nome         |
      | nome em branco  | nome         |
      | sem ativo       | ativo        |
      | ativo em branco | ativo        |

  Cenario: Excluir produto do edital existente
    Quando crio e excluo um produto do edital
    Entao a exclusao do produto do edital retorna status 204

  Cenario: Excluir produto do edital inexistente
    Quando excluo um produto do edital inexistente
    Entao a operacao de produto do edital retorna status 404

  Cenario: Atualizar produto do edital por PATCH
    Quando atualizo um produto do edital por PATCH com dados validos
    Entao o produto e atualizado e restaurado por PATCH

  Cenario: Atualizar produto do edital por PATCH com nome duplicado
    Quando atualizo produto do edital por PATCH com nome duplicado
    Entao a atualizacao do produto retorna item ja cadastrado

  Esquema do Cenario: Atualizar produto do edital por PATCH com dados invalidos
    Quando atualizo produto do edital por PATCH com erro "<erro>"
    Entao a atualizacao invalida do produto retorna erro no campo "<campo>"
    Exemplos:
      | erro            | campo        |
      | tipo invalido   | tipo_produto |
      | nome em branco  | nome         |
      | ativo em branco | ativo        |
