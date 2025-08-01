import datetime
import os
import xml.etree.ElementTree as ET

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import RequestFactory
from faker import Faker
from model_bakery import baker

from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.api.paginations import HistoricoDietasPagination
from sme_sigpae_api.dados_comuns.fluxo_status import (
    PedidoAPartirDaEscolaWorkflow,
    ReclamacaoProdutoWorkflow,
    SolicitacaoMedicaoInicialWorkflow,
)
from sme_sigpae_api.dados_comuns.parser_xml import ListXMLParser
from sme_sigpae_api.dieta_especial.models import (
    ClassificacaoDieta,
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
)
from sme_sigpae_api.perfil.models import ContentType
from utility.carga_dados.escola.importa_dados import (
    cria_diretorias_regionais,
    cria_lotes,
    cria_tipos_gestao,
)
from utility.carga_dados.terceirizada.importa_dados import cria_terceirizadas

from ...escola import models
from ..constants import COORDENADOR_LOGISTICA, DJANGO_ADMIN_PASSWORD
from ..models import (
    CentralDeDownload,
    LogSolicitacoesUsuario,
    Notificacao,
    TemplateMensagem,
)

fake = Faker("pt_BR")
Faker.seed(420)


@pytest.fixture(
    scope="function",
    params=[
        # dia, dias antecedencia, esperado
        # dia fake do teste: "2019-05-22"
        (datetime.date(2019, 5, 27), 2, True),
        (datetime.date(2019, 5, 25), 2, True),
        (datetime.date(2019, 5, 30), 5, True),
        (datetime.date(2019, 5, 28), 3, True),
    ],
)
def dias_teste_antecedencia(request):
    return request.param


@pytest.fixture(
    scope="function",
    params=[
        # dia, dias antecedencia, esperado
        # dia fake do teste: "2019-05-22"
        (
            datetime.date(2019, 5, 27),
            5,
            "Deve pedir com pelo menos 5 dias úteis de antecedência",
        ),
        (
            datetime.date(2019, 5, 28),
            5,
            "Deve pedir com pelo menos 5 dias úteis de antecedência",
        ),
        (
            datetime.date(2019, 5, 23),
            2,
            "Deve pedir com pelo menos 2 dias úteis de antecedência",
        ),
        (
            datetime.date(2019, 5, 21),
            2,
            "Deve pedir com pelo menos 2 dias úteis de antecedência",
        ),
    ],
)
def dias_teste_antecedencia_erro(request):
    return request.param


@pytest.fixture(
    scope="function",
    params=[
        # dia, esperado
        (datetime.date(2019, 12, 23), True),
        (datetime.date(2019, 12, 24), True),
        (datetime.date(2019, 12, 26), True),
        (datetime.date(2019, 12, 27), True),
    ],
)
def dias_uteis(request):
    return request.param


esperado = "Não é dia útil em São Paulo"


@pytest.fixture(
    scope="function",
    params=[
        # dia, esperado
        (datetime.date(2019, 12, 25), esperado),  # natal
        (datetime.date(2019, 1, 1), esperado),  # ano novo
        (datetime.date(2019, 7, 9), esperado),  # Revolução Constitucionalista
        (datetime.date(2019, 9, 7), esperado),  # independencia
        (datetime.date(2019, 1, 25), esperado),  # aniversario sp
    ],
)
def dias_nao_uteis(request):
    return request.param


@pytest.fixture(
    scope="function",
    params=[
        # dia,  esperado
        # dia fake do teste: "2019-05-22"
        (datetime.date(2019, 5, 22), True),
        (datetime.date(2019, 5, 27), True),
        (datetime.date(2019, 5, 28), True),
        (datetime.date(2019, 5, 23), True),
    ],
)
def dias_futuros(request):
    return request.param


dia_passado_esperado = "Não pode ser no passado"


@pytest.fixture(
    scope="function",
    params=[
        # dia,  esperado
        # dia fake do teste: "2019-05-22"
        (datetime.date(2019, 5, 21), dia_passado_esperado),
        (datetime.date(2019, 5, 20), dia_passado_esperado),
        (datetime.date(2018, 12, 12), dia_passado_esperado),
    ],
)
def dias_passados(request):
    return request.param


@pytest.fixture(
    scope="function",
    params=[
        # dia,  esperado
        # dia fake do teste: "2019-07-10" -> qua
        (2, datetime.date(2019, 7, 12)),  # sex
        (3, datetime.date(2019, 7, 15)),  # seg
        (5, datetime.date(2019, 7, 17)),  # qua
    ],
)
def dias_uteis_apos(request):
    return request.param


@pytest.fixture(
    scope="function",
    params=[
        # model-params-dict, esperado
        (
            {
                "_model": "TemplateMensagem",
                "assunto": "Inversão de cardápio",
                "template_html": '<p><span style="color: rgb(133,135,150);background-color:'
                ' rgb(255,255,255);font-size: 16px;">Ola @nome, a Inversão de'
                " cardápio #@id pedida por @criado_por está em @status. "
                "Acesse: @link</span></p>",
            },
            '<p><span style="color: rgb(133,135,150);background-color:'
            ' rgb(255,255,255);font-size: 16px;">Ola fulano, a Inversão de'
            " cardápio #FAKE_id_externo pedida por FAKE_criado_por está em FAKE_status. "
            "Acesse: http:teste.com</span></p>",
        ),
    ],
)
def template_mensagem(request):
    return request.param


@pytest.fixture
def template_mensagem_obj():
    return baker.make(TemplateMensagem, tipo=TemplateMensagem.ALTERACAO_CARDAPIO)


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture
def validators_models_object():
    return baker.make("dados_comuns.TemplateMensagem", assunto="TESTE")


@pytest.fixture
def validators_valor_str():
    return {"texto": "Nome", "none": None}


@pytest.fixture
def tipo_unidade():
    return baker.make("TipoUnidadeEscolar", iniciais="EMEF")


@pytest.fixture
def diretoria_regional():
    return baker.make("DiretoriaRegional", nome="DIRETORIA REGIONAL IPIRANGA")


@pytest.fixture
def escola(tipo_unidade, diretoria_regional):
    terceirizada = baker.make("Terceirizada")
    lote = baker.make(
        "Lote",
        terceirizada=terceirizada,
        nome="LOTE 07",
        diretoria_regional=diretoria_regional,
    )
    tipo_gestao = baker.make(
        "TipoGestao",
        nome="TERC TOTAL",
    )
    escola = baker.make(
        "Escola",
        lote=lote,
        nome="EMEF JOAO MENDES",
        codigo_eol="000546",
        tipo_unidade=tipo_unidade,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
    )
    return escola


@pytest.fixture
def dia_suspensao_atividades(escola):
    edital = baker.make("Edital", numero="78/SME/2023")
    contrato = baker.make(
        "Contrato", edital=edital, terceirizada=escola.lote.terceirizada
    )
    contrato.lotes.add(escola.lote)
    contrato.save()
    return baker.make(
        "DiaSuspensaoAtividades",
        tipo_unidade=escola.tipo_unidade,
        edital=edital,
        data=datetime.date(2023, 9, 26),
    )


@pytest.fixture(
    scope="function",
    params=[
        # dia do cardápio
        (datetime.date(2019, 5, 18)),
        (datetime.date(2019, 5, 19)),
        (datetime.date(2019, 5, 25)),
        (datetime.date(2019, 5, 26)),
        (datetime.date(2018, 6, 1)),
    ],
)
def dias_sem_cardapio(request):
    return request.param


@pytest.fixture(
    params=[
        (
            datetime.date(datetime.datetime.now().year - 1, 5, 26),
            "Solicitação deve ser solicitada no ano corrente",
        ),
        (
            datetime.date(datetime.datetime.now().year + 1, 1, 1),
            "Solicitação deve ser solicitada no ano corrente",
        ),
        (
            datetime.date(datetime.datetime.now().year + 2, 12, 1),
            "Solicitação deve ser solicitada no ano corrente",
        ),
    ]
)
def data_inversao_ano_diferente(request):
    return request.param


@pytest.fixture(
    params=[
        (datetime.date(2019, 5, 26), True),
        (datetime.date(2019, 1, 1), True),
        (datetime.date(2019, 12, 31), True),
    ]
)
def data_inversao_mesmo_ano(request):
    return request.param


@pytest.fixture
def client_autenticado_coordenador_codae(client, django_user_model):
    email, password, rf, cpf = (
        "cogestor_1@sme.prefeitura.sp.gov.br",
        DJANGO_ADMIN_PASSWORD,
        "0000001",
        "44426575052",
    )
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf, cpf=cpf
    )
    client.login(username=email, password=password)

    codae = baker.make(
        "Codae", nome="CODAE", uuid="b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd"
    )

    perfil_coordenador = baker.make(
        "Perfil",
        nome="COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA",
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )
    baker.make("Lote", uuid="143c2550-8bf0-46b4-b001-27965cfcd107")
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_coordenador,
        data_inicial=hoje,
        ativo=True,
    )

    return client


@pytest.fixture
def user_diretor_escola(django_user_model, escola):
    email = "user@escola.com"
    password = "admin@123"
    perfil_diretor = baker.make("Perfil", nome="DIRETOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional="123456",
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    return usuario, password


@pytest.fixture
def client_autenticado_da_escola(client, user_diretor_escola):
    usuario, password = user_diretor_escola
    client.login(username=usuario.email, password=password)
    return client


@pytest.fixture
def usuario_da_dre(django_user_model, diretoria_regional):
    email = "user@dre.com"
    password = DJANGO_ADMIN_PASSWORD
    perfil_cogestor_dre = baker.make("Perfil", nome="COGESTOR_DRE", ativo=True)
    usuario = django_user_model.objects.create_user(
        password=password, username=email, email=email, registro_funcional="123456"
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=diretoria_regional,
        perfil=perfil_cogestor_dre,
        data_inicial=hoje,
        ativo=True,
    )

    return usuario, password


@pytest.fixture
def client_autenticado_da_dre(client, usuario_da_dre):
    usuario, password = usuario_da_dre
    client.login(username=usuario.email, password=password)
    return client


@pytest.fixture
def usuario_teste_notificacao_autenticado(client, django_user_model):
    email, password = ("usuario_teste@admin.com", DJANGO_ADMIN_PASSWORD)
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_admin_dilog = baker.make("Perfil", nome=COORDENADOR_LOGISTICA, ativo=True)
    codae = baker.make("Codae")
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_admin_dilog,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)

    return user, client


@pytest.fixture
def user_administrador_medicao(django_user_model, escola):
    email = "user@escola.com"
    password = "admin@123"
    perfil_admin_medicao = baker.make(
        "Perfil", nome="ADMINISTRADOR_MEDICAO", ativo=True
    )
    usuario = django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional="123456",
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=escola,
        perfil=perfil_admin_medicao,
        data_inicial=hoje,
        ativo=True,
    )
    return usuario, password


@pytest.fixture
def client_autenticado_medicao(client, user_administrador_medicao):
    usuario, password = user_administrador_medicao
    client.login(username=usuario.email, password=password)
    return client


@pytest.fixture
def notificacao(usuario_teste_notificacao_autenticado):
    user, client = usuario_teste_notificacao_autenticado
    return baker.make(
        "Notificacao",
        tipo=Notificacao.TIPO_NOTIFICACAO_ALERTA,
        categoria=Notificacao.CATEGORIA_NOTIFICACAO_REQUISICAO_DE_ENTREGA,
        titulo="Nova requisição de entrega",
        descricao="A requisição 0000 está disponivel para envio ao distribuidor",
        usuario=user,
        lido=True,
    )


@pytest.fixture
def notificacao_de_pendencia(usuario_teste_notificacao_autenticado):
    user, client = usuario_teste_notificacao_autenticado
    return baker.make(
        "Notificacao",
        tipo=Notificacao.TIPO_NOTIFICACAO_PENDENCIA,
        categoria=Notificacao.CATEGORIA_NOTIFICACAO_GUIA_DE_REMESSA,
        titulo="Conferencia em atraso",
        descricao="A guia 0000 precisa ser conferida",
        usuario=user,
    )


@pytest.fixture
def notificacao_de_pendencia_com_requisicao(usuario_teste_notificacao_autenticado):
    distribuidor = baker.make(
        "Terceirizada",
        contatos=[baker.make("dados_comuns.Contato")],
        make_m2m=True,
        nome_fantasia="Alimentos SA",
    )
    requisicao = baker.make(
        "SolicitacaoRemessa",
        cnpj="12345678901234",
        numero_solicitacao="559890",
        sequencia_envio=1212,
        quantidade_total_guias=2,
        distribuidor=distribuidor,
    )
    user, client = usuario_teste_notificacao_autenticado
    return baker.make(
        "Notificacao",
        tipo=Notificacao.TIPO_NOTIFICACAO_PENDENCIA,
        categoria=Notificacao.CATEGORIA_NOTIFICACAO_GUIA_DE_REMESSA,
        titulo="Conferencia em atraso",
        descricao="A guia 0000 precisa ser conferida",
        usuario=user,
        requisicao=requisicao,
    )


@pytest.fixture
def arquivo():
    return SimpleUploadedFile("teste.pdf", bytes("CONTEUDO TESTE", encoding="utf-8"))


@pytest.fixture
def download(usuario_teste_notificacao_autenticado, arquivo):
    user, client = usuario_teste_notificacao_autenticado
    return baker.make(
        "CentralDeDownload",
        status=CentralDeDownload.STATUS_CONCLUIDO,
        identificador="teste.pdf",
        arquivo=arquivo,
        usuario=user,
        visto=False,
        criado_em=datetime.datetime.now(),
        msg_erro="",
    )


@pytest.fixture(
    scope="function",
    params=[
        "anexo.pdf",
        "anexo_1.xls",
        "anexo_2.xlsx",
    ],
)
def nomes_anexos_validos(request):
    return request.param


@pytest.fixture(
    scope="function",
    params=[
        "anexo.zip",
        "anexo_1.py",
        "anexo_2.js",
    ],
)
def nomes_anexos_invalidos(request):
    return request.param


@pytest.fixture
def data_maior_que_hoje():
    return datetime.date.today() + datetime.timedelta(days=10)


@pytest.fixture
def escola_cei():
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    diretoria_regional = baker.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL TESTE"
    )
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = baker.make("TipoUnidadeEscolar", iniciais="CEI DIRET")
    return baker.make(
        "Escola",
        nome="CEI DIRET TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
    )


@pytest.fixture
def periodo_escolar():
    return baker.make(models.PeriodoEscolar, nome="INTEGRAL")


@pytest.fixture
def logs_alunos_matriculados_periodo_escola(escola, periodo_escolar):
    hoje = datetime.date.today()
    ontem = hoje - datetime.timedelta(days=1)
    quatro_dias_atras = hoje - datetime.timedelta(days=4)
    quantidades = [10, 10]
    for quantidade in quantidades:
        baker.make(
            models.LogAlunosMatriculadosPeriodoEscola,
            escola=escola,
            periodo_escolar=periodo_escolar,
            quantidade_alunos=quantidade,
            tipo_turma=models.TipoTurma.REGULAR.name,
        )
    baker.make(
        models.LogAlunosMatriculadosPeriodoEscola,
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=100,
        tipo_turma=models.TipoTurma.REGULAR.name,
    )
    models.LogAlunosMatriculadosPeriodoEscola.objects.all().update(criado_em=ontem)
    models.LogAlunosMatriculadosPeriodoEscola.objects.filter(
        quantidade_alunos=100
    ).update(criado_em=quatro_dias_atras)
    return models.LogAlunosMatriculadosPeriodoEscola.objects.all()


@pytest.fixture
def logs_quantidade_dietas_autorizadas_escola_comum(escola, periodo_escolar):
    hoje = datetime.date.today()
    ontem = hoje - datetime.timedelta(days=1)
    tres_dias_atras = hoje - datetime.timedelta(days=3)
    quantidades = [10, 10]
    classificacao = baker.make(ClassificacaoDieta, nome="Tipo A")
    for quantidade in quantidades:
        baker.make(
            LogQuantidadeDietasAutorizadas,
            quantidade=quantidade,
            escola=escola,
            data=ontem,
            classificacao=classificacao,
            periodo_escolar=periodo_escolar,
        )
    baker.make(
        LogQuantidadeDietasAutorizadas,
        quantidade=50,
        escola=escola,
        data=tres_dias_atras,
        classificacao=classificacao,
        periodo_escolar=periodo_escolar,
    )
    return LogQuantidadeDietasAutorizadas.objects.all()


@pytest.fixture
def escola_cemei():
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    diretoria_regional = baker.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL TESTE"
    )
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = baker.make("TipoUnidadeEscolar", iniciais="CEMEI")
    return baker.make(
        "Escola",
        nome="CEMEI TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
    )


@pytest.fixture
def faixas_etarias_ativas():
    faixas = [
        (0, 1),
        (1, 4),
        (4, 6),
        (6, 8),
        (8, 12),
        (12, 24),
        (24, 48),
        (48, 72),
    ]
    return [
        baker.make("FaixaEtaria", inicio=inicio, fim=fim, ativo=True)
        for (inicio, fim) in faixas
    ]


@pytest.fixture
def logs_quantidade_dietas_autorizadas_escola_cei(
    escola_cei, periodo_escolar, faixas_etarias_ativas
):
    hoje = datetime.date.today()
    ontem = hoje - datetime.timedelta(days=1)
    quatro_dias_atras = hoje - datetime.timedelta(days=4)
    quantidades = [15, 15]
    classificacao = baker.make(ClassificacaoDieta, nome="Tipo B")
    for quantidade in quantidades:
        baker.make(
            LogQuantidadeDietasAutorizadasCEI,
            quantidade=quantidade,
            escola=escola_cei,
            data=ontem,
            classificacao=classificacao,
            periodo_escolar=periodo_escolar,
            faixa_etaria=faixas_etarias_ativas[0],
        )
    baker.make(
        LogQuantidadeDietasAutorizadasCEI,
        quantidade=50,
        escola=escola_cei,
        data=quatro_dias_atras,
        classificacao=classificacao,
        periodo_escolar=periodo_escolar,
        faixa_etaria=faixas_etarias_ativas[0],
    )
    return LogQuantidadeDietasAutorizadasCEI.objects.all()


@pytest.fixture
def logs_quantidade_dietas_autorizadas_escola_cemei(
    escola_cemei, periodo_escolar, faixas_etarias_ativas
):
    hoje = datetime.date.today()
    dois_dias_atras = hoje - datetime.timedelta(days=2)
    quatro_dias_atras = hoje - datetime.timedelta(days=5)
    quantidades = [25, 25]
    classificacao = baker.make(ClassificacaoDieta, nome="Tipo C")
    for quantidade in quantidades:
        baker.make(
            LogQuantidadeDietasAutorizadasCEI,
            quantidade=quantidade,
            escola=escola_cemei,
            data=dois_dias_atras,
            classificacao=classificacao,
            periodo_escolar=periodo_escolar,
            faixa_etaria=faixas_etarias_ativas[2],
        )
    baker.make(
        LogQuantidadeDietasAutorizadasCEI,
        quantidade=50,
        escola=escola_cemei,
        data=quatro_dias_atras,
        classificacao=classificacao,
        periodo_escolar=periodo_escolar,
        faixa_etaria=faixas_etarias_ativas[2],
    )
    return LogQuantidadeDietasAutorizadasCEI.objects.all()


@pytest.fixture
def obj_central_download():
    return baker.make("CentralDeDownload")


@pytest.fixture
def arquivo_temporario():
    # Cria o diretório MEDIA_ROOT se não existir
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    try:
        file_path = os.path.join(settings.MEDIA_ROOT, "test_file.pdf")
        with open(file_path, "w") as f:
            f.write("Teste de arquivo para exclusão")

        yield file_path

    finally:
        try:
            os.remove(file_path)
        except:
            pass


@pytest.fixture
def user_codae_produto(django_user_model):
    email = "test2@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_admin_gestao_produto = baker.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_GESTAO_PRODUTO,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf2",
    )
    hoje = datetime.date.today()
    codae = baker.make("Codae")
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_admin_gestao_produto,
        data_inicial=hoje,
        ativo=True,
    )
    return user


@pytest.fixture
def reclamacao_produto(django_user_model):
    email = "test@test1.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888881"
    )
    return baker.make(
        "ReclamacaoDeProduto",
        criado_por=usuario,
        status=ReclamacaoProdutoWorkflow.RESPONDIDO_TERCEIRIZADA,
    )


@pytest.fixture
def reclamacao_produto_codae_recusou(reclamacao_produto, user_codae_produto):
    kwargs = {
        "user": user_codae_produto,
        "anexos": [],
        "justificativa": "Produto não atende os requisitos.",
    }
    reclamacao_produto.status = ReclamacaoProdutoWorkflow.CODAE_RECUSOU
    reclamacao_produto.save()
    return kwargs, reclamacao_produto


@pytest.fixture
def dados_log_recusa(reclamacao_produto_codae_recusou):
    kwargs, reclamacao_produto = reclamacao_produto_codae_recusou
    log_recusa = reclamacao_produto.salvar_log_transicao(
        status_evento=LogSolicitacoesUsuario.CODAE_RECUSOU_RECLAMACAO, **kwargs
    )
    return kwargs, reclamacao_produto, log_recusa


@pytest.fixture
def dados_html(dados_log_recusa):
    _, reclamacao_produto, log_recusa = dados_log_recusa
    html = render_to_string(
        template_name="produto_codae_recusou_reclamacao.html",
        context={
            "titulo": "Reclamação Analisada",
            "reclamacao": reclamacao_produto,
            "log_recusa": log_recusa,
        },
    )
    return html


@pytest.fixture
def parser_xml():
    parser = ListXMLParser()
    xml_dicionario = """<root>
        <name>Maria Antônia</name>
        <age>10</age>
        <Str>Aluno com alergia a frutos do mar.</Str>
    </root>"""
    elemento_1 = ET.fromstring(xml_dicionario)

    xml_lista = """<root>
        <item>Paulo Antônio</item>
        <item>Maria Antônia</item>
    </root>"""
    elemento_2 = ET.fromstring(xml_lista)

    return parser, elemento_1, elemento_2


@pytest.fixture
def solicitacoes_abertas():
    baker.make(
        "SolicitacaoAberta",
        datetime_ultimo_acesso=datetime.datetime(2025, 2, 5, 12, 34, 54),
    )
    baker.make(
        "SolicitacaoAberta",
        datetime_ultimo_acesso=datetime.datetime(2025, 2, 10, 9, 18, 12),
    )
    solictacao = baker.make(
        "SolicitacaoAberta",
        datetime_ultimo_acesso=datetime.datetime(2025, 2, 10, 16, 28, 50),
    )
    return solictacao


@pytest.fixture
def user_admin_contratos(django_user_model):
    email = "test2@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="9888888"
    )
    codae = baker.make("Codae", nome="Codae - Administrador Contratos")
    perfil_admin_contratos = baker.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_CONTRATOS,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf2",
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_admin_contratos,
        data_inicial=hoje,
        ativo=True,
        content_type=ContentType.objects.get(model="codae"),
        object_id=codae.pk,
    )
    return user


@pytest.fixture
def user_dilog_abastecimento(django_user_model):
    email = "test3@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    codae = baker.make("Codae", nome="Codae - Dilog")
    perfil_dilog_abastecimento = baker.make(
        "Perfil",
        nome=constants.DILOG_ABASTECIMENTO,
        ativo=True,
        uuid="c204e9e2-5435-4b57-b0c5-c8fd0ea67b7b",
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_dilog_abastecimento,
        data_inicial=hoje,
        ativo=True,
        content_type=ContentType.objects.get(model="codae"),
        object_id=codae.pk,
    )
    return user


@pytest.fixture
def paginacao_historico_dietas():
    paginacao = HistoricoDietasPagination()
    requisicao = RequestFactory()

    return paginacao, requisicao


@pytest.fixture
def solicitacao_substituicao_cardapio(escola):
    motivo = baker.make(
        "MotivoAlteracaoCardapio", nome="Aniversariantes do mês", uuid=fake.uuid4()
    )
    periodo_escolar_integral = baker.make(
        models.PeriodoEscolar, nome="INTEGRAL", uuid=fake.uuid4()
    )
    periodo_escolar_manha = baker.make(
        models.PeriodoEscolar, nome="MANHA", uuid=fake.uuid4()
    )
    data_inicial = datetime.date(2024, 3, 1)
    data_final = datetime.date(2024, 3, 31)
    alteracao_cardapio = baker.make(
        "AlteracaoCardapio",
        escola=escola,
        motivo=motivo,
        data_inicial=data_inicial,
        data_final=data_final,
        status=PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
        uuid=fake.uuid4(),
    )
    baker.make(
        "SubstituicaoAlimentacaoNoPeriodoEscolar",
        alteracao_cardapio=alteracao_cardapio,
        periodo_escolar=periodo_escolar_integral,
        uuid=fake.uuid4(),
    )

    return {
        "escola": escola,
        "motivo": motivo,
        "substituicoes": [
            {"periodo_escolar": periodo_escolar_integral},
            {"periodo_escolar": periodo_escolar_manha},
        ],
    }


@pytest.fixture
def solicitacao_substituicao_cardapio_cei(escola):
    motivo = baker.make(
        "MotivoAlteracaoCardapio", nome="Aniversariantes do mês", uuid=fake.uuid4()
    )
    periodo_escolar_integral = baker.make(
        models.PeriodoEscolar, nome="INTEGRAL", uuid=fake.uuid4()
    )
    periodo_escolar_manha = baker.make(
        models.PeriodoEscolar, nome="MANHA", uuid=fake.uuid4()
    )
    data = datetime.date(2024, 3, 1)
    alteracao_cardapio = baker.make(
        "AlteracaoCardapioCEI",
        escola=escola,
        motivo=motivo,
        data=data,
        status=PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
        uuid=fake.uuid4(),
    )
    baker.make(
        "SubstituicaoAlimentacaoNoPeriodoEscolarCEI",
        alteracao_cardapio=alteracao_cardapio,
        periodo_escolar=periodo_escolar_integral,
        uuid=fake.uuid4(),
    )

    return {
        "escola": escola.uuid,
        "motivo": motivo.uuid,
        "substituicoes": [
            {"periodo_escolar": periodo_escolar_integral.uuid},
            {"periodo_escolar": periodo_escolar_manha.uuid},
        ],
    }


@pytest.fixture
def motivo_alteracao_cardapio_lanche_emergencial():
    return baker.make(
        "MotivoAlteracaoCardapio",
        nome="Lanche Emergencial",
        uuid="1ddec320-cd24-4cf4-9666-3e7b3a2b903c",
    )


@pytest.fixture
def escola_cemei_1():
    return baker.make(
        "Escola",
        uuid="1fc5fca2-2694-4781-be65-8331716c74a0",
        tipo_gestao__nome="TERC TOTAL",
    )


@pytest.fixture
def tipo_alimentacao_refeicao():
    return baker.make("cardapio.TipoAlimentacao", nome="Refeição")


@pytest.fixture
def tipo_alimentacao_lanche():
    return baker.make("cardapio.TipoAlimentacao", nome="Lanche")


@pytest.fixture
def tipo_alimentacao_lanche_emergencial():
    return baker.make("cardapio.TipoAlimentacao", nome="Lanche Emergencial")


@pytest.fixture
def periodo_manha():
    return baker.make(
        "escola.PeriodoEscolar",
        nome="MANHA",
        uuid="42325516-aebd-4a3d-97c0-2a77c317c6be",
    )


@pytest.fixture
def periodo_tarde():
    return baker.make(
        "escola.PeriodoEscolar",
        nome="TARDE",
        uuid="88966d6a-f9d5-4986-9ffb-25b6f41b0795",
    )


@pytest.fixture
def alteracao_cemei(
    escola_cemei_1,
    motivo_alteracao_cardapio_lanche_emergencial,
    tipo_alimentacao_refeicao,
    tipo_alimentacao_lanche_emergencial,
    periodo_manha,
):
    alteracao_cemei = baker.make(
        "AlteracaoCardapioCEMEI",
        escola=escola_cemei_1,
        alunos_cei_e_ou_emei="EMEI",
        alterar_dia="2025-04-28",
        motivo=motivo_alteracao_cardapio_lanche_emergencial,
        status="CODAE_AUTORIZADO",
    )
    subs1 = baker.make(
        "SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI",
        alteracao_cardapio=alteracao_cemei,
        periodo_escolar=periodo_manha,
    )
    subs1.tipos_alimentacao_de.set([tipo_alimentacao_refeicao])
    subs1.tipos_alimentacao_para.set([tipo_alimentacao_lanche_emergencial])
    subs1.save()
    baker.make(
        "DataIntervaloAlteracaoCardapioCEMEI",
        data="2025-04-28",
        alteracao_cardapio_cemei=alteracao_cemei,
    )
    return alteracao_cemei


@pytest.fixture
def client_autenticado_vinculo_escola_cemei(client, django_user_model, escola_cemei_1):
    email = "test@test1.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888889"
    )
    perfil_diretor = baker.make("Perfil", nome="DIRETOR_UE", ativo=True)
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=escola_cemei_1,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )

    client.login(username=email, password=password)
    return client, user


@pytest.fixture
def lotes():
    cria_diretorias_regionais()
    cria_tipos_gestao()
    cria_terceirizadas()
    cria_lotes()


@pytest.fixture
def solicitacao_sem_lancamento(escola):
    return baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola,
        mes="04",
        ano="2025",
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
    )


@pytest.fixture
def medicao_sem_lancamento(solicitacao_sem_lancamento):

    return baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_sem_lancamento,
        periodo_escolar=baker.make("PeriodoEscolar", nome="MANHA"),
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
        grupo=None,
    )


@pytest.fixture
def solicitacao_para_corecao(solicitacao_sem_lancamento, medicao_sem_lancamento):
    medicao_sem_lancamento.solicitacao = solicitacao_sem_lancamento

    solicitacao_sem_lancamento.status = (
        SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE
    )
    medicao_sem_lancamento.status = (
        SolicitacaoMedicaoInicialWorkflow.MEDICAO_SEM_LANCAMENTOS
    )

    medicao_sem_lancamento.save()
    solicitacao_sem_lancamento.save()

    return solicitacao_sem_lancamento
