from collections import defaultdict

from src.escola.utils import faixa_to_string

from ..constants import (
    UNIDADES_CEI,
    UNIDADES_CEMEI,
    UNIDADES_EMEBS,
    UNIDADES_EMEI_EMEF_CIEJA,
    UNIDADES_SEM_PERIODOS,
)
from .get_logs_historico_dietas import get_logs_historico_dietas


def gera_dicionario_historico_dietas(filtros):
    log_dietas = get_logs_historico_dietas(filtros)
    periodo_escolar_selecionado = False
    if "periodo_escolar__uuid__in" in filtros:
        periodo_escolar_selecionado = True
    escolas, total_dietas = _transformar_dados_escolas(
        log_dietas, periodo_escolar_selecionado
    )
    informacoes = _formatar_informacoes_historioco_dietas(escolas, total_dietas)
    return informacoes


def _transformar_dados_escolas(dados, periodo_escolar_selecionado=False):
    escolas = defaultdict(
        lambda: {
            "tipo_unidade": None,
            "lote": None,
            "classificacoes": defaultdict(
                lambda: {
                    "infantil": defaultdict(int),
                    "fundamental": defaultdict(int),
                    "periodos": defaultdict(int),
                    "por_idade": defaultdict(int),
                    "turma_infantil": defaultdict(int),
                    "faixa_etaria": defaultdict(int),
                    "total": 0,
                }
            ),
        }
    )

    tipos_unidades = {
        **{tipo: _unidades_tipo_emebs for tipo in UNIDADES_EMEBS},
        **{tipo: _unidades_tipos_emei_emef_cieja for tipo in UNIDADES_EMEI_EMEF_CIEJA},
        **{tipo: _unidades_tipos_cmct_ceugestao for tipo in UNIDADES_SEM_PERIODOS},
        **{tipo: _unidades_tipo_cemei for tipo in UNIDADES_CEMEI},
        **{tipo: _unidades_tipo_cei for tipo in UNIDADES_CEI},
    }

    total_dietas = 0
    for item in dados:
        nome_escola = item["nome_escola"]
        tipo_unidade = item["tipo_unidade"]

        escolas[nome_escola]["tipo_unidade"] = tipo_unidade
        escolas[nome_escola]["lote"] = item["lote"]
        escolas[nome_escola]["data"] = item["data"]

        unidade = tipos_unidades.get(tipo_unidade, lambda e, i, p: 0)
        total_dietas += unidade(item, escolas, periodo_escolar_selecionado)

    return escolas, total_dietas


def _formatar_informacoes_historioco_dietas(escolas, total_dietas):
    tipos_unidades = {
        **{tipo: _formatar_periodos_emebs for tipo in UNIDADES_EMEBS},
        **{
            tipo: _formatar_periodos_emei_emef_cieja
            for tipo in UNIDADES_EMEI_EMEF_CIEJA
        },
        **{tipo: _formatar_periodos_cemei for tipo in UNIDADES_CEMEI},
        **{tipo: _formatar_periodos_cei for tipo in UNIDADES_CEI},
    }

    resultado = []
    for escola_nome, dados_escola in escolas.items():
        for classificacao, dados_classificacao in dados_escola[
            "classificacoes"
        ].items():
            tipo_unidade = dados_escola["tipo_unidade"]
            informacao_escola_por_classificacao = {
                "data": dados_escola["data"],
                "lote": dados_escola["lote"],
                "unidade_educacional": escola_nome,
                "tipo_unidade": dados_escola["tipo_unidade"],
                "classificacao": classificacao,
                "total": dados_classificacao["total"],
            }
            unidade = tipos_unidades.get(tipo_unidade, lambda i, d: None)
            unidade(informacao_escola_por_classificacao, dados_classificacao)
            resultado.append(informacao_escola_por_classificacao)

    return {
        "total_dietas": total_dietas,
        "resultados": resultado,
    }


def _unidades_tipo_emebs(item, escolas, periodo_escolar_selecionado=False):
    nome_escola = item["nome_escola"]
    classificacao = item["nome_classificacao"]
    periodo_escola = item["nome_periodo_escolar"]
    tipo_turma = item["infantil_ou_fundamental"]
    cei_emei = item["cei_ou_emei"]
    quantidade = item["quantidade_total"]

    total_dietas = 0
    if periodo_escola:
        escolas[nome_escola]["classificacoes"][classificacao][f"{tipo_turma}".lower()][
            periodo_escola
        ] += quantidade
        if periodo_escolar_selecionado:
            escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
            total_dietas = quantidade
    elif periodo_escola is None and tipo_turma == "N/A" and cei_emei == "N/A":
        escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
        total_dietas = quantidade
    return total_dietas


def _unidades_tipos_emei_emef_cieja(item, escolas, periodo_escolar_selecionado=False):
    nome_escola = item["nome_escola"]
    classificacao = item["nome_classificacao"]
    periodo_escola = item["nome_periodo_escolar"]
    tipo_turma = item["infantil_ou_fundamental"]
    cei_emei = item["cei_ou_emei"]
    quantidade = item["quantidade_total"]

    total_dietas = 0
    if periodo_escola:
        escolas[nome_escola]["classificacoes"][classificacao]["periodos"][
            periodo_escola
        ] += quantidade
        if periodo_escolar_selecionado:
            escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
            total_dietas = quantidade
    elif periodo_escola is None and tipo_turma == "N/A" and cei_emei == "N/A":
        escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
        total_dietas = quantidade

    return total_dietas


