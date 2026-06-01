inversao\_dia\_cardapio
=======================

.. automodule:: src.cardapio.inversao_dia_cardapio
   :members:
   :show-inheritance:

admin
-----

.. automodule:: src.cardapio.inversao_dia_cardapio.admin
   :members:
   :show-inheritance:

models
------

.. automodule:: src.cardapio.inversao_dia_cardapio.models
   :members:
   :show-inheritance:
   :exclude-members:
      InversaoCardapio,
      DoesNotExist,
      MultipleObjectsReturned,
      get_next_by_criado_em,
      get_previous_by_criado_em,
      objects

.. autoclass:: InversaoCardapio
   :members:
   :show-inheritance:
   :exclude-members:
      alunos_da_cemei,
      alunos_da_cemei_2,
      criado_em,
      criado_por,
      criado_por_id,
      data_de_inversao,
      data_de_inversao_2,
      data_para_inversao,
      data_para_inversao_2,
      desta_semana,
      deste_mes,
      escola,
      escola_id,
      foi_solicitado_fora_do_prazo,
      DoesNotExist,
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
      status,
      terceirizada_conferiu_gestao,
      tipos_alimentacao,
      uuid,
      vencidos

   .. attribute:: alunos_da_cemei
      :type: str

      **Origem:**
      ``inversao_dia_cardapio/models.py``

      **Descrição:**
      Indica quais alunos da CEMEI são afetados no primeiro par de datas da inversão.

      O campo permite ``blank`` e possui valor padrão ``""``.

   .. attribute:: alunos_da_cemei_2
      :type: str

      **Origem:**
      ``inversao_dia_cardapio/models.py``

      **Descrição:**
      Indica quais alunos da CEMEI são afetados no segundo par de datas da inversão, quando informado.

      O campo permite ``blank`` e possui valor padrão ``""``.

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

   .. attribute:: data_de_inversao
      :type: datetime.date | None

      **Origem:**
      ``inversao_dia_cardapio/models.py``

      **Descrição:**
      Primeira data de origem da inversão de cardápio.

      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: data_de_inversao_2
      :type: datetime.date | None

      **Origem:**
      ``inversao_dia_cardapio/models.py``

      **Descrição:**
      Segunda data de origem da inversão de cardápio, utilizada quando há um segundo par de datas na solicitação.

      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: data_para_inversao
      :type: datetime.date | None

      **Origem:**
      ``inversao_dia_cardapio/models.py``

      **Descrição:**
      Primeira data de destino da inversão de cardápio.

      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: data_para_inversao_2
      :type: datetime.date | None

      **Origem:**
      ``inversao_dia_cardapio/models.py``

      **Descrição:**
      Segunda data de destino da inversão de cardápio, utilizada quando há um segundo par de datas na solicitação.

      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: desta_semana
      :type: inversao_dia_cardapio.managers.InversaoCardapioDestaSemanaManager

      **Origem:**
      ``inversao_dia_cardapio/managers/inversao_dia_cardapio_managers.py``

      **Descrição:**
      Manager customizado para consultar solicitações com datas previstas para os próximos 7 dias.

   .. attribute:: deste_mes
      :type: inversao_dia_cardapio.managers.InversaoCardapioDesteMesManager

      **Origem:**
      ``inversao_dia_cardapio/managers/inversao_dia_cardapio_managers.py``

      **Descrição:**
      Manager customizado para consultar solicitações com datas previstas para os próximos 30 dias.

   .. attribute:: escola
      :type: escola.Escola | None

      **Origem:**
      ``inversao_dia_cardapio/models.py``

      **Descrição:**
      Escola que efetuou a solicitação de inversão de dia de cardápio.

      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: escola_id
      :type: int | None

      **Origem:**
      ``inversao_dia_cardapio/models.py``

      **Descrição:**
      Identificador da escola que efetuou a solicitação de inversão de dia de cardápio.

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

   .. attribute:: motivo
      :type: str

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Campo textual que descreve o motivo da solicitação de inversão de cardápio.

      Pode ser uma string vazia, pois o campo permite ``blank``.

   .. attribute:: motivo_id
      :type: int | None

      **Origem:**
      ``inversao_dia_cardapio/models.py``

      **Descrição:**
      Não se aplica ao modelo atual de Inversão de Cardápio, pois ``motivo`` é um campo textual e não uma chave estrangeira.

      Mantido na documentação para compatibilidade com outros modelos de solicitação que utilizam ``motivo_id``.

   .. attribute:: objects
      :type: django.db.models.manager.Manager[InversaoCardapio]

      **Origem:**
      ``django.db.models.Manager``

      **Descrição:**
      Manager padrão do modelo, usado para consultas como ``all()``, ``filter()`` e ``get()``.

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

   .. attribute:: terceirizada_conferiu_gestao
      :type: bool

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Indica se a terceirizada marcou ciência da solicitação na Gestão de Alimentação.

      Quando ``True``, registra que a empresa conferiu o pedido sem necessariamente alterar o status do workflow.

   .. attribute:: tipos_alimentacao
      :type: django.db.models.QuerySet[TipoAlimentacao]

      **Origem:**
      ``inversao_dia_cardapio/models.py``

      **Descrição:**
      Relação M:N com os tipos de alimentação aos quais a inversão se aplica.

      Pode estar vazia quando a solicitação ainda não tiver tipos vinculados.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Identificador único do registro.

      Gerado automaticamente no momento da criação, sendo utilizado como identificador externo amigável.

   .. attribute:: vencidos
      :type: inversao_dia_cardapio.managers.InversaoCardapioVencidaManager

      **Origem:**
      ``inversao_dia_cardapio/managers/inversao_dia_cardapio_managers.py``

      **Descrição:**
      Manager customizado para consultar solicitações vencidas que ainda estão em status abertos do workflow.

api
---

.. automodule:: src.cardapio.inversao_dia_cardapio.api
   :members:
   :show-inheritance:

serializers
~~~~~~~~~~~

.. automodule:: src.cardapio.inversao_dia_cardapio.api.serializers
   :members:
   :show-inheritance:

serializers\_create
~~~~~~~~~~~~~~~~~~~

.. automodule:: src.cardapio.inversao_dia_cardapio.api.serializers_create
   :members:
   :show-inheritance:

validators
~~~~~~~~~~

.. automodule:: src.cardapio.inversao_dia_cardapio.api.validators
   :members:
   :show-inheritance:

viewsets
~~~~~~~~

.. automodule:: src.cardapio.inversao_dia_cardapio.api.viewsets
   :members:
   :show-inheritance:

fixtures
--------

.. automodule:: src.cardapio.inversao_dia_cardapio.fixtures
   :members:
   :show-inheritance:

fixtures/factories
~~~~~~~~~~~~~~~~~~

.. automodule:: src.cardapio.inversao_dia_cardapio.fixtures.factories
   :members:
   :show-inheritance:

.. automodule:: src.cardapio.inversao_dia_cardapio.fixtures.factories.inversao_cardapio_factory
   :members:
   :show-inheritance:

managers
--------

.. automodule:: src.cardapio.inversao_dia_cardapio.managers
   :members:
   :show-inheritance:

.. automodule:: src.cardapio.inversao_dia_cardapio.managers.inversao_dia_cardapio_managers
   :members:
   :show-inheritance:
