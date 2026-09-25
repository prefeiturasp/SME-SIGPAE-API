suspensao\_alimentacao\_cei
===========================

.. automodule:: src.cardapio.suspensao_alimentacao_cei
   :members:
   :show-inheritance:

admin
-----

.. automodule:: src.cardapio.suspensao_alimentacao_cei.admin
   :members:
   :show-inheritance:

models
------

.. automodule:: src.cardapio.suspensao_alimentacao_cei.models
   :members:
   :show-inheritance:
   :exclude-members:
      DoesNotExist,
      MultipleObjectsReturned,
      SuspensaoAlimentacaoDaCEI

.. autoclass:: SuspensaoAlimentacaoDaCEI
   :members:
   :show-inheritance:
   :exclude-members:
      criado_em,
      criado_por,
      criado_por_id,
      data,
      DESCRICAO,
      escola,
      escola_id,
      DoesNotExist,
      get_next_by_criado_em,
      get_next_by_data,
      get_previous_by_criado_em,
      get_previous_by_data,
      get_status_display,
      id,
      motivo,
      motivo_id,
      MultipleObjectsReturned,
      objects,
      observacao,
      outro_motivo,
      periodos_escolares,
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
      Usuário responsável pela criação do registro. O campo ainda permite ``null`` e ``blank``.

   .. attribute:: criado_por_id
      :type: int | None

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Identificador do usuário responsável pela criação do registro.

      Corresponde à chave primária de :class:`perfil.Usuario`.
      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: data
      :type: datetime.date

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Data da suspensão de alimentação de CEI.

      Representa o dia letivo em que não haverá aula na unidade educacional de CEI.

   .. attribute:: escola
      :type: escola.Escola

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Escola de CEI que efetuou a solicitação de suspensão de alimentação.

   .. attribute:: escola_id
      :type: int

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Identificador da escola de CEI que efetuou a solicitação de suspensão de alimentação.

      Corresponde à chave primária de :class:`escola.Escola`.

   .. attribute:: id
      :type: int

      **Origem:**
      ``django.db.models.Model``

      **Descrição:**
      Identificador interno do registro no banco de dados.

      Corresponde à chave primária gerada automaticamente pelo Django.

   .. attribute:: motivo
      :type: cardapio.MotivoSuspensao

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Motivo associado à solicitação de suspensão de alimentação de CEI.

      Motivos disponíveis:
         - Unidade sem atendimento
         - Parada Pedagógica

   .. attribute:: motivo_id
      :type: int

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Identificador do motivo associado à solicitação de suspensão de alimentação de CEI.

      Corresponde à chave primária de :class:`MotivoSuspensao`.

   .. attribute:: outro_motivo
      :type: str

      **Origem:**
      ``django.db.models.CharField``

      **Descrição:**
      Campo de texto livre para registrar um motivo alternativo, quando o motivo principal for "Outro".

      Pode ser uma string vazia, pois o campo permite ``blank``.

   .. attribute:: observacao
      :type: str

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Campo de texto livre para registrar observações complementares da solicitação.

      Pode ser uma string vazia, pois o campo permite ``blank``.

   .. attribute:: periodos_escolares
      :type: django.db.models.Manager[escola.PeriodoEscolar]

      **Origem:**
      ``django.db.models.ManyToManyField``

      **Descrição:**
      Períodos escolares associados à solicitação de suspensão de alimentação de CEI.

      Exemplo: manhã, tarde, noite ou integral, conforme os períodos cadastrados para a unidade.

      Trata-se de uma relação muitos-para-muitos com :class:`escola.PeriodoEscolar`.
      Pode ser uma lista vazia, pois o campo permite ``blank``.

   .. attribute:: rastro_dre
      :type: escola.DiretoriaRegional | None

      **Origem:**
      :class:`FluxoInformativoPartindoDaEscola`

      **Descrição:**
      Diretoria Regional de Educação vinculada ao rastro histórico da solicitação.

      Representa a DRE da escola no momento em que o rastro do pedido foi salvo.

   .. attribute:: rastro_dre_id
      :type: int | None

      **Origem:**
      :class:`FluxoInformativoPartindoDaEscola`

      **Descrição:**
      Identificador da DRE vinculada ao rastro histórico da solicitação.

      Corresponde à chave primária de :class:`escola.DiretoriaRegional`.
      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: rastro_escola
      :type: escola.Escola | None

      **Origem:**
      :class:`FluxoInformativoPartindoDaEscola`

      **Descrição:**
      Escola registrada no rastro histórico da solicitação.

      Representa a escola vinculada ao pedido no momento em que o rastro foi salvo.

   .. attribute:: rastro_escola_id
      :type: int | None

      **Origem:**
      :class:`FluxoInformativoPartindoDaEscola`

      **Descrição:**
      Identificador da escola registrada no rastro histórico da solicitação.

      Corresponde à chave primária de :class:`escola.Escola`.
      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: rastro_lote
      :type: escola.Lote | None

      **Origem:**
      :class:`FluxoInformativoPartindoDaEscola`

      **Descrição:**
      Lote registrado no rastro histórico da solicitação.

      Representa o lote da escola no momento em que o rastro foi salvo.

   .. attribute:: rastro_lote_id
      :type: int | None

      **Origem:**
      :class:`FluxoInformativoPartindoDaEscola`

      **Descrição:**
      Identificador do lote registrado no rastro histórico da solicitação.

      Corresponde à chave primária de :class:`escola.Lote`.
      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: rastro_terceirizada
      :type: terceirizada.Terceirizada | None

      **Origem:**
      :class:`FluxoInformativoPartindoDaEscola`

      **Descrição:**
      Terceirizada registrada no rastro histórico da solicitação.

      Representa a empresa terceirizada vinculada ao lote da escola no momento em que o rastro foi salvo.

   .. attribute:: rastro_terceirizada_id
      :type: int | None

      **Origem:**
      :class:`FluxoInformativoPartindoDaEscola`

      **Descrição:**
      Identificador da terceirizada registrada no rastro histórico da solicitação.

      Corresponde à chave primária de :class:`terceirizada.Terceirizada`.
      Pode ser ``None`` (campo permite ``null`` e ``blank``).

   .. attribute:: status
      :type: str

      **Origem:**
      ``django_xworkflows.models.StateField``

      **Descrição:**
      Estado atual da solicitação dentro do workflow informativo partindo da escola.

      Armazena um dos valores definidos em :class:`InformativoPartindoDaEscolaWorkflow`, como ``RASCUNHO``, ``INFORMADO``, ``TERCEIRIZADA_TOMOU_CIENCIA`` ou ``ESCOLA_CANCELOU``.

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

      Exemplo: ``INFORMADO`` retorna ``"Informado"``.

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

.. automodule:: src.cardapio.suspensao_alimentacao_cei.api
   :members:
   :show-inheritance:

serializers
~~~~~~~~~~~

.. automodule:: src.cardapio.suspensao_alimentacao_cei.api.serializers
   :members:
   :show-inheritance:

serializers\_create
~~~~~~~~~~~~~~~~~~~

.. automodule:: src.cardapio.suspensao_alimentacao_cei.api.serializers_create
   :members:
   :show-inheritance:

viewsets
~~~~~~~~

.. automodule:: src.cardapio.suspensao_alimentacao_cei.api.viewsets
   :members:
   :show-inheritance:

fixtures
--------

.. automodule:: src.cardapio.suspensao_alimentacao_cei.fixtures
   :members:
   :show-inheritance:

fixtures/factories
~~~~~~~~~~~~~~~~~~

.. automodule:: src.cardapio.suspensao_alimentacao_cei.fixtures.factories
   :members:
   :show-inheritance:

.. automodule:: src.cardapio.suspensao_alimentacao_cei.fixtures.factories.suspensao_alimentacao_cei_factory
   :members:
   :show-inheritance:
