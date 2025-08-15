import datetime
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from faker import Faker
from freezegun import freeze_time
from model_bakery import baker

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
from sme_sigpae_api.dados_comuns.constants import (
    DJANGO_ADMIN_PASSWORD,
    StatusProcessamentoArquivo,
)
from sme_sigpae_api.dados_comuns.fluxo_status import (
    HomologacaoProdutoWorkflow,
    PedidoAPartirDaEscolaWorkflow,
)
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.escola.utils import cria_arquivo_excel
from sme_sigpae_api.escola.utils_analise_dietas_ativas import (
    dict_codigo_aluno_por_codigo_escola as dict_aluno_utils_dieta,
)
from sme_sigpae_api.escola.utils_analise_dietas_ativas import (
    dict_codigos_escolas as dict_escola_utils_dieta,
)
from sme_sigpae_api.escola.utils_escola import (
    dict_codigo_aluno_por_codigo_escola as dict_aluno_utils_escola,
)
from sme_sigpae_api.escola.utils_escola import (
    dict_codigos_escolas as dict_escola_utils_escola,
)

from ...eol_servico.utils import dt_nascimento_from_api
from ...escola.api.serializers import (
    Aluno,
    EscolaSimplissimaSerializer,
    VinculoInstituicaoSerializer,
)
from ...medicao_inicial.models import SolicitacaoMedicaoInicial
from ...perfil.models import Vinculo
from .. import models

fake = Faker("pt_BR")
Faker.seed(420)


@pytest.fixture
def periodo_escolar():
    return baker.make(models.PeriodoEscolar, nome="INTEGRAL", tipo_turno=1)


@pytest.fixture
def tipo_unidade_escolar():
    cardapio1 = baker.make("cardapio.Cardapio", data=datetime.date(2019, 10, 11))
    cardapio2 = baker.make("cardapio.Cardapio", data=datetime.date(2019, 10, 15))
    return baker.make(
        models.TipoUnidadeEscolar, iniciais="EMEF", cardapios=[cardapio1, cardapio2]
    )


@pytest.fixture
def tipo_gestao():
    return baker.make(models.TipoGestao, nome="TERC TOTAL")


@pytest.fixture
def diretoria_regional(tipo_gestao):
    dre = baker.make(
        models.DiretoriaRegional,
        nome=fake.name(),
        uuid="d305add2-f070-4ad3-8c17-ba9664a7c655",
        make_m2m=True,
    )
    baker.make("Escola", diretoria_regional=dre, tipo_gestao=tipo_gestao)
    baker.make("Escola", diretoria_regional=dre, tipo_gestao=tipo_gestao)
    baker.make("Escola", diretoria_regional=dre, tipo_gestao=tipo_gestao)
    return dre


@pytest.fixture
def lote():
    return baker.make(
        models.Lote,
        nome="lote",
        iniciais="lt",
        uuid="49696643-7a47-4324-989b-9380177fef2d",
    )


@pytest.fixture
def escola(lote, tipo_gestao, diretoria_regional):
    return baker.make(
        models.Escola,
        nome=fake.name(),
        diretoria_regional=diretoria_regional,
        codigo_eol=fake.name()[:6],
        lote=lote,
        tipo_gestao=tipo_gestao,
        contato=baker.make("Contato", email="escola@email.com"),
        uuid="4282d012-2f38-4f04-97a3-217c49bb8040",
    )


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
def log_aluno_integral_cei(escola_cei, periodo_escolar):
    log = baker.make(
        "LogAlunosMatriculadosPeriodoEscola",
        escola=escola_cei,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=100,
    )
    log.criado_em = datetime.date(2025, 5, 5)
    log.save()
    return log


@pytest.fixture
def log_alunos_matriculados_integral_cei(escola_cei, periodo_escolar):
    return baker.make(
        "AlunosMatriculadosPeriodoEscola",
        escola=escola_cei,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=100,
    )


@pytest.fixture
def escola_cemei(periodo_escolar):
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    diretoria_regional = baker.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL TESTE"
    )
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = baker.make("TipoUnidadeEscolar", iniciais="CEMEI")
    escola = baker.make(
        "Escola",
        nome="CEMEI TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
    )
    baker.make(
        "Aluno",
        serie="1",
        escola=escola,
        periodo_escolar=periodo_escolar,
        ciclo=Aluno.CICLO_ALUNO_CEI,
    )
    baker.make(
        "Aluno",
        serie="5",
        escola=escola,
        periodo_escolar=periodo_escolar,
        ciclo=Aluno.CICLO_ALUNO_EMEI,
    )
    return escola


