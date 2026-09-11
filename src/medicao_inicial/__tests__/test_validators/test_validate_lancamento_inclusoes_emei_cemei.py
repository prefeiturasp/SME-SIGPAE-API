import datetime

import pytest
from model_bakery import baker

from src.cardapio.base.models import (
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from src.dados_comuns.constants import TIPOS_ALIMENTACAO
from src.inclusao_alimentacao.models import InclusaoDeAlimentacaoCEMEI
from src.medicao_inicial.utils import get_linhas_da_tabela
from src.medicao_inicial.validators import validate_lancamento_inclusoes_emei_cemei

pytestmark = pytest.mark.django_db

MES = "04"
ANO = "2026"


def _cria_solicitacao_e_medicao(escola, periodo):
    solicitacao = baker.make(
        "SolicitacaoMedicaoInicial", mes=MES, ano=ANO, escola=escola
    )
    medicao = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao,
        periodo_escolar=periodo,
    )
    return solicitacao, medicao


def _cria_inclusao_cemei(escola, periodo, tipos_alimentacao, dia):
    inclusao = baker.make(
        "InclusaoDeAlimentacaoCEMEI",
        escola=escola,
        status=InclusaoDeAlimentacaoCEMEI.workflow_class.CODAE_AUTORIZADO,
    )
    baker.make(
        "DiasMotivosInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=inclusao,
        data=datetime.date(int(ANO), int(MES), dia),
    )
    qt = baker.make(
        "QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=inclusao,
        periodo_escolar=periodo,
        quantidade_alunos=10,
    )
    qt.tipos_alimentacao.set(tipos_alimentacao)
    return inclusao


def _cria_valores(medicao, categoria, dia, nome_campos):
    for nome_campo in nome_campos:
        baker.make(
            "ValorMedicao",
            medicao=medicao,
            categoria_medicao=categoria,
            nome_campo=nome_campo,
            dia=dia,
            valor="1",
        )


def _get_nome_campos_lancaveis(escola, solicitacao, qt):
    eh_numero_alunos = qt.periodo_escolar not in escola.periodos_escolares(
        ano=solicitacao.ano, mes=solicitacao.mes
    )
    tipos_alimentacao = qt.tipos_alimentacao.exclude(
        nome=TIPOS_ALIMENTACAO.LANCHE_EMERGENCIAL.value
    )
    alimentacoes = list(set(tipos_alimentacao.values_list("nome", flat=True)))
    return get_linhas_da_tabela(alimentacoes, eh_numero_alunos)


class TestValidateLancamentoInclusoesEMEICEMEI:
    def test_quando_inclusao_autoriza_alimentacao_diferente_do_vinculo_nao_gera_erro(
        self,
        escola_cemei,
        categoria_medicao,
        tipo_unidade_escolar_emei,
        tipo_alimentacao_lanche,
        tipo_alimentacao_refeicao,
    ):
        periodo = baker.make("PeriodoEscolar", nome="INTEGRAL")
        solicitacao, medicao = _cria_solicitacao_e_medicao(escola_cemei, periodo)

        vinculo = (
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.create(
                tipo_unidade_escolar=tipo_unidade_escolar_emei,
                periodo_escolar=periodo,
            )
        )
        vinculo.tipos_alimentacao.add(tipo_alimentacao_refeicao)

        inclusao = _cria_inclusao_cemei(
            escola_cemei, periodo, [tipo_alimentacao_lanche], 5
        )
        qt = inclusao.quantidade_alunos_emei_da_inclusao_cemei.get()
        nome_campos = _get_nome_campos_lancaveis(escola_cemei, solicitacao, qt)
        _cria_valores(medicao, categoria_medicao, "05", nome_campos)

        lista_erros = validate_lancamento_inclusoes_emei_cemei(
            solicitacao,
            [],
            InclusaoDeAlimentacaoCEMEI.objects.filter(id=inclusao.id),
            escola_cemei,
            categoria_medicao,
            medicao,
        )

        assert lista_erros == []

    def test_quando_inclusao_autoriza_alimentacao_sem_lancamento_retorna_erro(
        self,
        escola_cemei,
        categoria_medicao,
        tipo_alimentacao_lanche,
    ):
        periodo = baker.make("PeriodoEscolar", nome="INTEGRAL")
        solicitacao, medicao = _cria_solicitacao_e_medicao(escola_cemei, periodo)

        inclusao = _cria_inclusao_cemei(
            escola_cemei, periodo, [tipo_alimentacao_lanche], 10
        )
        eh_numero_alunos = periodo not in escola_cemei.periodos_escolares(
            ano=solicitacao.ano, mes=solicitacao.mes
        )
        _cria_valores(
            medicao,
            categoria_medicao,
            "10",
            get_linhas_da_tabela([], eh_numero_alunos),
        )

        lista_erros = validate_lancamento_inclusoes_emei_cemei(
            solicitacao,
            [],
            InclusaoDeAlimentacaoCEMEI.objects.filter(id=inclusao.id),
            escola_cemei,
            categoria_medicao,
            medicao,
        )

        assert lista_erros == [
            {
                "periodo_escolar": medicao.nome_periodo_grupo,
                "erro": "Restam dias a serem lançados nas alimentações.",
            }
        ]

    def test_quando_inclusao_autoriza_lanche_emergencial_nao_gera_erro_sem_lancamento(
        self,
        escola_cemei,
        categoria_medicao,
        tipo_alimentacao_lanche_emergencial,
    ):
        periodo = baker.make("PeriodoEscolar", nome="INTEGRAL")
        solicitacao, medicao = _cria_solicitacao_e_medicao(escola_cemei, periodo)

        inclusao = _cria_inclusao_cemei(
            escola_cemei, periodo, [tipo_alimentacao_lanche_emergencial], 15
        )
        eh_numero_alunos = periodo not in escola_cemei.periodos_escolares(
            ano=solicitacao.ano, mes=solicitacao.mes
        )
        _cria_valores(
            medicao,
            categoria_medicao,
            "15",
            get_linhas_da_tabela([], eh_numero_alunos),
        )

        lista_erros = validate_lancamento_inclusoes_emei_cemei(
            solicitacao,
            [],
            InclusaoDeAlimentacaoCEMEI.objects.filter(id=inclusao.id),
            escola_cemei,
            categoria_medicao,
            medicao,
        )

        assert lista_erros == []
