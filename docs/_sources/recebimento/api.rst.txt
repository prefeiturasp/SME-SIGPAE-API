api
===

.. automodule:: src.recebimento.api
   :members:
   :show-inheritance:

A API do módulo expõe os seguintes endpoints (montados na raiz, sem
prefixo):

- ``GET /questoes-conferencia/`` — questões agrupadas por tipo de
  embalagem; ``GET /questoes-conferencia/lista-simples-questoes/`` —
  questões distintas (seletores).
- ``/questoes-por-produto/`` — CRUD das questões vinculadas à ficha
  técnica de cada produto; ``GET /questoes-por-produto/busca-questoes-cronograma/?cronograma_uuid={uuid}``.
- ``POST /rascunho-ficha-de-recebimento/`` e
  ``PUT /rascunho-ficha-de-recebimento/{uuid}/`` — criação/atualização de
  ficha como rascunho (sem assinar).
- ``/fichas-de-recebimento/`` — listagem, criação (assinada), detalhe e
  atualização; ações ``cadastrar-saldo-zero``, ``{uuid}/atualizar-saldo-zero``
  e ``{uuid}/gerar-pdf-ficha``.
- ``POST /reposicao-ficha-de-recebimento/`` e
  ``PUT /reposicao-ficha-de-recebimento/{uuid}/`` — ficha no fluxo de
  reposição de cronograma.
- ``GET /reposicao-cronograma-ficha-recebimento/`` — tipos de reposição
  (Repor, Crédito, Outros).
- ``/ajuste-saldo-laudo/`` — CRUD dos ajustes de saldo do laudo (ver
  submódulo ajuste_saldo_laudo).

viewsets
--------

.. automodule:: src.recebimento.api.viewsets
   :members:
   :show-inheritance:

``QuestoesConferenciaModelViewSet`` (``ReadOnlyModelViewSet``):

- **Permissões**: ``PermissaoParaVisualizarQuestoesConferencia``
  (``DILOG_QUALIDADE``).
- **Queryset**: questões ordenadas por ``posicao``.

Ações:

- ``list`` (GET): retorna ``{"results": {"primarias": [...], "secundarias": [...]}}``,
  agrupando por tipo de embalagem.
- ``lista_simples_questoes`` (GET ``lista-simples-questoes``): lista as
  questões distintas (``uuid`` e ``questao``), ordenadas pelo texto.

``QuestoesPorProdutoModelViewSet`` (``ModelViewSet``):

- **Permissões**: ``PermissaoParaVisualizarQuestoesConferencia``.
- **Queryset**: vínculos ordenados por ``-criado_em``.
- **Serializador dinâmico**: ``list`` → ``QuestoesPorProdutoSerializer``;
  ``retrieve`` → ``QuestoesPorProdutoSimplesSerializer``; demais ações →
  ``QuestoesPorProdutoCreateSerializer``.

Ações:

- ``busca_questoes_cronograma`` (GET ``busca-questoes-cronograma``,
  ``PermissaoParaVisualizarQuestoesConferencia``): busca as questões da
  ficha técnica de um cronograma (parâmetro obrigatório
  ``cronograma_uuid``); ``400`` para uuid inválido ou parâmetro ausente,
  ``404`` para cronograma inexistente e ``200`` vazio quando o produto não
  possui questões cadastradas.

``FichaDeRecebimentoRascunhoViewSet`` (``GenericViewSet`` com
``CreateModelMixin`` e ``UpdateModelMixin``):

- **Permissões**: ``PermissaoParaCadastrarFichaRecebimento``
  (``DILOG_QUALIDADE``).
- **Serializer**: ``FichaDeRecebimentoRascunhoSerializer`` — não inicia o
  fluxo (ficha permanece em ``RASCUNHO``); ao atualizar uma ficha
  ``ASSINADA``, executa ``volta_para_rascunho``.

Ações:

- ``create`` (POST): cria uma ficha rascunho (retorna ``201``).
- ``update`` (PUT): atualiza uma ficha rascunho (retorna ``200``).

``FichaRecebimentoModelViewSet`` (``GenericViewSet`` com ``ListModelMixin``,
``CreateModelMixin``, ``UpdateModelMixin`` e ``RetrieveModelMixin``):

- **Permissões**: ``PermissaoParaVisualizarFichaRecebimento``
  (``DILOG_QUALIDADE``, ``COORDENADOR_CODAE_DILOG_LOGISTICA``,
  ``DILOG_CRONOGRAMA``, ``DILOG_DIRETORIA`` e ``DILOG_ABASTECIMENTO``);
  criação/atualização (incluindo as variantes ``saldo_zero``) exigem
  ``PermissaoParaCadastrarFichaRecebimento``.
- **Queryset**: fichas ordenadas por ``-criado_em``, com filtros
  (``FichaRecebimentoFilter``) e paginação (``DefaultPagination``).
- **Serializador dinâmico**: ``create``/``update`` →
  ``FichaDeRecebimentoCreateSerializer``; ``create_saldo_zero``/
  ``update_saldo_zero`` → ``FichaDeRecebimentoCreateSerializerSaldoZero``;
  ``retrieve`` → ``FichaDeRecebimentoDetalharSerializer``; demais ações →
  ``FichaDeRecebimentoSerializer``.

Ações:

- ``create`` (POST): cria uma ficha assinada — verifica a autenticidade do
  usuário (senha) e o serializer executa ``inicia_fluxo``
  (RASCUNHO → ASSINADA); retorna ``201``.
- ``update`` (PUT): atualiza uma ficha (verifica a senha; ``inicia_fluxo``
  apenas quando a ficha está em ``RASCUNHO``).
- ``create_saldo_zero`` (POST ``cadastrar-saldo-zero``,
  ``PermissaoParaCadastrarFichaRecebimento``): cria uma ficha ignorando os
  campos validados com ``requiredSaldoTotalZero`` no frontend.
- ``update_saldo_zero`` (PUT ``{uuid}/atualizar-saldo-zero``,
  ``PermissaoParaCadastrarFichaRecebimento``): atualiza uma ficha
  ignorando os campos de saldo total zero.
- ``gerar_pdf_ficha`` (GET ``{uuid}/gerar-pdf-ficha``,
  ``PermissaoParaVisualizarRelatorioCronograma``): gera o PDF da ficha de
  recebimento (``get_pdf_ficha_recebimento``).

``FichaDeRecebimentoReposicaoViewSet`` (``GenericViewSet`` com
``CreateModelMixin`` e ``UpdateModelMixin``):

- **Permissões**: ``PermissaoParaCadastrarFichaRecebimento``.
- **Serializer**: ``FichaDeRecebimentoReposicaoSerializer`` — na criação e
  na atualização de fichas em ``RASCUNHO``, executa ``inicia_fluxo``.

Ações:

- ``create`` (POST): cria uma ficha no fluxo de reposição de cronograma.
- ``update`` (PUT): atualiza uma ficha de reposição.

``ReposicaoCronogramaFichaRecebimentoViewSet`` (``ReadOnlyModelViewSet``):

- Lista os tipos de reposição de cronograma disponíveis
  (``/reposicao-cronograma-ficha-recebimento/``).

filters
-------

.. automodule:: src.recebimento.api.filters
   :members:
   :show-inheritance:

- ``QuestoesPorProdutoFilter``: filtra por ``ficha_tecnica`` (uuid exato)
  e por ``questao`` (texto, considerando questões primárias e secundárias).
- ``FichaRecebimentoFilter``: filtra por ``numero_cronograma``
  (``icontains``), ``nome_produto`` (``icontains``), ``nome_empresa``
  (nome fantasia, ``icontains``), período de entrega
  (``data_inicial``/``data_final``) e ``status`` (múltipla escolha pelos
  estados do ``FichaDeRecebimentoWorkflow``).

permissions
-----------

.. automodule:: src.recebimento.api.permissions
   :members:
   :show-inheritance:

- ``PermissaoParaVisualizarQuestoesConferencia``: apenas ``DILOG_QUALIDADE``.
- ``PermissaoParaCadastrarFichaRecebimento``: apenas ``DILOG_QUALIDADE``.
- ``PermissaoParaVisualizarFichaRecebimento``: ``DILOG_QUALIDADE``,
  ``COORDENADOR_CODAE_DILOG_LOGISTICA``, ``DILOG_CRONOGRAMA``,
  ``DILOG_DIRETORIA`` e ``DILOG_ABASTECIMENTO``.

helpers
-------

.. automodule:: src.recebimento.api.helpers
   :members:
   :show-inheritance:

- ``criar_ficha`` / ``atualizar_ficha``: criam/atualizam a ficha com todos
  os relacionamentos (veículos, documentos, arquivos, questões e
  ocorrências). A atualização remove e recria os relacionamentos.
- ``criar_veiculos``: cria os ``VeiculoFichaDeRecebimento``.
- ``criar_arquivos``: cria os ``ArquivoFichaRecebimento`` a partir de
  base64 (convertidos para ``ContentFile``).
- ``criar_questoes``: cria as ``QuestaoFichaRecebimento``.
- ``criar_documentos_ficha``: cria os ``DocumentoFichaDeRecebimento`` com
  a quantidade recebida.
