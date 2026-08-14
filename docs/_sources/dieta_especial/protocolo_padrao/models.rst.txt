models
======

.. automodule:: src.dieta_especial.protocolo_padrao.models
   :members:
   :show-inheritance:
   :exclude-members:
      Alimento,
      SubstituicaoAlimento,
      AlimentoSubstituto,
      ProtocoloPadraoDietaEspecial,
      SubstituicaoAlimentoProtocoloPadrao,
      DoesNotExist,
      MultipleObjectsReturned

Alimento
--------

Alimento cadastrado para uso em protocolos padrão de dieta especial, com tipo
(edital ou próprio), marca e forma de listagem no protocolo.

.. autoclass:: Alimento
   :members:
   :show-inheritance:

SubstituicaoAlimento
--------------------

Substituição de alimento associada a uma solicitação de dieta especial,
indicando alimentos isentos ou a substituir por produtos/alimentos substitutos.

.. autoclass:: SubstituicaoAlimento
   :members:
   :show-inheritance:

AlimentoSubstituto
------------------

Vínculo (through) entre uma substituição de alimento de protocolo padrão e o
alimento substituto.

.. autoclass:: AlimentoSubstituto
   :members:
   :show-inheritance:

ProtocoloPadraoDietaEspecial
----------------------------

Protocolo padrão de dieta especial. Padroniza orientações gerais, status de
liberação, editais vinculados e histórico de alterações para as dietas.

.. autoclass:: ProtocoloPadraoDietaEspecial
   :members:
   :show-inheritance:

SubstituicaoAlimentoProtocoloPadrao
-----------------------------------

Substituição de alimento definida em um protocolo padrão de dieta especial.

.. autoclass:: SubstituicaoAlimentoProtocoloPadrao
   :members:
   :show-inheritance:
