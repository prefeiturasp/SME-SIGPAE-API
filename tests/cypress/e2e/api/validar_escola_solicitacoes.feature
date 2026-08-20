# language: pt
Funcionalidade: Validar solicitacoes da escola
  Contexto:
    Dado que estou autenticado como diretor de escola para consultar solicitacoes

  Esquema do Cenario: Consultar agrupamentos de solicitacoes da escola
    Quando consulto solicitacoes da escola pelo agrupamento "<agrupamento>"
    Entao a consulta de solicitacoes da escola retorna uma lista paginada valida
    Exemplos:
      | agrupamento                         |
      | autorizadas temporariamente dieta  |
      | autorizados                         |
      | autorizados dieta                   |
      | cancelados                          |
      | cancelados dieta                    |
      | inativas dieta                      |
      | inativas temporariamente dieta      |
      | negados                             |
      | negados dieta                       |
      | pendentes autorizacao dieta         |
      | pendentes autorizacao               |
      | aguardando vigencia dieta           |

  Cenario: Consultar solicitacoes detalhadas da escola
    Quando consulto as solicitacoes detalhadas da escola
    Entao a consulta detalhada da escola retorna dados validos

  Esquema do Cenario: Consultar outros agrupamentos autorizados da escola
    Quando consulto solicitacoes da escola pelo agrupamento "<agrupamento>"
    Entao a consulta de solicitacoes da escola retorna resultados validos
    Exemplos:
      | agrupamento             |
      | kit lanches autorizadas |
      | suspensoes autorizadas  |
