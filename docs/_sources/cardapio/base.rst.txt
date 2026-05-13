base
====

.. automodule:: src.cardapio.base
   :members:
   :show-inheritance:

admin
-----

.. automodule:: src.cardapio.base.admin
   :members:
   :show-inheritance:

models
------

.. automodule:: src.cardapio.base.models
   :members:
   :show-inheritance:
   :exclude-members:
      HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
      MotivoDRENaoValida,
      TipoAlimentacao,
      VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
      DoesNotExist,
      MultipleObjectsReturned

.. autoclass:: TipoAlimentacao
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, LANCHE_4H, LANCHE_EMERGENCIAL, MultipleObjectsReturned, nome, posicao, vinculos, substituicoes_periodo_escolar

   .. attribute:: nome
      :type: str

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Nome legível do tipo de alimentação exibido em cadastros, vínculos e solicitações.

   .. attribute:: posicao
      :type: int

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Posição usada para ordenar os tipos de alimentação nas telas e regras do cardápio.

   .. attribute:: vinculos
      :type: django.db.models.QuerySet[VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar]

      **Descrição:**
      Relação reversa M:N com :class:`VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar`.

      Reúne os vínculos de período escolar e tipo de unidade escolar em que esse tipo de alimentação pode ser servido.

.. autoclass:: HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, escola, hora_final, hora_inicial, periodo_escolar, tipo_alimentacao

   .. attribute:: hora_inicial
      :type: datetime.time

      **Descrição:**
      Horário inicial em que o tipo de alimentação pode ser ofertado.

   .. attribute:: hora_final
      :type: datetime.time

      **Descrição:**
      Horário final da janela de atendimento configurada.

   .. attribute:: escola
      :type: escola.Escola | None

      **Descrição:**
      Escola à qual a configuração de horário se aplica. Pode ser ``None`` em cadastros legados.

   .. attribute:: tipo_alimentacao
      :type: cardapio.TipoAlimentacao | None

      **Descrição:**
      Tipo de alimentação atendido pela faixa de horário configurada.

   .. attribute:: periodo_escolar
      :type: escola.PeriodoEscolar | None

      **Descrição:**
      Período escolar em que a faixa de horário é válida.

.. autoclass:: VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar
   :members:
   :show-inheritance:
   :exclude-members: ativo, DoesNotExist, MultipleObjectsReturned, periodo_escolar, tipo_unidade_escolar, tipos_alimentacao

   .. attribute:: ativo
      :type: bool

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Indica se o vínculo está habilitado para uso nas regras vigentes do cardápio.

   .. attribute:: tipo_unidade_escolar
      :type: escola.TipoUnidadeEscolar | None

      **Descrição:**
      Tipo de unidade escolar ao qual a regra de alimentação se aplica.

   .. attribute:: periodo_escolar
      :type: escola.PeriodoEscolar | None

      **Descrição:**
      Período escolar coberto pelo vínculo.

   .. attribute:: tipos_alimentacao
      :type: django.db.models.QuerySet[TipoAlimentacao]

      **Descrição:**
      Relação M:N com os tipos de alimentação autorizados para a combinação de período escolar e tipo de unidade escolar.

.. autoclass:: MotivoDRENaoValida
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, nome

   .. attribute:: nome
      :type: str

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Nome legível do motivo usado pela DRE para não validar uma solicitação.

api
---

.. automodule:: src.cardapio.base.api
   :members:
   :show-inheritance:

serializers
~~~~~~~~~~~

.. automodule:: src.cardapio.base.api.serializers
   :members:
   :show-inheritance:

serializers\_create
~~~~~~~~~~~~~~~~~~~

.. automodule:: src.cardapio.base.api.serializers_create
   :members:
   :show-inheritance:

validators
~~~~~~~~~~

.. automodule:: src.cardapio.base.api.validators
   :members:
   :show-inheritance:

viewsets
~~~~~~~~

.. automodule:: src.cardapio.base.api.viewsets
   :members:
   :show-inheritance:

fixtures
--------

.. automodule:: src.cardapio.base.fixtures
   :members:
   :show-inheritance:

fixtures/factories
~~~~~~~~~~~~~~~~~~

.. automodule:: src.cardapio.base.fixtures.factories
   :members:
   :show-inheritance:

.. automodule:: src.cardapio.base.fixtures.factories.base_factory
   :members:
   :show-inheritance:
