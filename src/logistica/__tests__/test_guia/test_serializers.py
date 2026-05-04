import pytest

from src.logistica.api.serializers.serializer_create import (
    NotificacaoOcorrenciasUpdateSerializer,
    PrevisoesContratuaisDaNotificacaoCreateSerializer,
    PrevisoesContratuaisDaNotificacaoUpdateSerializer,
)
from src.logistica.api.serializers.serializers import (
    PrevisaoContratualSimplesSerializer,
)
from src.logistica.models.guia import ConferenciaIndividualPorAlimento

pytestmark = pytest.mark.django_db


def test_previsao_contratual_simples_serializer(previsao_contratual):
    serializer = PrevisaoContratualSimplesSerializer(previsao_contratual)

    assert serializer.data["motivo_ocorrencia"] == previsao_contratual.motivo_ocorrencia
    assert (
        serializer.data["previsao_contratual"]
        == previsao_contratual.previsao_contratual
    )
    assert (
        serializer.data["justificativa_alteracao"]
        == previsao_contratual.justificativa_alteracao
    )
    assert serializer.data["aprovado"] == previsao_contratual.aprovado


def test_previsao_contratual_create_serializer():
    data = {
        "previsao_contratual": "Teste",
        "motivo_ocorrencia": ConferenciaIndividualPorAlimento.OCORRENCIA_ATRASO_ENTREGA,
    }

    serializer = PrevisoesContratuaisDaNotificacaoCreateSerializer(data=data)
    assert serializer.is_valid()

    serializer.save()
    assert serializer.instance.previsao_contratual == data["previsao_contratual"]
    assert serializer.instance.motivo_ocorrencia == data["motivo_ocorrencia"]

    data = {
        "previsao_contratual": "Teste",
        "motivo_ocorrencia": ConferenciaIndividualPorAlimento.OCORRENCIA_ATRASO_ENTREGA,
        "justificativa_alteracao": "Justificativa teste",
        "aprovado": True,
    }

    serializer = PrevisoesContratuaisDaNotificacaoCreateSerializer(data=data)
    assert serializer.is_valid()

    serializer.save()
    assert serializer.instance.previsao_contratual == data["previsao_contratual"]
    assert serializer.instance.motivo_ocorrencia == data["motivo_ocorrencia"]
    assert (
        serializer.instance.justificativa_alteracao == data["justificativa_alteracao"]
    )
    assert serializer.instance.aprovado == data["aprovado"]

    data = [
        {
            "previsao_contratual": "Previsão teste 1",
            "motivo_ocorrencia": ConferenciaIndividualPorAlimento.OCORRENCIA_ATRASO_ENTREGA,
            "justificativa_alteracao": "Justificativa previsao teste 1",
            "aprovado": False,
        },
        {
            "previsao_contratual": "Previsão teste 2",
            "motivo_ocorrencia": ConferenciaIndividualPorAlimento.OCORRENCIA_EMBALAGEM_DANIFICADA,
            "justificativa_alteracao": "",
            "aprovado": True,
        },
    ]

    serializer = PrevisoesContratuaisDaNotificacaoCreateSerializer(data=data, many=True)
    assert serializer.is_valid()

    serializer.save()
    assert serializer.instance[0].previsao_contratual == data[0]["previsao_contratual"]
    assert serializer.instance[0].motivo_ocorrencia == data[0]["motivo_ocorrencia"]
    assert (
        serializer.instance[0].justificativa_alteracao
        == data[0]["justificativa_alteracao"]
    )
    assert serializer.instance[0].aprovado == data[0]["aprovado"]

    assert serializer.instance[1].previsao_contratual == data[1]["previsao_contratual"]
    assert serializer.instance[1].motivo_ocorrencia == data[1]["motivo_ocorrencia"]
    assert (
        serializer.instance[1].justificativa_alteracao
        == data[1]["justificativa_alteracao"]
    )
    assert serializer.instance[1].aprovado == data[1]["aprovado"]


def test_previsoes_contratuais_update_serializer(notificacao_ocorrencia):
    data = [
        {
            "motivo_ocorrencia": ConferenciaIndividualPorAlimento.OCORRENCIA_ATRASO_ENTREGA,
            "justificativa_alteracao": "Justificativa previsao teste 1",
            "aprovado": False,
        },
        {
            "motivo_ocorrencia": ConferenciaIndividualPorAlimento.OCORRENCIA_EMBALAGEM_DANIFICADA,
            "justificativa_alteracao": "Justificativa previsao teste 2",
            "aprovado": True,
        },
    ]

    previsoes = notificacao_ocorrencia.previsoes_contratuais.all()
    serializer = PrevisoesContratuaisDaNotificacaoUpdateSerializer(
        previsoes, data=data, many=True
    )

    assert serializer.is_valid()

    serializer.save()

    previsoes = notificacao_ocorrencia.previsoes_contratuais.all()

    assert (
        previsoes.first().justificativa_alteracao == data[0]["justificativa_alteracao"]
    )
    assert previsoes.first().aprovado == data[0]["aprovado"]

    assert (
        previsoes.last().justificativa_alteracao == data[1]["justificativa_alteracao"]
    )
    assert previsoes.last().aprovado == data[1]["aprovado"]


def test_notificacao_ocorrencia_update_serializer(notificacao_ocorrencia):
    data = {
        "processo_sei": notificacao_ocorrencia.processo_sei,
        "previsoes": [
            {
                "previsao_contratual": "Previsão teste 1",
                "motivo_ocorrencia": ConferenciaIndividualPorAlimento.OCORRENCIA_ATRASO_ENTREGA,
                "justificativa_alteracao": "Justificativa previsao teste 1",
                "aprovado": False,
            },
            {
                "previsao_contratual": "Previsão teste 2",
                "motivo_ocorrencia": ConferenciaIndividualPorAlimento.OCORRENCIA_EMBALAGEM_DANIFICADA,
                "justificativa_alteracao": "",
                "aprovado": True,
            },
        ],
    }

    serializer = NotificacaoOcorrenciasUpdateSerializer(
        notificacao_ocorrencia, data=data
    )
    assert serializer.is_valid()

    serializer.save()
    previsoes = serializer.instance.previsoes_contratuais.all()

    assert previsoes.count() == 2

    assert (
        previsoes.first().previsao_contratual
        == data["previsoes"][0]["previsao_contratual"]
    )
    assert (
        previsoes.first().motivo_ocorrencia == data["previsoes"][0]["motivo_ocorrencia"]
    )
    assert (
        previsoes.first().justificativa_alteracao
        == data["previsoes"][0]["justificativa_alteracao"]
    )
    assert previsoes.first().aprovado == data["previsoes"][0]["aprovado"]

    assert (
        previsoes.last().previsao_contratual
        == data["previsoes"][1]["previsao_contratual"]
    )
    assert (
        previsoes.last().motivo_ocorrencia == data["previsoes"][1]["motivo_ocorrencia"]
    )
    assert (
        previsoes.last().justificativa_alteracao
        == data["previsoes"][1]["justificativa_alteracao"]
    )
    assert previsoes.last().aprovado == data["previsoes"][1]["aprovado"]
