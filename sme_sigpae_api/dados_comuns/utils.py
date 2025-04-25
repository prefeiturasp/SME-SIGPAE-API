import base64
import datetime
import logging
import os
import re
import uuid
from calendar import monthrange
from collections import defaultdict
from copy import deepcopy
from mimetypes import guess_extension, guess_type
from typing import Any

import environ
import numpy as np
import requests
from des.models import DynamicEmailConfiguration
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.mail import (
    EmailMessage,
    EmailMultiAlternatives,
    get_connection,
    send_mail,
)
from django.db.models import QuerySet
from django.template.loader import render_to_string
from workalendar.america import BrazilSaoPauloCity

from config.settings.base import URL_CONFIGS

from .constants import DAQUI_A_SETE_DIAS, DAQUI_A_TRINTA_DIAS, DOMINIOS_DEV
from .models import CentralDeDownload, LogSolicitacoesUsuario, Notificacao

calendar = BrazilSaoPauloCity()

env = environ.Env()

logger = logging.getLogger(__name__)


def eh_email_dev(email):
    for dominio in DOMINIOS_DEV:
        if email.endswith(dominio):
            return True
    return False


def remove_emails_dev(lista_emails, modo_debug=settings.DEBUG):
    """Remove emails que sao usados apenas em desenvolvimento quando a aplicação está em modo produção."""
    if modo_debug:
        return lista_emails

    nova_lista = []
    for email in lista_emails:
        if not eh_email_dev(email):
            nova_lista.append(email)

    return nova_lista


def envia_email_unico(
    assunto: str, corpo: str, email: str, template: str, dados_template: Any, html=None
):
    config = DynamicEmailConfiguration.get_solo()

    return send_mail(
        assunto, corpo, config.from_email or None, [email], html_message=html
    )


def envia_email_unico_com_anexo(
    assunto: str, corpo: str, email: str, anexo=[]
):  # noqa B006
    # Anexa um arquivo no email.
    # Usado em enviar_email_para_diretor_da_escola_destino.
    config = DynamicEmailConfiguration.get_solo()

    email = EmailMessage(assunto, corpo, config.from_email or None, [email])
    email.content_subtype = "html"
    _mimetypes, _ = guess_type(anexo.name)
    # Este anexo vem da pasta media.
    nome_anexo = anexo.name.split("/")[-1]
    nome_anexo = nome_anexo.replace("_auto", "")
    email.attach(nome_anexo, anexo.read(), _mimetypes)
    email.send()


def envia_email_unico_com_anexo_inmemory(
    assunto: str, corpo: str, email: str, anexo_nome: str, mimetypes: str, anexo=[]
):  # noqa E501
    # Rever a obrigatoriedade de anexo_nome e mimetypes para implementações futuras, ou generalização.
    config = DynamicEmailConfiguration.get_solo()

    email = EmailMessage(assunto, corpo, config.from_email or None, [email])
    email.content_subtype = "html"
    email.attach(anexo_nome, anexo, mimetypes)
    email.send()


def envia_email_em_massa(
    assunto: str,
    corpo: str,
    emails: list,
    template: str,
    dados_template: Any,
    html=None,
):
    config = DynamicEmailConfiguration.get_solo()
    from_email = config.from_email
    with get_connection() as connection:
        messages = []
        for email in remove_emails_dev(emails):
            message = EmailMultiAlternatives(assunto, corpo, from_email, [email])
            if html:
                message.attach_alternative(html, "text/html")
            messages.append(message)
        return connection.send_messages(messages)


def obter_dias_uteis_apos(dia: datetime.date, quantidade_dias: int):
    """Retorna o próximo dia útil após dia de parâmetro."""
    return calendar.add_working_days(dia, quantidade_dias)


def obter_dias_uteis_antes(dia: datetime.date, quantidade_dias: int):
    """Retorna o próximo dia útil antes do dia de parâmetro."""
    return calendar.sub_working_days(dia, quantidade_dias)


def eh_dia_util(date):
    return calendar.is_working_day(date)


def obter_primeiro_e_ultimo_dia_mes(ano, mes):
    """Retorna o primeiro e o último dia do mês."""

    primeiro_dia = datetime.date(ano, mes, 1)
    quantidade_dias = monthrange(ano, mes)[1]
    ultimo_dia = datetime.date(ano, mes, quantidade_dias)

    return primeiro_dia, ultimo_dia


