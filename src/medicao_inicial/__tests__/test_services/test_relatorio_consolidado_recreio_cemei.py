import pytest

from src.dados_comuns.constants import (
    DIETA_ESPECIAL_TIPO_A,
    GRUPO_RECREIO_NAS_FERIAS,
    GRUPO_RECREIO_NAS_FERIAS_0_A_3,
    GRUPO_RECREIO_NAS_FERIAS_4_A_14,
)
from src.medicao_inicial.services.relatorio_consolidado_recreio_cemei import (
    _define_filtro,
    _get_lista_alimentacoes,
    _get_lista_alimentacoes_dietas,
    _processa_dieta_especial,
    _processa_periodo_regular,
    _sort_and_merge,
    _unificar_dietas,
    get_alimentacoes_por_periodo,
    get_valores_tabela,
)

pytestmark = pytest.mark.django_db


def test_get_alimentacoes_por_periodo(
    solicitacao_recreio_cemei,
    faixas_etarias_ativas,
):
    colunas = get_alimentacoes_por_periodo([solicitacao_recreio_cemei])

    assert isinstance(colunas, list)

    assert (
        sum(1 for tupla in colunas if tupla[0] == GRUPO_RECREIO_NAS_FERIAS_0_A_3) == 8
    )

    assert (
        sum(1 for tupla in colunas if tupla[0] == GRUPO_RECREIO_NAS_FERIAS_4_A_14) == 6
    )

    assert (
        sum(
            1
            for tupla in colunas
            if tupla[0]
            == "DIETA ESPECIAL - TIPO A - RECREIO NAS FÉRIAS - DE 0 A 3 ANOS E 11 MESES"
        )
        == 8
    )

    assert (
        sum(
            1
            for tupla in colunas
            if tupla[0] == "DIETA ESPECIAL - TIPO A - RECREIO NAS FÉRIAS - 4 A 14 ANOS"
        )
        == 1
    )

    assert sum(1 for tupla in colunas if tupla[0] == "Colaboradores") == 6

    for faixa in faixas_etarias_ativas:
        assert sum(1 for tupla in colunas if tupla[1] == faixa.id) == 2

    assert sum(1 for tupla in colunas if tupla[1] == "refeicao") == 3

    assert sum(1 for tupla in colunas if tupla[1] == "sobremesa") == 2

    assert sum(1 for tupla in colunas if tupla[1] == "total_refeicoes_pagamento") == 2

    assert sum(1 for tupla in colunas if tupla[1] == "total_sobremesas_pagamento") == 2


def test_get_lista_alimentacoes(
    solicitacao_recreio_cemei,
    faixas_etarias_ativas,
):
    medicoes = solicitacao_recreio_cemei.medicoes.all()

    assert medicoes.count() == 3

    medicao_colaboradores = medicoes.get(grupo__nome="Colaboradores")

    medicao_cei = medicoes.get(grupo__nome=GRUPO_RECREIO_NAS_FERIAS_0_A_3)

    medicao_emei = medicoes.get(grupo__nome=GRUPO_RECREIO_NAS_FERIAS_4_A_14)

    colaboradores = _get_lista_alimentacoes(
        medicao_colaboradores,
        medicao_colaboradores.grupo.nome,
    )

    assert isinstance(colaboradores, list)

    assert colaboradores == [
        "refeicao",
        "repeticao_refeicao",
        "repeticao_sobremesa",
        "sobremesa",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]

    recreio_cei = _get_lista_alimentacoes(
        medicao_cei,
        medicao_cei.grupo.nome,
    )

    assert isinstance(recreio_cei, list)

    assert recreio_cei == [faixa.id for faixa in faixas_etarias_ativas]

    recreio_emei = _get_lista_alimentacoes(
        medicao_emei,
        medicao_emei.grupo.nome,
    )

    assert isinstance(recreio_emei, list)

    assert recreio_emei == [
        "refeicao",
        "repeticao_refeicao",
        "repeticao_sobremesa",
        "sobremesa",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]


def test_get_lista_alimentacoes_dietas(
    solicitacao_recreio_cemei,
    faixas_etarias_ativas,
):
    medicoes = solicitacao_recreio_cemei.medicoes.all()

    assert medicoes.count() == 3

    medicao_colaboradores = medicoes.get(grupo__nome="Colaboradores")

    medicao_cei = medicoes.get(grupo__nome=GRUPO_RECREIO_NAS_FERIAS_0_A_3)

    medicao_emei = medicoes.get(grupo__nome=GRUPO_RECREIO_NAS_FERIAS_4_A_14)

    categoria_dieta_a = DIETA_ESPECIAL_TIPO_A
    categoria_dieta_a_enteral = (
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
    )

    colaboradores = _get_lista_alimentacoes_dietas(
        medicao_colaboradores,
        categoria_dieta_a,
    )

    assert isinstance(colaboradores, list)
    assert colaboradores == []

    recreio_cei = _get_lista_alimentacoes_dietas(
        medicao_cei,
        categoria_dieta_a,
    )

    assert isinstance(recreio_cei, list)

    assert recreio_cei == [faixa.id for faixa in faixas_etarias_ativas]

    recreio_emei = _get_lista_alimentacoes_dietas(
        medicao_emei,
        categoria_dieta_a_enteral,
    )

    assert isinstance(recreio_emei, list)

    assert recreio_emei == [
        "refeicao",
    ]


