suspensao\_alimentacao
======================

.. automodule:: src.cardapio.suspensao_alimentacao
   :members:
   :show-inheritance:

admin
-----

.. automodule:: src.cardapio.suspensao_alimentacao.admin
   :members:
   :show-inheritance:

models
------

.. automodule:: src.cardapio.suspensao_alimentacao.models
   :members:
   :show-inheritance:
   :exclude-members:
      DoesNotExist,
      GrupoSuspensaoAlimentacao,
      MotivoSuspensao,
      MultipleObjectsReturned,
      QuantidadePorPeriodoSuspensaoAlimentacao,
      SuspensaoAlimentacao

.. autoclass:: GrupoSuspensaoAlimentacao
   :members:
   :show-inheritance:
   :exclude-members:
      criado_em,
      criado_por,
      criado_por_id,
      DESCRICAO,
      desta_semana,
      deste_mes,
      DIAS_UTEIS_PARA_CANCELAR,
      escola,
      escola_id,
      DoesNotExist,
      get_next_by_criado_em,
      get_previous_by_criado_em,
      get_status_display,
      id,
      id_externo,
      MultipleObjectsReturned,
      objects,
      observacao,
      quantidades_por_periodo,
      rastro_dre,
      rastro_dre_id,
      rastro_escola,
      rastro_escola_id,
      rastro_lote,
      rastro_lote_id,
      rastro_terceirizada,
      rastro_terceirizada_id,
      status,
      suspensoes_alimentacao,
      terceirizada_conferiu_gestao,
      uuid,
      workflow_class

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

   .. attribute:: desta_semana
      :type: GrupoSuspensaoAlimentacaoDestaSemanaManager

      **Origem:**
      ``suspensao_alimentacao/managers/suspensao_alimentacao_managers.py``

      **Descrição:**
      Manager que filtra apenas as solicitações de suspensão de alimentação da semana corrente.

      Retorna as solicitações cuja data de suspensão está dentro do intervalo da semana atual.

   .. attribute:: deste_mes
      :type: GrupoSuspensaoAlimentacaoDesteMesManager

      **Origem:**
      ``suspensao_alimentacao/managers/suspensao_alimentacao_managers.py``

      **Descrição:**
      Manager que filtra apenas as solicitações de suspensão de alimentação do mês corrente.

      Retorna as solicitações cuja data de suspensão está dentro do mês atual.

   .. attribute:: escola
      :type: escola.Escola | None

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Escola que efetuou a solicitação de suspensão de alimentação.

   .. attribute:: escola_id
      :type: int | None

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Identificador da escola que efetuou a solicitação de suspensão de alimentação.

      Corresponde à chave primária de :class:`escola.Escola`.
      Pode ser ``None``.

   .. attribute:: id
      :type: int

      **Origem:**
      ``django.db.models.Model``

      **Descrição:**
      Identificador interno do registro no banco de dados.

      Corresponde à chave primária gerada automaticamente pelo Django.

   .. attribute:: observacao
      :type: str

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Campo de texto livre para registrar observações complementares da solicitação.

      Pode ser uma string vazia, pois o campo permite ``blank``.

   .. attribute:: quantidades_por_periodo
      :type: django.db.models.QuerySet[QuantidadePorPeriodoSuspensaoAlimentacao]

      Relação reversa 1:N com :class:`QuantidadePorPeriodoSuspensaoAlimentacao`.

      Representa os períodos escolares da solicitação com suas respectivas quantidades de alunos
      e tipos de alimentação suspensos.

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

   .. attribute:: suspensoes_alimentacao
      :type: django.db.models.QuerySet[SuspensaoAlimentacao]

      Relação reversa 1:N com :class:`SuspensaoAlimentacao`.

      Representa todas as datas de suspensão associadas à solicitação, cada uma com seu respectivo motivo.

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

      Exemplo: ``INFORMADO``.

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

