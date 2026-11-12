import json
from unittest.mock import patch

import pytest
from rest_framework import status

from src.dados_comuns import constants as const
from src.dados_comuns.models import LogSolicitacoesUsuario
from src.pos_recebimento.models import (
    AssinaturaTermoRecebimentoProvisorio,
    TermoRecebimentoProvisorio,
)

pytestmark = pytest.mark.django_db

URL_PENDENTES = "/pos-recebimento/termos/pendentes-assinatura/"
URL_ASSINADOS = "/pos-recebimento/termos/assinados/"


SENHA_INCORRETA = "senha-errada"


def _url_assinar(termo):
    return f"/pos-recebimento/termos/{termo.uuid}/fiscal-assina-termo/"


def _assinar(client, termo, password=const.DJANGO_ADMIN_PASSWORD):
    return client.patch(
        _url_assinar(termo),
        content_type="application/json",
        data=json.dumps({"password": password}),
    )


def _login(client, usuario):
    client.logout()
    client.login(
        username=usuario.username,
        password=const.DJANGO_ADMIN_PASSWORD,
    )
    return client


def _uuids(response):
    return [termo["uuid"] for termo in response.json()["results"]]


def test_fiscal_assina_termo_registra_assinatura(
    client, tres_fiscais, termo_para_assinatura
):
    _login(client, tres_fiscais[0])
    response = _assinar(client, termo_para_assinatura)

    assert response.status_code == status.HTTP_200_OK
    assinatura = AssinaturaTermoRecebimentoProvisorio.objects.get(
        termo=termo_para_assinatura, usuario=tres_fiscais[0]
    )
    assert assinatura.etapa == AssinaturaTermoRecebimentoProvisorio.FISCAL_CONTRATO
    termo_para_assinatura.refresh_from_db()
    assert termo_para_assinatura.status == TermoRecebimentoProvisorio.ENVIADO_FISCAIS
    assert LogSolicitacoesUsuario.objects.filter(
        uuid_original=termo_para_assinatura.uuid,
        status_evento=(
            LogSolicitacoesUsuario.TERMO_RECEBIMENTO_PROVISORIO_ASSINADO_PELO_FISCAL
        ),
        usuario=tres_fiscais[0],
    ).exists()


def test_fiscal_assina_termo_senha_incorreta_retorna_401(
    client, tres_fiscais, termo_para_assinatura
):
    _login(client, tres_fiscais[0])
    response = _assinar(client, termo_para_assinatura, password=SENHA_INCORRETA)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not AssinaturaTermoRecebimentoProvisorio.objects.exists()


def test_fiscal_assina_termo_usuario_nao_e_fiscal_do_termo_retorna_403(
    client_autenticado_qualidade, termo_para_assinatura
):
    response = _assinar(client_autenticado_qualidade, termo_para_assinatura)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not AssinaturaTermoRecebimentoProvisorio.objects.exists()


@pytest.mark.parametrize(
    "nome_client",
    [
        "client_autenticado_dilog_cronograma",
        "client_autenticado_codae_dilog",
        "client_autenticado_dilog_diretoria",
        "client_autenticado_fornecedor",
        "client_autenticado_usuario_empresa",
    ],
)
def test_fiscal_assina_termo_perfil_sem_permissao_retorna_403(
    request, nome_client, termo_para_assinatura
):
    response = _assinar(request.getfixturevalue(nome_client), termo_para_assinatura)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not AssinaturaTermoRecebimentoProvisorio.objects.exists()


def test_fiscal_assina_termo_duas_vezes_retorna_400(
    client, tres_fiscais, termo_para_assinatura
):
    _login(client, tres_fiscais[0])
    assert _assinar(client, termo_para_assinatura).status_code == status.HTTP_200_OK

    response = _assinar(client, termo_para_assinatura)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert AssinaturaTermoRecebimentoProvisorio.objects.count() == 1