- ``criar_ocorrencias``: cria as ``OcorrenciaFichaRecebimento`` — permite
  no máximo uma ocorrência do tipo ``RECUSA`` por ficha ("Apenas uma
  ocorrência do tipo RECUSA é permitida por ficha de recebimento.").

serializers
~~~~~~~~~~~

.. automodule:: src.recebimento.api.serializers.serializers
   :members:
   :show-inheritance:

Serializadores de saída:

- ``QuestaoConferenciaSerializer``: questão completa (uuid, texto, tipo,
  obrigatoriedade e posição).
- ``QuestaoConferenciaSimplesSerializer``: ``uuid`` e ``questao``
  (seletores).
- ``QuestoesPorProdutoSerializer``: listagem — número da ficha, nome do
  produto e textos das questões primárias/secundárias ordenados por
  posição.
- ``QuestoesPorProdutoSimplesSerializer``: ``uuid``, ficha técnica e uuids
  das questões.
- ``QuestoesPorProdutoDetalheSerializer``: detalhe com as questões
  completas (usado no ``busca-questoes-cronograma``).
- ``QuestaoFichaRecebimentoSerializer``: resposta a uma questão na ficha.
- ``FichaDeRecebimentoSerializer``: linha da listagem — número do
  cronograma, produto, fornecedor, pregão, data de recebimento, status e
  ``programa_leve_leite``.
- ``VeiculoFichaDeRecebimentoSerializer``: veículo (exceto ``id`` e
  ``ficha_recebimento``).
- ``QuestaoFichaRecebimentoDetailSerializer``: resposta com a questão
  completa.
- ``OcorrenciaFichaRecebimentoSerializer``: ocorrência (exceto ``id`` e
  ``ficha_recebimento``).
- ``ArquivoFichaRecebimentoSerializer``: ``nome`` e URL completa do
  arquivo (prefixo da variável ``URL_ANEXO``).
- ``DadosCronogramaSerializer``: dados do cronograma derivados da etapa
  (uuid, número, embalagens, pesos líquidos e sistema de vedação).
- ``ReposicaoCronogramaFichaRecebimentoSerializer``: tipo de reposição.
- ``FichaDeRecebimentoDetalharSerializer``: detalhe completo — dados do
  cronograma, etapa, documentos com quantidade recebida, conformidades e
  divergências, veículos, questões, ocorrências, arquivos, observações e
  reposição.

serializer\_create
~~~~~~~~~~~~~~~~~~

.. automodule:: src.recebimento.api.serializers.serializers_create
   :members:
   :show-inheritance:

Serializadores de entrada:

- ``QuestoesPorProdutoCreateSerializer``: vincula a ficha técnica às
  questões primárias/secundárias (na atualização, substitui as anteriores).
- ``VeiculoFichaDeRecebimentoRascunhoSerializer``: veículo no rascunho.
- ``QuestaoFichaRecebimentoCreateSerializer``: resposta a uma questão
  (``questao_conferencia`` por uuid).
- ``ArquivoFichaRecebimentoCreateSerializer``: arquivo em base64 + nome.
- ``DocumentoFichaDeRecebimentoCreateSerializer``: vincula um documento
  (apenas ``APROVADO``) com a ``quantidade_recebida`` (obrigatória e maior
  que zero).
- ``OcorrenciaFichaRecebimentoCreateSerializer``: ocorrência com validações
  por tipo (ver regras em models.rst); quando ``rascunho=True``, as
  validações são ignoradas.
- ``FichaDeRecebimentoCreateSerializer``: criação/atualização da ficha
  assinada. Regras: (1) ``etapa``, ``data_entrega``,
  ``documentos_recebimento``, indicadores de conformidade,
  ``numero_lote_armazenagem``, ``numero_paletes``, os 4 pesos das
  embalagens primárias, ``veiculos``, ``sistema_vedacao_embalagem_secundaria``
  e ``questoes`` obrigatórios; (2) divergências: quando ``*_de_acordo`` é
  ``False``, a respectiva ``*_divergencia`` é obrigatória ("Campo
  obrigatório quando ... não está de acordo."); (3) veículos: ao menos um
  ("É necessário informar pelo menos um veículo."); (4) questões: todas as
  obrigatórias do produto devem ser respondidas ("Questões obrigatórias
  não respondidas: ..."). Na criação e na atualização de fichas em
  ``RASCUNHO``, executa ``inicia_fluxo``. Os campos de peso são
  normalizados de texto (``1.234,56`` → ``1234.56``).
- ``FichaDeRecebimentoCreateSerializerSaldoZero`` (herda o de criação):
  ignora os campos validados com ``requiredSaldoTotalZero`` no frontend; na
  atualização, limpa os campos de conformidade/pesos ausentes.
- ``FichaDeRecebimentoRascunhoSerializer``: rascunho — campos opcionais,
  não inicia o fluxo; ao atualizar uma ficha ``ASSINADA``, executa
  ``volta_para_rascunho``.
- ``FichaDeRecebimentoReposicaoSerializer``: ficha de reposição — exige
  ``etapa``, ``data_entrega``, ``observacao`` e ``reposicao_cronograma``;
  executa ``inicia_fluxo`` na criação/atualização de rascunho.
