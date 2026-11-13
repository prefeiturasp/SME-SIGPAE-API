from ..aluno.api.viewsets import (
    AlunoViewSet,
    FaixaEtariaViewSet,
)
from ..carga_dados.api.viewsets import (
    exportar_planilha_importacao_tipo_gestao_escola,
)
from ..codae.api.viewsets import (
    CODAESimplesViewSet,
)
from ..diretoria_regional.api.viewsets import (
    DiretoriaRegionalSimplissimaViewSet,
    DiretoriaRegionalViewSet,
)
from ..escola.api.viewsets import (
    DiaCalendarioViewSet,
    DiaSuspensaoAtividadesViewSet,
    EscolaParaFiltrosViewSet,
    EscolaPeriodoEscolarViewSet,
    EscolaQuantidadeAlunosPorPeriodoEFaixaViewSet,
    EscolaSimplesViewSet,
    EscolaSimplissimaComDREUnpaginatedViewSet,
    EscolaSimplissimaComDREViewSet,
    EscolaSimplissimaComEolViewSet,
    EscolaSimplissimaViewSet,
    GrupoUnidadeEscolarViewSet,
    HistoricoEscolaViewSet,
    PeriodoEscolarViewSet,
    PeriodosComMatriculadosPorUEViewSet,
    RelatorioAlunosMatriculadosViewSet,
    RelatorioControleDeFrequenciaViewSet,
    TipoGestaoViewSet,
    TipoUnidadeEscolarViewSet,
    periodos_cemei_evento_especifico,
    periodos_inclusao_continua_ativas,
)
from ..logs.api.viewsets import (
    LogAlunosMatriculadosFaixaEtariaDiaViewSet,
    LogAlunosMatriculadosPeriodoEscolaViewSet,
)
from ..lote.api.viewsets import (
    LoteSimplesViewSet,
    LoteViewSet,
)
from ..subprefeitura.api.viewsets import (
    SubprefeituraViewSet,
)

__all__ = [
    "AlunoViewSet",
    "CODAESimplesViewSet",
    "DiaCalendarioViewSet",
    "DiaSuspensaoAtividadesViewSet",
    "DiretoriaRegionalSimplissimaViewSet",
    "DiretoriaRegionalViewSet",
    "EscolaParaFiltrosViewSet",
    "EscolaPeriodoEscolarViewSet",
    "EscolaQuantidadeAlunosPorPeriodoEFaixaViewSet",
    "EscolaSimplesViewSet",
    "EscolaSimplissimaComDREUnpaginatedViewSet",
    "EscolaSimplissimaComDREViewSet",
    "EscolaSimplissimaComEolViewSet",
    "EscolaSimplissimaViewSet",
    "FaixaEtariaViewSet",
    "GrupoUnidadeEscolarViewSet",
    "HistoricoEscolaViewSet",
    "LogAlunosMatriculadosFaixaEtariaDiaViewSet",
    "LogAlunosMatriculadosPeriodoEscolaViewSet",
    "LoteSimplesViewSet",
    "LoteViewSet",
    "PeriodoEscolarViewSet",
    "PeriodosComMatriculadosPorUEViewSet",
    "RelatorioAlunosMatriculadosViewSet",
    "RelatorioControleDeFrequenciaViewSet",
    "SubprefeituraViewSet",
    "TipoGestaoViewSet",
    "TipoUnidadeEscolarViewSet",
    "exportar_planilha_importacao_tipo_gestao_escola",
    "periodos_cemei_evento_especifico",
    "periodos_inclusao_continua_ativas",
]
