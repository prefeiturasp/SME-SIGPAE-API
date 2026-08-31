api
===

.. automodule:: src.pre_recebimento.qualidade.api
   :members:
   :show-inheritance:

A API do submódulo expõe dois endpoints:

- ``/laboratorios/`` (basename ``laboratorios``) — CRUD de laboratórios,
  com ações de listagem para seletores e filtros.
- ``/tipos-embalagens/`` (basename ``tipos-embalagens``) — CRUD de tipos
  de embalagem (qualidade), com ações de listagem.

Endpoints de laboratórios:

- ``GET /laboratorios/`` — listagem paginada (``PreRecebimentoPagination``)
  com filtros (``LaboratorioFilter``).
- ``POST /laboratorios/`` — criação pela CODAE
  (``PermissaoParaCadastrarLaboratorio``).
- ``GET /laboratorios/<uuid>/`` — detalhe com os contatos.
- ``PATCH/DELETE /laboratorios/<uuid>/`` — atualização e exclusão
  (exclusão restrita a ``PermissaoParaCadastrarLaboratorio``).
- ``GET /laboratorios/lista-nomes-laboratorios/`` — nomes de todos os
  laboratórios (seletores).
- ``GET /laboratorios/lista-laboratorios-credenciados/`` — ``uuid`` e
  ``nome`` apenas dos laboratórios credenciados.
- ``GET /laboratorios/lista-laboratorios/`` — ``nome`` e ``cnpj`` de
  todos os laboratórios (filtros).

Endpoints de tipos de embalagem:

- ``GET /tipos-embalagens/`` — listagem paginada com filtros
  (``TipoEmbalagemQldFilter``).
- ``POST /tipos-embalagens/`` — criação
  (``PermissaoParaCadastrarVisualizarEmbalagem``).
- ``GET /tipos-embalagens/<uuid>/`` — detalhe.
- ``PATCH/DELETE /tipos-embalagens/<uuid>/`` — atualização e exclusão.
- ``GET /tipos-embalagens/lista-nomes-tipos-embalagens/`` — nomes
  (seletores).
- ``GET /tipos-embalagens/lista-abreviacoes-tipos-embalagens/`` —
  abreviações (seletores).
- ``GET /tipos-embalagens/lista-tipos-embalagens/`` — tipos completos.

viewsets
--------

.. automodule:: src.pre_recebimento.qualidade.api.viewsets
   :members:
   :show-inheritance:

``LaboratorioModelViewSet`` (``ModelViewSet`` com
``ViewSetActionPermissionMixin``):

- **Permissões**: ``PermissaoParaCadastrarLaboratorio`` (usuários da
  CODAE com perfis ``DILOG_QUALIDADE`` ou
  ``COORDENADOR_CODAE_DILOG_LOGISTICA``); ``create`` e ``delete``
  reforçados com a mesma permissão via ``permission_action_classes``.
- **Queryset**: todos os laboratórios ordenados por ``-criado_em``.
- **Serializador dinâmico**: ``list``/``retrieve`` →
  ``LaboratorioSerializer`` (com contatos); demais ações →
  ``LaboratorioCreateSerializer``.

Ações:

- ``lista_nomes_laboratorios`` (GET ``lista-nomes-laboratorios``): retorna
  ``{"results": [nomes]}`` de todos os laboratórios.
- ``lista_nomes_laboratorios_credenciados`` (GET
  ``lista-laboratorios-credenciados``): retorna
  ``{"results": [{"uuid", "nome"}]}`` apenas dos laboratórios com
  ``credenciado = True``.
- ``lista_laboratorios_para_filtros`` (GET ``lista-laboratorios``):
  retorna ``{"results": [{"nome", "cnpj"}]}`` de todos os laboratórios.

``TipoEmbalagemQldModelViewSet`` (``ModelViewSet``):

- **Permissões**: ``PermissaoParaCadastrarVisualizarEmbalagem`` (perfis
  ``DILOG_QUALIDADE``, ``DILOG_CRONOGRAMA`` e
  ``COORDENADOR_CODAE_DILOG_LOGISTICA``).
- **Queryset**: todos os tipos ordenados por ``-criado_em``.
- **Serializador dinâmico**: ``list``/``retrieve`` →
  ``TipoEmbalagemQldSerializer``; demais ações →
  ``TipoEmbalagemQldCreateSerializer``.

Ações:

- ``lista_nomes_tipos_embalagens`` (GET ``lista-nomes-tipos-embalagens``):
  retorna ``{"results": [nomes]}``.
- ``lista_abreviacoes_tipos_embalagens`` (GET
  ``lista-abreviacoes-tipos-embalagens``): retorna
  ``{"results": [abreviacoes]}``.
- ``lista_tipo_embalagem_completa`` (GET ``lista-tipos-embalagens``):
  retorna ``{"results": [tipos completos]}``.

filters
-------

.. automodule:: src.pre_recebimento.qualidade.api.filters
   :members:
   :show-inheritance:

- ``TipoEmbalagemQldFilter``: filtra por ``uuid`` (exato), ``nome``
  (``icontains``), ``abreviacao`` (exato) e ``data_cadastro`` (data exata
  de ``criado_em``).
- ``LaboratorioFilter``: filtra por ``uuid`` (exato), ``nome``
  (``icontains``), ``cnpj`` (``icontains``) e ``credenciado`` (booleano).

serializers
~~~~~~~~~~~

.. automodule:: src.pre_recebimento.qualidade.api.serializers.serializers
   :members:
   :show-inheritance:

Serializadores de saída:

- ``TipoEmbalagemQldSerializer``: tipo de embalagem completo (todos os
  campos, exceto ``id``).
- ``TipoEmbalagemQldSimplesSerializer``: ``uuid``, ``nome`` e
  ``abreviacao`` (seletores).
- ``LaboratorioSerializer``: laboratório completo (exceto ``id``), com os
  ``contatos`` serializados por ``ContatoSimplesSerializer``.
- ``LaboratorioSimplesFiltroSerializer``: ``nome`` e ``cnpj`` (filtros).
- ``LaboratorioCredenciadoSimplesSerializer``: ``uuid`` e ``nome``
  (laboratórios credenciados).

serializer\_create
~~~~~~~~~~~~~~~~~~

.. automodule:: src.pre_recebimento.qualidade.api.serializers.serializer_create
   :members:
   :show-inheritance:

Serializadores de entrada:

- ``LaboratorioCreateSerializer``: criação/atualização — exige os dados
  cadastrais (``nome``, ``cnpj``, ``cep``, ``logradouro``, ``numero``,
  ``bairro``, ``cidade``, ``estado``, ``credenciado``) e a lista de
  ``contatos``. O ``nome`` é normalizado em maiúsculas. Na atualização, os
  contatos existentes são excluídos e recriados.
- ``TipoEmbalagemQldCreateSerializer``: criação/atualização — exige
  ``nome`` e ``abreviacao``, ambos normalizados em maiúsculas.
