# language: pt
Funcionalidade: Validar documentos de recebimento
  Cenario: Consultar documentos de recebimento com sucesso
    Quando consulto documentos de recebimento com usuario autorizado
    Entao a consulta de documentos retorna status 200 e dados paginados validos
  Cenario: Consultar documentos de recebimento sem permissao
    Quando consulto documentos de recebimento com usuario CODAE
    Entao a consulta de documentos retorna status 403 e mensagem de permissao

  # O POST com sucesso permanece desabilitado porque nenhum usuario do .env possui permissao.

  Cenario: Gerar documentos de recebimento sem permissao
    Quando tento gerar documentos de recebimento com usuario CODAE
    Entao a geracao de documentos retorna status 403 e mensagem de permissao
