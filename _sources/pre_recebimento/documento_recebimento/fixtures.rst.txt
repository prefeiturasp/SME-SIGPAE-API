fixtures
========

factories
---------

.. automodule:: src.pre_recebimento.documento_recebimento.fixtures.factories
   :members:
   :show-inheritance:

.. automodule:: src.pre_recebimento.documento_recebimento.fixtures.factories.documentos_de_recebimento_factory
   :members:
   :show-inheritance:

Factories utilizadas nos testes:

- ``DocumentoDeRecebimentoFactory``: cria um ``DocumentoDeRecebimento`` com
  cronograma, número do laudo único, lotes, unidade de medida e
  laboratório (``SubFactory`` das factories de seus módulos).
- ``TipoDeDocumentoDeRecebimentoFactory``: cria um tipo de documento
  vinculado a um documento (padrão ``LAUDO``).
- ``ArquivoDoTipoDeDocumentoFactory``: cria um arquivo de tipo de documento
  com um arquivo PDF temporário.
- ``DataDeFabricaoEPrazoFactory``: cria datas de fabricação (no passado) e
  validade (no futuro) para um documento.
