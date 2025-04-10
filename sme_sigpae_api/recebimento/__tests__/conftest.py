from datetime import date, timedelta

import pytest
from faker import Faker

from sme_sigpae_api.dados_comuns.fluxo_status import (
    DocumentoDeRecebimentoWorkflow,
    FichaTecnicaDoProdutoWorkflow,
)
from sme_sigpae_api.pre_recebimento.fixtures.factories.cronograma_factory import (
    CronogramaFactory,
    EtapasDoCronogramaFactory,
)
from sme_sigpae_api.pre_recebimento.fixtures.factories.documentos_de_recebimento_factory import (
    DocumentoDeRecebimentoFactory,
)
from sme_sigpae_api.pre_recebimento.fixtures.factories.ficha_tecnica_do_produto_factory import (
    FichaTecnicaFactory,
)
from sme_sigpae_api.recebimento.fixtures.factories.ficha_de_recebimento_factory import (
    FichaDeRecebimentoFactory,
)
from sme_sigpae_api.recebimento.fixtures.factories.questao_conferencia_factory import (
    QuestaoConferenciaFactory,
)
from sme_sigpae_api.recebimento.fixtures.factories.questao_ficha_recebimento_factory import (
    QuestaoFichaRecebimentoFactory,
)
from sme_sigpae_api.recebimento.fixtures.factories.questoes_por_produto_factory import (
    QuestoesPorProdutoFactory,
)
from sme_sigpae_api.recebimento.models import (
    QuestaoConferencia,
    QuestaoFichaRecebimento,
)

fake = Faker("pt_BR")


@pytest.fixture
def questoes_conferencia(questao_conferencia_factory):
    return questao_conferencia_factory.create_batch(
        size=10,
        tipo_questao=[
            QuestaoConferencia.TIPO_QUESTAO_PRIMARIA,
            QuestaoConferencia.TIPO_QUESTAO_SECUNDARIA,
        ],
    )


@pytest.fixture
def payload_create_questoes_por_produto(
    ficha_tecnica_factory,
    questoes_conferencia,
):
    questoes = [str(q.uuid) for q in questoes_conferencia]

    return {
        "ficha_tecnica": str(
            ficha_tecnica_factory(status=FichaTecnicaDoProdutoWorkflow.APROVADA).uuid
        ),
        "questoes_primarias": questoes,
        "questoes_secundarias": questoes,
    }


@pytest.fixture
def payload_update_questoes_por_produto(questoes_conferencia):
    questoes = [str(q.uuid) for q in questoes_conferencia]

    return {
        "questoes_primarias": questoes,
        "questoes_secundarias": questoes,
    }


@pytest.fixture
def payload_ficha_recebimento_rascunho(
    etapas_do_cronograma_factory,
    documento_de_recebimento_factory,
    arquivo_pdf_base64,
):
    etapa = etapas_do_cronograma_factory()
    docs_recebimento = documento_de_recebimento_factory.create_batch(
        size=3,
        cronograma=etapa.cronograma,
        status=DocumentoDeRecebimentoWorkflow.APROVADO,
    )

    questao = QuestaoConferenciaFactory(
        tipo_questao=QuestaoConferencia.TIPO_QUESTAO_PRIMARIA
    )

    return {
        "etapa": str(etapa.uuid),
        "data_entrega": str(date.today() + timedelta(days=10)),
        "documentos_recebimento": [str(doc.uuid) for doc in docs_recebimento],
        "lote_fabricante_de_acordo": True,
        "lote_fabricante_divergencia": "",
        "data_fabricacao_de_acordo": True,
        "data_fabricacao_divergencia": "",
        "data_validade_de_acordo": True,
        "data_validade_divergencia": "",
        "numero_lote_armazenagem": str(fake.random_number(digits=10)),
        "numero_paletes": str(fake.random_number(digits=3)),
        "peso_embalagem_primaria_1": str(fake.random_number(digits=3)),
        "peso_embalagem_primaria_2": str(fake.random_number(digits=3)),
        "peso_embalagem_primaria_3": str(fake.random_number(digits=3)),
        "peso_embalagem_primaria_4": str(fake.random_number(digits=3)),
        "veiculos": [
            {
                "numero": "Veiculo 1",
                "temperatura_recebimento": str(fake.random_number(digits=3)),
                "temperatura_produto": str(fake.random_number(digits=3)),
                "placa": str(fake.random_number(digits=7)),
                "lacre": str(fake.random_number(digits=7)),
                "numero_sif_sisbi_sisp": str(fake.random_number(digits=10)),
                "numero_nota_fiscal": str(fake.random_number(digits=44)),
                "quantidade_nota_fiscal": "1234",
                "embalagens_nota_fiscal": "12",
                "quantidade_recebida": "1234",
                "embalagens_recebidas": "12",
                "estado_higienico_adequado": True,
                "termografo": True,
            },
            {
                "numero": "Veiculo 2",
                "temperatura_recebimento": str(fake.random_number(digits=3)),
                "temperatura_produto": str(fake.random_number(digits=3)),
                "placa": str(fake.random_number(digits=7)),
                "lacre": str(fake.random_number(digits=7)),
                "numero_sif_sisbi_sisp": str(fake.random_number(digits=10)),
                "numero_nota_fiscal": str(fake.random_number(digits=44)),
                "quantidade_nota_fiscal": "1234",
                "embalagens_nota_fiscal": "12",
                "quantidade_recebida": "1234",
                "embalagens_recebidas": "12",
                "estado_higienico_adequado": True,
                "termografo": True,
            },
        ],
        "sistema_vedacao_embalagem_secundaria": fake.text(max_nb_chars=100),
        "observacao": fake.text(max_nb_chars=100),
        "arquivos": [
            {"arquivo": arquivo_pdf_base64, "nome": "Arquivo1.pdf"},
            {"arquivo": arquivo_pdf_base64, "nome": "Arquivo2.pdf"},
        ],
        "questoes": [
            {
                "questao_conferencia": str(questao.uuid),
                "resposta": False,
                "tipo_questao": "PRIMARIA",
            }
        ],
    }


@pytest.fixture
def questoes_por_produto():
    ficha_tecnica = FichaTecnicaFactory()
    questoes_produto = QuestoesPorProdutoFactory(ficha_tecnica=ficha_tecnica)
    questao_primaria = QuestaoConferenciaFactory(
        tipo_questao=QuestaoConferencia.TIPO_QUESTAO_PRIMARIA
    )
    questao_secundaria = QuestaoConferenciaFactory(
        tipo_questao=QuestaoConferencia.TIPO_QUESTAO_SECUNDARIA
    )
    questoes_produto.questoes_primarias.add(questao_primaria)
    questoes_produto.questoes_secundarias.add(questao_secundaria)
    return questoes_produto


@pytest.fixture
def questao_ficha_recebimento():
    return QuestaoFichaRecebimentoFactory()


@pytest.fixture
def questao_conferencia():
    return QuestaoConferenciaFactory(
        tipo_questao=QuestaoConferencia.TIPO_QUESTAO_PRIMARIA
    )


@pytest.fixture
def ficha_recebimento():
    return FichaDeRecebimentoFactory()


@pytest.fixture
def etapa_cronograma():
    return EtapasDoCronogramaFactory()


@pytest.fixture
def ficha_recebimento_rascunho(etapa_cronograma):
    documento = DocumentoDeRecebimentoFactory(status="APROVADO")
    questao = QuestaoConferenciaFactory()

    return {
        "etapa": str(etapa_cronograma.uuid),
        "data_entrega": "2025-04-10",
        "documentos_recebimento": [str(documento.uuid)],
        "veiculos": [{"numero": "ABC1D23"}],
        "questoes": [
            {
                "questao_conferencia": str(questao.uuid),
                "resposta": True,
                "tipo_questao": QuestaoFichaRecebimento.TIPO_QUESTAO_PRIMARIA,
            }
        ],
    }


@pytest.fixture
def cronograma():
    return CronogramaFactory()


@pytest.fixture
def cronograma_completo(questoes_por_produto):
    return CronogramaFactory(ficha_tecnica=questoes_por_produto.ficha_tecnica)
