recebimento
===========

Módulo de recebimento do sistema SIGPAE. Formaliza o recebimento físico
dos produtos entregues contra as etapas dos cronogramas por meio da
**ficha de recebimento**, registro da inspeção de qualidade conduzida
pela DILOG Qualidade: conformidade de lotes, datas de fabricação e
validade, pesos das embalagens primárias, sistema de vedação da embalagem
secundária, veículos e notas fiscais, respostas às questões de
conferência, ocorrências (falta/recusa/outros), anexos e reposição de
cronograma.

O módulo é composto por:

- **Modelos**: :class:`FichaDeRecebimento <src.recebimento.models.FichaDeRecebimento>`
  (registro central, com workflow ``FluxoFichaDeRecebimento``) e os modelos
  complementares :class:`QuestaoConferencia`, :class:`QuestoesPorProduto`,
  :class:`ReposicaoCronogramaFichaRecebimento`,
  :class:`VeiculoFichaDeRecebimento`, :class:`ArquivoFichaRecebimento`,
  :class:`QuestaoFichaRecebimento`,
  :class:`DocumentoFichaDeRecebimento` e :class:`OcorrenciaFichaRecebimento`.
- **API**: endpoints ``/questoes-conferencia/``, ``/questoes-por-produto/``,
  ``/rascunho-ficha-de-recebimento/``, ``/fichas-de-recebimento/``,
  ``/reposicao-ficha-de-recebimento/``,
  ``/reposicao-cronograma-ficha-recebimento/`` e ``/ajuste-saldo-laudo/``.
- **Admin**: telas das questões de conferência, questões por produto,
  fichas de recebimento (com veículos, arquivos, questões e ocorrências em
  inlines) e reposições de cronograma.
- **Fixtures**: factories utilizadas nos testes e o seed data dos tipos de
  reposição.
- **Submódulo ajuste de saldo do laudo**: :class:`AjusteSaldo
  <src.recebimento.ajuste_saldo_laudo.models.AjusteSaldo>`, que registra
  descontos de quantidade contra o saldo do laudo dos documentos de
  recebimento.

Regra central de negócio: a ficha de recebimento nasce em ``RASCUNHO`` e é
assinada pela CODAE (transição ``inicia_fluxo``, status ``ASSINADA``); uma
ficha assinada volta para ``RASCUNHO`` (``volta_para_rascunho``) quando é
editada pelo rascunho. Apenas documentos de recebimento com status
``APROVADO`` podem ser vinculados a uma ficha, e apenas fichas ``ASSINADA``
são consideradas no cálculo do saldo do laudo e habilitam a empresa a
constar em um termo de recebimento definitivo.

.. automodule:: src.recebimento
   :members:
   :show-inheritance:

.. toctree::
   :maxdepth: 4

   recebimento/models
   recebimento/api
   recebimento/admin
   recebimento/fixtures
   recebimento/ajuste_saldo_laudo
