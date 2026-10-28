# language: pt
Funcionalidade: Validar homologacoes de produtos

  Cenario: Consultar numero de protocolo para analise sensorial
    Quando consulto o numero de protocolo de homologacoes de produtos
    Entao homologacoes de produtos retorna um protocolo valido

  Esquema do Cenario: Rejeitar homologacao inexistente ou UUID malformado
    Quando executo "GET" em homologacoes de produtos na rota "<rota>" com acesso "autenticado"
    Entao homologacoes de produtos retorna status 404
    Exemplos:
      | rota |
      | 00000000-0000-0000-0000-000000000000/ |
      | uuid-invalido/ |
      | 00000000-0000-0000-0000-000000000000/reclamacao/ |
      | 00000000-0000-0000-0000-000000000000/gerar-pdf-ficha-identificacao-produto/ |

  Esquema do Cenario: Rejeitar metodos indisponiveis no detalhe
    Quando executo "<metodo>" em homologacoes de produtos na rota "00000000-0000-0000-0000-000000000000/" com acesso "autenticado"
    Entao homologacoes de produtos retorna status 405
    Exemplos:
      | metodo |
      | POST |
      | PUT |
      | PATCH |

  Esquema do Cenario: Exigir autenticacao nas consultas
    Quando executo "GET" em homologacoes de produtos na rota "<rota>" com acesso "<acesso>"
    Entao homologacoes de produtos retorna status 401
    Exemplos:
      | rota | acesso |
      | numero_protocolo/ | ausente |
      | numero_protocolo/ | invalido |
      | aguardando-analise-sensorial/ | ausente |
      | aguardando-analise-sensorial/ | invalido |
      | 00000000-0000-0000-0000-000000000000/ | ausente |
      | 00000000-0000-0000-0000-000000000000/ | invalido |
      | 00000000-0000-0000-0000-000000000000/reclamacao/ | ausente |
      | 00000000-0000-0000-0000-000000000000/reclamacao/ | invalido |
      | 00000000-0000-0000-0000-000000000000/gerar-pdf-ficha-identificacao-produto/ | ausente |
      | 00000000-0000-0000-0000-000000000000/gerar-pdf-ficha-identificacao-produto/ | invalido |
      | 00000000-0000-0000-0000-000000000000/vinculos-ativos-produto-edital/ | ausente |
      | 00000000-0000-0000-0000-000000000000/vinculos-ativos-produto-edital/ | invalido |

  Esquema do Cenario: Exigir autenticacao nas acoes de homologacao
    Quando executo "<metodo>" em homologacoes de produtos na rota "00000000-0000-0000-0000-000000000000/<acao>" com acesso "<acesso>"
    Entao homologacoes de produtos retorna status 401
    Exemplos:
      | metodo | acao | acesso |
      | DELETE | | ausente |
      | DELETE | | invalido |
      | POST | gerar-pdf/ | ausente |
      | POST | gerar-pdf/ | invalido |
      | PATCH | codae-homologa/ | ausente |
      | PATCH | codae-homologa/ | invalido |
      | PATCH | codae-nao-homologa/ | ausente |
      | PATCH | codae-nao-homologa/ | invalido |
      | PATCH | codae-questiona-pedido/ | ausente |
      | PATCH | codae-questiona-pedido/ | invalido |
      | PATCH | codae-pede-analise-sensorial/ | ausente |
      | PATCH | codae-pede-analise-sensorial/ | invalido |
      | PATCH | codae-cancela-analise-sensorial/ | ausente |
      | PATCH | codae-cancela-analise-sensorial/ | invalido |
      | PATCH | codae-cancela-solicitacao-correcao/ | ausente |
      | PATCH | codae-cancela-solicitacao-correcao/ | invalido |
      | PATCH | terceirizada-cancela-solicitacao-correcao/ | ausente |
      | PATCH | terceirizada-cancela-solicitacao-correcao/ | invalido |
      | PATCH | escola-ou-nutri-reclama/ | ausente |
      | PATCH | escola-ou-nutri-reclama/ | invalido |
      | PATCH | codae-pede-analise-reclamacao/ | ausente |
      | PATCH | codae-pede-analise-reclamacao/ | invalido |
      | PATCH | codae-aceita-reclamacao/ | ausente |
      | PATCH | codae-aceita-reclamacao/ | invalido |
      | PATCH | codae-recusa-reclamacao/ | ausente |
      | PATCH | codae-recusa-reclamacao/ | invalido |
      | PATCH | suspender/ | ausente |
      | PATCH | suspender/ | invalido |
      | PATCH | ativar/ | ausente |
      | PATCH | ativar/ | invalido |
      | PATCH | terceirizada-responde-reclamacao/ | ausente |
      | PATCH | terceirizada-responde-reclamacao/ | invalido |
      | PATCH | cancela-solicitacao-homologacao/ | ausente |
      | PATCH | cancela-solicitacao-homologacao/ | invalido |
      | PATCH | alteracao-produto-homologado/ | ausente |
      | PATCH | alteracao-produto-homologado/ | invalido |
