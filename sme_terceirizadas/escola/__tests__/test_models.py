import datetime

import pytest
from freezegun import freeze_time

from ...cardapio.models import Cardapio
from ...dados_comuns.constants import DAQUI_A_SETE_DIAS, DAQUI_A_TRINTA_DIAS, SEM_FILTRO
from ..models import (
    DiretoriaRegional,
    FaixaEtaria,
    PlanilhaEscolaDeParaCodigoEolCodigoCoade,
    TipoGestao,
    TipoUnidadeEscolar
)

pytestmark = pytest.mark.django_db


@freeze_time('2019-10-11')
def test_tipo_unidade_escolar(tipo_unidade_escolar):
    assert isinstance(str(tipo_unidade_escolar), str)
    assert tipo_unidade_escolar.iniciais is not None
    assert tipo_unidade_escolar.cardapios.all() is not None
    cardapio_do_dia = tipo_unidade_escolar.get_cardapio(
        data=datetime.date.today())
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
    assert diretoria_regional.alteracoes_cardapio_pendentes_das_minhas_escolas is not None
    assert diretoria_regional.alteracoes_cardapio_autorizadas is not None
    assert diretoria_regional.solicitacao_kit_lanche_avulsa_autorizadas is not None
    assert diretoria_regional.solicitacao_kit_lanche_avulsa_reprovados is not None
    assert diretoria_regional.alteracoes_cardapio_reprovadas is not None
    assert diretoria_regional.inversoes_cardapio_autorizadas is not None
    assert diretoria_regional.inversoes_cardapio_reprovados is not None
    assert diretoria_regional.inclusoes_continuas_autorizadas is not None

    for filtro in [DAQUI_A_TRINTA_DIAS, DAQUI_A_SETE_DIAS, SEM_FILTRO]:
        assert diretoria_regional.solicitacoes_kit_lanche_das_minhas_escolas_a_validar(
            filtro) is not None
        assert diretoria_regional.alteracoes_cardapio_das_minhas_escolas_a_validar(
            filtro) is not None
        assert diretoria_regional.inclusoes_alimentacao_continua_das_minhas_escolas(
            filtro) is not None
        assert diretoria_regional.alteracoes_cardapio_das_minhas_escolas(
            filtro) is not None
        assert diretoria_regional.inversoes_cardapio_das_minhas_escolas(
            filtro) is not None


def test_escola(escola):
    assert isinstance(str(escola), str)
    assert escola.nome is not None
    assert escola.codigo_eol is not None
    assert isinstance(escola.diretoria_regional, DiretoriaRegional)
    assert isinstance(escola.tipo_unidade, TipoUnidadeEscolar)
    assert isinstance(escola.tipo_gestao, TipoGestao)
    assert escola.lote is not None
    assert escola.idades.all() is not None
    assert escola.periodos_escolares.all() is not None

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
        assert codae.solicitacoes_kit_lanche_das_minhas_escolas_a_validar(
            filtro) is not None
        assert codae.solicitacoes_unificadas(filtro) is not None
        assert codae.suspensoes_cardapio_das_minhas_escolas(filtro) is not None
        assert codae.alteracoes_cardapio_das_minhas(filtro) is not None
        assert codae.inclusoes_alimentacao_continua_das_minhas_escolas(
            filtro) is not None
        assert codae.grupos_inclusoes_alimentacao_normal_das_minhas_escolas(
            filtro) is not None
        assert codae.inversoes_cardapio_das_minhas_escolas(filtro) is not None


def test_lote(lote):
    assert isinstance(str(lote), str)
    assert lote.escolas is not None


def test_periodo_escolar(periodo_escolar):
    assert isinstance(str(periodo_escolar), str)


def test_sub_prefeitura(sub_prefeitura):
    assert isinstance(str(sub_prefeitura), str)


def test_aluno(aluno):
    assert aluno.__str__() == 'Fulano da Silva - 000001'


@freeze_time('2019-06-20')
def test_data_pertence_faixa_etaria_hoje(datas_e_faixas):
    (data, faixa_etaria, eh_pertencente) = datas_e_faixas
    assert faixa_etaria.data_pertence_a_faixa(
        data, datetime.date.today()) == eh_pertencente


def test_escola_periodo_escolar_alunos_por_faixa_etaria(faixas_etarias,
                                                        escola_periodo_escolar,
                                                        eolservice_get_informacoes_escola_turma_aluno):
    faixas_alunos = escola_periodo_escolar.alunos_por_faixa_etaria(
        datetime.date(2020, 10, 25))
    assert [i for i in faixas_alunos.values()] == [94, 18, 26]


def test_faixa_str():
    faixa = FaixaEtaria.objects.create(inicio=24, fim=48)
    assert str(faixa) == '2 anos - 4 anos'


def test_ordem(periodo_escolar):
    assert ('nome',) == periodo_escolar._meta.ordering


def test_instance_model_planilha_de_para_codigo_eol_codigo_codae(planilha_de_para_eol_codae):
    model = planilha_de_para_eol_codae
    assert isinstance(model, PlanilhaEscolaDeParaCodigoEolCodigoCoade)
    assert model.criado_em is not None
    assert model.planilha is not None
    assert model.codigos_codae_vinculados is not None


def test_meta_modelo_planilha_de_para_codigo_eol_codigo_codae(planilha_de_para_eol_codae):
    assert planilha_de_para_eol_codae._meta.verbose_name == 'Planilha De-Para: Código EOL x Código Codae'
    assert planilha_de_para_eol_codae._meta.verbose_name_plural == 'Planilhas De-Para: Código EOL x Código Codae'
