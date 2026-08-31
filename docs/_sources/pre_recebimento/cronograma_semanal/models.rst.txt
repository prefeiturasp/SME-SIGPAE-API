models
======

.. automodule:: src.pre_recebimento.cronograma_semanal.models
   :members:
   :show-inheritance:
   :exclude-members:
      CronogramaSemanal,
      ProgramacaoEntregaSemanal,
      DoesNotExist,
      MultipleObjectsReturned

CronogramaSemanal
-----------------

Cronograma semanal FLV derivado de um cronograma mensal Ponto a Ponto
assinado pela CODAE. Cada cronograma semanal possui uma ou mais
:class:`programações de entrega <ProgramacaoEntregaSemanal>` (por semana)
e um workflow próprio (``FluxoCronogramaSemanal``).

O status é gerenciado pelo ``FluxoCronogramaSemanal``:

- ``RASCUNHO`` (Rascunho) — estado inicial.
- ``ENVIADO_AO_FORNECEDOR`` (Enviado ao Fornecedor) — transição
  ``inicia_fluxo`` (assinatura e envio pela DILOG).
- ``FORNECEDOR_CIENTE`` (Fornecedor Ciente) — transição
  ``fornecedor_ciente``.
- A transição ``alterar_cronograma`` volta de ``FORNECEDOR_CIENTE`` para
  ``ENVIADO_AO_FORNECEDOR`` quando a DILOG altera o cronograma após a
  ciência do fornecedor.

Regras de negócio:

- O ``numero`` é gerado automaticamente no formato ``XXX/YYYY`` (ex.:
  ``001/2024``), onde ``XXX`` é o sequencial do ano e ``YYYY`` o ano
  (``gera_proximo_numero_cronograma_semanal``).
- O ``cronograma_mensal`` é obrigatório, do tipo Ponto a Ponto e com
  status ``ASSINADO_CODAE`` (validado no serializer de criação).
- O ``status`` inicia como ``RASCUNHO``.

.. autoclass:: CronogramaSemanal
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, alterado_em, alterar_cronograma, codae_aprova, criado_em, cronograma_mensal, cronograma_mensal_id, fornecedor_ciente, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, get_status_display, id, id_externo, inicia_fluxo, log_mais_recente, logs, numero, objects, observacoes, programacoes, salvar_log_transicao, status, uuid, workflow_class

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
      Identificador externo único do cronograma semanal.

   .. attribute:: id_externo
      :type: str

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemIdentificadorExternoAmigavel``)

      **Descrição:**
      Identificador externo amigável composto pelos 5 primeiros caracteres
      maiúsculos do UUID.

   .. attribute:: numero
      :type: str

      **Descrição:**
      Número único do cronograma semanal, gerado automaticamente no formato
      ``XXX/YYYY`` (sequencial do ano + ano). Preenchido na criação.

   .. attribute:: cronograma_mensal
      :type: cronograma_entrega.Cronograma

      **Descrição:**
      Cronograma mensal Ponto a Ponto do qual o semanal deriva
      (``on_delete=PROTECT``, ``related_name="cronogramas_semanais"``).
      Deve estar com status ``ASSINADO_CODAE``.

   .. attribute:: observacoes
      :type: str

      **Descrição:**
      Observações gerais sobre o cronograma semanal.

   .. attribute:: status
      :type: str

      **Origem:**
      ``dados_comuns/fluxo_status.py`` (``FluxoCronogramaSemanal``)

      **Descrição:**
      Status atual do workflow. Estados possíveis: ``RASCUNHO``,
      ``ENVIADO_AO_FORNECEDOR`` e ``FORNECEDOR_CIENTE``.

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

   .. attribute:: programacoes
      :type: django.db.models.QuerySet[ProgramacaoEntregaSemanal]

      **Descrição:**
      Relação reversa 1:N com :class:`ProgramacaoEntregaSemanal`
      (``related_name="programacoes"``). Lista as programações de entrega
      semanais do cronograma.

   .. attribute:: logs
      :type: list[LogSolicitacoesUsuario]

      **Origem:**
      ``dados_comuns/behaviors.py`` (``Logs``)

      **Descrição:**
      Lista dos registros de log de transições de status do cronograma
      semanal.

   .. attribute:: log_mais_recente
      :type: LogSolicitacoesUsuario | None

      **Origem:**
      ``dados_comuns/behaviors.py`` (``Logs``)

      **Descrição:**
      Último registro de log de transição de status do cronograma semanal.

ProgramacaoEntregaSemanal
-------------------------

Programação de entrega semanal de um cronograma semanal FLV. Cada
cronograma semanal pode ter múltiplas programações, cada uma com o mês
programado (``MM/YYYY``) e o intervalo de datas (``data_inicio`` e
``data_fim``) em que a entrega ocorre.

Regras de negócio:

- ``mes_programado`` segue o formato ``MM/YYYY``.
- ``data_fim`` deve ser posterior ou igual a ``data_inicio`` (validado no
  ``ProgramacaoEntregaSemanalCreateSerializer``).
- Ordenação padrão por ``mes_programado`` e ``data_inicio``.

.. autoclass:: ProgramacaoEntregaSemanal
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, alterado_em, criado_em, cronograma_semanal, cronograma_semanal_id, data_fim, data_inicio, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, id, mes_programado, objects, quantidade, uuid

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
      Identificador externo único da programação.

   .. attribute:: cronograma_semanal
      :type: CronogramaSemanal

      **Descrição:**
      Cronograma semanal ao qual a programação pertence
      (``on_delete=CASCADE``, ``related_name="programacoes"``).

   .. attribute:: mes_programado
      :type: str

      **Descrição:**
      Mês programado da entrega no formato ``MM/YYYY``.

   .. attribute:: data_inicio
      :type: datetime.date

      **Descrição:**
      Data de início da janela de entrega da semana.

   .. attribute:: data_fim
      :type: datetime.date

      **Descrição:**
      Data de fim da janela de entrega da semana.

   .. attribute:: quantidade
      :type: float

      **Descrição:**
      Quantidade a ser entregue na semana, na unidade de medida do
      cronograma mensal.

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
