import logging
import re
from calendar import monthrange
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List

from django.db.models import Case, Q, Value, When
from openpyxl import Workbook
from rest_framework.pagination import PageNumberPagination

from sme_sigpae_api.eol_servico.utils import EOLServicoSGP

from ..escola import models

logger = logging.getLogger("sigpae.taskEscola")


def meses_to_mes_e_ano_string(total_meses):
    anos = total_meses // 12
    meses = total_meses % 12

    saida = ""

    if anos > 0:
        saida = f"{anos:02d} {'ano' if anos == 1 else 'anos'}"
        if meses > 0:
            saida += " e "

    if anos == 0 or meses > 0:
        saida += f"{meses:02d} {'mês' if meses == 1 else 'meses'}"

    return saida


def faixa_to_string(inicio, fim):
    if fim - inicio == 1:
        return meses_to_mes_e_ano_string(inicio)
    if inicio == 0:
        str_inicio = "0 meses"
    else:
        str_inicio = (
            meses_to_mes_e_ano_string(inicio) if inicio >= 12 else f"{inicio:02d}"
        )
    str_fim = "06 anos" if fim == 72 else meses_to_mes_e_ano_string(fim - 1)

    return f"{str_inicio} a {str_fim}"


def string_to_faixa(faixa_str):
    if "a" in faixa_str:
        str_inicio, str_fim = faixa_str.split(" a ")
    else:
        str_inicio = str_fim = faixa_str

    inicio = string_to_meses(str_inicio)
    fim = (
        string_to_meses(str_fim) + 1
    )  # Adicionamos 1 porque a função faixa_to_string subtrai 1 do fim

    return inicio, fim


def string_to_meses(str_meses):
    if "ano" in str_meses:
        anos, restante = str_meses.split(" ano")
        anos = int(anos)
        meses = 0
        if " e " in restante:
            _, str_mes = restante.split(" e ")
            meses = int(str_mes.split(" ")[0])
        total_meses = anos * 12 + meses
    else:
        total_meses = int(str_meses.split(" ")[0])
    return total_meses


def remove_acentos(texto):
    resultado = re.sub("[àáâãäå]", "a", texto)
    resultado = re.sub("[èéêë]", "e", resultado)
    resultado = re.sub("[ìíîï]", "i", resultado)
    return resultado


def update_datetime_LogAlunosMatriculadosPeriodoEscola():
    from sme_sigpae_api.escola.models import LogAlunosMatriculadosPeriodoEscola

    hoje = date.today()
    logs_hoje = LogAlunosMatriculadosPeriodoEscola.objects.filter(criado_em__date=hoje)

    for log in logs_hoje:
        log.criado_em = log.criado_em - timedelta(days=1)
        log.save()


def registra_quantidade_matriculados(matriculas, ontem, tipo_turma):  # noqa C901
    import ast

    import pandas as pd

    from sme_sigpae_api.escola.models import (
        AlunosMatriculadosPeriodoEscola,
        Escola,
        LogAlunosMatriculadosPeriodoEscola,
        PeriodoEscolar,
    )

    objs = []
    matriculas = (
        pd.DataFrame(matriculas).astype(str).drop_duplicates().to_dict("records")
    )
    for matricula in matriculas:
        escola = Escola.objects.filter(codigo_eol=matricula["codigoEolEscola"]).first()
        turnos = ast.literal_eval(matricula["turnos"])
        periodos = []
        for turno_resp in turnos:
            turno = remove_acentos(turno_resp["turno"])
            periodo = PeriodoEscolar.objects.filter(nome=turno.upper()).first()
            if not periodo:
                logger.debug(
                    f'Periodo {turno_resp["turno"]} não encontrado na tabela de Períodos'
                )
                continue
            periodos.append(periodo)
            if tipo_turma == "REGULAR":
                create_update_objeto_escola_periodo_escolar(
                    escola, periodo, turno_resp["quantidade"]
                )
            matricula_sigpae = AlunosMatriculadosPeriodoEscola.objects.filter(
                tipo_turma=tipo_turma, escola=escola, periodo_escolar=periodo
            ).first()
            if matricula_sigpae:
                matricula_sigpae.quantidade_alunos = turno_resp["quantidade"]
                objs.append(matricula_sigpae)
            else:
                AlunosMatriculadosPeriodoEscola.criar(
                    escola=escola,
                    periodo_escolar=periodo,
                    quantidade_alunos=turno_resp["quantidade"],
                    tipo_turma=tipo_turma,
                )
            LogAlunosMatriculadosPeriodoEscola.criar(
                escola=escola,
                periodo_escolar=periodo,
                quantidade_alunos=turno_resp["quantidade"],
                data=ontem,
                tipo_turma=tipo_turma,
            )

        AlunosMatriculadosPeriodoEscola.objects.filter(
            tipo_turma=tipo_turma, escola=escola
        ).exclude(periodo_escolar__in=periodos).delete()
    AlunosMatriculadosPeriodoEscola.objects.bulk_update(objs, ["quantidade_alunos"])
    update_datetime_LogAlunosMatriculadosPeriodoEscola()


