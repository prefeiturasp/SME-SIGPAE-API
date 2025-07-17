import importlib

submodulos_admin = [
    "base",
    "cronograma_entrega",
    "documento_recebimento",
    "ficha_tecnica",
    "layout_embalagem",
    "qualidade",
]

for sub in submodulos_admin:
    importlib.import_module(f"sme_sigpae_api.pre_recebimento.{sub}.admin")