.. autoclass:: MotivoSuspensao
   :members:
   :show-inheritance:
   :exclude-members:
      DoesNotExist,
      id,
      MultipleObjectsReturned,
      nome,
      objects,
      suspensaoalimentacaodacei_set,
      suspensaoalimentacao_set,
      uuid

   .. attribute:: nome
      :type: str

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Nome do motivo de suspensão de alimentação.

      Exemplos:
         - Unidade sem atendimento
         - Parada Pedagógica

   .. attribute:: suspensaoalimentacao_set
      :type: django.db.models.QuerySet[SuspensaoAlimentacao]

      Relação reversa 1:N com :class:`SuspensaoAlimentacao`.

      Representa todas as datas de suspensão que utilizam este motivo.

   .. attribute:: suspensaoalimentacaodacei_set
      :type: django.db.models.QuerySet[SuspensaoAlimentacaoDaCEI]

      Relação reversa 1:N com :class:`SuspensaoAlimentacaoDaCEI`.

      Representa todas as datas de suspensão de CEI que utilizam este motivo.

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

.. autoclass:: SuspensaoAlimentacao
   :members:
   :show-inheritance:
   :exclude-members:
      cancelado,
      cancelado_em,
      cancelado_justificativa,
      cancelado_por,
      cancelado_por_id,
      data,
      DoesNotExist,
      get_alunos_cei_ou_emei_display,
      get_next_by_cancelado_em,
      get_next_by_data,
      get_previous_by_cancelado_em,
      get_previous_by_data,
      grupo_suspensao,
      grupo_suspensao_id,
      id,
      motivo,
      motivo_id,
      MultipleObjectsReturned,
      objects,
      outro_motivo,
      prioritario,
      uuid

   .. attribute:: data
      :type: datetime.date

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Data da suspensão de alimentação.

      Representa o dia letivo em que não haverá aula na unidade educacional.

   .. attribute:: motivo
      :type: cardapio.MotivoSuspensao

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Motivo da suspensão de alimentação associado a esta data.

      Motivos disponíveis:
         - Unidade sem atendimento
         - Parada Pedagógica

   .. attribute:: motivo_id
      :type: int

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Identificador do motivo de suspensão associado a esta data.

      Corresponde à chave primária de :class:`MotivoSuspensao`.

   .. attribute:: prioritario
      :type: bool

      **Origem:**
      ``django.db.models.BooleanField``

      **Descrição:**
      Indica se esta suspensão é considerada prioritária.

      Por padrão, é ``False``.

   .. attribute:: outro_motivo
      :type: str

      **Origem:**
      ``django.db.models.CharField``

      **Descrição:**
      Campo de texto livre para registrar um motivo alternativo, quando o motivo principal for "Outro".

      Pode ser uma string vazia, pois o campo permite ``blank``.

   .. method:: get_alunos_cei_ou_emei_display()

      **Origem:**
      ``django.db.models.CharField``

      **Descrição:**
      Relacionado ao campo ``alunos_cei_ou_emei``.

      Retorna a representação legível (label) do valor do campo ``alunos_cei_ou_emei``.

      O valor retornado corresponde ao texto definido em ``CEI_OU_EMEI_CHOICES``,
      sendo mais apropriado para exibição em interfaces (ex: telas e relatórios).

      :return: Texto legível da opção CEI/EMEI
      :rtype: str

      Opções: ``"Todos"``, ``"CEI"`` ou ``"EMEI"``.

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

   .. attribute:: cancelado
      :type: bool

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Indica se esta data específica de suspensão foi cancelada individualmente.

      Quando ``True``, a solicitação principal continua existindo, mas este dia deixa de valer.

   .. attribute:: cancelado_em
      :type: datetime.datetime | None

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Data e hora em que o cancelamento individual desta data foi registrado.

      Pode ser ``None`` quando a data ainda não foi cancelada.

   .. attribute:: cancelado_justificativa
      :type: str

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Justificativa informada para o cancelamento individual desta data.

      Permanece vazio quando não houver cancelamento ou quando nenhuma justificativa tiver sido registrada.

   .. attribute:: cancelado_por
      :type: perfil.Usuario | None

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Usuário responsável por cancelar individualmente esta data de suspensão.

      Pode ser ``None`` quando o cancelamento não foi realizado.

   .. attribute:: cancelado_por_id
      :type: int | None

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Identificador do usuário responsável pelo cancelamento individual desta data.

      Corresponde à chave primária de :class:`perfil.Usuario`.
      Pode ser ``None`` quando não houver usuário associado ao cancelamento.

