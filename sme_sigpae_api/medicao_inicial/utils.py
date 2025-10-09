import calendar
import datetime
import json
import logging
from calendar import monthrange
from collections import defaultdict
from functools import reduce

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import IntegerField, Sum
from django.db.models.functions import Cast
from django.db.utils import IntegrityError

from sme_sigpae_api.dados_comuns.constants import (
    MAX_COLUNAS,
    ORDEM_CAMPOS,
    ORDEM_PERIODOS_GRUPOS,
    ORDEM_PERIODOS_GRUPOS_CEI,
    ORDEM_PERIODOS_GRUPOS_CEMEI,
    ORDEM_PERIODOS_GRUPOS_EMEBS,
    TIPOS_TURMAS_EMEBS,
)
from sme_sigpae_api.dados_comuns.utils import convert_base64_to_contentfile
from sme_sigpae_api.dieta_especial.models import (
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
)
from sme_sigpae_api.escola.models import (
    Aluno,
    DiaCalendario,
    Escola,
    FaixaEtaria,
    GrupoUnidadeEscolar,
    LogAlunosMatriculadosFaixaEtariaDia,
    LogAlunosMatriculadosPeriodoEscola,
    Lote,
    PeriodoEscolar,
)
from sme_sigpae_api.escola.utils import string_to_faixa
from sme_sigpae_api.inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoNormal,
)
from sme_sigpae_api.medicao_inicial.models import (
    AlimentacaoLancamentoEspecial,
    RelatorioFinanceiro,
    SolicitacaoMedicaoInicial,
    ValorMedicao,
)
from sme_sigpae_api.paineis_consolidados.models import SolicitacoesEscola
from sme_sigpae_api.terceirizada.models import Edital

logger = logging.getLogger(__name__)


def get_lista_categorias_campos(medicao, tipo_turma=None):
    queryset = medicao.valores_medicao

    if tipo_turma:
        queryset = medicao.valores_medicao.filter(infantil_ou_fundamental=tipo_turma)

    lista_categorias_campos = sorted(
        list(
            queryset.exclude(
                nome_campo__in=["observacoes", "dietas_autorizadas", "matriculados"]
            )
            .values_list("categoria_medicao__nome", "nome_campo")
            .distinct()
        )
    )
    if medicao.grupo and medicao.grupo.nome == "Solicitações de Alimentação":
        lista_ = []
        if (
            "SOLICITAÇÕES DE ALIMENTAÇÃO",
            "lanche_emergencial",
        ) in lista_categorias_campos:
            lista_ += [
                ("LANCHE EMERGENCIAL", "solicitado"),
                ("LANCHE EMERGENCIAL", "consumido"),
            ]
        if ("SOLICITAÇÕES DE ALIMENTAÇÃO", "kit_lanche") in lista_categorias_campos:
            lista_ += [("KIT LANCHE", "solicitado"), ("KIT LANCHE", "consumido")]
        lista_categorias_campos = lista_
    return lista_categorias_campos


def get_lista_categorias_campos_cei(medicao):
    valores = (
        medicao.valores_medicao.exclude(
            nome_campo__in=["observacoes", "dietas_autorizadas", "matriculados"]
        )
        .values("categoria_medicao__nome", "faixa_etaria__fim", "faixa_etaria_id")
        .distinct()
    )

    faixa_etaria_ids = [v["faixa_etaria_id"] for v in valores]
    faixas_etarias = FaixaEtaria.objects.filter(id__in=faixa_etaria_ids, ativo=True)
    faixa_etaria_dict = {fe.id: str(fe) for fe in faixas_etarias}

    valores_ordenados = sorted(
        valores, key=lambda x: (x["categoria_medicao__nome"], x["faixa_etaria__fim"])
    )

    lista_categorias_campos = [
        (v["categoria_medicao__nome"], faixa_etaria_dict[v["faixa_etaria_id"]])
        for v in valores_ordenados
    ]

    return lista_categorias_campos


def build_dict_relacao_categorias_e_campos(medicao, tipo_turma=None):
    CATEGORIA = 0
    CAMPO = 1

    lista_categorias_campos = get_lista_categorias_campos(medicao, tipo_turma)
    dict_categorias_campos = {}
    for categoria_campo in lista_categorias_campos:
        if categoria_campo[CATEGORIA] not in dict_categorias_campos.keys():
            if "DIETA" in categoria_campo[CATEGORIA]:
                dict_categorias_campos[categoria_campo[CATEGORIA]] = ["aprovadas"]
            elif medicao.grupo and medicao.grupo.nome == "Solicitações de Alimentação":
                dict_categorias_campos[categoria_campo[CATEGORIA]] = []
            elif medicao.grupo and medicao.grupo.nome in [
                "Programas e Projetos",
                "ETEC",
            ]:
                dict_categorias_campos[categoria_campo[CATEGORIA]] = [
                    "total_refeicoes_pagamento",
                    "total_sobremesas_pagamento",
                ]
            else:
                dict_categorias_campos[categoria_campo[CATEGORIA]] = [
                    "matriculados",
                    "total_refeicoes_pagamento",
                    "total_sobremesas_pagamento",
                ]
            dict_categorias_campos[categoria_campo[CATEGORIA]] += [
                categoria_campo[CAMPO]
            ]
        else:
            dict_categorias_campos[categoria_campo[CATEGORIA]] += [
                categoria_campo[CAMPO]
            ]
    return dict_categorias_campos


def build_dict_relacao_categorias_e_campos_cei(medicao):
    CATEGORIA = 0
    FAIXA = 1

    lista_categorias_campos = get_lista_categorias_campos_cei(medicao)
    dict_categorias_campos = {}
    for categoria_campo in lista_categorias_campos:
        if categoria_campo[CATEGORIA] not in dict_categorias_campos.keys():
            dict_categorias_campos[categoria_campo[CATEGORIA]] = [
                categoria_campo[FAIXA]
            ]
        else:
            dict_categorias_campos[categoria_campo[CATEGORIA]] += [
                categoria_campo[FAIXA]
            ]
    return dict_categorias_campos


def get_tamanho_colunas_periodos(tabelas, ordem_periodos_grupos, tipo_unidade=None):
    for tabela in tabelas:
        for periodo in tabela["periodos"]:
            if tipo_unidade == "CEMEI" and periodo in ["INTEGRAL", "PARCIAL"]:
                tabela["len_periodos"] += [
                    sum(
                        (x["numero_campos"] * 2) + 1
                        for x in tabela["categorias_dos_periodos"][periodo]
                    )
                ]
            else:
                tabela["len_periodos"] += [
                    sum(
                        x["numero_campos"]
                        for x in tabela["categorias_dos_periodos"][periodo]
                    )
                ]
            tabela["ordem_periodos_grupos"] += [ordem_periodos_grupos[periodo]]


def get_ordem_grupos_cei(tabelas, ORDEM_PERIODOS_GRUPOS_CEI):
    for tabela in tabelas:
        for periodo in tabela["periodos"]:
            tabela["ordem_periodos_grupos"] += [ORDEM_PERIODOS_GRUPOS_CEI[periodo]]


def get_categorias_dos_periodos(
    nome_periodo,
    tabelas,
    indice_atual,
    categoria,
    dict_categorias_campos,
    segunda_tabela=False,
    limite_campos=0,
):
    numero_campos = len(dict_categorias_campos[categoria])
    if numero_campos > MAX_COLUNAS:
        if segunda_tabela:
            numero_campos = (
                (numero_campos - limite_campos)
                if limite_campos
                else (numero_campos - MAX_COLUNAS)
            )
        else:
            numero_campos = limite_campos if limite_campos else MAX_COLUNAS
    if nome_periodo in tabelas[indice_atual]["categorias_dos_periodos"].keys():
        tabelas[indice_atual]["categorias_dos_periodos"][nome_periodo].append(
            {
                "categoria": categoria,
                "numero_campos": numero_campos,
            }
        )
    else:
        tabelas[indice_atual]["categorias_dos_periodos"][nome_periodo] = [
            {
                "categoria": categoria,
                "numero_campos": numero_campos,
            }
        ]


def append_tabela(
    tabelas,
    indice_atual,
    nome_periodo,
    categoria,
    dict_categorias_campos,
    segunda_tabela=False,
    tipo_unidade=None,
    limite_campos=None,
):
    tabelas[indice_atual]["periodos"] += [nome_periodo]
    tabelas[indice_atual]["categorias"] += [categoria]

    if tipo_unidade == "CEMEI":
        if not segunda_tabela:
            faixas_etarias = tabelas[indice_atual]["faixas_etarias"]
            len_faixas = (len(faixas_etarias) * 2) - 1 if faixas_etarias else 0

            len_colunas = len(tabelas[indice_atual]["nomes_campos"]) + len_faixas
            limite_campos = MAX_COLUNAS - len_colunas
    elif limite_campos is None:
        limite_campos = MAX_COLUNAS - len(tabelas[indice_atual]["nomes_campos"])

    if segunda_tabela:
        tabelas = append_segunda_tabela(
            tipo_unidade,
            nome_periodo,
            tabelas,
            indice_atual,
            dict_categorias_campos,
            categoria,
            limite_campos,
        )
    else:
        if tipo_unidade == "CEMEI" and nome_periodo in ["INTEGRAL", "PARCIAL"]:
            tabelas[indice_atual]["faixas_etarias"] += [
                faixa for faixa in dict_categorias_campos[categoria]
            ][:limite_campos]
        else:
            tabelas[indice_atual]["nomes_campos"] += [
                campo
                for campo in ORDEM_CAMPOS
                if campo in dict_categorias_campos[categoria]
            ][:limite_campos]

        tabelas[indice_atual]["len_categorias"] += [limite_campos]
    get_categorias_dos_periodos(
        nome_periodo,
        tabelas,
        indice_atual,
        categoria,
        dict_categorias_campos,
        segunda_tabela,
        limite_campos,
    )
    return tabelas, limite_campos


def append_segunda_tabela(
    tipo_unidade,
    nome_periodo,
    tabelas,
    indice_atual,
    dict_categorias_campos,
    categoria,
    limite_campos,
):
    if tipo_unidade == "CEMEI" and nome_periodo in ["INTEGRAL", "PARCIAL"]:
        tabelas[indice_atual]["faixas_etarias"] += [
            faixa for faixa in dict_categorias_campos[categoria]
        ][limite_campos:]

        tabelas[indice_atual]["len_categorias"] += [
            (len(dict_categorias_campos[categoria][limite_campos:]) * 2) - 1
        ]
    else:
        tabelas[indice_atual]["nomes_campos"] += [
            campo
            for campo in ORDEM_CAMPOS
            if campo in dict_categorias_campos[categoria]
        ][limite_campos:]
        tabelas[indice_atual]["len_categorias"] += [
            len(dict_categorias_campos[categoria][limite_campos:])
        ]
    return tabelas


def build_headers_tabelas(solicitacao):
    tabelas = [
        {
            "periodos": [],
            "categorias": [],
            "nomes_campos": [],
            "len_periodos": [],
            "len_categorias": [],
            "valores_campos": [],
            "ordem_periodos_grupos": [],
            "dias_letivos": [],
            "categorias_dos_periodos": {},
        }
    ]

    indice_atual = 0
    for medicao in get_medicoes_ordenadas(solicitacao, ORDEM_PERIODOS_GRUPOS):
        dict_categorias_campos = build_dict_relacao_categorias_e_campos(medicao)
        for categoria in dict_categorias_campos.keys():
            nome_periodo = (
                medicao.periodo_escolar.nome
                if not medicao.grupo
                else (
                    f"{medicao.grupo.nome} - {medicao.periodo_escolar.nome}"
                    if medicao.periodo_escolar
                    else medicao.grupo.nome
                )
            )
            if (
                len(tabelas[indice_atual]["nomes_campos"])
                + len(dict_categorias_campos[categoria])
                > MAX_COLUNAS
            ) or (
                "total_refeicoes_pagamento" in tabelas[indice_atual]["nomes_campos"]
                and "total_refeicoes_pagamento" in dict_categorias_campos[categoria]
            ):
                if len(dict_categorias_campos[categoria]) > MAX_COLUNAS:
                    tabelas, limite = append_tabela(
                        tabelas,
                        indice_atual,
                        nome_periodo,
                        categoria,
                        dict_categorias_campos,
                    )
                    indice_atual += 1
                    tabelas += [
                        {
                            "periodos": [],
                            "categorias": [],
                            "nomes_campos": [],
                            "len_periodos": [],
                            "len_categorias": [],
                            "valores_campos": [],
                            "ordem_periodos_grupos": [],
                            "dias_letivos": [],
                            "categorias_dos_periodos": {},
                        }
                    ]
                    append_tabela(
                        tabelas,
                        indice_atual,
                        nome_periodo,
                        categoria,
                        dict_categorias_campos,
                        True,
                        limite_campos=limite,
                    )
                else:
                    indice_atual += 1
                    tabelas += [
                        {
                            "periodos": [],
                            "categorias": [],
                            "nomes_campos": [],
                            "len_periodos": [],
                            "len_categorias": [],
                            "valores_campos": [],
                            "ordem_periodos_grupos": [],
                            "dias_letivos": [],
                            "categorias_dos_periodos": {},
                        }
                    ]
                    tabelas[indice_atual]["periodos"] += [nome_periodo]
                    tabelas[indice_atual]["categorias"] += [categoria]
                    tabelas[indice_atual]["nomes_campos"] += [
                        campo
                        for campo in ORDEM_CAMPOS
                        if campo in dict_categorias_campos[categoria]
                    ]
                    tabelas[indice_atual]["len_categorias"] += [
                        len(dict_categorias_campos[categoria])
                    ]
                    get_categorias_dos_periodos(
                        nome_periodo,
                        tabelas,
                        indice_atual,
                        categoria,
                        dict_categorias_campos,
                    )
            else:
                adiciona_valores_header(
                    nome_periodo,
                    tabelas,
                    dict_categorias_campos,
                    indice_atual,
                    categoria,
                )
                get_categorias_dos_periodos(
                    nome_periodo,
                    tabelas,
                    indice_atual,
                    categoria,
                    dict_categorias_campos,
                )

    get_tamanho_colunas_periodos(tabelas, ORDEM_PERIODOS_GRUPOS)
    return tabelas


def build_headers_tabelas_emebs(solicitacao):
    tabelas = [
        {
            "periodos": [],
            "categorias": [],
            "nomes_campos": [],
            "len_periodos": [],
            "len_categorias": [],
            "valores_campos": [],
            "ordem_periodos_grupos": [],
            "dias_letivos": [],
            "categorias_dos_periodos": {},
        }
    ]

    indice_atual = 0

    for medicao in get_medicoes_ordenadas(solicitacao, ORDEM_PERIODOS_GRUPOS):
        for tipo_turma in TIPOS_TURMAS_EMEBS:
            dict_categorias_campos = build_dict_relacao_categorias_e_campos(
                medicao, tipo_turma
            )

            for categoria in dict_categorias_campos.keys():
                nome_periodo = (
                    f"{medicao.periodo_escolar.nome} - {tipo_turma}"
                    if not medicao.grupo
                    else (
                        f"{medicao.grupo.nome} - {medicao.periodo_escolar.nome} - {tipo_turma}"
                        if medicao.periodo_escolar
                        else f"{medicao.grupo.nome} - {tipo_turma}"
                    )
                )

                if (
                    len(tabelas[indice_atual]["nomes_campos"])
                    + len(dict_categorias_campos[categoria])
                    > MAX_COLUNAS
                ) or (
                    "total_refeicoes_pagamento" in tabelas[indice_atual]["nomes_campos"]
                    and "total_refeicoes_pagamento" in dict_categorias_campos[categoria]
                ):
                    if len(dict_categorias_campos[categoria]) > MAX_COLUNAS:
                        tabelas, limite = append_tabela(
                            tabelas,
                            indice_atual,
                            nome_periodo,
                            categoria,
                            dict_categorias_campos,
                        )
                        indice_atual += 1
                        tabelas += [
                            {
                                "periodos": [],
                                "categorias": [],
                                "nomes_campos": [],
                                "len_periodos": [],
                                "len_categorias": [],
                                "valores_campos": [],
                                "ordem_periodos_grupos": [],
                                "dias_letivos": [],
                                "categorias_dos_periodos": {},
                            }
                        ]
                        append_tabela(
                            tabelas,
                            indice_atual,
                            nome_periodo,
                            categoria,
                            dict_categorias_campos,
                            True,
                            limite_campos=limite,
                        )
                    else:
                        indice_atual += 1
                        tabelas += [
                            {
                                "periodos": [],
                                "categorias": [],
                                "nomes_campos": [],
                                "len_periodos": [],
                                "len_categorias": [],
                                "valores_campos": [],
                                "ordem_periodos_grupos": [],
                                "dias_letivos": [],
                                "categorias_dos_periodos": {},
                            }
                        ]
                        tabelas[indice_atual]["periodos"] += [nome_periodo]
                        tabelas[indice_atual]["categorias"] += [categoria]
                        tabelas[indice_atual]["nomes_campos"] += [
                            campo
                            for campo in ORDEM_CAMPOS
                            if campo in dict_categorias_campos[categoria]
                        ]
                        tabelas[indice_atual]["len_categorias"] += [
                            len(dict_categorias_campos[categoria])
                        ]
                        get_categorias_dos_periodos(
                            nome_periodo,
                            tabelas,
                            indice_atual,
                            categoria,
                            dict_categorias_campos,
                        )
                else:
                    adiciona_valores_header(
                        nome_periodo,
                        tabelas,
                        dict_categorias_campos,
                        indice_atual,
                        categoria,
                    )
                    get_categorias_dos_periodos(
                        nome_periodo,
                        tabelas,
                        indice_atual,
                        categoria,
                        dict_categorias_campos,
                    )

    get_tamanho_colunas_periodos(tabelas, ORDEM_PERIODOS_GRUPOS_EMEBS)
    return tabelas


def create_new_table():
    return {
        "periodos": [],
        "categorias": [],
        "len_periodos": [],
        "len_categorias": [],
        "valores_campos": [],
        "ordem_periodos_grupos": [],
    }


def add_periodo_to_table(  # noqa: C901
    table, nome_periodo, categoria, faixa, len_faixas, dict_categorias_campos
):
    if nome_periodo not in table["periodos"]:
        table["periodos"].append(nome_periodo)

    categoria_obj = next(
        (
            item
            for item in table["categorias"]
            if item["categoria"] == categoria and item["periodo"] == nome_periodo
        ),
        None,
    )

    if "periodo_values" not in table:
        table["periodo_values"] = defaultdict(int)
    if "categoria_values" not in table:
        table["categoria_values"] = defaultdict(int)

    if not categoria_obj:
        table["categorias"].append(
            {"categoria": categoria, "faixas_etarias": [faixa], "periodo": nome_periodo}
        )
        table["periodo_values"][nome_periodo] += 2
        nome_categoria = categoria
        if nome_periodo == "PARCIAL":
            nome_categoria = f"{categoria}__PARCIAL"
        table["categoria_values"][nome_categoria] += 2

        if len_faixas == len(dict_categorias_campos[categoria]):
            table["categorias"][-1]["faixas_etarias"].append("total")
            table["periodo_values"][nome_periodo] += 1
            table["categoria_values"][nome_categoria] += 1
    else:
        if faixa not in categoria_obj["faixas_etarias"]:
            categoria_obj["faixas_etarias"].append(faixa)

            table["periodo_values"][nome_periodo] += 2
            nome_categoria = categoria
            if nome_periodo == "PARCIAL":
                nome_categoria = f"{categoria}__PARCIAL"
            table["categoria_values"][nome_categoria] += 2

            if len_faixas == len(dict_categorias_campos[categoria]):
                categoria_obj["faixas_etarias"].append("total")
                table["periodo_values"][nome_periodo] += 1
                table["categoria_values"][nome_categoria] += 1

    table["len_periodos"] = [
        table["periodo_values"][periodo] for periodo in table["periodos"]
    ]
    if nome_periodo == "PARCIAL":
        table["len_categorias"] = [
            (
                table["categoria_values"][f'{cat_obj["categoria"]}__PARCIAL']
                if cat_obj["periodo"] == "PARCIAL"
                else table["categoria_values"][cat_obj["categoria"]]
            )
            for cat_obj in table["categorias"]
        ]
    else:
        table["len_categorias"] = [
            table["categoria_values"][cat_obj["categoria"]]
            for cat_obj in table["categorias"]
        ]


