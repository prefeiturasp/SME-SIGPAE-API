import uuid

import pytest
from pdfminer.high_level import extract_text
from rest_framework import status

from config.celery import app
from sme_sigpae_api.dados_comuns.models import CentralDeDownload, LogSolicitacoesUsuario
from sme_sigpae_api.imr.api.viewsets import FormularioSupervisaoModelViewSet
from sme_sigpae_api.imr.models import (
    FormularioSupervisao,
    PerfilDiretorSupervisao,
    TipoOcorrencia,
)

pytestmark = pytest.mark.django_db


def test_get_formularios_supervisao_com_nutrimanifestacao(
    client_autenticado_vinculo_nutrimanifestacao, formulario_supervisao_factory
):
    client, usuario = client_autenticado_vinculo_nutrimanifestacao

    formulario_supervisao_factory.create()
    formulario_supervisao_factory.create(formulario_base__usuario=usuario)

    response = client.get(f"/imr/formulario-supervisao/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 2


def test_get_categorias_nao_permitidas():
    view_instance = FormularioSupervisaoModelViewSet()

    # Teste para CEMEI
    categorias = view_instance._get_categorias_nao_permitidas("CEMEI")
    assert "LACTÁRIO" not in categorias
    assert "RESÍDUO DE ÓLEO UTILIZADO NA FRITURA" not in categorias

    # Teste para outro tipo de escola
    categorias = view_instance._get_categorias_nao_permitidas("EMEF")
    assert "LACTÁRIO" in categorias
    assert "RESÍDUO DE ÓLEO UTILIZADO NA FRITURA" not in categorias

    # Teste para CEI
    categorias = view_instance._get_categorias_nao_permitidas("CEI DIRET")
    assert "LACTÁRIO" not in categorias
    assert "RESÍDUO DE ÓLEO UTILIZADO NA FRITURA" in categorias


def test_tipos_ocorrencias(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    edital_factory,
    categoria_ocorrencia_factory,
    tipo_ocorrencia_factory,
    escola_factory,
    tipo_unidade_escolar_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao
    edital = edital_factory.create()

    categoria = categoria_ocorrencia_factory.create(
        perfis=[PerfilDiretorSupervisao.SUPERVISAO], posicao=1
    )
    categoria_lactario = categoria_ocorrencia_factory.create(
        nome="LACTÁRIO", perfis=[PerfilDiretorSupervisao.SUPERVISAO], posicao=2
    )
    tipo_unidade_emef = tipo_unidade_escolar_factory.create(iniciais="EMEF")
    escola_emef = escola_factory.create(tipo_unidade=tipo_unidade_emef)
    tipo_unidade_cemei = tipo_unidade_escolar_factory.create(iniciais="CEMEI")
    escola_cemei = escola_factory.create(tipo_unidade=tipo_unidade_cemei)

    tipo_ocorrencia_factory.create(
        edital=edital,
        descricao="Ocorrencia 1",
        perfis=[PerfilDiretorSupervisao.SUPERVISAO],
        categoria=categoria,
        posicao=1,
    )
    tipo_ocorrencia_factory.create(
        edital=edital,
        descricao="Ocorrencia 2",
        perfis=[PerfilDiretorSupervisao.SUPERVISAO],
        categoria=categoria,
        posicao=2,
    )
    tipo_ocorrencia_factory.create(
        edital=edital,
        descricao="Ocorrencia 3",
        perfis=[PerfilDiretorSupervisao.SUPERVISAO],
        categoria=categoria_lactario,
        posicao=3,
    )

    response = client.get(
        f"/imr/formulario-supervisao/tipos-ocorrencias/?edital_uuid={edital.uuid}&escola_uuid={escola_emef.uuid}"
    )

    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()

    assert len(response_data) == 2
    assert response_data[0]["descricao"] == "Ocorrencia 1"
    assert response_data[1]["descricao"] == "Ocorrencia 2"

    response_cemei = client.get(
        f"/imr/formulario-supervisao/tipos-ocorrencias/?edital_uuid={edital.uuid}&escola_uuid={escola_cemei.uuid}"
    )

    assert response_cemei.status_code == status.HTTP_200_OK

    response_cemei_data = response_cemei.json()

    assert len(response_cemei_data) == 3
    assert response_cemei_data[0]["descricao"] == "Ocorrencia 1"
    assert response_cemei_data[1]["descricao"] == "Ocorrencia 2"
    assert response_cemei_data[2]["descricao"] == "Ocorrencia 3"

    client.logout()


def test_tipos_ocorrencias_edital_does_not_exist(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    uuid_falso = uuid.uuid4()
    response = client.get(
        f"/imr/formulario-supervisao/tipos-ocorrencias/?edital_uuid={uuid_falso}"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Edital do tipo IMR com o UUID informado não foi encontrado."
    }

    client.logout()


def test_tipos_ocorrencias_escola_does_not_exist(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    edital_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    edital = edital_factory.create()
    uuid_falso = uuid.uuid4()
    response = client.get(
        f"/imr/formulario-supervisao/tipos-ocorrencias/?edital_uuid={edital.uuid}&escola_uuid={uuid_falso}"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Escola com o UUID informado não foi encontrada."
    }

    client.logout()


def test_tipos_ocorrencias_edital_ou_escola_UUID_invalido(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    escola_factory,
    edital_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao
    edital = edital_factory.create()
    escola = escola_factory.create()

    response = client.get(
        f"/imr/formulario-supervisao/tipos-ocorrencias/?edital_uuid=&escola_uuid={escola.uuid}"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.get(
        f"/imr/formulario-supervisao/tipos-ocorrencias/?edital_uuid={edital.uuid}&escola_uuid="
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    client.logout()


def test_url_lista_formularios_supervisao(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao
    response = client.get("/imr/formulario-supervisao/")
    assert response.status_code == status.HTTP_200_OK


def test_url_dashboard_supervisao(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    formulario_supervisao_factory.create()
    formulario_supervisao_factory.create(formulario_base__usuario=usuario)
    formulario_supervisao_factory.create(formulario_base__usuario=usuario)

    formulario_supervisao_factory.create(
        status=FormularioSupervisao.workflow_class.NUTRIMANIFESTACAO_A_VALIDAR
    )
    formulario_supervisao_factory.create(
        formulario_base__usuario=usuario,
        status=FormularioSupervisao.workflow_class.NUTRIMANIFESTACAO_A_VALIDAR,
    )
    formulario_supervisao_factory.create(
        formulario_base__usuario=usuario,
        status=FormularioSupervisao.workflow_class.NUTRIMANIFESTACAO_A_VALIDAR,
    )

    response = client.get("/imr/formulario-supervisao/dashboard/")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]

    em_preenchimento = next(
        result
        for result in results
        if result["status"] == FormularioSupervisao.workflow_class.EM_PREENCHIMENTO
    )
    assert em_preenchimento["total"] == 2

    nutrimanifestacao_a_validar = next(
        result
        for result in results
        if result["status"]
        == FormularioSupervisao.workflow_class.NUTRIMANIFESTACAO_A_VALIDAR
    )
    assert nutrimanifestacao_a_validar["total"] == 2

    total = next(
        result for result in results if result["status"] == "TODOS_OS_RELATORIOS"
    )
    assert total["total"] == 4


def test_get_respostas(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    edital_factory,
    escola_factory,
    lote_factory,
    contrato_factory,
    log_solicitacoes_usuario_factory,
    categoria_ocorrencia_factory,
    formulario_supervisao_factory,
    tipo_resposta_modelo_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
    resposta_campo_texto_simples_factory,
    resposta_campo_numerico_factory,
    ocorrencia_nao_se_aplica_factory,
):
    app.conf.update(CELERY_ALWAYS_EAGER=True)

    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    edital = edital_factory.create(numero="78/SME/2016")
    lote = lote_factory.create()
    escola_ = escola_factory.create(lote=lote)
    contrato = contrato_factory.create(
        edital=edital,
    )
    contrato.lotes.add(lote)
    contrato.save()

    formulario_supervisao = formulario_supervisao_factory.create(
        formulario_base__usuario=usuario,
        formulario_base__data="2024-06-26",
        escola=escola_,
        status=FormularioSupervisao.workflow_class.NUTRIMANIFESTACAO_A_VALIDAR,
    )
    log_solicitacoes_usuario_factory.create(
        uuid_original=formulario_supervisao.uuid,
        status_evento=LogSolicitacoesUsuario.RELATORIO_ENVIADO_PARA_CODAE,
        usuario=usuario,
    )

    tipo_resposta_campo_simples = tipo_resposta_modelo_factory.create(
        nome="RespostaCampoTextoSimples"
    )
    tipo_pergunta_parametrizacao_ocorrencia_texto_simples = (
        tipo_pergunta_parametrizacao_ocorrencia_factory(
            nome="Campo de Texto Simples", tipo_resposta=tipo_resposta_campo_simples
        )
    )

    tipo_resposta_campo_numerico = tipo_resposta_modelo_factory.create(
        nome="RespostaCampoNumerico"
    )
    tipo_pergunta_parametrizacao_ocorrencia_campo_numerico = (
        tipo_pergunta_parametrizacao_ocorrencia_factory.create(
            nome="Campo Numérico", tipo_resposta=tipo_resposta_campo_numerico
        )
    )

    categoria = categoria_ocorrencia_factory.create(
        posicao=1,
        nome="FUNCIONÁRIOS",
        perfis=[TipoOcorrencia.SUPERVISAO],
    )
    categoria_2 = categoria_ocorrencia_factory.create(
        posicao=2,
        nome="RECEBIMENTO DE ALIMENTOS",
        perfis=[TipoOcorrencia.SUPERVISAO],
    )

    tipo_ocorrencia_1 = tipo_ocorrencia_factory.create(
        posicao=1,
        titulo="UNIFORME DOS MANIPULADORES",
        descricao="Funcionários utilizavam uniforme completo? Se NÃO, detalhar qual item do uniforme faltou, o que "
        "estava utilizando em substituição aos itens previstos e nome completo do(s) funcionário(s).",
        penalidade__edital=edital,
        penalidade__numero_clausula="10.42",
        perfis=[TipoOcorrencia.SUPERVISAO],
        categoria=categoria,
        edital=edital,
    )
    tipo_ocorrencia_2 = tipo_ocorrencia_factory.create(
        posicao=1,
        titulo="CONDIÇÕES DE CONSERVAÇÃO DO UNIFORME E EPI",
        descricao="Funcionários utilizavam uniforme/EPI em boas condições de conservação "
        "(não estavam rasgados, furados)? Se NÃO, detalhar inadequação, "
        "qual item do uniforme/EPI e nome completo do(s) funcionário(s).",
        penalidade__edital=edital,
        penalidade__numero_clausula="10.43",
        perfis=[TipoOcorrencia.SUPERVISAO],
        categoria=categoria,
        edital=edital,
    )
    tipo_ocorrencia_factory.create(
        posicao=1,
        perfis=[TipoOcorrencia.SUPERVISAO],
        titulo="RECEBIMENTO DE ALIMENTOS",
        descricao="Realizou o controle quantitativo e qualitativo adequado no recebimento de alimentos "
        "(inclusive o preenchimento da respectiva planilha), de acordo com o Manual de Boas Práticas "
        "e a legislação vigente?  Se NÃO, especifique a inadequação",
        penalidade__edital=edital,
        penalidade__numero_clausula="10.44",
        categoria=categoria_2,
        edital=edital,
    )
    parametrizacao_texto_simples = parametrizacao_ocorrencia_factory.create(
        tipo_ocorrencia=tipo_ocorrencia_1,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_texto_simples,
        titulo="Qual uniforme faltou?",
    )
    parametrizacao_campo_numerico = parametrizacao_ocorrencia_factory.create(
        tipo_ocorrencia=tipo_ocorrencia_1,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_campo_numerico,
        titulo="Quantos uniformes faltaram?",
    )
    resposta_campo_texto_simples_factory.create(
        resposta="AVENTAL",
        grupo=1,
        parametrizacao=parametrizacao_texto_simples,
        formulario_base=formulario_supervisao.formulario_base,
    )
    resposta_campo_texto_simples_factory.create(
        resposta="TOUCA",
        grupo=2,
        parametrizacao=parametrizacao_texto_simples,
        formulario_base=formulario_supervisao.formulario_base,
    )
    resposta_campo_numerico_factory.create(
        resposta=10,
        grupo=1,
        parametrizacao=parametrizacao_campo_numerico,
        formulario_base=formulario_supervisao.formulario_base,
    )
    resposta_campo_numerico_factory.create(
        resposta=20,
        grupo=2,
        parametrizacao=parametrizacao_campo_numerico,
        formulario_base=formulario_supervisao.formulario_base,
    )

    parametrizacao_ocorrencia_factory.create(
        tipo_ocorrencia=tipo_ocorrencia_2,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_texto_simples,
        titulo="Qual EPI faltou?",
    )
    ocorrencia_nao_se_aplica_factory.create(
        descricao="Essa ocorrência não se aplica.",
        tipo_ocorrencia=tipo_ocorrencia_2,
        formulario_base=formulario_supervisao.formulario_base,
    )

    response = client.get(
        f"/imr/formulario-supervisao/{formulario_supervisao.uuid}/respostas/"
    )
    assert response.status_code == status.HTTP_200_OK

    respostas = response.json()
    assert len(respostas) == 4


def test_get_respostas_nao_se_aplica(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory,
    ocorrencia_nao_se_aplica_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    formulario_supervisao = formulario_supervisao_factory.create(
        formulario_base__usuario=usuario
    )

    ocorrencia_nao_se_aplica_factory.create(
        formulario_base=formulario_supervisao.formulario_base
    )
    ocorrencia_nao_se_aplica_factory.create(
        formulario_base=formulario_supervisao.formulario_base
    )
    ocorrencia_nao_se_aplica_factory.create(
        formulario_base=formulario_supervisao.formulario_base
    )

    response = client.get(
        f"/imr/formulario-supervisao/{formulario_supervisao.uuid}/respostas_nao_se_aplica/"
    )
    assert response.status_code == status.HTTP_200_OK

    results = response.json()
    assert len(results) == 3


def test_get_pdf_formulario_supervisao(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    edital_factory,
    escola_factory,
    lote_factory,
    contrato_factory,
    log_solicitacoes_usuario_factory,
    categoria_ocorrencia_factory,
    formulario_supervisao_factory,
    tipo_resposta_modelo_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
    resposta_campo_texto_simples_factory,
    resposta_campo_numerico_factory,
    ocorrencia_nao_se_aplica_factory,
):
    app.conf.update(CELERY_ALWAYS_EAGER=True)

    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    edital = edital_factory.create(numero="78/SME/2016")
    lote = lote_factory.create()
    escola_ = escola_factory.create(lote=lote)
    contrato = contrato_factory.create(
        edital=edital,
    )
    contrato.lotes.add(lote)
    contrato.save()

    formulario_supervisao = formulario_supervisao_factory.create(
        formulario_base__usuario=usuario,
        formulario_base__data="2024-06-26",
        escola=escola_,
        status=FormularioSupervisao.workflow_class.NUTRIMANIFESTACAO_A_VALIDAR,
    )
    log_solicitacoes_usuario_factory.create(
        uuid_original=formulario_supervisao.uuid,
        status_evento=LogSolicitacoesUsuario.RELATORIO_ENVIADO_PARA_CODAE,
        usuario=usuario,
    )

    tipo_resposta_campo_simples = tipo_resposta_modelo_factory.create(
        nome="RespostaCampoTextoSimples"
    )
    tipo_pergunta_parametrizacao_ocorrencia_texto_simples = (
        tipo_pergunta_parametrizacao_ocorrencia_factory(
            nome="Campo de Texto Simples", tipo_resposta=tipo_resposta_campo_simples
        )
    )

    tipo_resposta_campo_numerico = tipo_resposta_modelo_factory.create(
        nome="RespostaCampoNumerico"
    )
    tipo_pergunta_parametrizacao_ocorrencia_campo_numerico = (
        tipo_pergunta_parametrizacao_ocorrencia_factory.create(
            nome="Campo Numérico", tipo_resposta=tipo_resposta_campo_numerico
        )
    )

    categoria = categoria_ocorrencia_factory.create(
        posicao=1,
        nome="FUNCIONÁRIOS",
        perfis=[TipoOcorrencia.SUPERVISAO],
    )
    categoria_2 = categoria_ocorrencia_factory.create(
        posicao=2,
        nome="RECEBIMENTO DE ALIMENTOS",
        perfis=[TipoOcorrencia.SUPERVISAO],
    )

    tipo_ocorrencia_1 = tipo_ocorrencia_factory.create(
        posicao=1,
        titulo="UNIFORME DOS MANIPULADORES",
        descricao="Funcionários utilizavam uniforme completo? Se NÃO, detalhar qual item do uniforme faltou, o que "
        "estava utilizando em substituição aos itens previstos e nome completo do(s) funcionário(s).",
        penalidade__edital=edital,
        penalidade__numero_clausula="10.42",
        perfis=[TipoOcorrencia.SUPERVISAO],
        categoria=categoria,
        edital=edital,
    )
    tipo_ocorrencia_2 = tipo_ocorrencia_factory.create(
        posicao=1,
        titulo="CONDIÇÕES DE CONSERVAÇÃO DO UNIFORME E EPI",
        descricao="Funcionários utilizavam uniforme/EPI em boas condições de conservação "
        "(não estavam rasgados, furados)? Se NÃO, detalhar inadequação, "
        "qual item do uniforme/EPI e nome completo do(s) funcionário(s).",
        penalidade__edital=edital,
        penalidade__numero_clausula="10.43",
        perfis=[TipoOcorrencia.SUPERVISAO],
        categoria=categoria,
        edital=edital,
    )
    tipo_ocorrencia_factory.create(
        posicao=1,
        perfis=[TipoOcorrencia.SUPERVISAO],
        titulo="RECEBIMENTO DE ALIMENTOS",
        descricao="Realizou o controle quantitativo e qualitativo adequado no recebimento de alimentos "
        "(inclusive o preenchimento da respectiva planilha), de acordo com o Manual de Boas Práticas "
        "e a legislação vigente?  Se NÃO, especifique a inadequação",
        penalidade__edital=edital,
        penalidade__numero_clausula="10.44",
        categoria=categoria_2,
        edital=edital,
    )
    parametrizacao_texto_simples = parametrizacao_ocorrencia_factory.create(
        tipo_ocorrencia=tipo_ocorrencia_1,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_texto_simples,
        titulo="Qual uniforme faltou?",
    )
    parametrizacao_campo_numerico = parametrizacao_ocorrencia_factory.create(
        tipo_ocorrencia=tipo_ocorrencia_1,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_campo_numerico,
        titulo="Quantos uniformes faltaram?",
    )
    resposta_campo_texto_simples_factory.create(
        resposta="AVENTAL",
        grupo=1,
        parametrizacao=parametrizacao_texto_simples,
        formulario_base=formulario_supervisao.formulario_base,
    )
    resposta_campo_texto_simples_factory.create(
        resposta="TOUCA",
        grupo=2,
        parametrizacao=parametrizacao_texto_simples,
        formulario_base=formulario_supervisao.formulario_base,
    )
    resposta_campo_numerico_factory.create(
        resposta=10,
        grupo=1,
        parametrizacao=parametrizacao_campo_numerico,
        formulario_base=formulario_supervisao.formulario_base,
    )
    resposta_campo_numerico_factory.create(
        resposta=20,
        grupo=2,
        parametrizacao=parametrizacao_campo_numerico,
        formulario_base=formulario_supervisao.formulario_base,
    )

    parametrizacao_ocorrencia_factory.create(
        tipo_ocorrencia=tipo_ocorrencia_2,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_texto_simples,
        titulo="Qual EPI faltou?",
    )
    ocorrencia_nao_se_aplica_factory.create(
        descricao="Essa ocorrência não se aplica.",
        tipo_ocorrencia=tipo_ocorrencia_2,
        formulario_base=formulario_supervisao.formulario_base,
    )

    response = client.get(
        f"/imr/formulario-supervisao/{formulario_supervisao.uuid}/relatorio-pdf/"
    )
    assert response.status_code == status.HTTP_200_OK

    central_download = CentralDeDownload.objects.get()
    assert central_download.status == CentralDeDownload.STATUS_CONCLUIDO

    conteudo_pdf_pagina_1 = extract_text(
        central_download.arquivo.path, page_numbers=[0]
    )

    assert "Data da visita" in conteudo_pdf_pagina_1
    assert "26/06/2024" in conteudo_pdf_pagina_1
    assert "FUNCIONÁRIOS" in conteudo_pdf_pagina_1
    assert "Qual uniforme faltou?" in conteudo_pdf_pagina_1
    assert "AVENTAL" in conteudo_pdf_pagina_1
    assert "Quantos uniformes faltaram?" in conteudo_pdf_pagina_1
    assert "TOUCA" in conteudo_pdf_pagina_1
    assert "Qual EPI faltou?" not in conteudo_pdf_pagina_1
    assert "Essa ocorrência não se aplica." in conteudo_pdf_pagina_1
    assert "RECEBIMENTO DE ALIMENTOS" in conteudo_pdf_pagina_1


def test_get_pdf_formulario_supervisao_exception_error(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    edital_factory,
    escola_factory,
    lote_factory,
    contrato_factory,
    formulario_supervisao_factory,
    tipo_resposta_modelo_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
):
    app.conf.update(CELERY_ALWAYS_EAGER=True)

    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    edital = edital_factory.create(numero="78/SME/2016")
    lote = lote_factory.create()
    escola_ = escola_factory.create(lote=lote)
    contrato = contrato_factory.create(
        edital=edital,
    )
    contrato.lotes.add(lote)
    contrato.save()

    formulario_supervisao = formulario_supervisao_factory.create(
        formulario_base__usuario=usuario,
        formulario_base__data="2024-06-26",
        escola=escola_,
        status=FormularioSupervisao.workflow_class.NUTRIMANIFESTACAO_A_VALIDAR,
    )

    tipo_resposta_campo_simples = tipo_resposta_modelo_factory(
        nome="RespostaCampoTextoSimples"
    )
    tipo_pergunta_parametrizacao_ocorrencia_texto_simples = (
        tipo_pergunta_parametrizacao_ocorrencia_factory(
            nome="Campo de Texto Simples", tipo_resposta=tipo_resposta_campo_simples
        )
    )

    tipo_resposta_campo_numerico = tipo_resposta_modelo_factory(
        nome="RespostaCampoNumerico"
    )
    tipo_pergunta_parametrizacao_ocorrencia_campo_numerico = (
        tipo_pergunta_parametrizacao_ocorrencia_factory(
            nome="Campo Numérico", tipo_resposta=tipo_resposta_campo_numerico
        )
    )

    tipo_ocorrencia_1 = tipo_ocorrencia_factory.create(
        perfis=[TipoOcorrencia.SUPERVISAO],
        categoria__perfis=[TipoOcorrencia.SUPERVISAO],
        categoria__nome="FUNCIONÁRIOS",
        edital=edital,
    )
    tipo_ocorrencia_factory.create(
        perfis=[TipoOcorrencia.SUPERVISAO],
        categoria__perfis=[TipoOcorrencia.SUPERVISAO],
        categoria__nome="RECEBIMENTO DE ALIMENTOS",
        edital=edital,
    )
    parametrizacao_ocorrencia_factory(
        tipo_ocorrencia=tipo_ocorrencia_1,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_texto_simples,
        titulo="Qual uniforme faltou?",
    )
    parametrizacao_ocorrencia_factory(
        tipo_ocorrencia=tipo_ocorrencia_1,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_campo_numerico,
        titulo="Quantos uniformes faltaram?",
    )

    response = client.get(
        f"/imr/formulario-supervisao/{formulario_supervisao.uuid}/relatorio-pdf/"
    )
    assert response.status_code == status.HTTP_200_OK

    central_download = CentralDeDownload.objects.get()
    # Erro porque não há log de envio
    assert central_download.status == CentralDeDownload.STATUS_ERRO


def test_get_pdf_formulario_supervisao_error_does_not_exist(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    uuid_invalido = uuid.uuid4()
    response = client.get(f"/imr/formulario-supervisao/{uuid_invalido}/relatorio-pdf/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "FormularioSupervisao com o UUID informado não foi encontrado."
    }


def test_get_lista_nomes_nutricionistas(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    formulario_supervisao_factory.create(
        formulario_base__usuario__nome="FULANA DA SILVA"
    )
    formulario_supervisao_factory.create(
        formulario_base__usuario__nome="CICLANA DA SOUZA"
    )
    formulario_supervisao_factory.create(
        formulario_base__usuario__nome="BELTRANA SANTOS"
    )

    response = client.get(f"/imr/formulario-supervisao/lista_nomes_nutricionistas/")
    assert response.status_code == status.HTTP_200_OK

    results = response.json()["results"]
    assert len(results) == 3