.. autoclass:: QuantidadePorPeriodoSuspensaoAlimentacao
   :members:
   :show-inheritance:
   :exclude-members:
      alunos_cei_ou_emei,
      DoesNotExist,
      grupo_suspensao,
      grupo_suspensao_id,
      id,
      MultipleObjectsReturned,
      numero_alunos,
      objects,
      periodo_escolar,
      periodo_escolar_id,
      tipos_alimentacao,
      uuid

   .. attribute:: numero_alunos
      :type: int

      **Origem:**
      ``django.db.models.SmallIntegerField``

      **Descrição:**
      Quantidade de alunos sem alimentação neste período escolar da solicitação.

   .. attribute:: periodo_escolar
      :type: escola.PeriodoEscolar

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Período escolar ao qual esta quantidade de alunos se aplica.

      Exemplo: manhã, tarde, noite ou integral, conforme os períodos cadastrados para a unidade.

   .. attribute:: periodo_escolar_id
      :type: int

      **Origem:**
      ``django.db.models.ForeignKey``

      **Descrição:**
      Identificador do período escolar ao qual esta quantidade se aplica.

      Corresponde à chave primária de :class:`escola.PeriodoEscolar`.

   .. attribute:: tipos_alimentacao
      :type: django.db.models.Manager[TipoAlimentacao]

      **Origem:**
      ``django.db.models.ManyToManyField``

      **Descrição:**
      Conjunto de tipos de alimentação que estão suspensos neste período escolar.

      Trata-se de uma relação muitos-para-muitos com :class:`TipoAlimentacao`.

   .. attribute:: alunos_cei_ou_emei
      :type: str

      **Origem:**
      ``django.db.models.CharField``

      **Descrição:**
      Indica a qual grupo de alunos se destina a suspensão, quando a unidade escolar for
      do tipo CEMEI ou CEU CEMEI.

      Opções disponíveis:
         - ``TODOS``: ambos CEI e EMEI
         - ``CEI``: apenas alunos CEI
         - ``EMEI``: apenas alunos EMEI

      Pode ser uma string vazia, pois o campo permite ``blank``.

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

.. automodule:: src.cardapio.suspensao_alimentacao.api
   :members:
   :show-inheritance:

serializers
~~~~~~~~~~~

.. automodule:: src.cardapio.suspensao_alimentacao.api.serializers
   :members:
   :show-inheritance:

serializers\_create
~~~~~~~~~~~~~~~~~~~

.. automodule:: src.cardapio.suspensao_alimentacao.api.serializers_create
   :members:
   :show-inheritance:

viewsets
~~~~~~~~

.. automodule:: src.cardapio.suspensao_alimentacao.api.viewsets
   :members:
   :show-inheritance:

fixtures
--------

.. automodule:: src.cardapio.suspensao_alimentacao.fixtures
   :members:
   :show-inheritance:

fixtures/factories
~~~~~~~~~~~~~~~~~~

.. automodule:: src.cardapio.suspensao_alimentacao.fixtures.factories
   :members:
   :show-inheritance:

.. automodule:: src.cardapio.suspensao_alimentacao.fixtures.factories.suspensao_alimentacao_factory
   :members:
   :show-inheritance:

managers
--------

.. automodule:: src.cardapio.suspensao_alimentacao.managers
   :members:
   :show-inheritance:

.. automodule:: src.cardapio.suspensao_alimentacao.managers.suspensao_alimentacao_managers
   :members:
   :show-inheritance:
