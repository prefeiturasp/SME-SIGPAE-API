import pytest
from rest_framework.exceptions import ValidationError

from src.escola_aberta.api.serializers import (
    EscolaAbertaCreateSerializer,
    RecorrenciaSerializer,
    EscolaAbertaUnidadeParticipanteCreateSerializer
)
from src.escola_aberta.models import (
    EscolaAberta,
    EscolaAbertaUnidadeParticipante,
)


@pytest.mark.django_db
def test_recorrencia_data_inicial_maior_que_data_final():
    """Valida se data_inicial posterior a data_final gera erro."""
    data = {
        "data_inicial": "25/10/2026",
        "data_final": "20/10/2026",
        "dias_semana": ["0", "6"],
    }
    serializer = RecorrenciaSerializer(data=data)
    assert not serializer.is_valid()
    assert "data_inicial não pode ser maior que data_final" in str(
        serializer.errors["non_field_errors"]
    )


@pytest.mark.django_db
def test_recorrencia_sem_dias_semana():
    """Valida obrigatoriedade de ao menos um dia da semana."""
    data = {
        "data_inicial": "20/10/2026",
        "data_final": "25/10/2026",
        "dias_semana": [],
    }
    serializer = RecorrenciaSerializer(data=data)
    assert not serializer.is_valid()
    assert "Selecione ao menos um dia da semana" in str(
        serializer.errors["non_field_errors"]
    )


@pytest.mark.django_db
def test_unidades_participantes_repetidas(setup_escola_aberta_data):
    """Valida erro quando a mesma UE é enviada mais de uma vez na mesma requisição."""
    data = {
        "recorrencias": {
            "data_inicial": "12/10/2026",
            "data_final": "23/10/2026",
            "dias_semana": ["0", "6"],
        },
        "unidades_participantes": [
            {
                "lote": str(setup_escola_aberta_data["lote"].uuid),
                "unidade_educacional": str(setup_escola_aberta_data["escola_1"].uuid),
                "tipos_alimentacao": [str(setup_escola_aberta_data["tipo_alim"].uuid)],
                "num_participantes": 30,
            },
            {
                "lote": str(setup_escola_aberta_data["lote"].uuid),
                "unidade_educacional": str(setup_escola_aberta_data["escola_1"].uuid),
                "tipos_alimentacao": [str(setup_escola_aberta_data["tipo_alim"].uuid)],
                "num_participantes": 30,
            },
        ],
    }
    serializer = EscolaAbertaCreateSerializer(data=data)
    assert not serializer.is_valid()
    assert "Há unidades educacionais repetidas" in str(
        serializer.errors["unidades_participantes"]
    )


@pytest.mark.django_db
def test_validacao_duplicidade_mesma_ue_periodo_e_dia(setup_escola_aberta_data):
    """Testa regra de conflito: mesma UE + período sobreposto + dias de semana em comum."""
    # Primeiro cadastro: 10/10 a 20/10 nos dias 0 (domingo) e 6 (sábado)
    escola_aberta_existente = EscolaAberta.objects.create(
        data_inicial="2026-10-10",
        data_final="2026-10-20",
        dias_semana=["0", "6"],
    )
    unidade = EscolaAbertaUnidadeParticipante.objects.create(
        escola_aberta=escola_aberta_existente,
        lote=setup_escola_aberta_data["lote"],
        unidade_educacional=setup_escola_aberta_data["escola_1"],
    )
    unidade.tipos_alimentacao.add(setup_escola_aberta_data["tipo_alim"])

    # Tentativa conflitante: período sobreposto (15/10 a 25/10) compartilhando o dia 6 (sábado)
    payload_conflitante = {
        "recorrencias": {
            "data_inicial": "15/10/2026",
            "data_final": "25/10/2026",
            "dias_semana": ["5", "6"],
        },
        "unidades_participantes": [
            {
                "lote": str(setup_escola_aberta_data["lote"].uuid),
                "unidade_educacional": str(setup_escola_aberta_data["escola_1"].uuid),
                "tipos_alimentacao": [str(setup_escola_aberta_data["tipo_alim"].uuid)],
                "num_participantes": 30,
            }
        ],
    }
    serializer = EscolaAbertaCreateSerializer(data=payload_conflitante)
    assert not serializer.is_valid()
    assert "Já existe um cadastro com esta combinação de UE" in str(
        serializer.errors["non_field_errors"]
    )


@pytest.mark.django_db
def test_validacao_duplicidade_ignora_o_proprio_registro_no_update(
    setup_escola_aberta_data,
):
    """No update, o próprio registro não pode ser tratado como duplicado."""
    escola_aberta = EscolaAberta.objects.create(
        data_inicial="2026-10-10",
        data_final="2026-10-20",
        dias_semana=["0", "6"],
    )
    unidade = EscolaAbertaUnidadeParticipante.objects.create(
        escola_aberta=escola_aberta,
        lote=setup_escola_aberta_data["lote"],
        unidade_educacional=setup_escola_aberta_data["escola_1"],
    )
    unidade.tipos_alimentacao.add(setup_escola_aberta_data["tipo_alim_1"])

    payload = {
        "recorrencias": {
            "data_inicial": "10/10/2026",
            "data_final": "20/10/2026",
            "dias_semana": ["0", "6"],
        },
        "unidades_participantes": [
            {
                "lote": str(setup_escola_aberta_data["lote"].uuid),
                "unidade_educacional": str(setup_escola_aberta_data["escola_1"].uuid),
                "tipos_alimentacao": [
                    str(setup_escola_aberta_data["tipo_alim_1"].uuid)
                ],
                "num_participantes": 30,
            }
        ],
    }
    serializer = EscolaAbertaCreateSerializer(instance=escola_aberta, data=payload)
    assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db
def test_unidade_participante_num_participantes_obrigatorio(setup_escola_aberta_data):
    """Garante que num_participantes não pode ser nulo ou menor que 1."""
    dados_invalidos = {
        "lote": str(setup_escola_aberta_data["lote"].uuid),
        "unidade_educacional": str(setup_escola_aberta_data["escola_1"].uuid),
        "tipos_alimentacao": [str(setup_escola_aberta_data["tipo_alim_1"].uuid)],
        "num_participantes": 0,
    }
    serializer = EscolaAbertaUnidadeParticipanteCreateSerializer(data=dados_invalidos)
    assert not serializer.is_valid()
    assert "num_participantes" in serializer.errors


@pytest.mark.django_db
def test_unidade_participante_read_serializer_lote_nome_com_iniciais(setup_escola_aberta_data):
    """Valida se lote_nome formata corretamente como 'nome - iniciais'."""
    from src.escola_aberta.api.serializers import EscolaAbertaUnidadeParticipanteReadSerializer

    escola_aberta = EscolaAberta.objects.create(
        data_inicial="2026-10-10",
        data_final="2026-10-20",
        dias_semana=["0"],
    )
    unidade = EscolaAbertaUnidadeParticipante.objects.create(
        escola_aberta=escola_aberta,
        lote=setup_escola_aberta_data["lote"],
        unidade_educacional=setup_escola_aberta_data["escola_1"],
        num_participantes=25,
    )

    serializer = EscolaAbertaUnidadeParticipanteReadSerializer(instance=unidade)
    esperado = (
        f"{setup_escola_aberta_data['lote'].nome} - "
        f"{setup_escola_aberta_data['lote'].diretoria_regional.iniciais}"
    )
    assert serializer.data["lote_nome"] == esperado
