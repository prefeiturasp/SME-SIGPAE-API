models
======

.. automodule:: src.pre_recebimento.ficha_tecnica.models
   :members:
   :show-inheritance:
   :exclude-members:
      FabricanteFichaTecnica,
      FichaTecnicaDoProduto,
      InformacoesNutricionaisFichaTecnica,
      AnaliseFichaTecnica,
      DoesNotExist,
      MultipleObjectsReturned

FabricanteFichaTecnica
----------------------

Armazena os dados do fabricante (e do envasador/distribuidor) específicos
de uma ficha técnica. Diferente do cadastro global de
:class:`Fabricante <src.produto.models.Fabricante>`, estes dados são
"congelados" na ficha no momento do cadastro, podendo divergir do
cadastro mestre (CNPJ, endereço, contato, etc.).

A mesma entidade é usada tanto para o campo ``fabricante`` quanto para o
campo ``envasador_distribuidor`` da ficha (duas instâncias distintas).

.. autoclass:: FabricanteFichaTecnica
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, alterado_em, bairro, cep, cidade, cnpj, complemento, criado_em, email, endereco, estado, fabricante, fabricante_id, fichas_tecnicas_como_envasador_distribuidor, fichas_tecnicas_como_fabricante, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, id, numero, objects, telefone, uuid

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
      Identificador externo único do registro de fabricante da ficha.

   .. attribute:: fabricante
      :type: produto.Fabricante | None

      **Descrição:**
      Referência opcional ao cadastro global de fabricante
      (``on_delete=SET_NULL``). Quando presente, o nome exibido vem deste
      cadastro; os demais dados (endereço, contato) ficam neste modelo.

   .. attribute:: cnpj
      :type: str

      **Descrição:**
      CNPJ do fabricante/envasador (até 14 dígitos, mínimo 14 com
      ``MinLengthValidator``). Aceita apenas números (sem máscara).

   .. attribute:: cep
      :type: str

      **Descrição:**
      CEP (8 dígitos, sem máscara).

   .. attribute:: endereco
      :type: str

      **Descrição:**
      Logradouro do endereço.

   .. attribute:: numero
      :type: str

      **Descrição:**
      Número do endereço.

   .. attribute:: complemento
      :type: str

      **Descrição:**
      Complemento do endereço (ex.: bloco, andar, sala).

   .. attribute:: bairro
      :type: str

      **Descrição:**
      Bairro.

   .. attribute:: cidade
      :type: str

      **Descrição:**
      Cidade.

   .. attribute:: estado
      :type: str

      **Descrição:**
      Estado (UF). Utilizado no filtro do admin por estado.

   .. attribute:: email
      :type: str

      **Descrição:**
      E-mail de contato (``EmailField``).

   .. attribute:: telefone
      :type: str

      **Descrição:**
      Telefone de contato (até 13 caracteres, mínimo 8 com
      ``MinLengthValidator``).

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

FichaTecnicaDoProduto
---------------------

Modelo central do submódulo. Representa a ficha técnica de um produto
alimentício: especificações do produto, fabricante/envasador, tabela
nutricional, conservação, transporte, embalagens, rotulagem, responsável
técnico e modo de preparo.

O número da ficha é gerado automaticamente após a primeira gravação no
formato ``FTXXX`` (``XXX`` é o PK preenchido com zeros), via signal
``post_save``.

A ficha possui um **workflow de aprovação**
(``FichaTecnicaDoProdutoWorkflow``) com os estados:

- ``RASCUNHO`` (Rascunho) — estado inicial; cadastro parcial pelo fornecedor.
- ``ENVIADA_PARA_ANALISE`` (Enviada para Análise) — enviada pelo fornecedor para a GPCODAE (transição ``inicia_fluxo``).
- ``APROVADA`` (Aprovada) — aprovada pela GPCODAE (transição ``gpcodae_aprova``).
- ``ENVIADA_PARA_CORRECAO`` (Enviada para Correção) — devolvida ao fornecedor com correções (transição ``gpcodae_envia_para_correcao``).

O fluxo também permite: ``fornecedor_corrige`` (de ``ENVIADA_PARA_CORRECAO``
de volta para ``ENVIADA_PARA_ANALISE``) e ``fornecedor_atualiza`` (de
``APROVADA`` para ``ENVIADA_PARA_ANALISE`` — atualização de uma ficha já
aprovada). Cada transição gera um ``LogSolicitacoesUsuario`` do tipo
``FICHA_TECNICA_DO_PRODUTO`` e o envio para análise dispara e-mail de
notificação.

