import pytest
from faker import Faker

from sme_sigpae_api.dados_comuns.fluxo_status import CronogramaAlteracaoWorkflow

from ..cronograma_entrega.models import (
    Cronograma,
    SolicitacaoAlteracaoCronograma,
    EtapasDoCronograma,
    ProgramacaoDoRecebimentoDoCronograma,
)
from ..documento_recebimento.models import DocumentoDeRecebimento, TipoDeDocumentoDeRecebimento
from ..qualidade.models import Laboratorio, TipoEmbalagemQld
from ..base.models import UnidadeMedida
from ..layout_embalagem.models import LayoutDeEmbalagem, TipoDeEmbalagemDeLayout

pytestmark = pytest.mark.django_db

fake = Faker("pt_BR")

def test_cronograma_instance_model(cronograma):
    assert isinstance(cronograma, Cronograma)


def test_cronograma_srt_model(cronograma):
    assert cronograma.__str__() == "Cronograma: 001/2022A - Status: Rascunho"


def test_cronograma_meta_modelo(cronograma):
    assert cronograma._meta.verbose_name == "Cronograma"
    assert cronograma._meta.verbose_name_plural == "Cronogramas"


def test_etapas_do_cronograma_instance_model(etapa):
    assert isinstance(etapa, EtapasDoCronograma)


def test_etapas_do_cronograma_srt_model(etapa):
    assert (
        etapa.__str__()
        == f"Etapa {etapa.etapa} - {etapa.parte} - Cronograma {etapa.cronograma.numero}"
    )

    etapa.etapa = None
    etapa.save()
    assert str(etapa) == f"Etapa do Cronograma {etapa.cronograma.numero}"

    etapa.cronograma = None
    etapa.save()
    assert str(etapa) == "Etapa sem Cronograma"


def test_etapas_do_cronograma_meta_modelo(etapa):
    assert etapa._meta.verbose_name == "Etapa do Cronograma"
    assert etapa._meta.verbose_name_plural == "Etapas dos Cronogramas"


def test_programacao_de_recebimento_do_cronograma_instance_model(programacao):
    assert isinstance(programacao, ProgramacaoDoRecebimentoDoCronograma)


def test_programacao_de_recebimento_do_cronograma_srt_model(programacao):
    assert programacao.__str__() == "01/01/2022"


def test_programacao_de_recebimento_do_cronograma_meta_modelo(programacao):
    assert programacao._meta.verbose_name == "Programação do Recebimento do Cromograma"
    assert (
        programacao._meta.verbose_name_plural
        == "Programações dos Recebimentos dos Cromogramas"
    )


def test_laboratorio_instance_model(laboratorio):
    assert isinstance(laboratorio, Laboratorio)


def test_laboratorio_srt_model(laboratorio):
    assert laboratorio.__str__() == "Labo Test"


def test_laboratorio_meta_modelo(laboratorio):
    assert laboratorio._meta.verbose_name == "Laboratório"
    assert laboratorio._meta.verbose_name_plural == "Laboratórios"


def test_embalagem_instance_model(tipo_emabalagem_qld):
    assert isinstance(tipo_emabalagem_qld, TipoEmbalagemQld)


def test_embalagem_srt_model(tipo_emabalagem_qld):
    assert tipo_emabalagem_qld.__str__() == "CAIXA"


def test_embalagem_meta_modelo(tipo_emabalagem_qld):
    assert tipo_emabalagem_qld._meta.verbose_name == "Tipo de Embalagem (Qualidade)"
    assert (
        tipo_emabalagem_qld._meta.verbose_name_plural
        == "Tipos de Embalagens (Qualidade)"
    )


def test_unidade_medida_model(unidade_medida_logistica):
    """Deve possuir os campos nome e abreviacao."""
    assert unidade_medida_logistica.nome == "UNIDADE TESTE"
    assert unidade_medida_logistica.abreviacao == "ut"


def test_unidade_medida_model_str(unidade_medida_logistica):
    """Deve ser igual ao atributo nome."""
    assert str(unidade_medida_logistica) == unidade_medida_logistica.nome


def test_unidade_medida_model_save():
    """Deve converter atributo nome para caixa alta e atributo abreviacao para caixa baixa."""
    data = {"nome": "uma unidade qualquer", "abreviacao": "UMQ"}
    obj = UnidadeMedida.objects.create(**data)

    assert obj.nome.isupper()
    assert obj.abreviacao.islower()


def test_laboratorio_model_str(laboratorio):
    assert str(laboratorio) == laboratorio.nome


def test_programacao_recebimento_cronograma_model_str(programacao):
    assert str(programacao) == programacao.data_programada

    programacao.data_programada = ""
    programacao.save()
    assert str(programacao) == str(programacao.id)


def test_solicitacao_alteracao_cronograma_queryset_em_analise(
    solicitacao_cronograma_em_analise,
):
    qs = SolicitacaoAlteracaoCronograma.objects.em_analise()
    assert qs.count() == 1
    assert qs.first() == solicitacao_cronograma_em_analise


