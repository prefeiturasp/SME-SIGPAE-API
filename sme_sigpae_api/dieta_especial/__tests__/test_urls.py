import base64
import datetime
from datetime import date, timedelta

from rest_framework import status

from ...dados_comuns import constants
from ...dados_comuns.fluxo_status import DietaEspecialWorkflow
from ...terceirizada.models import Terceirizada
from ..constants import (
    ENDPOINT_ALERGIAS_INTOLERANCIAS,
    ENDPOINT_ALIMENTOS,
    ENDPOINT_CLASSIFICACOES_DIETA,
    ENDPOINT_MOTIVOS_NEGACAO,
)
from ..models import (
    AlergiaIntolerancia,
    Alimento,
    ClassificacaoDieta,
    MotivoNegacao,
    ProtocoloPadraoDietaEspecial,
    SolicitacaoDietaEspecial,
    SubstituicaoAlimento,
)


def endpoint_lista(client_autenticado, endpoint, quantidade):
    response = client_autenticado.get(f"/{endpoint}/")
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json) == quantidade


def test_url_endpoint_lista_alergias_intolerancias(
    client_autenticado, alergias_intolerancias
):
    endpoint_lista(client_autenticado, ENDPOINT_ALERGIAS_INTOLERANCIAS, quantidade=2)


def test_url_endpoint_lista_alimentos(client_autenticado, alimentos):
    endpoint_lista(client_autenticado, ENDPOINT_ALIMENTOS, quantidade=6)


def test_url_endpoint_lista_classificacoes_dieta(
    client_autenticado, classificacoes_dieta
):
    endpoint_lista(client_autenticado, ENDPOINT_CLASSIFICACOES_DIETA, quantidade=3)


def test_url_endpoint_lista_motivos_negacao(client_autenticado, motivos_negacao):
    endpoint_lista(client_autenticado, ENDPOINT_MOTIVOS_NEGACAO, quantidade=4)


def endpoint_detalhe(client_autenticado, endpoint, modelo, tem_nome=False):
    obj = modelo.objects.first()
    response = client_autenticado.get(f"/{endpoint}/{obj.id}/")
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert obj.descricao == json["descricao"]
    if tem_nome:
        assert obj.nome == json["nome"]


def test_url_endpoint_detalhe_alergias_intolerancias(
    client_autenticado, alergias_intolerancias
):
    endpoint_detalhe(
        client_autenticado, ENDPOINT_ALERGIAS_INTOLERANCIAS, AlergiaIntolerancia
    )


def test_url_endpoint_detalhe_classificacoes_dieta(
    client_autenticado, classificacoes_dieta
):
    endpoint_detalhe(
        client_autenticado,
        ENDPOINT_CLASSIFICACOES_DIETA,
        ClassificacaoDieta,
        tem_nome=True,
    )


def test_url_endpoint_detalhe_motivos_negacao(client_autenticado, motivos_negacao):
    endpoint_detalhe(client_autenticado, ENDPOINT_MOTIVOS_NEGACAO, MotivoNegacao)


