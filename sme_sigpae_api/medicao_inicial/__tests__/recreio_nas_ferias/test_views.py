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
    RecreioNasFeriasUnidadeTipoAlimentacao,
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
def test_criar_recreio_sucesso(client_autenticado_coordenador_codae, setup_data):
    """Testa a criação de um Recreio com sucesso"""
    RecreioNasFerias.objects.all().delete()
    RecreioNasFeriasUnidadeParticipante.objects.all().delete()

    data = {
        "titulo": "Recreio Novo",
        "data_inicio": "2025-10-27",
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
                "tipos_alimentacao_colaboradores": [
                    str(setup_data["tipo_alim_2"].uuid)
                ],
                "tipos_alimentacao_infantil": [],
            }
        ],
    }

    response = client_autenticado_coordenador_codae.post(
        setup_data["list_url"], data, content_type="application/json"
    )

    if response.status_code != status.HTTP_201_CREATED:
        print(f"Erro: {response.data}")

    assert response.status_code == status.HTTP_201_CREATED
    assert RecreioNasFerias.objects.count() == 1
    assert RecreioNasFeriasUnidadeParticipante.objects.count() == 1

    recreio = RecreioNasFerias.objects.first()
    assert recreio.titulo == "Recreio Novo"
    assert recreio.unidades_participantes.count() == 1


@pytest.mark.django_db
def test_criar_recreio_sem_titulo(client_autenticado_coordenador_codae, setup_data):
    """Testa a criação de um Recreio sem título (deve falhar)"""
    data = {
        "data_inicio": "2025-10-27",
        "data_fim": "2025-11-27",
        "unidades_participantes": [],
    }

    response = client_autenticado_coordenador_codae.post(
        setup_data["list_url"], data, content_type="application/json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "titulo" in response.data


@pytest.mark.django_db
def test_criar_recreio_com_multiplas_unidades(
    client_autenticado_coordenador_codae, setup_data
):
    """Testa a criação de um Recreio com múltiplas unidades"""
    RecreioNasFerias.objects.all().delete()
    RecreioNasFeriasUnidadeParticipante.objects.all().delete()

    escola2 = Escola.objects.create(
        nome="Escola Teste 2",
        codigo_eol="654321",
        diretoria_regional=setup_data["diretoria_regional"],
        tipo_unidade=setup_data["tipo_unidade"],
    )

    data = {
        "titulo": "Recreio Múltiplas Unidades",
        "data_inicio": "2025-10-27",
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
            },
            {
                "lote": str(setup_data["lote"].uuid),
                "unidade_educacional": str(escola2.uuid),
                "num_inscritos": 30,
                "num_colaboradores": 5,
                "liberar_medicao": False,
                "cei_ou_emei": "EMEI",
                "tipos_alimentacao_inscritos": [str(setup_data["tipo_alim_2"].uuid)],
                "tipos_alimentacao_colaboradores": [],
                "tipos_alimentacao_infantil": [],
            },
        ],
    }

    response = client_autenticado_coordenador_codae.post(
        setup_data["list_url"], data, content_type="application/json"
    )

    if response.status_code != status.HTTP_201_CREATED:
        print(f"Erro: {response.data}")

    assert response.status_code == status.HTTP_201_CREATED
    assert RecreioNasFeriasUnidadeParticipante.objects.count() == 2


@pytest.mark.django_db
def test_detalhar_recreio(client_autenticado_coordenador_codae, setup_data):
    """Testa a visualização de detalhes de um Recreio"""
    recreio = RecreioNasFerias.objects.create(
        titulo="Recreio Teste",
        data_inicio=date(2025, 10, 27),
        data_fim=date(2025, 11, 27),
    )

    url = reverse("recreio-nas-ferias-detail", kwargs={"uuid": recreio.uuid})
    response = client_autenticado_coordenador_codae.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["titulo"] == "Recreio Teste"
    assert response.data["uuid"] == str(recreio.uuid)