def test_fiscal_assina_termo_corrida_duplicada_retorna_400(
    client, tres_fiscais, termo_para_assinatura
):
    """Corrida: a validação passa, mas o registro já existe no banco."""
    _login(client, tres_fiscais[0])
    AssinaturaTermoRecebimentoProvisorio.objects.create(
        termo=termo_para_assinatura,
        usuario=tres_fiscais[0],
        etapa=AssinaturaTermoRecebimentoProvisorio.FISCAL_CONTRATO,
    )

    with patch.object(
        TermoRecebimentoProvisorio,
        "usuario_ja_assinou_fiscal",
        return_value=False,
    ):
        response = _assinar(client, termo_para_assinatura)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "já assinou" in response.json()["detail"]
    assert AssinaturaTermoRecebimentoProvisorio.objects.count() == 1


def test_assinaturas_dos_fiscais_podem_ocorrer_em_qualquer_ordem(
    client, tres_fiscais, termo_para_assinatura
):
    """Cenário 7: a etapa conclui somente após a terceira assinatura."""
    ordem = [tres_fiscais[1], tres_fiscais[2], tres_fiscais[0]]

    for indice, fiscal in enumerate(ordem):
        _login(client, fiscal)
        response = _assinar(client, termo_para_assinatura)

        assert response.status_code == status.HTTP_200_OK
        termo_para_assinatura.refresh_from_db()
        esperado = (
            TermoRecebimentoProvisorio.ENVIADO_DILOG
            if indice == 2
            else TermoRecebimentoProvisorio.ENVIADO_FISCAIS
        )
        assert termo_para_assinatura.status == esperado

    assert LogSolicitacoesUsuario.objects.filter(
        uuid_original=termo_para_assinatura.uuid,
        status_evento=(
            LogSolicitacoesUsuario.TERMO_RECEBIMENTO_PROVISORIO_ETAPA_FISCAIS_CONCLUIDA
        ),
    ).exists()


def test_etapa_fiscais_concluida_reflete_as_tres_assinaturas(
    client, tres_fiscais, termo_para_assinatura
):
    assert termo_para_assinatura.etapa_fiscais_concluida is False

    for fiscal in tres_fiscais[:2]:
        _login(client, fiscal)
        _assinar(client, termo_para_assinatura)
        assert termo_para_assinatura.etapa_fiscais_concluida is False

    _login(client, tres_fiscais[2])
    _assinar(client, termo_para_assinatura)
    assert termo_para_assinatura.etapa_fiscais_concluida is True


def test_etapa_conclui_com_fiscal_repetido_em_dois_papeis(
    client, tres_fiscais, termo_fiscais_repetidos
):
    """O fiscal repetido assina uma única vez, cobrindo os dois papéis."""
    _login(client, tres_fiscais[0])
    assert _assinar(client, termo_fiscais_repetidos).status_code == status.HTTP_200_OK

    termo_fiscais_repetidos.refresh_from_db()
    assert termo_fiscais_repetidos.status == TermoRecebimentoProvisorio.ENVIADO_FISCAIS

    resposta_repetida = _assinar(client, termo_fiscais_repetidos)
    assert resposta_repetida.status_code == status.HTTP_400_BAD_REQUEST

    _login(client, tres_fiscais[2])
    assert _assinar(client, termo_fiscais_repetidos).status_code == status.HTTP_200_OK

    termo_fiscais_repetidos.refresh_from_db()
    assert termo_fiscais_repetidos.status == TermoRecebimentoProvisorio.ENVIADO_DILOG
    assert termo_fiscais_repetidos.etapa_fiscais_concluida is True


def test_etapa_conclui_com_o_mesmo_fiscal_nos_tres_papeis(
    client, tres_fiscais, termo_fiscal_unico
):
    """A assinatura única conclui a etapa quando o fiscal ocupa os 3 papéis."""
    _login(client, tres_fiscais[0])
    assert _assinar(client, termo_fiscal_unico).status_code == status.HTTP_200_OK

    termo_fiscal_unico.refresh_from_db()
    assert termo_fiscal_unico.status == TermoRecebimentoProvisorio.ENVIADO_DILOG
    assert termo_fiscal_unico.etapa_fiscais_concluida is True


