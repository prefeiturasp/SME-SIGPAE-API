import datetime

import pytest
from django.core.management import call_command

from sme_sigpae_api.perfil.models import Usuario
from sme_sigpae_api.perfil.models.perfil import Perfil, Vinculo


@pytest.mark.django_db
def test_atualiza_username_com_rf_atualiza_usuarios_corretamente(
    setup_usuarios_command,
):
    usuario1 = setup_usuarios_command[0]
    usuario2 = setup_usuarios_command[1]
    usuario3 = setup_usuarios_command[2]
    usuario4 = setup_usuarios_command[3]

    usuario_admin = Usuario.objects.create(
        email="admin@admin.com", registro_funcional="9876544", username="admin_user"
    )

    call_command("atualiza_username_servidores")

    usuario1.refresh_from_db()
    usuario2.refresh_from_db()
    usuario3.refresh_from_db()
    usuario4.refresh_from_db()
    usuario_admin.refresh_from_db()

    assert usuario1.username == "1234567"
    assert usuario2.username == "754321"
    assert usuario3.username == "usuario3"
    assert usuario4.username == "usuario4"
    assert usuario_admin.username == "admin_user"


@pytest.mark.django_db
def test_atualiza_username_com_cpf(setup_vinculos_e_usuarios):
    call_command("atualiza_username_usuarios_empresas")

    usuario1 = Usuario.objects.get(uuid="a9469d8f-6578-4ebb-8b90-6a98fa97c188")
    usuario2 = Usuario.objects.get(uuid="32d150bc-6241-4967-a21b-2f219b2d5317")
    usuario3 = Usuario.objects.get(uuid="cd0bc9f3-17f8-4fe6-9dac-38dd108d6223")
    usuario4 = Usuario.objects.get(uuid="79cc6d39-5d2b-4ed8-8b02-25558db82952")

    assert usuario1.username == "12345678901"
    assert usuario2.username == "98765432109"
    assert usuario3.username == "usuario3"
    assert usuario4.username == "usuario4"


@pytest.mark.django_db
def test_migra_vinculos_escola(setup_vinculos_e_perfis):
    call_command("atualiza_vinculos_de_perfis_removidos")

    adm_ue = Perfil.objects.get(nome="ADMINISTRADOR_UE")
    vinculos_migrados = Vinculo.objects.filter(perfil=adm_ue)
    assert vinculos_migrados.count() > 0

    antigos = [
        "DIRETOR",
        "COORDENADOR_ESCOLA",
        "ADMINISTRADOR_ESCOLA",
        "ADMINISTRADOR_UE_PARCEIRA",
    ]
    assert not Vinculo.objects.filter(perfil__nome__in=antigos).exists()


@pytest.mark.django_db
def test_migra_vinculos_empresa(setup_vinculos_e_perfis):
    call_command("atualiza_vinculos_de_perfis_removidos")

    adm_empresa = Perfil.objects.get(nome="ADMINISTRADOR_EMPRESA")
    vinculos_migrados = Vinculo.objects.filter(perfil=adm_empresa)
    assert vinculos_migrados.count() > 0

    antigos = [
        "NUTRI_ADMIN_RESPONSAVEL",
        "ADMINISTRADOR_DISTRIBUIDORA",
        "ADMINISTRADOR_FORNECEDOR",
    ]
    assert not Vinculo.objects.filter(perfil__nome__in=antigos).exists()


@pytest.mark.django_db
def test_migra_vinculos_empresa_usuario_terceirizada(setup_vinculos_e_perfis):
    call_command("atualiza_vinculos_de_perfis_removidos")

    usuario_empresa = Perfil.objects.get(nome="USUARIO_EMPRESA")
    vinculos_migrados = Vinculo.objects.filter(perfil=usuario_empresa)
    assert vinculos_migrados.count() > 0

    assert not Vinculo.objects.filter(
        perfil__nome="ADMINISTRADOR_TERCEIRIZADA"
    ).exists()


@pytest.mark.django_db
def test_normaliza_vinculos(setup_normaliza_vinculos):
    hoje = datetime.date.today()

    call_command("normaliza_vinculos")

    desativados = Vinculo.objects.filter(
        ativo=False, data_inicial__isnull=False, data_final__isnull=False
    )
    assert desativados.count() == 6

    inicial_ajustada = Vinculo.objects.filter(
        ativo=True, data_inicial=hoje, data_final__isnull=True
    )
    assert inicial_ajustada.count() == 3

    ativados = Vinculo.objects.filter(
        ativo=True, data_inicial__isnull=False, data_final__isnull=True
    )
    assert ativados.count() == 6

    data_inicial_hoje = Vinculo.objects.filter(
        ativo=False, data_inicial=hoje, data_final__isnull=False
    )
    assert data_inicial_hoje.count() == 3


@pytest.mark.django_db
def test_unificar_perfis_dre(setup_unificar_perfis):
    cogestor_dre = Perfil.objects.get(nome="COGESTOR_DRE")
    call_command("unificar_perfis_dre")

    vinculados_cogestor_dre = Vinculo.objects.filter(perfil=cogestor_dre)
    assert (
        vinculados_cogestor_dre.count() == 6
    )  # 2 SUPLENTE + 2 ADMINISTRADOR_DRE + 2 COGESTOR

    perfil_nao_alterado = Perfil.objects.get(nome="NAO_ALTERADO")
    nao_alterados = Vinculo.objects.filter(perfil=perfil_nao_alterado)
    assert nao_alterados.count() == 2
