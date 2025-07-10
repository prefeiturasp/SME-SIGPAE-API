import pytest
from django.conf import settings
from django.utils import timezone
from freezegun import freeze_time
from model_mommy import mommy

from sme_sigpae_api.pre_recebimento.api.serializers.serializer_create import (
    CronogramaCreateSerializer,
    UnidadeMedidaCreateSerializer,
    novo_numero_solicitacao,
)
from sme_sigpae_api.pre_recebimento.api.serializers.serializers import (
    DocRecebimentoDetalharSerializer,
    EtapasDoCronogramaCalendarioSerializer,
    EtapasDoCronogramaSerializer,
    PainelCronogramaSerializer,
    UnidadeMedidaSerialzer,
)
from sme_sigpae_api.pre_recebimento.models import UnidadeMedida
from sme_sigpae_api.pre_recebimento.models.cronograma import Cronograma

pytestmark = pytest.mark.django_db


def test_etapas_cronograma_serializer(etapa):
    serializer = EtapasDoCronogramaSerializer(etapa)
    assert serializer.data["data_programada"] is None

    etapa.data_programada = timezone.now().date()
    etapa.save()
    serializer = EtapasDoCronogramaSerializer(etapa)
    assert serializer.data["data_programada"] == etapa.data_programada.strftime(
        "%d/%m/%Y"
    )


def test_unidade_medida_serializer(unidade_medida_logistica):
    """Deve serializar corretamente a instância de Unidade de Medida."""
    serializer = UnidadeMedidaSerialzer(unidade_medida_logistica)

    drf_date_format = settings.REST_FRAMEWORK["DATETIME_FORMAT"]

    assert serializer.data["uuid"] == str(unidade_medida_logistica.uuid)
    assert serializer.data["nome"] == str(unidade_medida_logistica.nome)
    assert serializer.data["abreviacao"] == str(unidade_medida_logistica.abreviacao)
    assert serializer.data["criado_em"] == unidade_medida_logistica.criado_em.strftime(
        drf_date_format
    )


def test_unidade_medida_create_serializer_creation():
    """Deve criar corretamente uma instância de Unidade de Medida."""
    data = {"nome": "UNIDADE MEDIDA", "abreviacao": "um"}

    serializer = UnidadeMedidaCreateSerializer(data=data)
    qtd_unidades_medida_antes = UnidadeMedida.objects.count()

    assert serializer.is_valid() is True
    assert serializer.validated_data["nome"] == data["nome"]
    assert serializer.validated_data["abreviacao"] == data["abreviacao"]

    instance = serializer.save()

    assert UnidadeMedida.objects.count() == qtd_unidades_medida_antes + 1
    assert instance.uuid is not None
    assert instance.criado_em is not None


def test_unidade_medida_create_serializer_updating(unidade_medida_logistica):
    """Deve criar corretamente uma instância de Unidade de Medida."""
    data = {"nome": "UNIDADE MEDIDA ATUALIZADA", "abreviacao": "uma"}

    serializer = UnidadeMedidaCreateSerializer(
        data=data, instance=unidade_medida_logistica
    )

    assert serializer.is_valid() is True
    assert serializer.validated_data["nome"] == data["nome"]
    assert serializer.validated_data["abreviacao"] == data["abreviacao"]


def test_painel_cronograma_serializer(cronograma, cronogramas_multiplos_status_com_log):
    cronograma_completo = Cronograma.objects.filter(numero="002/2023A").first()
    serializer = PainelCronogramaSerializer(cronograma_completo)

    assert cronograma_completo.empresa is not None
    assert serializer.data["empresa"] == str(cronograma_completo.empresa.nome_fantasia)
    assert cronograma_completo.ficha_tecnica.produto is not None
    assert serializer.data["produto"] == str(
        cronograma_completo.ficha_tecnica.produto.nome
    )
    assert cronograma_completo.log_mais_recente is not None
    assert serializer.data["log_mais_recente"].split(" ")[
        0
    ] == cronograma_completo.criado_em.strftime("%d/%m/%Y")

    cronograma_incompleto = cronograma
    serializer = PainelCronogramaSerializer(cronograma_incompleto)

    assert cronograma_incompleto.empresa is None
    assert cronograma_incompleto.ficha_tecnica is None
    assert cronograma_incompleto.log_mais_recente is None
    assert serializer.data[
        "log_mais_recente"
    ] == cronograma_incompleto.criado_em.strftime("%d/%m/%Y")


