# language: pt
Funcionalidade: Validar classificacoes de dieta
  Contexto:
    Dado que estou autenticado para consultar classificacoes de dieta
  Cenario: Consultar todas as classificacoes de dieta
    Quando consulto todas as classificacoes de dieta
    Entao a API retorna as classificacoes de dieta esperadas
  Cenario: Consultar classificacao de dieta por ID valido
    Quando consulto a classificacao de dieta pelo caminho "1/"
    Entao a API retorna a classificacao de dieta de ID 1
  Cenario: Consultar classificacao de dieta por ID invalido
    Quando consulto a classificacao de dieta pelo caminho "1111/"
    Entao a consulta de classificacao de dieta retorna status 404
