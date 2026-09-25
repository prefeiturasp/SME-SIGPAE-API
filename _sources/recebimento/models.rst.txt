models
======

.. automodule:: src.recebimento.models
   :members:
   :show-inheritance:
   :exclude-members:
      QuestaoConferencia,
      QuestoesPorProduto,
      ReposicaoCronogramaFichaRecebimento,
      FichaDeRecebimento,
      VeiculoFichaDeRecebimento,
      ArquivoFichaRecebimento,
      QuestaoFichaRecebimento,
      DocumentoFichaDeRecebimento,
      OcorrenciaFichaRecebimento,
      DoesNotExist,
      MultipleObjectsReturned

QuestaoConferencia
------------------

Questão de conferência utilizada nas fichas de recebimento. Compõe o
catálogo de perguntas de inspeção (embalagem primária e/ou secundária)
respondidas durante o recebimento.

Regras de negócio:

- ``tipo_questao`` é multi-seleção: ``PRIMARIA`` (Primária) e/ou
  ``SECUNDARIA`` (Secundária).
- ``pergunta_obrigatoria``: quando ``True``, exige ``posicao`` preenchida
  (validado em ``clean`` — "Posição é obrigatória se a pergunta for
  obrigatória.").
- No admin, a posição deve ser única por tipo de questão
  (``QuestaoForm``).
- ``status``: ``ATIVO`` (padrão) ou ``INATIVO``.

.. autoclass:: QuestaoConferencia
   :members:
   :show-inheritance:
   :exclude-members: ATIVO, DoesNotExist, INATIVO, MultipleObjectsReturned, STATUS_CHOICES, TIPO_QUESTAO_CHOICES, TIPO_QUESTAO_NOMES, TIPO_QUESTAO_PRIMARIA, TIPO_QUESTAO_SECUNDARIA, alterado_em, clean, criado_em, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, get_status_display, get_tipo_questao_display, id, objects, pergunta_obrigatoria, posicao, questao, status, tipo_questao, uuid

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
      Identificador externo único da questão.

   .. attribute:: questao
      :type: str

      **Descrição:**
      Texto da questão de conferência.

   .. attribute:: tipo_questao
      :type: str

      **Descrição:**
      Tipo(s) de embalagem a que a questão se aplica. Valores possíveis:
      ``PRIMARIA`` e ``SECUNDARIA`` (multi-seleção).

   .. attribute:: pergunta_obrigatoria
      :type: bool

      **Descrição:**
      Indica se a questão é obrigatória na ficha de recebimento. Quando
      ``True``, exige ``posicao``.

   .. attribute:: posicao
      :type: int | None

      **Descrição:**
      Posição da questão, usada para ordenação. Obrigatória quando
      ``pergunta_obrigatoria`` é ``True``.

   .. attribute:: status
      :type: str

      **Descrição:**
      Status da questão. Valores possíveis: ``ATIVO`` (padrão) e
      ``INATIVO``.

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

QuestoesPorProduto
------------------

Vínculo entre a ficha técnica do produto e as questões de conferência.
Define, para cada ficha técnica, quais questões de embalagem primária e
secundária devem ser respondidas na ficha de recebimento do produto.

Regras de negócio:

- ``ficha_tecnica`` é ``OneToOneField`` (``related_name="questoes_conferencia"``):
  cada ficha técnica possui um único conjunto de questões.
- As questões são relacionadas via M:N (``questoes_primarias`` e
  ``questoes_secundarias``).

.. autoclass:: QuestoesPorProduto
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, alterado_em, criado_em, ficha_tecnica, ficha_tecnica_id, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, id, objects, questoes_primarias, questoes_secundarias, uuid

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
      Identificador externo único do vínculo.

   .. attribute:: ficha_tecnica
      :type: ficha_tecnica.FichaTecnicaDoProduto

      **Descrição:**
      Ficha técnica do produto (``OneToOneField`` com
      ``on_delete=CASCADE``, ``related_name="questoes_conferencia"``).

   .. attribute:: questoes_primarias
      :type: django.db.models.Manager

      **Descrição:**
      Relação M:N com :class:`QuestaoConferencia` (questões de embalagem
      primária).

   .. attribute:: questoes_secundarias
      :type: django.db.models.Manager

      **Descrição:**
      Relação M:N com :class:`QuestaoConferencia` (questões de embalagem
      secundária).

   .. attribute:: criado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``CriadoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na criação do registro.

ReposicaoCronogramaFichaRecebimento
-----------------------------------

Tipo de reposição de cronograma escolhido na ficha de recebimento quando
há produtos faltantes ou recusados. Valores possíveis:

- ``Repor`` (Repor os produtos faltantes/recusados).
- ``Credito`` (Fazer uma carta de crédito do valor pago).
- ``Outros`` (Outros).

.. autoclass:: ReposicaoCronogramaFichaRecebimento
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, TIPO_CHOICES, alterado_em, criado_em, descricao, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, get_tipo_display, id, objects, tipo, uuid

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
      Identificador externo único do tipo de reposição.

   .. attribute:: tipo
      :type: str

      **Descrição:**
      Tipo da reposição. Valores possíveis: ``Repor``, ``Credito`` e
      ``Outros``.

   .. attribute:: descricao
      :type: str

      **Descrição:**
      Descrição da reposição.

   .. attribute:: criado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``CriadoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na criação do registro.

FichaDeRecebimento
------------------

Modelo central do módulo. Representa o registro do recebimento físico dos
produtos contra uma etapa do cronograma, com a inspeção de qualidade
conduzida pela DILOG Qualidade: conformidade dos lotes do fabricante,
datas de fabricação e validade, número do lote de armazenagem, paletes,
pesos das embalagens primárias, sistema de vedação da embalagem
secundária, respostas às questões de conferência, veículos e notas
fiscais, ocorrências, anexos e reposição de cronograma.

Possui um **workflow de assinatura** (``FichaDeRecebimentoWorkflow``):

- ``RASCUNHO`` (Rascunho) — estado inicial.
- ``ASSINADA`` (Assinado CODAE) — transição ``inicia_fluxo`` (assinatura
  pela CODAE); o log ``FICHA_RECEBIMENTO_ASSINADA`` é registrado
  automaticamente.
- A transição ``volta_para_rascunho`` retorna de ``ASSINADA`` para
  ``RASCUNHO`` quando a ficha é editada via rascunho.

Regras de negócio:

- A ``etapa`` é obrigatória (``on_delete=PROTECT``) e define o cronograma
  e o produto da ficha.
- Os ``documentos_recebimento`` vinculados devem estar com status
  ``APROVADO`` (validado no serializer de criação).
- A quantidade recebida por documento é registrada no modelo intermediário
  :class:`DocumentoFichaDeRecebimento`.
- Os campos de conformidade (``*_de_acordo``) quando ``False`` exigem a
  respectiva ``*_divergencia`` (validado no serializer de criação).
- Apenas uma ocorrência do tipo ``RECUSA`` é permitida por ficha.
- O saldo do laudo considera apenas fichas ``ASSINADA``
  (``calcular_saldo_laudo``).
- A empresa precisa de ao menos uma ficha ``ASSINADA`` para constar em um
  termo de recebimento definitivo.

.. autoclass:: FichaDeRecebimento
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, alterado_em, arquivos, criado_em, data_fabricacao_de_acordo, data_fabricacao_divergencia, data_validade_de_acordo, data_validade_divergencia, data_entrega, documentos_ficha, documentos_recebimento, etapa, etapa_id, fichas_recebimentos, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, get_status_display, houve_ocorrencia, id, id_externo, inicia_fluxo, log_mais_recente, logs, lote_fabricante_de_acordo, lote_fabricante_divergencia, numero_lote_armazenagem, numero_paletes, objects, observacao, observacoes_conferencia, ocorrencias, peso_embalagem_primaria_1, peso_embalagem_primaria_2, peso_embalagem_primaria_3, peso_embalagem_primaria_4, questoes_conferencia, reposicao_cronograma, reposicao_cronograma_id, salvar_log_transicao, sistema_vedacao_embalagem_secundaria, status, uuid, veiculos, volta_para_rascunho, workflow_class

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
      Identificador externo único da ficha de recebimento.

   .. attribute:: id_externo
      :type: str

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemIdentificadorExternoAmigavel``)

      **Descrição:**
      Identificador externo amigável composto pelos 5 primeiros caracteres
      maiúsculos do UUID.

   .. attribute:: etapa
      :type: cronograma_entrega.EtapasDoCronograma

      **Descrição:**
      Etapa do cronograma à qual a ficha se refere (``on_delete=PROTECT``,
      ``related_name="ficha_recebimento"``). Define o cronograma, o produto
      e a data programada da entrega.

   .. attribute:: data_entrega
      :type: datetime.date | None

      **Descrição:**
      Data efetiva da entrega registrada na ficha.

   .. attribute:: documentos_recebimento
      :type: django.db.models.Manager

      **Descrição:**
      Relação M:N com :class:`DocumentoDeRecebimento
      <src.pre_recebimento.documento_recebimento.models.DocumentoDeRecebimento>`
      através de :class:`DocumentoFichaDeRecebimento`
      (``related_name="fichas_recebimentos"``). Documentos vinculados à
      ficha, com a quantidade recebida por documento.

   .. attribute:: lote_fabricante_de_acordo
      :type: bool | None

      **Descrição:**
      Indica se o(s) lote(s) do fabricante observado(s) estão de acordo.
      Quando ``False``, exige ``lote_fabricante_divergencia``.

   .. attribute:: lote_fabricante_divergencia
      :type: str

      **Descrição:**
      Descrição da divergência no(s) lote(s) do fabricante. Obrigatória
      quando ``lote_fabricante_de_acordo`` é ``False``.

   .. attribute:: data_fabricacao_de_acordo
      :type: bool | None

      **Descrição:**
      Indica se a(s) data(s) de fabricação observada(s) estão de acordo.
      Quando ``False``, exige ``data_fabricacao_divergencia``.

   .. attribute:: data_fabricacao_divergencia
      :type: str

      **Descrição:**
      Descrição da divergência na(s) data(s) de fabricação. Obrigatória
      quando ``data_fabricacao_de_acordo`` é ``False``.

   .. attribute:: data_validade_de_acordo
      :type: bool | None

      **Descrição:**
      Indica se a(s) data(s) de validade observada(s) estão de acordo.
      Quando ``False``, exige ``data_validade_divergencia``.

   .. attribute:: data_validade_divergencia
      :type: str

      **Descrição:**
      Descrição da divergência na(s) data(s) de validade. Obrigatória
      quando ``data_validade_de_acordo`` é ``False``.

   .. attribute:: numero_lote_armazenagem
      :type: str

      **Descrição:**
      Número do lote de armazenagem.

   .. attribute:: numero_paletes
      :type: int | None

      **Descrição:**
      Número de paletes recebidos.

   .. attribute:: peso_embalagem_primaria_1
      :type: float | None

      **Descrição:**
      Peso da embalagem primária (1). Os campos ``peso_embalagem_primaria_2``
      a ``peso_embalagem_primaria_4`` seguem o mesmo padrão.

   .. attribute:: sistema_vedacao_embalagem_secundaria
      :type: str

      **Descrição:**
      Descrição do sistema de vedação da embalagem secundária.

   .. attribute:: questoes_conferencia
      :type: django.db.models.Manager

      **Descrição:**
      Relação M:N com :class:`QuestaoConferencia` através de
      :class:`QuestaoFichaRecebimento` (``related_name="fichas_vinculadas"``).
      Respostas às questões de conferência da ficha.

   .. attribute:: houve_ocorrencia
      :type: bool | None

      **Descrição:**
      Indica se houve ocorrência no recebimento.

   .. attribute:: observacoes_conferencia
      :type: str

      **Descrição:**
      Observações da conferência.

   .. attribute:: observacao
      :type: str

      **Descrição:**
      Observação geral da ficha.

   .. attribute:: reposicao_cronograma
      :type: ReposicaoCronogramaFichaRecebimento | None

      **Descrição:**
      Tipo de reposição de cronograma escolhido (``on_delete=PROTECT``,
      ``related_name="reposicao_cronograma"``).

   .. attribute:: veiculos
      :type: django.db.models.QuerySet[VeiculoFichaDeRecebimento]

      **Descrição:**
      Relação reversa 1:N com :class:`VeiculoFichaDeRecebimento`
      (``related_name="veiculos"``). Veículos e notas fiscais da ficha.

   .. attribute:: arquivos
      :type: django.db.models.QuerySet[ArquivoFichaRecebimento]

      **Descrição:**
      Relação reversa 1:N com :class:`ArquivoFichaRecebimento`
      (``related_name="arquivos"``). Anexos da ficha.

   .. attribute:: ocorrencias
      :type: django.db.models.QuerySet[OcorrenciaFichaRecebimento]

      **Descrição:**
      Relação reversa 1:N com :class:`OcorrenciaFichaRecebimento`
      (``related_name="ocorrencias"``). Ocorrências registradas na ficha.

   .. attribute:: documentos_ficha
      :type: django.db.models.QuerySet[DocumentoFichaDeRecebimento]

      **Descrição:**
      Relação reversa 1:N com :class:`DocumentoFichaDeRecebimento`
      (``related_name="documentos_ficha"``). Vínculos com os documentos de
      recebimento e as quantidades recebidas.

   .. attribute:: status
      :type: str

      **Origem:**
      ``dados_comuns/fluxo_status.py`` (``FichaDeRecebimentoWorkflow``)

      **Descrição:**
      Status atual do workflow. Estados possíveis: ``RASCUNHO`` e
      ``ASSINADA``.

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

   .. attribute:: logs
      :type: list[LogSolicitacoesUsuario]

      **Origem:**
      ``dados_comuns/behaviors.py`` (``Logs``)

      **Descrição:**
      Lista dos registros de log de transições de status da ficha.

   .. attribute:: log_mais_recente
      :type: LogSolicitacoesUsuario | None

      **Origem:**
      ``dados_comuns/behaviors.py`` (``Logs``)

      **Descrição:**
      Último registro de log de transição de status da ficha.

   .. attribute:: salvar_log_transicao
      :type: Callable

      **Descrição:**
      Registra no log uma transição de status da ficha, criando um
      ``LogSolicitacoesUsuario`` com o tipo ``FICHA_RECEBIMENTO``.

VeiculoFichaDeRecebimento
-------------------------

Veículo e nota fiscal de uma ficha de recebimento. Registra, por veículo
entregue, as temperaturas de recebimento e do produto, placa, lacre,
número SIF/SISBI/SISP, número da nota fiscal, quantidades e embalagens da
nota versus recebidas, estado higiênico-sanitário e uso de termógrafo.

.. autoclass:: VeiculoFichaDeRecebimento
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, embalagens_nota_fiscal, embalagens_recebidas, estado_higienico_adequado, ficha_recebimento, ficha_recebimento_id, id, lacre, numero, numero_nota_fiscal, numero_sif_sisbi_sisp, objects, placa, quantidade_nota_fiscal, quantidade_recebida, temperatura_produto, temperatura_recebimento, termografo

   .. attribute:: id
      :type: int

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django.

   .. attribute:: ficha_recebimento
      :type: FichaDeRecebimento

      **Descrição:**
      Ficha de recebimento à qual o veículo pertence (``on_delete=CASCADE``,
      ``related_name="veiculos"``).

   .. attribute:: numero
      :type: str

      **Descrição:**
      Número do veículo.

   .. attribute:: temperatura_recebimento
      :type: str

      **Descrição:**
      Temperatura da área de recebimento (°C).

   .. attribute:: temperatura_produto
      :type: str

      **Descrição:**
      Temperatura do produto (°C).

   .. attribute:: placa
      :type: str

      **Descrição:**
      Placa do veículo.

   .. attribute:: lacre
      :type: str

      **Descrição:**
      Número do lacre.

   .. attribute:: numero_sif_sisbi_sisp
      :type: str

      **Descrição:**
      Número SIF, SISBI ou SISP.

   .. attribute:: numero_nota_fiscal
      :type: str

      **Descrição:**
      Número da nota fiscal.

   .. attribute:: quantidade_nota_fiscal
      :type: decimal.Decimal | None

      **Descrição:**
      Quantidade da nota fiscal.

   .. attribute:: embalagens_nota_fiscal
      :type: int | None

      **Descrição:**
      Quantidade de embalagens da nota fiscal.

   .. attribute:: quantidade_recebida
      :type: decimal.Decimal | None

      **Descrição:**
      Quantidade efetivamente recebida.

   .. attribute:: embalagens_recebidas
      :type: int | None

      **Descrição:**
      Quantidade de embalagens recebidas.

   .. attribute:: estado_higienico_adequado
      :type: bool | None

      **Descrição:**
      Indica se o estado higiênico-sanitário do veículo está adequado.

   .. attribute:: termografo
      :type: bool | None

      **Descrição:**
      Indica se o veículo possui termógrafo.

ArquivoFichaRecebimento
-----------------------

Arquivo (PDF ou imagem) anexado a uma ficha de recebimento (termo de
recebimento, fotos, etc.).

Regras de negócio:

- Extensões aceitas: ``PDF``, ``PNG``, ``JPG`` e ``JPEG``
  (``FileExtensionValidator``).
- Tamanho máximo de 10 MB (``validate_file_size_10mb``).
- O arquivo é recebido como base64 pela API e convertido para
  ``ContentFile`` no helper de criação.
- A exclusão do registro também remove o arquivo físico do armazenamento
  (``TemArquivosDeletaveis``).

.. autoclass:: ArquivoFichaRecebimento
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, arquivo, ficha_recebimento, ficha_recebimento_id, id, nome, objects, uuid

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

   .. attribute:: ficha_recebimento
      :type: FichaDeRecebimento

      **Descrição:**
      Ficha de recebimento à qual o arquivo pertence (``on_delete=CASCADE``,
      ``related_name="arquivos"``).

   .. attribute:: arquivo
      :type: django.db.models.fields.files.FieldFile

      **Descrição:**
      Arquivo enviado (``upload_to="arquivos_fichas_de_recebimentos"``),
      aceitando PDF/PNG/JPG/JPEG até 10 MB.

   .. attribute:: nome
      :type: str

      **Descrição:**
      Nome de exibição do arquivo.

QuestaoFichaRecebimento
-----------------------

Resposta a uma questão de conferência em uma ficha de recebimento.
Registra a resposta (Sim/Não) e o tipo de embalagem (primária ou
secundária) da questão respondida.

Regras de negócio:

- ``unique_together`` em ``ficha_recebimento`` + ``questao_conferencia`` +
  ``tipo_questao``: a mesma questão não pode ser respondida duas vezes na
  mesma ficha para o mesmo tipo.

.. autoclass:: QuestaoFichaRecebimento
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, TIPO_QUESTAO_CHOICES, TIPO_QUESTAO_NOMES, TIPO_QUESTAO_PRIMARIA, TIPO_QUESTAO_SECUNDARIA, alterado_em, criado_em, ficha_recebimento, ficha_recebimento_id, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, get_tipo_questao_display, id, objects, questao_conferencia, questao_conferencia_id, resposta, tipo_questao, uuid

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
      Identificador externo único da resposta.

   .. attribute:: ficha_recebimento
      :type: FichaDeRecebimento

      **Descrição:**
      Ficha de recebimento da resposta (``on_delete=CASCADE``).

   .. attribute:: questao_conferencia
      :type: QuestaoConferencia

      **Descrição:**
      Questão de conferência respondida (``on_delete=CASCADE``).

   .. attribute:: resposta
      :type: bool | None

      **Descrição:**
      Resposta (Sim/Não) dada à questão.

   .. attribute:: tipo_questao
      :type: str

      **Descrição:**
      Tipo de embalagem da questão respondida. Valores possíveis:
      ``PRIMARIA`` e ``SECUNDARIA``.

   .. attribute:: criado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``CriadoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na criação do registro.

DocumentoFichaDeRecebimento
---------------------------

Modelo intermediário (through) da relação M:N entre fichas e documentos
de recebimento, registrando a ``quantidade_recebida`` de cada documento
na ficha. A combinação ficha + documento é única (``unique_together``).

.. autoclass:: DocumentoFichaDeRecebimento
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, alterado_em, criado_em, documento_recebimento, documento_recebimento_id, ficha_recebimento, ficha_recebimento_id, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, id, objects, quantidade_recebida, uuid

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
      Identificador externo único do vínculo.

   .. attribute:: ficha_recebimento
      :type: FichaDeRecebimento

      **Descrição:**
      Ficha de recebimento do vínculo (``on_delete=CASCADE``,
      ``related_name="documentos_ficha"``).

   .. attribute:: documento_recebimento
      :type: DocumentoDeRecebimento

      **Descrição:**
      Documento de recebimento do vínculo (``on_delete=CASCADE``,
      ``related_name="fichas_documentos"``).

   .. attribute:: quantidade_recebida
      :type: decimal.Decimal | None

      **Descrição:**
      Quantidade recebida do documento na ficha. Considerada no cálculo do
      saldo do laudo apenas quando a ficha está ``ASSINADA``.

   .. attribute:: criado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``CriadoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na criação do registro.

