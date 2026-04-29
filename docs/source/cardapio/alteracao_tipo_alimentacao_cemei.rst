alteracao\_tipo\_alimentacao\_cemei
====================================

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei
   :members:
   :show-inheritance:

admin
-----

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.admin
   :members:
   :show-inheritance:
   :exclude-members: extra, inlines, list_display, list_filter, media, model

models
------

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.models
   :members:
   :show-inheritance:
   :exclude-members:
      AlteracaoCardapioCEMEI,
      DataIntervaloAlteracaoCardapioCEMEI,
      DoesNotExist,
      FaixaEtariaSubstituicaoAlimentacaoCEMEICEI,
      MultipleObjectsReturned,
      SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI,
      SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI

.. autoclass:: AlteracaoCardapioCEMEI
   :members:
   :show-inheritance:
   :exclude-members:
      alunos_cei_e_ou_emei,
      alterar_dia,
      CEI,
      criado_em,
      criado_por,
      criado_por_id,
      data_final,
      data_inicial,
      datas_intervalo,
      DESCRICAO,
      desta_semana,
      deste_mes,
      EMEI,
      escola,
      escola_id,
      foi_solicitado_fora_do_prazo,
      DoesNotExist,
      get_alunos_cei_e_ou_emei_display,
      get_next_by_criado_em,
      get_previous_by_criado_em,
      get_status_display,
      id,
      motivo,
      motivo_id,
      MultipleObjectsReturned,
      objects,
      observacao,
      rastro_dre,
      rastro_dre_id,
      rastro_escola,
      rastro_escola_id,
      rastro_lote,
      rastro_lote_id,
      rastro_terceirizada,
      rastro_terceirizada_id,
      STATUS_CHOICES,
      status,
      substituicoes_cemei_cei_periodo_escolar,
      substituicoes_cemei_emei_periodo_escolar,
      terceirizada_conferiu_gestao,
      TODOS,
      uuid

   .. attribute:: alunos_cei_e_ou_emei
      :type: str

      **Origem:**
      ``alteracao_tipo_alimentacao_cemei/models.py``

      **Descrição:**
      Indica quais alunos são afetados pela solicitação: apenas CEI, apenas EMEI ou ambos (TODOS).

      Os valores possíveis são definidos pela constante ``STATUS_CHOICES``:

      - ``TODOS`` — todos os alunos (padrão)
      - ``CEI`` — apenas alunos da parte CEI
      - ``EMEI`` — apenas alunos da parte EMEI

   .. attribute:: alterar_dia
      :type: datetime.date | None

      **Origem:**
      ``alteracao_tipo_alimentacao_cemei/models.py``

      **Descrição:**
      Data única para a qual a substituição de alimentação se aplica.

      Quando preenchido, indica que a solicitação é de dia único.
      Mutuamente exclusivo com ``data_inicial`` / ``data_final``.
      Pode ser ``None`` quando a solicitação utiliza intervalo de datas.

   .. attribute:: criado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Timestamp preenchido automaticamente na criação do registro.

   .. attribute:: criado_por
      :type: perfil.Usuario | None

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Usuário responsável pela criação do registro.
      O campo ainda permite ``null`` e ``blank``.

   .. attribute:: criado_por_id
      :type: int | None

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Identificador do usuário responsável pela criação do registro.

      Corresponde à chave primária de :class:`perfil.Usuario`.
      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: data_inicial
      :type: datetime.date | None

      **Origem:**
      ``alteracao_tipo_alimentacao_cemei/models.py``

      **Descrição:**
      Data de início do intervalo de substituição de alimentação.

      Quando preenchido, indica que a solicitação abrange um período de datas.
      Deve ser usado em conjunto com ``data_final``.
      Pode ser ``None`` quando a solicitação é de dia único (``alterar_dia``).

   .. attribute:: data_final
      :type: datetime.date | None

      **Origem:**
      ``alteracao_tipo_alimentacao_cemei/models.py``

      **Descrição:**
      Data de fim do intervalo de substituição de alimentação.

      Deve ser usado em conjunto com ``data_inicial``.
      Pode ser ``None`` quando a solicitação é de dia único (``alterar_dia``).

   .. attribute:: datas_intervalo
      :type: django.db.models.QuerySet[DataIntervaloAlteracaoCardapioCEMEI]

      Relação reversa 1:N com :class:`DataIntervaloAlteracaoCardapioCEMEI`.

      Representa as datas individuais do intervalo de substituição, permitindo
      cancelamentos pontuais por data.

   .. attribute:: escola
      :type: escola.Escola | None

      **Origem:**
      :class:`EhAlteracaoCardapio`

      **Descrição:**
      Escola que efetuou a solicitação de alteração do tipo de alimentação.
      O campo ainda permite ``null`` e ``blank``.

   .. attribute:: escola_id
      :type: int | None

      **Origem:**
      :class:`EhAlteracaoCardapio`

      **Descrição:**
      Identificador da escola que efetuou a solicitação de alteração do tipo de alimentação.

      Corresponde à chave primária de :class:`escola.Escola`.
      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: foi_solicitado_fora_do_prazo
      :type: bool

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Indica se a solicitação foi criada fora do prazo regular de antecedência.

      Quando ``True``, significa que o pedido foi criado com 5 dias úteis ou menos de antecedência.

   .. attribute:: id
      :type: int

      **Origem:**
      ``django.db.models.Model``

      **Descrição:**
      Identificador interno do registro no banco de dados.

      Corresponde à chave primária gerada automaticamente pelo Django.

   .. attribute:: motivo
      :type: cardapio.MotivoAlteracaoCardapio | None

      **Origem:**
      :class:`EhAlteracaoCardapio`

      **Descrição:**
      Motivo associado à solicitação de alteração do tipo de alimentação.
      O campo ainda permite ``null`` e ``blank``.

   .. attribute:: motivo_id
      :type: int | None

      **Origem:**
      :class:`EhAlteracaoCardapio`

      **Descrição:**
      Identificador do motivo associado à solicitação de alteração do tipo de alimentação.

      Corresponde à chave primária de :class:`MotivoAlteracaoCardapio`.
      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: observacao
      :type: str

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Campo de texto livre para registrar observações complementares da solicitação.

      Pode ser uma string vazia, pois o campo permite ``blank``.

   .. attribute:: rastro_dre
      :type: escola.DiretoriaRegional | None

      **Origem:**
      :class:`FluxoAprovacaoPartindoDaEscola`

      **Descrição:**
      Diretoria Regional de Educação vinculada ao rastro histórico da solicitação.

      Representa a DRE da escola no momento em que o rastro do pedido foi salvo.

   .. attribute:: rastro_dre_id
      :type: int | None

      **Origem:**
      :class:`FluxoAprovacaoPartindoDaEscola`

      **Descrição:**
      Identificador da DRE vinculada ao rastro histórico da solicitação.

      Corresponde à chave primária de :class:`escola.DiretoriaRegional`.
      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: rastro_escola
      :type: escola.Escola | None

      **Origem:**
      :class:`FluxoAprovacaoPartindoDaEscola`

      **Descrição:**
      Escola registrada no rastro histórico da solicitação.

      Representa a escola vinculada ao pedido no momento em que o rastro foi salvo.

   .. attribute:: rastro_escola_id
      :type: int | None

      **Origem:**
      :class:`FluxoAprovacaoPartindoDaEscola`

      **Descrição:**
      Identificador da escola registrada no rastro histórico da solicitação.

      Corresponde à chave primária de :class:`escola.Escola`.
      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: rastro_lote
      :type: escola.Lote | None

      **Origem:**
      :class:`FluxoAprovacaoPartindoDaEscola`

      **Descrição:**
      Lote registrado no rastro histórico da solicitação.

      Representa o lote da escola no momento em que o rastro foi salvo.

   .. attribute:: rastro_lote_id
      :type: int | None

      **Origem:**
      :class:`FluxoAprovacaoPartindoDaEscola`

      **Descrição:**
      Identificador do lote registrado no rastro histórico da solicitação.

      Corresponde à chave primária de :class:`escola.Lote`.
      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: rastro_terceirizada
      :type: terceirizada.Terceirizada | None

      **Origem:**
      :class:`FluxoAprovacaoPartindoDaEscola`

      **Descrição:**
      Terceirizada registrada no rastro histórico da solicitação.

      Representa a empresa terceirizada vinculada ao lote da escola no momento em que o rastro foi salvo.

   .. attribute:: rastro_terceirizada_id
      :type: int | None

      **Origem:**
      :class:`FluxoAprovacaoPartindoDaEscola`

      **Descrição:**
      Identificador da terceirizada registrada no rastro histórico da solicitação.

      Corresponde à chave primária de :class:`terceirizada.Terceirizada`.
      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: status
      :type: str

      **Origem:**
      ``django_xworkflows.models.StateField``

      **Descrição:**
      Estado atual da solicitação dentro do workflow de aprovação partindo da escola.

      Armazena um dos valores definidos em :class:`PedidoAPartirDaEscolaWorkflow`, como ``RASCUNHO``, ``DRE_A_VALIDAR`` ou ``CODAE_AUTORIZADO``.

   .. attribute:: substituicoes_cemei_cei_periodo_escolar
      :type: django.db.models.QuerySet[SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI]

      Relação reversa 1:N com :class:`SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI`.

      Representa todas as substituições de tipo de alimentação vinculadas à parte CEI desta
      solicitação CEMEI, organizadas por período escolar e faixa etária.

   .. attribute:: substituicoes_cemei_emei_periodo_escolar
      :type: django.db.models.QuerySet[SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI]

      Relação reversa 1:N com :class:`SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI`.

      Representa todas as substituições de tipo de alimentação vinculadas à parte EMEI desta
      solicitação CEMEI, organizadas por período escolar e quantidade de alunos.

   .. attribute:: terceirizada_conferiu_gestao
      :type: bool

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Indica se a terceirizada marcou ciência da solicitação na Gestão de Alimentação.

      Quando ``True``, registra que a empresa conferiu o pedido sem necessariamente alterar o status do workflow.

   .. method:: get_status_display()

      **Origem:**
      ``django_xworkflows.models.StateField``

      **Descrição:**
      Relacionado ao campo ``status`` do workflow.

      Retorna a representação legível (label) do status atual da instância.

      O valor retornado corresponde ao texto definido em ``states`` do workflow,
      sendo mais apropriado para exibição em interfaces (ex: telas e relatórios).

      :return: Texto legível do status
      :rtype: str

      Exemplo: ``CODAE_AUTORIZADO`` retorna ``"CODAE autorizou pedido"``.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Identificador único do registro.

      Gerado automaticamente no momento da criação, sendo utilizado como
      identificador externo amigável.

      Pode ser utilizado em integrações externas e URLs públicas,
      evitando a exposição do identificador interno (ID).

