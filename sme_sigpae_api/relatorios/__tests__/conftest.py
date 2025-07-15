import datetime
import io

import pytest
from model_mommy import mommy
from PyPDF4 import PdfFileReader, PdfFileWriter
from weasyprint import HTML

from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
)
from sme_sigpae_api.dados_comuns.constants import DJANGO_ADMIN_PASSWORD
from sme_sigpae_api.dados_comuns.fluxo_status import FichaTecnicaDoProdutoWorkflow
from sme_sigpae_api.dados_comuns.models import TemplateMensagem
from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial
from sme_sigpae_api.escola.models import Aluno
from sme_sigpae_api.perfil.models.usuario import Usuario
from sme_sigpae_api.pre_recebimento.ficha_tecnica.fixtures.factories.ficha_tecnica_do_produto_factory import (
    FichaTecnicaFactory,
)


def criar_suspensoes(grupo_suspensao, datas_cancelamentos):
    """
    Cria objetos SuspensaoAlimentacao para o grupo_suspensao.
    :param grupo_suspensao: GrupoSuspensaoAlimentacao associado.
    :param datas_cancelamentos: Lista de tuplas (data, cancelado, justificativa).
    """
    for data, cancelado, justificativa in datas_cancelamentos:
        mommy.make(
            SuspensaoAlimentacao,
            data=data,
            grupo_suspensao=grupo_suspensao,
            cancelado=cancelado,
            cancelado_justificativa=justificativa,
        )


@pytest.fixture
def escola():
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make("Lote", terceirizada=terceirizada)
    diretoria_regional = mommy.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL IPIRANGA"
    )
    escola = mommy.make(
        "Escola",
        lote=lote,
        nome="EMEF JOAO MENDES",
        codigo_eol="000546",
        diretoria_regional=diretoria_regional,
    )
    return escola


@pytest.fixture
def escola_destino():
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make("Lote", terceirizada=terceirizada)
    diretoria_regional = mommy.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL IPIRANGA"
    )
    escola = mommy.make(
        "Escola",
        lote=lote,
        nome="EMEF MARCOS ANTONIO",
        codigo_eol="340546",
        diretoria_regional=diretoria_regional,
    )
    return escola


@pytest.fixture
def template_mensagem_dieta_especial():
    return mommy.make(
        TemplateMensagem,
        tipo=TemplateMensagem.DIETA_ESPECIAL,
        assunto="TESTE DIETA ESPECIAL",
        template_html="@id @criado_em @status @link",
    )


@pytest.fixture
def grupo_suspensao_alimentacao(escola):
    grupo_suspensao = mommy.make(
        GrupoSuspensaoAlimentacao,
        observacao="lorem ipsum",
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
    grupo_suspensao = mommy.make(
        GrupoSuspensaoAlimentacao,
        observacao="lorem ipsum",
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
    grupo_suspensao = mommy.make(
        GrupoSuspensaoAlimentacao,
        observacao="lorem ipsum",
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
    perfil_professor = mommy.make("perfil.Perfil", nome="ADMINISTRADOR_UE", ativo=False)
    mommy.make(
        "perfil.Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_professor,
        data_inicial=datetime.date.today(),
        ativo=True,
    )  # ativo
    return user, password


@pytest.fixture
def solicitacao_dieta_especial_a_autorizar(
    client, escola, template_mensagem_dieta_especial, usuario_escola
):
    user, password = usuario_escola
    client.login(username=user.email, password=password)

    aluno = mommy.make(
        Aluno,
        nome="Roberto Alves da Silva",
        codigo_eol="123456",
        data_nascimento="2000-01-01",
    )
    solic = mommy.make(
        SolicitacaoDietaEspecial,
        escola_destino=escola,
        rastro_escola=escola,
        rastro_terceirizada=escola.lote.terceirizada,
        aluno=aluno,
        ativo=True,
        criado_por=user,
    )
    solic.inicia_fluxo(user=user)

    return solic


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

    perfil = mommy.make("perfil.Perfil", nome="TERCEIRIZADA", ativo=False)
    mommy.make(
        "perfil.Vinculo",
        usuario=user,
        instituicao=escola.lote.terceirizada,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )

    solicitacao_dieta_especial_a_autorizar.codae_autoriza(user=user)

    return solicitacao_dieta_especial_a_autorizar


@pytest.fixture
def solicitacao_dieta_especial_cancelada(
    client, solicitacao_dieta_especial_autorizada, usuario_escola
):
    user, password = usuario_escola
    client.login(username=user.email, password=password)
    solicitacao_dieta_especial_autorizada.cancelar_pedido(
        user=user, justificativa="Não há necessidade"
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

    perfil = mommy.make("perfil.Perfil", nome="TERCEIRIZADA", ativo=False)
    mommy.make(
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
    solicitacao_dieta_especial_a_autorizar.motivo_alteracao_ue = mommy.make(
        "MotivoAlteracaoUE", nome="Dieta Especial - Recreio nas Férias"
    )
    solicitacao_dieta_especial_a_autorizar.save()
    solicitacao_dieta_especial_a_autorizar.codae_autoriza(user=user)

    return solicitacao_dieta_especial_a_autorizar


@pytest.fixture
def solicitacao_dieta_especial_inativa(
    client, solicitacao_dieta_especial_autorizada, usuario_escola
):
    user, password = usuario_escola
    client.login(username=user.email, password=password)
    solicitacao_dieta_especial_autorizada.inicia_fluxo_inativacao(
        user=user, justificativa="Não há necessidade"
    )
    solicitacao_dieta_especial_autorizada.codae_autoriza_inativacao(
        user=user, justificativa="Não há necessidade"
    )
    solicitacao_dieta_especial_autorizada.ativo = False
    solicitacao_dieta_especial_autorizada.save()
    return solicitacao_dieta_especial_autorizada


@pytest.fixture
def ficha_tecnica():
    ficha_tecnica = FichaTecnicaFactory(status=FichaTecnicaDoProdutoWorkflow.APROVADA)
    return ficha_tecnica


@pytest.fixture
def ficha_tecnica_sem_envasador(ficha_tecnica):
    ficha_tecnica.envasador_distribuidor = None
    ficha_tecnica.save()
    return ficha_tecnica
