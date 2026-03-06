import datetime
import logging

import requests
from django.core.management.base import BaseCommand
from requests import ConnectionError
from rest_framework import status

from sme_sigpae_api.dados_comuns.constants import (
    DJANGO_EOL_SGP_API_TOKEN,
    DJANGO_EOL_SGP_API_URL,
)
from sme_sigpae_api.escola.models import (
    Escola,
    HistoricoMatriculaAluno,
    LogAtualizaDadosAluno,
)

logger = logging.getLogger("sigpae.cmd_encerra_historicos_alunos_inativos")

DATA_FIM_PADRAO = datetime.date(2025, 12, 31)
CODIGO_SITUACAO_CONCLUIDO = 5
SITUACAO_CONCLUIDA = "Concluído"
STATUS_MATRICULA_ATIVA = [1, 6, 10, 13]
CODIGO_TURMA_REGULAR = 1


class Command(BaseCommand):
    help = (
        "Encerra históricos de matrícula ativos de alunos que não estão mais ativos "
        "na escola. data_fim = 31/12/2025 se não há outro histórico ativo em outra "
        "escola; caso contrário, data_fim = data_inicio do próximo histórico - 1 dia."
    )

    headers = {"x-api-eol-key": f"{DJANGO_EOL_SGP_API_TOKEN}"}

    def handle(self, *args, **options):
        escolas = Escola.objects.all()
        total = escolas.count()
        self.stdout.write(f"Processando {total} escolas...")

        for i, escola in enumerate(escolas):
            self.stdout.write(f"{i + 1}/{total} - {escola} (EOL: {escola.codigo_eol})")
            try:
                self._processa_escola(escola)
            except Exception as e:
                logger.error(f"Erro ao processar escola {escola.codigo_eol}: {e}")
                self.stdout.write(
                    self.style.ERROR(
                        f"Erro ao processar escola {escola.codigo_eol}: {e}"
                    )
                )

        self.stdout.write(self.style.SUCCESS("Processamento concluído."))

    def _obtem_alunos_ativos_escola(self, cod_eol_escola):
        """Consulta a API e retorna os códigos EOL dos alunos ativos na escola."""
        tentativas = 0
        max_tentativas = 10
        ano = datetime.date.today().year

        while tentativas < max_tentativas:
            try:
                response = requests.get(
                    f"{DJANGO_EOL_SGP_API_URL}/alunos/ues/{cod_eol_escola}/anosLetivos/{ano}",
                    headers=self.headers,
                    timeout=10,
                )
                self._salva_log_requisicao(response, cod_eol_escola)

                if response.status_code == status.HTTP_200_OK:
                    dados = response.json()
                    return {
                        str(r["codigoAluno"])
                        for r in dados
                        if r.get("codigoSituacaoMatricula") in STATUS_MATRICULA_ATIVA
                        and r.get("codigoTipoTurma") == CODIGO_TURMA_REGULAR
                    }
                elif response.status_code == status.HTTP_404_NOT_FOUND:
                    return set()

                tentativas += 1
                logger.warning(
                    f"Tentativa {tentativas}/{max_tentativas} para escola "
                    f"{cod_eol_escola}: Status {response.status_code}"
                )

            except ConnectionError as e:
                tentativas += 1
                msg = f"Erro de conexão para escola {cod_eol_escola}: {e}"
                LogAtualizaDadosAluno(
                    status=502,
                    codigo_eol=cod_eol_escola,
                    criado_em=datetime.date.today(),
                    msg_erro=msg,
                ).save()
                logger.error(msg)

        logger.error(
            f"Máximo de tentativas alcançado para a escola {cod_eol_escola}. Pulando."
        )
        return None

    def _salva_log_requisicao(self, response, cod_eol_escola):
        if response.status_code != status.HTTP_404_NOT_FOUND:
            msg_erro = "" if response.status_code == 200 else response.text
            LogAtualizaDadosAluno(
                status=response.status_code,
                codigo_eol=cod_eol_escola,
                criado_em=datetime.date.today(),
                msg_erro=msg_erro,
            ).save()

    def _processa_escola(self, escola):
        codigos_ativos = self._obtem_alunos_ativos_escola(escola.codigo_eol)
        if codigos_ativos is None:
            self.stdout.write(
                self.style.WARNING(
                    f"  Escola {escola.codigo_eol}: falha na API, pulando."
                )
            )
            return

        historicos_ativos = HistoricoMatriculaAluno.objects.filter(
            escola=escola,
            data_fim__isnull=True,
        ).select_related("aluno")

        encerrados = 0
        for historico in historicos_ativos:
            codigo_eol_aluno = str(historico.aluno.codigo_eol)
            if codigo_eol_aluno in codigos_ativos:
                continue

            data_fim = self._calcula_data_fim(historico)
            historico.data_fim = data_fim
            historico.codigo_situacao = CODIGO_SITUACAO_CONCLUIDO
            historico.situacao = SITUACAO_CONCLUIDA
            historico.save()
            encerrados += 1
            logger.debug(
                f"  Histórico encerrado: aluno {codigo_eol_aluno} na escola "
                f"{escola.codigo_eol} -> data_fim={data_fim}"
            )

        if encerrados:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  {encerrados} histórico(s) encerrado(s) na escola {escola.codigo_eol}."
                )
            )

    def _calcula_data_fim(self, historico: HistoricoMatriculaAluno) -> datetime.date:
        """
        Retorna a data_fim para encerramento do histórico:
        - 31/12/2025 se não há outro histórico ativo em outra escola
        - data_inicio do próximo histórico ativo (em outra escola) - 1 dia, caso exista
        """
        proximo_historico = (
            HistoricoMatriculaAluno.objects.filter(
                aluno=historico.aluno,
                data_fim__isnull=True,
            )
            .exclude(escola=historico.escola)
            .order_by("data_inicio")
            .first()
        )

        if proximo_historico:
            return proximo_historico.data_inicio - datetime.timedelta(days=1)

        return DATA_FIM_PADRAO
