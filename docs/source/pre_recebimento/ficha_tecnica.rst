ficha_tecnica
=============

Submódulo de fichas técnicas do pré-recebimento. Gerencia o cadastro,
a análise e a aprovação das fichas técnicas dos produtos alimentícios
fornecidos ao SIGPAE.

Uma ficha técnica descreve, por produto, as especificações de
fabricante/fornecedor, dados nutricionais, condições de conservação e
transporte, embalagens, rotulagem e responsável técnico. Ela passa por um
fluxo de aprovação que envolve o fornecedor (cadastro e correções), a
CODAE/GPCODAE (análise e aprovação) e pode ser vinculada a um ou mais
cronogramas de entrega.

O submódulo é composto por:

- **Modelos**: :class:`~src.pre_recebimento.ficha_tecnica.models.FichaTecnicaDoProduto`
  (ficha em si, com o workflow de aprovação),
  :class:`~src.pre_recebimento.ficha_tecnica.models.FabricanteFichaTecnica`
  (dados do fabricante específicos da ficha),
  :class:`~src.pre_recebimento.ficha_tecnica.models.InformacoesNutricionaisFichaTecnica`
  (tabela nutricional por 100 g/porção/valor diário) e
  :class:`~src.pre_recebimento.ficha_tecnica.models.AnaliseFichaTecnica`
  (análise da GPCODAE por bloco de conferência).
- **API**: endpoints de rascunho (fornecedor), cadastro/análise (CODAE),
  correção e atualização pelo fornecedor, dashboard, relatórios e geração
  de PDF/Excel.
- **Admin**: telas de administração com inlines de informações nutricionais
  e análises.

Regra central de negócio: as categorias de ficha (``PERECIVEIS``,
``NAO_PERECIVEIS`` e ``FLV``) exigem conjuntos diferentes de campos
obrigatórios, e os produtos orgânicos/alergênicos/líquidos possuem campos
dependentes obrigatórios.

.. automodule:: src.pre_recebimento.ficha_tecnica
   :members:
   :show-inheritance:

.. toctree::
   :maxdepth: 4

   ficha_tecnica/models
   ficha_tecnica/api
   ficha_tecnica/admin
   ficha_tecnica/fixtures
