import datetime

import pytest
from django.utils import timezone
from model_bakery import baker
from rest_framework import status
from uuid import uuid4

from src.dados_comuns import constants as const
from src.pos_recebimento.models import (
    CronogramaTermoRecebimentoDefinitivo,
    TermoRecebimentoDefinitivo,
)
from src.pre_recebimento.cronograma_entrega.fixtures.factories.cronograma_factory import (
    CronogramaFactory,
)
from src.terceirizada.fixtures.factories.terceirizada_factory import (
    ContratoFactory,
    EmpresaFactory,
)
from src.terceirizada.models import Terceirizada

pytestmark = pytest.mark.django_db

DATA_CADASTRO_TERMO = datetime.datetime(2026, 3, 15, 12, 0)


def _cria_client_empresa(django_user_model, client, empresa, nome_perfil):
    """Cliente autenticado com vínculo na empresa e perfil informados."""
    email = f"{nome_perfil.lower()}@test.com"
    user = django_user_model.objects.create_user(
        username=email,
        password=const.DJANGO_ADMIN_PASSWORD,
        email=email,
    )
    perfil = baker.make("Perfil", nome=nome_perfil, ativo=True)
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=empresa,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    client.login(username=email, password=const.DJANGO_ADMIN_PASSWORD)
    return client


@pytest.fixture
def empresa_fornecedora():
    return EmpresaFactory(
        nome_fantasia="Fornecedor Alimentos",
        tipo_servico=Terceirizada.FORNECEDOR,
    )


@pytest.fixture
def contrato_fornecedor(empresa_fornecedora):
    return ContratoFactory(terceirizada=empresa_fornecedora, numero="25/SME/2026")


@pytest.fixture
def client_admin_empresa(client, django_user_model, empresa_fornecedora):
    return _cria_client_empresa(
        django_user_model, client, empresa_fornecedora, const.ADMINISTRADOR_EMPRESA
    )


@pytest.fixture
def client_usuario_empresa(client, django_user_model, empresa_fornecedora):
    return _cria_client_empresa(
        django_user_model, client, empresa_fornecedora, const.USUARIO_EMPRESA
    )


@pytest.fixture
def client_usuario_empresa_nao_fornecedora(client, django_user_model):
    empresa = EmpresaFactory(tipo_servico=Terceirizada.TERCEIRIZADA)
    return _cria_client_empresa(
        django_user_model, client, empresa, const.USUARIO_EMPRESA
    )


def _cria_termo(
    empresa,
    contrato,
    django_user_model,
    status=TermoRecebimentoDefinitivo.ENVIADO_FORNECEDOR,
    data_cadastro=DATA_CADASTRO_TERMO,
    numeros_cronogramas=(),
):
    """Termo persistido diretamente, com data de cadastro fixa.

    ``criado_em`` é ``auto_now_add``, então só pode ser fixado via UPDATE.
    """
    sufixo = uuid4().hex[:8]
    fiscais = [
        django_user_model.objects.create_user(
            username=f"fiscal{indice}_{sufixo}@test.com",
            email=f"fiscal{indice}_{sufixo}@test.com",
            password=const.DJANGO_ADMIN_PASSWORD,
            registro_funcional=f"1234{indice}{sufixo[:2]}",
        )
        for indice in (1, 2, 3)
    ]
    termo = TermoRecebimentoDefinitivo.objects.create(
        empresa=empresa,
        contrato=contrato,
        fiscal_1=fiscais[0],
        fiscal_2=fiscais[1],
        fiscal_3=fiscais[2],
        texto_termo="<p>Termo de Recebimento Definitivo</p>",
        status=status,
    )
    for numero in numeros_cronogramas:
        CronogramaTermoRecebimentoDefinitivo.objects.create(
            termo=termo,
            cronograma=CronogramaFactory(contrato=contrato, empresa=empresa, numero=numero),
            quantidade_total_recebida="1234.56",
        )
    TermoRecebimentoDefinitivo.objects.filter(pk=termo.pk).update(
        criado_em=timezone.make_aware(data_cadastro)
    )
    termo.refresh_from_db()
    return termo


