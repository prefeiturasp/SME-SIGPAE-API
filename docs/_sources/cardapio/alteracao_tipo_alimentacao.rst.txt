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
      foi_solicitado_fora_do_prazo,
      DoesNotExist,
      get_next_by_criado_em,
      get_next_by_data_final,
      get_next_by_data_inicial,
      get_previous_by_criado_em,
      get_previous_by_data_final,
      get_previous_by_data_inicial,
      get_status_display,
      id,
      motivo,
      motivo_id,
      MultipleObjectsReturned,
      observacao,
      substituicoes_periodo_escolar,
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
      uuid

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
      Motivo associado à solicitação de alteração do tipo de alimentação. O campo ainda permite `null` e `blank`

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

   .. attribute:: substituicoes_periodo_escolar
      :type: django.db.models.QuerySet[SubstituicaoAlimentacaoNoPeriodoEscolar]

      Relação reversa 1:N com :class:`SubstituicaoAlimentacaoNoPeriodoEscolar`.

      Representa todas as substituições de tipo de alimentação vinculadas à solicitação, organizadas por período escolar.

      Cada registro associado define o período escolar, os tipos de alimentação substituídos, os tipos resultantes e a quantidade de alunos impactados.

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
