import logging

import environ
import requests
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from requests import ConnectionError

from ....dados_comuns.constants import DJANGO_EOL_API_TOKEN, DJANGO_EOL_API_URL
from ...models import Escola, EscolaPeriodoEscolar, PeriodoEscolar
from .helper import calcula_total_alunos_por_escola_por_periodo

env = environ.Env()

logger = logging.getLogger("sigpae.cmd_atualiza_total_alunos")


class Command(BaseCommand):
    help = "Atualiza os totais de alunos por período escolar das Escolas baseados na api do EOL"

    def handle(self, *args, **options):  # noqa C901
        headers = {"Authorization": f"Token {DJANGO_EOL_API_TOKEN}"}

        try:
            r = requests.get(
                f"{DJANGO_EOL_API_URL}/total_alunos/", headers=headers, timeout=120
            )
            json = r.json()
            logger.debug(f"payload da resposta: {json}")
        except ConnectionError as e:
            msg = f"Erro de conexão na api do  EOL: {e}"
            logger.error(msg)
            self.stdout.write(self.style.ERROR(msg))
            return
        escola_totais = calcula_total_alunos_por_escola_por_periodo(json)
        self._atualiza_totais_alunos_escola(escola_totais)

    def _atualiza_totais_alunos_escola(self, escola_totais):  # noqa C901
        for codigo_eol, dados in escola_totais.items():
            try:
                escola_object = Escola.objects.get(codigo_eol=codigo_eol)
                for periodo_escolar_str, quantidade_alunos_periodo in dados.items():
                    periodo_escolar_object = PeriodoEscolar.objects.get(
                        nome=periodo_escolar_str.upper()
                    )
                    (
                        escola_periodo,
                        created,
                    ) = EscolaPeriodoEscolar.objects.get_or_create(
                        periodo_escolar=periodo_escolar_object, escola=escola_object
                    )
                    if escola_periodo.quantidade_alunos != quantidade_alunos_periodo:
                        msg = f"Atualizando qtd alunos da escola {escola_object.nome} de {escola_periodo.quantidade_alunos} para {quantidade_alunos_periodo} no período da {periodo_escolar_object.nome}"  # noqa
                        logger.debug(msg)
                        self.stdout.write(self.style.SUCCESS(msg))
                        escola_periodo.quantidade_alunos = quantidade_alunos_periodo
                        escola_periodo.save()

            except ObjectDoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"Escola código EOL: {codigo_eol} não existe no banco ainda"
                    )
                )
                continue
            except IntegrityError as e:
                msg = f"Dados inconsistentes: {e}"
                logger.error(msg)
                self.stdout.write(self.style.ERROR(msg))
                continue
