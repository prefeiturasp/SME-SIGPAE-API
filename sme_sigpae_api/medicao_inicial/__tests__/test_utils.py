from calendar import monthrange
from collections import defaultdict

import pytest

from sme_sigpae_api.medicao_inicial.utils import (
    avalia_soma_total_com_dados_tabela_anterior,
    build_dict_relacao_categorias_e_campos,
    build_dict_relacao_categorias_e_campos_cei,
    build_headers_tabelas,
    build_headers_tabelas_cei,
    build_headers_tabelas_emebs,
    build_lista_campos_observacoes,
    build_row_primeira_tabela,
    build_tabela_somatorio_body,
    build_tabela_somatorio_dietas_body,
    build_tabelas_relatorio_medicao,
    build_tabelas_relatorio_medicao_cemei,
    build_tabelas_relatorio_medicao_emebs,
    get_lista_categorias_campos,
    get_lista_categorias_campos_cei,
    get_lista_dias_letivos,
    get_nome_campo,
    get_nome_periodo,
    get_somatorio_etec,
    get_somatorio_integral,
    get_somatorio_manha,
    get_somatorio_noite_eja,
    get_somatorio_programas_e_projetos,
    get_somatorio_solicitacoes_de_alimentacao,
    get_somatorio_tarde,
    get_somatorio_total_tabela,
    tratar_valores,
)

from .data import (
    HEADERS_TABELAS_EMEBS,
    OBSERVACOES_FUNDAMENTAL_EMEBS,
    OBSERVACOES_INFANTIL_EMEBS,
    TABELAS_EMEBS,
)

pytestmark = pytest.mark.django_db


def test_utils_build_dict_relacao_categorias_e_campos(
    solicitacao_medicao_inicial_varios_valores,
):
    assert build_dict_relacao_categorias_e_campos(
        solicitacao_medicao_inicial_varios_valores.medicoes.get(
            periodo_escolar__nome="MANHA"
        )
    ) == {
        "ALIMENTAÇÃO": [
            "matriculados",
            "total_refeicoes_pagamento",
            "total_sobremesas_pagamento",
            "lanche",
            "lanche_emergencial",
            "refeicao",
            "sobremesa",
        ],
        "DIETA ESPECIAL - TIPO A ENTERAL": [
            "aprovadas",
            "lanche",
            "lanche_emergencial",
            "refeicao",
            "sobremesa",
        ],
        "DIETA ESPECIAL - TIPO B": [
            "aprovadas",
            "lanche",
            "lanche_emergencial",
            "refeicao",
            "sobremesa",
        ],
    }


def test_utils_build_headers_tabelas(solicitacao_medicao_inicial_varios_valores):
    assert build_headers_tabelas(solicitacao_medicao_inicial_varios_valores) == [
        {
            "periodos": ["MANHA"],
            "categorias": ["ALIMENTAÇÃO", "DIETA ESPECIAL - TIPO A ENTERAL"],
            "nomes_campos": [
                "matriculados",
                "lanche",
                "refeicao",
                "total_refeicoes_pagamento",
                "sobremesa",
                "total_sobremesas_pagamento",
                "lanche_emergencial",
                "aprovadas",
                "lanche",
                "refeicao",
                "sobremesa",
                "lanche_emergencial",
            ],
            "len_periodos": [12],
            "len_categorias": [7, 5],
            "valores_campos": [],
            "ordem_periodos_grupos": [1],
            "dias_letivos": [],
            "categorias_dos_periodos": {
                "MANHA": [
                    {"categoria": "ALIMENTAÇÃO", "numero_campos": 7},
                    {
                        "categoria": "DIETA ESPECIAL - TIPO A ENTERAL",
                        "numero_campos": 5,
                    },
                ]
            },
        },
        {
            "periodos": ["MANHA", "TARDE"],
            "categorias": ["DIETA ESPECIAL - TIPO B", "ALIMENTAÇÃO"],
            "nomes_campos": [
                "aprovadas",
                "lanche",
                "refeicao",
                "sobremesa",
                "lanche_emergencial",
                "matriculados",
                "lanche",
                "refeicao",
                "total_refeicoes_pagamento",
                "sobremesa",
                "total_sobremesas_pagamento",
                "lanche_emergencial",
            ],
            "len_periodos": [5, 7],
            "len_categorias": [5, 7],
            "valores_campos": [],
            "ordem_periodos_grupos": [1, 2],
            "dias_letivos": [],
            "categorias_dos_periodos": {
                "MANHA": [{"categoria": "DIETA ESPECIAL - TIPO B", "numero_campos": 5}],
                "TARDE": [{"categoria": "ALIMENTAÇÃO", "numero_campos": 7}],
            },
        },
        {
            "periodos": ["TARDE"],
            "categorias": [
                "DIETA ESPECIAL - TIPO A ENTERAL",
                "DIETA ESPECIAL - TIPO B",
            ],
            "nomes_campos": [
                "aprovadas",
                "lanche",
                "refeicao",
                "sobremesa",
                "lanche_emergencial",
                "aprovadas",
                "lanche",
                "refeicao",
                "sobremesa",
                "lanche_emergencial",
            ],
            "len_periodos": [10],
            "len_categorias": [5, 5],
            "valores_campos": [],
            "ordem_periodos_grupos": [2],
            "dias_letivos": [],
            "categorias_dos_periodos": {
                "TARDE": [
                    {
                        "categoria": "DIETA ESPECIAL - TIPO A ENTERAL",
                        "numero_campos": 5,
                    },
                    {"categoria": "DIETA ESPECIAL - TIPO B", "numero_campos": 5},
                ]
            },
        },
    ]


