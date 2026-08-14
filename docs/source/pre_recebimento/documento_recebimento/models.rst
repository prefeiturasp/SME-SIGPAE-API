models
======

.. automodule:: src.pre_recebimento.documento_recebimento.models
   :members:
   :show-inheritance:
   :exclude-members:
      ArquivoDoTipoDeDocumento,
      TipoDeDocumentoDeRecebimento,
      DocumentoDeRecebimento,
      DataDeFabricaoEPrazo,
      DoesNotExist,
      MultipleObjectsReturned

ArquivoDoTipoDeDocumento
------------------------

Arquivo (PDF ou imagem) anexado a um tipo de documento de recebimento.
É o que efetivamente comprova o documento apresentado pelo fornecedor
(ex.: o PDF do laudo laboratorial).

Regras de negócio:

- Extensões aceitas: ``PDF``, ``PNG``, ``JPG`` e ``JPEG``
  (``FileExtensionValidator``).
- Tamanho máximo de 10 MB (``validate_file_size_10mb``).
- Ao excluir o registro, o arquivo físico também é removido do disco
  (override de ``delete``).

.. autoclass:: ArquivoDoTipoDeDocumento
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, arquivo, delete, id, nome, objects, tipo_de_documento, tipo_de_documento_id, uuid

   .. attribute:: id
      :type: int

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemChaveExterna``)

      **Descrição:**
      Identificador externo único do arquivo.

   .. attribute:: tipo_de_documento
      :type: TipoDeDocumentoDeRecebimento

      **Descrição:**
      Tipo de documento ao qual o arquivo pertence (``on_delete=CASCADE``).

   .. attribute:: arquivo
      :type: django.db.models.fields.files.FieldFile

      **Descrição:**
      Arquivo enviado (``upload_to="documentos_de_recebimento"``), aceitando
      PDF/PNG/JPG/JPEG até 10 MB. Recebido como base64 pela API e convertido
      para ``ContentFile`` no helper de criação.

   .. attribute:: nome
      :type: str

      **Descrição:**
      Nome de exibição do arquivo.

TipoDeDocumentoDeRecebimento
----------------------------

Tipo de documento exigido/apresentado no recebimento de um cronograma,
com seus arquivos anexados. O mesmo tipo não pode se repetir em um mesmo
documento (``unique_together`` entre ``documento_recebimento`` e
``tipo_documento``).

Tipos possíveis:

- ``LAUDO`` (Laudo) — obrigatório na correção de documentos.
- ``DECLARACAO_LEI_1512010`` (Declaração de atendimento a Lei Municipal: 15.120/10).
- ``CERTIFICADO_CONF_ORGANICA`` (Certificado de conformidade orgânica).
- ``RASTREABILIDADE`` (Rastreabilidade).
- ``DECLARACAO_MATERIA_ORGANICA`` (Declaração de Matéria Láctea).
- ``OUTROS`` (Outros) — exige ``descricao_documento``.

Regra de negócio: quando o tipo é ``LAUDO``, o serializador de criação
exige que cada arquivo tenha ``arquivo`` e ``nome`` preenchidos.

