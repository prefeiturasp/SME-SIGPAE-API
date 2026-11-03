# language: pt
Funcionalidade: Validar grupos de suspensoes de alimentacao

  Esquema do Cenario: Consultar suspensoes com perfil correspondente
    Quando consulto grupos de suspensoes de alimentacao na rota "<rota>" com perfil "<perfil>"
    Entao a consulta de grupos de suspensoes de alimentacao retorna uma lista
    Exemplos:
      | rota | perfil |
      | informadas/ | escola |
      | tomados-ciencia/ | escola |
      | meus_rascunhos/ | escola |
      | pedidos-codae/sem_filtro/ | codae |

  Cenario: Consultar listagem principal com usuario configurado
    Quando consulto grupos de suspensoes de alimentacao na rota "principal" com perfil "escola"
    Entao a consulta de grupos de suspensoes de alimentacao retorna uma lista

  Cenario: Consultar grupo de suspensao inexistente
    Quando consulto grupo de suspensao de alimentacao inexistente
    Entao grupos de suspensoes de alimentacao retorna status 404

  Esquema do Cenario: Exigir autenticacao nos metodos disponiveis
    Quando executo "<metodo>" em grupos de suspensoes de alimentacao na rota "<rota>" com acesso "<acesso>"
    Entao grupos de suspensoes de alimentacao retorna status 401
    Exemplos:
      | metodo | rota | acesso |
      | GET | principal | ausente |
      | GET | principal | invalido |
      | POST | principal | ausente |
      | POST | principal | invalido |
      | GET | existente/ | invalido |
      | PUT | existente/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | invalido |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | ausente |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/informa-suspensao/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/informa-suspensao/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/escola-cancela/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/escola-cancela/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/terceirizada-toma-ciencia/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/terceirizada-toma-ciencia/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/marcar-conferida/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/marcar-conferida/ | invalido |
      | GET | 00000000-0000-0000-0000-000000000000/relatorio/ | ausente |
      | GET | 00000000-0000-0000-0000-000000000000/relatorio/ | invalido |
      | GET | informadas/ | ausente |
      | GET | informadas/ | invalido |
      | GET | tomados-ciencia/ | ausente |
      | GET | tomados-ciencia/ | invalido |
      | GET | meus_rascunhos/ | ausente |
      | GET | meus_rascunhos/ | invalido |
      | GET | pedidos-codae/sem_filtro/ | ausente |
      | GET | pedidos-codae/sem_filtro/ | invalido |
      | GET | pedidos-terceirizadas/sem_filtro/ | ausente |
      | GET | pedidos-terceirizadas/sem_filtro/ | invalido |

  Cenario: Consultar detalhe de suspensao existente
    Quando consulto um grupo de suspensao de alimentacao existente para "detalhe"
    Entao o detalhe da suspensao corresponde ao registro consultado

  Cenario: Gerar relatorio PDF de suspensao existente
    Quando consulto um grupo de suspensao de alimentacao existente para "PDF"
    Entao o relatorio da suspensao retorna um PDF
