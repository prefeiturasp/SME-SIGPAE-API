import datetime

import pytest
from django.utils import timezone
from faker import Faker
from model_bakery import baker

from src.dados_comuns.constants import (
    ADMINISTRADOR_EMPRESA,
    COORDENADOR_CODAE_DILOG_LOGISTICA,
    DILOG_ABASTECIMENTO,
    DILOG_CRONOGRAMA,
    DJANGO_ADMIN_PASSWORD,
)
from src.pre_recebimento.cronograma_entrega.models import Cronograma
from src.pre_recebimento.cronograma_semanal.models import (
    CronogramaSemanal,
    ProgramacaoEntregaSemanal,
)
from src.terceirizada.models import Terceirizada

fake = Faker("pt_BR")


@pytest.fixture
def codae():
    return baker.make("Codae")


@pytest.fixture
def client_autenticado_vinculo_dilog_cronograma(client, django_user_model, codae):
    email = "dilogcronograma@test.com"
    password = DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional=str(fake.unique.random_int(min=100000, max=999999)),
    )
    perfil_dilog_cronograma = baker.make(
        "Perfil",
        nome=DILOG_CRONOGRAMA,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_dilog_cronograma,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    client.login(username=email, password=password)
    return client, user


@pytest.fixture
def client_autenticado_dilog_abastecimento(client, django_user_model):
    email = "dilogabastecimento@test.com"
    password = DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional=str(fake.unique.random_int(min=100000, max=999999)),
    )
    perfil_dilog_abastecimento = baker.make(
        "Perfil", nome=DILOG_ABASTECIMENTO, ativo=True
    )
    codae = baker.make("Codae")
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_dilog_abastecimento,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def cronograma_ponto_a_ponto_assinado(
    contrato_factory, empresa_factory, ficha_tecnica_factory
):
    from src.pre_recebimento.ficha_tecnica.models import (
        FichaTecnicaDoProduto,
    )

    empresa = empresa_factory(tipo_servico=Terceirizada.FORNECEDOR)
    contrato = contrato_factory(terceirizada=empresa)
    ficha = ficha_tecnica_factory(
        categoria=FichaTecnicaDoProduto.CATEGORIA_FLV,
        tipo_entrega=FichaTecnicaDoProduto.PONTO_A_PONTO,
    )
    return baker.make(
        Cronograma,
        numero="001/2024A",
        contrato=contrato,
        empresa=empresa,
        ficha_tecnica=ficha,
        status=Cronograma.workflow_class.ASSINADO_CODAE,
    )


@pytest.fixture
def cronograma_ponto_a_ponto_nao_assinado(
    contrato_factory, empresa_factory, ficha_tecnica_factory
):
    from src.pre_recebimento.ficha_tecnica.models import (
        FichaTecnicaDoProduto,
    )

    empresa = empresa_factory(tipo_servico=Terceirizada.FORNECEDOR)
    contrato = contrato_factory(terceirizada=empresa)
    ficha = ficha_tecnica_factory(
        categoria=FichaTecnicaDoProduto.CATEGORIA_FLV,
        tipo_entrega=FichaTecnicaDoProduto.PONTO_A_PONTO,
    )
    return baker.make(
        Cronograma,
        numero="002/2024A",
        contrato=contrato,
        empresa=empresa,
        ficha_tecnica=ficha,
        status=Cronograma.workflow_class.RASCUNHO,
    )


@pytest.fixture
def cronograma_nao_ponto_a_ponto_assinado(
    contrato_factory, empresa_factory, ficha_tecnica_factory
):
    from src.pre_recebimento.ficha_tecnica.models import (
        FichaTecnicaDoProduto,
    )

    empresa = empresa_factory(tipo_servico=Terceirizada.FORNECEDOR)
    contrato = contrato_factory(terceirizada=empresa)
    ficha = ficha_tecnica_factory(
        categoria=FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
        tipo_entrega=FichaTecnicaDoProduto.ARMAZEM,
    )
    return baker.make(
        Cronograma,
        numero="003/2024A",
        contrato=contrato,
        empresa=empresa,
        ficha_tecnica=ficha,
        status=Cronograma.workflow_class.ASSINADO_CODAE,
    )


