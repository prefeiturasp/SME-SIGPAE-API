import datetime
import json
import random
from io import BytesIO

import pandas as pd
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from model_bakery import baker

from sme_sigpae_api.dados_comuns.behaviors import TempoPasseio
from sme_sigpae_api.dados_comuns.fluxo_status import SolicitacaoMedicaoInicialWorkflow
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.escola.models import (
    DiaCalendario,
    Escola,
    LogAlunosMatriculadosPeriodoEscola,
    PeriodoEscolar,
    TipoTurma,
)
from sme_sigpae_api.medicao_inicial.models import (
    AlimentacaoLancamentoEspecial,
    Medicao,
    PermissaoLancamentoEspecial,
    SolicitacaoMedicaoInicial,
)
from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_cei import (
    insere_tabela_periodos_na_planilha as cei_insere_tabela,
)
from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_cemei import (
    insere_tabela_periodos_na_planilha as cemei_insere_tabela,
)
from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_emebs import (
    insere_tabela_periodos_na_planilha as emebs_insere_tabela,
)
from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_emei_emef import (
    insere_tabela_periodos_na_planilha as emei_emef_insere_tabela,
)


@pytest.fixture
def kit_lanche_1():
    return baker.make("KitLanche", nome="KIT 1")


@pytest.fixture
def kit_lanche_2():
    return baker.make("KitLanche", nome="KIT 2")


@pytest.fixture
def grupo_programas_e_projetos():
    return baker.make("GrupoMedicao", nome="Programas e Projetos")


@pytest.fixture
def grupo_etec():
    return baker.make("GrupoMedicao", nome="ETEC")


@pytest.fixture
def grupo_solicitacoes_alimentacao():
    return baker.make("GrupoMedicao", nome="Solicitações de Alimentação")


@pytest.fixture
def grupo_infantil_integral():
    return baker.make("GrupoMedicao", nome="Infantil INTEGRAL")


@pytest.fixture
def grupo_infantil_manha():
    return baker.make("GrupoMedicao", nome="Infantil MANHA")


@pytest.fixture
def grupo_infantil_tarde():
    return baker.make("GrupoMedicao", nome="Infantil TARDE")


@pytest.fixture
def motivo_inclusao_continua_programas_projetos():
    return baker.make("MotivoInclusaoContinua", nome="Programas/Projetos Contínuos")


@pytest.fixture
def motivo_inclusao_continua_etec():
    return baker.make("MotivoInclusaoContinua", nome="ETEC")


@pytest.fixture
def tipo_alimentacao_refeicao():
    return baker.make("TipoAlimentacao", nome="Refeição")


@pytest.fixture
def tipo_alimentacao_lanche():
    return baker.make("TipoAlimentacao", nome="Lanche")


@pytest.fixture
def tipo_alimentacao_lanche_4h():
    return baker.make("TipoAlimentacao", nome="Lanche 4h")


@pytest.fixture
def tipo_alimentacao_sobremesa():
    return baker.make("TipoAlimentacao", nome="Sobremesa")


@pytest.fixture
def tipo_alimentacao_almoco():
    return baker.make("TipoAlimentacao", nome="Almoço")


@pytest.fixture
def tipo_alimentacao_lanche_emergencial():
    return baker.make("TipoAlimentacao", nome="Lanche Emergencial")


@pytest.fixture
def classificacao_dieta_tipo_a():
    return baker.make("ClassificacaoDieta", nome="Tipo A")


@pytest.fixture
def classificacao_dieta_tipo_a_enteral():
    return baker.make("ClassificacaoDieta", nome="Tipo A ENTERAL")


@pytest.fixture
def tipo_unidade_escolar():
    return baker.make("TipoUnidadeEscolar", iniciais="EMEF")


@pytest.fixture
def tipo_unidade_escolar_ceu_emef():
    return baker.make("TipoUnidadeEscolar", iniciais="CEU EMEF")


@pytest.fixture
def tipo_unidade_escolar_ceu_emei():
    return baker.make("TipoUnidadeEscolar", iniciais="CEU EMEI")


@pytest.fixture
def tipo_unidade_escolar_emefm():
    return baker.make("TipoUnidadeEscolar", iniciais="EMEFM")


@pytest.fixture
def tipo_unidade_escolar_cieja():
    return baker.make("TipoUnidadeEscolar", iniciais="CIEJA")


@pytest.fixture
def tipo_unidade_escolar_ceu_gestao():
    return baker.make("TipoUnidadeEscolar", iniciais="CEU GESTAO")


@pytest.fixture
def dia_sobremesa_doce(tipo_unidade_escolar):
    edital = baker.make(
        "Edital",
        numero="Edital de Pregão nº 13/SME/2020",
        uuid="3a9082ae-2b8c-44f6-83af-fcab9452f932",
    )
    return baker.make(
        "DiaSobremesaDoce",
        data=datetime.date(2022, 8, 8),
        tipo_unidade=tipo_unidade_escolar,
        edital=edital,
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
    emef = baker.make(
        "TipoUnidadeEscolar",
        iniciais="EMEF",
        uuid="1cc3253b-e297-42b3-8e57-ebfd115a1aba",
    )
    baker.make("Escola", tipo_unidade=emef, uuid="95ad02fb-d746-4e0c-95f4-0181a99bc192")
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
    edital = baker.make(
        "Edital",
        numero="Edital de Pregão nº 75/SME/2022",
        uuid="85d4bdf1-79d3-4f93-87d7-9999ae4cd9c2",
    )
    edital = baker.make(
        "Edital",
        numero="Edital de Pregão nº 36/SME/2022",
        uuid="10b56d45-b82d-4cce-9a14-36bbb082ac4d",
    )
    edital = baker.make(
        "Edital",
        numero="Edital de Pregão nº 18/SME/2023",
        uuid="00f008ea-3410-4547-99e6-4e91e0168af8",
    )
    return client


@pytest.fixture
def escola(tipo_unidade_escolar, diretoria_regional):
    terceirizada = baker.make("Terceirizada")
    lote = baker.make(
        "Lote",
        nome="1",
        terceirizada=terceirizada,
        diretoria_regional=diretoria_regional,
    )
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    return baker.make(
        "Escola",
        nome="EMEF TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
        codigo_eol="123456",
    )


@pytest.fixture
def escola_emefm(diretoria_regional):
    terceirizada = baker.make("Terceirizada")
    lote = baker.make(
        "Lote",
        nome="1",
        terceirizada=terceirizada,
        diretoria_regional=diretoria_regional,
    )
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = baker.make("TipoUnidadeEscolar", iniciais="EMEFM")
    return baker.make(
        "Escola",
        nome="EMEFM TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
        codigo_eol="457692",
    )


@pytest.fixture
def escola_emei():
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    diretoria_regional = baker.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL TESTE"
    )
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = baker.make("TipoUnidadeEscolar", iniciais="EMEI")
    return baker.make(
        "Escola",
        nome="EMEI TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
        codigo_eol="987654",
    )


@pytest.fixture
def escola_ceu_emei(tipo_unidade_escolar_ceu_emei):
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    diretoria_regional = baker.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL TESTE"
    )
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    return baker.make(
        "Escola",
        nome="CEU EMEI TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar_ceu_emei,
        codigo_eol="876543",
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
        codigo_eol="765432",
    )


@pytest.fixture
def escola_cci():
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    diretoria_regional = baker.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL TESTE"
    )
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = baker.make("TipoUnidadeEscolar", iniciais="CCI")
    return baker.make(
        "Escola",
        nome="CCI TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
        codigo_eol="654321",
    )


@pytest.fixture
def log_aluno_integral_cei(escola_cei, periodo_escolar_integral):
    log = baker.make(
        "LogAlunosMatriculadosPeriodoEscola",
        escola=escola_cei,
        periodo_escolar=periodo_escolar_integral,
        quantidade_alunos=100,
    )
    log.criado_em = datetime.date(2025, 5, 5)
    log.save()
    return log


@pytest.fixture
def log_alunos_matriculados_integral_cei(escola_cei, periodo_escolar_integral):
    return baker.make(
        "AlunosMatriculadosPeriodoEscola",
        escola=escola_cei,
        periodo_escolar=periodo_escolar_integral,
        quantidade_alunos=100,
    )


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
        codigo_eol="543210",
    )


@pytest.fixture
def escola_ceu_cemei():
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    diretoria_regional = baker.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL TESTE"
    )
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = baker.make("TipoUnidadeEscolar", iniciais="CEU CEMEI")
    return baker.make(
        "Escola",
        nome="CEU CEMEI TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
        codigo_eol="432105",
    )


@pytest.fixture
def escola_emebs():
    terceirizada = baker.make("Terceirizada")
    diretoria_regional = baker.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL TESTE",
    )
    lote = baker.make(
        "Lote", terceirizada=terceirizada, diretoria_regional=diretoria_regional
    )
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = baker.make("TipoUnidadeEscolar", iniciais="EMEBS")
    return baker.make(
        "Escola",
        nome="EMEBS TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
        codigo_eol="000329",
    )


@pytest.fixture
def escola_ceu_gestao():
    terceirizada = baker.make("Terceirizada")
    diretoria_regional = baker.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL TESTE"
    )
    lote = baker.make(
        "Lote", terceirizada=terceirizada, diretoria_regional=diretoria_regional
    )
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = baker.make("TipoUnidadeEscolar", iniciais="CEU GESTAO")
    return baker.make(
        "Escola",
        nome="CEMEI TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
    )


@pytest.fixture
def aluno():
    return baker.make(
        "Aluno",
        nome="Roberto Alves da Silva",
        codigo_eol="123456",
        data_nascimento="2000-01-01",
        uuid="2d20157a-4e52-4d25-a4c7-9c0e6b67ee18",
    )


@pytest.fixture
def solicitacao_medicao_inicial_cemei(escola_cemei, categoria_medicao):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_integral = baker.make("PeriodoEscolar", nome="INTEGRAL")
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial", mes=4, ano=2023, escola=escola_cemei
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_integral,
    )
    baker.make(
        "FaixaEtaria", inicio=1, fim=10, uuid="0c914b27-c7cd-4682-a439-a4874745b005"
    )
    faixa_etaria = baker.make(
        "FaixaEtaria", inicio=1, fim=2, uuid="1d125c38-ce75-6974-b25d-a4874745b996"
    )
    baker.make(
        "ValorMedicao",
        dia="01",
        semana="1",
        nome_campo="frequencia",
        medicao=medicao,
        categoria_medicao=categoria_medicao,
        valor="10",
        faixa_etaria=faixa_etaria,
    )
    return solicitacao_medicao


@pytest.fixture
def solicitacao_medicao_inicial_cei(
    escola_cei, categoria_medicao, periodo_escolar_integral, periodo_escolar_manha
):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    baker.make(
        LogAlunosMatriculadosPeriodoEscola,
        escola=escola_cei,
        criado_em="01-04-2023",
        quantidade_alunos=100,
        periodo_escolar=periodo_escolar_manha,
    )
    baker.make(
        LogAlunosMatriculadosPeriodoEscola,
        escola=escola_cei,
        criado_em="01-04-2023",
        quantidade_alunos=100,
        periodo_escolar=periodo_escolar_integral,
    )
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=4,
        ano=2023,
        escola=escola_cei,
        ue_possui_alunos_periodo_parcial=True,
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_escolar_integral,
    )
    baker.make(
        "FaixaEtaria", inicio=1, fim=10, uuid="0c914b27-c7cd-4682-a439-a4874745b005"
    )
    baker.make("Aluno", periodo_escolar=periodo_escolar_manha, escola=escola_cei)
    return solicitacao_medicao


@pytest.fixture
def solicitacao_medicao_inicial_valores_cei(escola_cei, categoria_medicao):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_integral = baker.make("PeriodoEscolar", nome="INTEGRAL")
    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=4,
        ano=2023,
        escola=escola_cei,
        ue_possui_alunos_periodo_parcial=True,
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_manha = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
    )
    medicao_integral = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_integral,
    )
    faixa_etaria = baker.make(
        "FaixaEtaria", inicio=1, fim=10, uuid="0c914b27-c7cd-4682-a439-a4874745b005"
    )
    baker.make("Aluno", periodo_escolar=periodo_manha, escola=escola_cei)
    baker.make(
        "ValorMedicao",
        dia="01",
        semana="1",
        nome_campo="frequencia",
        medicao=medicao_manha,
        categoria_medicao=categoria_medicao,
        valor="10",
        faixa_etaria=faixa_etaria,
    )
    baker.make(
        "ValorMedicao",
        dia="01",
        semana="1",
        nome_campo="frequencia",
        medicao=medicao_integral,
        categoria_medicao=categoria_medicao,
        valor="05",
        faixa_etaria=faixa_etaria,
    )
    return solicitacao_medicao


@pytest.fixture
def make_solicitacao_medicao_inicial(escola):
    def handle(mes: int, ano: int, status: str | None = None):
        tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
        solicitacao_medicao = baker.make(
            "SolicitacaoMedicaoInicial",
            mes=mes,
            ano=ano,
            escola=escola,
            rastro_lote=escola.lote,
            status=status,
        )
        solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
        return solicitacao_medicao

    return handle


@pytest.fixture
def solicitacao_medicao_inicial(escola, categoria_medicao, aluno):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    historico = {
        "usuario": {
            "uuid": "a7f20675-50e1-46d2-a207-28543b93e19d",
            "nome": "usuario teste",
            "username": "12312312344",
            "email": "email@teste.com",
        },
        "criado_em": datetime.date.today().strftime("%Y-%m-%d %H:%M:%S"),
        "acao": "MEDICAO_CORRECAO_SOLICITADA",
        "alteracoes": [
            {
                "periodo_escolar": periodo_manha.nome,
                "tabelas_lancamentos": [
                    {
                        "categoria_medicao": "ALIMENTAÇÃO",
                        "semanas": [{"semana": "1", "dias": ["01"]}],
                    }
                ],
            },
        ],
    }
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial",
        uuid="bed4d779-2d57-4c5f-bf9c-9b93ddac54d9",
        mes=12,
        ano=2022,
        escola=escola,
        rastro_lote=escola.lote,
        historico=json.dumps([historico]),
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
    )
    baker.make(
        "AlunoPeriodoParcial",
        solicitacao_medicao_inicial=solicitacao_medicao,
        aluno=aluno,
        data=datetime.date(2022, 12, 1),
    )
    baker.make(
        "ValorMedicao",
        dia="01",
        semana="1",
        nome_campo="lanche",
        medicao=medicao,
        categoria_medicao=categoria_medicao,
        valor="10",
    )
    return solicitacao_medicao


@pytest.fixture
def solicitacao_medicao_inicial_medicao_enviada_pela_ue(solicitacao_medicao_inicial):
    for medicao in solicitacao_medicao_inicial.medicoes.all():
        medicao.status = (
            solicitacao_medicao_inicial.workflow_class.MEDICAO_APROVADA_PELA_DRE
        )
        medicao.save()
    solicitacao_medicao_inicial.status = (
        solicitacao_medicao_inicial.workflow_class.MEDICAO_ENVIADA_PELA_UE
    )
    solicitacao_medicao_inicial.save()
    return solicitacao_medicao_inicial


@pytest.fixture
def solicitacao_medicao_inicial_medicao_correcao_solicitada(
    solicitacao_medicao_inicial,
):
    solicitacao_medicao_inicial.status = (
        solicitacao_medicao_inicial.workflow_class.MEDICAO_CORRECAO_SOLICITADA
    )
    solicitacao_medicao_inicial.save()
    return solicitacao_medicao_inicial


@pytest.fixture
def solicitacao_medicao_inicial_medicao_correcao_solicitada_codae(
    solicitacao_medicao_inicial,
):
    solicitacao_medicao_inicial.status = (
        solicitacao_medicao_inicial.workflow_class.MEDICAO_CORRECAO_SOLICITADA_CODAE
    )
    solicitacao_medicao_inicial.save()
    return solicitacao_medicao_inicial


@pytest.fixture
def solicitacao_medicao_inicial_medicao_aprovada_pela_dre_ok(
    solicitacao_medicao_inicial,
):
    for medicao in solicitacao_medicao_inicial.medicoes.all():
        medicao.status = (
            solicitacao_medicao_inicial.workflow_class.MEDICAO_APROVADA_PELA_CODAE
        )
        medicao.save()
    solicitacao_medicao_inicial.status = (
        solicitacao_medicao_inicial.workflow_class.MEDICAO_APROVADA_PELA_DRE
    )
    solicitacao_medicao_inicial.save()
    return solicitacao_medicao_inicial


@pytest.fixture
def solicitacao_medicao_inicial_medicao_aprovada_pela_dre_nok(
    solicitacao_medicao_inicial,
):
    solicitacao_medicao_inicial.status = (
        solicitacao_medicao_inicial.workflow_class.MEDICAO_APROVADA_PELA_DRE
    )
    solicitacao_medicao_inicial.save()
    return solicitacao_medicao_inicial


@pytest.fixture
def solicitacao_medicao_inicial_medicao_enviada_pela_ue_nok(
    solicitacao_medicao_inicial,
):
    for medicao in solicitacao_medicao_inicial.medicoes.all():
        medicao.status = (
            solicitacao_medicao_inicial.workflow_class.MEDICAO_APROVADA_PELA_CODAE
        )
        medicao.save()
    solicitacao_medicao_inicial.status = (
        solicitacao_medicao_inicial.workflow_class.MEDICAO_ENVIADA_PELA_UE
    )
    solicitacao_medicao_inicial.save()
    return solicitacao_medicao_inicial


@pytest.fixture
def solicitacao_medicao_inicial_medicao_enviada_pela_ue_nok__2(
    solicitacao_medicao_inicial,
):
    for medicao in solicitacao_medicao_inicial.medicoes.all():
        medicao.status = (
            solicitacao_medicao_inicial.workflow_class.MEDICAO_APROVADA_PELA_DRE
        )
        medicao.save()
    status = (
        solicitacao_medicao_inicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
    )
    solicitacao_medicao_inicial.status = status
    solicitacao_medicao_inicial.save()
    return solicitacao_medicao_inicial


@pytest.fixture
def solicitacao_medicao_inicial_varios_valores(escola, categoria_medicao):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = baker.make("PeriodoEscolar", nome="TARDE")
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial", mes=12, ano=2022, escola=escola
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
    )
    medicao_programas_projetos = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_tarde,
    )
    categoria_dieta_a = baker.make(
        "CategoriaMedicao", nome="DIETA ESPECIAL - TIPO A ENTERAL"
    )
    categoria_dieta_b = baker.make("CategoriaMedicao", nome="DIETA ESPECIAL - TIPO B")
    for dia in ["01", "02", "03", "04", "05"]:
        for campo in ["lanche", "refeicao", "lanche_emergencial", "sobremesa"]:
            for categoria in [categoria_medicao, categoria_dieta_a, categoria_dieta_b]:
                for medicao_ in [medicao, medicao_programas_projetos]:
                    baker.make(
                        "ValorMedicao",
                        dia=dia,
                        nome_campo=campo,
                        medicao=medicao_,
                        categoria_medicao=categoria,
                        valor="10",
                    )
    return solicitacao_medicao


@pytest.fixture
def solicitacao_medicao_inicial_varios_valores_emebs(escola_emebs, categoria_medicao):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = baker.make("PeriodoEscolar", nome="TARDE")
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=12,
        ano=2023,
        escola=escola_emebs,
        uuid="da921e20-50f9-41ae-b2dc-4311d47029e8",
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_manha = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
    )
    medicao_tarde = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_tarde,
    )
    categoria_dieta_a = baker.make(
        "CategoriaMedicao", nome="DIETA ESPECIAL - TIPO A ENTERAL"
    )
    categoria_dieta_b = baker.make("CategoriaMedicao", nome="DIETA ESPECIAL - TIPO B")
    tipos_turmas = ["INFANTIL", "FUNDAMENTAL"]

    for dia in range(1, 15):
        baker.make(
            "DiaCalendario",
            escola=escola_emebs,
            data=f"2023-12-{dia:02d}",
            dia_letivo=True,
        )

    for dia in ["01", "02", "03", "04", "05"]:
        for tipo_turma in tipos_turmas:
            for campo in ["lanche", "refeicao", "sobremesa", "observacoes"]:
                for categoria in [
                    categoria_medicao,
                    categoria_dieta_a,
                    categoria_dieta_b,
                ]:
                    for medicao_ in [medicao_manha, medicao_tarde]:
                        baker.make(
                            "ValorMedicao",
                            dia=dia,
                            nome_campo=campo,
                            medicao=medicao_,
                            categoria_medicao=categoria,
                            valor=(
                                "10"
                                if campo != "observacoes"
                                else f"observação {tipo_turma} dia {dia}"
                            ),
                            infantil_ou_fundamental=tipo_turma,
                        )
    return solicitacao_medicao


@pytest.fixture
def solicitacao_medicao_inicial_varios_valores_ceu_gestao(
    escola_ceu_gestao,
    categoria_medicao,
    tipo_alimentacao_refeicao,
    tipo_alimentacao_lanche,
):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = baker.make("PeriodoEscolar", nome="TARDE")
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=12,
        ano=2023,
        escola=escola_ceu_gestao,
        uuid="416a47af-6022-4866-989f-9707b2213bfc",
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_manha = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
    )
    categoria_dieta_a = baker.make("CategoriaMedicao", nome="DIETA ESPECIAL - TIPO A")
    categoria_dieta_b = baker.make("CategoriaMedicao", nome="DIETA ESPECIAL - TIPO B")
    for dia in ["05"]:
        for campo in [
            "numero_de_alunos",
            "frequencia",
            "lanche",
            "refeicao",
            "repeticao_refeicao",
            "sobremesa",
        ]:
            for categoria in [categoria_medicao, categoria_dieta_a, categoria_dieta_b]:
                for medicao_ in [medicao_manha]:
                    baker.make(
                        "ValorMedicao",
                        dia=dia,
                        nome_campo=campo,
                        medicao=medicao_,
                        categoria_medicao=categoria,
                        valor="10",
                    )
    grupo_inclusao_normal = baker.make(
        "GrupoInclusaoAlimentacaoNormal",
        status="CODAE_AUTORIZADO",
        rastro_escola=escola_ceu_gestao,
        escola=escola_ceu_gestao,
    )

    baker.make(
        "InclusaoAlimentacaoNormal",
        grupo_inclusao=grupo_inclusao_normal,
        data=datetime.date(2023, 12, 5),
    )

    qp_manha = baker.make(
        "QuantidadePorPeriodo",
        grupo_inclusao_normal=grupo_inclusao_normal,
        numero_alunos=15,
        periodo_escolar=periodo_manha,
    )
    qp_manha.tipos_alimentacao.add(tipo_alimentacao_refeicao, tipo_alimentacao_lanche)
    qp_manha.save()

    qp_tarde = baker.make(
        "QuantidadePorPeriodo",
        grupo_inclusao_normal=grupo_inclusao_normal,
        numero_alunos=10,
        periodo_escolar=periodo_tarde,
    )
    qp_tarde.tipos_alimentacao.add(tipo_alimentacao_lanche)
    qp_tarde.save()

    return solicitacao_medicao


@pytest.fixture
def solicitacao_medicao_inicial_varios_valores_escola_cei(
    escola_cei, categoria_medicao
):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_integral = baker.make("PeriodoEscolar", nome="INTEGRAL")
    periodo_parcial = baker.make("PeriodoEscolar", nome="PARCIAL")
    periodo_tarde = baker.make("PeriodoEscolar", nome="TARDE")
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial", mes=12, ano=2022, escola=escola_cei
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_integral = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_integral,
    )
    medicao_parcial = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_parcial,
    )
    medicao_tarde = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_tarde,
    )
    categoria_dieta_a = baker.make(
        "CategoriaMedicao", nome="DIETA ESPECIAL - TIPO A ENTERAL"
    )
    for dia in ["01", "02", "03", "04"]:
        for categoria in [categoria_medicao, categoria_dieta_a]:
            valores = ["5", "9", "13"]
            for index, medicao_ in enumerate(
                [medicao_integral, medicao_parcial, medicao_tarde]
            ):
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo="frequencia",
                    medicao=medicao_,
                    categoria_medicao=categoria,
                    valor=valores[index],
                )
    return solicitacao_medicao


def medicao_infantil_manha(solicitacao_medicao, categoria_medicao):
    periodo_infantil_manha = baker.make("PeriodoEscolar", nome="Infantil MANHA")
    medicao_infantil_manha = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_infantil_manha,
    )
    categoria_dieta_a = baker.make(
        "CategoriaMedicao", nome="DIETA ESPECIAL - TIPO A ENTERAL"
    )
    for dia in ["01", "02"]:
        for campo in ["lanche", "refeicao", "lanche_emergencial", "sobremesa"]:
            for categoria in [categoria_medicao, categoria_dieta_a]:
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo=campo,
                    medicao=medicao_infantil_manha,
                    categoria_medicao=categoria,
                    valor="10",
                )


@pytest.fixture
def solicitacao_medicao_inicial_varios_valores_escola_cemei(
    escola_cemei, categoria_medicao
):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_integral = baker.make("PeriodoEscolar", nome="INTEGRAL")
    periodo_parcial = baker.make("PeriodoEscolar", nome="PARCIAL")
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial", mes=12, ano=2022, escola=escola_cemei
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_integral = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_integral,
    )
    medicao_parcial = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_parcial,
    )
    categoria_dieta_a = baker.make(
        "CategoriaMedicao", nome="DIETA ESPECIAL - TIPO A ENTERAL"
    )
    for dia in ["01", "02", "03"]:
        for categoria in [categoria_medicao, categoria_dieta_a]:
            valores = ["10", "20"]
            for index, medicao_ in enumerate([medicao_integral, medicao_parcial]):
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo="frequencia",
                    medicao=medicao_,
                    categoria_medicao=categoria,
                    valor=valores[index],
                )
    medicao_infantil_manha(solicitacao_medicao, categoria_medicao)
    return solicitacao_medicao


@pytest.fixture
def solicitacao_medicao_inicial_com_valores_repeticao(escola, categoria_medicao):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = baker.make("PeriodoEscolar", nome="TARDE")
    periodo_integral = baker.make("PeriodoEscolar", nome="INTEGRAL")
    periodo_noite = baker.make("PeriodoEscolar", nome="NOITE")
    grupo_solicitacoes_alimentacao = baker.make(
        "GrupoMedicao", nome="Solicitações de Alimentação"
    )
    grupo_programas_e_projetos = baker.make("GrupoMedicao", nome="Programas e Projetos")
    grupo_etec = baker.make("GrupoMedicao", nome="ETEC")
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial", mes=4, ano=2023, escola=escola
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_manha = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
    )
    medicao_tarde = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_tarde,
    )
    medicao_integral = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_integral,
    )
    medicao_noite = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_noite,
    )
    medicao_solicitacoes_alimentacao = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        grupo=grupo_solicitacoes_alimentacao,
    )
    medicao_programas_e_projetos = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        grupo=grupo_programas_e_projetos,
    )
    medicao_etec = baker.make(
        "Medicao", solicitacao_medicao_inicial=solicitacao_medicao, grupo=grupo_etec
    )
    for dia in ["10", "11"]:
        campos = [
            "lanche",
            "refeicao",
            "lanche_emergencial",
            "sobremesa",
            "repeticao_refeicao",
            "kit_lanche",
            "repeticao_sobremesa",
        ]
        for campo in campos:
            for medicao_ in [
                medicao_manha,
                medicao_tarde,
                medicao_integral,
                medicao_noite,
                medicao_solicitacoes_alimentacao,
                medicao_programas_e_projetos,
                medicao_etec,
            ]:
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo=campo,
                    medicao=medicao_,
                    categoria_medicao=categoria_medicao,
                    valor="25",
                )
    return solicitacao_medicao


