import os
import django
import datetime
from dateutil.relativedelta import relativedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()


ANO = 2024
MES = 10
DIAS_MES = 31
QUANTIDADE_ALUNOS = 25


def habilitar_dias_letivos():
    from sme_sigpae_api.escola.utils import calendario_sgp
    d = datetime.date(ANO, MES, 1)
    calendario_sgp(d)


def incluir_log_alunos_matriculados(periodos, escola):
    from sme_sigpae_api.escola.models import LogAlunosMatriculadosPeriodoEscola, PeriodoEscolar
    for periodo in periodos:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for dia in range(1, DIAS_MES + 1):
            log = LogAlunosMatriculadosPeriodoEscola(
                escola=escola,
                periodo_escolar=pe,
                quantidade_alunos=QUANTIDADE_ALUNOS
            )
            log.save()
            data = datetime.date(ANO, MES, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(criado_em=data)
        print(f"Logs do Período {periodo} cadastrados")


def obter_usuario(username, nome):
    from sme_sigpae_api.perfil.models.usuario import Usuario
    try:
        return Usuario.objects.get(username=username, nome=nome)
    except Exception:
        print(f"Nenhum usuário encontrado com  username={username} e nome={nome}")
        print("================== SCRIP CANCELADO ==================")
        exit()


if __name__ == "__main__":
    habilitar_dias_letivos()