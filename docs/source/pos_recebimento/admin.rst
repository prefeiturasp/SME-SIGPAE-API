admin
=====

.. automodule:: src.pos_recebimento.admin
   :members:
   :show-inheritance:

Configurações de administração do Pós-Recebimento:

- ``TermoRecebimentoProvisorioAdmin``: lista os termos com ``uuid``,
  ``empresa``, ``contrato``, ``valor_contrato``, ``status``, ``criado_em``
  e ``alterado_em``. Permite editar inline os cronogramas do termo
  (``CronogramaTermoRecebimentoProvisorioInline``, com ``cronograma`` e
  ``quantidade_total_recebida``), mantém os campos
  ``uuid``, ``criado_em``, ``alterado_em`` e ``criado_por`` como somente
  leitura, busca por nome fantasia da empresa, número do contrato ou
  ``uuid`` e filtra por ``status``.
- ``CronogramaTermoRecebimentoProvisorioAdmin``: lista os vínculos
  ``termo``/``cronograma`` com ``quantidade_total_recebida``, com busca por
  ``uuid`` do termo ou número do cronograma.
