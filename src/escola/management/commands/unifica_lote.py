import logging

import environ
from django.core.management import BaseCommand

from src.escola.models import Lote

logger = logging.getLogger("sigpae.cmd_unifica_lote")

env = environ.Env()


class Command(BaseCommand):
    help = "Unifica os lotes passados por parâmetro"

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("lote_nome_1", nargs="+", type=str)
        parser.add_argument("lote_nome_2", nargs="+", type=str)
        parser.add_argument("lote_nome_unificado", nargs="+", type=str)

    def handle(self, *args, **options):
        lote_nome_1 = options["lote_nome_1"][0]
        lote_nome_2 = options["lote_nome_2"][0]
        lote_nome_unificado = options["lote_nome_unificado"][0]

        self.stdout.write(
            self.style.SUCCESS(
                f"Renomeando lote {lote_nome_1} para {lote_nome_unificado}"
            )
        )
        lote_1 = Lote.objects.get(nome__icontains=lote_nome_1)
        lote_1.nome = lote_nome_unificado
        lote_1.save()
        lote_2 = Lote.objects.get(nome__icontains=lote_nome_2)

        self.stdout.write(self.style.SUCCESS("*** Geral ***"))

        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.escolas.count()} escolas passadas do "
                f"Lote {lote_nome_2} para o {lote_nome_1}"
            )
        )
        lote_2.escolas.update(lote=lote_1)
        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.contratos_do_lote.count()} "
                f"referências de contratos do lote {lote_nome_2} excluídas"
            )
        )
        for contrato in lote_2.contratos_do_lote.all():
            lote_2.contratos_do_lote.remove(contrato)

        self.stdout.write(self.style.SUCCESS("*** Gestão de Alimentação ***"))

        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.cardapio_alteracaocardapio_rastro_lote.count()} "
                f"alterações de cardápio passadas do Lote {lote_nome_2} "
                f"para o {lote_nome_1}"
            )
        )
        lote_2.cardapio_alteracaocardapio_rastro_lote.update(rastro_lote=lote_1)
        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.cardapio_alteracaocardapiocei_rastro_lote.count()} "
                f"alterações de cardápio CEI passadas do Lote {lote_nome_2} "
                f"para o {lote_nome_1}"
            )
        )
        lote_2.cardapio_alteracaocardapiocei_rastro_lote.update(rastro_lote=lote_1)
        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.cardapio_alteracaocardapiocemei_rastro_lote.count()} "
                f"alterações de cardápio CEMEI passadas do Lote {lote_nome_2} "
                f"para o {lote_nome_1}"
            )
        )
        lote_2.cardapio_alteracaocardapiocemei_rastro_lote.update(rastro_lote=lote_1)
        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.cardapio_gruposuspensaoalimentacao_rastro_lote.count()} "
                f"suspensões de alimentação passadas do Lote {lote_nome_2} "
                f"para o {lote_nome_1}"
            )
        )
        lote_2.cardapio_gruposuspensaoalimentacao_rastro_lote.update(rastro_lote=lote_1)
        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.cardapio_inversaocardapio_rastro_lote.count()} "
                f"inversões de cardápio passadas do Lote {lote_nome_2} "
                f"para o {lote_nome_1}"
            )
        )
        lote_2.cardapio_inversaocardapio_rastro_lote.update(rastro_lote=lote_1)

        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.cardapio_suspensaoalimentacaodacei_rastro_lote.count()} "
                f"suspensões de alimentação CEI passadas do Lote {lote_nome_2} "
                f"para o {lote_nome_1}"
            )
        )
        lote_2.cardapio_suspensaoalimentacaodacei_rastro_lote.update(rastro_lote=lote_1)

        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.inclusao_alimentacao_grupoinclusaoalimentacaonormal_rastro_lote.count()} "
                f"inclusões de alimentação passadas do Lote {lote_nome_2} para o {lote_nome_1}"
            )
        )
        lote_2.inclusao_alimentacao_grupoinclusaoalimentacaonormal_rastro_lote.update(
            rastro_lote=lote_1
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.inclusao_alimentacao_inclusaoalimentacaocontinua_rastro_lote.count()} "
                f"inclusões de alimentação contínuas passadas do Lote {lote_nome_2} "
                f"para o {lote_nome_1}"
            )
        )
        lote_2.inclusao_alimentacao_inclusaoalimentacaocontinua_rastro_lote.update(
            rastro_lote=lote_1
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.inclusao_alimentacao_inclusaoalimentacaodacei_rastro_lote.count()} "
                f"inclusões de alimentação CEI passadas do Lote {lote_nome_2} para o {lote_nome_1}"
            )
        )
        lote_2.inclusao_alimentacao_inclusaoalimentacaodacei_rastro_lote.update(
            rastro_lote=lote_1
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.inclusao_alimentacao_inclusaodealimentacaocemei_rastro_lote.count()} "
                f"inclusões de alimentação CEMEI passadas do Lote {lote_nome_2} para o {lote_nome_1}"
            )
        )
        lote_2.inclusao_alimentacao_inclusaodealimentacaocemei_rastro_lote.update(
            rastro_lote=lote_1
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.inclusao_alimentacao_inclusaodealimentacaocemei_rastro_lote.count()} "
                f"kit lanches passados do Lote {lote_nome_2} para o {lote_nome_1}"
            )
        )
        lote_2.kit_lanche_solicitacaokitlancheavulsa_rastro_lote.update(
            rastro_lote=lote_1
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.kit_lanche_solicitacaokitlancheceiavulsa_rastro_lote.count()} "
                f"kit lanches CEI passados do Lote {lote_nome_2} para o {lote_nome_1}"
            )
        )
        lote_2.kit_lanche_solicitacaokitlancheceiavulsa_rastro_lote.update(
            rastro_lote=lote_1
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.kit_lanche_solicitacaokitlanchecemei_rastro_lote.count()} "
                f"kit lanches CEMEI passados do Lote {lote_nome_2} para o {lote_nome_1}"
            )
        )
        lote_2.kit_lanche_solicitacaokitlanchecemei_rastro_lote.update(
            rastro_lote=lote_1
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.kit_lanche_solicitacaokitlancheunificada_rastro_lote.count()} "
                f"kit lanches unificados passados do Lote {lote_nome_2} para o {lote_nome_1}"
            )
        )
        lote_2.kit_lanche_solicitacaokitlancheunificada_rastro_lote.update(
            rastro_lote=lote_1
        )

        self.stdout.write(self.style.SUCCESS("*** Dieta Especial ***"))

        self.stdout.write(
            self.style.SUCCESS(
                f"{lote_2.dieta_especial_solicitacaodietaespecial_rastro_lote.count()} "
                f"solicitações de dieta especial passadas do Lote {lote_nome_2} "
                f"para o {lote_nome_1}"
            )
        )
        lote_2.dieta_especial_solicitacaodietaespecial_rastro_lote.update(
            rastro_lote=lote_1
        )

        self.stdout.write(self.style.SUCCESS(f"Exclui o lote {lote_nome_2}"))
        lote_2.delete()
