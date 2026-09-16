# language: pt
Funcionalidade: Validar terceirizadas
  Contexto:
    Dado que estou autenticado como CODAE para gerenciar terceirizadas
  Cenario: Consultar terceirizadas
    Quando consulto todas as terceirizadas
    Entao a lista de terceirizadas retorna dados completos
  Cenario: Consultar terceirizada por nome
    Quando consulto uma terceirizada por nome existente
    Entao a lista de terceirizadas retorna dados completos
  Cenario: Consultar terceirizada por UUID
    Quando consulto uma terceirizada por UUID existente
    Entao a terceirizada retorna dados completos
  Cenario: Consultar terceirizada por UUID invalido
    Quando consulto uma terceirizada por UUID invalido
    Entao a operacao de terceirizada retorna status 404
  Cenario: Cadastrar terceirizada
    Quando cadastro uma terceirizada valida
    Entao a terceirizada e criada e removida com sucesso
  Cenario: Cadastrar terceirizada com CPF duplicado
    Quando cadastro uma terceirizada com CPF de responsavel existente
    Entao o cadastro da terceirizada retorna status 400 e erro de CPF
  Cenario: Cadastrar terceirizada sem CNPJ
    Quando cadastro uma terceirizada com CNPJ em branco
    Entao o cadastro da terceirizada retorna status 400 e erro de CNPJ
  Cenario: Excluir terceirizada
    Quando cadastro e excluo uma terceirizada valida
    Entao a exclusao da terceirizada retorna status 204
  Cenario: Excluir terceirizada inexistente
    Quando excluo uma terceirizada por UUID invalido
    Entao a operacao de terceirizada retorna status 404
  Cenario: Atualizar terceirizada por PUT
    Quando atualizo uma terceirizada valida por PUT
    Entao a terceirizada e atualizada e removida com sucesso
  Cenario: Atualizar terceirizada inexistente por PUT
    Quando atualizo por PUT uma terceirizada com UUID invalido
    Entao a operacao de terceirizada retorna status 404
  Cenario: Atualizar terceirizada por PATCH
    Quando atualizo uma terceirizada valida por PATCH
    Entao a terceirizada e atualizada e removida com sucesso
  Cenario: Atualizar terceirizada inexistente por PATCH
    Quando atualizo por PATCH uma terceirizada com UUID invalido
    Entao a operacao de terceirizada retorna status 404
  Esquema do Cenario: Consultar listagens de terceirizadas
    Quando consulto a listagem de terceirizadas "<lista>"
    Entao a listagem "<lista>" retorna status 200 e dados validos
    Exemplos:
      | lista                |
      | emails_modulos       |
      | cnpjs                |
      | empresas_cronogramas |
      | nomes                |
      | distribuidores       |
      | simples              |
      | relatorio            |