@pytest.fixture
def solicitacao_medicao_inicial_dietas(
    escola, categoria_medicao_dieta_a, categoria_medicao_dieta_b
):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = baker.make("PeriodoEscolar", nome="TARDE")
    periodo_integral = baker.make("PeriodoEscolar", nome="INTEGRAL")
    periodo_noite = baker.make("PeriodoEscolar", nome="NOITE")
    grupo_programas_e_projetos = baker.make("GrupoMedicao", nome="Programas e Projetos")
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial", mes=4, ano=2023, escola=escola
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_manha = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
    )
    medicao_tarde = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_tarde,
    )
    medicao_integral = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_integral,
    )
    medicao_noite = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_noite,
    )
    medicao_programas_e_projetos = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        grupo=grupo_programas_e_projetos,
    )
    for categoria in [categoria_medicao_dieta_a, categoria_medicao_dieta_b]:
        campos = [
            "lanche",
            "lanche_4h",
        ]
        if "TIPO A" in categoria.nome:
            campos.append("refeicao")
        for dia in ["10", "11"]:
            for campo in campos:
                for medicao_ in [
                    medicao_tarde,
                    medicao_integral,
                    medicao_noite,
                    medicao_programas_e_projetos,
                ]:
                    baker.make(
                        "ValorMedicao",
                        dia=dia,
                        nome_campo=campo,
                        medicao=medicao_,
                        categoria_medicao=categoria,
                        valor="10",
                    )
        baker.make(
            "ValorMedicao",
            dia="10",
            nome_campo="lanche",
            medicao=medicao_manha,
            categoria_medicao=categoria_medicao_dieta_a,
            valor="0",
        )
    return solicitacao_medicao


@pytest.fixture
def medicao_solicitacoes_alimentacao(escola):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    categoria = baker.make("CategoriaMedicao", nome="SOLICITAÇÕES DE ALIMENTAÇÃO")
    grupo = baker.make("GrupoMedicao", nome="Solicitações de Alimentação")
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial", mes=6, ano=2023, escola=escola
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_solicitacoes_alimentacao = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=None,
        grupo=grupo,
    )
    for dia in ["01", "02", "03", "04", "05"]:
        for campo in [
            "lanche",
            "refeicao",
            "lanche_emergencial",
            "sobremesa",
            "kit_lanche",
        ]:
            baker.make(
                "ValorMedicao",
                dia=dia,
                nome_campo=campo,
                medicao=medicao_solicitacoes_alimentacao,
                categoria_medicao=categoria,
                valor="10",
            )
    return medicao_solicitacoes_alimentacao


@pytest.fixture
def medicao_solicitacoes_alimentacao_cei(escola):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    categoria = baker.make("CategoriaMedicao", nome="ALIMENTAÇÃO")
    periodo_escolar = baker.make("PeriodoEscolar", nome="INTEGRAL")
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial", mes=11, ano=2023, escola=escola
    )
    faixa_etaria = baker.make("FaixaEtaria", inicio=1, fim=3)
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_solicitacoes_alimentacao = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_escolar,
        grupo=None,
    )
    for dia in ["01", "02", "03", "04", "05"]:
        baker.make(
            "ValorMedicao",
            dia=dia,
            nome_campo="frequencia",
            medicao=medicao_solicitacoes_alimentacao,
            categoria_medicao=categoria,
            valor="10",
            faixa_etaria=faixa_etaria,
        )
    return medicao_solicitacoes_alimentacao


@pytest.fixture
def periodo_escolar_manha():
    return baker.make("PeriodoEscolar", nome="MANHA")


@pytest.fixture
def periodo_escolar_tarde():
    return baker.make("PeriodoEscolar", nome="TARDE")


@pytest.fixture
def periodo_escolar_noite():
    return baker.make("PeriodoEscolar", nome="NOITE")


@pytest.fixture
def periodo_escolar_integral():
    return baker.make("PeriodoEscolar", nome="INTEGRAL")


@pytest.fixture
def periodo_escolar_parcial():
    return baker.make("PeriodoEscolar", nome="PARCIAL")


@pytest.fixture
def categoria_alimentacoes():
    return baker.make("Cate")


@pytest.fixture
def escola_com_logs_para_medicao(
    periodo_escolar_manha,
    periodo_escolar_tarde,
    periodo_escolar_noite,
    escola,
    classificacao_dieta_tipo_a,
    classificacao_dieta_tipo_a_enteral,
    tipo_alimentacao_refeicao,
    tipo_alimentacao_lanche,
    grupo_programas_e_projetos,
    motivo_inclusao_continua_programas_projetos,
    motivo_inclusao_continua_etec,
    kit_lanche_1,
    kit_lanche_2,
):
    grupo_inclusao_normal = baker.make(
        "GrupoInclusaoAlimentacaoNormal",
        status="CODAE_AUTORIZADO",
        rastro_escola=escola,
        escola=escola,
    )

    baker.make(
        "InclusaoAlimentacaoNormal",
        grupo_inclusao=grupo_inclusao_normal,
        data=datetime.date(2023, 9, 3),
    )

    qp = baker.make(
        "QuantidadePorPeriodo",
        grupo_inclusao_normal=grupo_inclusao_normal,
        numero_alunos=100,
        periodo_escolar=periodo_escolar_manha,
    )
    qp.tipos_alimentacao.add(tipo_alimentacao_refeicao)
    qp.save()

    inclusao_continua_programas_projetos = baker.make(
        "InclusaoAlimentacaoContinua",
        escola=escola,
        rastro_escola=escola,
        data_inicial=datetime.date(2023, 9, 1),
        data_final=datetime.date(2023, 9, 30),
        motivo=motivo_inclusao_continua_programas_projetos,
        status="CODAE_AUTORIZADO",
    )

    inclusao_continua_etec = baker.make(
        "InclusaoAlimentacaoContinua",
        escola=escola,
        rastro_escola=escola,
        data_inicial=datetime.date(2023, 8, 15),
        data_final=datetime.date(2023, 9, 15),
        motivo=motivo_inclusao_continua_etec,
        status="CODAE_AUTORIZADO",
    )

    solicitacao_kit_lanche = baker.make(
        "SolicitacaoKitLanche",
        data=datetime.date(2023, 9, 12),
        tempo_passeio=TempoPasseio.OITO_OU_MAIS,
    )
    solicitacao_kit_lanche.kits.add(kit_lanche_1)
    solicitacao_kit_lanche.kits.add(kit_lanche_2)
    solicitacao_kit_lanche.save()

    baker.make(
        "SolicitacaoKitLancheAvulsa",
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        status="CODAE_AUTORIZADO",
        escola=escola,
        quantidade_alunos=100,
    )

    solicitacao_unificada = baker.make(
        "SolicitacaoKitLancheUnificada",
        status="CODAE_AUTORIZADO",
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        diretoria_regional=escola.lote.diretoria_regional,
        lista_kit_lanche_igual=False,
    )
    eq = baker.make(
        "EscolaQuantidade",
        solicitacao_unificada=solicitacao_unificada,
        escola=escola,
        quantidade_alunos=100,
    )
    eq.kits.add(kit_lanche_1)
    eq.kits.add(kit_lanche_2)
    eq.save()

    for periodo in [
        periodo_escolar_manha,
        periodo_escolar_tarde,
        periodo_escolar_noite,
    ]:
        qp = baker.make(
            "QuantidadePorPeriodo",
            inclusao_alimentacao_continua=inclusao_continua_programas_projetos,
            periodo_escolar=periodo,
            numero_alunos=10,
            dias_semana=[0, 1, 2, 3, 4, 5, 6],
        )
        qp.tipos_alimentacao.add(tipo_alimentacao_refeicao)
        qp.tipos_alimentacao.add(tipo_alimentacao_lanche)
        qp.save()

        qp = baker.make(
            "QuantidadePorPeriodo",
            inclusao_alimentacao_continua=inclusao_continua_etec,
            periodo_escolar=periodo,
            numero_alunos=10,
            dias_semana=[0, 1, 2, 3, 4, 5, 6],
        )
        qp.tipos_alimentacao.add(tipo_alimentacao_refeicao)
        qp.tipos_alimentacao.add(tipo_alimentacao_lanche)
        qp.save()

        baker.make(
            "AlunosMatriculadosPeriodoEscola",
            escola=escola,
            periodo_escolar=periodo,
            quantidade_alunos=100,
        )

        vinculo_alimentacao = baker.make(
            "VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
            tipo_unidade_escolar=escola.tipo_unidade,
            periodo_escolar=periodo,
        )
        vinculo_alimentacao.tipos_alimentacao.add(tipo_alimentacao_refeicao)
        vinculo_alimentacao.tipos_alimentacao.add(tipo_alimentacao_lanche)
        vinculo_alimentacao.save()

        baker.make("Aluno", escola=escola, periodo_escolar=periodo)

        for dia in range(1, 31):
            data = datetime.date(2023, 9, dia)
            log = baker.make(
                "LogAlunosMatriculadosPeriodoEscola",
                escola=escola,
                periodo_escolar=periodo,
                quantidade_alunos=100,
            )
            log.criado_em = data
            log.save()

            if periodo == periodo_escolar_manha:
                for classificacao in [
                    classificacao_dieta_tipo_a,
                    classificacao_dieta_tipo_a_enteral,
                ]:
                    baker.make(
                        "LogQuantidadeDietasAutorizadas",
                        data=datetime.date(2023, 9, dia),
                        escola=escola,
                        periodo_escolar=periodo,
                        classificacao=classificacao,
                        quantidade=10,
                    )
    return escola


@pytest.fixture
def solicitacao_medicao_inicial_teste_salvar_logs(
    escola_com_logs_para_medicao,
    tipo_contagem_alimentacao,
    periodo_escolar_manha,
    periodo_escolar_tarde,
    periodo_escolar_noite,
    categoria_medicao,
    categoria_medicao_dieta_a,
    grupo_programas_e_projetos,
    categoria_medicao_dieta_a_enteral_aminoacidos,
    grupo_etec,
    grupo_solicitacoes_alimentacao,
    categoria_medicao_solicitacoes_alimentacao,
):
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial",
        uuid="bed4d779-2d57-4c5f-bf9c-9b93ddac54d9",
        mes="09",
        ano=2023,
        escola=escola_com_logs_para_medicao,
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem_alimentacao])

    baker.make(
        "LogAlunosMatriculadosPeriodoEscola",
        escola=escola_com_logs_para_medicao,
        criado_em=datetime.date(2023, 9, 1),
        periodo_escolar=periodo_escolar_manha,
        quantidade_alunos=10,
    )

    baker.make(
        "LogAlunosMatriculadosPeriodoEscola",
        escola=escola_com_logs_para_medicao,
        criado_em=datetime.date(2023, 9, 1),
        periodo_escolar=periodo_escolar_tarde,
        quantidade_alunos=10,
    )

    baker.make(
        "LogAlunosMatriculadosPeriodoEscola",
        escola=escola_com_logs_para_medicao,
        criado_em=datetime.date(2023, 9, 1),
        periodo_escolar=periodo_escolar_noite,
        quantidade_alunos=10,
    )

    medicao_manha = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_escolar_manha,
    )
    baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_escolar_tarde,
    )
    baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_escolar_noite,
    )
    medicao_programas_projetos = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        grupo=grupo_programas_e_projetos,
    )
    medicao_etec = baker.make(
        "Medicao", solicitacao_medicao_inicial=solicitacao_medicao, grupo=grupo_etec
    )
    baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        grupo=grupo_solicitacoes_alimentacao,
    )
    for dia in range(1, 31):
        baker.make(
            "DiaCalendario",
            escola=escola_com_logs_para_medicao,
            data=f"2023-09-{dia:02d}",
            dia_letivo=False,
        )

    for medicao_ in [medicao_manha, medicao_programas_projetos, medicao_etec]:
        for dia in range(1, 31):
            for nome_campo in [
                "numero_de_alunos",
                "frequencia",
                "lanche",
                "lanche_4h",
                "refeicao",
                "repeticao_refeicao",
                "sobremesa",
                "repeticao_sobremesa",
            ]:
                baker.make(
                    "ValorMedicao",
                    medicao=medicao_,
                    nome_campo=nome_campo,
                    dia=f"{dia:02d}",
                    categoria_medicao=categoria_medicao,
                    valor="10",
                )
    for nome_campo in [
        "frequencia",
        "lanche",
        "lanche_4h",
        "refeicao",
    ]:
        for categoria_medicao in [
            categoria_medicao_dieta_a,
            categoria_medicao_dieta_a_enteral_aminoacidos,
        ]:
            baker.make(
                "ValorMedicao",
                nome_campo=nome_campo,
                medicao=medicao_manha,
                dia="03",
                categoria_medicao=categoria_medicao,
                valor="10",
            )

    return solicitacao_medicao


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
def solicitacao_medicao_inicial_teste_salvar_logs_cei(
    escola_cei,
    tipo_contagem_alimentacao,
    faixas_etarias_ativas,
    classificacao_dieta_tipo_a,
    classificacao_dieta_tipo_a_enteral,
    categoria_medicao,
    categoria_medicao_dieta_a,
    categoria_medicao_dieta_a_enteral_aminoacidos,
):
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial",
        uuid="7f7c79ec-bb92-11ee-ad73-5f84fbd2a2f0",
        mes="10",
        ano=2023,
        escola=escola_cei,
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem_alimentacao])
    solicitacao_medicao.ue_possui_alunos_periodo_parcial = True
    solicitacao_medicao.save()

    periodo_integral = baker.make("PeriodoEscolar", nome="INTEGRAL")
    periodo_parcial = baker.make("PeriodoEscolar", nome="PARCIAL")
    periodo_tarde = baker.make("PeriodoEscolar", nome="TARDE")

    baker.make("Aluno", serie="1", escola=escola_cei, periodo_escolar=periodo_integral)
    baker.make("Aluno", serie="2", escola=escola_cei, periodo_escolar=periodo_tarde)

    for periodo in [periodo_integral, periodo_parcial, periodo_tarde]:
        for dia in range(1, 32):
            log = baker.make(
                "LogAlunosMatriculadosFaixaEtariaDia",
                escola=escola_cei,
                periodo_escolar=periodo,
                faixa_etaria=faixas_etarias_ativas[2],
                quantidade=10,
                data=datetime.date(2023, 10, dia),
            )

            for classificacao in [
                classificacao_dieta_tipo_a,
                classificacao_dieta_tipo_a_enteral,
            ]:
                baker.make(
                    "LogQuantidadeDietasAutorizadasCEI",
                    escola=escola_cei,
                    periodo_escolar=periodo,
                    faixa_etaria=faixas_etarias_ativas[2],
                    quantidade=2,
                    data=datetime.date(2023, 10, dia),
                    classificacao=classificacao,
                )
                baker.make(
                    "LogQuantidadeDietasAutorizadasCEI",
                    escola=escola_cei,
                    periodo_escolar=periodo,
                    faixa_etaria=faixas_etarias_ativas[4],
                    quantidade=2,
                    data=datetime.date(2023, 10, dia),
                    classificacao=classificacao,
                )
    return solicitacao_medicao


