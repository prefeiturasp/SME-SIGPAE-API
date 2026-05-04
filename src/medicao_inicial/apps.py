import importlib

from django.apps import AppConfig


class MedicaoInicialConfig(AppConfig):
    name = "src.medicao_inicial"

    def import_models(self):
        super().import_models()
        importlib.import_module("src.medicao_inicial.historico_acesso_ue.models")
