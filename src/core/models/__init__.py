"""Fachada de modelos da app core (label ``escola``).

Os modelos vivem nas subapps de ``src.core``; este pacote apenas reexporta os
nomes para manter compatibilidade com os imports existentes.
"""

from ..aluno.models import (
    Aluno,
    AlunoPeriodoParcial,
    FaixaEtaria,
    HistoricoMatriculaAluno,
    MudancaFaixasEtarias,
    Responsavel,
    TipoTurma,
)
from ..carga_dados.models import (
    PlanilhaAtualizacaoTipoGestaoEscola,
    PlanilhaEscolaDeParaCodigoEolCodigoCoade,
)
from ..codae.models import Codae
from ..constants import (
    CEU_EMEF,
    CEU_EMEI,
    CIEJA,
    EMEF,
    EMEF_P_FOM,
    EMEFM,
    EMEI,
    EMEI_P_FOM,
    ESCOLA_TIPO_GESTAO_NOME,
    LISTA_TIPOS_UNIDADES,
)
from ..diretoria_regional.models import DiretoriaRegional
from ..escola.models import (
    AlunosMatriculadosPeriodoEscola,
    DiaCalendario,
    DiaSuspensaoAtividades,
    Escola,
    EscolaPeriodoEscolar,
    GrupoUnidadeEscolar,
    HistoricoEscola,
    PeriodoEscolar,
    TipoGestao,
    TipoUnidadeEscolar,
)
from ..logs.models import (
    LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar,
    LogAlunoPorDia,
    LogAlunosMatriculadosFaixaEtariaDia,
    LogAlunosMatriculadosPeriodoEscola,
    LogAtualizaDadosAluno,
    LogRotinaDiariaAlunos,
)
from ..lote.models import Lote
from ..subprefeitura.models import Subprefeitura

__all__ = [
    "Aluno",
    "AlunoPeriodoParcial",
    "AlunosMatriculadosPeriodoEscola",
    "CEU_EMEF",
    "CEU_EMEI",
    "CIEJA",
    "Codae",
    "DiaCalendario",
    "DiaSuspensaoAtividades",
    "DiretoriaRegional",
    "EMEF",
    "EMEFM",
    "EMEF_P_FOM",
    "EMEI",
    "EMEI_P_FOM",
    "ESCOLA_TIPO_GESTAO_NOME",
    "Escola",
    "EscolaPeriodoEscolar",
    "FaixaEtaria",
    "GrupoUnidadeEscolar",
    "HistoricoEscola",
    "HistoricoMatriculaAluno",
    "LISTA_TIPOS_UNIDADES",
    "LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar",
    "LogAlunoPorDia",
    "LogAlunosMatriculadosFaixaEtariaDia",
    "LogAlunosMatriculadosPeriodoEscola",
    "LogAtualizaDadosAluno",
    "LogRotinaDiariaAlunos",
    "Lote",
    "MudancaFaixasEtarias",
    "PeriodoEscolar",
    "PlanilhaAtualizacaoTipoGestaoEscola",
    "PlanilhaEscolaDeParaCodigoEolCodigoCoade",
    "Responsavel",
    "Subprefeitura",
    "TipoGestao",
    "TipoTurma",
    "TipoUnidadeEscolar",
]
