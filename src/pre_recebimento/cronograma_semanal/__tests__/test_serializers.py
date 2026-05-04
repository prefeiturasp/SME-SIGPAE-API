import pytest

from src.pre_recebimento.cronograma_entrega.api.serializers.serializers import (
    CronogramaMensalAssinadoSerializer,
)
from src.pre_recebimento.cronograma_semanal.api.serializers.serializer_create import (
    CronogramaSemanalAssinarEEnviarSerializer,
    CronogramaSemanalRascunhoSerializer,
    ProgramacaoEntregaSemanalCreateSerializer,
)
from src.pre_recebimento.cronograma_semanal.api.serializers.serializers import (
    CronogramaMensalSimplesSerializer,
    CronogramaSemanalDetailSerializer,
    CronogramaSemanalListagemSerializer,
    ProgramacaoEntregaSemanalDetailSerializer,
)

pytestmark = pytest.mark.django_db


class TestCronogramaMensalAssinadoSerializer:
    def test_serializer_campos(self, cronograma_ponto_a_ponto_assinado):
        serializer = CronogramaMensalAssinadoSerializer(
            cronograma_ponto_a_ponto_assinado
        )
        data = serializer.data

        assert "uuid" in data
        assert "numero" in data
        assert "produto_nome" in data
        assert "fornecedor_nome" in data
        assert "numero_contrato" in data

    def test_serializer_produto_nome(self, cronograma_ponto_a_ponto_assinado):
        serializer = CronogramaMensalAssinadoSerializer(
            cronograma_ponto_a_ponto_assinado
        )
        assert (
            serializer.data["produto_nome"]
            == cronograma_ponto_a_ponto_assinado.ficha_tecnica.produto.nome
        )

    def test_serializer_fornecedor_nome(self, cronograma_ponto_a_ponto_assinado):
        serializer = CronogramaMensalAssinadoSerializer(
            cronograma_ponto_a_ponto_assinado
        )
        assert (
            serializer.data["fornecedor_nome"]
            == cronograma_ponto_a_ponto_assinado.empresa.nome_fantasia
        )

    def test_serializer_numero_contrato(self, cronograma_ponto_a_ponto_assinado):
        serializer = CronogramaMensalAssinadoSerializer(
            cronograma_ponto_a_ponto_assinado
        )
        assert (
            serializer.data["numero_contrato"]
            == cronograma_ponto_a_ponto_assinado.contrato.numero
        )


class TestProgramacaoEntregaSemanalCreateSerializer:
    def test_serializer_valido(self):
        data = {
            "mes_programado": "03/2026",
            "data_inicio": "2026-03-01",
            "data_fim": "2026-03-31",
            "quantidade": 100.0,
        }
        serializer = ProgramacaoEntregaSemanalCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_serializer_mes_obrigatorio(self):
        data = {
            "data_inicio": "2026-03-01",
            "data_fim": "2026-03-31",
            "quantidade": 100.0,
        }
        serializer = ProgramacaoEntregaSemanalCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "mes_programado" in serializer.errors

    def test_serializer_data_inicio_obrigatorio(self):
        data = {
            "mes_programado": "03/2026",
            "data_fim": "2026-03-31",
            "quantidade": 100.0,
        }
        serializer = ProgramacaoEntregaSemanalCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "data_inicio" in serializer.errors

    def test_serializer_data_fim_obrigatorio(self):
        data = {
            "mes_programado": "03/2026",
            "data_inicio": "2026-03-01",
            "quantidade": 100.0,
        }
        serializer = ProgramacaoEntregaSemanalCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "data_fim" in serializer.errors

    def test_serializer_quantidade_obrigatorio(self):
        data = {
            "mes_programado": "03/2026",
            "data_inicio": "2026-03-01",
            "data_fim": "2026-03-31",
        }
        serializer = ProgramacaoEntregaSemanalCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "quantidade" in serializer.errors


