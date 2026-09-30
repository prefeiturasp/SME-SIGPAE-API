# language: pt
Funcionalidade: Validar categorias de perguntas frequentes

  Esquema do Cenario: Consultar categorias FAQ com sucesso
    Dado que estou autenticado como "escola" para categorias FAQ
    Quando consulto "<operacao>" de categorias FAQ
    Entao a consulta de categorias FAQ retorna sucesso
    Exemplos:
      | operacao |
      | listar   |
      | opcoes   |
      | perguntas |

  @categoria_faq_criada
  Cenario: Cadastrar consultar atualizar e excluir categoria FAQ
    Dado que estou autenticado como "gestor" para categorias FAQ
    E que criei uma categoria FAQ de teste
    Quando consulto a categoria FAQ criada
    E atualizo a categoria FAQ usando "atualizar"
    E consulto a categoria FAQ criada
    E atualizo a categoria FAQ usando "parcial"
    E consulto a categoria FAQ criada
    E excluo a categoria FAQ criada

  Esquema do Cenario: Rejeitar cadastro com nome invalido
    Dado que estou autenticado como "gestor" para categorias FAQ
    Quando envio categoria FAQ com nome "<tipo>" usando "cadastrar"
    Entao a categoria FAQ retorna erro no nome
    Exemplos:
      | tipo     |
      | ausente  |
      | vazio    |
      | espacos  |
      | longo    |

  @categoria_faq_criada
  Esquema do Cenario: Rejeitar atualizacao com nome invalido
    Dado que estou autenticado como "gestor" para categorias FAQ
    E que criei uma categoria FAQ de teste
    Quando envio categoria FAQ com nome "<tipo>" usando "<operacao>"
    Entao a categoria FAQ retorna erro no nome
    Quando consulto a categoria FAQ criada
    Exemplos:
      | operacao  | tipo    |
      | atualizar | ausente |
      | atualizar | vazio   |
      | parcial   | vazio   |
      | parcial   | longo   |

  @categoria_faq_criada
  Cenario: Rejeitar categoria duplicada
    Dado que estou autenticado como "gestor" para categorias FAQ
    E que criei uma categoria FAQ de teste
    Quando tento cadastrar categoria FAQ duplicada
    Entao a categoria FAQ retorna erro no nome

  Esquema do Cenario: Rejeitar UUID inexistente
    Dado que estou autenticado como "gestor" para categorias FAQ
    Quando acesso categoria FAQ inexistente usando "<operacao>"
    Entao a operacao de categoria FAQ retorna 404
    Exemplos:
      | operacao  |
      | detalhar  |
      | atualizar |
      | parcial   |
      | excluir   |

  Esquema do Cenario: Bloquear gestao de categorias para escola
    Dado que estou autenticado como "escola" para categorias FAQ
    Quando acesso categoria FAQ inexistente usando "<operacao>"
    Entao a operacao de categoria FAQ retorna 403
    Exemplos:
      | operacao  |
      | cadastrar |
      | atualizar |
      | parcial   |
      | excluir   |

  Esquema do Cenario: Exigir autenticacao em todas as operacoes FAQ
    Quando acesso categorias FAQ sem autenticacao usando "<operacao>"
    Entao a operacao de categoria FAQ retorna 401
    Exemplos:
      | operacao  |
      | listar    |
      | cadastrar |
      | detalhar  |
      | atualizar |
      | parcial   |
      | excluir   |
      | opcoes    |
      | perguntas |
