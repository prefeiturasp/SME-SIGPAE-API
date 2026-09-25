models
======

.. automodule:: src.recebimento.ajuste_saldo_laudo.models
   :members:
   :show-inheritance:
   :exclude-members:
      AjusteSaldo,
      DoesNotExist,
      MultipleObjectsReturned

AjusteSaldo
-----------

Ajuste (desconto) de saldo de um laudo de documento de recebimento.
Registra a ``quantidade_descontada`` de um documento, reduzindo o saldo
disponível do laudo.

Regras de negócio:

- A ``quantidade_descontada`` não pode ser maior que o saldo disponível do
  laudo (validado no ``AjusteSaldoCreateSerializer`` via
  ``calcular_saldo_laudo`` — "Quantidade descontada maior que saldo
  disponível.").
- Na atualização, o saldo após o desconto não pode ser menor que zero
  (``AjusteSaldoUpdateSerializer`` — "Saldo após desconto menor que 0").

.. autoclass:: AjusteSaldo
   :members:
   :show-inheritance:
   :exclude-members: DoesNotExist, MultipleObjectsReturned, alterado_em, criado_em, documento_recebimento, documento_recebimento_id, get_next_by_alterado_em, get_next_by_criado_em, get_previous_by_alterado_em, get_previous_by_criado_em, id, objects, quantidade_descontada, uuid

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
      Identificador externo único do ajuste.

   .. attribute:: documento_recebimento
      :type: DocumentoDeRecebimento

      **Descrição:**
      Documento de recebimento do laudo ajustado (``on_delete=CASCADE``,
      ``related_name="ajustes_saldo"``).

   .. attribute:: quantidade_descontada
      :type: decimal.Decimal

      **Descrição:**
      Quantidade descontada do saldo do laudo (Decimal com até 15 dígitos
      e 2 casas decimais).

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
