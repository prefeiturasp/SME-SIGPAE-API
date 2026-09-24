# language: pt
Funcionalidade: Consultar dados completos do usuario EOL

  Cenario: Rejeitar consulta de registro funcional inexistente
    Dado que estou autenticado para consultar dados completos do usuario EOL
    Quando consulto dados completos do usuario EOL com RF inexistente
    Entao a consulta completa do usuario EOL retorna 400
    E a consulta completa do usuario EOL informa usuario nao encontrado

  Cenario: Rejeitar consulta completa do usuario EOL sem autenticacao
    Quando consulto dados completos do usuario EOL sem autenticacao
    Entao a consulta completa do usuario EOL retorna 401

  Cenario: Rejeitar consulta completa do usuario EOL com token invalido
    Quando consulto dados completos do usuario EOL com token invalido
    Entao a consulta completa do usuario EOL retorna 401
