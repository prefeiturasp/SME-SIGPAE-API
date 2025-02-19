import datetime

import pytest
from faker import Faker
from model_mommy import mommy

from ...dados_comuns.behaviors import TempoPasseio
from ...dados_comuns.constants import (
    COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
    DJANGO_ADMIN_PASSWORD,
)
from ...dados_comuns.fluxo_status import (
    PedidoAPartirDaDiretoriaRegionalWorkflow,
    PedidoAPartirDaEscolaWorkflow,
)
from ...dados_comuns.models import TemplateMensagem
from ...escola.models import Aluno
from .. import models
from ..models import KitLanche

fake = Faker("pt_BR")
Faker.seed(420)


@pytest.fixture
def lote(diretoria_regional):
    return mommy.make("Lote", diretoria_regional=diretoria_regional)


@pytest.fixture
def terceirizada(lote):
    return mommy.make("Terceirizada", lotes=[lote])


@pytest.fixture
def codae():
    return mommy.make("CODAE")


@pytest.fixture
def diretoria_regional():
    return mommy.make("DiretoriaRegional", nome="DIRETORIA REGIONAL IPIRANGA")


@pytest.fixture
def tipo_unidade():
    return mommy.make("TipoUnidadeEscolar", iniciais="EMEF")


@pytest.fixture
def escola(diretoria_regional, lote, tipo_unidade):
    contato = mommy.make("dados_comuns.Contato", nome="FULANO", email="fake@email.com")
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    return mommy.make(
        "Escola",
        nome="EMEF TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        contato=contato,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade,
        uuid="230453bb-d6f1-4513-b638-8d6d150d1ac6",
    )


@pytest.fixture
def dia_suspensao_atividades_2019_11_13(escola):
    edital = mommy.make("Edital", numero="78/SME/2023")
    contrato = mommy.make(
        "Contrato", edital=edital, terceirizada=escola.lote.terceirizada
    )
    contrato.lotes.add(escola.lote)
    contrato.save()
    return mommy.make(
        "DiaSuspensaoAtividades",
        tipo_unidade=escola.tipo_unidade,
        edital=edital,
        data=datetime.date(2019, 11, 13),
    )


@pytest.fixture
def aluno():
    return mommy.make(
        Aluno,
        nome="Roberto Alves da Silva",
        codigo_eol="123456",
        data_nascimento="2000-01-01",
        uuid="2d20157a-4e52-4d25-a4c7-9c0e6b67ee18",
    )


@pytest.fixture
def edital():
    return mommy.make("Edital", numero="1", objeto="lorem ipsum")


@pytest.fixture()
def mocks_kit_lanche_cemei():
    mommy.make("KitLanche", uuid="b9c58783-9131-4e8d-a5fb-89974ca5cbfc")
    mommy.make("FaixaEtaria", uuid="a26bcacc-a9e0-4f2d-b03d-d9d5ff63f8e7")
    mommy.make("FaixaEtaria", uuid="2d20157a-4e52-4d25-a4c7-9c0e6b67ee18")


@pytest.fixture
def usuario_escola(django_user_model, escola):
    email = "userescola@escola.com"
    password = DJANGO_ADMIN_PASSWORD
    perfil_diretor = mommy.make("Perfil", nome="DIRETOR", ativo=True)
    usuario = django_user_model.objects.create_user(
        password=password,
        email=email,
        registro_funcional="1234567",
    )
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=usuario,
        instituicao=escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    return usuario


