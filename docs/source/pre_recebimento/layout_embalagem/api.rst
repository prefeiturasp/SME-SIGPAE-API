api
===

.. automodule:: src.pre_recebimento.layout_embalagem.api
   :members:
   :show-inheritance:

A API do submódulo expõe o endpoint ``/layouts-de-embalagem/`` (basename
``layouts-de-embalagem``), com CRUD e ações de análise/correção/dashboard:

- ``GET /layouts-de-embalagem/`` — listagem paginada
  (``DefaultPagination``) com filtros (``LayoutDeEmbalagemFilter``);
  fornecedores veem apenas os layouts das fichas técnicas da própria
  empresa.
- ``POST /layouts-de-embalagem/`` — criação pelo fornecedor
  (``UsuarioEhFornecedor``); o layout vai para ``ENVIADO_PARA_ANALISE``.
- ``GET /layouts-de-embalagem/<uuid>/`` — detalhe com tipos de embalagem,
  imagens, logs e log mais recente.
- ``PATCH/DELETE /layouts-de-embalagem/<uuid>/`` — atualização e exclusão
  (exclusão apenas por fornecedor).
- Ações ``detail=False``: ``dashboard``.
- Ações ``detail=True``: ``codae-aprova-ou-solicita-correcao``,
  ``fornecedor-realiza-correcao`` e
  ``download/{imagem_uuid}/`` (imagem assinada).

viewsets
--------

.. automodule:: src.pre_recebimento.layout_embalagem.api.viewsets
   :members:
   :show-inheritance:

``LayoutDeEmbalagemModelViewSet`` (``ModelViewSet`` com
``ViewSetActionPermissionMixin``):

- **Permissões**: visualização com
  ``PermissaoParaVisualizarLayoutDeEmbalagem``; ``create`` e ``delete``
  restritos a ``UsuarioEhFornecedor``; análise/dashboard com
  ``PermissaoParaDashboardLayoutEmbalagem``; correção com
  ``UsuarioEhFornecedor``.
- **Queryset dinâmico**: usuários fornecedores veem apenas layouts das
  fichas técnicas da própria empresa
  (``ficha_tecnica__empresa = vinculo_atual.instituicao``); ordenado por
  ``-criado_em``.
- **Serializador dinâmico**: ``list`` → ``LayoutDeEmbalagemSerializer``;
  ``retrieve`` → ``LayoutDeEmbalagemDetalheSerializer``; demais ações →
  ``LayoutDeEmbalagemCreateSerializer``.

Ações:

- ``codae_aprova_ou_solicita_correcao`` (PATCH
  ``codae-aprova-ou-solicita-correcao``,
  ``PermissaoParaDashboardLayoutEmbalagem``): analisa os tipos de
  embalagem — se todos estiverem ``APROVADO``, aprova o layout
  (``codae_aprova``); caso contrário, solicita correção
  (``codae_solicita_correcao``).
- ``dashboard`` (GET ``dashboard``,
  ``PermissaoParaDashboardLayoutEmbalagem``): painel por status via
  ``ServiceDashboardLayoutEmbalagem`` (``PainelLayoutEmbalagemSerializer``).
- ``fornecedor_realiza_correcao`` (PATCH ``fornecedor-realiza-correcao``,
  ``UsuarioEhFornecedor``): o fornecedor reenvia as imagens dos tipos
  reprovados, que voltam para ``EM_ANALISE``, e o layout volta para
  ``ENVIADO_PARA_ANALISE`` (``fornecedor_realiza_correcao``).
- ``download_imagem_assinada`` (GET ``download/{imagem_uuid}/``,
  ``PermissaoParaVisualizarLayoutDeEmbalagem``): gera e retorna o PDF da
  imagem com rodapé de assinatura digital; retorna ``404`` se a imagem não
  existir e ``401`` se a imagem não pertencer ao layout.

filters
-------

.. automodule:: src.pre_recebimento.layout_embalagem.filters
   :members:
   :show-inheritance:

``LayoutDeEmbalagemFilter`` filtra por ``numero_ficha_tecnica``
(``icontains``), ``nome_produto`` (``icontains``), ``nome_fornecedor``
(razão social, ``icontains``), ``pregao_chamada_publica``
(``icontains``), ``numero_cronograma`` (``icontains``) e ``status``
(múltipla escolha pelos estados do ``LayoutDeEmbalagemWorkflow``).

services
--------

.. automodule:: src.pre_recebimento.layout_embalagem.api.services
   :members:
   :show-inheritance:

``ServiceDashboardLayoutEmbalagem`` (herda ``BaseServiceDashboard``)
monta o painel de layouts de embalagem: para cada perfil autorizado
(``COORDENADOR_CODAE_DILOG_LOGISTICA``, ``DILOG_QUALIDADE``,
``COORDENADOR_GESTAO_PRODUTO``, ``ADMINISTRADOR_GESTAO_PRODUTO``,
``ADMINISTRADOR_CODAE_GABINETE``, ``DILOG_DIRETORIA``,
``DILOG_ABASTECIMENTO`` e ``DILOG_CRONOGRAMA``), define os status
exibidos (``ENVIADO_PARA_ANALISE``, ``APROVADO`` e
``SOLICITADO_CORRECAO``).

helpers
-------

.. automodule:: src.pre_recebimento.layout_embalagem.api.helpers
   :members:
   :show-inheritance:

- ``cria_tipos_de_embalagens``: cria os ``TipoDeEmbalagemDeLayout`` e seus
  ``ImagemDoTipoDeEmbalagem`` a partir do payload
  (``imagens_do_tipo_de_embalagem`` em base64, convertidos para
  ``ContentFile``).

serializers
~~~~~~~~~~~

.. automodule:: src.pre_recebimento.layout_embalagem.api.serializers.serializers
   :members:
   :show-inheritance:

Serializadores de saída:

- ``ImagemDoTipoEmbalagemLookupSerializer``: imagem de um tipo de
  embalagem (todos os campos, exceto ``id`` e ``tipo_de_embalagem``).
- ``TipoEmbalagemLayoutLookupSerializer``: tipo de embalagem com as
  ``imagens`` aninhadas (exceto ``id`` e ``layout_de_embalagem``).
- ``LayoutDeEmbalagemSerializer``: linha da listagem — número da ficha
  técnica, pregão/chamada pública, nome do produto, status (texto),
  ``criado_em`` e programa.
- ``LayoutDeEmbalagemDetalheSerializer``: detalhe — observações, status,
  tipos de embalagem (ordenados por primária/secundária/terciária via
  ``to_representation``), log mais recente, ``primeira_analise``, logs e
  programa.
- ``PainelLayoutEmbalagemSerializer``: linha do dashboard — produto,
  empresa, status, log mais recente, ``programa_leve_leite`` e
  ``eh_ficha_tecnica_flv``.

serializer\_create
~~~~~~~~~~~~~~~~~~

.. automodule:: src.pre_recebimento.layout_embalagem.api.serializers.serializer_create
   :members:
   :show-inheritance:

Serializadores de entrada:

- ``TipoDeEmbalagemDeLayoutCreateSerializer``: tipo de embalagem na criação
  — ``tipo_embalagem`` obrigatório e ``imagens_do_tipo_de_embalagem``
  (JSON, write-only); para os tipos primária e secundária, cada imagem
  exige ``arquivo`` e ``nome`` ("Este campo é obrigatório.").
- ``LayoutDeEmbalagemCreateSerializer``: criação/atualização pelo
  fornecedor — ``ficha_tecnica`` (uuid) obrigatória e sem status
  ``RASCUNHO`` ("Não é possível vincular com Ficha Técnica em rascunho.");
  na criação, persiste os tipos (helper) e chama ``inicia_fluxo``
  (o layout vai para ``ENVIADO_PARA_ANALISE``); na atualização, recria os
  tipos e chama ``fornecedor_atualiza`` (apenas layouts ``APROVADO``).
- ``TipoDeEmbalagemDeLayoutAnaliseSerializer``: tipo de embalagem na
  análise — para o tipo primária, exige ``uuid`` e ``status``
  ("UUID obrigatório para o tipo de embalagem informado.");
  ``complemento_do_status`` obrigatório.
- ``LayoutDeEmbalagemAnaliseSerializer``: análise da CODAE — na primeira
  análise, a quantidade de tipos recebida não pode ser menor que a
  existente ("Quantidade de Tipos de Embalagem recebida para primeira
  análise é menor que quantidade presente no Layout de Embalagem.");
  tipos novos podem ser criados (secundária/terciária) e, ao final,
  aprova ou solicita correção conforme ``aprovado``.
- ``TipoDeEmbalagemDeLayoutCorrecaoSerializer``: tipo de embalagem na
  correção — exige ``uuid``, ``tipo_embalagem`` e as novas imagens; o tipo
  deve existir ("UUID do tipo informado não existe.") e estar ``REPROVADO``
  ("O Tipo/UUID informado não pode ser corrigido pois não está reprovado.");
  cada imagem exige ``arquivo`` e ``nome`` ("arquivo/nome é obrigatório.").
- ``LayoutDeEmbalagemCorrecaoSerializer``: correção do fornecedor — os
  tipos reprovados voltam para ``EM_ANALISE`` com as novas imagens e o
  layout volta para ``ENVIADO_PARA_ANALISE``
  (``fornecedor_realiza_correcao``).
