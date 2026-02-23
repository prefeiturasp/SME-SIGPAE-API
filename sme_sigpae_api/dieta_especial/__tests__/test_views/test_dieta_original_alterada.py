import datetime

import pytest
from rest_framework import status

from sme_sigpae_api.dados_comuns.fluxo_status import DietaEspecialWorkflow
from sme_sigpae_api.dieta_especial.fixtures.factories.dieta_especial_base_factory import (
    AlergiaIntoleranciaFactory,
    AlimentoFactory,
    ClassificacaoDietaFactory,
    MotivoAlteracaoUEFactory,
    ProtocoloPadraoDietaEspecialFactory,
    SolicitacaoDietaEspecialFactory,
)
from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    AlunoFactory,
    EscolaFactory,
)
from sme_sigpae_api.produto.fixtures.factories.produto_factory import ProdutoFactory

pytestmark = pytest.mark.django_db


class TestDietaOriginalAlteradaSyncUpdate:
    """
    Testa se ao autorizar uma solicitação de dieta especial do tipo COMUM,
    a solicitação de ALTERACAO_UE do mesmo aluno também é atualizada com os mesmos dados.
    """

    def setup(self, escola):
        """Configura os modelos de teste usando factories.

        Cria três dietas:
        1. dieta_comum_autorizada: dieta COMUM já autorizada (CODAE_AUTORIZADO)
        2. dieta_alteracao_ue_autorizada: dieta ALTERACAO_UE já autorizada, vinculada à dieta_comum_autorizada
        3. dieta_nova_a_autorizar: nova dieta COMUM pendente de autorização (CODAE_A_AUTORIZAR)
        """
        alergia_leite = AlergiaIntoleranciaFactory.create(descricao="Alergia a Leite")
        alergia_ovo = AlergiaIntoleranciaFactory.create(descricao="Alergia a Ovo")
        alergia_soja = AlergiaIntoleranciaFactory.create(descricao="Alergia a Soja")

        tipo_a = ClassificacaoDietaFactory.create(nome="Tipo A")
        tipo_b = ClassificacaoDietaFactory.create(nome="Tipo B")
        tipo_a_enteral = ClassificacaoDietaFactory.create(nome="Tipo A Enteral")

        protocolo_padrao = ProtocoloPadraoDietaEspecialFactory.create(
            nome_protocolo="ALERGIA - LEITE E DERIVADOS",
            status="LIBERADO",
        )

        alimentos = [AlimentoFactory.create() for _ in range(6)]
        produtos = [ProdutoFactory.create() for _ in range(6)]

        substituicoes = []
        ids_produtos = [p.uuid for p in produtos]
        for i in range(4):
            substituicoes.append(
                {
                    "alimento": alimentos[i % len(alimentos)].id,
                    "tipo": "I" if i % 2 == 0 else "S",
                    "substitutos": ids_produtos[: min(3, len(ids_produtos))],
                }
            )

        aluno_teste = AlunoFactory(
            nome="João da Silva Santos",
            codigo_eol="7891234",
            data_nascimento="2015-05-10",
            escola=escola,
        )

        dieta_comum_autorizada = SolicitacaoDietaEspecialFactory.create(
            aluno=aluno_teste,
            rastro_escola=escola,
            escola_destino=escola,
            tipo_solicitacao=SolicitacaoDietaEspecial.COMUM,
            status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
            ativo=True,
            classificacao=tipo_a,
            nome_completo_pescritor="Dr. Roberto Médico Silva",
            registro_funcional_pescritor="CRM123",
            registro_funcional_nutricionista="CRN987654",
            observacoes="Aluno com alergia severa a laticínios",
            informacoes_adicionais="Informações adicionais sobre a dieta",
            protocolo_padrao=protocolo_padrao,
            nome_protocolo=protocolo_padrao.nome_protocolo,
            orientacoes_gerais="Evitar contato cruzado com derivados de leite",
            data_inicio=datetime.date.today(),
            caracteristicas_do_alimento="Alimentos sem lactose",
        )
        dieta_comum_autorizada.alergias_intolerancias.set([alergia_leite])

        motivo_alteracao = MotivoAlteracaoUEFactory.create(
            nome="Dieta Especial - Recreio nas Férias",
            descricao="Solicitação para recreio nas férias",
        )

        escola_destino = EscolaFactory.create(
            nome="EMEF DESTINO RECREIO",
            codigo_eol="999999",
            lote=escola.lote,
            diretoria_regional=escola.diretoria_regional,
            tipo_gestao=escola.tipo_gestao,
        )

        dieta_alteracao_ue_autorizada = SolicitacaoDietaEspecialFactory.create(
            aluno=aluno_teste,
            rastro_escola=escola,
            escola_destino=escola_destino,
            tipo_solicitacao=SolicitacaoDietaEspecial.ALTERACAO_UE,
            status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
            ativo=False,  # Dieta de alteração UE não fica ativa, apenas a COMUM
            dieta_alterada=dieta_comum_autorizada,
            motivo_alteracao_ue=motivo_alteracao,
            classificacao=tipo_a,
            nome_completo_pescritor="Dr. Roberto Médico Silva",
            registro_funcional_pescritor="CRM123",
            registro_funcional_nutricionista="CRN987654",
            observacoes="Aluno com alergia severa a laticínios",
            informacoes_adicionais="Informações adicionais sobre a dieta",
            protocolo_padrao=protocolo_padrao,
            nome_protocolo=protocolo_padrao.nome_protocolo,
            orientacoes_gerais="Evitar contato cruzado com derivados de leite",
            data_inicio=datetime.date.today(),
            data_termino=datetime.date.today() + datetime.timedelta(days=15),
            caracteristicas_do_alimento="Alimentos sem lactose",
        )
        dieta_alteracao_ue_autorizada.alergias_intolerancias.set([alergia_leite])

        # Cria uma nova dieta COMUM pendente de autorização (a ser testada)
        dieta_nova_a_autorizar = SolicitacaoDietaEspecialFactory.create(
            aluno=aluno_teste,
            rastro_escola=escola,
            escola_destino=escola,
            tipo_solicitacao=SolicitacaoDietaEspecial.COMUM,
            status=DietaEspecialWorkflow.CODAE_A_AUTORIZAR,
            ativo=False,
            classificacao=tipo_a,
            nome_completo_pescritor="Dr. Roberto Médico Silva",
            registro_funcional_pescritor="CRM123",
            registro_funcional_nutricionista="CRN987654",
            observacoes="Aluno com alergia severa a laticínios",
            informacoes_adicionais="Informações adicionais sobre a dieta",
            protocolo_padrao=protocolo_padrao,
            nome_protocolo=protocolo_padrao.nome_protocolo,
            orientacoes_gerais="Evitar contato cruzado com derivados de leite",
            data_inicio=datetime.date.today(),
            caracteristicas_do_alimento="Alimentos sem lactose",
        )
        dieta_nova_a_autorizar.alergias_intolerancias.set([alergia_leite])

        return {
            "alergia_leite": alergia_leite,
            "alergia_ovo": alergia_ovo,
            "alergia_soja": alergia_soja,
            "tipo_a": tipo_a,
            "tipo_b": tipo_b,
            "tipo_a_enteral": tipo_a_enteral,
            "protocolo_padrao": protocolo_padrao,
            "alimentos": alimentos,
            "produtos": produtos,
            "substituicoes": substituicoes,
            "aluno_teste": aluno_teste,
            "dieta_comum_autorizada": dieta_comum_autorizada,
            "dieta_nova_a_autorizar": dieta_nova_a_autorizar,
            "motivo_alteracao": motivo_alteracao,
            "escola_destino": escola_destino,
            "dieta_alteracao_ue_autorizada": dieta_alteracao_ue_autorizada,
        }

    def test_autoriza_dieta_comum_atualiza_dieta_alteracao_ue(
        self,
        client_autenticado_protocolo_dieta,
        escola,
    ):
        """
        Testa se ao autorizar uma NOVA solicitação de dieta especial do tipo COMUM,
        a solicitação de ALTERACAO_UE autorizada do mesmo aluno é atualizada com os mesmos dados.

        Cenário:
        - Existe uma dieta COMUM já autorizada (dieta_comum_autorizada)
        - Existe uma dieta ALTERACAO_UE já autorizada (dieta_alteracao_ue_autorizada), vinculada à dieta_comum_autorizada
        - Uma NOVA dieta COMUM é criada (dieta_nova_a_autorizar) com status CODAE_A_AUTORIZAR
        - Ao autorizar a nova dieta com dados atualizados, a dieta ALTERACAO_UE também deve ser atualizada
        """
        data = self.setup(escola)
        alergia_ovo = data["alergia_ovo"]
        alergia_soja = data["alergia_soja"]
        tipo_b = data["tipo_b"]
        substituicoes = data["substituicoes"]
        dieta_comum_autorizada = data["dieta_comum_autorizada"]
        dieta_nova_a_autorizar = data["dieta_nova_a_autorizar"]
        dieta_alteracao_ue_autorizada = data["dieta_alteracao_ue_autorizada"]

        novo_protocolo = ProtocoloPadraoDietaEspecialFactory(
            nome_protocolo="ALERGIA - OVO E DERIVADOS",
            status="LIBERADO",
        )

        payload_autorizacao = {
            "classificacao": tipo_b.id,  # Mudando de Tipo A para Tipo B
            "alergias_intolerancias": [
                alergia_ovo.id,  # Alergia a Ovo
                alergia_soja.id,  # Alergia a Soja
            ],
            "registro_funcional_nutricionista": "CRN111222 - Nutricionista Atualizado CODAE",
            "substituicoes": substituicoes,
            "informacoes_adicionais": "Informações adicionais ATUALIZADAS",
            "protocolo_padrao": str(novo_protocolo.uuid),
            "nome_protocolo": novo_protocolo.nome_protocolo,
            "orientacoes_gerais": "Orientações gerais ATUALIZADAS - Evitar ovo em todas as formas",
            "caracteristicas_do_alimento": "Características ATUALIZADAS dos alimentos",
        }

        url = f"/solicitacoes-dieta-especial/{dieta_nova_a_autorizar.uuid}/autorizar/"
        response = client_autenticado_protocolo_dieta.patch(
            url,
            data=payload_autorizacao,
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "Autorização de Dieta Especial realizada com sucesso!" in str(
            response.data
        )

        dieta_nova_a_autorizar.refresh_from_db()
        dieta_alteracao_ue_autorizada.refresh_from_db()

        # VERIFICA SE A NOVA DIETA COMUM FOI AUTORIZADA
        assert dieta_nova_a_autorizar.status == DietaEspecialWorkflow.CODAE_AUTORIZADO
        assert dieta_nova_a_autorizar.ativo is True
        assert dieta_nova_a_autorizar.classificacao.id == tipo_b.id
        assert (
            dieta_nova_a_autorizar.registro_funcional_nutricionista
            == "CRN111222 - Nutricionista Atualizado CODAE"
        )
        assert (
            dieta_nova_a_autorizar.informacoes_adicionais
            == "Informações adicionais ATUALIZADAS"
        )
        assert str(dieta_nova_a_autorizar.protocolo_padrao.uuid) == str(
            novo_protocolo.uuid
        )
        assert dieta_nova_a_autorizar.nome_protocolo == novo_protocolo.nome_protocolo
        assert (
            dieta_nova_a_autorizar.orientacoes_gerais
            == "Orientações gerais ATUALIZADAS - Evitar ovo em todas as formas"
        )
        assert (
            dieta_nova_a_autorizar.caracteristicas_do_alimento
            == "Características ATUALIZADAS dos alimentos"
        )

        # Verifica alergias/intolerâncias da nova dieta
        alergias_dieta_nova = set(
            dieta_nova_a_autorizar.alergias_intolerancias.values_list("id", flat=True)
        )
        assert alergias_dieta_nova == {
            alergia_ovo.id,
            alergia_soja.id,
        }

        # VERIFICA SE A DIETA DE ALTERACAO_UE TAMBÉM FOI ATUALIZADA COM OS MESMOS DADOS DA NOVA DIETA
        assert (
            dieta_alteracao_ue_autorizada.status
            == DietaEspecialWorkflow.CODAE_AUTORIZADO
        )
        assert dieta_alteracao_ue_autorizada.ativo is False
        assert dieta_alteracao_ue_autorizada.classificacao.id == tipo_b.id
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
            alergia_ovo.id,
            alergia_soja.id,
        }

        # Verifica que a dieta de ALTERACAO_UE mantém seus campos específicos
        assert (
            dieta_alteracao_ue_autorizada.tipo_solicitacao
            == SolicitacaoDietaEspecial.ALTERACAO_UE
        )
        assert dieta_alteracao_ue_autorizada.dieta_alterada == dieta_comum_autorizada
        assert dieta_alteracao_ue_autorizada.motivo_alteracao_ue is not None
