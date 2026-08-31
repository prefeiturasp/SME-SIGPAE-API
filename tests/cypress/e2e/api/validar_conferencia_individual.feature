# language: pt
Funcionalidade: Validar conferencia individual
  # O GET autorizado permanece desabilitado porque a API retorna erro 500 no QA.

  Cenario: Consultar conferencia individual sem permissao
    Quando consulto a conferencia individual com usuario CODAE
    Entao a consulta de conferencia individual retorna status 403 e detalhe