.. autoclass:: SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI
   :members:
   :show-inheritance:
   :exclude-members:
      alteracao_cardapio,
      alteracao_cardapio_id,
      DoesNotExist,
      faixas_etarias,
      id,
      MultipleObjectsReturned,
      objects,
      periodo_escolar,
      periodo_escolar_id,
      tipos_alimentacao_de,
      tipos_alimentacao_para,
      uuid

   .. attribute:: alteracao_cardapio
      :type: cardapio.AlteracaoCardapioCEMEI | None

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Solicitação de alteração do tipo de alimentação CEMEI à qual esta substituição CEI pertence.

      Pode ser ``None`` porque o campo permite ``null`` e ``blank``.

   .. attribute:: alteracao_cardapio_id
      :type: int | None

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Identificador da solicitação de alteração do tipo de alimentação CEMEI associada a esta substituição.

      Corresponde à chave primária de :class:`AlteracaoCardapioCEMEI`.
      Pode ser ``None`` porque o campo permite ``null`` e ``blank``.

   .. attribute:: faixas_etarias
      :type: django.db.models.QuerySet[FaixaEtariaSubstituicaoAlimentacaoCEMEICEI]

      Relação reversa 1:N com :class:`FaixaEtariaSubstituicaoAlimentacaoCEMEICEI`.

      Representa as faixas etárias com suas respectivas quantidades e matriculados
      para esta substituição de período escolar CEI.

   .. attribute:: id
      :type: int

      **Origem:**
      ``django.db.models.Model``

      **Descrição:**
      Identificador interno do registro no banco de dados.

      Corresponde à chave primária gerada automaticamente pelo Django.

   .. attribute:: periodo_escolar
      :type: escola.PeriodoEscolar

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Período escolar ao qual a substituição de alimentação CEI se aplica.

      Exemplo: manhã, tarde, noite ou integral.

   .. attribute:: periodo_escolar_id
      :type: int

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Identificador do período escolar ao qual esta substituição CEI se aplica.

      Corresponde à chave primária de :class:`escola.PeriodoEscolar`.

   .. attribute:: tipos_alimentacao_de
      :type: django.db.models.Manager[TipoAlimentacao]

      **Origem:**
      ``django.db.models.ManyToManyField``

      **Descrição:**
      Conjunto de tipos de alimentação originais que serão substituídos nesta solicitação CEI.

      Trata-se de uma relação muitos-para-muitos com :class:`TipoAlimentacao`.

   .. attribute:: tipos_alimentacao_para
      :type: django.db.models.Manager[TipoAlimentacao]

      **Origem:**
      ``django.db.models.ManyToManyField``

      **Descrição:**
      Conjunto de tipos de alimentação que passarão a ser oferecidos no lugar dos tipos originais (lado CEI).

      Trata-se de uma relação muitos-para-muitos com :class:`TipoAlimentacao`.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Identificador único do registro.

      Gerado automaticamente no momento da criação, sendo utilizado como identificador externo.

.. autoclass:: SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI
   :members:
   :show-inheritance:
   :exclude-members:
      alteracao_cardapio,
      alteracao_cardapio_id,
      DoesNotExist,
      id,
      matriculados_quando_criado,
      MultipleObjectsReturned,
      objects,
      periodo_escolar,
      periodo_escolar_id,
      qtd_alunos,
      tipos_alimentacao_de,
      tipos_alimentacao_para,
      uuid

   .. attribute:: alteracao_cardapio
      :type: cardapio.AlteracaoCardapioCEMEI | None

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Solicitação de alteração do tipo de alimentação CEMEI à qual esta substituição EMEI pertence.

      Pode ser ``None`` porque o campo permite ``null`` e ``blank``.

   .. attribute:: alteracao_cardapio_id
      :type: int | None

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Identificador da solicitação de alteração do tipo de alimentação CEMEI associada a esta substituição.

      Corresponde à chave primária de :class:`AlteracaoCardapioCEMEI`.
      Pode ser ``None`` porque o campo permite ``null`` e ``blank``.

   .. attribute:: id
      :type: int

      **Origem:**
      ``django.db.models.Model``

      **Descrição:**
      Identificador interno do registro no banco de dados.

      Corresponde à chave primária gerada automaticamente pelo Django.

   .. attribute:: matriculados_quando_criado
      :type: int

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Número total de alunos matriculados no período escolar EMEI no momento em que a solicitação foi criada.

      Mantém um registro histórico da matrícula, independentemente de alterações posteriores.

   .. attribute:: periodo_escolar
      :type: escola.PeriodoEscolar

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Período escolar ao qual a substituição de alimentação EMEI se aplica.

      Exemplo: manhã, tarde, noite ou integral.

   .. attribute:: periodo_escolar_id
      :type: int

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Identificador do período escolar ao qual esta substituição EMEI se aplica.

      Corresponde à chave primária de :class:`escola.PeriodoEscolar`.

   .. attribute:: qtd_alunos
      :type: int

      **Origem:**
      ``alteracao_tipo_alimentacao_cemei/models.py``

      **Descrição:**
      Quantidade de alunos da parte EMEI afetados por esta substituição de alimentação.

      Diferentemente do lado CEI (que usa faixas etárias), a parte EMEI expressa a quantidade
      diretamente como um inteiro positivo. O valor padrão é ``0``.

   .. attribute:: tipos_alimentacao_de
      :type: django.db.models.Manager[TipoAlimentacao]

      **Origem:**
      ``django.db.models.ManyToManyField``

      **Descrição:**
      Conjunto de tipos de alimentação originais que serão substituídos nesta solicitação EMEI.

      Trata-se de uma relação muitos-para-muitos com :class:`TipoAlimentacao`.

   .. attribute:: tipos_alimentacao_para
      :type: django.db.models.Manager[TipoAlimentacao]

      **Origem:**
      ``django.db.models.ManyToManyField``

      **Descrição:**
      Conjunto de tipos de alimentação que passarão a ser oferecidos no lugar dos tipos originais (lado EMEI).

      Trata-se de uma relação muitos-para-muitos com :class:`TipoAlimentacao`.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Identificador único do registro.

      Gerado automaticamente no momento da criação, sendo utilizado como identificador externo.

