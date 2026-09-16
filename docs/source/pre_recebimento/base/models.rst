models
======

.. automodule:: src.pre_recebimento.base.models
   :members:
   :show-inheritance:
   :exclude-members:
      UnidadeMedida,
      DoesNotExist,
      MultipleObjectsReturned

UnidadeMedida
-------------

Unidade de medida utilizada nas quantidades de pré-recebimento
(cronogramas, fichas técnicas e documentos de recebimento). O ``nome`` é
armazenado sempre em letras maiúsculas e a ``abreviacao`` sempre em
letras minúsculas — normalização aplicada no ``save`` e validada no
serializer de criação.

Regras de negócio:

- ``unique_together`` em ``nome``: não podem existir duas unidades com o
  mesmo nome.
- ``save`` normaliza ``nome`` para maiúsculas e ``abreviacao`` para
  minúsculas.
- O serializer de criação rejeita nomes que não estejam em maiúsculas
  ("O campo deve conter apenas letras maiúsculas.") e abreviações que não
  estejam em minúsculas ("O campo deve conter apenas letras minúsculas.").

.. autoclass:: UnidadeMedida
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, abreviacao, criado_em, get_next_by_criado_em, get_previous_by_criado_em, id, nome, objects, save, uuid

   .. attribute:: id
      :type: int

      **Descrição:**
      Chave primária inteira criada automaticamente pelo Django.

   .. attribute:: uuid
      :type: uuid.UUID

      **Origem:**
      ``dados_comuns/behaviors.py`` (``TemChaveExterna``)

      **Descrição:**
      Identificador externo único da unidade de medida.

   .. attribute:: nome
      :type: str

      **Origem:**
      ``dados_comuns/behaviors.py`` (``Nomeavel``)

      **Descrição:**
      Nome da unidade de medida (ex.: ``KG``, ``TON``). Armazenado sempre
      em letras maiúsculas e único.

   .. attribute:: abreviacao
      :type: str

      **Descrição:**
      Abreviação da unidade de medida (ex.: ``kg``, ``ton``). Armazenada
      sempre em letras minúsculas.

   .. attribute:: criado_em
      :type: datetime.datetime

      **Origem:**
      ``dados_comuns/behaviors.py`` (``CriadoEm``)

      **Descrição:**
      Timestamp preenchido automaticamente na criação do registro.
