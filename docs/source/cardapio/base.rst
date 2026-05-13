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
   :exclude-members: DoesNotExist, LANCHE_4H, LANCHE_EMERGENCIAL, MultipleObjectsReturned, horariodocombodotipodealimentacaoporunidadeescolar_set, id, inclusaoalimentacaodacei_set, inversaocardapio_set, nome, objects, parametrizacao_valor_tipo_alimentacao, periodos_escolares, posicao, quantidadedealunosemeiinclusaodealimentacaocemei_set, quantidadeporperiodo_set, quantidadeporperiodosuspensaoalimentacao_set, recreionasferiasunidadetipoalimentacao_set, respostas_relatorio_imr, substituicoes_alimento_para, substituicoes_alimentos_de, substituicoes_cei_tipo_alimentacao_de, substituicoes_cei_tipo_alimentacao_para, substituicoes_cemei_cei_alimento_para, substituicoes_cemei_cei_tipo_alimentacao_de, substituicoes_cemei_emei_alimento_para, substituicoes_cemei_emei_tipo_alimentacao_de, substituicoes_periodo_escolar, suspensoes_periodo_escolar, uuid, valormedicao_set, vinculos

   .. attribute:: id
      :type: int

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django para identificar o registro.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py``

      **Descrição:**
      Identificador externo único do tipo de alimentação, usado em integrações e endpoints que expõem UUID.

   .. attribute:: objects
      :type: django.db.models.manager.Manager[TipoAlimentacao]

      **Descrição:**
      Manager padrão do modelo, usado para construir consultas como ``all()``, ``filter()`` e ``get()``.

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

   .. attribute:: horariodocombodotipodealimentacaoporunidadeescolar_set
      :type: django.db.models.QuerySet[HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar]

      **Descrição:**
      Relação reversa 1:N com :class:`HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar`.

      Lista as faixas de horário cadastradas para este tipo de alimentação em escolas e períodos escolares específicos.

   .. attribute:: inclusaoalimentacaodacei_set
      :type: django.db.models.QuerySet[InclusaoAlimentacaoDaCEI]

      **Descrição:**
      Relação reversa M:N com :class:`InclusaoAlimentacaoDaCEI`.

      Reúne as solicitações de inclusão de alimentação por CEI que utilizam este tipo de alimentação no campo ``tipos_alimentacao``.

   .. attribute:: inversaocardapio_set
      :type: django.db.models.QuerySet[InversaoCardapio]

      **Descrição:**
      Relação reversa M:N com :class:`InversaoCardapio`.

      Reúne as inversões de cardápio que incluem este tipo de alimentação.

   .. attribute:: parametrizacao_valor_tipo_alimentacao
      :type: django.db.models.QuerySet[ParametrizacaoFinanceiraTabelaValor]

      **Descrição:**
      Relação reversa 1:N com :class:`ParametrizacaoFinanceiraTabelaValor`.

      Expõe as parametrizações financeiras em que este tipo de alimentação foi associado a um valor de tabela.

   .. attribute:: periodos_escolares
      :type: django.db.models.QuerySet[escola.PeriodoEscolar]

      **Descrição:**
      Relação reversa M:N com :class:`escola.PeriodoEscolar`.

      Indica em quais períodos escolares este tipo de alimentação pode ser ofertado diretamente.

   .. attribute:: quantidadedealunosemeiinclusaodealimentacaocemei_set
      :type: django.db.models.QuerySet[QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI]

      **Descrição:**
      Relação reversa M:N com :class:`QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI`.

      Reúne as quantidades de alunos da parte EMEI das inclusões CEMEI que usam este tipo de alimentação.

   .. attribute:: quantidadeporperiodo_set
      :type: django.db.models.QuerySet[QuantidadePorPeriodo]

      **Descrição:**
      Relação reversa M:N com :class:`QuantidadePorPeriodo`.

      Lista as quantidades por período de inclusões normais ou contínuas que incluem este tipo de alimentação.

   .. attribute:: quantidadeporperiodosuspensaoalimentacao_set
      :type: django.db.models.QuerySet[QuantidadePorPeriodoSuspensaoAlimentacao]

      **Descrição:**
      Relação reversa M:N com :class:`QuantidadePorPeriodoSuspensaoAlimentacao`.

      Reúne os registros de quantidade por período usados em suspensões de alimentação que referenciam este tipo de alimentação.

   .. attribute:: recreionasferiasunidadetipoalimentacao_set
      :type: django.db.models.QuerySet[RecreioNasFeriasUnidadeTipoAlimentacao]

      **Descrição:**
      Relação reversa 1:N com :class:`RecreioNasFeriasUnidadeTipoAlimentacao`.

      Lista as configurações de tipo de alimentação usadas pelas unidades participantes do programa Recreio nas Férias.

   .. attribute:: respostas_relatorio_imr
      :type: django.db.models.QuerySet[RespostaTipoAlimentacao]

      **Descrição:**
      Relação reversa 1:N com :class:`RespostaTipoAlimentacao`.

      Reúne as respostas de formulários de IMR cujo valor selecionado foi este tipo de alimentação.

   .. attribute:: substituicoes_alimento_para
      :type: django.db.models.QuerySet[SubstituicaoAlimentacaoNoPeriodoEscolar]

      **Descrição:**
      Relação reversa M:N com :class:`SubstituicaoAlimentacaoNoPeriodoEscolar`.

      Identifica as substituições de alteração de cardápio em que este tipo de alimentação aparece como destino da troca.

   .. attribute:: substituicoes_alimentos_de
      :type: django.db.models.QuerySet[SubstituicaoAlimentacaoNoPeriodoEscolar]

      **Descrição:**
      Relação reversa M:N com :class:`SubstituicaoAlimentacaoNoPeriodoEscolar`.

      Identifica as substituições de alteração de cardápio em que este tipo de alimentação aparece como origem da troca.

   .. attribute:: substituicoes_cei_tipo_alimentacao_de
      :type: django.db.models.QuerySet[SubstituicaoAlimentacaoNoPeriodoEscolarCEI]

      **Descrição:**
      Relação reversa M:N com :class:`SubstituicaoAlimentacaoNoPeriodoEscolarCEI`.

      Reúne as substituições de cardápio de CEI em que este tipo de alimentação faz parte do conjunto substituído.

   .. attribute:: substituicoes_cei_tipo_alimentacao_para
      :type: django.db.models.QuerySet[SubstituicaoAlimentacaoNoPeriodoEscolarCEI]

      **Descrição:**
      Relação reversa 1:N com :class:`SubstituicaoAlimentacaoNoPeriodoEscolarCEI`.

      Reúne as substituições de cardápio de CEI em que este tipo de alimentação é o resultado final da troca.

   .. attribute:: substituicoes_cemei_cei_alimento_para
      :type: django.db.models.QuerySet[SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI]

      **Descrição:**
      Relação reversa M:N com :class:`SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI`.

      Lista as substituições da parte CEI do CEMEI em que este tipo de alimentação é usado como destino da troca.

   .. attribute:: substituicoes_cemei_cei_tipo_alimentacao_de
      :type: django.db.models.QuerySet[SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI]

      **Descrição:**
      Relação reversa M:N com :class:`SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI`.

      Lista as substituições da parte CEI do CEMEI em que este tipo de alimentação compõe o conjunto de origem.

   .. attribute:: substituicoes_cemei_emei_alimento_para
      :type: django.db.models.QuerySet[SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI]

      **Descrição:**
      Relação reversa M:N com :class:`SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI`.

      Lista as substituições da parte EMEI do CEMEI em que este tipo de alimentação aparece como destino da troca.

   .. attribute:: substituicoes_cemei_emei_tipo_alimentacao_de
      :type: django.db.models.QuerySet[SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI]

      **Descrição:**
      Relação reversa M:N com :class:`SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI`.

      Lista as substituições da parte EMEI do CEMEI em que este tipo de alimentação compõe o conjunto de origem.

   .. attribute:: suspensoes_periodo_escolar
      :type: django.db.models.QuerySet[SuspensaoAlimentacaoNoPeriodoEscolar]

      **Descrição:**
      Relação reversa M:N com :class:`SuspensaoAlimentacaoNoPeriodoEscolar`.

      Reúne as suspensões de alimentação por período escolar em que este tipo de alimentação foi afetado.

   .. attribute:: valormedicao_set
      :type: django.db.models.QuerySet[ValorMedicao]

      **Descrição:**
      Relação reversa 1:N com :class:`ValorMedicao`.

      Lista os valores lançados na Medição Inicial que referenciam este tipo de alimentação.

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
