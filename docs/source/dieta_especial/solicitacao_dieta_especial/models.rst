models
======

.. automodule:: src.dieta_especial.solicitacao_dieta_especial.models
   :members:
   :show-inheritance:
   :exclude-members:
      SolicitacaoDietaEspecial,
      MotivoNegacao,
      MotivoAlteracaoUE,
      AlergiaIntolerancia,
      ClassificacaoDieta,
      Anexo,
      SolicitacoesDietaEspecialAtivasInativasPorAluno,
      DoesNotExist,
      MultipleObjectsReturned

SolicitacaoDietaEspecial
------------------------

Modelo central do módulo de dieta especial. Representa a solicitação de dieta
especial de um aluno, passando por um fluxo de autorização que envolve a
escola e a CODAE. Pode ser uma inclusão comum, alteração de U.E.,
cancelamento de dieta ou solicitação para aluno não matriculado.

.. autoclass:: SolicitacaoDietaEspecial
   :members:
   :show-inheritance:

MotivoNegacao
-------------

Catálogo de motivos de negação de uma solicitação, com vínculo opcional ao
processo de cancelamento ou inclusão.

.. autoclass:: MotivoNegacao
   :members:
   :show-inheritance:

MotivoAlteracaoUE
-----------------

Catálogo de motivos de alteração de unidade educacional de uma dieta especial.

.. autoclass:: MotivoAlteracaoUE
   :members:
   :show-inheritance:

AlergiaIntolerancia
-------------------

Catálogo de alergias e intolerâncias alimentares (diagnósticos) associadas às
dietas especiais.

.. autoclass:: AlergiaIntolerancia
   :members:
   :show-inheritance:

ClassificacaoDieta
------------------

Catálogo de classificações de dieta especial.

.. autoclass:: ClassificacaoDieta
   :members:
   :show-inheritance:

Anexo
-----

Anexo (arquivo) vinculado a uma solicitação de dieta especial, podendo ser
laudo de alta.

.. autoclass:: Anexo
   :members:
   :show-inheritance:

SolicitacoesDietaEspecialAtivasInativasPorAluno
-----------------------------------------------

Modelo não gerenciado (view) que consolida a quantidade de dietas ativas e
inativas por aluno.

.. autoclass:: SolicitacoesDietaEspecialAtivasInativasPorAluno
   :members:
   :show-inheritance:
