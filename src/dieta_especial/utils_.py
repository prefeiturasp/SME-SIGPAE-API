import json
import re
from collections import defaultdict
from datetime import datetime
from itertools import chain
from typing import List

from django.core.exceptions import ValidationError
from django.db.models import CharField, F, IntegerField, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce
from django.http import QueryDict

from src.dieta_especial.logs_models.models import (
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
)
from src.escola.utils import faixa_to_string

from .constants import (
    UNIDADES_CEI,
    UNIDADES_CEMEI,
    UNIDADES_EMEBS,
    UNIDADES_EMEI_EMEF_CIEJA,
    UNIDADES_SEM_PERIODOS,
)
from .solicitacao_dieta_especial.models import SolicitacaoDietaEspecial


def log_create(protocolo_padrao, user=None):
    historico = {}

    historico["created_at"] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    historico["user"] = (
        {
            "uuid": str(user.uuid),
            "email": user.email,
            "username": user.username,
            "nome": user.nome,
        }
        if user
        else user
    )
    historico["action"] = "CREATE"

    editais = []
    for edital in protocolo_padrao.editais.all():
        editais.append(edital.numero)

    substituicoes = []
    for substituicao in protocolo_padrao.substituicoes.all():
        alimentos_substitutos = [
            {"uuid": str(sub.uuid), "nome": sub.nome}
            for sub in substituicao.alimentos_substitutos.all()
        ]
        subs = [
            {"uuid": str(sub.uuid), "nome": sub.nome}
            for sub in substituicao.substitutos.all()
        ]

        substitutos = [*alimentos_substitutos, *subs]
        substituicoes.append(
            {
                "tipo": {"from": None, "to": substituicao.tipo},
                "alimento": {
                    "from": None,
                    "to": {
                        "id": substituicao.alimento.id,
                        "nome": substituicao.alimento.nome,
                    },
                },
                "substitutos": {"from": None, "to": substitutos},
            }
        )

    historico["changes"] = [
        {
            "field": "criado_em",
            "from": None,
            "to": protocolo_padrao.criado_em.strftime("%Y-%m-%d %H:%M:%S"),
        },
        {"field": "id", "from": None, "to": protocolo_padrao.id},
        {
            "field": "nome_protocolo",
            "from": None,
            "to": protocolo_padrao.nome_protocolo,
        },
        {
            "field": "orientacoes_gerais",
            "from": None,
            "to": protocolo_padrao.orientacoes_gerais,
        },
        {"field": "status", "from": None, "to": protocolo_padrao.status},
        {"field": "uuid", "from": None, "to": str(protocolo_padrao.uuid)},
        {"field": "substituicoes", "changes": substituicoes},
        {"field": "editais", "from": None, "to": editais},
    ]

    protocolo_padrao.historico = json.dumps([historico])
    protocolo_padrao.save()


def log_update(
    instance,
    validated_data,
    substituicoes_old,
    substituicoes_new,
    new_editais,
    old_editais,
    user=None,
):
    import json
    from datetime import datetime

    historico = {}
    changes = diff_protocolo_padrao(instance, validated_data, new_editais, old_editais)
    changes_subs = diff_substituicoes(substituicoes_old, substituicoes_new)

    if changes_subs:
        changes.append({"field": "substituicoes", "changes": changes_subs})

    if changes:
        historico["updated_at"] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        historico["user"] = (
            {
                "uuid": str(user.uuid),
                "email": user.email,
                "username": user.username,
                "nome": user.nome,
            }
            if user
            else user
        )
        historico["action"] = "UPDATE"
        historico["changes"] = changes

        hist = json.loads(instance.historico) if instance.historico else []
        hist.append(historico)

        instance.historico = json.dumps(hist)


def diff_protocolo_padrao(instance, validated_data, new_editais, old_editais):
    changes = []

    if instance.nome_protocolo != validated_data["nome_protocolo"]:
        changes.append(
            {
                "field": "nome_protocolo",
                "from": instance.nome_protocolo,
                "to": validated_data["nome_protocolo"],
            }
        )

    if instance.orientacoes_gerais != validated_data["orientacoes_gerais"]:
        changes.append(
            {
                "field": "orientacoes_gerais",
                "from": instance.orientacoes_gerais,
                "to": validated_data["orientacoes_gerais"],
            }
        )

    if instance.status != validated_data["status"]:
        changes.append(
            {"field": "status", "from": instance.status, "to": validated_data["status"]}
        )

    new_editais_list_ordered = set(
        new_editais.order_by("uuid").values_list("uuid", flat=True)
    )
    old_editais_list_ordered = set(
        old_editais.all().order_by("uuid").values_list("uuid", flat=True)
    )
    if new_editais_list_ordered != old_editais_list_ordered:
        changes.append(
            {
                "field": "editais",
                "from": [edital.numero for edital in old_editais.all()],
                "to": [edital.numero for edital in new_editais],
            }
        )

    return changes


