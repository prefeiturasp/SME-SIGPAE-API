base
====

Submódulo de dados de referência do pré-recebimento. Concentra os dados
compartilhados pelos demais submódulos, como as unidades de medida
utilizadas nas quantidades de cronogramas de entrega, fichas técnicas e
documentos de recebimento.

O submódulo é composto por:

- **Modelos**: :class:`UnidadeMedida <src.pre_recebimento.base.models.UnidadeMedida>`,
  com nome sempre em letras maiúsculas e abreviação em letras minúsculas.
- **API**: endpoint ``/unidades-medida-logistica/`` com CRUD completo e
  ação ``lista-nomes-abreviacoes``, restrito a perfis da CODAE
  (``DILOG_QUALIDADE``, ``DILOG_CRONOGRAMA`` e
  ``COORDENADOR_CODAE_DILOG_LOGISTICA``) e, na ação de listagem de
  nomes/abreviações, também aos perfis de empresa
  (``ADMINISTRADOR_EMPRESA`` e ``USUARIO_EMPRESA``).
- **Admin**: cadastro das unidades de medida com busca por nome e
  abreviação.
- **Fixtures**: factory ``UnidadeMedidaFactory`` utilizada nos testes.

Regra central de negócio: o nome da unidade de medida é sempre salvo em
letras maiúsculas e a abreviação em letras minúsculas (normalização no
``save`` do modelo e validação no serializer de criação).

.. automodule:: src.pre_recebimento.base
   :members:
   :show-inheritance:

.. toctree::
   :maxdepth: 4

   base/models
   base/api
   base/admin
   base/fixtures
