api
===

.. automodule:: src.pre_recebimento.documento_recebimento.api
   :members:
   :show-inheritance:

A API do submódulo expõe o endpoint ``/documentos-de-recebimento/``
(basename ``documentos-de-recebimento``), com CRUD completo e ações de
análise/correção/atualização/relatório:

- ``GET /documentos-de-recebimento/`` — listagem paginada com filtros
  (``DocumentoDeRecebimentoFilter``); fornecedores veem apenas os
  documentos dos próprios cronogramas.
- ``POST /documentos-de-recebimento/`` — criação pelo fornecedor
  (``UsuarioEhFornecedor``); o documento vai para ``ENVIADO_PARA_ANALISE``.
- ``GET /documentos-de-recebimento/<uuid>/`` — detalhe (visão do
  fornecedor ou da CODAE, conforme o perfil).
- ``PATCH/DELETE /documentos-de-recebimento/<uuid>/`` — atualização e
  exclusão (exclusão apenas por fornecedor).
- Ações ``detail=False``: ``dashboard``, ``listagem-relatorio`` e
  ``exportar-excel``.
- Ações ``detail=True``: ``analise-documentos-rascunho``,
  ``analise-documentos``, ``corrigir-documentos``,
  ``atualizar-documentos`` e ``download-laudo-assinado``.

viewsets
--------

.. automodule:: src.pre_recebimento.documento_recebimento.api.viewsets
   :members:
   :show-inheritance:

``DocumentoDeRecebimentoModelViewSet`` (``ModelViewSet`` com
``ViewSetActionPermissionMixin``):

- **Permissões**: leitura/visualização com
  ``PermissaoParaVisualizarDocumentosDeRecebimento``; ``create`` e
  ``delete`` restritos a ``UsuarioEhFornecedor``.
- **Queryset dinâmico**: usuários fornecedores veem apenas documentos de
  cronogramas da própria empresa
  (``cronograma__empresa = vinculo_atual.instituicao``).
- **Serializador dinâmico**: ``list`` → ``DocumentoDeRecebimentoSerializer``;
  ``retrieve`` → ``DocRecebimentoDetalharSerializer`` (fornecedor) ou
  ``DocRecebimentoDetalharCodaeSerializer`` (CODAE); demais ações →
  ``DocumentoDeRecebimentoCreateSerializer``.

Ações:

- ``dashboard`` (GET): painel por status via
  ``ServiceDashboardDocumentosDeRecebimento``.
- ``codae_analisa_documentos_rascunho`` (PATCH ``analise-documentos-rascunho``,
  ``UsuarioEhDilogQualidade``): salva a análise em rascunho (dados do
  laudo/laboratório/datas) sem alterar o status.
- ``codae_analisa_documentos`` (PATCH ``analise-documentos``,
  ``UsuarioEhDilogQualidade``): análise final — se houver
  ``correcao_solicitada`` o documento vai para ``ENVIADO_PARA_CORRECAO``
  (``qualidade_solicita_correcao``), senão é aprovado
  (``qualidade_aprova_analise``).
- ``fornecedor_realiza_correcao`` (PATCH ``corrigir-documentos``,
  ``UsuarioEhFornecedor``): recria os tipos de documento (exigindo ao
  menos um ``LAUDO``) e chama ``fornecedor_realiza_correcao`` (volta para
  ``ENVIADO_PARA_ANALISE``).
- ``fornecedor_realiza_atualizacao`` (PATCH ``atualizar-documentos``,
  ``UsuarioEhFornecedor``): atualiza os tipos de documento de um documento
  ``APROVADO`` (preservando o ``LAUDO``) e chama ``fornecedor_atualiza``
  (volta para ``ENVIADO_PARA_ANALISE``).
- ``download_laudo_assinado`` (GET ``download-laudo-assinado``): retorna o
  PDF do laudo assinado; retorna ``401`` se o documento não estiver
  ``APROVADO``.
- ``lista_relatorio`` (GET ``listagem-relatorio``,
  ``PermissaoParaRelatorioDocumentosDeRecebimento``): relatório por
  cronograma com os documentos (filtros ``CronogramaRelatorioDocumentosFilter``
  e ``status_documento``) e totalizadores (recebidos, pendentes de
  aprovação, enviados para correção, aprovados).
- ``exportar_excel`` (GET ``exportar-excel``,
  ``PermissaoParaRelatorioDocumentosDeRecebimento``): gera e baixa o
  ``relatorio_documentos_recebimento.xlsx`` com o mesmo queryset do
  relatório.

filters
-------

.. automodule:: src.pre_recebimento.documento_recebimento.api.filters
   :members:
   :show-inheritance:

``DocumentoDeRecebimentoFilter`` filtra por ``numero_cronograma``,
``nome_produto``, ``nome_fornecedor`` (razão social da empresa),
``status`` (múltiplo, pelos estados do workflow) e ``data_cadastro``.
``CronogramaRelatorioDocumentosFilter`` (usado no relatório) filtra os
cronogramas por ``empresa`` (uuid), ``nome_produto`` e
``numero_cronograma``.

services
--------

.. automodule:: src.pre_recebimento.documento_recebimento.api.services
   :members:
   :show-inheritance:

``ServiceDashboardDocumentosDeRecebimento`` (herda ``BaseServiceDashboard``)
monta o painel de documentos de recebimento: para cada perfil autorizado
(``DILOG_QUALIDADE``, ``COORDENADOR_CODAE_DILOG_LOGISTICA``,
``DILOG_CRONOGRAMA``, ``ADMINISTRADOR_CODAE_GABINETE`` e
``DILOG_DIRETORIA``), define os status exibidos (``ENVIADO_PARA_ANALISE``,
``APROVADO`` e ``ENVIADO_PARA_CORRECAO``).

