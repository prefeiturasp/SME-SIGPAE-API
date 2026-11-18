import importlib

from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "src.core"
    label = "escola"
    verbose_name = "Core"

    def import_models(self):
        super().import_models()
        importlib.import_module("src.core.dias_letivos.models")
