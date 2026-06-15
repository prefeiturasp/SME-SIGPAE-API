import datetime

import pytest
from freezegun import freeze_time
from model_bakery import baker

from src.medicao_inicial.utils import (
    build_tabela_somatorio_body_cei_recreio_nas_ferias,
    build_tabelas_relatorio_medicao,
)
from src.relatorios.relatorios import get_total_por_periodo

pytestmark = pytest.mark.django_db


@freeze_time("2026-01-10")
class TestUseCaseRelatorioPDFMedicaoEscolaRecreioNasFeriasCEI:
    def _setup_recreio_nas_ferias(self, escola_cei):
        self.recreio = baker.make(
            "RecreioNasFerias",
            titulo="Recreio nas Férias - Jan 2026",
            data_inicio=datetime.date(2026, 1, 7),
            data_fim=datetime.date(2026, 1, 23),
        )
        baker.make(
            "RecreioNasFeriasUnidadeParticipante",
            recreio_nas_ferias=self.recreio,
            lote=escola_cei.lote,
            unidade_educacional=escola_cei,
            num_inscritos=10,
            num_colaboradores=5,
            liberar_medicao=True,
            cei_ou_emei="CEI",
        )

    def _setup_solicitacao(self, solicitacao_medicao_inicial_factory, escola_cei):
        self.solicitacao = solicitacao_medicao_inicial_factory.create(
            escola=escola_cei,
            mes="01",
            ano="2026",
            recreio_nas_ferias=self.recreio,
            rastro_lote=escola_cei.lote,
        )

    def _setup_categorias(self, categoria_medicao_factory):
        self.categoria_alimentacao = categoria_medicao_factory.create(
            nome="ALIMENTAÇÃO"
        )
        self.categoria_dieta_a = categoria_medicao_factory.create(
            nome="DIETA ESPECIAL - TIPO A"
        )
        self.categoria_dieta_b = categoria_medicao_factory.create(
            nome="DIETA ESPECIAL - TIPO B"
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

    def _setup_logs_recreio(self, valor_medicao_factory):
        # Faixa 1: alimentação 10/dia, dieta A 2/dia
        for dia in range(7, 11):
            valor_medicao_factory.create(
                dia=f"{dia:02d}",
                valor="10",
                nome_campo="frequencia",
                medicao=self.medicao_recreio,
                categoria_medicao=self.categoria_alimentacao,
                faixa_etaria=self.faixa_1,
            )
            valor_medicao_factory.create(
                dia=f"{dia:02d}",
                valor="2",
                nome_campo="frequencia",
                medicao=self.medicao_recreio,
                categoria_medicao=self.categoria_dieta_a,
                faixa_etaria=self.faixa_1,
            )

        # Faixa 2: alimentação 5/dia, dieta B 1/dia
        for dia in range(7, 11):
            valor_medicao_factory.create(
                dia=f"{dia:02d}",
                valor="5",
                nome_campo="frequencia",
                medicao=self.medicao_recreio,
                categoria_medicao=self.categoria_alimentacao,
                faixa_etaria=self.faixa_2,
            )
            valor_medicao_factory.create(
                dia=f"{dia:02d}",
                valor="1",
                nome_campo="frequencia",
                medicao=self.medicao_recreio,
                categoria_medicao=self.categoria_dieta_b,
                faixa_etaria=self.faixa_2,
            )

    def _setup_logs_colaboradores(self, valor_medicao_factory):
        # 4 dias:
        # lanche = 5/dia => 20
        # refeicao pgto = min(3 + 4, 5) = 5/dia => 20
        # sobremesa pgto = min(2 + 5, 5) = 5/dia => 20
        for dia in range(7, 11):
            campos_valores = {
                "participantes": "5",
                "frequencia": "5",
                "lanche": "5",
                "refeicao": "3",
                "repeticao_refeicao": "4",
                "sobremesa": "2",
                "repeticao_sobremesa": "5",
            }
            for nome_campo, valor in campos_valores.items():
                valor_medicao_factory.create(
                    dia=f"{dia:02d}",
                    valor=valor,
                    nome_campo=nome_campo,
                    medicao=self.medicao_colaboradores,
                    categoria_medicao=self.categoria_alimentacao,
                    faixa_etaria=None,
                )

    def test_relatorio_solicitacao_medicao_por_escola_recreio_nas_ferias_cei(
        self,
        escola_cei,
        solicitacao_medicao_inicial_factory,
        valor_medicao_factory,
        medicao_factory,
        categoria_medicao_factory,
    ):
        self._setup_recreio_nas_ferias(escola_cei)
        self._setup_solicitacao(solicitacao_medicao_inicial_factory, escola_cei)
        self._setup_categorias(categoria_medicao_factory)
        self._setup_medicoes(medicao_factory)
        self._setup_faixas_etarias()
        self._setup_logs_recreio(valor_medicao_factory)
        self._setup_logs_colaboradores(valor_medicao_factory)

        build_tabelas = build_tabelas_relatorio_medicao(self.solicitacao)

        assert any(
            item.get("periodos") == ["Recreio nas Férias"] for item in build_tabelas
        )
        assert any(
            item.get("periodos") == ["Colaboradores"] for item in build_tabelas
        )

        dict_total_refeicoes = get_total_por_periodo(
            build_tabelas, "total_refeicoes_pagamento"
        )
        dict_total_sobremesas = get_total_por_periodo(
            build_tabelas, "total_sobremesas_pagamento"
        )

        assert dict_total_refeicoes["Colaboradores"] == 20
        assert dict_total_sobremesas["Colaboradores"] == 20

        somatorio = build_tabela_somatorio_body_cei_recreio_nas_ferias(
            self.solicitacao
        )

        assert somatorio["tabela_alimentacao"] == {
            "header": [
                "Faixa Etária",
                "Alimentação",
                "DIETA ESPECIAL - TIPO A",
                "DIETA ESPECIAL - TIPO B",
                "Total por Faixa Etária",
            ],
            "valores_campos": [
                [str(self.faixa_1), "40", "8", "0", "48"],
                [str(self.faixa_2), "20", "0", "4", "24"],
                ["Total", "60", "8", "4", "72"],
            ],
            "legenda": "*A tabela acima representa a soma das alimentações lançadas para os alunos em Recreio nas Férias - 01/2026",
        }

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

    def test_somatorio_cei_recreio_nas_ferias_sem_dieta_nao_exibe_colunas_de_dieta(
        self,
        escola_cei,
        solicitacao_medicao_inicial_factory,
        valor_medicao_factory,
        medicao_factory,
        categoria_medicao_factory,
    ):
        self._setup_recreio_nas_ferias(escola_cei)
        self._setup_solicitacao(solicitacao_medicao_inicial_factory, escola_cei)
        self._setup_categorias(categoria_medicao_factory)
        self._setup_medicoes(medicao_factory)
        self._setup_faixas_etarias()

        # Cria somente ALIMENTAÇÃO, sem nenhuma DIETA
        for dia in range(7, 11):
            valor_medicao_factory.create(
                dia=f"{dia:02d}",
                valor="10",
                nome_campo="frequencia",
                medicao=self.medicao_recreio,
                categoria_medicao=self.categoria_alimentacao,
                faixa_etaria=self.faixa_1,
            )
            valor_medicao_factory.create(
                dia=f"{dia:02d}",
                valor="5",
                nome_campo="frequencia",
                medicao=self.medicao_recreio,
                categoria_medicao=self.categoria_alimentacao,
                faixa_etaria=self.faixa_2,
            )

        somatorio = build_tabela_somatorio_body_cei_recreio_nas_ferias(
            self.solicitacao
        )

        tabela_alimentacao = somatorio["tabela_alimentacao"]

        assert tabela_alimentacao["header"] == [
            "Faixa Etária",
            "Alimentação",
            "Total por Faixa Etária",
        ]

        assert "DIETA ESPECIAL - TIPO A" not in tabela_alimentacao["header"]
        assert "DIETA ESPECIAL - TIPO B" not in tabela_alimentacao["header"]

        assert tabela_alimentacao["valores_campos"] == [
            [str(self.faixa_1), "40", "40"],
            [str(self.faixa_2), "20", "20"],
            ["Total", "60", "60"],
        ]
