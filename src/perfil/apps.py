from django.apps import AppConfig


class PerfilConfig(AppConfig):
    name = "src.perfil"
    verbose_name = "Custom User Management"

    def ready(self) -> None:
        from sme_sidecar_sdk import runtime
        from sme_sidecar_sdk.config import Settings

        runtime.configure(
            Settings(
                service_name="sigpae",
                service_version="1.0.0",
            )
        )
