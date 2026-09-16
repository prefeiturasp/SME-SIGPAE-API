models
======

.. automodule:: src.pre_recebimento.layout_embalagem.models
   :members:
   :show-inheritance:
   :exclude-members:
      ImagemDoTipoDeEmbalagem,
      TipoDeEmbalagemDeLayout,
      LayoutDeEmbalagem,
      DoesNotExist,
      MultipleObjectsReturned

ImagemDoTipoDeEmbalagem
-----------------------

Arquivo (PDF ou imagem) anexado a um tipo de embalagem de layout. É o que
efetivamente comprova o layout apresentado pelo fornecedor.

Regras de negócio:

- Extensões aceitas: ``PDF``, ``PNG``, ``JPG`` e ``JPEG``
  (``FileExtensionValidator``).
- Tamanho máximo de 10 MB (``validate_file_size_10mb``).
- Ao excluir o registro, o arquivo físico também é removido do disco
  (override de ``delete``).
- Na criação, o ``arquivo`` é recebido como base64 e convertido para
  ``ContentFile`` (helper ``cria_tipos_de_embalagens``).

.. autoclass:: ImagemDoTipoDeEmbalagem
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, arquivo, delete, id, nome, objects, tipo_de_embalagem, tipo_de_embalagem_id, uuid

   .. attribute:: id
      :type: int

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemChaveExterna``)

      **Descrição:**
      Identificador externo único da imagem.

   .. attribute:: tipo_de_embalagem
      :type: TipoDeEmbalagemDeLayout

      **Descrição:**
      Tipo de embalagem ao qual a imagem pertence (``on_delete=CASCADE``,
      ``related_name="imagens"``).

   .. attribute:: arquivo
      :type: django.db.models.fields.files.FieldFile

      **Descrição:**
      Arquivo enviado (``upload_to="layouts_de_embalagens"``), aceitando
      PDF/PNG/JPG/JPEG até 10 MB.

   .. attribute:: nome
      :type: str

      **Descrição:**
      Nome de exibição do arquivo.

TipoDeEmbalagemDeLayout
-----------------------

Tipo de embalagem (primária, secundária ou terciária) de um layout, com
status próprio de análise e as imagens enviadas. A combinação
``layout_de_embalagem`` + ``tipo_embalagem`` é única
(``unique_together``).

Regras de negócio:

- Status possíveis: ``APROVADO``, ``REPROVADO`` e ``EM_ANALISE`` (padrão).
- O ``complemento_do_status`` registra a justificativa da análise
  (obrigatório na análise via API).
- Na criação, os tipos primária e secundária exigem ao menos uma imagem
  com ``arquivo`` e ``nome``.

.. autoclass:: TipoDeEmbalagemDeLayout
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, STATUS_APROVADO, STATUS_CHOICES, STATUS_EM_ANALISE, STATUS_REPROVADO, TIPO_EMBALAGEM_CHOICES, TIPO_EMBALAGEM_PRIMARIA, TIPO_EMBALAGEM_SECUNDARIA, TIPO_EMBALAGEM_TERCIARIA, complemento_do_status, get_status_display, get_tipo_embalagem_display, id, imagens, layout_de_embalagem, layout_de_embalagem_id, objects, status, tipo_embalagem, uuid

   .. attribute:: id
      :type: int

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemChaveExterna``)

      **Descrição:**
      Identificador externo único do tipo de embalagem.

   .. attribute:: layout_de_embalagem
      :type: LayoutDeEmbalagem

      **Descrição:**
      Layout ao qual o tipo de embalagem pertence (``on_delete=CASCADE``,
      ``related_name="tipos_de_embalagens"``).

   .. attribute:: tipo_embalagem
      :type: str

      **Descrição:**
      Tipo da embalagem. Valores possíveis: ``PRIMARIA``, ``SECUNDARIA``
      e ``TERCIARIA``.

   .. attribute:: status
      :type: str

      **Descrição:**
      Status de análise do tipo de embalagem. Valores possíveis:
      ``APROVADO``, ``REPROVADO`` e ``EM_ANALISE`` (padrão).

   .. attribute:: complemento_do_status
      :type: str

      **Descrição:**
      Complemento/justificativa do status, preenchido pela CODAE na
      análise.

   .. attribute:: imagens
      :type: django.db.models.QuerySet[ImagemDoTipoDeEmbalagem]

      **Descrição:**
      Relação reversa 1:N com :class:`ImagemDoTipoDeEmbalagem`
      (``related_name="imagens"``). Lista as imagens deste tipo de
      embalagem.

LayoutDeEmbalagem
-----------------

Modelo central do submódulo. Representa o conjunto de imagens das
embalagens de um produto, vinculado a uma ficha técnica
(``OneToOneField``), enviado pelo fornecedor para aprovação da CODAE.

Possui um **workflow de aprovação** (``FluxoLayoutDeEmbalagem``) com os
estados:

- ``LAYOUT_CRIADO`` (Layout Criado) — estado inicial.
- ``ENVIADO_PARA_ANALISE`` (Enviado para Análise) — transição
  ``inicia_fluxo`` (envio pelo fornecedor).
