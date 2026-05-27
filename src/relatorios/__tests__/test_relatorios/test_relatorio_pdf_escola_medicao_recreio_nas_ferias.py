import datetime

import pytest
from freezegun import freeze_time

from src.medicao_inicial.utils import (
    build_tabela_somatorio_recreio_nas_ferias,
    build_tabelas_relatorio_medicao,
)
from src.relatorios.relatorios import get_total_por_periodo

pytestmark = pytest.mark.django_db


@freeze_time("2026-01-10")
class TestUseCaseRelatorioPDFMedicaoEscolaRecreioNasFerias:
    def _setup_periodos_escolares(self, periodo_escolar_factory):
        # Recreio nas Férias não usa período escolar, mas pode ser necessário
        # para a escola EMEF existir corretamente
        self.periodo_manha = periodo_escolar_factory.create(nome="MANHA")

    def _setup_tipos_alimentacao(self, tipo_alimentacao_factory):
        self.tipo_alimentacao_lanche = tipo_alimentacao_factory.create(nome="Lanche")
        self.tipo_alimentacao_lanche_4h = tipo_alimentacao_factory.create(
            nome="Lanche 4h"
        )
        self.tipo_alimentacao_refeicao = tipo_alimentacao_factory.create(
            nome="Refeição"
        )
        self.tipo_alimentacao_sobremesa = tipo_alimentacao_factory.create(
            nome="Sobremesa"
        )

    def _setup_categorias_medicao(self, categoria_medicao_factory):
        self.categoria_alimentacao = categoria_medicao_factory.create(
            nome="ALIMENTAÇÃO"
        )

    def _setup_core(
        self,
        periodo_escolar_factory,
        categoria_medicao_factory,
        tipo_alimentacao_factory,
    ):
        self._setup_periodos_escolares(periodo_escolar_factory)
        self._setup_tipos_alimentacao(tipo_alimentacao_factory)
        self._setup_categorias_medicao(categoria_medicao_factory)

    def _setup_escola_emef(
        self, diretoria_regional_factory, lote_factory, escola_factory
    ):
        self.dre = diretoria_regional_factory.create()
        self.lote = lote_factory.create(diretoria_regional=self.dre)
        self.escola_emef = escola_factory.create(
            nome="EMEF TESTE",
            tipo_gestao__nome="TERC TOTAL",
            lote=self.lote,
            diretoria_regional=self.dre,
        )

    def _setup_recreio_nas_ferias(
        self,
        recreio_nas_ferias_factory,
        recreio_nas_ferias_unidade_participante_factory,
        recreio_nas_ferias_unidade_tipo_alimentacao_factory,
        categoria_alimentacao_factory,
    ):
        self.recreio = recreio_nas_ferias_factory.create(
            titulo="Recreio nas Férias - Jan 2026",
            data_inicio=datetime.date(2026, 1, 7),
            data_fim=datetime.date(2026, 1, 23),
        )

        self.categoria_inscritos = categoria_alimentacao_factory.create(
            nome="Inscritos"
        )
        self.categoria_colaboradores_recreio = categoria_alimentacao_factory.create(
            nome="Colaboradores"
        )

        self.recreio_ue = recreio_nas_ferias_unidade_participante_factory.create(
            unidade_educacional=self.escola_emef,
            lote=self.lote,
            recreio_nas_ferias=self.recreio,
            num_inscritos=10,
            num_colaboradores=5,
            liberar_medicao=True,
        )

        for tipo in [
            self.tipo_alimentacao_lanche,
            self.tipo_alimentacao_lanche_4h,
            self.tipo_alimentacao_refeicao,
            self.tipo_alimentacao_sobremesa,
        ]:
            for categoria in [
                self.categoria_inscritos,
                self.categoria_colaboradores_recreio,
            ]:
                recreio_nas_ferias_unidade_tipo_alimentacao_factory.create(
                    recreio_ferias_unidade=self.recreio_ue,
                    tipo_alimentacao=tipo,
                    categoria=categoria,
                )

    def _setup_solicitacao_medicao_inicial(
        self, solicitacao_medicao_inicial_factory
    ):
        self.solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory.create(
            escola=self.escola_emef,
            mes="01",
            ano="2026",
            recreio_nas_ferias=self.recreio,
        )

    def _setup_medicao_recreio(self, medicao_factory):
        self.medicao_recreio = medicao_factory.create(
            solicitacao_medicao_inicial=self.solicitacao_medicao_inicial,
            periodo_escolar=None,
            grupo__nome="Recreio nas Férias",
        )

    def _setup_medicao_colaboradores(self, medicao_factory):
        self.medicao_colaboradores = medicao_factory.create(
            solicitacao_medicao_inicial=self.solicitacao_medicao_inicial,
            periodo_escolar=None,
            grupo__nome="Colaboradores",
        )

    def _setup_logs_medicao_recreio_alimentacao(self, valor_medicao_factory):
        # Dia 07 a 10 (4 dias dentro do período do recreio)
        for dia in range(7, 11):
            for nome_campo in [
                "participantes",
                "frequencia",
                "lanche",
                "lanche_4h",
                "refeicao",
                "repeticao_refeicao",
                "sobremesa",
                "repeticao_sobremesa",
            ]:
                valor_medicao_factory.create(
                    dia=f"{dia:02d}",
                    valor="10",
                    nome_campo=nome_campo,
                    medicao=self.medicao_recreio,
                    categoria_medicao=self.categoria_alimentacao,
                    faixa_etaria=None,
                )

    def _setup_logs_medicao_colaboradores_alimentacao(self, valor_medicao_factory):
        for dia in range(7, 11):
            for nome_campo in [
                "participantes",
                "frequencia",
                "lanche",
                "lanche_4h",
                "refeicao",
                "repeticao_refeicao",
                "sobremesa",
                "repeticao_sobremesa",
            ]:
                valor_medicao_factory.create(
                    dia=f"{dia:02d}",
                    valor="5",
                    nome_campo=nome_campo,
                    medicao=self.medicao_colaboradores,
                    categoria_medicao=self.categoria_alimentacao,
                    faixa_etaria=None,
                )

    @freeze_time("2026-01-10")
    def test_relatorio_solicitacao_medicao_por_escola_recreio_nas_ferias(
        self,
        escola_factory,
        lote_factory,
        diretoria_regional_factory,
        solicitacao_medicao_inicial_factory,
        periodo_escolar_factory,
        valor_medicao_factory,
        medicao_factory,
        categoria_medicao_factory,
        tipo_alimentacao_factory,
        recreio_nas_ferias_factory,
        recreio_nas_ferias_unidade_participante_factory,
        recreio_nas_ferias_unidade_tipo_alimentacao_factory,
        categoria_alimentacao_factory,
    ):
        self._setup_core(
            periodo_escolar_factory,
            categoria_medicao_factory,
            tipo_alimentacao_factory,
        )
        self._setup_escola_emef(
            diretoria_regional_factory, lote_factory, escola_factory
        )
        self._setup_recreio_nas_ferias(
            recreio_nas_ferias_factory,
            recreio_nas_ferias_unidade_participante_factory,
            recreio_nas_ferias_unidade_tipo_alimentacao_factory,
            categoria_alimentacao_factory,
        )
        self._setup_solicitacao_medicao_inicial(solicitacao_medicao_inicial_factory)

        self._setup_medicao_recreio(medicao_factory)
        self._setup_logs_medicao_recreio_alimentacao(valor_medicao_factory)

        self._setup_medicao_colaboradores(medicao_factory)
        self._setup_logs_medicao_colaboradores_alimentacao(valor_medicao_factory)

        build_tabelas = build_tabelas_relatorio_medicao(
            self.solicitacao_medicao_inicial
        )
        assert any(
            item.get("periodos") == ["Recreio nas Férias"] for item in build_tabelas
        ), "Nenhum item com periodos=['Recreio nas Férias'] encontrado"
        assert any(
            item.get("periodos") == ["Colaboradores"] for item in build_tabelas
        ), "Nenhum item com periodos=['Colaboradores'] encontrado"

        # --- totais por período ---
        dict_total_refeicoes = get_total_por_periodo(
            build_tabelas, "total_refeicoes_pagamento"
        )
        assert dict_total_refeicoes == {
            "Recreio nas Férias": 40,
            "Colaboradores": 20,
        }

        # sobremesa=10, repeticao_sobremesa=10 → min(20, 10) × 4 = 40
        dict_total_sobremesas = get_total_por_periodo(
            build_tabelas, "total_sobremesas_pagamento"
        )
        assert dict_total_sobremesas == {
            "Recreio nas Férias": 40,
            "Colaboradores": 20,
        }

        tabela_somatorio_participantes, tabela_somatorio_colaboradores = (
            build_tabela_somatorio_recreio_nas_ferias(
                self.solicitacao_medicao_inicial,
                dict_total_refeicoes,
                dict_total_sobremesas,
            )
        )

        # lanche=10 × 4 dias = 40, lanche_4h=40, refeicao=40, sobremesa=40
        # Dietas sem dados retornam 0 mas ainda aparecem no header/body
        assert tabela_somatorio_participantes == {
            "header": [
                "TIPOS ALIMENTAÇÃO",
                "ALIMENTAÇÕES PARA ALUNOS PARTICIPANTES",
                "DIETA TIPO A",
                "DIETA ENTERAL / REST. DE AMINOÁCIDOS",
                "DIETA TIPO B",
            ],
            "body": [
                ["Lanche", 40, 0, 0, 0],
                ["Lanche 4h", 40, 0, 0, 0],
                ["Refeição", 40, 0, 0, 0],
                ["Sobremesa", 40, 0, 0, 0],
            ],
        }

        # lanche=5 × 4 dias = 20, lanche_4h=20, refeicao=20, sobremesa=20
        assert tabela_somatorio_colaboradores == {
            "header": [
                "TIPOS ALIMENTAÇÃO",
                "TOTAL DE ALIMENTAÇÕES PARA COLABORADORES",
            ],
            "body": [
                ["Lanche", 20],
                ["Lanche 4h", 20],
                ["Refeição", 20],
                ["Sobremesa", 20],
            ],
        }