Regras de negócio por categoria (aplicadas nos serializadores/validators):

- **FLV** (hortifrutigranjeiros): exige ``organico`` e ``especie_variedade``.
- **Perecíveis**: exige ``organico``, ``prazo_validade_descongelamento``,
  ``temperatura_congelamento``, ``temperatura_veiculo``,
  ``condicoes_de_transporte`` e ``variacao_percentual``.
- **Não perecíveis**: exige ``organico`` e ``produto_eh_liquido``.

Campos dependentes obrigatórios:

- ``organico = True`` exige ``mecanismo_controle`` (CERTIFICACAO/OPAC/OCS).
- ``alergenicos = True`` exige ``ingredientes_alergenicos``.
- ``lactose = True`` exige ``lactose_detalhe``.
- ``produto_eh_liquido = True`` exige ``volume_embalagem_primaria`` e
  ``unidade_medida_volume_primaria``.

As declarações de conformidade com o Anexo I do Edital
(``embalagens_de_acordo_com_anexo`` e ``rotulo_legivel``) devem ser
marcadas como ``True`` na criação (validadas no serializador de criação).

.. autoclass:: FichaTecnicaDoProduto
   :members:
   :show-inheritance:
   :exclude-members: ALIMENTACAO_ESCOLAR, ARMAZEM, CATEGORIA_CHOICES, CATEGORIA_FLV, CATEGORIA_NAO_PERECIVEIS, CATEGORIA_PERECIVEIS, DoesNotExist, LEVE_LEITE, MECANISMO_CERTIFICACAO, MECANISMO_CONTROLE_CHOICES, MECANISMO_OCS, MECANISMO_OPAC, MultipleObjectsReturned, PONTO_A_PONTO, PROGRAMA_CHOICES, TIPO_ENTREGA_CHOICES, alergenicos, alterado_em, analises, arquivo, categoria, componentes_produto, condicoes_de_conservacao, condicoes_de_transporte, criado_em, cronograma, cronograma_set, embalagem_primaria, embalagem_secundaria, embalagens_de_acordo_com_anexo, empresa, empresa_id, envasador_distribuidor, envasador_distribuidor_id, especie_variedade, fabricante, fabricante_id, fornecedor_atualiza, fornecedor_corrige, gerar_numero_ficha_tecnica, get_categoria_display, get_mecanismo_controle_display, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, get_programa_display, get_status_display, get_tipo_entrega_display, gluten, gpcodae_aprova, gpcodae_envia_para_correcao, habilitacao, id, inicia_fluxo, informacoes_adicionais, informacoes_nutricionais, ingredientes_alergenicos, lactose, lactose_detalhe, layout_embalagem, log_mais_recente, logs, marca, marca_id, material_embalagem_primaria, mecanismo_controle, modo_de_preparo, nome_responsavel_tecnico, numero, numero_registro, numero_registro_orgao, objects, organico, peso_embalagem_primaria_vazia, peso_embalagem_secundaria_vazia, peso_liquido_embalagem_primaria, peso_liquido_embalagem_secundaria, ponto_a_ponto, porcao, prazo_validade, prazo_validade_descongelamento, pregao_chamada_publica, produto, produto_eh_liquido, produto_id, programa, questoes_conferencia, rotulo_legivel, salvar_log_ficha_tecnica_cadastrada, salvar_log_transicao, sistema_vedacao_embalagem_secundaria, status, temperatura_congelamento, temperatura_veiculo, tipo_entrega, unidade_medida_caseira, unidade_medida_porcao, unidade_medida_porcao_id, unidade_medida_primaria, unidade_medida_primaria_id, unidade_medida_primaria_vazia, unidade_medida_primaria_vazia_id, unidade_medida_secundaria, unidade_medida_secundaria_id, unidade_medida_secundaria_vazia, unidade_medida_secundaria_vazia_id, unidade_medida_volume_primaria, unidade_medida_volume_primaria_id, uuid, valor_unidade_caseira, variacao_percentual, volume_embalagem_primaria, workflow_class

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
      Identificador externo único da ficha, usado em integrações e endpoints.

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
      Número da ficha técnica, único, gerado automaticamente após a criação
      no formato ``FTXXX`` (``XXX`` = PK com zeros à esquerda).

   .. attribute:: produto
      :type: produto.NomeDeProdutoEdital

      **Descrição:**
      Produto (nome do produto do edital) ao qual a ficha se refere.
      Obrigatório com ``on_delete=PROTECT``.

   .. attribute:: marca
      :type: produto.Marca | None

      **Descrição:**
      Marca do produto (opcional, ``on_delete=PROTECT``).

   .. attribute:: categoria
      :type: str

      **Descrição:**
      Categoria do produto. Valores possíveis: ``PERECIVEIS`` (Perecíveis),
      ``NAO_PERECIVEIS`` (Não Perecíveis) e ``FLV``. Define o conjunto de
      campos obrigatórios da ficha.

   .. attribute:: tipo_entrega
      :type: str

      **Descrição:**
      Tipo de entrega. Valores possíveis: ``ARMAZEM`` (Armazém, default) e
      ``PONTO_A_PONTO`` (Ponto a Ponto). Fichas ``FLV`` + ``PONTO_A_PONTO``
      têm regras de análise simplificadas (não exigem os blocos de
      informações nutricionais, conservação, armazenamento, embalagem/
      rotulagem e modo de preparo).

   .. attribute:: programa
      :type: str

      **Descrição:**
      Programa de alimentação. Valores possíveis: ``LEVE_LEITE`` (Leve
      Leite) e ``ALIMENTACAO_ESCOLAR`` (Alimentação Escolar, default).

   .. attribute:: pregao_chamada_publica
      :type: str

      **Descrição:**
      Número do pregão eletrônico / chamada pública ao qual o produto está
      vinculado.

   .. attribute:: empresa
      :type: terceirizada.Terceirizada | None

      **Descrição:**
      Empresa fornecedora responsável pela ficha (``on_delete=CASCADE``).
      Utilizada para filtrar as fichas visíveis para usuários fornecedores.

   .. attribute:: fabricante
      :type: FabricanteFichaTecnica | None

      **Descrição:**
      Dados do fabricante específicos da ficha (``on_delete=CASCADE``).

   .. attribute:: envasador_distribuidor
      :type: FabricanteFichaTecnica | None

      **Descrição:**
      Dados do envasador/distribuidor específicos da ficha
      (``on_delete=CASCADE``).

   .. attribute:: prazo_validade
      :type: str

      **Descrição:**
      Prazo de validade do produto.

   .. attribute:: numero_registro
      :type: str

      **Descrição:**
      Número do registro do rótulo.

   .. attribute:: organico
      :type: bool | None

      **Descrição:**
      Indica se o produto é orgânico. Quando ``True``, exige
      ``mecanismo_controle``.

   .. attribute:: mecanismo_controle
      :type: str

      **Descrição:**
      Mecanismo de controle de produto orgânico. Valores possíveis:
      ``CERTIFICACAO`` (Certificação), ``OPAC`` e ``OCS``. Obrigatório
      quando ``organico = True``.

   .. attribute:: especie_variedade
      :type: str

      **Descrição:**
      Espécie ou variedade cultivada. Obrigatório para fichas ``FLV``.

   .. attribute:: componentes_produto
      :type: str

      **Descrição:**
      Componentes do produto (texto).

   .. attribute:: alergenicos
      :type: bool | None

      **Descrição:**
      Indica se o produto pode conter alergênicos. Quando ``True``, exige
      ``ingredientes_alergenicos``.

   .. attribute:: ingredientes_alergenicos
      :type: str

      **Descrição:**
      Ingredientes/aditivos alergênicos. Obrigatório quando
      ``alergenicos = True``.

   .. attribute:: gluten
      :type: bool | None

      **Descrição:**
      Indica se o produto contém glúten.

   .. attribute:: lactose
      :type: bool | None

      **Descrição:**
      Indica se o produto contém lactose. Quando ``True``, exige
      ``lactose_detalhe``.

   .. attribute:: lactose_detalhe
      :type: str

      **Descrição:**
      Detalhamento sobre a lactose. Obrigatório quando ``lactose = True``.

   .. attribute:: porcao
      :type: str | None

      **Descrição:**
      Porção (quantidade de referência para a tabela nutricional).

   .. attribute:: unidade_medida_porcao
      :type: base.UnidadeMedida | None

      **Descrição:**
      Unidade de medida da porção (ex.: g, ml).

   .. attribute:: valor_unidade_caseira
      :type: str | None

      **Descrição:**
      Medida caseira correspondente à porção (ex.: "1 colher de sopa").

   .. attribute:: unidade_medida_caseira
      :type: str

      **Descrição:**
      Unidade de medida caseira (texto livre).

   .. attribute:: informacoes_nutricionais
      :type: django.db.models.QuerySet[InformacoesNutricionaisFichaTecnica]

      **Descrição:**
      Relação reversa 1:N com :class:`InformacoesNutricionaisFichaTecnica`.
      Lista os itens da tabela nutricional da ficha (cada um com quantidade
      por 100 g, por porção e valor diário).

   .. attribute:: prazo_validade_descongelamento
      :type: str

      **Descrição:**
      Prazo de validade após o descongelamento, mantido sob refrigeração.
      Obrigatório para produtos perecíveis.

   .. attribute:: condicoes_de_conservacao
      :type: str

      **Descrição:**
      Condições de conservação e prazo máximo para consumo após a abertura
      da embalagem primária.

   .. attribute:: temperatura_congelamento
      :type: float | None

      **Descrição:**
      Temperatura de congelamento do produto. Obrigatório para perecíveis.

   .. attribute:: temperatura_veiculo
      :type: float | None

      **Descrição:**
      Temperatura interna do veículo para transporte. Obrigatório para
      perecíveis.

   .. attribute:: condicoes_de_transporte
      :type: str

      **Descrição:**
      Condições de transporte do produto. Obrigatório para perecíveis.

   .. attribute:: embalagem_primaria
      :type: str

      **Descrição:**
      Descrição da embalagem primária do produto.

   .. attribute:: embalagem_secundaria
      :type: str

      **Descrição:**
      Descrição da embalagem secundária do produto.

   .. attribute:: embalagens_de_acordo_com_anexo
      :type: bool | None

      **Descrição:**
      Declaração de que as embalagens primária e secundária estão de acordo
      com as especificações do Anexo I do Edital. Deve ser marcada como
      ``True`` na criação (validação no serializador).

   .. attribute:: material_embalagem_primaria
      :type: str

      **Descrição:**
      Material da embalagem primária.

   .. attribute:: produto_eh_liquido
      :type: bool | None

      **Descrição:**
      Indica se o produto é líquido. Quando ``True``, exige
      ``volume_embalagem_primaria`` e ``unidade_medida_volume_primaria``.
      Obrigatório para não perecíveis.

   .. attribute:: volume_embalagem_primaria
      :type: float | None

      **Descrição:**
      Volume do produto na embalagem primária.

   .. attribute:: unidade_medida_volume_primaria
      :type: base.UnidadeMedida | None

      **Descrição:**
      Unidade de medida do volume da embalagem primária.

   .. attribute:: peso_liquido_embalagem_primaria
      :type: float | None

      **Descrição:**
      Peso líquido do produto na embalagem primária.

   .. attribute:: unidade_medida_primaria
      :type: base.UnidadeMedida | None

      **Descrição:**
      Unidade de medida do peso líquido da embalagem primária.

   .. attribute:: peso_liquido_embalagem_secundaria
      :type: float | None

      **Descrição:**
      Peso líquido do produto na embalagem secundária.

   .. attribute:: unidade_medida_secundaria
      :type: base.UnidadeMedida | None

      **Descrição:**
      Unidade de medida do peso líquido da embalagem secundária.

   .. attribute:: peso_embalagem_primaria_vazia
      :type: float | None

      **Descrição:**
      Peso da embalagem primária vazia.

   .. attribute:: unidade_medida_primaria_vazia
      :type: base.UnidadeMedida | None

      **Descrição:**
      Unidade de medida do peso da embalagem primária vazia.

   .. attribute:: peso_embalagem_secundaria_vazia
      :type: float | None

      **Descrição:**
      Peso da embalagem secundária vazia.

   .. attribute:: unidade_medida_secundaria_vazia
      :type: base.UnidadeMedida | None

      **Descrição:**
      Unidade de medida do peso da embalagem secundária vazia.

   .. attribute:: variacao_percentual
      :type: float | None

      **Descrição:**
      Variação percentual aceita nos pesos. Obrigatório para perecíveis.

   .. attribute:: sistema_vedacao_embalagem_secundaria
      :type: str

      **Descrição:**
      Sistema de vedação da embalagem secundária.

   .. attribute:: rotulo_legivel
      :type: bool | None

      **Descrição:**
      Declaração de que o rótulo da embalagem primária (e secundária, se
      for o caso) conterá, de forma legível e indelével, todas as
      informações solicitadas no Anexo I do Edital. Deve ser marcada como
      ``True`` na criação.

   .. attribute:: nome_responsavel_tecnico
      :type: str

      **Descrição:**
      Nome completo do responsável técnico.

   .. attribute:: habilitacao
      :type: str

      **Descrição:**
      Habilitação do responsável técnico.

   .. attribute:: numero_registro_orgao
      :type: str

      **Descrição:**
      Número do registro em órgão competente do responsável técnico.

   .. attribute:: arquivo
      :type: django.db.models.fields.files.FieldFile | None

      **Descrição:**
      Arquivo PDF da ficha técnica (``upload_to="fichas_tecnicas"``), com
      validação de extensão PDF e tamanho máximo de 10 MB. Recebido como
      base64 pela API e convertido para ``ContentFile`` no helper de criação.

   .. attribute:: modo_de_preparo
      :type: str

      **Descrição:**
      Modo de preparo do produto.

   .. attribute:: informacoes_adicionais
      :type: str

      **Descrição:**
      Informações adicionais da ficha.

   .. attribute:: status
      :type: str

      **Origem:**
      ``dados_comuns/fluxo_status.py`` (``FichaTecnicaDoProdutoWorkflow``)

      **Descrição:**
      Status atual do workflow. Estados possíveis: ``RASCUNHO``,
      ``ENVIADA_PARA_ANALISE``, ``APROVADA`` e ``ENVIADA_PARA_CORRECAO``.

   .. attribute:: criado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``CriadoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na criação da ficha.

   .. attribute:: alterado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemAlteradoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na última alteração da ficha.

   .. attribute:: logs
      :type: list[LogSolicitacoesUsuario]

      **Origem:**
      ``dados_comuns/behaviors.py`` (``Logs``)

      **Descrição:**
      Lista dos registros de log de transições de status da ficha,
      ordenados por ``criado_em``.

   .. attribute:: log_mais_recente
      :type: LogSolicitacoesUsuario | None

      **Origem:**
      ``dados_comuns/behaviors.py`` (``Logs``)

      **Descrição:**
      Último registro de log de transição de status da ficha. Usado nos
      serializadores de painel/detalhe para exibir a data/hora da última
      movimentação.

   .. attribute:: analises
      :type: django.db.models.QuerySet[AnaliseFichaTecnica]

      **Descrição:**
      Relação reversa 1:N com :class:`AnaliseFichaTecnica`. Lista as
      análises da GPCODAE realizadas sobre a ficha, ordenáveis por
      ``criado_em`` (a análise vigente é a última).

   .. attribute:: cronograma
      :type: django.db.models.QuerySet[Cronograma]

      **Descrição:**
      Relação reversa com :class:`Cronograma
      <src.pre_recebimento.cronograma_entrega.models.Cronograma>` via o
      campo ``Cronograma.ficha_tecnica`` (definido sem ``related_name``).

      ``cronograma`` é o **nome de consulta (query name)** da relação —
      usado em filtros ORM como ``cronograma__isnull`` (endpoint
      ``lista-simples-sem-cronograma``). O accessor padrão de instância é
      ``cronograma_set``.

   .. attribute:: layout_embalagem
      :type: layout_embalagem.LayoutDeEmbalagem | None

      **Descrição:**
      Relação reversa 1:1 com :class:`LayoutDeEmbalagem
      <src.pre_recebimento.layout_embalagem.models.LayoutDeEmbalagem>`.
      Layout de embalagem vinculado à ficha, quando existir.

   .. attribute:: questoes_conferencia
      :type: recebimento.QuestoesPorProduto | None

      **Descrição:**
      Relação reversa 1:1 com :class:`QuestoesPorProduto
      <src.recebimento.models.QuestoesPorProduto>`. Questões de conferência
      de qualidade vinculadas à ficha, quando existirem.

   .. attribute:: ponto_a_ponto
      :type: bool

      **Descrição:**
      Propriedade que indica se a ficha é do tipo Ponto a Ponto (FLV).
      Retorna ``True`` quando ``tipo_entrega = PONTO_A_PONTO``. Usada nos
      serializadores e na lógica de análise: fichas FLV ponto a ponto não
      exigem os blocos de informações nutricionais, conservação,
      armazenamento, embalagem/rotulagem e modo de preparo.

   .. attribute:: salvar_log_transicao
      :type: Callable

      **Descrição:**
      Registra no log uma transição de status da ficha, criando um
      ``LogSolicitacoesUsuario`` com o tipo ``FICHA_TECNICA_DO_PRODUTO``.

InformacoesNutricionaisFichaTecnica
-----------------------------------

Item da tabela nutricional de uma ficha técnica. Vincula uma
:class:`InformacaoNutricional <src.produto.models.InformacaoNutricional>`
(ex.: "Valor energético", "Carboidratos") aos valores declarados por
100 g, por porção e o valor diário (percentual).

.. autoclass:: InformacoesNutricionaisFichaTecnica
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, ficha_tecnica, ficha_tecnica_id, id, informacao_nutricional, informacao_nutricional_id, objects, quantidade_por_100g, quantidade_porcao, uuid, valor_diario

   .. attribute:: id
      :type: int

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemChaveExterna``)

      **Descrição:**
      Identificador externo único do item nutricional.

   .. attribute:: ficha_tecnica
      :type: FichaTecnicaDoProduto

      **Descrição:**
      Ficha técnica à qual o item pertence (``on_delete=CASCADE``).

   .. attribute:: informacao_nutricional
      :type: produto.InformacaoNutricional

      **Descrição:**
      Informação nutricional de referência (nome do nutriente/informação),
      com ``on_delete=DO_NOTHING``.

   .. attribute:: quantidade_por_100g
      :type: str

      **Descrição:**
      Quantidade do nutriente por 100 g (texto, ex.: "12,5 g").

   .. attribute:: quantidade_porcao
      :type: str

      **Descrição:**
      Quantidade do nutriente por porção (texto).

   .. attribute:: valor_diario
      :type: str

      **Descrição:**
      Percentual do valor diário de referência (texto, ex.: "5%").

AnaliseFichaTecnica
-------------------

Registro da análise da ficha técnica pela GPCODAE. A análise é dividida
em blocos ("collapses") de conferência, cada um com um campo
``*_conferido`` (bool) e um campo ``*_correcoes`` (texto com as
observações/correções exigidas quando o bloco não foi aprovado).

Blocos de conferência:

- ``fabricante_envasador`` — fabricante e envasador/distribuidor.
- ``detalhes_produto`` — detalhes do produto (validade, orgânico, componentes, alergênicos, glúten, lactose).
- ``informacoes_nutricionais`` — tabela nutricional.
- ``conservacao`` — conservação e descongelamento (perecíveis).
- ``temperatura_e_transporte`` — temperaturas e transporte (perecíveis).
- ``armazenamento`` — embalagens (primária/secundária).
- ``embalagem_e_rotulagem`` — embalagens, pesos, vedações e rotulagem.
- ``responsavel_tecnico`` — responsável técnico e arquivo.
- ``modo_preparo`` — modo de preparo.
- ``outras_informacoes`` — informações adicionais (só booleano).

Regras de negócio da análise:

- A propriedade :attr:`aprovada` computa se todos os blocos necessários
  foram conferidos sem correções. Para fichas ``FLV`` ponto a ponto, os
  blocos de informações nutricionais, conservação, armazenamento,
  embalagem/rotulagem e modo de preparo são ignorados.