def update_instance_from_dict(instance, attrs, save=False):
    for attr, val in attrs.items():
        setattr(instance, attr, val)
    if save:
        instance.save()
    return instance


def url_configs(variable, content):
    # TODO: rever essa logica de link para trabalhar no front, tá dando voltas
    if "http" in env("REACT_APP_URL"):
        return env("REACT_APP_URL") + URL_CONFIGS[variable].format(**content)
    http_ou_https = "http://" if ":" in env("REACT_APP_URL") else "https://"
    return (
        http_ou_https + env("REACT_APP_URL") + URL_CONFIGS[variable].format(**content)
    )


def convert_base64_to_contentfile(base64_str: str):
    format, imgstr = base64_str.split(";base64,")
    if format == "data:application/vnd.ms-excel":
        ext = ".xls"
    else:
        ext = guess_extension(format[5:]) or ""
    data = ContentFile(base64.b64decode(imgstr), name=str(uuid.uuid4()) + ext)
    return data


def convert_image_to_base64(image_file, format):
    if not os.path.isfile(image_file):
        return None

    encoded_string = ""
    with open(image_file, "rb") as img_f:
        encoded_string = base64.b64encode(img_f.read())
    return "data:image/%s;base64,%s" % (format, encoded_string.decode("utf-8"))


def queryset_por_data(filtro_aplicado, model):
    if filtro_aplicado == DAQUI_A_SETE_DIAS:
        return model.desta_semana
    elif filtro_aplicado == DAQUI_A_TRINTA_DIAS:
        return model.deste_mes  # type: ignore
    return model.objects  # type: ignore


def convert_date_format(date, from_format, to_format):
    return datetime.datetime.strftime(
        datetime.datetime.strptime(date, from_format), to_format
    )


def size(b64string):
    return (len(b64string) * 3) / 4 - b64string.count("=", -2)


ULTIMO_DIA_DO_MES = {
    1: 31,
    2: 28,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31,
}


def subtrai_meses_de_data(meses, data):
    sub_anos = meses // 12
    sub_meses = meses % 12
    if data.month <= sub_meses:
        novo_ano = data.year - (sub_anos + 1)
        novo_mes = 12 - (sub_meses - data.month)
    else:
        novo_ano = data.year - sub_anos
        novo_mes = data.month - sub_meses
    if novo_ano % 20 == 0 and novo_mes == 2 and data.day > 29:
        novo_dia = 29
    elif data.day > ULTIMO_DIA_DO_MES[novo_mes]:
        novo_dia = ULTIMO_DIA_DO_MES[novo_mes]
    else:
        novo_dia = data.day
    return datetime.date(novo_ano, novo_mes, novo_dia)


def ordena_dias_semana_comeca_domingo(dias_semana):
    """
    Obtém uma lista de inteiros onde cada inteiro representa um dia da semana.

    No python, os dias da semana são
    - 0 = Segunda-feira
    - 1 = Terça-feira
    - ...
    - 6 = Domingo

    A função retorna uma lista de inteiros ordenados sendo que o número 6 sempre será o primeiro número.
    """
    return sorted(dias_semana, key=lambda x: -1 if x == 6 else x)


def gera_objeto_na_central_download(user, identificador):
    usuario = get_user_model().objects.get(username=user)
    obj_arquivo_download = CentralDeDownload.objects.create(
        identificador=identificador,
        arquivo=None,
        status=CentralDeDownload.STATUS_EM_PROCESSAMENTO,
        msg_erro="",
        visto=False,
        usuario=usuario,
    )
    obj_arquivo_download.save()

    return obj_arquivo_download


def atualiza_central_download(obj_central_download, identificador, arquivo):
    type_pdf = "application/pdf"
    type_xlsx = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    content_type = type_pdf if ".pdf" in identificador else type_xlsx

    obj_central_download.arquivo = SimpleUploadedFile(
        identificador, arquivo, content_type=content_type
    )
    obj_central_download.status = CentralDeDownload.STATUS_CONCLUIDO
    obj_central_download.save()


def atualiza_central_download_com_erro(obj_central_download, msg_erro):
    obj_central_download.status = CentralDeDownload.STATUS_ERRO
    obj_central_download.msg_erro = msg_erro
    obj_central_download.save()


class ExportExcelAction:
    @classmethod  # noqa
    def generate_header(cls, admin, model, list_display):
        def default_format(value):
            return value.replace("_", " ").upper()

        header = []
        for field_display in list_display:
            is_model_field = field_display in [f.name for f in model._meta.fields]
            is_admin_field = hasattr(admin, field_display)
            if is_model_field:
                field = model._meta.get_field(field_display)
                field_name = getattr(field, "verbose_name", field_display)
                header.append(default_format(field_name))
            elif is_admin_field:
                field = getattr(admin, field_display)
                field_name = getattr(
                    field, "short_description", default_format(field_display)
                )
                header.append(default_format(field_name))
            else:
                header.append(default_format(field_display))
        return header


def remove_tags_html_from_string(html_string: str):
    return re.sub(r"<.*?>", "", html_string)


def get_ultimo_dia_mes(date: datetime.date):
    if date.month == 12:
        return date.replace(day=31)
    return date.replace(month=date.month + 1, day=1) - datetime.timedelta(days=1)


def remove_multiplos_espacos(string: str):
    return " ".join(string.split())


def build_xlsx_generico(
    output, queryset_serializada, titulo, subtitulo, titulo_sheet, titulos_colunas
):
    LINHA_0 = 0
    LINHA_1 = 1
    LINHA_2 = 2
    LINHA_3 = 3

    ALTURA_COLUNA_30 = 30
    ALTURA_COLUNA_50 = 50

    import pandas as pd

    with pd.ExcelWriter(output, engine="xlsxwriter") as xlwriter:
        df = pd.DataFrame(queryset_serializada)

        # Adiciona linhas em branco no comeco do arquivo
        df_auxiliar = pd.DataFrame([[np.nan] * len(df.columns)], columns=df.columns)
        df = pd.concat([df_auxiliar, df], ignore_index=True)
        df = pd.concat([df_auxiliar, df], ignore_index=True)
        df = pd.concat([df_auxiliar, df], ignore_index=True)

        df.to_excel(xlwriter, titulo_sheet)
        workbook = xlwriter.book
        worksheet = xlwriter.sheets[titulo_sheet]
        worksheet.set_row(LINHA_0, ALTURA_COLUNA_50)
        worksheet.set_row(LINHA_1, ALTURA_COLUNA_30)
        worksheet.set_column("B:H", ALTURA_COLUNA_30)
        merge_format = workbook.add_format(
            {"align": "center", "bg_color": "#a9d18e", "border_color": "#198459"}
        )
        merge_format.set_align("vcenter")
        merge_format.set_bold()
        cell_format = workbook.add_format()
        cell_format.set_text_wrap()
        cell_format.set_align("vcenter")
        cell_format.set_bold()
        v_center_format = workbook.add_format()
        v_center_format.set_align("vcenter")
        single_cell_format = workbook.add_format({"bg_color": "#a9d18e"})
        len_cols = len(df.columns)
        worksheet.merge_range(0, 0, 0, len_cols, titulo, merge_format)

        worksheet.merge_range(LINHA_1, 0, LINHA_2, len_cols, subtitulo, cell_format)
        worksheet.insert_image(
            "A1", "sme_sigpae_api/static/images/logo-sigpae-light.png"
        )
        for index, titulo_coluna in enumerate(titulos_colunas, start=1):
            worksheet.write(LINHA_3, index, titulo_coluna, single_cell_format)

        df.reset_index(drop=True, inplace=True)
    output.seek(0)


def converte_numero_em_mes(mes):
    meses = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }

    return meses.get(mes, "Mês inválido")


def cria_copias_fk(obj, attr, attr_fk, obj_copia):
    for original in getattr(obj, attr).all():
        copia = deepcopy(original)
        copia.id = None
        copia.uuid = uuid.uuid4()
        setattr(copia, attr_fk, obj_copia)
        copia.save()


def cria_copias_m2m(obj, attr, obj_copia):
    for m2m_obj in getattr(obj, attr).all():
        getattr(obj_copia, attr).add(m2m_obj)
        obj_copia.save()


def datetime_range(start=None, end=None):
    dates = []
    if isinstance(start, str):
        start = datetime.datetime.strptime(start, "%Y-%m-%d").date()
    if isinstance(end, str):
        end = datetime.datetime.strptime(end, "%Y-%m-%d").date()
    span = end - start
    for i in range(span.days + 1):
        dates.append(start + datetime.timedelta(days=i))
    return dates


def analisa_logs_alunos_matriculados_periodo_escola():
    from sme_sigpae_api.escola.models import Escola

    escolas = Escola.objects.all()
    for index, escola in enumerate(escolas):
        msg = f"análise de LogAlunosMatriculadosPeriodoEscola para escola {escola.nome}"
        msg += f" ({index + 1}/{(escolas).count()})"
        try:
            logger.info(f"x-x-x-x Iniciando {msg} x-x-x-x")
            hoje = datetime.date.today()
            deletar_logs_alunos_matriculados_duplicados(escola, hoje)
            criar_logs_alunos_matriculados_inexistentes(escola, hoje)
            logger.info(f"x-x-x-x Finaliza {msg} x-x-x-x")
        except Exception as e:
            logger.error(f"x-x-x-x Erro na {msg} x-x-x-x")
            logger.error(f"`--> {e}")


def deletar_logs_alunos_matriculados_duplicados(escola, hoje):
    from sme_sigpae_api.escola.models import LogAlunosMatriculadosPeriodoEscola

    for i in range(1, 8):
        data = hoje - datetime.timedelta(days=i)
        logs = LogAlunosMatriculadosPeriodoEscola.objects.filter(
            escola=escola,
            criado_em__year=data.year,
            criado_em__month=data.month,
            criado_em__day=data.day,
        )
        logs_para_deletar = []
        for log in logs:
            logs_filtrados = logs.filter(
                periodo_escolar=log.periodo_escolar,
                tipo_turma=log.tipo_turma,
                cei_ou_emei=log.cei_ou_emei,
                infantil_ou_fundamental=log.infantil_ou_fundamental,
            ).order_by("-criado_em")
            for log_filtrado in logs_filtrados[1 : logs_filtrados.count()]:
                if log_filtrado.uuid not in logs_para_deletar:
                    logs_para_deletar.append(log_filtrado.uuid)
        logs.filter(uuid__in=logs_para_deletar).delete()


def criar_logs_alunos_matriculados_inexistentes(escola, hoje):
    from sme_sigpae_api.escola.models import LogAlunosMatriculadosPeriodoEscola

    for i in range(1, 8):
        data = hoje - datetime.timedelta(days=i)
        logs = LogAlunosMatriculadosPeriodoEscola.objects.filter(
            escola=escola,
            criado_em__year=data.year,
            criado_em__month=data.month,
            criado_em__day=data.day,
        )
        if not logs:
            for i_para_repetir in range(1, 6):
                quantidade_dias = i + i_para_repetir
                data_para_repetir = hoje - datetime.timedelta(days=quantidade_dias)
                logs_para_repetir = LogAlunosMatriculadosPeriodoEscola.objects.filter(
                    escola=escola,
                    criado_em__year=data_para_repetir.year,
                    criado_em__month=data_para_repetir.month,
                    criado_em__day=data_para_repetir.day,
                )
                if logs_para_repetir:
                    for log_para_criar in logs_para_repetir:
                        log_criado = LogAlunosMatriculadosPeriodoEscola.objects.create(
                            escola=log_para_criar.escola,
                            periodo_escolar=log_para_criar.periodo_escolar,
                            quantidade_alunos=log_para_criar.quantidade_alunos,
                            tipo_turma=log_para_criar.tipo_turma,
                            cei_ou_emei=log_para_criar.cei_ou_emei,
                            infantil_ou_fundamental=log_para_criar.infantil_ou_fundamental,
                        )
                        log_criado.criado_em = data
                        log_criado.save()
                    break


def analisa_logs_quantidade_dietas_autorizadas():
    from sme_sigpae_api.dieta_especial.models import (
        LogQuantidadeDietasAutorizadas,
        LogQuantidadeDietasAutorizadasCEI,
    )
    from sme_sigpae_api.escola.models import Escola

    escolas = Escola.objects.filter(tipo_gestao__nome="TERC TOTAL")
    for index, escola in enumerate(escolas):
        msg = "análise de LogQuantidadeDietasAutorizadas / LogQuantidadeDietasAutorizadasCEI"
        msg += f" para escola {escola.nome} ({index + 1}/{(escolas).count()})"
        try:
            logger.info(f"x-x-x-x Iniciando {msg} x-x-x-x")
            hoje = datetime.date.today()
            if escola.eh_cemei:
                analisa_logs_quantidade_dietas_autorizadas_cemei(escola, hoje)
            else:
                if escola.eh_cei:
                    modelo = LogQuantidadeDietasAutorizadasCEI
                else:
                    modelo = LogQuantidadeDietasAutorizadas
                deletar_logs_quantidade_dietas_autorizadas(escola, hoje, modelo)
                criar_logs_quantidade_dietas_autorizadas_inexistentes(
                    escola, hoje, modelo
                )
            logger.info(f"x-x-x-x Finaliza {msg} x-x-x-x")
        except Exception as e:
            logger.error(f"x-x-x-x Erro na {msg} x-x-x-x")
            logger.error(f"`--> {e}")


def analisa_logs_quantidade_dietas_autorizadas_cemei(escola, hoje):
    from sme_sigpae_api.dieta_especial.models import (
        LogQuantidadeDietasAutorizadas,
        LogQuantidadeDietasAutorizadasCEI,
    )

    for modelo in [LogQuantidadeDietasAutorizadas, LogQuantidadeDietasAutorizadasCEI]:
        deletar_logs_quantidade_dietas_autorizadas(escola, hoje, modelo)
        criar_logs_quantidade_dietas_autorizadas_inexistentes(escola, hoje, modelo)


def deletar_logs_quantidade_dietas_autorizadas(escola, hoje, modelo):
    for i in range(1, 8):
        data = hoje - datetime.timedelta(days=i)
        logs = modelo.objects.filter(
            escola=escola,
            data__year=data.year,
            data__month=data.month,
            data__day=data.day,
        )
        logs_para_deletar = []
        for log in logs:
            logs_filtrados = logs.filter(
                periodo_escolar=log.periodo_escolar, classificacao=log.classificacao
            ).order_by("-criado_em")
            if modelo.__name__ == "LogQuantidadeDietasAutorizadas":
                logs_filtrados = logs_filtrados.filter(
                    infantil_ou_fundamental=log.infantil_ou_fundamental
                ).order_by("-criado_em")
            if escola.eh_cei or (
                escola.eh_cemei
                and modelo.__name__ == "LogQuantidadeDietasAutorizadasCEI"
            ):
                logs_filtrados = logs_filtrados.filter(
                    faixa_etaria=log.faixa_etaria
                ).order_by("-criado_em")
            if escola.eh_cemei and modelo.__name__ == "LogQuantidadeDietasAutorizadas":
                logs_filtrados = logs_filtrados.filter(
                    cei_ou_emei=log.cei_ou_emei
                ).order_by("-criado_em")
            logs_para_deletar = logs_para_deletar + uuids_logs_para_deletar(
                logs_filtrados
            )
        logs.filter(uuid__in=logs_para_deletar).delete()


def uuids_logs_para_deletar(logs_filtrados):
    logs_para_deletar = []
    for log_filtrado in logs_filtrados[1 : logs_filtrados.count()]:
        if log_filtrado.uuid not in logs_para_deletar:
            logs_para_deletar.append(log_filtrado.uuid)
    return logs_para_deletar


def criar_logs_quantidade_dietas_autorizadas_inexistentes(escola, hoje, modelo):
    for i in range(1, 8):
        data = hoje - datetime.timedelta(days=i)
        logs = modelo.objects.filter(
            escola=escola,
            data__year=data.year,
            data__month=data.month,
            data__day=data.day,
        )
        if not logs:
            for i_para_repetir in range(1, 6):
                quantidade_dias = i + i_para_repetir
                data_para_repetir = hoje - datetime.timedelta(days=quantidade_dias)
                logs_para_repetir = modelo.objects.filter(
                    escola=escola,
                    data__year=data_para_repetir.year,
                    data__month=data_para_repetir.month,
                    data__day=data_para_repetir.day,
                )
                if logs_para_repetir:
                    for log_para_criar in logs_para_repetir:
                        create_objects_logs(escola, log_para_criar, data)
                    break


def create_objects_logs(escola, log_para_criar, data):
    from sme_sigpae_api.dieta_especial.models import (
        LogQuantidadeDietasAutorizadas,
        LogQuantidadeDietasAutorizadasCEI,
    )

    if escola.eh_cei or (
        escola.eh_cemei
        and log_para_criar._meta.model.__name__ == "LogQuantidadeDietasAutorizadasCEI"
    ):
        LogQuantidadeDietasAutorizadasCEI.objects.create(
            quantidade=log_para_criar.quantidade,
            escola=log_para_criar.escola,
            data=data,
            classificacao=log_para_criar.classificacao,
            periodo_escolar=log_para_criar.periodo_escolar,
            faixa_etaria=log_para_criar.faixa_etaria,
        )
    else:
        LogQuantidadeDietasAutorizadas.objects.create(
            quantidade=log_para_criar.quantidade,
            escola=log_para_criar.escola,
            data=data,
            classificacao=log_para_criar.classificacao,
            periodo_escolar=log_para_criar.periodo_escolar,
            cei_ou_emei=log_para_criar.cei_ou_emei,
            infantil_ou_fundamental=log_para_criar.infantil_ou_fundamental,
        )


def preencher_template_e_notificar(
    template,
    contexto_template,
    titulo_notificacao,
    tipo_notificacao,
    categoria_notificacao,
    link_acesse_aqui,
    usuarios,
    requisicao=None,
    solicitacao_alteracao=None,
    guia=None,
    cronograma=None,
):
    descricao_notificacao = render_to_string(
        template_name=template,
        context=contexto_template,
    )

    if usuarios:
        for usuario in usuarios:
            Notificacao.notificar(
                tipo=tipo_notificacao,
                categoria=categoria_notificacao,
                titulo=titulo_notificacao,
                descricao=descricao_notificacao,
                usuario=usuario,
                link=link_acesse_aqui,
                requisicao=requisicao,
                solicitacao_alteracao=solicitacao_alteracao,
                guia=guia,
                cronograma=cronograma,
            )


def eh_fim_de_semana(data: datetime.date):
    return data.weekday() >= 5


def custom_titled_filter(title):
    class Wrapper(admin.FieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance

    return Wrapper


def numero_com_agrupador_de_milhar_e_decimal(value: int | float) -> str:
    try:
        return (
            "{:,.2f}".format(float(value))
            .replace(",", " ")
            .replace(".", ",")
            .replace(" ", ".")
        )

    except (ValueError, TypeError):
        return value


def ordena_queryset_por_ultimo_log(queryset: QuerySet) -> list:
    all_logs = LogSolicitacoesUsuario.objects.filter(
        uuid_original__in=queryset.values_list("uuid", flat=True)
    ).order_by("criado_em")

    logs_by_uuid = defaultdict(list)
    for log in all_logs:
        logs_by_uuid[log.uuid_original].append(log)

    for obj in queryset:
        obj._prefetched_logs = logs_by_uuid.get(obj.uuid, [])
        obj.ultimo_log_cached = (
            obj._prefetched_logs[-1] if obj._prefetched_logs else None
        )

    queryset = sorted(
        queryset,
        key=lambda x: x.ultimo_log_cached.criado_em
        if x.ultimo_log_cached
        else datetime.datetime.min,
        reverse=True,
    )
    return queryset


def obter_versao_api():
    github_api_version = "2022-11-28"
    usuario = "prefeiturasp"
    repositorio = "SME-SIGPAE-API"
    url = f"https://api.github.com/repos/{usuario}/{repositorio}/releases/latest"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": github_api_version,
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        latest_release = response.json()
        return latest_release.get("tag_name")

    except requests.exceptions.RequestException as ex:
        logger.error(f"Erro na requisição: {ex}")
    except Exception as ex:
        logger.error(f"Não foi possível obter a última versão da API: {ex}")
    return None


def remove_duplicados_do_query_set(query_set: QuerySet | list) -> list:
    uuids_repetidos = set()
    return [
        solicitacao
        for solicitacao in query_set
        if solicitacao.uuid not in uuids_repetidos
        and not uuids_repetidos.add(solicitacao.uuid)
    ]
