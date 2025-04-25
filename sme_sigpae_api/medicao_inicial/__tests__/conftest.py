import datetime
import json
import random
from io import BytesIO

import pandas as pd
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from model_mommy import mommy

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
from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_excel import (
    _insere_tabela_periodos_na_planilha,
)


@pytest.fixture
def kit_lanche_1():
    return mommy.make("KitLanche", nome="KIT 1")


@pytest.fixture
def kit_lanche_2():
    return mommy.make("KitLanche", nome="KIT 2")


@pytest.fixture
def grupo_programas_e_projetos():
    return mommy.make("GrupoMedicao", nome="Programas e Projetos")


@pytest.fixture
def grupo_etec():
    return mommy.make("GrupoMedicao", nome="ETEC")


@pytest.fixture
def grupo_solicitacoes_alimentacao():
    return mommy.make("GrupoMedicao", nome="Solicitações de Alimentação")


@pytest.fixture
def motivo_inclusao_continua_programas_projetos():
    return mommy.make("MotivoInclusaoContinua", nome="Programas/Projetos Contínuos")


@pytest.fixture
def motivo_inclusao_continua_etec():
    return mommy.make("MotivoInclusaoContinua", nome="ETEC")


@pytest.fixture
def tipo_alimentacao_refeicao():
    return mommy.make("TipoAlimentacao", nome="Refeição")


@pytest.fixture
def tipo_alimentacao_lanche():
    return mommy.make("TipoAlimentacao", nome="Lanche")


@pytest.fixture
def tipo_alimentacao_lanche_4h():
    return mommy.make("TipoAlimentacao", nome="Lanche 4h")


@pytest.fixture
def tipo_alimentacao_sobremesa():
    return mommy.make("TipoAlimentacao", nome="Sobremesa")


@pytest.fixture
def tipo_alimentacao_almoco():
    return mommy.make("TipoAlimentacao", nome="Almoço")


@pytest.fixture
def tipo_alimentacao_lanche_emergencial():
    return mommy.make("TipoAlimentacao", nome="Lanche Emergencial")


@pytest.fixture
def classificacao_dieta_tipo_a():
    return mommy.make("ClassificacaoDieta", nome="Tipo A")


@pytest.fixture
def classificacao_dieta_tipo_a_enteral():
    return mommy.make("ClassificacaoDieta", nome="Tipo A ENTERAL")


@pytest.fixture
def tipo_unidade_escolar():
    return mommy.make("TipoUnidadeEscolar", iniciais="EMEF")


@pytest.fixture
def tipo_unidade_escolar_ceu_emef():
    return mommy.make("TipoUnidadeEscolar", iniciais="CEU EMEF")


@pytest.fixture
def tipo_unidade_escolar_emefm():
    return mommy.make("TipoUnidadeEscolar", iniciais="EMEFM")


@pytest.fixture
def tipo_unidade_escolar_cieja():
    return mommy.make("TipoUnidadeEscolar", iniciais="CIEJA")


@pytest.fixture
def tipo_unidade_escolar_ceu_gestao():
    return mommy.make("TipoUnidadeEscolar", iniciais="CEU GESTAO")