class TestCronogramaSemanalRascunhoSerializer:
    def test_serializer_valido(self, cronograma_ponto_a_ponto_assinado):
        data = {
            "cronograma_mensal": str(cronograma_ponto_a_ponto_assinado.uuid),
        }
        serializer = CronogramaSemanalRascunhoSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_serializer_com_observacoes(self, cronograma_ponto_a_ponto_assinado):
        data = {
            "cronograma_mensal": str(cronograma_ponto_a_ponto_assinado.uuid),
            "observacoes": "Observação de teste",
        }
        serializer = CronogramaSemanalRascunhoSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_serializer_cronograma_mensal_obrigatorio(self):
        data = {
            "observacoes": "Observação de teste",
        }
        serializer = CronogramaSemanalRascunhoSerializer(data=data)
        assert not serializer.is_valid()
        assert "cronograma_mensal" in serializer.errors

    def test_serializer_cronograma_nao_ponto_a_ponto(
        self, cronograma_nao_ponto_a_ponto_assinado
    ):
        data = {
            "cronograma_mensal": str(cronograma_nao_ponto_a_ponto_assinado.uuid),
        }
        serializer = CronogramaSemanalRascunhoSerializer(data=data)
        assert not serializer.is_valid()
        assert "cronograma_mensal" in serializer.errors
        assert "Ponto a Ponto" in str(serializer.errors["cronograma_mensal"])

    def test_serializer_cronograma_nao_assinado_codae(
        self, cronograma_ponto_a_ponto_nao_assinado
    ):
        data = {
            "cronograma_mensal": str(cronograma_ponto_a_ponto_nao_assinado.uuid),
        }
        serializer = CronogramaSemanalRascunhoSerializer(data=data)
        assert not serializer.is_valid()
        assert "cronograma_mensal" in serializer.errors
        assert "ASSINADO_CODAE" in str(serializer.errors["cronograma_mensal"])

    def test_serializer_com_programacoes(self, cronograma_ponto_a_ponto_assinado):
        data = {
            "cronograma_mensal": str(cronograma_ponto_a_ponto_assinado.uuid),
            "programacoes": [
                {
                    "mes_programado": "03/2026",
                    "data_inicio": "2026-03-01",
                    "data_fim": "2026-03-15",
                    "quantidade": 50.0,
                }
            ],
        }
        serializer = CronogramaSemanalRascunhoSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_serializer_sem_programacoes(self, cronograma_ponto_a_ponto_assinado):
        data = {
            "cronograma_mensal": str(cronograma_ponto_a_ponto_assinado.uuid),
        }
        serializer = CronogramaSemanalRascunhoSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_serializer_cronograma_inexistente(self):
        data = {
            "cronograma_mensal": "00000000-0000-0000-0000-000000000000",
        }
        serializer = CronogramaSemanalRascunhoSerializer(data=data)
        assert not serializer.is_valid()
        assert "cronograma_mensal" in serializer.errors

    def test_serializer_create(self, cronograma_ponto_a_ponto_assinado):
        data = {
            "cronograma_mensal": str(cronograma_ponto_a_ponto_assinado.uuid),
            "observacoes": "Teste de criação",
            "programacoes": [
                {
                    "mes_programado": "03/2026",
                    "data_inicio": "2026-03-01",
                    "data_fim": "2026-03-15",
                    "quantidade": 50.0,
                }
            ],
        }
        serializer = CronogramaSemanalRascunhoSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        cronograma_semanal = serializer.save()
        assert cronograma_semanal.uuid is not None
        assert cronograma_semanal.programacoes.count() == 1

    def test_serializer_update(
        self, cronograma_semanal_rascunho, cronograma_ponto_a_ponto_assinado
    ):
        data = {
            "cronograma_mensal": str(cronograma_ponto_a_ponto_assinado.uuid),
            "observacoes": "Observação atualizada",
        }
        serializer = CronogramaSemanalRascunhoSerializer(
            cronograma_semanal_rascunho, data=data, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        cronograma_semanal = serializer.save()
        assert cronograma_semanal.observacoes == "Observação atualizada"

    def test_serializer_update_substitui_programacoes(
        self, cronograma_semanal_rascunho, cronograma_ponto_a_ponto_assinado
    ):
        import datetime

        from django.utils import timezone

        from src.pre_recebimento.cronograma_semanal.models import (
            ProgramacaoEntregaSemanal,
        )

        ProgramacaoEntregaSemanal.objects.create(
            cronograma_semanal=cronograma_semanal_rascunho,
            mes_programado="01/2026",
            data_inicio=timezone.now().date(),
            data_fim=timezone.now().date() + datetime.timedelta(days=5),
            quantidade=10.0,
        )

        data = {
            "cronograma_mensal": str(cronograma_ponto_a_ponto_assinado.uuid),
            "programacoes": [
                {
                    "mes_programado": "03/2026",
                    "data_inicio": "2026-03-01",
                    "data_fim": "2026-03-15",
                    "quantidade": 50.0,
                },
                {
                    "mes_programado": "04/2026",
                    "data_inicio": "2026-04-01",
                    "data_fim": "2026-04-15",
                    "quantidade": 30.0,
                },
            ],
        }
        serializer = CronogramaSemanalRascunhoSerializer(
            cronograma_semanal_rascunho, data=data, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        cronograma_semanal = serializer.save()
        assert cronograma_semanal.programacoes.count() == 2

    def test_serializer_update_remove_programacoes(
        self, cronograma_semanal_rascunho, cronograma_ponto_a_ponto_assinado
    ):
        import datetime

        from django.utils import timezone

        from src.pre_recebimento.cronograma_semanal.models import (
            ProgramacaoEntregaSemanal,
        )

        ProgramacaoEntregaSemanal.objects.create(
            cronograma_semanal=cronograma_semanal_rascunho,
            mes_programado="01/2026",
            data_inicio=timezone.now().date(),
            data_fim=timezone.now().date() + datetime.timedelta(days=5),
            quantidade=10.0,
        )

        data = {
            "cronograma_mensal": str(cronograma_ponto_a_ponto_assinado.uuid),
            "programacoes": [],
        }
        serializer = CronogramaSemanalRascunhoSerializer(
            cronograma_semanal_rascunho, data=data, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        cronograma_semanal = serializer.save()
        assert cronograma_semanal.programacoes.count() == 0


class TestCronogramaMensalAssinadoSerializerCamposNulos:
    def test_serializer_campos_nulos(self):
        from model_bakery import baker

        from src.pre_recebimento.cronograma_entrega.api.serializers.serializers import (
            CronogramaMensalAssinadoSerializer,
        )
        from src.pre_recebimento.cronograma_entrega.models import Cronograma

        cronograma_vazio = baker.make(
            Cronograma,
            ficha_tecnica=None,
            empresa=None,
            contrato=None,
        )

        serializer = CronogramaMensalAssinadoSerializer(cronograma_vazio)
        data = serializer.data

        assert data["produto_nome"] is None
        assert data["fornecedor_nome"] is None
        assert data["numero_contrato"] is None


class TestCronogramaSemanalAssinarEEnviarSerializer:
    def test_serializer_valido_com_programacoes(
        self,
        cronograma_ponto_a_ponto_assinado,
        client_autenticado_vinculo_dilog_cronograma,
    ):
        client, user = client_autenticado_vinculo_dilog_cronograma
        data = {
            "cronograma_mensal": str(cronograma_ponto_a_ponto_assinado.uuid),
            "programacoes": [
                {
                    "mes_programado": "03/2026",
                    "data_inicio": "2026-03-01",
                    "data_fim": "2026-03-15",
                    "quantidade": 50.0,
                }
            ],
        }
        serializer = CronogramaSemanalAssinarEEnviarSerializer(
            data=data, context={"request": type("Request", (), {"user": user})()}
        )
        assert serializer.is_valid(), serializer.errors

    def test_serializer_sem_programacoes_obrigatorias(
        self,
        cronograma_ponto_a_ponto_assinado,
        client_autenticado_vinculo_dilog_cronograma,
    ):
        client, user = client_autenticado_vinculo_dilog_cronograma
        data = {
            "cronograma_mensal": str(cronograma_ponto_a_ponto_assinado.uuid),
        }
        serializer = CronogramaSemanalAssinarEEnviarSerializer(
            data=data, context={"request": type("Request", (), {"user": user})()}
        )
        assert not serializer.is_valid()
        assert "programacoes" in serializer.errors

    def test_serializer_programacoes_vazias(
        self,
        cronograma_ponto_a_ponto_assinado,
        client_autenticado_vinculo_dilog_cronograma,
    ):
        client, user = client_autenticado_vinculo_dilog_cronograma
        data = {
            "cronograma_mensal": str(cronograma_ponto_a_ponto_assinado.uuid),
            "programacoes": [],
        }
        serializer = CronogramaSemanalAssinarEEnviarSerializer(
            data=data, context={"request": type("Request", (), {"user": user})()}
        )
        assert not serializer.is_valid()
        assert "programacoes" in serializer.errors

    def test_serializer_create_transiciona_status(
        self,
        cronograma_ponto_a_ponto_assinado,
        client_autenticado_vinculo_dilog_cronograma,
    ):
        from src.dados_comuns.fluxo_status import CronogramaSemanalWorkflow

        client, user = client_autenticado_vinculo_dilog_cronograma
        data = {
            "cronograma_mensal": str(cronograma_ponto_a_ponto_assinado.uuid),
            "programacoes": [
                {
                    "mes_programado": "03/2026",
                    "data_inicio": "2026-03-01",
                    "data_fim": "2026-03-15",
                    "quantidade": 50.0,
                }
            ],
        }
        serializer = CronogramaSemanalAssinarEEnviarSerializer(
            data=data, context={"request": type("Request", (), {"user": user})()}
        )
        assert serializer.is_valid(), serializer.errors
        cronograma_semanal = serializer.save()
        assert (
            cronograma_semanal.status == CronogramaSemanalWorkflow.ENVIADO_AO_FORNECEDOR
        )

    def test_serializer_update_transiciona_status(
        self,
        cronograma_semanal_rascunho,
        cronograma_ponto_a_ponto_assinado,
        client_autenticado_vinculo_dilog_cronograma,
    ):
        from src.dados_comuns.fluxo_status import CronogramaSemanalWorkflow

        client, user = client_autenticado_vinculo_dilog_cronograma
        data = {
            "cronograma_mensal": str(cronograma_ponto_a_ponto_assinado.uuid),
            "programacoes": [
                {
                    "mes_programado": "03/2026",
                    "data_inicio": "2026-03-01",
                    "data_fim": "2026-03-15",
                    "quantidade": 50.0,
                }
            ],
        }
        serializer = CronogramaSemanalAssinarEEnviarSerializer(
            cronograma_semanal_rascunho,
            data=data,
            partial=True,
            context={"request": type("Request", (), {"user": user})()},
        )
        assert serializer.is_valid(), serializer.errors
        cronograma_semanal = serializer.save()
        assert (
            cronograma_semanal.status == CronogramaSemanalWorkflow.ENVIADO_AO_FORNECEDOR
        )


class TestCronogramaSemanalListagemSerializer:
    def test_serializer_campos(self, cronograma_semanal_rascunho):
        serializer = CronogramaSemanalListagemSerializer(cronograma_semanal_rascunho)
        data = serializer.data

        assert "uuid" in data
        assert "numero" in data
        assert "produto" in data
        assert "quantidade_total" in data
        assert "empresa" in data
        assert "status" in data
        assert "alterado_em" in data

        assert data["numero"] == cronograma_semanal_rascunho.cronograma_mensal.numero
        assert (
            data["produto"]
            == cronograma_semanal_rascunho.cronograma_mensal.ficha_tecnica.produto.nome
        )
        assert data["status"] == cronograma_semanal_rascunho.get_status_display()
        assert (
            data["empresa"]
            == cronograma_semanal_rascunho.cronograma_mensal.empresa.nome
        )

        assert (
            str(cronograma_semanal_rascunho.cronograma_mensal.qtd_total_programada)
            in data["quantidade_total"]
        )
        assert (
            str(cronograma_semanal_rascunho.cronograma_mensal.unidade_medida)
            in data["quantidade_total"]
        )


class TestProgramacaoEntregaSemanalDetailSerializer:
    def test_serializer_campos(self, programacao_entrega_semanal):
        serializer = ProgramacaoEntregaSemanalDetailSerializer(
            programacao_entrega_semanal
        )
        data = serializer.data
        assert "mes_programado" in data
        assert "data_inicio" in data
        assert "data_fim" in data
        assert "quantidade" in data

    def test_serializer_valores(self, programacao_entrega_semanal):
        serializer = ProgramacaoEntregaSemanalDetailSerializer(
            programacao_entrega_semanal
        )
        data = serializer.data
        assert data["mes_programado"] == programacao_entrega_semanal.mes_programado
        assert float(data["quantidade"]) == programacao_entrega_semanal.quantidade


class TestCronogramaMensalSimplesSerializer:
    def test_serializer_campos(self, cronograma_ponto_a_ponto_assinado):
        serializer = CronogramaMensalSimplesSerializer(
            cronograma_ponto_a_ponto_assinado
        )
        data = serializer.data
        assert "uuid" in data
        assert "numero" in data
        assert "empresa" in data
        assert "contrato" in data
        assert "numero_empenho" in data
        assert "qtd_total_empenho" in data
        assert "custo_unitario_produto" in data
        assert "unidade_medida" in data

    def test_serializer_empresa_dados(self, cronograma_ponto_a_ponto_assinado):
        serializer = CronogramaMensalSimplesSerializer(
            cronograma_ponto_a_ponto_assinado
        )
        data = serializer.data
        assert data["empresa"] is not None
        assert "nome_fantasia" in data["empresa"]
        assert "razao_social" in data["empresa"]

    def test_serializer_contrato_dados(self, cronograma_ponto_a_ponto_assinado):
        serializer = CronogramaMensalSimplesSerializer(
            cronograma_ponto_a_ponto_assinado
        )
        data = serializer.data
        assert data["contrato"] is not None
        assert "numero" in data["contrato"]
        assert "processo" in data["contrato"]

    def test_serializer_unidade_medida(self, cronograma_ponto_a_ponto_assinado):
        serializer = CronogramaMensalSimplesSerializer(
            cronograma_ponto_a_ponto_assinado
        )
        data = serializer.data
        if data["unidade_medida"]:
            assert "uuid" in data["unidade_medida"]
            assert "nome" in data["unidade_medida"]
            assert "abreviacao" in data["unidade_medida"]


class TestCronogramaSemanalDetailSerializer:
    def test_serializer_campos(self, cronograma_semanal_rascunho):
        serializer = CronogramaSemanalDetailSerializer(cronograma_semanal_rascunho)
        data = serializer.data
        assert "uuid" in data
        assert "numero" in data
        assert "status" in data
        assert "observacoes" in data
        assert "cronograma_mensal" in data
        assert "programacoes" in data
        assert "logs" in data

    def test_serializer_status_display(self, cronograma_semanal_rascunho):
        serializer = CronogramaSemanalDetailSerializer(cronograma_semanal_rascunho)
        data = serializer.data
        assert data["status"] == cronograma_semanal_rascunho.get_status_display()

    def test_serializer_numero(self, cronograma_semanal_rascunho):
        serializer = CronogramaSemanalDetailSerializer(cronograma_semanal_rascunho)
        data = serializer.data
        assert data["numero"] == cronograma_semanal_rascunho.numero

    def test_serializer_cronograma_mensal_dados(self, cronograma_semanal_rascunho):
        serializer = CronogramaSemanalDetailSerializer(cronograma_semanal_rascunho)
        data = serializer.data
        assert data["cronograma_mensal"] is not None
        assert "uuid" in data["cronograma_mensal"]
        assert "numero" in data["cronograma_mensal"]
        assert "empresa" in data["cronograma_mensal"]
        assert "contrato" in data["cronograma_mensal"]

    def test_serializer_programacoes(
        self, cronograma_semanal_rascunho, programacao_entrega_semanal
    ):
        serializer = CronogramaSemanalDetailSerializer(cronograma_semanal_rascunho)
        data = serializer.data
        assert isinstance(data["programacoes"], list)
        assert len(data["programacoes"]) >= 1
        prog = data["programacoes"][0]
        assert "mes_programado" in prog
        assert "data_inicio" in prog
        assert "data_fim" in prog
        assert "quantidade" in prog

    def test_serializer_logs(self, cronograma_semanal_rascunho):
        serializer = CronogramaSemanalDetailSerializer(cronograma_semanal_rascunho)
        data = serializer.data
        assert isinstance(data["logs"], list)

    def test_serializer_observacoes(self, cronograma_semanal_rascunho):
        serializer = CronogramaSemanalDetailSerializer(cronograma_semanal_rascunho)
        data = serializer.data
        assert data["observacoes"] == cronograma_semanal_rascunho.observacoes

    def test_serializer_sem_programacoes(self, cronograma_semanal_rascunho):
        from src.pre_recebimento.cronograma_semanal.models import (
            ProgramacaoEntregaSemanal,
        )

        ProgramacaoEntregaSemanal.objects.filter(
            cronograma_semanal=cronograma_semanal_rascunho
        ).delete()
        serializer = CronogramaSemanalDetailSerializer(cronograma_semanal_rascunho)
        data = serializer.data
        assert data["programacoes"] == []


class TestCronogramaSemanalRascunhosSerializer:
    def test_serializer_campos(self, cronograma_semanal_rascunho):
        from src.pre_recebimento.cronograma_semanal.api.serializers.serializers import (
            CronogramaSemanalRascunhosSerializer,
        )

        serializer = CronogramaSemanalRascunhosSerializer(cronograma_semanal_rascunho)
        data = serializer.data
        assert "uuid" in data
        assert "numero" in data
        assert "alterado_em" in data

    def test_serializer_valores(self, cronograma_semanal_rascunho):
        from src.pre_recebimento.cronograma_semanal.api.serializers.serializers import (
            CronogramaSemanalRascunhosSerializer,
        )

        serializer = CronogramaSemanalRascunhosSerializer(cronograma_semanal_rascunho)
        data = serializer.data
        assert data["uuid"] == str(cronograma_semanal_rascunho.uuid)
        assert data["numero"] == cronograma_semanal_rascunho.cronograma_mensal.numero
