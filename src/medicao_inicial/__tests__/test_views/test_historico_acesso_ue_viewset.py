import datetime

from model_bakery import baker
from rest_framework import status

from src.medicao_inicial.historico_acesso_ue.models import (
    HistoricoAcessoMedicaoInicialUE,
)


def test_total_por_dre_retorna_400_sem_parametros_obrigatorios(
    client_autenticado_coordenador_codae,
):
    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/historico-acesso-ue/total-por-dre/",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Parâmetros obrigatórios: mes, ano, dre_uuid"}


def test_total_por_dre_conta_historicos_sem_data_final_a_partir_do_mes_inicial(
    client_autenticado_coordenador_codae,
    diretoria_regional,
):
    escola_inicio_mes = baker.make(
        "Escola",
        nome="EMEF Inicio Mes",
        codigo_eol="100001",
        diretoria_regional=diretoria_regional,
    )
    escola_fim_mes = baker.make(
        "Escola",
        nome="EMEF Fim Mes",
        codigo_eol="100002",
        diretoria_regional=diretoria_regional,
    )
    baker.make(
        HistoricoAcessoMedicaoInicialUE,
        escola=escola_inicio_mes,
        data_inicial=datetime.date(2026, 4, 1),
        data_final=None,
    )
    baker.make(
        HistoricoAcessoMedicaoInicialUE,
        escola=escola_fim_mes,
        data_inicial=datetime.date(2026, 4, 30),
        data_final=None,
    )
    baker.make(
        HistoricoAcessoMedicaoInicialUE,
        escola=baker.make(
            "Escola", codigo_eol="100003", diretoria_regional=diretoria_regional
        ),
        data_inicial=datetime.date(2026, 5, 1),
        data_final=None,
    )
    baker.make(
        HistoricoAcessoMedicaoInicialUE,
        escola=baker.make("Escola", codigo_eol="100004"),
        data_inicial=datetime.date(2026, 4, 15),
        data_final=None,
    )

    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/historico-acesso-ue/total-por-dre/",
        {"mes": 4, "ano": 2026, "dre_uuid": str(diretoria_regional.uuid)},
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == 2

    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/historico-acesso-ue/total-por-dre/",
        {"mes": 5, "ano": 2026, "dre_uuid": str(diretoria_regional.uuid)},
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == 3


def test_total_por_dre_considera_intervalos_nas_bordas_do_mes(
    client_autenticado_coordenador_codae,
    diretoria_regional,
):
    baker.make(
        HistoricoAcessoMedicaoInicialUE,
        escola=baker.make(
            "Escola", codigo_eol="200001", diretoria_regional=diretoria_regional
        ),
        data_inicial=datetime.date(2026, 3, 31),
        data_final=datetime.date(2026, 4, 1),
    )
    baker.make(
        HistoricoAcessoMedicaoInicialUE,
        escola=baker.make(
            "Escola", codigo_eol="200002", diretoria_regional=diretoria_regional
        ),
        data_inicial=datetime.date(2026, 4, 30),
        data_final=datetime.date(2026, 5, 1),
    )
    baker.make(
        HistoricoAcessoMedicaoInicialUE,
        escola=baker.make(
            "Escola", codigo_eol="200003", diretoria_regional=diretoria_regional
        ),
        data_inicial=datetime.date(2026, 3, 1),
        data_final=datetime.date(2026, 3, 31),
    )

    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/historico-acesso-ue/total-por-dre/",
        {"mes": 4, "ano": 2026, "dre_uuid": str(diretoria_regional.uuid)},
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == 1


def test_total_por_dre_desconsidera_mes_da_data_final(
    client_autenticado_coordenador_codae,
    diretoria_regional,
):
    baker.make(
        HistoricoAcessoMedicaoInicialUE,
        escola=baker.make(
            "Escola", codigo_eol="210001", diretoria_regional=diretoria_regional
        ),
        data_inicial=datetime.date(2026, 1, 1),
        data_final=datetime.date(2026, 2, 1),
    )

    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/historico-acesso-ue/total-por-dre/",
        {"mes": 1, "ano": 2026, "dre_uuid": str(diretoria_regional.uuid)},
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == 1

    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/historico-acesso-ue/total-por-dre/",
        {"mes": 2, "ano": 2026, "dre_uuid": str(diretoria_regional.uuid)},
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == 0


def test_total_por_dre_nao_duplica_escola_com_multiplos_historicos_no_mes(
    client_autenticado_coordenador_codae,
    diretoria_regional,
):
    escola = baker.make(
        "Escola",
        nome="EMEF Repetida",
        codigo_eol="300001",
        diretoria_regional=diretoria_regional,
    )
    baker.make(
        HistoricoAcessoMedicaoInicialUE,
        escola=escola,
        data_inicial=datetime.date(2026, 4, 1),
        data_final=None,
    )
    baker.make(
        HistoricoAcessoMedicaoInicialUE,
        escola=escola,
        data_inicial=datetime.date(2026, 4, 10),
        data_final=datetime.date(2026, 4, 20),
    )

    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/historico-acesso-ue/total-por-dre/",
        {"mes": 4, "ano": 2026, "dre_uuid": str(diretoria_regional.uuid)},
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == 1