def test_termo_list_liberado_para_administrador_empresa(
    client_admin_empresa,
    empresa_fornecedora,
    contrato_fornecedor,
    django_user_model,
):
    termo = _cria_termo(
        empresa_fornecedora, contrato_fornecedor, django_user_model
    )

    response = client_admin_empresa.get("/pos-recebimento/termos/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["uuid"] == str(termo.uuid)


def test_termo_list_liberado_para_usuario_empresa(
    client_usuario_empresa,
    empresa_fornecedora,
    contrato_fornecedor,
    django_user_model,
):
    termo = _cria_termo(
        empresa_fornecedora, contrato_fornecedor, django_user_model
    )

    response = client_usuario_empresa.get("/pos-recebimento/termos/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["uuid"] == str(termo.uuid)


def test_termo_list_negado_para_usuario_empresa_nao_fornecedora(
    client_usuario_empresa_nao_fornecedora,
    empresa_fornecedora,
    contrato_fornecedor,
    django_user_model,
):
    _cria_termo(empresa_fornecedora, contrato_fornecedor, django_user_model)

    response = client_usuario_empresa_nao_fornecedora.get(
        "/pos-recebimento/termos/"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_termo_list_escopado_a_empresa_e_status_do_fornecedor(
    client_admin_empresa,
    empresa_fornecedora,
    contrato_fornecedor,
    django_user_model,
):
    termo_recebido = _cria_termo(
        empresa_fornecedora,
        contrato_fornecedor,
        django_user_model,
        status=TermoRecebimentoDefinitivo.ENVIADO_FISCAIS,
        data_cadastro=datetime.datetime(2026, 3, 15, 12, 0),
    )
    termo_assinado = _cria_termo(
        empresa_fornecedora,
        contrato_fornecedor,
        django_user_model,
        status=TermoRecebimentoDefinitivo.ASSINADO_FORNECEDOR,
        data_cadastro=datetime.datetime(2026, 3, 16, 12, 0),
    )
    _cria_termo(
        empresa_fornecedora,
        contrato_fornecedor,
        django_user_model,
        status=TermoRecebimentoDefinitivo.RASCUNHO,
        data_cadastro=datetime.datetime(2026, 3, 17, 12, 0),
    )
    _cria_termo(
        EmpresaFactory(tipo_servico=Terceirizada.FORNECEDOR),
        ContratoFactory(),
        django_user_model,
    )

    response = client_admin_empresa.get("/pos-recebimento/termos/")

    assert response.status_code == status.HTTP_200_OK
    uuids = [resultado["uuid"] for resultado in response.json()["results"]]
    assert uuids == [str(termo_assinado.uuid), str(termo_recebido.uuid)]


def test_termo_list_retorna_dados_do_grid_do_fornecedor(
    client_admin_empresa,
    empresa_fornecedora,
    contrato_fornecedor,
    django_user_model,
):
    termo = _cria_termo(
        empresa_fornecedora,
        contrato_fornecedor,
        django_user_model,
        status=TermoRecebimentoDefinitivo.ASSINADO_FORNECEDOR,
        numeros_cronogramas=("111/2026", "222/2026"),
    )
    produtos = [cronograma.ficha_tecnica.produto for cronograma in termo.cronogramas.all()]
    produtos[0].nome = "BISCOITO DE POLVILHO DOCE"
    produtos[1].nome = "LEITE EM PÓ INTEGRAL"
    for produto in produtos:
        produto.save()

    response = client_admin_empresa.get("/pos-recebimento/termos/")

    assert response.status_code == status.HTTP_200_OK
    resultado = response.json()["results"][0]
    assert resultado["numero_contrato"] == "25/SME/2026"
    assert resultado["produtos"] == [
        "BISCOITO DE POLVILHO DOCE",
        "LEITE EM PÓ INTEGRAL",
    ]
    assert resultado["data_cadastro"] == "15/03/2026"
    assert resultado["status"] == TermoRecebimentoDefinitivo.ASSINADO_FORNECEDOR


def test_termo_list_filtra_por_numero_contrato(
    client_admin_empresa,
    empresa_fornecedora,
    contrato_fornecedor,
    django_user_model,
):
    termo = _cria_termo(empresa_fornecedora, contrato_fornecedor, django_user_model)
    _cria_termo(
        empresa_fornecedora,
        ContratoFactory(terceirizada=empresa_fornecedora, numero="99/SME/2025"),
        django_user_model,
    )

    response = client_admin_empresa.get(
        "/pos-recebimento/termos/", {"numero_contrato": "25/SME"}
    )

    assert response.status_code == status.HTTP_200_OK
    uuids = [resultado["uuid"] for resultado in response.json()["results"]]
    assert uuids == [str(termo.uuid)]


def test_termo_list_filtra_por_produto(
    client_admin_empresa,
    empresa_fornecedora,
    contrato_fornecedor,
    django_user_model,
):
    termo = _cria_termo(
        empresa_fornecedora,
        contrato_fornecedor,
        django_user_model,
        numeros_cronogramas=("111/2026",),
    )
    termo_outro_produto = _cria_termo(
        empresa_fornecedora,
        ContratoFactory(terceirizada=empresa_fornecedora),
        django_user_model,
        numeros_cronogramas=("222/2026",),
    )
    produto = termo.cronogramas.first().ficha_tecnica.produto
    produto.nome = "BISCOITO DE POLVILHO"
    produto.save()

    response = client_admin_empresa.get(
        "/pos-recebimento/termos/", {"nome_produto": "BISCOITO"}
    )

    assert response.status_code == status.HTTP_200_OK
    uuids = [resultado["uuid"] for resultado in response.json()["results"]]
    assert uuids == [str(termo.uuid)]
    assert str(termo_outro_produto.uuid) not in uuids


def test_termo_list_filtra_por_status(
    client_admin_empresa,
    empresa_fornecedora,
    contrato_fornecedor,
    django_user_model,
):
    _cria_termo(
        empresa_fornecedora,
        contrato_fornecedor,
        django_user_model,
        status=TermoRecebimentoDefinitivo.ENVIADO_FORNECEDOR,
    )
    termo_assinado = _cria_termo(
        empresa_fornecedora,
        contrato_fornecedor,
        django_user_model,
        status=TermoRecebimentoDefinitivo.ASSINADO_FORNECEDOR,
    )

    response = client_admin_empresa.get(
        "/pos-recebimento/termos/",
        {"status": TermoRecebimentoDefinitivo.ASSINADO_FORNECEDOR},
    )

    assert response.status_code == status.HTTP_200_OK
    uuids = [resultado["uuid"] for resultado in response.json()["results"]]
    assert uuids == [str(termo_assinado.uuid)]


def test_termo_list_filtra_por_status_fornecedor_recebido(
    client_admin_empresa,
    empresa_fornecedora,
    contrato_fornecedor,
    django_user_model,
):
    termo_fiscais = _cria_termo(
        empresa_fornecedora,
        contrato_fornecedor,
        django_user_model,
        status=TermoRecebimentoDefinitivo.ENVIADO_FISCAIS,
        data_cadastro=datetime.datetime(2026, 3, 15, 12, 0),
    )
    termo_fornecedor = _cria_termo(
        empresa_fornecedora,
        contrato_fornecedor,
        django_user_model,
        status=TermoRecebimentoDefinitivo.ENVIADO_FORNECEDOR,
        data_cadastro=datetime.datetime(2026, 3, 16, 12, 0),
    )
    _cria_termo(
        empresa_fornecedora,
        contrato_fornecedor,
        django_user_model,
        status=TermoRecebimentoDefinitivo.ASSINADO_FORNECEDOR,
        data_cadastro=datetime.datetime(2026, 3, 17, 12, 0),
    )

    response = client_admin_empresa.get(
        "/pos-recebimento/termos/", {"status_fornecedor": "RECEBIDO"}
    )

    assert response.status_code == status.HTTP_200_OK
    uuids = [resultado["uuid"] for resultado in response.json()["results"]]
    assert uuids == [str(termo_fornecedor.uuid), str(termo_fiscais.uuid)]


def test_termo_list_filtra_por_status_fornecedor_assinado(
    client_admin_empresa,
    empresa_fornecedora,
    contrato_fornecedor,
    django_user_model,
):
    _cria_termo(
        empresa_fornecedora,
        contrato_fornecedor,
        django_user_model,
        status=TermoRecebimentoDefinitivo.ENVIADO_FORNECEDOR,
    )
    termo_assinado = _cria_termo(
        empresa_fornecedora,
        contrato_fornecedor,
        django_user_model,
        status=TermoRecebimentoDefinitivo.ASSINADO_FORNECEDOR,
        data_cadastro=datetime.datetime(2026, 3, 16, 12, 0),
    )

    response = client_admin_empresa.get(
        "/pos-recebimento/termos/", {"status_fornecedor": "ASSINADO"}
    )

    assert response.status_code == status.HTTP_200_OK
    uuids = [resultado["uuid"] for resultado in response.json()["results"]]
    assert uuids == [str(termo_assinado.uuid)]


def test_termo_list_filtra_por_periodo_de_cadastro(
    client_admin_empresa,
    empresa_fornecedora,
    contrato_fornecedor,
    django_user_model,
):
    _cria_termo(
        empresa_fornecedora,
        contrato_fornecedor,
        django_user_model,
        data_cadastro=datetime.datetime(2026, 1, 10, 12, 0),
    )
    termo_periodo = _cria_termo(
        empresa_fornecedora,
        contrato_fornecedor,
        django_user_model,
        data_cadastro=datetime.datetime(2026, 3, 15, 12, 0),
    )

    response = client_admin_empresa.get(
        "/pos-recebimento/termos/",
        {"data_inicial": "2026-03-01", "data_final": "2026-03-31"},
    )

    assert response.status_code == status.HTTP_200_OK
    uuids = [resultado["uuid"] for resultado in response.json()["results"]]
    assert uuids == [str(termo_periodo.uuid)]


def test_termo_retrieve_liberado_para_fornecedor(
    client_usuario_empresa,
    empresa_fornecedora,
    contrato_fornecedor,
    django_user_model,
):
    termo = _cria_termo(
        empresa_fornecedora,
        contrato_fornecedor,
        django_user_model,
        status=TermoRecebimentoDefinitivo.ASSINADO_FORNECEDOR,
    )

    response = client_usuario_empresa.get(f"/pos-recebimento/termos/{termo.uuid}/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["uuid"] == str(termo.uuid)


def test_termo_retrieve_de_outra_empresa_retorna_404(
    client_admin_empresa,
    django_user_model,
):
    termo_outra_empresa = _cria_termo(
        EmpresaFactory(tipo_servico=Terceirizada.FORNECEDOR),
        ContratoFactory(),
        django_user_model,
    )

    response = client_admin_empresa.get(
        f"/pos-recebimento/termos/{termo_outra_empresa.uuid}/"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
