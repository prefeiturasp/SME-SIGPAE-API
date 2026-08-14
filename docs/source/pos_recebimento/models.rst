models
======

.. automodule:: src.pos_recebimento.models
   :members:
   :show-inheritance:
   :exclude-members:
      TermoRecebimentoDefinitivo,
      CronogramaTermoRecebimentoDefinitivo,
      DoesNotExist,
      MultipleObjectsReturned

TermoRecebimentoDefinitivo
--------------------------

O Termo de Recebimento Definitivo é o documento que formaliza o
recebimento definitivo (físico e financeiro) de produtos de uma
empresa/contrato no módulo Pós-Recebimento. Ele registra a entrega final
de um conjunto de cronogramas de entrega, nomeia os fiscais responsáveis
(três usuários com perfil ``DILOG_QUALIDADE``) e carrega o texto do termo
(conteúdo rico, ex.: HTML gerado por um editor de texto).

Regras de negócio da criação:

- A **empresa** deve possuir ao menos uma ficha de recebimento com status
  "Assinado CODAE" (``FichaDeRecebimentoWorkflow.ASSINADA``). Essa regra é
  aplicada tanto na listagem de empresas disponíveis
  (``/terceirizadas/lista-empresas-pos-recebimento/``) quanto na validação
  do payload de criação do termo.
- O **contrato** deve pertencer à empresa selecionada
  (``contrato.terceirizada == empresa``).
- Cada **cronograma** deve pertencer ao contrato e à empresa selecionados
  e não pode ser repetido no mesmo payload.
- Os **fiscais** devem possuir vínculo ativo com o perfil ``DILOG_QUALIDADE``.
- O **texto do termo** é obrigatório e deve conter conteúdo textual após a
  remoção das tags HTML (não basta apenas ``<p></p>``).
- A criação via API **sempre persiste o termo com status ``ENVIADO``**
  (fluxo "Salvar e Enviar"), independentemente do default do modelo
  (``RASCUNHO``). O status ``RASCUNHO`` existe no modelo, mas não é
  utilizado pela API atual.

Cada cronograma do termo carrega o seu próprio **valor de contrato** e
**quantidade total recebida** (valores decimais de até 15 dígitos com 2
casas decimais), armazenados no modelo intermediário
:class:`CronogramaTermoRecebimentoDefinitivo` — ambos devem ser maiores
que zero.