def diff_substituicoes(substituicoes_old, substituicoes_new):  # noqa C901
    substituicoes = []

    # Tratando adição e edição de substituíções
    if substituicoes_old.all().count() <= len(substituicoes_new):
        for index, subs_new in enumerate(substituicoes_new):
            sub = {}

            try:
                subs = substituicoes_old.all().order_by("id")[index]
            except IndexError:
                subs = None

            if not subs or subs.alimento.id != subs_new["alimento"].id:
                sub["alimento"] = {
                    "from": {
                        "id": subs.alimento.id if subs else None,
                        "nome": subs.alimento.nome if subs else None,
                    },
                    "to": {
                        "id": subs_new["alimento"].id,
                        "nome": subs_new["alimento"].nome,
                    },
                }

            if not subs or subs.tipo != subs_new["tipo"]:
                sub["tipo"] = {
                    "from": subs.tipo if subs else None,
                    "to": subs_new["tipo"] if subs_new else None,
                }

            al_subs_ids = (
                subs.alimentos_substitutos.all()
                .order_by("id")
                .values_list("id", flat=True)
                if subs
                else []
            )
            subs_ids_old = (
                subs.substitutos.all().order_by("id").values_list("id", flat=True)
                if subs
                else []
            )

            ids_olds = [*al_subs_ids, *subs_ids_old]
            ids_news = sorted([s.id for s in subs_new["substitutos"]])

            from itertools import zip_longest

            if any(
                map(
                    lambda t: t[0] != t[1],
                    zip_longest(ids_olds, ids_news, fillvalue=False),
                )
            ):
                from_ = None

                if subs:
                    alimentos_substitutos = [
                        {"uuid": str(sub.uuid), "nome": sub.nome}
                        for sub in subs.alimentos_substitutos.all()
                    ]

                    substitutos_ = [
                        {"uuid": str(sub.uuid), "nome": sub.nome}
                        for sub in subs.substitutos.all()
                    ]

                    substitutos = [*alimentos_substitutos, *substitutos_]
                    from_ = (
                        [
                            {"uuid": sub["uuid"], "nome": sub["nome"]}
                            for sub in substitutos
                        ]
                        if substitutos
                        else None
                    )

                sub["substitutos"] = {
                    "from": from_,
                    "to": (
                        [
                            {"uuid": str(s.uuid), "nome": s.nome}
                            for s in subs_new["substitutos"]
                        ]
                        if subs_new["substitutos"]
                        else None
                    ),
                }

            if sub:
                substituicoes.append(sub)

    else:
        # trata a remoção de uma substituíção
        for index, subs in enumerate(substituicoes_old.all()):
            sub = {}
            try:
                subs_new = substituicoes_new[index]
            except IndexError:
                subs_new = None

            if not subs_new or subs.alimento.id != subs_new["alimento"].id:
                sub["alimento"] = {
                    "from": {"id": subs.alimento.id, "nome": subs.alimento.nome},
                    "to": {
                        "id": subs_new["alimento"].id if subs_new else None,
                        "nome": subs_new["alimento"].nome if subs_new else None,
                    },
                }

            if not subs_new or subs.tipo != subs_new["tipo"]:
                sub["tipo"] = {
                    "from": subs.tipo,
                    "to": subs_new["tipo"] if subs_new else None,
                }

            al_sub_ids = (
                subs.alimentos_substitutos.all()
                .order_by("id")
                .values_list("id", flat=True)
                if subs
                else []
            )
            subs_ids_old = (
                subs.substitutos.all().order_by("id").values_list("id", flat=True)
                if subs
                else []
            )

            ids_olds = [*al_sub_ids, *subs_ids_old]
            ids_news = (
                sorted([s.id for s in subs_new["substitutos"]]) if subs_new else []
            )

            from itertools import zip_longest

            if any(
                map(
                    lambda t: t[0] != t[1],
                    zip_longest(ids_olds, ids_news, fillvalue=False),
                )
            ):
                to_ = None
                if subs_new:
                    to_ = (
                        [
                            {"uuid": str(s.uuid), "nome": s.nome}
                            for s in subs_new["substitutos"]
                        ]
                        if subs_new["substitutos"]
                        else None
                    )

                alimentos_substitutos = [
                    {"uuid": str(sub.uuid), "nome": sub.nome}
                    for sub in subs.alimentos_substitutos.all()
                ]

                substitutos_ = [
                    {"uuid": str(sub.uuid), "nome": sub.nome}
                    for sub in subs.substitutos.all()
                ]

                substitutos = [*alimentos_substitutos, *substitutos_]

                sub["substitutos"] = {
                    "from": (
                        [
                            {"uuid": sub["uuid"], "nome": sub["nome"]}
                            for sub in substitutos
                        ]
                        if substitutos
                        else None
                    ),
                    "to": to_,
                }

            if sub:
                substituicoes.append(sub)

    return substituicoes