def build_headers_tabelas_cei(solicitacao):
    MAX_FAIXAS = 7
    tabelas = [create_new_table()]
    indice_atual = 0
    cont_faixas = 1
    for medicao in get_medicoes_ordenadas(solicitacao, ORDEM_PERIODOS_GRUPOS_CEI):
        dict_categorias_campos = build_dict_relacao_categorias_e_campos_cei(medicao)
        for categoria, faixas in dict_categorias_campos.items():
            nome_periodo = medicao.periodo_escolar.nome
            len_faixas = 0
            for faixa in faixas:
                len_faixas += 1
                if cont_faixas <= MAX_FAIXAS:
                    cont_faixas += 1
                    add_periodo_to_table(
                        tabelas[indice_atual],
                        nome_periodo,
                        categoria,
                        faixa,
                        len_faixas,
                        dict_categorias_campos,
                    )
                else:
                    cont_faixas = 2
                    indice_atual += 1
                    tabelas.append(create_new_table())
                    add_periodo_to_table(
                        tabelas[indice_atual],
                        nome_periodo,
                        categoria,
                        faixa,
                        len_faixas,
                        dict_categorias_campos,
                    )

    get_ordem_grupos_cei(tabelas, ORDEM_PERIODOS_GRUPOS_CEI)

    return tabelas


def build_headers_tabelas_cemei(solicitacao):
    tabelas = [cria_tabela_vazia_cemei()]
    indice_atual = 0
    len_colunas = 0

    for medicao in get_medicoes_ordenadas(solicitacao, ORDEM_PERIODOS_GRUPOS_CEMEI):
        dict_categorias_campos = build_dict_relacao_categorias_e_campos_cemei(medicao)

        for categoria in dict_categorias_campos.keys():
            nome_periodo = (
                medicao.periodo_escolar.nome
                if not medicao.grupo
                else (
                    f"{medicao.grupo.nome} - {medicao.periodo_escolar.nome}"
                    if medicao.periodo_escolar
                    else medicao.grupo.nome
                )
            )
            faixas_etarias = tabelas[indice_atual]["faixas_etarias"]
            len_faixas = sum(2 if faixa != "total" else 1 for faixa in faixas_etarias)

            len_colunas = (
                (len(dict_categorias_campos[categoria]) * 2) + 1
                if nome_periodo in ["INTEGRAL", "PARCIAL"]
                else len(dict_categorias_campos[categoria])
            )

            if (
                len(tabelas[indice_atual]["nomes_campos"]) + len_faixas + len_colunas
                > MAX_COLUNAS
            ) or (
                "total_refeicoes_pagamento" in tabelas[indice_atual]["nomes_campos"]
                and "total_refeicoes_pagamento" in dict_categorias_campos[categoria]
            ):
                if len(dict_categorias_campos[categoria]) > MAX_COLUNAS:
                    limite_campos = 0
                    tabelas, limite_campos = append_tabela(
                        tabelas,
                        indice_atual,
                        nome_periodo,
                        categoria,
                        dict_categorias_campos,
                        False,
                        "CEMEI",
                        limite_campos,
                    )
                    indice_atual += 1
                    tabelas += [cria_tabela_vazia_cemei()]
                    append_tabela(
                        tabelas,
                        indice_atual,
                        nome_periodo,
                        categoria,
                        dict_categorias_campos,
                        True,
                        "CEMEI",
                        limite_campos,
                    )
                else:
                    indice_atual += 1
                    tabelas += [cria_tabela_vazia_cemei()]
                    tabelas[indice_atual]["periodos"] += [nome_periodo]
                    tabelas[indice_atual]["categorias"] += [categoria]
                    tabelas[indice_atual]["nomes_campos"] += [
                        campo
                        for campo in ORDEM_CAMPOS
                        if campo in dict_categorias_campos[categoria]
                    ]
                    if nome_periodo in ["INTEGRAL", "PARCIAL"]:
                        tabelas[indice_atual]["faixas_etarias"] += [
                            faixa for faixa in dict_categorias_campos[categoria]
                        ]
                        tabelas[indice_atual]["len_categorias"] += [
                            (len(dict_categorias_campos[categoria]) * 2) + 1
                        ]
                    else:
                        tabelas[indice_atual]["len_categorias"] += [
                            len(dict_categorias_campos[categoria])
                        ]
                    get_categorias_dos_periodos(
                        nome_periodo,
                        tabelas,
                        indice_atual,
                        categoria,
                        dict_categorias_campos,
                    )
            else:
                adiciona_valores_header(
                    nome_periodo,
                    tabelas,
                    dict_categorias_campos,
                    indice_atual,
                    categoria,
                    "CEMEI",
                )
                get_categorias_dos_periodos(
                    nome_periodo,
                    tabelas,
                    indice_atual,
                    categoria,
                    dict_categorias_campos,
                )
            adiciona_campo_total_faixa_etaria(tabelas, nome_periodo, indice_atual)

    get_tamanho_colunas_periodos(tabelas, ORDEM_PERIODOS_GRUPOS_CEMEI, "CEMEI")
    return tabelas


def adiciona_valores_header(
    nome_periodo,
    tabelas,
    dict_categorias_campos,
    indice_atual,
    categoria,
    tipo_unidade=None,
):
    if nome_periodo not in tabelas[indice_atual]["periodos"]:
        tabelas[indice_atual]["periodos"] += [nome_periodo]
    if nome_periodo in ["INTEGRAL", "PARCIAL"] and tipo_unidade == "CEMEI":
        tabelas[indice_atual]["faixas_etarias"] += [
            faixa for faixa in dict_categorias_campos[categoria]
        ]
        tabelas[indice_atual]["len_categorias"] += [
            (len(dict_categorias_campos[categoria]) * 2) + 1
        ]
    else:
        tabelas[indice_atual]["len_categorias"] += [
            len(dict_categorias_campos[categoria])
        ]
    tabelas[indice_atual]["categorias"] += [categoria]
    tabelas[indice_atual]["nomes_campos"] += [
        campo for campo in ORDEM_CAMPOS if campo in dict_categorias_campos[categoria]
    ]


def adiciona_campo_total_faixa_etaria(tabelas, nome_periodo, indice_atual):
    if nome_periodo in ["INTEGRAL", "PARCIAL"]:
        tabelas[indice_atual]["faixas_etarias"].append("total")


def get_medicoes_ordenadas(solicitacao, ordem_campos):
    return sorted(
        solicitacao.medicoes.all(),
        key=lambda k: ordem_campos[k.nome_periodo_grupo],
    )


def build_dict_relacao_categorias_e_campos_cemei(medicao):
    if medicao.periodo_escolar and medicao.periodo_escolar.nome in [
        "INTEGRAL",
        "PARCIAL",
    ]:
        dict_categorias_campos = build_dict_relacao_categorias_e_campos_cei(medicao)
    else:
        dict_categorias_campos = build_dict_relacao_categorias_e_campos(medicao)
    return dict_categorias_campos


def cria_tabela_vazia_cemei():
    return {
        "periodos": [],
        "categorias": [],
        "nomes_campos": [],
        "faixas_etarias": [],
        "len_periodos": [],
        "len_categorias": [],
        "valores_campos": [],
        "ordem_periodos_grupos": [],
        "dias_letivos": [],
        "categorias_dos_periodos": {},
    }


def popula_campo_matriculados(
    dia,
    campo,
    indice_campo,
    valores_dia,
    logs_alunos_matriculados,
    categoria_corrente,
    periodo_corrente,
):
    if campo == "matriculados":
        try:
            periodo = get_nome_periodo(periodo_corrente)

            log = logs_alunos_matriculados.filter(
                periodo_escolar__nome=periodo, criado_em__day=dia
            ).first()
            if log:
                valores_dia += [log.quantidade_alunos]
            else:
                valores_dia += ["0"]
        except LogAlunosMatriculadosPeriodoEscola.DoesNotExist:
            valores_dia += ["0"]


def get_nome_periodo(periodo_corrente):
    if periodo_corrente in [
        "Infantil INTEGRAL",
        "Infantil MANHA",
        "Infantil TARDE",
    ]:
        periodo = periodo_corrente.split(" ")[1]
    else:
        periodo = periodo_corrente.split(" - ")[0]

    return periodo


def popula_campo_matriculados_cei(
    solicitacao, tabela, faixa_id, dia, indice_periodo, categoria_corrente, valores_dia
):
    periodo = tabela["periodos"][indice_periodo]
    medicoes = solicitacao.medicoes.all()
    medicao = medicoes.get(periodo_escolar__nome=periodo, grupo=None)
    try:
        valores_dia += [
            medicao.valores_medicao.get(
                dia=f"{dia:02d}",
                categoria_medicao__nome=categoria_corrente,
                faixa_etaria=faixa_id,
                nome_campo="matriculados",
            ).valor
        ]
    except ValorMedicao.DoesNotExist:
        valores_dia += ["0"]
    except ValorMedicao.MultipleObjectsReturned:
        valor_para_nao_excluir = (
            medicao.valores_medicao.filter(
                dia=f"{dia:02d}",
                categoria_medicao__nome=categoria_corrente,
                faixa_etaria=faixa_id,
                nome_campo="matriculados",
            )
            .order_by("-valor")
            .first()
        )

        medicao.valores_medicao.filter(
            dia=f"{dia:02d}",
            categoria_medicao__nome=categoria_corrente,
            faixa_etaria=faixa_id,
            nome_campo="matriculados",
        ).exclude(uuid=valor_para_nao_excluir.uuid).delete()
        valores_dia += [valor_para_nao_excluir.valor]


def get_nomes_classificacoes(categoria_corrente):
    if "ENTERAL" in categoria_corrente:
        classificacoes_nomes = [
            "Tipo A RESTRIÇÃO DE AMINOÁCIDOS",
            "Tipo A ENTERAL",
        ]
    elif "TIPO B" in categoria_corrente:
        classificacoes_nomes = [
            "Tipo B",
        ]
    else:
        classificacoes_nomes = ["Tipo A"]
    return classificacoes_nomes


def popula_campo_aprovadas(
    solicitacao,
    dia,
    campo,
    categoria_corrente,
    valores_dia,
    logs_dietas,
    periodo_corrente,
):
    if campo == "aprovadas":
        try:
            periodo = get_nome_periodo(periodo_corrente)
            classificacoes_nomes = get_nomes_classificacoes(categoria_corrente)
            logs_dietas = logs_dietas.filter(
                data__day=dia,
                data__month=solicitacao.mes,
                data__year=solicitacao.ano,
                classificacao__nome__in=classificacoes_nomes,
            )
            if periodo in ["Programas e Projetos", "ETEC"]:
                logs_dietas = logs_dietas.filter(periodo_escolar=None)
            else:
                logs_dietas = logs_dietas.filter(periodo_escolar__nome=periodo)
            quantidade = logs_dietas.aggregate(Sum("quantidade")).get("quantidade__sum")
            valores_dia += [quantidade or "0"]
        except LogQuantidadeDietasAutorizadas.DoesNotExist:
            valores_dia += ["0"]


def popula_campo_aprovadas_cei(
    solicitacao,
    faixa_id,
    dia,
    categoria_corrente,
    valores_dia,
    logs_dietas,
    tabela,
    indice_periodo,
):
    try:
        periodo = tabela["periodos"][indice_periodo]
        if "TIPO A" in categoria_corrente.upper():
            nomes_classificacoes = [
                "Tipo A",
                "Tipo A RESTRIÇÃO DE AMINOÁCIDOS",
                "Tipo A ENTERAL",
            ]
        else:
            nomes_classificacoes = ["Tipo B"]
        quantidade = (
            logs_dietas.filter(
                data__day=dia,
                data__month=solicitacao.mes,
                data__year=solicitacao.ano,
                faixa_etaria=faixa_id,
                periodo_escolar__nome=periodo,
                classificacao__nome__in=nomes_classificacoes,
            )
            .aggregate(Sum("quantidade"))
            .get("quantidade__sum")
        )
        valores_dia += [quantidade or "0"]
    except LogQuantidadeDietasAutorizadasCEI.DoesNotExist:
        valores_dia += ["0"]


def popula_campos_preenchidos_pela_escola(
    solicitacao, tabela, campo, dia, indice_periodo, categoria_corrente, valores_dia
):
    try:
        periodo_corrente = tabela["periodos"][indice_periodo]
        periodo = (
            get_nome_periodo(periodo_corrente)
            if solicitacao.escola.eh_emebs
            else periodo_corrente
        )
        tipo_turma = (
            periodo_corrente.split(" - ")[1] if solicitacao.escola.eh_emebs else "N/A"
        )

        medicoes = solicitacao.medicoes.all()
        if periodo in [
            "ETEC",
            "Solicitações de Alimentação",
            "Programas e Projetos",
            "Infantil INTEGRAL",
            "Infantil MANHA",
            "Infantil TARDE",
        ]:
            medicao = medicoes.get(grupo__nome=periodo)
        else:
            medicao = medicoes.get(periodo_escolar__nome=periodo, grupo=None)

        valores_dia += [
            medicao.valores_medicao.filter(
                dia=f"{dia:02d}",
                categoria_medicao__nome=categoria_corrente,
                nome_campo=campo,
                infantil_ou_fundamental=tipo_turma,
            )
            .first()
            .valor
        ]
    except (ValorMedicao.DoesNotExist, AttributeError):
        valores_dia += ["0"]


def popula_campos_preenchidos_pela_escola_cei(
    solicitacao, tabela, faixa_id, dia, indice_periodo, categoria_corrente, valores_dia
):
    try:
        periodo = tabela["periodos"][indice_periodo]
        medicoes = solicitacao.medicoes.all()
        medicao = medicoes.get(periodo_escolar__nome=periodo, grupo=None)
        quantidade = (
            medicao.valores_medicao.filter(
                dia=f"{dia:02d}",
                categoria_medicao__nome=categoria_corrente,
                faixa_etaria=faixa_id,
                nome_campo="frequencia",
            )
            .first()
            .valor
        )
        valores_dia += [quantidade]
    except (ValorMedicao.DoesNotExist, AttributeError):
        valores_dia += ["0"]


def contador_frequencia_diaria_cei(
    solicitacao, tabela, dia, indice_periodo, categoria_corrente
):
    try:
        periodo = tabela["periodos"][indice_periodo]
        medicoes = solicitacao.medicoes.all()
        medicao = medicoes.get(periodo_escolar__nome=periodo, grupo=None)
        queryset = medicao.valores_medicao.filter(
            dia=f"{int(dia):02d}",
            categoria_medicao__nome=categoria_corrente,
            nome_campo="frequencia",
        )

        total = queryset.annotate(
            valor_numerico=Cast("valor", IntegerField())
        ).aggregate(soma_total=Sum("valor_numerico"))["soma_total"]

    except ValorMedicao.DoesNotExist:
        total = 0
    return total if total else 0


def contador_frequencia_total_cei(
    solicitacao, tabela, faixa_id, indice_periodo, categoria_corrente
):
    try:
        periodo = tabela["periodos"][indice_periodo]
        medicoes = solicitacao.medicoes.all()
        medicao = medicoes.get(periodo_escolar__nome=periodo, grupo=None)
        queryset = medicao.valores_medicao.filter(
            faixa_etaria=faixa_id,
            categoria_medicao__nome=categoria_corrente,
            nome_campo="frequencia",
        )

        total = queryset.annotate(
            valor_numerico=Cast("valor", IntegerField())
        ).aggregate(soma_total=Sum("valor_numerico"))["soma_total"]

    except ValorMedicao.DoesNotExist:
        total = 0
    return total if total else 0


def popula_campo_consumido_solicitacoes_alimentacao(
    solicitacao, dia, campo, categoria_corrente, valores_dia
):
    if campo == "consumido":
        try:
            medicao = solicitacao.medicoes.get(grupo__nome__icontains="Solicitações")
            nome_campo = (
                "lanche_emergencial"
                if categoria_corrente == "LANCHE EMERGENCIAL"
                else "kit_lanche"
            )
            valores_dia += [
                medicao.valores_medicao.get(
                    dia=f"{dia:02d}", nome_campo=nome_campo
                ).valor
            ]
        except Exception:
            valores_dia += ["0"]


def get_indice(indexes_refeicao, indice_periodo):
    if len(indexes_refeicao) > 1:
        index_refeicao = indexes_refeicao[indice_periodo]
    else:
        index_refeicao = indexes_refeicao[0]
    return index_refeicao


def get_numero_campos(tabela, periodo_corrente, categoria_corrente):
    indice_periodo = tabela["periodos"].index(periodo_corrente)

    indices_categoria = [
        i
        for i, categoria in enumerate(tabela["categorias"])
        if categoria == categoria_corrente
    ]
    indice_categoria = get_indice(indices_categoria, indice_periodo)

    len_categorias = tabela["len_categorias"]
    len_categoria_corrente = len_categorias[indice_categoria]

    soma_periodos_anteriores = reduce(
        lambda x, y: x + y, len_categorias[:indice_categoria], 0
    )

    indice_inicial = (
        soma_periodos_anteriores
        if (
            indice_categoria
            and "faixas_etarias" in tabela
            and len(tabela["faixas_etarias"]) == 0
        )
        else 0
    )
    indice_final = len_categoria_corrente + soma_periodos_anteriores

    return indice_inicial, indice_final


