# language: pt
Funcionalidade: Validar marcas
  Contexto:
    Dado que estou autenticado como CODAE para gerenciar marcas
  Cenario: Consultar marcas
    Quando consulto todas as marcas
    Entao a consulta de marcas retorna status 200 e lista valida
  Cenario: Consultar marcas por edital valido
    Quando consulto marcas por um edital existente
    Entao a consulta de marcas retorna status 200 e lista valida
  Cenario: Consultar marcas por edital invalido
    Quando consulto marcas por um edital invalido
    Entao a consulta de marcas retorna status 200 e lista vazia
  Cenario: Consultar marca por UUID valido
    Quando consulto uma marca existente por UUID
    Entao a marca retorna status 200 e o UUID esperado
  Cenario: Consultar marca por UUID invalido
    Quando consulto uma marca por UUID invalido
    Entao a operacao de marca retorna status 404
  Cenario: Cadastrar marca
    Quando cadastro uma marca valida para remocao
    Entao a marca e criada e removida com sucesso
  Cenario: Excluir marca
    Quando cadastro e excluo uma marca valida
    Entao a exclusao da marca retorna status 204
  Cenario: Excluir marca inexistente
    Quando excluo uma marca por UUID invalido
    Entao a operacao de marca retorna status 404
  Cenario: Atualizar marca por PUT
    Quando atualizo uma marca valida por PUT
    Entao a marca atualizada retorna o nome esperado e e removida
  Cenario: Atualizar marca inexistente por PUT
    Quando atualizo por PUT uma marca com UUID invalido
    Entao a operacao de marca retorna status 404
  Cenario: Atualizar marca por PATCH
    Quando atualizo uma marca valida por PATCH
    Entao a marca atualizada retorna o nome esperado e e removida
  Cenario: Atualizar marca inexistente por PATCH
    Quando atualizo por PATCH uma marca com UUID invalido
    Entao a operacao de marca retorna status 404
  Esquema do Cenario: Consultar listas de nomes de marcas
    Quando consulto a lista de marcas "<lista>"
    Entao a lista de nomes de marcas retorna status 200 e dados validos
    Exemplos:
      | lista                 |
      | nomes                 |
      | avaliar_reclamacao    |
      | nova_reclamacao       |
      | responder_reclamacao  |
  Cenario: Consultar marcas para resposta da escola
    Quando consulto marcas para resposta da escola
    Entao a lista da escola retorna status permitido e dados coerentes
  Cenario: Consultar marcas para resposta da nutrisupervisao
    Quando consulto marcas para resposta da nutrisupervisao
    Entao a lista de nomes de marcas retorna status 200 e dados validos
  Cenario: Consultar nomes unicos de marcas
    Quando consulto nomes unicos de marcas
    Entao a consulta de nomes unicos retorna status 200 e results
