import datetime
from collections import Counter

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from sme_sigpae_api.dados_comuns.utils import quantidade_meses
from sme_sigpae_api.dieta_especial.constants import ETAPA_INFANTIL
from sme_sigpae_api.dieta_especial.models import (
    ClassificacaoDieta,
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
)
from sme_sigpae_api.escola.models import FaixaEtaria, PeriodoEscolar
from sme_sigpae_api.medicao_inicial.models import SolicitacaoMedicaoInicial


def cria_logs_totais_cei_por_faixa_etaria(logs_escola, ontem, escola):
    logs = [log for log in logs_escola if log.periodo_escolar.nome == "INTEGRAL"]
    if not logs:
        return logs_escola
    for classificacao in ClassificacaoDieta.objects.all():
        quantidade_total = sum(
            [log.quantidade for log in logs if log.classificacao == classificacao]
        )
        log_total = LogQuantidadeDietasAutorizadasCEI(
            data=ontem,
            escola=escola,
            quantidade=quantidade_total,
            classificacao=classificacao,
            periodo_escolar=logs[0].periodo_escolar,
            faixa_etaria=None,
        )
        logs_escola.append(log_total)
    return logs_escola


def get_quantidade_nao_matriculados_entre_4_e_6_anos(dietas):
    return dietas.filter(
        tipo_solicitacao="ALUNO_NAO_MATRICULADO",
        aluno__data_nascimento__lte=datetime.date.today() - relativedelta(years=4),
        aluno__data_nascimento__gte=datetime.date.today() - relativedelta(years=6),
    ).count()


def get_quantidade_nao_matriculados_maior_6_anos(dietas):
    return dietas.filter(
        tipo_solicitacao="ALUNO_NAO_MATRICULADO",
        aluno__data_nascimento__lte=datetime.date.today() - relativedelta(years=6),
    ).count()


def get_quantidade_dietas_emebs(each, dietas):
    dietas_sem_alunos_nao_matriculados = dietas.exclude(
        tipo_solicitacao="ALUNO_NAO_MATRICULADO"
    )
    if each == "INFANTIL":
        quantidade = dietas_sem_alunos_nao_matriculados.filter(
            aluno__etapa=ETAPA_INFANTIL
        ).count()
        quantidade += get_quantidade_nao_matriculados_entre_4_e_6_anos(dietas)
    elif each == "FUNDAMENTAL":
        quantidade = dietas_sem_alunos_nao_matriculados.exclude(
            aluno__etapa=ETAPA_INFANTIL
        ).count()
        quantidade += get_quantidade_nao_matriculados_maior_6_anos(dietas)
    else:
        quantidade = dietas_sem_alunos_nao_matriculados.count()
        quantidade += get_quantidade_nao_matriculados_maior_6_anos(dietas)
        quantidade += get_quantidade_nao_matriculados_entre_4_e_6_anos(dietas)
    return quantidade


def logs_a_criar_sem_periodo_escolar(
    logs_a_criar, escola, dietas_filtradas, ontem, classificacao
):
    if escola.eh_emebs:
        for each in ["INFANTIL", "FUNDAMENTAL", "N/A"]:
            quantidade = get_quantidade_dietas_emebs(each, dietas_filtradas)
            log = LogQuantidadeDietasAutorizadas(
                quantidade=quantidade,
                escola=escola,
                data=ontem,
                classificacao=classificacao,
                infantil_ou_fundamental=each,
            )
            logs_a_criar.append(log)
    else:
        log = LogQuantidadeDietasAutorizadas(
            quantidade=dietas_filtradas.count(),
            escola=escola,
            data=ontem,
            classificacao=classificacao,
        )
        logs_a_criar.append(log)
    return logs_a_criar


def logs_periodo_integral_cei_ou_emei_escola_cemei(
    logs_a_criar,
    dietas_autorizadas,
    classificacao,
    escola,
    periodo_escolar_nome,
    dict_periodos,
    ontem,
):
    dietas = dietas_autorizadas.filter(
        classificacao=classificacao, escola_destino=escola
    ).filter(
        Q(aluno__periodo_escolar__nome=periodo_escolar_nome)
        | Q(tipo_solicitacao="ALUNO_NAO_MATRICULADO")
    )
    series_cei = ["1", "2", "3", "4"]
    quantidade_cei = 0
    quantidade_emei = 0
    for dieta in dietas:
        if not dieta.aluno.serie:
            quantidade_cei += 1
            quantidade_emei += 1
        elif any(
            serie in dieta.aluno.serie for serie in series_cei if dieta.aluno.serie
        ):
            quantidade_cei += 1
        else:
            quantidade_emei += 1
    log_cei = LogQuantidadeDietasAutorizadas(
        quantidade=quantidade_cei,
        escola=escola,
        data=ontem,
        periodo_escolar=dict_periodos[periodo_escolar_nome],
        classificacao=classificacao,
        cei_ou_emei="CEI",
    )
    log_emei = LogQuantidadeDietasAutorizadas(
        quantidade=quantidade_emei,
        escola=escola,
        data=ontem,
        periodo_escolar=dict_periodos[periodo_escolar_nome],
        classificacao=classificacao,
        cei_ou_emei="EMEI",
    )
    return logs_a_criar + [log_cei] + [log_emei]


def gera_logs_dietas_escolas_comuns(escola, dietas_autorizadas, ontem):
    logs_a_criar = []
    dict_periodos = PeriodoEscolar.dict_periodos()
    for classificacao in ClassificacaoDieta.objects.all():
        dietas_filtradas = dietas_autorizadas.filter(
            classificacao=classificacao, escola_destino=escola
        )
        logs_a_criar = logs_a_criar_sem_periodo_escolar(
            logs_a_criar, escola, dietas_filtradas, ontem, classificacao
        )
        for periodo_escolar_nome in escola.periodos_escolares_com_alunos:
            dietas_filtradas_periodo = dietas_autorizadas.filter(
                classificacao=classificacao, escola_destino=escola
            ).filter(
                Q(aluno__periodo_escolar__nome=periodo_escolar_nome)
                | Q(tipo_solicitacao="ALUNO_NAO_MATRICULADO")
            )
            if escola.eh_cemei and periodo_escolar_nome == "INTEGRAL":
                logs_a_criar = logs_periodo_integral_cei_ou_emei_escola_cemei(
                    logs_a_criar,
                    dietas_autorizadas,
                    classificacao,
                    escola,
                    periodo_escolar_nome,
                    dict_periodos,
                    ontem,
                )
            if escola.eh_emebs:
                for each in ["INFANTIL", "FUNDAMENTAL"]:
                    quantidade = get_quantidade_dietas_emebs(
                        each, dietas_filtradas_periodo
                    )
                    log = LogQuantidadeDietasAutorizadas(
                        quantidade=quantidade,
                        escola=escola,
                        data=ontem,
                        periodo_escolar=dict_periodos[periodo_escolar_nome],
                        classificacao=classificacao,
                        infantil_ou_fundamental=each,
                    )
                    logs_a_criar.append(log)
            else:
                log = LogQuantidadeDietasAutorizadas(
                    quantidade=dietas_filtradas_periodo.count(),
                    escola=escola,
                    data=ontem,
                    periodo_escolar=dict_periodos[periodo_escolar_nome],
                    classificacao=classificacao,
                )
                logs_a_criar.append(log)
    return logs_a_criar


def append_periodo_parcial(periodos, solicitacao_medicao):
    if solicitacao_medicao.ue_possui_alunos_periodo_parcial:
        periodos.append("PARCIAL")
    return periodos


def append_faixas_dietas(dietas, escola):
    faixas = []
    series_cei = ["1", "2", "3", "4"]
    for dieta_periodo in dietas:
        data_nascimento = dieta_periodo.aluno.data_nascimento
        meses = quantidade_meses(datetime.date.today(), data_nascimento)
        ultima_faixa = FaixaEtaria.objects.filter(ativo=True).order_by("fim").last()
        if meses >= ultima_faixa.fim:
            faixa = ultima_faixa
        else:
            faixa = FaixaEtaria.objects.get(
                ativo=True, inicio__lte=meses, fim__gt=meses
            )
        if escola.eh_cemei and not any(
            serie in dieta_periodo.aluno.serie
            for serie in series_cei
            if dieta_periodo.aluno.serie
        ):
            continue
        faixas.append(faixa)
    return faixas


def criar_logs_integral_parcial(
    eh_integral,
    dietas,
    solicitacao_medicao,
    escola,
    ontem,
    classificacao,
    periodo,
    faixas,
):
    logs = []
    dict_periodos = PeriodoEscolar.dict_periodos()
    faixas_alunos_parciais = []
    for dieta in dietas:
        if dieta.aluno.nome in solicitacao_medicao.alunos_periodo_parcial.values_list(
            "aluno__nome", flat=True
        ):
            data_nascimento = dieta.aluno.data_nascimento
            meses = quantidade_meses(datetime.date.today(), data_nascimento)
            faixa = FaixaEtaria.objects.get(
                ativo=True, inicio__lte=meses, fim__gt=meses
            )
            faixas_alunos_parciais.append(faixa)
    faixas = faixas if eh_integral else faixas_alunos_parciais
    for faixa, quantidade in Counter(faixas).items():
        if eh_integral and faixa in Counter(faixas_alunos_parciais).keys():
            quantidade = quantidade - Counter(faixas_alunos_parciais).get(faixa)
        log = LogQuantidadeDietasAutorizadasCEI(
            quantidade=quantidade,
            escola=escola,
            data=ontem,
            classificacao=classificacao,
            periodo_escolar=dict_periodos[periodo],
            faixa_etaria=faixa,
        )
        logs.append(log)
    return logs


def faixas_por_periodo_e_faixa_etaria(escola, periodo):
    try:
        return escola.matriculados_por_periodo_e_faixa_etaria()[periodo]
    except KeyError:
        return escola.matriculados_por_periodo_e_faixa_etaria()["INTEGRAL"]


def condicoes(log, escola, ontem, classificacao, periodo, faixa):
    resultado = (
        log.escola == escola
        and log.data == ontem
        and log.classificacao == classificacao
        and log.periodo_escolar.nome == periodo
        and str(log.faixa_etaria.uuid) == faixa
    )
    return resultado


def existe_log(logs_a_criar, escola, ontem, classificacao, periodo, faixa):
    resultado = list(
        filter(
            lambda log: condicoes(log, escola, ontem, classificacao, periodo, faixa),
            logs_a_criar,
        )
    )
    return resultado


def append_logs_a_criar_de_quantidade_zero(logs_a_criar, periodos, escola, ontem):
    dict_periodos = PeriodoEscolar.dict_periodos()
    for periodo in periodos:
        faixas = faixas_por_periodo_e_faixa_etaria(escola, periodo)
        for faixa, _ in faixas.items():
            if faixa in [
                str(f)
                for f in FaixaEtaria.objects.filter(ativo=True).values_list(
                    "uuid", flat=True
                )
            ]:
                for classificacao in ClassificacaoDieta.objects.all():
                    if not existe_log(
                        logs_a_criar, escola, ontem, classificacao, periodo, faixa
                    ):
                        log = LogQuantidadeDietasAutorizadasCEI(
                            quantidade=0,
                            escola=escola,
                            data=ontem,
                            classificacao=classificacao,
                            periodo_escolar=dict_periodos[periodo],
                            faixa_etaria=FaixaEtaria.objects.get(uuid=faixa),
                        )
                        logs_a_criar.append(log)
    return logs_a_criar


def logs_a_criar_existe_solicitacao_medicao(escola, dietas_autorizadas, ontem):
    solicitacao_medicao = SolicitacaoMedicaoInicial.objects.get(
        escola__codigo_eol=escola.codigo_eol,
        mes=f"{datetime.date.today().month:02d}",
        ano=datetime.date.today().year,
    )
    dict_periodos = PeriodoEscolar.dict_periodos()
    logs_a_criar = []
    periodos = escola.periodos_escolares_com_alunos
    periodos = append_periodo_parcial(periodos, solicitacao_medicao)
    periodos = list(set(periodos))
    for periodo in periodos:
        for classificacao in ClassificacaoDieta.objects.all():
            dietas = dietas_autorizadas.filter(
                classificacao=classificacao, escola_destino=escola
            )
            dietas_filtradas_periodo = dietas.filter(
                aluno__periodo_escolar__nome=periodo
            )
            dietas_nao_matriculados = dietas.filter(
                tipo_solicitacao="ALUNO_NAO_MATRICULADO"
            )
            faixas = []
            faixas += append_faixas_dietas(dietas_filtradas_periodo, escola)
            faixas += append_faixas_dietas(dietas_nao_matriculados, escola)
            if periodo == "INTEGRAL" and "PARCIAL" in periodos:
                logs_a_criar += criar_logs_integral_parcial(
                    True,
                    dietas,
                    solicitacao_medicao,
                    escola,
                    ontem,
                    classificacao,
                    periodo,
                    faixas,
                )
            elif periodo == "PARCIAL":
                logs_a_criar += criar_logs_integral_parcial(
                    False,
                    dietas,
                    solicitacao_medicao,
                    escola,
                    ontem,
                    classificacao,
                    periodo,
                    None,
                )
            else:
                for faixa, quantidade in Counter(faixas).items():
                    log = LogQuantidadeDietasAutorizadasCEI(
                        quantidade=quantidade,
                        escola=escola,
                        data=ontem,
                        classificacao=classificacao,
                        periodo_escolar=dict_periodos[periodo],
                        faixa_etaria=faixa,
                    )
                    logs_a_criar.append(log)
    logs_a_criar = append_logs_a_criar_de_quantidade_zero(
        logs_a_criar, periodos, escola, ontem
    )
    return logs_a_criar


def logs_a_criar_nao_existe_solicitacao_medicao(escola, dietas_autorizadas, ontem):
    logs_a_criar = []
    periodos = escola.periodos_escolares_com_alunos
    dict_periodos = PeriodoEscolar.dict_periodos()
    for periodo in periodos:
        for classificacao in ClassificacaoDieta.objects.all():
            dietas = dietas_autorizadas.filter(
                classificacao=classificacao, escola_destino=escola
            )
            dietas_filtradas_periodo = dietas.filter(
                aluno__periodo_escolar__nome=periodo
            )
            dietas_nao_matriculados = dietas.filter(
                tipo_solicitacao="ALUNO_NAO_MATRICULADO"
            )
            faixas = []
            faixas += append_faixas_dietas(dietas_filtradas_periodo, escola)
            faixas += append_faixas_dietas(dietas_nao_matriculados, escola)
            for faixa, quantidade in Counter(faixas).items():
                log = LogQuantidadeDietasAutorizadasCEI(
                    quantidade=quantidade,
                    escola=escola,
                    data=ontem,
                    classificacao=classificacao,
                    periodo_escolar=dict_periodos[periodo],
                    faixa_etaria=faixa,
                )
                logs_a_criar.append(log)
    logs_a_criar = append_logs_a_criar_de_quantidade_zero(
        logs_a_criar, periodos, escola, ontem
    )
    return logs_a_criar


def gera_logs_dietas_escolas_cei(escola, dietas_autorizadas, ontem):
    try:
        return logs_a_criar_existe_solicitacao_medicao(
            escola, dietas_autorizadas, ontem
        )
    except ObjectDoesNotExist:
        return logs_a_criar_nao_existe_solicitacao_medicao(
            escola, dietas_autorizadas, ontem
        )
