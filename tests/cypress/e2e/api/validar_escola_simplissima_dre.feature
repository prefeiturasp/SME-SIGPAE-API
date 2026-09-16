# language: pt
Funcionalidade: Validar escolas simplissimas com DRE
  Contexto:
    Dado que estou autenticado como CODAE para consultar escolas simplissimas com DRE
  Cenario: Consultar lista de escolas simplissimas com DRE
    Quando consulto a lista de escolas simplissimas com DRE
    Entao a lista de escolas simplissimas com DRE retorna dados paginados
  Esquema do Cenario: Consultar escola simplissima com DRE por UUID
    Quando consulto a escola simplissima com DRE pelo UUID "<uuid>"
    Entao a escola simplissima com DRE retorna status <status>
    E quando encontrada apresenta os dados completos da escola com DRE
    Exemplos:
      | uuid                                 | status |
      | 141af3ae-7fc1-4850-9da3-f3ecf224d270 | 200    |
      | 8f1da4a7-11b6-4a09-9eaa-6633d066f26b | 404    |
