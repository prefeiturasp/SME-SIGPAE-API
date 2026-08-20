# language: pt
Funcionalidade: Validar itens de cadastros
  Contexto:
    Dado que estou autenticado como CODAE para gerenciar itens de cadastros
  Cenario: Consultar itens de cadastros
    Quando consulto todos os itens de cadastros
    Entao a lista de itens de cadastros retorna dados validos
  Esquema do Cenario: Filtrar itens de cadastros por valores validos
    Quando filtro itens de cadastros pelos campos "<campos>" existentes
    Entao o filtro de itens retorna dados validos
    Exemplos:
      | campos    |
      | nome      |
      | tipo      |
      | nome,tipo |
  Esquema do Cenario: Filtrar itens de cadastros por valor invalido
    Quando filtro itens de cadastros pelo campo "<campo>" invalido
    Entao o filtro de itens retorna lista vazia
    Exemplos:
      | campo |
      | nome  |
      | tipo  |
  Cenario: Consultar item de cadastro por UUID valido
    Quando consulto um item de cadastro existente por UUID
    Entao o item de cadastro retorna dados validos
  Cenario: Consultar item de cadastro por UUID invalido
    Quando consulto um item de cadastro por UUID invalido
    Entao a operacao de item de cadastro retorna status 404
  Cenario: Consultar lista de nomes dos itens
    Quando consulto a lista de nomes dos itens de cadastros
    Entao a lista de nomes retorna status 200 e resultados
  Cenario: Consultar tipos dos itens
    Quando consulto os tipos de itens de cadastros
    Entao os tipos de itens retornam dados validos
  Cenario: Cadastrar item de cadastro valido
    Quando cadastro um item de cadastro valido
    Entao o item de cadastro e criado e removido com sucesso
  Cenario: Cadastrar item duplicado
    Quando cadastro duas vezes o mesmo item de cadastro
    Entao o segundo cadastro retorna status 400 e o item e removido
  Esquema do Cenario: Cadastrar item invalido
    Quando cadastro um item de cadastro com dados "<tipo>"
    Entao o cadastro invalido do item retorna status 400
    Exemplos:
      | tipo          |
      | tipo_invalido |
      | campos_vazios |
      | campos_ausentes |
  Cenario: Excluir item de cadastro valido
    Quando cadastro e excluo um item de cadastro
    Entao a exclusao do item retorna status 204
  Cenario: Excluir item de cadastro inexistente
    Quando excluo um item de cadastro por UUID invalido
    Entao a operacao de item de cadastro retorna status 404
  Cenario: Atualizar item por PUT
    Quando atualizo um item de cadastro por PUT com dados "validos"
    Entao a atualizacao valida do item retorna status 200 e realiza limpeza
  Esquema do Cenario: Atualizar item invalido por PUT
    Quando atualizo um item de cadastro por PUT com dados "<tipo>"
    Entao a atualizacao invalida do item retorna erro e realiza limpeza quando necessario
    Exemplos:
      | tipo          |
      | tipo_invalido |
      | duplicado     |
      | campos_vazios |
      | campos_ausentes |
  Cenario: Atualizar item por PATCH
    Quando atualizo um item de cadastro por PATCH com dados "validos"
    Entao a atualizacao valida do item retorna status 200 e realiza limpeza
  Esquema do Cenario: Atualizar item invalido por PATCH
    Quando atualizo um item de cadastro por PATCH com dados "<tipo>"
    Entao a atualizacao invalida do item retorna erro e realiza limpeza quando necessario
    Exemplos:
      | tipo          |
      | tipo_invalido |
      | duplicado     |
      | campos_vazios |
