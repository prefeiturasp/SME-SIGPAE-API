import datetime

from django.core.management import BaseCommand

from ....eol_servico.utils import EOLServicoSGP
from ...models import Aluno, Escola, LogAlunoPorDia, LogAlunosMatriculadosFaixaEtariaDia
from .atualiza_cache_matriculados_por_faixa import Command as c


class Command(BaseCommand):
    help = "Criar registros de LogAlunoPorDia escolas CEI que relaciona log LogAlunosMatriculadosFaixaEtariaDia e Aluno - Março 2024"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                "*** Iniciando criação de registros LogAlunoPorDia escolas CEI ***"
            )
        )
        iniciais = [
            "CEI DIRET",
            "CEU CEI",
            "CEI",
            "CCI",
            "CCI/CIPS",
            "CEI CEU",
            "CEU CEMEI",
            "CEMEI",
        ]
        escolas = Escola.objects.filter(tipo_unidade__iniciais__in=iniciais)
        total_escolas = escolas.count()
        for i, escola in enumerate(escolas):
            self.stdout.write(
                self.style.SUCCESS(
                    "****************************************************************"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"*** Criando LogAlunoPorDia para {escola.nome} - ({i + 1}/{total_escolas}) ***"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "****************************************************************"
                )
            )
            self.criar_logs_alunos_por_dia(escola, total_escolas, i)
        self.stdout.write(
            self.style.SUCCESS(
                "*** Finalizando criação de registros LogAlunoPorDia escolas CEI ***"
            )
        )

    def update_or_create_logs_alunos_por_dia(self, lista_filtrada_alunos_eol, log):
        for aluno_eol in lista_filtrada_alunos_eol:
            try:
                aluno = Aluno.objects.get(codigo_eol=aluno_eol["cd_aluno"])
                LogAlunoPorDia.objects.update_or_create(
                    log_alunos_matriculados_faixa_dia=log,
                    aluno=aluno,
                    defaults={
                        "log_alunos_matriculados_faixa_dia": log,
                        "aluno": aluno,
                    },
                )
            except Aluno.DoesNotExist as e:
                self.stdout.write(self.style.ERROR(str(e)))

    def criar_logs_alunos_por_dia(self, escola, total_escolas, index_escola):
        logs = LogAlunosMatriculadosFaixaEtariaDia.objects.filter(
            escola=escola, data__month__in=[3, 4], data__year=2024
        )
        total_logs = logs.count()
        try:
            lista_alunos = EOLServicoSGP.get_alunos_por_escola_por_ano_letivo(
                escola.codigo_eol
            )
            if len(lista_alunos) == 0:
                ano_seguinte = datetime.datetime.today().year + 1
                lista_alunos = EOLServicoSGP.get_alunos_por_escola_por_ano_letivo(
                    escola.codigo_eol, ano_seguinte
                )

            for i, log in enumerate(logs):
                self.stdout.write(
                    self.style.SUCCESS(
                        f"****** Escola ({index_escola + 1} de {total_escolas}) -- Criando log ({i + 1}/{total_logs}) -- {log} ******"
                    )
                )
                if not log.periodo_escolar.nome == "PARCIAL":
                    periodo_do_log = log.periodo_escolar.nome
                    faixa_etaria_do_log = log.faixa_etaria
                    lista_filtrada_alunos_eol = c().get_lista_filtrada_alunos_eol(
                        lista_alunos, periodo_do_log, faixa_etaria_do_log
                    )
                    self.update_or_create_logs_alunos_por_dia(
                        lista_filtrada_alunos_eol, log
                    )
        except Exception as e:
            self.stdout.write(self.style.ERROR(str(e)))
