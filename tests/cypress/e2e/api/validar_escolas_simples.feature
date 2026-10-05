# language: pt
Funcionalidade: Validar escolas simples

  Cenario: Consultar listagem paginada
    Quando consulto a listagem de escolas simples
    Entao a operacao de escolas simples retorna 200
    E escolas simples retorna uma lista paginada valida

  Cenario: Consultar detalhe da escola
    Quando consulto o detalhe de uma escola simples existente
    Entao a operacao de escolas simples retorna 200
    E o detalhe de escolas simples corresponde a escola consultada

  Cenario: Validar deslocamento da paginacao
    Quando consulto escolas simples com deslocamento
    Entao a operacao de escolas simples retorna 200
    E escolas simples respeita o deslocamento

  Cenario: Consultar pagina alem do total
    Quando consulto escolas simples alem do total
    Entao a operacao de escolas simples retorna 200
    E escolas simples retorna pagina vazia

  Cenario: Aceitar PATCH vazio preservando dados
    Quando envio PATCH vazio para uma escola simples existente
    Entao a operacao de escolas simples retorna 200
    E o detalhe de escolas simples corresponde a escola consultada

  Cenario: Rejeitar PUT sem campos obrigatorios
    Quando envio PUT vazio para uma escola simples existente
    Entao a operacao de escolas simples retorna 400
    E escolas simples informa campos obrigatorios

  Esquema do Cenario: Rejeitar codigo EOL acima do limite
    Quando envio "<metodo>" com codigo EOL invalido para uma escola simples
    Entao a operacao de escolas simples retorna 400
    E escolas simples informa codigo EOL invalido
    Exemplos:
      | metodo |
      | PUT    |
      | PATCH  |

  Esquema do Cenario: Rejeitar escola inexistente
    Quando executo "<metodo>" em escolas simples na rota "detalhe" com acesso "autenticado"
    Entao a operacao de escolas simples retorna 404
    Exemplos:
      | metodo |
      | GET    |
      | PUT    |
      | PATCH  |

  Cenario: Rejeitar UUID malformado
    Quando executo "GET" em escolas simples na rota "malformado" com acesso "autenticado"
    Entao a operacao de escolas simples retorna 404

  Esquema do Cenario: Rejeitar acesso sem autenticacao
    Quando executo "<metodo>" em escolas simples na rota "<rota>" com acesso "anonimo"
    Entao a operacao de escolas simples retorna 401
    Exemplos:
      | metodo | rota     |
      | GET    | listagem |
      | GET    | detalhe  |
      | PUT    | detalhe  |
      | PATCH  | detalhe  |

  Esquema do Cenario: Rejeitar token invalido
    Quando executo "GET" em escolas simples na rota "<rota>" com acesso "token invalido"
    Entao a operacao de escolas simples retorna 401
    Exemplos:
      | rota     |
      | listagem |
      | detalhe  |

  Esquema do Cenario: Rejeitar metodos nao permitidos
    Quando executo "<metodo>" em escolas simples na rota "<rota>" com acesso "autenticado"
    Entao a operacao de escolas simples retorna 405
    Exemplos:
      | metodo | rota     |
      | POST   | listagem |
      | DELETE | detalhe  |
