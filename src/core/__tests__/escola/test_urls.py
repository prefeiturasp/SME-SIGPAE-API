import datetime
import json

from model_bakery import baker
from rest_framework import status

from src.dados_comuns.constants import StringsCaminhoModelos

from ...models import DiaSuspensaoAtividades, GrupoUnidadeEscolar
from ...services import NovoSGPServicoLogado, NovoSGPServicoLogadoException

ENDPOINT_ALUNOS_POR_PERIODO = "quantidade-alunos-por-periodo"


ENDPOINT_LOTES = "lotes"


ENDPOINT_LISTA_DIAS = "dias-suspensao-atividades/lista-dias"


def _mock_obter_token_erro(monkeypatch):
    def _raise_login_error(self):
        raise NovoSGPServicoLogadoException("Não foi possível logar no sistema")

    monkeypatch.setattr(NovoSGPServicoLogado, "_obter_token", _raise_login_error)


ENDPOINT_LOTES_SIMPLES = "lotes-simples"


def test_url_endpoint_quantidade_alunos_por_periodo(client_autenticado, escola):
    response = client_autenticado.get(
        f"/{ENDPOINT_ALUNOS_POR_PERIODO}/escola/{escola.uuid}/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_escola_simplissima_dre_unpaginated(
    client_autenticado_da_dre, diretoria_regional
):
    assert diretoria_regional.escolas.count() == 3
    response = client_autenticado_da_dre.get(
        "/escolas-simplissima-com-dre-unpaginated/terc-total/?dre=d305add2-f070-4ad3-8c17-ba9664a7c655"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 3


def test_url_endpoint_escola_simplessima_actions(
    client_autenticado_da_escola, diretoria_regional
):
    client = client_autenticado_da_escola

    response = client.get(f"/escolas-simplissima/{diretoria_regional.uuid}/")
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_periodos_escolares_actions(client_autenticado_da_escola):
    client = client_autenticado_da_escola

    agora = datetime.datetime.now()
    mes = agora.month
    ano = agora.year

    response = client.get(
        f"/periodos-escolares/inclusao-continua-por-mes/?mes={mes}&ano={ano}"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_periodos_escolares_inclusao_continua_por_mes_considera_encerrado_por_quantidade_periodo(
    client_autenticado_da_escola, escola
):
    client = client_autenticado_da_escola
    motivo = baker.make("MotivoInclusaoContinua", nome="Programa Contínuo")
    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = baker.make("PeriodoEscolar", nome="TARDE")
    periodo_noite = baker.make("PeriodoEscolar", nome="NOITE")
    inclusao = baker.make(
        "InclusaoAlimentacaoContinua",
        escola=escola,
        rastro_escola=escola,
        data_inicial=datetime.date(2026, 4, 20),
        data_final=datetime.date(2026, 5, 31),
        motivo=motivo,
        status="CODAE_AUTORIZADO",
    )
    baker.make(
        "QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao,
        periodo_escolar=periodo_manha,
        encerrado_a_partir_de=datetime.date(2026, 4, 30),
    )
    baker.make(
        "QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao,
        periodo_escolar=periodo_tarde,
        encerrado_a_partir_de=datetime.date(2026, 5, 10),
    )
    baker.make(
        "QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao,
        periodo_escolar=periodo_noite,
    )

    response = client.get(
        "/periodos-escolares/inclusao-continua-por-mes/?mes=05&ano=2026"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["periodos"] == {
        "TARDE": str(periodo_tarde.uuid),
        "NOITE": str(periodo_noite.uuid),
    }


def test_url_endpoint_periodos_escolares_inclusao_continua_por_mes_nao_retorna_quando_encerrada_antes_do_mes(
    client_autenticado_da_escola, escola
):
    client = client_autenticado_da_escola
    motivo = baker.make("MotivoInclusaoContinua", nome="Programa Contínuo")
    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    inclusao = baker.make(
        "InclusaoAlimentacaoContinua",
        escola=escola,
        rastro_escola=escola,
        data_inicial=datetime.date(2026, 4, 1),
        data_final=datetime.date(2026, 12, 31),
        motivo=motivo,
        status="CODAE_AUTORIZADO",
    )
    baker.make(
        "QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao,
        periodo_escolar=periodo_manha,
        encerrado_a_partir_de=datetime.date(2026, 4, 30),
    )

    response = client.get(
        "/periodos-escolares/inclusao-continua-por-mes/?mes=05&ano=2026"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["periodos"] is None


def test_url_endpoint_periodos_escolares_inclusao_continua_por_mes_ignora_periodo_cancelado(
    client_autenticado_da_escola, escola
):
    client = client_autenticado_da_escola
    motivo = baker.make("MotivoInclusaoContinua", nome="Programa Contínuo")
    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = baker.make("PeriodoEscolar", nome="TARDE")
    inclusao = baker.make(
        "InclusaoAlimentacaoContinua",
        escola=escola,
        rastro_escola=escola,
        data_inicial=datetime.date(2026, 5, 1),
        data_final=datetime.date(2026, 5, 31),
        motivo=motivo,
        status="CODAE_AUTORIZADO",
    )
    baker.make(
        "QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao,
        periodo_escolar=periodo_manha,
        cancelado=True,
    )
    baker.make(
        "QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao,
        periodo_escolar=periodo_tarde,
        cancelado=False,
    )

    response = client.get(
        "/periodos-escolares/inclusao-continua-por-mes/?mes=05&ano=2026"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["periodos"] == {
        "TARDE": str(periodo_tarde.uuid),
    }


def test_url_endpoint_periodos_escolares_inclusao_continua_por_mes_nao_retorna_sem_dia_da_semana_ativo(
    client_autenticado_da_escola, escola
):
    client = client_autenticado_da_escola
    motivo = baker.make("MotivoInclusaoContinua", nome="Programa Contínuo")
    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    inclusao = baker.make(
        "InclusaoAlimentacaoContinua",
        escola=escola,
        rastro_escola=escola,
        data_inicial=datetime.date(2026, 6, 1),
        data_final=datetime.date(2026, 9, 30),
        motivo=motivo,
        status="CODAE_AUTORIZADO",
    )
    baker.make(
        "QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao,
        periodo_escolar=periodo_manha,
        dias_semana=[4],
        encerrado_a_partir_de=datetime.date(2026, 7, 2),
    )

    response = client.get(
        "/periodos-escolares/inclusao-continua-por-mes/?mes=07&ano=2026"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["periodos"] is None


def test_url_endpoint_periodos_escolares_inclusao_continua_por_mes_retorna_quando_dia_da_semana_ainda_cabe_no_encerramento(
    client_autenticado_da_escola, escola
):
    client = client_autenticado_da_escola
    motivo = baker.make("MotivoInclusaoContinua", nome="Programa Contínuo")
    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    inclusao = baker.make(
        "InclusaoAlimentacaoContinua",
        escola=escola,
        rastro_escola=escola,
        data_inicial=datetime.date(2026, 6, 1),
        data_final=datetime.date(2026, 9, 30),
        motivo=motivo,
        status="CODAE_AUTORIZADO",
    )
    baker.make(
        "QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao,
        periodo_escolar=periodo_manha,
        dias_semana=[4],
        encerrado_a_partir_de=datetime.date(2026, 7, 3),
    )

    response = client.get(
        "/periodos-escolares/inclusao-continua-por-mes/?mes=07&ano=2026"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["periodos"] == {
        "MANHA": str(periodo_manha.uuid),
    }


def test_url_relatorios_alunos_matriculados_actions(client_autenticado_da_escola):
    client = client_autenticado_da_escola

    response = client.get("/relatorio-alunos-matriculados/filtros/")

    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()

    assert (
        len(response_data["lotes"]) == 1
    ), f"Esperado 1 lote, mas encontrou {len(response_data['lotes'])}"

    assert (
        len(response_data["diretorias_regionais"]) == 1
    ), f"Esperado 1 DRE, mas encontrou {len(response_data['diretorias_regionais'])}"

    assert (
        len(response_data["tipos_unidade_escolar"]) == 1
    ), f"Esperado 1 tipo unidade escolar, mas encontrou {len(response_data['tipos_unidade_escolar'])}"

    assert (
        len(response_data["escolas"]) == 1
    ), f"Esperado 1 escola, mas encontrou {len(response_data['escolas'])}"

    response = client.get("/relatorio-alunos-matriculados/filtrar/")
    assert response.status_code == status.HTTP_200_OK


def test_escolas_simplissimas_com_paginacao(client_autenticado_da_escola):
    response = client_autenticado_da_escola.get("/escolas-simplissima/?page=1")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 4
    assert "count" in response.json()


def test_escolas_simplissimas_sem_paginacao(client_autenticado_da_escola):
    response = client_autenticado_da_escola.get("/escolas-simplissima/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 4
    assert "count" not in response.json()


def test_url_endpoint_cria_dias_suspensao_atividades(
    client_autenticado_coordenador_codae, edital_factory
):
    edital_factory.create(
        numero="Edital de Pregão nº 75/SME/2022",
        uuid="85d4bdf1-79d3-4f93-87d7-9999ae4cd9c2",
    )
    edital_factory.create(
        numero="Edital de Pregão nº 36/SME/2022",
        uuid="10b56d45-b82d-4cce-9a14-36bbb082ac4d",
    )
    edital_factory.create(
        numero="Edital de Pregão nº 18/SME/2023",
        uuid="00f008ea-3410-4547-99e6-4e91e0168af8",
    )
    data = {
        "data": "2022-08-08",
        "cadastros_calendario": [
            {
                "editais": [
                    "85d4bdf1-79d3-4f93-87d7-9999ae4cd9c2",
                    "10b56d45-b82d-4cce-9a14-36bbb082ac4d",
                ],
                "tipo_unidades": [
                    "1cc3253b-e297-42b3-8e57-ebfd115a1aba",
                    "40ee89a7-dc70-4abb-ae21-369c67f2b9e3",
                ],
            },
            {
                "editais": [
                    "85d4bdf1-79d3-4f93-87d7-9999ae4cd9c2",
                    "00f008ea-3410-4547-99e6-4e91e0168af8",
                ],
                "tipo_unidades": [
                    "ac4858ff-1c11-41f3-b539-7a02696d6d1b",
                ],
            },
        ],
    }
    response = client_autenticado_coordenador_codae.post(
        "/dias-suspensao-atividades/", content_type="application/json", data=data
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert DiaSuspensaoAtividades.objects.count() == 6
    response = client_autenticado_coordenador_codae.get(
        "/dias-suspensao-atividades/?mes=8&ano=2022", content_type="application/json"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 6
    response = client_autenticado_coordenador_codae.get(
        "/dias-suspensao-atividades/?mes=9&ano=2022", content_type="application/json"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0
    data = {"data": "2022-08-08", "cadastros_calendario": []}
    response = client_autenticado_coordenador_codae.post(
        "/dias-suspensao-atividades/", content_type="application/json", data=data
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert DiaSuspensaoAtividades.objects.count() == 0


def test_url_endpoint_meses_anos(client_autenticado_da_escola):
    response = client_autenticado_da_escola.get(
        "/relatorio-controle-frequencia/meses-anos/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 3


def test_url_endpoint_filtros(client_autenticado_da_escola):
    response = client_autenticado_da_escola.get(
        "/relatorio-controle-frequencia/filtros/?mes=6&ano=2024"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["periodos"] == []
    assert response.data["data_inicial"] == datetime.date(2024, 6, 1)
    assert response.data["data_final"] == datetime.date(2024, 6, 30)


def test_url_endpoint_filtrar(
    client_autenticado_da_escola, periodo_escolar, periodo_escolar_parcial
):
    response = client_autenticado_da_escola.get(
        f"/relatorio-controle-frequencia/filtrar/?periodos={json.dumps([str(periodo_escolar.uuid)])}&data_inicial=2024-06-03&data_final=2024-06-25"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["periodos"].get("INTEGRAL") == 0
    assert response.data["total_matriculados"] == 0


def test_escola_simplissima_dre_unpaginated_nome_edital(
    client_autenticado_da_dre, escola_edital_41
):
    nome_edital = "Edital de Pregão nº 41/sme/2017"
    response = client_autenticado_da_dre.get(
        f"/escolas-simplissima-com-dre-unpaginated/terc-total/?nome_edital={nome_edital}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    escola = response.json()[0]
    assert escola_edital_41.nome == escola["nome"]
    assert nome_edital == escola["lote_obj"]["contratos_do_lote"][0]["edital_numero"]


def test_grupos_por_dre_quando_parametro_dre_nao_enviado(
    client_autenticado_da_dre, grupos_da_dre
):
    response = client_autenticado_da_dre.get("/grupos-unidade-escolar/por-dre/")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Parâmetro 'dre' é obrigatório."}


def test_grupos_por_dre_quando_parametro_dre_nao_existe(
    client_autenticado_da_dre, grupos_da_dre
):
    response = client_autenticado_da_dre.get(
        f"/grupos-unidade-escolar/por-dre/?dre={grupos_da_dre.escolas.first().uuid}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "DRE não encontrada."}


def test_grupos_por_dre_quando_parametro_dre_existe(
    client_autenticado_da_dre, grupos_da_dre
):
    response = client_autenticado_da_dre.get(
        f"/grupos-unidade-escolar/por-dre/?dre={grupos_da_dre.uuid}"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "grupos": [
            {"habilitado": True, "nome": GrupoUnidadeEscolar.GRUPO_1},
            {"habilitado": False, "nome": GrupoUnidadeEscolar.GRUPO_2},
            {"habilitado": False, "nome": GrupoUnidadeEscolar.GRUPO_3},
        ]
    }


def test_dia_calendario_sem_perido_escolar(
    client_autenticado_da_dre, dia_calendario_diurno, dia_calendario_noturno, escola
):
    response = client_autenticado_da_dre.get(
        f"/dias-calendario/?escola_uuid={escola.uuid}&mes=5&ano=2024"
    )

    assert response.status_code == status.HTTP_200_OK
    resposta = response.json()
    assert isinstance(resposta, list)
    assert len(resposta) == 1
    esperado = {
        "escola": escola.nome,
        "dia": "15",
        "periodo_escolar": None,
        "data": "15/05/2024",
        "dia_letivo": True,
        "criado_em": dia_calendario_diurno.criado_em.strftime("%d/%m/%Y %H:%M:%S"),
        "alterado_em": dia_calendario_diurno.alterado_em.strftime("%d/%m/%Y %H:%M:%S"),
    }
    for campo, valor in esperado.items():
        assert resposta[0][campo] == valor


def test_dia_calendario_com_perido_escolar(
    client_autenticado_da_dre,
    dia_calendario_diurno,
    dia_calendario_noturno,
    escola,
    periodo_escolar_noite,
):
    response = client_autenticado_da_dre.get(
        f"/dias-calendario/?escola_uuid={escola.uuid}&mes=5&ano=2024&periodo_escolar_uuid={periodo_escolar_noite.uuid}"
    )

    assert response.status_code == status.HTTP_200_OK
    resposta = response.json()
    assert isinstance(resposta, list)
    assert len(resposta) == 1
    esperado = {
        "escola": escola.nome,
        "dia": "15",
        "data": "15/05/2024",
        "dia_letivo": False,
        "criado_em": dia_calendario_noturno.criado_em.strftime("%d/%m/%Y %H:%M:%S"),
        "alterado_em": dia_calendario_noturno.alterado_em.strftime("%d/%m/%Y %H:%M:%S"),
    }
    for campo, valor in esperado.items():
        assert resposta[0][campo] == valor

    assert resposta[0]["periodo_escolar"]["uuid"] == str(periodo_escolar_noite.uuid)
    assert resposta[0]["periodo_escolar"]["nome"] == "NOITE"


def test_dia_calendario_mes_nao_cadastrado(
    client_autenticado_da_dre, escola, periodo_escolar_noite
):
    response = client_autenticado_da_dre.get(
        f"/dias-calendario/?escola_uuid={escola.uuid}&mes=6&ano=2024&periodo_escolar_uuid={periodo_escolar_noite.uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    resposta = response.json()
    assert isinstance(resposta, list)
    assert len(resposta) == 0


def test_url_endpoint_filtrar_total_unico_por_mes_usa_historico_matricula(
    client_autenticado_da_escola_cei,
    escola_cei,
    periodo_escolar,
    periodo_escolar_parcial,
    faixas_etarias_ativas,
):
    aluno = baker.make(
        "Aluno",
        nome="Criança Histórico",
        codigo_eol="1234567",
        escola=escola_cei,
    )
    baker.make(
        "HistoricoMatriculaAluno",
        aluno=aluno,
        escola=escola_cei,
        data_inicio=datetime.date(2024, 6, 1),
        data_fim=datetime.date(2024, 6, 30),
    )

    data_teste = datetime.date(2024, 6, 15)
    log_integral = baker.make(
        "LogAlunosMatriculadosFaixaEtariaDia",
        escola=escola_cei,
        periodo_escolar=periodo_escolar,
        faixa_etaria=faixas_etarias_ativas[0],
        quantidade=1,
        data=data_teste,
    )
    log_parcial = baker.make(
        "LogAlunosMatriculadosFaixaEtariaDia",
        escola=escola_cei,
        periodo_escolar=periodo_escolar_parcial,
        faixa_etaria=faixas_etarias_ativas[1],
        quantidade=1,
        data=data_teste,
    )
    baker.make(
        "LogAlunoPorDia", log_alunos_matriculados_faixa_dia=log_integral, aluno=aluno
    )
    baker.make(
        "LogAlunoPorDia", log_alunos_matriculados_faixa_dia=log_parcial, aluno=aluno
    )

    url = (
        f"/relatorio-controle-frequencia/filtrar/?"
        f"periodos={json.dumps([str(periodo_escolar.uuid), str(periodo_escolar_parcial.uuid)])}&"
        f"data_inicial=2024-06-01&data_final=2024-06-30&"
        f"mes_ano=06_2024"
    )

    response = client_autenticado_da_escola_cei.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["total_matriculados"] == 1


def test_url_endpoint_lista_dias_sem_parametros(client_autenticado):
    response = client_autenticado.get(f"/{ENDPOINT_LISTA_DIAS}/")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Informe escola, mes e ano."


def test_url_endpoint_lista_dias_escola_nao_encontrada(client_autenticado):
    response = client_autenticado.get(
        f"/{ENDPOINT_LISTA_DIAS}/",
        {"escola": "00000000-0000-0000-0000-000000000000", "mes": 5, "ano": 2026},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Escola não encontrada."


def test_url_endpoint_lista_dias_suspensos(client_autenticado, escola):
    edital_1 = baker.make(
        StringsCaminhoModelos.MODEL_EDITAL.value, numero="Edital 01/2026"
    )
    edital_2 = baker.make(
        StringsCaminhoModelos.MODEL_EDITAL.value, numero="Edital 02/2026"
    )
    lote = baker.make("Lote")

    contrato_1 = baker.make("terceirizada.Contrato", edital=edital_1, encerrado=False)
    contrato_1.lotes.add(lote)

    contrato_2 = baker.make("terceirizada.Contrato", edital=edital_2, encerrado=False)
    contrato_2.lotes.add(lote)

    escola.lote = lote
    escola.save()

    baker.make(
        DiaSuspensaoAtividades,
        data=datetime.date(2026, 5, 10),
        tipo_unidade=escola.tipo_unidade,
        edital=edital_1,
    )
    baker.make(
        DiaSuspensaoAtividades,
        data=datetime.date(2026, 5, 10),
        tipo_unidade=escola.tipo_unidade,
        edital=edital_2,
    )
    baker.make(
        DiaSuspensaoAtividades,
        data=datetime.date(2026, 5, 20),
        tipo_unidade=escola.tipo_unidade,
        edital=edital_1,
    )

    response = client_autenticado.get(
        f"/{ENDPOINT_LISTA_DIAS}/",
        {"escola": str(escola.uuid), "mes": 5, "ano": 2026},
    )

    assert response.status_code == status.HTTP_200_OK

    resultado = response.json()
    assert len(resultado) == 2

    assert resultado[0]["data"] == "10/05/2026"
    assert set(resultado[0]["editais"]) == {"Edital 01/2026", "Edital 02/2026"}

    assert resultado[1]["data"] == "20/05/2026"
    assert resultado[1]["editais"] == ["Edital 01/2026"]


def test_url_endpoint_lista_dias_nao_retorna_contrato_encerrado(
    client_autenticado, escola
):
    edital = baker.make(
        StringsCaminhoModelos.MODEL_EDITAL.value, numero="Edital 01/2026"
    )
    lote = baker.make("Lote")
    contrato = baker.make("terceirizada.Contrato", edital=edital, encerrado=True)
    contrato.lotes.add(lote)
    escola.lote = lote
    escola.save()

    baker.make(
        DiaSuspensaoAtividades,
        data=datetime.date(2026, 5, 10),
        tipo_unidade=escola.tipo_unidade,
        edital=edital,
    )

    response = client_autenticado.get(
        f"/{ENDPOINT_LISTA_DIAS}/",
        {"escola": str(escola.uuid), "mes": 5, "ano": 2026},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []
