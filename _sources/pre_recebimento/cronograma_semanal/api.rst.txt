api
===

.. automodule:: src.pre_recebimento.cronograma_semanal.api
   :members:
   :show-inheritance:

A API do submódulo expõe o endpoint ``/cronogramas-semanais/`` (basename
``cronogramas-semanais``), com criação de rascunho, listagem, detalhe,
calendário, assinatura/envio, ciência do fornecedor, alteração e geração
de PDF:

- ``GET /cronogramas-semanais/`` — listagem paginada
  (``PreRecebimentoPagination``) com filtros (``CronogramaSemanalFilter``);
  fornecedores veem apenas os cronogramas da própria empresa, sem os
  ``RASCUNHO``.
- ``POST /cronogramas-semanais/rascunho/`` — criação de rascunho
  (apenas ``cronograma_mensal`` obrigatório).
- ``GET /cronogramas-semanais/<uuid>/`` — detalhe com programações, dados
  do cronograma mensal e logs.
- ``PATCH /cronogramas-semanais/<uuid>/`` — atualização de rascunho.
- ``PATCH /cronogramas-semanais/<uuid>/assinar-e-enviar/`` — assina e
  envia o cronograma ao fornecedor (valida a senha do usuário).
- ``PATCH /cronogramas-semanais/<uuid>/fornecedor-ciente/`` — registra a
  ciência do fornecedor.
- ``PATCH /cronogramas-semanais/<uuid>/alterar-cronograma/`` — altera o
  cronograma após a ciência do fornecedor (valida a senha do usuário).
- ``GET /cronogramas-semanais/<uuid>/gerar-pdf-cronograma/`` — gera o PDF
  (apenas no status ``FORNECEDOR_CIENTE``).
- Ações ``detail=False``: ``calendario``, ``rascunho``,
  ``rascunhos`` e ``cronogramas-mensal-assinados``.

viewsets
--------

.. automodule:: src.pre_recebimento.cronograma_semanal.api.viewsets
   :members:
   :show-inheritance:

``CronogramaSemanalViewSet`` (``GenericViewSet`` com
``CreateModelMixin``, ``UpdateModelMixin``, ``ListModelMixin`` e
``RetrieveModelMixin``):

- **Permissões**: ``PermissaoParaVisualizarCronogramaSemanal`` por padrão;
  ``permission_action_classes`` define permissões por ação:
  ``rascunho``/``create``/``update``/``partial_update``/``rascunhos_listagem``/
  ``alterar_cronograma`` → ``PermissaoParaCriarCronogramaSemanal``
  (DILOG); ``fornecedor_ciente`` → ``PermissaoParaDarCienciaCronogramaSemanal``;
  ``calendario`` → ``PermissaoParaVisualizarCalendarioCronograma``.
- **Queryset dinâmico**: ``get_queryset`` usa ``select_related``
  (cronograma mensal, ficha técnica, produto, empresa) e
  ``prefetch_related`` (programações), ordenado por ``-alterado_em``.
- **Serializador dinâmico**: mapa por ação — ``rascunho``/``update``/
  ``partial_update`` → ``CronogramaSemanalRascunhoSerializer``;
  ``assinar_e_enviar`` → ``CronogramaSemanalAssinarEEnviarSerializer``;
  ``alterar_cronograma`` → ``CronogramaSemanalAlterarSerializer``;
  ``rascunhos_listagem`` → ``CronogramaSemanalRascunhosSerializer``;
  ``retrieve``/``fornecedor_ciente`` → ``CronogramaSemanalDetailSerializer``;
  ``list`` → ``CronogramaSemanalListagemSerializer``; ``calendario`` →
  ``CronogramaSemanalCalendarioSerializer``.

Ações:

- ``list`` (GET): lista os cronogramas semanais; para fornecedores
  (``ADMINISTRADOR_EMPRESA``/``USUARIO_EMPRESA`` com instituição
  fornecedora), filtra pela empresa e exclui ``RASCUNHO``.
- ``calendario`` (GET ``calendario``): lista os cronogramas para exibição
  no calendário, filtrando as programações por ``mes`` e ``ano``
  (obrigatórios) e excluindo ``RASCUNHO``; aceita filtro opcional por
  ``status``.
- ``rascunho`` (POST ``rascunho``,
  ``PermissaoParaCriarCronogramaSemanal``): cria um novo cronograma
  semanal como rascunho (apenas ``cronograma_mensal`` obrigatório) e
  registra o log ``CRONOGRAMA_SEMANAL_CRIADO``.
- ``rascunhos_listagem`` (GET ``rascunhos``,
  ``PermissaoParaCriarCronogramaSemanal``): lista os cronogramas com
  status ``RASCUNHO`` (``uuid``, ``numero`` e ``alterado_em``).
- ``cronogramas_mensal_assinados`` (GET ``cronogramas-mensal-assinados``):
  lista os cronogramas mensais do tipo Ponto a Ponto com status
  ``ASSINADO_CODAE`` (seletor do formulário de cadastro).
