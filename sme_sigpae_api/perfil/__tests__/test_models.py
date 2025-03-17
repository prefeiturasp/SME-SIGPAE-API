import datetime

import pytest
from django.db.utils import IntegrityError

from sme_sigpae_api.dados_comuns.constants import (
    ADMINISTRADOR_CONTRATOS,
    DILOG_ABASTECIMENTO,
)

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


def test_atualiza_cargo_adm_contratos(usuario_administrador_contratos):
    usuario_administrador_contratos.atualizar_cargo()
    usuario_administrador_contratos.refresh_from_db()
    assert usuario_administrador_contratos.cargo == "Analista"


def test_desativa_cargo_adm_contratos(usuario_administrador_contratos):
    usuario_administrador_contratos.desativa_cargo()
    usuario_administrador_contratos.refresh_from_db()
    assert usuario_administrador_contratos.cargos.last().nome == "Analista"
    assert usuario_administrador_contratos.cargos.last().ativo is False
    assert usuario_administrador_contratos.cargos.last().data_final is not None


def test_usuario_adm_contratos(usuario_administrador_contratos):
    assert (
        usuario_administrador_contratos.vinculo_atual.perfil.nome
        == ADMINISTRADOR_CONTRATOS
    )
    assert usuario_administrador_contratos.tipo_usuario == "administrador_contratos"


def test_atualiza_cargo_dilog_abastecimento(usuario_dilog_abastecimento):
    usuario_dilog_abastecimento.atualizar_cargo()
    usuario_dilog_abastecimento.refresh_from_db()
    assert usuario_dilog_abastecimento.cargo == "Coordenador"


def test_desativa_cargodilog_abastecimento(usuario_dilog_abastecimento):
    usuario_dilog_abastecimento.desativa_cargo()
    usuario_dilog_abastecimento.refresh_from_db()
    assert usuario_dilog_abastecimento.cargos.last().nome == "Coordenador"
    assert usuario_dilog_abastecimento.cargos.last().ativo is False
    assert usuario_dilog_abastecimento.cargos.last().data_final is not None


def test_usuario_dilog_abastecimento(usuario_dilog_abastecimento):
    assert usuario_dilog_abastecimento.vinculo_atual.perfil.nome == DILOG_ABASTECIMENTO
    assert usuario_dilog_abastecimento.tipo_usuario == "pre_recebimento"
