models
======

.. automodule:: src.pre_recebimento.cronograma_entrega.models
   :members:
   :show-inheritance:
   :exclude-members:
      Cronograma,
      EtapasDoCronograma,
      ProgramacaoDoRecebimentoDoCronograma,
      SolicitacaoAlteracaoCronograma,
      SolicitacaoAlteracaoCronogramaQuerySet,
      InterrupcaoProgramadaEntrega,
      DoesNotExist,
      MultipleObjectsReturned

Cronograma
----------

Cronograma é o modelo central do módulo de pré-recebimento. Representa o
planejamento de entregas de um produto alimentício ao longo de um período,
vinculado a um contrato e empresa fornecedora. Cada cronograma possui um
fluxo de aprovação que envolve fornecedor, DILOG Abastecimento e CODAE.

Um cronograma pode ser de dois tipos:

- **Armazenável**: Produtos comuns estocados em armazém. Possui etapas com datas específicas (DD/MM/YYYY), programações de recebimento e embalagem secundária.
- **FLV Ponto a Ponto**: Hortifrutigranjeiros entregues diretamente pelo fornecedor às escolas. Possui apenas etapas mensais (MM/YYYY), sem armazém, embalagem secundária ou programações de recebimento.

.. autoclass:: Cronograma
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, alterado_em, armazem, armazem_id, codae_assina, codae_realiza_alteracao, contrato, contrato_id, criado_em, cronogramas_semanais, custo_unitario_produto, data_autorizacao, dilog_abastecimento_assina, documentos_de_recebimento, empresa, empresa_id, etapas, ficha_tecnica, ficha_tecnica_id, finaliza_solicitacao_alteracao, fornecedor_assina, fornecedor_solicita_alteracao, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, get_status_display, id, id_externo, inicia_fluxo, log_mais_recente, logs, notificacoes_do_cronograma, numero, numero_empenho, objects, observacoes, ponto_a_ponto, programacoes_de_recebimento, qtd_total_empenho, qtd_total_programada, salvar_log_transicao, solicitacoes_de_alteracao, status, tipo_embalagem_secundaria, tipo_embalagem_secundaria_id, unidade_medida, unidade_medida_id, uuid

   .. attribute:: id
      :type: int

      **Origem:**
      ``dados_comuns/behaviors.py`` (``ModeloBase``)

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django para identificar o cronograma.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemChaveExterna``)

      **Descrição:**
      Identificador externo único do cronograma, usado em integrações e endpoints que expõem UUID.

   .. attribute:: numero
      :type: str

      **Descrição:**
      Número único do cronograma, gerado automaticamente no formato ``XXX/YYYYA`` (armazenável)
      ou ``XXX/YYYYP`` (ponto a ponto), onde ``XXX`` é o sequencial e ``YYYY`` o ano.

   .. attribute:: status
      :type: str

      **Origem:**
      ``dados_comuns/fluxo_status.py`` (``FluxoCronograma``)

      **Descrição:**
      Status atual do workflow do cronograma. Os estados possíveis são:
      ``RASCUNHO``, ``ASSINADO_E_ENVIADO_AO_FORNECEDOR``, ``ASSINADO_FORNECEDOR``,
      ``ASSINADO_DILOG_ABASTECIMENTO``, ``ASSINADO_CODAE``, ``SOLICITADO_ALTERACAO``,
      ``ALTERACAO_CODAE``.

   .. attribute:: criado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``CriadoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na criação do cronograma.

   .. attribute:: alterado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemAlteradoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na última alteração do cronograma.

   .. attribute:: contrato
      :type: terceirizada.Contrato | None

      **Descrição:**
      Contrato vinculado ao cronograma. Define o número do contrato, pregão/chamada pública,
      ata e demais informações contratuais.

   .. attribute:: empresa
      :type: terceirizada.Terceirizada | None

      **Descrição:**
      Empresa fornecedora responsável pela entrega dos produtos.

   .. attribute:: qtd_total_programada
      :type: float | None

      **Descrição:**
      Quantidade total programada para entrega, na unidade de medida definida
      em ``unidade_medida``.

   .. attribute:: unidade_medida
      :type: UnidadeMedida | None

      **Descrição:**
      Unidade de medida da quantidade programada (ex.: kg, ton, unidades).

   .. attribute:: armazem
      :type: terceirizada.Terceirizada | None

      **Descrição:**
      Distribuidor/armazém responsável pelo armazenamento dos produtos.

   .. attribute:: ficha_tecnica
      :type: ficha_tecnica.FichaTecnicaDoProduto | None

      **Descrição:**
      Ficha técnica do produto alimentício, contendo especificações, embalagens,
      marca, categoria e programa (ex.: LEVE_LEITE).

   .. attribute:: tipo_embalagem_secundaria
      :type: qualidade.TipoEmbalagemQld | None

      **Descrição:**
      Tipo de embalagem secundária utilizada no produto, conforme cadastro
      no módulo de qualidade.

   .. attribute:: custo_unitario_produto
      :type: float | None

      **Descrição:**
      Custo unitário do produto em reais (R$).

   .. attribute:: numero_empenho
      :type: str

      **Descrição:**
      Número do empenho associado ao cronograma.

   .. attribute:: qtd_total_empenho
      :type: float | None

      **Descrição:**
      Quantidade total registrada no empenho.

   .. attribute:: observacoes
      :type: str

      **Descrição:**
      Observações gerais sobre o cronograma, registradas durante a criação.

   .. attribute:: etapas
      :type: django.db.models.QuerySet[EtapasDoCronograma]

      **Descrição:**
      Relação reversa 1:N com :class:`EtapasDoCronograma`.

      Lista as etapas programadas de entrega do cronograma, cada uma com
      data, quantidade, empenho e embalagens.

   .. attribute:: programacoes_de_recebimento
      :type: django.db.models.QuerySet[ProgramacaoDoRecebimentoDoCronograma]

      **Descrição:**
      Relação reversa 1:N com :class:`ProgramacaoDoRecebimentoDoCronograma`.

      Lista as programações de recebimento associadas ao cronograma.

   .. attribute:: solicitacoes_de_alteracao
      :type: django.db.models.QuerySet[SolicitacaoAlteracaoCronograma]

      **Descrição:**
      Relação reversa 1:N com :class:`SolicitacaoAlteracaoCronograma`.

      Lista as solicitações de alteração já realizadas para este cronograma.

   .. attribute:: logs
      :type: list[LogSolicitacoesUsuario]

      **Origem:**
      ``dados_comuns/behaviors.py`` (``Logs``)

      **Descrição:**
      Lista dos registros de log de transições de status do cronograma,
      ordenados por ``criado_em``.

   .. attribute:: log_mais_recente
      :type: LogSolicitacoesUsuario | None

      **Origem:**
      ``dados_comuns/behaviors.py`` (``Logs``)

      **Descrição:**
      Último registro de log de transição de status do cronograma.

   .. attribute:: id_externo
      :type: str

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemIdentificadorExternoAmigavel``)

      **Descrição:**
      Identificador externo amigável composto pelos 5 primeiros caracteres
      maiúsculos do UUID.

   .. attribute:: ponto_a_ponto
      :type: bool

      **Descrição:**
      Propriedade que indica se o cronograma é do tipo Ponto a Ponto (FLV).
      Retorna ``True`` quando a ficha técnica tem categoria ``FLV`` e
      tipo de entrega ``PONTO_A_PONTO``.

   .. attribute:: salvar_log_transicao
      :type: Callable

      **Descrição:**
      Registra no log uma transição de status do cronograma, criando um
      ``LogSolicitacoesUsuario`` com o tipo ``CRONOGRAMA``.

EtapasDoCronograma
------------------

Cada cronograma é dividido em uma ou mais etapas de entrega. Uma etapa
representa uma remessa programada, com data, quantidade, empenho e total de
embalagens. As etapas são a unidade que efetivamente aparece no calendário
de entregas e são validadas contra as :class:`interrupções <InterrupcaoProgramadaEntrega>`.

.. autoclass:: EtapasDoCronograma
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, alterado_em, criado_em, cronograma, cronograma_id, data_programada, etapa, etapas_to_json, ficha_recebimento, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, id, objects, parte, quantidade, qtd_total_empenho, numero_empenho, total_embalagens, uuid

   .. attribute:: id
      :type: int

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django para identificar a etapa.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemChaveExterna``)

      **Descrição:**
      Identificador externo único da etapa, usado em integrações.

   .. attribute:: cronograma
      :type: Cronograma | None

      **Descrição:**
      Cronograma ao qual a etapa pertence.

   .. attribute:: numero_empenho
      :type: str

      **Descrição:**
      Número do empenho específico para esta etapa.

   .. attribute:: qtd_total_empenho
      :type: float | None

      **Descrição:**
      Quantidade total do empenho alocada para esta etapa.

   .. attribute:: etapa
      :type: int | None

      **Descrição:**
      Número sequencial da etapa (1 a 100), utilizado para ordenação.

   .. attribute:: parte
      :type: int | None

      **Descrição:**
      Subdivisão da etapa (parte), quando a etapa é desmembrada em entregas
      menores.

   .. attribute:: data_programada
      :type: date | None

      **Descrição:**
      Data programada para entrega da etapa.

   .. attribute:: quantidade
      :type: float | None

      **Descrição:**
      Quantidade a ser entregue nesta etapa, na unidade de medida do cronograma.

   .. attribute:: total_embalagens
      :type: float | None

      **Descrição:**
      Total de embalagens previstas para esta etapa.

   .. attribute:: criado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``CriadoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na criação do registro.

   .. attribute:: alterado_em
      :type: datetime.datetime

      **Descrição:**
      Timestamp preenchido automaticamente na última alteração do registro.

ProgramacaoDoRecebimentoDoCronograma
------------------------------------

Exclusiva para cronogramas do tipo armazenável. Define as datas em que o
recebimento físico dos produtos deve ocorrer e o tipo de carga (paletizada ou
estivada/batida). Serve como guia para a logística de recebimento nos armazéns.

.. autoclass:: ProgramacaoDoRecebimentoDoCronograma
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, alterado_em, cronograma, cronograma_id, criado_em, data_programada, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, id, objects, tipo_carga, uuid

   .. attribute:: id
      :type: int

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django para identificar a programação.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemChaveExterna``)

      **Descrição:**
      Identificador externo único da programação, usado em integrações.

   .. attribute:: cronograma
      :type: Cronograma | None

      **Descrição:**
      Cronograma ao qual a programação de recebimento está vinculada.

   .. attribute:: data_programada
      :type: str

      **Descrição:**
      Data programada para recebimento. Campo texto para aceitar tanto
      datas completas quanto formato MM/YYYY (usado em cronogramas ponto a ponto).

   .. attribute:: tipo_carga
      :type: str

      **Descrição:**
      Tipo de carga para recebimento. Valores possíveis:
      ``PALETIZADA`` (Paletizada) ou ``ESTIVADA_BATIDA`` (Estivada / Batida).

SolicitacaoAlteracaoCronograma
-------------------------------

Quando um cronograma já está assinado e em vigor, fornecedores ou a CODAE
podem solicitar alterações nas etapas e programações de recebimento. Esta
solicitação passa por um fluxo de aprovação próprio: a DILOG Abastecimento
revisa, o cronograma toma ciência, a DILOG Abastecimento aprova ou reprova,
e por fim a DILOG aprova ou reprova. Se aprovada, as etapas e programações
novas substituem as antigas no :class:`cronograma <Cronograma>` original.

