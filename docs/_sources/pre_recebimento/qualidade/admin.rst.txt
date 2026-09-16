admin
=====

.. automodule:: src.pre_recebimento.qualidade.admin
   :members:
   :show-inheritance:

Configurações de administração do submódulo de qualidade:

- ``Laboratoriodmin``: lista os laboratórios com ``nome``, ``cnpj``,
  ``cidade`` e ``credenciado``; ordena por ``-criado_em``; busca por nome e
  filtra por nome. O ``nome`` é normalizado em letras maiúsculas
  (``CaixaAltaNomeForm``) e ``uuid`` é somente leitura.
- ``EmbalagemQldAdmin``: lista os tipos de embalagem com ``nome``,
  ``abreviacao`` e ``criado_em``; busca por nome. O ``nome`` é normalizado
  em letras maiúsculas (``CaixaAltaNomeForm``) e ``uuid`` é somente leitura.
