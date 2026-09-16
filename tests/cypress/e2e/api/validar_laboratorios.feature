# language: pt
Funcionalidade: Validar laboratorios
  Contexto:
    Dado que estou autenticado como DILOG qualidade para gerenciar laboratorios
  Cenario: Consultar laboratorios
    Quando consulto todos os laboratorios
    Entao a consulta de laboratorios retorna status permitido e lista valida
  Esquema do Cenario: Filtrar laboratorios por valor existente
    Quando filtro laboratorios pelo campo existente "<campo>"
    Entao o filtro valido de laboratorios retorna dados coerentes
    Exemplos:
      | campo |
      | nome  |
      | cnpj  |
      | uuid  |
  Esquema do Cenario: Filtrar laboratorios por valor inexistente
    Quando filtro laboratorios pelo campo inexistente "<campo>"
    Entao o filtro inexistente retorna lista vazia ou permissao negada
    Exemplos:
      | campo |
      | nome  |
      | cnpj  |
      | uuid  |
  Cenario: Consultar laboratorio por UUID existente
    Quando consulto um laboratorio existente por UUID
    Entao o laboratorio por UUID retorna dados coerentes
  Cenario: Consultar laboratorio por UUID invalido
    Quando consulto um laboratorio por UUID invalido
    Entao a operacao de laboratorio retorna status de erro permitido
  Esquema do Cenario: Consultar listagens de laboratorios
    Quando consulto a listagem de laboratorios "<lista>"
    Entao a listagem de laboratorios retorna status permitido e dados validos
    Exemplos:
      | lista        |
      | completa     |
      | credenciados |
      | nomes        |
  Cenario: Cadastrar laboratorio valido
    Quando cadastro um laboratorio com dados "validos"
    Entao o cadastro valido retorna sucesso ou permissao negada e realiza limpeza
  Esquema do Cenario: Cadastrar laboratorio invalido
    Quando cadastro um laboratorio com dados "<tipo>"
    Entao o cadastro invalido retorna validacao ou permissao negada
    Exemplos:
      | tipo             |
      | booleanos_invalidos |
      | campos_em_branco |
      | campos_ausentes  |
  Cenario: Excluir laboratorio valido
    Quando cadastro e excluo um laboratorio valido
    Entao a exclusao valida retorna status permitido
  Cenario: Excluir laboratorio inexistente
    Quando excluo um laboratorio por UUID invalido
    Entao a operacao de laboratorio retorna status de erro permitido
  Cenario: Atualizar laboratorio valido por PUT
    Quando atualizo por PUT um laboratorio com dados "validos"
    Entao a atualizacao valida retorna sucesso ou permissao negada e realiza limpeza
  Esquema do Cenario: Atualizar laboratorio invalido por PUT
    Quando atualizo por PUT um laboratorio com dados "<tipo>"
    Entao a atualizacao invalida retorna validacao ou permissao negada e realiza limpeza
    Exemplos:
      | tipo                |
      | booleanos_invalidos |
      | campos_ausentes     |
      | campos_em_branco    |
  Cenario: Atualizar laboratorio inexistente por PUT
    Quando atualizo por PUT um laboratorio com UUID invalido
    Entao a operacao de laboratorio retorna status de erro permitido
  Cenario: Atualizar laboratorio valido por PATCH
    Quando atualizo por PATCH um laboratorio com dados "validos"
    Entao a atualizacao valida retorna sucesso ou permissao negada e realiza limpeza
  Esquema do Cenario: Atualizar laboratorio invalido por PATCH
    Quando atualizo por PATCH um laboratorio com dados "<tipo>"
    Entao a atualizacao invalida retorna validacao ou permissao negada e realiza limpeza
    Exemplos:
      | tipo                |
      | booleanos_invalidos |
      | campos_em_branco    |
  Cenario: Atualizar laboratorio inexistente por PATCH
    Quando atualizo por PATCH um laboratorio com UUID invalido
    Entao a operacao de laboratorio retorna status de erro permitido