.. autoclass:: TipoDeDocumentoDeRecebimento
   :members:
   :show-inheritance:
   :exclude-members: CERTIFICADO_CONF_ORGANICA, DECLARACAO_LEI_1512010, DECLARACAO_MATERIA_ORGANICA, DoesNotExist, LAUDO, MultipleObjectsReturned, OUTROS, RASTREABILIDADE, TIPO_DOC_CHOICES, TIPO_DOC_CERTIFICADO_CONF_ORGANICA, TIPO_DOC_DECLARACAO_LEI_1512010, TIPO_DOC_DECLARACAO_MATERIA_ORGANICA, TIPO_DOC_LAUDO, TIPO_DOC_OUTROS, TIPO_DOC_RASTREABILIDADE, arquivos, descricao_documento, documento_recebimento, documento_recebimento_id, get_tipo_documento_display, id, objects, tipo_documento, uuid

   .. attribute:: id
      :type: int

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemChaveExterna``)

      **Descrição:**
      Identificador externo único do tipo de documento.

   .. attribute:: documento_recebimento
      :type: DocumentoDeRecebimento

      **Descrição:**
      Documento de recebimento ao qual o tipo pertence
      (``on_delete=CASCADE``).

   .. attribute:: tipo_documento
      :type: str

      **Descrição:**
      Tipo do documento. Valores possíveis: ``LAUDO``,
      ``DECLARACAO_LEI_1512010``, ``CERTIFICADO_CONF_ORGANICA``,
      ``RASTREABILIDADE``, ``DECLARACAO_MATERIA_ORGANICA`` e ``OUTROS``.

   .. attribute:: descricao_documento
      :type: str

      **Descrição:**
      Descrição do documento. Obrigatória quando ``tipo_documento = OUTROS``.

   .. attribute:: arquivos
      :type: django.db.models.QuerySet[ArquivoDoTipoDeDocumento]

      **Descrição:**
      Relação reversa 1:N com :class:`ArquivoDoTipoDeDocumento`
      (``related_name="arquivos"``). Lista os arquivos anexados a este tipo
      de documento.

DocumentoDeRecebimento
----------------------

Modelo central do submódulo. Representa o conjunto de documentos de
recebimento apresentados pelo fornecedor para um cronograma de entrega,
incluindo o número do laudo, o laboratório credenciado, a quantidade do
laudo, o lote e as datas de fabricação/validade/prazo de recebimento.

Possui um **workflow de aprovação**
(``DocumentoDeRecebimentoWorkflow``) com os estados:

- ``DOCUMENTO_CRIADO`` (Documento Criado) — estado inicial.
- ``ENVIADO_PARA_ANALISE`` (Enviado para Análise) — enviado pelo
  fornecedor (transição ``inicia_fluxo``); dispara notificação e e-mail
  para os perfis ``DILOG_QUALIDADE`` e ``COORDENADOR_CODAE_DILOG_LOGISTICA``.
- ``ENVIADO_PARA_CORRECAO`` (Enviado para Correção) — a CODAE solicitou
  correções (transição ``qualidade_solicita_correcao``, com o texto em
  ``correcao_solicitada``).
- ``APROVADO`` (Aprovado) — a CODAE aprovou (transição
  ``qualidade_aprova_analise``).

O fluxo também permite ``fornecedor_realiza_correcao`` (de
``ENVIADO_PARA_CORRECAO`` para ``ENVIADO_PARA_ANALISE``) e
``fornecedor_atualiza`` (de ``APROVADO`` para ``ENVIADO_PARA_ANALISE``).
Cada transição gera um ``LogSolicitacoesUsuario`` do tipo
``DOCUMENTO_DE_RECEBIMENTO``.

Regras de negócio:

- Ao corrigir um documento (fornecedor), é obrigatório informar ao menos
  um tipo ``LAUDO`` (validado no ``DocumentoDeRecebimentoCorrecaoSerializer``).
  Na criação, quando um tipo ``LAUDO`` é informado, cada arquivo deve ter
  ``arquivo`` e ``nome`` preenchidos.
- O laudo assinado (``arquivo_laudo_assinado``) é gerado a partir do log de
  aprovação (``DOCUMENTO_APROVADO``) e do arquivo de tipo ``LAUDO``; o
  endpoint de download restringe a geração a documentos ``APROVADO``.
- O saldo do laudo é calculado como ``quantidade_laudo`` menos o total
  recebido em fichas assinadas menos os ajustes de saldo
  (``calcular_saldo_laudo``, no serializador).

