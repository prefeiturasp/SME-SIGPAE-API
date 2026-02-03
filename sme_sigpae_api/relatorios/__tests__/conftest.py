import datetime
import io

import pytest
from freezegun import freeze_time
from model_bakery import baker
from PyPDF4 import PdfFileReader, PdfFileWriter
from weasyprint import HTML

from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
)
from sme_sigpae_api.dados_comuns.constants import DJANGO_ADMIN_PASSWORD
from sme_sigpae_api.dados_comuns.fluxo_status import FichaTecnicaDoProdutoWorkflow
from sme_sigpae_api.dados_comuns.models import (
    LogSolicitacoesUsuario,
    TemplateMensagem,
)
from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial
from sme_sigpae_api.escola.models import Aluno, Lote
from sme_sigpae_api.perfil.models.usuario import Usuario
from sme_sigpae_api.pre_recebimento.cronograma_entrega.fixtures.factories.cronograma_factory import (
    CronogramaFactory,
    EtapasDoCronogramaFactory,
)
from sme_sigpae_api.pre_recebimento.documento_recebimento.fixtures.factories.documentos_de_recebimento_factory import (
    DocumentoDeRecebimentoFactory,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.fixtures.factories.ficha_tecnica_do_produto_factory import (
    FichaTecnicaFactory,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto
from sme_sigpae_api.recebimento.fixtures.factories.ficha_de_recebimento_factory import (
    FichaDeRecebimentoFactory,
    VeiculoFichaDeRecebimentoFactory,
)
from sme_sigpae_api.recebimento.fixtures.factories.reposicao_cronograma_factory import (
    ReposicaoCronogramaFichaRecebimentoFactory,
)
from sme_sigpae_api.recebimento.models import (
    OcorrenciaFichaRecebimento,
)

LOREM_IPSUM = "lorem ipsum"
JUSTIFICATIVA_NAO_NECESSIDADE = "Não há necessidade"


def criar_suspensoes(grupo_suspensao, datas_cancelamentos):
    """
    Cria objetos SuspensaoAlimentacao para o grupo_suspensao.
    :param grupo_suspensao: GrupoSuspensaoAlimentacao associado.
    :param datas_cancelamentos: Lista de tuplas (data, cancelado, justificativa).
    """
    for data, cancelado, justificativa in datas_cancelamentos:
        baker.make(
            SuspensaoAlimentacao,
            data=data,
            grupo_suspensao=grupo_suspensao,
            cancelado=cancelado,
            cancelado_justificativa=justificativa,
        )


@pytest.fixture
def escola():
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    diretoria_regional = baker.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL IPIRANGA"
    )
    escola = baker.make(
        "Escola",
        lote=lote,
        nome="EMEF JOAO MENDES",
        codigo_eol="000546",
        diretoria_regional=diretoria_regional,
    )
    return escola


@pytest.fixture
def escola_destino():
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    diretoria_regional = baker.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL IPIRANGA"
    )
    escola = baker.make(
        "Escola",
        lote=lote,
        nome="EMEF MARCOS ANTONIO",
        codigo_eol="340546",
        diretoria_regional=diretoria_regional,
    )
    return escola


@pytest.fixture
def template_mensagem_dieta_especial():
    return baker.make(
        TemplateMensagem,
        tipo=TemplateMensagem.DIETA_ESPECIAL,
        assunto="TESTE DIETA ESPECIAL",
        template_html="@id @criado_em @status @link",
    )


@pytest.fixture
def grupo_suspensao_alimentacao(escola):
    grupo_suspensao = baker.make(
        GrupoSuspensaoAlimentacao,
        observacao=LOREM_IPSUM,
        escola=escola,
        rastro_escola=escola,
        status="INFORMADO",
    )
    criar_suspensoes(
        grupo_suspensao,
        [
            (datetime.date(2025, 1, 20), False, ""),
            (datetime.date(2025, 1, 21), False, ""),
            (datetime.date(2025, 1, 22), False, ""),
            (datetime.date(2025, 1, 23), False, ""),
            (datetime.date(2025, 1, 24), False, ""),
        ],
    )

    return grupo_suspensao


@pytest.fixture
def grupo_suspensao_alimentacao_cancelamento_parcial(escola):
    grupo_suspensao = baker.make(
        GrupoSuspensaoAlimentacao,
        observacao=LOREM_IPSUM,
        escola=escola,
        rastro_escola=escola,
        status="INFORMADO",
    )
    criar_suspensoes(
        grupo_suspensao,
        [
            (datetime.date(2025, 1, 20), True, "Cancelado por motivos maiores"),
            (datetime.date(2025, 1, 21), False, ""),
            (
                datetime.date(2025, 1, 22),
                True,
                "Ajustes internos necessários para o funcionamento da unidade.",
            ),
            (datetime.date(2025, 1, 23), False, ""),
            (datetime.date(2025, 1, 24), False, ""),
        ],
    )

    return grupo_suspensao


@pytest.fixture
def grupo_suspensao_alimentacao_cancelamento_total(escola):
    grupo_suspensao = baker.make(
        GrupoSuspensaoAlimentacao,
        observacao=LOREM_IPSUM,
        escola=escola,
        rastro_escola=escola,
        status="ESCOLA_CANCELOU",
    )
    criar_suspensoes(
        grupo_suspensao,
        [
            (datetime.date(2025, 1, 20), True, "Cancelado por falta de recursos"),
            (datetime.date(2025, 1, 21), True, "Cancelamento preventivo"),
            (datetime.date(2025, 1, 22), True, "Interrupção necessária"),
            (datetime.date(2025, 1, 23), True, "Manutenção na unidade"),
            (datetime.date(2025, 1, 24), True, "Suspensão devido a reformas"),
        ],
    )

    return grupo_suspensao


@pytest.fixture
def usuario_escola(escola):
    email = "escola@admin.com"
    password = DJANGO_ADMIN_PASSWORD
    rf = "1545933"
    user = Usuario.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf
    )
    perfil_professor = baker.make("perfil.Perfil", nome="ADMINISTRADOR_UE", ativo=False)
    baker.make(
        "perfil.Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_professor,
        data_inicial="2024-12-10",
        ativo=True,
    )  # ativo
    return user, password


@pytest.fixture
def aluno():
    return baker.make(
        Aluno,
        nome="Roberto Alves da Silva",
        codigo_eol="123456",
        data_nascimento="2000-01-01",
    )


@freeze_time("2025-12-10")
@pytest.fixture
def solicitacao_dieta_especial_a_autorizar(
    client, escola, template_mensagem_dieta_especial, usuario_escola, aluno
):
    user, password = usuario_escola
    # client.login(username=user.email, password=password)

    solic = baker.make(
        SolicitacaoDietaEspecial,
        escola_destino=escola,
        rastro_escola=escola,
        rastro_terceirizada=escola.lote.terceirizada,
        aluno=aluno,
        ativo=False,
        criado_por=user,
        criado_em="2025-12-10",
    )
    solic.inicia_fluxo(user=user)
    log = solic.logs.filter(status_evento=LogSolicitacoesUsuario.INICIO_FLUXO).last()
    log.criado_em = "2025-12-10"
    log.save()

    return solic


@freeze_time("2025-12-20")
@pytest.fixture
def solicitacao_dieta_especial_autorizada(
    client, escola, solicitacao_dieta_especial_a_autorizar
):
    email = "terceirizada@admin.com"
    password = DJANGO_ADMIN_PASSWORD
    rf = "4545454"
    user = Usuario.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf
    )
    client.login(username=email, password=password)

    perfil = baker.make("perfil.Perfil", nome="TERCEIRIZADA", ativo=False)
    baker.make(
        "perfil.Vinculo",
        usuario=user,
        instituicao=escola.lote.terceirizada,
        perfil=perfil,
        data_inicial="2024-12-20",
        ativo=True,
    )

    solicitacao_dieta_especial_a_autorizar.codae_autoriza(user=user)
    log = solicitacao_dieta_especial_a_autorizar.logs.filter(
        status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU
    ).last()
    log.criado_em = "2025-12-20"
    log.save()
    solicitacao_dieta_especial_a_autorizar.ativo = True
    solicitacao_dieta_especial_a_autorizar.save()
    return solicitacao_dieta_especial_a_autorizar


@pytest.fixture
def solicitacao_dieta_especial_cancelada(
    client, solicitacao_dieta_especial_autorizada, usuario_escola
):
    user, password = usuario_escola
    client.login(username=user.email, password=password)
    solicitacao_dieta_especial_autorizada.cancelar_pedido(
        user=user, justificativa=JUSTIFICATIVA_NAO_NECESSIDADE
    )
    solicitacao_dieta_especial_autorizada.ativo = False
    solicitacao_dieta_especial_autorizada.save()
    return solicitacao_dieta_especial_autorizada


@pytest.fixture
def gerar_pdf_simples():
    pdf_final = io.BytesIO()
    documento = PdfFileWriter()

    for i in range(2):
        html = HTML(
            string=f"<h1>Dieta especial autorizada para o aluno Fulano{i+1} - Página {i+1}</h1>"
        ).write_pdf()
        pagina_pdf = PdfFileReader(io.BytesIO(html))
        documento.addPage(pagina_pdf.getPage(0))

    documento.write(pdf_final)
    pdf_final.seek(0)
    return pdf_final


@pytest.fixture
def solicitacao_dieta_especial_autorizada_alteracao_ue(
    client,
    escola,
    solicitacao_dieta_especial_a_autorizar,
    escola_destino,
    template_mensagem_dieta_especial,
):
    email = "terceirizada@admin.com"
    password = DJANGO_ADMIN_PASSWORD
    rf = "4545454"
    user = Usuario.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf
    )
    client.login(username=email, password=password)

    perfil = baker.make("perfil.Perfil", nome="TERCEIRIZADA", ativo=False)
    baker.make(
        "perfil.Vinculo",
        usuario=user,
        instituicao=escola.lote.terceirizada,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )

    solicitacao_dieta_especial_a_autorizar.tipo_solicitacao = "ALTERACAO_UE"
    solicitacao_dieta_especial_a_autorizar.escola_destino = escola_destino
    solicitacao_dieta_especial_a_autorizar.data_inicio = datetime.date(2025, 1, 20)
    solicitacao_dieta_especial_a_autorizar.data_termino = datetime.date(2025, 2, 20)
    solicitacao_dieta_especial_a_autorizar.motivo_alteracao_ue = baker.make(
        "MotivoAlteracaoUE", nome="Dieta Especial - Recreio nas Férias"
    )
    solicitacao_dieta_especial_a_autorizar.save()
    solicitacao_dieta_especial_a_autorizar.codae_autoriza(user=user)

    return solicitacao_dieta_especial_a_autorizar


@pytest.fixture
def solicitacao_dieta_especial_inativa(
    client, solicitacao_dieta_especial_autorizada, usuario_escola, escola, aluno
):
    user, password = usuario_escola

    # Desativando 1 @ dieta
    solicitacao_dieta_especial_autorizada.ativo = False
    solicitacao_dieta_especial_autorizada.save()

    # Criando 2 dieta
    solicitacao_dieta_especial_inativa = baker.make(
        SolicitacaoDietaEspecial,
        escola_destino=escola,
        rastro_escola=escola,
        rastro_terceirizada=escola.lote.terceirizada,
        aluno=aluno,
        ativo=False,
        criado_por=user,
        criado_em="2026-01-08",
    )
    solicitacao_dieta_especial_inativa.inicia_fluxo(user=user)
    log = solicitacao_dieta_especial_inativa.logs.filter(
        status_evento=LogSolicitacoesUsuario.INICIO_FLUXO
    ).last()
    log.criado_em = "2026-01-08"
    log.save()

    solicitacao_dieta_especial_inativa.codae_autoriza(user=user)
    log = solicitacao_dieta_especial_inativa.logs.filter(
        status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU
    ).last()
    log.criado_em = "2026-01-26"
    log.save()
    solicitacao_dieta_especial_inativa.ativo = False
    solicitacao_dieta_especial_inativa.save()

    return solicitacao_dieta_especial_autorizada


@pytest.fixture
def solicitacao_dieta_especial_inativa_com_log(
    solicitacao_dieta_especial_inativa, usuario_escola
):

    user, password = usuario_escola
    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=solicitacao_dieta_especial_inativa.uuid,
        status_evento=LogSolicitacoesUsuario.CODAE_INATIVOU,
        usuario=user,
        criado_em=datetime.datetime(
            2026, 2, 1, 23, 59, 59, tzinfo=datetime.timezone.utc
        ),
    )
    return solicitacao_dieta_especial_inativa


@pytest.fixture
def ficha_tecnica():
    ficha_tecnica = FichaTecnicaFactory(status=FichaTecnicaDoProdutoWorkflow.APROVADA)
    return ficha_tecnica


@pytest.fixture
def ficha_tecnica_sem_envasador(ficha_tecnica):
    ficha_tecnica.envasador_distribuidor = None
    ficha_tecnica.save()
    return ficha_tecnica


@pytest.fixture
def lote():
    diretoria_regional = baker.make("DiretoriaRegional", iniciais="IP")
    return baker.make(Lote, nome="3567-3", diretoria_regional=diretoria_regional)


@pytest.fixture
def mock_produtos_relatorio_reclamacao(lote):
    return [
        {
            "nome": "ACHOCOLATADO EM PÓ",
            "marca": {"nome": "TECNUTRI"},
            "fabricante": {"nome": "TECNUTRI SA"},
            "ultima_homologacao": {
                "criado_em": "01/07/2022 16:21:04",
                "reclamacoes": [
                    {
                        "reclamante_registro_funcional": "8115257",
                        "logs": [
                            {
                                "status_evento_explicacao": "CODAE recusou reclamação",
                                "criado_em": "05/08/2022 11:04:22",
                                "justificativa": "<p>deu certooo</p>",
                            }
                        ],
                        "reclamante_cargo": "ANALISTA DE SAUDE NIVEL I",
                        "reclamante_nome": "SUPER USUARIO ESCOLA EMEF",
                        "reclamacao": "<p>produto vencido</p>",
                        "escola": {
                            "nome": "EMEF PERICLES EUGENIO DA SILVA RAMOS",
                            "codigo_eol": "017981",
                            "diretoria_regional": {"iniciais": "IP"},
                            "lote": {
                                "nome": lote.nome,
                                "terceirizada": {
                                    "nome_fantasia": "ALIMENTAR GESTÃO DE SERVIÇOS LTDA"
                                },
                            },
                        },
                        "status": "CODAE_RECUSOU",
                        "status_titulo": "CODAE recusou",
                        "criado_em": "15/07/2022 13:11:33",
                        "id_externo": "93C77",
                    }
                ],
                "status_titulo": "Escola/Nutricionista reclamou do produto",
                "editais_reclamacoes": ["Edital de Pregão 001", "Edital de Pregão 004"],
            },
        }
    ]


@pytest.fixture
def mock_filtros_relatorio_reclamacao(lote):
    lote_dois = baker.make(
        Lote,
        nome="1235-8",
        diretoria_regional=baker.make("DiretoriaRegional", iniciais="LPSD"),
    )
    return {
        "editais": [
            "Edital de Pregão 001",
            "Edital de Pregão 002",
            "Edital de Pregão 003",
            "Edital de Pregão 004",
        ],
        "lotes": [
            str(lote.uuid),
            str(lote_dois.uuid),
        ],
        "data_inicial_reclamacao": "01/01/2022",
        "data_final_reclamacao": "19/08/2025",
    }


@pytest.fixture
def ficha_recebimento_com_ocorrencia():
    """Ficha de recebimento com ocorrência criada usando factories."""

    unidade_medida = baker.make(
        "pre_recebimento.UnidadeMedida", nome="QUILOGRAMA", abreviacao="kg"
    )
    cronograma = CronogramaFactory(unidade_medida=unidade_medida)
    etapa = EtapasDoCronogramaFactory(cronograma=cronograma)

    ficha = FichaDeRecebimentoFactory(
        etapa=etapa,
        observacao="Recebimento com problemas detectados",
        houve_ocorrencia=True,
    )

    doc_recebimento = DocumentoDeRecebimentoFactory()
    baker.make(
        "recebimento.DocumentoFichaDeRecebimento",
        ficha_recebimento=ficha,
        documento_recebimento=doc_recebimento,
        quantidade_recebida=10.00,
    )

    VeiculoFichaDeRecebimentoFactory(
        ficha_recebimento=ficha,
        numero="VEÍCULO 01",
        temperatura_recebimento="22°C",
        temperatura_produto="4°C",
        lacre="LACRE123456",
        numero_sif_sisbi_sisp="SIF123456",
        numero_nota_fiscal="NF123456",
        quantidade_nota_fiscal=2000.00,
        embalagens_nota_fiscal=3000,
        quantidade_recebida=1000.00,
        embalagens_recebidas=1500,
        estado_higienico_adequado=True,
        termografo=True,
        placa="ABC1234",
    )

    OcorrenciaFichaRecebimento.objects.create(
        ficha_recebimento=ficha,
        tipo="FALTA",
        relacao="CRONOGRAMA",
        quantidade="5",
        descricao="Faltaram 5 unidades do produto",
        numero_nota="NF123456",
    )

    return ficha


@pytest.fixture
def ficha_recebimento_reposicao():
    """Ficha de recebimento de reposição."""

    cronograma = CronogramaFactory()
    etapa = EtapasDoCronogramaFactory(cronograma=cronograma)

    reposicao_cronograma = ReposicaoCronogramaFichaRecebimentoFactory()
    reposicao_cronograma.tipo = "Repor"
    reposicao_cronograma.descricao = "REPOR OS PRODUTOS FALTANTES/RECUSADOS"
    reposicao_cronograma.save()

    ficha = FichaDeRecebimentoFactory(
        etapa=etapa,
        observacao="Ficha de recebimento de reposição",
        reposicao_cronograma=reposicao_cronograma,
        houve_ocorrencia=False,
    )

    return ficha


@pytest.fixture
def ficha_recebimento_carta_credito():
    """Ficha de recebimento com carta de crédito."""

    cronograma = CronogramaFactory()
    etapa = EtapasDoCronogramaFactory(cronograma=cronograma)

    reposicao_cronograma = ReposicaoCronogramaFichaRecebimentoFactory()
    reposicao_cronograma.tipo = "Credito"
    reposicao_cronograma.descricao = "FAZER UMA CARTA DE CRÉDITO DO VALOR PAGO"
    reposicao_cronograma.save()

    ficha = FichaDeRecebimentoFactory(
        etapa=etapa,
        observacao="Ficha de recebimento com carta de crédito",
        reposicao_cronograma=reposicao_cronograma,
        houve_ocorrencia=False,
    )

    return ficha


@pytest.fixture
def cronograma(
    fabricante_ficha_tecnica_factory,
    produto_logistica_factory,
    marca_factory,
):
    unidade_medida = baker.make(
        "pre_recebimento.UnidadeMedida", nome="QUILOGRAMA", abreviacao="kg"
    )

    tipo_embalagem = baker.make(
        "pre_recebimento.TipoEmbalagemQld", nome="CAIXA", abreviacao="cx"
    )

    empresa = baker.make(
        "terceirizada.Terceirizada",
        nome_fantasia="Alimentos LTDA",
        cnpj="12345678000190",
        endereco="Rua das Flores, 123 - São Paulo/SP",
    )

    armazem = baker.make(
        "terceirizada.Terceirizada",
        nome_fantasia="Armazém Central",
        cnpj="98765432000110",
        endereco="Avenida Industrial, 456 - São Paulo/SP",
    )

    contrato = baker.make(
        "terceirizada.Contrato",
        numero="001/2024",
        numero_pregao="PE-2024-001",
        programa="LEVE_LEITE",
    )

    ficha_tecnica = baker.make(
        "pre_recebimento.FichaTecnicaDoProduto",
        produto=produto_logistica_factory(),
        empresa=empresa,
        fabricante=fabricante_ficha_tecnica_factory(),
        marca=marca_factory(),
        envasador_distribuidor=fabricante_ficha_tecnica_factory(),
        categoria=FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
        unidade_medida_porcao=unidade_medida,
        unidade_medida_primaria=unidade_medida,
        unidade_medida_secundaria=unidade_medida,
        unidade_medida_primaria_vazia=unidade_medida,
        unidade_medida_secundaria_vazia=unidade_medida,
        status=FichaTecnicaDoProduto.workflow_class.ENVIADA_PARA_ANALISE,
        programa=FichaTecnicaDoProduto.LEVE_LEITE,
    )

    cronograma = CronogramaFactory(
        numero="001/2024A",
        contrato=contrato,
        empresa=empresa,
        qtd_total_programada=1000.0,
        unidade_medida=unidade_medida,
        armazem=armazem,
        tipo_embalagem_secundaria=tipo_embalagem,
        custo_unitario_produto=15.50,
        observacoes="Cronograma de teste com observações específicas",
        ficha_tecnica=ficha_tecnica,
    )

    EtapasDoCronogramaFactory(
        cronograma=cronograma,
        numero_empenho="2024NE000123",
        qtd_total_empenho=500.0,
        etapa=1,
        parte=1,
        data_programada=datetime.date(2024, 6, 15),
        quantidade=300.0,
        total_embalagens=20.0,
    )

    EtapasDoCronogramaFactory(
        cronograma=cronograma,
        numero_empenho="2024NE000124",
        qtd_total_empenho=500.0,
        etapa=1,
        parte=2,
        data_programada=datetime.date(2024, 6, 20),
        quantidade=200.0,
        total_embalagens=15.0,
    )

    return cronograma


@pytest.fixture
def categoria_dieta_a():
    return baker.make("CategoriaMedicao", nome="DIETA ESPECIAL - TIPO A")


@pytest.fixture
def solicitacoes_medicao_inicial_emef(
    escola,
    categoria_dieta_a,
):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_integral = baker.make("PeriodoEscolar", nome="INTEGRAL")
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=10,
        ano=2025,
        escola=escola,
        ue_possui_alunos_periodo_parcial=True,
        rastro_lote=escola.lote,
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_integral = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_integral,
    )
    faixa_etaria = baker.make(
        "FaixaEtaria", inicio=1, fim=10, uuid="0c914b27-c7cd-4682-a439-a4874745b005"
    )
    baker.make("Aluno", periodo_escolar=periodo_integral, escola=escola)
    baker.make(
        "ValorMedicao",
        dia="01",
        semana="1",
        nome_campo="frequencia",
        medicao=medicao_integral,
        categoria_medicao=categoria_dieta_a,
        valor="10",
        faixa_etaria=faixa_etaria,
    )
    return solicitacao_medicao


@pytest.fixture
def solicitacao_medicao_inicial_aprovada_codae(
    solicitacoes_medicao_inicial_emef,
    django_user_model,
):
    usuario = django_user_model.objects.create_user(
        nome="Usuário TESTE",
        username="medicao_teste",
        password=DJANGO_ADMIN_PASSWORD,
        email="medicao@escola.com",
        registro_funcional="123456",
    )

    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=solicitacoes_medicao_inicial_emef.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
        criado_em=datetime.datetime(
            2025, 11, 27, 14, 9, 11, tzinfo=datetime.timezone.utc
        ),
        usuario=usuario,
    )

    for medicao in solicitacoes_medicao_inicial_emef.medicoes.all():
        medicao.status = (
            solicitacoes_medicao_inicial_emef.workflow_class.MEDICAO_APROVADA_PELA_CODAE
        )
        medicao.save()
    solicitacoes_medicao_inicial_emef.status = (
        solicitacoes_medicao_inicial_emef.workflow_class.MEDICAO_APROVADA_PELA_CODAE
    )
    solicitacoes_medicao_inicial_emef.save()
    return solicitacoes_medicao_inicial_emef
