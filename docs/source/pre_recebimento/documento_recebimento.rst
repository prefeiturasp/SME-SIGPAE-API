documento_recebimento
=====================

Submódulo de documentos de recebimento do pré-recebimento. Gerencia os
documentos que o fornecedor deve apresentar para cada cronograma de
entrega (laudo laboratorial, declarações, certificados, rastreabilidade,
etc.), o fluxo de análise da CODAE/DILOG Qualidade (aprovação ou correção)
e a assinatura digital do laudo.

O submódulo é composto por:

- **Modelos**: :class:`~src.pre_recebimento.documento_recebimento.models.DocumentoDeRecebimento`
  (documento por cronograma, com workflow de aprovação),
  :class:`~src.pre_recebimento.documento_recebimento.models.TipoDeDocumentoDeRecebimento`
  (tipos de documento e seus arquivos),
  :class:`~src.pre_recebimento.documento_recebimento.models.ArquivoDoTipoDeDocumento`
  (arquivo de um tipo de documento) e
  :class:`~src.pre_recebimento.documento_recebimento.models.DataDeFabricaoEPrazo`
  (datas de fabricação/validade e prazo máximo de recebimento do lote).
- **API**: endpoints de cadastro pelo fornecedor, análise pela CODAE
  (rascunho e final), correção/atualização pelo fornecedor, download do
  laudo assinado, dashboard e relatórios.
- **Admin**: telas com inlines aninhadas (tipos de documento → arquivos).

Regras centrais de negócio:

- O documento nasce com status ``DOCUMENTO_CRIADO`` e, ao ser enviado
  pelo fornecedor, vai para ``ENVIADO_PARA_ANALISE`` (notificação e e-mail
  para ``DILOG_QUALIDADE`` e ``COORDENADOR_CODAE_DILOG_LOGISTICA``).
- A CODAE pode aprovar (``APROVADO``) ou enviar para correção
  (``ENVIADO_PARA_CORRECAO``) com uma ``correcao_solicitada``.
- O fornecedor corrige (volta para ``ENVIADO_PARA_ANALISE``) ou atualiza
  um documento já aprovado (também volta para ``ENVIADO_PARA_ANALISE``).
- Na correção, o documento deve conter ao menos um tipo ``LAUDO``; na
  criação, um tipo ``LAUDO`` informado exige arquivos com ``arquivo`` e
  ``nome``.

.. automodule:: src.pre_recebimento.documento_recebimento
   :members:
   :show-inheritance:

.. toctree::
   :maxdepth: 4

   documento_recebimento/models
   documento_recebimento/api
   documento_recebimento/admin
   documento_recebimento/fixtures
