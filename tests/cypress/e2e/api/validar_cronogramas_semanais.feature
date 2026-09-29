# language: pt
Funcionalidade: Validar cronogramas semanais

  Contexto:
    Dado que estou autenticado para cronogramas semanais

  Esquema do Cenario: Consultar listagens semanais com sucesso
    Quando consulto cronogramas semanais pela operacao "<operacao>"
    Entao a consulta semanal retorna lista com sucesso
    Exemplos:
      | operacao |
      | get / |
      | get rascunhos/ |
      | get cronogramas-mensal-assinados/ |
      | get listagem-relatorio/ |
      | get calendario/ |

  Cenario: Consultar detalhe semanal com sucesso
    Quando consulto detalhe de cronograma semanal existente
    Entao o detalhe semanal corresponde ao UUID consultado

  Esquema do Cenario: Rejeitar UUID semanal inexistente
    Quando acesso semanal inexistente usando "<operacao>"
    Entao a operacao semanal retorna 404
    Exemplos:
      | operacao |
      | get {uuid}/ |
      | put {uuid}/ |
      | patch {uuid}/ |

  Esquema do Cenario: Rejeitar rascunho semanal invalido
    Quando cadastro rascunho semanal com mensal "<tipo>"
    Entao o rascunho semanal informa erro no cronograma mensal
    Exemplos:
      | tipo |
      | ausente |
      | inexistente |

  Esquema do Cenario: Rejeitar calendario semanal sem parametros validos
    Quando consulto calendario semanal com parametros "<parametros>"
    Entao a operacao semanal retorna 400
    Exemplos:
      | parametros |
      | ausentes |
      | invalidos |

  Esquema do Cenario: Exigir autenticacao nos metodos semanais
    Quando acesso operacao semanal "<operacao>" sem autenticacao
    Entao a operacao semanal retorna 401
    Exemplos:
      | operacao |
      | get / |
      | post / |
      | get {uuid}/ |
      | put {uuid}/ |
      | patch {uuid}/ |
      | patch {uuid}/alterar-cronograma/ |
      | patch {uuid}/assinar-e-enviar/ |
      | patch {uuid}/fornecedor-ciente/ |
      | get {uuid}/gerar-pdf-cronograma/ |
      | get calendario/ |
      | get cronogramas-mensal-assinados/ |
      | get gerar-relatorio-xlsx-async/ |
      | get listagem-relatorio/ |
      | post rascunho/ |
      | get rascunhos/ |