@pytest.fixture
def escola_emebs(periodo_escolar):
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    diretoria_regional = baker.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL TESTE"
    )
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = baker.make("TipoUnidadeEscolar", iniciais="EMEBS")
    escola = baker.make(
        "Escola",
        nome="EMEBS TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
    )
    baker.make(
        "Aluno",
        etapa=Aluno.ETAPA_INFANTIL,
        escola=escola,
        periodo_escolar=periodo_escolar,
    )
    baker.make("Aluno", serie=14, escola=escola, periodo_escolar=periodo_escolar)
    return escola


@pytest.fixture
def escola_simplissima_serializer(escola):
    return EscolaSimplissimaSerializer(escola)


@pytest.fixture
def faixa_idade_escolar():
    return baker.make(models.FaixaIdadeEscolar, nome=fake.name())


@pytest.fixture
def codae(escola):
    return baker.make(models.Codae, make_m2m=True)


@pytest.fixture
def periodo_escolar_parcial():
    return baker.make(models.PeriodoEscolar, nome="PARCIAL")


@pytest.fixture
def escola_periodo_escolar(periodo_escolar):
    return baker.make(models.EscolaPeriodoEscolar, periodo_escolar=periodo_escolar)


@pytest.fixture
def sub_prefeitura():
    return baker.make(models.Subprefeitura)


@pytest.fixture
def vinculo(escola):
    return baker.make(
        Vinculo, uuid="a19baa09-f8cc-49a7-a38d-2a38270ddf45", instituicao=escola
    )


@pytest.fixture
def vinculo_instituto_serializer(vinculo):
    return VinculoInstituicaoSerializer(vinculo)


@pytest.fixture
def aluno(escola, periodo_escolar):
    return baker.make(
        models.Aluno,
        nome="Fulano da Silva",
        codigo_eol="000001",
        data_nascimento=datetime.date(2000, 1, 1),
        escola=escola,
        periodo_escolar=periodo_escolar,
    )


@pytest.fixture
def usuario_coordenador_codae(django_user_model):
    email, password, rf, cpf = (
        "cogestor_1@sme.prefeitura.sp.gov.br",
        "adminadmin",
        "0000001",
        "44426575052",
    )
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf, cpf=cpf
    )

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

    baker.make(
        "TipoUnidadeEscolar",
        iniciais="EMEF",
        uuid="1cc3253b-e297-42b3-8e57-ebfd115a1aba",
    )
    baker.make(
        "TipoUnidadeEscolar",
        iniciais="CEU GESTAO",
        uuid="40ee89a7-dc70-4abb-ae21-369c67f2b9e3",
    )
    baker.make(
        "TipoUnidadeEscolar",
        iniciais="CIEJA",
        uuid="ac4858ff-1c11-41f3-b539-7a02696d6d1b",
    )

    return user, password


@pytest.fixture
def client_autenticado_coordenador_codae(client, usuario_coordenador_codae):
    usuario, password = usuario_coordenador_codae
    client.login(username=usuario.email, password=password)
    return client


@pytest.fixture
def usuario_diretor_escola(django_user_model, escola):
    email = "user@escola.com"
    password = DJANGO_ADMIN_PASSWORD

    perfil_diretor = baker.make("Perfil", nome="DIRETOR_UE", ativo=True)

    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="123456"
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
def client_autenticado_da_escola(client, usuario_diretor_escola):
    usuario, password = usuario_diretor_escola
    client.login(username=usuario.email, password=password)
    return client


