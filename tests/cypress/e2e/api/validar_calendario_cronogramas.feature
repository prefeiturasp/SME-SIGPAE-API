# language: pt
Funcionalidade: Validar calendario de cronogramas
  Contexto:
    Dado que estou autenticado para consultar o calendario de cronogramas
  Esquema do Cenario: Consultar calendario de cronogramas sem permissao
    Quando consulto o calendario de cronogramas com parametros "<parametros>"
    Entao o calendario de cronogramas retorna status 403 e detalhe
    Exemplos:
      | parametros          |
      | /?mes=3&ano=2025    |
      |                     |
      | /?mes=3&ano=202     |
      | /?mes=13&ano=2025   |