.. autoclass:: TermoRecebimentoDefinitivo
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, ENVIADO, MultipleObjectsReturned, RASCUNHO, STATUS_CHOICES, alterado_em, alterado_por, alterado_por_id, contrato, contrato_id, criado_em, criado_por, criado_por_id, cronogramas, cronogramas_termo, empresa, empresa_id, fiscal_1, fiscal_1_id, fiscal_2, fiscal_2_id, fiscal_3, fiscal_3_id, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, get_status_display, id, objects, status, termos_recebimento_definitivo_alterados, termos_recebimento_definitivo_fiscal_1, termos_recebimento_definitivo_fiscal_2, termos_recebimento_definitivo_fiscal_3, texto_termo, uuid

   .. attribute:: id
      :type: int

      **Origem:**
      ``dados_comuns/behaviors.py`` (``ModeloBase``)

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django para identificar o termo.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemChaveExterna``)

      **Descrição:**
      Identificador externo único do termo, usado em integrações, endpoints
      que expõem UUID e como referência nas mensagens de log.

   .. attribute:: empresa
      :type: terceirizada.Terceirizada

      **Descrição:**
      Empresa fornecedora responsável pelas entregas formalizadas no termo.
      Campo obrigatório com ``on_delete=PROTECT`` (não pode ser removida
      enquanto houver termo vinculado).

      Regra de negócio: a empresa deve possuir ao menos uma ficha de
      recebimento "Assinado CODAE" (``FichaDeRecebimentoWorkflow.ASSINADA``)
      para ser utilizada em um termo.

   .. attribute:: contrato
      :type: terceirizada.Contrato

      **Descrição:**
      Contrato ao qual as entregas pertencem. Campo obrigatório com
      ``on_delete=PROTECT``.

      Regra de negócio: o contrato deve pertencer à empresa selecionada
      (``contrato.terceirizada == empresa``).

   .. attribute:: cronogramas
      :type: django.db.models.QuerySet[Cronograma]

      **Descrição:**
      Relação M:N com :class:`Cronograma
      <src.pre_recebimento.cronograma_entrega.models.Cronograma>` através do
      modelo intermediário :class:`CronogramaTermoRecebimentoDefinitivo`.

      Lista os cronogramas de entrega formalizados no termo. Cada vínculo
      carrega o ``valor_contrato`` e a ``quantidade_total_recebida``
      específicos daquele cronograma (ver ``cronogramas_termo``).

      Regra de negócio: cada cronograma deve pertencer ao contrato e à
      empresa selecionados e não pode ser repetido no mesmo termo
      (``unique_together`` entre ``termo`` e ``cronograma``).

   .. attribute:: cronogramas_termo
      :type: django.db.models.QuerySet[CronogramaTermoRecebimentoDefinitivo]

      **Descrição:**
      Relação reversa 1:N com :class:`CronogramaTermoRecebimentoDefinitivo`
      (``related_name="cronogramas_termo"``).

      Acesso direto às linhas intermediárias do termo, incluindo o valor de
      contrato e a quantidade total recebida de cada cronograma. É a fonte
      utilizada pelo serializador de saída para expor os cronogramas com
      seus valores.

   .. attribute:: fiscal_1
      :type: perfil.Usuario

      **Descrição:**
      Primeiro fiscal responsável pelo recebimento. Campo obrigatório com
      ``on_delete=PROTECT`` (usuário não pode ser removido enquanto houver
      termo vinculado).

      Regra de negócio: o usuário deve possuir vínculo ativo com o perfil
      ``DILOG_QUALIDADE``.

   .. attribute:: fiscal_2
      :type: perfil.Usuario

      **Descrição:**
      Segundo fiscal responsável pelo recebimento. Mesmas regras de
      ``fiscal_1`` (obrigatório, ``on_delete=PROTECT``, perfil
      ``DILOG_QUALIDADE`` com vínculo ativo).

   .. attribute:: fiscal_3
      :type: perfil.Usuario

      **Descrição:**
      Terceiro fiscal responsável pelo recebimento. Mesmas regras de
      ``fiscal_1`` (obrigatório, ``on_delete=PROTECT``, perfil
      ``DILOG_QUALIDADE`` com vínculo ativo).

   .. attribute:: texto_termo
      :type: str

      **Descrição:**
      Texto do termo em conteúdo rico (aceita HTML, ex.: produzido por
      editor de texto). Obrigatório e deve conter conteúdo textual após a
      remoção das tags HTML.

   .. attribute:: status
      :type: str

      **Descrição:**
      Status do termo. Valores possíveis: ``RASCUNHO`` (Rascunho) e
      ``ENVIADO`` (Enviado). O default do modelo é ``RASCUNHO``, porém a
      criação via API **sempre persiste ``ENVIADO``** (fluxo "Salvar e
      Enviar").

   .. attribute:: criado_por
      :type: perfil.Usuario | None

      **Origem:**
      ``dados_comuns/behaviors.py`` (``CriadoPor``)

      **Descrição:**
      Usuário que criou o termo. Preenchido com o usuário autenticado da
      requisição no momento da criação via API.

   .. attribute:: alterado_por
      :type: perfil.Usuario | None

      **Descrição:**
      Usuário que realizou a última alteração do termo. Preenchido com o
      usuário autenticado da requisição no momento da criação via API
      (mesmo usuário de ``criado_por`` na criação).

   .. attribute:: criado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``CriadoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na criação do termo.

   .. attribute:: alterado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemAlteradoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na última alteração do termo.

CronogramaTermoRecebimentoDefinitivo
------------------------------------

Modelo intermediário (through) que vincula um :class:`TermoRecebimentoDefinitivo`
a um :class:`Cronograma <src.pre_recebimento.cronograma_entrega.models.Cronograma>`.

Como cada cronograma de um termo pode ter valores financeiros próprios,
o valor de contrato e a quantidade total recebida são armazenados **neste
modelo** (por cronograma) e não no termo. O mesmo cronograma não pode
aparecer duas vezes no mesmo termo (``unique_together`` entre ``termo`` e
``cronograma``).

Regras de negócio na criação:

- ``valor_contrato`` deve ser maior que zero.
- ``quantidade_total_recebida`` deve ser maior que zero.
- O cronograma deve pertencer ao contrato e à empresa selecionados no termo.

.. autoclass:: CronogramaTermoRecebimentoDefinitivo
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, cronograma, cronograma_id, id, objects, quantidade_total_recebida, termo, termo_id, valor_contrato

   .. attribute:: id
      :type: int

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django para identificar o vínculo.

   .. attribute:: termo
      :type: TermoRecebimentoDefinitivo

      **Descrição:**
      Termo de Recebimento Definitivo ao qual o vínculo pertence.
      ``on_delete=CASCADE``: ao remover o termo, os vínculos são removidos
      junto.

   .. attribute:: cronograma
      :type: Cronograma

      **Descrição:**
      Cronograma de entrega vinculado ao termo. ``on_delete=PROTECT``: o
      cronograma não pode ser removido enquanto houver termo vinculado.

   .. attribute:: valor_contrato
      :type: decimal.Decimal

      **Descrição:**
      Valor de contrato (em reais) relativo a este cronograma dentro do
      termo. Decimal com até 15 dígitos e 2 casas decimais. Deve ser maior
      que zero.

   .. attribute:: quantidade_total_recebida
      :type: decimal.Decimal

      **Descrição:**
      Quantidade total recebida relativa a este cronograma dentro do termo.
      Decimal com até 15 dígitos e 2 casas decimais. Deve ser maior que zero.
