admin
=====

.. automodule:: src.pre_recebimento.ficha_tecnica.admin
   :members:
   :show-inheritance:

Configurações de administração do submódulo de fichas técnicas:

- ``FichaTecnicaDoProdutoAdmin``: lista as fichas com ``numero``,
  ``produto``, ``categoria``, ``empresa`` e ``fabricante``; permite editar
  inline as informações nutricionais (``InformacoesNutricionaisFichaTecnicaInline``)
  e as análises (``AnaliseFichaTecnicaInline``); busca por nome do produto,
  número, categoria, nome da empresa e nome do fabricante; filtra por
  ``status``.
- ``FabricanteFichaTecnicaAdmin``: lista os fabricantes das fichas com
  fabricante, cidade, estado, telefone e e-mail; filtra por ``estado``;
  busca por nome do fabricante, CNPJ, cidade e e-mail; mantém ``uuid`` como
  somente leitura.
