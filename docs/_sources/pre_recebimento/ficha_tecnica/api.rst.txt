api
===

.. automodule:: src.pre_recebimento.ficha_tecnica.api
   :members:
   :show-inheritance:

A API do submódulo expõe dois conjuntos de endpoints (prefixo raiz, sem
``pre-recebimento/`` no path — ver ``src/pre_recebimento/urls.py``):

**Rascunho (fornecedor):**

- ``POST /rascunho-ficha-tecnica/`` — cria um rascunho de ficha técnica
  (permanece em ``RASCUNHO``).
- ``PATCH /rascunho-ficha-tecnica/<uuid>/`` — atualiza o rascunho.

**Ficha técnica (lista/detalhe/cadastro/análise):**

- ``GET /ficha-tecnica/`` — listagem paginada com filtros
  (``FichaTecnicaFilter``); fornecedores veem apenas as fichas da própria
  empresa.
- ``GET /ficha-tecnica/<uuid>/`` — detalhe completo.
- ``POST /ficha-tecnica/`` — cadastro de ficha (Perecíveis/Não perecíveis
  ou FLV conforme a ``categoria``) que já envia a ficha para análise
  (``inicia_fluxo``).
- ``PATCH /ficha-tecnica/<uuid>/`` — atualização.
- Ações ``detail=False``: ``dashboard``, ``lista-simples``,
  ``lista-simples-aprovadas``, ``lista-simples-sem-cronograma``,
  ``lista-simples-sem-layout-embalagem``,
  ``lista-simples-sem-questoes-conferencia``, ``listagem-relatorio`` e
  ``exportar-excel``.
- Ações ``detail=True``: ``dados-cronograma``, ``detalhar-com-analise``,
  ``rascunho-analise-gpcodae`` (POST/PUT), ``analise-gpcodae`` (POST/PUT),
  ``correcao-fornecedor`` (PATCH), ``atualizacao-fornecedor`` (PATCH) e
  ``gerar-pdf-ficha`` (GET).

viewsets
--------

.. automodule:: src.pre_recebimento.ficha_tecnica.api.viewsets
   :members:
   :show-inheritance:

``FichaTecnicaRascunhoViewSet``
  Criação e atualização de rascunhos (apenas ``UsuarioEhFornecedor``). O
  rascunho não inicia o fluxo (permanece em ``RASCUNHO``).

``FichaTecnicaModelViewSet``
  CRUD completo (list/retrieve/create/update) com:

  - **Queryset dinâmico**: usuários fornecedores veem apenas as fichas da
    própria empresa (``empresa=vinculo_atual.instituicao``).
  - **Serializador dinâmico**: ``list`` → ``FichaTecnicaListagemSerializer``;
    ``retrieve`` → ``FichaTecnicaDetalharSerializer``; ``create``/``update``
    → ``FichaTecnicaFLVCreateSerializer`` quando a ficha é da categoria
    ``FLV``, senão ``FichaTecnicaCreateSerializer``; ``listagem_relatorio``
    → ``RelatorioFichaTecnicaSerializer``.
  - **Verificação de autenticidade** no ``create``/``update`` e nas ações
    de correção/atualização do fornecedor
    (``verificar_autenticidade_usuario``).

  Ações:

  - ``dashboard``: painel de fichas por status com os filtros
    ``FichaTecnicaFilter``, via ``ServiceDashboardFichaTecnica``.
  - ``lista_simples``: fichas fora do status ``RASCUNHO`` (filtradas por
    empresa quando o usuário é fornecedor).
  - ``lista_simples_aprovadas``: fichas no status ``APROVADA``.
  - ``lista_simples_sem_cronograma``: fichas sem vínculo com cronograma e
    fora de ``RASCUNHO`` (usado para vincular fichas a cronogramas).
  - ``lista_simples_sem_layout_embalagem``: fichas sem layout de embalagem
    (fora de ``RASCUNHO``).
  - ``lista_simples_sem_questoes_conferencia``: fichas sem questões de
    conferência cadastradas (fora de ``RASCUNHO``).
  - ``dados_cronograma``: dados da ficha para o cadastro de cronograma.
  - ``detalhar_com_analise``: detalhe + análise mais recente + log mais
    recente.
  - ``rascunho_analise_gpcodae`` (POST/PUT): salva a análise em rascunho
    (``AnaliseFichaTecnicaRascunhoSerializer``) — não altera o status da
    ficha. Retorna ``201`` na criação e ``200`` na atualização.
  - ``analise_gpcodae`` (POST/PUT): registra a análise final
    (``AnaliseFichaTecnicaCreateSerializer``) e **altera o status da ficha**
    (aprova ou envia para correção conforme ``aprovada``).
  - ``correcao_fornecedor`` (PATCH): fornecedor corrige uma ficha no
    status ``ENVIADA_PARA_CORRECAO``
    (``CorrecaoFichaTecnicaSerializer``), validando apenas os campos dos
    blocos reprovados; após salvar, a ficha volta para ``ENVIADA_PARA_ANALISE``
    e é gerada uma nova análise.
  - ``atualizacao_fornecedor`` (PATCH): fornecedor atualiza uma ficha
    ``APROVADA`` (``FichaTecnicaAtualizacaoSerializer``), o que reabre a
    análise (a ficha volta para ``ENVIADA_PARA_ANALISE``).
  - ``gerar_pdf_ficha`` (GET): gera o PDF da ficha técnica
    (``get_pdf_ficha_tecnica``).
  - ``listagem_relatorio`` (GET): relatório paginado com totalizadores
    (aprovadas, enviadas para correção, pendentes de aprovação), excluindo
    fichas da categoria ``FLV``.
  - ``exportar_excel`` (GET): dispara a task assíncrona
    ``exporta_relatorio_fichas_tecnicas_xlsx`` com o mesmo queryset do
    relatório e responde "Solicitação de geração de arquivo recebida com
    sucesso."

filters
-------

.. automodule:: src.pre_recebimento.ficha_tecnica.api.filters
   :members:
   :show-inheritance:

``FichaTecnicaFilter`` permite filtrar por ``numero_ficha``,
``nome_produto``, ``nome_empresa``, ``empresa`` (uuid), ``pregao``,
``status`` (múltiplo, pelos estados do workflow), ``data_cadastro``,
``categoria`` e ``programa``.

services
--------

.. automodule:: src.pre_recebimento.ficha_tecnica.api.services
   :members:
   :show-inheritance:

``ServiceDashboardFichaTecnica`` (herda ``BaseServiceDashboard``) monta o
painel de fichas técnicas: para cada perfil autorizado, define os status
exibidos (``ENVIADA_PARA_ANALISE``, ``APROVADA`` e
``ENVIADA_PARA_CORRECAO``). Perfis contemplados: ``COORDENADOR_GESTAO_PRODUTO``,
``ADMINISTRADOR_GESTAO_PRODUTO``, ``COORDENADOR_CODAE_DILOG_LOGISTICA``,
``ADMINISTRADOR_CODAE_GABINETE``, ``DILOG_DIRETORIA``, ``DILOG_QUALIDADE``,
``DILOG_ABASTECIMENTO`` e ``DILOG_CRONOGRAMA``.

validators
----------

.. automodule:: src.pre_recebimento.ficha_tecnica.api.validators
   :members:
   :show-inheritance:

Funções de validação por categoria:

- ``valida_campos_flv_ficha_tecnica``: exige ``organico`` e
  ``especie_variedade``.
- ``valida_campos_pereciveis_ficha_tecnica``: exige ``organico``,
  ``prazo_validade_descongelamento``, ``temperatura_congelamento``,
  ``temperatura_veiculo``, ``condicoes_de_transporte`` e
  ``variacao_percentual``.
- ``valida_campos_nao_pereciveis_ficha_tecnica``: exige ``organico`` e
  ``produto_eh_liquido``.
- ``valida_campos_dependentes_ficha_tecnica``: regras dependentes
  (orgânico → ``mecanismo_controle``; alergênico → ``ingredientes_alergenicos``;
  lactose → ``lactose_detalhe``; líquido → volume e unidade de medida).
- ``valida_ingredientes_alergenicos_ficha_tecnica``: alergênico exige
  ``ingredientes_alergenicos``.

``ServiceValidacaoCorrecaoFichaTecnica`` valida a correção do fornecedor:

- Só permite corrigir fichas no status ``ENVIADA_PARA_CORRECAO``.
- Exige os campos obrigatórios de cada bloco reprovado (collapse) — os
  conjuntos ``CAMPOS_OBRIGATORIOS_COMUNS``, ``CAMPOS_PERECIVEIS``,
  ``CAMPOS_NAO_PERECIVEIS`` e ``CAMPOS_FLV`` definem, por bloco, os campos
  obrigatórios, dependentes e opcionais.
- Rejeita campos não permitidos no bloco sendo corrigido (um atributo só é
  aceito se pertencer aos campos daquele bloco).
- Os blocos a corrigir são obtidos da análise mais recente (campos
  ``*_conferido = False``).

helpers
-------

.. automodule:: src.pre_recebimento.ficha_tecnica.api.helpers
   :members:
   :show-inheritance:

Funções auxiliares da criação/atualização:

- ``cria_ficha_tecnica``: cria a ficha, o fabricante/envasador e as
  informações nutricionais; converte o ``arquivo`` (base64) em
  ``ContentFile``.
- ``atualiza_ficha_tecnica``: atualiza os dados da ficha, criando
  fabricantes/informações nutricionais novos quando necessário (e apagando
  as informações nutricionais antigas na atualização).
- ``limpar_campos_dependentes_ficha_tecnica``: ao marcar ``organico``/
  ``alergenicos``/``lactose``/``produto_eh_liquido`` como ``False``, limpa
  os campos dependentes correspondentes.
- ``gerar_nova_analise_ficha_tecnica``: cria uma nova análise a partir da
  anterior, preservando os blocos aprovados e as correções pendentes
  (usado após correção/atualização do fornecedor).
- ``reseta_analise_atualizacao``: marca como ``False`` os blocos da análise
  afetados pelos campos alterados na atualização do fornecedor.
