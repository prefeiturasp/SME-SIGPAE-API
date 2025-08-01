import pytest

from sme_sigpae_api.recebimento.models import (
    QuestaoConferencia,
    QuestaoFichaRecebimento,
)

pytestmark = pytest.mark.django_db


def test_questao_conferencia_instance_model(questao_conferencia_factory):
    questao_conferencia = questao_conferencia_factory.create()
    assert isinstance(questao_conferencia, QuestaoConferencia)


def test_questao_conferencia_srt_model(questao_conferencia_factory):
    questao_conferencia = questao_conferencia_factory.create(
        questao="IDENTIFICACÃO DO PRODUTO"
    )
    assert questao_conferencia.__str__() == "IDENTIFICACÃO DO PRODUTO"


def test_questao_conferencia_meta_modelo(questao_conferencia_factory):
    questao_conferencia = questao_conferencia_factory.create()
    assert questao_conferencia._meta.verbose_name == "Questão para Conferência"
    assert questao_conferencia._meta.verbose_name_plural == "Questões para Conferência"


def test_model_ficha_recebimento_meta(ficha_de_recebimento_factory):
    ficha_recebimento = ficha_de_recebimento_factory.create()

    assert ficha_recebimento._meta.verbose_name == "Ficha de Recebimento"
    assert ficha_recebimento._meta.verbose_name_plural == "Fichas de Recebimentos"


def test_model_ficha_recebimento_str(ficha_de_recebimento_factory):
    ficha_recebimento = ficha_de_recebimento_factory.create()

    assert (
        str(ficha_recebimento)
        == f"Ficha de Recebimento - {str(ficha_recebimento.etapa)}"
    )


def test_model_arquivo_ficha_recebimento_str(arquivo_ficha_de_recebimento_factory):
    arquivo = arquivo_ficha_de_recebimento_factory(nome="arquivo-teste.pdf")

    assert str(arquivo) == f"{arquivo.nome} - {arquivo.ficha_recebimento}"


def test_questao_ficha_recebimento_instance_model(questao_ficha_recebimento_factory):
    questao_ficha_recebimento = questao_ficha_recebimento_factory.create()
    assert isinstance(questao_ficha_recebimento, QuestaoFichaRecebimento)


def test_questao_ficha_recebimento_srt_model(questao_ficha_recebimento_factory):
    questao_ficha_recebimento = questao_ficha_recebimento_factory.create()
    assert (
        questao_ficha_recebimento.__str__()
        == f"{questao_ficha_recebimento.questao_conferencia.questao} - {questao_ficha_recebimento.ficha_recebimento}"
    )


def test_questao_ficha_recebimento_meta_modelo(questao_ficha_recebimento_factory):
    questao_ficha_recebimento = questao_ficha_recebimento_factory.create()
    assert (
        questao_ficha_recebimento._meta.verbose_name
        == "Questão por Ficha de Recebimento"
    )
    assert (
        questao_ficha_recebimento._meta.verbose_name_plural
        == "Questões por Fichas de Recebimento"
    )


def test_ocorrencia_ficha_recebimento_str(
    ocorrencia_ficha_recebimento_factory, ficha_de_recebimento
):
    """Testa a representação em string do modelo."""
    ocorrencia = ocorrencia_ficha_recebimento_factory.create(
        ficha_recebimento=ficha_de_recebimento, tipo="FALTA"
    )
    assert str(ocorrencia) == f"{ficha_de_recebimento} - Falta"


def test_ocorrencia_ficha_recebimento_meta(ocorrencia_ficha_recebimento_factory):
    """Testa os metadados do modelo."""
    ocorrencia = ocorrencia_ficha_recebimento_factory.create()
    assert ocorrencia._meta.verbose_name == "Ocorrência da Ficha de Recebimento"
    assert (
        ocorrencia._meta.verbose_name_plural == "Ocorrências das Fichas de Recebimento"
    )
    assert ocorrencia._meta.ordering == ["criado_em"]


def test_ocorrencia_ficha_recebimento_fields(ocorrencia_ficha_recebimento_factory):
    """Testa a criação de uma instância com todos os campos."""
    ocorrencia = ocorrencia_ficha_recebimento_factory.create(
        tipo="RECUSA",
        relacao="TOTAL",
        numero_nota="NF12345",
        quantidade="10 unidades",
        descricao="Produto recusado",
    )

    assert ocorrencia.tipo == "RECUSA"
    assert ocorrencia.relacao == "TOTAL"
    assert ocorrencia.numero_nota == "NF12345"
    assert ocorrencia.quantidade == "10 unidades"
    assert ocorrencia.descricao == "Produto recusado"
