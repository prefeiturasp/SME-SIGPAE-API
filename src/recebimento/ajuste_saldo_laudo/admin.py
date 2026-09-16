"""Configuração do Django Admin do submódulo de ajuste de saldo do laudo."""

from django.contrib import admin

from .models import AjusteSaldo

admin.site.register(AjusteSaldo)
