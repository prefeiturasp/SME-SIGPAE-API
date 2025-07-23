import datetime
import random

import pytest
from freezegun import freeze_time
from model_bakery import baker
from rest_framework.exceptions import ValidationError

from ..api.serializers.serializers_create import (
    SolicitacaoKitLancheAvulsaCreationSerializer,
    SolicitacaoKitLancheUnificadaCreationSerializer,
)
from ..models import (
    SolicitacaoKitLanche,
    SolicitacaoKitLancheAvulsa,
    SolicitacaoKitLancheUnificada,
)

pytestmark = pytest.mark.django_db


@freeze_time("2019-10-16")
def test_kit_lanche_avulso_serializer_validators():
    serializer_obj = SolicitacaoKitLancheAvulsaCreationSerializer()
    lote = baker.make("Lote")
    escola = baker.make("Escola", lote=lote)
    attrs = dict(
        quantidade_alunos=777,
        escola=escola,
        confirmar=True,
        solicitacao_kit_lanche=dict(data=datetime.date(2019, 10, 18)),
    )
    response = serializer_obj.validate(attrs=attrs)
    assert response == attrs


@freeze_time("2019-10-16")
def test_kit_lanche_avulso_serializer_validators_error(
    kits_avulsos_param_erro_serializer,
):
    (
        qtd_alunos_escola,
        qtd_alunos_pedido,
        dia,
        erro_esperado,
    ) = kits_avulsos_param_erro_serializer
    serializer_obj = SolicitacaoKitLancheAvulsaCreationSerializer()
    lote = baker.make("Lote")
    escola = baker.make("Escola", lote=lote)

    attrs = dict(
        quantidade_alunos=qtd_alunos_pedido,
        escola=escola,
        solicitacao_kit_lanche=dict(data=dia),
    )
    with pytest.raises(ValidationError, match=erro_esperado):
        serializer_obj.validate(attrs=attrs)


@freeze_time("2019-7-16")
def test_kit_lanche_avulso_serializer_creators(kits_avulsos_param_serializer):
    qtd_alunos_escola, quantidade_alunos_pedido, data = kits_avulsos_param_serializer

    class FakeObject(object):
        user = baker.make("perfil.Usuario")

    serializer_obj = SolicitacaoKitLancheAvulsaCreationSerializer(
        context={"request": FakeObject}
    )
    lote = baker.make("Lote")
    escola = baker.make("Escola", lote=lote)
    aluno = baker.make("escola.Aluno")
    validated_data_create = dict(
        quantidade_alunos=quantidade_alunos_pedido,
        escola=escola,
        solicitacao_kit_lanche=dict(data=data),
        alunos_com_dieta_especial_participantes=[aluno],
    )

    serializer_obj.validate(attrs=validated_data_create)

    response_created = serializer_obj.create(validated_data=validated_data_create)
    assert isinstance(response_created, SolicitacaoKitLancheAvulsa)
    assert response_created.criado_por == FakeObject.user
    assert response_created.escola == escola
    assert response_created.solicitacao_kit_lanche.data == data
    assert response_created.quantidade_alunos == quantidade_alunos_pedido
    assert response_created.status == SolicitacaoKitLancheAvulsa.workflow_class.RASCUNHO

    data2 = data + datetime.timedelta(days=1)
    validated_data_update = dict(
        quantidade_alunos=quantidade_alunos_pedido,
        escola=escola,
        solicitacao_kit_lanche=dict(data=data2),
        alunos_com_dieta_especial_participantes=[aluno],
    )

    serializer_obj.validate(attrs=validated_data_update)

    response_updated = serializer_obj.update(
        instance=response_created, validated_data=validated_data_update
    )
    assert isinstance(response_updated, SolicitacaoKitLancheAvulsa)
    assert response_created.solicitacao_kit_lanche.data == data2


@freeze_time("2019-10-16")
def test_kit_lanche_unificado_serializer_validators_lista_igual(
    kits_unificados_param_serializer, periodo_escolar
):
    serializer_obj = SolicitacaoKitLancheUnificadaCreationSerializer()
    kits = baker.make("KitLanche", _quantity=3)
    qtd_alunos_escola, quantidade_alunos_pedido, data = kits_unificados_param_serializer
    escola = baker.make("Escola", nome="teste")
    baker.make(
        "escola.AlunosMatriculadosPeriodoEscola",
        escola=escola,
        quantidade_alunos=800,
        periodo_escolar=periodo_escolar,
    )
    escola_quantidades = []
    for _ in range(3):
        eq = baker.make("EscolaQuantidade", quantidade_alunos=quantidade_alunos_pedido)
        escola_quantidades.append(
            dict(quantidade_alunos=eq.quantidade_alunos, kits=[], escola=escola)
        )

    lista_kit_lanche_igual = True
    attrs = dict(
        lista_kit_lanche_igual=lista_kit_lanche_igual,
        escolas_quantidades=escola_quantidades,
        solicitacao_kit_lanche=dict(
            data=data, kits=kits, tempo_passeio=SolicitacaoKitLanche.CINCO_A_SETE
        ),
    )
    response = serializer_obj.validate(data=attrs)
    assert response == attrs