.. autoclass:: FaixaEtariaSubstituicaoAlimentacaoCEMEICEI
   :members:
   :show-inheritance:
   :exclude-members:
      DoesNotExist,
      faixa_etaria,
      faixa_etaria_id,
      id,
      matriculados_quando_criado,
      MultipleObjectsReturned,
      objects,
      quantidade,
      substituicao_alimentacao,
      substituicao_alimentacao_id,
      uuid

   .. attribute:: faixa_etaria
      :type: escola.FaixaEtaria

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Faixa etária a que se refere esta entrada de substituição de alimentação CEI do CEMEI.

      Exemplo: de 0 a 1 ano, de 1 a 2 anos, etc.

   .. attribute:: faixa_etaria_id
      :type: int

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Identificador da faixa etária associada a esta entrada.

      Corresponde à chave primária de :class:`escola.FaixaEtaria`.

   .. attribute:: id
      :type: int

      **Origem:**
      ``django.db.models.Model``

      **Descrição:**
      Identificador interno do registro no banco de dados.

      Corresponde à chave primária gerada automaticamente pelo Django.

   .. attribute:: matriculados_quando_criado
      :type: int

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Número de alunos matriculados nesta faixa etária no momento em que a solicitação foi criada.

      Mantém um registro histórico da matrícula, independentemente de alterações posteriores.

   .. attribute:: quantidade
      :type: int

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Quantidade de alunos desta faixa etária afetados pela substituição de alimentação.

   .. attribute:: substituicao_alimentacao
      :type: cardapio.SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Substituição de alimentação no período escolar CEI do CEMEI à qual esta faixa etária pertence.

   .. attribute:: substituicao_alimentacao_id
      :type: int

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Identificador da substituição de alimentação no período escolar CEI associada a esta faixa etária.

      Corresponde à chave primária de :class:`SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI`.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Identificador único do registro.

      Gerado automaticamente no momento da criação, sendo utilizado como identificador externo.

