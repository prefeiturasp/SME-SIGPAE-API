import datetime

import pytest
from freezegun import freeze_time

from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.medicao_inicial.utils import (
    build_tabela_somatorio_body,
    build_tabelas_relatorio_medicao,
)
from sme_sigpae_api.relatorios.relatorios import get_total_por_periodo

pytestmark = pytest.mark.django_db


@freeze_time("2025-09-01")
class TestUseCaseRelatorioPDFMedicaoEscolaSemAlunosRegulares:
    def _setup_periodos_escolares(self, periodo_escolar_factory):
        self.periodo_tarde = periodo_escolar_factory.create(nome="TARDE")
        self.periodo_noite = periodo_escolar_factory.create(nome="NOITE")

    def _setup_tipos_alimentacao(self, tipo_alimentacao_factory):
        self.tipo_alimentacao_lanche = tipo_alimentacao_factory.create(nome="Lanche")
        self.tipo_alimentacao_refeicao = tipo_alimentacao_factory.create(
            nome="Refeição"
        )
        self.tipo_alimentacao_sobremesa = tipo_alimentacao_factory.create(
            nome="Sobremesa"
        )

    def _setup_classificacoes_dieta_especial(self, classificacao_dieta_factory):
        self.classificacao_tipo_a_enteral = classificacao_dieta_factory.create(
            nome="Tipo A ENTERAL"
        )
        self.classificacao_tipo_b = classificacao_dieta_factory.create(nome="Tipo B")

    def _setup_categorias_medicao(self, categoria_medicao_factory):
        self.categoria_medicao_dieta_tipo_a_enteral_aminoacidos = (
            categoria_medicao_factory.create(
                nome="DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
            )
        )
        self.categoria_medicao_dieta_tipo_b = categoria_medicao_factory.create(
            nome="DIETA ESPECIAL - TIPO B"
        )
        self.categoria_solicitacoes_alimentacao = categoria_medicao_factory.create(
            nome="SOLICITAÇÕES DE ALIMENTAÇÃO"
        )
        self.categoria_alimentacao = categoria_medicao_factory.create(
            nome="ALIMENTAÇÃO"
        )

    def _setup_core(
        self,
        periodo_escolar_factory,
        classificacao_dieta_factory,
        categoria_medicao_factory,
        tipo_alimentacao_factory,
    ):
        self._setup_periodos_escolares(periodo_escolar_factory)
        self._setup_classificacoes_dieta_especial(classificacao_dieta_factory)
        self._setup_tipos_alimentacao(tipo_alimentacao_factory)
        self._setup_categorias_medicao(categoria_medicao_factory)

    def _setup_escola_cmct(
        self, diretoria_regional_factory, lote_factory, escola_factory
    ):
        self.dre = diretoria_regional_factory.create()
        self.lote = lote_factory.create(diretoria_regional=self.dre)
        self.escola_cmct = escola_factory.create(
            nome="CMCT VALDYR",
            tipo_gestao__nome="TERC TOTAL",
            lote=self.lote,
            diretoria_regional=self.dre,
        )

    def _setup_usuario_escola(self, usuario_factory, vinculo_factory):
        self.usuario_escola = usuario_factory.create()
        self.vinculo_escola_diretor = vinculo_factory.create(
            usuario=self.usuario_escola,
            object_id=self.escola_cmct.id,
            instituicao=self.escola_cmct,
            perfil__nome="DIRETOR_UE",
            data_inicial="2025-09-01",
            data_final=None,
            ativo=True,
        )

    def _setup_inclusao_normal(
        self,
        grupo_inclusao_alimentacao_normal_factory,
        inclusao_alimentacao_normal_factory,
        quantidade_por_periodo_factory,
        log_solicitacoes_usuario_factory,
    ):
        self.grupo_inclusao_alimentacao_normal = (
            grupo_inclusao_alimentacao_normal_factory.create(
                escola=self.escola_cmct,
                rastro_lote=self.lote,
                rastro_dre=self.dre,
                rastro_escola=self.escola_cmct,
                status=PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
            )
        )
        inclusao_alimentacao_normal_factory.create(
            data="2025-09-02",
            grupo_inclusao=self.grupo_inclusao_alimentacao_normal,
        )
        quantidade_por_periodo_factory.create(
            grupo_inclusao_normal=self.grupo_inclusao_alimentacao_normal,
            inclusao_alimentacao_continua=None,
            periodo_escolar=self.periodo_tarde,
            numero_alunos=100,
            tipos_alimentacao=[self.tipo_alimentacao_refeicao],
        )
        quantidade_por_periodo_factory.create(
            grupo_inclusao_normal=self.grupo_inclusao_alimentacao_normal,
            inclusao_alimentacao_continua=None,
            periodo_escolar=self.periodo_noite,
            numero_alunos=100,
            tipos_alimentacao=[self.tipo_alimentacao_sobremesa],
        )
        log_solicitacoes_usuario_factory.create(
            uuid_original=self.grupo_inclusao_alimentacao_normal.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            usuario=self.usuario_escola,
        )

    def _setup_inclusao_continua(
        self,
        motivo_inclusao_continua_factory,
        inclusao_alimentacao_continua_factory,
        quantidade_por_periodo_factory,
        log_solicitacoes_usuario_factory,
    ):
        self.motivo_inclusao_continua = motivo_inclusao_continua_factory.create(
            nome="Programas e Projetos"
        )
        self.inclusao_continua = inclusao_alimentacao_continua_factory.create(
            escola=self.escola_cmct,
            motivo=self.motivo_inclusao_continua,
            rastro_escola=self.escola_cmct,
            rastro_lote=self.lote,
            rastro_dre=self.dre,
            rastro_terceirizada=self.escola_cmct.lote.terceirizada,
            data_inicial=datetime.date(2025, 9, 1),
            data_final=datetime.date(2025, 9, 30),
            status="CODAE_AUTORIZADO",
        )
        quantidade_por_periodo_factory.create(
            numero_alunos=10,
            periodo_escolar=self.periodo_noite,
            inclusao_alimentacao_continua=self.inclusao_continua,
            dias_semana=[0, 1, 2, 3, 4, 5, 6],
            tipos_alimentacao=[self.tipo_alimentacao_sobremesa],
        )
        log_solicitacoes_usuario_factory.create(
            uuid_original=self.inclusao_continua.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            usuario=self.usuario_escola,
        )

    def _setup_solicitacao_medicao_inicial(self, solicitacao_medicao_inicial_factory):
        self.solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory.create(
            escola=self.escola_cmct, mes="09", ano="2025"
        )

    def _setup_medicao_tarde(self, medicao_factory):
        self.medicao_tarde = medicao_factory.create(
            solicitacao_medicao_inicial=self.solicitacao_medicao_inicial,
            periodo_escolar=self.periodo_tarde,
            grupo=None,
        )

    def _setup_logs_medicao_tarde_alimentacao(self, valor_medicao_factory):
        for nome_campo in [
            "numero_de_alunos",
            "frequencia",
            "refeicao",
            "repeticao_refeicao",
        ]:
            valor_medicao_factory.create(
                dia="02",
                valor="100",
                nome_campo=nome_campo,
                medicao=self.medicao_tarde,
                categoria_medicao=self.categoria_alimentacao,
                faixa_etaria=None,
            )

    def _setup_logs_medicao_tarde_dieta_tipo_a_enteral_aminoacidos(
        self, log_quantidade_dietas_autorizadas_factory, valor_medicao_factory
    ):
        for i in range(1, 31):
            log_quantidade_dietas_autorizadas_factory.create(
                escola=self.escola_cmct,
                quantidade=2,
                classificacao=self.classificacao_tipo_a_enteral,
                periodo_escolar=None,
                data=datetime.date(2025, 9, i),
            )
            valor_medicao_factory.create(
                dia=f"{i:02d}",
                valor="2",
                nome_campo="dietas_autorizadas",
                medicao=self.medicao_tarde,
                categoria_medicao=self.categoria_medicao_dieta_tipo_a_enteral_aminoacidos,
                faixa_etaria=None,
            )
        for nome_campo in ["frequencia", "refeicao"]:
            valor_medicao_factory.create(
                dia="02",
                valor="2",
                nome_campo=nome_campo,
                medicao=self.medicao_tarde,
                categoria_medicao=self.categoria_medicao_dieta_tipo_a_enteral_aminoacidos,
                faixa_etaria=None,
            )

    def _setup_medicao_noite(self, medicao_factory):
        self.medicao_noite = medicao_factory.create(
            solicitacao_medicao_inicial=self.solicitacao_medicao_inicial,
            periodo_escolar=self.periodo_noite,
            grupo=None,
        )

    def _setup_logs_medicao_noite_alimentacao(self, valor_medicao_factory):
        for nome_campo in [
            "numero_de_alunos",
            "frequencia",
            "sobremesa",
            "repeticao_sobremesa",
        ]:
            valor_medicao_factory.create(
                dia="02",
                valor="100",
                nome_campo=nome_campo,
                medicao=self.medicao_noite,
                categoria_medicao=self.categoria_alimentacao,
                faixa_etaria=None,
            )

    def _setup_medicao_programas_projetos(self, medicao_factory):
        self.medicao_programas_projetos = medicao_factory.create(
            solicitacao_medicao_inicial=self.solicitacao_medicao_inicial,
            periodo_escolar=None,
            grupo__nome="Programas e Projetos",
        )

    def _setup_logs_medicao_inclusao_continua(
        self, valor_medicao_factory, dia_calendario_factory
    ):
        for i in range(1, 31):
            dia_calendario_factory.create(
                escola=self.escola_cmct, data=datetime.date(2025, 9, i), dia_letivo=True
            )
            for nome_campo in [
                "numero_de_alunos",
                "frequencia",
                "sobremesa",
                "repeticao_sobremesa",
            ]:
                valor_medicao_factory.create(
                    dia=f"{i:02d}",
                    valor="10",
                    nome_campo=nome_campo,
                    medicao=self.medicao_programas_projetos,
                    categoria_medicao=self.categoria_alimentacao,
                    faixa_etaria=None,
                )

    @freeze_time("2025-09-01")
    def test_relatorio_solicitacao_medicao_por_escola_sem_alunos_regulares(
        self,
        escola_factory,
        lote_factory,
        diretoria_regional_factory,
        solicitacao_medicao_inicial_factory,
        classificacao_dieta_factory,
        periodo_escolar_factory,
        log_quantidade_dietas_autorizadas_factory,
        valor_medicao_factory,
        medicao_factory,
        categoria_medicao_factory,
        grupo_inclusao_alimentacao_normal_factory,
        quantidade_por_periodo_factory,
        inclusao_alimentacao_normal_factory,
        log_solicitacoes_usuario_factory,
        usuario_factory,
        vinculo_factory,
        tipo_alimentacao_factory,
        motivo_inclusao_continua_factory,
        inclusao_alimentacao_continua_factory,
        dia_calendario_factory,
    ):
        self._setup_core(
            periodo_escolar_factory,
            classificacao_dieta_factory,
            categoria_medicao_factory,
            tipo_alimentacao_factory,
        )
        self._setup_escola_cmct(
            diretoria_regional_factory, lote_factory, escola_factory
        )
        self._setup_usuario_escola(usuario_factory, vinculo_factory)
        self._setup_inclusao_normal(
            grupo_inclusao_alimentacao_normal_factory,
            inclusao_alimentacao_normal_factory,
            quantidade_por_periodo_factory,
            log_solicitacoes_usuario_factory,
        )

        self._setup_solicitacao_medicao_inicial(solicitacao_medicao_inicial_factory)

        self._setup_medicao_tarde(medicao_factory)
        self._setup_logs_medicao_tarde_alimentacao(valor_medicao_factory)
        self._setup_logs_medicao_tarde_dieta_tipo_a_enteral_aminoacidos(
            log_quantidade_dietas_autorizadas_factory, valor_medicao_factory
        )

        self._setup_medicao_noite(medicao_factory)
        self._setup_logs_medicao_noite_alimentacao(valor_medicao_factory)

        self._setup_inclusao_continua(
            motivo_inclusao_continua_factory,
            inclusao_alimentacao_continua_factory,
            quantidade_por_periodo_factory,
            log_solicitacoes_usuario_factory,
        )
        self._setup_medicao_programas_projetos(medicao_factory)
        self._setup_logs_medicao_inclusao_continua(
            valor_medicao_factory, dia_calendario_factory
        )

        build_tabelas = build_tabelas_relatorio_medicao(
            self.solicitacao_medicao_inicial
        )
        assert any(
            item.get("periodos") == ["TARDE"] for item in build_tabelas
        ), "Nenhum item com periodos=['TARDE'] encontrado"
        assert any(
            item.get("periodos") == ["NOITE"] for item in build_tabelas
        ), "Nenhum item com periodos=['NOITE'] encontrado"
        assert any(
            item.get("periodos") == ["Programas e Projetos"] for item in build_tabelas
        ), "Nenhum item com periodos=['Programas e Projetos'] encontrado"

        dict_total_refeicoes = get_total_por_periodo(
            build_tabelas, "total_refeicoes_pagamento"
        )
        assert dict_total_refeicoes == {
            "NOITE": 0,
            "Programas e Projetos": 0,
            "TARDE": 100,
        }

        dict_total_sobremesas = get_total_por_periodo(
            build_tabelas, "total_sobremesas_pagamento"
        )
        assert dict_total_sobremesas == {
            "TARDE": 0,
            "NOITE": 100,
            "Programas e Projetos": 300,
        }

        primeira_tabela_somatorio, segunda_tabela_somatorio = (
            build_tabela_somatorio_body(
                self.solicitacao_medicao_inicial,
                dict_total_refeicoes,
                dict_total_sobremesas,
            )
        )
        assert primeira_tabela_somatorio == {
            "header": [
                "TIPOS DE ALIMENTAÇÃO",
                "TARDE",
                "Programas e Projetos",
                "TOTAL",
            ],
            "body": [["Refeição", 100, 0, 100], ["Sobremesa", 0, 300, 300]],
        }
        assert segunda_tabela_somatorio == {
            "header": ["NOITE", "TOTAL"],
            "body": [[0, 0], [100, 100]],
        }