@pytest.fixture
def solicitacao_medicao_inicial_com_grupo(escola, categoria_medicao_dieta_a):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    grupo = baker.make("GrupoMedicao", nome="Programas e Projetos")
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial",
        uuid="bed4d779-2d57-4c5f-bf9c-9b93ddac54d9",
        mes=12,
        ano=2022,
        escola=escola,
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
        grupo=grupo,
    )
    baker.make(
        "ValorMedicao",
        categoria_medicao=categoria_medicao_dieta_a,
        medicao=medicao,
        nome_campo="frequencia",
        valor="10",
    )
    return solicitacao_medicao


@pytest.fixture
def solicitacoes_medicao_inicial(escola):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    escola_2 = baker.make("Escola")
    s1 = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=6,
        ano=2022,
        escola=escola,
        status="MEDICAO_ENVIADA_PELA_UE",
    )
    s1.tipos_contagem_alimentacao.set([tipo_contagem])

    s2 = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=1,
        ano=2023,
        escola=escola,
        status="MEDICAO_ENVIADA_PELA_UE",
    )
    s2.tipos_contagem_alimentacao.set([tipo_contagem])

    s3 = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=2,
        ano=2023,
        escola=escola,
        status="MEDICAO_CORRECAO_SOLICITADA",
    )
    s3.tipos_contagem_alimentacao.set([tipo_contagem])

    s4 = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=2,
        ano=2023,
        escola=escola_2,
        status="MEDICAO_CORRECAO_SOLICITADA",
    )
    s4.tipos_contagem_alimentacao.set([tipo_contagem])

    s5 = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=3,
        ano=2023,
        escola=escola,
        status="MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE",
    )
    s5.tipos_contagem_alimentacao.set([tipo_contagem])

    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=s1.uuid,
        status_evento=55,  # MEDICAO_ENVIADA_PELA_UE
        solicitacao_tipo=16,
    )  # MEDICAO_INICIAL
    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=s2.uuid,
        status_evento=55,  # MEDICAO_ENVIADA_PELA_UE
        solicitacao_tipo=16,
    )  # MEDICAO_INICIAL
    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=s3.uuid,
        status_evento=64,  # MEDICAO_CORRECAO_SOLICITADA
        solicitacao_tipo=16,
    )  # MEDICAO_INICIAL
    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=s4.uuid,
        status_evento=64,  # MEDICAO_CORRECAO_SOLICITADA
        solicitacao_tipo=16,
    )  # MEDICAO_INICIAL
    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=s5.uuid,
        status_evento=54,  # MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        solicitacao_tipo=16,
    )  # MEDICAO_INICIAL


@pytest.fixture
def solicitacoes_medicao_inicial_codae(escola):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    s1 = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=4,
        ano=2022,
        escola=escola,
        status="MEDICAO_APROVADA_PELA_DRE",
    )
    s1.tipos_contagem_alimentacao.set([tipo_contagem])

    s2 = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=7,
        ano=2023,
        escola=escola,
        status="MEDICAO_APROVADA_PELA_DRE",
    )
    s2.tipos_contagem_alimentacao.set([tipo_contagem])

    s3 = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=2,
        ano=2023,
        escola=escola,
        status="MEDICAO_CORRECAO_SOLICITADA_CODAE",
    )
    s3.tipos_contagem_alimentacao.set([tipo_contagem])

    s4 = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=12,
        ano=2023,
        escola=escola,
        status="MEDICAO_CORRIGIDA_PARA_CODAE",
    )
    s4.tipos_contagem_alimentacao.set([tipo_contagem])

    s5 = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=3,
        ano=2023,
        escola=escola,
        status="MEDICAO_APROVADA_PELA_CODAE",
    )
    s5.tipos_contagem_alimentacao.set([tipo_contagem])

    s6 = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=2,
        ano=2024,
        escola=escola,
        status="MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE",
    )
    s6.tipos_contagem_alimentacao.set([tipo_contagem])

    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=s1.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_DRE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
    )
    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=s2.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_DRE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
    )
    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=s3.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA_CODAE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
    )
    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=s4.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_CORRIGIDA_PARA_CODAE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
    )
    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=s5.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
    )
    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=s6.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
    )


@pytest.fixture
def solicitacao_medicao_inicial_sem_arquivo(escola):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas COloridas")
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial",
        uuid="fb6d1870-a397-4e87-8218-13d316a0ffea",
        mes=6,
        ano=2022,
        escola=escola,
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    return solicitacao_medicao


@pytest.fixture
def parametrizacao_financeira_emef(
    edital,
    escola,
    tipo_unidade_escolar,
    tipo_unidade_escolar_ceu_emef,
    tipo_unidade_escolar_emefm,
    tipo_unidade_escolar_cieja,
    tipo_unidade_escolar_ceu_gestao,
    tipo_alimentacao_refeicao,
    tipo_alimentacao_almoco,
    tipo_alimentacao_lanche,
    tipo_alimentacao_lanche_4h,
    tipo_alimentacao_lanche_emergencial,
    tipo_alimentacao_sobremesa,
):
    parametrizacao_financeira = baker.make(
        "ParametrizacaoFinanceira",
        edital=edital,
        lote=escola.lote,
        tipos_unidades=[
            tipo_unidade_escolar,
            tipo_unidade_escolar_ceu_emef,
            tipo_unidade_escolar_emefm,
            tipo_unidade_escolar_cieja,
            tipo_unidade_escolar_ceu_gestao,
        ],
        legenda="Parametrização Financeira: Legenda Inicial",
    )

    parametrizacao_financeira_tabela = baker.make(
        "ParametrizacaoFinanceiraTabela",
        parametrizacao_financeira=parametrizacao_financeira,
        nome="Preço das Alimentações",
    )
    baker.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela,
        tipo_alimentacao=tipo_alimentacao_refeicao,
        grupo="EMEF / CEUEMEF / EMEFM",
        valor_colunas={
            "valor_unitario": 2,
            "valor_unitario_reajuste": 3,
        },
    )
    baker.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela,
        tipo_alimentacao=tipo_alimentacao_refeicao,
        grupo="CIEJA / EJA",
        valor_colunas={
            "valor_unitario": 8,
            "valor_unitario_reajuste": 5,
        },
    )
    baker.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela,
        tipo_alimentacao=tipo_alimentacao_almoco,
        valor_colunas={
            "valor_unitario": 5,
            "valor_unitario_reajuste": 2,
        },
    )
    baker.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela,
        tipo_alimentacao=tipo_alimentacao_lanche,
        valor_colunas={
            "valor_unitario": 7,
            "valor_unitario_reajuste": 5,
        },
    )
    baker.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela,
        tipo_alimentacao=tipo_alimentacao_lanche_4h,
        valor_colunas={
            "valor_unitario": 4,
            "valor_unitario_reajuste": 2,
        },
    )
    baker.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela,
        tipo_alimentacao=tipo_alimentacao_sobremesa,
        valor_colunas={
            "valor_unitario": 8,
            "valor_unitario_reajuste": 6,
        },
    )
    baker.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela,
        tipo_alimentacao=tipo_alimentacao_lanche_emergencial,
        valor_colunas={
            "valor_unitario": 12,
            "valor_unitario_reajuste": 10,
        },
    )

    parametrizacao_financeira_tabela_dietas_a = baker.make(
        "ParametrizacaoFinanceiraTabela",
        parametrizacao_financeira=parametrizacao_financeira,
        nome="Dietas Tipo A e Tipo A Enteral",
    )
    baker.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela_dietas_a,
        grupo="Dieta Enteral",
        tipo_alimentacao=tipo_alimentacao_refeicao,
        valor_colunas={
            "percentual_acrescimo": 3,
            "valor_unitario": 7,
            "valor_unitario_total": 7.21,
        },
    )
    baker.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela_dietas_a,
        grupo="Dieta Enteral",
        tipo_alimentacao=tipo_alimentacao_lanche,
        valor_colunas={
            "percentual_acrescimo": 6,
            "valor_unitario": 8,
            "valor_unitario_total": 8.48,
        },
    )
    baker.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela_dietas_a,
        grupo="Dieta Enteral",
        tipo_alimentacao=tipo_alimentacao_lanche_4h,
        valor_colunas={
            "percentual_acrescimo": 6,
            "valor_unitario": 7,
            "valor_unitario_total": 7.42,
        },
    )

    parametrizacao_financeira_tabela_dietas_b = baker.make(
        "ParametrizacaoFinanceiraTabela",
        parametrizacao_financeira=parametrizacao_financeira,
        nome="Dietas Tipo B",
    )
    baker.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela_dietas_b,
        grupo="Dieta Enteral",
        tipo_alimentacao=tipo_alimentacao_lanche,
        valor_colunas={
            "percentual_acrescimo": 6,
            "valor_unitario": 7,
            "valor_unitario_total": 7.42,
        },
    )
    baker.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela_dietas_b,
        grupo="Dieta Enteral",
        tipo_alimentacao=tipo_alimentacao_lanche_4h,
        valor_colunas={
            "percentual_acrescimo": 6,
            "valor_unitario": 7,
            "valor_unitario_total": 7.42,
        },
    )
    return parametrizacao_financeira


@pytest.fixture
def anexo_ocorrencia_medicao_inicial(solicitacao_medicao_inicial):
    nome = "arquivo_teste.pdf"
    arquivo = SimpleUploadedFile(
        "arquivo_teste.pdf", bytes("CONTENT", encoding="utf-8")
    )
    return baker.make(
        "OcorrenciaMedicaoInicial",
        uuid="1ace193a-6c2c-4686-b9ed-60a922ad0e1a",
        nome_ultimo_arquivo=nome,
        ultimo_arquivo=arquivo,
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
        status="MEDICAO_ENVIADA_PELA_UE",
    )


@pytest.fixture
def solicitacao_com_anexo_e_medicoes_aprovadas(solicitacao_medicao_inicial):
    nome = "arquivo_teste.pdf"
    arquivo = SimpleUploadedFile(
        "arquivo_teste.pdf", bytes("CONTENT", encoding="utf-8")
    )
    baker.make(
        "OcorrenciaMedicaoInicial",
        uuid="1ace193a-6c2c-4686-b9ed-60a922ad0e1a",
        nome_ultimo_arquivo=nome,
        ultimo_arquivo=arquivo,
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
        status="MEDICAO_APROVADA_PELA_CODAE",
    )
    medicao = solicitacao_medicao_inicial.medicoes.get()
    medicao.status = "MEDICAO_APROVADA_PELA_CODAE"
    medicao.save()
    usuario_escola = baker.make(
        "Usuario", nome="TESTE DA SILVA", cargo="DIRETOR DE ESCOLA"
    )
    perfil_diretor = baker.make("Perfil", nome="DIRETOR_UE", ativo=True)
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=usuario_escola,
        instituicao=solicitacao_medicao_inicial.escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    usuario_dre = baker.make(
        "Usuario", nome="TESTE DA SILVA", cargo="DIRETOR DE ESCOLA"
    )
    perfil_cogestor = baker.make("Perfil", nome="COGESTOR_DRE", ativo=True)
    baker.make(
        "Vinculo",
        usuario=usuario_dre,
        instituicao=solicitacao_medicao_inicial.escola.lote.diretoria_regional,
        perfil=perfil_cogestor,
        data_inicial=hoje,
        ativo=True,
    )
    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=solicitacao_medicao_inicial.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_ENVIADA_PELA_UE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
        usuario=usuario_escola,
    )
    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=solicitacao_medicao_inicial.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_DRE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
        usuario=usuario_dre,
    )
    return solicitacao_medicao_inicial


@pytest.fixture
def anexo_ocorrencia_medicao_inicial_status_aprovado_dre(solicitacao_medicao_inicial):
    nome = "arquivo_teste.pdf"
    arquivo = SimpleUploadedFile(
        "arquivo_teste.pdf", bytes("CONTENT", encoding="utf-8")
    )
    return baker.make(
        "OcorrenciaMedicaoInicial",
        uuid="04fb4c1c-0e31-4936-93a7-f2760b968c3b",
        nome_ultimo_arquivo=nome,
        ultimo_arquivo=arquivo,
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
        status="MEDICAO_APROVADA_PELA_DRE",
    )


@pytest.fixture
def anexo_ocorrencia_medicao_inicial_status_inicial(escola):
    nome = "arquivo_teste.pdf"
    arquivo = SimpleUploadedFile(
        "arquivo_teste.pdf", bytes("CONTENT", encoding="utf-8")
    )
    solicitacao_medicao = baker.make("SolicitacaoMedicaoInicial", escola=escola)
    return baker.make(
        "OcorrenciaMedicaoInicial",
        uuid="2bed204b-2c1c-4686-b5e3-60a922ad0e1a",
        nome_ultimo_arquivo=nome,
        ultimo_arquivo=arquivo,
        solicitacao_medicao_inicial=solicitacao_medicao,
        status="MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE",
    )


@pytest.fixture
def anexo_ocorrencia_medicao_inicial_status_aprovado_pela_dre():
    nome = "arquivo_teste.pdf"
    arquivo = SimpleUploadedFile(
        "arquivo_teste.pdf", bytes("CONTENT", encoding="utf-8")
    )
    solicitacao_medicao = baker.make("SolicitacaoMedicaoInicial")
    return baker.make(
        "OcorrenciaMedicaoInicial",
        uuid="2bed204b-2c1c-4686-b5e3-60a922ad0e1a",
        nome_ultimo_arquivo=nome,
        ultimo_arquivo=arquivo,
        solicitacao_medicao_inicial=solicitacao_medicao,
        status="MEDICAO_APROVADO_PELA_DRE",
    )


