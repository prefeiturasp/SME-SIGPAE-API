import datetime
import logging
import timeit

import environ
import requests
from django.core.management.base import BaseCommand
from requests import ConnectionError

from ....dados_comuns.constants import DJANGO_EOL_SGP_API_TOKEN, DJANGO_EOL_SGP_API_URL
from ...models import (
    Aluno,
    Escola,
    LogAtualizaDadosAluno,
    LogRotinaDiariaAlunos,
    PeriodoEscolar,
)

env = environ.Env()

logger = logging.getLogger("sigpae.cmd_atualiza_alunos_escolas")


class Command(BaseCommand):
    help = "Atualiza os dados de alunos das Escolas baseados na api do SGP"
    headers = {"x-api-eol-key": f"{DJANGO_EOL_SGP_API_TOKEN}"}
    timeout = 10
    contador_alunos = 0
    total_alunos = 0
    status_matricula_ativa = [1, 6, 10, 13]  # status para matrículas ativas
    codigo_turma_regular = 1  # código da turma para matrículas do tipo REGULAR

    def __init__(self):
        """Atualiza os dados de alunos das Escolas baseados na api do SGP."""
        super().__init__()
        lista_tipo_turnos = list(
            PeriodoEscolar.objects.filter(tipo_turno__isnull=False).values_list(
                "tipo_turno", flat=True
            )
        )
        dict_periodos_escolares_por_tipo_turno = {}
        for tipo_turno in lista_tipo_turnos:
            dict_periodos_escolares_por_tipo_turno[
                tipo_turno
            ] = PeriodoEscolar.objects.get(tipo_turno=tipo_turno)
        self.dict_periodos_escolares_por_tipo_turno = (
            dict_periodos_escolares_por_tipo_turno
        )

    def handle(self, *args, **options):
        try:
            tic = timeit.default_timer()

            quantidade_alunos_antes = Aluno.objects.all().count()

            hoje = datetime.date.today()
            ano = hoje.year
            ultimo_dia_setembro = datetime.date(ano, 10, 1) - datetime.timedelta(days=1)

            if hoje > ultimo_dia_setembro:
                self._atualiza_todas_as_escolas_d_menos_2()
            else:
                self._atualiza_todas_as_escolas_d_menos_1()

            quantidade_alunos_atual = Aluno.objects.all().count()

            LogRotinaDiariaAlunos.objects.create(
                quantidade_alunos_antes=quantidade_alunos_antes,
                quantidade_alunos_atual=quantidade_alunos_atual,
            )

            toc = timeit.default_timer()
            result = round(toc - tic, 2)
            if result > 60:
                logger.debug(f"Total time: {round(result // 60, 2)} min")
            else:
                logger.debug(f"Total time: {round(result, 2)} s")

        except MaxRetriesExceeded as e:
            logger.error(str(e))
            self.stdout.write(
                self.style.ERROR("Execution stopped due to repeated failures.")
            )

    def _salva_logs_requisicao(self, r, cod_eol_escola):
        if not r.status_code == 404:
            msg_erro = "" if r.status_code == 200 else r.text
            log_erro = LogAtualizaDadosAluno(
                status=r.status_code,
                codigo_eol=cod_eol_escola,
                criado_em=datetime.date.today(),
                msg_erro=msg_erro,
            )
            log_erro.save()

    def _obtem_alunos_escola(self, cod_eol_escola, ano_param=None):  # noqa C901
        ano = datetime.date.today().year
        tentativas = 0
        max_tentativas = 10

        while tentativas < max_tentativas:
            try:
                r = requests.get(
                    f"{DJANGO_EOL_SGP_API_URL}/alunos/ues/{cod_eol_escola}/anosLetivos/{ano_param or ano}",
                    headers=self.headers,
                )
                self._salva_logs_requisicao(r, cod_eol_escola)

                # If status is 200 or 404, return the result or an empty list
                if r.status_code == 201:
                    return r.json()
                elif r.status_code == 404:
                    return []

                # Increment retry counter for other status codes
                tentativas += 1
                logger.warning(
                    f"Tentativa {tentativas}/{max_tentativas} for escola {cod_eol_escola}: Status {r.status_code}"
                )

            except ConnectionError as e:
                tentativas += 1
                msg = f"Erro de conexão na API do EOL para escola {cod_eol_escola}: {e}"
                log_erro = LogAtualizaDadosAluno(
                    status=502,
                    codigo_eol=cod_eol_escola,
                    criado_em=datetime.date.today(),
                    msg_erro=msg,
                )
                log_erro.save()
                logger.error(msg)
                self.stdout.write(self.style.ERROR(msg))

        raise MaxRetriesExceeded(
            f"Máximo de tentativas alcançada para a escola {cod_eol_escola}. Abortado."
        )

    def _monta_obj_aluno(self, registro, escola, data_nascimento):
        obj_aluno = Aluno(
            nome=registro["nomeAluno"].strip(),
            codigo_eol=registro["codigoAluno"],
            data_nascimento=data_nascimento,
            escola=escola,
            serie=registro["turmaNome"],
            periodo_escolar=self.dict_periodos_escolares_por_tipo_turno[
                registro["tipoTurno"]
            ],
            etapa=registro.get("etapaEnsino", None),
            ciclo=registro.get("cicloEnsino", None),
            desc_etapa=registro.get("descEtapaEnsino", ""),
            desc_ciclo=registro.get("descCicloEnsino", ""),
        )
        return obj_aluno

    def _atualiza_aluno(self, aluno, registro, data_nascimento, escola):
        aluno.nome = registro["nomeAluno"].strip()
        aluno.codigo_eol = registro["codigoAluno"]
        aluno.data_nascimento = data_nascimento
        aluno.escola = escola
        aluno.nao_matriculado = False
        aluno.serie = registro["turmaNome"]
        aluno.periodo_escolar = self.dict_periodos_escolares_por_tipo_turno[
            registro["tipoTurno"]
        ]
        aluno.etapa = registro.get("etapaEnsino", None)
        aluno.ciclo = registro.get("cicloEnsino", None)
        aluno.desc_etapa = registro.get("descEtapaEnsino", "")
        aluno.desc_ciclo = registro.get("descCicloEnsino", "")
        aluno.save()

    def get_todos_os_registros(self):
        escolas = Escola.objects.all()
        proximo_ano = datetime.date.today().year + 1

        total = escolas.count()
        todos_os_registros = []
        for i, escola in enumerate(escolas):
            logger.debug(f"{i + 1}/{total} - {escola}")
            dados_alunos_escola = self._obtem_alunos_escola(escola.codigo_eol)
            dados_alunos_escola_prox_ano = self._obtem_alunos_escola(
                escola.codigo_eol, proximo_ano
            )
            if (
                dados_alunos_escola
                and type(dados_alunos_escola) is list
                and len(dados_alunos_escola) > 0
            ):
                for dado in dados_alunos_escola:
                    dado["codigoEolEscola"] = escola.codigo_eol
                todos_os_registros += dados_alunos_escola
            if (
                dados_alunos_escola_prox_ano
                and type(dados_alunos_escola_prox_ano) is list
                and len(dados_alunos_escola_prox_ano) > 0
            ):
                for dado in dados_alunos_escola_prox_ano:
                    dado["codigoEolEscola"] = escola.codigo_eol
                todos_os_registros += dados_alunos_escola_prox_ano
        todos_os_registros = sorted(
            todos_os_registros,
            key=lambda registro_: (
                registro_["codigoAluno"],
                registro_["anoLetivo"],
            ),
        )
        return todos_os_registros

    def _atualiza_todas_as_escolas_d_menos_2(self):
        todos_os_registros = self.get_todos_os_registros()
        self.total_alunos += len(todos_os_registros)
        alunos_ativos = []
        novos_alunos = {}
        for registro in todos_os_registros:
            self.contador_alunos += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"{self.contador_alunos} DE UM TOTAL DE {self.total_alunos} MATRICULAS"
                )
            )
            if registro["codigoAluno"] in alunos_ativos:
                continue
            if (
                registro["codigoSituacaoMatricula"] in self.status_matricula_ativa
                and registro["codigoTipoTurma"] == self.codigo_turma_regular
            ):
                alunos_ativos.append(registro["codigoAluno"])
                escola = Escola.objects.get(codigo_eol=registro["codigoEolEscola"])
                data_nascimento = registro["dataNascimento"].split("T")[0]
                try:
                    aluno = Aluno.objects.get(codigo_eol=registro["codigoAluno"])
                    self._atualiza_aluno(aluno, registro, data_nascimento, escola)
                except Aluno.DoesNotExist:
                    novos_alunos[registro["codigoAluno"]] = self._monta_obj_aluno(
                        registro, escola, data_nascimento
                    )
        self.stdout.write(self.style.SUCCESS("criando alunos... aguarde..."))
        Aluno.objects.bulk_create(novos_alunos.values())
        self.stdout.write(self.style.SUCCESS("desvinculando alunos... aguarde..."))
        Aluno.objects.filter(escola__isnull=False).exclude(
            codigo_eol__in=alunos_ativos
        ).update(nao_matriculado=True, escola=None)

    def _desvincular_matriculas(self, alunos):
        for aluno in alunos:
            aluno.nao_matriculado = True
            aluno.escola = None
            aluno.save()

    def aluno_matriculado_prox_ano(self, dados, aluno_nome):
        aluno_encontrado = next(
            (aluno for aluno in dados if aluno["nomeAluno"] == aluno_nome), None
        )
        return (
            aluno_encontrado
            and aluno_encontrado["codigoSituacaoMatricula"]
            in self.status_matricula_ativa
        )

    def _atualiza_alunos_da_escola(
        self, escola, dados_alunos_escola, dados_alunos_escola_prox_ano
    ):
        novos_alunos = {}
        self.total_alunos += len(dados_alunos_escola)
        codigos_consultados = []
        for registro in dados_alunos_escola:
            self.contador_alunos += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"{self.contador_alunos} DE UM TOTAL DE {self.total_alunos} MATRICULAS"
                )
            )
            if (
                registro["codigoSituacaoMatricula"] in self.status_matricula_ativa
                or self.aluno_matriculado_prox_ano(
                    dados_alunos_escola_prox_ano, registro["nomeAluno"]
                )
            ) and registro["codigoTipoTurma"] == self.codigo_turma_regular:
                codigos_consultados.append(registro["codigoAluno"])
                aluno = Aluno.objects.filter(codigo_eol=registro["codigoAluno"]).first()
                data_nascimento = registro["dataNascimento"].split("T")[0]
                if aluno:
                    self._atualiza_aluno(aluno, registro, data_nascimento, escola)
                else:
                    novos_alunos[registro["codigoAluno"]] = self._monta_obj_aluno(
                        registro, escola, data_nascimento
                    )

        alunos_nao_consultados = Aluno.objects.filter(escola=escola).exclude(
            codigo_eol__in=codigos_consultados
        )
        self._desvincular_matriculas(alunos_nao_consultados)
        Aluno.objects.bulk_create(novos_alunos.values())

    def _atualiza_todas_as_escolas_d_menos_1(self):
        escolas = Escola.objects.all()
        proximo_ano = datetime.date.today().year + 1

        total = escolas.count()
        for i, escola in enumerate(escolas):
            logger.debug(f"{i+1}/{total} - {escola}")
            dados_alunos_escola = self._obtem_alunos_escola(escola.codigo_eol)
            dados_alunos_escola_prox_ano = self._obtem_alunos_escola(
                escola.codigo_eol, proximo_ano
            )
            if (
                dados_alunos_escola
                and type(dados_alunos_escola) is list
                and len(dados_alunos_escola) > 0
            ):
                self._atualiza_alunos_da_escola(
                    escola, dados_alunos_escola, dados_alunos_escola_prox_ano
                )


class MaxRetriesExceeded(Exception):
    pass
