from src.terceirizada.models import Terceirizada

empresas = [
    {"empresa": "SINGULAR GESTAO DE SERVIÇOS LTDA", "lotes": [4, 5, 8, 9]},
    {"empresa": "APETECE SISTEMAS DE ALIMENTAÇAO S/A. ", "lotes": [3, 6, 10, 11]},
    {"empresa": "S.H.A COMERCIO DE ALIMENTOS LTDA", "lotes": [2, 12, 7]},
    {"empresa": "P.R.M. SERVIÇOS E MAO DE OBRA ESPECIALIZADA EIRELI  ", "lotes": [1]},
    {"empresa": "COMERCIAL MILANO BRASIL", "lotes": [13]},
]

for empresa in empresas:
    emp = Terceirizada(
        nome=empresa["empresa"],
    )
    emp.save()
    emp.lote.set(empresa["lotes"])
    emp.save()
