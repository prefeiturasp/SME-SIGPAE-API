import datetime
from types import SimpleNamespace

import pytest
from django.utils import timezone
from model_bakery import baker

from src.dados_comuns import constants
from src.dados_comuns.fluxo_status import FichaDeRecebimentoWorkflow
from src.pos_recebimento.models import (
    CronogramaTermoRecebimentoDefinitivo,
    TermoRecebimentoDefinitivo,
)
from src.pre_recebimento.cronograma_entrega.fixtures.factories.cronograma_factory import (
    CronogramaFactory,
    EtapasDoCronogramaFactory,
)
from src.pre_recebimento.ficha_tecnica.fixtures.factories.ficha_tecnica_do_produto_factory import (
    FichaTecnicaFactory,
)
from src.produto.models import NomeDeProdutoEdital
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
                "quantidade_total_recebida": "1234.56",
            }
        ],
        "fiscal_1": str(tres_fiscais[0].uuid),
        "fiscal_2": str(tres_fiscais[1].uuid),
        "fiscal_3": str(tres_fiscais[2].uuid),
        "valor_contrato": "150000.00",
        "texto_termo": "<p>Termo de Recebimento Definitivo</p>",
    }


DATA_CADASTRO_TERMO = datetime.datetime(2026, 3, 15, 12, 0)


def _cria_termo(
    empresa,
    contrato,
    fiscais,
    numeros_cronogramas=(),
    data_cadastro=DATA_CADASTRO_TERMO,
):
    """Termo com data de cadastro fixa e os cronogramas informados.

    ``criado_em`` é ``auto_now_add``, então só pode ser fixado via UPDATE.
    """
    termo = TermoRecebimentoDefinitivo.objects.create(
        empresa=empresa,
        contrato=contrato,
        fiscal_1=fiscais[0],
        fiscal_2=fiscais[1],
        fiscal_3=fiscais[2],
        valor_contrato="150000.00",
        texto_termo="<p>Termo de Recebimento Definitivo</p>",
        status=TermoRecebimentoDefinitivo.ENVIADO_FISCAIS,
    )
    for numero in numeros_cronogramas:
        CronogramaTermoRecebimentoDefinitivo.objects.create(
            termo=termo,
            cronograma=CronogramaFactory(
                contrato=contrato, empresa=empresa, numero=numero
            ),
            quantidade_total_recebida="1234.56",
        )
    TermoRecebimentoDefinitivo.objects.filter(pk=termo.pk).update(
        criado_em=timezone.make_aware(data_cadastro)
    )
    termo.refresh_from_db()
    return termo


@pytest.fixture
def termo_listagem(empresa, contrato, tres_fiscais):
    """Termo com dois cronogramas, para a listagem."""
    return _cria_termo(empresa, contrato, tres_fiscais, ("111/2026", "222/2026"))


@pytest.fixture
def termo_listagem_sem_cronogramas(empresa, contrato, tres_fiscais):
    return _cria_termo(empresa, contrato, tres_fiscais)


@pytest.fixture
def termos_listagem_ordenados(empresa, contrato, tres_fiscais):
    """Três termos com datas de cadastro distintas, do mais antigo ao mais recente."""
    return [
        _cria_termo(
            empresa,
            contrato,
            tres_fiscais,
            data_cadastro=datetime.datetime(ano, 3, 15, 12, 0),
        )
        for ano in (2024, 2025, 2026)
    ]


@pytest.fixture
def client_fiscal(client, usuario_fiscal):
    """Client autenticado como o fiscal (perfil DILOG_QUALIDADE)."""
    client.login(
        username=usuario_fiscal.username,
        password=constants.DJANGO_ADMIN_PASSWORD,
    )
    return client, usuario_fiscal


def _cria_termo_do_painel(empresa, contrato, fiscais, status, cronogramas=()):
    """Termo para o painel de assinaturas."""

    termo = TermoRecebimentoDefinitivo.objects.create(
        empresa=empresa,
        contrato=contrato,
        fiscal_1=fiscais[0],
        fiscal_2=fiscais[1],
        fiscal_3=fiscais[2],
        status=status,
    )
    for numero, nome_produto in cronogramas:
        produto, _ = NomeDeProdutoEdital.objects.get_or_create(
            nome=nome_produto,
            tipo_produto=NomeDeProdutoEdital.LOGISTICA,
        )
        ficha_tecnica = FichaTecnicaFactory(produto=produto)
        CronogramaTermoRecebimentoDefinitivo.objects.create(
            termo=termo,
            cronograma=CronogramaFactory(
                contrato=contrato,
                empresa=empresa,
                numero=numero,
                ficha_tecnica=ficha_tecnica,
            ),
            quantidade_total_recebida="1234.56",
        )
    TermoRecebimentoDefinitivo.objects.filter(pk=termo.pk).update(
        criado_em=timezone.make_aware(DATA_CADASTRO_TERMO)
    )
    termo.refresh_from_db()
    return termo


@pytest.fixture
def termos_painel_assinatura(usuario_fiscal, tres_fiscais):
    """Quatro termos cobrindo as combinações de status e de fiscal.

    - ``pendente_do_fiscal``: ENVIADO_FISCAIS, usuário é o fiscal_1;
    - ``pendente_de_outro_fiscal``: ENVIADO_FISCAIS, usuário não é fiscal;
    - ``de_outro_status``: ENVIADO_DILOG, usuário é o fiscal_1;
    - ``assinado_do_fiscal``: ASSINADO_FORNECEDOR, usuário é o fiscal_2.
    """
    fiscais_com_usuario = [usuario_fiscal, tres_fiscais[1], tres_fiscais[2]]

    empresa_alfa = EmpresaFactory(nome_fantasia="ALFA ALIMENTOS")
    contrato_alfa = ContratoFactory(terceirizada=empresa_alfa, numero="111/2026")
    outra_empresa = EmpresaFactory()

    return SimpleNamespace(
        pendente_do_fiscal=_cria_termo_do_painel(
            empresa_alfa,
            contrato_alfa,
            fiscais_com_usuario,
            TermoRecebimentoDefinitivo.ENVIADO_FISCAIS,
            (("001/2026", "MAMAO PAPAYA"), ("002/2026", "ABACATE")),
        ),
        pendente_de_outro_fiscal=_cria_termo_do_painel(
            outra_empresa,
            ContratoFactory(terceirizada=outra_empresa),
            list(tres_fiscais),
            TermoRecebimentoDefinitivo.ENVIADO_FISCAIS,
            (("003/2026", "BANANA PRATA"),),
        ),
        de_outro_status=_cria_termo_do_painel(
            empresa_alfa,
            contrato_alfa,
            fiscais_com_usuario,
            TermoRecebimentoDefinitivo.ENVIADO_DILOG,
        ),
        assinado_do_fiscal=_cria_termo_do_painel(
            empresa_alfa,
            contrato_alfa,
            [tres_fiscais[0], usuario_fiscal, tres_fiscais[2]],
            TermoRecebimentoDefinitivo.ASSINADO_FORNECEDOR,
            # Dois cronogramas do mesmo produto: o painel deve exibir o
            # nome uma única vez.
            (("005/2026", "MAMAO PAPAYA"), ("006/2026", "MAMAO PAPAYA")),
        ),
    )