@freeze_time("2019-10-16")
def test_kit_lanche_unificado_serializer_validators_lista_nao_igual(
    kits_unificados_param_serializer,
):
    serializer_obj = SolicitacaoKitLancheUnificadaCreationSerializer()
    qtd_alunos_escola, quantidade_alunos_pedido, data = kits_unificados_param_serializer

    escola = baker.make("Escola")
    escola_quantidades = []
    for _ in range(3):
        kits = baker.make("KitLanche", _quantity=random.randint(1, 3))
        eq = baker.make("EscolaQuantidade", quantidade_alunos=quantidade_alunos_pedido)
        escola_quantidades.append(
            dict(quantidade_alunos=eq.quantidade_alunos, kits=kits, escola=escola)
        )

    lista_kit_lanche_igual = False
    attrs = dict(
        lista_kit_lanche_igual=lista_kit_lanche_igual,
        escolas_quantidades=escola_quantidades,
        solicitacao_kit_lanche=dict(data=data, kits=[], tempo_passeio=None),
    )
    response = serializer_obj.validate(data=attrs)
    assert response == attrs


@freeze_time("2019-10-16")
def test_kit_lanche_unificado_serializer_creators_lista_igual(
    kits_unificados_param_serializer,
):
    class FakeObject(object):
        user = baker.make("perfil.Usuario")

    serializer_obj = SolicitacaoKitLancheUnificadaCreationSerializer(
        context={"request": FakeObject}
    )

    kits = baker.make("KitLanche", _quantity=3)
    qtd_alunos_escola, quantidade_alunos_pedido, data = kits_unificados_param_serializer
    escola = baker.make("Escola", nome="teste")
    diretoria_regional = baker.make("DiretoriaRegional", nome="teste")

    escola_quantidades = []
    for _ in range(3):
        eq = baker.make("EscolaQuantidade", quantidade_alunos=quantidade_alunos_pedido)
        escola_quantidades.append(
            dict(quantidade_alunos=eq.quantidade_alunos, kits=[], escola=escola)
        )

    lista_kit_lanche_igual = True
    validated_data_create = dict(
        lista_kit_lanche_igual=lista_kit_lanche_igual,
        escolas_quantidades=escola_quantidades,
        diretoria_regional=diretoria_regional,
        solicitacao_kit_lanche=dict(
            data=data, kits=kits, tempo_passeio=SolicitacaoKitLanche.CINCO_A_SETE
        ),
    )
    response_create = serializer_obj.create(validated_data=validated_data_create)
    assert isinstance(response_create, SolicitacaoKitLancheUnificada)
    assert response_create.escolas_quantidades.count() == 3
    assert response_create.criado_por == FakeObject.user
    assert response_create.diretoria_regional == diretoria_regional
    assert response_create.lista_kit_lanche_igual is True
    assert response_create.solicitacao_kit_lanche.data == data
    assert response_create.solicitacao_kit_lanche.kits.count() == 3
    assert (
        response_create.solicitacao_kit_lanche.tempo_passeio
        == SolicitacaoKitLanche.CINCO_A_SETE
    )

    validated_data_update = dict(
        lista_kit_lanche_igual=lista_kit_lanche_igual,
        escolas_quantidades=escola_quantidades[:2],
        diretoria_regional=diretoria_regional,
        solicitacao_kit_lanche=dict(
            data=data, kits=kits[:1], tempo_passeio=SolicitacaoKitLanche.QUATRO
        ),
    )
    response_update = serializer_obj.update(
        instance=response_create, validated_data=validated_data_update
    )

    assert isinstance(response_update, SolicitacaoKitLancheUnificada)
    assert response_update.escolas_quantidades.count() == 2
    assert response_update.lista_kit_lanche_igual is True
    assert response_update.solicitacao_kit_lanche.data == data
    assert response_update.solicitacao_kit_lanche.kits.count() == 1
    assert (
        response_update.solicitacao_kit_lanche.tempo_passeio
        == SolicitacaoKitLanche.QUATRO
    )
