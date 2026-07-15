import importlib

submodulos_admin = [
    "base",
    "cronograma_entrega",
    "cronograma_semanal",
    "documento_recebimento",
    "ficha_tecnica",
    "layout_embalagem",
    "qualidade",
]

for sub in submodulos_admin:
    importlib.import_module(f"src.pre_recebimento.{sub}.admin")
