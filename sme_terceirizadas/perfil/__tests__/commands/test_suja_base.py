import os
from unittest import TestCase, mock

import pytest
from django.core.management import call_command
from model_mommy import mommy

from sme_terceirizadas.dados_comuns.models import Contato
from sme_terceirizadas.perfil.models import Usuario
from sme_terceirizadas.terceirizada.models import Terceirizada


class SujaBaseCommandTest(TestCase):
    def call_command(self, *args, **kwargs):
        call_command(
            'suja_base',
            *args,
            **kwargs,
        )

    def setUp(self) -> None:
        mommy.make(
            Usuario,
            nome='Fulano da Silva',
            email='fulano@teste.com',
            cpf='52347255100',
            registro_funcional='1234567'
        )
        mommy.make(
            Contato,
            email='fulano_2@teste.com',
        )
        mommy.make(
            Terceirizada,
            representante_email='fulano_3@teste.com',
            responsavel_email='fulano_4@teste.com',
        )

    @pytest.mark.django_db(transaction=True)
    def test_command_suja_base(self) -> None:
        usuario = Usuario.objects.get()
        contato = Contato.objects.get()
        terceirizada = Terceirizada.objects.get()
        assert 'fake_' not in usuario.email
        self.call_command()
        usuario.refresh_from_db()
        contato.refresh_from_db()
        terceirizada.refresh_from_db()
        assert 'fake_' in usuario.email
        assert 'fake_' in contato.email
        assert 'fake_' in terceirizada.representante_email
        assert 'fake_' in terceirizada.responsavel_email

    @mock.patch.dict(os.environ, {'DJANGO_ENV': 'production'})
    @pytest.mark.django_db(transaction=True)
    def test_command_suja_base_django_env_production(self) -> None:
        usuario = Usuario.objects.get()
        contato = Contato.objects.get()
        terceirizada = Terceirizada.objects.get()
        assert 'fake_' not in usuario.email
        self.call_command()
        usuario.refresh_from_db()
        contato.refresh_from_db()
        terceirizada.refresh_from_db()
        assert 'fake_' not in usuario.email
        assert 'fake_' not in contato.email
        assert 'fake_' not in terceirizada.representante_email
        assert 'fake_' not in terceirizada.responsavel_email
