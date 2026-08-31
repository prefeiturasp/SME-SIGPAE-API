qualidade
=========

Submódulo de qualidade do pré-recebimento. Concentra os dados de
referência do controle de qualidade: laboratórios credenciados que emitem
laudos e tipos de embalagem (qualidade) utilizados nos cronogramas de
entrega.

O submódulo é composto por:

- **Modelos**: :class:`Laboratorio <src.pre_recebimento.qualidade.models.Laboratorio>`
  (com flag ``credenciado``) e
  :class:`TipoEmbalagemQld <src.pre_recebimento.qualidade.models.TipoEmbalagemQld>`.
- **API**: endpoints ``/laboratorios/`` e ``/tipos-embalagens/``, com
  CRUD completo e ações de listagem para seletores e filtros.
- **Admin**: cadastro de laboratórios e tipos de embalagem, com nome
  normalizado em letras maiúsculas (``CaixaAltaNomeForm``).
- **Fixtures**: factories ``LaboratorioFactory`` e
  ``TipoEmbalagemQldFactory`` utilizadas nos testes.

Regra central de negócio: apenas laboratórios com ``credenciado = True``
são listados no endpoint ``lista-laboratorios-credenciados``, usado na
seleção de laboratório dos documentos de recebimento.

.. automodule:: src.pre_recebimento.qualidade
   :members:
   :show-inheritance:

.. toctree::
   :maxdepth: 4

   qualidade/models
   qualidade/api
   qualidade/admin
   qualidade/fixtures
