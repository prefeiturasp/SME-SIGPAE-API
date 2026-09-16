api
===

.. automodule:: src.pos_recebimento.api
   :members:
   :show-inheritance:

O módulo de API do Pós-Recebimento expõe um único endpoint de criação:

- ``POST /pos-recebimento/termos/`` — criação do Termo de Recebimento
  Definitivo (basename ``termos-recebimento-definitivo``).

O payload de criação espera os uuids de ``empresa``, ``contrato``,
``cronogramas`` (cada um com ``valor_contrato`` e
``quantidade_total_recebida``), ``fiscal_1``, ``fiscal_2``, ``fiscal_3`` e
``texto_termo``. Respostas: ``201`` com o termo serializado, ``400`` com os
erros de validação ou ``403`` para usuários sem permissão.

viewsets
--------

.. automodule:: src.pos_recebimento.api.viewsets
   :members:
   :show-inheritance:

O ``TermoRecebimentoDefinitivoViewSet`` implementa o fluxo "Salvar e
Enviar": a criação é feita em uma única operação e o termo é persistido
com status ``ENVIADO``, independentemente do default do modelo
(``RASCUNHO``). O ``criado_por`` e o ``alterado_por`` são preenchidos com
o usuário autenticado da requisição.

O fluxo de criação:

1. O serializador de criação valida o payload (ver ``serializers_create``).
2. ``perform_create`` retira os cronogramas do ``validated_data``, salva o
   termo com ``status=ENVIADO`` e os usuários da requisição.
3. Para cada item de cronograma é criada uma linha do modelo intermediário
   :class:`~src.pos_recebimento.models.CronogramaTermoRecebimentoDefinitivo`
   com o ``cronograma``, ``valor_contrato`` e ``quantidade_total_recebida``.
4. A resposta ``201`` é montada com o serializador de saída
   (:class:`TermoRecebimentoDefinitivoSerializer
   <src.pos_recebimento.api.serializers.serializers.TermoRecebimentoDefinitivoSerializer>`),
   que já traz empresa, contrato, cronogramas (com valores) e fiscais
   serializados pelos serializers de seus respectivos módulos.

permissions
-----------

.. automodule:: src.pos_recebimento.api.permissions
   :members:
   :show-inheritance:

Permissão ``PermissaoParaCadastrarTermoRecebimentoDefinitivo``: apenas
usuários autenticados, com vínculo atual ativo vinculado à CODAE
(instituição ``Codae``) e cujo perfil do vínculo atual seja
``DILOG_CRONOGRAMA`` ou ``COORDENADOR_CODAE_DILOG_LOGISTICA`` podem acessar
as funcionalidades do Pós-Recebimento.

Além do endpoint de criação de termos, essa mesma permissão protege as
listagens de apoio ao cadastro, implementadas em outros módulos:

- ``GET /terceirizadas/lista-empresas-pos-recebimento/`` — empresas com ao
  menos uma ficha de recebimento "Assinado CODAE".
- ``GET /cronogramas/lista-cronogramas-pos-recebimento/?contrato_id=<uuid>``
  — cronogramas vinculados ao contrato selecionado.
- ``GET /cronogramas/<uuid>/dados-cronograma-pos-recebimento/`` — dados do
  cronograma para preenchimento automático do cadastro.
- ``GET /usuarios/fiscais/`` — usuários com perfil ``DILOG_QUALIDADE`` e
  vínculo ativo para seleção dos fiscais.

services
--------

.. automodule:: src.pos_recebimento.api.services
   :members:
   :show-inheritance:

O ``TermoRecebimentoDefinitivoService`` concentra as regras de negócio do
Pós-Recebimento. Atualmente mantém apenas a regra
``empresa_tem_ficha_assinada``: verifica se a empresa possui ao menos uma
ficha de recebimento com status "Assinado CODAE"
(``FichaDeRecebimentoWorkflow.ASSINADA``), navegando pela relação
``empresa -> cronogramas -> etapas -> ficha de recebimento``.

serializers
~~~~~~~~~~~

.. automodule:: src.pos_recebimento.api.serializers.serializers
   :members:
   :show-inheritance:

Serializadores de saída (somente leitura):

- :class:`CronogramaTermoRecebimentoDefinitivoSerializer`: expõe o
  cronograma (serializado por ``CronogramaSimplesSerializer``), o
  ``valor_contrato`` e a ``quantidade_total_recebida``.
- :class:`TermoRecebimentoDefinitivoSerializer`: serializa o termo com
  empresa (``TerceirizadaSimplesSerializer``), contrato
  (``ContratoSimplesSerializer``), cronogramas (via relação reversa
  ``cronogramas_termo``, cada um com seus valores), fiscais
  (``UsuarioSimplesSerializer``), ``texto_termo``, ``status`` e timestamps
  de criação/alteração. Todos os campos são somente leitura.

serializers\_create
~~~~~~~~~~~~~~~~~~~

.. automodule:: src.pos_recebimento.api.serializers.serializers_create
   :members:
   :show-inheritance:

Serializadores de criação (entrada):

- :class:`CronogramaTermoRecebimentoDefinitivoCreateSerializer`: item de
  cronograma do payload, composto por ``cronograma`` (uuid via
  ``SlugRelatedField``), ``valor_contrato`` e ``quantidade_total_recebida``
  (decimais com até 15 dígitos e 2 casas decimais).
- :class:`TermoRecebimentoDefinitivoCreateSerializer`: serializador
  principal do create. Recebe os uuids de empresa, contrato, cronogramas e
  fiscais e aplica as regras de negócio (na ordem):

  1. **Campos obrigatórios**: ``empresa``, ``contrato``, ``cronogramas``
     (não pode ser vazio — ``allow_empty=False``), ``fiscal_1``,
     ``fiscal_2``, ``fiscal_3`` e ``texto_termo``.
  2. **Empresa com ficha assinada**: a empresa deve possuir ao menos uma
     ficha de recebimento "Assinado CODAE".
  3. **Contrato da empresa**: ``contrato.terceirizada`` deve ser a empresa
     selecionada.
  4. **Cronogramas**: não podem repetir uuid no mesmo payload; cada
     cronograma deve pertencer ao contrato selecionado
     (``cronograma.contrato``) e à empresa selecionada
     (``cronograma.empresa``).
  5. **Fiscais**: cada um deve possuir vínculo ativo com o perfil
     ``DILOG_QUALIDADE``.
  6. **Valores por cronograma**: ``valor_contrato`` e
     ``quantidade_total_recebida`` devem ser maiores que zero.
  7. **Texto do termo**: obrigatório e deve conter conteúdo textual após a
     remoção das tags HTML (``validate_texto_termo``).

  Mensagens de erro padrão por campo não encontrado: "Empresa não
  encontrada.", "Contrato não encontrado.", "Cronograma não encontrado." e
  "Fiscal N não encontrado.".
