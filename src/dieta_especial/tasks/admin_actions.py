from celery import shared_task

from src.dieta_especial.carga_dados.models import PlanilhaDietasAtivas
from src.escola.utils_escola import get_escolas


@shared_task
def get_escolas_task():
    obj = (
        PlanilhaDietasAtivas.objects.first()
    )  # Tem um problema aqui, e se selecionar outro arquivo?
    arquivo = obj.arquivo
    arquivo_unidades_da_rede = obj.arquivo_unidades_da_rede
    get_escolas(arquivo, arquivo_unidades_da_rede, obj.tempfile, in_memory=True)
