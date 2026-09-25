admin
=====

.. automodule:: src.recebimento.admin
   :members:
   :show-inheritance:

Configurações de administração do módulo de recebimento:

- ``QuestaoConferenciaAdmin``: lista as questões com ``questao``,
  ``tipo_questao``, ``pergunta_obrigatoria``, ``posicao`` e ``status``;
  ordena por posição e criação; busca por texto da questão; filtra por tipo
  e status. ``pergunta_obrigatoria`` e ``posicao`` são editáveis na
  listagem; ``uuid`` é somente leitura. Usa ``QuestaoForm``, que valida a
  unicidade da posição por tipo de questão.
- ``QuestoesPorProdutoAdmin``: lista os vínculos pela ficha técnica e edita
  as questões primárias/secundárias com ``filter_horizontal``.
- ``FichaDeRecebimentoAdmin``: lista as fichas pela representação textual e
  ``data_entrega``, com os veículos, arquivos, questões e ocorrências
  editados em inlines (``VeiculoFichaDeRecebimentoInline``,
  ``ArquivoFichaRecebimentoInline``, ``QuestaoFichaRecebimentoInline`` e
  ``OcorrenciaFichaRecebimentoInline``).
- ``ReposicaoCronogramaFichaRecebimento``: registrado no admin (tipos de
  reposição).
- O submódulo ``ajuste_saldo_laudo`` é importado e registra o
  ``AjusteSaldo`` no admin (ver recebimento/ajuste_saldo_laudo/admin).