@pytest.fixture
def cronograma_ponto_a_ponto_assinado_2(
    contrato_factory, empresa_factory, ficha_tecnica_factory
):
    from src.pre_recebimento.ficha_tecnica.models import (
        FichaTecnicaDoProduto,
    )

    empresa = empresa_factory(tipo_servico=Terceirizada.FORNECEDOR)
    contrato = contrato_factory(terceirizada=empresa)
    ficha = ficha_tecnica_factory(
        categoria=FichaTecnicaDoProduto.CATEGORIA_FLV,
        tipo_entrega=FichaTecnicaDoProduto.PONTO_A_PONTO,
    )
    return baker.make(
        Cronograma,
        numero="005/2024A",
        contrato=contrato,
        empresa=empresa,
        ficha_tecnica=ficha,
        status=Cronograma.workflow_class.ASSINADO_CODAE,
    )


@pytest.fixture
def cronograma_semanal_enviado_ao_fornecedor(cronograma_ponto_a_ponto_assinado):
    from src.dados_comuns.fluxo_status import CronogramaSemanalWorkflow

    return baker.make(
        CronogramaSemanal,
        cronograma_mensal=cronograma_ponto_a_ponto_assinado,
        status=CronogramaSemanalWorkflow.ENVIADO_AO_FORNECEDOR,
    )


@pytest.fixture
def cronograma_semanal_fornecedor_ciente(cronograma_ponto_a_ponto_assinado):
    from src.dados_comuns.fluxo_status import CronogramaSemanalWorkflow

    return baker.make(
        CronogramaSemanal,
        cronograma_mensal=cronograma_ponto_a_ponto_assinado,
        status=CronogramaSemanalWorkflow.FORNECEDOR_CIENTE,
    )


@pytest.fixture
def cronograma_semanal_rascunho(cronograma_ponto_a_ponto_assinado):
    return baker.make(
        CronogramaSemanal,
        cronograma_mensal=cronograma_ponto_a_ponto_assinado,
        observacoes="Teste de observação",
    )


@pytest.fixture
def programacao_entrega_semanal(cronograma_semanal_rascunho):
    return baker.make(
        ProgramacaoEntregaSemanal,
        cronograma_semanal=cronograma_semanal_rascunho,
        mes_programado="03/2026",
        data_inicio=timezone.now().date(),
        data_fim=timezone.now().date() + datetime.timedelta(days=5),
        quantidade=100.0,
    )


@pytest.fixture
def client_autenticado_coordenador_codae_dilog(client, django_user_model, codae):
    email = "coordenador_codae_dilog@test.com"
    password = DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="7777777"
    )
    perfil = baker.make(
        "Perfil",
        nome=COORDENADOR_CODAE_DILOG_LOGISTICA,
        ativo=True,
        uuid="51c20c8b-7e57-41ed-9433-ccb92e8afaf2",
    )
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    client.login(username=email, password=password)
    return client, user


@pytest.fixture
def payload_cronograma_semanal_rascunho(cronograma_ponto_a_ponto_assinado):
    return {
        "cronograma_mensal": str(cronograma_ponto_a_ponto_assinado.uuid),
        "observacoes": "Rascunho de teste",
    }


@pytest.fixture
def payload_cronograma_semanal_com_programacoes(cronograma_ponto_a_ponto_assinado):
    return {
        "cronograma_mensal": str(cronograma_ponto_a_ponto_assinado.uuid),
        "observacoes": "Rascunho com programações",
        "programacoes": [
            {
                "mes_programado": "03/2026",
                "data_inicio": "2026-03-01",
                "data_fim": "2026-03-15",
                "quantidade": 50.0,
            },
            {
                "mes_programado": "04/2026",
                "data_inicio": "2026-04-01",
                "data_fim": "2026-04-15",
                "quantidade": 30.0,
            },
        ],
    }


@pytest.fixture
def cronograma_semanal_com_programacao_marco(cronograma_ponto_a_ponto_assinado):
    from src.dados_comuns.fluxo_status import CronogramaSemanalWorkflow

    semanal = baker.make(
        CronogramaSemanal,
        cronograma_mensal=cronograma_ponto_a_ponto_assinado,
        status=CronogramaSemanalWorkflow.ENVIADO_AO_FORNECEDOR,
    )
    baker.make(
        "pre_recebimento.ProgramacaoEntregaSemanal",
        cronograma_semanal=semanal,
        data_inicio="2026-03-01",
        data_fim="2026-03-15",
        quantidade=50.0,
    )
    return semanal


