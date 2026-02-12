import datetime
import uuid as uuid_module

from model_bakery import baker
from rest_framework import status


class TestHistoricoEscolaEndpoint:
    """Testes para o endpoint de histórico da escola."""

    def test_historico_escola_sem_parametro_mes(self, get_historico_escola):
        """Testa requisição sem o parâmetro mes - deve retornar 400."""
        escola = baker.make("Escola")

        response = get_historico_escola(escola.uuid, ano=2023)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.json()
        assert "obrigatórios" in response.json()["detail"]

    def test_historico_escola_sem_parametro_ano(self, get_historico_escola):
        """Testa requisição sem o parâmetro ano - deve retornar 400."""
        escola = baker.make("Escola")

        response = get_historico_escola(escola.uuid, mes=1)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.json()
        assert "obrigatórios" in response.json()["detail"]

    def test_historico_escola_sem_parametros_mes_e_ano(self, get_historico_escola):
        """Testa requisição sem os parâmetros mes e ano - deve retornar 400."""
        escola = baker.make("Escola")

        response = get_historico_escola(escola.uuid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.json()
        assert "obrigatórios" in response.json()["detail"]

    def test_historico_escola_mes_invalido_nao_numerico(self, get_historico_escola):
        """Testa requisição com mes não numérico - deve retornar 400."""
        escola = baker.make("Escola")

        response = get_historico_escola(escola.uuid, mes="abc", ano=2023)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.json()
        assert "números inteiros" in response.json()["detail"]

    def test_historico_escola_ano_invalido_nao_numerico(self, get_historico_escola):
        """Testa requisição com ano não numérico - deve retornar 400."""
        escola = baker.make("Escola")

        response = get_historico_escola(escola.uuid, mes=1, ano="xyz")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.json()
        assert "números inteiros" in response.json()["detail"]

    def test_historico_escola_mes_menor_que_um(self, get_historico_escola):
        """Testa requisição com mes < 1 - deve retornar 400."""
        escola = baker.make("Escola")

        response = get_historico_escola(escola.uuid, mes=0, ano=2023)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.json()
        assert "entre 1 e 12" in response.json()["detail"]

    def test_historico_escola_mes_maior_que_doze(self, get_historico_escola):
        """Testa requisição com mes > 12 - deve retornar 400."""
        escola = baker.make("Escola")

        response = get_historico_escola(escola.uuid, mes=13, ano=2023)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.json()
        assert "entre 1 e 12" in response.json()["detail"]

    def test_historico_escola_mes_negativo(self, get_historico_escola):
        """Testa requisição com mes negativo - deve retornar 400."""
        escola = baker.make("Escola")

        response = get_historico_escola(escola.uuid, mes=-5, ano=2023)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.json()
        assert "entre 1 e 12" in response.json()["detail"]

    def test_historico_escola_uuid_invalido(self, get_historico_escola):
        """Testa requisição com UUID inválido - deve retornar 404."""
        uuid_invalido = uuid_module.uuid4()

        response = get_historico_escola(uuid_invalido, mes=1, ano=2023)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()
        assert "não encontrada" in response.json()["detail"]

    def test_historico_escola_sem_historico_retorna_dados_atuais(
        self, get_historico_escola
    ):
        """
        Testa que quando não existe histórico vigente,
        retorna os dados atuais da escola.
        """
        tipo_unidade = baker.make("TipoUnidadeEscolar", iniciais="EMEF")
        escola = baker.make("Escola", nome="Escola Teste", tipo_unidade=tipo_unidade)

        response = get_historico_escola(escola.uuid, mes=6, ano=2023)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["nome"] == "Escola Teste"
        assert data["tipo_unidade"]["iniciais"] == "EMEF"
        assert "uuid" in data["tipo_unidade"]

    def test_historico_escola_com_historico_vigente_retorna_dados_historico(
        self, get_historico_escola
    ):
        """
        Testa que quando existe histórico vigente para o período,
        retorna os dados do histórico.
        """
        tipo_unidade_atual = baker.make(
            "TipoUnidadeEscolar",
            iniciais="EMEF",
        )
        tipo_unidade_historico = baker.make(
            "TipoUnidadeEscolar",
            iniciais="CEI",
        )

        escola = baker.make(
            "Escola", nome="Escola Nome Atual", tipo_unidade=tipo_unidade_atual
        )

        baker.make(
            "HistoricoEscola",
            escola=escola,
            nome="Escola Nome Antigo",
            tipo_unidade=tipo_unidade_historico,
            data_inicial=datetime.date(2022, 12, 1),
            data_final=datetime.date(2023, 3, 31),
        )

        response = get_historico_escola(escola.uuid, mes=1, ano=2023)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["nome"] == "Escola Nome Antigo"
        assert data["tipo_unidade"]["iniciais"] == "CEI"
        assert "uuid" in data["tipo_unidade"]

    def test_historico_escola_com_historico_fora_do_periodo_retorna_dados_atuais(
        self, get_historico_escola
    ):
        """
        Testa que quando o histórico existe mas não está vigente para o período,
        retorna os dados atuais da escola.
        """
        tipo_unidade_atual = baker.make(
            "TipoUnidadeEscolar",
            iniciais="EMEF",
        )
        tipo_unidade_historico = baker.make(
            "TipoUnidadeEscolar",
            iniciais="CEI",
        )

        escola = baker.make(
            "Escola", nome="Escola Nome Atual", tipo_unidade=tipo_unidade_atual
        )

        baker.make(
            "HistoricoEscola",
            escola=escola,
            nome="Escola Nome Antigo",
            tipo_unidade=tipo_unidade_historico,
            data_inicial=datetime.date(2022, 12, 1),
            data_final=datetime.date(2023, 3, 31),
        )

        response = get_historico_escola(escola.uuid, mes=6, ano=2023)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["nome"] == "Escola Nome Atual"
        assert data["tipo_unidade"]["iniciais"] == "EMEF"

    def test_historico_escola_com_data_inicial_null(self, get_historico_escola):
        """
        Testa que quando o histórico tem data_inicial NULL (vigente desde sempre),
        retorna os dados do histórico.
        """
        tipo_unidade_atual = baker.make(
            "TipoUnidadeEscolar",
            iniciais="EMEF",
        )
        tipo_unidade_historico = baker.make(
            "TipoUnidadeEscolar",
            iniciais="CEI",
        )

        escola = baker.make(
            "Escola", nome="Escola Nome Atual", tipo_unidade=tipo_unidade_atual
        )

        baker.make(
            "HistoricoEscola",
            escola=escola,
            nome="Escola Nome Historico",
            tipo_unidade=tipo_unidade_historico,
            data_inicial=None,
            data_final=datetime.date(2025, 12, 31),
        )

        response = get_historico_escola(escola.uuid, mes=12, ano=2025)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["nome"] == "Escola Nome Historico"
        assert data["tipo_unidade"]["iniciais"] == "CEI"

    def test_historico_escola_multiplos_historicos_retorna_primeiro(
        self, get_historico_escola
    ):
        """
        Testa que quando existem múltiplos históricos vigentes,
        retorna o primeiro encontrado.
        """
        tipo_unidade_historico1 = baker.make(
            "TipoUnidadeEscolar",
            iniciais="CEI",
        )
        tipo_unidade_historico2 = baker.make(
            "TipoUnidadeEscolar",
            iniciais="EMEI",
        )

        escola = baker.make("Escola")

        baker.make(
            "HistoricoEscola",
            escola=escola,
            nome="Historico 1",
            tipo_unidade=tipo_unidade_historico1,
            data_inicial=datetime.date(2023, 1, 1),
            data_final=datetime.date(2023, 12, 31),
        )
        baker.make(
            "HistoricoEscola",
            escola=escola,
            nome="Historico 2",
            tipo_unidade=tipo_unidade_historico2,
            data_inicial=datetime.date(2023, 1, 1),
            data_final=datetime.date(2023, 12, 31),
        )

        response = get_historico_escola(escola.uuid, mes=6, ano=2023)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["nome"] in ["Historico 1", "Historico 2"]

    def test_historico_escola_data_limite_inicio_periodo(self, get_historico_escola):
        """
        Testa que a data de referência no início do período (dia 1)
        está incluída no range do histórico.
        """
        tipo_unidade_historico = baker.make("TipoUnidadeEscolar", iniciais="CEI")

        escola = baker.make("Escola")

        baker.make(
            "HistoricoEscola",
            escola=escola,
            nome="Historico Teste",
            tipo_unidade=tipo_unidade_historico,
            data_inicial=datetime.date(2023, 1, 1),
            data_final=datetime.date(2023, 12, 31),
        )

        response = get_historico_escola(escola.uuid, mes=1, ano=2023)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["nome"] == "Historico Teste"

    def test_historico_escola_data_limite_fim_periodo(self, get_historico_escola):
        """
        Testa que a data de referência no final do período
        está incluída no range do histórico.
        """
        tipo_unidade_historico = baker.make(
            "TipoUnidadeEscolar",
            iniciais="CEI",
        )

        escola = baker.make("Escola")

        baker.make(
            "HistoricoEscola",
            escola=escola,
            nome="Historico Teste",
            tipo_unidade=tipo_unidade_historico,
            data_inicial=datetime.date(2023, 1, 1),
            data_final=datetime.date(2023, 12, 1),
        )

        response = get_historico_escola(escola.uuid, mes=12, ano=2023)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["nome"] == "Historico Teste"

    def test_historico_escola_ano_bissexto(self, get_historico_escola):
        """
        Testa que o endpoint funciona corretamente com ano bissexto.
        """
        escola = baker.make("Escola", nome="Escola Bissexto")

        response = get_historico_escola(escola.uuid, mes=2, ano=2024)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["nome"] == "Escola Bissexto"