def popula_campo_total_refeicoes_pagamento(
    solicitacao,
    tabela,
    campo,
    categoria_corrente,
    valores_dia,
    indice_periodo,
    tabelas,
    indice_tabela,
):
    if campo == "total_refeicoes_pagamento":
        try:
            periodo_corrente = tabela["periodos"][indice_periodo]
            indice_inicial, indice_final = get_numero_campos(
                tabela, periodo_corrente, categoria_corrente
            )
            dia = valores_dia[0]
            campos = tabela["nomes_campos"][indice_inicial:indice_final]
            valores = valores_dia[indice_inicial + 1 : indice_final + 1]
            tabela_anterior = tabelas[indice_tabela - 1]
            periodos_tabela_anterior = tabela_anterior["periodos"]
            campos_tabela_anterior = []
            valores_tabela_anterior = []
            if (
                indice_tabela > 0
                and periodo_corrente in periodos_tabela_anterior
                and categoria_corrente in tabela_anterior["categorias"]
            ):
                (
                    indice_inicial_tabela_anterior,
                    indice_final_tabela_anterior,
                ) = get_numero_campos(
                    tabela_anterior, periodo_corrente, categoria_corrente
                )
                campos_tabela_anterior = tabela_anterior["nomes_campos"][
                    indice_inicial_tabela_anterior:indice_final_tabela_anterior
                ]
                valores_tabela_anterior = tabela_anterior["valores_campos"][
                    int(dia - 1)
                ][indice_inicial_tabela_anterior + 1 : indice_final_tabela_anterior + 1]
            valor_refeicao = get_valor_campo(
                campos,
                campos_tabela_anterior,
                indice_periodo,
                tabela,
                tabela_anterior,
                valores,
                valores_tabela_anterior,
                "refeicao",
            )
            valor_repeticao_refeicao = get_valor_campo(
                campos,
                campos_tabela_anterior,
                indice_periodo,
                tabela,
                tabela_anterior,
                valores,
                valores_tabela_anterior,
                "repeticao_refeicao",
            )
            valor_segunda_refeicao = get_valor_campo(
                campos,
                campos_tabela_anterior,
                indice_periodo,
                tabela,
                tabela_anterior,
                valores,
                valores_tabela_anterior,
                "2_refeicao_1_oferta",
            )
            valor_repeticao_segunda_refeicao = get_valor_campo(
                campos,
                campos_tabela_anterior,
                indice_periodo,
                tabela,
                tabela_anterior,
                valores,
                valores_tabela_anterior,
                "repeticao_2_refeicao",
            )
            valor_matriculados = get_valor_campo(
                campos,
                campos_tabela_anterior,
                indice_periodo,
                tabela,
                tabela_anterior,
                valores,
                valores_tabela_anterior,
                "matriculados",
            )
            valor_numero_de_alunos = get_valor_campo(
                campos,
                campos_tabela_anterior,
                indice_periodo,
                tabela,
                tabela_anterior,
                valores,
                valores_tabela_anterior,
                "numero_de_alunos",
            )
            eh_emebs_infantil = (
                solicitacao.escola.eh_emebs
                and tabela["periodos"][indice_periodo].split(" - ")[1] == "INFANTIL"
            )
            if (
                solicitacao.escola.eh_emei
                or solicitacao.escola.eh_cemei
                or eh_emebs_infantil
            ):
                valores_dia = get_valor_total_emei_cemei(
                    solicitacao,
                    valores_dia,
                    valor_refeicao,
                    valor_repeticao_refeicao,
                    valor_segunda_refeicao,
                    valor_repeticao_segunda_refeicao,
                    valor_matriculados,
                    valor_numero_de_alunos,
                )
            else:
                valor_comparativo = (
                    valor_matriculados
                    if int(valor_matriculados) > 0
                    else valor_numero_de_alunos
                )
                total_refeicao = int(valor_refeicao) + int(valor_repeticao_refeicao)
                total_refeicao = min(int(total_refeicao), int(valor_comparativo))

                total_refeicao_2a_oferta = int(valor_segunda_refeicao) + int(
                    valor_repeticao_segunda_refeicao
                )
                total_refeicao_2a_oferta = min(
                    int(total_refeicao_2a_oferta), int(valor_comparativo)
                )
                valores_dia += [total_refeicao + total_refeicao_2a_oferta]
        except Exception:
            valores_dia += ["0"]


def get_valor_total_emei_cemei(
    solicitacao,
    valores_dia,
    valor_refeicao,
    valor_repeticao_refeicao,
    valor_segunda_refeicao,
    valor_repeticao_segunda_refeicao,
    valor_matriculados,
    valor_numero_de_alunos,
):
    editais = Edital.objects.filter(uuid__in=solicitacao.escola.editais)
    tem_edital_imr = editais.filter(eh_imr=True).exists()

    if tem_edital_imr and (solicitacao.escola.eh_emei or solicitacao.escola.eh_cemei):
        valor_comparativo = (
            valor_matriculados
            if int(valor_matriculados) > 0
            else valor_numero_de_alunos
        )

        total_refeicao = int(valor_refeicao) + int(valor_repeticao_refeicao)
        total_refeicao = min(int(total_refeicao), int(valor_comparativo))

        total_refeicao_2a_oferta = int(valor_segunda_refeicao) + int(
            valor_repeticao_segunda_refeicao
        )
        total_refeicao_2a_oferta = min(
            int(total_refeicao_2a_oferta), int(valor_comparativo)
        )

        valores_dia += [total_refeicao + total_refeicao_2a_oferta]
    else:
        valores_dia += [int(valor_refeicao) + int(valor_segunda_refeicao)]
    return valores_dia


def get_valor_campo(
    campos,
    campos_tabela_anterior,
    indice_periodo,
    tabela,
    tabela_anterior,
    valores_dia,
    valores_tabela_anterior,
    nome_campo,
):
    if nome_campo not in campos and nome_campo in campos_tabela_anterior:
        indexes_campo = [
            i for i, campo in enumerate(campos_tabela_anterior) if campo == nome_campo
        ]
        index_campo = get_indice(indexes_campo, indice_periodo)
        len_faixas = 0

        if "faixas_etarias" in tabela_anterior:
            faixas_etarias = tabela_anterior["faixas_etarias"]
            len_faixas = (len(faixas_etarias) * 2) - 1 if faixas_etarias else 0

        valor_campo = (
            valores_tabela_anterior[index_campo + len_faixas]
            if nome_campo in campos_tabela_anterior
            and len(tabela_anterior["valores_campos"])
            else 0
        )
    elif nome_campo in campos:
        indexes_campo = [i for i, campo in enumerate(campos) if campo == nome_campo]
        index_campo = get_indice(indexes_campo, indice_periodo)
        len_faixas = 0

        if "faixas_etarias" in tabela:
            faixas_etarias = tabela["faixas_etarias"]
            len_faixas = (len(faixas_etarias) * 2) - 1 if faixas_etarias else 0

        valor_campo = (
            valores_dia[index_campo + len_faixas] if nome_campo in campos else 0
        )

    else:
        valor_campo = 0
    return valor_campo


def popula_campo_total_sobremesas_pagamento(
    solicitacao,
    tabela,
    campo,
    categoria_corrente,
    valores_dia,
    indice_periodo,
    tabelas,
    indice_tabela,
):
    if campo == "total_sobremesas_pagamento":
        try:
            periodo_corrente = tabela["periodos"][indice_periodo]
            indice_inicial, indice_final = get_numero_campos(
                tabela, periodo_corrente, categoria_corrente
            )
            dia = valores_dia[0]
            campos = tabela["nomes_campos"][indice_inicial:indice_final]
            valores = valores_dia[indice_inicial + 1 : indice_final + 1]
            tabela_anterior = tabelas[indice_tabela - 1]
            periodos_tabela_anterior = tabela_anterior["periodos"]
            campos_tabela_anterior = []
            valores_tabela_anterior = []
            if (
                indice_tabela > 0
                and periodo_corrente in periodos_tabela_anterior
                and categoria_corrente in tabela_anterior["categorias"]
            ):
                (
                    indice_inicial_tabela_anterior,
                    indice_final_tabela_anterior,
                ) = get_numero_campos(
                    tabela_anterior, periodo_corrente, categoria_corrente
                )
                campos_tabela_anterior = tabela_anterior["nomes_campos"][
                    indice_inicial_tabela_anterior:indice_final_tabela_anterior
                ]
                valores_tabela_anterior = tabela_anterior["valores_campos"][
                    int(dia - 1)
                ][indice_inicial_tabela_anterior + 1 : indice_final_tabela_anterior + 1]

            valor_sobremesa = get_valor_campo(
                campos,
                campos_tabela_anterior,
                indice_periodo,
                tabela,
                tabela_anterior,
                valores,
                valores_tabela_anterior,
                "sobremesa",
            )

            valor_repeticao_sobremesa = get_valor_campo(
                campos,
                campos_tabela_anterior,
                indice_periodo,
                tabela,
                tabela_anterior,
                valores,
                valores_tabela_anterior,
                "repeticao_sobremesa",
            )

            valor_segunda_sobremesa = get_valor_campo(
                campos,
                campos_tabela_anterior,
                indice_periodo,
                tabela,
                tabela_anterior,
                valores,
                valores_tabela_anterior,
                "2_sobremesa_1_oferta",
            )

            valor_repeticao_segunda_sobremesa = get_valor_campo(
                campos,
                campos_tabela_anterior,
                indice_periodo,
                tabela,
                tabela_anterior,
                valores,
                valores_tabela_anterior,
                "repeticao_2_sobremesa",
            )

            valor_matriculados = get_valor_campo(
                campos,
                campos_tabela_anterior,
                indice_periodo,
                tabela,
                tabela_anterior,
                valores,
                valores_tabela_anterior,
                "matriculados",
            )

            valor_numero_de_alunos = get_valor_campo(
                campos,
                campos_tabela_anterior,
                indice_periodo,
                tabela,
                tabela_anterior,
                valores,
                valores_tabela_anterior,
                "numero_de_alunos",
            )

            eh_emebs_infantil = (
                solicitacao.escola.eh_emebs
                and tabela["periodos"][indice_periodo].split(" - ")[1] == "INFANTIL"
            )

            if (
                solicitacao.escola.eh_emei
                or solicitacao.escola.eh_cemei
                or eh_emebs_infantil
            ):
                valores_dia = get_valor_total_emei_cemei(
                    solicitacao,
                    valores_dia,
                    valor_sobremesa,
                    valor_repeticao_sobremesa,
                    valor_segunda_sobremesa,
                    valor_repeticao_segunda_sobremesa,
                    valor_matriculados,
                    valor_numero_de_alunos,
                )
            else:
                valor_comparativo = (
                    valor_matriculados
                    if valor_matriculados > 0
                    else valor_numero_de_alunos
                )

                total_sobremesa = int(valor_sobremesa) + int(valor_repeticao_sobremesa)
                total_sobremesa = min(int(total_sobremesa), int(valor_comparativo))

                total_sobremesa_2a_oferta = int(valor_segunda_sobremesa) + int(
                    valor_repeticao_segunda_sobremesa
                )
                total_sobremesa_2a_oferta = min(
                    int(total_sobremesa_2a_oferta), int(valor_comparativo)
                )

                valores_dia += [total_sobremesa + total_sobremesa_2a_oferta]
        except Exception:
            valores_dia += ["0"]


def popula_solicitado_total_lanche_emergencial(
    categoria_corrente, alteracoes_lanche_emergencial, valores_dia, dia
):
    if categoria_corrente != "LANCHE EMERGENCIAL":
        return valores_dia

    total_lanche_emergencial = sum(
        alt["numero_alunos"]
        for alt in alteracoes_lanche_emergencial
        if alt["dia"] == f"{dia:02d}"
    )
    valores_dia += [total_lanche_emergencial]
    return valores_dia


def popula_solicitado_total_kit_lanche(
    categoria_corrente, kits_lanches, valores_dia, dia
):
    if categoria_corrente != "KIT LANCHE":
        return valores_dia

    total_kits = sum(
        [kit["numero_alunos"] for kit in kits_lanches if kit["dia"] == f"{dia:02d}"]
    )
    valores_dia += [total_kits]
    return valores_dia


def popula_campo_solicitado(
    solicitacao,
    tabela,
    campo,
    dia,
    categoria_corrente,
    valores_dia,
    alteracoes_lanche_emergencial,
    kits_lanches,
):
    if campo != "solicitado":
        return
    try:
        valores_dia = popula_solicitado_total_lanche_emergencial(
            categoria_corrente, alteracoes_lanche_emergencial, valores_dia, dia
        )
        valores_dia = popula_solicitado_total_kit_lanche(
            categoria_corrente, kits_lanches, valores_dia, dia
        )
    except Exception:
        valores_dia += ["0"]


def popula_campo_total(
    tabela, campo, valores_dia, indice_categoria, indice_campo, categoria_corrente
):
    if campo in ["matriculados", "numero_de_alunos", "frequencia", "aprovadas"]:
        valores_dia += ["-"]
    else:
        try:
            if indice_categoria == 0:
                values = [
                    valores[tabela["nomes_campos"].index(campo) + 1]
                    for valores in tabela["valores_campos"]
                ]
            else:
                i = 1
                indice_valor_campo = 0
                while i <= indice_categoria:
                    indice_valor_campo += tabela["len_categorias"][indice_categoria - i]
                    i += 1
                indice_valor_campo += indice_campo
                values = [
                    valores[indice_valor_campo + 1]
                    for valores in tabela["valores_campos"]
                ]
            valores_dia += [sum(int(x) for x in values)]
        except Exception:
            valores_dia += ["0"]


def popula_campo_total_cei(
    tabela, campo, valores_dia, indice_categoria, indice_campo, categoria_corrente
):
    if campo in ["matriculados", "numero_de_alunos", "frequencia", "aprovadas"]:
        valores_dia += ["-"]
    else:
        try:
            if indice_categoria == 0:
                values = [
                    valores[tabela["nomes_campos"].index(campo) + 1]
                    for valores in tabela["valores_campos"]
                ]
            else:
                i = 1
                indice_valor_campo = 0
                while i <= indice_categoria:
                    indice_valor_campo += tabela["len_categorias"][indice_categoria - i]
                    i += 1
                indice_valor_campo += indice_campo
                values = [
                    valores[indice_valor_campo + 1]
                    for valores in tabela["valores_campos"]
                ]
            valores_dia += [sum(int(x) for x in values)]
        except Exception:
            valores_dia += ["0"]


def get_eh_dia_letivo(dia, solicitacao):
    if not dia == "Total":
        try:
            eh_dia_letivo = DiaCalendario.objects.get(
                escola=solicitacao.escola,
                data__day=dia,
                data__month=solicitacao.mes,
                data__year=solicitacao.ano,
            ).dia_letivo
            return eh_dia_letivo
        except Exception:
            return False


def popula_campos(
    solicitacao,
    tabela,
    dia,
    indice_periodo,
    logs_alunos_matriculados,
    logs_dietas,
    alteracoes_lanche_emergencial,
    kits_lanches,
    tabelas,
    indice_tabela,
):
    valores_dia = [dia]
    eh_dia_letivo = get_eh_dia_letivo(dia, solicitacao)
    indice_campo = 0
    indice_categoria = 0
    popula_campos_nomes(
        solicitacao,
        tabela,
        dia,
        indice_campo,
        indice_categoria,
        indice_periodo,
        valores_dia,
        logs_alunos_matriculados,
        logs_dietas,
        tabelas,
        indice_tabela,
        alteracoes_lanche_emergencial,
        kits_lanches,
    )
    tabela["valores_campos"] += [valores_dia]
    tabela["dias_letivos"] += [eh_dia_letivo if not dia == "Total" else False]


def avalia_soma_total_com_dados_tabela_anterior(
    valores_para_soma,
    todas_faixas_anterior,
    index,
    index_primeira_coluna_total,
    tabela_anterior,
):
    if (
        todas_faixas_anterior
        and todas_faixas_anterior[-1] != "total"
        and index == index_primeira_coluna_total
    ):
        valores_campos_linha_total_tabela_anterior = tabela_anterior["valores_campos"][
            -1
        ]
        qtd_items_antes_total = todas_faixas_anterior[::-1].index("total")
        valores_tabela_anterior_para_somar = valores_campos_linha_total_tabela_anterior[
            -(qtd_items_antes_total * 2) :
        ]
        valores_para_soma += valores_tabela_anterior_para_somar
    return valores_para_soma


def popula_campos_cei(  # noqa C901
    solicitacao,
    tabela,
    dia,
    indice_periodo,
    logs_dietas,
    total_mensal_categoria,
    tabela_anterior,
):
    valores_dia = [dia]
    indice_campo = 0
    indice_categoria = 0
    indice_faixa = 0
    todas_faixas = []
    todas_faixas_anterior = []

    for categoria in tabela["categorias"]:
        todas_faixas += categoria["faixas_etarias"]
    if tabela_anterior:
        for categoria in tabela_anterior["categorias"]:
            todas_faixas_anterior += categoria["faixas_etarias"]

    categoria_corrente = tabela["categorias"][indice_categoria]["categoria"]
    faixas_etarias = tabela["categorias"][indice_categoria]["faixas_etarias"]
    len_faixas = len([item for item in faixas_etarias if "total" not in item])

    for index, faixa in enumerate(todas_faixas):
        if faixa == "total":
            indice_campo += 1
            if dia != "Total":
                total = contador_frequencia_diaria_cei(
                    solicitacao, tabela, dia, indice_periodo, categoria_corrente
                )
                total_mensal_categoria = total_mensal_categoria + total
                valores_dia += [str(total if total else 0)]
            else:
                indice_inicial = 0
                indice_final = 0
                for i, faixa in enumerate(todas_faixas[:index]):
                    if faixa != "total":
                        indice_final += 2
                    else:
                        indice_final += 1
                        indice_inicial = indice_final
                valores_dia_ = [valor for valor in valores_dia if valor != "Total"]
                valores_para_soma = valores_dia_[indice_inicial:indice_final]
                index_primeira_coluna_total = todas_faixas.index("total")
                valores_para_soma = avalia_soma_total_com_dados_tabela_anterior(
                    valores_para_soma,
                    todas_faixas_anterior,
                    index,
                    index_primeira_coluna_total,
                    tabela_anterior,
                )
                valores_dia += [
                    str(sum([int(v) for v in valores_para_soma if v.isdigit()]))
                ]
                total_mensal_categoria = 0

        else:
            if indice_faixa > len_faixas - 1:
                indice_faixa = 0
                indice_categoria += 1
                categoria_corrente = tabela["categorias"][indice_categoria]["categoria"]
                faixas_etarias = tabela["categorias"][indice_categoria][
                    "faixas_etarias"
                ]
                len_faixas = len(
                    [item for item in faixas_etarias if "total" not in item]
                )

                if indice_campo > tabela["len_periodos"][
                    indice_periodo
                ] - 1 and indice_periodo + 1 < len(tabela["periodos"]):
                    indice_periodo += 1
            popula_faixas_dias(
                dia,
                solicitacao,
                tabela,
                faixa,
                indice_periodo,
                categoria_corrente,
                valores_dia,
                logs_dietas,
            )
            indice_campo += 2
            indice_faixa += 1
    tabela["valores_campos"] += [valores_dia]
    return total_mensal_categoria


def get_alteracoes_lanche_emergencial(solicitacao):
    escola_uuid = solicitacao.escola.uuid
    mes = solicitacao.mes
    ano = solicitacao.ano
    query_set = SolicitacoesEscola.get_autorizados(escola_uuid=escola_uuid)
    query_set = query_set.filter(data_evento__month=mes, data_evento__year=ano)
    query_set = query_set.filter(data_evento__lt=datetime.date.today())
    query_set = query_set.filter(motivo__icontains="Emergencial")
    aux = []
    sem_uuid_repetido = []
    for resultado in query_set:
        if resultado.uuid not in aux:
            aux.append(resultado.uuid)
            sem_uuid_repetido.append(resultado)
    query_set = sem_uuid_repetido
    alteracoes_lanche_emergencial = []
    for alteracao_alimentacao in query_set:
        alteracao = alteracao_alimentacao.get_raw_model.objects.get(
            uuid=alteracao_alimentacao.uuid
        )
        if solicitacao.escola.eh_cemei:
            alteracoes_lanche_emergencial.append(
                {
                    "dia": f"{alteracao.data.day:02d}",
                    "numero_alunos": alteracao.numero_alunos,
                }
            )
        else:
            alteracoes_lanche_emergencial.append(
                {
                    "dia": f"{alteracao.data.day:02d}",
                    "numero_alunos": sum(
                        [
                            sub.qtd_alunos
                            for sub in alteracao.substituicoes_periodo_escolar.all()
                        ]
                    ),
                }
            )
    return alteracoes_lanche_emergencial


