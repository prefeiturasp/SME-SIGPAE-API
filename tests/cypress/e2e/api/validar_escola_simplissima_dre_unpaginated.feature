# language: pt
Funcionalidade: Validar escolas simplissimas com DRE sem paginacao

  Contexto:
    Dado que estou autenticado como CODAE para consultar escola simplissima sem paginacao

  Esquema do Cenario: Consultar escola simplissima por UUID
    Quando consulto a escola simplissima sem paginacao pelo UUID "<uuid>"
    Entao a consulta da escola simplissima sem paginacao retorna status <status>
    E quando encontrada apresenta os dados esperados da escola

    Exemplos:
      | uuid                                 | status |
      | 141af3ae-7fc1-4850-9da3-f3ecf224d270 | 200    |
      | 141af3ae-7fc1-4850-9da3-f3ecf224d271 | 404    |
