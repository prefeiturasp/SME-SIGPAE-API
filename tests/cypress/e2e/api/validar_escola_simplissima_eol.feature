# language: pt
Funcionalidade: Validar escolas simplissimas com EOL
  Contexto:
    Dado que estou autenticado como CODAE para consultar escolas simplissimas com EOL
  Cenario: Consultar escolas simplissimas com EOL
    Quando consulto a lista de escolas simplissimas com EOL
    Entao a lista de escolas com EOL retorna status 200 e dados paginados
  Esquema do Cenario: Consultar escola simplissima com EOL por UUID
    Quando consulto a escola simplissima com EOL pelo UUID "<uuid>"
    Entao a escola simplissima com EOL retorna status <status>
    E quando encontrada apresenta os campos de EOL
    Exemplos:
      | uuid                                 | status |
      | 141af3ae-7fc1-4850-9da3-f3ecf224d270 | 200    |
      | 141af3ae-7fc1-4850-9da3-f3ecf224d271 | 404    |
