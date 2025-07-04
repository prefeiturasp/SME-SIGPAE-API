import logging
import timeit
from datetime import datetime

import requests
from django.core.management.base import BaseCommand, CommandParser
from requests import ConnectionError

from ....dados_comuns.constants import DJANGO_EOL_SGP_API_TOKEN, DJANGO_EOL_SGP_API_URL
from ...models import Aluno, Escola, HistoricoMatriculaAluno

logger = logging.getLogger("sigpae.cmd_registra_historico_matriculas_alunos")


class Command(BaseCommand):
    help = "Registra o historico de matriculas dos alunos baseados na api do SGP"
    headers = {"x-api-eol-key": f"{DJANGO_EOL_SGP_API_TOKEN}"}

    def __init__(self):
        super().__init__()
        self.alunos = Aluno.objects.all().exclude(codigo_eol__isnull=True)

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--ano",
            help="Especifica o ano vigente que sera usado como base na consulta ao SGP",
            type=int,
        )

    def _get_ano_atual(self):
        return datetime.today().year

    def handle(self, *args, **options):
        tic = timeit.default_timer()

        ano_letivo = options.get("ano") or self._get_ano_atual()

        self._gera_historico_matriculas_alunos(ano_letivo)

        toc = timeit.default_timer()

        result = round(toc - tic, 2)
        if result > 60:
            logger.debug(f"Total time: {round(result // 60, 2)} min")
        else:
            logger.debug(f"Total time: {round(result, 2)} s")

    def _obtem_matriculas_aluno(self, cod_eol_aluno, ano_letivo):
        try:
            url = f"{DJANGO_EOL_SGP_API_URL}/alunos/{cod_eol_aluno}/turmas/anosLetivos/{ano_letivo}/matriculaTurma/true/tipoTurma/true"
            r = requests.get(url=url, headers=self.headers, timeout=120)
            if r.status_code == 200:
                json = r.json()
                return json
            else:
                return []
        except ConnectionError as e:
            msg = f"Erro de conexão na api do EOL: {e}"
            logger.error(msg)
            self.stdout.write(self.style.ERROR(msg))
            return []

    def _agrupa_matriculas_por_escola(self, matriculas):
        matriculas_agrupadas_por_escola = {}
        for matricula in matriculas:
            codigo_eol_escola = matricula.get("codigoEscola")
            if matriculas_agrupadas_por_escola.get(codigo_eol_escola) is None:
                matriculas_agrupadas_por_escola[codigo_eol_escola] = [matricula]
            else:
                matriculas_agrupadas_por_escola[codigo_eol_escola].append(matricula)
        return matriculas_agrupadas_por_escola

    def _gera_historico_das_matriculas_da_escola(
        self, aluno, codigo_eol_escola, matriculas
    ):
        try:
            data_inicio = None
            data_fim = None
            codigo_situacao = None
            situacao = None

            for matricula in matriculas:
                codigo_situacao_matricula = matricula.get("codigoSituacaoMatricula")
                situacao_matricula = matricula.get("situacaoMatricula").upper()
                data_situacao = matricula.get("dataSituacao", "").split("T")[0]
                data_situacao = datetime.strptime(data_situacao, "%Y-%m-%d")

                if situacao_matricula == "ATIVO" and (
                    data_inicio is None or data_situacao < data_inicio
                ):
                    data_inicio = data_situacao
                    codigo_situacao = codigo_situacao_matricula
                    situacao = situacao_matricula
                elif situacao_matricula == "CONCLUÍDO":
                    data_fim = data_situacao
                    codigo_situacao = codigo_situacao_matricula
                    situacao = situacao_matricula

            escola = Escola.objects.get(codigo_eol=codigo_eol_escola)

            _, criado = HistoricoMatriculaAluno.objects.update_or_create(
                aluno=aluno,
                escola=escola,
                defaults={
                    "data_inicio": data_inicio,
                    "data_fim": data_fim,
                    "codigo_situacao": codigo_situacao,
                    "situacao": situacao,
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"ESCOLA {escola}: HISTORICO {'CRIADO' if criado else 'ATUALIZADO'} COM SUCESSO"
                )
            )
        except Exception as err:
            logger.warning(
                f"Nao foi possivel gerar o historico de matriculas do aluno {aluno} da escola {codigo_eol_escola}: {err}"
            )

    def _gera_historico_matriculas_alunos(self, ano_letivo: int):
        logger.debug(f"Ano de referencia: {ano_letivo}")
        total = len(self.alunos)
        for i, aluno in enumerate(self.alunos):
            logger.debug(f"{i + 1}/{total} - {aluno}")
            matriculas = self._obtem_matriculas_aluno(aluno.codigo_eol, ano_letivo)

            matriculas_agrupadas_por_escola = self._agrupa_matriculas_por_escola(
                matriculas
            )

            for (
                codigo_eol_escola,
                matriculas,
            ) in matriculas_agrupadas_por_escola.items():
                self._gera_historico_das_matriculas_da_escola(
                    aluno, codigo_eol_escola, matriculas
                )
