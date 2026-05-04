import datetime

import pytest
from django.utils import timezone
from model_bakery import baker

from src.pre_recebimento.cronograma_semanal.models import (
    CronogramaSemanal,
    ProgramacaoEntregaSemanal,
)

pytestmark = pytest.mark.django_db


class TestCronogramaSemanalModel:
    def test_cria_cronograma_semanal(self, cronograma_ponto_a_ponto_assinado):
        cronograma_semanal = CronogramaSemanal.objects.create(
            cronograma_mensal=cronograma_ponto_a_ponto_assinado,
            observacoes="Teste de cronograma semanal",
        )
        assert cronograma_semanal.uuid is not None
        assert cronograma_semanal.cronograma_mensal == cronograma_ponto_a_ponto_assinado
        assert cronograma_semanal.observacoes == "Teste de cronograma semanal"

    def test_cronograma_semanal_str(self, cronograma_semanal_rascunho):
        esperado = f"Cronograma Semanal {cronograma_semanal_rascunho.uuid} - Status: {cronograma_semanal_rascunho.get_status_display()}"
        assert str(cronograma_semanal_rascunho) == esperado

    def test_status_inicial_rascunho(self, cronograma_ponto_a_ponto_assinado):
        cronograma_semanal = CronogramaSemanal.objects.create(
            cronograma_mensal=cronograma_ponto_a_ponto_assinado
        )
        assert cronograma_semanal.status == "RASCUNHO"

    def test_relacionamento_cronograma_mensal(self, cronograma_semanal_rascunho):
        assert cronograma_semanal_rascunho.cronograma_mensal is not None
        assert cronograma_semanal_rascunho.cronograma_mensal.ponto_a_ponto is True

    def test_cronograma_semanal_tem_identificador_externo(
        self, cronograma_ponto_a_ponto_assinado
    ):
        cronograma_semanal = CronogramaSemanal.objects.create(
            cronograma_mensal=cronograma_ponto_a_ponto_assinado
        )
        assert hasattr(cronograma_semanal, "id_externo")
        assert cronograma_semanal.id_externo == str(cronograma_semanal.uuid).upper()[:5]

    def test_cronograma_semanal_tem_logs(self, cronograma_ponto_a_ponto_assinado):
        cronograma_semanal = CronogramaSemanal.objects.create(
            cronograma_mensal=cronograma_ponto_a_ponto_assinado
        )
        assert hasattr(cronograma_semanal, "criado_em")
        assert hasattr(cronograma_semanal, "alterado_em")

    def test_observacoes_blank(self, cronograma_ponto_a_ponto_assinado):
        cronograma_semanal = CronogramaSemanal.objects.create(
            cronograma_mensal=cronograma_ponto_a_ponto_assinado
        )
        assert cronograma_semanal.observacoes == ""

    def test_verbose_name(self):
        assert CronogramaSemanal._meta.verbose_name == "Cronograma Semanal"
        assert CronogramaSemanal._meta.verbose_name_plural == "Cronogramas Semanais"


class TestProgramacaoEntregaSemanalModel:
    def test_cria_programacao_entrega_semanal(self, cronograma_semanal_rascunho):
        data_inicio = timezone.now().date()
        data_fim = data_inicio + datetime.timedelta(days=10)

        programacao = ProgramacaoEntregaSemanal.objects.create(
            cronograma_semanal=cronograma_semanal_rascunho,
            mes_programado="03/2026",
            data_inicio=data_inicio,
            data_fim=data_fim,
            quantidade=150.5,
        )
        assert programacao.uuid is not None
        assert programacao.mes_programado == "03/2026"
        assert programacao.quantidade == 150.5

    def test_programacao_entrega_semanal_str(self, programacao_entrega_semanal):
        esperado = f"Programação {programacao_entrega_semanal.mes_programado} - {programacao_entrega_semanal.data_inicio} a {programacao_entrega_semanal.data_fim}"
        assert str(programacao_entrega_semanal) == esperado

    def test_relacionamento_cronograma_semanal(self, programacao_entrega_semanal):
        assert programacao_entrega_semanal.cronograma_semanal is not None

    def test_programacoes_related_name(self, cronograma_semanal_rascunho):
        baker.make(
            ProgramacaoEntregaSemanal,
            cronograma_semanal=cronograma_semanal_rascunho,
            mes_programado="01/2026",
            _quantity=3,
        )
        assert cronograma_semanal_rascunho.programacoes.count() == 3

    def test_ordenacao_programacoes(self, cronograma_semanal_rascunho):
        data_base = timezone.now().date()
        baker.make(
            ProgramacaoEntregaSemanal,
            cronograma_semanal=cronograma_semanal_rascunho,
            mes_programado="04/2026",
            data_inicio=data_base,
            _quantity=1,
        )
        baker.make(
            ProgramacaoEntregaSemanal,
            cronograma_semanal=cronograma_semanal_rascunho,
            mes_programado="03/2026",
            data_inicio=data_base,
            _quantity=1,
        )
        baker.make(
            ProgramacaoEntregaSemanal,
            cronograma_semanal=cronograma_semanal_rascunho,
            mes_programado="02/2026",
            data_inicio=data_base,
            _quantity=1,
        )

        programacoes = list(cronograma_semanal_rascunho.programacoes.all())
        assert programacoes[0].mes_programado == "02/2026"
        assert programacoes[1].mes_programado == "03/2026"
        assert programacoes[2].mes_programado == "04/2026"

    def test_verbose_name(self):
        assert (
            ProgramacaoEntregaSemanal._meta.verbose_name
            == "Programação de Entrega Semanal"
        )
        assert (
            ProgramacaoEntregaSemanal._meta.verbose_name_plural
            == "Programações de Entrega Semanal"
        )

    def test_campos_obrigatorios(self, cronograma_semanal_rascunho):
        programacao = ProgramacaoEntregaSemanal.objects.create(
            cronograma_semanal=cronograma_semanal_rascunho,
            mes_programado="05/2026",
            data_inicio=timezone.now().date(),
            data_fim=timezone.now().date() + datetime.timedelta(days=5),
            quantidade=100.0,
        )
        assert programacao.mes_programado == "05/2026"
        assert programacao.data_inicio is not None
        assert programacao.data_fim is not None
        assert programacao.quantidade == 100.0
