# language: pt
Funcionalidade: Validar dias uteis

  Contexto:
    Dado que estou autenticado como CODAE para consultar dias uteis

  Cenario: Consultar os proximos dias uteis
    Quando consulto os proximos dias uteis
    Entao a consulta de dias uteis retorna status 200 e as datas esperadas