def test_permissoes_dieta_especial_viewset(
    client_autenticado_vinculo_escola_dieta,
    solicitacao_dieta_especial,
    solicitacao_dieta_especial_outra_dre,
):
    client, user = client_autenticado_vinculo_escola_dieta
    # pode ver os dados de uma suspensão de alimentação da mesma escola
    response = client.get(
        f"/solicitacoes-dieta-especial/{solicitacao_dieta_especial.uuid}/"
    )
    assert response.status_code == status.HTTP_200_OK
    # Não pode ver dados de uma suspensão de alimentação de outra escola
    response = client.get(
        f"/solicitacoes-dieta-especial/{solicitacao_dieta_especial_outra_dre.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    response = client.delete(
        f"/solicitacoes-dieta-especial/{solicitacao_dieta_especial.uuid}/"
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_url_criar_dieta(
    client_autenticado_vinculo_escola,
    periodo_escolar_integral,
):
    payload = {
        "observacoes": "<p>dsadsadasd</p>\n",
        "aluno_json": {
            "codigo_eol": "6",
            "nome": "ADRIANO RIBEIRO MINANTE",
            "data_nascimento": "01/07/1982",
        },
        "nome_completo_pescritor": "fffdasdasdasd",
        "registro_funcional_pescritor": "aasddd",
        "anexos": [
            {
                "arquivo": "data:image/png;base64,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",  # noqa
                "nome": "Captura de tela de 2020-01-16 10-17-02.png",
            }
        ],
    }
    response = client_autenticado_vinculo_escola.post(
        "/solicitacoes-dieta-especial/", content_type="application/json", data=payload
    )
    assert response.status_code == status.HTTP_201_CREATED
    response = client_autenticado_vinculo_escola.post(
        "/solicitacoes-dieta-especial/", content_type="application/json", data=payload
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == ["Aluno já possui Solicitação de Dieta Especial pendente"]


def test_url_criar_dieta_duplicada_alteracao_ue_recreio_ferias(
    client_autenticado_vinculo_escola_dieta,
    periodo_escolar_integral,
    solicitacao_dieta_especial_aprovada_alteracao_ue,
    motivo_alteracao_ue,
):
    client, user = client_autenticado_vinculo_escola_dieta
    dieta_aprovada = solicitacao_dieta_especial_aprovada_alteracao_ue
    motivo_alteracao_ue = motivo_alteracao_ue

    # Prepare payload using real data from fixture
    payload = {
        "codigo_eol_aluno": dieta_aprovada.aluno.codigo_eol,
        "nome_aluno": dieta_aprovada.aluno.nome,
        "data_nascimento": dieta_aprovada.aluno.data_nascimento,
        "motivo_alteracao": motivo_alteracao_ue.uuid,
        "codigo_eol_escola": dieta_aprovada.rastro_escola.codigo_eol,
        "nome_escola": dieta_aprovada.rastro_escola.nome,
        "observacoes_alteracao": "<p>teste11</p>",
        "data_inicio": date.today().strftime("%d/%m/%Y"),
        "data_termino": (date.today() + timedelta(days=10)).strftime("%d/%m/%Y"),
        "dieta_alterada": dieta_aprovada.dieta_alterada.uuid,
        "escola_destino": dieta_aprovada.escola_destino.codigo_eol,
    }

    response = client.post(
        "/solicitacoes-dieta-especial/alteracao-ue/",
        content_type="application/json",
        data=payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == [
        "Já foi realizada uma alteração de UE para o aluno por motivo de Recreio nas Férias"
    ]


def test_url_criar_dieta_error(client_autenticado_vinculo_escola):
    payload = {
        "observacoes": "<p>dsadsadasd</p>\n",
        "aluno_json": {
            "codigo_eol": "123ABC",
            "nome": "OLA TENHO QUE DAR ERRRO OLA TENHO QUE DAR ERRRO OLA TENHO QUE DAR ERRRO OLA TENHO QUE DAR ERRRO OLA TENHO QUE DAR ERRRO OLA TENHO QUE DAR ERRRO OLA TENHO QUE DAR ERRRO OLA TENHO QUE DAR ERRRO",  # noqa
            "data_nascimento": "33/07/1982",
        },
        "nome_completo_pescritor": "fffdasdasdasd",
        "registro_funcional_pescritor": "aasddd",
        "anexos": [
            {
                "arquivo": "data:image/png;base64,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",  # noqa
                "nome": "Captura de tela de 2020-01-16 10-17-02.png",
            }
        ],
    }
    response = client_autenticado_vinculo_escola.post(
        "/solicitacoes-dieta-especial/", content_type="application/json", data=payload
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "aluno_json": [
            "{'codigo_eol': [ErrorDetail(string='Deve ter somente dígitos', code='invalid')], "
            "'nome': [ErrorDetail(string='Certifique-se de que este campo não tenha mais de 100 caracteres.', "
            "code='max_length')], "
            "'data_nascimento': [ErrorDetail(string='Formato de data inválido, deve ser dd/mm/aaaa', code='invalid')]}"
        ]
    }


def test_url_criar_dieta_erro_sem_anexos(client_autenticado_vinculo_escola):
    payload = {
        "observacoes": "<p>dsadsadasd</p>\n",
        "aluno_json": {
            "codigo_eol": "6",
            "nome": "ADRIANO RIBEIRO MINANTE",
            "data_nascimento": "01/07/1982",
        },
        "nome_completo_pescritor": "fffdasdasdasd",
        "registro_funcional_pescritor": "aasddd",
        "anexos": [],
    }
    response = client_autenticado_vinculo_escola.post(
        "/solicitacoes-dieta-especial/", content_type="application/json", data=payload
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"anexos": ["Anexos não pode ser vazio"]}


def test_url_criar_dieta_erro_anexo_muito_grande(client_autenticado_vinculo_escola):
    with open("sme_sigpae_api/static/files/teste_tamanho.pdf", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    payload = {
        "observacoes": "<p>dsadsadasd</p>\n",
        "aluno_json": {
            "codigo_eol": "6",
            "nome": "ADRIANO RIBEIRO MINANTE",
            "data_nascimento": "01/07/1982",
        },
        "nome_completo_pescritor": "fffdasdasdasd",
        "registro_funcional_pescritor": "aasddd",
        "anexos": [
            {
                "arquivo": "data:application/pdf;base64,"
                + encoded_string.decode("utf-8"),
                "nome": "oi.pdf",
            }
        ],
    }
    response = client_autenticado_vinculo_escola.post(
        "/solicitacoes-dieta-especial/", content_type="application/json", data=payload
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"anexos": ["O tamanho máximo de um arquivo é 10MB"]}


def test_url_criar_dieta_erro_aluno_falta_atributo(client_autenticado_vinculo_escola):
    payload = {
        "observacoes": "<p>dsadsadasd</p>\n",
        "aluno_json": {
            "nome": "ADRIANO RIBEIRO MINANTE",
            "data_nascimento": "01/07/1982",
        },
        "nome_completo_pescritor": "fffdasdasdasd",
        "registro_funcional_pescritor": "aasddd",
        "anexos": [
            {
                "arquivo": "data:image/png;base64,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",  # noqa
                "nome": "oi.pdf",
            }
        ],
    }
    response = client_autenticado_vinculo_escola.post(
        "/solicitacoes-dieta-especial/", content_type="application/json", data=payload
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"aluno_json": ["deve ter atributo codigo_eol"]}


def test_url_atualizar_dieta(
    client_autenticado_vinculo_escola,  # noqa C901
    solicitacao_dieta_especial,
    classificacoes_dieta,
    alergias_intolerancias,
    protocolo_padrao_dieta_especial,
    substituicoes,
):
    payload = {
        "observacoes": "<p>dsadsadasd</p>\n",
        "nome_completo_pescritor": "fffdasdasdasd",
        "registro_funcional_pescritor": "aasddd",
        "anexos": [
            {
                "arquivo": "data:image/png;base64,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",  # noqa
                "nome": "Captura de tela de 2020-01-16 10-17-02.png",
            }
        ],
        "classificacao": classificacoes_dieta[1].id,
        "alergias_intolerancias": [alergias_intolerancias[1].id],
        "informacoes_adicionais": "Um textinho bem pequenininho",
        "protocolo_padrao": protocolo_padrao_dieta_especial.uuid,
        "nome_protocolo": protocolo_padrao_dieta_especial.nome_protocolo,
        "orientacoes_gerais": "Um texto grande aqui",
        "substituicoes": substituicoes,
    }
    response = client_autenticado_vinculo_escola.patch(
        f"/solicitacoes-dieta-especial/{solicitacao_dieta_especial.uuid}/",
        content_type="application/json",
        data=payload,
    )
    assert response.status_code == status.HTTP_200_OK

    solic = SolicitacaoDietaEspecial.objects.first()

    assert solic.observacoes == payload["observacoes"][:-1]
    assert solic.nome_completo_pescritor == payload["nome_completo_pescritor"]
    assert solic.registro_funcional_pescritor == payload["registro_funcional_pescritor"]
    assert solic.informacoes_adicionais == payload["informacoes_adicionais"]
    assert solic.classificacao == classificacoes_dieta[1]

    for solic_anexo, payload_anexo in zip(solic.anexos, payload["anexos"]):
        assert solic_anexo.nome == payload_anexo["nome"]

    for ai in solic.alergias_intolerancias.all():
        assert ai.id in payload["alergias_intolerancias"]

    qs_substituicoes = SubstituicaoAlimento.objects.filter(
        solicitacao_dieta_especial=solic
    )
    assert qs_substituicoes.count() == len(payload["substituicoes"])

    for obj, substituicao in zip(qs_substituicoes, payload["substituicoes"]):
        assert obj.alimento.id == substituicao["alimento"]
        assert obj.tipo == substituicao["tipo"]
        for obj_substituto in obj.substitutos.all():
            assert obj_substituto.uuid in substituicao["substitutos"]


def test_url_endpoint_autorizar_dieta(
    client_autenticado_vinculo_codae_dieta,
    solicitacao_dieta_especial,
    payload_autorizar,
):
    obj = SolicitacaoDietaEspecial.objects.first()
    obj.status = SolicitacaoDietaEspecial.workflow_class.CODAE_A_AUTORIZAR
    obj.save()
    data_termino = datetime.date.today() + datetime.timedelta(days=60)
    payload_autorizar["data_termino"] = data_termino.isoformat()
    response = client_autenticado_vinculo_codae_dieta.patch(
        f"/solicitacoes-dieta-especial/{obj.uuid}/autorizar/",
        content_type="application/json",
        data=payload_autorizar,
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["detail"] == "Autorização de Dieta Especial realizada com sucesso!"

    obj.refresh_from_db()

    assert obj.status == DietaEspecialWorkflow.CODAE_AUTORIZADO
    assert (
        obj.registro_funcional_nutricionista
        == payload_autorizar["registro_funcional_nutricionista"]
    )
    assert obj.informacoes_adicionais == payload_autorizar["informacoes_adicionais"]
    assert obj.ativo is True
    for ai in obj.alergias_intolerancias.all():
        assert ai.id in payload_autorizar["alergias_intolerancias"]
    assert obj.classificacao.id == payload_autorizar["classificacao"]
    assert obj.data_termino.year == data_termino.year
    assert obj.data_termino.month == data_termino.month
    assert obj.data_termino.day == data_termino.day

    qs_substituicoes = SubstituicaoAlimento.objects.filter(
        solicitacao_dieta_especial=obj
    )
    assert qs_substituicoes.count() == len(payload_autorizar["substituicoes"])

    for obj, substituicao in zip(qs_substituicoes, payload_autorizar["substituicoes"]):
        assert obj.alimento.id == substituicao["alimento"]
        assert obj.tipo == substituicao["tipo"]
        for obj_substituto in obj.substitutos.all():
            assert obj_substituto.uuid in substituicao["substitutos"]


def test_url_endpoint_autorizar_dieta_gestao_alimentacao(
    client_autenticado_vinculo_codae_gestao_alimentacao_dieta,
    solicitacao_dieta_especial,
    payload_autorizar,
):
    client, user = client_autenticado_vinculo_codae_gestao_alimentacao_dieta
    obj = SolicitacaoDietaEspecial.objects.first()
    obj.status = SolicitacaoDietaEspecial.workflow_class.CODAE_A_AUTORIZAR
    obj.save()
    response = client.patch(
        f"/solicitacoes-dieta-especial/{obj.uuid}/autorizar/",
        content_type="application/json",
        data=payload_autorizar,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_url_endpoint_autorizar_dieta_atributos_obrigatorios(
    client_autenticado_vinculo_codae_dieta,
    solicitacao_dieta_especial,
    payload_autorizar,
):
    obj = SolicitacaoDietaEspecial.objects.first()

    campos = [
        "alergias_intolerancias",
        "classificacao",
        "registro_funcional_nutricionista",
        "substituicoes",
    ]
    for campo in campos:
        payload = payload_autorizar.copy()
        payload.pop(campo)

        response = client_autenticado_vinculo_codae_dieta.patch(
            f"/solicitacoes-dieta-especial/{obj.uuid}/autorizar/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        json = response.json()
        assert json["detail"].startswith("Dados inválidos")
        assert json["detail"].find(f"deve ter atributo {campo}") > -1


def test_url_endpoint_autorizar_dieta_atributos_lista_nao_vazios(
    client_autenticado_vinculo_codae_dieta,
    solicitacao_dieta_especial,
    payload_autorizar,
):
    obj = SolicitacaoDietaEspecial.objects.first()

    campos = ["substituicoes", "alergias_intolerancias"]
    for campo in campos:
        payload = payload_autorizar.copy()
        payload[campo] = []

        response = client_autenticado_vinculo_codae_dieta.patch(
            f"/solicitacoes-dieta-especial/{obj.uuid}/autorizar/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        json = response.json()
        assert json["detail"].startswith("Dados inválidos")
        assert json["detail"].find(f"atributo {campo} não pode ser vazio") > -1


def test_url_endpoint_autorizar_dieta_atributos_string_nao_vazios(
    client_autenticado_vinculo_codae_dieta,
    solicitacao_dieta_especial,
    payload_autorizar,
):
    obj = SolicitacaoDietaEspecial.objects.first()

    payload_autorizar["registro_funcional_nutricionista"] = ""

    response = client_autenticado_vinculo_codae_dieta.patch(
        f"/solicitacoes-dieta-especial/{obj.uuid}/autorizar/",
        content_type="application/json",
        data=payload_autorizar,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    json = response.json()
    assert json["detail"].startswith("Dados inválidos")
    assert (
        json["detail"].find(
            "atributo registro_funcional_nutricionista não pode ser vazio"
        )
        > -1
    )


def test_url_endpoint_autorizar_dieta_atributos_string_vazios(
    client_autenticado_vinculo_codae_dieta,
    solicitacao_dieta_especial,
    payload_autorizar,
):
    obj = SolicitacaoDietaEspecial.objects.first()
    obj.status = SolicitacaoDietaEspecial.workflow_class.CODAE_A_AUTORIZAR
    obj.save()
    payload_autorizar["informacoes_adicionais"] = ""

    response = client_autenticado_vinculo_codae_dieta.patch(
        f"/solicitacoes-dieta-especial/{obj.uuid}/autorizar/",
        content_type="application/json",
        data=payload_autorizar,
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["detail"] == "Autorização de Dieta Especial realizada com sucesso!"


def test_url_endpoint_autorizar_dieta_data_termino_no_passado(
    client_autenticado_vinculo_codae_dieta,
    solicitacao_dieta_especial,
    payload_autorizar,
):
    obj = SolicitacaoDietaEspecial.objects.first()
    obj.status = SolicitacaoDietaEspecial.workflow_class.CODAE_A_AUTORIZAR
    obj.save()
    data_termino = datetime.date.today() - datetime.timedelta(days=60)
    payload_autorizar["data_termino"] = data_termino.isoformat()
    response = client_autenticado_vinculo_codae_dieta.patch(
        f"/solicitacoes-dieta-especial/{obj.uuid}/autorizar/",
        content_type="application/json",
        data=payload_autorizar,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    json = response.json()
    assert (
        json["detail"]
        == "Dados inválidos [ErrorDetail(string='Não pode ser no passado', code='invalid')]"
    )


def test_url_endpoint_cancelar_dieta(
    client_autenticado_vinculo_escola_dieta, solicitacao_dieta_especial_a_autorizar
):
    obj = SolicitacaoDietaEspecial.objects.first()
    data = {"justificativa": "Uma justificativa fajuta"}
    client, user = client_autenticado_vinculo_escola_dieta
    response = client.post(
        f"/solicitacoes-dieta-especial/{obj.uuid}/escola-cancela-dieta-especial/",
        content_type="application/json",
        data=data,
    )
    obj.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert obj.status == DietaEspecialWorkflow.ESCOLA_CANCELOU
    response = client.post(
        f"/solicitacoes-dieta-especial/{obj.uuid}/escola-cancela-dieta-especial/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'cancelar_pedido' isn't available from state "
        + "'ESCOLA_CANCELOU'."
    }


def test_url_endpoint_negar_cancelamento_dieta(
    client_autenticado_vinculo_escola_dieta,
    solicitacao_dieta_especial_a_autorizar,
    motivos_negacao,
):
    obj = SolicitacaoDietaEspecial.objects.first()
    data = {
        "justificativa": "Uma justificativa fajuta",
        "motivo_negacao": motivos_negacao[0].id,
    }
    client, user = client_autenticado_vinculo_escola_dieta
    response = client.post(
        f"/solicitacoes-dieta-especial/{obj.uuid}/negar-cancelamento-dieta-especial/",
        content_type="application/json",
        data=data,
    )
    obj.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert obj.status == DietaEspecialWorkflow.CODAE_NEGOU_CANCELAMENTO
    client, user = client_autenticado_vinculo_escola_dieta
    response = client.post(
        f"/solicitacoes-dieta-especial/{obj.uuid}/negar-cancelamento-dieta-especial/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'negar_cancelamento_pedido' isn't available from state "
        + "'CODAE_NEGOU_CANCELAMENTO'."
    }


def test_url_endpoint_negar_dieta(
    client_autenticado_vinculo_codae_dieta, solicitacao_dieta_especial, motivos_negacao
):
    obj = SolicitacaoDietaEspecial.objects.first()
    obj.status = SolicitacaoDietaEspecial.workflow_class.CODAE_A_AUTORIZAR
    obj.save()
    data = {
        "justificativa_negacao": "Uma justificativa fajuta",
        "motivo_negacao": motivos_negacao[0].id,
        "registro_funcional_nutricionista": "ELABORADO por USUARIO NUTRICIONISTA CODAE - CRN null",
    }
    response = client_autenticado_vinculo_codae_dieta.post(
        f"/solicitacoes-dieta-especial/{obj.uuid}/negar/",
        content_type="application/json",
        data=data,
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["mensagem"] == "Solicitação de Dieta Especial Negada"

    obj.refresh_from_db()

    assert obj.status == DietaEspecialWorkflow.CODAE_NEGOU_PEDIDO
    assert obj.justificativa_negacao == data["justificativa_negacao"]
    assert obj.motivo_negacao.id == data["motivo_negacao"]
    assert (
        obj.registro_funcional_nutricionista == data["registro_funcional_nutricionista"]
    )


def test_url_endpoint_tomar_ciencia_dieta(
    client_autenticado_vinculo_terceirizada_dieta, solicitacao_dieta_especial
):
    obj = SolicitacaoDietaEspecial.objects.first()
    obj.status = SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO
    obj.save()
    response = client_autenticado_vinculo_terceirizada_dieta.post(
        f"/solicitacoes-dieta-especial/{obj.uuid}/tomar_ciencia/",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["mensagem"] == "Ciente da solicitação de dieta especial"

    obj.refresh_from_db()

    assert obj.status == DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA


def test_url_endpoint_marcar_conferida(
    client_autenticado_vinculo_terceirizada_dieta, solicitacao_dieta_especial
):
    obj = SolicitacaoDietaEspecial.objects.first()
    assert not obj.conferido

    response = client_autenticado_vinculo_terceirizada_dieta.patch(
        f"/solicitacoes-dieta-especial/{obj.uuid}/marcar-conferida/",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert "conferido" in json.keys()
    assert json["conferido"]
    obj = SolicitacaoDietaEspecial.objects.first()
    assert obj.conferido


def test_url_endpoint_escola_solicita_inativacao_dieta(
    client_autenticado_vinculo_escola_dieta, solicitacao_dieta_especial
):
    # TODO: Corrigir endpoint e testes

    obj = SolicitacaoDietaEspecial.objects.first()
    obj.status = SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO
    obj.save()

    data = {
        "justificativa": "<p>alta pelo médico</p>",
        "anexos": [
            {
                "nome": "Teste",
                "base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAaQAAAGkCAIAAADxLsZiAAAFyklEQVR4nOzWUZHbYBA"
                + "GwThlHsYmEEIhEMImBgshJHL6rZtuAvs9Te17Zv4A/HZ/Vw8AuIPYAQliBySIHZAgdkCC2AEJYgckiB2QIHZAgtgB"
                + "CWIHJIgdkCB2QILYAQliBySIHZAgdkCC2AEJYgckiB2QIHZAgtgBCWIHJIgdkCB2QILYAQliBySIHZAgdkCC2AEJY"
                + "gckiB2QIHZAgtgBCe/VAx7svI7VEyjaPvvqCY/kswMSxA5IEDsgQeyABLEDEsQOSBA7IEHsgASxAxLEDkgQOyBB7I"
                + "AEsQMSxA5IEDsgQeyABLEDEsQOSBA7IEHsgASxAxLEDkgQOyBB7IAEsQMSxA5IEDsgQeyABLEDEsQOSBA7IEHsgAS"
                + "xAxLEDkgQOyBB7IAEsQMSxA5IEDsgQeyABLEDEsQOSBA7IEHsgASxAxLEDkgQOyBB7IAEsQMSxA5IEDsgQeyABLED"
                + "EsQOSBA7IEHsgASxAxLEDkgQOyBB7IAEsQMSxA5IEDsgQeyABLEDEsQOSBA7IEHsgASxAxJeM3PPpfM67jkEPMv22"
                + "W+44rMDEsQOSBA7IEHsgASxAxLEDkgQOyBB7IAEsQMSxA5IEDsgQeyABLEDEsQOSBA7IEHsgASxAxLEDkgQOyBB7I"
                + "AEsQMSxA5IEDsgQeyABLEDEsQOSBA7IEHsgASxAxLEDkgQOyBB7IAEsQMSxA5IEDsgQeyABLEDEsQOSBA7IEHsgAS"
                + "xAxLEDkgQOyBB7IAEsQMSxA5IEDsgQeyABLEDEsQOSBA7IEHsgASxAxLEDkgQOyBB7IAEsQMSxA5IEDsgQeyABLED"
                + "EsQOSBA7IEHsgASxAxLEDkgQOyBB7IAEsQMSxA5IeM3M6g1PdV7H6gkUbZ999YRH8tkBCWIHJIgdkCB2QILYAQliB"
                + "ySIHZAgdkCC2AEJYgckiB2QIHZAgtgBCWIHJIgdkCB2QILYAQliBySIHZAgdkCC2AEJYgckiB2QIHZAgtgBCWIHJI"
                + "gdkCB2QILYAQliBySIHZAgdkCC2AEJYgckiB2QIHZAgtgBCWIHJIgdkCB2QILYAQliBySIHZAgdkCC2AEJYgckiB2"
                + "QIHZAgtgBCWIHJIgdkCB2QILYAQliBySIHZAgdkCC2AEJYgckiB2QIHZAgtgBCWIHJIgdkCB2QILYAQliBySIHZAg"
                + "dkCC2AEJr5lZvQHgx/nsgASxAxLEDkgQOyBB7IAEsQMSxA5IEDsgQeyABLEDEsQOSBA7IEHsgASxAxLEDkgQOyBB7"
                + "IAEsQMSxA5IEDsgQeyABLEDEsQOSBA7IEHsgASxAxLEDkgQOyBB7IAEsQMSxA5IEDsgQeyABLEDEsQOSBA7IEHsgA"
                + "SxAxLEDkgQOyBB7IAEsQMSxA5IEDsgQeyABLEDEsQOSBA7IEHsgASxAxLEDkgQOyBB7IAEsQMSxA5IEDsgQeyABLE"
                + "DEsQOSBA7IEHsgASxAxLEDkgQOyBB7IAEsQMSxA5IEDsg4b16AF/kvI7VE/6/7bOvnsBX8NkBCWIHJIgdkCB2QILY"
                + "AQliBySIHZAgdkCC2AEJYgckiB2QIHZAgtgBCWIHJIgdkCB2QILYAQliBySIHZAgdkCC2AEJYgckiB2QIHZAgtgBC"
                + "WIHJIgdkCB2QILYAQliBySIHZAgdkCC2AEJYgckiB2QIHZAgtgBCWIHJIgdkCB2QILYAQliBySIHZAgdkCC2AEJYg"
                + "ckiB2QIHZAgtgBCWIHJIgdkCB2QILYAQliBySIHZAgdkCC2AEJYgckiB2QIHZAgtgBCWIHJIgdkCB2QILYAQliByS"
                + "IHZAgdkCC2AEJYgckvGZm9QaAH+ezAxLEDkgQOyBB7IAEsQMSxA5IEDsgQeyABLEDEsQOSBA7IEHsgASxAxLEDkgQ"
                + "OyBB7IAEsQMSxA5IEDsgQeyABLEDEsQOSBA7IEHsgASxAxLEDkgQOyBB7IAEsQMSxA5IEDsgQeyABLEDEv4FAAD//"
                + "xmNHVuA/EwlAAAAAElFTkSuQmCC",
            }
        ],
    }
    client, user = client_autenticado_vinculo_escola_dieta
    response = client.post(
        f"/solicitacoes-dieta-especial/{obj.uuid}/escola-solicita-inativacao/",
        content_type="application/json",
        data=data,
    )

    assert response.status_code == status.HTTP_200_OK
    obj.refresh_from_db()
    assert obj.status == DietaEspecialWorkflow.CODAE_AUTORIZADO
    response = client.post(
        f"/solicitacoes-dieta-especial/{obj.uuid}/escola-solicita-inativacao/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Já existe uma solicitação de cancelamento para essa dieta"
    }


def test_url_endpoint_codae_autoriza_inativacao_dieta(
    client_autenticado_vinculo_codae_dieta, solicitacao_dieta_especial
):
    obj = SolicitacaoDietaEspecial.objects.first()
    obj.status = SolicitacaoDietaEspecial.workflow_class.ESCOLA_SOLICITOU_INATIVACAO
    obj.save()
    response = client_autenticado_vinculo_codae_dieta.patch(
        f"/solicitacoes-dieta-especial/{obj.uuid}/codae-autoriza-inativacao/",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    obj.refresh_from_db()
    assert obj.status == DietaEspecialWorkflow.CODAE_AUTORIZOU_INATIVACAO
    response = client_autenticado_vinculo_codae_dieta.patch(
        f"/solicitacoes-dieta-especial/{obj.uuid}/codae-autoriza-inativacao/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'codae_autoriza_inativacao' isn't available from state "
        + "'CODAE_AUTORIZOU_INATIVACAO'."
    }


def test_url_endpoint_terceirizada_toma_ciencia_inativacao_dieta(
    client_autenticado_vinculo_terceirizada_dieta, solicitacao_dieta_especial
):
    obj = SolicitacaoDietaEspecial.objects.first()
    obj.status = SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZOU_INATIVACAO
    obj.save()
    response = client_autenticado_vinculo_terceirizada_dieta.patch(
        f"/solicitacoes-dieta-especial/{obj.uuid}/terceirizada-toma-ciencia-inativacao/",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    obj.refresh_from_db()
    assert obj.status == DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO
    response = client_autenticado_vinculo_terceirizada_dieta.patch(
        f"/solicitacoes-dieta-especial/{obj.uuid}/terceirizada-toma-ciencia-inativacao/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'terceirizada_toma_ciencia_inativacao' isn't available "
        + "from state 'TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO'."
    }


def test_gerar_protocolo_dieta_especial_protocolo(
    client_autenticado, solicitacao_dieta_especial_autorizada
):
    response = client_autenticado.get(
        f"/solicitacoes-dieta-especial/{solicitacao_dieta_especial_autorizada.uuid}/{constants.PROTOCOLO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == f'filename="dieta_especial_{solicitacao_dieta_especial_autorizada.id_externo}.pdf"'
    )
    assert "PDF-1." in str(response.content)
    assert isinstance(response.content, bytes)


def test_gerar_protocolo_dieta_especial_relatorio(
    client_autenticado, solicitacao_dieta_especial_autorizada
):
    response = client_autenticado.get(
        f"/solicitacoes-dieta-especial/{solicitacao_dieta_especial_autorizada.uuid}/{constants.RELATORIO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == f'filename="dieta_especial_{solicitacao_dieta_especial_autorizada.id_externo}.pdf"'
    )
    assert "PDF-1." in str(response.content)
    assert isinstance(response.content, bytes)


def test_relatorio_dieta_especial_terceirizada_lista_autorizadas(
    client_autenticado, solicitacao_dieta_especial_autorizada
):
    assert Terceirizada.objects.count() == 1
    response = client_autenticado.get(
        "/solicitacoes-dieta-especial/relatorio-dieta-especial-terceirizada/"
        "?status_selecionado=AUTORIZADAS&"
        "terceirizada=a8fefdd3-b5ff-47e0-8338-ce5d7c6d8a52"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


def test_relatorio_dieta_especial_terceirizada_lista_canceladas(
    client_autenticado,
    solicitacao_dieta_especial_codae_autorizou_inativacao,
    solicitacao_dieta_especial_cancelada_automaticamente,
):
    response = client_autenticado.get(
        "/solicitacoes-dieta-especial/relatorio-dieta-especial-terceirizada/?status_selecionado=CANCELADAS"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 2


def test_imprime_relatorio_dieta_especial(
    client_autenticado, solicitacao_dieta_especial_autorizada
):
    data = {
        "escola": [solicitacao_dieta_especial_autorizada.escola.uuid],
        "diagnostico": [AlergiaIntolerancia.objects.get().id],
    }
    response = client_autenticado.post(
        "/solicitacoes-dieta-especial/imprime-relatorio-dieta-especial/", data=data
    )
    assert response.status_code == status.HTTP_200_OK


def test_imprime_relatorio_dieta_especial_validation_error(
    client_autenticado, solicitacao_dieta_especial_autorizada
):
    data = {"escola": ["a"]}
    response = client_autenticado.post(
        "/solicitacoes-dieta-especial/imprime-relatorio-dieta-especial/", data=data
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_cadastro_protocolo_dieta_especial(client_autenticado_protocolo_dieta):
    alimentao_id = (
        Alimento.objects.exclude(uuid="e67b6e67-7501-4d6e-8fac-ce219df3ed2b").get().id
    )
    data = {
        "nome_protocolo": "ALERGIA - ABACATE",
        "orientacoes_gerais": "<ul><li>Substituição do <strong>Abacate,&nbsp;</strong>bem como "
        "preparações contendo este.</li><li>É importante observar sempre os rótulos dos "
        "alimentos,&nbsp;tendo em vista que a composição do produto pode ser alterada pela "
        "empresa fabricante a qualquer tempo.</li></ul>",
        "status": "NAO_LIBERADO",
        "editais": [
            "b7b6a0a7-b230-4783-94b6-8d3d22041ab3",
            "60f5a64e-8652-422d-a6e9-0a36717829c9",
        ],
        "substituicoes": [
            {
                "alimento": alimentao_id,
                "tipo": "I",
                "substitutos": ["e67b6e67-7501-4d6e-8fac-ce219df3ed2b"],
            }
        ],
    }
    response = client_autenticado_protocolo_dieta.post(
        "/protocolo-padrao-dieta-especial/", content_type="application/json", data=data
    )
    assert response.status_code == status.HTTP_201_CREATED
    uuid = response.json()["uuid"]

    response = client_autenticado_protocolo_dieta.get(
        "/protocolo-padrao-dieta-especial/?editais[]=b7b6a0a7-b230-4783-94b6-8d3d22041ab3"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1

    response = client_autenticado_protocolo_dieta.get(
        "/protocolo-padrao-dieta-especial/?editais[]=4f7287e5-da63-4b23-8bbc-48cc6722c91e"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 0

    response = client_autenticado_protocolo_dieta.post(
        "/protocolo-padrao-dieta-especial/", content_type="application/json", data=data
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Já existe um protocolo padrão com esse nome" in response.json()[0]
    data["nome_protocolo"] = "ALERGIA - BANANA"
    client_autenticado_protocolo_dieta.post(
        "/protocolo-padrao-dieta-especial/", content_type="application/json", data=data
    )
    response_400 = client_autenticado_protocolo_dieta.put(
        f"/protocolo-padrao-dieta-especial/{uuid}/",
        content_type="application/json",
        data=data,
    )
    assert response_400.status_code == status.HTTP_400_BAD_REQUEST
    assert "Já existe um protocolo padrão com esse nome" in response_400.json()[0]
    data["nome_protocolo"] = "ALERGIA - ABACATE"
    data["editais"] = []
    response = client_autenticado_protocolo_dieta.put(
        f"/protocolo-padrao-dieta-especial/{uuid}/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK


def test_cadastro_protocolo_dieta_especial_lista_status(
    client_autenticado_protocolo_dieta,
):
    response = client_autenticado_protocolo_dieta.get(
        "/protocolo-padrao-dieta-especial/lista-status/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == len(
        ProtocoloPadraoDietaEspecial.STATUS_NOMES.keys()
    )


def test_cadastro_protocolo_dieta_especial_nomes_protocolos_liberados(
    client_autenticado_protocolo_dieta, massa_dados_protocolo_padrao_test
):
    alimentao_id = (
        Alimento.objects.exclude(uuid="e67b6e67-7501-4d6e-8fac-ce219df3ed2b").get().id
    )
    data = {
        "nome_protocolo": "ALERGIA - ABACATE",
        "orientacoes_gerais": "<ul><li>Substituição do <strong>Abacate,&nbsp;</strong>bem como "
        "preparações contendo este.</li><li>É importante observar sempre os rótulos dos "
        "alimentos,&nbsp;tendo em vista que a composição do produto pode ser alterada pela "
        "empresa fabricante a qualquer tempo.</li></ul>",
        "status": "LIBERADO",
        "editais": [
            massa_dados_protocolo_padrao_test["editais"][0],
            massa_dados_protocolo_padrao_test["editais"][1],
        ],
        "substituicoes": [
            {
                "alimento": alimentao_id,
                "tipo": "I",
                "substitutos": ["e67b6e67-7501-4d6e-8fac-ce219df3ed2b"],
            }
        ],
    }
    client_autenticado_protocolo_dieta.post(
        "/protocolo-padrao-dieta-especial/", content_type="application/json", data=data
    )
    response = client_autenticado_protocolo_dieta.get(
        "/protocolo-padrao-dieta-especial/nomes/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1

    dieta_especial_uuid = massa_dados_protocolo_padrao_test["dieta_uuid"]
    response = client_autenticado_protocolo_dieta.get(
        f"/protocolo-padrao-dieta-especial/lista-protocolos-liberados/?dieta_especial_uuid={dieta_especial_uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


def test_cadastro_protocolo_dieta_especial_nomes_protocolos_liberados_parceiras(
    client_autenticado_vinculo_codae_dieta,
    solicitacao_dieta_especial_parceira,
    protocolo_padrao_edital_parceira,
):
    # dado uma solicitacao de uma escola parceira
    # e um protocolo padrao do edital PARCEIRA

    # quando
    response = client_autenticado_vinculo_codae_dieta.get(
        f"/protocolo-padrao-dieta-especial/lista-protocolos-liberados/?dieta_especial_uuid={solicitacao_dieta_especial_parceira.uuid}"
    )

    # entao
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


def test_filtros_relatorio_dieta_especial_validation_error(
    client_autenticado_vinculo_terceirizada_dieta,
):
    response = client_autenticado_vinculo_terceirizada_dieta.get(
        "/solicitacoes-dieta-especial/filtros-relatorio-dieta-especial/"
        "?terceirizada=a8fefdd3-b5ff-47e0-8338-ce5d7c6d8a52"
        "&status=AUTORIZADAS"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "status": [
            "Faça uma escolha válida. AUTORIZADAS não é uma das escolhas disponíveis."
        ]
    }


def test_filtros_relatorio_dieta_especial_success(
    client_autenticado_vinculo_terceirizada_dieta,
):
    response = client_autenticado_vinculo_terceirizada_dieta.get(
        "/solicitacoes-dieta-especial/filtros-relatorio-dieta-especial/"
        "?terceirizada=a8fefdd3-b5ff-47e0-8338-ce5d7c6d8a52"
        "&status_selecionado=AUTORIZADAS"
    )
    assert response.status_code == status.HTTP_200_OK
    response.json().pop("classificacoes")
    assert response.json() == {
        "alergias_intolerancias": [],
        "lotes": [
            {
                "nome": "LOTE 07 - DIRETORIA REGIONAL IPIRANGA",
                "uuid": "429446c2-5b17-4ada-96ae-cce369dd4ae1",
            }
        ],
        "protocolos_padrao": [
            {"nome": "ALERGIA - OVO", "uuid": "5d7f80b8-7b62-441b-89da-4d5dd5c1e7e8"}
        ],
        "tipos_gestao": [
            {"nome": "TERC TOTAL", "uuid": "8bd3931b-8636-44ba-9d8e-81b29067eed1"}
        ],
        "tipos_unidades": [],
    }


def test_relatorio_historico_dieta_especial(
    client_autenticado_vinculo_terceirizada_dieta,
    log_dietas_autorizadas,
    log_dietas_autorizadas_cei,
):
    response = client_autenticado_vinculo_terceirizada_dieta.get(
        "/solicitacoes-dieta-especial/relatorio-historico-dieta-especial/?data=20/03/2024"
    )
    assert response.status_code == status.HTTP_200_OK
    historico = response.json()
    assert historico["count"] == 4
    assert historico["page_size"] == 10
    assert historico["previous"] is None
    assert historico["next"] is None
    assert historico["total_dietas"] == 83
    assert historico["data"] == "20/03/2024"

    assert len(historico["results"]) == 4
    assert historico["results"] == [
        {
            "lote": "",
            "unidade_educacional": "CEI DIRET JOAO MENDES",
            "tipo_unidade": "CEI DIRET",
            "classificacao": "Tipo B",
            "total": 32,
            "data": "20/03/2024",
            "periodos": [
                {
                    "periodo": "INTEGRAL",
                    "faixa_etaria": [
                        {"faixa": "0 meses a 05 meses", "autorizadas": 10}
                    ],
                },
                {
                    "periodo": "MANHA",
                    "faixa_etaria": [{"faixa": "07 a 11 meses", "autorizadas": 11}],
                },
            ],
        },
        {
            "lote": "",
            "unidade_educacional": "CEMEI",
            "tipo_unidade": "CEMEI",
            "classificacao": "Tipo A",
            "total": 25,
            "data": "20/03/2024",
            "periodos": {
                "por_idade": [
                    {
                        "periodo": "INTEGRAL",
                        "faixa_etaria": [
                            {"faixa": "0 meses a 05 meses", "autorizadas": 12}
                        ],
                    },
                    {
                        "periodo": "MANHA",
                        "faixa_etaria": [{"faixa": "07 a 11 meses", "autorizadas": 13}],
                    },
                ]
            },
        },
        {
            "lote": "",
            "unidade_educacional": "CEMEI",
            "tipo_unidade": "CEMEI",
            "classificacao": "Tipo B",
            "total": 15,
            "data": "20/03/2024",
            "periodos": {
                "turma_infantil": [
                    {"periodo": "INTEGRAL", "autorizadas": 7},
                    {"periodo": "MANHA", "autorizadas": 8},
                ]
            },
        },
        {
            "lote": "",
            "unidade_educacional": "EMEBS",
            "tipo_unidade": "EMEBS",
            "classificacao": "Tipo A",
            "total": 11,
            "data": "20/03/2024",
            "periodos": {
                "infantil": [{"periodo": "INTEGRAL", "autorizadas": 5}],
                "fundamental": [{"periodo": "MANHA", "autorizadas": 6}],
            },
        },
    ]


def test_relatorio_historico_dieta_especial_retona_data_obrigatoria(
    client_autenticado_vinculo_terceirizada_dieta,
):
    response = client_autenticado_vinculo_terceirizada_dieta.get(
        "/solicitacoes-dieta-especial/relatorio-historico-dieta-especial/"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "`data` é um parâmetro obrigatório."}


def test_relatorio_historico_dieta_especial_retona_data_padrao_incorreto(
    client_autenticado_vinculo_terceirizada_dieta,
):
    response = client_autenticado_vinculo_terceirizada_dieta.get(
        "/solicitacoes-dieta-especial/relatorio-historico-dieta-especial/?data=2025-02-06"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "A data 2025-02-06 não corresponde ao formato esperado 'dd/mm/YYYY'."
    }


def test_relatorio_historico_dieta_especial_cliente_nao_autorizado(
    client_autenticado_dilog,
):
    response = client_autenticado_dilog.get(
        "/solicitacoes-dieta-especial/relatorio-historico-dieta-especial/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você não tem permissão para executar essa ação."
    }


def test_relatorio_recreio_nas_ferias(
    client_autenticado_vinculo_terceirizada_dieta, relatorio_recreio_nas_ferias
):
    response = client_autenticado_vinculo_terceirizada_dieta.get(
        "/solicitacoes-dieta-especial/relatorio-recreio-nas-ferias/"
    )
    assert response.status_code == status.HTTP_200_OK
    json_resposta = response.json()
    assert json_resposta["count"] == 4
    resultado = json_resposta["results"]

    assert resultado[0]["aluno"]["nome"] == "Maria"
    assert resultado[0]["escola"]["nome"] == "Escola Guaianases"
    assert resultado[0]["escola_destino"]["nome"] == "CEMEI"
    assert (
        resultado[0]["alergias_intolerancias"][0]["descricao"]
        == "Alergia a derivados do trigo"
    )
    assert resultado[0]["classificacao"]["nome"] == "Tipo B"

    assert resultado[1]["aluno"]["nome"] == "Carla"
    assert resultado[1]["escola"]["nome"] == "PARCEIRA"
    assert resultado[1]["escola_destino"]["nome"] == "EMEBS"
    assert (
        resultado[1]["alergias_intolerancias"][0]["descricao"]
        == "Alergia a derivados do trigo"
    )
    assert resultado[1]["classificacao"]["nome"] == "Tipo B"

    assert resultado[2]["aluno"]["nome"] == "Antonio"
    assert resultado[2]["escola"]["nome"] == "EMEF JOAO MENDES"
    assert resultado[2]["escola_destino"]["nome"] == "Escola Guaianases"
    assert (
        resultado[2]["alergias_intolerancias"][0]["descricao"] == "Alergia a chocolate"
    )
    assert resultado[2]["classificacao"]["nome"] == "Tipo A"

    assert resultado[3]["aluno"]["nome"] == "Carlos"
    assert resultado[3]["escola"]["nome"] == "CEMEI"
    assert resultado[3]["escola_destino"]["nome"] == "PARCEIRA"
    assert (
        resultado[3]["alergias_intolerancias"][0]["descricao"] == "Alergia a chocolate"
    )
    assert resultado[3]["classificacao"]["nome"] == "Tipo A"


def test_relatorio_recreio_nas_ferias_cliente_nao_autorizado(client_autenticado_dilog):
    response = client_autenticado_dilog.get(
        "/solicitacoes-dieta-especial/relatorio-recreio-nas-ferias/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você não tem permissão para executar essa ação."
    }


def test_codae_atualiza_protocolo(
    client_autenticado_vinculo_codae_dieta,
    solicitacao_historico_atualizacao_protocolo,
    substituicao_alimento_dieta,
    mock_request_codae_atualiza_protocolo,
):
    response = client_autenticado_vinculo_codae_dieta.patch(
        f"/solicitacoes-dieta-especial/{str(solicitacao_historico_atualizacao_protocolo.uuid)}/codae-atualiza-protocolo/",
        content_type="application/json",
        data=mock_request_codae_atualiza_protocolo,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"detail": "Edição realizada com sucesso!"}

    response = client_autenticado_vinculo_codae_dieta.get(
        f"/solicitacoes-dieta-especial/{str(solicitacao_historico_atualizacao_protocolo.uuid)}/",
        content_type="application/json",
        data=mock_request_codae_atualiza_protocolo,
    )

    assert response.status_code == status.HTTP_200_OK
    assert "logs" in response.json()
    log = response.json()["logs"][-1]
    assert "justificativa" in log
    justificativa = log["justificativa"]
    assert justificativa is not None and justificativa != ""

    assert "Relação por Diagnóstico" in justificativa
    assert "Alergia a chocolate" in justificativa
    assert "Alergia a derivados do trigo" in justificativa

    assert "Classificação da Dieta" in justificativa
    assert "Tipo A" in justificativa
    assert "Tipo B" in justificativa

    assert "Nome do Protocolo Padrão" in justificativa
    assert "ALERGIA A AVEIA" in justificativa
    assert "ALERGIA A ABACAXI" in justificativa

    assert "Orientações Gerais" in justificativa
    assert "A criança tem alergia ao cacau" in justificativa
    assert "A criança tem alergia ao cacau 70%." in justificativa

    assert "Informações adicionais" in justificativa
    assert "Nenhuma informção a ser adicionada." in justificativa
    assert (
        "Caso a criança insira chocolate, levar imediatamente ao hospital."
        in justificativa
    )

    assert "Data de término" in justificativa
    assert "Sem data término" in justificativa
    assert "Com data de término 25/10/2026" in justificativa

    assert "Substituições de Alimentos" in justificativa
    assert justificativa.count("SUBSTITUIR") == 4
    assert justificativa.count("ISENTO") == 0

    assert "ITEM EXCLUÍDO" in justificativa
    assert "Achocolatado" in justificativa
    assert "<li> Suco de Laranja</li>" in justificativa
    assert "<li> Suco de Morango</li>" in justificativa
    assert "<li> Suco de Uva</li>" in justificativa

    assert "ITEM INCLUIDO" in justificativa
    assert "Biscoito de Chocolate" in justificativa
    assert "<li> Biscoito de Leite com Coco</li>" in justificativa
    assert "<li> Biscoito de Maizena</li>" in justificativa

    assert "ITEM ALTERADO DE" in justificativa
    assert "ITEM ALTERADO PARA" in justificativa
    assert "Bolo de Chocolate" in justificativa
    assert justificativa.count("<li> Bolo de Fubá</li>") == 2
    assert justificativa.count("<li> Bolo de Laranja</li>") == 2
    assert justificativa.count("<li> Bolo de Limão</li>") == 1


def test_codae_atualiza_protocolo_exception(
    client_autenticado_vinculo_codae_dieta,
    solicitacao_historico_atualizacao_protocolo,
    substituicao_alimento_dieta,
    mock_request_codae_atualiza_protocolo,
):
    mock_request_codae_atualiza_protocolo["alergias_intolerancias"] = {"str": 25}
    response = client_autenticado_vinculo_codae_dieta.patch(
        f"/solicitacoes-dieta-especial/{str(solicitacao_historico_atualizacao_protocolo.uuid)}/codae-atualiza-protocolo/",
        content_type="application/json",
        data=mock_request_codae_atualiza_protocolo,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Ocorreu um erro ao gerar as informações do histórico: invalid literal for int() with base 10: 'str'"
    }

    mock_request_codae_atualiza_protocolo["alergias_intolerancias"] = []
    response = client_autenticado_vinculo_codae_dieta.patch(
        f"/solicitacoes-dieta-especial/{str(solicitacao_historico_atualizacao_protocolo.uuid)}/codae-atualiza-protocolo/",
        content_type="application/json",
        data=mock_request_codae_atualiza_protocolo,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Dados inválidos [ErrorDetail(string='atributo alergias_intolerancias não pode ser vazio', code='invalid')]"
    }


def test_relatorio_recreio_exportar_xlsx(
    client_autenticado_vinculo_codae_gestao_alimentacao_dieta,
):
    client, user = client_autenticado_vinculo_codae_gestao_alimentacao_dieta
    response = client.get(
        "/solicitacoes-dieta-especial/relatorio-recreio-nas-ferias/exportar-excel/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert (
        response.json()["detail"]
        == "Solicitação de geração de arquivo recebida com sucesso."
    )
