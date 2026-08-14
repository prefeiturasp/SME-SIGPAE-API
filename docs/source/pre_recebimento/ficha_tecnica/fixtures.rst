fixtures
========

factories
---------

.. automodule:: src.pre_recebimento.ficha_tecnica.fixtures.factories
   :members:
   :show-inheritance:

.. automodule:: src.pre_recebimento.ficha_tecnica.fixtures.factories.fabricante_ficha_tecnica_factory
   :members:
   :show-inheritance:

.. automodule:: src.pre_recebimento.ficha_tecnica.fixtures.factories.ficha_tecnica_do_produto_factory
   :members:
   :show-inheritance:

Factories utilizadas nos testes:

- ``FabricanteFichaTecnicaFactory``: cria um ``FabricanteFichaTecnica`` com
  fabricante (``SubFactory`` de ``FabricanteFactory``) e dados de endereço/
  contato gerados pelo Faker pt_BR (CNPJ sem máscara, CEP sem máscara, etc.).
- ``FichaTecnicaFactory``: cria uma ``FichaTecnicaDoProduto`` com empresa,
  produto (``ProdutoLogisticaFactory``), marca, categoria (Perecíveis ou
  Não Perecíveis), programa (Leve Leite ou Alimentação Escolar), pesos e
  unidades de medida, embalagens e fabricante/envasador.
- ``AnaliseFichaTecnicaFactory``: cria uma ``AnaliseFichaTecnica`` vinculada
  a uma ``FichaTecnicaFactory``.
