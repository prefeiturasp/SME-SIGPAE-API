import importlib

submodulos_admin = [
    "carga_dados",
    "logs_models",
    "protocolo_padrao",
    "solicitacao_dieta_especial",
]

for sub in submodulos_admin:
    importlib.import_module(f"src.dieta_especial.{sub}.admin")