def get_kit_lanche(solicitacao):
    escola_uuid = solicitacao.escola.uuid
    mes = solicitacao.mes
    ano = solicitacao.ano
    query_set = SolicitacoesEscola.get_autorizados(escola_uuid=escola_uuid)
    query_set = query_set.filter(data_evento__month=mes, data_evento__year=ano)
    query_set = query_set.filter(data_evento__lt=datetime.date.today())
    query_set = query_set.filter(desc_doc__icontains="Kit Lanche")
    aux = []
    sem_uuid_repetido = []
    for resultado in query_set:
        if resultado.uuid not in aux:
            aux.append(resultado.uuid)
            sem_uuid_repetido.append(resultado)
    query_set = sem_uuid_repetido
    kits_lanches = []
    for kit_lanche in query_set:
        kit_lanche = kit_lanche.get_raw_model.objects.get(uuid=kit_lanche.uuid)
        solicitacao_kit_lanche = (
            kit_lanche
            if solicitacao.escola.eh_cemei
            else kit_lanche.solicitacao_kit_lanche
        )
        if kit_lanche:
            kits_lanches.append(
                {
                    "dia": f"{solicitacao_kit_lanche.data.day:02d}",
                    "numero_alunos": kit_lanche.quantidade_alimentacoes,
                }
            )

    return kits_lanches


def popula_tabelas(solicitacao, tabelas):
    dias_no_mes = range(
        1, monthrange(int(solicitacao.ano), int(solicitacao.mes))[1] + 1
    )
    logs_alunos_matriculados = LogAlunosMatriculadosPeriodoEscola.objects.filter(
        escola=solicitacao.escola,
        criado_em__month=solicitacao.mes,
        criado_em__year=solicitacao.ano,
        tipo_turma="REGULAR",
    )
    logs_dietas = LogQuantidadeDietasAutorizadas.objects.filter(
        escola=solicitacao.escola,
        data__month=solicitacao.mes,
        data__year=solicitacao.ano,
    )
    alteracoes_lanche_emergencial = get_alteracoes_lanche_emergencial(solicitacao)
    kits_lanches = get_kit_lanche(solicitacao)
    indice_periodo = 0
    quantidade_tabelas = range(0, len(tabelas))
    for indice_tabela in quantidade_tabelas:
        tabela = tabelas[indice_tabela]
        for dia in list(dias_no_mes) + ["Total"]:
            popula_campos(
                solicitacao,
                tabela,
                dia,
                indice_periodo,
                logs_alunos_matriculados,
                logs_dietas,
                alteracoes_lanche_emergencial,
                kits_lanches,
                tabelas,
                indice_tabela,
            )
    return tabelas


def popula_tabelas_emebs(solicitacao, tabelas):
    dias_no_mes = range(
        1, monthrange(int(solicitacao.ano), int(solicitacao.mes))[1] + 1
    )
    indice_periodo = 0
    quantidade_tabelas = range(0, len(tabelas))

    alteracoes_lanche_emergencial = get_alteracoes_lanche_emergencial(solicitacao)
    kits_lanches = get_kit_lanche(solicitacao)

    for indice_tabela in quantidade_tabelas:
        tabela = tabelas[indice_tabela]
        for dia in list(dias_no_mes) + ["Total"]:
            valores_dia = [dia]
            eh_dia_letivo = get_eh_dia_letivo(dia, solicitacao)
            indice_campo = 0
            indice_categoria = 0

            popula_valores_campos(
                solicitacao,
                tabela,
                dia,
                indice_campo,
                indice_categoria,
                indice_periodo,
                valores_dia,
                tabelas,
                indice_tabela,
                alteracoes_lanche_emergencial,
                kits_lanches,
            )
            tabela["valores_campos"] += [valores_dia]
            tabela["dias_letivos"] += [eh_dia_letivo if not dia == "Total" else False]
    return tabelas


def popula_valores_campos(
    solicitacao,
    tabela,
    dia,
    indice_campo,
    indice_categoria,
    indice_periodo,
    valores_dia,
    tabelas,
    indice_tabela,
    alteracoes_lanche_emergencial,
    kits_lanches,
):
    categoria_corrente = tabela["categorias"][indice_categoria]
    periodo_corrente = tabela["periodos"][indice_periodo]
    logs_alunos_matriculados = get_logs_emebs(
        solicitacao, "alunos_matriculados", periodo_corrente
    )
    logs_dietas = get_logs_emebs(solicitacao, "dietas", periodo_corrente)
    for campo in tabela["nomes_campos"]:
        if indice_campo > tabela["len_categorias"][indice_categoria] - 1:
            indice_campo = 0
            indice_categoria += 1
            categoria_corrente = tabela["categorias"][indice_categoria]
            periodo_corrente = tabela["periodos"][indice_periodo]

            logs_alunos_matriculados = get_logs_emebs(
                solicitacao, "alunos_matriculados", periodo_corrente
            )
            logs_dietas = get_logs_emebs(solicitacao, "dietas", periodo_corrente)

            if indice_categoria > len(
                tabela["categorias_dos_periodos"][periodo_corrente]
            ) - 1 and indice_periodo + 1 < len(tabela["periodos"]):
                indice_periodo += 1
                periodo_corrente = tabela["periodos"][indice_periodo]

                logs_alunos_matriculados = get_logs_emebs(
                    solicitacao, "alunos_matriculados", periodo_corrente
                )
                logs_dietas = get_logs_emebs(solicitacao, "dietas", periodo_corrente)
        if dia == "Total":
            popula_campo_total(
                tabela,
                campo,
                valores_dia,
                indice_categoria,
                indice_campo,
                categoria_corrente,
            )
        else:
            popula_campo_matriculados(
                dia,
                campo,
                indice_campo,
                valores_dia,
                logs_alunos_matriculados,
                categoria_corrente,
                periodo_corrente,
            )

            popula_campo_aprovadas(
                solicitacao,
                dia,
                campo,
                categoria_corrente,
                valores_dia,
                logs_dietas,
                periodo_corrente,
            )

            popula_campo_total_refeicoes_pagamento(
                solicitacao,
                tabela,
                campo,
                categoria_corrente,
                valores_dia,
                indice_periodo,
                tabelas,
                indice_tabela,
            )

            popula_campo_total_sobremesas_pagamento(
                solicitacao,
                tabela,
                campo,
                categoria_corrente,
                valores_dia,
                indice_periodo,
                tabelas,
                indice_tabela,
            )
            popula_campo_solicitado(
                solicitacao,
                tabela,
                campo,
                dia,
                categoria_corrente,
                valores_dia,
                alteracoes_lanche_emergencial,
                kits_lanches,
            )
            popula_campo_consumido_solicitacoes_alimentacao(
                solicitacao, dia, campo, categoria_corrente, valores_dia
            )

            if campo not in [
                "matriculados",
                "aprovadas",
                "total_refeicoes_pagamento",
                "total_sobremesas_pagamento",
                "solicitado",
                "consumido",
            ]:
                popula_campos_preenchidos_pela_escola(
                    solicitacao,
                    tabela,
                    campo,
                    dia,
                    indice_periodo,
                    categoria_corrente,
                    valores_dia,
                )
        indice_campo += 1


def get_logs_emebs(solicitacao, tipo_log, periodo_corrente):
    tipo_turma = periodo_corrente.split(" - ")[1]
    logs = None

    if tipo_log == "dietas":
        logs = LogQuantidadeDietasAutorizadas.objects.filter(
            escola=solicitacao.escola,
            data__month=solicitacao.mes,
            data__year=solicitacao.ano,
            infantil_ou_fundamental=tipo_turma,
        )
    elif tipo_log == "alunos_matriculados":
        logs = LogAlunosMatriculadosPeriodoEscola.objects.filter(
            escola=solicitacao.escola,
            criado_em__month=solicitacao.mes,
            criado_em__year=solicitacao.ano,
            tipo_turma="REGULAR",
            infantil_ou_fundamental=tipo_turma,
        )
    return logs


def get_lista_dias_letivos(solicitacao):
    _, num_dias = monthrange(int(solicitacao.ano), int(solicitacao.mes))
    return [get_eh_dia_letivo(dia, solicitacao) for dia in range(1, num_dias + 1)]


def popula_tabelas_cei(solicitacao, tabelas):
    dias_no_mes = range(
        1, monthrange(int(solicitacao.ano), int(solicitacao.mes))[1] + 1
    )
    logs_dietas = LogQuantidadeDietasAutorizadasCEI.objects.filter(
        escola=solicitacao.escola,
        data__month=solicitacao.mes,
        data__year=solicitacao.ano,
    )

    indice_periodo = 0
    quantidade_tabelas = range(0, len(tabelas))
    total_mensal_categoria = 0

    for indice_tabela in quantidade_tabelas:
        tabela = tabelas[indice_tabela]
        tabela_anterior = tabelas[indice_tabela - 1] if indice_tabela > 0 else None
        for dia in list(dias_no_mes) + ["Total"]:
            total_mensal_categoria = popula_campos_cei(
                solicitacao,
                tabela,
                dia,
                indice_periodo,
                logs_dietas,
                total_mensal_categoria,
                tabela_anterior,
            )

    dias_letivos = get_lista_dias_letivos(solicitacao)

    return tabelas, dias_letivos


def popula_tabelas_cemei(solicitacao, tabelas):
    dias_no_mes = range(
        1, monthrange(int(solicitacao.ano), int(solicitacao.mes))[1] + 1
    )
    logs_alunos_matriculados = LogAlunosMatriculadosPeriodoEscola.objects.filter(
        escola=solicitacao.escola,
        criado_em__month=solicitacao.mes,
        criado_em__year=solicitacao.ano,
        tipo_turma="REGULAR",
    )

    alteracoes_lanche_emergencial = get_alteracoes_lanche_emergencial(solicitacao)
    kits_lanches = get_kit_lanche(solicitacao)

    quantidade_tabelas = range(0, len(tabelas))

    for indice_tabela in quantidade_tabelas:
        tabela = tabelas[indice_tabela]
        for dia in list(dias_no_mes) + ["Total"]:
            popula_campos_cemei(
                solicitacao,
                tabela,
                dia,
                logs_alunos_matriculados,
                alteracoes_lanche_emergencial,
                kits_lanches,
                tabelas,
                indice_tabela,
            )
    return tabelas


def popula_campos_cemei(
    solicitacao,
    tabela,
    dia,
    logs_alunos_matriculados,
    alteracoes_lanche_emergencial,
    kits_lanches,
    tabelas,
    indice_tabela,
):
    valores_dia = [dia]
    eh_dia_letivo = get_eh_dia_letivo(dia, solicitacao)
    indice_campo = 0
    indice_categoria = 0
    indice_periodo = 0

    categoria_corrente = tabela["categorias"][indice_categoria]
    faixas_etarias = tabela["faixas_etarias"]
    periodo_corrente = tabela["periodos"][indice_periodo]

    modelo = (
        LogQuantidadeDietasAutorizadasCEI
        if periodo_corrente in ["INTEGRAL", "PARCIAL"]
        else LogQuantidadeDietasAutorizadas
    )

    logs_dietas = modelo.objects.filter(
        escola=solicitacao.escola,
        data__month=solicitacao.mes,
        data__year=solicitacao.ano,
    )

    if len(faixas_etarias):
        (
            indice_periodo,
            indice_categoria,
        ) = popula_campos_faixas_etarias(
            solicitacao,
            tabela,
            dia,
            indice_periodo,
            logs_dietas,
            categoria_corrente,
            indice_campo,
            faixas_etarias,
            valores_dia,
            indice_categoria,
        )

    if len(tabela["nomes_campos"]):
        popula_campos_nomes(
            solicitacao,
            tabela,
            dia,
            indice_campo,
            indice_categoria,
            indice_periodo,
            valores_dia,
            logs_alunos_matriculados,
            logs_dietas,
            tabelas,
            indice_tabela,
            alteracoes_lanche_emergencial,
            kits_lanches,
        )

    tabela["valores_campos"] += [valores_dia]
    tabela["dias_letivos"] += [eh_dia_letivo if not dia == "Total" else False]


def popula_campos_nomes(
    solicitacao,
    tabela,
    dia,
    indice_campo,
    indice_categoria,
    indice_periodo,
    valores_dia,
    logs_alunos_matriculados,
    logs_dietas,
    tabelas,
    indice_tabela,
    alteracoes_lanche_emergencial,
    kits_lanches,
):
    categoria_corrente = tabela["categorias"][indice_categoria]
    periodo_corrente = tabela["periodos"][indice_periodo]
    indice_nome_por_periodo = 0
    for campo in tabela["nomes_campos"]:
        if indice_campo > tabela["len_categorias"][indice_categoria] - 1:
            indice_campo = 0
            indice_categoria += 1
            categoria_corrente = tabela["categorias"][indice_categoria]
            if indice_nome_por_periodo > tabela["len_periodos"][indice_periodo] - 1:
                indice_periodo += 1
                periodo_corrente = tabela["periodos"][indice_periodo]
                indice_nome_por_periodo = 0
        if dia == "Total":
            popula_campo_total(
                tabela,
                campo,
                valores_dia,
                indice_categoria,
                indice_campo,
                categoria_corrente,
            )
        else:
            popula_campo_matriculados(
                dia,
                campo,
                indice_campo,
                valores_dia,
                logs_alunos_matriculados,
                categoria_corrente,
                periodo_corrente,
            )
            popula_campo_aprovadas(
                solicitacao,
                dia,
                campo,
                categoria_corrente,
                valores_dia,
                logs_dietas,
                periodo_corrente,
            )
            popula_campo_consumido_solicitacoes_alimentacao(
                solicitacao, dia, campo, categoria_corrente, valores_dia
            )
            popula_campo_total_refeicoes_pagamento(
                solicitacao,
                tabela,
                campo,
                categoria_corrente,
                valores_dia,
                indice_periodo,
                tabelas,
                indice_tabela,
            )
            popula_campo_total_sobremesas_pagamento(
                solicitacao,
                tabela,
                campo,
                categoria_corrente,
                valores_dia,
                indice_periodo,
                tabelas,
                indice_tabela,
            )
            popula_campo_solicitado(
                solicitacao,
                tabela,
                campo,
                dia,
                categoria_corrente,
                valores_dia,
                alteracoes_lanche_emergencial,
                kits_lanches,
            )
            if campo not in [
                "matriculados",
                "aprovadas",
                "total_refeicoes_pagamento",
                "total_sobremesas_pagamento",
                "solicitado",
                "consumido",
            ]:
                popula_campos_preenchidos_pela_escola(
                    solicitacao,
                    tabela,
                    campo,
                    dia,
                    indice_periodo,
                    categoria_corrente,
                    valores_dia,
                )
        indice_campo += 1
        indice_nome_por_periodo += 1


def popula_campos_faixas_etarias(
    solicitacao,
    tabela,
    dia,
    indice_periodo,
    logs_dietas,
    categoria_corrente,
    indice_campo,
    faixas_etarias,
    valores_dia,
    indice_categoria,
):
    indice_faixa = 0
    len_faixa = 0

    for faixa in faixas_etarias:
        len_faixa = get_indice_faixa(len_faixa, faixa, indice_faixa)

        if len_faixa > tabela["len_categorias"][indice_categoria] - 1:
            indice_faixa = 0
            len_faixa = 0
            indice_categoria += 1
            categoria_corrente = tabela["categorias"][indice_categoria]
            periodo_corrente = tabela["periodos"][indice_periodo]
            if indice_categoria > len(
                tabela["categorias_dos_periodos"][periodo_corrente]
            ) - 1 and indice_periodo + 1 < len(tabela["periodos"]):
                indice_periodo += 1
        if faixa == "total":
            if dia != "Total":
                valores_dia = popula_total_faixas(
                    tabela,
                    indice_periodo,
                    valores_dia,
                    solicitacao,
                    dia,
                    categoria_corrente,
                )

            else:
                popula_campo_total_cemei(
                    tabela, valores_dia, indice_categoria, indice_faixa
                )

        else:
            popula_faixas_dias(
                dia,
                solicitacao,
                tabela,
                faixa,
                indice_periodo,
                categoria_corrente,
                valores_dia,
                logs_dietas,
            )
        indice_faixa += 1
    indice_periodo += 1
    indice_categoria += 1
    return indice_periodo, indice_categoria


def popula_campo_total_cemei(tabela, valores_dia, indice_categoria, indice_faixa):
    try:
        indice_valor_campo = tabela["len_categorias"][indice_categoria]

        if indice_categoria == 0:
            values = [
                valores[indice_valor_campo] for valores in tabela["valores_campos"]
            ]
        else:
            i = 1
            while i <= indice_categoria:
                indice_valor_campo += tabela["len_categorias"][indice_categoria - i]
                i += 1
            values = [
                valores[indice_valor_campo] for valores in tabela["valores_campos"]
            ]
        valores_dia += [sum(int(x) for x in values)]
    except Exception:
        valores_dia += ["0"]


def get_indice_faixa(len_faixa, faixa, indice_faixa):
    if indice_faixa == 0:
        len_faixa = 0
    else:
        len_faixa += 2 if faixa != "total" else 1

    return len_faixa


def popula_total_faixas(
    tabela,
    indice_periodo,
    valores_dia,
    solicitacao,
    dia,
    categoria_corrente,
):
    total = contador_frequencia_diaria_cei(
        solicitacao, tabela, dia, indice_periodo, categoria_corrente
    )

    valores_dia += [str(total if total else 0)]

    return valores_dia


def popula_faixas_dias(
    dia,
    solicitacao,
    tabela,
    faixa,
    indice_periodo,
    categoria_corrente,
    valores_dia,
    logs_dietas,
):
    inicio, fim = string_to_faixa(faixa)
    faixa_id = FaixaEtaria.objects.get(inicio=inicio, fim=fim, ativo=True).id
    if dia == "Total":
        total = contador_frequencia_total_cei(
            solicitacao,
            tabela,
            faixa_id,
            indice_periodo,
            categoria_corrente,
        )
        valores_dia += ["-", str(total if total else 0)]
    else:
        if categoria_corrente == "ALIMENTAÇÃO":
            popula_campo_matriculados_cei(
                solicitacao,
                tabela,
                faixa_id,
                dia,
                indice_periodo,
                categoria_corrente,
                valores_dia,
            )

        else:
            popula_campo_aprovadas_cei(
                solicitacao,
                faixa_id,
                dia,
                categoria_corrente,
                valores_dia,
                logs_dietas,
                tabela,
                indice_periodo,
            )

        popula_campos_preenchidos_pela_escola_cei(
            solicitacao,
            tabela,
            faixa_id,
            dia,
            indice_periodo,
            categoria_corrente,
            valores_dia,
        )


def build_tabelas_relatorio_medicao(solicitacao):
    tabelas_com_headers = build_headers_tabelas(solicitacao)
    tabelas_populadas = popula_tabelas(solicitacao, tabelas_com_headers)
    return tabelas_populadas


def build_tabelas_relatorio_medicao_cei(solicitacao):
    tabelas_com_headers = build_headers_tabelas_cei(solicitacao)
    tabelas_populadas, dias_letivos = popula_tabelas_cei(
        solicitacao, tabelas_com_headers
    )

    return tabelas_populadas, dias_letivos


