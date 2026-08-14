tasks
=====

Submódulo de tarefas assíncronas do módulo de dieta especial. Reúne as tasks
Celery de processamento de dietas, cancelamento automático, geração diária de
logs e geração de relatórios em PDF e XLSX.

.. automodule:: src.dieta_especial.tasks
   :members:
   :show-inheritance:

.. toctree::
   :maxdepth: 4

   tasks/admin_actions
   tasks/logs
   tasks/processamentos
   tasks/relatorio_pdf
   tasks/relatorio_terceirizadas_pdf
   tasks/relatorio_terceirizadas_xlsx
   tasks/relatorio_historico_logs_pdf
   tasks/relatorio_historico_logs_xlsx
   tasks/relatorio_recreio_nas_ferias_pdf
   tasks/relatorio_recreio_nas_ferias_xlsx
   tasks/utils
