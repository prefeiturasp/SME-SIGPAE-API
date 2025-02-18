import datetime
from collections import Counter

import pytest
from django.contrib import admin
from freezegun import freeze_time

from ...cardapio.models import Cardapio
from ...dados_comuns.constants import DAQUI_A_SETE_DIAS, DAQUI_A_TRINTA_DIAS, SEM_FILTRO
from ..admin import PlanilhaAtualizacaoTipoGestaoEscolaAdmin
from ..models import (
    AlunosMatriculadosPeriodoEscola,
    DiaCalendario,
    DiretoriaRegional,
    FaixaEtaria,
    LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar,
    LogAlunosMatriculadosFaixaEtariaDia,
    LogAlunosMatriculadosPeriodoEscola,
    LogAtualizaDadosAluno,
    LogRotinaDiariaAlunos,
    PlanilhaAtualizacaoTipoGestaoEscola,
    PlanilhaEscolaDeParaCodigoEolCodigoCoade,
    TipoGestao,
    TipoUnidadeEscolar,
)
from .conftest import mocked_informacoes_escola_turma_aluno

pytestmark = pytest.mark.django_db


@freeze_time("2019-10-11")
def test_tipo_unidade_escolar(tipo_unidade_escolar):
    assert isinstance(str(tipo_unidade_escolar), str)
    assert tipo_unidade_escolar.iniciais is not None
    assert tipo_unidade_escolar.cardapios.all() is not None
    cardapio_do_dia = tipo_unidade_escolar.get_cardapio(data=datetime.date.today())
    assert isinstance(cardapio_do_dia, Cardapio)


def test_tipo_gestao(tipo_gestao):
    assert isinstance(str(tipo_gestao), str)
    assert tipo_gestao.nome is not None


def test_diretoria_regional(diretoria_regional, escola):
    assert isinstance(str(diretoria_regional), str)
    assert diretoria_regional.nome is not None
    assert diretoria_regional.escolas is not None
    assert escola in diretoria_regional.escolas.all()

    assert diretoria_regional.inclusoes_normais_autorizadas is not None
    assert diretoria_regional.inclusoes_continuas_reprovadas is not None
    assert diretoria_regional.inclusoes_normais_reprovadas is not None
    assert (
        diretoria_regional.alteracoes_cardapio_pendentes_das_minhas_escolas is not None
    )
    assert diretoria_regional.alteracoes_cardapio_autorizadas is not None
    assert diretoria_regional.solicitacao_kit_lanche_avulsa_autorizadas is not None
    assert diretoria_regional.solicitacao_kit_lanche_avulsa_reprovados is not None
    assert diretoria_regional.alteracoes_cardapio_reprovadas is not None
    assert diretoria_regional.inversoes_cardapio_autorizadas is not None
    assert diretoria_regional.inversoes_cardapio_reprovados is not None
    assert diretoria_regional.inclusoes_continuas_autorizadas is not None

    for filtro in [DAQUI_A_TRINTA_DIAS, DAQUI_A_SETE_DIAS, SEM_FILTRO]:
        assert (
            diretoria_regional.solicitacoes_kit_lanche_das_minhas_escolas_a_validar(
                filtro
            )
            is not None
        )
        assert (
            diretoria_regional.solicitacoes_kit_lanche_cemei_das_minhas_escolas_a_validar(
                filtro
            )
            is not None
        )
        assert (
            diretoria_regional.alteracoes_cardapio_das_minhas_escolas_a_validar(filtro)
            is not None
        )
        assert (
            diretoria_regional.inclusoes_alimentacao_continua_das_minhas_escolas(filtro)
            is not None
        )
        assert (
            diretoria_regional.inclusoes_alimentacao_cemei_das_minhas_escolas(filtro)
            is not None
        )
        assert (
            diretoria_regional.alteracoes_cardapio_das_minhas_escolas(filtro)
            is not None
        )
        assert (
            diretoria_regional.alteracoes_cardapio_cei_das_minhas_escolas(filtro)
            is not None
        )
        assert (
            diretoria_regional.alteracoes_cardapio_cemei_das_minhas_escolas(filtro)
            is not None
        )
        assert (
            diretoria_regional.inversoes_cardapio_das_minhas_escolas(filtro) is not None
        )


def test_escola(escola):
    assert isinstance(str(escola), str)
    assert escola.nome is not None
    assert escola.codigo_eol is not None
    assert isinstance(escola.diretoria_regional, DiretoriaRegional)
    assert isinstance(escola.tipo_unidade, TipoUnidadeEscolar)
    assert isinstance(escola.tipo_gestao, TipoGestao)
    assert escola.lote is not None
    assert escola.idades.all() is not None
    assert escola.periodos_escolares().all() is not None

    assert escola.grupos_inclusoes is not None
    assert escola.inclusoes_continuas is not None


def test_faixa_idade_escolar(faixa_idade_escolar):
    assert isinstance(str(faixa_idade_escolar), str)
    assert faixa_idade_escolar.nome is not None


def test_codae(codae):
    assert isinstance(str(codae), str)
    assert codae.inversoes_cardapio_autorizadas is not None
    assert codae.inversoes_cardapio_reprovados is not None
    assert codae.solicitacoes_unificadas_autorizadas is not None
    assert codae.inclusoes_continuas_autorizadas is not None
    assert codae.inclusoes_normais_autorizadas is not None
    assert codae.inclusoes_continuas_reprovadas is not None
    assert codae.inclusoes_normais_reprovadas is not None
    assert codae.solicitacao_kit_lanche_avulsa_autorizadas is not None
    assert codae.solicitacao_kit_lanche_avulsa_reprovadas is not None
    assert codae.alteracoes_cardapio_autorizadas is not None
    assert codae.alteracoes_cardapio_reprovadas is not None

    for filtro in [DAQUI_A_TRINTA_DIAS, DAQUI_A_SETE_DIAS, SEM_FILTRO]:
        assert (
            codae.solicitacoes_kit_lanche_das_minhas_escolas_a_validar(filtro)
            is not None
        )
        assert (
            codae.solicitacoes_kit_lanche_cemei_das_minhas_escolas_a_validar(filtro)
            is not None
        )
        assert codae.solicitacoes_unificadas(filtro) is not None
        assert codae.suspensoes_cardapio_das_minhas_escolas(filtro) is not None
        assert codae.alteracoes_cardapio_das_minhas(filtro) is not None
        assert codae.alteracoes_cardapio_cei_das_minhas(filtro) is not None
        assert codae.alteracoes_cardapio_cemei_das_minhas_escolas(filtro) is not None
        assert (
            codae.inclusoes_alimentacao_continua_das_minhas_escolas(filtro) is not None
        )
        assert codae.inclusoes_alimentacao_cemei_das_minhas_escolas(filtro) is not None
        assert (
            codae.grupos_inclusoes_alimentacao_normal_das_minhas_escolas(filtro)
            is not None
        )
        assert codae.inversoes_cardapio_das_minhas_escolas(filtro) is not None


def test_lote(lote):
    assert isinstance(str(lote), str)
    assert lote.escolas is not None


def test_periodo_escolar(periodo_escolar):
    assert isinstance(str(periodo_escolar), str)


def test_sub_prefeitura(sub_prefeitura):
    assert isinstance(str(sub_prefeitura), str)


def test_aluno(aluno):
    assert aluno.__str__() == "Fulano da Silva - 000001"


@freeze_time("2019-06-20")
def test_data_pertence_faixa_etaria_hoje(datas_e_faixas):
    (data, faixa_etaria, eh_pertencente) = datas_e_faixas
    assert (
        faixa_etaria.data_pertence_a_faixa(data, datetime.date.today())
        == eh_pertencente
    )


def test_escola_periodo_escolar_alunos_por_faixa_etaria(
    faixas_etarias,
    escola_periodo_escolar,
    eolservicosgp_get_lista_alunos,
):
    faixas_alunos = escola_periodo_escolar.alunos_por_faixa_etaria(
        datetime.date(2020, 10, 25)
    )
    assert [i for i in faixas_alunos.values()] == [2, 1]


def test_faixa_str():
    faixa = FaixaEtaria.objects.create(inicio=24, fim=48)
    assert str(faixa) == "02 anos a 03 anos e 11 meses"


def test_ordem(periodo_escolar):
    assert ("posicao",) == periodo_escolar._meta.ordering