@pytest.fixture
def client_autenticado_da_escola(
    client, django_user_model, escola, aluno, mocks_kit_lanche_cemei
):
    email = "user@escola.com"
    password = DJANGO_ADMIN_PASSWORD
    perfil_diretor = mommy.make("Perfil", nome="DIRETOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional="123456",
    )
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=usuario,
        instituicao=escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_da_dre(client, django_user_model, diretoria_regional):
    email = "user@dre.com"
    password = DJANGO_ADMIN_PASSWORD
    perfil_adm_dre = mommy.make("Perfil", nome="ADM_DRE", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="123456"
    )
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=usuario,
        instituicao=diretoria_regional,
        perfil=perfil_adm_dre,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_da_codae(client, django_user_model, codae):
    email = "foo@codae.com"
    password = DJANGO_ADMIN_PASSWORD
    perfil_adm_codae = mommy.make(
        "Perfil", nome=COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA, ativo=True
    )
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="123456"
    )
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=usuario,
        instituicao=codae,
        perfil=perfil_adm_codae,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_da_terceirizada(client, django_user_model, terceirizada):
    email = "foo@codae.com"
    password = DJANGO_ADMIN_PASSWORD
    perfil_adm_terc = mommy.make("Perfil", nome="TERCEIRIZADA", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="123456"
    )
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=usuario,
        instituicao=terceirizada,
        perfil=perfil_adm_terc,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def kit_lanche(edital):
    return mommy.make(
        models.KitLanche,
        nome=fake.name(),
        descricao=fake.text()[:160],
        status="ATIVO",
        edital=edital,
    )


@pytest.fixture
def item_kit_lanche():
    return mommy.make(models.ItemKitLanche, nome=fake.name())


@pytest.fixture
def solicitacao_avulsa(escola, terceirizada):
    mommy.make("escola.EscolaPeriodoEscolar", escola=escola, quantidade_alunos=500)
    mommy.make(TemplateMensagem, tipo=TemplateMensagem.SOLICITACAO_KIT_LANCHE_AVULSA)
    kits = mommy.make(models.KitLanche, _quantity=3)
    solicitacao_kit_lanche = mommy.make(
        models.SolicitacaoKitLanche, kits=kits, data=datetime.date(2000, 1, 1)
    )
    return mommy.make(
        models.SolicitacaoKitLancheAvulsa,
        local=fake.text()[:160],
        quantidade_alunos=300,
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        escola=escola,
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
        rastro_terceirizada=terceirizada,
    )


@pytest.fixture
def solicitacao_cei(escola, terceirizada):
    mommy.make("escola.EscolaPeriodoEscolar", escola=escola, quantidade_alunos=500)
    mommy.make(TemplateMensagem, tipo=TemplateMensagem.SOLICITACAO_KIT_LANCHE_AVULSA)
    kits = mommy.make(models.KitLanche, _quantity=3)
    solicitacao_kit_lanche = mommy.make(
        models.SolicitacaoKitLanche, kits=kits, data=datetime.date(2000, 1, 1)
    )
    return mommy.make(
        models.SolicitacaoKitLancheCEIAvulsa,
        local=fake.text()[:160],
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        escola=escola,
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
        rastro_terceirizada=terceirizada,
    )


@pytest.fixture
def solicitacao_avulsa_rascunho(solicitacao_avulsa):
    solicitacao_avulsa.status = PedidoAPartirDaEscolaWorkflow.RASCUNHO
    solicitacao_avulsa.quantidade_alunos = 200
    solicitacao_avulsa.save()

    return solicitacao_avulsa


@pytest.fixture
def solicitacao_avulsa_dre_a_validar(solicitacao_avulsa):
    solicitacao_avulsa.status = PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    solicitacao_avulsa.quantidade_alunos = 200
    solicitacao_avulsa.save()

    return solicitacao_avulsa


@pytest.fixture
def solicitacao_avulsa_dre_validado(solicitacao_avulsa):
    solicitacao_avulsa.status = PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    solicitacao_avulsa.quantidade_alunos = 200
    solicitacao_avulsa.save()
    return solicitacao_avulsa


@pytest.fixture
def solicitacao_avulsa_codae_questionado(solicitacao_avulsa):
    solicitacao_avulsa.status = PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO
    solicitacao_avulsa.quantidade_alunos = 200
    solicitacao_avulsa.save()
    return solicitacao_avulsa


@pytest.fixture
def solic_avulsa_terc_respondeu_questionamento(solicitacao_avulsa):
    solicitacao_avulsa.status = (
        PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO
    )
    solicitacao_avulsa.quantidade_alunos = 200
    solicitacao_avulsa.save()
    return solicitacao_avulsa


@pytest.fixture
def solicitacao_avulsa_codae_autorizado(solicitacao_avulsa, escola):
    solicitacao_kit_lanche = mommy.make(
        models.SolicitacaoKitLanche, data=datetime.datetime(2019, 11, 18)
    )
    solicitacao_avulsa.status = PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    solicitacao_avulsa.solicitacao_kit_lanche = solicitacao_kit_lanche
    solicitacao_avulsa.quantidade_alunos = 200
    solicitacao_avulsa.save()
    return solicitacao_avulsa


@pytest.fixture
def solicitacao_unificada_lista_igual(
    escola, diretoria_regional, terceirizada, usuario_escola
):
    mommy.make(TemplateMensagem, tipo=TemplateMensagem.SOLICITACAO_KIT_LANCHE_UNIFICADA)
    kits = mommy.make(models.KitLanche, _quantity=3)
    solicitacao_kit_lanche = mommy.make(
        models.SolicitacaoKitLanche,
        data=datetime.date(2019, 10, 14),
        tempo_passeio=models.SolicitacaoKitLanche.OITO_OU_MAIS,
        kits=kits,
    )
    escolas_quantidades = mommy.make(
        "EscolaQuantidade",
        escola=escola,
        _quantity=10,
        quantidade_alunos=100,
        cancelado_por=usuario_escola,
        cancelado=True,
        cancelado_em=datetime.date.today(),
    )
    solicitacao_unificada = mommy.make(
        models.SolicitacaoKitLancheUnificada,
        local=fake.text()[:160],
        lista_kit_lanche_igual=True,
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        outro_motivo=fake.text(),
        diretoria_regional=diretoria_regional,
        rastro_dre=diretoria_regional,
        rastro_terceirizada=terceirizada,
    )
    solicitacao_unificada.escolas_quantidades.set(escolas_quantidades)
    return solicitacao_unificada


@pytest.fixture
def solicitacao_unificada_lista_igual_codae_a_autorizar(
    solicitacao_unificada_lista_igual,
):
    solicitacao_unificada_lista_igual.status = (
        PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_A_AUTORIZAR
    )
    solicitacao_unificada_lista_igual.save()
    return solicitacao_unificada_lista_igual


@pytest.fixture
def solicitacao_unificada_lista_igual_codae_questionado(
    solicitacao_unificada_lista_igual,
):
    solicitacao_unificada_lista_igual.status = (
        PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_QUESTIONADO
    )
    solicitacao_unificada_lista_igual.save()
    return solicitacao_unificada_lista_igual


@pytest.fixture
def solicitacao_unificada_lista_igual_codae_autorizado(
    solicitacao_unificada_lista_igual,
):
    solicitacao_unificada_lista_igual.status = (
        PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_AUTORIZADO
    )
    solicitacao_unificada_lista_igual.save()
    return solicitacao_unificada_lista_igual


@pytest.fixture
def solicitacao_unificada_lotes_diferentes():
    kits = mommy.make(models.KitLanche, _quantity=3)
    solicitacao_kit_lanche = mommy.make(
        models.SolicitacaoKitLanche,
        tempo_passeio=models.SolicitacaoKitLanche.OITO_OU_MAIS,
        kits=kits,
    )
    dre = mommy.make("escola.DiretoriaRegional", nome=fake.name())
    solicitacao_unificada = mommy.make(
        models.SolicitacaoKitLancheUnificada,
        local=fake.text()[:160],
        lista_kit_lanche_igual=True,
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        outro_motivo=fake.text(),
        diretoria_regional=dre,
    )
    lote_um = mommy.make("escola.Lote")
    escola_um = mommy.make("escola.Escola", lote=lote_um)
    escola_dois = mommy.make("escola.Escola", lote=lote_um)
    escola_tres = mommy.make("escola.Escola", lote=lote_um)
    mommy.make(
        models.EscolaQuantidade,
        escola=escola_um,
        solicitacao_unificada=solicitacao_unificada,
    )
    mommy.make(
        models.EscolaQuantidade,
        escola=escola_dois,
        solicitacao_unificada=solicitacao_unificada,
    )
    mommy.make(
        models.EscolaQuantidade,
        escola=escola_tres,
        solicitacao_unificada=solicitacao_unificada,
    )
    lote_dois = mommy.make("escola.Lote")
    escola_quatro = mommy.make("escola.Escola", lote=lote_dois)
    escola_cinco = mommy.make("escola.Escola", lote=lote_dois)
    mommy.make(
        models.EscolaQuantidade,
        escola=escola_quatro,
        solicitacao_unificada=solicitacao_unificada,
    )
    mommy.make(
        models.EscolaQuantidade,
        escola=escola_cinco,
        solicitacao_unificada=solicitacao_unificada,
    )
    return solicitacao_unificada


@pytest.fixture
def solicitacao_unificada_lotes_iguais():
    kits = mommy.make(models.KitLanche, _quantity=3)
    solicitacao_kit_lanche = mommy.make(
        models.SolicitacaoKitLanche,
        tempo_passeio=models.SolicitacaoKitLanche.OITO_OU_MAIS,
        kits=kits,
    )
    dre = mommy.make("escola.DiretoriaRegional", nome=fake.name())
    solicitacao_unificada = mommy.make(
        models.SolicitacaoKitLancheUnificada,
        local=fake.text()[:160],
        lista_kit_lanche_igual=True,
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        outro_motivo=fake.text(),
        diretoria_regional=dre,
    )
    lote_um = mommy.make("escola.Lote")
    escola_um = mommy.make("escola.Escola", lote=lote_um)
    escola_dois = mommy.make("escola.Escola", lote=lote_um)
    escola_tres = mommy.make("escola.Escola", lote=lote_um)
    escola_quatro = mommy.make("escola.Escola", lote=lote_um)
    escola_cinco = mommy.make("escola.Escola", lote=lote_um)
    mommy.make(
        models.EscolaQuantidade,
        escola=escola_um,
        solicitacao_unificada=solicitacao_unificada,
    )
    mommy.make(
        models.EscolaQuantidade,
        escola=escola_dois,
        solicitacao_unificada=solicitacao_unificada,
    )
    mommy.make(
        models.EscolaQuantidade,
        escola=escola_tres,
        solicitacao_unificada=solicitacao_unificada,
    )
    mommy.make(
        models.EscolaQuantidade,
        escola=escola_quatro,
        solicitacao_unificada=solicitacao_unificada,
    )
    mommy.make(
        models.EscolaQuantidade,
        escola=escola_cinco,
        solicitacao_unificada=solicitacao_unificada,
    )
    return solicitacao_unificada


@pytest.fixture
def solicitacao():
    kits = mommy.make(models.KitLanche, nome=fake.name(), _quantity=3)
    return mommy.make(
        models.SolicitacaoKitLanche,
        descricao=fake.text(),
        motivo=fake.text(),
        tempo_passeio=TempoPasseio.CINCO_A_SETE,
        kits=kits,
    )


@pytest.fixture(
    params=[
        (0, True),
        (1, True),
        (2, True),
    ]
)
def horarios_passeio(request):
    return request.param


erro_esperado_passeio = "tempo de passeio deve ser qualquer uma das opções:"


@pytest.fixture(
    params=[
        ("0", erro_esperado_passeio),
        ("TESTE", erro_esperado_passeio),
        (3, erro_esperado_passeio),
    ]
)
def horarios_passeio_invalido(request):
    return request.param


@pytest.fixture(
    params=[
        # tempo passeio, qtd kits
        (0, 1),
        (1, 2),
        (2, 3),
    ]
)
def tempo_kits(request):
    return request.param


@pytest.fixture(
    params=[
        # para testar no dia 2/10/19
        # data do evento, tag
        (datetime.date(2019, 9, 30), "VENCIDO"),
        (datetime.date(2019, 10, 1), "VENCIDO"),
        (datetime.date(2019, 10, 2), "PRIORITARIO"),
        (datetime.date(2019, 10, 3), "PRIORITARIO"),
        (datetime.date(2019, 10, 4), "PRIORITARIO"),
        (datetime.date(2019, 10, 5), "PRIORITARIO"),
        (datetime.date(2019, 10, 6), "PRIORITARIO"),
        (datetime.date(2019, 10, 7), "LIMITE"),
        (datetime.date(2019, 10, 8), "LIMITE"),
        (datetime.date(2019, 10, 9), "LIMITE"),
        (datetime.date(2019, 10, 10), "REGULAR"),
        (datetime.date(2019, 10, 11), "REGULAR"),
        (datetime.date(2019, 10, 12), "REGULAR"),
        (datetime.date(2019, 10, 13), "REGULAR"),
    ]
)
def kits_avulsos_parametros(request):
    return request.param


@pytest.fixture(
    params=[
        # para testar no dia 20/12/19
        # data do evento, tag
        (datetime.date(2019, 12, 18), "VENCIDO"),
        (datetime.date(2019, 12, 19), "VENCIDO"),
        (datetime.date(2019, 12, 20), "PRIORITARIO"),
        (datetime.date(2019, 12, 21), "PRIORITARIO"),
        (datetime.date(2019, 12, 22), "PRIORITARIO"),
        (datetime.date(2019, 12, 23), "PRIORITARIO"),
        (datetime.date(2019, 12, 24), "PRIORITARIO"),
        (datetime.date(2019, 12, 25), "PRIORITARIO"),
        (datetime.date(2019, 12, 26), "LIMITE"),
        (datetime.date(2019, 12, 27), "LIMITE"),
        (datetime.date(2019, 12, 28), "LIMITE"),
        (datetime.date(2019, 12, 29), "LIMITE"),
        (datetime.date(2019, 12, 30), "LIMITE"),
        (datetime.date(2019, 12, 31), "REGULAR"),
        (datetime.date(2020, 1, 1), "REGULAR"),
    ]
)
def kits_avulsos_parametros2(request):
    return request.param


@pytest.fixture(
    params=[
        # para testar no dia 3/10/19
        # data do evento, status
        (datetime.date(2019, 10, 2), PedidoAPartirDaEscolaWorkflow.RASCUNHO),
        (datetime.date(2019, 10, 1), PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO),
        (
            datetime.date(2019, 9, 30),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
        (datetime.date(2019, 9, 29), PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO),
        (datetime.date(2019, 9, 28), PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO),
        (datetime.date(2019, 9, 27), PedidoAPartirDaEscolaWorkflow.RASCUNHO),
        (
            datetime.date(2019, 9, 26),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
    ]
)
def kits_avulsos_datas_passado_parametros(request):
    return request.param


@pytest.fixture(
    params=[
        # para testar no dia 3/10/19
        (datetime.date(2019, 10, 3)),
        (datetime.date(2019, 10, 4)),
        (datetime.date(2019, 10, 5)),
        (datetime.date(2019, 10, 6)),
        (datetime.date(2019, 10, 7)),
        (datetime.date(2019, 10, 8)),
        (datetime.date(2019, 10, 9)),
        (datetime.date(2019, 10, 10)),
    ]
)
def kits_avulsos_datas_semana(request):
    return request.param


@pytest.fixture(
    params=[
        # para testar no dia 3/10/19
        (datetime.date(2019, 10, 3)),
        (datetime.date(2019, 10, 8)),
        (datetime.date(2019, 10, 10)),
        (datetime.date(2019, 10, 15)),
        (datetime.date(2019, 10, 20)),
        (datetime.date(2019, 11, 3)),
    ]
)
def kits_avulsos_datas_mes(request):
    return request.param


@pytest.fixture(
    params=[
        # para testar no dia 3/10/19
        # data do evento, status
        (datetime.date(2019, 10, 2), PedidoAPartirDaDiretoriaRegionalWorkflow.RASCUNHO),
        (
            datetime.date(2019, 10, 1),
            PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_A_AUTORIZAR,
        ),
        (
            datetime.date(2019, 9, 30),
            PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_PEDIU_DRE_REVISAR,
        ),
        (datetime.date(2019, 9, 29), PedidoAPartirDaDiretoriaRegionalWorkflow.RASCUNHO),
        (
            datetime.date(2019, 9, 28),
            PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_PEDIU_DRE_REVISAR,
        ),
        (
            datetime.date(2019, 9, 27),
            PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_A_AUTORIZAR,
        ),
        (
            datetime.date(2019, 9, 26),
            PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_PEDIU_DRE_REVISAR,
        ),
    ]
)
def kits_unificados_datas_passado_parametros(request):
    return request.param


@pytest.fixture(
    params=[
        # qtd_alunos_escola, qtd_alunos_pedido, dia, erro esperado TODO ver esse confirmar... erro esperado
        (100, 100, datetime.date(2001, 1, 1), "Não pode ser no passado"),
        (
            100,
            99,
            datetime.date(2019, 10, 16),
            "Deve pedir com pelo menos 2 dias úteis de antecedência",
        ),
        (
            100,
            99,
            datetime.date(2019, 10, 16),
            "Deve pedir com pelo menos 2 dias úteis de antecedência",
        ),
        (
            100,
            99,
            datetime.date(2019, 10, 17),
            "Deve pedir com pelo menos 2 dias úteis de antecedência",
        ),
    ]
)
def kits_avulsos_param_erro_serializer(request):
    return request.param


@pytest.fixture(
    params=[
        # qtd_alunos_escola, qtd_alunos_pedido, dia
        (100, 100, datetime.date(2019, 8, 1)),
        (1000, 77, datetime.date(2019, 10, 20)),
        (1000, 700, datetime.date(2019, 10, 20)),
    ]
)
def kits_avulsos_param_serializer(request):
    return request.param


@pytest.fixture(
    params=[
        # qtd_alunos_escola, qtd_alunos_pedido, dia
        (1000, 77, datetime.date(2019, 10, 20)),
        (1000, 700, datetime.date(2019, 10, 20)),
        (100, 100, datetime.date(2019, 12, 1)),
    ]
)
def kits_unificados_param_serializer(request):
    return request.param


@pytest.fixture
def escola_quantidade():
    return mommy.make(models.EscolaQuantidade)


@pytest.fixture
def periodo_escolar():
    return mommy.make("PeriodoEscolar", nome="INTEGRAL")


@pytest.fixture
def kit_lanche_cemei():
    kit_lanche_cemei = mommy.make(
        "SolicitacaoKitLancheCEMEI", local="Parque do Ibirapuera", data="2022-10-25"
    )

    mommy.make("KitLanche", nome="KIT 1")
    mommy.make("KitLanche", nome="KIT 2")
    mommy.make("KitLanche", nome="KIT 3")
    kits = KitLanche.objects.all()

    solicitacao_cei = mommy.make(
        "SolicitacaoKitLancheCEIdaCEMEI",
        solicitacao_kit_lanche_cemei=kit_lanche_cemei,
        kits=kits,
    )
    mommy.make(
        "FaixasQuantidadesKitLancheCEIdaCEMEI",
        solicitacao_kit_lanche_cei_da_cemei=solicitacao_cei,
        quantidade_alunos=10,
        matriculados_quando_criado=20,
    )
    mommy.make(
        "FaixasQuantidadesKitLancheCEIdaCEMEI",
        solicitacao_kit_lanche_cei_da_cemei=solicitacao_cei,
        quantidade_alunos=10,
        matriculados_quando_criado=20,
    )
    mommy.make(
        "FaixasQuantidadesKitLancheCEIdaCEMEI",
        solicitacao_kit_lanche_cei_da_cemei=solicitacao_cei,
        quantidade_alunos=10,
        matriculados_quando_criado=20,
    )

    mommy.make(
        "SolicitacaoKitLancheEMEIdaCEMEI",
        solicitacao_kit_lanche_cemei=kit_lanche_cemei,
        quantidade_alunos=10,
        matriculados_quando_criado=20,
        kits=kits,
    )

    return kit_lanche_cemei