.. autoclass:: DocumentoDeRecebimento
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, ajustes_saldo, alterado_em, arquivo_laudo_assinado, correcao_solicitada, criado_em, cronograma, cronograma_id, data_final_lote, datas_fabricacao_e_prazos, fichas_documentos, fichas_recebimentos, fornecedor_atualiza, fornecedor_realiza_correcao, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, get_status_display, id, inicia_fluxo, laboratorio, laboratorio_id, log_mais_recente, logs, numero_laudo, numero_lote_laudo, objects, qualidade_aprova_analise, qualidade_solicita_correcao, quantidade_laudo, salvar_log_transicao, status, tipos_de_documentos, unidade_medida, unidade_medida_id, uuid, workflow_class

   .. attribute:: id
      :type: int

      **Origem:**
      ``dados_comuns/behaviors.py`` (``ModeloBase``)

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemChaveExterna``)

      **Descrição:**
      Identificador externo único do documento de recebimento.

   .. attribute:: id_externo
      :type: str

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemIdentificadorExternoAmigavel``)

      **Descrição:**
      Identificador externo amigável composto pelos 5 primeiros caracteres
      maiúsculos do UUID.

   .. attribute:: cronograma
      :type: cronograma_entrega.Cronograma

      **Descrição:**
      Cronograma de entrega ao qual o documento se refere
      (``on_delete=PROTECT``). Fornecedores só veem documentos dos seus
      próprios cronogramas.

   .. attribute:: numero_laudo
      :type: str

      **Descrição:**
      Número do laudo. Obrigatório na criação.

   .. attribute:: laboratorio
      :type: qualidade.Laboratorio | None

      **Descrição:**
      Laboratório credenciado responsável pelo laudo
      (``on_delete=PROTECT``, opcional).

   .. attribute:: quantidade_laudo
      :type: decimal.Decimal | None

      **Descrição:**
      Quantidade total do laudo (Decimal com até 15 dígitos e 2 casas
      decimais). Base do cálculo do saldo do laudo.

   .. attribute:: numero_lote_laudo
      :type: str

      **Descrição:**
      Número(s) do(s) lote(s) do laudo (pode conter vários, separados).

   .. attribute:: unidade_medida
      :type: base.UnidadeMedida | None

      **Descrição:**
      Unidade de medida da quantidade do laudo.

   .. attribute:: data_final_lote
      :type: datetime.date | None

      **Descrição:**
      Data de conclusão do laudo (data final do lote).

   .. attribute:: correcao_solicitada
      :type: str

      **Descrição:**
      Texto da correção solicitada pela CODAE quando o documento foi
      enviado para correção. Também usado pelo serializador de análise
      para decidir entre aprovar ou solicitar correção.

   .. attribute:: status
      :type: str

      **Origem:**
      ``dados_comuns/fluxo_status.py`` (``DocumentoDeRecebimentoWorkflow``)

      **Descrição:**
      Status atual do workflow. Estados possíveis: ``DOCUMENTO_CRIADO``,
      ``ENVIADO_PARA_ANALISE``, ``ENVIADO_PARA_CORRECAO`` e ``APROVADO``.

   .. attribute:: criado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``CriadoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na criação do documento.

   .. attribute:: alterado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemAlteradoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na última alteração do documento.

   .. attribute:: logs
      :type: list[LogSolicitacoesUsuario]

      **Origem:**
      ``dados_comuns/behaviors.py`` (``Logs``)

      **Descrição:**
      Lista dos registros de log de transições de status do documento,
      ordenados por ``criado_em``.

   .. attribute:: log_mais_recente
      :type: LogSolicitacoesUsuario | None

      **Origem:**
      ``dados_comuns/behaviors.py`` (``Logs``)

      **Descrição:**
      Último registro de log de transição de status do documento.

   .. attribute:: tipos_de_documentos
      :type: django.db.models.QuerySet[TipoDeDocumentoDeRecebimento]

      **Descrição:**
      Relação reversa 1:N com :class:`TipoDeDocumentoDeRecebimento`
      (``related_name="tipos_de_documentos"``). Lista os tipos de documento
      apresentados (laudo, declarações, certificados, etc.), cada um com
      seus arquivos.

   .. attribute:: datas_fabricacao_e_prazos
      :type: django.db.models.QuerySet[DataDeFabricaoEPrazo]

      **Descrição:**
      Relação reversa 1:N com :class:`DataDeFabricaoEPrazo`
      (``related_name="datas_fabricacao_e_prazos"``). Lista as datas de
      fabricação/validade e os prazos máximos de recebimento do lote.

   .. attribute:: fichas_documentos
      :type: django.db.models.QuerySet[DocumentoFichaDeRecebimento]

      **Descrição:**
      Relação reversa 1:N com :class:`DocumentoFichaDeRecebimento
      <src.recebimento.models.DocumentoFichaDeRecebimento>`
      (``related_name="fichas_documentos"``). Vínculo com as fichas de
      recebimento que registraram quantidades recebidas contra este
      documento.

   .. attribute:: fichas_recebimentos
      :type: django.db.models.QuerySet[FichaDeRecebimento]

      **Descrição:**
      Relação M:N com :class:`FichaDeRecebimento
      <src.recebimento.models.FichaDeRecebimento>` através de
      ``DocumentoFichaDeRecebimento`` (``related_name="fichas_recebimentos"``).

   .. attribute:: ajustes_saldo
      :type: django.db.models.QuerySet[AjusteSaldo]

      **Descrição:**
      Relação reversa 1:N com :class:`AjusteSaldo
      <src.recebimento.ajuste_saldo_laudo.models.AjusteSaldo>`
      (``related_name="ajustes_saldo"``). Ajustes (descontos) de saldo do
      laudo registrados posteriormente.

   .. attribute:: arquivo_laudo_assinado
      :type: bytes

      **Descrição:**
      Propriedade que gera o PDF do laudo assinado digitalmente: busca o
      log de aprovação (``DOCUMENTO_APROVADO``), o arquivo do tipo
      ``LAUDO`` e mescla o rodapé de assinatura digital na última página.
      Lança ``ValidationError`` se não houver log de aprovação.

   .. attribute:: salvar_log_transicao
      :type: Callable

      **Descrição:**
      Registra no log uma transição de status do documento, criando um
      ``LogSolicitacoesUsuario`` com o tipo ``DOCUMENTO_DE_RECEBIMENTO``.

