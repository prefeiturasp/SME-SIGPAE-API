import datetime
import json
import random
from io import BytesIO
from itertools import product
from unittest.mock import MagicMock
from django.urls import reverse

import pandas as pd
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from model_bakery import baker
from src.dados_comuns.constants import (
    DJANGO_ADMIN_PASSWORD,
)
from src.cardapio.base.models import TipoAlimentacao
from src.dados_comuns.constants import TIPOS_ALIMENTACAO, TIPOS_UNIDADE_ESCOLAR
from src.escola.models import DiretoriaRegional, Escola, Lote, TipoUnidadeEscolar
from src.escola_aberta.models import (
    EscolaAberta,
    EscolaAbertaUnidadeParticipante,
)

@pytest.fixture
def setup_escola_aberta_data():
    EscolaAberta.objects.all().delete()
    EscolaAbertaUnidadeParticipante.objects.all().delete()
    TipoAlimentacao.objects.all().delete()
    Escola.objects.all().delete()
    Lote.objects.all().delete()
    DiretoriaRegional.objects.all().delete()
    TipoUnidadeEscolar.objects.all().delete()

    tipo_unidade = TipoUnidadeEscolar.objects.create(
        iniciais=TIPOS_UNIDADE_ESCOLAR.EMEF.value
    )
    diretoria_regional = DiretoriaRegional.objects.create(
        nome="DRE Teste",
        iniciais="DT",
    )
    lote = Lote.objects.create(
        nome="Lote 01",
        diretoria_regional=diretoria_regional,
    )

    escola_1 = Escola.objects.create(
        nome="EMEF Teste 1",
        codigo_eol="123456",
        diretoria_regional=diretoria_regional,
        tipo_unidade=tipo_unidade,
    )
    escola_2 = Escola.objects.create(
        nome="EMEF Teste 2",
        codigo_eol="654321",
        diretoria_regional=diretoria_regional,
        tipo_unidade=tipo_unidade,
    )

    tipo_alim_1 = TipoAlimentacao.objects.create(nome=TIPOS_ALIMENTACAO.LANCHE.value)
    tipo_alim_2 = TipoAlimentacao.objects.create(nome=TIPOS_ALIMENTACAO.ALMOCO.value)

    list_url = reverse("escola-aberta-list")

    return {
        "tipo_unidade": tipo_unidade,
        "diretoria_regional": diretoria_regional,
        "lote": lote,
        "escola_1": escola_1,
        "escola_2": escola_2,
        "tipo_alim": tipo_alim_1,
        "tipo_alim_1": tipo_alim_1,
        "tipo_alim_2": tipo_alim_2,
        "list_url": list_url,
    }


@pytest.fixture
def client_autenticado_coordenador_codae(client, django_user_model):
    email, password, rf, cpf = (
        "cogestor_1@sme.prefeitura.sp.gov.br",
        DJANGO_ADMIN_PASSWORD,
        "0000001",
        "44426575052",
    )
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf, cpf=cpf
    )
    client.login(username=email, password=password)

    codae = baker.make(
        "Codae", nome="CODAE", uuid="b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd"
    )

    perfil_coordenador = baker.make(
        "Perfil",
        nome="COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA",
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )
    baker.make("Lote", uuid="143c2550-8bf0-46b4-b001-27965cfcd107")
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_coordenador,
        data_inicial=hoje,
        ativo=True,
    )

    return client
