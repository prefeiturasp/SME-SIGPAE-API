import datetime

import pytest
from model_bakery import baker
from rest_framework import status

from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.fluxo_status import DietaEspecialWorkflow
from sme_sigpae_api.dieta_especial.models import (
    AlergiaIntolerancia,
    Alimento,
    ClassificacaoDieta,
    ProtocoloPadraoDietaEspecial,
    SolicitacaoDietaEspecial,
)
from sme_sigpae_api.escola.models import Aluno
from sme_sigpae_api.produto.models import Produto

pytestmark = pytest.mark.django_db


@pytest.fixture
def alergias_intolerancias_fixture():
    """Cria alergias/intolerâncias para o teste."""
    alergia_1 = baker.make(AlergiaIntolerancia, descricao="Alergia a Leite")
    alergia_2 = baker.make(AlergiaIntolerancia, descricao="Alergia a Ovo")
    alergia_3 = baker.make(AlergiaIntolerancia, descricao="Alergia a Soja")
    return [alergia_1, alergia_2, alergia_3]


@pytest.fixture
def classificacoes_fixture():
    """Cria classificações para o teste."""
    tipo_a = baker.make(ClassificacaoDieta, nome="Tipo A")
    tipo_b = baker.make(ClassificacaoDieta, nome="Tipo B")
    tipo_a_enteral = baker.make(ClassificacaoDieta, nome="Tipo A Enteral")
    return [tipo_a, tipo_b, tipo_a_enteral]


@pytest.fixture
def protocolo_padrao_fixture():
    """Cria protocolo padrão para o teste."""
    return baker.make(
        ProtocoloPadraoDietaEspecial,
        nome_protocolo="ALERGIA - LEITE E DERIVADOS",
        status="LIBERADO",
    )


@pytest.fixture
def alimentos_fixture():
    """Cria alimentos para o teste."""
    baker.make(Alimento, _quantity=6)
    return Alimento.objects.all()


@pytest.fixture
def produtos_fixture():
    """Cria produtos para o teste."""
    baker.make(Produto, _quantity=6)
    return Produto.objects.all()


@pytest.fixture
def substituicoes_fixture(alimentos_fixture, produtos_fixture):
    """Cria substituições para o teste."""
    substituicoes = []
    ids_produtos = [p.uuid for p in produtos_fixture]
    for i in range(4):
        substituicoes.append(
            {
                "alimento": alimentos_fixture[i % len(alimentos_fixture)].id,
                "tipo": "I" if i % 2 == 0 else "S",
                "substitutos": ids_produtos[: min(3, len(ids_produtos))],
            }
        )
    return substituicoes


@pytest.fixture
def aluno_teste(escola):
    """Cria um aluno para o teste."""
    return baker.make(
        Aluno,
        nome="João da Silva Santos",
        codigo_eol="7891234",
        data_nascimento="2015-05-10",
        escola=escola,
    )


@pytest.fixture
def dieta_comum_autorizada(
    aluno_teste,
    escola,
    alergias_intolerancias_fixture,
    classificacoes_fixture,
    protocolo_padrao_fixture,
    substituicoes_fixture,
    alimentos_fixture,
    produtos_fixture,
    template_mensagem_dieta_especial,
):
    """Cria uma solicitação de dieta especial COMUM autorizada com todos os campos preenchidos."""
    dieta = baker.make(
        SolicitacaoDietaEspecial,
        aluno=aluno_teste,
        rastro_escola=escola,
        escola_destino=escola,
        tipo_solicitacao=SolicitacaoDietaEspecial.COMUM,
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        ativo=True,
        classificacao=classificacoes_fixture[0],
        nome_completo_pescritor="Dr. Roberto Médico Silva",
        registro_funcional_pescritor="CRM123",
        registro_funcional_nutricionista="CRN987654",
        observacoes="Aluno com alergia severa a laticínios",
        informacoes_adicionais="Informações adicionais sobre a dieta",
        protocolo_padrao=protocolo_padrao_fixture,
        nome_protocolo=protocolo_padrao_fixture.nome_protocolo,
        orientacoes_gerais="Evitar contato cruzado com derivados de leite",
        data_inicio=datetime.date.today(),
        caracteristicas_do_alimento="Alimentos sem lactose",
    )
    # Adiciona alergias/intolerâncias
    dieta.alergias_intolerancias.set([alergias_intolerancias_fixture[0]])
    return dieta


@pytest.fixture
def dieta_alteracao_ue_autorizada(
    aluno_teste,
    escola,
    dieta_comum_autorizada,
    alergias_intolerancias_fixture,
    classificacoes_fixture,
    protocolo_padrao_fixture,
    substituicoes_fixture,
    alimentos_fixture,
    produtos_fixture,
    template_mensagem_dieta_especial,
):
    """Cria uma solicitação de dieta especial ALTERACAO_UE autorizada do mesmo aluno."""
    motivo_alteracao = baker.make(
        "MotivoAlteracaoUE",
        nome="Dieta Especial - Recreio nas Férias",
        descricao="Solicitação para recreio nas férias",
    )

    escola_destino = baker.make(
        "Escola",
        nome="EMEF DESTINO RECREIO",
        codigo_eol="999999",
        lote=escola.lote,
        diretoria_regional=escola.diretoria_regional,
        tipo_gestao=escola.tipo_gestao,
    )

    dieta_alteracao = baker.make(
        SolicitacaoDietaEspecial,
        aluno=aluno_teste,
        rastro_escola=escola,
        escola_destino=escola_destino,
        tipo_solicitacao=SolicitacaoDietaEspecial.ALTERACAO_UE,
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        ativo=True,
        dieta_alterada=dieta_comum_autorizada,
        motivo_alteracao_ue=motivo_alteracao,
        classificacao=classificacoes_fixture[0],
        nome_completo_pescritor="Dr. Roberto Médico Silva",
        registro_funcional_pescritor="CRM123",
        registro_funcional_nutricionista="CRN987654",
        observacoes="Aluno com alergia severa a laticínios",
        informacoes_adicionais="Informações adicionais sobre a dieta",
        protocolo_padrao=protocolo_padrao_fixture,
        nome_protocolo=protocolo_padrao_fixture.nome_protocolo,
        orientacoes_gerais="Evitar contato cruzado com derivados de leite",
        data_inicio=datetime.date.today(),
        data_termino=datetime.date.today() + datetime.timedelta(days=15),
        caracteristicas_do_alimento="Alimentos sem lactose",
    )
    # Adiciona as mesmas alergias/intolerâncias da dieta comum
    dieta_alteracao.alergias_intolerancias.set([alergias_intolerancias_fixture[0]])
    return dieta_alteracao


