import datetime
import json
import uuid

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from faker import Faker
from model_mommy import mommy

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

# from sme_sigpae_api.escola.utils_analise_dietas_ativas import (
#     dict_codigo_aluno_por_codigo_escola,
#     dict_codigos_escolas,
# )


fake = Faker("pt_BR")
Faker.seed(420)


@pytest.fixture
def tipo_unidade_escolar():
    cardapio1 = mommy.make("cardapio.Cardapio", data=datetime.date(2019, 10, 11))
    cardapio2 = mommy.make("cardapio.Cardapio", data=datetime.date(2019, 10, 15))
    return mommy.make(
        models.TipoUnidadeEscolar, iniciais="EMEF", cardapios=[cardapio1, cardapio2]
    )


@pytest.fixture
def tipo_gestao():
    return mommy.make(models.TipoGestao, nome="TERC TOTAL")


@pytest.fixture
def diretoria_regional(tipo_gestao):
    dre = mommy.make(
        models.DiretoriaRegional,
        nome=fake.name(),
        uuid="d305add2-f070-4ad3-8c17-ba9664a7c655",
        make_m2m=True,
    )
    mommy.make("Escola", diretoria_regional=dre, tipo_gestao=tipo_gestao)
    mommy.make("Escola", diretoria_regional=dre, tipo_gestao=tipo_gestao)
    mommy.make("Escola", diretoria_regional=dre, tipo_gestao=tipo_gestao)
    return dre


@pytest.fixture
def lote():
    return mommy.make(
        models.Lote,
        nome="lote",
        iniciais="lt",
        uuid="49696643-7a47-4324-989b-9380177fef2d",
    )


@pytest.fixture
def escola(lote, tipo_gestao, diretoria_regional):
    return mommy.make(
        models.Escola,
        nome=fake.name(),
        diretoria_regional=diretoria_regional,
        codigo_eol=fake.name()[:6],
        lote=lote,
        tipo_gestao=tipo_gestao,
    )


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
def escola_cemei(periodo_escolar):
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make("Lote", terceirizada=terceirizada)
    diretoria_regional = mommy.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL TESTE"
    )
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = mommy.make("TipoUnidadeEscolar", iniciais="CEMEI")
    escola = mommy.make(
        "Escola",
        nome="CEMEI TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
    )
    mommy.make(
        "Aluno",
        serie="1",
        escola=escola,
        periodo_escolar=periodo_escolar,
        ciclo=Aluno.CICLO_ALUNO_CEI,
    )
    mommy.make(
        "Aluno",
        serie="5",
        escola=escola,
        periodo_escolar=periodo_escolar,
        ciclo=Aluno.CICLO_ALUNO_EMEI,
    )
    return escola


@pytest.fixture
def escola_emebs(periodo_escolar):
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make("Lote", terceirizada=terceirizada)
    diretoria_regional = mommy.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL TESTE"
    )
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = mommy.make("TipoUnidadeEscolar", iniciais="EMEBS")
    escola = mommy.make(
        "Escola",
        nome="EMEBS TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
    )
    mommy.make(
        "Aluno",
        etapa=Aluno.ETAPA_INFANTIL,
        escola=escola,
        periodo_escolar=periodo_escolar,
    )
    mommy.make("Aluno", serie=14, escola=escola, periodo_escolar=periodo_escolar)
    return escola


@pytest.fixture
def escola_simplissima_serializer(escola):
    return EscolaSimplissimaSerializer(escola)


@pytest.fixture
def faixa_idade_escolar():
    return mommy.make(models.FaixaIdadeEscolar, nome=fake.name())


@pytest.fixture
def codae(escola):
    return mommy.make(models.Codae, make_m2m=True)


@pytest.fixture
def periodo_escolar():
    return mommy.make(models.PeriodoEscolar, nome="INTEGRAL", tipo_turno=1)


@pytest.fixture
def periodo_escolar_parcial():
    return mommy.make(models.PeriodoEscolar, nome="PARCIAL")


@pytest.fixture
def escola_periodo_escolar(periodo_escolar):
    return mommy.make(models.EscolaPeriodoEscolar, periodo_escolar=periodo_escolar)


@pytest.fixture
def sub_prefeitura():
    return mommy.make(models.Subprefeitura)


@pytest.fixture
def vinculo(escola):
    return mommy.make(
        Vinculo, uuid="a19baa09-f8cc-49a7-a38d-2a38270ddf45", instituicao=escola
    )


@pytest.fixture
def vinculo_instituto_serializer(vinculo):
    return VinculoInstituicaoSerializer(vinculo)


@pytest.fixture
def aluno(escola):
    return mommy.make(
        models.Aluno,
        nome="Fulano da Silva",
        codigo_eol="000001",
        data_nascimento=datetime.date(2000, 1, 1),
        escola=escola,
    )