def build_tabelas_relatorio_medicao_cemei(solicitacao):
    tabelas_com_headers = build_headers_tabelas_cemei(solicitacao)
    tabelas_populadas = popula_tabelas_cemei(solicitacao, tabelas_com_headers)
    return tabelas_populadas


def build_tabelas_relatorio_medicao_emebs(solicitacao):
    tabelas_com_headers = build_headers_tabelas_emebs(solicitacao)
    tabelas_populadas = popula_tabelas_emebs(solicitacao, tabelas_com_headers)
    return tabelas_populadas


def build_lista_campos_observacoes(solicitacao, tipo_turma=None):
    observacoes = list(
        solicitacao.medicoes.filter(
            valores_medicao__nome_campo="observacoes",
            valores_medicao__infantil_ou_fundamental=(
                tipo_turma if tipo_turma is not None else "N/A"
            ),
        )
        .values_list(
            "valores_medicao__dia",
            "periodo_escolar__nome",
            "valores_medicao__categoria_medicao__nome",
            "valores_medicao__valor",
            "grupo__nome",
        )
        .order_by(
            "valores_medicao__dia",
            "grupo__nome",
            "periodo_escolar__nome",
            "valores_medicao__categoria_medicao__nome",
        )
    )
    return observacoes


def tratar_lanches_de_permissoes_lancamentos(total_por_nome_campo: dict):
    total_por_nome_campo["lanche"] = total_por_nome_campo.pop(
        "lanche", 0
    ) + total_por_nome_campo.pop("2_lanche_5h", 0)
    total_por_nome_campo["lanche_4h"] = total_por_nome_campo.pop(
        "lanche_4h", 0
    ) + total_por_nome_campo.pop("2_lanche_4h", 0)
    return total_por_nome_campo


def tratar_segunda_refeicao_permissoes_lancamentos(
    total_por_nome_campo: dict, eh_emei=False
):
    total_por_nome_campo["refeicao"] = total_por_nome_campo.pop(
        "refeicao", 0
    ) + total_por_nome_campo.pop("2_refeicao_1_oferta", 0)

    total_repeticao_2_refeicao = total_por_nome_campo.pop("repeticao_2_refeicao", 0)

    if not eh_emei:
        total_por_nome_campo["refeicao"] += total_repeticao_2_refeicao

    return total_por_nome_campo


def tratar_segunda_sobremesa_permissoes_lancamentos(
    total_por_nome_campo: dict, eh_emei=False
):
    total_por_nome_campo["sobremesa"] = total_por_nome_campo.pop(
        "sobremesa", 0
    ) + total_por_nome_campo.pop("2_sobremesa_1_oferta", 0)

    total_repeticao_2_sobremesa = total_por_nome_campo.pop("repeticao_2_sobremesa", 0)

    if not eh_emei:
        total_por_nome_campo["sobremesa"] += total_repeticao_2_sobremesa

    return total_por_nome_campo


def get_total_refeicao_tratado_cemei(total_por_nome_campo) -> int:
    total_por_nome_campo.pop("repeticao_refeicao", None)
    total_por_nome_campo.pop("repeticao_2_refeicao", None)
    return total_por_nome_campo.pop("refeicao", 0) + total_por_nome_campo.pop(
        "2_refeicao_1_oferta", 0
    )


def get_total_sobremesa_tratado_cemei(total_por_nome_campo) -> int:
    total_por_nome_campo.pop("repeticao_sobremesa", None)
    total_por_nome_campo.pop("repeticao_2_sobremesa", None)
    return total_por_nome_campo.pop("sobremesa", 0) + total_por_nome_campo.pop(
        "2_sobremesa_1_oferta", 0
    )


def get_total_lanche_tratado_cemei(total_por_nome_campo) -> int:
    return (
        total_por_nome_campo.pop("lanche", 0)
        + total_por_nome_campo.pop("2_lanche_4h", 0)
        + total_por_nome_campo.pop("2_lanche_5h", 0)
    )


def tratar_valores_cemei(total_por_nome_campo: dict):
    total_por_nome_campo["refeicao"] = get_total_refeicao_tratado_cemei(
        total_por_nome_campo
    )
    total_por_nome_campo["sobremesa"] = get_total_sobremesa_tratado_cemei(
        total_por_nome_campo
    )
    total_por_nome_campo["lanche"] = get_total_lanche_tratado_cemei(
        total_por_nome_campo
    )

    return total_por_nome_campo


def tratar_valores(escola, total_por_nome_campo: dict):
    _total_por_nome_campo = total_por_nome_campo.copy()

    if escola.eh_cemei:
        return tratar_valores_cemei(_total_por_nome_campo)

    _total_por_nome_campo = tratar_lanches_de_permissoes_lancamentos(
        _total_por_nome_campo
    )

    total_repeticao_refeicao = _total_por_nome_campo.pop("repeticao_refeicao", 0)
    total_repeticao_sobremesa = _total_por_nome_campo.pop("repeticao_sobremesa", 0)

    if escola.eh_emei:
        _total_por_nome_campo = tratar_segunda_refeicao_permissoes_lancamentos(
            _total_por_nome_campo, True
        )
        _total_por_nome_campo = tratar_segunda_sobremesa_permissoes_lancamentos(
            _total_por_nome_campo, True
        )
    else:
        _total_por_nome_campo["refeicao"] = (
            _total_por_nome_campo.pop("refeicao", 0) + total_repeticao_refeicao
        )
        _total_por_nome_campo["sobremesa"] = (
            _total_por_nome_campo.pop("sobremesa", 0) + total_repeticao_sobremesa
        )

        _total_por_nome_campo = tratar_segunda_refeicao_permissoes_lancamentos(
            _total_por_nome_campo
        )
        _total_por_nome_campo = tratar_segunda_sobremesa_permissoes_lancamentos(
            _total_por_nome_campo
        )

    return _total_por_nome_campo


def get_nome_campo(campo):
    campos = {
        "desjejum": "Desjejum",
        "colacao": "Colação",
        "refeicao_tarde": "Refeição da tarde",
        "almoco": "Almoco",
        "lanche": "Lanche",
        "lanche_4h": "Lanche 4h",
        "lanche_extra": "Lanche Extra",
        "refeicao": "Refeição",
        "repeticao_refeicao": "Repetição de Refeição",
        "lanche_emergencial": "Lanche Emergencial",
        "kit_lanche": "Kit Lanche",
        "sobremesa": "Sobremesa",
        "repeticao_sobremesa": "Repetição de Sobremesa",
    }
    return campos.get(campo, campo)


def somar_lanches(values, medicao, campo, tipo_turma=None):
    if campo == "lanche":
        values_lanche_e_2_lanche_5h = medicao.valores_medicao.filter(
            categoria_medicao__nome="ALIMENTAÇÃO",
            nome_campo__in=["lanche", "2_lanche_5h"],
            infantil_ou_fundamental=tipo_turma if tipo_turma is not None else "N/A",
        )
        values = values_lanche_e_2_lanche_5h
    if campo == "lanche_4h":
        values_lanche_4h_e_2_lanche_4h = medicao.valores_medicao.filter(
            categoria_medicao__nome="ALIMENTAÇÃO",
            nome_campo__in=["lanche_4h", "2_lanche_4h"],
            infantil_ou_fundamental=tipo_turma if tipo_turma is not None else "N/A",
        )
        values = values_lanche_4h_e_2_lanche_4h
    return values


def somar_valores_semelhantes(
    values,
    medicao,
    campo,
    solicitacao,
    dict_total_refeicoes,
    dict_total_sobremesas,
    tipo_turma=None,
):
    medicao_nome = get_medicao_nome(solicitacao, medicao, tipo_turma)

    if campo == "refeicao":
        if medicao_nome in dict_total_refeicoes.keys():
            values = dict_total_refeicoes[medicao_nome]
        else:
            values_repeticao_refeicao = medicao.valores_medicao.filter(
                categoria_medicao__nome="ALIMENTAÇÃO",
                nome_campo__in=[
                    "repeticao_refeicao",
                    "2_refeicao_1_oferta",
                    "repeticao_2_refeicao",
                ],
                infantil_ou_fundamental=(
                    tipo_turma if tipo_turma is not None else "N/A"
                ),
            )
            values = values | values_repeticao_refeicao
    if campo == "sobremesa":
        if medicao_nome in dict_total_sobremesas.keys():
            values = dict_total_sobremesas[medicao_nome]
        else:
            values_repeticao_sobremesa = medicao.valores_medicao.filter(
                categoria_medicao__nome="ALIMENTAÇÃO",
                nome_campo__in=[
                    "repeticao_sobremesa",
                    "2_sobremesa_1_oferta",
                    "repeticao_2_sobremesa",
                ],
                infantil_ou_fundamental=(
                    tipo_turma if tipo_turma is not None else "N/A"
                ),
            )
            values = values | values_repeticao_sobremesa
    values = somar_lanches(values, medicao, campo, tipo_turma)
    return values


def get_medicao_nome(solicitacao, medicao, tipo_turma):
    nome_periodo_escolar = (
        medicao.periodo_escolar.nome if medicao.periodo_escolar else None
    )
    nome_grupo = medicao.grupo.nome if medicao.grupo else None

    if solicitacao.escola.eh_emebs:
        medicao_nome = (
            f"{nome_periodo_escolar} - {tipo_turma}"
            if nome_periodo_escolar
            else f"{nome_grupo} - {tipo_turma}"
        )
    else:
        medicao_nome = nome_periodo_escolar or nome_grupo

    return medicao_nome


def get_somatorio_manha(
    campo, solicitacao, dict_total_refeicoes, dict_total_sobremesas, tipo_turma=None
):
    try:
        if solicitacao.escola.eh_cemei:
            medicao = solicitacao.medicoes.get(grupo__nome="Infantil MANHA")
        else:
            medicao = solicitacao.medicoes.get(
                periodo_escolar__nome="MANHA",
                grupo=None,
            )
        values = medicao.valores_medicao.filter(
            categoria_medicao__nome="ALIMENTAÇÃO",
            nome_campo=campo,
            infantil_ou_fundamental=tipo_turma if tipo_turma is not None else "N/A",
        )
        values = somar_valores_semelhantes(
            values,
            medicao,
            campo,
            solicitacao,
            dict_total_refeicoes,
            dict_total_sobremesas,
            tipo_turma,
        )
        somatorio_manha = (
            values if type(values) is int else sum([int(v.valor) for v in values])
        )
        if somatorio_manha == 0:
            somatorio_manha = 0
    except Exception:
        somatorio_manha = 0
    return somatorio_manha


def get_somatorio_tarde(
    campo, solicitacao, dict_total_refeicoes, dict_total_sobremesas, tipo_turma=None
):
    try:
        if solicitacao.escola.eh_cemei:
            medicao = solicitacao.medicoes.get(grupo__nome="Infantil TARDE")
        else:
            medicao = solicitacao.medicoes.get(
                periodo_escolar__nome="TARDE", grupo=None
            )
        values = medicao.valores_medicao.filter(
            categoria_medicao__nome="ALIMENTAÇÃO",
            nome_campo=campo,
            infantil_ou_fundamental=tipo_turma if tipo_turma is not None else "N/A",
        )
        values = somar_valores_semelhantes(
            values,
            medicao,
            campo,
            solicitacao,
            dict_total_refeicoes,
            dict_total_sobremesas,
            tipo_turma,
        )
        somatorio_tarde = (
            values if type(values) is int else sum([int(v.valor) for v in values])
        )
        if somatorio_tarde == 0:
            somatorio_tarde = 0
    except Exception:
        somatorio_tarde = 0
    return somatorio_tarde


def get_somatorio_integral(
    campo, solicitacao, dict_total_refeicoes, dict_total_sobremesas, tipo_turma=None
):
    try:
        if solicitacao.escola.eh_cemei:
            medicao = solicitacao.medicoes.get(grupo__nome="Infantil INTEGRAL")
        else:
            medicao = solicitacao.medicoes.get(
                periodo_escolar__nome="INTEGRAL", grupo=None
            )
        values = medicao.valores_medicao.filter(
            categoria_medicao__nome="ALIMENTAÇÃO",
            nome_campo=campo,
            infantil_ou_fundamental=tipo_turma if tipo_turma is not None else "N/A",
        )
        values = somar_valores_semelhantes(
            values,
            medicao,
            campo,
            solicitacao,
            dict_total_refeicoes,
            dict_total_sobremesas,
            tipo_turma,
        )
        somatorio_integral = (
            values if type(values) is int else sum([int(v.valor) for v in values])
        )
        if somatorio_integral == 0:
            somatorio_integral = 0
    except Exception:
        somatorio_integral = 0
    return somatorio_integral


def get_somatorio_programas_e_projetos(
    campo, solicitacao, dict_total_refeicoes, dict_total_sobremesas, tipo_turma=None
):
    try:
        medicoes = solicitacao.medicoes.filter(grupo__nome="Programas e Projetos")
        somatorio_programas_e_projetos = 0
        for medicao in medicoes:
            qs_values = medicao.valores_medicao.filter(
                categoria_medicao__nome="ALIMENTAÇÃO",
                nome_campo=campo,
                infantil_ou_fundamental=tipo_turma if tipo_turma is not None else "N/A",
            )
            qs_values = somar_valores_semelhantes(
                qs_values,
                medicao,
                campo,
                solicitacao,
                dict_total_refeicoes,
                dict_total_sobremesas,
                tipo_turma,
            )
            if type(qs_values) is int:
                somatorio_programas_e_projetos = qs_values
            else:
                somatorio_programas_e_projetos = sum([int(v.valor) for v in qs_values])
        if somatorio_programas_e_projetos == 0:
            somatorio_programas_e_projetos = 0
    except Exception:
        somatorio_programas_e_projetos = 0
    return somatorio_programas_e_projetos


def get_somatorio_solicitacoes_de_alimentacao(campo, solicitacao):
    try:
        medicao = solicitacao.medicoes.get(grupo__nome="Solicitações de Alimentação")
        values = medicao.valores_medicao.filter(nome_campo=campo)
        somatorio_solicitacoes_de_alimentacao = sum([int(v.valor) for v in values])
        if somatorio_solicitacoes_de_alimentacao == 0:
            somatorio_solicitacoes_de_alimentacao = 0
    except Exception:
        somatorio_solicitacoes_de_alimentacao = 0
    return somatorio_solicitacoes_de_alimentacao


def get_somatorio_total_tabela(valores_somatorios_tabela):
    valores_somatorio = []
    [valores_somatorio.append(v) for v in valores_somatorios_tabela if v != " - "]
    try:
        somatorio_total_tabela = sum([int(v) for v in valores_somatorio])
        if somatorio_total_tabela == 0:
            somatorio_total_tabela = 0
    except Exception:
        somatorio_total_tabela = 0
    return somatorio_total_tabela


def get_somatorio_eja_helper(
    periodo_nome,
    tipo_alimentacao,
    solicitacao,
    dict_total_refeicoes,
    dict_total_sobremesas,
    tipo_turma=None,
):
    try:
        medicao = solicitacao.medicoes.get(
            periodo_escolar__nome=periodo_nome, grupo=None
        )
        values = medicao.valores_medicao.filter(
            categoria_medicao__nome="ALIMENTAÇÃO",
            nome_campo=tipo_alimentacao,
            infantil_ou_fundamental=tipo_turma if tipo_turma is not None else "N/A",
        )
        values = somar_valores_semelhantes(
            values,
            medicao,
            tipo_alimentacao,
            solicitacao,
            dict_total_refeicoes,
            dict_total_sobremesas,
            tipo_turma,
        )
        somatorio = (
            values if type(values) is int else sum([int(v.valor) for v in values])
        )
        if somatorio == 0:
            somatorio = 0
    except Exception:
        somatorio = 0
    return somatorio


def get_somatorio_noite_eja(
    tipo_alimentacao,
    solicitacao,
    dict_total_refeicoes,
    dict_total_sobremesas,
    tipo_turma=None,
):
    return get_somatorio_eja_helper(
        "NOITE",
        tipo_alimentacao,
        solicitacao,
        dict_total_refeicoes,
        dict_total_sobremesas,
        tipo_turma,
    )


def get_somatorio_intermediario_eja(
    tipo_alimentacao,
    solicitacao,
    dict_total_refeicoes,
    dict_total_sobremesas,
    tipo_turma=None,
):
    return get_somatorio_eja_helper(
        "INTERMEDIARIO",
        tipo_alimentacao,
        solicitacao,
        dict_total_refeicoes,
        dict_total_sobremesas,
        tipo_turma,
    )


def get_somatorio_vespertino_eja(
    tipo_alimentacao,
    solicitacao,
    dict_total_refeicoes,
    dict_total_sobremesas,
    tipo_turma=None,
):
    return get_somatorio_eja_helper(
        "VESPERTINO",
        tipo_alimentacao,
        solicitacao,
        dict_total_refeicoes,
        dict_total_sobremesas,
        tipo_turma,
    )


def get_somatorio_etec(campo, solicitacao, dict_total_refeicoes, dict_total_sobremesas):
    try:
        medicao = solicitacao.medicoes.get(grupo__nome="ETEC")
        values = medicao.valores_medicao.filter(
            categoria_medicao__nome="ALIMENTAÇÃO", nome_campo=campo
        )
        values = somar_valores_semelhantes(
            values,
            medicao,
            campo,
            solicitacao,
            dict_total_refeicoes,
            dict_total_sobremesas,
        )
        somatorio_etec = (
            values if type(values) is int else sum([int(v.valor) for v in values])
        )
        if somatorio_etec == 0:
            somatorio_etec = 0
    except Exception:
        somatorio_etec = 0
    return somatorio_etec


def build_tabela_somatorio_header(
    medicao, primeira_tabela_header, segunda_tabela_header=[], categoria=None
):
    nome_periodo = (
        medicao.periodo_escolar.nome
        if not medicao.grupo
        else (
            f"{medicao.grupo.nome} - {medicao.periodo_escolar.nome}"
            if medicao.periodo_escolar
            else medicao.grupo.nome
        )
    )
    if categoria == "DIETA":
        if nome_periodo.upper() in ["ETEC", "SOLICITAÇÕES DE ALIMENTAÇÃO"]:
            pass
        elif nome_periodo.upper() == "NOITE":
            segunda_tabela_header.append(nome_periodo)
        else:
            primeira_tabela_header.append(nome_periodo)
    else:
        if nome_periodo.upper() in ["NOITE", "ETEC"]:
            segunda_tabela_header.append(nome_periodo)
        else:
            primeira_tabela_header.append(nome_periodo)

    return primeira_tabela_header, segunda_tabela_header


