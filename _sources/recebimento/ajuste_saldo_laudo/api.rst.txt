api
===

.. automodule:: src.recebimento.ajuste_saldo_laudo.api
   :members:
   :show-inheritance:

A API do submódulo expõe o endpoint ``/ajuste-saldo-laudo/`` (basename
``ajuste-saldo-laudo``), restrito ao perfil ``DILOG_QUALIDADE``:

- ``GET /ajuste-saldo-laudo/`` — listagem paginada
  (``DefaultPagination``) com filtros (``AjusteSaldoFilter``).
- ``POST /ajuste-saldo-laudo/`` — criação de um ajuste (valida contra o
  saldo disponível do laudo).
- ``GET /ajuste-saldo-laudo/<uuid>/`` — detalhe de um ajuste.
- ``PATCH /ajuste-saldo-laudo/<uuid>/`` — atualização da quantidade
  descontada.
- ``DELETE /ajuste-saldo-laudo/<uuid>/`` — exclusão.
- ``GET /ajuste-saldo-laudo/cronogramas-mensal-com-documentos/`` — lista
  os cronogramas mensais que possuem documentos de recebimento.
- ``GET /ajuste-saldo-laudo/documentos-do-cronograma/?cronograma_uuid={uuid}``
  — lista os documentos de recebimento de um cronograma para ajuste de
  saldo.

viewsets
--------

.. automodule:: src.recebimento.ajuste_saldo_laudo.api.viewsets
   :members:
   :show-inheritance:

``AjusteSaldoModelViewSet`` (``ModelViewSet`` com
``ViewSetActionPermissionMixin``):

- **Permissões**: ``UsuarioEhDilogQualidade`` (classe e ações
  ``cronogramas_mensal_com_documentos`` e ``documentos_do_cronograma``).
- **Queryset**: ajustes com ``select_related`` (documento, cronograma,
  empresa e ficha técnica/produto), ordenados por ``-criado_em``.
- **Serializadores**: ``create`` → ``AjusteSaldoCreateSerializer``;
  ``partial_update`` → ``AjusteSaldoUpdateSerializer``; ``retrieve`` →
  ``AjusteSaldoDetalharSerializer``; listagem → ``AjusteSaldoListagemSerializer``.

Ações:

- ``create`` (POST): cria um ajuste validando a quantidade contra o saldo
  disponível.
- ``list`` (GET): lista os ajustes paginados com filtros.
- ``retrieve`` (GET ``{uuid}``): detalha um ajuste (``404`` se não
  encontrado).
- ``partial_update`` (PATCH ``{uuid}``): atualiza a quantidade descontada.
- ``cronogramas_mensal_com_documentos`` (GET
  ``cronogramas-mensal-com-documentos``): lista os cronogramas mensais com
  documentos de recebimento (``CronogramaMensalAssinadoSerializer``).
- ``documentos_do_cronograma`` (GET ``documentos-do-cronograma``): lista os
  documentos de um cronograma (``cronograma_uuid`` obrigatório — ``400``
  sem o parâmetro, ``404`` para cronograma inexistente).

filters
-------

.. automodule:: src.recebimento.ajuste_saldo_laudo.api.filters
   :members:
   :show-inheritance:

``AjusteSaldoFilter`` filtra por ``numero_cronograma`` (``icontains``),
``nome_empresa`` (nome fantasia, ``icontains``) e ``nome_produto``
(``icontains``), todos derivados do documento de recebimento.

serializers
~~~~~~~~~~~

.. automodule:: src.recebimento.ajuste_saldo_laudo.api.serializers.serializers
   :members:
   :show-inheritance:

Serializadores de saída:

- ``AjusteSaldoDetalharSerializer``: detalhe — número do cronograma, número
  do laudo, unidade de medida e quantidade descontada.
- ``AjusteSaldoListagemSerializer``: linha da listagem — número do
  cronograma, produto, fornecedor, número do laudo, unidade de medida e
  quantidade descontada (somente leitura).

serializer\_create
~~~~~~~~~~~~~~~~~~

.. automodule:: src.recebimento.ajuste_saldo_laudo.api.serializers.serializer_create
   :members:
   :show-inheritance:

Serializadores de entrada:

- ``AjusteSaldoCreateSerializer``: criação — ``documento_recebimento``
  (uuid) e ``quantidade_descontada`` obrigatórios. Validações:
  (1) quantidade a descontar obrigatória ("Quantidade a descontar é
  obrigatória."); (2) quantidade descontada não pode ser maior que o saldo
  disponível ("Quantidade descontada maior que saldo disponível.").
- ``AjusteSaldoUpdateSerializer``: atualização — nova
  ``quantidade_descontada`` obrigatória; o saldo após o desconto não pode
  ser menor que zero ("Saldo após desconto menor que 0").