@freeze_time((timezone.now() + timezone.timedelta(2)))
def test_painel_cronograma_serializer_log_recente(cronogramas_multiplos_status_com_log):
    cronograma_completo = Cronograma.objects.filter(numero="002/2023A").first()
    serializer = PainelCronogramaSerializer(cronograma_completo)

    expected_date = (timezone.now() - timezone.timedelta(2)).strftime("%d/%m/%Y")
    assert serializer.data["log_mais_recente"] == expected_date


def test_gera_proximo_numero_cronograma_sem_ultimo_cronograma():
    numero = CronogramaCreateSerializer().gera_proximo_numero_cronograma()
    assert numero == f"001/{timezone.now().year}A"


def test_gera_proximo_numero_cronograma_com_ultimo_cronograma(cronograma):
    numero = CronogramaCreateSerializer().gera_proximo_numero_cronograma()
    assert (
        numero
        == f"{str(int(cronograma.numero[:3]) + 1).zfill(3)}/{timezone.now().year}A"
    )


def test_novo_numero_solicitacao(solicitacao_cronograma_em_analise):
    solicitacao = solicitacao_cronograma_em_analise

    solicitacao.numero_solicitacao = ""
    solicitacao.save()

    novo_numero_solicitacao(solicitacao)
    assert solicitacao.numero_solicitacao == f"{str(solicitacao.pk).zfill(8)}-ALT"


def test_etapas_do_cronograma_calendario_serializer(
    etapa_com_quantidade_e_data,
    cronograma_assinado_perfil_dilog,
    unidade_medida_logistica,
):
    cronograma = cronograma_assinado_perfil_dilog
    etapa = etapa_com_quantidade_e_data
    cronograma.unidade_medida = unidade_medida_logistica
    etapa.cronograma = cronograma
    etapa.save()

    serializer = EtapasDoCronogramaCalendarioSerializer(etapa)

    assert serializer.data["uuid"] == str(etapa.uuid)
    assert serializer.data["nome_produto"] == cronograma.ficha_tecnica.produto.nome
    assert serializer.data["numero_cronograma"] == cronograma.numero
    assert serializer.data["nome_fornecedor"] == cronograma.empresa.nome_fantasia
    assert serializer.data["data_programada"] == etapa.data_programada.strftime(
        "%d/%m/%Y"
    )
    assert serializer.data["numero_empenho"] == etapa.numero_empenho
    assert serializer.data["etapa"] == f"Etapa {etapa.etapa}"
    assert serializer.data["parte"] == etapa.parte
    assert serializer.data["quantidade"] == etapa.quantidade
    assert serializer.data["status"] == cronograma.get_status_display()
    assert serializer.data["unidade_medida"] == cronograma.unidade_medida.abreviacao


def test_doc_recebimento_serializer_pregao_chamada_publica(cronograma_chamada_publica):
    doc_recebimento = mommy.make(
        "DocumentoDeRecebimento", cronograma=cronograma_chamada_publica
    )

    serializer = DocRecebimentoDetalharSerializer(doc_recebimento)

    print(cronograma_chamada_publica.contrato.numero_chamada_publica)
    print(serializer.data["pregao_chamada_publica"])

    assert (
        serializer.data["pregao_chamada_publica"]
        == cronograma_chamada_publica.contrato.numero_chamada_publica
    )
    assert serializer.data["pregao_chamada_publica"] == "CP-2022-01"


def test_doc_recebimento_serializer_pregao_eletronico(cronograma_recebido):
    doc_recebimento = mommy.make(
        "DocumentoDeRecebimento", cronograma=cronograma_recebido
    )

    serializer = DocRecebimentoDetalharSerializer(doc_recebimento)

    assert (
        serializer.data["pregao_chamada_publica"]
        == cronograma_recebido.contrato.numero_pregao
    )
    assert serializer.data["pregao_chamada_publica"] == "123456789"


def test_doc_recebimento_serializer_qualquer_modalidade(cronograma_qualquer):
    doc_recebimento = mommy.make(
        "DocumentoDeRecebimento", cronograma=cronograma_qualquer
    )

    serializer = DocRecebimentoDetalharSerializer(doc_recebimento)

    assert (
        serializer.data["pregao_chamada_publica"]
        == cronograma_qualquer.contrato.numero_chamada_publica
    )
    assert serializer.data["pregao_chamada_publica"] == "CP-2022-02"