def build_tabela_somatorio_body(
    solicitacao, dict_total_refeicoes, dict_total_sobremesas, tipo_turma=None
):
    campos_tipos_alimentacao = []
    primeira_tabela_header = []
    segunda_tabela_header = []

    ORDEM_PERIODOS_CEMEI = {
        "Infantil INTEGRAL": 1,
        "Infantil MANHA": 2,
        "Infantil TARDE": 3,
        "Solicitações de Alimentação": 4,
    }

    ordem_periodos = (
        ORDEM_PERIODOS_CEMEI if solicitacao.escola.eh_cemei else ORDEM_PERIODOS_GRUPOS
    )

    medicoes = sorted(
        [
            medicao
            for medicao in solicitacao.medicoes.all()
            if medicao.nome_periodo_grupo in list(ordem_periodos)
        ],
        key=lambda k: ordem_periodos[k.nome_periodo_grupo],
    )

    for medicao in medicoes:
        primeira_tabela_header, segunda_tabela_header = build_tabela_somatorio_header(
            medicao, primeira_tabela_header, segunda_tabela_header, "ALIMENTAÇÃO"
        )
        queryset = (
            medicao.valores_medicao.filter(infantil_ou_fundamental=tipo_turma)
            if tipo_turma is not None
            else medicao.valores_medicao
        )

        campos = (
            queryset.exclude(
                nome_campo__in=[
                    "observacoes",
                    "dietas_autorizadas",
                    "frequencia",
                    "matriculados",
                    "numero_de_alunos",
                    "repeticao_refeicao",
                    "repeticao_sobremesa",
                    "2_lanche_4h",
                    "2_lanche_5h",
                    "2_refeicao_1_oferta",
                    "repeticao_2_refeicao",
                    "2_sobremesa_1_oferta",
                    "repeticao_2_sobremesa",
                ]
            )
            .values_list("nome_campo", flat=True)
            .distinct()
        )
        [
            campos_tipos_alimentacao.append(campo)
            for campo in campos
            if campo not in campos_tipos_alimentacao
        ]
    campos_tipos_alimentacao = [
        campo for campo in ORDEM_CAMPOS if campo in campos_tipos_alimentacao
    ]
    primeira_tabela_somatorio = {"header": primeira_tabela_header, "body": []}
    segunda_tabela_somatorio = {"header": segunda_tabela_header, "body": []}
    for tipo_alimentacao in campos_tipos_alimentacao:
        primeira_tabela_somatorio, segunda_tabela_somatorio = somatorio_periodo(
            tipo_alimentacao,
            dict_total_refeicoes,
            dict_total_sobremesas,
            solicitacao,
            primeira_tabela_somatorio,
            segunda_tabela_somatorio,
            tipo_turma,
        )
    primeira_tabela_somatorio, segunda_tabela_somatorio = adiciona_nomes_header(
        primeira_tabela_somatorio,
        segunda_tabela_somatorio,
        "ALIMENTAÇÃO",
        "TIPOS DE ALIMENTAÇÃO",
    )

    if solicitacao.escola.eh_cemei:
        if campos_tipos_alimentacao:
            campos_tipos_alimentacao.append("Total por Períodos")
            primeira_tabela_somatorio = total_por_periodos_cemei(
                primeira_tabela_somatorio
            )
            return primeira_tabela_somatorio

    return primeira_tabela_somatorio, segunda_tabela_somatorio


def adiciona_nomes_header(
    primeira_tabela_somatorio, segunda_tabela_somatorio, categoria, nome
):
    if primeira_tabela_somatorio["header"]:
        primeira_tabela_somatorio["header"].insert(0, nome)
        primeira_tabela_somatorio["header"].append("TOTAL")
    if segunda_tabela_somatorio["header"]:
        segunda_tabela_somatorio["header"].append("TOTAL")

    if categoria == "DIETA":
        if segunda_tabela_somatorio["header"]:
            segunda_tabela_somatorio["header"].insert(0, nome)

    return primeira_tabela_somatorio, segunda_tabela_somatorio


def get_somatorio_dietas(
    campo, solicitacao, tipo_dieta, periodo=None, grupo=None, tipo_turma=None
):
    # ajustar para filtrar periodo/grupo EJA
    try:
        medicao = solicitacao.medicoes.get(
            periodo_escolar__nome=periodo, grupo__nome=grupo
        )
        values = medicao.valores_medicao.filter(
            categoria_medicao__nome__icontains=tipo_dieta,
            nome_campo=campo,
            infantil_ou_fundamental=tipo_turma if tipo_turma is not None else "N/A",
        )
        somatorio_dietas = (
            values if type(values) is int else sum([int(v.valor) for v in values])
        )
        if somatorio_dietas == 0:
            somatorio_dietas = 0
    except Exception:
        somatorio_dietas = 0
    return somatorio_dietas


def build_tabela_somatorio_dietas_body(solicitacao, tipo_dieta, tipo_turma=None):
    campos_tipos_alimentacao = []
    primeira_tabela_header = []
    segunda_tabela_header = []

    ordem_periodos = ORDEM_PERIODOS_GRUPOS

    medicoes = sorted(
        [
            medicao
            for medicao in solicitacao.medicoes.all()
            if medicao.nome_periodo_grupo in list(ordem_periodos)
        ],
        key=lambda k: ordem_periodos[k.nome_periodo_grupo],
    )

    for medicao in medicoes:
        primeira_tabela_header, segunda_tabela_header = build_tabela_somatorio_header(
            medicao, primeira_tabela_header, segunda_tabela_header, "DIETA"
        )

        campos = (
            medicao.valores_medicao.exclude(
                nome_campo__in=[
                    "observacoes",
                    "dietas_autorizadas",
                    "frequencia",
                    "matriculados",
                    "numero_de_alunos",
                    "repeticao_refeicao",
                    "repeticao_sobremesa",
                    "2_lanche_4h",
                    "2_lanche_5h",
                    "2_refeicao_1_oferta",
                    "repeticao_2_refeicao",
                    "2_sobremesa_1_oferta",
                    "repeticao_2_sobremesa",
                ]
            )
            .filter(
                categoria_medicao__nome__icontains=tipo_dieta,
                infantil_ou_fundamental=tipo_turma if tipo_turma is not None else "N/A",
            )
            .values_list("nome_campo", flat=True)
            .distinct()
        )
        [
            campos_tipos_alimentacao.append(campo)
            for campo in campos
            if campo not in campos_tipos_alimentacao
        ]
    campos_tipos_alimentacao = [
        campo for campo in ORDEM_CAMPOS if campo in campos_tipos_alimentacao
    ]

    primeira_tabela_somatorio = {"header": primeira_tabela_header, "body": []}
    segunda_tabela_somatorio = {"header": segunda_tabela_header, "body": []}

    for tipo_alimentacao in campos_tipos_alimentacao:
        primeira_tabela_somatorio, segunda_tabela_somatorio = somatorio_periodo_dietas(
            tipo_alimentacao,
            solicitacao,
            primeira_tabela_somatorio,
            segunda_tabela_somatorio,
            tipo_dieta,
            tipo_turma,
        )

    primeira_tabela_somatorio, segunda_tabela_somatorio = adiciona_nomes_header(
        primeira_tabela_somatorio, segunda_tabela_somatorio, "DIETA", tipo_dieta
    )

    return primeira_tabela_somatorio, segunda_tabela_somatorio


def somatorio_periodo_dietas(
    tipo_alimentacao,
    solicitacao,
    primeira_tabela_somatorio,
    segunda_tabela_somatorio,
    tipo_dieta,
    tipo_turma=None,
):
    valores_somatorios_primeira_tabela = []

    for periodo in primeira_tabela_somatorio["header"]:
        if periodo == "Programas e Projetos":
            somatorio_dieta = get_somatorio_dietas(
                tipo_alimentacao,
                solicitacao,
                tipo_dieta,
                None,
                periodo,
                tipo_turma=tipo_turma,
            )
        else:
            somatorio_dieta = get_somatorio_dietas(
                tipo_alimentacao,
                solicitacao,
                tipo_dieta,
                periodo,
                tipo_turma=tipo_turma,
            )
        valores_somatorios_primeira_tabela.append(somatorio_dieta)

    somatorio_total_primeira_tabela_dietas = sum(
        somatorio if not isinstance(somatorio, str) else 0
        for somatorio in valores_somatorios_primeira_tabela
    )

    primeira_tabela_somatorio["body"].append(
        [
            get_nome_campo(tipo_alimentacao),
            *valores_somatorios_primeira_tabela,
            somatorio_total_primeira_tabela_dietas,
        ]
    )

    if segunda_tabela_somatorio:
        valores_somatorios_segunda_tabela = []

        for periodo in segunda_tabela_somatorio["header"]:
            somatorio_dieta = get_somatorio_dietas(
                tipo_alimentacao,
                solicitacao,
                tipo_dieta,
                periodo,
                tipo_turma=tipo_turma,
            )
            valores_somatorios_segunda_tabela.append(somatorio_dieta)
        somatorio_total_segunda_tabela_dietas = sum(
            somatorio if not isinstance(somatorio, str) else 0
            for somatorio in valores_somatorios_segunda_tabela
        )

        segunda_tabela_somatorio["body"].append(
            [
                get_nome_campo(tipo_alimentacao),
                *valores_somatorios_segunda_tabela,
                somatorio_total_segunda_tabela_dietas,
            ]
        )

    return primeira_tabela_somatorio, segunda_tabela_somatorio


def get_somatorio_periodos_params(
    periodo,
    tipo_alimentacao,
    solicitacao,
    dict_total_refeicoes,
    dict_total_sobremesas,
    tipo_turma,
):
    if periodo.upper() == "ETEC":
        return (
            tipo_alimentacao,
            solicitacao,
            dict_total_refeicoes,
            dict_total_sobremesas,
        )
    elif periodo.upper() == "SOLICITAÇÕES DE ALIMENTAÇÃO":
        return tipo_alimentacao, solicitacao
    else:
        return (
            tipo_alimentacao,
            solicitacao,
            dict_total_refeicoes,
            dict_total_sobremesas,
            tipo_turma,
        )


def somatorio_periodo(
    tipo_alimentacao,
    dict_total_refeicoes,
    dict_total_sobremesas,
    solicitacao,
    primeira_tabela_somatorio,
    segunda_tabela_somatorio=[],
    tipo_turma=None,
):
    periodo_func = {
        "MANHA": get_somatorio_manha,
        "TARDE": get_somatorio_tarde,
        "INTEGRAL": get_somatorio_integral,
        "Programas e Projetos": get_somatorio_programas_e_projetos,
        "Solicitações de Alimentação": get_somatorio_solicitacoes_de_alimentacao,
        "NOITE": get_somatorio_noite_eja,
        "INTERMEDIARIO": get_somatorio_intermediario_eja,
        "VESPERTINO": get_somatorio_vespertino_eja,
        "ETEC": get_somatorio_etec,
    }

    valores_somatorios_primeira_tabela = []

    for periodo in primeira_tabela_somatorio["header"]:
        nome_periodo = (
            get_nome_periodo(periodo) if solicitacao.escola.eh_cemei else periodo
        )

        params = get_somatorio_periodos_params(
            nome_periodo,
            tipo_alimentacao,
            solicitacao,
            dict_total_refeicoes,
            dict_total_sobremesas,
            tipo_turma,
        )
        somatorio = periodo_func[nome_periodo](*params)
        valores_somatorios_primeira_tabela.append(somatorio)

    somatorio_total_primeira_tabela = get_somatorio_total_tabela(
        valores_somatorios_primeira_tabela
    )

    primeira_tabela_somatorio["body"].append(
        [
            get_nome_campo(tipo_alimentacao),
            *valores_somatorios_primeira_tabela,
            somatorio_total_primeira_tabela,
        ]
    )

    if segunda_tabela_somatorio:
        valores_somatorios_segunda_tabela = []
        for nome_periodo in segunda_tabela_somatorio["header"]:
            params = get_somatorio_periodos_params(
                nome_periodo,
                tipo_alimentacao,
                solicitacao,
                dict_total_refeicoes,
                dict_total_sobremesas,
                tipo_turma,
            )
            somatorio = periodo_func[nome_periodo](*params)
            valores_somatorios_segunda_tabela.append(somatorio)

        somatorio_total_primeira_tabela = get_somatorio_total_tabela(
            valores_somatorios_segunda_tabela
        )

        segunda_tabela_somatorio["body"].append(
            [*valores_somatorios_segunda_tabela, somatorio_total_primeira_tabela]
        )

    return primeira_tabela_somatorio, segunda_tabela_somatorio


def total_por_periodos_cemei(
    tabela_somatorio,
):
    periodos = tabela_somatorio["header"][1:]
    valores_somatorios = []

    for indice, _ in enumerate(periodos):
        valores = [valores[indice + 1] for valores in tabela_somatorio["body"]]
        total = sum(int(valor) for valor in valores) or 0
        valores_somatorios.append(total)

    tabela_somatorio["body"].append(
        [
            "Total por Períodos",
            *valores_somatorios,
        ]
    )
    return tabela_somatorio


def build_valores_campos(solicitacao, tabela):  # noqa C901
    medicoes = solicitacao.medicoes.all()

    # Identificar todas as faixas etárias disponíveis
    faixas_etarias_ids = set()
    for medicao in medicoes:
        faixas_etarias_ids.update(
            medicao.valores_medicao.all()
            .values_list("faixa_etaria", flat=True)
            .distinct()
        )

    faixas_etarias = FaixaEtaria.objects.filter(id__in=faixas_etarias_ids, ativo=True)
    faixa_etaria_dict = {fe.id: str(fe) for fe in faixas_etarias}

    valores_campos = []
    categorias = tabela["categorias"]
    totais = ["total"] + [0] * len(categorias)

    for faixa_id, faixa_nome in faixa_etaria_dict.items():
        linha = [faixa_nome]

        for indice_periodo, periodo in enumerate(tabela["periodos"]):
            len_periodo_anterior = (
                tabela["len_periodos"][indice_periodo - 1] if indice_periodo >= 1 else 0
            )
            len_periodo_atual = tabela["len_periodos"][indice_periodo]
            indice_inicial = (
                indice_periodo if indice_periodo == 0 else len_periodo_anterior
            )
            indice_final = (
                len_periodo_atual
                if indice_periodo == 0
                else len_periodo_atual + len_periodo_anterior
            )
            categorias = tabela["categorias"][indice_inicial:indice_final]

            for idx_categoria, categoria in enumerate(categorias):
                if categoria == "total":
                    break
                try:
                    medicao = medicoes.get(periodo_escolar__nome=periodo, grupo=None)
                    valores_frequencia = medicao.valores_medicao.filter(
                        categoria_medicao__nome=categoria,
                        faixa_etaria=faixa_id,
                        nome_campo="frequencia",
                    ).values_list("valor", flat=True)

                    quantidade = sum(
                        int(valor) for valor in valores_frequencia if valor.isdigit()
                    )
                    linha.append(str(quantidade))

                    indice_total = len_periodo_anterior + idx_categoria + 1
                    totais[indice_total] += quantidade

                except ObjectDoesNotExist:
                    linha.append(0)

            total = sum(
                int(val) for val in linha[-(len_periodo_atual - 1) :] if val != 0
            )
            linha.append(str(total))

            totais[len_periodo_atual + len_periodo_anterior] += total

        valores_campos.append(linha)

    totais = [str(total) if isinstance(total, int) else total for total in totais]
    valores_campos.append(totais)

    return valores_campos


def build_tabela_somatorio_body_cei(solicitacao):
    ORDEM_PERIODOS_GRUPOS_CEI = {
        "INTEGRAL": 1,
        "PARCIAL": 2,
        "MANHA": 3,
        "TARDE": 4,
    }

    medicoes = sorted(
        [
            medicao
            for medicao in solicitacao.medicoes.all()
            if medicao.nome_periodo_grupo in list(ORDEM_PERIODOS_GRUPOS_CEI)
        ],
        key=lambda k: ORDEM_PERIODOS_GRUPOS_CEI[k.nome_periodo_grupo],
    )

    tabelas = []

    for medicao in medicoes:
        nome_periodo = (
            medicao.periodo_escolar.nome
            if not medicao.grupo
            else (
                f"{medicao.grupo.nome} - {medicao.periodo_escolar.nome}"
                if medicao.periodo_escolar
                else medicao.grupo.nome
            )
        )

        categorias = list(
            medicao.valores_medicao.values_list(
                "categoria_medicao__nome", flat=True
            ).distinct()
        )
        categorias.append("total")

        if not tabelas or len(tabelas[-1]["periodos"]) > 1:
            tabela = {
                "periodos": [nome_periodo],
                "categorias": categorias,
                "ordem_periodos_grupos": [ORDEM_PERIODOS_GRUPOS_CEI[nome_periodo]],
                "len_periodos": [len(categorias)],
                "valores_campos": [],
            }
            tabelas.append(tabela)
        else:
            tabelas[-1]["periodos"].append(nome_periodo)
            tabelas[-1]["categorias"] += categorias
            tabelas[-1]["ordem_periodos_grupos"].append(
                ORDEM_PERIODOS_GRUPOS_CEI[nome_periodo]
            )
            tabelas[-1]["len_periodos"].append(len(categorias))

    for tabela in tabelas:
        tabela["valores_campos"] = build_valores_campos(solicitacao, tabela)

    return tabelas


def atualizar_anexos_ocorrencia(anexos, solicitacao_medicao_inicial):
    for anexo in anexos:
        if ".pdf" in anexo["nome"]:
            arquivo = convert_base64_to_contentfile(anexo["base64"])
            solicitacao_medicao_inicial.ocorrencia.ultimo_arquivo = arquivo
            solicitacao_medicao_inicial.ocorrencia.nome_ultimo_arquivo = anexo.get(
                "nome"
            )
            solicitacao_medicao_inicial.ocorrencia.save()


def atualizar_status_ocorrencia(
    status_ocorrencia,
    status_correcao_solicitada_codae,
    solicitacao_medicao_inicial,
    request,
    justificativa,
):
    if status_ocorrencia == status_correcao_solicitada_codae:
        solicitacao_medicao_inicial.ocorrencia.ue_corrige_ocorrencia_para_codae(
            user=request.user, justificativa=justificativa
        )
    else:
        solicitacao_medicao_inicial.ocorrencia.ue_corrige(
            user=request.user, justificativa=justificativa
        )


def dict_informacoes_iniciais(user, acao):
    return {
        "usuario": {
            "uuid": str(user.uuid),
            "nome": user.nome,
            "username": user.username,
            "email": user.email,
        },
        "criado_em": datetime.datetime.today().strftime("%d/%m/%Y %H:%M:%S"),
        "acao": acao,
        "alteracoes": [],
    }


def get_medicoes_por_acao(solicitacao, acao):
    if acao == "MEDICAO_CORRECAO_SOLICITADA_CODAE":
        return solicitacao.medicoes.filter(status="MEDICAO_CORRECAO_SOLICITADA_CODAE")
    else:
        return solicitacao.medicoes.filter(status="MEDICAO_CORRECAO_SOLICITADA")


def criar_log_solicitar_correcao_periodos(user, solicitacao, acao):
    log = dict_informacoes_iniciais(user, acao)
    medicoes = get_medicoes_por_acao(solicitacao, acao)
    if not medicoes:
        return
    for medicao in medicoes:
        if medicao.periodo_escolar:
            periodo_nome = medicao.periodo_escolar.nome
        else:
            periodo_nome = medicao.grupo.nome

        alteracoes_dict = {
            "periodo_escolar": periodo_nome,
            "justificativa": medicao.logs.last().justificativa,
            "tabelas_lancamentos": [],
        }
        valores_medicao = medicao.valores_medicao.filter(
            habilitado_correcao=True
        ).order_by("semana")
        tabelas_lancamentos = (
            valores_medicao.order_by("categoria_medicao__nome")
            .values_list("categoria_medicao__nome", flat=True)
            .distinct()
        )

        for tabela in tabelas_lancamentos:
            valores_da_tabela = valores_medicao.filter(categoria_medicao__nome=tabela)
            semanas = valores_da_tabela.values_list("semana", flat=True).distinct()
            tabela_dict = {"categoria_medicao": tabela, "semanas": []}

            for semana in semanas:
                dias = valores_da_tabela.filter(semana=semana)
                dias = list(
                    dias.order_by("dia").values_list("dia", flat=True).distinct()
                )
                semana_dict = {"semana": semana, "dias": dias}
                tabela_dict["semanas"].append(semana_dict)
            alteracoes_dict["tabelas_lancamentos"].append(tabela_dict)
        log["alteracoes"].append(alteracoes_dict)
    return log