def test_instance_model_planilha_de_para_codigo_eol_codigo_codae(
    planilha_de_para_eol_codae,
):
    model = planilha_de_para_eol_codae
    assert isinstance(model, PlanilhaEscolaDeParaCodigoEolCodigoCoade)
    assert model.criado_em is not None
    assert model.planilha is not None
    assert model.codigos_codae_vinculados is not None


def test_meta_modelo_planilha_de_para_codigo_eol_codigo_codae(
    planilha_de_para_eol_codae,
):
    assert (
        planilha_de_para_eol_codae._meta.verbose_name
        == "Planilha De-Para: Código EOL x Código Codae"
    )
    assert (
        planilha_de_para_eol_codae._meta.verbose_name_plural
        == "Planilhas De-Para: Código EOL x Código Codae"
    )


def test_instance_model_planilha_atualizacao_tipo_gestao_escolas(
    planilha_atualizacao_tipo_gestao,
):
    model = planilha_atualizacao_tipo_gestao
    assert isinstance(model, PlanilhaAtualizacaoTipoGestaoEscola)
    assert model.criado_em is not None
    assert model.conteudo is not None
    assert model.status is not None


def test_meta_modelo_planilha_atualizacao_tipo_gestao_escolas(
    planilha_atualizacao_tipo_gestao,
):
    assert (
        planilha_atualizacao_tipo_gestao._meta.verbose_name
        == "Planilha Atualização Tipo Gestão Escola"
    )
    assert (
        planilha_atualizacao_tipo_gestao._meta.verbose_name_plural
        == "Planilha Atualização Tipo Gestão Escola"
    )


def test_admin_planilha_atualizacao_tipo_gestao_escolas():
    model_admin = PlanilhaAtualizacaoTipoGestaoEscolaAdmin(
        PlanilhaAtualizacaoTipoGestaoEscola, admin.site
    )
    # pylint: disable=W0212
    assert admin.site._registry[PlanilhaAtualizacaoTipoGestaoEscola]
    assert model_admin.list_display == ("__str__", "criado_em", "status")
    assert (
        model_admin.change_list_template
        == "admin/escola/importacao_tipos_de_gestao_das_escolas.html"
    )
    assert model_admin.actions == ("processa_planilha",)


def test_modelo_alunos_matriculados_periodo_escola_regular(
    alunos_matriculados_periodo_escola_regular,
):
    model = alunos_matriculados_periodo_escola_regular
    assert isinstance(model, AlunosMatriculadosPeriodoEscola)
    assert model.criado_em is not None
    assert model.escola is not None
    assert model.periodo_escolar is not None
    assert model.quantidade_alunos == 50
    assert model.tipo_turma == "REGULAR"


def test_modelo_alunos_matriculados_periodo_escola_programas(
    alunos_matriculados_periodo_escola_programas,
):
    model = alunos_matriculados_periodo_escola_programas
    assert isinstance(model, AlunosMatriculadosPeriodoEscola)
    assert model.criado_em is not None
    assert model.escola is not None
    assert model.periodo_escolar is not None
    assert model.quantidade_alunos == 50
    assert model.tipo_turma == "PROGRAMAS"


def test_modelo_log_alunos_matriculados_periodo_escola_regular(
    log_alunos_matriculados_periodo_escola_regular,
):
    model = log_alunos_matriculados_periodo_escola_regular
    assert isinstance(model, LogAlunosMatriculadosPeriodoEscola)
    assert model.criado_em is not None
    assert model.escola is not None
    assert model.periodo_escolar is not None
    assert model.quantidade_alunos == 50
    assert model.tipo_turma == "REGULAR"


def test_modelo_log_alunos_matriculados_periodo_escola_programas(
    log_alunos_matriculados_periodo_escola_programas,
):
    model = log_alunos_matriculados_periodo_escola_programas
    assert isinstance(model, LogAlunosMatriculadosPeriodoEscola)
    assert model.criado_em is not None
    assert model.escola is not None
    assert model.periodo_escolar is not None
    assert model.quantidade_alunos == 50
    assert model.tipo_turma == "PROGRAMAS"


def test_criar_alunos_matriculados_periodo_escola_regular(escola, periodo_escolar):
    assert AlunosMatriculadosPeriodoEscola.objects.count() == 0
    AlunosMatriculadosPeriodoEscola.criar(
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=32,
        tipo_turma="REGULAR",
    )
    assert AlunosMatriculadosPeriodoEscola.objects.count() == 1
    assert AlunosMatriculadosPeriodoEscola.objects.first().tipo_turma == "REGULAR"
    AlunosMatriculadosPeriodoEscola.criar(
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=40,
        tipo_turma="REGULAR",
    )
    obj = AlunosMatriculadosPeriodoEscola.objects.all()[0]
    assert f"tem {obj.quantidade_alunos} alunos" in obj.__str__()


def test_criar_log_alunos_matriculados_periodo_escola_regular(escola, periodo_escolar):
    hoje = datetime.date.today()
    assert LogAlunosMatriculadosPeriodoEscola.objects.count() == 0
    LogAlunosMatriculadosPeriodoEscola.criar(
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=32,
        data=hoje,
        tipo_turma="REGULAR",
    )
    assert LogAlunosMatriculadosPeriodoEscola.objects.count() == 1
    assert LogAlunosMatriculadosPeriodoEscola.objects.first().tipo_turma == "REGULAR"
    log = LogAlunosMatriculadosPeriodoEscola.objects.all()[0]
    assert f"tem {log.quantidade_alunos} alunos" in log.__str__()


def test_criar_log_alunos_matriculados_periodo_escola_cemei_regular(
    escola_cemei, periodo_escolar
):
    hoje = datetime.date.today()
    assert LogAlunosMatriculadosPeriodoEscola.objects.count() == 0
    LogAlunosMatriculadosPeriodoEscola.criar(
        escola=escola_cemei,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=32,
        data=hoje,
        tipo_turma="REGULAR",
    )
    assert LogAlunosMatriculadosPeriodoEscola.objects.count() == 3
    assert (
        LogAlunosMatriculadosPeriodoEscola.objects.filter(cei_ou_emei="CEI").exists()
        is True
    )
    assert (
        LogAlunosMatriculadosPeriodoEscola.objects.filter(cei_ou_emei="EMEI").exists()
        is True
    )
    assert LogAlunosMatriculadosPeriodoEscola.objects.first().tipo_turma == "REGULAR"
    log = LogAlunosMatriculadosPeriodoEscola.objects.all()[0]
    assert f"tem {log.quantidade_alunos} alunos" in log.__str__()


def test_criar_log_alunos_matriculados_periodo_escola_emebs_regular(
    escola_emebs, periodo_escolar
):
    hoje = datetime.date.today()
    assert LogAlunosMatriculadosPeriodoEscola.objects.count() == 0
    LogAlunosMatriculadosPeriodoEscola.criar(
        escola=escola_emebs,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=32,
        data=hoje,
        tipo_turma="REGULAR",
    )
    assert LogAlunosMatriculadosPeriodoEscola.objects.count() == 3
    assert (
        LogAlunosMatriculadosPeriodoEscola.objects.filter(
            infantil_ou_fundamental="INFANTIL", quantidade_alunos=1
        ).exists()
        is True
    )
    assert (
        LogAlunosMatriculadosPeriodoEscola.objects.filter(
            infantil_ou_fundamental="FUNDAMENTAL", quantidade_alunos=1
        ).exists()
        is True
    )
    assert LogAlunosMatriculadosPeriodoEscola.objects.first().tipo_turma == "REGULAR"
    log = LogAlunosMatriculadosPeriodoEscola.objects.all()[0]
    assert f"tem {log.quantidade_alunos} alunos" in log.__str__()


def test_dia_calendario_e_dia_letivo(dia_calendario_letivo):
    model = dia_calendario_letivo
    assert isinstance(model, DiaCalendario)
    assert model.criado_em is not None
    assert model.data is not None
    assert model.escola is not None
    assert model.dia_letivo
    assert "é dia letivo" in dia_calendario_letivo.__str__()


def test_dia_calendario_nao_e_dia_letivo(dia_calendario_nao_letivo):
    model = dia_calendario_nao_letivo
    assert isinstance(model, DiaCalendario)
    assert model.criado_em is not None
    assert model.data is not None
    assert model.escola is not None
    assert not model.dia_letivo
    assert "não é dia letivo" in dia_calendario_nao_letivo.__str__()


def test_log_alunos_matriculados_faixa_etaria_dia(
    log_alunos_matriculados_faixa_etaria_dia,
):
    model = log_alunos_matriculados_faixa_etaria_dia
    quantidade = model.quantidade
    faixa_etaria = model.faixa_etaria
    assert isinstance(model, LogAlunosMatriculadosFaixaEtariaDia)
    assert model.criado_em is not None
    assert model.data is not None
    assert f"{quantidade} aluno(s)" in model.__str__()
    assert f"faixa etária {faixa_etaria}" in model.__str__()


def test_log_atualiza_dados_aluno(log_atualiza_dados_aluno):
    model = log_atualiza_dados_aluno
    codigo_eol = model.codigo_eol
    criado_em = model.criado_em
    assert isinstance(model, LogAtualizaDadosAluno)
    assert model.criado_em is not None
    assert model.status == 200
    assert (
        model.__str__()
        == f'Requisicao para Escola: "#{codigo_eol}" na data de: "{criado_em}"'
    )


def test_log_rotina_diaria_alunos(log_rotina_diaria_alunos):
    model = log_rotina_diaria_alunos
    criado_em = model.criado_em.strftime("%Y-%m-%d %H:%M:%S")
    quant_antes = model.quantidade_alunos_antes
    quant_atual = model.quantidade_alunos_atual
    string_model = (
        f"Criado em {criado_em} - Quant. de alunos antes: {quant_antes}. "
        f"Quant. de alunos atual: {quant_atual}"
    )
    assert isinstance(model, LogRotinaDiariaAlunos)
    assert model.criado_em is not None
    assert model.__str__() == string_model


def test_log_alteracao_quantidade_alunos_por_escola_periodo(
    log_alteracao_quantidade_alunos_por_escola_periodo,
):
    model = log_alteracao_quantidade_alunos_por_escola_periodo
    quantidade_anterior = model.quantidade_alunos_de
    quantidade_atual = model.quantidade_alunos_para
    escola = model.escola.nome
    string_model = f"Alteração de: {quantidade_anterior} alunos, para: {quantidade_atual} alunos na escola: {escola}"
    assert isinstance(model, LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar)
    assert model.criado_em is not None
    assert model.__str__() == string_model


@freeze_time("2023-08-28")
def test_alunos_por_periodo_e_faixa_etaria(
    escola, faixas_etarias, periodo_escolar, eolservicosgp_get_lista_alunos
):
    response = escola.alunos_por_periodo_e_faixa_etaria()
    assert len(response) == 1
    assert response["INTEGRAL"] == Counter(
        {
            f"{str([f for f in faixas_etarias if f.inicio == 48][0].uuid)}": 3,
        }
    )


@freeze_time("2023-08-28")
def test_alunos_periodo_parcial_e_faixa_etaria(
    escola_cei,
    faixas_etarias,
    alunos_periodo_parcial,
    periodo_escolar,
    eolservicosgp_get_lista_alunos,
):
    response = escola_cei.alunos_periodo_parcial_e_faixa_etaria()
    assert len(response) == 1
    assert response["PARCIAL"] == Counter(
        {
            f"{str([f for f in faixas_etarias if f.inicio == 48][0].uuid)}": 2,
        }
    )


@freeze_time("2023-08-28")
def test_alunos_por_periodo_e_faixa_etaria_objetos_alunos(
    escola_cei, faixas_etarias, alunos
):
    response = escola_cei.alunos_por_periodo_e_faixa_etaria_objetos_alunos()
    assert len(response) == 1
    assert response["INTEGRAL"] == Counter(
        {
            f"{str([f for f in faixas_etarias if f.inicio == 48][0].uuid)}": 3,
        }
    )


@freeze_time("2023-08-28")
def test_alunos_por_faixa_etaria(
    escola_cei, faixas_etarias, eolservicosgp_get_lista_alunos
):
    response = escola_cei.alunos_por_faixa_etaria()
    assert len(response.items()) == 1
    assert response == Counter(
        {
            f"{str([f for f in faixas_etarias if f.inicio == 48][0].uuid)}": 3,
        }
    )


def test_dia_suspensao_atividades_model(dia_suspensao_atividades):
    assert (
        dia_suspensao_atividades.__str__()
        == "08/08/2022 - EMEF - Edital Edital de Pregão nº 13/SME/2020"
    )