- Ao salvar uma análise com ``aprovada = True`` a ficha é aprovada
  (``gpcodae_aprova``); caso contrário é enviada para correção
  (``gpcodae_envia_para_correcao``).
- Na análise, um bloco marcado ``*_conferido = False`` exige
  ``*_correcoes`` preenchido; um bloco ``True`` exige ``*_correcoes`` vazio.

.. autoclass:: AnaliseFichaTecnica
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, aprovada, alterado_em, armazenamento_conferido, armazenamento_correcoes, conservacao_conferido, conservacao_correcoes, criado_em, criado_por, criado_por_id, detalhes_produto_conferido, detalhes_produto_correcoes, embalagem_e_rotulagem_conferido, embalagem_e_rotulagem_correcoes, fabricante_envasador_conferido, fabricante_envasador_correcoes, ficha_tecnica, ficha_tecnica_id, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, id, informacoes_nutricionais_conferido, informacoes_nutricionais_correcoes, modo_preparo_conferido, modo_preparo_correcoes, objects, outras_informacoes_conferido, responsavel_tecnico_conferido, responsavel_tecnico_correcoes, temperatura_e_transporte_conferido, temperatura_e_transporte_correcoes, uuid

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
      Identificador externo único da análise.

   .. attribute:: ficha_tecnica
      :type: FichaTecnicaDoProduto

      **Descrição:**
      Ficha técnica analisada (``on_delete=CASCADE``). Uma ficha pode ter
      várias análises ao longo do tempo (a vigente é a última por
      ``criado_em``).

   .. attribute:: fabricante_envasador_conferido
      :type: bool | None

      **Descrição:**
      Bloco "Fabricante/Envasador" conferido (sem correções pendentes).

   .. attribute:: fabricante_envasador_correcoes
      :type: str

      **Descrição:**
      Correções exigidas no bloco "Fabricante/Envasador".

   .. attribute:: detalhes_produto_conferido
      :type: bool | None

      **Descrição:**
      Bloco "Detalhes do Produto" conferido.

   .. attribute:: detalhes_produto_correcoes
      :type: str

      **Descrição:**
      Correções exigidas no bloco "Detalhes do Produto".

   .. attribute:: informacoes_nutricionais_conferido
      :type: bool | None

      **Descrição:**
      Bloco "Informações Nutricionais" conferido. Ignorado para fichas
      FLV ponto a ponto.

   .. attribute:: informacoes_nutricionais_correcoes
      :type: str

      **Descrição:**
      Correções exigidas no bloco "Informações Nutricionais".

   .. attribute:: conservacao_conferido
      :type: bool | None

      **Descrição:**
      Bloco "Conservação" conferido (perecíveis).

   .. attribute:: conservacao_correcoes
      :type: str

      **Descrição:**
      Correções exigidas no bloco "Conservação".

   .. attribute:: temperatura_e_transporte_conferido
      :type: bool | None

      **Descrição:**
      Bloco "Temperatura e Transporte" conferido (perecíveis). Aceita
      ``None`` na validação de aprovação.

   .. attribute:: temperatura_e_transporte_correcoes
      :type: str

      **Descrição:**
      Correções exigidas no bloco "Temperatura e Transporte".

   .. attribute:: armazenamento_conferido
      :type: bool | None

      **Descrição:**
      Bloco "Armazenamento" conferido.

   .. attribute:: armazenamento_correcoes
      :type: str

      **Descrição:**
      Correções exigidas no bloco "Armazenamento".

   .. attribute:: embalagem_e_rotulagem_conferido
      :type: bool | None

      **Descrição:**
      Bloco "Embalagem e Rotulagem" conferido.

   .. attribute:: embalagem_e_rotulagem_correcoes
      :type: str

      **Descrição:**
      Correções exigidas no bloco "Embalagem e Rotulagem".

   .. attribute:: responsavel_tecnico_conferido
      :type: bool | None

      **Descrição:**
      Bloco "Responsável Técnico" conferido.

   .. attribute:: responsavel_tecnico_correcoes
      :type: str

      **Descrição:**
      Correções exigidas no bloco "Responsável Técnico".

   .. attribute:: modo_preparo_conferido
      :type: bool | None

      **Descrição:**
      Bloco "Modo de Preparo" conferido.

   .. attribute:: modo_preparo_correcoes
      :type: str

      **Descrição:**
      Correções exigidas no bloco "Modo de Preparo".

   .. attribute:: outras_informacoes_conferido
      :type: bool | None

      **Descrição:**
      Bloco "Outras Informações" conferido. Não possui campo de correções;
      é sempre exigido ``True`` para a aprovação.

   .. attribute:: criado_por
      :type: perfil.Usuario | None

      **Origem:**
      ``dados_comuns/behaviors.py`` (``CriadoPor``)

      **Descrição:**
      Usuário que realizou a análise.

   .. attribute:: criado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``CriadoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na criação da análise.

   .. attribute:: alterado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemAlteradoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na última alteração da análise.

   .. attribute:: aprovada
      :type: bool

      **Descrição:**
      Propriedade que indica se a análise aprovou a ficha. Todos os blocos
      exigidos devem estar ``True`` e sem correções, com exceção de
      ``temperatura_e_transporte`` (aceita ``None``). Para fichas FLV ponto
      a ponto, os blocos de informações nutricionais, conservação,
      armazenamento, embalagem/rotulagem e modo de preparo são ignorados.