def test_solicitacao_alteracao_cronograma_queryset_filtrar_por_status(
    solicitacao_cronograma_em_analise,
    solicitacao_cronograma_ciente,
    solicitacao_cronograma_aprovado_dilog_abastecimento,
    ficha_tecnica_perecivel_enviada_para_analise,
    empresa,
):
    qs = SolicitacaoAlteracaoCronograma.objects.filtrar_por_status(
        status=[
            CronogramaAlteracaoWorkflow.EM_ANALISE,
            CronogramaAlteracaoWorkflow.APROVADO_DILOG_ABASTECIMENTO,
        ]
    )
    assert qs.count() == 2
    assert solicitacao_cronograma_em_analise in qs
    assert solicitacao_cronograma_aprovado_dilog_abastecimento in qs
    assert solicitacao_cronograma_ciente not in qs

    solicitacao_cronograma_em_analise.cronograma.empresa = empresa
    solicitacao_cronograma_em_analise.cronograma.ficha_tecnica = (
        ficha_tecnica_perecivel_enviada_para_analise
    )
    solicitacao_cronograma_em_analise.cronograma.save()

    qs = SolicitacaoAlteracaoCronograma.objects.filtrar_por_status(
        status=[CronogramaAlteracaoWorkflow.EM_ANALISE],
        filtros={"nome_fornecedor": empresa.nome_fantasia},
    )
    assert qs.count() == 1

    qs = SolicitacaoAlteracaoCronograma.objects.filtrar_por_status(
        status=[CronogramaAlteracaoWorkflow.EM_ANALISE],
        filtros={
            "numero_cronograma": solicitacao_cronograma_em_analise.cronograma.numero
        },
    )
    assert qs.count() == 1

    qs = SolicitacaoAlteracaoCronograma.objects.filtrar_por_status(
        status=[CronogramaAlteracaoWorkflow.EM_ANALISE],
        filtros={
            "nome_produto": ficha_tecnica_perecivel_enviada_para_analise.produto.nome
        },
    )
    assert qs.count() == 1


def test_layout_de_embalagem_instance_model(layout_de_embalagem):
    model = layout_de_embalagem
    assert isinstance(model, LayoutDeEmbalagem)
    assert model.ficha_tecnica
    assert model.observacoes


def test_layout_de_embalagem_srt_model(layout_de_embalagem):
    numero_ficha = layout_de_embalagem.ficha_tecnica.numero
    produto_ficha = layout_de_embalagem.ficha_tecnica.produto.nome

    assert (
        str(layout_de_embalagem)
        == f"Layout de Embalagens {numero_ficha} - {produto_ficha}"
    )


def test_layout_de_embalagem_meta_modelo(layout_de_embalagem):
    assert layout_de_embalagem._meta.verbose_name == "Layout de Embalagem"
    assert layout_de_embalagem._meta.verbose_name_plural == "Layouts de Embalagem"


def test_tipo_de_embalagem_instance_model(tipo_de_embalagem_de_layout):
    model = tipo_de_embalagem_de_layout
    assert isinstance(model, TipoDeEmbalagemDeLayout)
    assert model.layout_de_embalagem
    assert model.tipo_embalagem
    assert model.status
    assert model.complemento_do_status


def test_tipo_de_embalagem_srt_model(tipo_de_embalagem_de_layout):
    assert tipo_de_embalagem_de_layout.__str__() == "PRIMARIA - APROVADO"


def test_tipo_de_embalagem_meta_modelo(tipo_de_embalagem_de_layout):
    assert (
        tipo_de_embalagem_de_layout._meta.verbose_name == "Tipo de Embalagem de Layout"
    )
    assert (
        tipo_de_embalagem_de_layout._meta.verbose_name_plural
        == "Tipos de Embalagens de Layout"
    )


def test_documento_de_recebimento_instance_model(documento_de_recebimento_factory):
    documento_de_recebimento = documento_de_recebimento_factory.create()
    model = documento_de_recebimento
    assert isinstance(model, DocumentoDeRecebimento)
    assert model.cronograma
    assert model.numero_laudo


def test_documento_de_recebimento_srt_model(documento_de_recebimento_factory):
    documento = documento_de_recebimento_factory.create()
    assert (
        documento.__str__()
        == f"{documento.cronograma.numero} - Laudo: {documento.numero_laudo}"
    )


def test_documento_de_recebimento_meta_modelo(documento_de_recebimento_factory):
    documento_de_recebimento = documento_de_recebimento_factory.create()
    assert documento_de_recebimento._meta.verbose_name == "Documento de Recebimento"
    assert (
        documento_de_recebimento._meta.verbose_name_plural
        == "Documentos de Recebimento"
    )


def test_tipo_de_documento_de_recebimento_instance_model(
    tipo_de_documento_de_recebimento_factory,
):
    tipo_de_documento = tipo_de_documento_de_recebimento_factory.create(
        descricao_documento=fake.text()
    )
    model = tipo_de_documento
    assert isinstance(model, TipoDeDocumentoDeRecebimento)
    assert model.documento_recebimento
    assert model.tipo_documento
    assert model.descricao_documento


def test_tipo_de_documento_de_recebimento_srt_model(
    tipo_de_documento_de_recebimento_factory,
):
    obj = tipo_de_documento_de_recebimento_factory.create()
    assert (
        obj.__str__()
        == f"{obj.documento_recebimento.cronograma.numero} - {obj.tipo_documento}"
    )


def test_tipo_de_documento_de_recebimento_meta_modelo(
    tipo_de_documento_de_recebimento_factory,
):
    obj = tipo_de_documento_de_recebimento_factory.create()
    assert obj._meta.verbose_name == "Tipo de Documento de Recebimento"
    assert obj._meta.verbose_name_plural == "Tipos de Documentos de Recebimento"
