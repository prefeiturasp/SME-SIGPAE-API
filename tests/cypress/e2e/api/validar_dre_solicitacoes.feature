# language: pt
Funcionalidade: Validar solicitacoes da DRE
  Contexto:
    Dado que estou autenticado para consultar solicitacoes da DRE

  Esquema do Cenario: Consultar agrupamentos de solicitacoes da DRE
    Quando consulto solicitacoes da DRE pelo agrupamento "<agrupamento>"
    Entao a consulta de solicitacoes da DRE retorna dados ou permissao negada
    Exemplos:
      | agrupamento                        |
      | aguardando codae                   |
      | autorizadas temporariamente dieta |
      | autorizados                        |
      | autorizados dieta                  |
      | cancelados                         |
      | cancelados dieta                   |
      | inativas dieta                     |
      | inativas temporariamente dieta     |
      | negados                            |
      | negados dieta                      |
      | pendentes autorizacao dieta        |
      | pendentes autorizacao              |

  Cenario: Consultar solicitacoes detalhadas da DRE
    Quando consulto as solicitacoes detalhadas da DRE
    Entao a consulta detalhada da DRE retorna dados ou permissao negada

  Esquema do Cenario: Consultar pendencias da DRE por filtro e visao
    Quando consulto pendencias da DRE com filtro "<filtro>" e visao "<visao>"
    Entao a consulta filtrada da DRE retorna dados ou permissao negada
    Exemplos:
      | filtro            | visao            |
      | daqui_a_7_dias    | dre              |
      | daqui_a_7_dias    | lote             |
      | daqui_a_7_dias    | tipo_solicitacao |
      | sem_filtro        | dre              |
      | sem_filtro        | lote             |
      | sem_filtro        | tipo_solicitacao |
      | daqui_a_30_dias   | dre              |
      | daqui_a_30_dias   | lote             |
      | daqui_a_30_dias   | tipo_solicitacao |
