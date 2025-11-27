from datetime import date

import pytest
from django.urls import reverse
from rest_framework import status

from sme_sigpae_api.cardapio.base.models import TipoAlimentacao
from sme_sigpae_api.escola.models import (
    DiretoriaRegional,
    Escola,
    Lote,
    TipoUnidadeEscolar,
)
from sme_sigpae_api.medicao_inicial.recreio_nas_ferias.models import (
    CategoriaAlimentacao,
    RecreioNasFerias,
    RecreioNasFeriasUnidadeParticipante,
)


@pytest.fixture
def setup_data():
    """Configuração inicial para os testes"""
    RecreioNasFerias.objects.all().delete()
    RecreioNasFeriasUnidadeParticipante.objects.all().delete()
    CategoriaAlimentacao.objects.all().delete()
    TipoAlimentacao.objects.all().delete()
    Escola.objects.all().delete()
    Lote.objects.all().delete()
    DiretoriaRegional.objects.all().delete()
    TipoUnidadeEscolar.objects.all().delete()

    cat_inscritos, _ = CategoriaAlimentacao.objects.get_or_create(nome="Inscritos")
    cat_colaboradores, _ = CategoriaAlimentacao.objects.get_or_create(
        nome="Colaboradores"
    )
    cat_infantil, _ = CategoriaAlimentacao.objects.get_or_create(nome="Infantil")

    tipo_unidade = TipoUnidadeEscolar.objects.create(iniciais="CEI")
    diretoria_regional = DiretoriaRegional.objects.create(nome="DRE Teste")
    lote = Lote.objects.create(nome="Lote 01")
    escola = Escola.objects.create(
        nome="Escola Teste",
        codigo_eol="123456",
        diretoria_regional=diretoria_regional,
        tipo_unidade=tipo_unidade,
    )

    tipo_alim_1 = TipoAlimentacao.objects.create(nome="Lanche")
    tipo_alim_2 = TipoAlimentacao.objects.create(nome="Almoço")

    list_url = reverse("recreio-nas-ferias-list")

    return {
        "cat_inscritos": cat_inscritos,
        "cat_colaboradores": cat_colaboradores,
        "cat_infantil": cat_infantil,
        "tipo_unidade": tipo_unidade,
        "diretoria_regional": diretoria_regional,
        "lote": lote,
        "escola": escola,
        "tipo_alim_1": tipo_alim_1,
        "tipo_alim_2": tipo_alim_2,
        "list_url": list_url,
    }


@pytest.mark.django_db
def test_criar_recreio_data_fim_anterior_data_inicio(
    client_autenticado_coordenador_codae, setup_data
):
    """Testa a criação de um Recreio com data_fim anterior a data_inicio (deve falhar)"""
    data = {
        "titulo": "Recreio Teste",
        "data_inicio": "2025-11-27",
        "data_fim": "2025-10-27",
        "unidades_participantes": [
            {
                "lote": str(setup_data["lote"].uuid),
                "unidade_educacional": str(setup_data["escola"].uuid),
                "num_inscritos": 50,
                "num_colaboradores": 10,
                "liberar_medicao": True,
                "cei_ou_emei": "CEI",
                "tipos_alimentacao_inscritos": [str(setup_data["tipo_alim_1"].uuid)],
                "tipos_alimentacao_colaboradores": [],
                "tipos_alimentacao_infantil": [],
            }
        ],
    }

    response = client_autenticado_coordenador_codae.post(
        setup_data["list_url"], data, content_type="application/json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "data_fim" in response.data
    assert "data de fim não pode ser anterior" in str(response.data["data_fim"]).lower()


@pytest.mark.django_db
def test_criar_recreio_datas_iguais(client_autenticado_coordenador_codae, setup_data):
    """Testa a criação de um Recreio com data_inicio igual a data_fim (deve passar)"""
    RecreioNasFerias.objects.all().delete()

    data = {
        "titulo": "Recreio Um Dia",
        "data_inicio": "2025-11-27",
        "data_fim": "2025-11-27",
        "unidades_participantes": [
            {
                "lote": str(setup_data["lote"].uuid),
                "unidade_educacional": str(setup_data["escola"].uuid),
                "num_inscritos": 50,
                "num_colaboradores": 10,
                "liberar_medicao": True,
                "cei_ou_emei": "CEI",
                "tipos_alimentacao_inscritos": [str(setup_data["tipo_alim_1"].uuid)],
                "tipos_alimentacao_colaboradores": [],
                "tipos_alimentacao_infantil": [],
            }
        ],
    }

    response = client_autenticado_coordenador_codae.post(
        setup_data["list_url"], data, content_type="application/json"
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert RecreioNasFerias.objects.count() == 1
