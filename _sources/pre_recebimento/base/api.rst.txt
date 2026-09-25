api
===

.. automodule:: src.pre_recebimento.base.api
   :members:
   :show-inheritance:

A API do submódulo expõe o endpoint ``/unidades-medida-logistica/``
(basename ``unidades-medida-logistica``), com CRUD completo:

- ``GET /unidades-medida-logistica/`` — listagem paginada
  (``DefaultPagination``) com filtros (``UnidadeMedidaFilter``).
- ``POST /unidades-medida-logistica/`` — criação pela CODAE
  (``PermissaoParaCadastrarVisualizarUnidadesMedida``); valida a
  capitalização de nome e abreviação.
- ``GET /unidades-medida-logistica/<uuid>/`` — detalhe.
- ``PATCH/DELETE /unidades-medida-logistica/<uuid>/`` — atualização e
  exclusão.
- ``GET /unidades-medida-logistica/lista-nomes-abreviacoes/`` — ação
  ``detail=False`` que lista os pares ``nome``/``abreviacao`` de todas as
  unidades (acessível também aos perfis de empresa via
  ``PermissaoParaVisualizarUnidadesMedida``).

viewsets
--------

.. automodule:: src.pre_recebimento.base.api.viewsets
   :members:
   :show-inheritance:

``UnidadeMedidaViewset`` (``ModelViewSet``):

- **Permissões**: ``PermissaoParaCadastrarVisualizarUnidadesMedida``
  (usuários da CODAE com perfis ``DILOG_QUALIDADE``,
  ``DILOG_CRONOGRAMA`` ou ``COORDENADOR_CODAE_DILOG_LOGISTICA``); a ação
  ``lista-nomes-abreviacoes`` usa
  ``PermissaoParaVisualizarUnidadesMedida``, que libera também os perfis
  ``ADMINISTRADOR_EMPRESA`` e ``USUARIO_EMPRESA``.
- **Queryset**: todos os registros ordenados por ``-criado_em``.
- **Serializador dinâmico**: ``list``/``retrieve`` →
  ``UnidadeMedidaSerialzer`` (com ``criado_em``); demais ações →
  ``UnidadeMedidaCreateSerializer`` (valida capitalização).

Ações:

- ``listar_nomes_abreviacoes`` (GET ``lista-nomes-abreviacoes``,
  ``PermissaoParaVisualizarUnidadesMedida``): retorna
  ``{"results": [{"uuid", "nome", "abreviacao"}]}`` para popular seletores.

filters
-------

.. automodule:: src.pre_recebimento.base.api.filters
   :members:
   :show-inheritance:

``UnidadeMedidaFilter`` filtra por ``nome`` (``icontains``),
``abreviacao`` (``icontains``) e ``data_cadastro`` (data exata de
``criado_em``).

services
--------

.. automodule:: src.pre_recebimento.base.api.services
   :members:
   :show-inheritance:

``BaseServiceDashboard`` é o service base para montagem dos dados dos
dashboards por perfil e status. Deve ser estendido pelos services
concretos dos submódulos, que sobrescrevem ``STATUS_POR_PERFIL`` com o
mapeamento de perfis para os status exibidos nos cards.

- ``get_dashboard_status(user)``: retorna a lista de status do perfil do
  usuário; lança ``ValueError("Perfil não existe")`` para perfis não
  mapeados.
- ``get_dados_dashboard()``: se houver o parâmetro ``status`` na query
  string, retorna a visualização "ver mais" para os status informados;
  caso contrário, agrupa os dados por status (cards) conforme o perfil.
- ``_get_dados_ver_mais`` / ``_get_dados_cards``: montagem dos dados
  paginados (``offset``/``limit``, padrão 6) por status.

paginations
-----------

.. automodule:: src.pre_recebimento.base.api.paginations
   :members:
   :show-inheritance:

``PreRecebimentoPagination`` é a paginação padrão das listagens de
pré-recebimento: página com 10 registros, tamanho configurável via
``page_size`` (máximo 100).

serializers
~~~~~~~~~~~

.. automodule:: src.pre_recebimento.base.api.serializers.serializers
   :members:
   :show-inheritance:

Serializadores de saída:

- ``UnidadeMedidaSimplesSerializer``: ``uuid``, ``nome`` e ``abreviacao``
  (somente leitura) — usado na ação ``lista-nomes-abreviacoes``.
- ``UnidadeMedidaSerialzer``: ``uuid``, ``nome``, ``abreviacao`` e
  ``criado_em`` (somente leitura) — usado em listagens e detalhes.

serializer\_create
~~~~~~~~~~~~~~~~~~

.. automodule:: src.pre_recebimento.base.api.serializers.serializer_create
   :members:
   :show-inheritance:

Serializador de entrada:

- ``UnidadeMedidaCreateSerializer``: criação/atualização — ``uuid`` e
  ``criado_em`` somente leitura. Validações:

  1. ``nome`` deve conter apenas letras maiúsculas ("O campo deve conter
     apenas letras maiúsculas.").
  2. ``abreviacao`` deve conter apenas letras minúsculas ("O campo deve
     conter apenas letras minúsculas.").
