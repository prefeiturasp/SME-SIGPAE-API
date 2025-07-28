import datetime
import random

import pytest
from model_bakery import baker

from ..api.serializers.serializers_create_cei import (
    FaixaEtariaSolicitacaoKitLancheCEIAvulsaCreateSerializer,
    SolicitacaoKitLancheCEIAvulsaCreationSerializer,
)


@pytest.mark.django_db
def test_faixa_etaria_kit_lanche_cei_serializer():
    faixa_etaria = baker.make("escola.FaixaEtaria")
    solic = baker.make("kit_lanche.SolicitacaoKitLancheCEIAvulsa")
    data = {
        "solicitacao_kit_lanche_avulsa": solic.uuid,
        "faixa_etaria": faixa_etaria.uuid,
        "quantidade": 42,
    }
    serializer = FaixaEtariaSolicitacaoKitLancheCEIAvulsaCreateSerializer(data=data)

    assert serializer.is_valid()


@pytest.mark.django_db
def test_kit_lanche_cei_avulsa_serializer_create_create():
    class FakeObject(object):
        user = baker.make("perfil.Usuario")

    hoje = datetime.date.today()
    # TODO: Achar uma forma de esse teste travar a data atual do sistema,
    #       se rodar dia 25/12 pra frente, vai dar problema
    data = hoje + datetime.timedelta(days=7)
    # SOLUÇÃO PALIATIVA: se for um dia a partir de 25/12, ignora o teste
    if data.year != hoje.year:
        return

    alunos = baker.make("escola.Aluno", _quantity=4)
    alunos_com_dieta = [aluno.uuid for aluno in alunos]

    escola = baker.make("escola.Escola")
    local = "Tão-tão distante"

    kits_lanche = baker.make("kit_lanche.KitLanche", _quantity=2)
    kits_escolhidos = [kit.uuid for kit in kits_lanche]
    tempo_passeio = 1

    faixas_etarias = baker.make("escola.FaixaEtaria", _quantity=5)
    faixas_etarias = [
        {"quantidade": random.randint(1, 20), "faixa_etaria": i.uuid}
        for i in faixas_etarias
    ]

    data = {
        "alunos_com_dieta_especial_participantes": alunos_com_dieta,
        "escola": escola.uuid,
        "local": local,
        "solicitacao_kit_lanche": {
            "descricao": "Um texto aleatório",
            "data": data,
            "kits": kits_escolhidos,
            "tempo_passeio": tempo_passeio,
        },
        "faixas_etarias": faixas_etarias,
    }

    serializer_obj = SolicitacaoKitLancheCEIAvulsaCreationSerializer(
        context={"request": FakeObject}, data=data
    )
    assert serializer_obj.is_valid()


@pytest.mark.django_db  # noqa C901
def test_kit_lanche_cei_avulsa_serializer_create_update():
    hoje = datetime.date.today()
    # TODO: Achar uma forma de esse teste travar a data atual do sistema,
    #       se rodar dia 25/12 pra frente, vai dar problema
    data = hoje + datetime.timedelta(days=7)
    # SOLUÇÃO PALIATIVA: se for um dia a partir de 25/12, ignora o teste
    if data.year != hoje.year:
        return

    solic = baker.make("kit_lanche.SolicitacaoKitLancheCEIAvulsa")

    alunos = baker.make("escola.Aluno", _quantity=4)
    alunos_com_dieta = [aluno.uuid for aluno in alunos]

    escola = baker.make("escola.Escola")
    local = "Tão-tão distante"
    descricao = "Um texto aleatório"

    kits_lanche = baker.make("kit_lanche.KitLanche", _quantity=2)
    kits_escolhidos = [kit.uuid for kit in kits_lanche]
    tempo_passeio = 1

    faixas_etarias = baker.make("escola.FaixaEtaria", _quantity=5)
    faixas_etarias = [
        {"quantidade": random.randint(1, 20), "faixa_etaria": i.uuid}
        for i in faixas_etarias
    ]

    validated_data = {
        "alunos_com_dieta_especial_participantes": alunos_com_dieta,
        "escola": escola.uuid,
        "local": local,
        "solicitacao_kit_lanche": {
            "descricao": descricao,
            "data": data,
            "kits": kits_escolhidos,
            "tempo_passeio": tempo_passeio,
        },
        "faixas_etarias": faixas_etarias,
    }

    serializer_obj = SolicitacaoKitLancheCEIAvulsaCreationSerializer(
        solic, data=validated_data
    )
    assert serializer_obj.is_valid()
