alteracao\_tipo\_alimentacao
===========================

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao
   :members:
   :show-inheritance:

admin
-----

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.admin
   :members:
   :show-inheritance:

behaviors
---------

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.behaviors
   :members:
   :show-inheritance:

models
------

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models
   :members:
   :show-inheritance:
   :exclude-members: AlteracaoCardapio, DoesNotExist, MultipleObjectsReturned

.. autoclass:: AlteracaoCardapio
   :members:
   :show-inheritance:
   :exclude-members:
      criado_em,
      criado_por,
      criado_por_id,
      data_final,
      data_inicial,
      datas_intervalo,
      escola,
      escola_id,
      DoesNotExist,
      get_next_by_criado_em,
      get_next_by_data_final,
      get_next_by_data_inicial,
      get_previous_by_criado_em,
      get_previous_by_data_final,
      get_previous_by_data_inicial,
      get_status_display,
      MultipleObjectsReturned

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
      Usuario responsavel pela criacao do registro. O campo ainda permite `null` e `blank`

      (perfil.Usuario | None): Usuario responsavel pela criacao doregistro. O campo ainda permite `null` e `blank`
   
   .. attribute:: criado_por_id
      :type: int | None

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Identificador do usuário responsável pela criação do registro.

      Corresponde à chave primária de :class:`perfil.Usuario`.
      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: data_inicial
      :type: datetime.date

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Data inicial do período de validade da solicitação de alteração do tipo de alimentação.

      Caso data_inicial é igual a data_final, a solicitação de alteração do tipo de alimentação é válida apenas para um dia específico. 
      Caso data_inicial seja anterior a data_final, a solicitação de alteração do tipo de alimentação é válida para um período de dias.
   
   .. attribute:: data_final
      :type: datetime.date

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Data final do período de validade da solicitação de alteração do tipo de alimentação.

      Caso data_inicial é igual a data_final, a solicitação de alteração do tipo de alimentação é válida apenas para um dia específico. 
      Caso data_inicial seja anterior a data_final, a solicitação de alteração do tipo de alimentação é válida para um período de dias.

   .. attribute:: datas_intervalo
      :type: django.db.models.QuerySet[DataIntervaloAlteracaoCardapio]

      Relação reversa 1:N com :class:`DataIntervaloAlteracaoCardapio`.

      Representa todas as datas associadas à alteração de cardápio, individualmente. 
      
      Essa relação é especialmente útil para casos em que a alteração de cardápio abrange um intervalo de dias, permitindo acessar cada dia específico dentro desse intervalo.

      Modelo criado, especificamente, para por **cancelar dias individualmente** de uma solicitação de alteração do tipo de alimentação que abrange um intervalo de dias.

   .. attribute:: escola
      :type: escola.Escola | None

      **Origem:**
      :class:`EhAlteracaoCardapio`

      **Descrição:**
      Escola que efetuou a solicitação de alteração do tipo de alimentação. O campo ainda permite `null` e `blank`

   .. attribute:: escola_id
      :type: int | None

      **Origem:**
      :class:`EhAlteracaoCardapio`

      **Descrição:**
      Identificador da escola que efetuou a solicitação de alteração do tipo de alimentação.

      Corresponde à chave primária de :class:`escola.Escola`.
      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. method:: get_status_display()
      :rtype: str

      **Origem:**
      ``django_xworkflows.models.StateField``

      **Descrição:**
      Relacionado ao campo ``status`` do workflow.

      Retorna a representação legível (label) do status atual da instância.

      O valor retornado corresponde ao texto definido em ``states`` do workflow,
      sendo mais apropriado para exibição em interfaces (ex: telas e relatórios).

      Exemplo:
      - ``CODAE_AUTORIZADO`` → ``"CODAE autorizou pedido"``

api
---

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api
   :members:
   :show-inheritance:

api/serializers
~~~~~~~~~~~~~~~

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.serializers
   :members:
   :show-inheritance:

api/serializers\_create
~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.serializers_create
   :members:
   :show-inheritance:

api/validators
~~~~~~~~~~~~~~

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.validators
   :members:
   :show-inheritance:

api/viewsets
~~~~~~~~~~~~

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.viewsets
   :members:
   :show-inheritance:

fixtures
--------

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.fixtures
   :members:
   :show-inheritance:

fixtures/factories
~~~~~~~~~~~~~~~~~~

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.fixtures.factories
   :members:
   :show-inheritance:

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.fixtures.factories.alteracao_tipo_alimentacao_factory
   :members:
   :show-inheritance:

managers
--------

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.managers
   :members:
   :show-inheritance:

.. automodule:: sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.managers.alteracao_tipo_alimentacao_managers
   :members:
   :show-inheritance:
