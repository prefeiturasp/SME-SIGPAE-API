from datetime import datetime

from sme_sigpae_api.dados_comuns.fluxo_status import (
    CronogramaWorkflow,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import (
    EtapasDoCronograma,
    ProgramacaoDoRecebimentoDoCronograma,
)


def cria_etapas_de_cronograma(etapas, cronograma=None):
    etapas_criadas = []
    for etapa in etapas:
        etapas_criadas.append(
            EtapasDoCronograma.objects.create(cronograma=cronograma, **etapa)
        )
    return etapas_criadas


def cria_programacao_de_cronograma(programacoes, cronograma=None):
    programacoes_criadas = []
    for programacao in programacoes:
        programacoes_criadas.append(
            ProgramacaoDoRecebimentoDoCronograma.objects.create(
                cronograma=cronograma, **programacao
            )
        )
    return programacoes_criadas


def totalizador_relatorio_cronograma(queryset):
    status_count = {
        CronogramaWorkflow.states[s].title: queryset.filter(status=s).count()
        for s in CronogramaWorkflow.states
    }
    ordered_status_count = dict(
        sorted(status_count.items(), key=lambda e: e[1], reverse=True)
    )
    return ordered_status_count


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except (ValueError, AttributeError):
        return None


def passa_filtro_data_etapa(etapa_data, data_inicio_obj, data_fim_obj):
    data_programada = etapa_data.get("data_programada")
    if not data_programada:
        return False

    try:
        data_etapa = datetime.strptime(data_programada, "%d/%m/%Y").date()
        if data_inicio_obj and data_etapa < data_inicio_obj:
            return False
        if data_fim_obj and data_etapa > data_fim_obj:
            return False

        return True
    except (ValueError, AttributeError):
        return False


def processar_situacao_recebido(
    situacoes,
    tem_fichas_sem_ocorrencia,
    fichas_recebimento,
    incluir_etapa,
    fichas_finais,
):
    if "Recebido" in situacoes and tem_fichas_sem_ocorrencia:
        incluir_etapa = True
        fichas_finais = [
            f for f in fichas_recebimento if f.get("houve_ocorrencia") in (None, False)
        ]
    return incluir_etapa, fichas_finais


def processar_situacao_ocorrencia(
    situacoes,
    tem_fichas_com_ocorrencia,
    tem_fichas_sem_ocorrencia,
    fichas_recebimento,
    incluir_etapa,
    fichas_finais,
):
    if "Ocorrência" in situacoes and tem_fichas_com_ocorrencia:
        incluir_etapa = True
        fichas_com_ocorrencia = [
            f for f in fichas_recebimento if f.get("houve_ocorrencia") is True
        ]
        if "Recebido" in situacoes and tem_fichas_sem_ocorrencia:
            fichas_finais = fichas_finais + fichas_com_ocorrencia
        else:
            fichas_finais = fichas_com_ocorrencia
    return incluir_etapa, fichas_finais


def processar_situacao_a_receber(
    situacoes,
    fichas_recebimento,
    tem_fichas_com_ocorrencia,
    tem_fichas_sem_ocorrencia,
    incluir_etapa,
    fichas_finais,
):
    if "A Receber" in situacoes:
        if not fichas_recebimento or (
            tem_fichas_com_ocorrencia and not tem_fichas_sem_ocorrencia
        ):
            incluir_etapa = True
            if "Ocorrência" not in situacoes:
                fichas_finais = []
    return incluir_etapa, fichas_finais


def aplicar_filtros_etapa(
    etapa_data, data_inicio_obj, data_fim_obj, situacoes, tem_filtro_situacao
):
    if data_inicio_obj or data_fim_obj:
        if not passa_filtro_data_etapa(etapa_data, data_inicio_obj, data_fim_obj):
            return False

    if tem_filtro_situacao:
        return passa_filtro_situacao(etapa_data, situacoes)

    return True


def passa_filtro_situacao(etapa_data, situacoes):
    if not situacoes or len(situacoes) == 3:
        return True

    fichas_recebimento = etapa_data.get("fichas_recebimento", [])

    tem_fichas_com_ocorrencia = any(
        f.get("houve_ocorrencia") is True for f in fichas_recebimento
    )
    tem_fichas_sem_ocorrencia = any(
        f.get("houve_ocorrencia") in (None, False) for f in fichas_recebimento
    )

    incluir_etapa = False
    fichas_finais = []

    incluir_etapa, fichas_finais = processar_situacao_recebido(
        situacoes,
        tem_fichas_sem_ocorrencia,
        fichas_recebimento,
        incluir_etapa,
        fichas_finais,
    )

    incluir_etapa, fichas_finais = processar_situacao_ocorrencia(
        situacoes,
        tem_fichas_com_ocorrencia,
        tem_fichas_sem_ocorrencia,
        fichas_recebimento,
        incluir_etapa,
        fichas_finais,
    )

    incluir_etapa, fichas_finais = processar_situacao_a_receber(
        situacoes,
        fichas_recebimento,
        tem_fichas_com_ocorrencia,
        tem_fichas_sem_ocorrencia,
        incluir_etapa,
        fichas_finais,
    )

    if incluir_etapa:
        etapa_data["fichas_recebimento"] = fichas_finais

    return incluir_etapa


def filtrar_etapas(serialized_data, request):
    data_inicial = request.query_params.get("data_inicial")
    data_final = request.query_params.get("data_final")
    situacoes = request.query_params.getlist("situacao", [])

    if not any([data_inicial, data_final, situacoes]) or len(situacoes) == 3:
        return serialized_data

    data_inicio_obj = parse_date(data_inicial) if data_inicial else None
    data_fim_obj = parse_date(data_final) if data_final else None
    tem_filtro_situacao = situacoes and len(situacoes) < 3

    for i in range(len(serialized_data) - 1, -1, -1):
        cronograma_data = serialized_data[i]
        etapas = cronograma_data.get("etapas", [])

        for j in range(len(etapas) - 1, -1, -1):
            etapa_data = etapas[j]
            deve_manter_etapa = aplicar_filtros_etapa(
                etapa_data,
                data_inicio_obj,
                data_fim_obj,
                situacoes,
                tem_filtro_situacao,
            )

            if not deve_manter_etapa:
                etapas.pop(j)

        if not etapas:
            serialized_data.pop(i)

    return serialized_data