def is_alpha_numeric_and_has_single_space(descricao):
    return bool(re.match(r"[A-Za-z0-9\s]+$", descricao))


def gerar_filtros_relatorio_historico(query_params: QueryDict) -> tuple:
    map_filtros = {
        "escola__tipo_gestao__uuid": query_params.get("tipo_gestao", None),
        "escola__tipo_unidade__uuid__in": query_params.getlist(
            "tipos_unidades_selecionadas", None
        ),
        "escola__lote__uuid": query_params.get("lote", None),
        "escola__uuid__in": query_params.getlist(
            "unidades_educacionais_selecionadas", None
        ),
        "periodo_escolar__uuid__in": query_params.getlist(
            "periodos_escolares_selecionadas", None
        ),
        "classificacao__id__in": query_params.getlist(
            "classificacoes_selecionadas", None
        ),
        "quantidade__gt": 0,
    }

    data_dieta = query_params.get("data")
    if not data_dieta:
        raise ValidationError("`data` é um parâmetro obrigatório.")
    try:
        formato = "%d/%m/%Y"
        data = datetime.strptime(data_dieta, formato)
    except ValueError:
        raise ValidationError(
            f"A data {data_dieta} não corresponde ao formato esperado 'dd/mm/YYYY'."
        )

    map_filtros.update(
        {"data__day": data.day, "data__month": data.month, "data__year": data.year}
    )

    filtros = {
        key: value for key, value in map_filtros.items() if value not in [None, []]
    }
    return filtros, data_dieta


def _dados_dietas_escolas_cei(filtros: dict, eh_exportacao: bool = False) -> List[dict]:
    queryset = LogQuantidadeDietasAutorizadasCEI.objects.filter(**filtros)
    if eh_exportacao:
        queryset = queryset.filter(faixa_etaria__isnull=False)

    logs_dietas_escolas_cei = (
        queryset.select_related(
            "escola",
            "periodo_escolar",
            "escola__tipo_unidade",
            "classificacao",
            "faixa_etaria",
        )
        .annotate(
            nome_escola=F("escola__nome"),
            nome_periodo_escolar=Coalesce(F("periodo_escolar__nome"), Value(None)),
            tipo_unidade=F("escola__tipo_unidade__iniciais"),
            lote=F("escola__lote__nome"),
            dre=F("escola__lote__diretoria_regional__iniciais"),
            nome_classificacao=F("classificacao__nome"),
            quantidade_total=Sum("quantidade"),
            inicio=Coalesce(F("faixa_etaria__inicio"), Value(None)),
            fim=Coalesce(F("faixa_etaria__fim"), Value(None)),
            infantil_ou_fundamental=Value(None, output_field=CharField()),
            cei_ou_emei=Value(None, output_field=CharField()),
        )
        .values(
            "nome_escola",
            "tipo_unidade",
            "lote",
            "dre",
            "nome_classificacao",
            "nome_periodo_escolar",
            "infantil_ou_fundamental",
            "cei_ou_emei",
            "data",
            "quantidade_total",
            "inicio",
            "fim",
        )
        .order_by("nome_escola", "faixa_etaria__inicio")
    )

    return logs_dietas_escolas_cei


def _dados_dietas_escolas_comuns(filtros: dict) -> QuerySet[dict]:
    filtro_por_tipo_unidade = Q(
        Q(
            escola__tipo_unidade__iniciais__in=UNIDADES_EMEBS,
            periodo_escolar__isnull=True,
            cei_ou_emei="N/A",
            infantil_ou_fundamental__in=["FUNDAMENTAL", "INFANTIL"],
        )
        | Q(
            escola__tipo_unidade__iniciais__in=UNIDADES_CEMEI,
            periodo_escolar__nome="INTEGRAL",
            cei_ou_emei__in=["CEI", "EMEI"],
        )
    )
    logs_dietas_outras_escolas = (
        LogQuantidadeDietasAutorizadas.objects.filter(**filtros)
        .exclude(filtro_por_tipo_unidade)
        .select_related(
            "escola", "periodo_escolar", "escola__tipo_unidade", "classificacao"
        )
        .annotate(
            nome_escola=F("escola__nome"),
            nome_periodo_escolar=Coalesce(F("periodo_escolar__nome"), Value(None)),
            tipo_unidade=F("escola__tipo_unidade__iniciais"),
            lote=F("escola__lote__nome"),
            dre=F("escola__lote__diretoria_regional__iniciais"),
            nome_classificacao=F("classificacao__nome"),
            quantidade_total=Sum("quantidade"),
            inicio=Value(None, output_field=IntegerField()),
            fim=Value(None, output_field=IntegerField()),
        )
        .values(
            "nome_escola",
            "tipo_unidade",
            "lote",
            "dre",
            "nome_classificacao",
            "nome_periodo_escolar",
            "infantil_ou_fundamental",
            "cei_ou_emei",
            "data",
            "quantidade_total",
            "inicio",
            "fim",
        )
        .order_by("nome_escola")
    )

    return logs_dietas_outras_escolas


