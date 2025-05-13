from calendar import monthrange
from datetime import date

from django.db.models import Count, F, Q, Sum
from workalendar.america import BrazilSaoPauloCity

from ..cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
from ..cardapio.base.models import TipoAlimentacao
from ..dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow
from ..dieta_especial.models import ClassificacaoDieta
from ..escola.models import Aluno, LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar
from ..inclusao_alimentacao.models import QuantidadePorPeriodo
from ..kit_lanche.models import SolicitacaoKitLancheAvulsa
from ..paineis_consolidados.models import MoldeConsolidado


def mes_para_faixa(mes_string):
    (mes, ano) = mes_string.split("/")
    mes = int(mes)
    ano = int(ano)
    ultimo_dia_do_mes = monthrange(ano, mes)[1]
    return (
        date(ano, mes, 1),
        date(ano, mes, ultimo_dia_do_mes),
    )


def eh_feriado_ou_fds(data):
    calendario = BrazilSaoPauloCity()
    return data.weekday() >= 5 or calendario.is_holiday(data)


def total_merendas_secas_por_escola_periodo_escolar_e_data(
    escola_periodo_escolar, data
):
    return QuantidadePorPeriodo.objects.filter(
        Q(
            inclusao_alimentacao_continua__escola=escola_periodo_escolar.escola,
            inclusao_alimentacao_continua__data_inicial__lte=data,
            inclusao_alimentacao_continua__data_final__gte=data,
            inclusao_alimentacao_continua__status=PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
        )
        | Q(
            grupo_inclusao_normal__escola=escola_periodo_escolar.escola,
            grupo_inclusao_normal__inclusoes_normais__data=data,
            grupo_inclusao_normal__status=PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
        ),
        periodo_escolar=escola_periodo_escolar.periodo_escolar,
        dias_semana__contains=[data.weekday()],
        tipos_alimentacao__nome__iexact="merenda seca",
    ).aggregate(total_merendas_secas=Sum("numero_alunos"))["total_merendas_secas"]


def total_kits_lanche_por_escola_e_data(escola, data):
    return (
        SolicitacaoKitLancheAvulsa.objects.filter(
            escola=escola,
            solicitacao_kit_lanche__data=data,
            status=PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
        )
        .annotate(
            total_kits=F("quantidade_alunos") * Count("solicitacao_kit_lanche__kits")
        )
        .aggregate(Sum("total_kits"))["total_kits__sum"]
    )


def alteracoes_de_cardapio_por_escola_periodo_escolar_e_data(
    escola_periodo_escolar, data
):
    refeicao = TipoAlimentacao.objects.get(nome="refeição")
    lanche = TipoAlimentacao.objects.get(nome="lanche")

    qs = AlteracaoCardapio.objects.filter(
        data_inicial__lte=data,
        data_final__gte=data,
        escola=escola_periodo_escolar.escola,
        status=PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
        substituicoes_periodo_escolar__periodo_escolar=escola_periodo_escolar.periodo_escolar,
    )

    rpl = qs.filter(
        Q(
            substituicoes_periodo_escolar__tipo_alimentacao_de__tipos_alimentacao=refeicao,
            substituicoes_periodo_escolar__tipo_alimentacao_para__tipos_alimentacao=lanche,
        )
    )

    if rpl.count():
        return "RPL"

    lpr = qs.filter(
        Q(
            substituicoes_periodo_escolar__tipo_alimentacao_de__tipos_alimentacao=lanche,
            substituicoes_periodo_escolar__tipo_alimentacao_para__tipos_alimentacao=refeicao,
        )
    )

    if lpr.count():
        return "LPR"


def matriculados_convencional_em_uma_data(escola_periodo, data):
    log_posterior = (
        LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar.objects.filter(
            escola=escola_periodo.escola,
            periodo_escolar=escola_periodo.periodo_escolar,
            criado_em__date__gt=data,
        )
        .order_by("criado_em")
        .first()
    )

    if log_posterior:
        return log_posterior.quantidade_alunos_de
    else:
        return escola_periodo.quantidade_alunos


def matriculados_em_uma_data(escola_periodo, data):
    filtros_data_dieta = [
        (
            Q(dietas_especiais__data_termino__isnull=True)
            | Q(dietas_especiais__data_termino__gte=data)
        )
        & (
            Q(dietas_especiais__data_inicio__isnull=True)
            & Q(dietas_especiais__criado_em__date__lte=data)
            | Q(dietas_especiais__data_inicio__isnull=False)
            & Q(dietas_especiais__data_inicio__lte=data)
        )
    ]
    filtros_outros = {
        "escola": escola_periodo.escola,
        "periodo_escolar": escola_periodo.periodo_escolar,
        "dietas_especiais__ativo": True,
        "dietas_especiais__status__in": MoldeConsolidado.AUTORIZADO_STATUS_DIETA_ESPECIAL,
    }

    classificacoes_a = ClassificacaoDieta.objects.filter(
        nome__in=["Tipo A", "Tipo A Enteral"]
    )
    classificacoes_b = ClassificacaoDieta.objects.filter(nome__in=["Tipo B"])

    quantidade_alunos_dieta_a = Aluno.objects.filter(
        dietas_especiais__classificacao__in=classificacoes_a,
        *filtros_data_dieta,
        **filtros_outros
    ).count()
    quantidade_alunos_dieta_b = Aluno.objects.filter(
        dietas_especiais__classificacao__in=classificacoes_b,
        *filtros_data_dieta,
        **filtros_outros
    ).count()

    return {
        "convencional": matriculados_convencional_em_uma_data(escola_periodo, data),
        "grupoA": quantidade_alunos_dieta_a,
        "grupoB": quantidade_alunos_dieta_b,
    }