- ``APROVADO`` (Aprovado) — transição ``codae_aprova``, quando todos os
  tipos de embalagem estão ``APROVADO``.
- ``SOLICITADO_CORRECAO`` (Solicitado Correção) — transição
  ``codae_solicita_correcao``.

O fluxo também permite ``fornecedor_realiza_correcao`` (de
``SOLICITADO_CORRECAO`` para ``ENVIADO_PARA_ANALISE``) e
``fornecedor_atualiza`` (de ``APROVADO`` para ``ENVIADO_PARA_ANALISE``).
Cada transição gera um ``LogSolicitacoesUsuario`` do tipo
``LAYOUT_DE_EMBALAGEM``, com a justificativa quando houver.

Regras de negócio:

- A ficha técnica vinculada não pode estar em rascunho ("Não é possível
  vincular com Ficha Técnica em rascunho.").
- O layout é aprovado somente quando todos os tipos de embalagem estão
  ``APROVADO`` (propriedade ``aprovado``).
- A propriedade ``eh_primeira_analise`` indica se a análise atual é a
  primeira (o log mais recente não é ``LAYOUT_CORRECAO_REALIZADA``); na
  primeira análise, a CODAE deve receber a mesma quantidade de tipos de
  embalagem existentes.
- A imagem assinada (``arquivo_imagem_assinada``) é gerada a partir do log
  de aprovação (``LAYOUT_APROVADO``) com rodapé de assinatura digital;
  PDFs recebem o merge diretamente, PNG/JPG são convertidos para PDF antes.

.. autoclass:: LayoutDeEmbalagem
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, alterado_em, aprovado, arquivo_imagem_assinada, codae_aprova, codae_solicita_correcao, criado_em, eh_primeira_analise, ficha_tecnica, ficha_tecnica_id, fornecedor_atualiza, fornecedor_realiza_correcao, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, get_status_display, id, id_externo, inicia_fluxo, log_mais_recente, logs, objects, observacoes, salvar_log_transicao, status, tipos_de_embalagens, uuid, workflow_class

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
      Identificador externo único do layout de embalagem.

   .. attribute:: id_externo
      :type: str

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemIdentificadorExternoAmigavel``)

      **Descrição:**
      Identificador externo amigável composto pelos 5 primeiros caracteres
      maiúsculos do UUID.

   .. attribute:: ficha_tecnica
      :type: ficha_tecnica.FichaTecnicaDoProduto | None

      **Descrição:**
      Ficha técnica do produto vinculada ao layout
      (``OneToOneField`` com ``on_delete=PROTECT``,
      ``related_name="layout_embalagem"``).

   .. attribute:: observacoes
      :type: str

      **Descrição:**
      Observações gerais sobre o layout, registradas pelo fornecedor.

   .. attribute:: status
      :type: str

      **Origem:**
      ``dados_comuns/fluxo_status.py`` (``FluxoLayoutDeEmbalagem``)

      **Descrição:**
      Status atual do workflow. Estados possíveis: ``LAYOUT_CRIADO``,
      ``ENVIADO_PARA_ANALISE``, ``APROVADO`` e ``SOLICITADO_CORRECAO``.

   .. attribute:: criado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``CriadoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na criação do registro.

   .. attribute:: alterado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemAlteradoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na última alteração do registro.

   .. attribute:: tipos_de_embalagens
      :type: django.db.models.QuerySet[TipoDeEmbalagemDeLayout]

      **Descrição:**
      Relação reversa 1:N com :class:`TipoDeEmbalagemDeLayout`
      (``related_name="tipos_de_embalagens"``). Lista os tipos de embalagem
      (primária, secundária e terciária) do layout, cada um com suas
      imagens.

   .. attribute:: logs
      :type: list[LogSolicitacoesUsuario]

      **Origem:**
      ``dados_comuns/behaviors.py`` (``Logs``)

      **Descrição:**
      Lista dos registros de log de transições de status do layout.

   .. attribute:: log_mais_recente
      :type: LogSolicitacoesUsuario | None

      **Origem:**
      ``dados_comuns/behaviors.py`` (``Logs``)

      **Descrição:**
      Último registro de log de transição de status do layout.

   .. attribute:: aprovado
      :type: bool

      **Descrição:**
      Propriedade que indica se todos os tipos de embalagem do layout
      estão ``APROVADO``.

   .. attribute:: eh_primeira_analise
      :type: bool

      **Descrição:**
      Propriedade que indica se a análise atual é a primeira (o log mais
      recente não é ``LAYOUT_CORRECAO_REALIZADA``).

   .. attribute:: salvar_log_transicao
      :type: Callable

      **Descrição:**
      Registra no log uma transição de status do layout, criando um
      ``LogSolicitacoesUsuario`` com o tipo ``LAYOUT_DE_EMBALAGEM`` e a
      justificativa quando houver.

   .. attribute:: arquivo_imagem_assinada
      :type: Callable

      **Descrição:**
      Gera o arquivo da imagem com rodapé de assinatura digital: busca o
      log de aprovação (``LAYOUT_APROVADO``) e aplica o merge na última
      página — diretamente para PDFs e após conversão para PDF no caso de
      PNG/JPG. Lança ``ValidationError`` se não houver log de aprovação.