def get_logs_historico_dietas(filtros, eh_exportacao=False) -> list:
    log_escolas_cei = _dados_dietas_escolas_cei(filtros, eh_exportacao)
    log_escolas = _dados_dietas_escolas_comuns(filtros)
    if eh_exportacao:
        log_escolas = [
            log
            for log in log_escolas
            if log.get("nome_periodo_escolar") is not None
            or log.get("tipo_unidade") in {"CEU GESTAO", "CMCT"}
        ]
    log_dietas = sorted(
        chain(log_escolas_cei, log_escolas), key=lambda x: x["nome_escola"]
    )
    return log_dietas


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


def filtra_relatorio_recreio_nas_ferias(query_params: QueryDict) -> QuerySet:
    """
    Retorna um queryset unificado com alunos matriculados e não matriculados que atendem aos critérios do Recreio nas Férias.

    Args:
        query_params (QueryDict): Parâmetros de filtro da requisição.
    Returns:
        QuerySet: Conjunto de solicitações filtradas e ordenadas por escola de destino.
    """
    filtros = gera_filtros_relatorio_recreio_nas_ferias(query_params)
    padrao = filtros.get("padrao", {})
    matriculado = filtros.get("matriculado", {})
    nao_matriculado = filtros.get("nao_matriculado", {})

    status_permitidos = [
        SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
        SolicitacaoDietaEspecial.workflow_class.TERMINADA_AUTOMATICAMENTE_SISTEMA,
    ]

    filtro_matriculados = Q(
        status__in=status_permitidos,
        tipo_solicitacao="ALTERACAO_UE",
        motivo_alteracao_ue__nome__icontains="recreio",
        **padrao,
        **matriculado,
    )

    filtro_nao_matriculados = Q(
        status__in=status_permitidos,
        tipo_solicitacao__in=[
            SolicitacaoDietaEspecial.COMUM,
            SolicitacaoDietaEspecial.ALUNO_NAO_MATRICULADO,
        ],
        dieta_para_recreio_ferias=True,
        **padrao,
        **nao_matriculado,
    )

    queryset = SolicitacaoDietaEspecial.objects.filter(
        filtro_matriculados | filtro_nao_matriculados
    ).order_by("escola_destino__nome")

    return queryset


def gera_filtros_relatorio_recreio_nas_ferias(query_params: QueryDict) -> dict:
    """
    Gera os dicionários de filtros com base nos parâmetros da requisição.

    Args:
        query_params (QueryDict): Parâmetros enviados na requisição HTTP.
    Returns:
        dict:  Dicionário com filtros para padrao, matriculado e nao_matriculado.
    """
    filtros = {
        "padrao": {
            "escola_destino__lote__uuid": query_params.get("lote", None),
            "escola_destino__uuid__in": query_params.getlist(
                "unidades_educacionais_selecionadas", None
            ),
            "classificacao__id__in": query_params.getlist(
                "classificacoes_selecionadas", None
            ),
            "alergias_intolerancias__id__in": query_params.getlist(
                "alergias_intolerancias_selecionadas", None
            ),
        },
        "matriculado": {},
        "nao_matriculado": {},
    }

    data_inicio = query_params.get("data_inicio")
    data_fim = query_params.get("data_fim")

    if data_inicio:
        data_ini = _parse_data(data_inicio, "data_inicio")
        filtros["padrao"]["data_termino__gte"] = data_ini
    if data_fim:
        data_fim = _parse_data(data_fim, "data_fim")
        filtros["padrao"]["data_inicio__lte"] = data_fim

    filtros["padrao"] = {
        key: value
        for key, value in filtros["padrao"].items()
        if value not in [None, []]
    }
    return filtros


def _parse_data(valor: str, campo: str) -> datetime:
    """
    Converte string de data no formato 'dd/mm/yyyy' para objeto date
    Args:
        valor (str): string contendo a data.
        campo (str): nome do campo para mensagens de erro.
    Raises:
        ValidationError: se o formato da data for inválido.
    Returns:
        datetime:  objeto date convertido.
    """
    try:
        return datetime.strptime(valor, "%d/%m/%Y").date()
    except ValueError:
        raise ValidationError(
            f"Formato de data inválido para '{campo}'. Use o formato dd/mm/yyyy"
        )
