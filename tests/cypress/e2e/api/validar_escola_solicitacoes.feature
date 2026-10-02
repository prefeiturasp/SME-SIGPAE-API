# language: pt
Funcionalidade: Validar solicitacoes da escola
  Contexto:
    Dado que estou autenticado como diretor de escola para consultar solicitacoes

  Esquema do Cenario: Consultar agrupamentos de solicitacoes da escola
    Quando consulto solicitacoes da escola pelo agrupamento "<agrupamento>"
    Entao a consulta de solicitacoes da escola retorna uma lista paginada valida
    Exemplos:
      | agrupamento                       |
      | autorizadas temporariamente dieta |
      | autorizados                       |
      | autorizados dieta                 |
      | cancelados                        |
      | cancelados dieta                  |
      | inativas dieta                    |
      | inativas temporariamente dieta    |
      | negados                           |
      | negados dieta                     |
      | pendentes autorizacao dieta       |
      | pendentes autorizacao             |
      | aguardando vigencia dieta         |

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

  Esquema do Cenario: Consultar agrupamentos mensais faltantes da escola
    Quando consulto a rota mensal da escola "<rota>"
    Entao a consulta de solicitacoes da escola retorna resultados validos
    Exemplos:
      | rota                               |
      | alteracoes-alimentacao-autorizadas |
      | inclusoes-autorizadas              |
      | inclusoes-etec-autorizadas         |

  Cenario: Consultar periodos com solicitacoes autorizadas do CEU Gestao
    Quando consulto a rota mensal da escola "ceu-gestao-periodos-com-solicitacoes-autorizadas"
    Entao a consulta de periodos da escola retorna uma lista valida

  Cenario: Consultar ultimo dia com solicitacao autorizada no mes
    Quando consulto a rota mensal da escola "ultimo-dia-com-solicitacao-autorizada-no-mes"
    Entao a consulta da escola retorna a ultima data ou nenhum resultado

  Esquema do Cenario: Filtrar relatorios de solicitacoes da escola
    Quando envio os filtros de solicitacoes da escola para "<rota>"
    Entao o relatorio de solicitacoes da escola retorna dados validos
    Exemplos:
      | rota                                     |
      | filtrar-solicitacoes-ga                  |
      | filtrar-solicitacoes-cards-totalizadores |
      | filtrar-solicitacoes-graficos            |

  Esquema do Cenario: Solicitar exportacao de solicitacoes da escola
    Quando envio os filtros de solicitacoes da escola para "<rota>"
    Entao a exportacao de solicitacoes da escola confirma o recebimento
    Exemplos:
      | rota          |
      | exportar-pdf  |
      | exportar-xlsx |

  Esquema do Cenario: Rejeitar metodos nao permitidos em solicitacoes da escola
    Quando executo "<metodo>" na rota de solicitacoes da escola "<rota>" com acesso "autenticado"
    Entao a operacao de solicitacoes da escola retorna 405
    Exemplos:
      | metodo | rota                    |
      | POST   | autorizados             |
      | PUT    | autorizados             |
      | DELETE | autorizados             |
      | GET    | filtrar-solicitacoes-ga |

  Esquema do Cenario: Rejeitar solicitacoes da escola sem autenticacao
    Quando executo "<metodo>" na rota de solicitacoes da escola "<rota>" com acesso "anonimo"
    Entao a operacao de solicitacoes da escola retorna 401
    Exemplos:
      | metodo | rota                                             |
      | GET    | aguardando-vigencia-dieta/{escola_uuid}          |
      | GET    | alteracoes-alimentacao-autorizadas               |
      | GET    | autorizadas-temporariamente-dieta/{escola_uuid}  |
      | GET    | autorizados                                      |
      | GET    | autorizados-dieta/{escola_uuid}                  |
      | GET    | cancelados                                       |
      | GET    | cancelados-dieta/{escola_uuid}                   |
      | GET    | ceu-gestao-periodos-com-solicitacoes-autorizadas |
      | POST   | exportar-pdf                                     |
      | POST   | exportar-xlsx                                    |
      | POST   | filtrar-solicitacoes-cards-totalizadores         |
      | POST   | filtrar-solicitacoes-ga                          |
      | POST   | filtrar-solicitacoes-graficos                    |
      | GET    | inativas-dieta/{escola_uuid}                     |
      | GET    | inativas-temporariamente-dieta/{escola_uuid}     |
      | GET    | inclusoes-autorizadas                            |
      | GET    | inclusoes-etec-autorizadas                       |
      | GET    | kit-lanches-autorizadas                          |
      | GET    | negados                                          |
      | GET    | negados-dieta/{escola_uuid}                      |
      | GET    | pendentes-autorizacao                            |
      | GET    | pendentes-autorizacao-dieta/{escola_uuid}        |
      | GET    | solicitacoes-detalhadas                          |
      | GET    | suspensoes-autorizadas                           |
      | GET    | ultimo-dia-com-solicitacao-autorizada-no-mes     |
