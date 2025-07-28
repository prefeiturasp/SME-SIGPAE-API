import base64
import datetime
import json

import pytest
from faker import Faker
from model_bakery import baker
from model_bakery.random_gen import gen_integer
from pytest_factoryboy import register

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.fixtures.factories.alteracao_tipo_alimentacao_factory import (
    AlteracaoCardapioFactory,
    DataIntervaloAlteracaoCardapioFactory,
    MotivoAlteracaoCardapioFactory,
    SubstituicaoAlimentacaoNoPeriodoEscolarFactory,
)
from sme_sigpae_api.cardapio.base.fixtures.factories.base_factory import (
    TipoAlimentacaoFactory,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolarFactory,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.fixtures.factories.fabricante_ficha_tecnica_factory import (
    FabricanteFichaTecnicaFactory,
)
from sme_sigpae_api.recebimento.fixtures.factories.ocorrencia_ficha_recebimento_factory import OcorrenciaFichaRecebimentoFactory
from sme_sigpae_api.recebimento.fixtures.factories.questao_ficha_recebimento_factory import (
    QuestaoFichaRecebimentoFactory,
)

from .dados_comuns import constants
from .dados_comuns.fixtures.factories.dados_comuns_factories import (
    ContatoFactory,
    LogSolicitacoesUsuarioFactory,
)
from .dados_comuns.models import TemplateMensagem
from .dieta_especial.fixtures.factories.dieta_especial_base_factory import (
    ClassificacaoDietaFactory,
    LogQuantidadeDietasAutorizadasCEIFactory,
    LogQuantidadeDietasAutorizadasFactory,
    SolicitacaoDietaEspecialFactory,
)
from .eol_servico.utils import EOLServicoSGP
from .escola.fixtures.factories.dia_suspensao_atividades_factory import (
    DiaSuspensaoAtividadesFactory,
)
from .escola.fixtures.factories.escola_factory import (
    AlunoFactory,
    AlunosMatriculadosPeriodoEscolaFactory,
    DiretoriaRegionalFactory,
    EscolaFactory,
    FaixaEtariaFactory,
    HistoricoMatriculaAlunoFactory,
    LogAlunosMatriculadosFaixaEtariaDiaFactory,
    LogAlunosMatriculadosPeriodoEscolaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
    TipoGestaoFactory,
    TipoUnidadeEscolarFactory,
)
from .imr.fixtures.factories.imr_base_factory import (
    AnexosFormularioBaseFactory,
    CategoriaOcorrenciaFactory,
    EditalEquipamentoFactory,
    EditalInsumoFactory,
    EditalMobiliarioFactory,
    EditalReparoEAdaptacaoFactory,
    EditalUtensilioCozinhaFactory,
    EditalUtensilioMesaFactory,
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
from .inclusao_alimentacao.fixtures.factories.base_factory import (
    DiasMotivosInclusaoDeAlimentacaoCEIFactory,
    DiasMotivosInclusaoDeAlimentacaoCEMEIFactory,
    GrupoInclusaoAlimentacaoNormalFactory,
    InclusaoAlimentacaoContinuaFactory,
    InclusaoAlimentacaoDaCEIFactory,
    InclusaoAlimentacaoNormalFactory,
    InclusaoDeAlimentacaoCEMEIFactory,
    MotivoInclusaoContinuaFactory,
    MotivoInclusaoNormalFactory,
    QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEIFactory,
    QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEIFactory,
    QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEIFactory,
    QuantidadePorPeriodoFactory,
)
from .inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
)
from .kit_lanche.fixtures.factories.base_factory import (
    FaixaEtariaSolicitacaoKitLancheCEIAvulsaFactory,
    KitLancheFactory,
    SolicitacaoKitLancheAvulsaFactory,
    SolicitacaoKitLancheCEIAvulsaFactory,
    SolicitacaoKitLancheFactory,
)
from .medicao_inicial.fixtures.factories.base_factory import (
    CategoriaMedicaoFactory,
    GrupoMedicaoFactory,
    TipoContagemAlimentacaoFactory,
)
from .medicao_inicial.fixtures.factories.solicitacao_medicao_inicial_base_factory import (
    MedicaoFactory,
    SolicitacaoMedicaoInicialFactory,
    ValorMedicaoFactory,
)
from .perfil.fixtures.factories.perfil_base_factories import UsuarioFactory
from .pre_recebimento.base.fixtures.factories.unidade_medida_factory import (
    UnidadeMedidaFactory,
)
from .pre_recebimento.cronograma_entrega.fixtures.factories.cronograma_factory import (
    CronogramaFactory,
    EtapasDoCronogramaFactory,
)
from .pre_recebimento.documento_recebimento.fixtures.factories.documentos_de_recebimento_factory import (
    ArquivoDoTipoDeDocumentoFactory,
    DataDeFabricaoEPrazoFactory,
    DocumentoDeRecebimentoFactory,
    TipoDeDocumentoDeRecebimentoFactory,
)
from .pre_recebimento.ficha_tecnica.fixtures.factories.ficha_tecnica_do_produto_factory import (
    AnaliseFichaTecnicaFactory,
    FichaTecnicaFactory,
)
from .pre_recebimento.layout_embalagem.fixtures.factories.layout_embalagem_factory import (
    LayoutDeEmbalagemFactory,
)
from .pre_recebimento.qualidade.fixtures.factories.laboratorio_factory import (
    LaboratorioFactory,
)
from .pre_recebimento.qualidade.fixtures.factories.tipo_embalagem_qld_factory import (
    TipoEmbalagemQldFactory,
)
from .produto.fixtures.factories.produto_factory import (
    DataHoraVinculoProdutoEditalFactory,
    FabricanteFactory,
    HomologacaoProdutoFactory,
    InformacaoNutricionalFactory,
    MarcaFactory,
    ProdutoEditalFactory,
    ProdutoFactory,
    ProdutoLogisticaFactory,
    ProdutoTerceirizadaFactory,
    ReclamacaoDeProdutoFactory,
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
register(FabricanteFichaTecnicaFactory)
register(LaboratorioFactory)
register(MarcaFactory)
register(ProdutoLogisticaFactory)
register(ProdutoTerceirizadaFactory)
register(TipoDeDocumentoDeRecebimentoFactory)
register(ArquivoDoTipoDeDocumentoFactory)
register(UnidadeMedidaFactory)
register(EtapasDoCronogramaFactory)
register(TipoDeInformacaoNutricionalFactory)
register(InformacaoNutricionalFactory)
register(LayoutDeEmbalagemFactory)
register(TipoEmbalagemQldFactory)
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
register(OcorrenciaFichaRecebimentoFactory)
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
register(EditalInsumoFactory)
register(EditalReparoEAdaptacaoFactory)
register(EditalMobiliarioFactory)
register(EditalEquipamentoFactory)
register(EditalUtensilioMesaFactory)
register(EditalUtensilioCozinhaFactory)
register(InclusaoAlimentacaoDaCEIFactory)
register(FaixaEtariaFactory)
register(QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEIFactory)
register(DiasMotivosInclusaoDeAlimentacaoCEIFactory)
register(MotivoInclusaoNormalFactory)
register(GrupoInclusaoAlimentacaoNormalFactory)
register(InclusaoAlimentacaoNormalFactory)
register(QuantidadePorPeriodoFactory)
register(KitLancheFactory)
register(SolicitacaoKitLancheFactory)
register(SolicitacaoKitLancheAvulsaFactory)
register(AlunoFactory)
register(SolicitacaoDietaEspecialFactory)
register(ClassificacaoDietaFactory)
register(InclusaoDeAlimentacaoCEMEIFactory)
register(QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEIFactory)
register(QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEIFactory)
register(DiasMotivosInclusaoDeAlimentacaoCEMEIFactory)
register(TipoAlimentacaoFactory)
register(VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolarFactory)
register(MotivoAlteracaoCardapioFactory)
register(AlteracaoCardapioFactory)
register(DataIntervaloAlteracaoCardapioFactory)
register(SubstituicaoAlimentacaoNoPeriodoEscolarFactory)
register(ProdutoFactory)
register(HomologacaoProdutoFactory)
register(ProdutoEditalFactory)
register(DataHoraVinculoProdutoEditalFactory)
register(ReclamacaoDeProdutoFactory)
register(DiaSuspensaoAtividadesFactory)
register(LogQuantidadeDietasAutorizadasFactory)
register(LogQuantidadeDietasAutorizadasCEIFactory)
register(HistoricoMatriculaAlunoFactory)
register(QuestaoFichaRecebimentoFactory)
register(TipoGestaoFactory)
register(LogAlunosMatriculadosFaixaEtariaDiaFactory)
register(ContatoFactory)
register(TipoContagemAlimentacaoFactory)
register(GrupoMedicaoFactory)
register(CategoriaMedicaoFactory)
register(MedicaoFactory)
register(ValorMedicaoFactory)
register(InclusaoAlimentacaoContinuaFactory)
register(MotivoInclusaoContinuaFactory)
register(SolicitacaoKitLancheCEIAvulsaFactory)
register(FaixaEtariaSolicitacaoKitLancheCEIAvulsaFactory)
register(AlunosMatriculadosPeriodoEscolaFactory)


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
    lote = baker.make("Lote", nome="lote", iniciais="lt")
    perfil_diretor = baker.make(
        "Perfil",
        nome="DIRETOR_UE",
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )
    diretoria_regional = baker.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL IPIRANGA",
        uuid="7da9acec-48e1-430c-8a5c-1f1efc666fad",
    )
    cardapio1 = baker.make("cardapio.Cardapio", data=datetime.date(2019, 10, 11))
    cardapio2 = baker.make("cardapio.Cardapio", data=datetime.date(2019, 10, 15))
    tipo_unidade_escolar = baker.make(
        "escola.TipoUnidadeEscolar",
        iniciais=f.name()[:10],
        cardapios=[cardapio1, cardapio2],
        uuid="56725de5-89d3-4edf-8633-3e0b5c99e9d4",
    )
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    escola = baker.make(
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
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    baker.make(
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
    perfil_cogestor = baker.make("Perfil", nome=constants.COGESTOR_DRE, ativo=True)
    diretoria_regional = baker.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL IPIRANGA"
    )
    hoje = datetime.date.today()
    baker.make(
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
    perfil_admin_gestao_alimentacao = baker.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
        ativo=True,
    )
    codae = baker.make("Codae")
    hoje = datetime.date.today()
    baker.make(
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
    perfil_admin_dilog = baker.make(
        "Perfil", nome=constants.COORDENADOR_LOGISTICA, ativo=True
    )
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
    perfil_admin_dilog = baker.make(
        "Perfil", nome=constants.COORDENADOR_CODAE_DILOG_LOGISTICA, ativo=True
    )
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
    perfil_admin_dilog = baker.make(
        "Perfil", nome=constants.ADMINISTRADOR_REPRESENTANTE_CODAE, ativo=True
    )
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
    perfil_admin_qualidade = baker.make(
        "Perfil", nome=constants.DILOG_QUALIDADE, ativo=True
    )
    codae = baker.make("Codae")
    hoje = datetime.date.today()
    baker.make(
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
    perfil_admin_distribuidor = baker.make(
        "Perfil", nome=constants.ADMINISTRADOR_EMPRESA, ativo=True
    )
    distribuidor = baker.make("Terceirizada", tipo_servico="DISTRIBUIDOR_ARMAZEM")
    hoje = datetime.date.today()
    baker.make(
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
    perfil_admin_fornecedor = baker.make(
        "Perfil", nome=constants.ADMINISTRADOR_EMPRESA, ativo=True
    )
    fornecedor = empresa
    hoje = datetime.date.today()
    baker.make(
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
    perfil_admin_escola_abastecimento = baker.make(
        "Perfil", nome=constants.ADMINISTRADOR_UE, ativo=True
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_admin_escola_abastecimento,
        data_inicial=hoje,
        ativo=True,
    )
    baker.make(
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
    perfil_admin_dilog = baker.make(
        "Perfil", nome=constants.DILOG_CRONOGRAMA, ativo=True
    )
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
    perfil_admin_dilog = baker.make(
        "Perfil", nome=constants.DINUTRE_DIRETORIA, ativo=True
    )
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
    perfil_dilog_diretoria = baker.make(
        "Perfil", nome=constants.DILOG_DIRETORIA, ativo=True
    )
    codae = baker.make("Codae")
    hoje = datetime.date.today()
    baker.make(
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
    return baker.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL IPIRANGA",
        iniciais="IP",
        uuid="7da9acec-48e1-430c-8a5c-1f1efc666fad",
        codigo_eol=987656,
    )


@pytest.fixture
def escola_um(diretoria_regional_ip):
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    return baker.make(
        "Escola",
        lote=lote,
        diretoria_regional=diretoria_regional_ip,
        uuid="a7b9cf39-ab0a-4c6f-8e42-230243f9763f",
    )


@pytest.fixture
def inclusoes_continuas(terceirizada, escola_um):
    inclusao = baker.make(
        "InclusaoAlimentacaoContinua",
        escola=escola_um,
        status=InclusaoAlimentacaoContinua.workflow_class.CODAE_AUTORIZADO,
    )
    return inclusao


@pytest.fixture
def inclusoes_normais(terceirizada, escola_um):
    return baker.make(
        "GrupoInclusaoAlimentacaoNormal",
        escola=escola_um,
        status=GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
    )


@pytest.fixture
def alteracoes_cardapio(terceirizada, escola_um):
    return baker.make("AlteracaoCardapio")


@pytest.fixture
def arquivo_pdf_base64():
    arquivo = f"data:aplication/pdf;base64,{base64.b64encode(b'arquivo pdf teste').decode('utf-8')}"
    return arquivo


@pytest.fixture
def arquivo_base64():
    arquivo = f"data:image/jpeg;base64,{base64.b64encode(b'arquivo imagem teste').decode('utf-8')}"
    return arquivo


@pytest.fixture
def eolservicosgp_get_lista_alunos(monkeypatch):
    with open(
        "sme_sigpae_api/escola/__tests__/massa_eolservicosgp_lista_alunos.json"
    ) as jsfile:
        js = json.load(jsfile)
    return monkeypatch.setattr(
        EOLServicoSGP, "get_alunos_por_escola_por_ano_letivo", lambda x: js
    )


@pytest.fixture
def client_autenticado_vinculo_coordenador_supervisao_nutricao(
    client, django_user_model, codae
):
    email = "nutri@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_supervisao_nutricao = baker.make(
        "Perfil",
        nome=constants.COORDENADOR_SUPERVISAO_NUTRICAO,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )

    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_supervisao_nutricao,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    client.login(username=email, password=password)
    return client, user


def gen_capped_positive_small_int():
    return gen_integer(1, 10000)


baker.generators.add(
    "django.db.models.PositiveSmallIntegerField", gen_capped_positive_small_int
)
