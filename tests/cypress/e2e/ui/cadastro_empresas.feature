# language: pt

Funcionalidade: Cadastro de Empresas

  Cenário: Cadastrar empresa com sucesso
    Dado que acesso o sistema
<<<<<<< HEAD
    Quando informo os dados do usuário "DILOG_CRONOGRAMA" no dispositivo "web"
    E clico no botão acessar

  Cenário: Cadastro de empresa com sucesso
    Quando acesso o menu Cadastros > Empresas
    E preencho os campos obrigatórios de cadastro da empresa
=======
    E acesso o menu Cadastros > Empresas
    Quando preencho os campos obrigatórios de cadastro da empresa
>>>>>>> upstream/testes
    E clico no botão Salvar
    E confirmo a ação no modal de confirmação
    Então devo visualizar a mensagem "Empresa cadastrada com sucesso"
