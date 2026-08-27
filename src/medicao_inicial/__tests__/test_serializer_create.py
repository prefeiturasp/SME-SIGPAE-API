import pytest
from model_bakery import baker

from src.dados_comuns.constants import TIPOS_UNIDADE_ESCOLAR
from src.medicao_inicial.api.serializers_create import (
    DescontoFinanceiroUpdateSerializer,
)
from src.medicao_inicial.models import DescontoFinanceiro


@pytest.mark.django_db
def test_desconto_financeiro_serializer_grupo_cei_create(
    relatorio_financeiro_cei,
    escola_ceu_gestao,
    faixas_etarias_ativas,
    periodo_escolar_parcial,
    clausula_desconto,
):
    payload = {
        "relatorio_financeiro_id": str(relatorio_financeiro_cei.uuid),
        "unidades_educacionais": [str(escola_ceu_gestao.uuid)],
        "tipo_lancamento": "ALIMENTACOES",
        "faixa_etaria": str(faixas_etarias_ativas[0].uuid),
        "periodo_escolar": periodo_escolar_parcial.nome,
        "clausula_desconto": str(clausula_desconto.uuid),
        "quantidade": 10,
    }

    serializer = DescontoFinanceiroUpdateSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors

    instance = serializer.save()

    assert instance.tipo_lancamento == "ALIMENTACOES"
    assert instance.quantidade == 10
    assert instance.relatorio_financeiro == relatorio_financeiro_cei
    assert list(instance.unidades_educacionais.all()) == [escola_ceu_gestao]


@pytest.mark.django_db
def test_desconto_financeiro_serializer_grupo_cei_update(
    relatorio_financeiro_cei,
    escola_ceu_gestao,
    faixas_etarias_ativas,
    periodo_escolar_parcial,
    clausula_desconto,
):
    obj = baker.make(
        DescontoFinanceiro,
        relatorio_financeiro=relatorio_financeiro_cei,
        faixa_etaria=faixas_etarias_ativas[0],
        periodo_escolar=periodo_escolar_parcial,
        clausula_desconto=clausula_desconto,
        quantidade=5,
        tipo_lancamento="DIETAS_TIPO_A",
    )

    obj.unidades_educacionais.set([escola_ceu_gestao])

    payload = {
        "tipo_lancamento": "ALIMENTACOES",
        "quantidade": 20,
    }

    serializer = DescontoFinanceiroUpdateSerializer(
        instance=obj,
        data=payload,
        partial=True,
    )

    assert serializer.is_valid(), serializer.errors

    updated = serializer.save()

    assert updated.tipo_lancamento == "ALIMENTACOES"
    assert updated.quantidade == 20


@pytest.mark.django_db
def test_desconto_financeiro_grupo_cei_campos_obrigatorios(
    relatorio_financeiro_cei,
    escola_ceu_gestao,
    clausula_desconto,
):
    payload = {
        "relatorio_financeiro_id": str(relatorio_financeiro_cei.uuid),
        "unidades_educacionais": [str(escola_ceu_gestao.uuid)],
        "tipo_lancamento": "ALIMENTACOES",
        "clausula_desconto": str(clausula_desconto.uuid),
        "quantidade": 10,
    }

    serializer = DescontoFinanceiroUpdateSerializer(data=payload)

    assert not serializer.is_valid()
    assert "faixa_etaria" in serializer.errors
    assert "periodo_escolar" in serializer.errors
    assert serializer.errors["faixa_etaria"][0] == "Campo obrigatório para o grupo."
    assert serializer.errors["periodo_escolar"][0] == "Campo obrigatório para o grupo."


@pytest.mark.django_db
def test_desconto_financeiro_grupo_emei_nao_permite_faixa_etaria(
    relatorio_financeiro_emei,
    escola_ceu_gestao,
    faixas_etarias_ativas,
    clausula_desconto,
):
    payload = {
        "relatorio_financeiro_id": str(relatorio_financeiro_emei.uuid),
        "unidades_educacionais": [str(escola_ceu_gestao.uuid)],
        "tipo_lancamento": "ALIMENTACOES",
        "faixa_etaria": str(faixas_etarias_ativas[0].uuid),
        "clausula_desconto": str(clausula_desconto.uuid),
        "quantidade": 10,
    }

    serializer = DescontoFinanceiroUpdateSerializer(data=payload)

    assert not serializer.is_valid()
    assert "faixa_etaria" in serializer.errors
    assert (
        serializer.errors["faixa_etaria"][0]
        == "Não é permitido informar faixa etária para este grupo."
    )


@pytest.mark.django_db
def test_desconto_financeiro_grupo_cemei_campos_obrigatorios(
    relatorio_financeiro_cemei,
    escola_cemei,
    clausula_desconto,
    faixas_etarias_ativas,
):
    payload = {
        "relatorio_financeiro_id": str(relatorio_financeiro_cemei.uuid),
        "unidades_educacionais": [str(escola_cemei.uuid)],
        "tipo_lancamento": "DIETAS_TIPO_B",
        "clausula_desconto": str(clausula_desconto.uuid),
        "quantidade": 1,
    }

    serializer = DescontoFinanceiroUpdateSerializer(data=payload)

    assert not serializer.is_valid()

    assert "cei_ou_emei" in serializer.errors
    assert serializer.errors["cei_ou_emei"][0] == "Campo obrigatório para o grupo."

    payload["cei_ou_emei"] = TIPOS_UNIDADE_ESCOLAR.CEI.value

    serializer = DescontoFinanceiroUpdateSerializer(data=payload)

    assert not serializer.is_valid()

    assert "faixa_etaria" in serializer.errors
    assert "periodo_escolar" in serializer.errors

    assert serializer.errors["faixa_etaria"][0] == "Campo obrigatório para o grupo."
    assert serializer.errors["periodo_escolar"][0] == "Campo obrigatório para o grupo."

    payload["cei_ou_emei"] = TIPOS_UNIDADE_ESCOLAR.EMEI.value
    payload["faixa_etaria"] = str(faixas_etarias_ativas[0].uuid)

    serializer = DescontoFinanceiroUpdateSerializer(data=payload)

    assert not serializer.is_valid()

    assert "faixa_etaria" in serializer.errors
    assert (
        serializer.errors["faixa_etaria"][0]
        == "Não é permitido informar faixa etária para este grupo."
    )


@pytest.mark.django_db
def test_desconto_financeiro_serializer_grupo_cemei(
    relatorio_financeiro_cemei,
    escola_cemei,
    faixas_etarias_ativas,
    periodo_escolar_parcial,
    clausula_desconto,
    tipo_alimentacao_refeicao,
):
    payload_create = {
        "relatorio_financeiro_id": str(relatorio_financeiro_cemei.uuid),
        "unidades_educacionais": [str(escola_cemei.uuid)],
        "tipo_lancamento": "DIETAS_TIPO_A",
        "faixa_etaria": str(faixas_etarias_ativas[0].uuid),
        "periodo_escolar": periodo_escolar_parcial.nome,
        "clausula_desconto": str(clausula_desconto.uuid),
        "quantidade": 11,
        "cei_ou_emei": TIPOS_UNIDADE_ESCOLAR.CEI.value,
    }

    serializer = DescontoFinanceiroUpdateSerializer(data=payload_create)
    assert serializer.is_valid(), serializer.errors

    instance_created = serializer.save()

    assert instance_created.tipo_lancamento == "DIETAS_TIPO_A"
    assert instance_created.cei_ou_emei == TIPOS_UNIDADE_ESCOLAR.CEI.value
    assert instance_created.faixa_etaria == faixas_etarias_ativas[0]
    assert instance_created.periodo_escolar == periodo_escolar_parcial

    payload_update = {
        "cei_ou_emei": TIPOS_UNIDADE_ESCOLAR.EMEI.value,
        "tipo_alimentacao": str(tipo_alimentacao_refeicao.uuid),
        "faixa_etaria": None,
        "periodo_escolar": None,
    }

    serializer = DescontoFinanceiroUpdateSerializer(
        instance=instance_created,
        data=payload_update,
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors

    instance_updated = serializer.save()

    assert instance_updated.cei_ou_emei == TIPOS_UNIDADE_ESCOLAR.EMEI.value
    assert instance_updated.tipo_alimentacao == tipo_alimentacao_refeicao
    assert instance_updated.faixa_etaria is None
    assert instance_updated.periodo_escolar is None


@pytest.mark.django_db
def test_desconto_financeiro_grupo_emebs_campos_obrigatorios(
    relatorio_financeiro_emebs,
    escola_emebs,
    clausula_desconto,
):
    payload = {
        "relatorio_financeiro_id": str(relatorio_financeiro_emebs.uuid),
        "unidades_educacionais": [str(escola_emebs.uuid)],
        "tipo_lancamento": "DIETAS_TIPO_A",
        "clausula_desconto": str(clausula_desconto.uuid),
        "quantidade": 1,
    }

    serializer = DescontoFinanceiroUpdateSerializer(data=payload)

    assert not serializer.is_valid()

    assert "infantil_ou_fundamental" in serializer.errors
    assert (
        serializer.errors["infantil_ou_fundamental"][0]
        == "Campo obrigatório para o grupo."
    )


@pytest.mark.django_db
def test_desconto_financeiro_serializer_grupo_emebs(
    relatorio_financeiro_emebs,
    escola_emebs,
    tipo_alimentacao_refeicao,
    clausula_desconto,
):
    payload_create = {
        "relatorio_financeiro_id": str(relatorio_financeiro_emebs.uuid),
        "unidades_educacionais": [str(escola_emebs.uuid)],
        "tipo_lancamento": "DIETAS_TIPO_A",
        "tipo_alimentacao": str(tipo_alimentacao_refeicao.uuid),
        "clausula_desconto": str(clausula_desconto.uuid),
        "quantidade": 11,
        "infantil_ou_fundamental": "INFANTIL",
    }

    serializer = DescontoFinanceiroUpdateSerializer(data=payload_create)
    assert serializer.is_valid(), serializer.errors

    instance_created = serializer.save()

    assert instance_created.tipo_lancamento == "DIETAS_TIPO_A"
    assert instance_created.infantil_ou_fundamental == "INFANTIL"
    assert instance_created.tipo_alimentacao == tipo_alimentacao_refeicao

    payload_update = {
        "infantil_ou_fundamental": "FUNDAMENTAL",
        "faixa_etaria": None,
        "periodo_escolar": None,
    }

    serializer = DescontoFinanceiroUpdateSerializer(
        instance=instance_created,
        data=payload_update,
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors

    instance_updated = serializer.save()

    assert instance_updated.infantil_ou_fundamental == "FUNDAMENTAL"
    assert instance_updated.tipo_alimentacao == tipo_alimentacao_refeicao