OcorrenciaFichaRecebimento
--------------------------

Ocorrência registrada durante o recebimento: faltas (``FALTA``), recusas
(``RECUSA``) ou outros motivos (``OUTROS_MOTIVOS``), com a relação
(cronograma, nota fiscal, total ou parcial), número da nota, quantidade e
descrição.

Regras de negócio (validadas no serializer de criação, fora do rascunho):

- ``FALTA``: relação obrigatória ``CRONOGRAMA`` ou ``NOTA_FISCAL``.
- ``RECUSA``: relação obrigatória ``TOTAL`` ou ``PARCIAL`` e número da
  nota obrigatório.
- ``OUTROS_MOTIVOS``: ``relacao`` e ``numero_nota`` são zerados.
- ``quantidade`` é obrigatória para os tipos diferentes de
  ``OUTROS_MOTIVOS``.
- Apenas uma ocorrência do tipo ``RECUSA`` é permitida por ficha (validado
  no helper de criação).

.. autoclass:: OcorrenciaFichaRecebimento
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, RELACAO_CHOICES, RELACAO_CRONOGRAMA, RELACAO_NOTA_FISCAL, RELACAO_PARCIAL, RELACAO_TOTAL, TIPO_CHOICES, TIPO_FALTA, TIPO_OUTROS, TIPO_RECUSA, alterado_em, criado_em, descricao, ficha_recebimento, ficha_recebimento_id, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, get_relacao_display, get_tipo_display, id, numero_nota, objects, quantidade, relacao, tipo, uuid

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
      Identificador externo único da ocorrência.

   .. attribute:: ficha_recebimento
      :type: FichaDeRecebimento

      **Descrição:**
      Ficha de recebimento da ocorrência (``on_delete=CASCADE``,
      ``related_name="ocorrencias"``).

   .. attribute:: tipo
      :type: str

      **Descrição:**
      Tipo da ocorrência. Valores possíveis: ``FALTA`` (Falta), ``RECUSA``
      (Recusa) e ``OUTROS_MOTIVOS`` (Outros Motivos).

   .. attribute:: relacao
      :type: str

      **Descrição:**
      Relação da ocorrência. Valores possíveis: ``CRONOGRAMA``,
      ``NOTA_FISCAL``, ``TOTAL`` e ``PARCIAL``.

   .. attribute:: numero_nota
      :type: str

      **Descrição:**
      Número da nota fiscal relacionada à ocorrência.

   .. attribute:: quantidade
      :type: str

      **Descrição:**
      Quantidade envolvida na ocorrência.

   .. attribute:: descricao
      :type: str

      **Descrição:**
      Descrição detalhada da ocorrência.

   .. attribute:: criado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``CriadoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na criação do registro.
