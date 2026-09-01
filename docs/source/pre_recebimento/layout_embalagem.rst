layout\_embalagem
=================

Submódulo de layout de embalagem do pré-recebimento. Gerencia o envio,
pela empresa fornecedora, das imagens das embalagens (primária, secundária
e terciária) de um produto, e a aprovação pela CODAE — com possibilidade
de solicitação de correção e reenvio.

O submódulo é composto por:

- **Modelos**: :class:`LayoutDeEmbalagem <src.pre_recebimento.layout_embalagem.models.LayoutDeEmbalagem>`
  (com workflow ``FluxoLayoutDeEmbalagem``),
  :class:`TipoDeEmbalagemDeLayout <src.pre_recebimento.layout_embalagem.models.TipoDeEmbalagemDeLayout>`
  e
  :class:`ImagemDoTipoDeEmbalagem <src.pre_recebimento.layout_embalagem.models.ImagemDoTipoDeEmbalagem>`.
- **API**: endpoint ``/layouts-de-embalagem/`` com CRUD (criação pelo
  fornecedor), análise da CODAE, correção do fornecedor, dashboard e
  download da imagem assinada.
- **Admin**: cadastro dos layouts com tipos de embalagem e imagens em
  inlines aninhados.
- **Fixtures**: factory ``LayoutDeEmbalagemFactory`` utilizada nos testes.

Regra central de negócio: o fluxo do ``FluxoLayoutDeEmbalagem`` inicia em
``LAYOUT_CRIADO`` e segue para ``ENVIADO_PARA_ANALISE``; a CODAE aprova
(``APROVADO``) ou solicita correção (``SOLICITADO_CORRECAO``); o
fornecedor corrige (volta para ``ENVIADO_PARA_ANALISE``) ou atualiza um
layout aprovado. O layout só é aprovado quando **todos** os tipos de
embalagem estão ``APROVADO``.

.. automodule:: src.pre_recebimento.layout_embalagem
   :members:
   :show-inheritance:

.. toctree::
   :maxdepth: 4

   layout_embalagem/models
   layout_embalagem/api
   layout_embalagem/admin
   layout_embalagem/fixtures
