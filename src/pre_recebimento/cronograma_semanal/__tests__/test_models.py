import datetime

import pytest
from django.utils import timezone
from model_bakery import baker

from src.pre_recebimento.cronograma_semanal.models import (
    CronogramaSemanal,
    ProgramacaoEntregaSemanal,
)
from src.pre_recebimento.cronograma_entrega.models import EtapasDoCronograma

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


class TestEtapasDoCronogramaQuantidadeEstimada:
    """Testes para a propriedade quantidade_estimada_disponivel de EtapasDoCronograma.

    A propriedade calcula: quantidade_original - soma(ProgramacaoEntregaSemanal.quantidade)
    para o mesmo cronograma e mesmo mês (data_programada).
    """

    def test_sem_programacoes_semanais_retorna_quantidade_original(
        self, cronograma_ponto_a_ponto_com_etapas
    ):
        """Cenário: nenhuma programação semanal → restante = quantidade original."""
        etapa = EtapasDoCronograma.objects.filter(
            cronograma=cronograma_ponto_a_ponto_com_etapas
        ).first()
        assert etapa.quantidade_estimada_disponivel == etapa.quantidade

    def test_com_uma_programacao_parcial(
        self, cronograma_ponto_a_ponto_com_etapas
    ):
        """Cenário: uma programação semanal com valor menor que o original."""
        etapa = EtapasDoCronograma.objects.filter(
            cronograma=cronograma_ponto_a_ponto_com_etapas,
            data_programada="2026-03-01",
        ).first()
        mes = etapa.data_programada.strftime("%m/%Y")

        cronograma_semanal = baker.make(
            CronogramaSemanal,
            cronograma_mensal=etapa.cronograma,
        )
        baker.make(
            ProgramacaoEntregaSemanal,
            cronograma_semanal=cronograma_semanal,
            mes_programado=mes,
            quantidade=5000.0,
        )

        assert etapa.quantidade_estimada_disponivel == 500.0 - 5000.0

    def test_soma_excede_o_original_retorna_negativo(
        self, cronograma_ponto_a_ponto_com_etapas
    ):
        """Cenário: programações somam mais que o original → saldo negativo."""
        etapa = EtapasDoCronograma.objects.filter(
            cronograma=cronograma_ponto_a_ponto_com_etapas,
            data_programada="2026-04-01",
        ).first()
        mes = etapa.data_programada.strftime("%m/%Y")

        cronograma_semanal = baker.make(
            CronogramaSemanal,
            cronograma_mensal=etapa.cronograma,
        )
        baker.make(
            ProgramacaoEntregaSemanal,
            cronograma_semanal=cronograma_semanal,
            mes_programado=mes,
            quantidade=600.0,
        )

        assert etapa.quantidade_estimada_disponivel == 500.0 - 600.0
        assert etapa.quantidade_estimada_disponivel < 0

    def test_soma_exatamente_igual_retorna_zero(
        self, cronograma_ponto_a_ponto_com_etapas
    ):
        """Cenário: programações usam todo o quantitativo → restante = 0."""
        etapa = EtapasDoCronograma.objects.filter(
            cronograma=cronograma_ponto_a_ponto_com_etapas,
            data_programada="2026-03-01",
        ).first()
        mes = etapa.data_programada.strftime("%m/%Y")

        cronograma_semanal = baker.make(
            CronogramaSemanal,
            cronograma_mensal=etapa.cronograma,
        )
        baker.make(
            ProgramacaoEntregaSemanal,
            cronograma_semanal=cronograma_semanal,
            mes_programado=mes,
            quantidade=500.0,
        )

        assert etapa.quantidade_estimada_disponivel == 0

    def test_multiplas_programacoes_mesmo_mes(
        self, cronograma_ponto_a_ponto_com_etapas
    ):
        """Cenário: múltiplas programações no mesmo mês → soma acumulada."""
        etapa = EtapasDoCronograma.objects.filter(
            cronograma=cronograma_ponto_a_ponto_com_etapas,
            data_programada="2026-03-01",
        ).first()
        mes = etapa.data_programada.strftime("%m/%Y")

        cronograma_semanal = baker.make(
            CronogramaSemanal,
            cronograma_mensal=etapa.cronograma,
        )
        baker.make(
            ProgramacaoEntregaSemanal,
            cronograma_semanal=cronograma_semanal,
            mes_programado=mes,
            quantidade=100.0,
        )
        baker.make(
            ProgramacaoEntregaSemanal,
            cronograma_semanal=cronograma_semanal,
            mes_programado=mes,
            quantidade=200.0,
        )

        assert etapa.quantidade_estimada_disponivel == 500.0 - 300.0

    def test_sem_data_programada_retorna_none(
        self, cronograma_ponto_a_ponto_com_etapas
    ):
        """Cenário: etapa sem data → None."""
        etapa = baker.make(
            EtapasDoCronograma,
            cronograma=cronograma_ponto_a_ponto_com_etapas,
            data_programada=None,
            quantidade=1000.0,
        )
        assert etapa.quantidade_estimada_disponivel is None

    def test_apenas_programacoes_do_mesmo_cronograma(
        self,
        cronograma_ponto_a_ponto_com_etapas,
        cronograma_ponto_a_ponto_assinado_2,
    ):
        """Cenário: programações de OUTRO cronograma não afetam o cálculo."""
        etapa = EtapasDoCronograma.objects.filter(
            cronograma=cronograma_ponto_a_ponto_com_etapas,
            data_programada="2026-03-01",
        ).first()
        mes = etapa.data_programada.strftime("%m/%Y")

        # Cria programação num cronograma DIFERENTE
        outro_semanal = baker.make(
            CronogramaSemanal,
            cronograma_mensal=cronograma_ponto_a_ponto_assinado_2,
        )
        baker.make(
            ProgramacaoEntregaSemanal,
            cronograma_semanal=outro_semanal,
            mes_programado=mes,
            quantidade=99999.0,
        )

        # O saldo do etapa original não deve ser afetado
        assert etapa.quantidade_estimada_disponivel == 500.0

    def test_apenas_programacoes_do_mesmo_mes(
        self, cronograma_ponto_a_ponto_com_etapas
    ):
        """Cenário: programações de mês diferente não afetam."""
        etapa = EtapasDoCronograma.objects.filter(
            cronograma=cronograma_ponto_a_ponto_com_etapas,
            data_programada="2026-03-01",
        ).first()

        outro_semanal = baker.make(
            CronogramaSemanal,
            cronograma_mensal=etapa.cronograma,
        )
        baker.make(
            ProgramacaoEntregaSemanal,
            cronograma_semanal=outro_semanal,
            mes_programado="05/2026",  # mês diferente
            quantidade=99999.0,
        )

        # O saldo do mês 03/2026 não deve ser afetado
        assert etapa.quantidade_estimada_disponivel == 500.0

    def test_multiplas_etapas_mesmo_mes_retorna_saldo_agregado(
        self,
        cronograma_ponto_a_ponto_com_etapas,
    ):
        """Cenário: duas etapas no mesmo mês (100.000 + 75.000 = 175.000),
        programação semanal de 25.000 → ambas as etapas retornam 150.000."""
        cronograma = cronograma_ponto_a_ponto_com_etapas

        # Cria duas etapas no mesmo mês (03/2026)
        etapa_100k = baker.make(
            EtapasDoCronograma,
            cronograma=cronograma,
            data_programada=datetime.date(2026, 3, 15),
            quantidade=100000.0,
        )
        etapa_75k = baker.make(
            EtapasDoCronograma,
            cronograma=cronograma,
            data_programada=datetime.date(2026, 3, 20),
            quantidade=75000.0,
        )

        # Cria um cronograma semanal com programação de 25.000 para 03/2026
        cronograma_semanal = baker.make(
            CronogramaSemanal,
            cronograma_mensal=cronograma,
        )
        baker.make(
            ProgramacaoEntregaSemanal,
            cronograma_semanal=cronograma_semanal,
            mes_programado="03/2026",
            quantidade=25000.0,
        )

        # Ambas as etapas devem retornar o mesmo saldo agregado
        # (inclui a etapa de 500 do fixture para o mesmo mês)
        assert etapa_100k.quantidade_estimada_disponivel == 150500.0
        assert etapa_75k.quantidade_estimada_disponivel == 150500.0
