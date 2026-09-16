fixtures
========

factories
---------

O submódulo de cronograma semanal **não possui factories dedicadas**: os
testes (em ``src/pre_recebimento/cronograma_semanal/__tests__/``) criam
as instâncias de :class:`CronogramaSemanal
<src.pre_recebimento.cronograma_semanal.models.CronogramaSemanal>` e
:class:`ProgramacaoEntregaSemanal
<src.pre_recebimento.cronograma_semanal.models.ProgramacaoEntregaSemanal>`
diretamente com ``model_bakery`` (``baker.make``), reutilizando as
factories de ``cronograma_entrega`` (``contrato_factory``,
``empresa_factory``) e de ``ficha_tecnica`` (``ficha_tecnica_factory``)
para montar o cenário do cronograma mensal Ponto a Ponto assinado.
