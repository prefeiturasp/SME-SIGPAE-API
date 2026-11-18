import importlib

from django.contrib import admin

from .dias_letivos.admin import DiaLetivoSIGPAEAdmin
from .dias_letivos.models import DiaLetivoSIGPAE

SUBMODULOS_ADMIN = [
    "aluno",
    "carga_dados",
    "codae",
    "diretoria_regional",
    "escola",
    "logs",
    "lote",
    "subprefeitura",
]

for submodulo in SUBMODULOS_ADMIN:
    importlib.import_module(f"src.core.{submodulo}.admin")

admin.site.register(DiaLetivoSIGPAE, DiaLetivoSIGPAEAdmin)
