import shutil
import tempfile

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from src.imr.admin import FaixaPontuacaoIMRForm, TipoOcorrenciaForm
from src.imr.models import (
    AnexosFormularioBase,
    TipoOcorrencia,
    TipoPenalidade,
)

pytestmark = pytest.mark.django_db

MEDIA_ROOT = tempfile.mkdtemp()


def test_tipo_gravidade_instance_model(tipo_gravidade_factory):
    tipo = "Leve"
    tipo_gravidade = tipo_gravidade_factory.create(tipo=tipo)
    assert tipo_gravidade.__str__() == tipo_gravidade.tipo


def test_tipo_penalidade_instance_model(tipo_penalidade_factory):
    tipo_penalidade = tipo_penalidade_factory.create()
    assert isinstance(tipo_penalidade, TipoPenalidade)


def test_tipo_penalidade_srt_model(tipo_penalidade_factory, edital_factory):
    edital = edital_factory.create(numero="SME/01/24")
    tipo_penalidade = tipo_penalidade_factory.create(
        numero_clausula="1.1.16", edital=edital
    )
    assert tipo_penalidade.__str__() == "Item: 1.1.16 - Edital: SME/01/24"


def test_tipo_penalidade_meta_modelo(tipo_penalidade_factory):
    tipo_penalidade = tipo_penalidade_factory.create()
    assert tipo_penalidade._meta.verbose_name == "Tipo de Penalidade"
    assert tipo_penalidade._meta.verbose_name_plural == "Tipos de Penalidades"


def test_obrigacao_penalidade_instance_model(obrigacao_penalidade_factory):
    descricao = "Anexo I, itens 5.69"
    obrigacao_penalidade = obrigacao_penalidade_factory.create(descricao=descricao)
    assert obrigacao_penalidade.__str__() == obrigacao_penalidade.descricao


def test_importacao_planilha_tipo_penalidade_instance_model(
    importacao_planilha_tipo_penalidade_factory,
):
    conteudo = SimpleUploadedFile(
        "arquivo_para_carga_tipo_penalidade.xlsx", b"these are the file contents!"
    )
    importacao_planilha_tipo_penalidade = (
        importacao_planilha_tipo_penalidade_factory.create(conteudo=conteudo)
    )
    assert (
        importacao_planilha_tipo_penalidade.__str__()
        == importacao_planilha_tipo_penalidade.conteudo.name
    )
    shutil.rmtree(MEDIA_ROOT, ignore_errors=True)


def test_categoria_ocorrencia_instance_model(categoria_ocorrencia_factory):
    nome = "FUNCIONARIOS"
    categoria_ocorrencia = categoria_ocorrencia_factory.create(nome=nome)
    assert categoria_ocorrencia.__str__() == nome


def test_tipo_ocorrencia_instance_model(tipo_ocorrencia_factory):
    tipo_ocorrencia = tipo_ocorrencia_factory.create()
    assert isinstance(tipo_ocorrencia, TipoOcorrencia)


def test_tipo_ocorrencia_srt_model(tipo_ocorrencia_factory, edital_factory):
    edital = edital_factory.create(numero="SME/02/24")
    tipo_ocorrencia = tipo_ocorrencia_factory.create(titulo="CARDÁPIO", edital=edital)
    assert tipo_ocorrencia.__str__() == "SME/02/24 - CARDÁPIO"


def test_tipo_ocorrencia_meta_modelo(tipo_ocorrencia_factory):
    tipo_ocorrencia = tipo_ocorrencia_factory.create()
    assert tipo_ocorrencia._meta.verbose_name == "Tipo de Ocorrência"
    assert tipo_ocorrencia._meta.verbose_name_plural == "Tipos de Ocorrência"


def test_importacao_planilha_tipo_ocorrencia_instance_model(
    importacao_planilha_tipo_ocorrencia_factory,
):
    conteudo = SimpleUploadedFile(
        "arquivo_para_carga_tipo_ocorrencia.xlsx", b"these are the file contents!"
    )
    importacao_planilha_tipo_ocorrencia = (
        importacao_planilha_tipo_ocorrencia_factory.create(conteudo=conteudo)
    )
    assert (
        importacao_planilha_tipo_ocorrencia.__str__()
        == importacao_planilha_tipo_ocorrencia.conteudo.name
    )
    shutil.rmtree(MEDIA_ROOT, ignore_errors=True)


def test_validation_error_nao_eh_imr_pontuacao_tolerancia_preenchidos():
    data = {"eh_imr": False, "pontuacao": 1, "tolerancia": 1}
    form = TipoOcorrenciaForm(data=data)

    assert form.is_valid() is False
    assert form.errors["pontuacao"] == ["Pontuação só deve ser preenchida se for IMR."]
    assert form.errors["tolerancia"] == [
        "Tolerância só deve ser preenchida se for IMR."
    ]


def test_validation_error_eh_imr_pontuacao_tolerancia_nao_preenchidos():
    data = {"eh_imr": True, "pontuacao": None, "tolerancia": None}
    form = TipoOcorrenciaForm(data=data)

    assert form.is_valid() is False
    assert form.errors["pontuacao"] == ["Pontuação deve ser preenchida se for IMR."]
    assert form.errors["tolerancia"] == ["Tolerância deve ser preenchida se for IMR."]


def test_validation_faixa_pontuacao_imr_intervalo_existente(faixa_pontuacao_factory):
    faixa_pontuacao_factory.create(pontuacao_minima=5, pontuacao_maxima=10)

    data = {"pontuacao_minima": 1, "pontuacao_maxima": 4, "porcentagem_desconto": 1}
    form = FaixaPontuacaoIMRForm(data=data)

    assert form.is_valid() is True


def test_validation_error_faixa_pontuacao_imr_pontuacao_minima_intervalo_existente(
    faixa_pontuacao_factory,
):
    faixa_pontuacao_factory.create(pontuacao_minima=5, pontuacao_maxima=10)

    data = {"pontuacao_minima": 1, "pontuacao_maxima": 5, "porcentagem_desconto": 1}
    form = FaixaPontuacaoIMRForm(data=data)

    assert form.is_valid() is False
    assert form.errors["pontuacao_maxima"] == [
        "Esta pontuação máxima já se encontra dentro de outra faixa."
    ]


def test_validation_error_faixa_pontuacao_imr_pontuacao_maxima_intervalo_existente(
    faixa_pontuacao_factory,
):
    faixa_pontuacao_factory.create(pontuacao_minima=5, pontuacao_maxima=10)

    data = {"pontuacao_minima": 10, "pontuacao_maxima": 15, "porcentagem_desconto": 1}
    form = FaixaPontuacaoIMRForm(data=data)

    assert form.is_valid() is False
    assert form.errors["pontuacao_minima"] == [
        "Esta pontuação mínima já se encontra dentro de outra faixa."
    ]


def test_tipo_ocorrencia_para_diretor_manager(
    categoria_ocorrencia_factory, tipo_ocorrencia_factory
):
    categoria_diretor = categoria_ocorrencia_factory.create(
        perfis=[TipoOcorrencia.DIRETOR]
    )
    categoria_supervisao = categoria_ocorrencia_factory.create(
        perfis=[TipoOcorrencia.SUPERVISAO]
    )
    categoria_ambos = categoria_ocorrencia_factory.create(
        perfis=[TipoOcorrencia.SUPERVISAO, TipoOcorrencia.DIRETOR]
    )
    tipo_ocorrencia_factory.create(
        categoria=categoria_diretor, perfis=[TipoOcorrencia.DIRETOR]
    )
    tipo_ocorrencia_factory.create(
        categoria=categoria_ambos,
        perfis=[TipoOcorrencia.SUPERVISAO, TipoOcorrencia.DIRETOR],
    )
    tipo_ocorrencia_factory.create(
        categoria=categoria_supervisao, perfis=[TipoOcorrencia.SUPERVISAO]
    )

    assert TipoOcorrencia.para_diretores.count() == 2