class TestDietaOriginalAlteradaSyncUpdate:
    """
    Testa se ao autorizar uma solicitação de dieta especial do tipo COMUM,
    a solicitação de ALTERACAO_UE do mesmo aluno também é atualizada com os mesmos dados.
    """

    def test_autoriza_dieta_comum_atualiza_dieta_alteracao_ue(
        self,
        client_autenticado_protocolo_dieta,
        dieta_comum_autorizada,
        dieta_alteracao_ue_autorizada,
        alergias_intolerancias_fixture,
        classificacoes_fixture,
        protocolo_padrao_fixture,
        substituicoes_fixture,
        alimentos_fixture,
        produtos_fixture,
    ):
        """
        Testa se ao autorizar uma dieta COMUM com novos dados,
        a dieta ALTERACAO_UE autorizada do mesmo aluno é atualizada com os mesmos dados.
        """
        # Muda o status da dieta comum para CODAE_A_AUTORIZAR para poder autorizar novamente
        dieta_comum_autorizada.status = DietaEspecialWorkflow.CODAE_A_AUTORIZAR
        dieta_comum_autorizada.ativo = False
        dieta_comum_autorizada.save()

        # Prepara o payload com novos dados para autorização
        novo_protocolo = baker.make(
            ProtocoloPadraoDietaEspecial,
            nome_protocolo="ALERGIA - OVO E DERIVADOS",
            status="LIBERADO",
        )

        payload_autorizacao = {
            "classificacao": classificacoes_fixture[
                1
            ].id,  # Mudando de Tipo A para Tipo B
            "alergias_intolerancias": [
                alergias_intolerancias_fixture[1].id,  # Alergia a Ovo
                alergias_intolerancias_fixture[2].id,  # Alergia a Soja
            ],
            "registro_funcional_nutricionista": "CRN111222 - Nutricionista Atualizado CODAE",
            "substituicoes": substituicoes_fixture,  # Adicionado campo obrigatório
            "informacoes_adicionais": "Informações adicionais ATUALIZADAS",
            "protocolo_padrao": str(novo_protocolo.uuid),
            "nome_protocolo": novo_protocolo.nome_protocolo,
            "orientacoes_gerais": "Orientações gerais ATUALIZADAS - Evitar ovo em todas as formas",
            "caracteristicas_do_alimento": "Características ATUALIZADAS dos alimentos",
        }

        # Faz a requisição PATCH para autorizar a dieta comum com os novos dados
        url = f"/solicitacoes-dieta-especial/{dieta_comum_autorizada.uuid}/autorizar/"
        response = client_autenticado_protocolo_dieta.patch(
            url,
            data=payload_autorizacao,
            content_type="application/json",
        )

        # Verifica se a requisição foi bem-sucedida
        assert response.status_code == status.HTTP_200_OK
        assert "Autorização de Dieta Especial realizada com sucesso!" in str(
            response.data
        )

        # Recarrega as dietas do banco de dados
        dieta_comum_autorizada.refresh_from_db()
        dieta_alteracao_ue_autorizada.refresh_from_db()

        # VERIFICA SE A DIETA COMUM FOI ATUALIZADA
        assert dieta_comum_autorizada.status == DietaEspecialWorkflow.CODAE_AUTORIZADO
        assert dieta_comum_autorizada.ativo is True
        assert dieta_comum_autorizada.classificacao.id == classificacoes_fixture[1].id
        assert (
            dieta_comum_autorizada.registro_funcional_nutricionista
            == "CRN111222 - Nutricionista Atualizado CODAE"
        )
        assert (
            dieta_comum_autorizada.informacoes_adicionais
            == "Informações adicionais ATUALIZADAS"
        )
        assert str(dieta_comum_autorizada.protocolo_padrao.uuid) == str(
            novo_protocolo.uuid
        )
        assert dieta_comum_autorizada.nome_protocolo == novo_protocolo.nome_protocolo
        assert (
            dieta_comum_autorizada.orientacoes_gerais
            == "Orientações gerais ATUALIZADAS - Evitar ovo em todas as formas"
        )
        assert (
            dieta_comum_autorizada.caracteristicas_do_alimento
            == "Características ATUALIZADAS dos alimentos"
        )

        # Verifica alergias/intolerâncias da dieta comum
        alergias_dieta_comum = set(
            dieta_comum_autorizada.alergias_intolerancias.values_list("id", flat=True)
        )
        assert alergias_dieta_comum == {
            alergias_intolerancias_fixture[1].id,
            alergias_intolerancias_fixture[2].id,
        }

        # VERIFICA SE A DIETA DE ALTERACAO_UE TAMBÉM FOI ATUALIZADA COM OS MESMOS DADOS
        assert (
            dieta_alteracao_ue_autorizada.status
            == DietaEspecialWorkflow.CODAE_AUTORIZADO
        )
        assert dieta_alteracao_ue_autorizada.ativo is False
        assert (
            dieta_alteracao_ue_autorizada.classificacao.id
            == classificacoes_fixture[1].id
        )
        assert (
            dieta_alteracao_ue_autorizada.registro_funcional_nutricionista
            == "CRN111222 - Nutricionista Atualizado CODAE"
        )
        assert (
            dieta_alteracao_ue_autorizada.informacoes_adicionais
            == "Informações adicionais ATUALIZADAS"
        )
        assert str(dieta_alteracao_ue_autorizada.protocolo_padrao.uuid) == str(
            novo_protocolo.uuid
        )
        assert (
            dieta_alteracao_ue_autorizada.nome_protocolo
            == novo_protocolo.nome_protocolo
        )
        assert (
            dieta_alteracao_ue_autorizada.orientacoes_gerais
            == "Orientações gerais ATUALIZADAS - Evitar ovo em todas as formas"
        )
        assert (
            dieta_alteracao_ue_autorizada.caracteristicas_do_alimento
            == "Características ATUALIZADAS dos alimentos"
        )

        # Verifica alergias/intolerâncias da dieta de alteração UE
        alergias_dieta_alteracao = set(
            dieta_alteracao_ue_autorizada.alergias_intolerancias.values_list(
                "id", flat=True
            )
        )
        assert alergias_dieta_alteracao == {
            alergias_intolerancias_fixture[1].id,
            alergias_intolerancias_fixture[2].id,
        }

        # Verifica que a dieta de ALTERACAO_UE mantém seus campos específicos
        assert (
            dieta_alteracao_ue_autorizada.tipo_solicitacao
            == SolicitacaoDietaEspecial.ALTERACAO_UE
        )
        assert dieta_alteracao_ue_autorizada.dieta_alterada == dieta_comum_autorizada
        assert dieta_alteracao_ue_autorizada.motivo_alteracao_ue is not None