def _unidades_tipos_cmct_ceugestao(item, escolas, periodo_escolar_selecionado=False):
    nome_escola = item["nome_escola"]
    classificacao = item["nome_classificacao"]
    quantidade = item["quantidade_total"]

    escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
    return quantidade


def _unidades_tipo_cei(item, escolas, periodo_escolar_selecionado=False):
    nome_escola = item["nome_escola"]
    classificacao = item["nome_classificacao"]
    periodo_escola = item["nome_periodo_escolar"]
    quantidade = item["quantidade_total"]
    inicio = item["inicio"]
    fim = item["fim"]

    total_dietas = 0
    if inicio is not None and fim is not None:
        faixa_etaria_infantil = faixa_to_string(item["inicio"], item["fim"])
        if (
            escolas[nome_escola]["classificacoes"][classificacao]["periodos"][
                periodo_escola
            ]
            == 0
        ):
            escolas[nome_escola]["classificacoes"][classificacao]["periodos"][
                periodo_escola
            ] = []

        escolas[nome_escola]["classificacoes"][classificacao]["periodos"][
            periodo_escola
        ].append({"faixa": faixa_etaria_infantil, "autorizadas": quantidade})
        if periodo_escola in ["MANHA", "TARDE"]:
            total_dietas = quantidade
            escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
    else:
        escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
        total_dietas = quantidade

    return total_dietas


def _unidades_tipo_cemei(item, escolas, periodo_escolar_selecionado=False):  # noqa
    nome_escola = item["nome_escola"]
    classificacao = item["nome_classificacao"]
    periodo_escola = item["nome_periodo_escolar"]
    tipo_turma = item["infantil_ou_fundamental"]
    cei_emei = item["cei_ou_emei"]
    quantidade = item["quantidade_total"]
    inicio = item["inicio"]
    fim = item["fim"]

    total_dietas = 0
    if inicio is not None and fim is not None:
        faixa_etaria_infantil = faixa_to_string(item["inicio"], item["fim"])
        if (
            escolas[nome_escola]["classificacoes"][classificacao]["por_idade"][
                periodo_escola
            ]
            == 0
        ):
            escolas[nome_escola]["classificacoes"][classificacao]["por_idade"][
                periodo_escola
            ] = []
        escolas[nome_escola]["classificacoes"][classificacao]["por_idade"][
            periodo_escola
        ].append({"faixa": faixa_etaria_infantil, "autorizadas": quantidade})
    elif inicio is None and fim is None and tipo_turma is None and cei_emei is None:
        escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
        total_dietas = quantidade
    elif periodo_escola:
        escolas[nome_escola]["classificacoes"][classificacao]["turma_infantil"][
            periodo_escola
        ] = quantidade
        if periodo_escolar_selecionado:
            escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
            total_dietas = quantidade
    elif periodo_escola is None and tipo_turma == "N/A" and cei_emei == "N/A":
        escolas[nome_escola]["classificacoes"][classificacao]["total"] += quantidade
        total_dietas = quantidade

    return total_dietas


def _formatar_periodos_emebs(informacao_escola_por_classificacao, dados_classificacao):
    informacao_escola_por_classificacao["periodos"] = {}
    infantil = dados_classificacao["infantil"]
    if len(infantil) > 0:
        informacao_escola_por_classificacao["periodos"]["infantil"] = [
            {"periodo": p, "autorizadas": q} for p, q in infantil.items()
        ]
    fundamental = dados_classificacao["fundamental"]
    if len(fundamental) > 0:
        informacao_escola_por_classificacao["periodos"]["fundamental"] = [
            {"periodo": p, "autorizadas": q} for p, q in fundamental.items()
        ]


def _formatar_periodos_emei_emef_cieja(
    informacao_escola_por_classificacao, dados_classificacao
):
    informacao_escola_por_classificacao["periodos"] = [
        {"periodo": p, "autorizadas": q}
        for p, q in dados_classificacao["periodos"].items()
    ]


def _formatar_periodos_cemei(informacao_escola_por_classificacao, dados_classificacao):
    informacao_escola_por_classificacao["periodos"] = {}
    turma_infantil = dados_classificacao["turma_infantil"]
    if len(turma_infantil) > 0:
        informacao_escola_por_classificacao["periodos"]["turma_infantil"] = [
            {"periodo": p, "autorizadas": q} for p, q in turma_infantil.items()
        ]
    por_idade = dados_classificacao["por_idade"]
    if len(por_idade) > 0:
        informacao_escola_por_classificacao["periodos"]["por_idade"] = [
            {"periodo": p, "faixa_etaria": q} for p, q in por_idade.items()
        ]


def _formatar_periodos_cei(informacao_escola_por_classificacao, dados_classificacao):
    informacao_escola_por_classificacao["periodos"] = [
        {"periodo": p, "faixa_etaria": q}
        for p, q in dados_classificacao["periodos"].items()
    ]
