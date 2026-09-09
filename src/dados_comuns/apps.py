import importlib

from django.apps import AppConfig


class DadosComunsConfig(AppConfig):
    name = "src.dados_comuns"

    def ready(self) -> None:
        importlib.import_module("src.dados_comuns.signals")

        """Inicializa os recursos compartilhados da SDK."""
        from sme_sidecar_sdk import runtime
        from sme_sidecar_sdk.config import Settings

        runtime.configure(
            Settings(
                service_name="sigpae",
                service_version="1.0.0",
            )
        )