def test_assinados_traz_termo_com_fiscais_repetidos(
    client, tres_fiscais, termo_fiscais_repetidos
):
    _login(client, tres_fiscais[0])
    _assinar(client, termo_fiscais_repetidos)
    _login(client, tres_fiscais[2])
    _assinar(client, termo_fiscais_repetidos)

    for fiscal in (tres_fiscais[0], tres_fiscais[2]):
        _login(client, fiscal)
        response = client.get(URL_ASSINADOS)
        assert str(termo_fiscais_repetidos.uuid) in _uuids(response)


def test_fiscal_assina_termo_fora_da_etapa_dos_fiscais_retorna_400(
    client, tres_fiscais, termo_para_assinatura
):
    TermoRecebimentoProvisorio.objects.filter(pk=termo_para_assinatura.pk).update(
        status=TermoRecebimentoProvisorio.ENVIADO_DILOG
    )

    _login(client, tres_fiscais[0])
    response = _assinar(client, termo_para_assinatura)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not AssinaturaTermoRecebimentoProvisorio.objects.exists()


def test_pendentes_assinatura_exclui_termo_ja_assinado_pelo_fiscal(
    client, tres_fiscais, termo_para_assinatura
):
    """Cenário 5: o termo sai do card só para o fiscal que assinou."""
    _login(client, tres_fiscais[0])
    _assinar(client, termo_para_assinatura)

    response = client.get(URL_PENDENTES)
    assert str(termo_para_assinatura.uuid) not in _uuids(response)

    _login(client, tres_fiscais[1])
    response = client.get(URL_PENDENTES)
    assert str(termo_para_assinatura.uuid) in _uuids(response)


def test_assinados_traz_termo_com_etapa_dos_fiscais_concluida(
    client, tres_fiscais, termo_para_assinatura
):
    """Card 'Assinados': etapa concluída aparece para os três fiscais."""
    for fiscal in tres_fiscais:
        _login(client, fiscal)
        assert _assinar(client, termo_para_assinatura).status_code == status.HTTP_200_OK

    for fiscal in tres_fiscais:
        _login(client, fiscal)
        response = client.get(URL_ASSINADOS)
        assert str(termo_para_assinatura.uuid) in _uuids(response)


def test_assinados_nao_traz_termo_com_etapa_dos_fiscais_pendente(
    client, tres_fiscais, termo_para_assinatura
):
    _login(client, tres_fiscais[0])
    _assinar(client, termo_para_assinatura)
    _login(client, tres_fiscais[1])
    _assinar(client, termo_para_assinatura)

    response = client.get(URL_ASSINADOS)
    assert str(termo_para_assinatura.uuid) not in _uuids(response)


def test_pendentes_assinatura_negado_para_dilog_diretoria(
    client, usuario_dilog_diretoria, tres_fiscais, termo_para_assinatura
):
    """Nem com a etapa dos fiscais concluída a Diretoria acessa o Painel."""
    for fiscal in tres_fiscais:
        _login(client, fiscal)
        _assinar(client, termo_para_assinatura)

    termo_para_assinatura.refresh_from_db()
    assert termo_para_assinatura.status == TermoRecebimentoProvisorio.ENVIADO_DILOG

    _login(client, usuario_dilog_diretoria)

    assert client.get(URL_PENDENTES).status_code == status.HTTP_403_FORBIDDEN


def test_retrieve_pode_assinar_true_para_fiscal_com_assinatura_pendente(
    client, tres_fiscais, termo_para_assinatura
):
    _login(client, tres_fiscais[0])
    response = client.get(f"/pos-recebimento/termos/{termo_para_assinatura.uuid}/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["pode_assinar"] is True


def test_retrieve_pode_assinar_false_apos_assinar(
    client, tres_fiscais, termo_para_assinatura
):
    _login(client, tres_fiscais[0])
    _assinar(client, termo_para_assinatura)

    response = client.get(f"/pos-recebimento/termos/{termo_para_assinatura.uuid}/")

    assert response.json()["pode_assinar"] is False


def test_retrieve_pode_assinar_false_para_usuario_que_nao_e_fiscal(
    client_autenticado_dilog_cronograma, termo_para_assinatura
):
    response = client_autenticado_dilog_cronograma.get(
        f"/pos-recebimento/termos/{termo_para_assinatura.uuid}/"
    )

    assert response.json()["pode_assinar"] is False
