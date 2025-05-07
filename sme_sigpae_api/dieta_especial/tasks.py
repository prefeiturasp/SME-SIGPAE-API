import datetime
import io
import json
import logging

import numpy as np
from celery import shared_task
from rest_framework.exceptions import ValidationError

from sme_sigpae_api.dieta_especial.models import (
    ClassificacaoDieta,
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
    PlanilhaDietasAtivas,
    ProtocoloPadraoDietaEspecial,
    SolicitacaoDietaEspecial,
)
from sme_sigpae_api.escola.utils_escola import get_escolas

from ..dados_comuns.utils import (
    atualiza_central_download,
    atualiza_central_download_com_erro,
    convert_dict_to_querydict,
    converte_numero_em_mes,
    gera_objeto_na_central_download,
)
from ..escola.models import Escola, Lote
from ..escola.utils import faixa_to_string
from ..perfil.models import Usuario
from ..relatorios.relatorios import relatorio_dietas_especiais_terceirizada
from .api.serializers import (
    SolicitacaoDietaEspecialExportXLSXSerializer,
    SolicitacaoDietaEspecialNutriSupervisaoExportXLSXSerializer,
)
from .utils import (
    cancela_dietas_ativas_automaticamente,
    gera_logs_dietas_escolas_cei,
    gera_logs_dietas_escolas_comuns,
    gerar_filtros_relatorio_historico,
    get_logs_historico_dietas,
    inicia_dietas_temporarias,
    termina_dietas_especiais,
)

logger = logging.getLogger(__name__)


# https://docs.celeryproject.org/en/latest/userguide/tasks.html
@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
)
def processa_dietas_especiais_task():
    usuario_admin = Usuario.objects.get(pk=1)
    inicia_dietas_temporarias(usuario=usuario_admin)
    termina_dietas_especiais(usuario=usuario_admin)


@shared_task
def cancela_dietas_ativas_automaticamente_task():
    cancela_dietas_ativas_automaticamente()


@shared_task
def get_escolas_task():
    obj = (
        PlanilhaDietasAtivas.objects.first()
    )  # Tem um problema aqui, e se selecionar outro arquivo?
    arquivo = obj.arquivo
    arquivo_unidades_da_rede = obj.arquivo_unidades_da_rede
    get_escolas(arquivo, arquivo_unidades_da_rede, obj.tempfile, in_memory=True)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gera_pdf_relatorio_dieta_especial_async(user, nome_arquivo, ids_dietas, data):
    from ..dieta_especial.forms import RelatorioDietaForm
    from ..dieta_especial.models import SolicitacaoDietaEspecial
    from ..relatorios.relatorios import relatorio_geral_dieta_especial_pdf

    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        form = RelatorioDietaForm(data)
        if not form.is_valid():
            raise ValidationError(form.errors)
        queryset = SolicitacaoDietaEspecial.objects.filter(id__in=ids_dietas)
        usuario = Usuario.objects.get(username=user)
        arquivo = relatorio_geral_dieta_especial_pdf(form, queryset, usuario)
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")


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


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
)
def gera_logs_dietas_especiais_diariamente():
    logger.info(
        "x-x-x-x Iniciando a geração de logs de dietas especiais autorizadas diaria x-x-x-x"
    )
    ontem = datetime.date.today() - datetime.timedelta(days=1)
    dietas_autorizadas = SolicitacaoDietaEspecial.objects.filter(
        tipo_solicitacao__in=["COMUM", "ALTERACAO_UE", "ALUNO_NAO_MATRICULADO"],
        status__in=[
            SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            SolicitacaoDietaEspecial.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            SolicitacaoDietaEspecial.workflow_class.ESCOLA_SOLICITOU_INATIVACAO,
        ],
        ativo=True,
    )
    logs_a_criar_escolas_comuns = []
    logs_a_criar_escolas_cei = []
    escolas = Escola.objects.filter(tipo_gestao__nome="TERC TOTAL")
    for index, escola in enumerate(escolas):
        msg = "x-x-x-x Logs de quantidade de dietas autorizadas para a escola"
        msg += f" {escola.nome} ({index + 1}/{(escolas).count()}) x-x-x-x"
        logger.info(msg)
        if escola.eh_cei:
            logs_escola = gera_logs_dietas_escolas_cei(
                escola, dietas_autorizadas, ontem
            )
            logs_escola = cria_logs_totais_cei_por_faixa_etaria(
                logs_escola, ontem, escola
            )
            logs_a_criar_escolas_cei += logs_escola
        elif escola.eh_cemei:
            logs_a_criar_escolas_comuns += gera_logs_dietas_escolas_comuns(
                escola, dietas_autorizadas, ontem
            )

            logs_escola = gera_logs_dietas_escolas_cei(
                escola, dietas_autorizadas, ontem
            )
            logs_escola = cria_logs_totais_cei_por_faixa_etaria(
                logs_escola, ontem, escola
            )
            logs_a_criar_escolas_cei += logs_escola
        else:
            logs_a_criar_escolas_comuns += gera_logs_dietas_escolas_comuns(
                escola, dietas_autorizadas, ontem
            )
    LogQuantidadeDietasAutorizadas.objects.bulk_create(logs_a_criar_escolas_comuns)
    LogQuantidadeDietasAutorizadasCEI.objects.bulk_create(logs_a_criar_escolas_cei)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gera_pdf_relatorio_dietas_especiais_terceirizadas_async(
    user, nome_arquivo, ids_dietas, data, filtros
):
    from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial

    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        query_set = SolicitacaoDietaEspecial.objects.filter(id__in=ids_dietas)
        usuario = Usuario.objects.get(username=user)
        solicitacoes = []
        for solicitacao in query_set:
            classificacao = (
                solicitacao.classificacao.nome if solicitacao.classificacao else "--"
            )
            dados_solicitacoes = {
                "codigo_eol_aluno": solicitacao.aluno.codigo_eol,
                "nome_aluno": solicitacao.aluno.nome,
                "nome_escola": solicitacao.escola.nome,
                "classificacao": classificacao,
                "protocolo_padrao": solicitacao.nome_protocolo,
                "alergias_intolerancias": solicitacao.alergias_intolerancias,
            }
            if data.get("status_selecionado") == "CANCELADAS":
                dados_solicitacoes["data_cancelamento"] = solicitacao.data_ultimo_log
            solicitacoes.append(dados_solicitacoes)
        exibir_diagnostico = usuario.tipo_usuario != "terceirizada"
        now = datetime.datetime.now()
        data_pt = f"{now.day} de {converte_numero_em_mes(now.month)} de {now.year}"
        dados = {
            "usuario_nome": usuario.nome,
            "status": data.get("status_selecionado").lower(),
            "filtros": filtros,
            "solicitacoes": solicitacoes,
            "quantidade_solicitacoes": query_set.count(),
            "diagnostico": exibir_diagnostico,
            "data_extracao": data_pt,
        }
        arquivo = relatorio_dietas_especiais_terceirizada(dados=dados)
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")


def build_titulo(lotes, status, classificacoes, protocolos, data_inicial, data_final):
    titulo = (
        f'Dietas {"Autorizadas" if status.upper() == "AUTORIZADAS" else "Canceladas"}:'
    )
    if lotes:
        nomes_lotes = ",".join(
            [lote.nome for lote in Lote.objects.filter(uuid__in=lotes)]
        )
        titulo += f" | {nomes_lotes}"
    if classificacoes:
        nomes_classificacoes = ",".join(
            [
                classificacao.nome
                for classificacao in ClassificacaoDieta.objects.filter(
                    id__in=classificacoes
                )
            ]
        )
        titulo += f" | Classificação(ões) da dieta: {nomes_classificacoes}"
    if protocolos:
        nomes_protocolos = ", ".join(
            [
                protocolo.nome_protocolo
                for protocolo in ProtocoloPadraoDietaEspecial.objects.filter(
                    uuid__in=protocolos
                )
            ]
        )
        titulo += f" | Protocolo(s) padrão(ões): {nomes_protocolos}"
    if data_inicial:
        titulo += f" | Data inicial: {data_inicial}"
    if data_final:
        titulo += f" | Data final: {data_final}"
    return titulo


def build_xlsx(
    output,
    serializer,
    queryset,
    status,
    lotes,
    classificacoes,
    protocolos,
    data_inicial,
    data_final,
    exibir_diagnostico=False,
):
    import pandas as pd

    xlwriter = pd.ExcelWriter(output, engine="xlsxwriter")

    df = pd.DataFrame(serializer.data)

    # Adiciona linhas em branco no comeco do arquivo
    df_auxiliar = pd.DataFrame([[np.nan] * len(df.columns)], columns=df.columns)
    df = df_auxiliar.append(df, ignore_index=True)
    df = df_auxiliar.append(df, ignore_index=True)
    df = df_auxiliar.append(df, ignore_index=True)

    df.to_excel(xlwriter, "Solicitações de dieta especial")
    workbook = xlwriter.book
    worksheet = xlwriter.sheets["Solicitações de dieta especial"]
    worksheet.set_row(0, 30)
    worksheet.set_row(1, 30)
    worksheet.set_column("B:F", 30)
    merge_format = workbook.add_format({"align": "center", "bg_color": "#a9d18e"})
    merge_format.set_align("vcenter")
    cell_format = workbook.add_format()
    cell_format.set_text_wrap()
    cell_format.set_align("vcenter")
    v_center_format = workbook.add_format()
    v_center_format.set_align("vcenter")
    single_cell_format = workbook.add_format({"bg_color": "#a9d18e"})
    len_cols = len(df.columns)
    worksheet.merge_range(
        0, 0, 0, len_cols, "Relatório de dietas especiais", merge_format
    )
    titulo = build_titulo(
        lotes, status, classificacoes, protocolos, data_inicial, data_final
    )
    worksheet.merge_range(1, 0, 2, len_cols - 1, titulo, cell_format)
    worksheet.merge_range(
        1,
        len_cols,
        2,
        len_cols,
        f"Total de dietas: {queryset.count()}",
        v_center_format,
    )
    worksheet.write(3, 1, "COD.EOL do Aluno", single_cell_format)
    worksheet.write(3, 2, "Nome do Aluno", single_cell_format)
    worksheet.write(3, 3, "Nome da Escola", single_cell_format)
    worksheet.write(3, 4, "Classificação da dieta", single_cell_format)
    worksheet.write(
        3,
        5,
        "Relação por Diagnóstico" if exibir_diagnostico else "Protocolo Padrão",
        single_cell_format,
    )
    if status.upper() == "CANCELADAS":
        worksheet.set_column("G:G", 30)
        worksheet.write(3, 6, "Data de cancelamento", single_cell_format)
    df.reset_index(drop=True, inplace=True)
    xlwriter.save()
    output.seek(0)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gera_xlsx_relatorio_dietas_especiais_terceirizadas_async(
    user, nome_arquivo, ids_dietas, data, lotes, classificacoes, protocolos_padrao
):
    from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial

    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        query_set = SolicitacaoDietaEspecial.objects.filter(id__in=ids_dietas)
        usuario = Usuario.objects.get(username=user)
        solicitacoes = []
        for solicitacao in query_set:
            classificacao = (
                solicitacao.classificacao.nome if solicitacao.classificacao else "--"
            )
            dados_solicitacoes = {
                "codigo_eol_aluno": solicitacao.aluno.codigo_eol,
                "nome_aluno": solicitacao.aluno.nome,
                "nome_escola": solicitacao.escola.nome,
                "classificacao": classificacao,
                "protocolo_padrao": solicitacao.nome_protocolo,
                "alergias_intolerancias": solicitacao.alergias_intolerancias,
            }
            if data.get("status_selecionado") == "CANCELADAS":
                dados_solicitacoes["data_cancelamento"] = solicitacao.data_ultimo_log
            solicitacoes.append(dados_solicitacoes)
        exibir_diagnostico = usuario.tipo_usuario != "terceirizada"
        if exibir_diagnostico:
            serializer = SolicitacaoDietaEspecialNutriSupervisaoExportXLSXSerializer(
                query_set, context={"status": data.get("status_selecionado")}, many=True
            )
        else:
            serializer = SolicitacaoDietaEspecialExportXLSXSerializer(
                query_set, context={"status": data.get("status_selecionado")}, many=True
            )
        data_inicial = data.get("data_inicial", None)
        data_final = data.get("data_final", None)

        output = io.BytesIO()
        build_xlsx(
            output,
            serializer,
            query_set,
            data.get("status_selecionado"),
            lotes,
            classificacoes,
            protocolos_padrao,
            data_inicial,
            data_final,
            exibir_diagnostico,
        )
        atualiza_central_download(obj_central_download, nome_arquivo, output.read())
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")


def get_faixa_etaria_cei(log: dict, faixa_etaria: str) -> str:
    if log["tipo_unidade"] not in [
        "CEI DIRET",
        "CEU CEI",
        "CEI",
        "CCI",
        "CCI/CIPS",
        "CEI CEU",
    ]:
        return faixa_etaria
    faixa_etaria = faixa_to_string(log["inicio"], log["fim"])
    return faixa_etaria


def get_faixa_etaria_cemei(log: dict, faixa_etaria: str) -> str:
    if log["tipo_unidade"] not in ["CEMEI", "CEU CEMEI"]:
        return faixa_etaria
    if log["inicio"]:
        faixa_etaria = faixa_to_string(log["inicio"], log["fim"])
    else:
        faixa_etaria = "Infantil"
    return faixa_etaria


def get_faixa_etaria_emebs(log: dict, faixa_etaria: str) -> str:
    if log["tipo_unidade"] != "EMEBS":
        return faixa_etaria
    if log["infantil_ou_fundamental"] == "INFANTIL":
        faixa_etaria = "Infantil (4 a 6 anos)"
    elif log["infantil_ou_fundamental"] == "FUNDAMENTAL":
        faixa_etaria = "Fundamental (acima de 6 anos)"
    return faixa_etaria


def get_faixa_etaria(log: dict) -> str:
    faixa_etaria = ""
    faixa_etaria = get_faixa_etaria_cei(log, faixa_etaria)
    faixa_etaria = get_faixa_etaria_cemei(log, faixa_etaria)
    faixa_etaria = get_faixa_etaria_emebs(log, faixa_etaria)
    return faixa_etaria


def build_xlsx_relatorio_historico_dietas(output, logs_dietas: list[dict]) -> None:
    import pandas as pd

    xlwriter = pd.ExcelWriter(output, engine="xlsxwriter")

    logs_dietas_formatados = [
        {
            "dre_lote": f"{log['lote']} - DRE {log['dre']}",
            "unidade_educacional": log["nome_escola"],
            "classificacao_da_dieta": log["nome_classificacao"],
            "periodo": log["nome_periodo_escolar"],
            "faixa_etaria": get_faixa_etaria(log),
            "dietas_autorizadas": log["quantidade_total"],
            "data_de_referencia": log["data"].strftime("%d/%m/%Y"),
        }
        for log in logs_dietas
    ]

    df = pd.DataFrame(logs_dietas_formatados)

    # Adiciona linhas em branco no comeco do arquivo
    df_auxiliar = pd.DataFrame([[np.nan] * len(df.columns)], columns=df.columns)
    df = df_auxiliar.append(df, ignore_index=True)
    df = df_auxiliar.append(df, ignore_index=True)
    df = df_auxiliar.append(df, ignore_index=True)

    df.to_excel(xlwriter, "Histórico de Dietas Autorizadas")
    workbook = xlwriter.book
    worksheet = xlwriter.sheets["Histórico de Dietas Autorizadas"]
    worksheet.set_row(0, 30)
    worksheet.set_row(1, 30)
    worksheet.set_column("B:H", 30)
    worksheet.set_column("C:C", 50)
    merge_format = workbook.add_format({"align": "center", "bg_color": "#a9d18e"})
    merge_format.set_align("vcenter")
    cell_format = workbook.add_format()
    cell_format.set_text_wrap()
    cell_format.set_align("vcenter")
    v_center_format = workbook.add_format()
    v_center_format.set_align("vcenter")
    single_cell_format = workbook.add_format({"bg_color": "#a9d18e"})
    len_cols = len(df.columns)
    worksheet.merge_range(
        0, 0, 0, len_cols, "Relatório Histórico de Dietas Autorizadas", merge_format
    )
    titulo = "xablau"
    worksheet.merge_range(1, 0, 2, len_cols, titulo, cell_format)
    worksheet.write(3, 1, "Lote/DRE", single_cell_format)
    worksheet.write(3, 2, "Unidade Educacional", single_cell_format)
    worksheet.write(3, 3, "Classificação da Dieta", single_cell_format)
    worksheet.write(3, 4, "Período", single_cell_format)
    worksheet.write(3, 5, "Faixa Etária", single_cell_format)
    worksheet.write(3, 6, "Dietas Autorizadas", single_cell_format)
    worksheet.write(3, 7, "Data de Referência", single_cell_format)
    df.reset_index(drop=True, inplace=True)
    xlwriter.save()
    output.seek(0)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gera_xlsx_relatorio_historico_dietas_especiais_async(user, nome_arquivo, data):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        data_json = json.loads(data)
        querydict_params = convert_dict_to_querydict(data_json)
        filtros, data_dieta = gerar_filtros_relatorio_historico(
            querydict_params, eh_exportacao=True
        )
        logs_dietas = get_logs_historico_dietas(filtros)
        output = io.BytesIO()
        build_xlsx_relatorio_historico_dietas(output, logs_dietas)
        atualiza_central_download(obj_central_download, nome_arquivo, output.read())
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")
