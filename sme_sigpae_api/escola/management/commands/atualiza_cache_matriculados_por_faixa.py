from datetime import date, timedelta

import environ
import redis
from django.core.management.base import BaseCommand

from ....eol_servico.utils import EOLServicoSGP, dt_nascimento_from_api
from ...models import (
    Aluno,
    Escola,
    FaixaEtaria,
    LogAlunoPorDia,
    LogAlunosMatriculadosFaixaEtariaDia,
    PeriodoEscolar,
)

env = environ.Env()

REDIS_HOST = env("REDIS_HOST")
REDIS_PORT = env("REDIS_PORT")
REDIS_DB = env("REDIS_DB")
REDIS_PREFIX = env("REDIS_PREFIX")

redis_connection = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
)


class Command(BaseCommand):
    help_text = "Atualiza cache do Redis e tabela LogAlunosMatriculadosFaixaEtariaDia "
    help_text += "com alunos matriculados por escola, faixa etária e período escolar"
    help = help_text

    def handle(self, *args, **options):
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
        for escola in escolas:
            self._criar_cache_matriculados_por_faixa(escola)
            self._salvar_matriculados_por_faixa_dia(escola)

    def _criar_cache_matriculados_por_faixa(self, escola):
        try:
            msg = f"Atualizando cache para escola {escola.codigo_eol} - {escola.nome}"
            self.stdout.write(self.style.SUCCESS(msg))
            periodos_faixas = escola.alunos_por_periodo_e_faixa_etaria()
            for periodo, qtdFaixas in periodos_faixas.items():
                nome_periodo = self._formatar_periodo_eol(periodo)
                redis_connection.delete(
                    f"{REDIS_PREFIX}-{str(escola.uuid)}-{nome_periodo}"
                )
                redis_connection.hset(
                    name=f"{REDIS_PREFIX}-{str(escola.uuid)}-{nome_periodo}",
                    mapping=dict(qtdFaixas),
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(str(e)))

    def _formatar_periodo_eol(self, periodo):
        if periodo == "MANHÃ":
            return "MANHA"
        if periodo == "INTERMEDIÁRIO":
            return "INTERMEDIARIO"
        return periodo

    def _duplica_dia_anterior(self, escola):
        ontem = date.today() - timedelta(days=1)
        logs = LogAlunosMatriculadosFaixaEtariaDia.objects.filter(
            escola=escola, data=ontem - timedelta(days=1)
        )
        for log in logs:
            (
                log_alunos_matriculados_faixa_dia,
                _,
            ) = LogAlunosMatriculadosFaixaEtariaDia.objects.update_or_create(
                escola=escola,
                periodo_escolar=log.periodo_escolar,
                faixa_etaria=log.faixa_etaria,
                data=ontem,
                defaults={
                    "escola": escola,
                    "periodo_escolar": log.periodo_escolar,
                    "faixa_etaria": log.faixa_etaria,
                    "quantidade": log.quantidade,
                    "data": ontem,
                },
            )
            self._cria_log_aluno_por_dia(escola, log_alunos_matriculados_faixa_dia)

    def periodos_integral_sem_alunos_pariciais(self, periodos, periodo_parcial):
        if "INTEGRAL" in periodos and "PARCIAL" in periodo_parcial:
            chaves_comuns = set(periodo_parcial["PARCIAL"].keys()).intersection(
                periodos["INTEGRAL"].keys()
            )
            for chave in chaves_comuns:
                periodos["INTEGRAL"][chave] -= periodo_parcial["PARCIAL"][chave]
        return {**periodo_parcial, **periodos}

    def trata_cemei_ao_gerar_logs(self, escola, periodo, faixa_obj, quantidade):
        pula_gerar_logs = False
        if escola.eh_cemei:
            if periodo != "INTEGRAL":
                pula_gerar_logs = True
            quantidade = escola.quantidade_alunos_cei_por_periodo_por_faixa(
                "INTEGRAL", faixa_obj
            )
            if quantidade == 0:
                pula_gerar_logs = True
        return pula_gerar_logs, quantidade

    def get_lista_filtrada_alunos_eol(
        self, lista_alunos_eol, periodo_do_log, faixa_etaria_do_log
    ):
        lista_filtrada_alunos_eol = []
        for aluno in lista_alunos_eol:
            if aluno["tipoTurno"] == periodo_do_log:
                faixa = FaixaEtaria.objects.get(uuid=faixa_etaria_do_log.uuid)
                aluno_data_nascimento = dt_nascimento_from_api(aluno["dataNascimento"])
                if faixa.data_pertence_a_faixa(aluno_data_nascimento, date.today()):
                    lista_filtrada_alunos_eol.append(aluno)
        return lista_filtrada_alunos_eol

    def _cria_log_aluno_por_dia(self, escola, log_alunos_matriculados_faixa_dia):
        lista_alunos_eol = (
            EOLServicoSGP.get_lista_alunos_por_escola_ano_corrente_ou_seguinte(
                escola.codigo_eol
            )
        )
        if not log_alunos_matriculados_faixa_dia.periodo_escolar.nome == "PARCIAL":
            periodo_do_log = (
                log_alunos_matriculados_faixa_dia.periodo_escolar.tipo_turno
            )
            faixa_etaria_do_log = log_alunos_matriculados_faixa_dia.faixa_etaria
            lista_filtrada_alunos_eol = self.get_lista_filtrada_alunos_eol(
                lista_alunos_eol, periodo_do_log, faixa_etaria_do_log
            )
            for aluno_eol in lista_filtrada_alunos_eol:
                try:
                    aluno = Aluno.objects.get(codigo_eol=aluno_eol["codigoAluno"])
                    LogAlunoPorDia.objects.update_or_create(
                        log_alunos_matriculados_faixa_dia=log_alunos_matriculados_faixa_dia,
                        aluno=aluno,
                        defaults={
                            "log_alunos_matriculados_faixa_dia": log_alunos_matriculados_faixa_dia,
                            "aluno": aluno,
                        },
                    )
                except Aluno.DoesNotExist as e:
                    self.stdout.write(self.style.ERROR(str(e)))

    def _salvar_matriculados_por_faixa_dia(self, escola):
        try:
            msg = f"Salvando matriculados por faixa da escola {escola.codigo_eol} - {escola.nome}"
            self.stdout.write(self.style.SUCCESS(msg))
            ontem = date.today() - timedelta(days=1)
            periodos_faixas_gerais = escola.alunos_por_periodo_e_faixa_etaria()
            periodos_faixas_parciais = escola.alunos_periodo_parcial_e_faixa_etaria(
                ontem
            )
            periodos_faixas = self.periodos_integral_sem_alunos_pariciais(
                periodos_faixas_gerais, periodos_faixas_parciais
            )
            for periodo, qtd_faixas in periodos_faixas.items():
                periodo_escolar = PeriodoEscolar.objects.get(
                    nome=self._formatar_periodo_eol(periodo)
                )
                for faixa_etaria, quantidade in qtd_faixas.items():
                    faixa_obj = FaixaEtaria.objects.get(uuid=faixa_etaria)
                    pula_gerar_logs, quantidade = self.trata_cemei_ao_gerar_logs(
                        escola, periodo, faixa_obj, quantidade
                    )
                    if pula_gerar_logs:
                        continue
                    (
                        log_alunos_matriculados_faixa_dia,
                        _,
                    ) = LogAlunosMatriculadosFaixaEtariaDia.objects.update_or_create(
                        escola=escola,
                        periodo_escolar=periodo_escolar,
                        faixa_etaria=faixa_obj,
                        data=ontem,
                        defaults={
                            "escola": escola,
                            "periodo_escolar": periodo_escolar,
                            "faixa_etaria": faixa_obj,
                            "quantidade": quantidade,
                            "data": ontem,
                        },
                    )
                    self._cria_log_aluno_por_dia(
                        escola, log_alunos_matriculados_faixa_dia
                    )

        except Exception as e:
            self.stdout.write(self.style.ERROR(str(e)))
            self._duplica_dia_anterior(escola)
