# language: pt
Funcionalidade: Validar faixas etarias

  Contexto:
    Dado que estou autenticado na API como CODAE para consultar faixas etarias

  Cenario: Validar GET com sucesso de faixas etarias
    Quando consulto as faixas etarias
    Entao a consulta de faixas etarias deve retornar status 200 e dados paginados validos

  Esquema do Cenario: Consultar faixas com limite
    Quando consulto faixas etarias com limite <limite>
    Entao a consulta de faixas etarias deve retornar status 200 e dados paginados validos
    E a pagina de faixas etarias respeita o limite
    Exemplos:
      | limite |
      | 1      |
      | 2      |

  Cenario: Consultar faixa por deslocamento
    Quando consulto a segunda faixa etaria por deslocamento
    Entao a pagina retorna somente a segunda faixa etaria

  Cenario: Consultar depois da ultima faixa
    Quando consulto faixas etarias depois do total
    Entao a pagina de faixas etarias esta vazia

  Esquema do Cenario: Rejeitar acesso sem autenticacao valida
    Quando executo "<metodo>" em faixas etarias com acesso "<acesso>"
    Entao faixas etarias retorna status 401
    Exemplos:
      | metodo | acesso   |
      | GET    | ausente  |
      | GET    | invalido |
      | POST   | ausente  |
      | POST   | invalido |

  Esquema do Cenario: Rejeitar metodos nao permitidos
    Quando executo "<metodo>" em faixas etarias com acesso "valido"
    Entao faixas etarias retorna status 405
    Exemplos:
      | metodo |
      | PUT    |
      | PATCH  |
      | DELETE |

  Esquema do Cenario: Rejeitar cadastro invalido
    Quando cadastro faixas etarias com dados invalidos "<caso>"
    Entao a resposta de faixas etarias informa erro no campo "<campo>"
    Exemplos:
      | caso                   | campo                   |
      | sem justificativa      | justificativa           |
      | justificativa vazia    | justificativa           |
      | sem faixas             | faixas_etarias_ativadas  |
      | faixas nulas           | faixas_etarias_ativadas  |
      | faixas tipo invalido    | faixas_etarias_ativadas  |
      | sem inicio             | faixas_etarias_ativadas  |
      | sem fim                | faixas_etarias_ativadas  |
      | inicio texto           | faixas_etarias_ativadas  |
      | fim texto              | faixas_etarias_ativadas  |
      | inicio negativo        | faixas_etarias_ativadas  |
      | fim acima do limite    | faixas_etarias_ativadas  |
      | inicio igual ao fim    | faixas_etarias_ativadas  |
      | inicio maior que fim   | faixas_etarias_ativadas  |

  @ambiente_descartavel
  Cenario: Substituir faixas etarias com sucesso em ambiente descartavel
    Dado que o ambiente de faixas etarias e descartavel
    Quando substituo as faixas etarias por dados validos
    Entao as novas faixas etarias ficam ativas
