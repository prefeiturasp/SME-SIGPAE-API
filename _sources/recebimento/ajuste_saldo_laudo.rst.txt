ajuste\_saldo\_laudo
====================

Submódulo de ajuste de saldo do laudo do módulo de recebimento. Gerencia
os descontos de quantidade contra o saldo disponível dos laudos dos
documentos de recebimento (aprovados pela DILOG Qualidade).

O submódulo é composto por:

- **Modelos**: :class:`AjusteSaldo <src.recebimento.ajuste_saldo_laudo.models.AjusteSaldo>`,
  com a ``quantidade_descontada`` por documento de recebimento.
- **API**: endpoint ``/ajuste-saldo-laudo/`` com CRUD, restrito ao perfil
  ``DILOG_QUALIDADE``, e ações de listagem de cronogramas e documentos.
- **Admin**: registro do ``AjusteSaldo``.

Regra central de negócio: a quantidade descontada não pode ser maior que
o saldo disponível do laudo, calculado por ``calcular_saldo_laudo``
(quantidade do laudo menos o total recebido em fichas ``ASSINADA`` menos
os ajustes já registrados). Na atualização, o saldo após o desconto não
pode ser menor que zero.

.. automodule:: src.recebimento.ajuste_saldo_laudo
   :members:
   :show-inheritance:

.. toctree::
   :maxdepth: 4

   ajuste_saldo_laudo/models
   ajuste_saldo_laudo/api
   ajuste_saldo_laudo/admin
