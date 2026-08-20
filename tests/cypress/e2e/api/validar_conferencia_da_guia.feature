# language: pt
Funcionalidade: Validar conferencia da guia
  Contexto:
    Dado que estou autenticado como abastecimento para gerenciar conferencia da guia
  Cenario: Consultar conferencias da guia
    Quando consulto as conferencias da guia
    Entao a lista de conferencias retorna status permitido e dados validos
  Cenario: Cadastrar conferencia da guia valida
    Quando cadastro uma conferencia da guia com dados "validos"
    Entao o cadastro valido da conferencia retorna sucesso ou permissao e realiza limpeza
  Esquema do Cenario: Cadastrar conferencia da guia invalida
    Quando cadastro uma conferencia da guia com dados "<tipo>"
    Entao a conferencia invalida retorna erro no campo "<campo>" ou permissao negada
    Exemplos:
      | tipo             | campo            |
      | sem_placa        | placa_veiculo    |
      | sem_motorista    | nome_motorista   |
      | sem_data         | data_recebimento |
      | sem_hora         | hora_recebimento |
      | sem_guia         | guia             |
      | guia_invalida    | guia             |
  Cenario: Excluir conferencia da guia valida
    Quando cadastro e excluo uma conferencia da guia
    Entao a exclusao da conferencia retorna status permitido
  Cenario: Excluir conferencia da guia inexistente
    Quando excluo uma conferencia da guia por UUID invalido
    Entao a exclusao invalida retorna status 403 ou 404
  Cenario: Atualizar conferencia da guia valida por PUT
    Quando atualizo por PUT uma conferencia da guia com dados "validos"
    Entao a atualizacao valida da conferencia retorna sucesso ou permissao e realiza limpeza
  Esquema do Cenario: Atualizar conferencia da guia invalida por PUT
    Quando atualizo por PUT uma conferencia da guia com dados "<tipo>"
    Entao a conferencia invalida retorna erro no campo "<campo>" ou permissao negada
    Exemplos:
      | tipo             | campo            |
      | sem_placa        | placa_veiculo    |
      | sem_motorista    | nome_motorista   |
      | sem_data         | data_recebimento |
      | sem_hora         | hora_recebimento |
      | sem_guia         | guia             |
      | guia_invalida    | guia             |
  Cenario: Atualizar conferencia da guia valida por PATCH
    Quando atualizo por PATCH uma conferencia da guia com dados "validos"
    Entao a atualizacao valida da conferencia retorna sucesso ou permissao e realiza limpeza
  Esquema do Cenario: Atualizar conferencia da guia invalida por PATCH
    Quando atualizo por PATCH uma conferencia da guia com dados "<tipo>"
    Entao a conferencia invalida retorna erro no campo "<campo>" ou permissao negada
    Exemplos:
      | tipo             | campo            |
      | sem_placa        | placa_veiculo    |
      | sem_motorista    | nome_motorista   |
      | sem_data         | data_recebimento |
      | sem_hora         | hora_recebimento |
      | sem_guia         | guia             |
      | guia_invalida    | guia             |
