import datetime

import pytest
from django.db.utils import IntegrityError

from sme_sigpae_api.dados_comuns.constants import ADMINISTRADOR_DICAE
from sme_sigpae_api.perfil.models.usuario import Cargo

from ..models import Perfil, Usuario

pytestmark = pytest.mark.django_db


def test_perfil(perfil):
    assert perfil.nome == "título do perfil"
    assert perfil.__str__() == "título do perfil"


def test_perfis_vinculados(perfis_vinculados, perfil_distribuidor):
    assert perfis_vinculados.perfil_master == perfil_distribuidor
    assert isinstance(perfis_vinculados.perfis_subordinados.all()[0], Perfil)


def test_usuario(usuario):
    assert usuario.nome == "Fulano da Silva"
    assert usuario.email == "fulano@teste.com"
    assert usuario.tipo_usuario == "indefinido"


def test_meta_modelo(perfil):
    assert perfil._meta.verbose_name == "Perfil"
    assert perfil._meta.verbose_name_plural == "Perfis"


def test_instance_model(perfil):
    assert isinstance(perfil, Perfil)


def test_vinculo(vinculo):
    assert isinstance(vinculo.data_final, datetime.date) or vinculo.data_final is None
    assert isinstance(vinculo.usuario, Usuario)
    assert isinstance(vinculo.perfil, Perfil)
    assert vinculo.status is vinculo.STATUS_ATIVO
    vinculo.finalizar_vinculo()
    assert vinculo.status is vinculo.STATUS_FINALIZADO
    assert vinculo.data_final is not None
    assert vinculo.ativo is False


def test_vinculo_aguardando_ativacao(vinculo_aguardando_ativacao):
    assert (
        vinculo_aguardando_ativacao.status
        is vinculo_aguardando_ativacao.STATUS_AGUARDANDO_ATIVACAO
    )


def test_vinculo_invalido(vinculo_invalido):
    with pytest.raises(IntegrityError, match="Status invalido"):
        vinculo_invalido.status


def test_vinculo_diretoria_regional(vinculo_diretoria_regional):
    assert vinculo_diretoria_regional.usuario.tipo_usuario == "diretoriaregional"


def test_vinculos(usuario_3):
    assert usuario_3.vinculos.count() == 1


def test_atualiza_cargo(usuario_administrador_dicae):
    usuario_administrador_dicae.atualizar_cargo()
    usuario_administrador_dicae.refresh_from_db()
    assert usuario_administrador_dicae.cargo == "Analista"


def test_desativa_cargo(usuario_administrador_dicae):
    usuario_administrador_dicae.desativa_cargo()
    usuario_administrador_dicae.refresh_from_db()
    assert usuario_administrador_dicae.cargos.last().nome == "Analista"
    assert usuario_administrador_dicae.cargos.last().ativo is False
    assert usuario_administrador_dicae.cargos.last().data_final is not None


def test_usuario_dicae(usuario_administrador_dicae):
    assert usuario_administrador_dicae.vinculo_atual.perfil.nome == ADMINISTRADOR_DICAE