def log_anterior_para_busca(acao):
    if acao == "MEDICAO_APROVADA_PELA_DRE":
        return "MEDICAO_CORRECAO_SOLICITADA"
    return "MEDICAO_CORRECAO_SOLICITADA_CODAE"


def criar_log_aprovar_periodos_corrigidos(user, solicitacao, acao):
    if not solicitacao.historico:
        return
    log = dict_informacoes_iniciais(user, acao)
    historico = json.loads(solicitacao.historico)
    lista_logs = list(
        filter(lambda log: log["acao"] == log_anterior_para_busca(acao), historico)
    )
    for log_do_historico in lista_logs:
        for alteracao in log_do_historico["alteracoes"]:
            log["alteracoes"].append({"periodo_escolar": alteracao["periodo_escolar"]})
    return log


def encontrar_ou_criar_log_inicial(user, acao, historico):
    lista_logs = list(
        filter(lambda log: log["acao"] == acao and log == historico[-1], historico)
    )
    if not lista_logs:
        return dict_informacoes_iniciais(user, acao)
    else:
        return lista_logs[0]


def buscar_valores_medicao(
    medicao, dia, nome_campo, categoria_medicao, uuid_faixa_etaria
):
    filtro = {
        "medicao": medicao,
        "dia": dia,
        "nome_campo": nome_campo,
        "categoria_medicao": categoria_medicao,
    }
    if uuid_faixa_etaria:
        filtro["faixa_etaria__uuid"] = (
            uuid_faixa_etaria.uuid
            if isinstance(uuid_faixa_etaria, FaixaEtaria)
            else uuid_faixa_etaria
        )
    return ValorMedicao.objects.filter(**filtro)


def gerar_dicionario_e_buscar_valores_medicao(data, medicao):
    dicionario_alteracoes = {}

    for valor_atualizado in data:
        if not valor_atualizado:
            continue

        valor_medicao = buscar_valores_medicao(
            medicao,
            valor_atualizado.get("dia", ""),
            valor_atualizado.get("nome_campo", ""),
            valor_atualizado.get("categoria_medicao", ""),
            valor_atualizado.get("faixa_etaria", ""),
        )

        if (
            valor_medicao.exists()
            and valor_medicao.first().valor != valor_atualizado.get("valor")
        ):
            dicionario_alteracoes[str(valor_medicao.first().uuid)] = (
                valor_atualizado.get("valor")
            )

    valores_medicao = ValorMedicao.objects.filter(uuid__in=dicionario_alteracoes.keys())
    return dicionario_alteracoes, valores_medicao


def buscar_valores_medicao_por_categoria(valores_medicao, categoria):
    return valores_medicao.filter(categoria_medicao__nome=categoria)


def criar_dia_dict(
    valores_da_tabela, dia, medicao, dicionario_alteracoes, tabela, semana
):
    dia_dict = {"dia": dia, "campos": []}
    faixas_etarias = [
        faixa
        for faixa in valores_da_tabela.filter(dia=dia)
        .values_list("faixa_etaria", flat=True)
        .distinct()
        if faixa is not None
    ]

    chave = "faixa_etaria" if faixas_etarias else "nome_campo"
    valores_chave = (
        valores_da_tabela.filter(dia=dia).values_list(chave, flat=True).distinct()
    )

    for valor in valores_chave:
        filtro = {
            chave: valor,
            "semana": semana,
            "dia": dia,
            "categoria_medicao__nome": tabela,
            "medicao": medicao,
        }
        vm = valores_da_tabela.get(**filtro)

        campo = {
            "campo_nome": str(getattr(vm, chave)),
            "de": vm.valor,
            "para": dicionario_alteracoes.get(str(vm.uuid), vm.valor),
        }
        dia_dict["campos"].append(campo)

    return dia_dict


def criar_log_escola_corrigiu(
    medicao, valores_medicao, dicionario_alteracoes, log_inicial, historico, solicitacao
):
    periodo_nome = (
        medicao.periodo_escolar.nome if medicao.periodo_escolar else medicao.grupo.nome
    )
    alteracoes_dict = {"periodo_escolar": periodo_nome, "tabelas_lancamentos": []}

    for tabela in valores_medicao.values_list(
        "categoria_medicao__nome", flat=True
    ).distinct():
        valores_da_tabela = buscar_valores_medicao_por_categoria(
            valores_medicao, tabela
        )
        tabelas_dict = {
            "categoria_medicao": tabela,
            "semanas": [
                {
                    "semana": semana,
                    "dias": [
                        criar_dia_dict(
                            valores_da_tabela.filter(semana=semana),
                            dia,
                            medicao,
                            dicionario_alteracoes,
                            tabela,
                            semana,
                        )
                        for dia in valores_da_tabela.filter(semana=semana)
                        .values_list("dia", flat=True)
                        .distinct()
                    ],
                }
                for semana in valores_da_tabela.values_list(
                    "semana", flat=True
                ).distinct()
            ],
        }
        alteracoes_dict["tabelas_lancamentos"].append(tabelas_dict)

    log_inicial["alteracoes"].append(alteracoes_dict)
    historico.append(log_inicial)
    solicitacao.historico = json.dumps(historico)
    solicitacao.save()


def get_alteracoes_log(lista_alteracoes, log_inicial, periodo_nome):
    if not lista_alteracoes:
        log_inicial["alteracoes"].append(
            {"periodo_escolar": periodo_nome, "tabelas_lancamentos": []}
        )
        cp_alteracao_dict = log_inicial["alteracoes"][-1]
    else:
        cp_alteracao_dict = lista_alteracoes[0]
    alteracao_idx = log_inicial["alteracoes"].index(cp_alteracao_dict)
    return log_inicial, cp_alteracao_dict, alteracao_idx


def atualiza_ou_cria_tabela_lancamentos_log(
    valor_medicao, cp_alteracao_dict, log_inicial, alteracao_idx
):
    categoria_medicao = valor_medicao.categoria_medicao.nome
    lista = cp_alteracao_dict["tabelas_lancamentos"]
    lista_categorias = list(
        filter(lambda tabela: tabela["categoria_medicao"] == categoria_medicao, lista)
    )
    if not lista_categorias:
        log_inicial["alteracoes"][alteracao_idx]["tabelas_lancamentos"].append(
            {"categoria_medicao": categoria_medicao, "semanas": []}
        )
        cp_categorias_dict = log_inicial["alteracoes"][alteracao_idx][
            "tabelas_lancamentos"
        ][-1]
    else:
        cp_categorias_dict = lista_categorias[0]
    categoria_idx = cp_alteracao_dict["tabelas_lancamentos"].index(cp_categorias_dict)
    return log_inicial, cp_categorias_dict, categoria_idx


def atualiza_ou_cria_semanas_log(
    lista_semanas,
    log_inicial,
    alteracao_idx,
    categoria_idx,
    valor_medicao,
    cp_categorias_dict,
):
    if not lista_semanas:
        log_inicial["alteracoes"][alteracao_idx]["tabelas_lancamentos"][categoria_idx][
            "semanas"
        ].append({"semana": valor_medicao.semana, "dias": []})
        cp_semana_dict = log_inicial["alteracoes"][alteracao_idx]
        cp_semana_dict = cp_semana_dict["tabelas_lancamentos"][categoria_idx][
            "semanas"
        ][-1]
    else:
        cp_semana_dict = lista_semanas[0]
    semana_idx = cp_categorias_dict["semanas"].index(cp_semana_dict)
    return log_inicial, semana_idx, cp_semana_dict


def atualiza_ou_cria_dias_log(
    lista_dias,
    log_inicial,
    alteracao_idx,
    categoria_idx,
    semana_idx,
    valor_medicao,
    cp_semana_dict,
):
    if not lista_dias:
        (
            log_inicial["alteracoes"][alteracao_idx]["tabelas_lancamentos"][
                categoria_idx
            ]["semanas"][semana_idx]["dias"]
        ).append({"dia": valor_medicao.dia, "campos": []})
        cp_dias_dict = log_inicial["alteracoes"][alteracao_idx]["tabelas_lancamentos"][
            categoria_idx
        ]
        cp_dias_dict = cp_dias_dict["semanas"][semana_idx]["dias"][-1]
    else:
        cp_dias_dict = lista_dias[0]
    dia_idx = cp_semana_dict["dias"].index(cp_dias_dict)
    return log_inicial, dia_idx, cp_dias_dict


def atualiza_ou_cria_nome_campo_log(
    lista_campos,
    log_inicial,
    alteracao_idx,
    categoria_idx,
    semana_idx,
    dia_idx,
    cp_dias_dict,
    valor_medicao,
    value,
):
    if not lista_campos:
        (
            log_inicial["alteracoes"][alteracao_idx]["tabelas_lancamentos"][
                categoria_idx
            ]["semanas"][semana_idx]["dias"][dia_idx]["campos"]
        ).append(
            {
                "campo_nome": (
                    str(valor_medicao.faixa_etaria)
                    if valor_medicao.faixa_etaria
                    else valor_medicao.nome_campo
                ),
                "de": valor_medicao.valor,
                "para": value,
            }
        )
        cp_campos_dict = log_inicial["alteracoes"][alteracao_idx][
            "tabelas_lancamentos"
        ][categoria_idx]
        cp_campos_dict = cp_campos_dict["semanas"][semana_idx]["dias"][dia_idx][
            "campos"
        ][-1]
    else:
        cp_campos_dict = lista_campos[0]
    campo_idx = cp_dias_dict["campos"].index(cp_campos_dict)
    return log_inicial, campo_idx, cp_campos_dict


def atualizar_log_escola_corrigiu(
    historico, log_inicial, medicao, dicionario_alteracoes, solicitacao
):
    log_idx = historico.index(log_inicial)
    if medicao.periodo_escolar:
        periodo_nome = medicao.periodo_escolar.nome
    else:
        periodo_nome = medicao.grupo.nome

    lista_alteracoes = list(
        filter(
            lambda a: a["periodo_escolar"] == periodo_nome, log_inicial["alteracoes"]
        )
    )

    log_inicial, cp_alteracao_dict, alteracao_idx = get_alteracoes_log(
        lista_alteracoes, log_inicial, periodo_nome
    )
    for key, value in dicionario_alteracoes.items():
        valor_medicao = ValorMedicao.objects.get(uuid=key)
        (
            log_inicial,
            cp_categorias_dict,
            categoria_idx,
        ) = atualiza_ou_cria_tabela_lancamentos_log(
            valor_medicao, cp_alteracao_dict, log_inicial, alteracao_idx
        )

        lista_semanas = list(
            filter(
                lambda s: s["semana"] == valor_medicao.semana,
                cp_categorias_dict["semanas"],
            )
        )

        log_inicial, semana_idx, cp_semana_dict = atualiza_ou_cria_semanas_log(
            lista_semanas,
            log_inicial,
            alteracao_idx,
            categoria_idx,
            valor_medicao,
            cp_categorias_dict,
        )

        lista_dias = list(
            filter(lambda dia: dia["dia"] == valor_medicao.dia, cp_semana_dict["dias"])
        )

        log_inicial, dia_idx, cp_dias_dict = atualiza_ou_cria_dias_log(
            lista_dias,
            log_inicial,
            alteracao_idx,
            categoria_idx,
            semana_idx,
            valor_medicao,
            cp_semana_dict,
        )

        lista_campos = list(
            filter(
                lambda c: c["campo_nome"] == valor_medicao.nome_campo,
                cp_dias_dict["campos"],
            )
        )

        log_inicial, campo_idx, cp_campos_dict = atualiza_ou_cria_nome_campo_log(
            lista_campos,
            log_inicial,
            alteracao_idx,
            categoria_idx,
            semana_idx,
            dia_idx,
            cp_dias_dict,
            valor_medicao,
            value,
        )

        (
            historico[log_idx]["alteracoes"][alteracao_idx]["tabelas_lancamentos"][
                categoria_idx
            ]["semanas"][semana_idx]["dias"][dia_idx]["campos"][campo_idx]["para"]
        ) = value
    solicitacao.historico = json.dumps(historico)
    solicitacao.save()


def log_alteracoes_escola_corrige_periodo(user, medicao, acao, data):
    solicitacao = medicao.solicitacao_medicao_inicial
    if not solicitacao.historico:
        return
    historico = json.loads(solicitacao.historico)
    log_inicial = encontrar_ou_criar_log_inicial(user, acao, historico)

    dicionario_alteracoes, valores_medicao = gerar_dicionario_e_buscar_valores_medicao(
        data, medicao
    )
    if not valores_medicao:
        return
    if not log_inicial["alteracoes"]:
        criar_log_escola_corrigiu(
            medicao,
            valores_medicao,
            dicionario_alteracoes,
            log_inicial,
            historico,
            solicitacao,
        )
    else:
        atualizar_log_escola_corrigiu(
            historico, log_inicial, medicao, dicionario_alteracoes, solicitacao
        )


def tratar_workflow_todos_lancamentos(usuario, raw_sql):
    if usuario.tipo_usuario == "medicao":
        raw_sql += (
            "WHERE %(solicitacao_medicao_inicial)s.status IN ("
            "'MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE', "
            "'MEDICAO_APROVADA_PELA_DRE', "
            "'MEDICAO_CORRECAO_SOLICITADA_CODAE', "
            "'MEDICAO_CORRIGIDA_PARA_CODAE', "
            "'MEDICAO_APROVADA_PELA_CODAE') "
        )
    elif usuario.tipo_usuario == "diretoriaregional":
        raw_sql += "WHERE NOT %(solicitacao_medicao_inicial)s.status = " "'' "
    else:
        raw_sql += (
            "WHERE NOT %(solicitacao_medicao_inicial)s.status = "
            "'MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE' "
        )
    return raw_sql


def get_valor_total(escola, total_por_nome_campo, medicao):
    valor_total = sum(total_por_nome_campo.values())
    if escola.eh_cei or (
        escola.eh_cemei
        and ("Infantil" not in medicao.nome_periodo_grupo)
        and ("Solicitações" not in medicao.nome_periodo_grupo)
        and ("Programas" not in medicao.nome_periodo_grupo)
    ):
        fator_multiplicativo = 2
        if medicao.nome_periodo_grupo == "INTEGRAL":
            fator_multiplicativo = 5
        elif medicao.nome_periodo_grupo == "PARCIAL":
            fator_multiplicativo = 3
        valor_total *= fator_multiplicativo
    return valor_total


def get_campos_a_desconsiderar(escola, medicao):
    campos_a_desconsiderar = ["matriculados", "numero_de_alunos", "observacoes"]
    if not (
        escola.eh_cei
        or (
            escola.eh_cemei
            and "Infantil" not in medicao.nome_periodo_grupo
            and "Programas" not in medicao.nome_periodo_grupo
        )
    ):
        campos_a_desconsiderar.append("frequencia")
    return campos_a_desconsiderar


def get_dict_alimentacoes_lancamentos_especiais(
    alimentacoes_lancamentos_especiais_names,
):
    dict_alimentacoes_lancamentos_especiais = []
    for alimentacao in AlimentacaoLancamentoEspecial.objects.all():
        if alimentacao.name in alimentacoes_lancamentos_especiais_names:
            dict_alimentacoes_lancamentos_especiais.append(
                {"nome": alimentacao.nome, "name": alimentacao.name, "uuid": None}
            )
    return dict_alimentacoes_lancamentos_especiais


def build_tabela_relatorio_consolidado(ids_solicitacoes):
    primeira_tabela = []
    segunda_tabela = []

    for id_solicitacao in ids_solicitacoes:
        try:
            solicitacao = SolicitacaoMedicaoInicial.objects.get(uuid=id_solicitacao)
            row_primeira_tabela = build_row_solicitacao(solicitacao, 0)
            row_segunda_tabela = build_row_solicitacao(solicitacao, 1)

            primeira_tabela.append(row_primeira_tabela)
            segunda_tabela.append(row_segunda_tabela)
        except Exception as e:
            logger.error(f"Erro ao gerar tabela somatorio: {e}")
    return primeira_tabela, segunda_tabela


def build_row_solicitacao(solicitacao, id_tabela):
    eh_primeira_tabela = id_tabela == 0

    campos_categorias_primeira_tabela = [
        {
            "categoria": "Solicitação Alimentação",
            "campos": ["lanche_emergencial", "kit_lanche"],
        },
        {"categoria": "MANHA", "campos": ["lanche", "refeicao", "sobremesa"]},
        {"categoria": "TARDE", "campos": ["lanche", "refeicao", "sobremesa"]},
        {
            "categoria": "INTEGRAL",
            "campos": ["lanche_4h", "lanche", "refeicao", "sobremesa"],
        },
        {"categoria": "NOITE", "campos": ["lanche", "refeicao", "sobremesa"]},
    ]

    campos_categorias_segunda_tabela = [
        {
            "categoria": "Programas e Projetos",
            "campos": ["lanche_4h", "lanche", "refeicao", "sobremesa"],
        },
        {"categoria": "ETEC", "campos": ["lanche_4h", "refeicao", "sobremesa"]},
        {
            "categoria": "DIETA TIPO A",
            "campos": ["lanche_4h", "lanche_5h", "refeicao"],
            "classificacao": ["Tipo A RESTRIÇÃO DE AMINOÁCIDOS", "Tipo A ENTERAL"],
        },
        {
            "categoria": "DIETA TIPO B",
            "campos": ["lanche_4h", "lanche_5h"],
            "classificacao": ["TIPO B"],
        },
    ]

    if eh_primeira_tabela:
        return build_row_primeira_tabela(solicitacao, campos_categorias_primeira_tabela)
    return build_row_segunda_tabela(solicitacao, campos_categorias_segunda_tabela)


def get_total_solicitacoes_periodo(solicitacao, nome_campo):
    try:
        medicao = solicitacao.medicoes.get(grupo__nome__icontains="Solicitações")

        total = sum(
            int(medicao.valor)
            for medicao in medicao.valores_medicao.filter(nome_campo=nome_campo)
            if medicao.valor != "-"
        )
    except Exception:
        total = "-"
    return total or "-"


def get_total_campo_periodo(solicitacao, periodo, nome_campo):
    try:
        medicao = solicitacao.medicoes.get(periodo_escolar__nome=periodo, grupo=None)

        if nome_campo == "lanche":
            valores = medicao.valores_medicao.filter(
                categoria_medicao__nome="ALIMENTAÇÃO",
                nome_campo__in=["lanche", "2_lanche_5h"],
            )
        elif nome_campo == "lanche_4h":
            valores = medicao.valores_medicao.filter(
                categoria_medicao__nome="ALIMENTAÇÃO",
                nome_campo__in=["lanche_4h", "2_lanche_4h"],
            )
        else:
            valores = medicao.valores_medicao.filter(
                categoria_medicao__nome="ALIMENTAÇÃO", nome_campo=nome_campo
            )
        total = sum(
            int(valor_medicao.valor)
            for valor_medicao in valores
            if valor_medicao.valor != "-"
        )
    except Exception:
        total = "-"
    return total or "-"


