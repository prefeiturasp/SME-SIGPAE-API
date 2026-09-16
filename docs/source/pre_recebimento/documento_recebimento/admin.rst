admin
=====

.. automodule:: src.pre_recebimento.documento_recebimento.admin
   :members:
   :show-inheritance:

Configurações de administração do submódulo de documentos de recebimento:

- ``DocumentoDeRecebimentoAdmin`` (``NestedModelAdmin``): lista os
  documentos com cronograma (``get_cronograma``), produto
  (``get_produto``, lido de ``cronograma.ficha_tecnica.produto.nome``),
  número do laudo e data de criação; busca por número do cronograma ou
  nome do produto; mantém ``uuid`` como somente leitura; usa o formulário
  ``ArquivoForm`` e inlines aninhadas: ``TipoDocumentoRecebimentoInline``
  (tipos de documento, com ``uuid`` somente leitura) contendo
  ``ArquivoDoTipoDeDocumentoInline`` (arquivos do tipo).
- ``DataDeFabricaoEPrazo`` é registrado com o admin padrão do Django.
