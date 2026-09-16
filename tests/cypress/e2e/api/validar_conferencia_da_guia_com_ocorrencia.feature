# language: pt
Funcionalidade: Validar conferencia da guia com ocorrencia
  Contexto:
    Dado que estou autenticado como abastecimento para conferencia com ocorrencia
  Cenario: Listar conferencias com ocorrencia
    Quando consulto a lista de conferencias com ocorrencia
    Entao a lista de conferencias com ocorrencia retorna dados validos
  Cenario: Consultar conferencia com ocorrencia por UUID
    Quando consulto uma conferencia com ocorrencia existente por UUID
    Entao a conferencia com ocorrencia retorna os dados esperados
  Cenario: Consultar conferencia com ocorrencia inexistente
    Quando consulto uma conferencia com ocorrencia por UUID inexistente
    Entao a conferencia com ocorrencia retorna status 404
  Cenario: Atualizar conferencia ativa por PUT
    Quando atualizo por PUT uma conferencia com ocorrencia ativa
    Entao a atualizacao da conferencia retorna status 200 e o UUID esperado
  Cenario: Atualizar conferencia de guia arquivada
    Quando atualizo por PUT uma conferencia vinculada a guia arquivada
    Entao a atualizacao da conferencia arquivada retorna status 400
  Cenario: Atualizar parcialmente conferencia ativa
    Quando atualizo por PATCH uma conferencia com ocorrencia ativa
    Entao a atualizacao da conferencia retorna status 200 e o UUID esperado
  Cenario: Atualizar parcialmente conferencia inexistente
    Quando atualizo por PATCH uma conferencia com ocorrencia inexistente
    Entao a conferencia com ocorrencia retorna status 404
  Cenario: Excluir conferencia inexistente
    Quando excluo uma conferencia com ocorrencia inexistente
    Entao a conferencia com ocorrencia retorna status 404
  Cenario: Cadastrar conferencia com ocorrencia
    Quando cadastro uma conferencia da guia com ocorrencia valida
    Entao o cadastro da conferencia com ocorrencia retorna status 201 e dados validos
  Cenario: Cadastrar conferencia com dados invalidos
    Quando cadastro uma conferencia com ocorrencia invalida
    Entao o cadastro da conferencia com ocorrencia retorna status 400