- ``retorna_status_ficha_tecnica``/``formata_cnpj_ficha_tecnica``/
  ``formata_telefone_ficha_tecnica``: utilitários de exibição.

relatorio\_fichas\_tecnicas\_excel
----------------------------------

.. automodule:: src.pre_recebimento.ficha_tecnica.api.relatorio_fichas_tecnicas_excel
   :members:
   :show-inheritance:

Geração do arquivo Excel do Relatório de Fichas Técnicas
(``gera_relatorio_fichas_tecnicas_xlsx``), usado pela task assíncrona
``exporta_relatorio_fichas_tecnicas_xlsx``. O relatório contém 18 colunas
(nome do produto, empresa, categoria, programa, pregão, fabricante,
validade, orgânico, mecanismo de controle, alergênicos, glúten, lactose,
líquido, pesos e unidades de medida, status), com sanitização contra
fórmulas (injeção de ``=``/``+``/``-``/``@``), formatação numérica dos
pesos e largura dinâmica das colunas.

serializers
~~~~~~~~~~~

.. automodule:: src.pre_recebimento.ficha_tecnica.api.serializers.serializers
   :members:
   :show-inheritance:

Serializadores de saída:

- ``FichaTecnicaSimplesSerializer``: lista enxuta (uuid, número, produto,
  uuid da empresa, pregão, programa, ``ponto_a_ponto``).
- ``FichaTecnicaCronogramaSerializer``: dados da ficha usados no cadastro
  de cronograma (marca e unidades de medida de volume/pesos).
- ``FichaTecnicaListagemSerializer``: listagem da tela (nome do produto,
  data de cadastro formatada, status com ``get_status_display``).
- ``InformacoesNutricionaisFichaTecnicaSerializer``: item nutricional com a
  ``InformacaoNutricional`` aninhada.
- ``FabricanteFichaTecnicaSerializer``: fabricante/envasador com o
  ``Fabricante`` aninhado.
- ``FichaTecnicaDetalharSerializer``: detalhe completo da ficha, com
  produto, marca, empresa, fabricante/envasador, unidades de medida,
  informações nutricionais e ``logs``.
- ``AnaliseFichaTecnicaSerializer``: análise com o campo computado
  ``aprovada``.
- ``FichaTecnicaComAnaliseDetalharSerializer``: detalhe + análise mais
  recente + log mais recente formatado.
- ``PainelFichaTecnicaSerializer``: linha do dashboard (número, produto,
  empresa, status, log mais recente, ``programa_leve_leite``).
- ``RelatorioFichaTecnicaSerializer``: linha do relatório (produto, empresa,
  categoria/programa/status com display).

serializer\_create
~~~~~~~~~~~~~~~~~~

.. automodule:: src.pre_recebimento.ficha_tecnica.api.serializers.serializer_create
   :members:
   :show-inheritance:

Serializadores de entrada:

- ``InformacoesNutricionaisFichaTecnicaCreateSerializer``: item nutricional
  do payload (``informacao_nutricional`` por uuid).
- ``FabricanteFichaTecnicaCreateSerializer``: fabricante/envasador do
  payload; o campo ``fabricante`` é opcional quando o serializador é usado
  em correções (``fabricante_opcional=True``).
- ``FichaTecnicaRascunhoSerializer``: cadastro de rascunho (todos os campos
  opcionais); ao criar, registra o log de cadastro mas **não** inicia o
  fluxo.
- ``FichaTecnicaCreateSerializer``: cadastro definitivo (campos
  obrigatórios conforme a tela), valida os campos por categoria e dependentes,
  exige os checkboxes do Anexo I (``embalagens_de_acordo_com_anexo`` e
  ``rotulo_legivel`` = ``True``), valida que o ``arquivo`` é PDF e, ao
  criar/atualizar, **inicia o fluxo** (ficha vai para ``ENVIADA_PARA_ANALISE``).
- ``FichaTecnicaFLVCreateSerializer``: cadastro de fichas FLV (exige
  ``organico``, ``especie_variedade``, responsável técnico e arquivo).
- ``AnaliseFichaTecnicaRascunhoSerializer``: análise em rascunho da
  GPCODAE (todos os blocos opcionais) — não altera o status da ficha.
- ``AnaliseFichaTecnicaCreateSerializer``: análise final da GPCODAE. Para
  fichas FLV ponto a ponto, remove os blocos inexistentes; valida que
  ``*_conferido = False`` exige ``*_correcoes`` preenchido e vice-versa; ao
  salvar, **aprova ou envia para correção** a ficha conforme ``aprovada``.
- ``CorrecaoFichaTecnicaSerializer``: correção do fornecedor
  (``ServiceValidacaoCorrecaoFichaTecnica`` + validação de campos
  dependentes); ao atualizar, limpa os campos dependentes, chama
  ``fornecedor_corrige`` e gera nova análise.
- ``FichaTecnicaAtualizacaoSerializer``: atualização de ficha aprovada pelo
  fornecedor; gera nova análise (resetando os blocos afetados), chama
  ``fornecedor_atualiza`` e reabre o fluxo de análise.
