import importlib

submodulos_admin = [
    "alteracao_tipo_alimentacao",
    "alteracao_tipo_alimentacao_cei",
    "alteracao_tipo_alimentacao_cemei",
    "base",
    "inversao_dia_cardapio",
    "suspensao_alimentacao",
    "suspensao_alimentacao_cei",
]

for sub in submodulos_admin:
    importlib.import_module(f"sme_sigpae_api.cardapio.{sub}.admin")