- ``assinar_e_enviar`` (PATCH ``assinar-e-enviar``, valida a senha do
  usuário): executa a transição ``inicia_fluxo``
  (``RASCUNHO`` → ``ENVIADO_AO_FORNECEDOR``); exige ao menos uma
  programação.
- ``fornecedor_ciente`` (PATCH ``fornecedor-ciente``,
  ``PermissaoParaDarCienciaCronogramaSemanal``): executa a transição
  ``fornecedor_ciente`` (``ENVIADO_AO_FORNECEDOR`` → ``FORNECEDOR_CIENTE``).
- ``alterar_cronograma`` (PATCH ``alterar-cronograma``, valida a senha do
  usuário): executa a transição ``alterar_cronograma``
  (``FORNECEDOR_CIENTE`` → ``ENVIADO_AO_FORNECEDOR``).
- ``gerar_pdf_cronograma`` (GET ``gerar-pdf-cronograma``): gera o PDF do
  cronograma semanal; retorna ``400`` se o status não for
  ``FORNECEDOR_CIENTE`` ("O PDF só pode ser gerado para cronogramas no
  status Fornecedor Ciente.").

filters
-------

.. automodule:: src.pre_recebimento.cronograma_semanal.api.filters
   :members:
   :show-inheritance:

``CronogramaSemanalFilter`` filtra por ``numero`` (número do cronograma
mensal, ``icontains``), ``nome_empresa`` (nome fantasia, ``icontains``),
``nome_produto`` (``icontains``), ``status`` (múltipla escolha pelos
estados do ``CronogramaSemanalWorkflow``) e período
``data_inicial``/``data_final`` (``%d/%m/%Y``). O filtro de período é
aplicado em ``filter_queryset`` via subquery ``Exists`` nas programações:
mantém apenas os cronogramas com programações cujo período intercepta o
intervalo informado.

serializers
~~~~~~~~~~~

.. automodule:: src.pre_recebimento.cronograma_semanal.api.serializers.serializers
   :members:
   :show-inheritance:

Serializadores de saída:

- ``CronogramaSemanalListagemSerializer``: linha da listagem — número do
  cronograma mensal, produto, quantidade total (do cronograma mensal),
  unidade de medida (abreviação), empresa e status (texto).
- ``CronogramaSemanalCalendarioSerializer``: linha do calendário — número,
  produto, fornecedor (nome fantasia), empenho, unidade de medida e as
  programações do mês/ano (``data_inicio``, ``data_fim`` e ``quantidade``).
- ``ProgramacaoEntregaSemanalDetailSerializer``: leitura de uma programação
  (``mes_programado``, ``data_inicio``, ``data_fim`` e ``quantidade``).
- ``CronogramaMensalSimplesSerializer``: dados resumidos do cronograma
  mensal (empresa, contrato, unidade de medida, produto e empenho).
- ``CronogramaSemanalRascunhosSerializer``: rascunho na listagem
  (``uuid``, ``numero`` e ``alterado_em``).
- ``CronogramaSemanalDetailSerializer``: detalhe — status (texto),
  observações, cronograma mensal (``CronogramaMensalSimplesSerializer``),
  programações e logs.

serializer\_create
~~~~~~~~~~~~~~~~~~

.. automodule:: src.pre_recebimento.cronograma_semanal.api.serializers.serializer_create
   :members:
   :show-inheritance:

Serializadores de entrada:

- ``ProgramacaoEntregaSemanalCreateSerializer``: criação de programação —
  ``mes_programado``, ``data_inicio``, ``data_fim`` e ``quantidade``
  obrigatórios; valida que ``data_fim`` não seja anterior a ``data_inicio``
  ("Data fim deve ser posterior à data início.").
- ``CronogramaSemanalRascunhoSerializer``: criação/atualização de rascunho
  — ``cronograma_mensal`` (uuid) obrigatório; ``observacoes`` e
  ``programacoes`` opcionais. Validações:
  (1) o cronograma mensal deve ser do tipo Ponto a Ponto ("O cronograma
  mensal deve ser do tipo Ponto a Ponto."); (2) o cronograma mensal deve
  estar com status ``ASSINADO_CODAE`` ("O cronograma mensal deve estar com
  status ASSINADO_CODAE."). Na criação, o número é gerado no formato
  ``XXX/YYYY`` (``gera_proximo_numero_cronograma_semanal``) e as
  programações são criadas em transação atômica. Na atualização, as
  programações são recriadas (``bulk_create``).
- ``CronogramaSemanalAssinarEEnviarSerializer`` (herda o rascunho):
  assinatura/envio — ``programacoes`` obrigatórias (ao menos uma: "É
  necessário adicionar pelo menos uma programação."); executa
  ``inicia_fluxo`` após salvar (``RASCUNHO`` → ``ENVIADO_AO_FORNECEDOR``).
- ``CronogramaSemanalAlterarSerializer`` (herda assinar-e-enviar):
  alteração após ciência do fornecedor — executa ``alterar_cronograma``
  (``FORNECEDOR_CIENTE`` → ``ENVIADO_AO_FORNECEDOR``).