@pytest.fixture
def client_autenticado_coordenador_codae(client, django_user_model):
    email, password, rf, cpf = (
        "cogestor_1@sme.prefeitura.sp.gov.br",
        "adminadmin",
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
    mommy.make(
        "TipoUnidadeEscolar",
        iniciais="EMEF",
        uuid="1cc3253b-e297-42b3-8e57-ebfd115a1aba",
    )
    mommy.make(
        "TipoUnidadeEscolar",
        iniciais="CEU GESTAO",
        uuid="40ee89a7-dc70-4abb-ae21-369c67f2b9e3",
    )
    mommy.make(
        "TipoUnidadeEscolar",
        iniciais="CIEJA",
        uuid="ac4858ff-1c11-41f3-b539-7a02696d6d1b",
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
def client_autenticado_da_dre(client, django_user_model, diretoria_regional):
    email = "user@dre.com"
    password = "admin@123"
    perfil_adm_dre = mommy.make("Perfil", nome="ADM_DRE", ativo=True)
    usuario = django_user_model.objects.create_user(
        password=password, username=email, email=email, registro_funcional="123456"
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
def faixas_etarias(faixas_etarias_ativas):
    return faixas_etarias_ativas + mommy.make("FaixaEtaria", ativo=False, _quantity=8)


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
        mommy.make("FaixaEtaria", inicio=inicio_faixa, fim=fim_faixa, ativo=True),
        eh_pertencente,
    )


@pytest.fixture
def arquivo():
    return SimpleUploadedFile(
        "planilha-teste.pdf", bytes("CONTEUDO TESTE TESTE TESTE", encoding="utf-8")
    )


@pytest.fixture
def planilha_de_para_eol_codae(arquivo):
    return mommy.make(
        "PlanilhaEscolaDeParaCodigoEolCodigoCoade",
        planilha=arquivo,
        criado_em=datetime.date.today(),
        codigos_codae_vinculados=False,
    )


@pytest.fixture
def planilha_atualizacao_tipo_gestao(arquivo):
    return mommy.make(
        "PlanilhaAtualizacaoTipoGestaoEscola",
        conteudo=arquivo,
        criado_em=datetime.date.today(),
        status="SUCESSO",
    )


@pytest.fixture
def alunos_matriculados_periodo_escola_regular(escola, periodo_escolar):
    return mommy.make(
        models.AlunosMatriculadosPeriodoEscola,
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=50,
        tipo_turma=models.TipoTurma.REGULAR.name,
    )


@pytest.fixture
def alunos_matriculados_periodo_escola_programas(escola, periodo_escolar):
    return mommy.make(
        models.AlunosMatriculadosPeriodoEscola,
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=50,
        tipo_turma=models.TipoTurma.PROGRAMAS.name,
    )


@pytest.fixture
def log_alunos_matriculados_periodo_escola_regular(escola, periodo_escolar):
    return mommy.make(
        models.LogAlunosMatriculadosPeriodoEscola,
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=50,
        tipo_turma=models.TipoTurma.REGULAR.name,
    )


@pytest.fixture
def log_alunos_matriculados_periodo_escola_programas(escola, periodo_escolar):
    return mommy.make(
        models.LogAlunosMatriculadosPeriodoEscola,
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=50,
        tipo_turma=models.TipoTurma.PROGRAMAS.name,
    )


@pytest.fixture
def dia_calendario_letivo(escola):
    return mommy.make(
        models.DiaCalendario,
        escola=escola,
        data=datetime.datetime(2021, 9, 24),
        dia_letivo=True,
    )


@pytest.fixture
def dia_calendario_nao_letivo(escola):
    return mommy.make(
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
    return mommy.make(
        models.LogAlunosMatriculadosFaixaEtariaDia,
        escola=escola,
        periodo_escolar=periodo_escolar,
        faixa_etaria=faixas_etarias_ativas[0],
        quantidade=100,
        data=datetime.date.today(),
    )


@pytest.fixture
def log_atualiza_dados_aluno(escola):
    return mommy.make(
        models.LogAtualizaDadosAluno, codigo_eol=escola.codigo_eol, status=200
    )


@pytest.fixture
def log_alteracao_quantidade_alunos_por_escola_periodo(escola, periodo_escolar):
    return mommy.make(
        models.LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar,
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos_de=15,
        quantidade_alunos_para=30,
    )


@pytest.fixture
def log_rotina_diaria_alunos():
    return mommy.make(
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
        aluno = mommy.make(
            "Aluno",
            codigo_eol=informacao_aluno["codigoAluno"],
            data_nascimento=dt_nascimento_from_api(informacao_aluno["dataNascimento"]),
            escola=escola_cei,
            periodo_escolar=periodo_escolar,
        )
        mommy.make(
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
        mommy.make(
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
    return mommy.make(
        "DiaSuspensaoAtividades",
        data=datetime.date(2022, 8, 8),
        tipo_unidade=tipo_unidade_escolar,
    )


@pytest.fixture
def dados_planilha_alunos_matriculados(alunos_matriculados_periodo_escola_regular):
    faixas_etarias = [{"nome": "04 anos a 06 anos", "uuid": uuid.uuid4()}]
    queryset = [
        {
            "dre": alunos_matriculados_periodo_escola_regular.escola.diretoria_regional.nome,
            "lote": alunos_matriculados_periodo_escola_regular.escola.lote.nome
            if alunos_matriculados_periodo_escola_regular.escola.lote
            else " - ",
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
            "lote": alunos_matriculados_periodo_escola_regular.escola.lote.nome
            if alunos_matriculados_periodo_escola_regular.escola.lote
            else " - ",
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
    mommy.make("ProtocoloDeDietaEspecial", nome="Protocolo1")
    mommy.make("ProtocoloDeDietaEspecial", nome="Protocolo2")
    mommy.make("ProtocoloDeDietaEspecial", nome="Protocolo3")


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