def test_build_headers_tabelas_cei(
    solicitacao_medicao_inicial_valores_cei,
):
    assert build_headers_tabelas_cei(solicitacao_medicao_inicial_valores_cei) == [
        {
            "periodos": ["INTEGRAL", "MANHA"],
            "categorias": [
                {
                    "categoria": "ALIMENTAÇÃO",
                    "faixas_etarias": ["01 a 09 meses", "total"],
                    "periodo": "INTEGRAL",
                },
                {
                    "categoria": "ALIMENTAÇÃO",
                    "faixas_etarias": ["01 a 09 meses", "total"],
                    "periodo": "MANHA",
                },
            ],
            "len_periodos": [3, 3],
            "len_categorias": [6, 6],
            "valores_campos": [],
            "ordem_periodos_grupos": [1, 3],
            "periodo_values": defaultdict(int, {"INTEGRAL": 3, "MANHA": 3}),
            "categoria_values": defaultdict(int, {"ALIMENTAÇÃO": 6}),
        }
    ]


def test_build_headers_tabelas_emebs(solicitacao_medicao_inicial_varios_valores_emebs):
    assert (
        build_headers_tabelas_emebs(solicitacao_medicao_inicial_varios_valores_emebs)
        == HEADERS_TABELAS_EMEBS
    )


def test_get_lista_dias_letivos(solicitacao_medicao_inicial_varios_valores):
    dias_letivos = get_lista_dias_letivos(solicitacao_medicao_inicial_varios_valores)

    _, num_dias = monthrange(
        int(solicitacao_medicao_inicial_varios_valores.ano),
        int(solicitacao_medicao_inicial_varios_valores.mes),
    )

    assert len(dias_letivos) == num_dias


def test_get_nome_periodo():
    assert get_nome_periodo("Infantil INTEGRAL") == "INTEGRAL"
    assert get_nome_periodo("Infantil MANHA") == "MANHA"
    assert get_nome_periodo("Infantil TARDE") == "TARDE"
    assert get_nome_periodo("Fundamental MANHA") == "Fundamental MANHA"
    assert get_nome_periodo("EJA NOITE") == "EJA NOITE"


