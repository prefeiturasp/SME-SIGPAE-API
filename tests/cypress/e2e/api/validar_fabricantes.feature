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
