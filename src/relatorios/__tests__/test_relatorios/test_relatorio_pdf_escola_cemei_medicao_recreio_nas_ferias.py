import datetime

import pytest
from freezegun import freeze_time
from model_bakery import baker

from src.medicao_inicial.utils import (
    build_tabela_somatorio_body_cemei_recreio_nas_ferias,
)

pytestmark = pytest.mark.django_db


@freeze_time("2026-01-10")
class TestUseCaseRelatorioPDFMedicaoEscolaRecreioNasFeriasCEMEI:
    def _setup_recreio_nas_ferias(self, escola_cemei):
        self.recreio = baker.make(
            "RecreioNasFerias",
            titulo="Recreio nas Férias - Jan 2026",
            data_inicio=datetime.date(2026, 1, 7),
            data_fim=datetime.date(2026, 1, 23),
        )
        baker.make(
            "RecreioNasFeriasUnidadeParticipante",
            recreio_nas_ferias=self.recreio,
            lote=escola_cemei.lote,
            unidade_educacional=escola_cemei,
            num_inscritos=10,
            num_colaboradores=5,
            liberar_medicao=True,
            cei_ou_emei="N/A",  # Ajustado para N/A
        )

    def _setup_solicitacao(self, solicitacao_medicao_inicial_factory, escola_cemei):
        self.solicitacao = solicitacao_medicao_inicial_factory.create(
            escola=escola_cemei,
            mes="01",
            ano="2026",
            recreio_nas_ferias=self.recreio,
            rastro_lote=escola_cemei.lote,
        )

    def _setup_categorias(self, categoria_medicao_factory):
        self.categoria_alimentacao = categoria_medicao_factory.create(
            nome="ALIMENTAÇÃO"
        )
        self.categoria_dieta_a = categoria_medicao_factory.create(
            nome="DIETA TIPO A"
        )
        self.categoria_dieta_b = categoria_medicao_factory.create(
            nome="DIETA TIPO B"
        )

    def _setup_medicoes(self, medicao_factory):
        self.medicao_0a3 = medicao_factory.create(
            solicitacao_medicao_inicial=self.solicitacao,
            periodo_escolar=None,
            grupo__nome="Recreio nas Férias - de 0 a 3 anos e 11 meses",
        )
        self.medicao_4a14 = medicao_factory.create(
            solicitacao_medicao_inicial=self.solicitacao,
            periodo_escolar=None,
            grupo__nome="Recreio nas Férias - 4 a 14 anos",
        )
        self.medicao_colaboradores = medicao_factory.create(
            solicitacao_medicao_inicial=self.solicitacao,
            periodo_escolar=None,
            grupo__nome="Colaboradores",
        )

    def _setup_faixas_etarias(self):
        self.faixa_1 = baker.make(
            "FaixaEtaria",
            inicio=0,
            fim=11,
            ativo=True,
        )
        self.faixa_2 = baker.make(
            "FaixaEtaria",
            inicio=12,
            fim=35,
            ativo=True,
        )

    def _setup_logs_0a3(self, valor_medicao_factory):
        # Faixa 1: alimentação 10/dia, dieta A 2/dia — 4 dias
        # Faixa 2: alimentação 5/dia, dieta B 1/dia — 4 dias
        for dia in range(7, 11):
            valor_medicao_factory.create(
                dia=f"{dia:02d}",
                valor="10",
                nome_campo="frequencia",
                medicao=self.medicao_0a3,
                categoria_medicao=self.categoria_alimentacao,
                faixa_etaria=self.faixa_1,
            )
            valor_medicao_factory.create(
                dia=f"{dia:02d}",
                valor="2",
                nome_campo="frequencia",
                medicao=self.medicao_0a3,
                categoria_medicao=self.categoria_dieta_a,
                faixa_etaria=self.faixa_1,
            )
            valor_medicao_factory.create(
                dia=f"{dia:02d}",
                valor="5",
                nome_campo="frequencia",
                medicao=self.medicao_0a3,
                categoria_medicao=self.categoria_alimentacao,
                faixa_etaria=self.faixa_2,
            )
            valor_medicao_factory.create(
                dia=f"{dia:02d}",
                valor="1",
                nome_campo="frequencia",
                medicao=self.medicao_0a3,
                categoria_medicao=self.categoria_dieta_b,
                faixa_etaria=self.faixa_2,
            )

    def _setup_logs_4a14(self, valor_medicao_factory):
        # 4 dias: lanche=80/dia, refeicao=50/dia, sobremesa=40/dia
        # dieta A: lanche=5/dia
        # dieta B: lanche=3/dia
        for dia in range(7, 11):
            for nome_campo, valor in [("lanche", "80"), ("refeicao", "50"), ("sobremesa", "40")]:
                valor_medicao_factory.create(
                    dia=f"{dia:02d}",
                    valor=valor,
                    nome_campo=nome_campo,
                    medicao=self.medicao_4a14,
                    categoria_medicao=self.categoria_alimentacao,
                    faixa_etaria=None,
                )
            valor_medicao_factory.create(
                dia=f"{dia:02d}",
                valor="5",
                nome_campo="lanche",
                medicao=self.medicao_4a14,
                categoria_medicao=self.categoria_dieta_a,
                faixa_etaria=None,
            )
            valor_medicao_factory.create(
                dia=f"{dia:02d}",
                valor="3",
                nome_campo="lanche",
                medicao=self.medicao_4a14,
                categoria_medicao=self.categoria_dieta_b,
                faixa_etaria=None,
            )

    def _setup_logs_colaboradores(self, valor_medicao_factory):
        # 4 dias:
        # lanche = 5/dia => 20
        # refeicao pgto = min(3 + 4, 5) = 5/dia => 20
        # sobremesa pgto = min(2 + 5, 5) = 5/dia => 20
        for dia in range(7, 11):
            for nome_campo, valor in {
                "participantes": "5",
                "frequencia": "5",
                "lanche": "5",
                "refeicao": "3",
                "repeticao_refeicao": "4",
                "sobremesa": "2",
                "repeticao_sobremesa": "5",
            }.items():
                valor_medicao_factory.create(
                    dia=f"{dia:02d}",
                    valor=valor,
                    nome_campo=nome_campo,
                    medicao=self.medicao_colaboradores,
                    categoria_medicao=self.categoria_alimentacao,
                    faixa_etaria=None,
                )

    def test_somatorio_cemei_recreio_nas_ferias_completo(
        self,
        escola_cemei,
        solicitacao_medicao_inicial_factory,
        valor_medicao_factory,
        medicao_factory,
        categoria_medicao_factory,
    ):
        self._setup_recreio_nas_ferias(escola_cemei)
        self._setup_solicitacao(solicitacao_medicao_inicial_factory, escola_cemei)
        self._setup_categorias(categoria_medicao_factory)
        self._setup_medicoes(medicao_factory)
        self._setup_faixas_etarias()
        self._setup_logs_0a3(valor_medicao_factory)
        self._setup_logs_4a14(valor_medicao_factory)
        self._setup_logs_colaboradores(valor_medicao_factory)

        somatorio = build_tabela_somatorio_body_cemei_recreio_nas_ferias(self.solicitacao)

        # --- tabela_cei: 0 a 3 anos ---
        assert somatorio["tabela_cei"] == {
            "titulo": "Alimentações para alunos - de 0 a 3 anos e 11 meses",
            "header": [
                "Faixa Etária",
                "Alimentação",
                "DIETA TIPO A",
                "DIETA TIPO B",
                "Total por Faixa Etária",
            ],
            "valores_campos": [
                [str(self.faixa_1), "40", "8", "0", "48"],
                [str(self.faixa_2), "20", "0", "4", "24"],
                ["Total", "60", "8", "4", "72"],
            ],
            "legenda": "*A tabela acima representa a soma das alimentações lançadas para os alunos em Recreio nas Férias - 01/2026",
        }

        # --- tabela_emei: 4 a 14 anos ---
        assert somatorio["tabela_emei"] == {
            "titulo": "Alimentações para alunos - de 4 a 14 anos",
            "header": [
                "Tipos de Alimentação",
                "Total de Alimentações",
                "DIETA TIPO A",
                "DIETA TIPO B",
                "Solicitações de Alimentação",
            ],
            "valores_campos": [
                ["Lanche", "320", "20", "12", "0"],
                ["Refeição", "200", "0", "0", "0"],
                ["Sobremesa", "160", "0", "0", "0"],
            ],
            "legenda": "*A tabela acima representa a soma das alimentações lançadas para os alunos em Recreio nas Férias - 01/2026",
        }

        # --- tabela_colaboradores: colaboradores ---
        assert somatorio["tabela_colaboradores"] == {
            "header": [
                "Tipos de Alimentação",
                "Total de Alimentações para Colaboradores",
            ],
            "valores_campos": [
                ["Lanche", "20"],
                ["Refeição", "20"],
                ["Sobremesa", "20"],
            ],
            "legenda": "*A tabela acima representa a soma das alimentações lançadas para os colaboradores em Recreio nas Férias - 01/2026",
        }

    def test_somatorio_cemei_recreio_nas_ferias_sem_dieta_nao_exibe_colunas_dieta(
        self,
        escola_cemei,
        solicitacao_medicao_inicial_factory,
        valor_medicao_factory,
        medicao_factory,
        categoria_medicao_factory,
    ):
        self._setup_recreio_nas_ferias(escola_cemei)
        self._setup_solicitacao(solicitacao_medicao_inicial_factory, escola_cemei)
        self._setup_categorias(categoria_medicao_factory)
        self._setup_medicoes(medicao_factory)
        self._setup_faixas_etarias()

        # Apenas ALIMENTAÇÃO, sem dietas
        for dia in range(7, 11):
            valor_medicao_factory.create(
                dia=f"{dia:02d}",
                valor="10",
                nome_campo="frequencia",
                medicao=self.medicao_0a3,
                categoria_medicao=self.categoria_alimentacao,
                faixa_etaria=self.faixa_1,
            )
            for nome_campo, valor in [("lanche", "80"), ("refeicao", "50")]:
                valor_medicao_factory.create(
                    dia=f"{dia:02d}",
                    valor=valor,
                    nome_campo=nome_campo,
                    medicao=self.medicao_4a14,
                    categoria_medicao=self.categoria_alimentacao,
                    faixa_etaria=None,
                )

        somatorio = build_tabela_somatorio_body_cemei_recreio_nas_ferias(self.solicitacao)

        assert somatorio["tabela_cei"]["header"] == [
            "Faixa Etária",
            "Alimentação",
            "Total por Faixa Etária",
        ]
        assert "DIETA TIPO A" not in somatorio["tabela_cei"]["header"]
        assert "DIETA TIPO B" not in somatorio["tabela_cei"]["header"]

        assert somatorio["tabela_emei"]["header"] == [
            "Tipos de Alimentação",
            "Total de Alimentações",
            "Solicitações de Alimentação",
        ]
        assert "DIETA TIPO A" not in somatorio["tabela_emei"]["header"]
        assert "DIETA TIPO B" not in somatorio["tabela_emei"]["header"]
