models
======

.. automodule:: src.dieta_especial.logs_models.models
   :members:
   :show-inheritance:
   :exclude-members:
      LogDietasAtivasCanceladasAutomaticamente,
      LogQuantidadeDietasAutorizadas,
      LogQuantidadeDietasAutorizadasCEI,
      LogQuantidadeDietasAutorizadasRecreioNasFerias,
      LogQuantidadeDietasAutorizadasRecreioNasFeriasCEI,
      DoesNotExist,
      MultipleObjectsReturned

LogDietasAtivasCanceladasAutomaticamente
----------------------------------------

Log de dietas ativas canceladas automaticamente pelo sistema, registrando
origem e destino da escola e o código EOL do aluno.

.. autoclass:: LogDietasAtivasCanceladasAutomaticamente
   :members:
   :show-inheritance:

LogQuantidadeDietasAutorizadas
------------------------------

Log da quantidade de dietas autorizadas por escola, classificação e período
escolar.

.. autoclass:: LogQuantidadeDietasAutorizadas
   :members:
   :show-inheritance:

LogQuantidadeDietasAutorizadasCEI
---------------------------------

Log da quantidade de dietas autorizadas por escola CEI, incluindo faixa
etária.

.. autoclass:: LogQuantidadeDietasAutorizadasCEI
   :members:
   :show-inheritance:

LogQuantidadeDietasAutorizadasRecreioNasFerias
----------------------------------------------

Log da quantidade de dietas autorizadas por escola no contexto do Recreio nas
Férias.

.. autoclass:: LogQuantidadeDietasAutorizadasRecreioNasFerias
   :members:
   :show-inheritance:

LogQuantidadeDietasAutorizadasRecreioNasFeriasCEI
-------------------------------------------------

Log da quantidade de dietas autorizadas por escola CEI no contexto do Recreio
nas Férias, incluindo faixa etária.

.. autoclass:: LogQuantidadeDietasAutorizadasRecreioNasFeriasCEI
   :members:
   :show-inheritance:
