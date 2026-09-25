import pytest

from src.pos_recebimento.api.serializers.serializers import (
    TermoRecebimentoDefinitivoListagemSerializer,
    TermoRecebimentoDefinitivoPainelAssinaturaSerializer,
)
from src.pos_recebimento.models import TermoRecebimentoDefinitivo

pytestmark = pytest.mark.django_db


def test_listagem_retorna_apenas_os_campos_do_grid(termo_listagem):
    data = TermoRecebimentoDefinitivoListagemSerializer(termo_listagem).data

    assert set(data.keys()) == {
        "uuid",
        "nome_empresa",
        "cnpj_empresa",
        "numero_contrato",
        "numeros_cronogramas",
        "produtos",
        "status",
        "status_display",
        "data_cadastro",
        "alterado_em",
    }


def test_listagem_serializa_dados_do_termo(termo_listagem, empresa, contrato):
    data = TermoRecebimentoDefinitivoListagemSerializer(termo_listagem).data

    assert data["uuid"] == str(termo_listagem.uuid)
    assert data["nome_empresa"] == empresa.nome_fantasia
    assert data["cnpj_empresa"] == empresa.cnpj
    assert data["numero_contrato"] == contrato.numero
    assert data["status"] == TermoRecebimentoDefinitivo.ENVIADO_FISCAIS
    assert data["status_display"] == "Enviado Fiscais"
    assert data["data_cadastro"] == "15/03/2026"


def test_listagem_retorna_numeros_dos_cronogramas(termo_listagem):
    data = TermoRecebimentoDefinitivoListagemSerializer(termo_listagem).data

    assert sorted(data["numeros_cronogramas"]) == ["111/2026", "222/2026"]


def test_painel_assinatura_retorna_apenas_os_campos_do_card(
    termos_painel_assinatura,
):
    data = TermoRecebimentoDefinitivoPainelAssinaturaSerializer(
        termos_painel_assinatura.pendente_do_fiscal
    ).data

    assert set(data.keys()) == {
        "uuid",
        "empresa",
        "numero_contrato",
        "numeros_cronogramas",
        "nomes_produtos",
        "criado_em",
    }


def test_painel_assinatura_serializa_dados_do_termo(termos_painel_assinatura):
    termo = termos_painel_assinatura.pendente_do_fiscal

    data = TermoRecebimentoDefinitivoPainelAssinaturaSerializer(termo).data

    assert data["uuid"] == str(termo.uuid)
    assert data["empresa"] == "ALFA ALIMENTOS"
    assert data["numero_contrato"] == "111/2026"
    assert sorted(data["numeros_cronogramas"]) == ["001/2026", "002/2026"]
    assert sorted(data["nomes_produtos"]) == ["ABACATE", "MAMAO PAPAYA"]
    assert data["criado_em"] == "15/03/2026"


def test_painel_assinatura_nao_repete_nome_de_produto(termos_painel_assinatura):
    """Cronogramas distintos com o mesmo produto rendem um único nome."""
    data = TermoRecebimentoDefinitivoPainelAssinaturaSerializer(
        termos_painel_assinatura.assinado_do_fiscal
    ).data

    assert data["nomes_produtos"] == ["MAMAO PAPAYA"]