def create_update_objeto_escola_periodo_escolar(
    escola, periodo, quantidade_alunos_periodo
):
    from sme_sigpae_api.escola.models import EscolaPeriodoEscolar

    escola_periodo, created = EscolaPeriodoEscolar.objects.get_or_create(
        periodo_escolar=periodo, escola=escola
    )
    if escola_periodo.quantidade_alunos != quantidade_alunos_periodo:
        escola_periodo.quantidade_alunos = quantidade_alunos_periodo
        escola_periodo.save()


def duplica_dia_anterior(dre, dois_dias_atras, ontem, tipo_turma_name):
    from sme_sigpae_api.escola.models import LogAlunosMatriculadosPeriodoEscola

    logs = LogAlunosMatriculadosPeriodoEscola.objects.filter(
        escola__diretoria_regional=dre,
        criado_em__date=dois_dias_atras,
        tipo_turma=tipo_turma_name,
    )
    for log in logs:
        LogAlunosMatriculadosPeriodoEscola.criar(
            escola=log.escola,
            periodo_escolar=log.periodo_escolar,
            quantidade_alunos=log.quantidade_alunos,
            data=ontem,
            tipo_turma=tipo_turma_name,
        )
    update_datetime_LogAlunosMatriculadosPeriodoEscola()


def registro_quantidade_alunos_matriculados_por_escola_periodo(tipo_turma):
    from sme_sigpae_api.escola.models import DiretoriaRegional

    hoje = date.today()
    ontem = hoje - timedelta(days=1)
    dres = DiretoriaRegional.objects.all()
    total = len(dres)
    cont = 1
    for dre in dres:
        logger.debug(f"Processando {cont} de {total}")
        logger.debug(
            f"""Consultando matriculados da dre com Nome: {dre.nome}
        e código eol: {dre.codigo_eol}, data: {hoje.strftime('%Y-%m-%d')} para o tipo turma {tipo_turma.name}"""
        )
        try:
            resposta = EOLServicoSGP.matricula_por_escola(
                codigo_eol=dre.codigo_eol,
                data=hoje.strftime("%Y-%m-%d"),
                tipo_turma=tipo_turma.value,
            )
            logger.debug(resposta)

            registra_quantidade_matriculados(resposta, ontem, tipo_turma.name)
        except Exception as e:
            dois_dias_atras = ontem - timedelta(days=1)
            duplica_dia_anterior(dre, dois_dias_atras, ontem, tipo_turma.name)
            logger.error(
                f"Houve um erro inesperado ao consultar a Diretoria Regional {dre} : {str(e)}; "
                "as quantidades de alunos foram duplicadas do dia anterior"
            )
        cont += 1


def processa_dias_letivos(lista_dias_letivos, escola):
    from sme_sigpae_api.escola.models import DiaCalendario

    for dia_dict in lista_dias_letivos:
        data = datetime.strptime(dia_dict["data"], "%Y-%m-%dT00:00:00")
        dia_calendario: DiaCalendario = DiaCalendario.objects.filter(
            escola=escola,
            data__year=data.year,
            data__month=data.month,
            data__day=data.day,
        ).first()
        if not dia_calendario:
            dia_calendario = DiaCalendario.objects.create(
                escola=escola, data=data, dia_letivo=dia_dict["ehLetivo"]
            )
        else:
            dia_calendario.dia_letivo = dia_dict["ehLetivo"]
            dia_calendario.save()


def calendario_sgp():  # noqa C901
    import pandas as pd

    from sme_sigpae_api.escola.models import Escola
    from sme_sigpae_api.escola.services import NovoSGPServico

    hoje = date.today()
    escolas = Escola.objects.all()
    total = len(escolas)
    for cont, escola in enumerate(escolas, 1):
        logger.debug(f"Processando {cont} de {total}")
        logger.debug(
            f"""Consultando dias letivos da escola com Nome: {escola.nome}
        e código eol: {escola.codigo_eol}, data: {hoje.strftime('%Y-%m-%d')}"""
        )
        try:
            data_inicio = hoje.strftime("%Y-%m-%d")
            data_final = (hoje + pd.DateOffset(months=3)).date()
            data_fim = data_final.strftime("%Y-%m-%d")

            resposta = NovoSGPServico.dias_letivos(
                codigo_eol=escola.codigo_eol, data_inicio=data_inicio, data_fim=data_fim
            )
            logger.debug(resposta)

            processa_dias_letivos(resposta, escola)
        except Exception as e:
            logger.error(f"Dados não encontrados para escola {escola} : {str(e)}")
            logger.debug("Tentando buscar dias letivos no novo sgp para turno da noite")
            try:
                resposta = NovoSGPServico.dias_letivos(
                    codigo_eol=escola.codigo_eol,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    tipo_turno=3,
                )

                processa_dias_letivos(resposta, escola)
            except Exception as e:
                logger.error(
                    f"Erro ao buscar por turno noite para escola {escola} : {str(e)}"
                )


class EscolaSimplissimaPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"


def lotes_endpoint_filtrar_relatorio_alunos_matriculados(instituicao, Codae, Lote):
    if isinstance(instituicao, Codae):
        lotes = Lote.objects.all()
    else:
        lotes = instituicao.lotes.filter(escolas__isnull=False)
    return lotes


def deletar_alunos_periodo_parcial_outras_escolas(escola, data_referencia):
    from .models import AlunoPeriodoParcial

    AlunoPeriodoParcial.objects.filter(
        solicitacao_medicao_inicial__escola=escola,
        solicitacao_medicao_inicial__mes=str(data_referencia.month).zfill(2),
        solicitacao_medicao_inicial__ano=str(data_referencia.year),
    ).exclude(aluno__escola__codigo_eol=escola.codigo_eol).delete()


def eh_dia_sem_atividade_escolar(escola, data, alteracao):
    from sme_sigpae_api.escola.models import DiaCalendario, DiaSuspensaoAtividades

    try:
        dia_calendario = DiaCalendario.objects.get(escola=escola, data=data)
        eh_dia_letivo = dia_calendario.dia_letivo
    except DiaCalendario.DoesNotExist:
        eh_dia_letivo = True
    eh_dia_de_suspensao = DiaSuspensaoAtividades.eh_dia_de_suspensao(escola, data)
    periodos_escolares_alteracao = alteracao.substituicoes.values_list(
        "periodo_escolar"
    )
    return (
        (not eh_dia_letivo or eh_dia_de_suspensao)
        and not escola.grupos_inclusoes.filter(
            inclusoes_normais__cancelado=False,
            inclusoes_normais__data=data,
            quantidades_por_periodo__periodo_escolar__in=periodos_escolares_alteracao,
            status="CODAE_AUTORIZADO",
        ).exists()
        and not escola.inclusoes_continuas.filter(
            status="CODAE_AUTORIZADO",
            data_inicial__lte=data,
            data_final__gte=data,
            quantidades_por_periodo__periodo_escolar__in=periodos_escolares_alteracao,
            quantidades_por_periodo__cancelado=False,
        )
        .filter(
            Q(quantidades_por_periodo__dias_semana__icontains=DiaCalendario.SABADO)
            | Q(quantidades_por_periodo__dias_semana__icontains=DiaCalendario.DOMINGO)
        )
        .exists()
    )


def analise_alunos_dietas_somente_uma_data(
    datetime_autorizacao, data_inicial, data_final, dieta, alunos_com_dietas_autorizadas
):
    from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario

    if (
        data_inicial is not None
        and data_final is not None
        and data_inicial == data_final
    ):
        if datetime_autorizacao < datetime.strptime(data_inicial, "%Y-%m-%d") and (
            (dieta.logs.last().status_evento == LogSolicitacoesUsuario.CODAE_AUTORIZOU)
            or (
                dieta.logs.last().status_evento
                != LogSolicitacoesUsuario.CODAE_AUTORIZOU
                and dieta.logs.last().criado_em
                > datetime.strptime(data_inicial, "%Y-%m-%d")
            )
        ):
            alunos_com_dietas_autorizadas.append(
                {
                    "aluno": dieta.aluno.nome,
                    "tipo_dieta": dieta.classificacao.nome,
                    "data_autorizacao": dieta.data_autorizacao,
                }
            )
    return alunos_com_dietas_autorizadas


def get_alunos_com_dietas_autorizadas(query_params, escola):
    from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
    from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial

    solicitacoes_dietas_comuns = SolicitacaoDietaEspecial.objects.filter(
        aluno__escola=escola, tipo_solicitacao="COMUM"
    )
    dietas_com_log_autorizado = [
        s
        for s in solicitacoes_dietas_comuns
        if s.logs.filter(status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU)
    ]
    data_inicial = query_params.get("data_inicial")
    data_final = query_params.get("data_final")
    alunos_com_dietas_autorizadas = []
    for dieta in dietas_com_log_autorizado:
        datetime_autorizacao = datetime.strptime(dieta.data_autorizacao, "%d/%m/%Y")
        if data_inicial and data_final:
            if (
                datetime_autorizacao >= datetime.strptime(data_inicial, "%Y-%m-%d")
                and datetime_autorizacao <= datetime.strptime(data_final, "%Y-%m-%d")
            ) or (
                datetime_autorizacao < datetime.strptime(data_inicial, "%Y-%m-%d")
                and (
                    (
                        dieta.logs.last().status_evento
                        == LogSolicitacoesUsuario.CODAE_AUTORIZOU
                    )
                    or (
                        dieta.logs.last().status_evento
                        != LogSolicitacoesUsuario.CODAE_AUTORIZOU
                        and dieta.logs.last().criado_em
                        > datetime.strptime(data_inicial, "%Y-%m-%d")
                    )
                )
            ):
                alunos_com_dietas_autorizadas.append(
                    {
                        "aluno": dieta.aluno.nome,
                        "tipo_dieta": dieta.classificacao.nome,
                        "data_autorizacao": dieta.data_autorizacao,
                    }
                )
        elif not data_inicial and not data_final:
            mes_ano = query_params.get("mes_ano")
            mes, ano = mes_ano.split("_")
            _, num_dias = monthrange(
                int(ano),
                int(mes),
            )
            if (
                datetime_autorizacao
                >= datetime.strptime(f"{1}/{mes}/{ano}", "%d/%m/%Y")
                and datetime_autorizacao
                <= datetime.strptime(f"{num_dias}/{mes}/{ano}", "%d/%m/%Y")
            ) or (
                datetime_autorizacao < datetime.strptime(f"{1}/{mes}/{ano}", "%d/%m/%Y")
                and (
                    (
                        dieta.logs.last().status_evento
                        == LogSolicitacoesUsuario.CODAE_AUTORIZOU
                    )
                    or (
                        dieta.logs.last().status_evento
                        != LogSolicitacoesUsuario.CODAE_AUTORIZOU
                        and dieta.logs.last().criado_em
                        > datetime.strptime(f"{1}/{mes}/{ano}", "%d/%m/%Y")
                    )
                )
            ):
                alunos_com_dietas_autorizadas.append(
                    {
                        "aluno": dieta.aluno.nome,
                        "tipo_dieta": dieta.classificacao.nome,
                        "data_autorizacao": dieta.data_autorizacao,
                    }
                )
        alunos_com_dietas_autorizadas = analise_alunos_dietas_somente_uma_data(
            datetime_autorizacao,
            data_inicial,
            data_final,
            dieta,
            alunos_com_dietas_autorizadas,
        )
    return alunos_com_dietas_autorizadas


def trata_filtro_data_relatorio_controle_frequencia_pdf(
    filtros, query_params, ano, mes, num_dias
):
    hoje = date.today()
    ontem = hoje - timedelta(days=1)
    mes_seguinte = False
    _, _, dia_inicial = (
        query_params.get("data_inicial").split("-")
        if query_params.get("data_inicial")
        else [None, None, None]
    )
    if int(mes) > hoje.month:
        filtros["data"] = f"{hoje.year}-{hoje.month}-{ontem.day}"
        mes_seguinte = True
    elif (
        int(mes) == hoje.month
        and query_params.get("data_inicial") == query_params.get("data_final")
        and dia_inicial
        and int(dia_inicial) >= hoje.day
    ):
        filtros["data"] = ontem
    elif int(mes) == hoje.month and query_params.get(
        "data_inicial"
    ) != query_params.get("data_final"):
        if dia_inicial and int(dia_inicial) >= hoje.day:
            filtros["data"] = ontem
    else:
        filtros["data__gte"] = query_params.get("data_inicial", f"{ano}-{mes}-{'01'}")
        filtros["data__lte"] = query_params.get("data_final", f"{ano}-{mes}-{num_dias}")
    return mes_seguinte


def eh_mes_atual(query_params):
    mes_ano = query_params.get("mes_ano")
    mes, _ = mes_ano.split("_")
    hoje = date.today()
    return int(mes) == hoje.month


def alunos_por_faixa_append(alunos_por_faixa, aluno):
    if aluno not in alunos_por_faixa:
        alunos_por_faixa.append(aluno)
    return alunos_por_faixa


def dias_append(dias, dia, alunos_por_dia):
    return dias.append(
        {
            "dia": f"{dia:02d}",
            "alunos_por_dia": alunos_por_dia,
        }
    )


def trata_dados_futuro_mes_atual(
    queryset_periodo_faixa,
    log_periodo_faixa,
    dias,
    alunos_por_dia,
    num_dias,
    query_params,
):
    data_inicial = query_params.get("data_inicial")
    data_final = query_params.get("data_final")
    hoje = date.today()
    if queryset_periodo_faixa.order_by("data").last().uuid == log_periodo_faixa.uuid:
        if data_inicial and data_inicial == data_final:
            ano, mes, dia_inicial = query_params.get("data_inicial").split("-")
            datetime_inicial = date(int(ano), int(mes), int(dia_inicial))
            if datetime_inicial >= hoje:
                dias_append(dias, int(dia_inicial), alunos_por_dia)
        else:
            dia = log_periodo_faixa.data.day + 1
            while int(dia) <= int(num_dias):
                dias_append(dias, dia, alunos_por_dia)
                dia += 1


def trata_dados_futuro(
    mes_atual,
    log_periodo_faixa,
    alunos_por_dia,
    alunos_por_faixa,
    dias,
    query_params,
    queryset_periodo,
    queryset_periodo_faixa,
    uuid_faixas,
):
    for log_aluno_dia in log_periodo_faixa.logs_alunos_por_dia.all():
        data_nascimento = log_aluno_dia.aluno.data_nascimento
        aluno = f"{log_aluno_dia.aluno.nome} - {data_nascimento.day:02d}/{data_nascimento.month:02d}/{data_nascimento.year}"
        alunos_por_dia.append(aluno)
        alunos_por_faixa_append(alunos_por_faixa, aluno)
    mes_ano = query_params.get("mes_ano")
    mes, ano = mes_ano.split("_")
    _, num_dias = monthrange(
        int(ano),
        int(mes),
    )
    if mes_atual:
        dias_append(dias, log_periodo_faixa.data.day, alunos_por_dia)
        trata_dados_futuro_mes_atual(
            queryset_periodo_faixa,
            log_periodo_faixa,
            dias,
            alunos_por_dia,
            num_dias,
            query_params,
        )
    else:
        dia = 1
        if query_params.get("data_inicial"):
            _, _, dia_inicial = query_params.get("data_inicial").split("-")
            dia = int(dia_inicial)
            num_dias = 1
        if query_params.get("data_final"):
            _, _, dia_final = query_params.get("data_final").split("-")
            num_dias = int(dia_final)
        while dia <= num_dias:
            dias_append(dias, dia, alunos_por_dia)
            dia += 1


