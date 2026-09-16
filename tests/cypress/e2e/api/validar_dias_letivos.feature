# language: pt
Funcionalidade: Validar dias letivos

  Cenario: Validar GET de dias letivos com sucesso
    Quando consulto os dias letivos com um usuario CODAE
    Entao a consulta de dias letivos retorna status 200 e uma lista valida

  Cenario: Validar GET de dias letivos sem permissao
    Quando consulto os dias letivos com um usuario diretor de UE
    Entao a consulta de dias letivos retorna status 403 e mensagem de permissao