def test_build_tabelas_relatorio_medicao(solicitacao_medicao_inicial_varios_valores):
    assert build_tabelas_relatorio_medicao(
        solicitacao_medicao_inicial_varios_valores
    ) == [
        {
            "periodos": ["MANHA"],
            "categorias": ["ALIMENTAÇÃO", "DIETA ESPECIAL - TIPO A ENTERAL"],
            "nomes_campos": [
                "matriculados",
                "lanche",
                "refeicao",
                "total_refeicoes_pagamento",
                "sobremesa",
                "total_sobremesas_pagamento",
                "lanche_emergencial",
                "aprovadas",
                "lanche",
                "refeicao",
                "sobremesa",
                "lanche_emergencial",
            ],
            "len_periodos": [12],
            "len_categorias": [7, 5],
            "valores_campos": [
                [1, "0", "10", "10", 0, "10", "0", "10", "0", "10", "10", "10", "10"],
                [2, "0", "10", "10", 0, "10", "0", "10", "0", "10", "10", "10", "10"],
                [3, "0", "10", "10", 0, "10", "0", "10", "0", "10", "10", "10", "10"],
                [4, "0", "10", "10", 0, "10", "0", "10", "0", "10", "10", "10", "10"],
                [5, "0", "10", "10", 0, "10", "0", "10", "0", "10", "10", "10", "10"],
                [6, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [7, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [8, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [9, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [10, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [11, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [12, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [13, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [14, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [15, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [16, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [17, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [18, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [19, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [20, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [21, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [22, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [23, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [24, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [25, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [26, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [27, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [28, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [29, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [30, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                [31, "0", "0", "0", 0, "0", "0", "0", "0", "0", "0", "0", "0"],
                ["Total", "-", 50, 50, 0, 50, 0, 50, "-", 50, 50, 50, 50],
            ],
            "ordem_periodos_grupos": [1],
            "dias_letivos": [
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
            ],
            "categorias_dos_periodos": {
                "MANHA": [
                    {"categoria": "ALIMENTAÇÃO", "numero_campos": 7},
                    {
                        "categoria": "DIETA ESPECIAL - TIPO A ENTERAL",
                        "numero_campos": 5,
                    },
                ]
            },
        },
        {
            "periodos": ["MANHA", "TARDE"],
            "categorias": ["DIETA ESPECIAL - TIPO B", "ALIMENTAÇÃO"],
            "nomes_campos": [
                "aprovadas",
                "lanche",
                "refeicao",
                "sobremesa",
                "lanche_emergencial",
                "matriculados",
                "lanche",
                "refeicao",
                "total_refeicoes_pagamento",
                "sobremesa",
                "total_sobremesas_pagamento",
                "lanche_emergencial",
            ],
            "len_periodos": [5, 7],
            "len_categorias": [5, 7],
            "valores_campos": [
                [1, "0", "10", "10", "10", "10", "0", "10", "10", 0, "10", "0", "10"],
                [2, "0", "10", "10", "10", "10", "0", "10", "10", 0, "10", "0", "10"],
                [3, "0", "10", "10", "10", "10", "0", "10", "10", 0, "10", "0", "10"],
                [4, "0", "10", "10", "10", "10", "0", "10", "10", 0, "10", "0", "10"],
                [5, "0", "10", "10", "10", "10", "0", "10", "10", 0, "10", "0", "10"],
                [6, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [7, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [8, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [9, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [10, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [11, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [12, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [13, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [14, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [15, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [16, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [17, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [18, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [19, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [20, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [21, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [22, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [23, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [24, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [25, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [26, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [27, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [28, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [29, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [30, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                [31, "0", "0", "0", "0", "0", "0", "0", "0", 0, "0", "0", "0"],
                ["Total", "-", 50, 50, 50, 50, "-", 50, 50, 0, 50, 0, 50],
            ],
            "ordem_periodos_grupos": [1, 2],
            "dias_letivos": [
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
            ],
            "categorias_dos_periodos": {
                "MANHA": [{"categoria": "DIETA ESPECIAL - TIPO B", "numero_campos": 5}],
                "TARDE": [{"categoria": "ALIMENTAÇÃO", "numero_campos": 7}],
            },
        },
        {
            "periodos": ["TARDE"],
            "categorias": [
                "DIETA ESPECIAL - TIPO A ENTERAL",
                "DIETA ESPECIAL - TIPO B",
            ],
            "nomes_campos": [
                "aprovadas",
                "lanche",
                "refeicao",
                "sobremesa",
                "lanche_emergencial",
                "aprovadas",
                "lanche",
                "refeicao",
                "sobremesa",
                "lanche_emergencial",
            ],
            "len_periodos": [10],
            "len_categorias": [5, 5],
            "valores_campos": [
                [1, "0", "10", "10", "10", "10", "0", "10", "10", "10", "10"],
                [2, "0", "10", "10", "10", "10", "0", "10", "10", "10", "10"],
                [3, "0", "10", "10", "10", "10", "0", "10", "10", "10", "10"],
                [4, "0", "10", "10", "10", "10", "0", "10", "10", "10", "10"],
                [5, "0", "10", "10", "10", "10", "0", "10", "10", "10", "10"],
                [6, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [7, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [8, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [9, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [10, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [11, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [12, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [13, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [14, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [15, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [16, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [17, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [18, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [19, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [20, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [21, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [22, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [23, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [24, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [25, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [26, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [27, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [28, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [29, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [30, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                [31, "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
                ["Total", "-", 50, 50, 50, 50, "-", 50, 50, 50, 50],
            ],
            "ordem_periodos_grupos": [2],
            "dias_letivos": [
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
            ],
            "categorias_dos_periodos": {
                "TARDE": [
                    {
                        "categoria": "DIETA ESPECIAL - TIPO A ENTERAL",
                        "numero_campos": 5,
                    },
                    {"categoria": "DIETA ESPECIAL - TIPO B", "numero_campos": 5},
                ]
            },
        },
    ]


def test_build_tabelas_relatorio_medicao_emebs(
    solicitacao_medicao_inicial_varios_valores_emebs,
):
    assert (
        build_tabelas_relatorio_medicao_emebs(
            solicitacao_medicao_inicial_varios_valores_emebs
        )
        == TABELAS_EMEBS
    )


def test_build_lista_campos_observacoes_emebs(
    solicitacao_medicao_inicial_varios_valores_emebs,
):
    observacoes_infantil = build_lista_campos_observacoes(
        solicitacao_medicao_inicial_varios_valores_emebs, "INFANTIL"
    )
    assert observacoes_infantil == OBSERVACOES_INFANTIL_EMEBS

    observacoes_fundamental = build_lista_campos_observacoes(
        solicitacao_medicao_inicial_varios_valores_emebs, "FUNDAMENTAL"
    )
    assert observacoes_fundamental == OBSERVACOES_FUNDAMENTAL_EMEBS


def test_utils_get_lista_categorias_campos(medicao_solicitacoes_alimentacao):
    assert get_lista_categorias_campos(medicao_solicitacoes_alimentacao) == [
        ("LANCHE EMERGENCIAL", "solicitado"),
        ("LANCHE EMERGENCIAL", "consumido"),
        ("KIT LANCHE", "solicitado"),
        ("KIT LANCHE", "consumido"),
    ]


def test_utils_get_lista_categorias_campos_cei(medicao_solicitacoes_alimentacao_cei):
    assert get_lista_categorias_campos_cei(medicao_solicitacoes_alimentacao_cei) == [
        ("ALIMENTAÇÃO", "01 a 02 meses")
    ]


def test_build_dict_relacao_categorias_e_campos_cei(
    medicao_solicitacoes_alimentacao_cei,
):
    assert build_dict_relacao_categorias_e_campos_cei(
        medicao_solicitacoes_alimentacao_cei
    ) == {"ALIMENTAÇÃO": ["01 a 02 meses"]}


def test_utils_tratar_valores(escola, escola_emei):
    campos = [
        "lanche",
        "refeicao",
        "lanche_emergencial",
        "sobremesa",
        "repeticao_refeicao",
        "kit_lanche",
        "repeticao_sobremesa",
        "2_lanche_5h",
        "2_lanche_4h",
        "2_refeicao_1_oferta",
        "repeticao_2_refeicao",
        "2_sobremesa_1_oferta",
        "repeticao_2_sobremesa",
    ]
    total_por_nome_campo = {campo: 10 for campo in campos}
    assert tratar_valores(escola_emei, total_por_nome_campo) == {
        "lanche_emergencial": 10,
        "kit_lanche": 10,
        "lanche": 20,
        "lanche_4h": 10,
        "refeicao": 20,
        "sobremesa": 20,
    }
    assert tratar_valores(escola, total_por_nome_campo) == {
        "lanche_emergencial": 10,
        "kit_lanche": 10,
        "lanche": 20,
        "lanche_4h": 10,
        "refeicao": 40,
        "sobremesa": 40,
    }


def test_utils_get_nome_campo():
    assert get_nome_campo("lanche_4h") == "Lanche 4h"
    assert get_nome_campo("repeticao_sobremesa") == "Repetição de Sobremesa"


def test_utils_get_somatorio_manha(solicitacao_medicao_inicial_com_valores_repeticao):
    assert (
        get_somatorio_manha(
            "refeicao", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 100
    )
    assert (
        get_somatorio_manha(
            "sobremesa", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 100
    )
    assert (
        get_somatorio_manha(
            "lanche_4h", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 0
    )


def test_utils_get_somatorio_tarde(solicitacao_medicao_inicial_com_valores_repeticao):
    assert (
        get_somatorio_tarde(
            "refeicao", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 100
    )
    assert (
        get_somatorio_tarde(
            "sobremesa", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 100
    )
    assert (
        get_somatorio_tarde(
            "lanche_4h", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 0
    )


def test_utils_get_somatorio_integral(
    solicitacao_medicao_inicial_com_valores_repeticao,
):
    assert (
        get_somatorio_integral(
            "refeicao", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 100
    )
    assert (
        get_somatorio_integral(
            "sobremesa", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 100
    )
    assert (
        get_somatorio_integral(
            "lanche_4h", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 0
    )


def test_build_tabelas_relatorio_medicao_cemei(solicitacao_medicao_inicial_cemei):
    assert build_tabelas_relatorio_medicao_cemei(solicitacao_medicao_inicial_cemei) == [
        {
            "periodos": ["INTEGRAL"],
            "categorias": ["ALIMENTAÇÃO"],
            "nomes_campos": [],
            "faixas_etarias": ["01 mês", "total"],
            "len_periodos": [3],
            "len_categorias": [3],
            "valores_campos": [
                [1, "0", "10", "10"],
                [2, "0", "0", "0"],
                [3, "0", "0", "0"],
                [4, "0", "0", "0"],
                [5, "0", "0", "0"],
                [6, "0", "0", "0"],
                [7, "0", "0", "0"],
                [8, "0", "0", "0"],
                [9, "0", "0", "0"],
                [10, "0", "0", "0"],
                [11, "0", "0", "0"],
                [12, "0", "0", "0"],
                [13, "0", "0", "0"],
                [14, "0", "0", "0"],
                [15, "0", "0", "0"],
                [16, "0", "0", "0"],
                [17, "0", "0", "0"],
                [18, "0", "0", "0"],
                [19, "0", "0", "0"],
                [20, "0", "0", "0"],
                [21, "0", "0", "0"],
                [22, "0", "0", "0"],
                [23, "0", "0", "0"],
                [24, "0", "0", "0"],
                [25, "0", "0", "0"],
                [26, "0", "0", "0"],
                [27, "0", "0", "0"],
                [28, "0", "0", "0"],
                [29, "0", "0", "0"],
                [30, "0", "0", "0"],
                ["Total", "-", "10", 10],
            ],
            "ordem_periodos_grupos": [1],
            "dias_letivos": [
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
            ],
            "categorias_dos_periodos": {
                "INTEGRAL": [{"categoria": "ALIMENTAÇÃO", "numero_campos": 1}]
            },
        }
    ]


def test_utils_get_somatorio_noite_eja(
    solicitacao_medicao_inicial_com_valores_repeticao,
):
    assert (
        get_somatorio_noite_eja(
            "refeicao", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 100
    )
    assert (
        get_somatorio_noite_eja(
            "sobremesa", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 100
    )
    assert (
        get_somatorio_noite_eja(
            "lanche_4h", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 0
    )


def test_utils_get_somatorio_etec(solicitacao_medicao_inicial_com_valores_repeticao):
    assert (
        get_somatorio_etec(
            "refeicao", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 100
    )
    assert (
        get_somatorio_etec(
            "sobremesa", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 100
    )
    assert (
        get_somatorio_etec(
            "lanche_4h", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 0
    )


def test_utils_get_somatorio_solicitacoes_de_alimentacao(
    solicitacao_medicao_inicial_com_valores_repeticao,
):
    solicitacao = solicitacao_medicao_inicial_com_valores_repeticao
    assert (
        get_somatorio_solicitacoes_de_alimentacao("lanche_emergencial", solicitacao)
        == 50
    )
    assert get_somatorio_solicitacoes_de_alimentacao("kit_lanche", solicitacao) == 50
    assert get_somatorio_solicitacoes_de_alimentacao("lanche_4h", solicitacao) == 0


def test_utils_get_somatorio_programas_e_projetos(
    solicitacao_medicao_inicial_com_valores_repeticao,
):
    assert (
        get_somatorio_programas_e_projetos(
            "refeicao", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 100
    )
    assert (
        get_somatorio_programas_e_projetos(
            "sobremesa", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 100
    )
    assert (
        get_somatorio_programas_e_projetos(
            "lanche_4h", solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
        )
        == 0
    )


def test_utils_get_somatorio_total_tabela(
    solicitacao_medicao_inicial_com_valores_repeticao,
):
    solicitacao = solicitacao_medicao_inicial_com_valores_repeticao
    somatorio_manha = get_somatorio_manha("refeicao", solicitacao, {}, {})
    somatorio_tarde = get_somatorio_tarde("refeicao", solicitacao, {}, {})
    somatorio_integral = get_somatorio_integral("refeicao", solicitacao, {}, {})
    somatorio_programas_e_projetos = get_somatorio_programas_e_projetos(
        "refeicao", solicitacao, {}, {}
    )
    somatorio_solicitacoes_de_alimentacao = get_somatorio_solicitacoes_de_alimentacao(
        "refeicao", solicitacao
    )
    valores_somatorios_tabela = [
        somatorio_manha,
        somatorio_tarde,
        somatorio_integral,
        somatorio_programas_e_projetos,
        somatorio_solicitacoes_de_alimentacao,
    ]
    assert get_somatorio_total_tabela(valores_somatorios_tabela) == 450


def test_utils_build_tabela_somatorio_body(
    solicitacao_medicao_inicial_com_valores_repeticao,
):
    primeira_tabela_somatorio, segunda_tabela_somatorio = build_tabela_somatorio_body(
        solicitacao_medicao_inicial_com_valores_repeticao, {}, {}
    )

    assert primeira_tabela_somatorio["body"] == [
        ["Lanche", 50, 50, 50, 50, 50, 250],
        ["Refeição", 100, 100, 100, 100, 50, 450],
        ["Kit Lanche", 50, 50, 50, 50, 50, 250],
        ["Sobremesa", 100, 100, 100, 100, 50, 450],
        ["Lanche Emergencial", 50, 50, 50, 50, 50, 250],
    ]

    assert segunda_tabela_somatorio["body"] == [
        [50, 50, 100],
        [100, 100, 200],
        [50, 50, 100],
        [100, 100, 200],
        [50, 50, 100],
    ]


def test_utils_build_tabela_somatorio_dietas_body(
    solicitacao_medicao_inicial_dietas,
):
    primeira_tabela_tipo_a, segunda_tabela_tipo_a = build_tabela_somatorio_dietas_body(
        solicitacao_medicao_inicial_dietas, "TIPO A"
    )

    assert primeira_tabela_tipo_a["body"] == [
        ["Lanche", 0, 20, 20, 20, 60],
        ["Lanche 4h", 0, 20, 20, 20, 60],
        ["Refeição", 0, 20, 20, 20, 60],
    ]

    assert segunda_tabela_tipo_a["body"] == [
        ["Lanche", 20, 20],
        ["Lanche 4h", 20, 20],
        ["Refeição", 20, 20],
    ]

    primeira_tabela_tipo_b, segunda_tabela_tipo_b = build_tabela_somatorio_dietas_body(
        solicitacao_medicao_inicial_dietas, "TIPO B"
    )

    assert primeira_tabela_tipo_b["body"] == [
        ["Lanche", 0, 20, 20, 20, 60],
        ["Lanche 4h", 0, 20, 20, 20, 60],
    ]
    assert segunda_tabela_tipo_b["body"] == [["Lanche", 20, 20], ["Lanche 4h", 20, 20]]


def test_build_row_primeira_tabela(solicitacao_medicao_inicial_com_valores_repeticao):
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

    assert build_row_primeira_tabela(
        solicitacao_medicao_inicial_com_valores_repeticao,
        campos_categorias_primeira_tabela,
    ) == [
        solicitacao_medicao_inicial_com_valores_repeticao.escola.tipo_unidade,
        "123456",
        "EMEF TESTE",
        50,
        50,
        50,
        "-",
        "-",
        50,
        "-",
        "-",
        "-",
        50,
        "-",
        "-",
        50,
        "-",
        "-",
    ]


def test_avalia_soma_total_com_dados_tabela_anterior():
    valores_para_soma = ["-", "123", "-", "35"]
    todas_faixas_anterior = [
        "01 a 03 meses",
        "04 a 05 meses",
        "07 a 11 meses",
        "01 ano a 03 anos e 11 meses",
        "04 anos a 06 anos",
        "total",
        "04 a 05 meses",
        "06 meses",
    ]
    index = 2
    index_primeira_coluna_total = 2
    tabela_anterior = {
        "periodos": ["INTEGRAL"],
        "categorias": [
            {
                "categoria": "ALIMENTAÇÃO",
                "faixas_etarias": [
                    "01 a 03 meses",
                    "04 a 05 meses",
                    "07 a 11 meses",
                    "01 ano a 03 anos e 11 meses",
                    "04 anos a 06 anos",
                    "total",
                ],
                "periodo": "INTEGRAL",
            },
            {
                "categoria": "DIETA ESPECIAL - TIPO B",
                "faixas_etarias": ["04 a 05 meses", "06 meses"],
                "periodo": "INTEGRAL",
            },
        ],
        "len_periodos": [15],
        "len_categorias": [11, 4],
        "valores_campos": [
            [
                1,
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
            ],
            [
                2,
                "2",
                "0",
                "1",
                "0",
                "7",
                "0",
                "108",
                "0",
                "48",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
            ],
            [
                3,
                "2",
                "0",
                "1",
                "0",
                "7",
                "0",
                "108",
                "0",
                "48",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
            ],
            [
                4,
                "2",
                "0",
                "1",
                "0",
                "7",
                "0",
                "107",
                "0",
                "49",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
            ],
            [
                5,
                "2",
                "2",
                "1",
                "1",
                "7",
                "7",
                "107",
                "38",
                "49",
                "16",
                "64",
                "0",
                "0",
                "0",
                "0",
            ],
            [
                6,
                "2",
                "2",
                "1",
                "1",
                "8",
                "8",
                "106",
                "39",
                "49",
                "18",
                "68",
                "0",
                "0",
                "0",
                "0",
            ],
            [
                7,
                "2",
                "2",
                "1",
                "1",
                "8",
                "8",
                "106",
                "40",
                "49",
                "20",
                "71",
                "0",
                "0",
                "0",
                "0",
            ],
            [
                8,
                "3",
                "0",
                "1",
                "0",
                "8",
                "0",
                "106",
                "0",
                "49",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
            ],
            [
                9,
                "3",
                "0",
                "1",
                "0",
                "8",
                "0",
                "106",
                "0",
                "49",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
            ],
            [
                10,
                "3",
                "3",
                "1",
                "1",
                "8",
                "8",
                "106",
                "54",
                "49",
                "37",
                "103",
                "0",
                "0",
                "0",
                "0",
            ],
            [
                11,
                "3",
                "3",
                "0",
                "0",
                "8",
                "8",
                "106",
                "50",
                "50",
                "28",
                "89",
                1,
                "0",
                "0",
                "0",
            ],
            [
                12,
                "3",
                "3",
                "0",
                "0",
                "8",
                "7",
                "106",
                "57",
                "50",
                "27",
                "94",
                1,
                "0",
                "0",
                "0",
            ],
            [
                13,
                "4",
                "4",
                "0",
                "0",
                "8",
                "8",
                "106",
                "53",
                "50",
                "30",
                "95",
                1,
                "0",
                "0",
                "0",
            ],
            [
                14,
                "4",
                "4",
                "0",
                "0",
                "8",
                "7",
                "106",
                "50",
                "50",
                "26",
                "87",
                1,
                "0",
                "0",
                "0",
            ],
            [
                15,
                "4",
                "4",
                "0",
                "0",
                "8",
                "8",
                "107",
                "50",
                "49",
                "30",
                "92",
                1,
                "1",
                "0",
                "0",
            ],
            [
                16,
                "4",
                "0",
                "0",
                "0",
                "7",
                "0",
                "107",
                "0",
                "50",
                "0",
                "0",
                1,
                "0",
                "0",
                "0",
            ],
            [
                17,
                "4",
                "4",
                "0",
                "0",
                "7",
                "6",
                "106",
                "83",
                "50",
                "42",
                "135",
                1,
                "0",
                "0",
                "0",
            ],
            [
                18,
                "4",
                "4",
                "0",
                "0",
                "7",
                "6",
                "106",
                "89",
                "50",
                "48",
                "147",
                1,
                "1",
                "0",
                "0",
            ],
            [
                19,
                "4",
                "4",
                "0",
                "0",
                "7",
                "6",
                "106",
                "80",
                "50",
                "41",
                "131",
                1,
                "1",
                "0",
                "0",
            ],
            [
                20,
                "4",
                "4",
                "0",
                "0",
                "7",
                "5",
                "106",
                "81",
                "50",
                "46",
                "136",
                1,
                "1",
                "0",
                "0",
            ],
            [
                21,
                "4",
                "4",
                "1",
                "1",
                "7",
                "5",
                "106",
                "71",
                "50",
                "38",
                "119",
                "0",
                "0",
                1,
                "1",
            ],
            [
                22,
                "2",
                "0",
                "2",
                "0",
                "7",
                "0",
                "109",
                "0",
                "50",
                "0",
                "0",
                "0",
                "0",
                1,
                "0",
            ],
            [
                23,
                "2",
                "0",
                "2",
                "0",
                "7",
                "0",
                "109",
                "0",
                "50",
                "0",
                "0",
                "0",
                "0",
                1,
                "0",
            ],
            [
                24,
                "2",
                "2",
                "2",
                "2",
                "7",
                "6",
                "109",
                "80",
                "50",
                "46",
                "136",
                "0",
                "0",
                1,
                "0",
            ],
            [
                25,
                "2",
                "2",
                "2",
                "2",
                "7",
                "6",
                "110",
                "79",
                "50",
                "48",
                "137",
                "0",
                "0",
                1,
                "0",
            ],
            [
                26,
                "2",
                "2",
                "2",
                "2",
                "7",
                "6",
                "110",
                "80",
                "50",
                "48",
                "138",
                "0",
                "0",
                1,
                "0",
            ],
            [
                27,
                "2",
                "2",
                "2",
                "2",
                "7",
                "6",
                "111",
                "73",
                "51",
                "47",
                "130",
                "0",
                "0",
                1,
                "1",
            ],
            [
                28,
                "1",
                "1",
                "3",
                "3",
                "7",
                "6",
                "110",
                "73",
                "53",
                "46",
                "129",
                "0",
                "0",
                1,
                "0",
            ],
            [
                "Total",
                "-",
                "56",
                "-",
                "16",
                "-",
                "127",
                "-",
                "1220",
                "-",
                "682",
                "2101",
                "-",
                "4",
                "-",
                "2",
            ],
        ],
    }

    valor_de_retorno = avalia_soma_total_com_dados_tabela_anterior(
        valores_para_soma,
        todas_faixas_anterior,
        index,
        index_primeira_coluna_total,
        tabela_anterior,
    )
    assert valor_de_retorno == ["-", "123", "-", "35", "-", "4", "-", "2"]

    soma = sum(int(item) for item in valor_de_retorno if str(item).isdigit())
    assert soma == 164
