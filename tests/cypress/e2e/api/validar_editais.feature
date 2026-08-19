# language: pt
Funcionalidade: Validar editais
  Contexto:
    Dado que estou autenticado como DRE para consultar editais
  Cenario: Consultar lista de editais
    Quando consulto a lista de editais
    Entao a lista de editais retorna status 200 e os dados esperados
  Esquema do Cenario: Consultar edital por UUID
    Quando consulto um edital pelo UUID "<uuid>"
    Entao a consulta do edital retorna status <status>
    E quando encontrado apresenta os campos esperados do edital
    Exemplos:
      | uuid                                 | status |
      | e40ccae2-2080-4510-aeee-d1b8dcacc3b8 | 200    |
      | 3fa85f64-5717-4562-b3fc-2c963f66afa6 | 404    |
  Cenario: Consultar lista de numeros de editais
    Quando consulto a lista de numeros de editais
    Entao a lista de numeros de editais retorna status 200 e dados validos
