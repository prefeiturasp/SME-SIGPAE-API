import logging

import environ
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from ...models import (
    DiretoriaRegional,
    Escola,
    Subprefeitura,
    TipoGestao,
    TipoUnidadeEscolar,
)

env = environ.Env()

logger = logging.getLogger("sigpae.cmd_exclui_codido_codae_escolas_especificas")


class Command(BaseCommand):
    help = "Remove código codae de escolas que não fazem parte do piloto em produção do SIGPAE"

    try:
        tipo_unidade_cei_parceiro = TipoUnidadeEscolar.objects.get(iniciais="CR.P.CONV")
        tipo_gestao_parceira = TipoGestao.objects.get(nome="PARCEIRA")
        tipo_gestao_mista = TipoGestao.objects.get(nome="MISTA")
        tipo_gestao_direta = TipoGestao.objects.get(nome="DIRETA")
        sub_pinheiros = Subprefeitura.objects.get(nome="PINHEIROS")
        dre_fb = DiretoriaRegional.objects.get(codigo_eol="108400")
        dre_sao_mateus = DiretoriaRegional.objects.get(codigo_eol="109200")
    except ObjectDoesNotExist as e:
        msg = f"Parametros não encontrados. Por favor realize o cadastro: {e}"
        logger.error(msg)
        exit()

    def handle(self, *args, **options):
        self._exclui_codigo_codade_cei_parceiro()
        self._exclui_codigo_codade_mistas_e_diretas()

    def _exclui_codigo_codade_cei_parceiro(self):
        """
        Exclui os códidos cadae de todas as CEIs Parceiros.

        Exceto das DRES FB e São Mateus e Subprefeitura de Pinheiros
        """
        escolas = (
            Escola.objects.filter(
                tipo_gestao=self.tipo_gestao_parceira,
                tipo_unidade=self.tipo_unidade_cei_parceiro,
            )
            .exclude(subprefeitura=self.sub_pinheiros)
            .exclude(diretoria_regional__in=(self.dre_fb, self.dre_sao_mateus))
            .exclude(codigo_codae__isnull=True)
        )
        qtd = escolas.count()
        escolas.update(codigo_codae=None)
        logger.debug(
            f"Códigos codae excluidos de {qtd} escolas do tipo gestão parceira e tipo unidade cei parceira"
        )

    def _exclui_codigo_codade_mistas_e_diretas(self):
        """
        Exclui os códidos cadae de todas as unidades do tipo de gestão mista e diretas.

        Exceto das Subprefeitura de Pinheiros.
        """
        escolas = (
            Escola.objects.filter(
                tipo_gestao__in=(self.tipo_gestao_mista, self.tipo_gestao_parceira)
            )
            .exclude(subprefeitura=self.sub_pinheiros)
            .exclude(codigo_codae__isnull=True)
        )
        qtd = escolas.count()
        escolas.update(codigo_codae=None)
        logger.debug(
            f"Códigos codae excluidos de {qtd} escolas do tipo gestão mista e direta"
        )