@pytest.fixture
def sol_med_inicial_devolvida_pela_dre_para_ue(escola):
    nome = "arquivo_teste.pdf"
    arquivo = SimpleUploadedFile(
        "arquivo_teste.pdf", bytes("CONTENT", encoding="utf-8")
    )
    solicitacao = baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola,
        status="MEDICAO_CORRECAO_SOLICITADA",
        uuid="d9de8653-4910-423e-9381-e391c2ae8ecb",
        com_ocorrencias=True,
    )
    baker.make(
        "OcorrenciaMedicaoInicial",
        uuid="ea7299a3-3eb6-4858-a7b4-387446c607a1",
        nome_ultimo_arquivo=nome,
        ultimo_arquivo=arquivo,
        solicitacao_medicao_inicial=solicitacao,
        status="MEDICAO_CORRECAO_SOLICITADA",
    )
    return solicitacao


@pytest.fixture
def sol_med_inicial_devolvida_pela_codae_para_ue(escola):
    nome = "arquivo_teste.pdf"
    arquivo = SimpleUploadedFile(
        "arquivo_teste.pdf", bytes("CONTENT", encoding="utf-8")
    )
    solicitacao = baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola,
        status="MEDICAO_CORRECAO_SOLICITADA_CODAE",
        uuid="d9de8653-4910-423e-9381-e391c2ae8ecb",
        com_ocorrencias=True,
    )
    baker.make(
        "OcorrenciaMedicaoInicial",
        uuid="ea7299a3-3eb6-4858-a7b4-387446c607a1",
        nome_ultimo_arquivo=nome,
        ultimo_arquivo=arquivo,
        solicitacao_medicao_inicial=solicitacao,
        status="MEDICAO_CORRECAO_SOLICITADA_CODAE",
    )
    return solicitacao


@pytest.fixture
def responsavel(solicitacao_medicao_inicial):
    nome = "tester"
    rf = "1234567"
    return baker.make(
        "medicao_inicial.Responsavel",
        nome=nome,
        rf=rf,
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
    )


@pytest.fixture
def tipo_contagem_alimentacao():
    return baker.make("TipoContagemAlimentacao", nome="Fichas")


@pytest.fixture
def periodo_escolar():
    return baker.make("PeriodoEscolar", nome="INTEGRAL")


@pytest.fixture
def medicao(solicitacao_medicao_inicial, periodo_escolar):
    return baker.make(
        "Medicao",
        periodo_escolar=periodo_escolar,
        uuid="5a3a3941-1b91-4b9f-b410-c3547e224eb5",
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
    )


@pytest.fixture
def medicao_status_inicial(
    solicitacao_medicao_inicial, periodo_escolar, categoria_medicao
):
    medicao = baker.make(
        "Medicao",
        periodo_escolar=periodo_escolar,
        uuid="7041e451-43a7-4d2f-abc6-d0960121d2fb",
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
        status="MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE",
    )
    valor = 10
    nome_campo = "observacoes"
    tipo_alimentacao = baker.make(
        "TipoAlimentacao", nome="Lanche", uuid="0367af8d-26bd-40b5-83d2-9e337622ba50"
    )
    baker.make(
        "ValorMedicao",
        valor=valor,
        nome_campo=nome_campo,
        medicao=medicao,
        uuid="128f36e2-ea93-4e05-9641-50b0c79ddb5e",
        dia=22,
        categoria_medicao=categoria_medicao,
        tipo_alimentacao=tipo_alimentacao,
    )
    return medicao


@pytest.fixture
def medicao_status_enviada_pela_ue(
    solicitacao_medicao_inicial, periodo_escolar, categoria_medicao
):
    medicao = baker.make(
        "Medicao",
        periodo_escolar=periodo_escolar,
        uuid="cbe62cc7-55e9-435d-8c3f-845b6fa20c2e",
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
        status="MEDICAO_ENVIADA_PELA_UE",
    )
    valor = 10
    nome_campo = "observacoes"
    tipo_alimentacao = baker.make(
        "TipoAlimentacao", nome="Lanche", uuid="837ed21a-d535-4df2-aa37-f186e4e51392"
    )
    baker.make(
        "ValorMedicao",
        valor=valor,
        nome_campo=nome_campo,
        medicao=medicao,
        uuid="932d0e67-e434-4071-99dc-b1c4bcdd9310",
        dia=22,
        categoria_medicao=categoria_medicao,
        tipo_alimentacao=tipo_alimentacao,
    )
    return medicao


@pytest.fixture
def medicao_aprovada_pela_dre(
    solicitacao_medicao_inicial, periodo_escolar, categoria_medicao
):
    medicao = baker.make(
        "Medicao",
        periodo_escolar=periodo_escolar,
        uuid="65f112a5-8b4b-495b-a29e-1d75fb0b5eeb",
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
        status="MEDICAO_APROVADA_PELA_DRE",
    )
    valor = 20
    nome_campo = "observacoes"
    tipo_alimentacao = baker.make(
        "TipoAlimentacao", nome="Lanche", uuid="a5ea11b6-a043-47cd-ba69-d6b207312cbd"
    )
    baker.make(
        "ValorMedicao",
        valor=valor,
        nome_campo=nome_campo,
        medicao=medicao,
        uuid="0b599490-477f-487b-a49e-c8e7cfdcd00b",
        dia=25,
        categoria_medicao=categoria_medicao,
        tipo_alimentacao=tipo_alimentacao,
    )
    return medicao


@pytest.fixture
def categoria_medicao():
    return baker.make(
        "CategoriaMedicao", nome="ALIMENTAÇÃO", id=random.randint(1, 1000000)
    )


@pytest.fixture
def categoria_medicao_dieta_a():
    return baker.make("CategoriaMedicao", nome="DIETA ESPECIAL - TIPO A")


@pytest.fixture
def categoria_medicao_dieta_a_enteral_aminoacidos():
    return baker.make(
        "CategoriaMedicao",
        nome="DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS",
    )


@pytest.fixture
def categoria_medicao_dieta_b():
    return baker.make("CategoriaMedicao", nome="DIETA ESPECIAL - TIPO B")


@pytest.fixture
def categoria_medicao_solicitacoes_alimentacao():
    return baker.make("CategoriaMedicao", nome="SOLICITAÇÕES DE ALIMENTAÇÃO")


@pytest.fixture
def valor_medicao(medicao, categoria_medicao):
    valor = 13
    nome_campo = "observacoes"
    tipo_alimentacao = baker.make(
        "TipoAlimentacao", nome="Lanche", uuid="b58b7946-67c4-416c-82cf-f26a470fb93e"
    )
    return baker.make(
        "ValorMedicao",
        valor=valor,
        nome_campo=nome_campo,
        medicao=medicao,
        uuid="fc2fbc0a-8dda-4c8e-b5cf-c40ecff52a5c",
        dia=13,
        categoria_medicao=categoria_medicao,
        tipo_alimentacao=tipo_alimentacao,
    )


@pytest.fixture
def client_autenticado_diretoria_regional(client, django_user_model, escola):
    email = "test@test.com"
    password = "admin@123"
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_cogestor = baker.make("Perfil", nome="COGESTOR_DRE", ativo=True)
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=escola.diretoria_regional,
        perfil=perfil_cogestor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_da_escola(client, django_user_model, escola):
    email = "user@escola.com"
    password = "admin@123"
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
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_da_escola_cei(client, django_user_model, escola_cei):
    email = "user@escola_cei.com"
    password = "admin@123"
    perfil_diretor = baker.make("Perfil", nome="DIRETOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="123456"
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=escola_cei,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_da_escola_cemei(client, django_user_model, escola_cemei):
    email = "user@escola_cemei.com"
    password = "admin@123"
    perfil_diretor = baker.make("Perfil", nome="DIRETOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="123456"
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=escola_cemei,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_da_escola_ceu_gestao(
    client, django_user_model, escola_ceu_gestao
):
    email = "user@escola_ceu_gestao.com"
    password = "admin@123"
    perfil_diretor = baker.make("Perfil", nome="DIRETOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="123456"
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=escola_ceu_gestao,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_da_escola_emebs(client, django_user_model, escola_emebs):
    email = "user@escola_emebs.com"
    password = "admin@123"
    perfil_diretor = baker.make("Perfil", nome="DIRETOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="123456"
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=escola_emebs,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_adm_da_escola(client, django_user_model, escola):
    email = "user@escola_adm.com"
    password = "admin@1234"
    perfil_diretor = baker.make("Perfil", nome="ADMINISTRADOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="1234567"
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
    client.login(username=email, password=password)
    return client


@pytest.fixture
def user_administrador_medicao(django_user_model):
    email = "codae@medicao.com"
    password = "admin@1234"
    perfil_medicao = baker.make("Perfil", nome="ADMINISTRADOR_MEDICAO", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="1234588"
    )
    codae = baker.make("Codae")
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=codae,
        perfil=perfil_medicao,
        data_inicial=hoje,
        ativo=True,
    )
    return usuario, password


@pytest.fixture
def client_autenticado_codae_medicao(client, user_administrador_medicao):
    usuario, password = user_administrador_medicao
    client.login(username=usuario.email, password=password)
    return client


@pytest.fixture
def dia_para_corrigir(categoria_medicao, medicao):
    return baker.make(
        "DiaParaCorrigir",
        uuid="d5c33bdc-6c3e-4e70-a7f4-60603362f386",
        medicao=medicao,
        categoria_medicao=categoria_medicao,
        dia="01",
    )


@pytest.fixture
def alimentacoes_lancamentos_especiais():
    for alimentacao in [
        {"nome": "2ª Refeição 1ª oferta", "posicao": 1},
        {"nome": "Repetição 2ª Refeição", "posicao": 2},
        {"nome": "2ª Sobremesa 1ª oferta", "posicao": 3},
        {"nome": "Repetição 2ª Sobremesa", "posicao": 4},
        {"nome": "2º Lanche 4h", "posicao": 5},
        {"nome": "2º Lanche 5h", "posicao": 6},
        {"nome": "Lanche Extra", "posicao": 7},
    ]:
        if not AlimentacaoLancamentoEspecial.objects.filter(
            nome=alimentacao["nome"], posicao=alimentacao["posicao"]
        ).exists():
            AlimentacaoLancamentoEspecial.objects.create(
                nome=alimentacao["nome"], posicao=alimentacao["posicao"]
            )
    return AlimentacaoLancamentoEspecial.objects.all()


@pytest.fixture
def permissoes_lancamento_especial(
    escola, escola_emei, alimentacoes_lancamentos_especiais
):
    usuario = baker.make("Usuario", email="admin2@admin.com", is_superuser=True)
    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = baker.make("PeriodoEscolar", nome="TARDE")
    alimentacoes = alimentacoes_lancamentos_especiais
    baker.make(
        "PermissaoLancamentoEspecial",
        alimentacoes_lancamento_especial=[
            alimentacoes[0],
            alimentacoes[2],
            alimentacoes[5],
            alimentacoes[6],
        ],
        criado_por=usuario,
        data_inicial="2023-08-13",
        data_final="2023-08-15",
        escola=escola,
        diretoria_regional=escola.diretoria_regional,
        periodo_escolar=periodo_manha,
    )
    baker.make(
        "PermissaoLancamentoEspecial",
        alimentacoes_lancamento_especial=[
            alimentacoes[1],
            alimentacoes[3],
            alimentacoes[5],
        ],
        criado_por=usuario,
        data_inicial="2023-08-02",
        data_final="2023-08-09",
        escola=escola,
        diretoria_regional=escola.diretoria_regional,
        periodo_escolar=periodo_tarde,
    )
    baker.make(
        "PermissaoLancamentoEspecial",
        alimentacoes_lancamento_especial=[
            alimentacoes[1],
            alimentacoes[3],
            alimentacoes[4],
            alimentacoes[5],
            alimentacoes[6],
        ],
        criado_por=usuario,
        data_inicial="2023-08-10",
        data_final="2023-08-12",
        escola=escola_emei,
        diretoria_regional=escola.diretoria_regional,
        periodo_escolar=periodo_manha,
    )
    return PermissaoLancamentoEspecial.objects.all()


@pytest.fixture
def logs_alunos_matriculados_periodo_escola_cemei(escola_cemei):
    quantidades = [10, 20]
    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = baker.make("PeriodoEscolar", nome="TARDE")
    for quantidade in quantidades:
        baker.make(
            LogAlunosMatriculadosPeriodoEscola,
            escola=escola_cemei,
            periodo_escolar=periodo_manha,
            quantidade_alunos=quantidade,
            tipo_turma=TipoTurma.REGULAR.name,
        )
    baker.make(
        LogAlunosMatriculadosPeriodoEscola,
        escola=escola_cemei,
        periodo_escolar=periodo_tarde,
        quantidade_alunos=50,
        tipo_turma=TipoTurma.REGULAR.name,
    )
    return LogAlunosMatriculadosPeriodoEscola.objects.all()


@pytest.fixture
def grupo_escolar(
    tipo_unidade_escolar,
    tipo_unidade_escolar_ceu_emef,
    tipo_unidade_escolar_emefm,
    tipo_unidade_escolar_cieja,
    tipo_unidade_escolar_ceu_gestao,
):
    grupo_escolar = baker.make(
        "GrupoUnidadeEscolar",
        nome="Grupo 4",
        uuid="5bd9ad5c-e0ab-4812-b2b6-336fc8988960",
        tipos_unidades=[
            tipo_unidade_escolar,
            tipo_unidade_escolar_ceu_emef,
            tipo_unidade_escolar_emefm,
            tipo_unidade_escolar_cieja,
            tipo_unidade_escolar_ceu_gestao,
        ],
    )
    return grupo_escolar.uuid


@pytest.fixture
def diretoria_regional():
    diretoria_regional = baker.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL IPIRANGA",
        uuid="3972e0e9-2d8e-472a-9dfa-30cd219a6d9a",
    )
    return diretoria_regional


@pytest.fixture
def edital():
    edital = baker.make(
        "terceirizada.Edital",
        numero="Edital de Pregão nº 78/SME/2024",
        uuid="f76f367c-f9c4-463e-aefb-0ff434d93ae9",
    )
    return edital


@pytest.fixture
def contrato(edital):
    terceirizada = baker.make("terceirizada.Terceirizada")
    lote = baker.make("escola.Lote", terceirizada=terceirizada)
    contrato = baker.make(
        "terceirizada.Contrato",
        lotes=[lote],
        edital=edital,
        numero="Contrato 78/SME/2024",
        uuid="13cb1ff3-a2c8-47ad-a17f-145b38f72ef0",
    )
    return contrato


@pytest.fixture
def empenho(edital, contrato):
    empenho = baker.make(
        "Empenho",
        numero="123456",
        contrato=contrato,
        edital=edital,
        tipo_empenho="PRINCIPAL",
        status="ATIVO",
        valor_total="100.50",
    )
    return empenho


@pytest.fixture
def faixa_etaria():
    return baker.make(
        "FaixaEtaria", inicio=1, fim=4, uuid="1d125c38-ce75-6974-b25d-a4874745b996"
    )


@pytest.fixture
def make_log_matriculados_faixa_etaria_dia(faixa_etaria):
    def handle(
        dia: int,
        escola: Escola,
        solicitacao: SolicitacaoMedicaoInicial,
        periodo_escolar: PeriodoEscolar,
    ):
        data = datetime.datetime(int(solicitacao.ano), int(solicitacao.mes), dia).date()
        baker.make(
            "LogAlunosMatriculadosFaixaEtariaDia",
            escola=escola,
            data=data,
            faixa_etaria=faixa_etaria,
            periodo_escolar=periodo_escolar,
            quantidade=10,
        )

    return handle


@pytest.fixture
def solicitacao_medicao_inicial_cemei_simples(escola_cemei):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial", mes=4, ano=2023, escola=escola_cemei
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])

    return solicitacao_medicao


@pytest.fixture
def make_dia_letivo():
    def handle(dia: int, mes: int, ano: int, escola: Escola):
        data = datetime.datetime(ano, mes, dia).date()
        return baker.make(DiaCalendario, escola=escola, data=data, dia_letivo=True)

    return handle


@pytest.fixture
def make_periodo_escolar():
    def handle(nome: str):
        if PeriodoEscolar.objects.filter(nome=nome).exists():
            return PeriodoEscolar.objects.get(nome=nome)
        return baker.make("PeriodoEscolar", nome=nome)

    return handle


@pytest.fixture
def make_medicao():
    def handle(solicitacao: SolicitacaoMedicaoInicial, periodo_escolar: PeriodoEscolar):
        return baker.make(
            "Medicao",
            solicitacao_medicao_inicial=solicitacao,
            periodo_escolar=periodo_escolar,
        )

    return handle


@pytest.fixture
def make_valor_medicao_faixa_etaria(categoria_medicao, faixa_etaria):
    def handle(medicao: Medicao, valor: str, dia: int):
        return baker.make(
            "ValorMedicao",
            dia=str(dia).rjust(2, "0"),
            semana="1",
            nome_campo="frequencia",
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=valor,
            faixa_etaria=faixa_etaria,
        )

    return handle


@pytest.fixture
def make_valores_medicao():
    def handle(*args, **kwargs):
        return baker.make("ValorMedicao", **kwargs)

    return handle


@pytest.fixture
def usuario(django_user_model):
    return baker.make(django_user_model)


@pytest.fixture
def periodos_integral_parcial_e_logs(escola, faixas_etarias_ativas):
    periodo_integral = baker.make("PeriodoEscolar", nome="INTEGRAL")
    periodo_parcial = baker.make("PeriodoEscolar", nome="PARCIAL")

    for periodo in [periodo_integral, periodo_parcial]:
        for dia in range(1, 5):
            baker.make(
                "LogAlunosMatriculadosFaixaEtariaDia",
                escola=escola,
                periodo_escolar=periodo,
                faixa_etaria=faixas_etarias_ativas[len(faixas_etarias_ativas) - 1],
                quantidade=2,
                data=datetime.date(2022, 12, dia),
            )


@pytest.fixture
def solicitacao_escola_ceuemei(escola_ceu_emei):
    return baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola_ceu_emei,
        mes="04",
        ano="2025",
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
    )


@pytest.fixture
def solicitacao_relatorio_consolidado_grupo_emef(escola):
    return baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola,
        mes="04",
        ano="2025",
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
    )


@pytest.fixture
def solicitacao_relatorio_consolidado_grupo_emei(escola_emei):
    return baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola_emei,
        mes="04",
        ano="2025",
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
    )


@pytest.fixture
def medicao_grupo_solicitacao_alimentacao(
    solicitacao_relatorio_consolidado_grupo_emef,
    solicitacao_relatorio_consolidado_grupo_emei,
    grupo_solicitacoes_alimentacao,
):
    medicao_emef = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_emef,
        periodo_escolar=None,
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
        grupo=grupo_solicitacoes_alimentacao,
    )

    medicao_emei = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_emei,
        periodo_escolar=None,
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
        grupo=grupo_solicitacoes_alimentacao,
    )

    return medicao_emef, medicao_emei


@pytest.fixture
def medicao_grupo_alimentacao(
    solicitacao_relatorio_consolidado_grupo_emef,
    solicitacao_relatorio_consolidado_grupo_emei,
    periodo_escolar_manha,
):
    medicao_emef = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_emef,
        periodo_escolar=periodo_escolar_manha,
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
        grupo=None,
    )

    medicao_emei = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_emei,
        periodo_escolar=periodo_escolar_manha,
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
        grupo=None,
    )

    return medicao_emef, medicao_emei


@pytest.fixture
def relatorio_consolidado_xlsx_emef(
    solicitacao_relatorio_consolidado_grupo_emef,
    medicao_grupo_alimentacao,
    medicao_grupo_solicitacao_alimentacao,
    categoria_medicao,
    categoria_medicao_dieta_a,
    categoria_medicao_dieta_a_enteral_aminoacidos,
    categoria_medicao_dieta_b,
    categoria_medicao_solicitacoes_alimentacao,
):
    medicao_alimentacao_emef, _ = medicao_grupo_alimentacao
    medicao_solicitacao_emef, _ = medicao_grupo_solicitacao_alimentacao

    for dia in ["01", "02", "03", "04", "05"]:
        for campo in ["lanche", "lanche_4h", "refeicao", "sobremesa"]:
            baker.make(
                "ValorMedicao",
                dia=dia,
                nome_campo=campo,
                medicao=medicao_alimentacao_emef,
                categoria_medicao=categoria_medicao,
                valor="25",
            )
            if campo in ["lanche", "lanche_4h"]:
                for categoria in [
                    categoria_medicao_dieta_a,
                    categoria_medicao_dieta_b,
                    categoria_medicao_dieta_a_enteral_aminoacidos,
                ]:
                    baker.make(
                        "ValorMedicao",
                        dia=dia,
                        nome_campo=campo,
                        medicao=medicao_alimentacao_emef,
                        categoria_medicao=categoria,
                        valor="2",
                    )
            elif campo == "refeicao":
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo=campo,
                    medicao=medicao_alimentacao_emef,
                    categoria_medicao=categoria_medicao_dieta_a_enteral_aminoacidos,
                    valor="2",
                )
        if dia == "05":
            for campo in ["kit_lanche", "lanche_emergencial"]:
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo=campo,
                    medicao=medicao_solicitacao_emef,
                    categoria_medicao=categoria_medicao_solicitacoes_alimentacao,
                    valor="10",
                )

        baker.make(
            "ValorMedicao",
            dia=dia,
            nome_campo="matriculados",
            medicao=medicao_alimentacao_emef,
            categoria_medicao=categoria_medicao,
            valor="100",
        )
        baker.make(
            "ValorMedicao",
            dia=dia,
            nome_campo="frequencia",
            medicao=medicao_alimentacao_emef,
            categoria_medicao=categoria_medicao,
            valor="90",
        )

    return solicitacao_relatorio_consolidado_grupo_emef


@pytest.fixture
def relatorio_consolidado_xlsx_emei(
    solicitacao_relatorio_consolidado_grupo_emei,
    medicao_grupo_alimentacao,
    medicao_grupo_solicitacao_alimentacao,
    categoria_medicao,
    categoria_medicao_dieta_a,
    categoria_medicao_dieta_a_enteral_aminoacidos,
    categoria_medicao_dieta_b,
    categoria_medicao_solicitacoes_alimentacao,
):
    _, medicao_alimentacao_emei = medicao_grupo_alimentacao
    _, medicao_solicitacao_emei = medicao_grupo_solicitacao_alimentacao

    for dia in ["01", "02", "03", "04", "05"]:
        for campo in ["lanche", "lanche_4h", "refeicao", "sobremesa"]:
            baker.make(
                "ValorMedicao",
                dia=dia,
                nome_campo=campo,
                medicao=medicao_alimentacao_emei,
                categoria_medicao=categoria_medicao,
                valor="30",
            )
            if campo in ["lanche", "lanche_4h"]:
                for categoria in [
                    categoria_medicao_dieta_a,
                    categoria_medicao_dieta_b,
                    categoria_medicao_dieta_a_enteral_aminoacidos,
                ]:
                    baker.make(
                        "ValorMedicao",
                        dia=dia,
                        nome_campo=campo,
                        medicao=medicao_alimentacao_emei,
                        categoria_medicao=categoria,
                        valor="4",
                    )
            elif campo == "refeicao":
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo=campo,
                    medicao=medicao_alimentacao_emei,
                    categoria_medicao=categoria_medicao_dieta_a_enteral_aminoacidos,
                    valor="4",
                )
        if dia == "05":
            for campo in ["kit_lanche", "lanche_emergencial"]:
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo=campo,
                    medicao=medicao_solicitacao_emei,
                    categoria_medicao=categoria_medicao_solicitacoes_alimentacao,
                    valor="5",
                )

        baker.make(
            "ValorMedicao",
            dia=dia,
            nome_campo="matriculados",
            medicao=medicao_alimentacao_emei,
            categoria_medicao=categoria_medicao,
            valor="90",
        )
        baker.make(
            "ValorMedicao",
            dia=dia,
            nome_campo="frequencia",
            medicao=medicao_alimentacao_emei,
            categoria_medicao=categoria_medicao,
            valor="80",
        )

    return solicitacao_relatorio_consolidado_grupo_emei


@pytest.fixture
def mock_query_params_excel_emef(
    solicitacao_relatorio_consolidado_grupo_emef, grupo_escolar
):
    return {
        "dre": solicitacao_relatorio_consolidado_grupo_emef.escola.diretoria_regional.uuid,
        "status": "MEDICAO_APROVADA_PELA_CODAE",
        "grupo_escolar": grupo_escolar,
        "mes": solicitacao_relatorio_consolidado_grupo_emef.mes,
        "ano": solicitacao_relatorio_consolidado_grupo_emef.ano,
        "lotes[]": solicitacao_relatorio_consolidado_grupo_emef.escola.lote.uuid,
        "lotes": [solicitacao_relatorio_consolidado_grupo_emef.escola.lote.uuid],
    }


@pytest.fixture
def mock_query_params_excel_emei(solicitacao_relatorio_consolidado_grupo_emei):
    grupo_escolar = baker.make(
        "GrupoUnidadeEscolar",
        nome="Grupo 3",
        uuid="f573268f-e94b-4d4d-a92e-5ed5453b82e6",
        tipos_unidades=[
            baker.make("TipoUnidadeEscolar", iniciais="EMEI"),
            baker.make("TipoUnidadeEscolar", iniciais="CEU EMEI"),
            baker.make("TipoUnidadeEscolar", iniciais="EMEI P FOM"),
        ],
    )
    return {
        "dre": solicitacao_relatorio_consolidado_grupo_emei.escola.diretoria_regional.uuid,
        "status": "MEDICAO_APROVADA_PELA_CODAE",
        "grupo_escolar": grupo_escolar,
        "mes": solicitacao_relatorio_consolidado_grupo_emei.mes,
        "ano": solicitacao_relatorio_consolidado_grupo_emei.ano,
        "lotes[]": solicitacao_relatorio_consolidado_grupo_emei.escola.lote.uuid,
        "lotes": [solicitacao_relatorio_consolidado_grupo_emei.escola.lote.uuid],
    }


@pytest.fixture
def mock_colunas():
    return [
        ("Solicitações de Alimentação", "kit_lanche"),
        ("Solicitações de Alimentação", "lanche_emergencial"),
        ("MANHA", "lanche"),
        ("MANHA", "lanche_4h"),
        ("MANHA", "refeicao"),
        ("MANHA", "total_refeicoes_pagamento"),
        ("MANHA", "sobremesa"),
        ("MANHA", "total_sobremesas_pagamento"),
        ("DIETA ESPECIAL - TIPO A", "lanche"),
        ("DIETA ESPECIAL - TIPO A", "lanche_4h"),
        ("DIETA ESPECIAL - TIPO A", "refeicao"),
        ("DIETA ESPECIAL - TIPO B", "lanche"),
        ("DIETA ESPECIAL - TIPO B", "lanche_4h"),
    ]


@pytest.fixture
def mock_linhas_emef():
    return [
        [
            "EMEF",
            "123456",
            "EMEF TESTE",
            10.0,
            10.0,
            125.0,
            125.0,
            125.0,
            125,
            125.0,
            125,
            20.0,
            20.0,
            10.0,
            10.0,
            10.0,
        ]
    ]


@pytest.fixture
def mock_linhas_emei():
    return [
        [
            "EMEI",
            "987654",
            "EMEI TESTE",
            5.0,
            5.0,
            150.0,
            150.0,
            150.0,
            150.0,
            150.0,
            150.0,
            40.0,
            40.0,
            20.0,
            20.0,
            20.0,
        ]
    ]


@pytest.fixture
def informacoes_excel_writer_emef(
    relatorio_consolidado_xlsx_emef, mock_colunas, mock_linhas_emef
):
    arquivo = BytesIO()
    aba = f"Relatório Consolidado {relatorio_consolidado_xlsx_emef.mes}-{ relatorio_consolidado_xlsx_emef.ano}"
    writer = pd.ExcelWriter(arquivo, engine="xlsxwriter")
    workbook = writer.book
    worksheet = workbook.add_worksheet(aba)
    worksheet.set_default_row(20)
    df = emei_emef_insere_tabela(aba, mock_colunas, mock_linhas_emef, writer)
    try:
        yield aba, writer, workbook, worksheet, df, arquivo
    finally:
        workbook.close()
        writer.close()


@pytest.fixture
def informacoes_excel_writer_emei(
    relatorio_consolidado_xlsx_emei, mock_colunas, mock_linhas_emei
):
    arquivo = BytesIO()
    aba = f"Relatório Consolidado {relatorio_consolidado_xlsx_emei.mes}-{ relatorio_consolidado_xlsx_emei.ano}"
    writer = pd.ExcelWriter(arquivo, engine="xlsxwriter")
    workbook = writer.book
    worksheet = workbook.add_worksheet(aba)
    worksheet.set_default_row(20)
    df = emei_emef_insere_tabela(aba, mock_colunas, mock_linhas_emei, writer)
    try:
        yield aba, writer, workbook, worksheet, df, arquivo
    finally:
        workbook.close()
        writer.close()


@pytest.fixture
def clausula_desconto(edital):
    return baker.make(
        "ClausulaDeDesconto",
        numero_clausula="N485959",
        porcentagem_desconto=0.12,
        edital=edital,
    )


@pytest.fixture
def relatorio_financeiro():
    return baker.make(
        "RelatorioFinanceiro",
        grupo_unidade_escolar=baker.make("GrupoUnidadeEscolar"),
        lote=baker.make("escola.Lote"),
        mes="10",
        ano="2025",
    )


@pytest.fixture
def solicitacao_relatorio_consolidado_grupo_cei(escola_cei):
    return baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola_cei,
        mes="04",
        ano="2025",
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
    )


@pytest.fixture
def solicitacao_escola_cci(escola_cci):
    return baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola_cci,
        mes="04",
        ano="2025",
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
    )


@pytest.fixture
def relatorio_consolidado_xlsx_cei(
    solicitacao_relatorio_consolidado_grupo_cei,
    periodo_escolar_integral,
    periodo_escolar_parcial,
    periodo_escolar_manha,
    periodo_escolar_tarde,
    categoria_medicao,
    categoria_medicao_dieta_a,
    categoria_medicao_dieta_b,
    faixas_etarias_ativas,
):
    medicao_integral = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_cei,
        periodo_escolar=periodo_escolar_integral,
    )
    medicao_parcial = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_cei,
        periodo_escolar=periodo_escolar_parcial,
    )
    medicao_manha = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_cei,
        periodo_escolar=periodo_escolar_manha,
    )

    medicao_tarde = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_cei,
        periodo_escolar=periodo_escolar_tarde,
    )

    for dia in ["01", "02", "03", "04"]:
        for medicao in [
            medicao_integral,
            medicao_parcial,
            medicao_manha,
            medicao_tarde,
        ]:
            if medicao in [medicao_integral, medicao_parcial]:
                for faixa in faixas_etarias_ativas:
                    baker.make(
                        "ValorMedicao",
                        dia=dia,
                        nome_campo="frequencia",
                        medicao=medicao,
                        categoria_medicao=categoria_medicao,
                        valor=20,
                        faixa_etaria=faixa,
                    )
                    baker.make(
                        "ValorMedicao",
                        dia=dia,
                        nome_campo="frequencia",
                        medicao=medicao,
                        categoria_medicao=categoria_medicao_dieta_a,
                        valor=2,
                        faixa_etaria=faixa,
                    )
                    baker.make(
                        "ValorMedicao",
                        dia=dia,
                        nome_campo="frequencia",
                        medicao=medicao,
                        categoria_medicao=categoria_medicao_dieta_b,
                        valor=2,
                        faixa_etaria=faixa,
                    )

            elif medicao == medicao_manha:
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo="frequencia",
                    medicao=medicao,
                    categoria_medicao=categoria_medicao,
                    valor=20,
                    faixa_etaria=faixas_etarias_ativas[2],
                )
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo="frequencia",
                    medicao=medicao,
                    categoria_medicao=categoria_medicao,
                    valor=15,
                    faixa_etaria=faixas_etarias_ativas[4],
                )
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo="frequencia",
                    medicao=medicao,
                    categoria_medicao=categoria_medicao_dieta_a,
                    valor=2,
                    faixa_etaria=faixas_etarias_ativas[2],
                )
            elif medicao == medicao_tarde:
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo="frequencia",
                    medicao=medicao,
                    categoria_medicao=categoria_medicao,
                    valor=15,
                    faixa_etaria=faixas_etarias_ativas[3],
                )
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo="frequencia",
                    medicao=medicao,
                    categoria_medicao=categoria_medicao,
                    valor=20,
                    faixa_etaria=faixas_etarias_ativas[6],
                )
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo="frequencia",
                    medicao=medicao,
                    categoria_medicao=categoria_medicao_dieta_b,
                    valor=1,
                    faixa_etaria=faixas_etarias_ativas[3],
                )
    return solicitacao_relatorio_consolidado_grupo_cei


@pytest.fixture
def mock_query_params_excel_cei(solicitacao_relatorio_consolidado_grupo_cei):
    grupo_escolar = baker.make(
        "GrupoUnidadeEscolar",
        nome="Grupo 1",
        uuid="782d1da2-bec0-4afb-b560-d63332a719f6",
        tipos_unidades=[
            baker.make("TipoUnidadeEscolar", iniciais="CEI DIRET"),
            baker.make("TipoUnidadeEscolar", iniciais="CEU CEI"),
            baker.make("TipoUnidadeEscolar", iniciais="CEI"),
            baker.make("TipoUnidadeEscolar", iniciais="CCI"),
            baker.make("TipoUnidadeEscolar", iniciais="CCI/CIPS"),
            baker.make("TipoUnidadeEscolar", iniciais="CEI CEU"),
        ],
    )
    return {
        "dre": solicitacao_relatorio_consolidado_grupo_cei.escola.diretoria_regional.uuid,
        "status": "MEDICAO_APROVADA_PELA_CODAE",
        "grupo_escolar": grupo_escolar,
        "mes": solicitacao_relatorio_consolidado_grupo_cei.mes,
        "ano": solicitacao_relatorio_consolidado_grupo_cei.ano,
        "lotes[]": solicitacao_relatorio_consolidado_grupo_cei.escola.lote.uuid,
        "lotes": [solicitacao_relatorio_consolidado_grupo_cei.escola.lote.uuid],
    }


@pytest.fixture
def mock_colunas_cei(faixas_etarias_ativas):
    faixas = [faixa.id for faixa in faixas_etarias_ativas]
    colunas = []

    colunas.extend(("INTEGRAL", faixa) for faixa in faixas)
    colunas.extend(("DIETA ESPECIAL - TIPO A - INTEGRAL", faixa) for faixa in faixas)
    colunas.extend(("DIETA ESPECIAL - TIPO B - INTEGRAL", faixa) for faixa in faixas)

    colunas.extend(("PARCIAL", faixa) for faixa in faixas)
    colunas.extend(("DIETA ESPECIAL - TIPO A - PARCIAL", faixa) for faixa in faixas)
    colunas.extend(("DIETA ESPECIAL - TIPO B - PARCIAL", faixa) for faixa in faixas)

    colunas.append(("MANHA", faixas_etarias_ativas[2].id))
    colunas.append(("MANHA", faixas_etarias_ativas[4].id))

    colunas.append(("TARDE", faixas_etarias_ativas[3].id))
    colunas.append(("TARDE", faixas_etarias_ativas[6].id))

    colunas.append(("DIETA ESPECIAL - TIPO A", faixas_etarias_ativas[2].id))
    colunas.append(("DIETA ESPECIAL - TIPO B", faixas_etarias_ativas[3].id))

    return colunas


@pytest.fixture
def mock_linhas_cei():
    return [
        [
            "CEI DIRET",
            "765432",
            "CEI DIRET TESTE",
            80.0,
            80.0,
            80.0,
            80.0,
            80.0,
            80.0,
            80.0,
            80.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            80.0,
            80.0,
            80.0,
            80.0,
            80.0,
            80.0,
            80.0,
            80.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            8.0,
            80.0,
            60.0,
            60.0,
            80.0,
            8.0,
            4.0,
        ]
    ]


@pytest.fixture
def informacoes_excel_writer_cei(
    relatorio_consolidado_xlsx_cei, mock_colunas_cei, mock_linhas_cei
):
    arquivo = BytesIO()
    aba = f"Relatório Consolidado {relatorio_consolidado_xlsx_cei.mes}-{ relatorio_consolidado_xlsx_cei.ano}"
    writer = pd.ExcelWriter(arquivo, engine="xlsxwriter")
    workbook = writer.book
    worksheet = workbook.add_worksheet(aba)
    worksheet.set_default_row(20)
    df = cei_insere_tabela(aba, mock_colunas_cei, mock_linhas_cei, writer)
    try:
        yield aba, writer, workbook, worksheet, df, arquivo
    finally:
        workbook.close()
        writer.close()


@pytest.fixture
def solicitacao_relatorio_consolidado_grupo_cemei(escola_cemei):
    return baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola_cemei,
        mes="04",
        ano="2025",
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
    )


@pytest.fixture
def solicitacao_escola_ceu_cemei(escola_ceu_cemei):
    return baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola_ceu_cemei,
        mes="04",
        ano="2025",
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
    )


@pytest.fixture
def relatorio_consolidado_xlsx_cemei(
    solicitacao_relatorio_consolidado_grupo_cemei,
    periodo_escolar_integral,
    periodo_escolar_parcial,
    faixas_etarias_ativas,
    categoria_medicao,
    categoria_medicao_dieta_a,
    categoria_medicao_dieta_a_enteral_aminoacidos,
    categoria_medicao_dieta_b,
    grupo_infantil_integral,
    grupo_infantil_manha,
    grupo_infantil_tarde,
    grupo_solicitacoes_alimentacao,
    categoria_medicao_solicitacoes_alimentacao,
):
    medicao_integral = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_cemei,
        periodo_escolar=periodo_escolar_integral,
    )
    medicao_parcial = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_cemei,
        periodo_escolar=periodo_escolar_parcial,
    )

    medicao_infantil_integral = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_cemei,
        grupo=grupo_infantil_integral,
    )
    medicao_infantil_manha = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_cemei,
        grupo=grupo_infantil_manha,
    )
    medicao_infantil_tarde = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_cemei,
        grupo=grupo_infantil_tarde,
    )

    solicitacao_alimentacao = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_cemei,
        grupo=grupo_solicitacoes_alimentacao,
    )

    for dia in ["01", "02", "03", "04", "05"]:
        if dia == "05":
            for campo in ["kit_lanche", "lanche_emergencial"]:
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo=campo,
                    medicao=solicitacao_alimentacao,
                    categoria_medicao=categoria_medicao_solicitacoes_alimentacao,
                    valor="5",
                )
        for medicao in [medicao_integral, medicao_parcial]:
            for faixa in faixas_etarias_ativas:
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo="frequencia",
                    medicao=medicao,
                    categoria_medicao=categoria_medicao,
                    valor=20,
                    faixa_etaria=faixa,
                )
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo="frequencia",
                    medicao=medicao,
                    categoria_medicao=categoria_medicao_dieta_a,
                    valor=2,
                    faixa_etaria=faixa,
                )
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo="frequencia",
                    medicao=medicao,
                    categoria_medicao=categoria_medicao_dieta_b,
                    valor=3,
                    faixa_etaria=faixa,
                )
        for medicao in [
            medicao_infantil_integral,
            medicao_infantil_manha,
            medicao_infantil_tarde,
        ]:
            for campo in ["lanche", "lanche_4h", "refeicao", "sobremesa"]:
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo=campo,
                    medicao=medicao,
                    categoria_medicao=categoria_medicao,
                    valor="30",
                )
                if campo in ["lanche", "lanche_4h"]:
                    for categoria in [
                        categoria_medicao_dieta_a,
                        categoria_medicao_dieta_b,
                        categoria_medicao_dieta_a_enteral_aminoacidos,
                    ]:
                        baker.make(
                            "ValorMedicao",
                            dia=dia,
                            nome_campo=campo,
                            medicao=medicao,
                            categoria_medicao=categoria,
                            valor=1,
                        )
                elif campo == "refeicao":
                    baker.make(
                        "ValorMedicao",
                        dia=dia,
                        nome_campo=campo,
                        medicao=medicao,
                        categoria_medicao=categoria_medicao_dieta_a_enteral_aminoacidos,
                        valor=1,
                    )

    return solicitacao_relatorio_consolidado_grupo_cemei


@pytest.fixture
def mock_query_params_excel_cemei(solicitacao_relatorio_consolidado_grupo_cemei):
    grupo_escolar = baker.make(
        "GrupoUnidadeEscolar",
        nome="Grupo 2",
        uuid="012dc7a2-eb11-4000-96b9-e3c5130dc64c",
        tipos_unidades=[
            baker.make("TipoUnidadeEscolar", iniciais="CEMEI"),
            baker.make("TipoUnidadeEscolar", iniciais="CEU CEMEI"),
        ],
    )
    return {
        "dre": solicitacao_relatorio_consolidado_grupo_cemei.escola.diretoria_regional.uuid,
        "status": "MEDICAO_APROVADA_PELA_CODAE",
        "grupo_escolar": grupo_escolar,
        "mes": solicitacao_relatorio_consolidado_grupo_cemei.mes,
        "ano": solicitacao_relatorio_consolidado_grupo_cemei.ano,
        "lotes[]": solicitacao_relatorio_consolidado_grupo_cemei.escola.lote.uuid,
        "lotes": [solicitacao_relatorio_consolidado_grupo_cemei.escola.lote.uuid],
    }


@pytest.fixture
def mock_colunas_cemei(faixas_etarias_ativas):
    colunas = [
        ("Solicitações de Alimentação", "kit_lanche"),
        ("Solicitações de Alimentação", "lanche_emergencial"),
    ]
    faixas = [faixa.id for faixa in faixas_etarias_ativas]

    colunas.extend(("INTEGRAL", faixa) for faixa in faixas)
    colunas.extend(("DIETA ESPECIAL - TIPO A - INTEGRAL", faixa) for faixa in faixas)
    colunas.extend(("DIETA ESPECIAL - TIPO B - INTEGRAL", faixa) for faixa in faixas)
    colunas.extend(("PARCIAL", faixa) for faixa in faixas)
    colunas.extend(("DIETA ESPECIAL - TIPO A - PARCIAL", faixa) for faixa in faixas)
    colunas.extend(("DIETA ESPECIAL - TIPO B - PARCIAL", faixa) for faixa in faixas)

    for periodo in ["Infantil INTEGRAL", "Infantil MANHA", "Infantil TARDE"]:
        for campo in [
            "lanche",
            "lanche_4h",
            "refeicao",
            "total_refeicoes_pagamento",
            "sobremesa",
            "total_sobremesas_pagamento",
        ]:
            colunas.append((periodo, campo))

    colunas.append(("DIETA ESPECIAL - TIPO A - INFANTIL", "lanche"))
    colunas.append(("DIETA ESPECIAL - TIPO A - INFANTIL", "lanche_4h"))
    colunas.append(("DIETA ESPECIAL - TIPO A - INFANTIL", "refeicao"))
    colunas.append(("DIETA ESPECIAL - TIPO B - INFANTIL", "lanche"))
    colunas.append(("DIETA ESPECIAL - TIPO B - INFANTIL", "lanche_4h"))

    return colunas


@pytest.fixture
def mock_linhas_cemei():
    return [
        [
            "CEMEI",
            "543210",
            "CEMEI TESTE",
            5.0,
            5.0,
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            15.0,
            15.0,
            15.0,
            15.0,
            15.0,
            15.0,
            15.0,
            15.0,
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            15.0,
            15.0,
            15.0,
            15.0,
            15.0,
            15.0,
            15.0,
            15.0,
            150.0,
            150.0,
            150.0,
            150.0,
            150.0,
            150.0,
            150.0,
            150.0,
            150.0,
            150.0,
            150.0,
            150.0,
            150.0,
            150.0,
            150.0,
            150.0,
            150.0,
            150.0,
            30.0,
            30.0,
            15.0,
            15.0,
            15.0,
        ]
    ]


@pytest.fixture
def informacoes_excel_writer_cemei(
    relatorio_consolidado_xlsx_cemei, mock_colunas_cemei, mock_linhas_cemei
):
    arquivo = BytesIO()
    aba = f"Relatório Consolidado {relatorio_consolidado_xlsx_cemei.mes}-{ relatorio_consolidado_xlsx_cemei.ano}"
    writer = pd.ExcelWriter(arquivo, engine="xlsxwriter")
    workbook = writer.book
    worksheet = workbook.add_worksheet(aba)
    worksheet.set_default_row(20)
    df = cemei_insere_tabela(aba, mock_colunas_cemei, mock_linhas_cemei, writer)
    try:
        yield aba, writer, workbook, worksheet, df, arquivo
    finally:
        workbook.close()
        writer.close()


@pytest.fixture
def solicitacao_escola_emebs():
    return baker.make(
        "SolicitacaoMedicaoInicial",
        escola=baker.make("Escola", nome="EMEBS PRIMEIRA"),
        mes="04",
        ano="2025",
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
    )


@pytest.fixture
def solicitacao_relatorio_consolidado_grupo_emebs(escola_emebs):
    return baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola_emebs,
        mes="04",
        ano="2025",
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
    )


@pytest.fixture
def relatorio_consolidado_xlsx_emebs(
    solicitacao_relatorio_consolidado_grupo_emebs,
    periodo_escolar_manha,
    periodo_escolar_tarde,
    periodo_escolar_integral,
    periodo_escolar_noite,
    categoria_medicao,
    categoria_medicao_dieta_a,
    categoria_medicao_dieta_a_enteral_aminoacidos,
    categoria_medicao_dieta_b,
    grupo_solicitacoes_alimentacao,
    categoria_medicao_solicitacoes_alimentacao,
    grupo_programas_e_projetos,
):
    medicao_manha = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_emebs,
        periodo_escolar=periodo_escolar_manha,
    )
    medicao_tarde = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_emebs,
        periodo_escolar=periodo_escolar_tarde,
    )

    medicao_integral = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_emebs,
        periodo_escolar=periodo_escolar_integral,
    )

    medicao_noite = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_emebs,
        periodo_escolar=periodo_escolar_noite,
    )

    medicao_programas_e_projetos = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_emebs,
        grupo=grupo_programas_e_projetos,
    )
    solicitacao_alimentacao = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_emebs,
        grupo=grupo_solicitacoes_alimentacao,
    )

    for dia in ["01", "02", "03", "04", "05"]:
        if dia == "05":
            for campo in ["kit_lanche", "lanche_emergencial"]:
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo=campo,
                    medicao=solicitacao_alimentacao,
                    categoria_medicao=categoria_medicao_solicitacoes_alimentacao,
                    valor="5",
                    infantil_ou_fundamental="FUNDAMENTAL",
                )

        for medicao in [
            medicao_manha,
            medicao_tarde,
            medicao_integral,
            medicao_noite,
            medicao_programas_e_projetos,
        ]:
            for turma in ["INFANTIL", "FUNDAMENTAL"]:
                if medicao == medicao_noite and turma == "INFANTIL":
                    continue
                if medicao == medicao_programas_e_projetos:
                    baker.make(
                        "ValorMedicao",
                        dia=dia,
                        nome_campo="numero_de_alunos",
                        medicao=medicao,
                        categoria_medicao=categoria_medicao,
                        valor="90",
                        infantil_ou_fundamental=turma,
                    )
                else:
                    baker.make(
                        "ValorMedicao",
                        dia=dia,
                        nome_campo="matriculados",
                        medicao=medicao,
                        categoria_medicao=categoria_medicao,
                        valor="90",
                        infantil_ou_fundamental=turma,
                    )
                baker.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo="frequencia",
                    medicao=medicao,
                    categoria_medicao=categoria_medicao,
                    valor="80",
                    infantil_ou_fundamental=turma,
                )

                for campo in ["lanche", "lanche_4h", "refeicao", "sobremesa"]:
                    baker.make(
                        "ValorMedicao",
                        dia=dia,
                        nome_campo=campo,
                        medicao=medicao,
                        categoria_medicao=categoria_medicao,
                        valor="70",
                        infantil_ou_fundamental=turma,
                    )
                    if campo in ["lanche", "lanche_4h"]:
                        for categoria in [
                            categoria_medicao_dieta_a,
                            categoria_medicao_dieta_b,
                            categoria_medicao_dieta_a_enteral_aminoacidos,
                        ]:
                            baker.make(
                                "ValorMedicao",
                                dia=dia,
                                nome_campo=campo,
                                medicao=medicao,
                                categoria_medicao=categoria,
                                valor=1,
                                infantil_ou_fundamental=turma,
                            )
                    elif campo == "refeicao":
                        baker.make(
                            "ValorMedicao",
                            dia=dia,
                            nome_campo=campo,
                            medicao=medicao,
                            categoria_medicao=categoria_medicao_dieta_a_enteral_aminoacidos,
                            valor=1,
                            infantil_ou_fundamental=turma,
                        )

    return solicitacao_relatorio_consolidado_grupo_emebs


@pytest.fixture
def mock_query_params_excel_emebs(solicitacao_relatorio_consolidado_grupo_emebs):
    grupo_escolar = baker.make(
        "GrupoUnidadeEscolar",
        nome="Grupo 5",
        uuid="172a2ae6-c417-49d3-91d3-a2dae3d8a56b",
        tipos_unidades=[
            baker.make("TipoUnidadeEscolar", iniciais="EMEBS"),
        ],
    )
    return {
        "dre": solicitacao_relatorio_consolidado_grupo_emebs.escola.diretoria_regional.uuid,
        "status": "MEDICAO_APROVADA_PELA_CODAE",
        "grupo_escolar": grupo_escolar,
        "mes": solicitacao_relatorio_consolidado_grupo_emebs.mes,
        "ano": solicitacao_relatorio_consolidado_grupo_emebs.ano,
        "lotes[]": solicitacao_relatorio_consolidado_grupo_emebs.escola.lote.uuid,
        "lotes": [solicitacao_relatorio_consolidado_grupo_emebs.escola.lote.uuid],
    }


@pytest.fixture
def mock_colunas_emebs():
    colunas = [
        ("", "Solicitações de Alimentação", "lanche_emergencial"),
        ("", "Solicitações de Alimentação", "kit_lanche"),
    ]

    for turma in ["INFANTIL", "FUNDAMENTAL"]:
        for periodo in ["MANHA", "TARDE", "INTEGRAL", "NOITE", "Programas e Projetos"]:
            if turma == "INFANTIL" and periodo == "NOITE":
                continue

            for campo in [
                "lanche",
                "lanche_4h",
                "refeicao",
                "total_refeicoes_pagamento",
                "sobremesa",
                "total_sobremesas_pagamento",
            ]:
                if periodo == "Programas e Projetos" and campo == "sobremesa":
                    continue
                colunas.append((turma, periodo, campo))

        colunas.append((turma, "DIETA ESPECIAL - TIPO A", "lanche"))
        colunas.append((turma, "DIETA ESPECIAL - TIPO A", "lanche_4h"))
        colunas.append((turma, "DIETA ESPECIAL - TIPO A", "refeicao"))
        colunas.append((turma, "DIETA ESPECIAL - TIPO B", "lanche"))
        colunas.append((turma, "DIETA ESPECIAL - TIPO B", "lanche_4h"))
    return colunas


@pytest.fixture
def mock_linhas_emebs():
    return [
        [
            "EMEBS",
            "000329",
            "EMEBS TESTE",
            5.0,
            5.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            350.0,
            40.0,
            40.0,
            20.0,
            20.0,
            20.0,
            350.0,
            350.0,
            350.0,
            350,
            350.0,
            350,
            350.0,
            350.0,
            350.0,
            350,
            350.0,
            350,
            350.0,
            350.0,
            350.0,
            350,
            350.0,
            350,
            350.0,
            350.0,
            350.0,
            350,
            350.0,
            350,
            350.0,
            350.0,
            350.0,
            350,
            350,
            50.0,
            50.0,
            25.0,
            25.0,
            25.0,
        ]
    ]


@pytest.fixture
def informacoes_excel_writer_emebs(
    relatorio_consolidado_xlsx_emebs, mock_colunas_emebs, mock_linhas_emebs
):
    arquivo = BytesIO()
    aba = f"Relatório Consolidado {relatorio_consolidado_xlsx_emebs.mes}-{ relatorio_consolidado_xlsx_emebs.ano}"
    writer = pd.ExcelWriter(arquivo, engine="xlsxwriter")
    workbook = writer.book
    worksheet = workbook.add_worksheet(aba)
    worksheet.set_default_row(20)
    df = emebs_insere_tabela(aba, mock_colunas_emebs, mock_linhas_emebs, writer)
    try:
        yield aba, writer, workbook, worksheet, df, arquivo
    finally:
        workbook.close()
        writer.close()


@pytest.fixture
def solicitacao_sem_lancamento(solicitacao_relatorio_consolidado_grupo_emef, usuario):
    medicao = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado_grupo_emef,
        periodo_escolar=baker.make("PeriodoEscolar", nome="MANHA"),
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_SEM_LANCAMENTOS,
        grupo=None,
    )
    kwargs = {"justificativa": "Não houve aula no período"}
    solicitacao_relatorio_consolidado_grupo_emef.salvar_log_transicao(
        LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE, usuario, **kwargs
    )
    medicao.salvar_log_transicao(
        LogSolicitacoesUsuario.MEDICAO_SEM_LANCAMENTOS, usuario, **kwargs
    )

    return solicitacao_relatorio_consolidado_grupo_emef


@pytest.fixture
def solicitacao_sem_lancamento_com_correcao(solicitacao_sem_lancamento, usuario):
    kwargs = {"justificativa": "Houve alimentação ofertadada nesse período"}
    solicitacao_sem_lancamento.status = (
        SolicitacaoMedicaoInicialWorkflow.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
    )
    solicitacao_sem_lancamento.save()
    solicitacao_sem_lancamento.salvar_log_transicao(
        LogSolicitacoesUsuario.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
        usuario,
        **kwargs,
    )
    return solicitacao_sem_lancamento


@pytest.fixture
def medicao_sem_lancamento_com_correcao(
    solicitacao_sem_lancamento_com_correcao, usuario
):
    kwargs = {"justificativa": "Houve alimentação ofertadada nesse período"}
    medicao = solicitacao_sem_lancamento_com_correcao.medicoes.first()
    medicao.status = (
        SolicitacaoMedicaoInicialWorkflow.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
    )
    medicao.save()
    medicao.salvar_log_transicao(
        LogSolicitacoesUsuario.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
        usuario,
        **kwargs,
    )

    return solicitacao_sem_lancamento_com_correcao


@pytest.fixture
def mock_exportacao_relatorio_adesao(diretoria_regional, escola):
    lotes = [baker.make("Lote", nome=f"Lote {i:02d}") for i in range(1, 4)]

    resultados = {
        "MANHA": {
            "LANCHE": {
                "total_servido": 140,
                "total_frequencia": 755,
                "total_adesao": 0.1854,
            },
            "SOBREMESA": {
                "total_servido": 140,
                "total_frequencia": 755,
                "total_adesao": 0.1854,
            },
        },
        "TARDE": {
            "LANCHE": {
                "total_servido": 130,
                "total_frequencia": 745,
                "total_adesao": 0.1745,
            },
            "SOBREMESA": {
                "total_servido": 250,
                "total_frequencia": 745,
                "total_adesao": 0.3356,
            },
        },
    }

    query_params = {
        "mes_ano": "03_2025",
        "diretoria_regional": str(diretoria_regional.uuid),
        "lotes[]": str(lotes[0].uuid),
        "lotes[]": str(lotes[1].uuid),
        "lotes[]": str(lotes[2].uuid),
        "escola": f"{escola.codigo_eol} - {escola.nome} - 3567-2",
        "periodo_lancamento_de": "05/03/2025",
        "periodo_lancamento_ate": "15/03/2025",
        "lotes": [str(lote.uuid) for lote in lotes],
    }
    return resultados, query_params


@pytest.fixture
def mock_exportacao_informacoes_excel_writer():
    arquivo = BytesIO()
    aba = "Relatório de Adesão"
    writer = pd.ExcelWriter(arquivo, engine="xlsxwriter")
    workbook = writer.book
    worksheet = workbook.add_worksheet(aba)

    colunas = [
        "Tipo de Alimentação",
        "Total de Alimentações Servidas",
        "Número Total de Frequência",
        "% de Adesão",
    ]
    try:
        yield colunas, aba, writer, workbook, worksheet, arquivo
    finally:
        workbook.close()
        writer.close()
