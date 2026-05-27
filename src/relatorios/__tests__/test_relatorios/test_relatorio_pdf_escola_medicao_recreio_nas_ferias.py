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
        categoria_medicao_factory,
        tipo_alimentacao_factory,
    ):
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

        # --- build_tabelas ---
        build_tabelas = build_tabelas_relatorio_medicao(
            self.solicitacao_medicao_inicial
        )
        assert any(
            item.get("periodos") == ["Recreio nas Férias"] for item in build_tabelas
        ), "Nenhum item com periodos=['Recreio nas Férias'] encontrado"
        assert any(
            item.get("periodos") == ["Colaboradores"] for item in build_tabelas
        ), "Nenhum item com periodos=['Colaboradores'] encontrado"

        dict_total_refeicoes = get_total_por_periodo(
            build_tabelas, "total_refeicoes_pagamento"
        )
        assert dict_total_refeicoes == {
            "Recreio nas Férias": 40,
            "Colaboradores": 20,
        }

        dict_total_sobremesas = get_total_por_periodo(
            build_tabelas, "total_sobremesas_pagamento"
        )
        assert dict_total_sobremesas == {
            "Recreio nas Férias": 40,
            "Colaboradores": 20,
        }

        # --- somatorio recreio ---
        tabela_somatorio_participantes, tabela_somatorio_colaboradores = (
            build_tabela_somatorio_recreio_nas_ferias(
                self.solicitacao_medicao_inicial,
                dict_total_refeicoes,
                dict_total_sobremesas,
            )
        )

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


@freeze_time("2026-01-10")
class TestUseCaseRelatorioPDFMedicaoEscolaRecreioNasFeriasEMEI:
    """
    Testa o cálculo de pagamento de refeição/sobremesa para EMEI no Recreio nas Férias.

    A lógica difere da EMEF em `popula_campo_total_refeicoes_pagamento`:
    - EMEI sem edital IMR → refeicao + segunda_refeicao (sem min, sem repeticao)
    - EMEI com edital IMR → min(refeicao + repeticao, participantes)

    Valores usados para forçar a diferença:
      participantes=10, refeicao=8, repeticao_refeicao=6
      → sem IMR: 8 + 0 (sem segunda_refeicao) = 8 por dia
      → com IMR: min(8 + 6, 10) = 10 por dia
    """

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

    def _setup_escola_emei(
        self, diretoria_regional_factory, lote_factory, escola_factory
    ):
        self.dre = diretoria_regional_factory.create()
        self.lote = lote_factory.create(diretoria_regional=self.dre)
        self.escola_emei = escola_factory.create(
            nome="EMEI TESTE",
            tipo_unidade__iniciais="EMEI",
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
            unidade_educacional=self.escola_emei,
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

    def _setup_solicitacao(self, solicitacao_medicao_inicial_factory):
        self.solicitacao = solicitacao_medicao_inicial_factory.create(
            escola=self.escola_emei,
            mes="01",
            ano="2026",
            recreio_nas_ferias=self.recreio,
        )

    def _setup_medicoes(self, medicao_factory):
        self.medicao_recreio = medicao_factory.create(
            solicitacao_medicao_inicial=self.solicitacao,
            periodo_escolar=None,
            grupo__nome="Recreio nas Férias",
        )
        self.medicao_colaboradores = medicao_factory.create(
            solicitacao_medicao_inicial=self.solicitacao,
            periodo_escolar=None,
            grupo__nome="Colaboradores",
        )

    def _setup_logs_recreio(self, valor_medicao_factory):
        campos_valores = {
            "participantes": "10",
            "frequencia": "10",
            "lanche": "8",
            "lanche_4h": "8",
            "refeicao": "8",
            "repeticao_refeicao": "6",
            "sobremesa": "8",
            "repeticao_sobremesa": "6",
        }
        for dia in range(7, 11):  # 4 dias
            for nome_campo, valor in campos_valores.items():
                valor_medicao_factory.create(
                    dia=f"{dia:02d}",
                    valor=valor,
                    nome_campo=nome_campo,
                    medicao=self.medicao_recreio,
                    categoria_medicao=self.categoria_alimentacao,
                    faixa_etaria=None,
                )

    def _setup_logs_colaboradores(self, valor_medicao_factory):
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
    def test_emei_sem_imr_nao_aplica_min_na_refeicao(
        self,
        escola_factory,
        lote_factory,
        diretoria_regional_factory,
        solicitacao_medicao_inicial_factory,
        valor_medicao_factory,
        medicao_factory,
        categoria_medicao_factory,
        tipo_alimentacao_factory,
        recreio_nas_ferias_factory,
        recreio_nas_ferias_unidade_participante_factory,
        recreio_nas_ferias_unidade_tipo_alimentacao_factory,
        categoria_alimentacao_factory,
    ):
        """
        EMEI sem edital IMR: total_refeicoes = refeicao (sem min, sem repeticao).
        refeicao=8 × 4 dias = 32 (repeticao_refeicao=6 é ignorada).
        """
        self._setup_tipos_alimentacao(tipo_alimentacao_factory)
        self._setup_categorias_medicao(categoria_medicao_factory)
        self._setup_escola_emei(
            diretoria_regional_factory, lote_factory, escola_factory
        )
        # Sem contrato IMR — escola.editais retorna []
        self._setup_recreio_nas_ferias(
            recreio_nas_ferias_factory,
            recreio_nas_ferias_unidade_participante_factory,
            recreio_nas_ferias_unidade_tipo_alimentacao_factory,
            categoria_alimentacao_factory,
        )
        self._setup_solicitacao(solicitacao_medicao_inicial_factory)
        self._setup_medicoes(medicao_factory)
        self._setup_logs_recreio(valor_medicao_factory)
        self._setup_logs_colaboradores(valor_medicao_factory)

        build_tabelas = build_tabelas_relatorio_medicao(self.solicitacao)
        dict_total_refeicoes = get_total_por_periodo(
            build_tabelas, "total_refeicoes_pagamento"
        )
        dict_total_sobremesas = get_total_por_periodo(
            build_tabelas, "total_sobremesas_pagamento"
        )

        # Sem IMR: refeicao=8 × 4 dias = 32 (repeticao ignorada)
        assert dict_total_refeicoes["Recreio nas Férias"] == 32
        # Sem IMR: sobremesa=8 × 4 dias = 32 (repeticao ignorada)
        assert dict_total_sobremesas["Recreio nas Férias"] == 32
        # Colaboradores sempre usa o else (sem IMR check): min(5+5, 5) × 4 = 20
        assert dict_total_refeicoes["Colaboradores"] == 20
        assert dict_total_sobremesas["Colaboradores"] == 20

    @freeze_time("2026-01-10")
    def test_emei_com_imr_aplica_min_na_refeicao(
        self,
        escola_factory,
        lote_factory,
        diretoria_regional_factory,
        solicitacao_medicao_inicial_factory,
        valor_medicao_factory,
        medicao_factory,
        categoria_medicao_factory,
        tipo_alimentacao_factory,
        recreio_nas_ferias_factory,
        recreio_nas_ferias_unidade_participante_factory,
        recreio_nas_ferias_unidade_tipo_alimentacao_factory,
        categoria_alimentacao_factory,
        edital_factory,
        contrato_factory,
    ):
        self._setup_tipos_alimentacao(tipo_alimentacao_factory)
        self._setup_categorias_medicao(categoria_medicao_factory)
        self._setup_escola_emei(
            diretoria_regional_factory, lote_factory, escola_factory
        )

        # Associa edital IMR à escola via contrato no lote
        edital_imr = edital_factory.create(eh_imr=True)
        contrato_factory.create(
            edital=edital_imr,
            terceirizada=self.escola_emei.lote.terceirizada,
            lotes=[self.escola_emei.lote],
        )

        self._setup_recreio_nas_ferias(
            recreio_nas_ferias_factory,
            recreio_nas_ferias_unidade_participante_factory,
            recreio_nas_ferias_unidade_tipo_alimentacao_factory,
            categoria_alimentacao_factory,
        )
        self._setup_solicitacao(solicitacao_medicao_inicial_factory)
        self._setup_medicoes(medicao_factory)
        self._setup_logs_recreio(valor_medicao_factory)
        self._setup_logs_colaboradores(valor_medicao_factory)

        build_tabelas = build_tabelas_relatorio_medicao(self.solicitacao)
        dict_total_refeicoes = get_total_por_periodo(
            build_tabelas, "total_refeicoes_pagamento"
        )
        dict_total_sobremesas = get_total_por_periodo(
            build_tabelas, "total_sobremesas_pagamento"
        )

        # Com IMR: min(8 + 6, 10) = 10 × 4 dias = 40
        assert dict_total_refeicoes["Recreio nas Férias"] == 40
        # Com IMR: min(8 + 6, 10) = 10 × 4 dias = 40
        assert dict_total_sobremesas["Recreio nas Férias"] == 40
        # Colaboradores usa else (sem IMR check): min(5+5, 5) × 4 = 20
        assert dict_total_refeicoes["Colaboradores"] == 20
        assert dict_total_sobremesas["Colaboradores"] == 20
