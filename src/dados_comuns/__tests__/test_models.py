import pytest
from django.contrib import admin

from ..models import CentralDeDownload, Notificacao, VersaoSistema

pytestmark = pytest.mark.django_db


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


def test_versao_sistema_singleton():
    v1 = VersaoSistema.objects.get()
    assert v1.id == 1
    assert v1.pk == 1
    v1.versao = "1.0.0"
    v1.save()

    v2 = VersaoSistema.objects.get()
    assert v2.pk == 1
    assert v2.versao == "1.0.0"
    assert VersaoSistema.objects.count() == 1

    v3 = VersaoSistema.objects.get()
    assert v3.pk == 1
    assert v3.versao == "1.0.0"


def test_srt_model_versao_sistema():
    v = VersaoSistema.objects.get()
    v.versao = "2.0.0"
    v.save()
    assert str(v) == "2.0.0"


def test_meta_modelo_versao_sistema():
    v = VersaoSistema.objects.get()
    assert v._meta.verbose_name == "Versão do Sistema"
    assert v._meta.verbose_name_plural == "Versões do Sistema"


def test_admin_versao_sistema():
    assert admin.site._registry[VersaoSistema]
