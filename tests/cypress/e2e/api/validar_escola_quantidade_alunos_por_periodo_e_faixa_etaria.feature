# language: pt
Funcionalidade: Validar somatorio de alunos por faixa etaria

  Cenario: Consultar somatorio de faixas etarias com sucesso
    Quando consulto o somatorio de faixas etarias de uma escola existente
    Entao a operacao de somatorio de faixas etarias retorna 200
    E o somatorio de faixas etarias retorna quantidades validas

  Esquema do Cenario: Rejeitar autenticacao ausente ou invalida
    Quando consulto o somatorio de faixas etarias com acesso "<acesso>"
    Entao a operacao de somatorio de faixas etarias retorna 401
    E o somatorio de faixas etarias informa erro de autenticacao
    Exemplos:
      | acesso         |
      | anonimo        |
      | token invalido |

  Esquema do Cenario: Rejeitar UUID de escola invalido ou inexistente
    Quando consulto o somatorio de faixas etarias para o UUID "<uuid>"
    Entao a operacao de somatorio de faixas etarias retorna 404
    Exemplos:
      | uuid                                 |
      | 00000000-0000-0000-0000-000000000000 |
      | uuid-invalido                        |

  Esquema do Cenario: Informar erro para data de referencia invalida
    Quando consulto o somatorio de faixas etarias com data "<data>"
    Entao a operacao de somatorio de faixas etarias retorna 200
    E o somatorio de faixas etarias informa data invalida
    Exemplos:
      | data          |
      | data-invalida |
      | 2026-02-30    |

  Esquema do Cenario: Rejeitar metodos nao permitidos no somatorio
    Quando executo "<metodo>" na rota de somatorio de faixas etarias
    Entao a operacao de somatorio de faixas etarias retorna 405
    Exemplos:
      | metodo |
      | POST   |
      | PUT    |
      | PATCH  |
      | DELETE |