def get_total_refeicoes_sobremesas_pagamento_por_periodo(solicitacao, periodo, campo):
    try:
        dias_no_mes = range(
            1, monthrange(int(solicitacao.ano), int(solicitacao.mes))[1] + 1
        )
        medicao = solicitacao.medicoes.get(periodo_escolar__nome=periodo, grupo=None)
        total = 0

        for dia in dias_no_mes:
            if campo == "refeicao":
                valor_sobremesa = get_valor_campo_dia(medicao, "refeicao", dia)
                valor_repeticao_sobremesa = get_valor_campo_dia(
                    medicao, "repeticao_refeicao", dia
                )
                total_alimentacao = valor_sobremesa + valor_repeticao_sobremesa
            else:
                valor_sobremesa = get_valor_campo_dia(medicao, "sobremesa", dia)
                valor_repeticao_sobremesa = get_valor_campo_dia(
                    medicao, "repeticao_sobremesa", dia
                )
                total_alimentacao = valor_sobremesa + valor_repeticao_sobremesa

            valor_matriculados = get_valor_campo_dia(medicao, "matriculados", dia)
            valor_numero_de_alunos = get_valor_campo_dia(
                medicao, "numero_de_alunos", dia
            )
            valor_comparativo = (
                valor_matriculados if valor_matriculados > 0 else valor_numero_de_alunos
            )

            total_alimentacao = min(total_alimentacao, valor_comparativo)
            total += total_alimentacao
    except Exception:
        total = "-"
    return total or "-"


def get_valor_campo_dia(medicao, nome_campo, dia):
    valor_medicao = medicao.valores_medicao.filter(
        categoria_medicao__nome="ALIMENTAÇÃO",
        nome_campo=nome_campo,
        dia=f"{dia:02d}",
    ).first()
    valor = int(valor_medicao.valor) if valor_medicao else 0
    return valor


def get_total_campo_grupo(solicitacao, grupo, nome_campo):
    try:
        medicao = solicitacao.medicoes.get(grupo__nome=grupo)

        if nome_campo == "lanche":
            valores = medicao.valores_medicao.filter(
                categoria_medicao__nome="ALIMENTAÇÃO",
                nome_campo__in=["lanche", "2_lanche_5h"],
            )
        elif nome_campo == "lanche_4h":
            valores = medicao.valores_medicao.filter(
                categoria_medicao__nome="ALIMENTAÇÃO",
                nome_campo__in=["lanche_4h", "2_lanche_4h"],
            )
        else:
            valores = medicao.valores_medicao.filter(
                categoria_medicao__nome="ALIMENTAÇÃO", nome_campo=nome_campo
            )
        total = sum(
            int(valor_medicao.valor)
            for valor_medicao in valores
            if valor_medicao.valor != "-"
        )
    except Exception:
        total = "-"
    return total or "-"


def get_total_refeicoes_sobremesas_pagamento_por_grupo(solicitacao, grupo, campo):
    try:
        dias_no_mes = range(
            1, monthrange(int(solicitacao.ano), int(solicitacao.mes))[1] + 1
        )
        medicao = solicitacao.medicoes.get(grupo__nome=grupo)
        total = 0

        for dia in dias_no_mes:
            if campo == "refeicao":
                valor_sobremesa = get_valor_campo_dia(medicao, "refeicao", dia)
                valor_repeticao_sobremesa = get_valor_campo_dia(
                    medicao, "repeticao_refeicao", dia
                )
                total_alimentacao = valor_sobremesa + valor_repeticao_sobremesa
            else:
                valor_sobremesa = get_valor_campo_dia(medicao, "sobremesa", dia)
                valor_repeticao_sobremesa = get_valor_campo_dia(
                    medicao, "repeticao_sobremesa", dia
                )
                total_alimentacao = valor_sobremesa + valor_repeticao_sobremesa

            valor_matriculados = get_valor_campo_dia(medicao, "matriculados", dia)
            valor_numero_de_alunos = get_valor_campo_dia(
                medicao, "numero_de_alunos", dia
            )
            valor_comparativo = (
                valor_matriculados if valor_matriculados > 0 else valor_numero_de_alunos
            )

            total_alimentacao = min(total_alimentacao, valor_comparativo)
            total += total_alimentacao
    except Exception:
        total = "-"
    return total or "-"


def get_total_dietas(solicitacao, classificacoes):
    try:
        logs_dietas = LogQuantidadeDietasAutorizadas.objects.filter(
            escola=solicitacao.escola,
            data__month=solicitacao.mes,
            data__year=solicitacao.ano,
            classificacao__nome__in=classificacoes,
        )
        quantidade = logs_dietas.aggregate(Sum("quantidade")).get("quantidade__sum")
        total = quantidade or "-"

    except LogQuantidadeDietasAutorizadas.DoesNotExist:
        total = "-"
    return total


def build_row_primeira_tabela(solicitacao, campos_categorias):
    body_tabela = [
        solicitacao.escola.tipo_unidade,
        solicitacao.escola.codigo_eol,
        solicitacao.escola.nome,
    ]

    for campo_categoria in campos_categorias:
        if campo_categoria["categoria"] == "Solicitação Alimentação":
            for campo in campo_categoria["campos"]:
                valor_campo = get_total_solicitacoes_periodo(solicitacao, campo)
                body_tabela.append(valor_campo)
        else:
            for campo in campo_categoria["campos"]:
                if campo in ["refeicao", "sobremesa"]:
                    valor_campo = get_total_refeicoes_sobremesas_pagamento_por_periodo(
                        solicitacao, campo_categoria["categoria"], campo
                    )
                    body_tabela.append(valor_campo)
                else:
                    valor_campo = get_total_campo_periodo(
                        solicitacao, campo_categoria["categoria"], campo
                    )
                    body_tabela.append(valor_campo)
    return body_tabela


def build_row_segunda_tabela(solicitacao, campos_categorias):
    body_tabela = [
        solicitacao.escola.tipo_unidade,
        solicitacao.escola.codigo_eol,
        solicitacao.escola.nome,
    ]

    for campo_categoria in campos_categorias:
        if "DIETA" in campo_categoria["categoria"]:
            for campo in campo_categoria["campos"]:
                valor_campo = get_total_dietas(
                    solicitacao, campo_categoria["classificacao"]
                )
                body_tabela.append(valor_campo)
        else:
            for campo in campo_categoria["campos"]:
                if campo in ["refeicao", "sobremesa"]:
                    valor_campo = get_total_refeicoes_sobremesas_pagamento_por_grupo(
                        solicitacao, campo_categoria["categoria"], campo
                    )
                    body_tabela.append(valor_campo)
                else:
                    valor_campo = get_total_campo_grupo(
                        solicitacao, campo_categoria["categoria"], campo
                    )
                    body_tabela.append(valor_campo)
    return body_tabela


def get_name_campo(campo):
    campos = {
        "Número de Alunos": "numero_de_alunos",
        "Matriculados": "matriculados",
        "Frequência": "frequencia",
        "Solicitado": "solicitado",
        "Desjejum": "desjejum",
        "Lanche": "lanche",
        "Lanche 4h": "lanche_4h",
        "Refeição": "refeicao",
        "Repetição de Refeição": "repeticao_refeicao",
        "Sobremesa": "sobremesa",
        "Repetição de Sobremesa": "repeticao_sobremesa",
        "Colação": "colacao",
        "Almoço": "almoco",
        "Refeição da tarde": "refeicao_tarde",
        "2º Lanche 4h": "2_lanche_4h",
        "2º Lanche 5h": "2_lanche_5h",
        "Lanche Extra": "lanche_extra",
        "2ª Refeição 1ª oferta": "2_refeicao_1_oferta",
        "Repetição 2ª Refeição": "repeticao_2_refeicao",
        "2ª Sobremesa 1ª oferta": "2_sobremesa_1_oferta",
        "Repetição 2ª Sobremesa": "repeticao_2_sobremesa",
    }
    return campos.get(campo, campo)


def trata_numero_de_alunos(linhas_da_tabela, tem_numero_de_alunos):
    if tem_numero_de_alunos:
        linhas_da_tabela.insert(0, "numero_de_alunos")
    else:
        linhas_da_tabela.insert(0, "matriculados")
    return linhas_da_tabela


def get_linhas_da_tabela(alimentacoes, tem_numero_de_alunos=False):
    linhas_da_tabela = ["frequencia"]
    linhas_da_tabela = trata_numero_de_alunos(linhas_da_tabela, tem_numero_de_alunos)
    for alimentacao in alimentacoes:
        nome_formatado = get_name_campo(alimentacao)
        linhas_da_tabela.append(nome_formatado)
        if nome_formatado == "refeicao":
            linhas_da_tabela.append("repeticao_refeicao")
        if nome_formatado == "sobremesa":
            linhas_da_tabela.append("repeticao_sobremesa")
    return linhas_da_tabela


def get_periodos_escolares_comuns_com_inclusoes_normais(solicitacao):
    ano = solicitacao.ano
    mes = solicitacao.mes
    escola = solicitacao.escola
    uuids_inclusoes_normais = GrupoInclusaoAlimentacaoNormal.objects.filter(
        status="CODAE_AUTORIZADO",
        escola__uuid=escola.uuid,
        inclusoes_normais__cancelado=False,
        inclusoes_normais__data__month=mes,
        inclusoes_normais__data__year=ano,
        inclusoes_normais__data__lt=datetime.date.today(),
    ).values_list("uuid", flat=True)

    periodos_escolares_inclusoes = PeriodoEscolar.objects.filter(
        quantidadeporperiodo__grupo_inclusao_normal__uuid__in=uuids_inclusoes_normais
    ).distinct()
    return periodos_escolares_inclusoes


def get_lista_dias_inclusoes_escola_sem_alunos_regulares(solicitacao):
    escola = solicitacao.escola
    lista_inclusoes = []

    inclusoes_uuids = list(
        set(
            GrupoInclusaoAlimentacaoNormal.objects.filter(
                escola=escola,
                status=GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
            ).values_list("inclusoes_normais__uuid", flat=True)
        )
    )
    inclusoes = InclusaoAlimentacaoNormal.objects.filter(
        uuid__in=inclusoes_uuids,
        data__month=int(solicitacao.mes),
        data__year=int(solicitacao.ano),
        cancelado=False,
    ).order_by("data")

    for inclusao in inclusoes:
        grupo = inclusao.grupo_inclusao
        for periodo in grupo.quantidades_periodo.all():
            tipos_alimentacao = periodo.tipos_alimentacao.exclude(
                nome="Lanche Emergencial"
            )
            alimentacoes = list(set(tipos_alimentacao.values_list("nome", flat=True)))
            linhas_da_tabela = get_linhas_da_tabela(alimentacoes, True)

            dia_da_inclusao = str(inclusao.data.day)
            if len(dia_da_inclusao) == 1:
                dia_da_inclusao = "0" + str(inclusao.data.day)
            lista_inclusoes.append(
                {
                    "periodo_escolar": periodo.periodo_escolar.nome,
                    "dia": dia_da_inclusao,
                    "linhas_da_tabela": linhas_da_tabela,
                }
            )
    return lista_inclusoes


def incluir_lanche(nomes_campos, campo, lista_inclusoes, inclusao):
    [
        nomes_campos.append(campo)
        for inc in lista_inclusoes
        if inclusao["periodo_escolar"] == inc["periodo_escolar"]
        and campo in inc["linhas_da_tabela"]
    ]
    return nomes_campos


def agrupa_permissoes_especiais_por_dia(permissoes_especiais, mes, ano):
    permissoes_especiais_por_dia = {}
    for permissao in permissoes_especiais:
        dia_inicial = 1
        dia_final = calendar.monthrange(int(ano), int(mes))[1]
        if permissao.data_inicial.month == int(mes):
            dia_inicial = permissao.data_inicial.day
        if permissao.data_final and permissao.data_final.month == int(mes):
            dia_final = permissao.data_final.day
        nome_periodo_escolar = permissao.periodo_escolar.nome
        permissao_id_externo = permissao.id_externo
        alimentacoes = [
            alimentacao.name
            for alimentacao in permissao.alimentacoes_lancamento_especial.all()
        ]
        for dia in range(dia_inicial, dia_final + 1):
            permissoes_especiais_por_dia[f"{dia:02d}"] = {
                "periodo": nome_periodo_escolar,
                "alimentacoes": alimentacoes,
                "permissao_id_externo": permissao_id_externo,
            }
    return permissoes_especiais_por_dia


def queryset_alunos_matriculados(escola):
    if escola.eh_cei or escola.eh_cemei:
        qs = LogAlunosMatriculadosFaixaEtariaDia.objects.all()
    else:
        qs = LogAlunosMatriculadosPeriodoEscola.objects.all()
    return qs


def get_data_relatorio(query_params):
    if query_params.get("data_inicial"):
        ano, mes, dia = query_params.get("data_inicial").split("-")
        data_relatorio = f"{dia}/{mes}/{ano}"
    else:
        data_relatorio = datetime.datetime.now().date().strftime("%d/%m/%Y")
    return data_relatorio


def get_queryset_filtrado(vs_relatorio_controle, queryset, filtros, periodos_uuids):
    if periodos_uuids:
        filtros = vs_relatorio_controle.validar_periodos(filtros, periodos_uuids)
    if filtros:
        queryset = queryset.filter(**filtros)
    return queryset


def get_pdf_merge_cabecalho(
    pdf_relatorio_controle_frequencia,
    pdf_cabecalho_relatorio_controle_frequencia,
    pdf_writer,
):
    for page in range(pdf_relatorio_controle_frequencia.getNumPages()):
        page = pdf_relatorio_controle_frequencia.getPage(page)
        page.mergePage(pdf_cabecalho_relatorio_controle_frequencia.getPage(0))
        pdf_writer.addPage(page)
    return pdf_writer


def cria_relatorios_financeiros_por_grupo_unidade_escolar(data):
    for grupo in GrupoUnidadeEscolar.objects.all():
        lotes_uuid = list(
            set(
                Escola.objects.filter(
                    tipo_unidade__in=grupo.tipos_unidades.all(),
                    acesso_modulo_medicao_inicial=True,
                ).values_list("lote__uuid", flat=True)
            )
        )
        for lote_uuid in lotes_uuid:
            (
                todas_solicitacoes_aprovadas_codae,
                solicitacoes,
            ) = grupo.todas_solicitacoes_medicao_do_grupo_aprovadas_codae(
                data, lote_uuid
            )
            if todas_solicitacoes_aprovadas_codae:
                try:
                    relatorio_financeiro = RelatorioFinanceiro.objects.create(
                        grupo_unidade_escolar=grupo,
                        lote=Lote.objects.get(uuid=lote_uuid),
                        mes=f"{data.month:02d}",
                        ano=f"{data.year}",
                    )
                    solicitacoes.update(relatorio_financeiro=relatorio_financeiro)
                except IntegrityError:
                    continue


def cria_logs_parcial(logs, periodo, solicitacao, periodo_escolar, data, faixa_etaria):
    if not logs and periodo == "PARCIAL":
        LogAlunosMatriculadosFaixaEtariaDia.objects.create(
            escola=solicitacao.escola,
            periodo_escolar=periodo_escolar,
            quantidade=1,
            data=data,
            faixa_etaria=faixa_etaria,
        )


def subtrai_quantidade(log):
    if log.quantidade > 0:
        log.quantidade -= 1
        log.save()


def atualiza_quantidade_logs_adicao(logs, periodo):
    for log in logs:
        if periodo == "PARCIAL":
            log.quantidade += 1
            log.save()
        else:
            subtrai_quantidade(log)


def atualiza_logs_adicao(solicitacao, aluno_periodo_parcial, aluno):
    aluno_data = aluno_periodo_parcial.get("data", "")
    if isinstance(aluno_data, datetime.date):
        aluno_data = f"{aluno_data.day}/{aluno_data.month}/{aluno_data.year}"
    (dia, mes, ano) = aluno_data.split("/")
    dia = int(dia)
    mes = int(mes)
    ano = int(ano)
    if not solicitacao.alunos_periodo_parcial.filter(
        aluno=aluno, data=datetime.date(ano, mes, dia)
    ).exists():
        for periodo in ["PARCIAL", "INTEGRAL"]:
            periodo_escolar = PeriodoEscolar.objects.get(nome=periodo)
            quantidade_dias = monthrange(int(solicitacao.ano), int(solicitacao.mes))[1]
            ultimo_dia_do_mes = datetime.date(
                int(solicitacao.ano), int(solicitacao.mes), quantidade_dias
            )
            while dia <= ultimo_dia_do_mes.day:
                data = datetime.date(
                    int(solicitacao.ano), int(solicitacao.mes), int(dia)
                )
                faixa_etaria = aluno.faixa_etaria(data)
                logs = LogAlunosMatriculadosFaixaEtariaDia.objects.filter(
                    escola=solicitacao.escola,
                    periodo_escolar=periodo_escolar,
                    data__year=int(solicitacao.ano),
                    data__month=int(solicitacao.mes),
                    data__day=int(dia),
                    faixa_etaria=faixa_etaria,
                )
                cria_logs_parcial(
                    logs, periodo, solicitacao, periodo_escolar, data, faixa_etaria
                )
                atualiza_quantidade_logs_adicao(logs, periodo)
                dia += 1


def atualiza_quantidade_logs_remocao(logs, periodo):
    for log in logs:
        if periodo == "PARCIAL":
            subtrai_quantidade(log)
        else:
            log.quantidade += 1
            log.save()


def atualiza_logs_remocao(solicitacao, aluno_periodo_parcial, aluno):
    aluno_data_removido = aluno_periodo_parcial.get("data_removido", "")
    if isinstance(aluno_data_removido, datetime.date):
        aluno_data_removido = f"{aluno_data_removido.day}/{aluno_data_removido.month}/{aluno_data_removido.year}"
    (dia, mes, ano) = aluno_data_removido.split("/")
    dia = int(dia)
    mes = int(mes)
    ano = int(ano)
    if not solicitacao.alunos_periodo_parcial.filter(
        aluno=aluno, data_removido=datetime.date(ano, mes, dia)
    ).exists():
        for periodo in ["PARCIAL", "INTEGRAL"]:
            periodo_escolar = PeriodoEscolar.objects.get(nome=periodo)
            quantidade_dias = monthrange(int(solicitacao.ano), int(solicitacao.mes))[1]
            ultimo_dia_do_mes = datetime.date(
                int(solicitacao.ano), int(solicitacao.mes), quantidade_dias
            )
            while dia <= ultimo_dia_do_mes.day:
                data = datetime.date(
                    int(solicitacao.ano), int(solicitacao.mes), int(dia)
                )
                faixa_etaria = aluno.faixa_etaria(data)
                logs = LogAlunosMatriculadosFaixaEtariaDia.objects.filter(
                    escola=solicitacao.escola,
                    periodo_escolar=periodo_escolar,
                    data__year=int(solicitacao.ano),
                    data__month=int(solicitacao.mes),
                    data__day=dia,
                    faixa_etaria=faixa_etaria,
                )
                atualiza_quantidade_logs_remocao(logs, periodo)
                dia += 1


def atualiza_alunos_periodo_parcial(solicitacao, alunos_periodo_parcial):
    for aluno_periodo_parcial in alunos_periodo_parcial:
        aluno_uuid = aluno_periodo_parcial.get("aluno")
        aluno = Aluno.objects.get(uuid=aluno_uuid)
        atualiza_logs_adicao(solicitacao, aluno_periodo_parcial, aluno)
        if aluno_periodo_parcial.get("data_removido", ""):
            atualiza_logs_remocao(solicitacao, aluno_periodo_parcial, aluno)
    for medicao in solicitacao.medicoes.all():
        medicao.valores_medicao.filter(
            nome_campo__in=["frequencia", "observacoes"]
        ).delete()
