import calendar
import datetime

from django.core.management import BaseCommand

from sme_sigpae_api.dieta_especial.logs.models import (
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
)
from sme_sigpae_api.escola.models import Escola, LogAlunosMatriculadosPeriodoEscola


class Command(BaseCommand):
    help = "Deleta logs duplicados e cria logs, caso não existam, dos modelos de "
    help += "LogQuantidadeDietasAutorizadas, LogQuantidadeDietasAutorizadasCEI e LogAlunosMatriculadosPeriodoEscola"
    help += " do mês de Agosto de 2023"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                "Iniciando análise de LogAlunosMatriculadosPeriodoEscola"
            )
        )
        self.analisa_logs_alunos_matriculados_mes()
        self.stdout.write(
            self.style.SUCCESS("Finaliza análise de LogAlunosMatriculadosPeriodoEscola")
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Iniciando análise de LogQuantidadeDietasAutorizadas / LogQuantidadeDietasAutorizadasCEI"
            )
        )
        self.analisa_logs_quantidade_dietas_autorizadas_mes()
        self.stdout.write(
            self.style.SUCCESS(
                "Finaliza análise de LogQuantidadeDietasAutorizadas / LogQuantidadeDietasAutorizadasCEI"
            )
        )

    def analisa_logs_alunos_matriculados_mes(self, mes=8, ano=2023):
        escolas = Escola.objects.all()
        for index, escola in enumerate(escolas):
            msg = f"análise de LogAlunosMatriculadosPeriodoEscola para escola {escola.nome}"
            msg += f" ({index + 1}/{(escolas).count()})"
            try:
                self.stdout.write(
                    self.style.WARNING(f"x-x-x-x Iniciando {msg} x-x-x-x")
                )
                self.deletar_logs_alunos_matriculados_duplicados_mes(escola, mes, ano)
                self.criar_logs_alunos_matriculados_inexistentes_mes(escola, mes, ano)
                self.stdout.write(self.style.WARNING(f"x-x-x-x Finaliza {msg} x-x-x-x"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"x-x-x-x Erro na {msg} x-x-x-x"))
                self.stdout.write(self.style.ERROR(f"`--> {e}"))

    def deletar_logs_alunos_matriculados_duplicados_mes(self, escola, mes, ano):
        for dia in range(calendar._monthlen(ano, mes), 0, -1):
            logs = LogAlunosMatriculadosPeriodoEscola.objects.filter(
                escola=escola,
                criado_em__year=ano,
                criado_em__month=mes,
                criado_em__day=dia,
            )
            logs_para_deletar = []
            for log in logs:
                logs_filtrados = logs.filter(
                    periodo_escolar=log.periodo_escolar, tipo_turma=log.tipo_turma
                ).order_by("-criado_em")
                for log_filtrado in logs_filtrados[1 : logs_filtrados.count()]:
                    if log_filtrado.uuid not in logs_para_deletar:
                        logs_para_deletar.append(log_filtrado.uuid)
            logs.filter(uuid__in=logs_para_deletar).delete()

    def criar_logs_alunos_matriculados_inexistentes_mes(self, escola, mes, ano):
        for dia in range(calendar._monthlen(ano, mes), 0, -1):
            data = datetime.date(ano, mes, dia)
            logs = LogAlunosMatriculadosPeriodoEscola.objects.filter(
                escola=escola,
                criado_em__year=ano,
                criado_em__month=mes,
                criado_em__day=dia,
            )
            if not logs:
                for i_para_repetir in range(1, 7):
                    data_para_repetir = data - datetime.timedelta(days=i_para_repetir)
                    logs_para_repetir = (
                        LogAlunosMatriculadosPeriodoEscola.objects.filter(
                            escola=escola,
                            criado_em__year=data_para_repetir.year,
                            criado_em__month=data_para_repetir.month,
                            criado_em__day=data_para_repetir.day,
                        )
                    )
                    if logs_para_repetir:
                        for log_para_criar in logs_para_repetir:
                            log_criado = (
                                LogAlunosMatriculadosPeriodoEscola.objects.create(
                                    escola=log_para_criar.escola,
                                    periodo_escolar=log_para_criar.periodo_escolar,
                                    quantidade_alunos=log_para_criar.quantidade_alunos,
                                    tipo_turma=log_para_criar.tipo_turma,
                                )
                            )
                            log_criado.criado_em = data
                            log_criado.save()
                        break

    def analisa_logs_quantidade_dietas_autorizadas_mes(self, mes=8, ano=2023):
        escolas = Escola.objects.filter(tipo_gestao__nome="TERC TOTAL")
        for index, escola in enumerate(escolas):
            msg = "análise de LogQuantidadeDietasAutorizadas / LogQuantidadeDietasAutorizadasCEI"
            msg += f" para escola {escola.nome} ({index + 1}/{(escolas).count()})"
            try:
                self.stdout.write(
                    self.style.WARNING(f"x-x-x-x Iniciando {msg} x-x-x-x")
                )
                self.deletar_logs_quantidade_dietas_autorizadas_mes(escola, mes, ano)
                self.criar_logs_quantidade_dietas_autorizadas_inexistentes_mes(
                    escola, mes, ano
                )
                self.stdout.write(self.style.WARNING(f"x-x-x-x Finaliza {msg} x-x-x-x"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"x-x-x-x Erro na {msg} x-x-x-x"))
                self.stdout.write(self.style.ERROR(f"`--> {e}"))

    def deletar_logs_quantidade_dietas_autorizadas_mes(self, escola, mes, ano):
        modelo = self.get_modelo(escola)
        for dia in range(calendar._monthlen(ano, mes), 0, -1):
            logs = modelo.objects.filter(
                escola=escola, data__year=ano, data__month=mes, data__day=dia
            )
            logs_para_deletar = []
            for log in logs:
                logs_filtrados = logs.filter(
                    periodo_escolar=log.periodo_escolar, classificacao=log.classificacao
                ).order_by("-criado_em")
                if escola.eh_cei:
                    logs_filtrados = logs_filtrados.filter(
                        faixa_etaria=log.faixa_etaria
                    ).order_by("-criado_em")
                for log_filtrado in logs_filtrados[1 : logs_filtrados.count()]:
                    if log_filtrado.uuid not in logs_para_deletar:
                        logs_para_deletar.append(log_filtrado.uuid)
            logs.filter(uuid__in=logs_para_deletar).delete()

    def criar_logs_quantidade_dietas_autorizadas_inexistentes_mes(
        self, escola, mes, ano
    ):
        modelo = self.get_modelo(escola)
        for dia in range(calendar._monthlen(ano, mes), 0, -1):
            data = datetime.date(ano, mes, dia)
            logs = modelo.objects.filter(
                escola=escola, data__year=ano, data__month=mes, data__day=dia
            )
            if not logs:
                for i_para_repetir in range(1, 7):
                    data_para_repetir = data - datetime.timedelta(days=i_para_repetir)
                    logs_para_repetir = modelo.objects.filter(
                        escola=escola,
                        data__year=data_para_repetir.year,
                        data__month=data_para_repetir.month,
                        data__day=data_para_repetir.day,
                    )
                    if logs_para_repetir:
                        for log_para_criar in logs_para_repetir:
                            self.create_objects_logs_mes(escola, log_para_criar, data)
                        break

    def create_objects_logs_mes(self, escola, log_para_criar, data):
        if escola.eh_cei:
            LogQuantidadeDietasAutorizadasCEI.objects.create(
                quantidade=log_para_criar.quantidade,
                escola=log_para_criar.escola,
                data=data,
                classificacao=log_para_criar.classificacao,
                periodo_escolar=log_para_criar.periodo_escolar,
                faixa_etaria=log_para_criar.faixa_etaria,
            )
        else:
            LogQuantidadeDietasAutorizadas.objects.create(
                quantidade=log_para_criar.quantidade,
                escola=log_para_criar.escola,
                data=data,
                classificacao=log_para_criar.classificacao,
                periodo_escolar=log_para_criar.periodo_escolar,
            )

    def get_modelo(self, escola):
        if escola.eh_cei:
            modelo = LogQuantidadeDietasAutorizadasCEI
        else:
            modelo = LogQuantidadeDietasAutorizadas
        return modelo
