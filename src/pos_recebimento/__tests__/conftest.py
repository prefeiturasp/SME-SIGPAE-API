import datetime

import pytest
from model_bakery import baker

from src.dados_comuns import constants
from src.dados_comuns.fluxo_status import FichaDeRecebimentoWorkflow
from src.pre_recebimento.cronograma_entrega.fixtures.factories.cronograma_factory import (
    CronogramaFactory,
    EtapasDoCronogramaFactory,
)
from src.recebimento.fixtures.factories.ficha_de_recebimento_factory import (
    FichaDeRecebimentoFactory,
)
from src.terceirizada.fixtures.factories.terceirizada_factory import (
    ContratoFactory,
    EmpresaFactory,
)


@pytest.fixture
def empresa():
    return EmpresaFactory()


@pytest.fixture
def contrato(empresa):
    return ContratoFactory(terceirizada=empresa)


@pytest.fixture
def cronograma(empresa, contrato):
    return CronogramaFactory(contrato=contrato, empresa=empresa)


@pytest.fixture
def ficha_assinada():
    """Ficha de recebimento com status 'Assinado CODAE' vinculada a um
    cronograma/empresa próprios (independentes das fixtures empresa/contrato)."""
    empresa = EmpresaFactory()
    contrato = ContratoFactory(terceirizada=empresa)
    cronograma = CronogramaFactory(contrato=contrato, empresa=empresa)
    etapa = EtapasDoCronogramaFactory(cronograma=cronograma)
    return FichaDeRecebimentoFactory(
        etapa=etapa, status=FichaDeRecebimentoWorkflow.ASSINADA
    )


@pytest.fixture
def usuario_fiscal(django_user_model):
    """Usuário com perfil DILOG_QUALIDADE vinculado à CODAE."""
    email = "fiscal@test.com"
    user = django_user_model.objects.create_user(
        username=email,
        password=constants.DJANGO_ADMIN_PASSWORD,
        email=email,
        registro_funcional="1234567",
        nome="Fiscal de Qualidade",
    )
    perfil = baker.make("Perfil", nome=constants.DILOG_QUALIDADE, ativo=True)
    codae = baker.make("Codae")
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    return user


@pytest.fixture
def tres_fiscais(django_user_model):
    """Três usuários com perfil DILOG_QUALIDADE para o cadastro do termo."""
    fiscais = []
    for i in range(1, 4):
        email = f"fiscal{i}@test.com"
        user = django_user_model.objects.create_user(
            username=email,
            password=constants.DJANGO_ADMIN_PASSWORD,
            email=email,
            registro_funcional=f"12345{i}",
            nome=f"Fiscal de Qualidade {i}",
        )
        perfil = baker.make("Perfil", nome=constants.DILOG_QUALIDADE, ativo=True)
        codae = baker.make("Codae")
        baker.make(
            "Vinculo",
            usuario=user,
            instituicao=codae,
            perfil=perfil,
            data_inicial=datetime.date.today(),
            ativo=True,
        )
        fiscais.append(user)
    return fiscais


@pytest.fixture
def payload_termo(ficha_assinada, tres_fiscais):
    """Payload válido para criação do Termo de Recebimento Definitivo."""
    cronograma = ficha_assinada.etapa.cronograma
    return {
        "empresa": str(cronograma.empresa.uuid),
        "contrato": str(cronograma.contrato.uuid),
        "cronogramas": [
            {
                "cronograma": str(cronograma.uuid),
                "valor_contrato": "150000.00",
                "quantidade_total_recebida": "1234.56",
            }
        ],
        "fiscal_1": str(tres_fiscais[0].uuid),
        "fiscal_2": str(tres_fiscais[1].uuid),
        "fiscal_3": str(tres_fiscais[2].uuid),
        "texto_termo": "<p>Termo de Recebimento Definitivo</p>",
    }