@pytest.fixture
def cronograma_ponto_a_ponto_com_etapas(
    contrato_factory, empresa_factory, ficha_tecnica_factory
):
    from src.pre_recebimento.ficha_tecnica.models import (
        FichaTecnicaDoProduto,
    )

    empresa = empresa_factory(tipo_servico=Terceirizada.FORNECEDOR)
    contrato = contrato_factory(terceirizada=empresa)
    ficha = ficha_tecnica_factory(
        categoria=FichaTecnicaDoProduto.CATEGORIA_FLV,
        tipo_entrega=FichaTecnicaDoProduto.PONTO_A_PONTO,
    )
    cronograma = baker.make(
        Cronograma,
        numero="004/2024A",
        contrato=contrato,
        empresa=empresa,
        ficha_tecnica=ficha,
        status=Cronograma.workflow_class.ASSINADO_CODAE,
        numero_empenho="EMP001",
        qtd_total_empenho=1000.0,
        custo_unitario_produto=5.50,
    )

    baker.make(
        "EtapasDoCronograma",
        cronograma=cronograma,
        data_programada="2026-03-01",
        quantidade=500.0,
        etapa=1,
    )
    baker.make(
        "EtapasDoCronograma",
        cronograma=cronograma,
        data_programada="2026-04-01",
        quantidade=500.0,
        etapa=2,
    )

    return cronograma


@pytest.fixture
def cronograma_semanal_para_relatorio(cronograma_ponto_a_ponto_com_etapas):
    """Cronograma semanal com duas programações de entrega, para o relatório.

    O cronograma mensal de origem já traz ``qtd_total_empenho`` e
    ``custo_unitario_produto`` preenchidos.
    """
    from src.dados_comuns.fluxo_status import CronogramaSemanalWorkflow

    semanal = baker.make(
        CronogramaSemanal,
        numero="010/2026",
        cronograma_mensal=cronograma_ponto_a_ponto_com_etapas,
        status=CronogramaSemanalWorkflow.ENVIADO_AO_FORNECEDOR,
    )
    for mes, inicio, fim, quantidade in (
        ("03/2026", datetime.date(2026, 3, 1), datetime.date(2026, 3, 15), 50.0),
        ("04/2026", datetime.date(2026, 4, 1), datetime.date(2026, 4, 15), 30.0),
    ):
        baker.make(
            ProgramacaoEntregaSemanal,
            cronograma_semanal=semanal,
            mes_programado=mes,
            data_inicio=inicio,
            data_fim=fim,
            quantidade=quantidade,
        )
    return semanal


@pytest.fixture
def cronogramas_semanais_relatorio(
    cronograma_ponto_a_ponto_com_etapas, cronograma_ponto_a_ponto_assinado_2
):
    """Dois cronogramas semanais para exercitar os filtros do relatório.

    Diferem em empresa, produto, número (mensal e semanal), status e meses
    de entrega:

    - ``001/2026``: mensal ``004/2024A``, Enviado ao Fornecedor, com
      programações em 03/2026 e 05/2026;
    - ``002/2026``: mensal ``005/2024A``, Fornecedor Ciente, com uma
      programação em 04/2026.
    """
    from src.dados_comuns.fluxo_status import CronogramaSemanalWorkflow

    primeiro = baker.make(
        CronogramaSemanal,
        numero="001/2026",
        cronograma_mensal=cronograma_ponto_a_ponto_com_etapas,
        status=CronogramaSemanalWorkflow.ENVIADO_AO_FORNECEDOR,
    )
    segundo = baker.make(
        CronogramaSemanal,
        numero="002/2026",
        cronograma_mensal=cronograma_ponto_a_ponto_assinado_2,
        status=CronogramaSemanalWorkflow.FORNECEDOR_CIENTE,
    )
    programacoes = (
        (primeiro, "03/2026", datetime.date(2026, 3, 1), datetime.date(2026, 3, 15)),
        (primeiro, "05/2026", datetime.date(2026, 5, 1), datetime.date(2026, 5, 15)),
        (segundo, "04/2026", datetime.date(2026, 4, 1), datetime.date(2026, 4, 15)),
    )
    for semanal, mes, data_inicio, data_fim in programacoes:
        baker.make(
            ProgramacaoEntregaSemanal,
            cronograma_semanal=semanal,
            mes_programado=mes,
            data_inicio=data_inicio,
            data_fim=data_fim,
            quantidade=50.0,
        )
    return primeiro, segundo


@pytest.fixture
def cronograma_semanal_completo_para_excel(contrato_factory, empresa_factory):
    """Cronograma semanal com todos os campos do Excel preenchidos.

    Os valores reproduzem as duas primeiras linhas do protótipo do
    relatório, para que as asserções do teste sejam legíveis. Tem duas
    programações de entrega, ambas em junho/2026.
    """
    from src.dados_comuns.fluxo_status import CronogramaSemanalWorkflow
    from src.pre_recebimento.base.models import UnidadeMedida
    from src.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto

    empresa = empresa_factory(
        nome_fantasia="BELA VISTA", tipo_servico=Terceirizada.FORNECEDOR
    )
    modalidade = baker.make("Modalidade", nome="Pregão Eletronico")
    contrato = contrato_factory(
        terceirizada=empresa,
        numero="44/SME/CODAE/2026",
        processo="444.2026/004444-4",
        modalidade=modalidade,
    )
    unidade_medida = baker.make(UnidadeMedida, nome="Unidade", abreviacao="un")
    produto = baker.make("NomeDeProdutoEdital", nome="CAQUI")
    ficha = baker.make(
        FichaTecnicaDoProduto,
        produto=produto,
        categoria=FichaTecnicaDoProduto.CATEGORIA_FLV,
        tipo_entrega=FichaTecnicaDoProduto.PONTO_A_PONTO,
    )
    mensal = baker.make(
        Cronograma,
        numero="012/2026A",
        empresa=empresa,
        contrato=contrato,
        ficha_tecnica=ficha,
        unidade_medida=unidade_medida,
        numero_empenho="44.444/2026",
        qtd_total_empenho=25000.0,
        custo_unitario_produto=1.35,
        status=Cronograma.workflow_class.ASSINADO_CODAE,
    )

    semanal = baker.make(
        CronogramaSemanal,
        numero="012/2026P",
        cronograma_mensal=mensal,
        status=CronogramaSemanalWorkflow.ENVIADO_AO_FORNECEDOR,
    )
    for data_inicio, data_fim in (
        (datetime.date(2026, 6, 20), datetime.date(2026, 6, 23)),
        (datetime.date(2026, 6, 25), datetime.date(2026, 6, 28)),
    ):
        baker.make(
            ProgramacaoEntregaSemanal,
            cronograma_semanal=semanal,
            mes_programado="06/2026",
            data_inicio=data_inicio,
            data_fim=data_fim,
            quantidade=8250.0,
        )
    return semanal


@pytest.fixture
def programacao_de_julho(cronograma_semanal_completo_para_excel):
    """Terceira programação, em outro mês, para exercitar o filtro."""
    return baker.make(
        ProgramacaoEntregaSemanal,
        cronograma_semanal=cronograma_semanal_completo_para_excel,
        mes_programado="07/2026",
        data_inicio=datetime.date(2026, 7, 1),
        data_fim=datetime.date(2026, 7, 10),
        quantidade=1000.0,
    )


@pytest.fixture
def cronograma_semanal_sem_programacoes(cronograma_ponto_a_ponto_assinado_2):
    """Cronograma semanal sem nenhuma programação de entrega."""
    from src.dados_comuns.fluxo_status import CronogramaSemanalWorkflow

    return baker.make(
        CronogramaSemanal,
        numero="099/2026",
        cronograma_mensal=cronograma_ponto_a_ponto_assinado_2,
        status=CronogramaSemanalWorkflow.ENVIADO_AO_FORNECEDOR,
    )


@pytest.fixture
def empresa_fornecedor(cronograma_ponto_a_ponto_assinado):
    return cronograma_ponto_a_ponto_assinado.empresa


@pytest.fixture
def client_autenticado_vinculo_fornecedor(
    client, django_user_model, empresa_fornecedor
):
    """
    Retorna um client autenticado com perfil ADMINISTRADOR_EMPRESA vinculado a um fornecedor.
    """
    email = "fornecedor_test@teste.com"
    password = DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional=str(fake.unique.random_int(min=100000, max=999999)),
    )
    perfil_fornecedor = baker.make("Perfil", nome=ADMINISTRADOR_EMPRESA, ativo=True)
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=empresa_fornecedor,
        perfil=perfil_fornecedor,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    client.login(username=email, password=password)
    return client, user


@pytest.fixture
def cronograma_semanal_outra_empresa(cronograma_ponto_a_ponto_assinado_2):
    """Cronograma semanal vinculado a uma empresa diferente da do fornecedor padrão."""
    return baker.make(
        "pre_recebimento.CronogramaSemanal",
        cronograma_mensal=cronograma_ponto_a_ponto_assinado_2,
    )
