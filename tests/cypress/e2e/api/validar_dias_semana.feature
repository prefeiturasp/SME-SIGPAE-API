# language: pt
Funcionalidade: Consultar dias da semana

  Cenario: Consultar os sete dias da semana com sucesso
    Quando consulto os dias da semana autenticado
    Entao a consulta dos dias da semana retorna os sete dias

  Esquema do Cenario: Rejeitar consulta dos dias da semana sem credencial valida
    Quando consulto os dias da semana com acesso "<acesso>"
    Entao a consulta dos dias da semana rejeita a autenticacao
    Exemplos:
      | acesso             |
      | sem autenticacao   |
      | token invalido     |
