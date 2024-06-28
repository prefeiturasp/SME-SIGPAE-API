import base64
import datetime

import pytest
from faker import Faker
from model_mommy import mommy
from pytest_factoryboy import register

from .dados_comuns import constants
from .dados_comuns.fixtures.factories.dados_comuns_factories import (
    LogSolicitacoesUsuarioFactory,
)
from .dados_comuns.models import TemplateMensagem
from .escola.fixtures.factories.escola_factory import (
    DiretoriaRegionalFactory,
    EscolaFactory,
    LogAlunosMatriculadosPeriodoEscolaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
    TipoUnidadeEscolarFactory,
)
from .imr.fixtures.factories.imr_base_factory import (
    AnexosFormularioBaseFactory,
    CategoriaOcorrenciaFactory,
    EquipamentoFactory,
    FaixaPontuacaoFactory,
    FormularioDiretorFactory,
    FormularioOcorrenciasBaseFactory,
    FormularioSupervisaoFactory,
    InsumoFactory,
    MobiliarioFactory,
    ObrigacaoPenalidadeFactory,
    OcorrenciaNaoSeAplicaFactory,
    ParametrizacaoOcorrenciaFactory,
    PeriodoVisitaFactory,
    ReparoEAdaptacaoFactory,
    RespostaCampoNumericoFactory,
    RespostaCampoTextoSimplesFactory,
    TipoGravidadeFactory,
    TipoOcorrenciaFactory,
    TipoPenalidadeFactory,
    TipoPerguntaParametrizacaoOcorrenciaFactory,
    TipoRespostaModeloFactory,
    UtensilioCozinhaFactory,
    UtensilioMesaFactory,
)
from .imr.fixtures.factories.imr_importacao_planilha_base_factory import (
    ImportacaoPlanilhaTipoOcorrenciaFactory,
    ImportacaoPlanilhaTipoPenalidadeFactory,
)
from .inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
)
from .medicao_inicial.fixtures.factories.solicitacao_medicao_inicial_base_factory import (
    SolicitacaoMedicaoInicialFactory,
)
from .perfil.fixtures.factories.perfil_base_factories import UsuarioFactory
from .pre_recebimento.fixtures.factories.cronograma_factory import (
    CronogramaFactory,
    EtapasDoCronogramaFactory,
    LaboratorioFactory,
)
from .pre_recebimento.fixtures.factories.documentos_de_recebimento_factory import (
    DataDeFabricaoEPrazoFactory,
    DocumentoDeRecebimentoFactory,
    TipoDeDocumentoDeRecebimentoFactory,
)
from .pre_recebimento.fixtures.factories.ficha_tecnica_do_produto_factory import (
    AnaliseFichaTecnicaFactory,
    FichaTecnicaFactory,
)
from .pre_recebimento.fixtures.factories.layout_embalagem_factory import (
    LayoutDeEmbalagemFactory,
)
from .pre_recebimento.fixtures.factories.unidade_medida_factory import (
    UnidadeMedidaFactory,
)
from .produto.fixtures.factories.produto_factory import (
    FabricanteFactory,
    InformacaoNutricionalFactory,
    MarcaFactory,
    ProdutoLogisticaFactory,
    ProdutoTerceirizadaFactory,
    TipoDeInformacaoNutricionalFactory,
)
from .recebimento.fixtures.factories.ficha_de_recebimento_factory import (
    ArquivoFichaDeRecebimentoFactory,
    FichaDeRecebimentoFactory,
    VeiculoFichaDeRecebimentoFactory,
)
from .recebimento.fixtures.factories.questao_conferencia_factory import (
    QuestaoConferenciaFactory,
)
from .recebimento.fixtures.factories.questoes_por_produto_factory import (
    QuestoesPorProdutoFactory,
)
from .terceirizada.fixtures.factories.terceirizada_factory import (
    ContratoFactory,
    EditalFactory,
    EmpresaFactory,
)

f = Faker(locale="pt-Br")

register(CronogramaFactory)
register(DocumentoDeRecebimentoFactory)
register(EmpresaFactory)
register(FabricanteFactory)
register(FichaTecnicaFactory)
register(LaboratorioFactory)
register(MarcaFactory)
register(ProdutoLogisticaFactory)
register(ProdutoTerceirizadaFactory)
register(TipoDeDocumentoDeRecebimentoFactory)
register(UnidadeMedidaFactory)
register(EtapasDoCronogramaFactory)
register(TipoDeInformacaoNutricionalFactory)
register(InformacaoNutricionalFactory)
register(LayoutDeEmbalagemFactory)
register(AnaliseFichaTecnicaFactory)
register(QuestaoConferenciaFactory)
register(QuestoesPorProdutoFactory)
register(EditalFactory)
register(TipoPenalidadeFactory)
register(TipoGravidadeFactory)
register(CategoriaOcorrenciaFactory)
register(TipoOcorrenciaFactory)
register(FichaDeRecebimentoFactory)
register(ContratoFactory)
register(FaixaPontuacaoFactory)
register(DataDeFabricaoEPrazoFactory)
register(VeiculoFichaDeRecebimentoFactory)
register(ArquivoFichaDeRecebimentoFactory)
register(UtensilioMesaFactory)
register(UtensilioCozinhaFactory)
register(EquipamentoFactory)
register(MobiliarioFactory)
register(ReparoEAdaptacaoFactory)
register(InsumoFactory)
register(TipoPerguntaParametrizacaoOcorrenciaFactory)
register(TipoRespostaModeloFactory)
register(ParametrizacaoOcorrenciaFactory)
register(ObrigacaoPenalidadeFactory)
register(EscolaFactory)
register(PeriodoEscolarFactory)
register(LogAlunosMatriculadosPeriodoEscolaFactory)
register(DiretoriaRegionalFactory)
register(TipoUnidadeEscolarFactory)
register(SolicitacaoMedicaoInicialFactory)
register(ImportacaoPlanilhaTipoPenalidadeFactory)
register(ImportacaoPlanilhaTipoOcorrenciaFactory)
register(PeriodoVisitaFactory)
register(UsuarioFactory)
register(FormularioOcorrenciasBaseFactory)
register(AnexosFormularioBaseFactory)
register(FormularioSupervisaoFactory)
register(FormularioDiretorFactory)
register(LoteFactory)
register(LogSolicitacoesUsuarioFactory)
register(RespostaCampoTextoSimplesFactory)
register(RespostaCampoNumericoFactory)
register(OcorrenciaNaoSeAplicaFactory)


@pytest.fixture
def client_autenticado(client, django_user_model):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_admin_django(client, django_user_model):
    email = "admDoDjango@xxx.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional="8888888",
        is_staff=True,
        is_superuser=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_escola(client, django_user_model):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    lote = mommy.make("Lote", nome="lote", iniciais="lt")
    perfil_diretor = mommy.make(
        "Perfil",
        nome="DIRETOR_UE",
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )
    diretoria_regional = mommy.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL IPIRANGA",
        uuid="7da9acec-48e1-430c-8a5c-1f1efc666fad",
    )
    cardapio1 = mommy.make("cardapio.Cardapio", data=datetime.date(2019, 10, 11))
    cardapio2 = mommy.make("cardapio.Cardapio", data=datetime.date(2019, 10, 15))
    tipo_unidade_escolar = mommy.make(
        "escola.TipoUnidadeEscolar",
        iniciais=f.name()[:10],
        cardapios=[cardapio1, cardapio2],
        uuid="56725de5-89d3-4edf-8633-3e0b5c99e9d4",
    )
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    escola = mommy.make(
        "Escola",
        nome="EMEI NOE AZEVEDO, PROF",
        uuid="b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd",
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        codigo_eol="256341",
        tipo_unidade=tipo_unidade_escolar,
        lote=lote,
    )
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    mommy.make(
        TemplateMensagem,
        assunto="TESTE",
        tipo=TemplateMensagem.DIETA_ESPECIAL,
        template_html="@id @criado_em @status @link",
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_diretoria_regional(client, django_user_model):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_cogestor = mommy.make("Perfil", nome=constants.COGESTOR_DRE, ativo=True)
    diretoria_regional = mommy.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL IPIRANGA"
    )
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=diretoria_regional,
        perfil=perfil_cogestor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_codae_gestao_alimentacao(client, django_user_model):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_admin_gestao_alimentacao = mommy.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
        ativo=True,
    )
    codae = mommy.make("Codae")
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_admin_gestao_alimentacao,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_dilog(client, django_user_model):
    email = "dilog@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional=str(f.unique.random_int(min=100000, max=999999)),
    )
    perfil_admin_dilog = mommy.make(
        "Perfil", nome=constants.COORDENADOR_LOGISTICA, ativo=True
    )
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
    return client


@pytest.fixture
def client_autenticado_codae_dilog(client, django_user_model):
    email = "codaedilog@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional=str(f.unique.random_int(min=100000, max=999999)),
    )
    perfil_admin_dilog = mommy.make(
        "Perfil", nome=constants.COORDENADOR_CODAE_DILOG_LOGISTICA, ativo=True
    )
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
    return client


@pytest.fixture
def client_autenticado_representante_codae(client, django_user_model):
    email = "representante@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username="8888888",
        password=password,
        email=email,
        registro_funcional=str(f.unique.random_int(min=100000, max=999999)),
    )
    perfil_admin_dilog = mommy.make(
        "Perfil", nome=constants.ADMINISTRADOR_REPRESENTANTE_CODAE, ativo=True
    )
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
    return client


@pytest.fixture
def client_autenticado_qualidade(client, django_user_model):
    email = "qualidade@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional=str(f.unique.random_int(min=100000, max=999999)),
    )
    perfil_admin_qualidade = mommy.make(
        "Perfil", nome=constants.DILOG_QUALIDADE, ativo=True
    )
    codae = mommy.make("Codae")
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_admin_qualidade,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_distribuidor(client, django_user_model):
    email = "distribuidor@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email
    )
    perfil_admin_distribuidor = mommy.make(
        "Perfil", nome=constants.ADMINISTRADOR_EMPRESA, ativo=True
    )
    distribuidor = mommy.make("Terceirizada", tipo_servico="DISTRIBUIDOR_ARMAZEM")
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=distribuidor,
        perfil=perfil_admin_distribuidor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_fornecedor(client, django_user_model, empresa):
    email = "fornecedor@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email
    )
    perfil_admin_fornecedor = mommy.make(
        "Perfil", nome=constants.ADMINISTRADOR_EMPRESA, ativo=True
    )
    fornecedor = empresa
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=fornecedor,
        perfil=perfil_admin_fornecedor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_escola_abastecimento(client, django_user_model, escola):
    email = "escolaab@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional=str(f.unique.random_int(min=100000, max=999999)),
    )
    perfil_admin_escola_abastecimento = mommy.make(
        "Perfil", nome=constants.ADMINISTRADOR_UE, ativo=True
    )
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_admin_escola_abastecimento,
        data_inicial=hoje,
        ativo=True,
    )
    mommy.make(
        TemplateMensagem,
        assunto="TESTE",
        tipo=TemplateMensagem.DIETA_ESPECIAL,
        template_html="@id @criado_em @status @link",
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_dilog_cronograma(client, django_user_model):
    email = "cronograma@teste.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional=str(f.unique.random_int(min=100000, max=999999)),
    )
    perfil_admin_dilog = mommy.make(
        "Perfil", nome=constants.DILOG_CRONOGRAMA, ativo=True
    )
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
    return client


@pytest.fixture
def client_autenticado_dinutre_diretoria(client, django_user_model):
    email = "dinutrediretoria@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional=str(f.unique.random_int(min=100000, max=999999)),
    )
    perfil_admin_dilog = mommy.make(
        "Perfil", nome=constants.DINUTRE_DIRETORIA, ativo=True
    )
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
    return client


@pytest.fixture
def client_autenticado_dilog_diretoria(client, django_user_model):
    email = "dilogdiretoria@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional=str(f.unique.random_int(min=100000, max=999999)),
    )
    perfil_dilog_diretoria = mommy.make(
        "Perfil", nome=constants.DILOG_DIRETORIA, ativo=True
    )
    codae = mommy.make("Codae")
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_dilog_diretoria,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def diretoria_regional_ip():
    return mommy.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL IPIRANGA",
        iniciais="IP",
        uuid="7da9acec-48e1-430c-8a5c-1f1efc666fad",
        codigo_eol=987656,
    )


@pytest.fixture
def escola_um(diretoria_regional_ip):
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make("Lote", terceirizada=terceirizada)
    return mommy.make(
        "Escola",
        lote=lote,
        diretoria_regional=diretoria_regional_ip,
        uuid="a7b9cf39-ab0a-4c6f-8e42-230243f9763f",
    )


@pytest.fixture
def inclusoes_continuas(terceirizada, escola_um):
    inclusao = mommy.make(
        "InclusaoAlimentacaoContinua",
        escola=escola_um,
        status=InclusaoAlimentacaoContinua.workflow_class.CODAE_AUTORIZADO,
    )
    return inclusao


@pytest.fixture
def inclusoes_normais(terceirizada, escola_um):
    return mommy.make(
        "GrupoInclusaoAlimentacaoNormal",
        escola=escola_um,
        status=GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
    )


@pytest.fixture
def alteracoes_cardapio(terceirizada, escola_um):
    return mommy.make("AlteracaoCardapio")


@pytest.fixture
def arquivo_pdf_base64():
    arquivo = f"data:aplication/pdf;base64,{base64.b64encode(b'arquivo pdf teste').decode('utf-8')}"
    return arquivo


@pytest.fixture
def arquivo_base64():
    arquivo = f"data:image/jpeg;base64,{base64.b64encode(b'arquivo imagem teste').decode('utf-8')}"
    return arquivo