@pytest.fixture
def dia_sobremesa_doce(tipo_unidade_escolar):
    edital = mommy.make(
        "Edital",
        numero="Edital de Pregão nº 13/SME/2020",
        uuid="3a9082ae-2b8c-44f6-83af-fcab9452f932",
    )
    return mommy.make(
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
    emef = mommy.make(
        "TipoUnidadeEscolar",
        iniciais="EMEF",
        uuid="1cc3253b-e297-42b3-8e57-ebfd115a1aba",
    )
    mommy.make("Escola", tipo_unidade=emef, uuid="95ad02fb-d746-4e0c-95f4-0181a99bc192")
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
    edital = mommy.make(
        "Edital",
        numero="Edital de Pregão nº 75/SME/2022",
        uuid="85d4bdf1-79d3-4f93-87d7-9999ae4cd9c2",
    )
    edital = mommy.make(
        "Edital",
        numero="Edital de Pregão nº 36/SME/2022",
        uuid="10b56d45-b82d-4cce-9a14-36bbb082ac4d",
    )
    edital = mommy.make(
        "Edital",
        numero="Edital de Pregão nº 18/SME/2023",
        uuid="00f008ea-3410-4547-99e6-4e91e0168af8",
    )
    return client


@pytest.fixture
def escola(tipo_unidade_escolar, diretoria_regional):
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make(
        "Lote",
        nome="1",
        terceirizada=terceirizada,
        diretoria_regional=diretoria_regional,
    )
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    return mommy.make(
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
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make(
        "Lote",
        nome="1",
        terceirizada=terceirizada,
        diretoria_regional=diretoria_regional,
    )
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = mommy.make("TipoUnidadeEscolar", iniciais="EMEFM")
    return mommy.make(
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
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make("Lote", terceirizada=terceirizada)
    diretoria_regional = mommy.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL TESTE"
    )
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = mommy.make("TipoUnidadeEscolar", iniciais="EMEI")
    return mommy.make(
        "Escola",
        nome="EMEI TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
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
def escola_emebs():
    terceirizada = mommy.make("Terceirizada")
    diretoria_regional = mommy.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL TESTE",
    )
    lote = mommy.make(
        "Lote", terceirizada=terceirizada, diretoria_regional=diretoria_regional
    )
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = mommy.make("TipoUnidadeEscolar", iniciais="EMEBS")
    return mommy.make(
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
    terceirizada = mommy.make("Terceirizada")
    diretoria_regional = mommy.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL TESTE"
    )
    lote = mommy.make(
        "Lote", terceirizada=terceirizada, diretoria_regional=diretoria_regional
    )
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = mommy.make("TipoUnidadeEscolar", iniciais="CEU GESTAO")
    return mommy.make(
        "Escola",
        nome="CEMEI TESTE",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
    )


@pytest.fixture
def aluno():
    return mommy.make(
        "Aluno",
        nome="Roberto Alves da Silva",
        codigo_eol="123456",
        data_nascimento="2000-01-01",
        uuid="2d20157a-4e52-4d25-a4c7-9c0e6b67ee18",
    )


@pytest.fixture
def solicitacao_medicao_inicial_cemei(escola_cemei, categoria_medicao):
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_integral = mommy.make("PeriodoEscolar", nome="INTEGRAL")
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial", mes=4, ano=2023, escola=escola_cemei
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_integral,
    )
    mommy.make(
        "FaixaEtaria", inicio=1, fim=10, uuid="0c914b27-c7cd-4682-a439-a4874745b005"
    )
    faixa_etaria = mommy.make(
        "FaixaEtaria", inicio=1, fim=2, uuid="1d125c38-ce75-6974-b25d-a4874745b996"
    )
    mommy.make(
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
def solicitacao_medicao_inicial_cei(escola_cei, categoria_medicao):
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_integral = mommy.make("PeriodoEscolar", nome="INTEGRAL")
    periodo_manha = mommy.make("PeriodoEscolar", nome="MANHA")
    mommy.make(
        LogAlunosMatriculadosPeriodoEscola,
        escola=escola_cei,
        criado_em="01-04-2023",
        quantidade_alunos=100,
        periodo_escolar=periodo_manha,
    )
    mommy.make(
        LogAlunosMatriculadosPeriodoEscola,
        escola=escola_cei,
        criado_em="01-04-2023",
        quantidade_alunos=100,
        periodo_escolar=periodo_integral,
    )
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial",
        mes=4,
        ano=2023,
        escola=escola_cei,
        ue_possui_alunos_periodo_parcial=True,
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_integral,
    )
    mommy.make(
        "FaixaEtaria", inicio=1, fim=10, uuid="0c914b27-c7cd-4682-a439-a4874745b005"
    )
    mommy.make("Aluno", periodo_escolar=periodo_manha, escola=escola_cei)
    return solicitacao_medicao


@pytest.fixture
def solicitacao_medicao_inicial_valores_cei(escola_cei, categoria_medicao):
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_integral = mommy.make("PeriodoEscolar", nome="INTEGRAL")
    periodo_manha = mommy.make("PeriodoEscolar", nome="MANHA")
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial",
        mes=4,
        ano=2023,
        escola=escola_cei,
        ue_possui_alunos_periodo_parcial=True,
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_manha = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
    )
    medicao_integral = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_integral,
    )
    faixa_etaria = mommy.make(
        "FaixaEtaria", inicio=1, fim=10, uuid="0c914b27-c7cd-4682-a439-a4874745b005"
    )
    mommy.make("Aluno", periodo_escolar=periodo_manha, escola=escola_cei)
    mommy.make(
        "ValorMedicao",
        dia="01",
        semana="1",
        nome_campo="frequencia",
        medicao=medicao_manha,
        categoria_medicao=categoria_medicao,
        valor="10",
        faixa_etaria=faixa_etaria,
    )
    mommy.make(
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
        tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
        solicitacao_medicao = mommy.make(
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
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_manha = mommy.make("PeriodoEscolar", nome="MANHA")
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
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial",
        uuid="bed4d779-2d57-4c5f-bf9c-9b93ddac54d9",
        mes=12,
        ano=2022,
        escola=escola,
        rastro_lote=escola.lote,
        historico=json.dumps([historico]),
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
    )
    mommy.make(
        "AlunoPeriodoParcial",
        solicitacao_medicao_inicial=solicitacao_medicao,
        aluno=aluno,
        data=datetime.date(2022, 12, 1),
    )
    mommy.make(
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
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_manha = mommy.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = mommy.make("PeriodoEscolar", nome="TARDE")
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial", mes=12, ano=2022, escola=escola
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
    )
    medicao_programas_projetos = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_tarde,
    )
    categoria_dieta_a = mommy.make(
        "CategoriaMedicao", nome="DIETA ESPECIAL - TIPO A ENTERAL"
    )
    categoria_dieta_b = mommy.make("CategoriaMedicao", nome="DIETA ESPECIAL - TIPO B")
    for dia in ["01", "02", "03", "04", "05"]:
        for campo in ["lanche", "refeicao", "lanche_emergencial", "sobremesa"]:
            for categoria in [categoria_medicao, categoria_dieta_a, categoria_dieta_b]:
                for medicao_ in [medicao, medicao_programas_projetos]:
                    mommy.make(
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
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_manha = mommy.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = mommy.make("PeriodoEscolar", nome="TARDE")
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial",
        mes=12,
        ano=2023,
        escola=escola_emebs,
        uuid="da921e20-50f9-41ae-b2dc-4311d47029e8",
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_manha = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
    )
    medicao_tarde = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_tarde,
    )
    categoria_dieta_a = mommy.make(
        "CategoriaMedicao", nome="DIETA ESPECIAL - TIPO A ENTERAL"
    )
    categoria_dieta_b = mommy.make("CategoriaMedicao", nome="DIETA ESPECIAL - TIPO B")
    tipos_turmas = ["INFANTIL", "FUNDAMENTAL"]

    for dia in range(1, 15):
        mommy.make(
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
                        mommy.make(
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
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_manha = mommy.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = mommy.make("PeriodoEscolar", nome="TARDE")
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial",
        mes=12,
        ano=2023,
        escola=escola_ceu_gestao,
        uuid="416a47af-6022-4866-989f-9707b2213bfc",
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_manha = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
    )
    categoria_dieta_a = mommy.make("CategoriaMedicao", nome="DIETA ESPECIAL - TIPO A")
    categoria_dieta_b = mommy.make("CategoriaMedicao", nome="DIETA ESPECIAL - TIPO B")
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
                    mommy.make(
                        "ValorMedicao",
                        dia=dia,
                        nome_campo=campo,
                        medicao=medicao_,
                        categoria_medicao=categoria,
                        valor="10",
                    )
    grupo_inclusao_normal = mommy.make(
        "GrupoInclusaoAlimentacaoNormal",
        status="CODAE_AUTORIZADO",
        rastro_escola=escola_ceu_gestao,
        escola=escola_ceu_gestao,
    )

    mommy.make(
        "InclusaoAlimentacaoNormal",
        grupo_inclusao=grupo_inclusao_normal,
        data=datetime.date(2023, 12, 5),
    )

    qp_manha = mommy.make(
        "QuantidadePorPeriodo",
        grupo_inclusao_normal=grupo_inclusao_normal,
        numero_alunos=15,
        periodo_escolar=periodo_manha,
    )
    qp_manha.tipos_alimentacao.add(tipo_alimentacao_refeicao, tipo_alimentacao_lanche)
    qp_manha.save()

    qp_tarde = mommy.make(
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
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_integral = mommy.make("PeriodoEscolar", nome="INTEGRAL")
    periodo_parcial = mommy.make("PeriodoEscolar", nome="PARCIAL")
    periodo_tarde = mommy.make("PeriodoEscolar", nome="TARDE")
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial", mes=12, ano=2022, escola=escola_cei
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_integral = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_integral,
    )
    medicao_parcial = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_parcial,
    )
    medicao_tarde = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_tarde,
    )
    categoria_dieta_a = mommy.make(
        "CategoriaMedicao", nome="DIETA ESPECIAL - TIPO A ENTERAL"
    )
    for dia in ["01", "02", "03", "04"]:
        for categoria in [categoria_medicao, categoria_dieta_a]:
            valores = ["5", "9", "13"]
            for index, medicao_ in enumerate(
                [medicao_integral, medicao_parcial, medicao_tarde]
            ):
                mommy.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo="frequencia",
                    medicao=medicao_,
                    categoria_medicao=categoria,
                    valor=valores[index],
                )
    return solicitacao_medicao