helpers
-------

.. automodule:: src.pre_recebimento.documento_recebimento.api.helpers
   :members:
   :show-inheritance:

- ``cria_tipos_de_documentos``: cria os ``TipoDeDocumentoDeRecebimento`` e
  seus ``ArquivoDoTipoDeDocumento`` a partir do payload
  (``arquivos_do_tipo_de_documento`` em base64, convertidos para
  ``ContentFile``).
- ``cria_datas_e_prazos_doc_recebimento``: cria as
  ``DataDeFabricaoEPrazo`` de um documento.

relatorio\_documentos\_recebimento\_excel
-----------------------------------------

.. automodule:: src.pre_recebimento.documento_recebimento.api.relatorio_documentos_recebimento_excel
   :members:
   :show-inheritance:

Geração do Excel do Relatório de Documentos de Recebimento
(``gera_relatorio_documentos_recebimento_xlsx``). O relatório tem 20
colunas (cronograma, produto, empresa, pregão, processo SEI, laudo,
status, laboratório, datas de fabricação/validade, lotes, datas,
unidade, quantidades e saldos do laudo, observações e solicitação de
correção), com sanitização contra injeção de fórmulas e formatação
numérica das quantidades/saldos.

serializers
~~~~~~~~~~~

.. automodule:: src.pre_recebimento.documento_recebimento.api.serializers.serializers
   :members:
   :show-inheritance:

Serializadores de saída:

- ``calcular_saldo_laudo``: função que calcula o saldo do laudo
  (``quantidade_laudo`` − total recebido em fichas assinadas − ajustes de
  saldo).
- ``DocRecebimentoFichaDeRecebimentoSerializer``: dados do documento na
  ficha de recebimento (datas de fabricação/validade, quantidade recebida
  e saldo do laudo).
- ``DocumentoDeRecebimentoSerializer``: linha da listagem (cronograma,
  pregão, produto, ``programa_leve_leite``, status e data de cadastro).
- ``PainelDocumentoDeRecebimentoSerializer``: linha do dashboard (produto,
  empresa, status, log mais recente).
- ``ArquivoDoTipoDeDocumentoLookupSerializer`` /
  ``TipoDocumentoDeRecebimentoLookupSerializer``: arquivos e tipos com seus
  arquivos aninhados.
- ``DocRecebimentoDetalharSerializer``: detalhe para o fornecedor
  (tipos de documento, logs, correção solicitada).
- ``DocRecebimentoDetalharCodaeSerializer``: detalhe para a CODAE (com
  laboratório, unidade de medida, datas de fabricação/prazos, número SEI,
  fornecedor e saldo do laudo).
- ``DocumentoDeRecebimentoDetalheRelatorioSerializer``: linha do relatório
  (laboratório, unidade, quantidades, saldos, datas e status).
- ``CronogramaRelatorioDocumentosSerializer``: cronograma do relatório com
  os documentos aninhados.
- ``DocumentoDeRecebimentoParaAjusteSaldoSerializer``: dados para o ajuste
  de saldo do laudo (unidade, quantidade e saldo atual).

serializer\_create
~~~~~~~~~~~~~~~~~~

.. automodule:: src.pre_recebimento.documento_recebimento.api.serializers.serializer_create
   :members:
   :show-inheritance:

Serializadores de entrada:

- ``TipoDeDocumentoDeRecebimentoCreateSerializer``: tipo do documento com
  ``arquivos_do_tipo_de_documento`` (JSON, write-only); quando o tipo é
  ``LAUDO``, exige ``arquivo`` e ``nome`` em cada arquivo.
- ``DocumentoDeRecebimentoCreateSerializer``: criação pelo fornecedor —
  ``cronograma`` (uuid) e ``numero_laudo`` obrigatórios; cria os tipos de
  documento (helper) e chama ``inicia_fluxo`` (o documento vai para
  ``ENVIADO_PARA_ANALISE``).
- ``DataDeFabricaoEPrazoAnalisarRascunhoSerializer``: dados de
  fabricação/prazo em rascunho (todos opcionais).
- ``DataDeFabricaoEPrazoAnalisarSerializer``: versão da análise final —
  ``data_fabricacao``, ``data_validade`` e ``prazo_maximo_recebimento``
  obrigatórios; quando o prazo é ``OUTRO``, exige ``justificativa``.
- ``DocumentoDeRecebimentoAnalisarRascunhoSerializer``: análise em rascunho
  (laboratório, unidade, quantidade, lote, data final e datas/prazos) —
  não altera o status.
- ``DocumentoDeRecebimentoAnalisarSerializer`` (herda
  ``CamposObrigatóriosMixin``): análise final da CODAE. O campo
  ``correcao_solicitada`` é opcional; quando preenchido, todos os demais
  campos tornam-se opcionais e o documento é enviado para correção
  (``qualidade_solicita_correcao``); caso contrário, é aprovado
  (``qualidade_aprova_analise``).
- ``TipoDeDocumentoDeRecebimentoCorrecaoSerializer``: tipo de documento na
  correção — ``OUTROS`` exige ``descricao_documento``; todo arquivo exige
  ``arquivo`` e ``nome``.
- ``DocumentoDeRecebimentoCorrecaoSerializer``: correção do fornecedor —
  exige ao menos um tipo ``LAUDO``; apaga os tipos antigos (com seus
  arquivos), recria os novos e chama ``fornecedor_realiza_correcao``.
- ``DocumentoDeRecebimentoAtualizacaoSerializer``: atualização de documento
  aprovado pelo fornecedor — recria os tipos (exceto o ``LAUDO``) e chama
  ``fornecedor_atualiza``.
