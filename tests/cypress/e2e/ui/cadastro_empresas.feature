# language: pt

Funcionalidade: Cadastro de Empresas
  Como usuário Codae ou Cronograma
  Preciso realizar o cadastro de empresas
  Para que fiquem disponíveis no sistema

  Contexto:
    Dado que estou logado no sistema com usuário "Codae" e "senha"

  Cenário: Cadastro de empresa com sucesso
    Quando acesso o menu Cadastros > Empresas
    E preencho os campos obrigatórios de cadastro da empresa
    E clico no botão Salvar
    E confirmo a ação no modal de confirmação
    Então devo visualizar a mensagem "Empresa cadastrada com sucesso"
