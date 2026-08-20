# language: pt
Funcionalidade: Validar escolas simplissimas
  Contexto:
    Dado que estou autenticado como CODAE para consultar escolas simplissimas
  Cenario: Consultar lista de escolas simplissimas
    Quando consulto a lista de escolas simplissimas
    Entao a lista de escolas simplissimas retorna dados paginados
  Cenario: Consultar escolas simplissimas por UUID da DRE
    Quando consulto escolas simplissimas pelo UUID da DRE
    Entao a consulta por UUID retorna escolas simplissimas validas
  Cenario: Consultar escolas simplissimas pelo filtro de DRE
    Quando filtro escolas simplissimas pela DRE
    Entao a consulta filtrada retorna escolas vinculadas a DRE
