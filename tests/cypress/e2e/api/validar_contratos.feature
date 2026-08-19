# language: pt
Funcionalidade: Validar contratos
  Cenario: Consultar contratos paginados com sucesso
    Quando consulto dois contratos com usuario autorizado
    Entao a lista de contratos retorna status 200 e dois contratos validos
  Cenario: Consultar contratos sem autenticacao
    Quando consulto contratos sem autenticacao
    Entao a lista de contratos retorna status 401
  Cenario: Consultar contrato por UUID com sucesso
    Quando consulto o contrato pelo UUID valido
    Entao o contrato retorna status 200 e os dados esperados
  Cenario: Consultar contrato por UUID inexistente
    Quando consulto um contrato por UUID inexistente
    Entao o contrato inexistente retorna pagina HTML com status 404
