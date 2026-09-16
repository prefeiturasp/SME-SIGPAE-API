admin
=====

.. automodule:: src.pos_recebimento.admin
   :members:
   :show-inheritance:

Configurações de administração do Pós-Recebimento:

- ``TermoRecebimentoDefinitivoAdmin``: lista os termos com ``uuid``,
  ``empresa``, ``contrato``, ``status``, ``criado_em`` e ``alterado_em``.
  Permite editar inline os cronogramas do termo
  (``CronogramaTermoRecebimentoDefinitivoInline``, com ``cronograma``,
  ``valor_contrato`` e ``quantidade_total_recebida``), mantém os campos
  ``uuid``, ``criado_em``, ``alterado_em`` e ``criado_por`` como somente
  leitura, busca por nome fantasia da empresa, número do contrato ou
  ``uuid`` e filtra por ``status``.
- ``CronogramaTermoRecebimentoDefinitivoAdmin``: lista os vínculos
  ``termo``/``cronograma`` com ``valor_contrato`` e
  ``quantidade_total_recebida``, com busca por ``uuid`` do termo ou número
  do cronograma.