DataDeFabricaoEPrazo
--------------------

Datas de fabricação e validade dos lotes do laudo, com o prazo máximo
para recebimento. O ``prazo_maximo_recebimento`` é informado em dias
(30/60/90/120/180) ou ``OUTRO`` (com justificativa); quando diferente de
``OUTRO``, a ``data_maxima_recebimento`` é calculada automaticamente
(signal ``pre_save``) somando o prazo à ``data_fabricacao``.

.. autoclass:: DataDeFabricaoEPrazo
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, PRAZO_120, PRAZO_180, PRAZO_30, PRAZO_60, PRAZO_90, PRAZO_CHOICES, PRAZO_OUTRO, data_fabricacao, data_maxima_recebimento, data_validade, documento_recebimento, documento_recebimento_id, get_prazo_maximo_recebimento_display, id, justificativa, objects, prazo_maximo_recebimento, uuid

   .. attribute:: id
      :type: int

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemChaveExterna``)

      **Descrição:**
      Identificador externo único do registro.

   .. attribute:: documento_recebimento
      :type: DocumentoDeRecebimento

      **Descrição:**
      Documento de recebimento ao qual o registro pertence
      (``on_delete=CASCADE``).

   .. attribute:: data_fabricacao
      :type: datetime.date | None

      **Descrição:**
      Data de fabricação do lote. Obrigatória na análise final.

   .. attribute:: data_validade
      :type: datetime.date | None

      **Descrição:**
      Data de validade do lote. Obrigatória na análise final.

   .. attribute:: data_maxima_recebimento
      :type: datetime.date | None

      **Descrição:**
      Data máxima de recebimento do lote. Calculada automaticamente no
      ``pre_save`` como ``data_fabricacao + prazo_maximo_recebimento``
      quando o prazo é numérico (diferente de ``OUTRO``).

   .. attribute:: prazo_maximo_recebimento
      :type: str

      **Descrição:**
      Prazo máximo para recebimento em dias. Valores possíveis: ``30``,
      ``60``, ``90``, ``120``, ``180`` e ``OUTRO``. Obrigatório na análise
      final; quando ``OUTRO``, exige ``justificativa``.

   .. attribute:: justificativa
      :type: str

      **Descrição:**
      Justificativa. Obrigatória quando ``prazo_maximo_recebimento = OUTRO``.
