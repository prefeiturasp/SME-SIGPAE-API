# language: pt

Funcionalidade: Cadastro de Empresas

  Cenário: Cadastrar empresa com sucesso
    Dado que acesso o sistema
    E acesso o menu Cadastros > Empresas
    Quando preencho os campos obrigatórios de cadastro da empresa
    E clico no botão Salvar
    E confirmo a ação no modal de confirmação
    Então devo visualizar a mensagem "Empresa cadastrada com sucesso"