.. autoclass:: DataIntervaloAlteracaoCardapioCEMEI
   :members:
   :show-inheritance:
   :exclude-members:
      alteracao_cardapio_cemei,
      alteracao_cardapio_cemei_id,
      cancelado,
      cancelado_em,
      cancelado_justificativa,
      cancelado_por,
      cancelado_por_id,
      criado_em,
      data,
      DoesNotExist,
      get_next_by_criado_em,
      get_next_by_data,
      get_previous_by_criado_em,
      get_previous_by_data,
      id,
      MultipleObjectsReturned,
      objects,
      uuid

   .. attribute:: alteracao_cardapio_cemei
      :type: cardapio.AlteracaoCardapioCEMEI

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Solicitação de alteração do tipo de alimentação CEMEI à qual esta data do intervalo pertence.

   .. attribute:: alteracao_cardapio_cemei_id
      :type: int

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Identificador da solicitação CEMEI associada a esta data do intervalo.

      Corresponde à chave primária de :class:`AlteracaoCardapioCEMEI`.

   .. attribute:: cancelado
      :type: bool

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Indica se esta data específica do intervalo foi cancelada individualmente.

      Quando ``True``, a data foi excluída do escopo da solicitação sem invalidar as demais datas.
      O padrão é ``False``.

   .. attribute:: cancelado_justificativa
      :type: str

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Justificativa fornecida ao cancelar individualmente esta data do intervalo.

      Pode ser uma string vazia quando não há justificativa registrada.

   .. attribute:: cancelado_em
      :type: datetime.datetime | None

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Timestamp preenchido automaticamente no momento em que esta data do intervalo foi cancelada individualmente.

      Pode ser ``None`` enquanto o cancelamento não tiver ocorrido.

   .. attribute:: cancelado_por
      :type: perfil.Usuario | None

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Usuário responsável pelo cancelamento individual desta data do intervalo.

      Pode ser ``None`` se o cancelamento ainda não ocorreu ou se o campo não foi preenchido.

   .. attribute:: cancelado_por_id
      :type: int | None

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Identificador do usuário responsável pelo cancelamento individual desta data do intervalo.

      Corresponde à chave primária de :class:`perfil.Usuario`.
      Pode ser ``None`` se o cancelamento ainda não ocorreu ou se o campo não foi preenchido.

   .. attribute:: criado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Timestamp preenchido automaticamente na criação do registro.

   .. attribute:: data
      :type: datetime.date

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Data específica que compõe o intervalo da solicitação CEMEI.

   .. attribute:: id
      :type: int

      **Origem:**
      ``django.db.models.Model``

      **Descrição:**
      Identificador interno do registro no banco de dados.

      Corresponde à chave primária gerada automaticamente pelo Django.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Identificador único do registro.

      Gerado automaticamente no momento da criação, sendo utilizado como identificador externo.

api
---

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.api
   :members:
   :show-inheritance:

serializers
~~~~~~~~~~~

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.api.serializers
   :members:
   :show-inheritance:

serializers\_create
~~~~~~~~~~~~~~~~~~~

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.api.serializers_create
   :members:
   :show-inheritance:

viewsets
~~~~~~~~

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.api.viewsets
   :members:
   :show-inheritance:

fixtures
--------

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.fixtures
   :members:
   :show-inheritance:

fixtures/factories
~~~~~~~~~~~~~~~~~~

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.fixtures.factories
   :members:
   :show-inheritance:

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.fixtures.factories.alteracao_tipo_alimentacao_cemei_factory
   :members:
   :show-inheritance:

managers
--------

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.managers
   :members:
   :show-inheritance:

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.managers.alteracao_tipo_alimentacao_cemei_managers
   :members:
   :show-inheritance:
