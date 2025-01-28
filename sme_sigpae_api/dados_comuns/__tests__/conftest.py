import datetime
import os

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from faker import Faker
from model_mommy import mommy

from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.fluxo_status import ReclamacaoProdutoWorkflow
from sme_sigpae_api.dieta_especial.models import (
    ClassificacaoDieta,
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
)

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
    return mommy.make(TemplateMensagem, tipo=TemplateMensagem.ALTERACAO_CARDAPIO)


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture
def validators_models_object():
    return mommy.make("dados_comuns.TemplateMensagem", assunto="TESTE")


@pytest.fixture
def validators_valor_str():
    return {"texto": "Nome", "none": None}


@pytest.fixture
def tipo_unidade():
    return mommy.make("TipoUnidadeEscolar", iniciais="EMEF")


@pytest.fixture
def escola(tipo_unidade):
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    return mommy.make(
        models.Escola,
        nome=fake.name(),
        codigo_eol=fake.name()[:6],
        tipo_unidade=tipo_unidade,
        tipo_gestao=tipo_gestao,
    )


@pytest.fixture
def dia_suspensao_atividades(escola):
    return mommy.make(
        "DiaSuspensaoAtividades",
        tipo_unidade=escola.tipo_unidade,
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

    codae = mommy.make(
        "Codae", nome="CODAE", uuid="b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd"
    )

    perfil_coordenador = mommy.make(
        "Perfil",
        nome="COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA",
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )
    mommy.make("Lote", uuid="143c2550-8bf0-46b4-b001-27965cfcd107")
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_coordenador,
        data_inicial=hoje,
        ativo=True,
    )

    return client


@pytest.fixture
def client_autenticado_da_escola(client, django_user_model, escola):
    email = "user@escola.com"
    password = "admin@123"
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
def usuario_teste_notificacao_autenticado(client, django_user_model):
    email, password = ("usuario_teste@admin.com", DJANGO_ADMIN_PASSWORD)
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_admin_dilog = mommy.make("Perfil", nome=COORDENADOR_LOGISTICA, ativo=True)
    codae = mommy.make("Codae")
    hoje = datetime.date.today()
    mommy.make(
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
def notificacao(usuario_teste_notificacao_autenticado):
    user, client = usuario_teste_notificacao_autenticado
    return mommy.make(
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
    return mommy.make(
        "Notificacao",
        tipo=Notificacao.TIPO_NOTIFICACAO_PENDENCIA,
        categoria=Notificacao.CATEGORIA_NOTIFICACAO_GUIA_DE_REMESSA,
        titulo="Conferencia em atraso",
        descricao="A guia 0000 precisa ser conferida",
        usuario=user,
    )


@pytest.fixture
def notificacao_de_pendencia_com_requisicao(usuario_teste_notificacao_autenticado):
    distribuidor = mommy.make(
        "Terceirizada",
        contatos=[mommy.make("dados_comuns.Contato")],
        make_m2m=True,
        nome_fantasia="Alimentos SA",
    )
    requisicao = mommy.make(
        "SolicitacaoRemessa",
        cnpj="12345678901234",
        numero_solicitacao="559890",
        sequencia_envio=1212,
        quantidade_total_guias=2,
        distribuidor=distribuidor,
    )
    user, client = usuario_teste_notificacao_autenticado
    return mommy.make(
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
    return mommy.make(
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
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make("Lote", terceirizada=terceirizada)
    diretoria_regional = mommy.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL TESTE"
    )
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = mommy.make("TipoUnidadeEscolar", iniciais="CEI DIRET")
    return mommy.make(
        "Escola",
        nome="CEI DIRET TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
    )


@pytest.fixture
def periodo_escolar():
    return mommy.make(models.PeriodoEscolar, nome="INTEGRAL")


@pytest.fixture
def logs_alunos_matriculados_periodo_escola(escola, periodo_escolar):
    hoje = datetime.date.today()
    ontem = hoje - datetime.timedelta(days=1)
    quatro_dias_atras = hoje - datetime.timedelta(days=4)
    quantidades = [10, 10]
    for quantidade in quantidades:
        mommy.make(
            models.LogAlunosMatriculadosPeriodoEscola,
            escola=escola,
            periodo_escolar=periodo_escolar,
            quantidade_alunos=quantidade,
            tipo_turma=models.TipoTurma.REGULAR.name,
        )
    mommy.make(
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
    classificacao = mommy.make(ClassificacaoDieta, nome="Tipo A")
    for quantidade in quantidades:
        mommy.make(
            LogQuantidadeDietasAutorizadas,
            quantidade=quantidade,
            escola=escola,
            data=ontem,
            classificacao=classificacao,
            periodo_escolar=periodo_escolar,
        )
    mommy.make(
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
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make("Lote", terceirizada=terceirizada)
    diretoria_regional = mommy.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL TESTE"
    )
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = mommy.make("TipoUnidadeEscolar", iniciais="CEMEI")
    return mommy.make(
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
        mommy.make("FaixaEtaria", inicio=inicio, fim=fim, ativo=True)
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
    classificacao = mommy.make(ClassificacaoDieta, nome="Tipo B")
    for quantidade in quantidades:
        mommy.make(
            LogQuantidadeDietasAutorizadasCEI,
            quantidade=quantidade,
            escola=escola_cei,
            data=ontem,
            classificacao=classificacao,
            periodo_escolar=periodo_escolar,
            faixa_etaria=faixas_etarias_ativas[0],
        )
    mommy.make(
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
    classificacao = mommy.make(ClassificacaoDieta, nome="Tipo C")
    for quantidade in quantidades:
        mommy.make(
            LogQuantidadeDietasAutorizadasCEI,
            quantidade=quantidade,
            escola=escola_cemei,
            data=dois_dias_atras,
            classificacao=classificacao,
            periodo_escolar=periodo_escolar,
            faixa_etaria=faixas_etarias_ativas[2],
        )
    mommy.make(
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
    return mommy.make("CentralDeDownload")


@pytest.fixture
def arquivo_temporario():
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
    perfil_admin_gestao_produto = mommy.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_GESTAO_PRODUTO,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf2",
    )
    hoje = datetime.date.today()
    codae = mommy.make("Codae")
    mommy.make(
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
    return mommy.make(
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
