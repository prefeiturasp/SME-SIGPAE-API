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

  @listas_contratos
  Cenario: Consultar contratos de pos recebimento por empresa
    Quando consulto contratos de pos recebimento de uma empresa existente
    Entao os contratos de pos recebimento incluem o contrato da empresa

  @listas_contratos
  Cenario: Consultar numeros de contratos cadastrados
    Quando consulto os numeros de contratos cadastrados
    Entao a consulta retorna uma lista de numeros de contratos

  @listas_contratos
  Esquema do Cenario: Bloquear listas auxiliares de contratos sem autenticacao
    Quando consulto a lista auxiliar de contratos "<operacao>" sem autenticacao
    Entao a lista de contratos retorna status 401
    Exemplos:
      | operacao        |
      | pos_recebimento |
      | numeros         |

  @listas_contratos
  Esquema do Cenario: Consultar pos recebimento sem empresa valida
    Quando consulto contratos de pos recebimento com empresa "<condicao>"
    Entao a lista de contratos de pos recebimento fica vazia
    Exemplos:
      | condicao    |
      | ausente     |
      | invalida    |
      | inexistente |