def formata_periodos_pdf_controle_frequencia(
    qtd_matriculados, queryset, query_params, escola, mes_seguinte
):
    from .models import FaixaEtaria

    periodos = []
    mes_atual = eh_mes_atual(query_params)
    for periodo_key in qtd_matriculados["periodos"].keys():
        faixas = []
        queryset_periodo = queryset.filter(periodo_escolar__nome=periodo_key)
        uuid_faixas = list(
            set(queryset_periodo.values_list("faixa_etaria__uuid", flat=True))
        )
        for uuid_faixa in uuid_faixas:
            queryset_periodo_faixa = queryset_periodo.filter(
                faixa_etaria__uuid=uuid_faixa
            )
            dias = []
            alunos_por_faixa = []
            for log_periodo_faixa in queryset_periodo_faixa:
                alunos_por_dia = []
                if mes_seguinte or mes_atual:
                    trata_dados_futuro(
                        mes_atual,
                        log_periodo_faixa,
                        alunos_por_dia,
                        alunos_por_faixa,
                        dias,
                        query_params,
                        queryset_periodo,
                        queryset_periodo_faixa,
                        uuid_faixas,
                    )
                else:
                    for log_aluno_dia in log_periodo_faixa.logs_alunos_por_dia.all():
                        data_nascimento = log_aluno_dia.aluno.data_nascimento
                        aluno = f"{log_aluno_dia.aluno.nome} - {data_nascimento.day:02d}/{data_nascimento.month:02d}/{data_nascimento.year}"
                        alunos_por_dia.append(aluno)
                        alunos_por_faixa_append(alunos_por_faixa, aluno)
                    dias_append(dias, log_periodo_faixa.data.day, alunos_por_dia)
            faixas.append(
                {
                    "nome_faixa": FaixaEtaria.objects.get(uuid=uuid_faixa).__str__(),
                    "dias": dias,
                    "alunos_por_faixa": alunos_por_faixa,
                }
            )
        alunos_com_dietas_autorizadas = get_alunos_com_dietas_autorizadas(
            query_params, escola
        )
        periodos.append(
            {
                "periodo": periodo_key,
                "quantidade": qtd_matriculados["periodos"][periodo_key],
                "faixas": faixas,
                "alunos_com_dietas_autorizadas": alunos_com_dietas_autorizadas,
            }
        )
    return periodos


def ordenar_alunos_matriculados(queryset):
    ordenacao = Case(
        When(
            tipo_turma=models.TipoTurma.REGULAR.name,
            periodo_escolar__nome="MANHA",
            then=Value(1),
        ),
        When(
            tipo_turma=models.TipoTurma.REGULAR.name,
            periodo_escolar__nome="TARDE",
            then=Value(2),
        ),
        When(
            tipo_turma=models.TipoTurma.REGULAR.name,
            periodo_escolar__nome="INTEGRAL",
            then=Value(3),
        ),
        When(
            tipo_turma=models.TipoTurma.REGULAR.name,
            periodo_escolar__nome="NOITE",
            then=Value(4),
        ),
        When(
            tipo_turma=models.TipoTurma.PROGRAMAS.name,
            periodo_escolar__nome="MANHA",
            then=Value(5),
        ),
        When(
            tipo_turma=models.TipoTurma.PROGRAMAS.name,
            periodo_escolar__nome="INTERMEDIARIO",
            then=Value(6),
        ),
        When(
            tipo_turma=models.TipoTurma.PROGRAMAS.name,
            periodo_escolar__nome="TARDE",
            then=Value(7),
        ),
        When(
            tipo_turma=models.TipoTurma.PROGRAMAS.name,
            periodo_escolar__nome="VESPERTINO",
            then=Value(8),
        ),
        When(
            tipo_turma=models.TipoTurma.PROGRAMAS.name,
            periodo_escolar__nome="NOITE",
            then=Value(9),
        ),
    )
    queryset = queryset.annotate(ordering=ordenacao).order_by(
        "escola__nome", "ordering"
    )
    return queryset


def cria_arquivo_excel(caminho_arquivo: Path, dados: List[Dict[str, str]]):
    """
    Cria um arquivo Excel a partir dos dados fornecidos.s
    """
    wb = Workbook()
    ws = wb.active
    ws.append(list(dados[0].keys()))
    for row in dados:
        ws.append(list(row.values()))
    wb.save(caminho_arquivo)