@pytest.mark.django_db
def test_criar_recreio_com_uuid_invalido(
    client_autenticado_coordenador_codae, setup_data
):
    """Testa a criação com UUID inválido (deve falhar)"""
    data = {
        "titulo": "Recreio Teste",
        "data_inicio": "2025-10-27",
        "data_fim": "2025-11-27",
        "unidades_participantes": [
            {
                "lote": "uuid-invalido",
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


@pytest.mark.django_db
def test_listar_recreios(client_autenticado_coordenador_codae, setup_data):
    recreio1 = RecreioNasFerias.objects.create(
        titulo="Recreio 1", data_inicio=date(2025, 10, 1), data_fim=date(2025, 10, 10)
    )
    recreio2 = RecreioNasFerias.objects.create(
        titulo="Recreio 2", data_inicio=date(2025, 11, 1), data_fim=date(2025, 11, 10)
    )

    unidade1 = RecreioNasFeriasUnidadeParticipante.objects.create(
        recreio_nas_ferias=recreio1,
        lote=setup_data["lote"],
        unidade_educacional=setup_data["escola"],
        num_inscritos=30,
        num_colaboradores=5,
        liberar_medicao=True,
        cei_ou_emei="CEI",
    )
    RecreioNasFeriasUnidadeTipoAlimentacao.objects.create(
        recreio_ferias_unidade=unidade1,
        tipo_alimentacao=setup_data["tipo_alim_1"],
        categoria=setup_data["cat_inscritos"],
    )

    unidade2 = RecreioNasFeriasUnidadeParticipante.objects.create(
        recreio_nas_ferias=recreio2,
        lote=setup_data["lote"],
        unidade_educacional=setup_data["escola"],
        num_inscritos=40,
        num_colaboradores=8,
        liberar_medicao=False,
        cei_ou_emei="EMEI",
    )
    RecreioNasFeriasUnidadeTipoAlimentacao.objects.create(
        recreio_ferias_unidade=unidade2,
        tipo_alimentacao=setup_data["tipo_alim_2"],
        categoria=setup_data["cat_inscritos"],
    )

    response = client_autenticado_coordenador_codae.get(setup_data["list_url"])
    assert response.status_code == status.HTTP_200_OK

    results = (
        response.data.get("results")
        if isinstance(response.data, dict) and "results" in response.data
        else response.data
    )

    assert (
        response.data.get("count") if isinstance(response.data, dict) else len(results)
    ) == 2
    assert len(results) == 2

    titulos = [item["titulo"] for item in results]
    assert "Recreio 1" in titulos
    assert "Recreio 2" in titulos

    primeiro_item = results[0]
    assert "uuid" in primeiro_item
    assert "titulo" in primeiro_item
    assert "data_inicio" in primeiro_item
    assert "data_fim" in primeiro_item
    assert "unidades_participantes" in primeiro_item


@pytest.mark.django_db
def test_atualizar_recreio_completo(client_autenticado_coordenador_codae, setup_data):
    recreio = RecreioNasFerias.objects.create(
        titulo="Antigo Título",
        data_inicio=date(2025, 10, 1),
        data_fim=date(2025, 10, 10),
    )

    unidade_antiga = RecreioNasFeriasUnidadeParticipante.objects.create(
        recreio_nas_ferias=recreio,
        lote=setup_data["lote"],
        unidade_educacional=setup_data["escola"],
        num_inscritos=20,
        num_colaboradores=3,
        liberar_medicao=True,
        cei_ou_emei="CEI",
    )
    RecreioNasFeriasUnidadeTipoAlimentacao.objects.create(
        recreio_ferias_unidade=unidade_antiga,
        tipo_alimentacao=setup_data["tipo_alim_1"],
        categoria=setup_data["cat_inscritos"],
    )

    nova_escola = Escola.objects.create(
        nome="Nova Escola",
        codigo_eol="987654",
        diretoria_regional=setup_data["diretoria_regional"],
        tipo_unidade=setup_data["tipo_unidade"],
    )

    data = {
        "titulo": "Novo Título",
        "data_inicio": "2025-11-01",
        "data_fim": "2025-11-10",
        "unidades_participantes": [
            {
                "lote": str(setup_data["lote"].uuid),
                "unidade_educacional": str(nova_escola.uuid),
                "num_inscritos": 60,
                "num_colaboradores": 12,
                "liberar_medicao": False,
                "cei_ou_emei": "EMEI",
                "tipos_alimentacao_inscritos": [str(setup_data["tipo_alim_2"].uuid)],
                "tipos_alimentacao_colaboradores": [],
                "tipos_alimentacao_infantil": [],
            }
        ],
    }

    url = reverse("recreio-nas-ferias-detail", kwargs={"uuid": recreio.uuid})
    response = client_autenticado_coordenador_codae.put(
        url, data, content_type="application/json"
    )

    assert response.status_code == status.HTTP_200_OK

    recreio.refresh_from_db()
    assert recreio.titulo == "Novo Título"
    assert str(recreio.data_inicio) == "2025-11-01"
    assert str(recreio.data_fim) == "2025-11-10"

    assert recreio.unidades_participantes.count() == 1
    unidade_atualizada = recreio.unidades_participantes.first()
    assert unidade_atualizada.unidade_educacional == nova_escola
    assert unidade_atualizada.num_inscritos == 60
    assert unidade_atualizada.liberar_medicao is False
    assert unidade_atualizada.cei_ou_emei == "EMEI"

    exists = RecreioNasFeriasUnidadeTipoAlimentacao.objects.filter(
        recreio_ferias_unidade=unidade_atualizada,
        tipo_alimentacao=setup_data["tipo_alim_2"],
        categoria=setup_data["cat_inscritos"],
    ).exists()
    assert exists


@pytest.mark.django_db
def test_atualizar_recreio_parcial_mantem_unidades(
    client_autenticado_coordenador_codae, setup_data
):
    recreio = RecreioNasFerias.objects.create(
        titulo="Título Antigo",
        data_inicio=date(2025, 10, 1),
        data_fim=date(2025, 10, 10),
    )

    # Criar unidade + relação de tipo de alimentação
    unidade = RecreioNasFeriasUnidadeParticipante.objects.create(
        recreio_nas_ferias=recreio,
        lote=setup_data["lote"],
        unidade_educacional=setup_data["escola"],
        num_inscritos=25,
        num_colaboradores=4,
        liberar_medicao=True,
        cei_ou_emei="CEI",
    )
    RecreioNasFeriasUnidadeTipoAlimentacao.objects.create(
        recreio_ferias_unidade=unidade,
        tipo_alimentacao=setup_data["tipo_alim_1"],
        categoria=setup_data["cat_inscritos"],
    )

    data = {
        "titulo": "Título Atualizado",
    }

    url = reverse("recreio-nas-ferias-detail", kwargs={"uuid": recreio.uuid})
    response = client_autenticado_coordenador_codae.patch(
        url, data, content_type="application/json"
    )

    assert response.status_code == status.HTTP_200_OK

    recreio.refresh_from_db()
    assert recreio.titulo == "Título Atualizado"

    # As unidades devem ter sido mantidas
    assert recreio.unidades_participantes.count() == 1
    unidade_atual = recreio.unidades_participantes.first()
    assert unidade_atual.num_inscritos == 25
    assert unidade_atual.num_colaboradores == 4
    assert unidade_atual.liberar_medicao is True
    assert unidade_atual.cei_ou_emei == "CEI"

    # A relação de tipos de alimentação também deve permanecer
    relacoes = RecreioNasFeriasUnidadeTipoAlimentacao.objects.filter(
        recreio_ferias_unidade=unidade_atual
    )
    assert relacoes.count() == 1
    rel = relacoes.first()
    assert rel.tipo_alimentacao == setup_data["tipo_alim_1"]
    assert rel.categoria == setup_data["cat_inscritos"]
