# language: pt

Funcionalidade: Login

  Esquema do Cenário: Validar login com perfil "<perfil>"
    Dado que acesso o sistema
    Quando informo os dados do usuário "<perfil>" no dispositivo "<device>"
    E clico no botão acessar
    Então o sistema deve abrir a tela inicial

    Exemplos:
      | perfil                              | device |
      | COORDENADOR_LOGISTICA               | web    |
      | COORDENADOR_CODAE_DILOG_LOGISTICA   | web    |
      | COORDENADOR_SUPERVISAO_NUTRICAO     | web    |
      | DILOG_CRONOGRAMA                    | web    |
      | DILOG_QUALIDADE                     | web    |
      | ABASTECIMENTO                       | web    |
      | DIRETOR_UE                          | web    |
      | CODAE                               | web    |
      | GPCODAE                             | web    |
      | DRE                                 | web    |

  Esquema do Cenário: Validar mensagens de erro no login para "<perfil>"
    Dado que acesso o sistema
    Quando informo os dados do usuário "<perfil>" no dispositivo "<device>"
    E clico no botão acessar
    Então sistema apresenta "<mensagem>"

    Exemplos:
      | perfil              | device | mensagem                          |
      | USUARIO_INVALIDO    | web    | Não foi possível logar no sistema |
      | SENHA_INVALIDA      | web    | Não foi possível logar no sistema |
      | USUARIO_INEXISTENTE | web    | Não foi possível logar no sistema |
      | USUARIO_EM_BRANCO   | web    | Campo obrigatório                 |
      | SENHA_EM_BRANCO     | web    | Campo obrigatório                 |