def test_tipo_ocorrencia_para_supervisao_manager(
    categoria_ocorrencia_factory, tipo_ocorrencia_factory
):
    categoria_diretor = categoria_ocorrencia_factory.create(
        perfis=[TipoOcorrencia.DIRETOR]
    )
    categoria_supervisao = categoria_ocorrencia_factory.create(
        perfis=[TipoOcorrencia.SUPERVISAO]
    )
    categoria_ambos = categoria_ocorrencia_factory.create(
        perfis=[TipoOcorrencia.SUPERVISAO, TipoOcorrencia.DIRETOR]
    )
    tipo_ocorrencia_factory.create(
        categoria=categoria_diretor, perfis=[TipoOcorrencia.DIRETOR]
    )
    tipo_ocorrencia_factory.create(
        categoria=categoria_ambos,
        perfis=[TipoOcorrencia.SUPERVISAO, TipoOcorrencia.DIRETOR],
    )
    tipo_ocorrencia_factory.create(
        categoria=categoria_supervisao, perfis=[TipoOcorrencia.SUPERVISAO]
    )

    assert TipoOcorrencia.para_nutrisupervisores.count() == 2


def test_tipo_resposta_modelo_instance_model(tipo_resposta_modelo_factory):
    nome = "RespostaCampoTextoSimples"
    tipo_resposta_modelo = tipo_resposta_modelo_factory.create(nome=nome)
    assert tipo_resposta_modelo.__str__() == nome


def test_tipo_pergunta_parametrizacao_ocorrencia_instance_model(
    tipo_pergunta_parametrizacao_ocorrencia_factory,
):
    nome = "Campo de Texto Simples"
    tipo_pergunta_parametrizacao_ocorrencia = (
        tipo_pergunta_parametrizacao_ocorrencia_factory.create(nome=nome)
    )
    assert tipo_pergunta_parametrizacao_ocorrencia.__str__() == nome


def test_parametrizacao_ocorrencia_instance_model(
    edital_factory,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
):
    titulo_tipo_ocorrencia = "CARDAPIO"
    edital = edital_factory.create(numero="SME/02/24")
    tipo_ocorrencia = tipo_ocorrencia_factory.create(
        titulo=titulo_tipo_ocorrencia, edital=edital
    )

    nome_tipo_pergunta = "Campo de Texto Simples"
    tipo_pergunta_parametrizacao_ocorrencia = (
        tipo_pergunta_parametrizacao_ocorrencia_factory.create(nome=nome_tipo_pergunta)
    )

    titulo = "Qual item do uniforme faltou?"
    parametrizacao_ocorrencia = parametrizacao_ocorrencia_factory.create(
        posicao=1,
        tipo_ocorrencia=tipo_ocorrencia,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia,
        titulo=titulo,
    )
    assert (
        parametrizacao_ocorrencia.__str__()
        == f"{tipo_ocorrencia.__str__()} {nome_tipo_pergunta} - 1 - {titulo}"
    )


def test_periodo_visita_instance_model(periodo_visita_factory):
    nome = "Manhã/Tarde"
    periodo_visita = periodo_visita_factory.create(nome=nome)
    assert periodo_visita.__str__() == nome


def test_formulario_ocorrencias_base(formulario_ocorrencias_base_factory):
    nome_usuario = "FULANO DA SILVA"
    data = "2024-06-10"
    formulario_ocorrencias_base = formulario_ocorrencias_base_factory.create(
        usuario__nome=nome_usuario, data=data
    )
    assert formulario_ocorrencias_base.__str__() == f"{nome_usuario} - {data}"


def test_anexos_formulario_base_instance_model(
    anexos_formulario_base_factory, formulario_ocorrencias_base_factory
):
    nome_usuario = "FULANO DA SILVA"
    data = "2024-06-10"
    formulario_ocorrencias_base = formulario_ocorrencias_base_factory.create(
        usuario__nome=nome_usuario, data=data
    )
    anexo = SimpleUploadedFile("anexo.pdf", b"these are the file contents!")
    anexo_formulario_base = anexos_formulario_base_factory.create(
        anexo=anexo, formulario_base=formulario_ocorrencias_base
    )
    assert (
        anexo_formulario_base.__str__()
        == f"{anexo_formulario_base.anexo.name} - {formulario_ocorrencias_base.__str__()}"
    )

    anexo_formulario_base.delete()
    assert AnexosFormularioBase.objects.count() == 0
