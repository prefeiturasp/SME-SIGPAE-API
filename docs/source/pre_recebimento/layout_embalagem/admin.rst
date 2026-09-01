admin
=====

.. automodule:: src.pre_recebimento.layout_embalagem.admin
   :members:
   :show-inheritance:

Configurações de administração do submódulo de layout de embalagem:

- ``ImagemDoTipoDeEmbalagemInline``: inline aninhado das imagens de um
  tipo de embalagem.
- ``TipoEmbalagemLayoutInline``: inline aninhado dos tipos de embalagem de
  um layout (``uuid`` somente leitura), com as imagens em inline interno.
- ``LayoutDeEmbalagemAdmin``: lista os layouts com a representação textual,
  ficha técnica, produto e ``criado_em``; busca por número da ficha
  técnica ou nome do produto; ``uuid`` é somente leitura; os tipos de
  embalagem e suas imagens são editados em inlines aninhados.
