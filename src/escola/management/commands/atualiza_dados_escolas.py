import logging

import environ
import requests
from django.core.management.base import BaseCommand
from requests import ConnectionError

from ....dados_comuns.constants import DJANGO_EOL_SGP_API_TOKEN, DJANGO_EOL_SGP_API_URL
from ....dados_comuns.models import Contato, Endereco
from ...models import DiretoriaRegional, Escola, Subprefeitura, TipoUnidadeEscolar

env = environ.Env()

logger = logging.getLogger("sigpae.cmd_atualiza_dados_escolas")


class Command(BaseCommand):
    help = "Atualiza os dados das Escolas baseados na api do EOL do SGP"
    headers = {"x-api-eol-key": f"{DJANGO_EOL_SGP_API_TOKEN}"}
    timeout = 10
    contador_escolas = 0
    total_escolas = 0

    def handle(self, *args, **options):  # noqa C901
        diretorias_regionais = DiretoriaRegional.objects.all()
        for dre in diretorias_regionais:
            try:
                self._atualiza_dados_escola(dre)
            except ConnectionError as e:
                msg = f"Erro de conexão na api do  EOL: {e}"
                logger.error(msg)
                self.stdout.write(self.style.ERROR(msg))
            except requests.exceptions.ReadTimeout as re:
                msg = f"readTimeout: {re}"
                logger.error(msg)
                self.stdout.write(self.style.ERROR(msg))
            except Exception as ex:
                msg = f"Erro ao tentar atualizar dados da escola: {ex}"
                logger.error(msg)
                self.stdout.write(self.style.ERROR(msg))

    def _atualiza_dados_escola(self, dre):
        response = requests.get(
            f"{DJANGO_EOL_SGP_API_URL}/DREs/{dre.codigo_eol}/escola/Sigpae",
            headers=self.headers,
            timeout=self.timeout,
        )

        escolas_list = response.json()
        self.total_escolas += len(escolas_list)
        for escola_dict in escolas_list:
            self.contador_escolas += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"{self.contador_escolas} DE UM TOTAL DE {self.total_escolas} ESCOLAS"
                )
            )
            escola = self._atualiza_dados_iniciais_da_escola(dre, escola_dict)
            self._atualiza_dados_contato_e_endereco_da_escola(escola)

    def _atualiza_dados_iniciais_da_escola(  # noqa C901
        self, dre: DiretoriaRegional, escola_dict: dict
    ):
        codigo_eol_escola = escola_dict["codigoEscola"].strip()
        nome_unidade_educacao = escola_dict["nomeEscola"].strip()
        nome_tipo_escola = escola_dict["siglaTipoEscola"].strip()
        if nome_tipo_escola == "CEU":
            nome_tipo_escola = "CEU GESTAO"
        nome_escola = f"{nome_tipo_escola} {nome_unidade_educacao}"
        nome_subprefeitura = escola_dict["nomeSubprefeitura"].strip()

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"DRE: {dre} - Escola: {nome_escola} : {codigo_eol_escola} : {len(nome_tipo_escola)}"
                )
            )
        )

        tipo_unidade, _ = TipoUnidadeEscolar.objects.get_or_create(
            iniciais=nome_tipo_escola, defaults={"ativo": True}
        )  # noqa
        subprefeitura, _ = Subprefeitura.objects.get_or_create(nome=nome_subprefeitura)

        escola, _ = Escola.objects.update_or_create(
            codigo_eol=codigo_eol_escola,
            defaults={
                "nome": nome_escola,
                "diretoria_regional": dre,
                "tipo_unidade": tipo_unidade,
                "subprefeitura": subprefeitura,
            },
        )
        msg = (
            f"Criando ou Atualizando dados iniciais da escola {escola} : {nome_escola}"
        )
        self.stdout.write(self.style.SUCCESS(msg))

        return escola

    def _atualiza_dados_contato_e_endereco_da_escola(self, escola: Escola):  # noqa C901
        response = requests.get(
            f"{DJANGO_EOL_SGP_API_URL}/escolas/dados/{escola.codigo_eol}",
            headers=self.headers,
            timeout=self.timeout,
        )
        escola_dados = response.json()

        if escola.endereco:
            endereco = escola.endereco
        else:
            endereco = Endereco()
        endereco.logradouro = (
            escola_dados["tipoLogradouro"].strip()
            + " "
            + escola_dados["logradouro"].strip()
        )

        if escola_dados["numero"] and escola_dados["numero"].strip() != "S/N":
            endereco.numero = escola_dados["numero"].strip()
        endereco.bairro = escola_dados["bairro"].strip()
        endereco.cep = escola_dados["cep"]
        endereco.save()

        if escola.endereco is None:
            escola.endereco = endereco

        if escola.contato:
            contato = escola.contato
        else:
            contato = Contato()

        if escola_dados["email"]:
            contato.email = escola_dados["email"].strip()
            if env("DJANGO_ENV") != "production":
                contato.email = "fake_" + contato.email

        if (
            escola_dados["telefone"]
            and len(escola_dados["telefone"]) <= 10
            and len(escola_dados["telefone"]) >= 8
        ):
            contato.telefone = escola_dados["telefone"].strip()
        contato.save()

        if escola.contato is None:
            escola.contato = contato
        escola.save()