def test_unificar_dietas():
    dietas = {
        (
            "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS "
            "- RECREIO NAS FÉRIAS - 4 A 14 ANOS"
        ): [
            "refeicao",
        ],
        ("DIETA ESPECIAL - TIPO A - RECREIO NAS FÉRIAS - 4 A 14 ANOS"): [
            "sobremesa",
        ],
    }

    resultado = _unificar_dietas(dietas)

    assert resultado == {
        ("DIETA ESPECIAL - TIPO A - RECREIO NAS FÉRIAS - 4 A 14 ANOS"): [
            "refeicao",
            "sobremesa",
        ]
    }


def test_sort_and_merge():
    periodos = {
        GRUPO_RECREIO_NAS_FERIAS_4_A_14: [
            "sobremesa",
            "refeicao",
            "refeicao",
        ]
    }

    dietas = {
        "DIETA ESPECIAL - TIPO A - RECREIO NAS FÉRIAS - 4 A 14 ANOS": [
            "sobremesa",
            "refeicao",
        ]
    }

    resultado = _sort_and_merge(
        periodos,
        dietas,
    )

    assert resultado[GRUPO_RECREIO_NAS_FERIAS_4_A_14] == [
        "refeicao",
        "sobremesa",
    ]

    assert resultado["DIETA ESPECIAL - TIPO A - RECREIO NAS FÉRIAS - 4 A 14 ANOS"] == [
        "refeicao",
        "sobremesa",
    ]


def test_define_filtro_dieta():
    resultado = _define_filtro(
        "DIETA ESPECIAL - TIPO A - RECREIO NAS FÉRIAS - 4 A 14 ANOS"
    )

    assert resultado == {"grupo__nome__icontains": "4 A 14 ANOS"}


def test_define_filtro_periodo():
    resultado = _define_filtro("Colaboradores")

    assert resultado == {"grupo__nome": "Colaboradores"}

    resultado = _define_filtro(
        "DIETA ESPECIAL - TIPO A - RECREIO NAS FÉRIAS - 4 A 14 ANOS"
    )

    assert resultado == {"grupo__nome__icontains": "4 A 14 ANOS"}


def test_processa_dieta_especial_recreio_cei(
    solicitacao_recreio_cemei,
    monkeypatch,
):
    monkeypatch.setattr(
        "src.medicao_inicial.services.relatorio_consolidado_recreio_cei.processa_dieta_especial",
        lambda *args, **kwargs: 100,
    )

    resultado = _processa_dieta_especial(
        solicitacao_recreio_cemei,
        {},
        "refeicao",
        ("DIETA ESPECIAL - TIPO A - " "RECREIO NAS FÉRIAS - DE 0 A 3 ANOS E 11 MESES"),
    )

    assert resultado == 100


def test_processa_dieta_especial_recreio_emei(
    solicitacao_recreio_cemei,
    monkeypatch,
):
    monkeypatch.setattr(
        "src.medicao_inicial.services.relatorio_consolidado_recreio_emei_emef.processa_dieta_especial",
        lambda *args, **kwargs: 200,
    )

    resultado = _processa_dieta_especial(
        solicitacao_recreio_cemei,
        {},
        "refeicao",
        ("DIETA ESPECIAL - TIPO A - " "RECREIO NAS FÉRIAS - 4 A 14 ANOS"),
    )

    assert resultado == 200


def test_processa_periodo_regular_cei(
    solicitacao_recreio_cemei,
    monkeypatch,
):
    monkeypatch.setattr(
        "src.medicao_inicial.services.relatorio_consolidado_recreio_cei.processa_grupos_recreio",
        lambda *args, **kwargs: 300,
    )

    resultado = _processa_periodo_regular(
        solicitacao_recreio_cemei,
        {},
        "refeicao",
        GRUPO_RECREIO_NAS_FERIAS_0_A_3,
    )

    assert resultado == 300


def test_processa_periodo_regular_emei(
    solicitacao_recreio_cemei,
    monkeypatch,
):
    monkeypatch.setattr(
        "src.medicao_inicial.services.relatorio_consolidado_recreio_emei_emef.processa_grupos_recreio",
        lambda *args, **kwargs: 400,
    )

    resultado = _processa_periodo_regular(
        solicitacao_recreio_cemei,
        {},
        "refeicao",
        GRUPO_RECREIO_NAS_FERIAS_4_A_14,
    )

    assert resultado == 400


def test_get_valores_tabela(
    solicitacao_recreio_cemei,
    monkeypatch,
):
    monkeypatch.setattr(
        "src.medicao_inicial.services.relatorio_consolidado_recreio_cemei.ordenar_unidades",
        lambda solicitacoes: solicitacoes,
    )

    monkeypatch.setattr(
        "src.medicao_inicial.services.relatorio_consolidado_recreio_cemei.get_valores_iniciais",
        lambda _solicitacao: [
            "CEMEI",
            "123456",
            "CEMEI TESTE",
        ],
    )

    def mock_processa_periodo_campo(
        _solicitacao,
        _periodo,
        _campo,
        valores,
        _query_params=None,
    ):
        return valores + [100]

    monkeypatch.setattr(
        "src.medicao_inicial.services.relatorio_consolidado_recreio_cemei._processa_periodo_campo",
        mock_processa_periodo_campo,
    )

    resultado = get_valores_tabela(
        [solicitacao_recreio_cemei],
        [
            (
                GRUPO_RECREIO_NAS_FERIAS,
                "refeicao",
            ),
            (
                "Colaboradores",
                "sobremesa",
            ),
        ],
    )

    assert resultado == [
        [
            "CEMEI",
            "123456",
            "CEMEI TESTE",
            100,
            100,
        ]
    ]
