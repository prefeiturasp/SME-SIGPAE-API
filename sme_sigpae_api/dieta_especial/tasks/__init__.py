from sme_sigpae_api.dieta_especial.tasks.logs import (
    gera_logs_dietas_especiais_diariamente,
)
from sme_sigpae_api.dieta_especial.tasks.processamentos import (
    cancela_dietas_ativas_automaticamente_task,
    processa_dietas_especiais_task,
)
from sme_sigpae_api.dieta_especial.tasks.relatorio_historico_logs_pdf import (
    gera_pdf_relatorio_historico_dietas_especiais_async,
)
from sme_sigpae_api.dieta_especial.tasks.relatorio_historico_logs_xlsx import (
    gera_xlsx_relatorio_historico_dietas_especiais_async,
)
from sme_sigpae_api.dieta_especial.tasks.relatorio_pdf import (
    gera_pdf_relatorio_dieta_especial_async,
)
from sme_sigpae_api.dieta_especial.tasks.relatorio_terceirizadas_pdf import (
    gera_pdf_relatorio_dietas_especiais_terceirizadas_async,
)
from sme_sigpae_api.dieta_especial.tasks.relatorio_terceirizadas_xlsx import (
    gera_xlsx_relatorio_dietas_especiais_terceirizadas_async,
)
from sme_sigpae_api.dieta_especial.tasks.relatorio_recreio_nas_ferias_pdf import (
    gera_pdf_relatorio_recreio_nas_ferias_async,
)

__all__ = [
    "gera_logs_dietas_especiais_diariamente",
    "cancela_dietas_ativas_automaticamente_task",
    "processa_dietas_especiais_task",
    "gera_pdf_relatorio_historico_dietas_especiais_async",
    "gera_xlsx_relatorio_historico_dietas_especiais_async",
    "gera_pdf_relatorio_dieta_especial_async",
    "gera_pdf_relatorio_dietas_especiais_terceirizadas_async",
    "gera_xlsx_relatorio_dietas_especiais_terceirizadas_async",
    "gera_pdf_relatorio_recreio_nas_ferias_async",
]
