import uuid

import pytest
from model_bakery import baker
from pypdf import PdfReader
from rest_framework import status

from config.celery import app
from src.dados_comuns import constants
from src.dados_comuns.models import CentralDeDownload, LogSolicitacoesUsuario
from src.imr.api.viewsets import FormularioSupervisaoModelViewSet
from src.imr.models import (
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

    response = client.get("/imr/formulario-supervisao/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 2


def test_get_categorias_nao_permitidas():
    view_instance = FormularioSupervisaoModelViewSet()

    # Teste para CEMEI
    categorias = view_instance._get_categorias_nao_permitidas(
        constants.TIPOS_UNIDADE_ESCOLAR.CEMEI.value
    )
    assert "LACTÁRIO" not in categorias
    assert "RESÍDUO DE ÓLEO UTILIZADO NA FRITURA" not in categorias

    # Teste para outro tipo de escola
    categorias = view_instance._get_categorias_nao_permitidas(
        constants.TIPOS_UNIDADE_ESCOLAR.EMEF.value
    )
    assert "LACTÁRIO" in categorias
    assert "RESÍDUO DE ÓLEO UTILIZADO NA FRITURA" not in categorias

    # Teste para CEI
    categorias = view_instance._get_categorias_nao_permitidas(
        constants.TIPO_UNIDADE_CEI_DIRET
    )
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
    tipo_unidade_emef = tipo_unidade_escolar_factory.create(
        iniciais=constants.TIPOS_UNIDADE_ESCOLAR.EMEF.value
    )
    escola_emef = escola_factory.create(tipo_unidade=tipo_unidade_emef)
    tipo_unidade_cemei = tipo_unidade_escolar_factory.create(
        iniciais=constants.TIPOS_UNIDADE_ESCOLAR.CEMEI.value
    )
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


def test_administrador_supervisao_lista_apenas_os_proprios_relatorios(
    client_autenticado_administrador_supervisao_nutricao,
    formulario_supervisao_factory,
):
    client, usuario = client_autenticado_administrador_supervisao_nutricao
    relatorio_proprio = formulario_supervisao_factory.create(
        formulario_base__usuario=usuario
    )
    formulario_supervisao_factory.create()

    response = client.get("/imr/formulario-supervisao/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["uuid"] == str(relatorio_proprio.uuid)


def test_dashboard_administrador_supervisao_contabiliza_apenas_relatorios_proprios(
    client_autenticado_administrador_supervisao_nutricao,
    formulario_supervisao_factory,
):
    client, usuario = client_autenticado_administrador_supervisao_nutricao
    formulario_supervisao_factory.create(formulario_base__usuario=usuario)
    formulario_supervisao_factory.create()

    response = client.get(
        "/imr/formulario-supervisao/dashboard/", {"novo_painel": "false"}
    )

    assert response.status_code == status.HTTP_200_OK
    total = next(
        resultado
        for resultado in response.json()["results"]
        if resultado["status"] == "TODOS_OS_RELATORIOS"
    )
    assert total["total"] == 1


def test_administrador_supervisao_nao_acessa_relatorio_de_outra_nutricionista(
    client_autenticado_administrador_supervisao_nutricao,
    formulario_supervisao_factory,
):
    client, _ = client_autenticado_administrador_supervisao_nutricao
    relatorio = formulario_supervisao_factory.create()

    response = client.get(f"/imr/formulario-supervisao/{relatorio.uuid}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_administrador_supervisao_nao_gera_pdf_de_outra_nutricionista(
    client_autenticado_administrador_supervisao_nutricao,
    formulario_supervisao_factory,
):
    client, _ = client_autenticado_administrador_supervisao_nutricao
    relatorio = formulario_supervisao_factory.create()

    response = client.get(f"/imr/formulario-supervisao/{relatorio.uuid}/relatorio-pdf/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_administrador_supervisao_lista_apenas_seu_nome(
    client_autenticado_administrador_supervisao_nutricao,
    formulario_supervisao_factory,
):
    client, usuario = client_autenticado_administrador_supervisao_nutricao
    formulario_supervisao_factory.create(formulario_base__usuario=usuario)
    formulario_supervisao_factory.create(
        formulario_base__usuario__nome="Outra nutricionista"
    )

    response = client.get("/imr/formulario-supervisao/lista_nomes_nutricionistas/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"] == [usuario.nome]


def test_cogestor_dre_lista_apenas_relatorios_da_propria_dre(
    client_autenticado_cogestor_dre,
    diretoria_regional_factory,
    escola_factory,
    formulario_supervisao_factory,
):
    client, diretoria_regional = client_autenticado_cogestor_dre
    outra_diretoria = diretoria_regional_factory.create()
    escola_da_dre = escola_factory.create(diretoria_regional=diretoria_regional)
    escola_de_outra_dre = escola_factory.create(diretoria_regional=outra_diretoria)
    relatorio_da_dre = formulario_supervisao_factory.create(escola=escola_da_dre)
    formulario_supervisao_factory.create(escola=escola_de_outra_dre)

    response = client.get("/imr/formulario-supervisao/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["uuid"] == str(relatorio_da_dre.uuid)


def test_cogestor_dre_nao_amplia_escopo_com_filtro(
    client_autenticado_cogestor_dre,
    diretoria_regional_factory,
    escola_factory,
    formulario_supervisao_factory,
):
    client, _ = client_autenticado_cogestor_dre
    outra_diretoria = diretoria_regional_factory.create()
    outra_escola = escola_factory.create(diretoria_regional=outra_diretoria)
    formulario_supervisao_factory.create(escola=outra_escola)

    response = client.get(
        "/imr/formulario-supervisao/",
        {"diretoria_regional": str(outra_diretoria.uuid)},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 0


def test_terceirizada_lista_apenas_relatorios_dos_proprios_lotes(
    client_autenticado_terceirizada,
    lote_factory,
    escola_factory,
    formulario_supervisao_factory,
):
    client, terceirizada = client_autenticado_terceirizada
    lote_da_terceirizada = lote_factory.create(terceirizada=terceirizada)
    lote_de_outra_terceirizada = lote_factory.create()
    escola_da_terceirizada = escola_factory.create(lote=lote_da_terceirizada)
    escola_de_outra_terceirizada = escola_factory.create(
        lote=lote_de_outra_terceirizada
    )
    relatorio_da_terceirizada = formulario_supervisao_factory.create(
        escola=escola_da_terceirizada
    )
    formulario_supervisao_factory.create(escola=escola_de_outra_terceirizada)

    response = client.get("/imr/formulario-supervisao/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["uuid"] == str(relatorio_da_terceirizada.uuid)


@pytest.mark.parametrize(
    "nome_perfil",
    [
        constants.COORDENADOR_SUPERVISAO_NUTRICAO,
        constants.COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
        constants.ADMINISTRADOR_MEDICAO,
        constants.ADMINISTRADOR_CODAE_GABINETE,
        constants.DINUTRE_DIRETORIA,
        constants.COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
    ],
)
def test_perfis_codae_listam_todos_os_relatorios(
    client,
    django_user_model,
    codae,
    formulario_supervisao_factory,
    nome_perfil,
):
    senha = constants.DJANGO_ADMIN_PASSWORD
    email = f"{nome_perfil.lower()}@test.com"
    usuario = django_user_model.objects.create_user(
        username=email,
        password=senha,
        email=email,
        registro_funcional="4321098",
    )
    perfil = baker.make("Perfil", nome=nome_perfil, ativo=True)
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=codae,
        perfil=perfil,
        data_inicial="2026-08-24",
        ativo=True,
    )
    formulario_supervisao_factory.create()
    formulario_supervisao_factory.create()
    client.login(username=usuario.username, password=senha)

    response = client.get("/imr/formulario-supervisao/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 2


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

    response = client.get(
        "/imr/formulario-supervisao/dashboard/", {"novo_painel": "false"}
    )
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]

    em_preenchimento = next(
        result
        for result in results
        if result["status"] == FormularioSupervisao.workflow_class.EM_PREENCHIMENTO
    )
    assert em_preenchimento["total"] == 3

    nutrimanifestacao_a_validar = next(
        result
        for result in results
        if result["status"]
        == FormularioSupervisao.workflow_class.NUTRIMANIFESTACAO_A_VALIDAR
    )
    assert nutrimanifestacao_a_validar["total"] == 3

    total = next(
        result for result in results if result["status"] == "TODOS_OS_RELATORIOS"
    )
    assert total["total"] == 6


@pytest.mark.parametrize(
    "parametros",
    [{}, {"novo_painel": "true"}],
    ids=["sem_parametro", "novo_painel_true"],
)
def test_dashboard_retorna_painel_novo_por_padrao_ou_com_flag_true(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    parametros,
):
    cliente = client_autenticado_vinculo_coordenador_supervisao_nutricao[0]

    resposta = cliente.get("/imr/formulario-supervisao/dashboard/", parametros)

    assert resposta.status_code == status.HTTP_200_OK
    resultados = resposta.json()["results"]
    assert [resultado["status"] for resultado in resultados] == [
        "EM_PREENCHIMENTO",
        "NUTRIMANIFESTACAO_A_VALIDAR",
        "COM_COMENTARIOS_DE_CODAE",
        "CORRIGIDO_PELA_SUPERVISAO",
        "VALIDADO_POR_CODAE",
    ]
    assert [resultado["label"] for resultado in resultados] == [
        "Em preenchimento pela Supervisão",
        "Enviados pela Supervisão",
        "Devolvidos com comentários",
        "Corrigidos pela Supervisão",
        "Validados pela CODAE",
    ]


def test_dashboard_retorna_painel_anterior_com_flag_false(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
):
    cliente = client_autenticado_vinculo_coordenador_supervisao_nutricao[0]

    resposta = cliente.get(
        "/imr/formulario-supervisao/dashboard/", {"novo_painel": "false"}
    )

    assert resposta.status_code == status.HTTP_200_OK
    resultados = resposta.json()["results"]
    assert [resultado["status"] for resultado in resultados] == [
        "EM_PREENCHIMENTO",
        "NUTRIMANIFESTACAO_A_VALIDAR",
        "COM_COMENTARIOS_DE_CODAE",
        "VALIDADO_POR_CODAE",
        "APROVADO",
        "TODOS_OS_RELATORIOS",
    ]
    assert [resultado["label"] for resultado in resultados] == [
        "Em Preenchimento",
        "Enviado para CODAE",
        "Com comentários de CODAE",
        "Validado pela CODAE",
        "Aprovados",
        "Todos os Relatórios",
    ]


def test_dashboard_contagem_por_status_respeita_as_quantidades(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory,
    escola_factory,
):
    cliente = client_autenticado_vinculo_coordenador_supervisao_nutricao[0]
    usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao[1]
    escola = escola_factory.create()
    
    quantidades_esperadas = {
        "EM_PREENCHIMENTO": 2,
        "NUTRIMANIFESTACAO_A_VALIDAR": 1,
        "COM_COMENTARIOS_DE_CODAE": 3,
        "CORRIGIDO_PELA_SUPERVISAO": 1,
        "VALIDADO_POR_CODAE": 2,
    }

    for status_relatorio, quantidade in quantidades_esperadas.items():
        formulario_supervisao_factory.create_batch(
            quantidade,
            escola=escola,
            formulario_base__usuario=usuario,
            status=status_relatorio,
        )

    formulario_supervisao_factory.create(
        escola=escola,
        formulario_base__usuario=usuario,
        status=FormularioSupervisao.workflow_class.APROVADO,
    )

    resposta = cliente.get(
        "/imr/formulario-supervisao/dashboard/", {"novo_painel": "true"}
    )

    assert resposta.status_code == status.HTTP_200_OK
    totais = {}
    for resultado in resposta.json()["results"]:
        totais[resultado["status"]] = resultado["total"]

    assert totais == quantidades_esperadas
    assert sum(totais.values()) == 9


def test_dashboard_contagem_por_status_sem_relatorios_retorna_zero(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
):
    cliente = client_autenticado_vinculo_coordenador_supervisao_nutricao[0]

    resposta = cliente.get(
        "/imr/formulario-supervisao/dashboard/", {"novo_painel": "true"}
    )

    assert resposta.status_code == status.HTTP_200_OK
    resultados = resposta.json()["results"]
    assert len(resultados) == 5
    for resultado in resultados:
        assert resultado["total"] == 0


def test_dashboard_contagem_por_status_nao_duplica_relatorio_entre_cards(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory,
):
    cliente = client_autenticado_vinculo_coordenador_supervisao_nutricao[0]
    usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao[1]
    formulario_supervisao_factory.create(
        formulario_base__usuario=usuario,
        status=FormularioSupervisao.workflow_class.CORRIGIDO_PELA_SUPERVISAO,
    )

    resposta = cliente.get(
        "/imr/formulario-supervisao/dashboard/", {"novo_painel": "true"}
    )

    assert resposta.status_code == status.HTTP_200_OK
    resultados = resposta.json()["results"]
    assert len(resultados) == 5
    total_contabilizado = 0

    for resultado in resultados:
        quantidade_esperada = 0
        if resultado["status"] == "CORRIGIDO_PELA_SUPERVISAO":
            quantidade_esperada = 1

        assert resultado["total"] == quantidade_esperada
        total_contabilizado += resultado["total"]

    assert total_contabilizado == 1


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

    reader = PdfReader(central_download.arquivo.path)
    page = reader.pages[0]
    conteudo_pdf_pagina_1 = page.extract_text()

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

    response = client.get("/imr/formulario-supervisao/lista_nomes_nutricionistas/")
    assert response.status_code == status.HTTP_200_OK

    results = response.json()["results"]
    assert len(results) == 3

@pytest.mark.parametrize(
    "nome_perfil",
    [
        constants.COORDENADOR_SUPERVISAO_NUTRICAO,
        constants.COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
        constants.ADMINISTRADOR_MEDICAO,
        constants.ADMINISTRADOR_CODAE_GABINETE,
        constants.DINUTRE_DIRETORIA,
        constants.COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
    ],
)
def test_perfis_codae_acessam_dashboard_novo(
    client,
    django_user_model,
    codae,
    nome_perfil,
):
    senha = constants.DJANGO_ADMIN_PASSWORD
    email = f"{nome_perfil.lower()}@test.com"
    usuario = django_user_model.objects.create_user(
        username=email,
        password=senha,
        email=email,
        registro_funcional="4321098",
    )
    perfil = baker.make("Perfil", nome=nome_perfil, ativo=True)
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=codae,
        perfil=perfil,
        data_inicial="2026-08-24",
        ativo=True,
    )
    client.login(username=usuario.username, password=senha)
    resposta = client.get("/imr/formulario-supervisao/dashboard/", {"novo_painel": "true"})
    assert resposta.status_code == status.HTTP_200_OK


def test_diretor_escola_nao_acessa_dashboard_novo(
    client_autenticado_diretor_escola
):
    cliente = client_autenticado_diretor_escola["client"]
    resposta = cliente.get("/imr/formulario-supervisao/dashboard/",{"novo_painel": "true"})
    assert resposta.status_code == status.HTTP_403_FORBIDDEN

def test_dashboard_filtra_relatorios_por_mes(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory,
):
    cliente = client_autenticado_vinculo_coordenador_supervisao_nutricao[0]

    formulario_supervisao_factory.create(
        formulario_base__data="2026-09-01"
    )
    formulario_supervisao_factory.create(
        formulario_base__data="2026-09-30"
    )
    formulario_supervisao_factory.create(
        formulario_base__data="2026-10-01"
    )

    resposta = cliente.get(
        "/imr/formulario-supervisao/dashboard/",
        {"novo_painel": "true", "mes": "9"},
    )

    assert resposta.status_code == status.HTTP_200_OK

    totais = {}
    for resultado in resposta.json()["results"]:
        totais[resultado["status"]] = resultado["total"]

    assert totais["EM_PREENCHIMENTO"] == 2
    assert sum(totais.values()) == 2


def test_dashboard_filtra_relatorios_por_ano(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory,
    escola_factory
):
    cliente = client_autenticado_vinculo_coordenador_supervisao_nutricao[0]
    usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao[1]
    escola = escola_factory.create()
    datas_visitas = [
        "2026-01-01",
        "2026-12-31",
        "2025-12-31",
        "2027-01-01"
    ]

    for data_visita in datas_visitas:
        formulario_supervisao_factory.create(
            escola=escola,
            formulario_base__usuario=usuario,
            formulario_base__data=data_visita
        )

    resposta = cliente.get(
        "/imr/formulario-supervisao/dashboard/",
        {"novo_painel": "true", "ano": 2026}
    )

    assert resposta.status_code == status.HTTP_200_OK
    totais = {}
    for resultado in resposta.json()["results"]:
        totais[resultado["status"]] = resultado["total"]

    assert totais["EM_PREENCHIMENTO"] == 2
    assert sum(totais.values()) == 2


def test_dashboard_filtra_relatorios_por_dre(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory,
    escola_factory,
    diretoria_regional_factory
):
    cliente = client_autenticado_vinculo_coordenador_supervisao_nutricao[0]
    usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao[1]
    diretoria = diretoria_regional_factory.create()
    primeira_escola = escola_factory.create(diretoria_regional=diretoria)
    segunda_escola = escola_factory.create(diretoria_regional=diretoria)
    escola_de_outra_dre = escola_factory.create()

    for escola in [primeira_escola, segunda_escola, escola_de_outra_dre]:
        formulario_supervisao_factory.create(
            escola=escola,
            formulario_base__usuario=usuario,
            formulario_base__data="2026-09-10"
        )

    resposta = cliente.get(
        "/imr/formulario-supervisao/dashboard/",
        {"novo_painel": "true", "diretoria_regional": str(diretoria.uuid)}
    )

    assert resposta.status_code == status.HTTP_200_OK
    totais = {}
    for resultado in resposta.json()["results"]:
        totais[resultado["status"]] = resultado["total"]

    assert totais["EM_PREENCHIMENTO"] == 2
    assert sum(totais.values()) == 2


def test_filtros_dre_mes_e_ano_mantem_dashboard_e_listagem_coerentes(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory,
    escola_factory
):
    cliente = client_autenticado_vinculo_coordenador_supervisao_nutricao[0]
    usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao[1]
    escola = escola_factory.create()
    escola_de_outra_dre = escola_factory.create()
    relatorio_inicio = formulario_supervisao_factory.create(
        escola=escola,
        formulario_base__usuario=usuario,
        formulario_base__data="2026-09-01"
    )
    relatorio_fim = formulario_supervisao_factory.create(
        escola=escola,
        formulario_base__usuario=usuario,
        formulario_base__data="2026-09-30",
        status=FormularioSupervisao.workflow_class.NUTRIMANIFESTACAO_A_VALIDAR
    )

    for escola_relatorio, data_visita in [
        (escola, "2026-08-31"),
        (escola, "2025-09-10"),
        (escola_de_outra_dre, "2026-09-10")
    ]:
        formulario_supervisao_factory.create(
            escola=escola_relatorio,
            formulario_base__usuario=usuario,
            formulario_base__data=data_visita
        )

    parametros = {
        "diretoria_regional": str(escola.diretoria_regional.uuid),
        "mes": 9,
        "ano": 2026
    }
    resposta_dashboard = cliente.get(
        "/imr/formulario-supervisao/dashboard/",
        {**parametros, "novo_painel": "true"}
    )

    assert resposta_dashboard.status_code == status.HTTP_200_OK
    totais = {}
    for resultado in resposta_dashboard.json()["results"]:
        totais[resultado["status"]] = resultado["total"]

    assert totais["EM_PREENCHIMENTO"] == 1
    assert totais["NUTRIMANIFESTACAO_A_VALIDAR"] == 1
    assert sum(totais.values()) == 2

    resposta_listagem = cliente.get(
        "/imr/formulario-supervisao/", parametros
    )

    assert resposta_listagem.status_code == status.HTTP_200_OK
    dados_listagem = resposta_listagem.json()
    assert dados_listagem["count"] == sum(totais.values())
    uuids_retornados = set()
    for resultado in dados_listagem["results"]:
        uuids_retornados.add(resultado["uuid"])

    assert uuids_retornados == {
        str(relatorio_inicio.uuid),
        str(relatorio_fim.uuid)
    }


def test_dashboard_filtros_sem_correspondencia_retornam_cards_zerados(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory
):
    cliente = client_autenticado_vinculo_coordenador_supervisao_nutricao[0]
    usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao[1]
    relatorio = formulario_supervisao_factory.create(
        formulario_base__usuario=usuario,
        formulario_base__data="2026-09-10"
    )
    diretoria = relatorio.escola.diretoria_regional

    resposta = cliente.get(
        "/imr/formulario-supervisao/dashboard/",
        {
            "novo_painel": "true",
            "diretoria_regional": str(diretoria.uuid),
            "mes": 10,
            "ano": 2026
        }
    )

    assert resposta.status_code == status.HTTP_200_OK
    resultados = resposta.json()["results"]
    assert len(resultados) == 5
    for resultado in resultados:
        assert resultado["total"] == 0


@pytest.mark.parametrize(
    "rota",
    ["/imr/formulario-supervisao/dashboard/", "/imr/formulario-supervisao/"],
    ids=["dashboard", "listagem"]
)
@pytest.mark.parametrize(
    "campo, valor",
    [("mes", 0), ("mes", 13), ("mes", "abc"), ("ano", "abc")],
    ids=[
        "mes_zero",
        "mes_maior_que_doze",
        "mes_nao_numerico",
        "ano_nao_numerico"
    ]
)
def test_filtros_rejeitam_valores_invalidos(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    rota,
    campo,
    valor
):
    cliente = client_autenticado_vinculo_coordenador_supervisao_nutricao[0]

    resposta = cliente.get(rota, {campo: valor})

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert campo in resposta.json()


def test_dashboard_status_selecionado_nao_restringe_totais_dos_cards(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory,
    escola_factory
):
    cliente = client_autenticado_vinculo_coordenador_supervisao_nutricao[0]
    usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao[1]
    escola = escola_factory.create()
    formulario_supervisao_factory.create_batch(
        2,
        escola=escola,
        formulario_base__usuario=usuario,
        formulario_base__data="2026-09-10"
    )
    formulario_supervisao_factory.create(
        escola=escola,
        formulario_base__usuario=usuario,
        formulario_base__data="2026-09-10",
        status=FormularioSupervisao.workflow_class.NUTRIMANIFESTACAO_A_VALIDAR
    )

    resposta = cliente.get(
        "/imr/formulario-supervisao/dashboard/",
        {
            "novo_painel": "true",
            "diretoria_regional": str(escola.diretoria_regional.uuid),
            "mes": 9,
            "ano": 2026,
            "status": "EM_PREENCHIMENTO"
        }
    )

    assert resposta.status_code == status.HTTP_200_OK
    totais = {}
    for resultado in resposta.json()["results"]:
        totais[resultado["status"]] = resultado["total"]

    assert totais["EM_PREENCHIMENTO"] == 2
    assert totais["NUTRIMANIFESTACAO_A_VALIDAR"] == 1
    assert sum(totais.values()) == 3


@pytest.mark.parametrize(
    "parametros, datas_esperadas",
    [
        ({"mes": 9}, ["10/09/2026", "10/09/2025"]),
        ({"ano": 2026}, ["10/09/2026", "10/10/2026"]),
        ({"mes": 9, "ano": 2026}, ["10/09/2026"])
    ],
    ids=["mes", "ano", "mes_e_ano"]
)
def test_listagem_filtra_relatorios_por_mes_e_ano(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory,
    escola_factory,
    parametros,
    datas_esperadas
):
    cliente = client_autenticado_vinculo_coordenador_supervisao_nutricao[0]
    usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao[1]
    escola = escola_factory.create()

    for data_visita in ["2026-09-10", "2025-09-10", "2026-10-10"]:
        formulario_supervisao_factory.create(
            escola=escola,
            formulario_base__usuario=usuario,
            formulario_base__data=data_visita
        )

    resposta = cliente.get("/imr/formulario-supervisao/", parametros)

    assert resposta.status_code == status.HTTP_200_OK
    dados = resposta.json()
    assert dados["count"] == len(datas_esperadas)
    datas_retornadas = []
    for resultado in dados["results"]:
        datas_retornadas.append(resultado["data"])

    assert sorted(datas_retornadas) == sorted(datas_esperadas)
