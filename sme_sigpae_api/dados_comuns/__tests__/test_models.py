import pytest
from django.contrib import admin
from model_bakery import baker

from ..models import CentralDeDownload, Notificacao

pytestmark = pytest.mark.django_db


def test_template_mensagem(template_mensagem):
    params, esperado = template_mensagem
    template = baker.make(**params)
    assert isinstance(template.assunto, str)
    assert isinstance(template.template_html, str)


def test_template_mensagem_obj(template_mensagem_obj):
    assert template_mensagem_obj.__str__() == "Alteração do tipo de Alimentação"


def test_instance_model_notificacao(notificacao, django_user_model):
    model = notificacao
    assert isinstance(model, Notificacao)
    assert model.titulo
    assert model.descricao
    assert model.tipo
    assert model.categoria
    assert model.criado_em
    assert model.uuid
    assert isinstance(model.usuario, django_user_model)
    assert model.id


def test_srt_model_notificacao(notificacao):
    assert str(notificacao) == "Nova requisição de entrega"


def test_meta_modelo_notificacao(notificacao):
    assert notificacao._meta.verbose_name == "Notificação"
    assert notificacao._meta.verbose_name_plural == "Notificações"


def test_admin_notificacao():
    assert admin.site._registry[Notificacao]


def test_notificar(notificacao):
    Notificacao.notificar(
        tipo=Notificacao.TIPO_NOTIFICACAO_AVISO,
        categoria=Notificacao.CATEGORIA_NOTIFICACAO_GUIA_DE_REMESSA,
        titulo="Hoje tem entrega de alimentos",
        descricao="teste",
        usuario=notificacao.usuario,
        link="/teste/",
    )

    obj = Notificacao.objects.last()

    assert obj.tipo == Notificacao.TIPO_NOTIFICACAO_AVISO
    assert obj.categoria == Notificacao.CATEGORIA_NOTIFICACAO_GUIA_DE_REMESSA
    assert obj.titulo == "Hoje tem entrega de alimentos"
    assert obj.descricao == "teste"
    assert obj.usuario == notificacao.usuario
    assert obj.link == "/teste/"


def test_resolver_pendencia(notificacao_de_pendencia_com_requisicao):
    Notificacao.notificar(
        tipo=Notificacao.TIPO_NOTIFICACAO_PENDENCIA,
        categoria=Notificacao.CATEGORIA_NOTIFICACAO_GUIA_DE_REMESSA,
        titulo="Hoje tem entrega de alimentos",
        descricao="teste",
        usuario=notificacao_de_pendencia_com_requisicao.usuario,
        link="/teste/",
        requisicao=notificacao_de_pendencia_com_requisicao.requisicao,
    )

    obj = Notificacao.objects.last()

    assert obj.tipo == Notificacao.TIPO_NOTIFICACAO_PENDENCIA
    assert obj.categoria == Notificacao.CATEGORIA_NOTIFICACAO_GUIA_DE_REMESSA
    assert obj.titulo == "Hoje tem entrega de alimentos"
    assert obj.descricao == "teste"
    assert obj.usuario == notificacao_de_pendencia_com_requisicao.usuario
    assert obj.link == "/teste/"
    assert obj.requisicao == notificacao_de_pendencia_com_requisicao.requisicao
    assert obj.resolvido is False
    assert obj.lido is False

    Notificacao.resolver_pendencia(
        titulo=obj.titulo, requisicao=notificacao_de_pendencia_com_requisicao.requisicao
    )

    obj2 = Notificacao.objects.last()

    assert obj2.tipo == Notificacao.TIPO_NOTIFICACAO_PENDENCIA
    assert obj2.categoria == Notificacao.CATEGORIA_NOTIFICACAO_GUIA_DE_REMESSA
    assert obj2.titulo == "Hoje tem entrega de alimentos"
    assert obj2.descricao == "teste"
    assert obj2.usuario == notificacao_de_pendencia_com_requisicao.usuario
    assert obj2.link == "/teste/"
    assert obj2.requisicao == notificacao_de_pendencia_com_requisicao.requisicao
    assert obj2.resolvido is True
    assert obj2.lido is True


def test_instance_model_central_download(download, django_user_model):
    model = download
    assert isinstance(model, CentralDeDownload)
    assert model.status
    assert model.identificador
    assert model.arquivo
    assert isinstance(model.usuario, django_user_model)
    assert model.criado_em
    assert model.uuid
    assert model.id


def test_srt_model_central_download(download):
    assert str(download) == "teste.pdf"


def test_meta_modelo_central_download(download):
    assert download._meta.verbose_name == "Central de Download"
    assert download._meta.verbose_name_plural == "Central de Downloads"