def medicao_infantil_manha(solicitacao_medicao, categoria_medicao):
    periodo_infantil_manha = mommy.make("PeriodoEscolar", nome="Infantil MANHA")
    medicao_infantil_manha = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_infantil_manha,
    )
    categoria_dieta_a = mommy.make(
        "CategoriaMedicao", nome="DIETA ESPECIAL - TIPO A ENTERAL"
    )
    for dia in ["01", "02"]:
        for campo in ["lanche", "refeicao", "lanche_emergencial", "sobremesa"]:
            for categoria in [categoria_medicao, categoria_dieta_a]:
                mommy.make(
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
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_integral = mommy.make("PeriodoEscolar", nome="INTEGRAL")
    periodo_parcial = mommy.make("PeriodoEscolar", nome="PARCIAL")
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial", mes=12, ano=2022, escola=escola_cemei
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_integral = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_integral,
    )
    medicao_parcial = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_parcial,
    )
    categoria_dieta_a = mommy.make(
        "CategoriaMedicao", nome="DIETA ESPECIAL - TIPO A ENTERAL"
    )
    for dia in ["01", "02", "03"]:
        for categoria in [categoria_medicao, categoria_dieta_a]:
            valores = ["10", "20"]
            for index, medicao_ in enumerate([medicao_integral, medicao_parcial]):
                mommy.make(
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
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_manha = mommy.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = mommy.make("PeriodoEscolar", nome="TARDE")
    periodo_integral = mommy.make("PeriodoEscolar", nome="INTEGRAL")
    periodo_noite = mommy.make("PeriodoEscolar", nome="NOITE")
    grupo_solicitacoes_alimentacao = mommy.make(
        "GrupoMedicao", nome="Solicitações de Alimentação"
    )
    grupo_programas_e_projetos = mommy.make("GrupoMedicao", nome="Programas e Projetos")
    grupo_etec = mommy.make("GrupoMedicao", nome="ETEC")
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial", mes=4, ano=2023, escola=escola
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_manha = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
    )
    medicao_tarde = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_tarde,
    )
    medicao_integral = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_integral,
    )
    medicao_noite = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_noite,
    )
    medicao_solicitacoes_alimentacao = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        grupo=grupo_solicitacoes_alimentacao,
    )
    medicao_programas_e_projetos = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        grupo=grupo_programas_e_projetos,
    )
    medicao_etec = mommy.make(
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
                mommy.make(
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
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_manha = mommy.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = mommy.make("PeriodoEscolar", nome="TARDE")
    periodo_integral = mommy.make("PeriodoEscolar", nome="INTEGRAL")
    periodo_noite = mommy.make("PeriodoEscolar", nome="NOITE")
    grupo_programas_e_projetos = mommy.make("GrupoMedicao", nome="Programas e Projetos")
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial", mes=4, ano=2023, escola=escola
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_manha = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
    )
    medicao_tarde = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_tarde,
    )
    medicao_integral = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_integral,
    )
    medicao_noite = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_noite,
    )
    medicao_programas_e_projetos = mommy.make(
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
                    mommy.make(
                        "ValorMedicao",
                        dia=dia,
                        nome_campo=campo,
                        medicao=medicao_,
                        categoria_medicao=categoria,
                        valor="10",
                    )
        mommy.make(
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
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    categoria = mommy.make("CategoriaMedicao", nome="SOLICITAÇÕES DE ALIMENTAÇÃO")
    grupo = mommy.make("GrupoMedicao", nome="Solicitações de Alimentação")
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial", mes=6, ano=2023, escola=escola
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_solicitacoes_alimentacao = mommy.make(
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
            mommy.make(
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
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    categoria = mommy.make("CategoriaMedicao", nome="ALIMENTAÇÃO")
    periodo_escolar = mommy.make("PeriodoEscolar", nome="INTEGRAL")
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial", mes=11, ano=2023, escola=escola
    )
    faixa_etaria = mommy.make("FaixaEtaria", inicio=1, fim=3)
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao_solicitacoes_alimentacao = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_escolar,
        grupo=None,
    )
    for dia in ["01", "02", "03", "04", "05"]:
        mommy.make(
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
    return mommy.make("PeriodoEscolar", nome="MANHA")


@pytest.fixture
def periodo_escolar_tarde():
    return mommy.make("PeriodoEscolar", nome="TARDE")


@pytest.fixture
def periodo_escolar_noite():
    return mommy.make("PeriodoEscolar", nome="NOITE")


@pytest.fixture
def categoria_alimentacoes():
    return mommy.make("Cate")


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
    grupo_inclusao_normal = mommy.make(
        "GrupoInclusaoAlimentacaoNormal",
        status="CODAE_AUTORIZADO",
        rastro_escola=escola,
        escola=escola,
    )

    mommy.make(
        "InclusaoAlimentacaoNormal",
        grupo_inclusao=grupo_inclusao_normal,
        data=datetime.date(2023, 9, 3),
    )

    qp = mommy.make(
        "QuantidadePorPeriodo",
        grupo_inclusao_normal=grupo_inclusao_normal,
        numero_alunos=100,
        periodo_escolar=periodo_escolar_manha,
    )
    qp.tipos_alimentacao.add(tipo_alimentacao_refeicao)
    qp.save()

    inclusao_continua_programas_projetos = mommy.make(
        "InclusaoAlimentacaoContinua",
        escola=escola,
        rastro_escola=escola,
        data_inicial=datetime.date(2023, 9, 1),
        data_final=datetime.date(2023, 9, 30),
        motivo=motivo_inclusao_continua_programas_projetos,
        status="CODAE_AUTORIZADO",
    )

    inclusao_continua_etec = mommy.make(
        "InclusaoAlimentacaoContinua",
        escola=escola,
        rastro_escola=escola,
        data_inicial=datetime.date(2023, 8, 15),
        data_final=datetime.date(2023, 9, 15),
        motivo=motivo_inclusao_continua_etec,
        status="CODAE_AUTORIZADO",
    )

    solicitacao_kit_lanche = mommy.make(
        "SolicitacaoKitLanche",
        data=datetime.date(2023, 9, 12),
        tempo_passeio=TempoPasseio.OITO_OU_MAIS,
    )
    solicitacao_kit_lanche.kits.add(kit_lanche_1)
    solicitacao_kit_lanche.kits.add(kit_lanche_2)
    solicitacao_kit_lanche.save()

    mommy.make(
        "SolicitacaoKitLancheAvulsa",
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        status="CODAE_AUTORIZADO",
        escola=escola,
        quantidade_alunos=100,
    )

    solicitacao_unificada = mommy.make(
        "SolicitacaoKitLancheUnificada",
        status="CODAE_AUTORIZADO",
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        diretoria_regional=escola.lote.diretoria_regional,
        lista_kit_lanche_igual=False,
    )
    eq = mommy.make(
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
        qp = mommy.make(
            "QuantidadePorPeriodo",
            inclusao_alimentacao_continua=inclusao_continua_programas_projetos,
            periodo_escolar=periodo,
            numero_alunos=10,
            dias_semana=[0, 1, 2, 3, 4, 5, 6],
        )
        qp.tipos_alimentacao.add(tipo_alimentacao_refeicao)
        qp.tipos_alimentacao.add(tipo_alimentacao_lanche)
        qp.save()

        qp = mommy.make(
            "QuantidadePorPeriodo",
            inclusao_alimentacao_continua=inclusao_continua_etec,
            periodo_escolar=periodo,
            numero_alunos=10,
            dias_semana=[0, 1, 2, 3, 4, 5, 6],
        )
        qp.tipos_alimentacao.add(tipo_alimentacao_refeicao)
        qp.tipos_alimentacao.add(tipo_alimentacao_lanche)
        qp.save()

        mommy.make(
            "AlunosMatriculadosPeriodoEscola",
            escola=escola,
            periodo_escolar=periodo,
            quantidade_alunos=100,
        )

        vinculo_alimentacao = mommy.make(
            "VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
            tipo_unidade_escolar=escola.tipo_unidade,
            periodo_escolar=periodo,
        )
        vinculo_alimentacao.tipos_alimentacao.add(tipo_alimentacao_refeicao)
        vinculo_alimentacao.tipos_alimentacao.add(tipo_alimentacao_lanche)
        vinculo_alimentacao.save()

        mommy.make("Aluno", escola=escola, periodo_escolar=periodo)

        for dia in range(1, 31):
            data = datetime.date(2023, 9, dia)
            log = mommy.make(
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
                    mommy.make(
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
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial",
        uuid="bed4d779-2d57-4c5f-bf9c-9b93ddac54d9",
        mes="09",
        ano=2023,
        escola=escola_com_logs_para_medicao,
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem_alimentacao])

    mommy.make(
        "LogAlunosMatriculadosPeriodoEscola",
        escola=escola_com_logs_para_medicao,
        criado_em=datetime.date(2023, 9, 1),
        periodo_escolar=periodo_escolar_manha,
        quantidade_alunos=10,
    )

    mommy.make(
        "LogAlunosMatriculadosPeriodoEscola",
        escola=escola_com_logs_para_medicao,
        criado_em=datetime.date(2023, 9, 1),
        periodo_escolar=periodo_escolar_tarde,
        quantidade_alunos=10,
    )

    mommy.make(
        "LogAlunosMatriculadosPeriodoEscola",
        escola=escola_com_logs_para_medicao,
        criado_em=datetime.date(2023, 9, 1),
        periodo_escolar=periodo_escolar_noite,
        quantidade_alunos=10,
    )

    medicao_manha = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_escolar_manha,
    )
    mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_escolar_tarde,
    )
    mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_escolar_noite,
    )
    medicao_programas_projetos = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        grupo=grupo_programas_e_projetos,
    )
    medicao_etec = mommy.make(
        "Medicao", solicitacao_medicao_inicial=solicitacao_medicao, grupo=grupo_etec
    )
    mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        grupo=grupo_solicitacoes_alimentacao,
    )
    for dia in range(1, 31):
        mommy.make(
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
                mommy.make(
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
            mommy.make(
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
        mommy.make("FaixaEtaria", inicio=inicio, fim=fim, ativo=True)
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
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial",
        uuid="7f7c79ec-bb92-11ee-ad73-5f84fbd2a2f0",
        mes="10",
        ano=2023,
        escola=escola_cei,
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem_alimentacao])
    solicitacao_medicao.ue_possui_alunos_periodo_parcial = True
    solicitacao_medicao.save()

    periodo_integral = mommy.make("PeriodoEscolar", nome="INTEGRAL")
    periodo_parcial = mommy.make("PeriodoEscolar", nome="PARCIAL")
    periodo_tarde = mommy.make("PeriodoEscolar", nome="TARDE")

    mommy.make("Aluno", serie="1", escola=escola_cei, periodo_escolar=periodo_integral)
    mommy.make("Aluno", serie="2", escola=escola_cei, periodo_escolar=periodo_tarde)

    for periodo in [periodo_integral, periodo_parcial, periodo_tarde]:
        for dia in range(1, 32):
            log = mommy.make(
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
                mommy.make(
                    "LogQuantidadeDietasAutorizadasCEI",
                    escola=escola_cei,
                    periodo_escolar=periodo,
                    faixa_etaria=faixas_etarias_ativas[2],
                    quantidade=2,
                    data=datetime.date(2023, 10, dia),
                    classificacao=classificacao,
                )
                mommy.make(
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
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_manha = mommy.make("PeriodoEscolar", nome="MANHA")
    grupo = mommy.make("GrupoMedicao", nome="Programas e Projetos")
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial",
        uuid="bed4d779-2d57-4c5f-bf9c-9b93ddac54d9",
        mes=12,
        ano=2022,
        escola=escola,
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
        grupo=grupo,
    )
    mommy.make(
        "ValorMedicao",
        categoria_medicao=categoria_medicao_dieta_a,
        medicao=medicao,
        nome_campo="frequencia",
        valor="10",
    )
    return solicitacao_medicao


@pytest.fixture
def solicitacoes_medicao_inicial(escola):
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    escola_2 = mommy.make("Escola")
    s1 = mommy.make(
        "SolicitacaoMedicaoInicial",
        mes=6,
        ano=2022,
        escola=escola,
        status="MEDICAO_ENVIADA_PELA_UE",
    )
    s1.tipos_contagem_alimentacao.set([tipo_contagem])

    s2 = mommy.make(
        "SolicitacaoMedicaoInicial",
        mes=1,
        ano=2023,
        escola=escola,
        status="MEDICAO_ENVIADA_PELA_UE",
    )
    s2.tipos_contagem_alimentacao.set([tipo_contagem])

    s3 = mommy.make(
        "SolicitacaoMedicaoInicial",
        mes=2,
        ano=2023,
        escola=escola,
        status="MEDICAO_CORRECAO_SOLICITADA",
    )
    s3.tipos_contagem_alimentacao.set([tipo_contagem])

    s4 = mommy.make(
        "SolicitacaoMedicaoInicial",
        mes=2,
        ano=2023,
        escola=escola_2,
        status="MEDICAO_CORRECAO_SOLICITADA",
    )
    s4.tipos_contagem_alimentacao.set([tipo_contagem])

    s5 = mommy.make(
        "SolicitacaoMedicaoInicial",
        mes=3,
        ano=2023,
        escola=escola,
        status="MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE",
    )
    s5.tipos_contagem_alimentacao.set([tipo_contagem])

    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=s1.uuid,
        status_evento=55,  # MEDICAO_ENVIADA_PELA_UE
        solicitacao_tipo=16,
    )  # MEDICAO_INICIAL
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=s2.uuid,
        status_evento=55,  # MEDICAO_ENVIADA_PELA_UE
        solicitacao_tipo=16,
    )  # MEDICAO_INICIAL
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=s3.uuid,
        status_evento=64,  # MEDICAO_CORRECAO_SOLICITADA
        solicitacao_tipo=16,
    )  # MEDICAO_INICIAL
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=s4.uuid,
        status_evento=64,  # MEDICAO_CORRECAO_SOLICITADA
        solicitacao_tipo=16,
    )  # MEDICAO_INICIAL
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=s5.uuid,
        status_evento=54,  # MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        solicitacao_tipo=16,
    )  # MEDICAO_INICIAL


@pytest.fixture
def solicitacoes_medicao_inicial_codae(escola):
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    s1 = mommy.make(
        "SolicitacaoMedicaoInicial",
        mes=4,
        ano=2022,
        escola=escola,
        status="MEDICAO_APROVADA_PELA_DRE",
    )
    s1.tipos_contagem_alimentacao.set([tipo_contagem])

    s2 = mommy.make(
        "SolicitacaoMedicaoInicial",
        mes=7,
        ano=2023,
        escola=escola,
        status="MEDICAO_APROVADA_PELA_DRE",
    )
    s2.tipos_contagem_alimentacao.set([tipo_contagem])

    s3 = mommy.make(
        "SolicitacaoMedicaoInicial",
        mes=2,
        ano=2023,
        escola=escola,
        status="MEDICAO_CORRECAO_SOLICITADA_CODAE",
    )
    s3.tipos_contagem_alimentacao.set([tipo_contagem])

    s4 = mommy.make(
        "SolicitacaoMedicaoInicial",
        mes=12,
        ano=2023,
        escola=escola,
        status="MEDICAO_CORRIGIDA_PARA_CODAE",
    )
    s4.tipos_contagem_alimentacao.set([tipo_contagem])

    s5 = mommy.make(
        "SolicitacaoMedicaoInicial",
        mes=3,
        ano=2023,
        escola=escola,
        status="MEDICAO_APROVADA_PELA_CODAE",
    )
    s5.tipos_contagem_alimentacao.set([tipo_contagem])

    s6 = mommy.make(
        "SolicitacaoMedicaoInicial",
        mes=2,
        ano=2024,
        escola=escola,
        status="MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE",
    )
    s6.tipos_contagem_alimentacao.set([tipo_contagem])

    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=s1.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_DRE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
    )
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=s2.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_DRE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
    )
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=s3.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA_CODAE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
    )
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=s4.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_CORRIGIDA_PARA_CODAE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
    )
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=s5.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
    )
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=s6.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
    )


@pytest.fixture
def solicitacao_medicao_inicial_sem_arquivo(escola):
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas COloridas")
    solicitacao_medicao = mommy.make(
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
    parametrizacao_financeira = mommy.make(
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

    parametrizacao_financeira_tabela = mommy.make(
        "ParametrizacaoFinanceiraTabela",
        parametrizacao_financeira=parametrizacao_financeira,
        nome="Preço das Alimentações",
    )
    mommy.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela,
        tipo_alimentacao=tipo_alimentacao_refeicao,
        grupo="EMEF / CEUEMEF / EMEFM",
        valor_colunas={
            "valor_unitario": 2,
            "valor_unitario_reajuste": 3,
        },
    )
    mommy.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela,
        tipo_alimentacao=tipo_alimentacao_refeicao,
        grupo="CIEJA / EJA",
        valor_colunas={
            "valor_unitario": 8,
            "valor_unitario_reajuste": 5,
        },
    )
    mommy.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela,
        tipo_alimentacao=tipo_alimentacao_almoco,
        valor_colunas={
            "valor_unitario": 5,
            "valor_unitario_reajuste": 2,
        },
    )
    mommy.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela,
        tipo_alimentacao=tipo_alimentacao_lanche,
        valor_colunas={
            "valor_unitario": 7,
            "valor_unitario_reajuste": 5,
        },
    )
    mommy.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela,
        tipo_alimentacao=tipo_alimentacao_lanche_4h,
        valor_colunas={
            "valor_unitario": 4,
            "valor_unitario_reajuste": 2,
        },
    )
    mommy.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela,
        tipo_alimentacao=tipo_alimentacao_sobremesa,
        valor_colunas={
            "valor_unitario": 8,
            "valor_unitario_reajuste": 6,
        },
    )
    mommy.make(
        "ParametrizacaoFinanceiraTabelaValor",
        tabela=parametrizacao_financeira_tabela,
        tipo_alimentacao=tipo_alimentacao_lanche_emergencial,
        valor_colunas={
            "valor_unitario": 12,
            "valor_unitario_reajuste": 10,
        },
    )

    parametrizacao_financeira_tabela_dietas_a = mommy.make(
        "ParametrizacaoFinanceiraTabela",
        parametrizacao_financeira=parametrizacao_financeira,
        nome="Dietas Tipo A e Tipo A Enteral",
    )
    mommy.make(
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
    mommy.make(
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
    mommy.make(
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

    parametrizacao_financeira_tabela_dietas_b = mommy.make(
        "ParametrizacaoFinanceiraTabela",
        parametrizacao_financeira=parametrizacao_financeira,
        nome="Dietas Tipo B",
    )
    mommy.make(
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
    mommy.make(
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
    return mommy.make(
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
    mommy.make(
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
    usuario_escola = mommy.make(
        "Usuario", nome="TESTE DA SILVA", cargo="DIRETOR DE ESCOLA"
    )
    perfil_diretor = mommy.make("Perfil", nome="DIRETOR_UE", ativo=True)
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=usuario_escola,
        instituicao=solicitacao_medicao_inicial.escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    usuario_dre = mommy.make(
        "Usuario", nome="TESTE DA SILVA", cargo="DIRETOR DE ESCOLA"
    )
    perfil_cogestor = mommy.make("Perfil", nome="COGESTOR_DRE", ativo=True)
    mommy.make(
        "Vinculo",
        usuario=usuario_dre,
        instituicao=solicitacao_medicao_inicial.escola.lote.diretoria_regional,
        perfil=perfil_cogestor,
        data_inicial=hoje,
        ativo=True,
    )
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=solicitacao_medicao_inicial.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_ENVIADA_PELA_UE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
        usuario=usuario_escola,
    )
    mommy.make(
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
    return mommy.make(
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
    solicitacao_medicao = mommy.make("SolicitacaoMedicaoInicial", escola=escola)
    return mommy.make(
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
    solicitacao_medicao = mommy.make("SolicitacaoMedicaoInicial")
    return mommy.make(
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
    solicitacao = mommy.make(
        "SolicitacaoMedicaoInicial",
        escola=escola,
        status="MEDICAO_CORRECAO_SOLICITADA",
        uuid="d9de8653-4910-423e-9381-e391c2ae8ecb",
        com_ocorrencias=True,
    )
    mommy.make(
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
    solicitacao = mommy.make(
        "SolicitacaoMedicaoInicial",
        escola=escola,
        status="MEDICAO_CORRECAO_SOLICITADA_CODAE",
        uuid="d9de8653-4910-423e-9381-e391c2ae8ecb",
        com_ocorrencias=True,
    )
    mommy.make(
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
    return mommy.make(
        "medicao_inicial.Responsavel",
        nome=nome,
        rf=rf,
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
    )


@pytest.fixture
def tipo_contagem_alimentacao():
    return mommy.make("TipoContagemAlimentacao", nome="Fichas")


@pytest.fixture
def periodo_escolar():
    return mommy.make("PeriodoEscolar", nome="INTEGRAL")


@pytest.fixture
def medicao(solicitacao_medicao_inicial, periodo_escolar):
    return mommy.make(
        "Medicao",
        periodo_escolar=periodo_escolar,
        uuid="5a3a3941-1b91-4b9f-b410-c3547e224eb5",
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
    )


@pytest.fixture
def medicao_status_inicial(
    solicitacao_medicao_inicial, periodo_escolar, categoria_medicao
):
    medicao = mommy.make(
        "Medicao",
        periodo_escolar=periodo_escolar,
        uuid="7041e451-43a7-4d2f-abc6-d0960121d2fb",
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
        status="MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE",
    )
    valor = 10
    nome_campo = "observacoes"
    tipo_alimentacao = mommy.make(
        "TipoAlimentacao", nome="Lanche", uuid="0367af8d-26bd-40b5-83d2-9e337622ba50"
    )
    mommy.make(
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
    medicao = mommy.make(
        "Medicao",
        periodo_escolar=periodo_escolar,
        uuid="cbe62cc7-55e9-435d-8c3f-845b6fa20c2e",
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
        status="MEDICAO_ENVIADA_PELA_UE",
    )
    valor = 10
    nome_campo = "observacoes"
    tipo_alimentacao = mommy.make(
        "TipoAlimentacao", nome="Lanche", uuid="837ed21a-d535-4df2-aa37-f186e4e51392"
    )
    mommy.make(
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
    medicao = mommy.make(
        "Medicao",
        periodo_escolar=periodo_escolar,
        uuid="65f112a5-8b4b-495b-a29e-1d75fb0b5eeb",
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
        status="MEDICAO_APROVADA_PELA_DRE",
    )
    valor = 20
    nome_campo = "observacoes"
    tipo_alimentacao = mommy.make(
        "TipoAlimentacao", nome="Lanche", uuid="a5ea11b6-a043-47cd-ba69-d6b207312cbd"
    )
    mommy.make(
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
    return mommy.make(
        "CategoriaMedicao", nome="ALIMENTAÇÃO", id=random.randint(1, 10000)
    )


@pytest.fixture
def categoria_medicao_dieta_a():
    return mommy.make("CategoriaMedicao", nome="DIETA ESPECIAL - TIPO A")


@pytest.fixture
def categoria_medicao_dieta_a_enteral_aminoacidos():
    return mommy.make(
        "CategoriaMedicao",
        nome="DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS",
    )


@pytest.fixture
def categoria_medicao_dieta_b():
    return mommy.make("CategoriaMedicao", nome="DIETA ESPECIAL - TIPO B")


@pytest.fixture
def categoria_medicao_solicitacoes_alimentacao():
    return mommy.make("CategoriaMedicao", nome="SOLICITAÇÕES DE ALIMENTAÇÃO")


@pytest.fixture
def valor_medicao(medicao, categoria_medicao):
    valor = 13
    nome_campo = "observacoes"
    tipo_alimentacao = mommy.make(
        "TipoAlimentacao", nome="Lanche", uuid="b58b7946-67c4-416c-82cf-f26a470fb93e"
    )
    return mommy.make(
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
    perfil_cogestor = mommy.make("Perfil", nome="COGESTOR_DRE", ativo=True)
    hoje = datetime.date.today()
    mommy.make(
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
    perfil_diretor = mommy.make("Perfil", nome="DIRETOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="123456"
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
def client_autenticado_da_escola_cei(client, django_user_model, escola_cei):
    email = "user@escola_cei.com"
    password = "admin@123"
    perfil_diretor = mommy.make("Perfil", nome="DIRETOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="123456"
    )
    hoje = datetime.date.today()
    mommy.make(
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
    perfil_diretor = mommy.make("Perfil", nome="DIRETOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="123456"
    )
    hoje = datetime.date.today()
    mommy.make(
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
    perfil_diretor = mommy.make("Perfil", nome="DIRETOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="123456"
    )
    hoje = datetime.date.today()
    mommy.make(
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
    perfil_diretor = mommy.make("Perfil", nome="DIRETOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="123456"
    )
    hoje = datetime.date.today()
    mommy.make(
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
    perfil_diretor = mommy.make("Perfil", nome="ADMINISTRADOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="1234567"
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
def client_autenticado_codae_medicao(client, django_user_model):
    email = "codae@medicao.com"
    password = "admin@1234"
    perfil_medicao = mommy.make("Perfil", nome="ADMINISTRADOR_MEDICAO", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="1234588"
    )
    codae = mommy.make("Codae")
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=usuario,
        instituicao=codae,
        perfil=perfil_medicao,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def dia_para_corrigir(categoria_medicao, medicao):
    return mommy.make(
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
    usuario = mommy.make("Usuario", email="admin2@admin.com", is_superuser=True)
    periodo_manha = mommy.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = mommy.make("PeriodoEscolar", nome="TARDE")
    alimentacoes = alimentacoes_lancamentos_especiais
    mommy.make(
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
    mommy.make(
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
    mommy.make(
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
    periodo_manha = mommy.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = mommy.make("PeriodoEscolar", nome="TARDE")
    for quantidade in quantidades:
        mommy.make(
            LogAlunosMatriculadosPeriodoEscola,
            escola=escola_cemei,
            periodo_escolar=periodo_manha,
            quantidade_alunos=quantidade,
            tipo_turma=TipoTurma.REGULAR.name,
        )
    mommy.make(
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
    grupo_escolar = mommy.make(
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
    diretoria_regional = mommy.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL IPIRANGA",
        uuid="3972e0e9-2d8e-472a-9dfa-30cd219a6d9a",
    )
    return diretoria_regional


@pytest.fixture
def edital():
    edital = mommy.make(
        "terceirizada.Edital",
        numero="Edital de Pregão nº 78/SME/2024",
        uuid="f76f367c-f9c4-463e-aefb-0ff434d93ae9",
    )
    return edital


@pytest.fixture
def contrato(edital):
    terceirizada = mommy.make("terceirizada.Terceirizada")
    lote = mommy.make("escola.Lote", terceirizada=terceirizada)
    contrato = mommy.make(
        "terceirizada.Contrato",
        lotes=[lote],
        edital=edital,
        numero="Contrato 78/SME/2024",
        uuid="13cb1ff3-a2c8-47ad-a17f-145b38f72ef0",
    )
    return contrato


@pytest.fixture
def empenho(edital, contrato):
    empenho = mommy.make(
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
    return mommy.make(
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
        mommy.make(
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
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial", mes=4, ano=2023, escola=escola_cemei
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])

    return solicitacao_medicao


@pytest.fixture
def make_dia_letivo():
    def handle(dia: int, mes: int, ano: int, escola: Escola):
        data = datetime.datetime(ano, mes, dia).date()
        return mommy.make(DiaCalendario, escola=escola, data=data, dia_letivo=True)

    return handle


@pytest.fixture
def make_periodo_escolar():
    def handle(nome: str):
        if PeriodoEscolar.objects.filter(nome=nome).exists():
            return PeriodoEscolar.objects.get(nome=nome)
        return mommy.make("PeriodoEscolar", nome=nome)

    return handle


@pytest.fixture
def make_medicao():
    def handle(solicitacao: SolicitacaoMedicaoInicial, periodo_escolar: PeriodoEscolar):
        return mommy.make(
            "Medicao",
            solicitacao_medicao_inicial=solicitacao,
            periodo_escolar=periodo_escolar,
        )

    return handle


@pytest.fixture
def make_valor_medicao_faixa_etaria(categoria_medicao, faixa_etaria):
    def handle(medicao: Medicao, valor: str, dia: int):
        return mommy.make(
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
        return mommy.make("ValorMedicao", **kwargs)

    return handle


@pytest.fixture
def usuario(django_user_model):
    return mommy.make(django_user_model)


@pytest.fixture
def periodos_integral_parcial_e_logs(escola, faixas_etarias_ativas):
    periodo_integral = mommy.make("PeriodoEscolar", nome="INTEGRAL")
    periodo_parcial = mommy.make("PeriodoEscolar", nome="PARCIAL")

    for periodo in [periodo_integral, periodo_parcial]:
        for dia in range(1, 5):
            mommy.make(
                "LogAlunosMatriculadosFaixaEtariaDia",
                escola=escola,
                periodo_escolar=periodo,
                faixa_etaria=faixas_etarias_ativas[len(faixas_etarias_ativas) - 1],
                quantidade=2,
                data=datetime.date(2022, 12, dia),
            )


@pytest.fixture
def solicitacao_relatorio_consolidado(escola):
    return mommy.make(
        "SolicitacaoMedicaoInicial",
        escola=escola,
        mes="04",
        ano="2025",
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
    )


@pytest.fixture
def medicao_grupo_solicitacao_alimentacao(
    solicitacao_relatorio_consolidado, grupo_solicitacoes_alimentacao
):
    return mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado,
        periodo_escolar=None,
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
        grupo=grupo_solicitacoes_alimentacao,
    )


@pytest.fixture
def medicao_grupo_alimentacao(solicitacao_relatorio_consolidado, periodo_escolar_manha):
    return mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_relatorio_consolidado,
        periodo_escolar=periodo_escolar_manha,
        status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
        grupo=None,
    )


@pytest.fixture
def mock_relatorio_consolidado_xlsx(
    solicitacao_relatorio_consolidado,
    medicao_grupo_alimentacao,
    categoria_medicao,
    categoria_medicao_dieta_a,
    categoria_medicao_dieta_b,
    medicao_grupo_solicitacao_alimentacao,
    categoria_medicao_solicitacoes_alimentacao,
):
    for dia in ["01", "02", "03", "04", "05"]:
        for campo in ["lanche", "lanche_4h", "refeicao", "sobremesa"]:
            for categoria in [
                categoria_medicao,
                categoria_medicao_dieta_a,
                categoria_medicao_dieta_b,
            ]:
                mommy.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo=campo,
                    medicao=medicao_grupo_alimentacao,
                    categoria_medicao=categoria,
                    valor="25",
                )
        if dia == "05":
            for campo in ["kit_lanche", "lanche_emergencial"]:
                mommy.make(
                    "ValorMedicao",
                    dia=dia,
                    nome_campo=campo,
                    medicao=medicao_grupo_solicitacao_alimentacao,
                    categoria_medicao=categoria_medicao_solicitacoes_alimentacao,
                    valor="10",
                )

        mommy.make(
            "ValorMedicao",
            dia=dia,
            nome_campo="matriculados",
            medicao=medicao_grupo_alimentacao,
            categoria_medicao=categoria_medicao,
            valor="100",
        )
        mommy.make(
            "ValorMedicao",
            dia=dia,
            nome_campo="frequencia",
            medicao=medicao_grupo_alimentacao,
            categoria_medicao=categoria_medicao,
            valor="90",
        )

    return solicitacao_relatorio_consolidado


@pytest.fixture
def mock_query_params_excel(solicitacao_relatorio_consolidado, grupo_escolar):
    return {
        "dre": solicitacao_relatorio_consolidado.escola.diretoria_regional.uuid,
        "status": "MEDICAO_APROVADA_PELA_CODAE",
        "grupo_escolar": grupo_escolar,
        "mes": solicitacao_relatorio_consolidado.mes,
        "ano": solicitacao_relatorio_consolidado.ano,
        "lotes[]": solicitacao_relatorio_consolidado.escola.lote.uuid,
        "lotes": [solicitacao_relatorio_consolidado.escola.lote.uuid],
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
        ("DIETA ESPECIAL - TIPO A", "sobremesa"),
        ("DIETA ESPECIAL - TIPO B", "lanche"),
        ("DIETA ESPECIAL - TIPO B", "lanche_4h"),
        ("DIETA ESPECIAL - TIPO B", "refeicao"),
        ("DIETA ESPECIAL - TIPO B", "sobremesa"),
    ]


@pytest.fixture
def mock_linhas():
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
            125.0,
            125.0,
            125.0,
            125.0,
            125.0,
            125.0,
            125.0,
            125.0,
        ]
    ]


@pytest.fixture
def informacoes_excel_writer(
    mock_relatorio_consolidado_xlsx, mock_colunas, mock_linhas
):
    arquivo = BytesIO()
    aba = f"Relatório Consolidado {mock_relatorio_consolidado_xlsx.mes}-{ mock_relatorio_consolidado_xlsx.ano}"
    writer = pd.ExcelWriter(arquivo, engine="xlsxwriter")
    workbook = writer.book
    worksheet = workbook.add_worksheet(aba)
    worksheet.set_default_row(20)
    df = _insere_tabela_periodos_na_planilha(aba, mock_colunas, mock_linhas, writer)
    try:
        yield aba, writer, workbook, worksheet, df, arquivo
    finally:
        workbook.close()
        writer.close()
