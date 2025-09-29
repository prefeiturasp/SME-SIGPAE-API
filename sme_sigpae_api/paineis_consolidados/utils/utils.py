import calendar
import datetime
import unicodedata

from dateutil.relativedelta import relativedelta
from django.db.models import Q

from sme_sigpae_api.cardapio.base.models import (
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from sme_sigpae_api.dados_comuns.utils import get_ultimo_dia_mes
from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial
from sme_sigpae_api.escola.models import DiretoriaRegional, Lote
from sme_sigpae_api.inclusao_alimentacao.models import (
    QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI,
)
from sme_sigpae_api.terceirizada.models import Terceirizada


def formata_resultado_inclusoes_etec_autorizadas(dia, mes, ano, inclusao):
    if (
        get_ultimo_dia_mes(datetime.date(int(ano), int(mes), 1)) < datetime.date.today()
        or dia < datetime.date.today().day
    ):
        for qp in inclusao.quantidades_por_periodo.all():
            alimentacoes = ", ".join(
                [
                    unicodedata.normalize("NFD", alimentacao.nome.replace(" ", "_"))
                    .encode("ascii", "ignore")
                    .decode("utf-8")
                    for alimentacao in qp.tipos_alimentacao.all()
                ]
            ).lower()
            return {
                "dia": f"{dia:02d}",
                "periodo": f"{qp.periodo_escolar.nome}",
                "alimentacoes": alimentacoes,
                "tipos_alimentacao": list(
                    set(qp.tipos_alimentacao.all().values_list("nome", flat=True))
                ),
                "numero_alunos": qp.numero_alunos,
                "inclusao_id_externo": inclusao.id_externo,
            }


def tratar_dias_duplicados(return_dict):
    dict_tratado = []
    dias_tratados = []
    for obj in return_dict:
        dia = obj["dia"]
        obj_dias_iguais = [r for r in return_dict if r["dia"] == dia]
        if obj["dia"] not in dias_tratados:
            if len(obj_dias_iguais) > 1:
                numero_de_alunos = max(
                    obj_dias_iguais, key=lambda obj: obj["numero_alunos"]
                )["numero_alunos"]
                novo_objeto = {
                    "dia": dia,
                    "periodo": obj["periodo"],
                    "alimentacoes": ", ".join(
                        [obj["alimentacoes"] for obj in obj_dias_iguais]
                    ),
                    "numero_alunos": numero_de_alunos,
                    "inclusao_id_externo": None,
                }
                dict_tratado.append(novo_objeto)
            else:
                dict_tratado.append(obj)
            dias_tratados.append(obj["dia"])
    return dict_tratado


def tratar_data_evento_final_no_mes(data_evento_final_no_mes, sol_escola, big_range):
    if sol_escola.data_evento_2.month != sol_escola.data_evento.month and not big_range:
        retorno = (sol_escola.data_evento + relativedelta(day=31)).day
    else:
        retorno = data_evento_final_no_mes
    return retorno


def get_dias_inclusao(obj, model_obj):
    objects = {
        "ALT_CARDAPIO": "datas_intervalo",
        "ALT_CARDAPIO_CEMEI": "datas_intervalo",
        "INC_ALIMENTA": "inclusoes_normais",
        "INC_ALIMENTA_CEI": "dias_motivos_da_inclusao_cei",
        "INC_ALIMENTA_CEMEI": "dias_motivos_da_inclusao_cemei",
        "SUSP_ALIMENTACAO": "suspensoes_alimentacao",
    }
    return getattr(model_obj, objects[obj.tipo_doc]).all()


def tratar_periodo_parcial(nome_periodo_escolar):
    if nome_periodo_escolar == "PARCIAL":
        nome_periodo_escolar = "INTEGRAL"
    return nome_periodo_escolar


def tratar_periodo_parcial_cemei(nome_periodo_escolar, suspensao):
    if not suspensao.escola.eh_cemei:
        return nome_periodo_escolar
    if (
        nome_periodo_escolar == "PARCIAL"
        and suspensao.quantidades_por_periodo.filter(
            alunos_cei_ou_emei__in=["CEI", "Todos"], periodo_escolar__nome="INTEGRAL"
        ).exists()
    ):
        nome_periodo_escolar = "INTEGRAL"
    elif (
        "Infantil" in nome_periodo_escolar
        and suspensao.quantidades_por_periodo.filter(
            alunos_cei_ou_emei__in=["EMEI", "Todos"],
            periodo_escolar__nome=nome_periodo_escolar.split(" ")[1],
        ).exists()
    ):
        nome_periodo_escolar = nome_periodo_escolar.split(" ")[1]
    return nome_periodo_escolar


def tratar_append_return_dict(dia, mes, ano, periodo, inclusao, return_dict):
    if (
        get_ultimo_dia_mes(datetime.date(int(ano), int(mes), 1)) < datetime.date.today()
        or dia < datetime.date.today().day
    ):
        if isinstance(periodo, QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI):
            queryset_tipos_alimentacao = (
                VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.get(
                    tipo_unidade_escolar__iniciais="EMEI",
                    periodo_escolar=periodo.periodo_escolar,
                ).tipos_alimentacao.exclude(nome="Lanche Emergencial")
            )
        else:
            queryset_tipos_alimentacao = periodo.tipos_alimentacao.all()
        alimentacoes = ", ".join(
            [
                unicodedata.normalize("NFD", alimentacao.nome.replace(" ", "_"))
                .encode("ascii", "ignore")
                .decode("utf-8")
                for alimentacao in queryset_tipos_alimentacao
            ]
        ).lower()
        return return_dict.append(
            {
                "dia": f"{dia:02d}",
                "periodo": f"{periodo.periodo_escolar.nome}",
                "alimentacoes": alimentacoes,
                "numero_alunos": (
                    periodo.numero_alunos
                    if hasattr(periodo, "numero_alunos")
                    else periodo.quantidade_alunos
                ),
                "dias_semana": (
                    periodo.dias_semana if hasattr(periodo, "dias_semana") else None
                ),
                "inclusao_id_externo": inclusao.id_externo,
            }
        )


def criar_dict_dias_inclusoes_continuas(
    i, data_evento_final_no_mes, periodo, ano, mes, inclusao, return_dict
):
    while i <= data_evento_final_no_mes:
        if (
            not periodo.dias_semana
            or (datetime.date(int(ano), int(mes), i).weekday()) in periodo.dias_semana
        ):
            tratar_append_return_dict(i, mes, ano, periodo, inclusao, return_dict)
        i += 1


def tratar_inclusao_continua(mes, ano, periodo, inclusao, return_dict):
    if inclusao.data_evento.month != int(mes) and inclusao.data_evento_2.month == int(
        mes
    ):
        # data_inicial fora e data_final dentro do mês analisado
        i = datetime.date(int(ano), int(mes), 1).day
        data_evento_final_no_mes = inclusao.data_evento_2.day
    elif inclusao.data_evento.month == int(mes) and inclusao.data_evento_2.month != int(
        mes
    ):
        # data_inicial dentro e data_final fora do mês analisado
        i = inclusao.data_evento.day
        data_evento_final_no_mes = (inclusao.data_evento + relativedelta(day=31)).day
    elif inclusao.data_evento.month == int(mes) and inclusao.data_evento_2.month == int(
        mes
    ):
        # data_inicial e data_final dentro do mês analisado
        i = inclusao.data_evento.day
        data_evento_final_no_mes = inclusao.data_evento_2.day
    elif inclusao.data_evento.month != int(mes) and inclusao.data_evento_2.month != int(
        mes
    ):
        # data_inicial e data_final fora do mês analisado
        i = datetime.date(int(ano), int(mes), 1).day
        data_evento_final_no_mes = calendar.monthrange(int(ano), int(mes))[1]
    criar_dict_dias_inclusoes_continuas(
        i, data_evento_final_no_mes, periodo, ano, mes, inclusao, return_dict
    )


def get_numero_alunos_alteracao_alimentacao(alteracao):
    if alteracao.DESCRICAO == "Alteração do Tipo de Alimentação CEMEI":
        numero_alunos = sum(
            alteracao.substituicoes_cemei_emei_periodo_escolar.values_list(
                "qtd_alunos", flat=True
            )
        )
    else:
        numero_alunos = sum(
            alteracao.substituicoes_periodo_escolar.values_list("qtd_alunos", flat=True)
        )
    return numero_alunos


def get_label_dataset_grafico_total_dre_lote(request, eh_relatorio_dietas_autorizadas):
    label_data = {
        "AUTORIZADOS": "Autorizadas",
        "CANCELADOS": "Canceladas",
        "NEGADOS": "Negadas",
        "RECEBIDAS": "Recebidas",
    }
    if eh_relatorio_dietas_autorizadas:
        label = "Total de Dietas Especiais Autorizadas por DRE e Lote"
    else:
        label = f"Total de Solicitações {label_data[request.data.get('status')]} por DRE e Lote"
    return label


def get_lotes_dataset_grafico_total_dre_lote(
    lotes, request, instituicao, queryset, eh_relatorio_dietas_autorizadas
):
    if eh_relatorio_dietas_autorizadas and request.data.get("lote"):
        lotes = [request.data.get("lote")]
    if not lotes and not eh_relatorio_dietas_autorizadas:
        if isinstance(instituicao, Terceirizada):
            lotes = Lote.objects.filter(terceirizada=instituicao)
        elif isinstance(instituicao, DiretoriaRegional):
            lotes = Lote.objects.filter(
                uuid__in=list(set(queryset.values_list("lote_uuid", flat=True)))
            )
        else:
            lotes = Lote.objects.all()
        lotes = lotes.values_list("uuid", flat=True)
    return lotes


def get_queryset_filtrado_dataset_grafico_total_dre_lote(
    queryset, lote_uuid, request, eh_relatorio_dietas_autorizadas
):
    alergias_ids = request.data.get("alergias_intolerancias_selecionadas", [])
    cei_polo = request.data.get("cei_polo", False)
    recreio_nas_ferias = request.data.get("recreio_nas_ferias", False)

    if eh_relatorio_dietas_autorizadas:
        queryset = queryset.filter(lote_escola_destino_uuid=lote_uuid)
        lista_uuids = [uuid for uuid in set(queryset.values_list("uuid", flat=True))]
        dietas = SolicitacaoDietaEspecial.objects.filter(uuid__in=lista_uuids)
        if alergias_ids:
            dietas = dietas.filter(alergias_intolerancias__in=alergias_ids).distinct()
        if cei_polo and not recreio_nas_ferias:
            dietas = dietas.filter(motivo_alteracao_ue__nome__icontains="polo")
        if recreio_nas_ferias and not cei_polo:
            dietas = dietas.filter(motivo_alteracao_ue__nome__icontains="recreio")
        if cei_polo and recreio_nas_ferias:
            dietas = dietas.filter(
                Q(motivo_alteracao_ue__nome__icontains="polo")
                | Q(motivo_alteracao_ue__nome__icontains="recreio")
            )
        return dietas
    else:
        return queryset.filter(lote_uuid=lote_uuid)
