cronograma\_semanal
===================

Submódulo de cronogramas semanais FLV. Gerencia os cronogramas semanais
de hortifrutigranjeiros, derivados dos cronogramas mensais Ponto a Ponto
assinados, com as programações de entrega de cada semana.

O submódulo é composto por:

- **Modelos**: :class:`CronogramaSemanal <src.pre_recebimento.cronograma_semanal.models.CronogramaSemanal>`
  (com workflow ``FluxoCronogramaSemanal``) e
  :class:`ProgramacaoEntregaSemanal <src.pre_recebimento.cronograma_semanal.models.ProgramacaoEntregaSemanal>`.
- **API**: endpoint ``/cronogramas-semanais/`` com criação de rascunho,
  listagem, detalhe, calendário, assinatura/envio, ciência do fornecedor,
  alteração e geração de PDF.
- **Admin**: cadastro dos cronogramas semanais com as programações de
  entrega em inline.
- **Fixtures**: factory ``CronogramaSemanalFactory`` utilizada nos testes.

Regra central de negócio: um cronograma semanal só pode ser criado a
partir de um cronograma mensal do tipo **Ponto a Ponto** com status
``ASSINADO_CODAE``. O fluxo do ``FluxoCronogramaSemanal`` inicia em
``RASCUNHO`` e segue ``ENVIADO_AO_FORNECEDOR`` → ``FORNECEDOR_CIENTE``;
após a ciência do fornecedor, a DILOG pode alterar o cronograma
(``alterar_cronograma``, de ``FORNECEDOR_CIENTE`` para
``ENVIADO_AO_FORNECEDOR``).

.. automodule:: src.pre_recebimento.cronograma_semanal
   :members:
   :show-inheritance:

.. toctree::
   :maxdepth: 4

   cronograma_semanal/models
   cronograma_semanal/api
   cronograma_semanal/admin
   cronograma_semanal/fixtures
