admin
=====

.. automodule:: src.pre_recebimento.cronograma_semanal.admin
   :members:
   :show-inheritance:

Configurações de administração do submódulo de cronograma semanal:

- ``ProgramacaoEntregaSemanalInline``: inline tabular das programações de
  entrega do cronograma semanal (``mes_programado``, ``data_inicio``,
  ``data_fim`` e ``quantidade``; ``uuid`` somente leitura).
- ``CronogramaSemanalAdmin``: lista os cronogramas com ``numero``,
  ``cronograma_mensal``, ``status`` e ``criado_em``; filtra por ``status``
  e ``criado_em``; busca por número do cronograma semanal ou do cronograma
  mensal. ``uuid``, ``numero``, ``criado_em`` e ``alterado_em`` são
  somente leitura; as programações são editadas via inline.
- ``ProgramacaoEntregaSemanalAdmin``: lista as programações com ``uuid``,
  ``cronograma_semanal``, ``mes_programado``, ``data_inicio`` e
  ``data_fim``; filtra por ``mes_programado``; busca por ``uuid``.
