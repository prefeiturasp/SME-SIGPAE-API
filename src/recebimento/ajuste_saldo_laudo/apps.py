"""Configuração do app de ajuste de saldo do laudo."""

from django.apps import AppConfig


class AjusteSaldoLaudoConfig(AppConfig):
    """App config do submódulo de ajuste de saldo do laudo."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.recebimento.ajuste_saldo_laudo"
    verbose_name = "Ajuste de Saldo do Laudo"
