from django.urls import include, path
from rest_framework import routers

from .aluno.api import viewsets as aluno_viewsets
from .codae.api import viewsets as codae_viewsets
from .diretoria_regional.api import viewsets as diretoria_regional_viewsets
from .escola.api import viewsets as escola_viewsets
from .logs.api import viewsets as logs_viewsets
from .lote.api import viewsets as lote_viewsets
from .subprefeitura.api import viewsets as subprefeitura_viewsets

router = routers.DefaultRouter()

router.register(
    "faixas-etarias", aluno_viewsets.FaixaEtariaViewSet, basename="Faixas Etárias"
)
router.register(
    "escola-quantidade-alunos-por-periodo-e-faixa-etaria",
    escola_viewsets.EscolaQuantidadeAlunosPorPeriodoEFaixaViewSet,
    basename="escola-quantidade-alunos-por-periodo-e-faixa-etaria",
)
router.register(
    "escolas-simples", escola_viewsets.EscolaSimplesViewSet, basename="escolas-simples"
)
router.register(
    "escolas-para-filtros",
    escola_viewsets.EscolaParaFiltrosViewSet,
    basename="escolas-para-filtros",
)
router.register(
    "escolas-simplissima",
    escola_viewsets.EscolaSimplissimaViewSet,
    basename="escolas-simplissima",
)
router.register(
    "escolas-simplissima-com-dre",
    escola_viewsets.EscolaSimplissimaComDREViewSet,
    basename="escolas-simplissima-com-dre",
)
router.register(
    "escolas-simplissima-com-eol",
    escola_viewsets.EscolaSimplissimaComEolViewSet,
    basename="escolas-simplissima-com-eol",
)
router.register(
    "escolas-simplissima-com-dre-unpaginated",
    escola_viewsets.EscolaSimplissimaComDREUnpaginatedViewSet,
    basename="escolas-simplissima-unpaginated",
)
router.register(
    "periodos-escolares", escola_viewsets.PeriodoEscolarViewSet, basename="periodos"
)
router.register(
    "periodos-com-matriculados-por-ue",
    escola_viewsets.PeriodosComMatriculadosPorUEViewSet,
    basename="periodos-com-matriculados",
)
router.register(
    "diretorias-regionais",
    diretoria_regional_viewsets.DiretoriaRegionalViewSet,
    basename="dres",
)
router.register(
    "diretorias-regionais-simplissima",
    diretoria_regional_viewsets.DiretoriaRegionalSimplissimaViewSet,
    basename="dres-simplissima",
)
router.register(
    "lotes-simples", lote_viewsets.LoteSimplesViewSet, basename="lotes-simples"
)
router.register("lotes", lote_viewsets.LoteViewSet, basename="lotes")
router.register(
    "tipos-gestao", escola_viewsets.TipoGestaoViewSet, basename="tipos-gestao"
)
router.register(
    "subprefeituras",
    subprefeitura_viewsets.SubprefeituraViewSet,
    basename="subprefeituras",
)
router.register("codae", codae_viewsets.CODAESimplesViewSet, basename="codae")
router.register(
    "tipos-unidade-escolar",
    escola_viewsets.TipoUnidadeEscolarViewSet,
    basename="tipos-unidade-escolar",
)
router.register(
    "quantidade-alunos-por-periodo",
    escola_viewsets.EscolaPeriodoEscolarViewSet,
    basename="quantidade-alunos-por-periodo",
)
router.register("alunos", aluno_viewsets.AlunoViewSet, basename="alunos")
router.register(
    "matriculados-no-mes",
    logs_viewsets.LogAlunosMatriculadosPeriodoEscolaViewSet,
    basename="matriculados-no-mes",
)
router.register(
    "dias-calendario", escola_viewsets.DiaCalendarioViewSet, basename="dias-calendario"
)
router.register(
    "relatorio-alunos-matriculados",
    escola_viewsets.RelatorioAlunosMatriculadosViewSet,
    basename="relatorio-alunos-matriculados",
)
router.register(
    "log-alunos-matriculados-faixa-etaria-dia",
    logs_viewsets.LogAlunosMatriculadosFaixaEtariaDiaViewSet,
    basename="log-alunos-matriculados-faixa-etaria-dia",
)
router.register(
    "dias-suspensao-atividades", escola_viewsets.DiaSuspensaoAtividadesViewSet
)
router.register("grupos-unidade-escolar", escola_viewsets.GrupoUnidadeEscolarViewSet)
router.register(
    "relatorio-controle-frequencia",
    escola_viewsets.RelatorioControleDeFrequenciaViewSet,
    basename="relatorio-controle-frequencia",
)
router.register(
    "historico-escola",
    escola_viewsets.HistoricoEscolaViewSet,
    basename="historico-escola",
)

urlpatterns = [path("", include(router.urls))]
