import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db.models import Sum
from model_bakery import baker
from rest_framework import serializers
from rest_framework.test import APIRequestFactory

from src.pre_recebimento.documento_recebimento.api.serializers.serializers import (
    calcular_saldo_laudo,
)
from src.pre_recebimento.documento_recebimento.models import DocumentoDeRecebimento
from src.recebimento.ajuste_saldo_laudo.api.serializers.serializer_create import (
    AjusteSaldoCreateSerializer,
)
from src.recebimento.ajuste_saldo_laudo.models import AjusteSaldo

pytestmark = pytest.mark.django_db


def test_ajuste_saldo_create_serializer():
    user = baker.make(get_user_model())
    documento = baker.make(DocumentoDeRecebimento, quantidade_laudo=Decimal("100.00"))

    factory = APIRequestFactory()
    request = factory.post("/fake")
    request.user = user

    data = {
        "documento_recebimento": str(documento.uuid),
        "quantidade_descontada": "10.00",
    }

    serializer = AjusteSaldoCreateSerializer(data=data, context={"request": request})
    assert serializer.is_valid(), serializer.errors
    ajuste = serializer.save()

    ajuste.refresh_from_db()
    assert ajuste.quantidade_descontada == Decimal("10.00")

    total_ajustes = AjusteSaldo.objects.filter(
        documento_recebimento=documento
    ).aggregate(total=Sum("quantidade_descontada"))["total"]
    if total_ajustes is None:
        total_ajustes = Decimal("0.00")
    expected_saldo = documento.quantidade_laudo - Decimal(str(total_ajustes))

    saldo_calculado = calcular_saldo_laudo(documento)
    assert saldo_calculado == expected_saldo


def test_ajuste_saldo_create_serializer_insufficient_saldo():
    user = baker.make(get_user_model())
    documento = baker.make(DocumentoDeRecebimento, quantidade_laudo=Decimal("5.00"))

    factory = APIRequestFactory()
    request = factory.post("/fake")
    request.user = user

    data = {
        "documento_recebimento": str(documento.uuid),
        "quantidade_descontada": "10.00",
    }

    serializer = AjusteSaldoCreateSerializer(data=data, context={"request": request})
    assert serializer.is_valid(), serializer.errors

    with pytest.raises(serializers.ValidationError):
        serializer.save()
