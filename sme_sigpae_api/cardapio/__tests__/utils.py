from rest_framework import status


def _checa_se_terceirizada_marcou_conferencia_na_gestao_de_alimentacao(
    client_autenticado, classe, path
):
    obj = classe.objects.first()
    assert not obj.terceirizada_conferiu_gestao

    response = client_autenticado.patch(
        f"/{path}/{obj.uuid}/marcar-conferida/", content_type="application/json"
    )

    assert response.status_code == status.HTTP_200_OK

    result = response.json()
    assert "terceirizada_conferiu_gestao" in result.keys()
    assert result["terceirizada_conferiu_gestao"]

    obj = classe.objects.first()
    assert obj.terceirizada_conferiu_gestao
