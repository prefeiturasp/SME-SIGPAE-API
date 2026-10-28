# language: pt
Funcionalidade: Validar guias da requisicao

  Esquema do Cenario: Consultar guias com perfil correspondente
    Quando consulto guias da requisicao na rota "<rota>" com perfil "<perfil>"
    Entao guias da requisicao retorna uma lista valida
    Exemplos:
      | rota | perfil |
      | lista-numeros/ | logistica |
      | unidades-escolares/ | logistica |
      | inconsistencias/ | dilog |

  Esquema do Cenario: Rejeitar guia inexistente ou UUID malformado
    Quando executo "GET" em guias da requisicao na rota "<rota>" com acesso "autenticado"
    Entao guias da requisicao retorna status 404
    Exemplos:
      | rota |
      | 00000000-0000-0000-0000-000000000000/ |
      | uuid-invalido/ |

  Esquema do Cenario: Exigir autenticacao nos metodos disponiveis
    Quando executo "<metodo>" em guias da requisicao na rota "<rota>" com acesso "<acesso>"
    Entao guias da requisicao retorna status 401
    Exemplos:
      | metodo | rota | acesso |
      | GET | principal | ausente |
      | GET | principal | invalido |
      | POST | principal | ausente |
      | POST | principal | invalido |
      | GET | 00000000-0000-0000-0000-000000000000/ | ausente |
      | GET | 00000000-0000-0000-0000-000000000000/ | invalido |
      | PUT | 00000000-0000-0000-0000-000000000000/ | ausente |
      | PUT | 00000000-0000-0000-0000-000000000000/ | invalido |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | ausente |
      | PATCH | 00000000-0000-0000-0000-000000000000/ | invalido |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | ausente |
      | DELETE | 00000000-0000-0000-0000-000000000000/ | invalido |
      | GET | lista-numeros/ | ausente |
      | GET | lista-numeros/ | invalido |
      | GET | inconsistencias/ | ausente |
      | GET | inconsistencias/ | invalido |
      | GET | guias-escola/ | ausente |
      | GET | guias-escola/ | invalido |
      | GET | guia-para-conferencia/ | ausente |
      | GET | guia-para-conferencia/ | invalido |
      | GET | guias-com-ocorrencias-sem-notificacao/ | ausente |
      | GET | guias-com-ocorrencias-sem-notificacao/ | invalido |
      | GET | unidades-escolares/ | ausente |
      | GET | unidades-escolares/ | invalido |
      | GET | lista-guias-para-insucesso/ | ausente |
      | GET | lista-guias-para-insucesso/ | invalido |
      | GET | guia-para-insucesso/ | ausente |
      | GET | guia-para-insucesso/ | invalido |
      | PATCH | vincula-guias/ | ausente |
      | PATCH | vincula-guias/ | invalido |
      | GET | 00000000-0000-0000-0000-000000000000/gerar-pdf-distribuidor/ | ausente |
      | GET | 00000000-0000-0000-0000-000000000000/gerar-pdf-distribuidor/ | invalido |
      | GET | 00000000-0000-0000-0000-000000000000/relatorio-guia-remessa/ | ausente |
      | GET | 00000000-0000-0000-0000-000000000000/relatorio-guia-remessa/ | invalido |
      | GET | 00000000-0000-0000-0000-000000000000/detalhe-guia-de-remessa/ | ausente |
      | GET | 00000000-0000-0000-0000-000000000000/detalhe-guia-de-remessa/ | invalido |
