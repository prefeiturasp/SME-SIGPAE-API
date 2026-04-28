import importlib

from django.apps import AppConfig


class MedicaoInicialConfig(AppConfig):
    name = "sme_sigpae_api.medicao_inicial"

    def import_models(self):
        super().import_models()
        importlib.import_module(
            "sme_sigpae_api.medicao_inicial.historico_acesso_ue.models"
        )
