import pytest
from model_bakery import baker

from src.medicao_inicial.api.serializers_create import DescontoFinanceiroUpdateSerializer
from src.medicao_inicial.models import DescontoFinanceiro


@pytest.mark.django_db
def test_desconto_financeiro_serializer_create(
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
def test_desconto_financeiro_serializer_update(
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
def test_desconto_financeiro_serializer_create_cei_campos_obrigatorios(
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
def test_desconto_financeiro_serializer_create_emei_nao_permite_faixa_etaria(
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