@pytest.fixture
def client_autenticado_da_dre(client, django_user_model, diretoria_regional):
    email = "user@dre.com"
    password = DJANGO_ADMIN_PASSWORD
    perfil_adm_dre = baker.make("Perfil", nome="ADM_DRE", ativo=True)
    usuario = django_user_model.objects.create_user(
        password=password, username=email, email=email, registro_funcional="123456"
    )
    hoje = datetime.date.today()
    baker.make(
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
def faixas_etarias(faixas_etarias_ativas):
    return faixas_etarias_ativas + baker.make("FaixaEtaria", ativo=False, _quantity=8)


# Data referencia = 2019-06-20
@pytest.fixture(
    params=[
        # (data, faixa, data_pertence_a_faixa) E800 noqa
        (datetime.date(2019, 6, 15), 0, 1, True),
        (datetime.date(2019, 6, 20), 0, 1, False),
        (datetime.date(2019, 5, 20), 0, 1, True),
        (datetime.date(2019, 5, 19), 0, 1, False),
        (datetime.date(2019, 4, 20), 0, 1, False),
        (datetime.date(2019, 4, 20), 1, 3, True),
        (datetime.date(2019, 2, 10), 1, 3, False),
    ]
)
def datas_e_faixas(request):
    (data, inicio_faixa, fim_faixa, eh_pertencente) = request.param
    return (
        data,
        baker.make("FaixaEtaria", inicio=inicio_faixa, fim=fim_faixa, ativo=True),
        eh_pertencente,
    )


@pytest.fixture
def arquivo():
    return SimpleUploadedFile(
        "planilha-teste.pdf", bytes("CONTEUDO TESTE TESTE TESTE", encoding="utf-8")
    )


@pytest.fixture
def planilha_de_para_eol_codae(arquivo):
    return baker.make(
        "PlanilhaEscolaDeParaCodigoEolCodigoCoade",
        planilha=arquivo,
        criado_em=datetime.date.today(),
        codigos_codae_vinculados=False,
    )


@pytest.fixture
def planilha_atualizacao_tipo_gestao(arquivo):
    return baker.make(
        "PlanilhaAtualizacaoTipoGestaoEscola",
        conteudo=arquivo,
        criado_em=datetime.date.today(),
        status="SUCESSO",
    )


@pytest.fixture
def alunos_matriculados_periodo_escola_regular(escola, periodo_escolar):
    return baker.make(
        models.AlunosMatriculadosPeriodoEscola,
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=50,
        tipo_turma=models.TipoTurma.REGULAR.name,
    )


@pytest.fixture
def alunos_matriculados_periodo_escola_programas(escola, periodo_escolar):
    return baker.make(
        models.AlunosMatriculadosPeriodoEscola,
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=50,
        tipo_turma=models.TipoTurma.PROGRAMAS.name,
    )


@pytest.fixture
def log_alunos_matriculados_periodo_escola_regular(escola, periodo_escolar):
    return baker.make(
        models.LogAlunosMatriculadosPeriodoEscola,
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=50,
        tipo_turma=models.TipoTurma.REGULAR.name,
    )


@pytest.fixture
def log_alunos_matriculados_periodo_escola_programas(escola, periodo_escolar):
    return baker.make(
        models.LogAlunosMatriculadosPeriodoEscola,
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=50,
        tipo_turma=models.TipoTurma.PROGRAMAS.name,
    )


@pytest.fixture
def dia_calendario_letivo(escola):
    return baker.make(
        models.DiaCalendario,
        escola=escola,
        data=datetime.datetime(2021, 9, 24),
        dia_letivo=True,
    )


@pytest.fixture
def dia_calendario_nao_letivo(escola):
    return baker.make(
        models.DiaCalendario,
        escola=escola,
        data=datetime.datetime(2021, 9, 25),
        dia_letivo=False,
    )


def mocked_response(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.text = json_data
            self.status_code = status_code
            self.content = b"erro"

        def json(self):
            return self.json_data

    return MockResponse(*args, **kwargs)


def mocked_token_novosgp():
    return {"token": "abc123"}


def mocked_foto_aluno_novosgp():
    return {
        "codigo": "a28395ef-74db-48c0-923a-0e86509f9d59",
        "nome": "IMG_0106.jpg",
        "download": {
            "item1": "/9j/4AAQSkZJRgABAQAAAQABAA==",
            "item2": "image/jpeg",
            "item3": "IMG_0106.jpg",
        },
    }


@pytest.fixture
def log_alunos_matriculados_faixa_etaria_dia(
    escola, periodo_escolar, faixas_etarias_ativas
):
    return baker.make(
        models.LogAlunosMatriculadosFaixaEtariaDia,
        escola=escola,
        periodo_escolar=periodo_escolar,
        faixa_etaria=faixas_etarias_ativas[0],
        quantidade=100,
        data=datetime.date.today(),
    )


@pytest.fixture
def log_atualiza_dados_aluno(escola):
    return baker.make(
        models.LogAtualizaDadosAluno, codigo_eol=escola.codigo_eol, status=200
    )


@pytest.fixture
def log_alteracao_quantidade_alunos_por_escola_periodo(escola, periodo_escolar):
    return baker.make(
        models.LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar,
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos_de=15,
        quantidade_alunos_para=30,
    )


@pytest.fixture
def log_rotina_diaria_alunos():
    return baker.make(
        models.LogRotinaDiariaAlunos,
        quantidade_alunos_antes=10,
        quantidade_alunos_atual=20,
    )


def mocked_informacoes_escola_turma_aluno():
    informacoes = [
        {
            "codigoAluno": 8888888,
            "tipoTurno": 1,
            "codigoSituacaoMatricula": 13,
            "dataNascimento": "2018-06-17T00:00:00",
        },
        {
            "codigoAluno": 9999999,
            "tipoTurno": 1,
            "codigoSituacaoMatricula": 14,
            "dataNascimento": "2018-07-22T00:00:00",
        },
        {
            "codigoAluno": 7777777,
            "tipoTurno": 1,
            "codigoSituacaoMatricula": 13,
            "dataNascimento": "2019-03-22T00:00:00",
        },
    ]
    return informacoes


@pytest.fixture
def alunos_periodo_parcial(escola_cei, periodo_escolar):
    data = datetime.date(2023, 8, 28)
    solicitacao_medicao = SolicitacaoMedicaoInicial.objects.create(
        escola=escola_cei, ano=data.year, mes=f"{data.month:02d}"
    )
    for i in range(0, len(mocked_informacoes_escola_turma_aluno()), 2):
        informacao_aluno = mocked_informacoes_escola_turma_aluno()[i]
        aluno = baker.make(
            "Aluno",
            codigo_eol=informacao_aluno["codigoAluno"],
            data_nascimento=dt_nascimento_from_api(informacao_aluno["dataNascimento"]),
            escola=escola_cei,
            periodo_escolar=periodo_escolar,
        )
        baker.make(
            models.AlunoPeriodoParcial,
            solicitacao_medicao_inicial=solicitacao_medicao,
            aluno=aluno,
            escola=escola_cei,
        )
    return models.AlunoPeriodoParcial.objects.all()


@pytest.fixture
def alunos(escola_cei, periodo_escolar):
    for i in range(0, len(mocked_informacoes_escola_turma_aluno())):
        informacao_aluno = mocked_informacoes_escola_turma_aluno()[i]
        baker.make(
            "Aluno",
            codigo_eol=informacao_aluno["codigoAluno"],
            data_nascimento=dt_nascimento_from_api(informacao_aluno["dataNascimento"]),
            escola=escola_cei,
            periodo_escolar=periodo_escolar,
            serie=f"{i}A",
            ciclo=Aluno.CICLO_ALUNO_CEI,
        )
    return models.Aluno.objects.all()


@pytest.fixture
def dia_suspensao_atividades(tipo_unidade_escolar):
    edital = baker.make(
        "Edital",
        numero="Edital de Pregão nº 13/SME/2020",
        uuid="3a9082ae-2b8c-44f6-83af-fcab9452f932",
    )
    return baker.make(
        "DiaSuspensaoAtividades",
        data=datetime.date(2022, 8, 8),
        tipo_unidade=tipo_unidade_escolar,
        edital=edital,
    )


@pytest.fixture
def dados_planilha_alunos_matriculados(alunos_matriculados_periodo_escola_regular):
    faixas_etarias = [{"nome": "04 anos a 06 anos", "uuid": uuid.uuid4()}]
    queryset = [
        {
            "dre": alunos_matriculados_periodo_escola_regular.escola.diretoria_regional.nome,
            "lote": (
                alunos_matriculados_periodo_escola_regular.escola.lote.nome
                if alunos_matriculados_periodo_escola_regular.escola.lote
                else " - "
            ),
            "tipo_unidade": alunos_matriculados_periodo_escola_regular.escola.tipo_unidade.iniciais,
            "escola": alunos_matriculados_periodo_escola_regular.escola.nome,
            "periodo_escolar": alunos_matriculados_periodo_escola_regular.periodo_escolar.nome,
            "tipo_turma": alunos_matriculados_periodo_escola_regular.tipo_turma,
            "eh_cei": alunos_matriculados_periodo_escola_regular.escola.eh_cei,
            "eh_cemei": alunos_matriculados_periodo_escola_regular.escola.eh_cemei,
            "matriculados": alunos_matriculados_periodo_escola_regular.quantidade_alunos,
            "alunos_por_faixa_etaria": alunos_matriculados_periodo_escola_regular.escola.matriculados_por_periodo_e_faixa_etaria(),
        }
    ]
    dados = {
        "faixas_etarias": faixas_etarias,
        "queryset": queryset,
        "usuario": "Faker usuario",
    }

    return dados


@pytest.fixture
def dados_planilha_alunos_matriculados_cei_cemei(
    alunos_matriculados_periodo_escola_regular,
):
    faixas_etarias = [{"nome": "04 anos a 06 anos", "uuid": uuid.uuid4()}]
    queryset = [
        {
            "dre": alunos_matriculados_periodo_escola_regular.escola.diretoria_regional.nome,
            "lote": (
                alunos_matriculados_periodo_escola_regular.escola.lote.nome
                if alunos_matriculados_periodo_escola_regular.escola.lote
                else " - "
            ),
            "tipo_unidade": alunos_matriculados_periodo_escola_regular.escola.tipo_unidade.iniciais,
            "escola": alunos_matriculados_periodo_escola_regular.escola.nome,
            "periodo_escolar": alunos_matriculados_periodo_escola_regular.periodo_escolar.nome,
            "tipo_turma": alunos_matriculados_periodo_escola_regular.tipo_turma,
            "eh_cei": True,
            "eh_cemei": alunos_matriculados_periodo_escola_regular.escola.eh_cemei,
            "matriculados": alunos_matriculados_periodo_escola_regular.quantidade_alunos,
            "alunos_por_faixa_etaria": alunos_matriculados_periodo_escola_regular.escola.matriculados_por_periodo_e_faixa_etaria(),
        }
    ]
    dados = {
        "faixas_etarias": faixas_etarias,
        "queryset": queryset,
        "usuario": "Faker usuario",
    }

    return dados


@pytest.fixture
def protocolos():
    baker.make("ProtocoloDeDietaEspecial", nome="Protocolo1")
    baker.make("ProtocoloDeDietaEspecial", nome="Protocolo2")
    baker.make("ProtocoloDeDietaEspecial", nome="Protocolo3")


@pytest.fixture
def variaveis_globais_dieta():
    global dict_escola_utils_dieta, dict_aluno_utils_dieta

    dict_escola_utils_dieta.clear()
    dict_aluno_utils_dieta.clear()

    dict_escola_utils_dieta.update(
        {
            "1001": "123456789",
            "1002": "987654321",
        }
    )
    dict_aluno_utils_dieta.update(
        {
            "20001": "Escola A",
            "20002": "Escola B",
            "20003": "Escola C",
        }
    )

    yield dict_escola_utils_dieta, dict_aluno_utils_dieta

    dict_escola_utils_dieta.clear()
    dict_aluno_utils_dieta.clear()


@pytest.fixture
def variaveis_globais_escola():
    global dict_escola_utils_escola, dict_aluno_utils_dieta

    dict_escola_utils_escola.clear()
    dict_aluno_utils_escola.clear()

    dict_escola_utils_escola.update(
        {
            "1001": "123456789",
            "1002": "987654321",
        }
    )
    dict_aluno_utils_escola.update(
        {
            "20001": "Escola A",
            "20002": "Escola B",
            "20003": "Escola C",
        }
    )

    yield dict_escola_utils_escola, dict_aluno_utils_escola

    dict_escola_utils_escola.clear()
    dict_aluno_utils_escola.clear()


@pytest.fixture
def codigo_codae_das_escolas():
    escola1 = baker.make("Escola", codigo_eol="123456", codigo_codae="00000")
    escola2 = baker.make("Escola", codigo_eol="789012", codigo_codae="00000")
    planilha = baker.make(
        "PlanilhaEscolaDeParaCodigoEolCodigoCoade", codigos_codae_vinculados=False
    )

    return escola1, escola2, planilha


@pytest.fixture
def tipo_gestao_das_escolas():
    caminho_arquivo_escola = Path(f"/tmp/{uuid.uuid4()}.xlsx")
    cria_arquivo_excel(
        caminho_arquivo_escola,
        [
            {"CÓDIGO EOL": 123456, "TIPO": "PARCEIRA"},
            {"CÓDIGO EOL": 789012, "TIPO": "DIRETA"},
        ],
    )

    with open(caminho_arquivo_escola, "rb") as f:
        uploaded_file = SimpleUploadedFile(
            "escolas.xlsx",
            f.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    parceira = baker.make("TipoGestao", nome="PARCEIRA")
    direta = baker.make("TipoGestao", nome="DIRETA")
    mista = baker.make("TipoGestao", nome="MISTA")
    tercerizada = baker.make("TipoGestao", nome="TERC TOTAL")

    escola1 = baker.make("Escola", codigo_eol="123456", tipo_gestao=None)
    escola2 = baker.make("Escola", codigo_eol="789012", tipo_gestao=None)

    planilha_atualizacao_tipo_gestao = baker.make(
        "PlanilhaAtualizacaoTipoGestaoEscola",
        conteudo=uploaded_file,
        criado_em=datetime.date.today(),
        status=StatusProcessamentoArquivo.PENDENTE.value,
    )
    return (
        escola1,
        escola2,
        planilha_atualizacao_tipo_gestao,
        caminho_arquivo_escola,
        parceira,
        direta,
    )


@pytest.fixture
def update_log_alunos_matriculados(
    log_alunos_matriculados_periodo_escola_regular,
    log_alunos_matriculados_periodo_escola_programas,
):
    log_alunos_matriculados_periodo_escola_regular.criado_em = datetime.date(2025, 2, 5)
    log_alunos_matriculados_periodo_escola_regular.save()

    log_alunos_matriculados_periodo_escola_programas.criado_em = datetime.date(
        2025, 2, 1
    )
    log_alunos_matriculados_periodo_escola_programas.save()

    return (
        log_alunos_matriculados_periodo_escola_regular,
        log_alunos_matriculados_periodo_escola_programas,
    )


@pytest.fixture
def dicionario_de_alunos_matriculados():
    manha = baker.make(models.PeriodoEscolar, nome="MANHA")
    tarde = baker.make(models.PeriodoEscolar, nome="TARDE")
    integral = baker.make(models.PeriodoEscolar, nome="INTEGRAL")

    escola = baker.make(models.Escola, codigo_eol=fake.name()[:6])
    alunos_matriculados_integral = baker.make(
        models.AlunosMatriculadosPeriodoEscola,
        escola=escola,
        periodo_escolar=integral,
        tipo_turma=models.TipoTurma.REGULAR.name,
        quantidade_alunos=25,
    )
    alunos_matriculados_manha = baker.make(
        models.AlunosMatriculadosPeriodoEscola,
        escola=escola,
        periodo_escolar=manha,
        tipo_turma=models.TipoTurma.REGULAR.name,
        quantidade_alunos=25,
    )
    alunos_matriculados_noite = baker.make(
        models.AlunosMatriculadosPeriodoEscola,
        escola=escola,
        tipo_turma=models.TipoTurma.PROGRAMAS.name,
        quantidade_alunos=25,
    )

    matriculados = [
        {
            "codigoEolEscola": escola.codigo_eol,
            "turnos": [
                {
                    "turno": alunos_matriculados_integral.periodo_escolar.nome,
                    "quantidade": alunos_matriculados_integral.quantidade_alunos,
                },
                {
                    "turno": alunos_matriculados_manha.periodo_escolar.nome,
                    "quantidade": alunos_matriculados_manha.quantidade_alunos,
                },
                {
                    "turno": "noite",
                    "quantidade": alunos_matriculados_noite.quantidade_alunos,
                },
            ],
        }
    ]

    escolas = baker.make(models.Escola, _quantity=6)
    for escola in escolas:
        matriculados.append(
            {
                "codigoEolEscola": escola.codigo_eol,
                "turnos": [{"turno": "integral", "quantidade": 40}],
            }
        )
    return matriculados


@pytest.fixture
def lista_dias_letivos(escola, dia_calendario_letivo, dia_calendario_nao_letivo):
    dias_letivos = [
        {
            "data": dia_calendario_letivo.data.strftime("%Y-%m-%dT00:00:00"),
            "ehLetivo": dia_calendario_letivo.dia_letivo,
        },
        {
            "data": dia_calendario_nao_letivo.data.strftime("%Y-%m-%dT00:00:00"),
            "ehLetivo": dia_calendario_nao_letivo.dia_letivo,
        },
        {
            "data": datetime.datetime(2021, 9, 26).strftime("%Y-%m-%dT00:00:00"),
            "ehLetivo": False,
        },
    ]
    return escola, dias_letivos


@pytest.fixture
def excluir_alunos_periodo_parcial(escola, aluno, escola_cei):
    data = datetime.datetime(2025, 2, 7)
    solicitacao_medicao_inicial = baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola,
        ano=data.year,
        mes=f"{data.month:02d}",
    )
    baker.make(
        "AlunoPeriodoParcial",
        aluno=aluno,
        escola=escola,
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
    )

    data_referencia = datetime.datetime(2025, 1, 1)
    solicitacao_medicao_inicial = baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola,
        ano=data_referencia.year,
        mes=f"{data_referencia.month:02d}",
    )
    baker.make(
        "AlunoPeriodoParcial",
        aluno=aluno,
        escola=escola,
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
    )

    solicitacao_medicao_inicial = baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola_cei,
        ano=data_referencia.year,
        mes=f"{data_referencia.month:02d}",
    )
    baker.make(
        "AlunoPeriodoParcial",
        aluno=aluno,
        escola=escola_cei,
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
    )

    return escola_cei, data_referencia


@pytest.fixture
def alteracao_cardapio(escola):
    return baker.make(
        AlteracaoCardapio,
        escola=escola,
        observacao="teste",
        data_inicial=datetime.date(2025, 2, 1),
        data_final=datetime.date(2025, 3, 17),
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
    )


@freeze_time("2025-01-01")
@pytest.fixture
def dieta_codae_autorizou(aluno, escola):
    aluno.nome = "Antônio"
    aluno.save()
    classificacao = baker.make("ClassificacaoDieta", nome="Tipo A")
    solicitacao_dieta = baker.make(
        "SolicitacaoDietaEspecial",
        rastro_escola=escola,
        aluno=aluno,
        classificacao=classificacao,
        tipo_solicitacao="COMUM",
    )
    solicitacao_dieta.criado_em = datetime.date(2025, 1, 1)
    solicitacao_dieta.save()

    log = baker.make(
        "LogSolicitacoesUsuario",
        status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        uuid_original=solicitacao_dieta.uuid,
    )
    log.criado_em = datetime.date(2025, 1, 1)
    log.save()

    return solicitacao_dieta


@pytest.fixture
def dieta_cancelada(aluno, escola):
    aluno.nome = "Lucas"
    aluno.save()
    classificacao = baker.make("ClassificacaoDieta", nome="Tipo B")

    solicitacao_dieta = baker.make(
        "SolicitacaoDietaEspecial",
        rastro_escola=escola,
        aluno=aluno,
        classificacao=classificacao,
    )
    baker.make(
        "LogSolicitacoesUsuario",
        status_evento=LogSolicitacoesUsuario.CANCELADO_ALUNO_MUDOU_ESCOLA,
        uuid_original=solicitacao_dieta.uuid,
    )
    return solicitacao_dieta


@pytest.fixture
def mock_diretoria_regional():
    dre_mock = MagicMock()
    dre_mock.nome = "DRE Teste"
    dre_mock.codigo_eol = "12345"
    return [dre_mock]


@pytest.fixture
def mock_tipo_turma():
    mock = MagicMock()
    mock.name = "Ensino Fundamental"
    mock.value = "EF"
    return mock


@pytest.fixture
def mock_escolas(escola):
    escola_mock = MagicMock()
    escola_mock.nome = escola.nome
    escola_mock.codigo_eol = "12345"
    return [escola_mock]


@pytest.fixture
def users_diretor_escola(django_user_model, escola):
    user = django_user_model.objects.create_user(
        username="system@admin.com", email="system@admin.com"
    )
    perfil_diretor = baker.make(
        "Perfil",
        nome="DIRETOR_UE",
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
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

    return user


@pytest.fixture
def solicitacoes_vencidas(
    users_diretor_escola,
    grupo_inclusao_alimentacao_normal_factory,
    inclusao_alimentacao_normal_factory,
    log_solicitacoes_usuario_factory,
):
    instituicao = users_diretor_escola.vinculo_atual.instituicao

    grupo_inclusao_alimentacao_normal = (
        grupo_inclusao_alimentacao_normal_factory.create(
            escola=instituicao,
            rastro_lote=instituicao.lote,
            rastro_dre=instituicao.diretoria_regional,
            rastro_escola=instituicao,
            status=PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
        )
    )
    inclusao_alimentacao_normal_factory.create(
        data="2025-01-14",
        grupo_inclusao=grupo_inclusao_alimentacao_normal,
    )
    log_solicitacoes_usuario_factory.create(
        uuid_original=grupo_inclusao_alimentacao_normal.uuid,
        status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
        usuario=users_diretor_escola,
    )


@pytest.fixture
def solicitacoes_pendentes_autorizacao_vencidas(
    users_diretor_escola,
    grupo_inclusao_alimentacao_normal_factory,
    inclusao_alimentacao_normal_factory,
    log_solicitacoes_usuario_factory,
):
    instituicao = users_diretor_escola.vinculo_atual.instituicao

    grupo_inclusao_alimentacao_normal = (
        grupo_inclusao_alimentacao_normal_factory.create(
            escola=instituicao,
            rastro_lote=instituicao.lote,
            rastro_dre=instituicao.diretoria_regional,
            rastro_escola=instituicao,
            status=PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
        )
    )
    inclusao_alimentacao_normal_factory.create(
        data="2025-01-14",
        grupo_inclusao=grupo_inclusao_alimentacao_normal,
    )
    log_solicitacoes_usuario_factory.create(
        uuid_original=grupo_inclusao_alimentacao_normal.uuid,
        status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
        usuario=users_diretor_escola,
    )

    grupo_inclusao_alimentacao_normal = (
        grupo_inclusao_alimentacao_normal_factory.create(
            escola=instituicao,
            rastro_lote=instituicao.lote,
            rastro_dre=instituicao.diretoria_regional,
            rastro_escola=instituicao,
            status=PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO,
        )
    )
    inclusao_alimentacao_normal_factory.create(
        data="2025-01-14",
        grupo_inclusao=grupo_inclusao_alimentacao_normal,
    )
    log_solicitacoes_usuario_factory.create(
        uuid_original=grupo_inclusao_alimentacao_normal.uuid,
        status_evento=LogSolicitacoesUsuario.DRE_VALIDOU,
        usuario=users_diretor_escola,
    )


@pytest.fixture
def escola_edital_41(escola):
    edital = baker.make(
        "Edital",
        numero="Edital de Pregão nº 41/sme/2017",
        uuid="12288b47-9d27-4089-8c2e-48a6061d83ea",
    )
    contrato = baker.make(
        "Contrato",
        terceirizada=baker.make("Terceirizada"),
        edital=edital,
        make_m2m=True,
        uuid="44d51e10-8999-48bb-889a-1540c9e8c895",
    )
    contrato.lotes.set([escola.lote])

    marca = baker.make("Marca", nome="NAMORADOS")
    fabricante = baker.make("Fabricante", nome="Fabricante 001")
    produto = baker.make("Produto", nome="ARROZ", marca=marca, fabricante=fabricante)
    homologacao = baker.make(
        "HomologacaoProduto",
        produto=produto,
        rastro_terceirizada=escola.lote.terceirizada,
        status=HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO,
    )

    log = baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=homologacao.uuid,
        criado_em=datetime.date(2023, 1, 1),
        status_evento=22,  # CODAE_HOMOLOGADO
        solicitacao_tipo=10,
    )  # HOMOLOGACAO_PRODUTO
    log.criado_em = datetime.date(2023, 1, 1)
    log.save()

    pe_1 = baker.make(
        "ProdutoEdital",
        produto=produto,
        edital=edital,
        tipo_produto="Comum",
        uuid="0f81a49b-0836-42d5-af9e-12cbd7ca76a8",
    )

    return escola


@pytest.fixture
def tipo_alimentacao():
    return baker.make("cardapio.TipoAlimentacao", nome="Refeição")


@pytest.fixture
def tipo_alimentacao_lanche_emergencial():
    return baker.make("cardapio.TipoAlimentacao", nome="Sobremesa")


@pytest.fixture
def escola_cmct(tipo_alimentacao, tipo_alimentacao_lanche_emergencial):
    noite = baker.make(models.PeriodoEscolar, nome="NOITE", tipo_turno=2)
    manha = baker.make(models.PeriodoEscolar, nome="MANHA", tipo_turno=1)
    tipo_unidade_escolar = baker.make(models.TipoUnidadeEscolar, iniciais="CMCT")
    baker.make(
        "cardapio.VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        periodo_escolar=manha,
        tipo_unidade_escolar=tipo_unidade_escolar,
        tipos_alimentacao=[tipo_alimentacao, tipo_alimentacao_lanche_emergencial],
    )
    baker.make(
        "cardapio.VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        periodo_escolar=noite,
        tipo_unidade_escolar=tipo_unidade_escolar,
        tipos_alimentacao=[tipo_alimentacao, tipo_alimentacao_lanche_emergencial],
    )

    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    diretoria_regional = baker.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL TESTE"
    )
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    escola = baker.make(
        "Escola",
        nome="CMCT TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
    )
    baker.make(
        "Aluno",
        escola=escola,
        periodo_escolar=manha,
    )
    baker.make(
        "Aluno",
        escola=escola,
        periodo_escolar=noite,
    )

    baker.make(
        models.AlunosMatriculadosPeriodoEscola,
        escola=escola,
        periodo_escolar=manha,
        quantidade_alunos=50,
        tipo_turma=models.TipoTurma.PROGRAMAS.name,
    )
    baker.make(
        models.AlunosMatriculadosPeriodoEscola,
        escola=escola,
        periodo_escolar=noite,
        quantidade_alunos=50,
        tipo_turma=models.TipoTurma.PROGRAMAS.name,
    )

    return escola


@pytest.fixture
def mock_request():
    request = MagicMock()
    request.user = MagicMock()
    request.user.vinculo_atual.perfil.nome = None
    request.user.vinculo_atual.content_type.model = None
    return request
