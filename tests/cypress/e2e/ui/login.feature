# language: pt
Funcionalidade: Login

backgroud

  Esquema do Cenário: Validar Login para o cenário "<cenario>" 
    Dado eu acesso o sistema com a visualização "<device>"
    E informo os dados nos campos "<usuario>" e "<senha>"
    Quando clico no botão acessar
    Então sistema realiza validacao necessesaria "<mensagem>" para o cenario "<cenario>"

    Exemplos:
      | usuario     | senha      | device| mensagem 						             | cenario                                                   |
      | 07206148808 | adminadmin | web   | DILOG    						             |  COORDENADOR_LOGISTICA                     			         |
	    | 44481464720 | adminadmin | web	 | DISTRIBUIDOR    					         |  ADMINISTRADOR_EMPRESA                      				       |
	    | 45849486747 | adminadmin | web	 | UE 				      		             |  ADMINISTRADOR_UE										                     |
	    | 71317366000 | adminadmin | web	 | CEI PARCEIRA 					           |  DIRETOR_UE												                       |
	    | 34830129905 | adminadmin | web	 | DRE 		 						               |  COGESTOR_DRE										                         |
	    | 78716427742 | adminadmin | web	 | Terceirizada 					           |  ADMINISTRADOR_EMPRESA								                     |
      | 01341145409 | adminadmin | web	 | CODAE     						             |  COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA				       |
	    | 26088238070 | adminadmin | web	 |  NUTRICIONISTA SUPERVISAO 	       |  COORDENADOR_SUPERVISAO_NUTRICAO						               |
	    | 66118250103 | adminadmin | web	 | NUTRIMANIFESTACAO 	               |  COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAOCOGESTOR_DRE |
      | 3256563     | dsaa       | web   | Não foi possível logar no sistema | Usuario invalido                                          |
      | 24402217083 | admin      | web   | Não foi possível logar no sistema | Senha invalida                                            |
	    | 11111111111 | senhainv   | web   | Não foi possível logar no sistema | Usuario inexistente                                       |
      |             | adminadmin | web   | Campo obrigatório                 | Usuario em branco                                         |
      | 07206148808 |            | web   | Campo obrigatório                 | Senha em branco                                           |