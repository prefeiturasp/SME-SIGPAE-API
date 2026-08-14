pos_recebimento
===============

Módulo de pós-recebimento do sistema SIGPAE. Gerencia a formalização do
recebimento definitivo de produtos de uma empresa/contrato por meio do
Termo de Recebimento Definitivo, documento que vincula um ou mais
cronogramas de entrega, os fiscais responsáveis (perfil
``DILOG_QUALIDADE``) e o texto do termo.

O módulo é composto por:

- **Modelos**: :class:`~src.pos_recebimento.models.TermoRecebimentoDefinitivo`
  (termo em si) e o modelo intermediário
  :class:`~src.pos_recebimento.models.CronogramaTermoRecebimentoDefinitivo`
  (cronograma do termo, com valor de contrato e quantidade total recebida
  próprios).
- **API**: endpoint único de criação (``POST /pos-recebimento/termos/``),
  com permissão restrita aos perfis ``DILOG_CRONOGRAMA`` e
  ``COORDENADOR_CODAE_DILOG_LOGISTICA`` vinculados à CODAE.
- **Admin**: telas de administração dos dois modelos, com edição inline
  dos cronogramas do termo.

Regra central de negócio: a empresa só pode ser utilizada em um termo se
possuir ao menos uma ficha de recebimento com status "Assinado CODAE"
(``FichaDeRecebimentoWorkflow.ASSINADA``). A criação do termo pela API
sempre persiste o termo com status ``ENVIADO`` (fluxo "Salvar e Enviar").

.. automodule:: src.pos_recebimento
   :members:
   :show-inheritance:

.. toctree::
   :maxdepth: 4

   pos_recebimento/models
   pos_recebimento/api
   pos_recebimento/admin
