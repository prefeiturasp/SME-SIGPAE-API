# language: pt
Funcionalidade: Validar editais e contratos
  Contexto:
    Dado que estou autenticado como DRE para gerenciar editais e contratos
  Cenario: Consultar editais e contratos
    Quando consulto a lista de editais e contratos
    Entao a lista de editais e contratos retorna dados validos
  Esquema do Cenario: Consultar edital e contrato por UUID
    Quando consulto edital e contrato pelo UUID "<uuid>"
    Entao a consulta de edital e contrato retorna status <status>
    E quando encontrado apresenta os campos esperados
    Exemplos:
      | uuid                                 | status |
      | e40ccae2-2080-4510-aeee-d1b8dcacc3b8 | 200    |
      | 3fa85f64-5717-4562-b3fc-2c963f66afa6 | 404    |
  Cenario: Cadastrar edital e contrato
    Quando cadastro um edital e contrato valido
    Entao o edital e contrato e criado e removido com sucesso
  Cenario: Excluir edital e contrato
    Quando cadastro e excluo um edital e contrato valido
    Entao a exclusao do edital e contrato retorna status 204
  Cenario: Excluir edital e contrato inexistente
    Quando excluo um edital e contrato por UUID inexistente
    Entao a exclusao do edital e contrato retorna status 404
  Cenario: Atualizar edital e contrato por PUT
    Quando atualizo um edital e contrato valido por PUT
    Entao o edital e contrato e atualizado e removido com sucesso
  Cenario: Atualizar edital e contrato pelo fluxo PATCH existente
    Quando atualizo um edital e contrato pelo fluxo PATCH existente
    Entao o edital e contrato e atualizado e removido com sucesso