.. autoclass:: SolicitacaoAlteracaoCronograma
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, alterado_em, criado_em, cronograma, cronograma_id, cronograma_confirma_ciencia, etapas_antigas, etapas_novas, gerar_numero_solicitacao, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, get_status_display, id, id_externo, justificativa, log_mais_recente, logs, numero_solicitacao, objects, programacoes_novas, qtd_total_programada, salvar_log_transicao, status, usuario_solicitante, usuario_solicitante_id, uuid

   .. attribute:: id
      :type: int

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django para identificar a solicitação.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemChaveExterna``)

      **Descrição:**
      Identificador externo único da solicitação, usado em integrações e endpoints.

   .. attribute:: objects
      :type: SolicitacaoAlteracaoCronogramaQuerySet

      **Descrição:**
      Manager personalizado que fornece métodos de filtro por status
      (``filtrar_por_status``, ``em_analise``).

   .. attribute:: numero_solicitacao
      :type: str

      **Descrição:**
      Número único da solicitação, gerado automaticamente no formato
      ``XXXXXXXX-ALT``, onde ``XXXXXXXX`` é o PK preenchido com zeros.

   .. attribute:: status
      :type: str

      **Origem:**
      ``dados_comuns/fluxo_status.py`` (``FluxoAlteracaoCronograma``)

      **Descrição:**
      Status atual do workflow de alteração. Os estados possíveis são:
      ``SOLICITACAO_CRIADA``, ``EM_ANALISE``, ``CRONOGRAMA_CIENTE``,
      ``APROVADO_DILOG_ABASTECIMENTO``, ``REPROVADO_DILOG_ABASTECIMENTO``,
      ``APROVADO_DILOG``, ``REPROVADO_DILOG``, ``ALTERACAO_ENVIADA_FORNECEDOR``,
      ``FORNECEDOR_CIENTE``.

   .. attribute:: cronograma
      :type: Cronograma

      **Descrição:**
      Cronograma original ao qual a solicitação de alteração se refere.

   .. attribute:: qtd_total_programada
      :type: float | None

      **Descrição:**
      Nova quantidade total programada proposta na alteração.

   .. attribute:: etapas_antigas
      :type: django.db.models.QuerySet[EtapasDoCronograma]

      **Descrição:**
      Relação M:N com :class:`EtapasDoCronograma`.

      Etapas originais do cronograma no momento da solicitação, mantidas
      como referência para comparação com as etapas novas.

   .. attribute:: etapas_novas
      :type: django.db.models.QuerySet[EtapasDoCronograma]

      **Descrição:**
      Relação M:N com :class:`EtapasDoCronograma`.

      Novas etapas propostas na solicitação de alteração. Em caso de
      aprovação pela DILOG, substituem as ``etapas_antigas`` no cronograma.

   .. attribute:: programacoes_novas
      :type: django.db.models.QuerySet[ProgramacaoDoRecebimentoDoCronograma]

      **Descrição:**
      Relação M:N com :class:`ProgramacaoDoRecebimentoDoCronograma`.

      Novas programações de recebimento propostas para substituir as
      programações atuais do cronograma.

   .. attribute:: justificativa
      :type: str

      **Descrição:**
      Justificativa fornecida pelo solicitante (fornecedor ou CODAE)
      para a alteração.

   .. attribute:: usuario_solicitante
      :type: perfil.Usuario

      **Descrição:**
      Usuário que criou a solicitação de alteração.

   .. attribute:: criado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``CriadoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na criação da solicitação.

   .. attribute:: logs
      :type: list[LogSolicitacoesUsuario]

      **Origem:**
      ``dados_comuns/behaviors.py`` (``Logs``)

      **Descrição:**
      Lista dos registros de log de transições de status da solicitação.

SolicitacaoAlteracaoCronogramaQuerySet
--------------------------------------

QuerySet personalizado que ordena as solicitações pelo log mais recente e
oferece filtros por fornecedor, número do cronograma e nome do produto.

.. autoclass:: SolicitacaoAlteracaoCronogramaQuerySet
   :members:
   :show-inheritance:

InterrupcaoProgramadaEntrega
----------------------------

Gerencia os dias em que não pode haver entrega. Feriados, emendas, reuniões
e inventários são cadastrados aqui e consultados pelo calendário de cronogramas
para impedir que :class:`etapas <EtapasDoCronograma>` sejam agendadas nessas
datas. A interrupção é separada por tipo de calendário: armazenável ou ponto a
ponto.

.. autoclass:: InterrupcaoProgramadaEntrega
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, alterado_em, criado_em, data, descricao_motivo, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, id, motivo, objects, tipo_calendario, uuid

   .. attribute:: id
      :type: int

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemChaveExterna``)

      **Descrição:**
      Identificador externo único da interrupção, usado em integrações.

   .. attribute:: data
      :type: datetime.date

      **Descrição:**
      Data em que a entrega está suspensa. Utilizada pelo calendário de
      cronogramas para impedir o cadastro de etapas nesta data.

   .. attribute:: motivo
      :type: str

      **Descrição:**
      Motivo da interrupção. Valores possíveis:
      ``EMENDA``, ``REUNIAO``, ``INVENTARIO``, ``FERIADO``, ``OUTROS``.

   .. attribute:: descricao_motivo
      :type: str

      **Descrição:**
      Descrição detalhada do motivo. Obrigatório quando ``motivo = OUTROS``.

   .. attribute:: tipo_calendario
      :type: str

      **Descrição:**
      Tipo de calendário ao qual a interrupção se aplica.
      ``ARMAZENAVEL`` (Armazenável): bloqueia o calendário de cronogramas
      armazenáveis. ``PONTO_A_PONTO`` (Ponto a Ponto): bloqueia o
      calendário de cronogramas FLV.
