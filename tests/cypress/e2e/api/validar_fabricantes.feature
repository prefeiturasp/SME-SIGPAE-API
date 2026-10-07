# language: pt
Funcionalidade: Validar fabricantes
  Contexto:
    Dado que estou autenticado como CODAE para consultar fabricantes
  Cenario: Consultar fabricantes
    Quando consulto todos os fabricantes
    Entao a consulta de fabricantes retorna status 200 e uma lista valida
  
  Cenario: Consultar fabricante por UUID valido
    Quando consulto o fabricante pelo UUID valido
    Entao o fabricante retorna status 200 e os campos esperados
  
  Cenario: Consultar fabricante por UUID invalido
    Quando consulto o fabricante pelo UUID invalido
    Entao o fabricante invalido retorna status 403 ou 404
  
  Cenario: Consultar lista de nomes de fabricantes
    Quando consulto a lista de nomes de fabricantes
    Entao a consulta de fabricantes retorna status 200 e uma lista valida
  
  Cenario: Consultar fabricantes para avaliar reclamacao
    Quando consulto fabricantes para avaliar reclamacao
    Entao a consulta de fabricantes retorna status 200 e uma lista valida
  
  Cenario: Consultar fabricantes para nova reclamacao
    Quando consulto fabricantes para nova reclamacao
    Entao a consulta de fabricantes retorna status 200 e uma lista valida
  
  Cenario: Consultar fabricantes para responder reclamacao
    Quando consulto fabricantes para responder reclamacao
    Entao a consulta de fabricantes retorna status 200 e uma lista valida
  
  Cenario: Consultar fabricantes para resposta da escola
    Quando consulto fabricantes para resposta da escola
    Entao a consulta da escola retorna status permitido e dados coerentes
  
  Cenario: Consultar fabricantes para resposta da nutrisupervisao
    Quando consulto fabricantes para resposta da nutrisupervisao
    Entao a consulta retorna status 200 e uma propriedade results
  
  Cenario: Consultar nomes unicos de fabricantes
    Quando consulto nomes unicos de fabricantes
    Entao a consulta retorna status 200 e uma propriedade results

  Cenario: Criar atualizar parcialmente atualizar completamente e excluir fabricante temporario
    Quando executo o ciclo de cadastro e alteracao de fabricante
    Entao fabricantes retorna status 404

  Cenario: Rejeitar UUID malformado
    Quando consulto fabricante com UUID malformado
    Entao fabricantes retorna status 404

  Esquema do Cenario: Consultar fabricantes paginados
    Quando consulto fabricantes com limite <limite> e deslocamento <offset>
    Entao fabricantes retorna pagina com limite solicitado
    Exemplos:
      | limite | offset |
      | 1      | 0      |
      | 2      | 1      |

  Cenario: Consultar fabricantes depois do total
    Quando consulto fabricantes apos o total
    Entao fabricantes retorna lista vazia

  Cenario: Consultar fabricantes sem edital correspondente
    Quando consulto fabricantes com edital inexistente
    Entao fabricantes retorna lista vazia

  Cenario: Filtrar nomes por reclamacoes
    Quando consulto nomes de fabricantes filtrados por reclamacoes
    Entao a consulta de fabricantes retorna status 200 e uma lista valida

  Cenario: Negar rota exclusiva de escola ao perfil CODAE
    Quando consulto reclamacao de escola com perfil CODAE
    Entao fabricantes retorna status 403

  Esquema do Cenario: Negar consultas sem autenticacao valida
    Quando consulto fabricantes na rota "<rota>" com acesso "<acesso>"
    Entao fabricantes retorna status 401
    Exemplos:
      | rota                                               | acesso   |
      | lista                                              | ausente  |
      | lista                                              | invalido |
      | 00000000-0000-0000-0000-000000000000               | ausente  |
      | 00000000-0000-0000-0000-000000000000               | invalido |
      | lista-nomes                                        | ausente  |
      | lista-nomes                                        | invalido |
      | lista-nomes-avaliar-reclamacao                      | ausente  |
      | lista-nomes-avaliar-reclamacao                      | invalido |
      | lista-nomes-nova-reclamacao                         | ausente  |
      | lista-nomes-nova-reclamacao                         | invalido |
      | lista-nomes-responder-reclamacao                    | ausente  |
      | lista-nomes-responder-reclamacao                    | invalido |
      | lista-nomes-responder-reclamacao-escola             | ausente  |
      | lista-nomes-responder-reclamacao-escola             | invalido |
      | lista-nomes-responder-reclamacao-nutrisupervisor     | ausente  |
      | lista-nomes-responder-reclamacao-nutrisupervisor     | invalido |
      | lista-nomes-unicos                                 | ausente  |
      | lista-nomes-unicos                                 | invalido |
