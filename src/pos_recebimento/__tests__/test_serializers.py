import pytest

from src.pos_recebimento.api.serializers.serializers import (
    TermoRecebimentoDefinitivoListagemSerializer,
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
