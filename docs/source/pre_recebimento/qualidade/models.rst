models
======

.. automodule:: src.pre_recebimento.qualidade.models
   :members:
   :show-inheritance:
   :exclude-members:
      Laboratorio,
      TipoEmbalagemQld,
      DoesNotExist,
      MultipleObjectsReturned

Laboratorio
-----------

Laboratório credenciado que emite laudos de qualidade. Registra os dados
cadastrais (CNPJ, endereço) e se o laboratório está credenciado
(``credenciado``). Apenas laboratórios credenciados são listados no
endpoint ``lista-laboratorios-credenciados``, usado na seleção de
laboratório dos documentos de recebimento.

Regras de negócio:

- ``nome`` é único e normalizado em letras maiúsculas (``CaixaAltaNomeForm``
  no admin e ``create``/``update`` do serializer).
- ``cnpj`` possui validador ``MinLengthValidator(14)`` (apenas dígitos).
- Os contatos são gerenciados via relação M:N com ``dados_comuns.Contato``
  e substituídos integralmente na atualização via API.

.. autoclass:: Laboratorio
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, alterado_em, bairro, cep, cidade, cnpj, complemento, contatos, credenciado, criado_em, estado, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, id, logradouro, nome, numero, objects, uuid

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
      Identificador externo único do laboratório.

   .. attribute:: nome
      :type: str

      **Descrição:**
      Nome do laboratório. Único e normalizado em letras maiúsculas.

   .. attribute:: cnpj
      :type: str

      **Descrição:**
      CNPJ do laboratório (somente dígitos, 14 posições). Obrigatório na
      criação via API.

   .. attribute:: cep
      :type: str

      **Descrição:**
      CEP do laboratório (somente dígitos, 8 posições).

   .. attribute:: logradouro
      :type: str

      **Descrição:**
      Logradouro do endereço do laboratório.

   .. attribute:: numero
      :type: str

      **Descrição:**
      Número do endereço do laboratório.

   .. attribute:: complemento
      :type: str

      **Descrição:**
      Complemento do endereço do laboratório.

   .. attribute:: bairro
      :type: str

      **Descrição:**
      Bairro do endereço do laboratório.

   .. attribute:: cidade
      :type: str

      **Descrição:**
      Cidade do endereço do laboratório.

   .. attribute:: estado
      :type: str

      **Descrição:**
      Estado do endereço do laboratório.

   .. attribute:: credenciado
      :type: bool

      **Descrição:**
      Indica se o laboratório está credenciado. Apenas laboratórios
      credenciados são exibidos no endpoint
      ``lista-laboratorios-credenciados``.

   .. attribute:: contatos
      :type: django.db.models.Manager

      **Descrição:**
      Relação M:N com ``dados_comuns.Contato`` (``blank=True``). Contatos
      do laboratório (telefones, e-mails).

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

TipoEmbalagemQld
----------------

Tipo de embalagem (qualidade) utilizado em cronogramas de entrega.
Representa o tipo de embalagem secundária registrado no controle de
qualidade e referenciado pelos cronogramas (campo
``tipo_embalagem_secundaria`` de :class:`Cronograma
<src.pre_recebimento.cronograma_entrega.models.Cronograma>`).

Regras de negócio:

- ``nome`` é único e normalizado em letras maiúsculas (admin via
  ``CaixaAltaNomeForm`` e serializer de criação).
- ``abreviacao`` também é normalizada em letras maiúsculas na criação via
  API.

.. autoclass:: TipoEmbalagemQld
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, abreviacao, alterado_em, criado_em, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, id, nome, objects, uuid

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
      Identificador externo único do tipo de embalagem.

   .. attribute:: nome
      :type: str

      **Descrição:**
      Nome do tipo de embalagem (ex.: ``SACO PLASTICO``). Único e
      normalizado em letras maiúsculas.

   .. attribute:: abreviacao
      :type: str

      **Descrição:**
      Abreviação do tipo de embalagem. Normalizada em letras maiúsculas.

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
