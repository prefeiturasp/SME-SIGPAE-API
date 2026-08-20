# language: pt
Funcionalidade: Validar solicitacoes da CODAE
  Contexto:
    Dado que estou autenticado como CODAE para consultar solicitacoes

  Esquema do Cenario: Consultar agrupamentos de solicitacoes da CODAE
    Quando consulto solicitacoes da CODAE pelo agrupamento "<agrupamento>"
    Entao a consulta agrupada da CODAE retorna dados ou permissao negada
    Exemplos:
      | agrupamento                        |
      | pendentes autorizacao dieta        |
      | autorizados dieta                  |
      | inativas dieta                     |
      | negados dieta                      |
      | cancelados dieta                   |
      | autorizadas temporariamente dieta |
      | autorizados                        |
      | cancelados                         |
      | negados                            |
      | pendentes autorizacao              |
      | questionamentos                    |

  Cenario: Consultar dietas inativas temporariamente
    Quando consulto dietas inativas temporariamente na CODAE
    Entao a consulta agrupada da CODAE retorna uma lista paginada com status 200

  Cenario: Consultar solicitacoes detalhadas da CODAE
    Quando consulto solicitacoes detalhadas da CODAE
    Entao a consulta detalhada da CODAE retorna dados validos

  Esquema do Cenario: Consultar pendentes por filtro na CODAE
    Quando consulto pendentes da CODAE com filtro "<filtro>"
    Entao a consulta filtrada da CODAE retorna dados ou permissao negada
    Exemplos:
      | filtro          |
      | daqui_a_7_dias  |
      | sem_filtro      |
      | daqui_a_30_dias |

  Cenario: Consultar pendentes com filtro invalido na CODAE
    Quando consulto pendentes da CODAE com filtro "outro_filtro"
    Entao a consulta da CODAE retorna status 404

  Esquema do Cenario: Consultar pendentes por filtro e visao na CODAE
    Quando consulto pendentes da CODAE com filtro "<filtro>" e visao "<visao>"
    Entao a consulta filtrada por visao da CODAE retorna dados validos
    Exemplos:
      | filtro          | visao            |
      | daqui_a_7_dias  | dre              |
      | daqui_a_7_dias  | lote             |
      | daqui_a_7_dias  | tipo_solicitacao |
      | sem_filtro      | dre              |
      | sem_filtro      | lote             |
      | sem_filtro      | tipo_solicitacao |
      | daqui_a_30_dias | dre              |
      | daqui_a_30_dias | lote             |
      | daqui_a_30_dias | tipo_solicitacao |
