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
   :exclude-members: criado_em, criado_por, criado_por_id, DoesNotExist, MultipleObjectsReturned

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
