fixtures
========

factories
---------

.. automodule:: src.recebimento.fixtures.factories
   :members:
   :show-inheritance:

.. automodule:: src.recebimento.fixtures.factories.ficha_de_recebimento_factory
   :members:
   :show-inheritance:

.. automodule:: src.recebimento.fixtures.factories.ocorrencia_ficha_recebimento_factory
   :members:
   :show-inheritance:

.. automodule:: src.recebimento.fixtures.factories.questao_conferencia_factory
   :members:
   :show-inheritance:

.. automodule:: src.recebimento.fixtures.factories.questao_ficha_recebimento_factory
   :members:
   :show-inheritance:

.. automodule:: src.recebimento.fixtures.factories.questoes_por_produto_factory
   :members:
   :show-inheritance:

.. automodule:: src.recebimento.fixtures.factories.reposicao_cronograma_factory
   :members:
   :show-inheritance:

Factories utilizadas nos testes:

- ``FichaDeRecebimentoFactory``: cria uma ``FichaDeRecebimento`` vinculada
  a uma ``EtapasDoCronogramaFactory``, com ``data_entrega`` futura e pesos
  das embalagens primárias aleatórios.
- ``VeiculoFichaDeRecebimentoFactory``: cria um veículo com número
  sequencial.
- ``ArquivoFichaDeRecebimentoFactory``: cria um arquivo com um PDF de
  teste (base64 convertido para ``ContentFile``).
- ``OcorrenciaFichaRecebimentoFactory``: cria uma ocorrência com tipo,
  relação, quantidade, descrição e número da nota aleatórios.
- ``QuestaoConferenciaFactory``: cria uma questão com texto aleatório e
  posição sequencial.
- ``QuestaoFichaRecebimentoFactory``: cria uma resposta a uma questão com
  resposta e tipo de embalagem aleatórios.
- ``QuestoesPorProdutoFactory``: cria o vínculo com uma
  ``FichaTecnicaFactory``.
- ``ReposicaoCronogramaFichaRecebimentoFactory``: cria um tipo de
  reposição com valores padrão.

dados de carga
--------------

O seed data dos tipos de reposição de cronograma
(``src/recebimento/data/reposicao_cronograma.py``) contém os registros
iniciais consumidos pela carga de dados:

- ``Repor`` — REPOR OS PRODUTOS FALTANTES/RECUSADOS.
- ``Credito`` — FAZER UMA CARTA DE CRÉDITO DO VALOR PAGO.

Há também o fixture YAML ``reposicao_cronograma_ficha_recebimento.yaml``
com os mesmos registros.
