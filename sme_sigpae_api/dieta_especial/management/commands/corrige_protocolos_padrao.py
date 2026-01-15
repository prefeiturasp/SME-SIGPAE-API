import logging

from django.core.management import BaseCommand
from django.db.models import F, Func, Value

from sme_sigpae_api.dieta_especial.models import (
    ProtocoloPadraoDietaEspecial,
    SolicitacaoDietaEspecial,
)

logger = logging.getLogger("sigpae.cmd_corrige_protocolos_padrao_dieta_especial")
NOVO_HIFEN = " - NOVO"
NOVO_PARENTESES = " (NOVO)"


class Command(BaseCommand):
    """Script para corrigir protocolos padrão de dieta especial."""

    help = "Corrige protocolos padrão de dieta especial"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("*** Corrigindo Protocolos Padrão ***"))
        self.remove_novo()
        self.trata_excecoes()
        self.exclui_protocolos_nao_liberados()
        self.inativa_solicitacoes_de_alunos()

    def remove_novo(self):
        self.stdout.write(
            self.style.SUCCESS('Corrigindo protocolos com "NOVO" no nome')
        )
        qtd_novos = (
            ProtocoloPadraoDietaEspecial.objects.filter(
                nome_protocolo__icontains=NOVO_HIFEN
            ).count()
            + ProtocoloPadraoDietaEspecial.objects.filter(
                nome_protocolo__icontains=NOVO_PARENTESES
            ).count()
        )
        ProtocoloPadraoDietaEspecial.objects.filter(
            nome_protocolo__icontains=NOVO_HIFEN
        ).update(
            nome_protocolo=Func(
                F("nome_protocolo"), Value(NOVO_HIFEN), Value(""), function="replace"
            )
        )
        ProtocoloPadraoDietaEspecial.objects.filter(
            nome_protocolo__icontains=NOVO_PARENTESES
        ).update(
            nome_protocolo=Func(
                F("nome_protocolo"), Value(NOVO_PARENTESES), Value(""), function="replace"
            )
        )
        self.stdout.write(self.style.SUCCESS(f"{qtd_novos} corrigidos"))

    def trata_excecoes(self):
        protocolos_a_excluir = [
            "APLV (BEBIDA DE SOJA OU LEITE DE CABRA)",
            "APLV (BEBIDA DE SOJA SABORIZADA)",
            "APLV (APTAMIL DE SOJA)" "APLV (SUCO DE FRUTA)",
        ]
        for nome_protocolo in protocolos_a_excluir:
            try:
                protocolo = ProtocoloPadraoDietaEspecial.objects.get(
                    nome_protocolo=nome_protocolo
                )
                if protocolo.solicitacoes_dietas_especiais.exists():
                    self.stdout.write(
                        self.style.ERROR(
                            f"{nome_protocolo} possui dietas especiais. Não pode ser "
                            "excluído."
                        )
                    )
                else:
                    protocolo.delete()
                    self.stdout.write(
                        self.style.SUCCESS(f"{nome_protocolo} excluido com " "sucesso")
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"EXCEPTION ERROR {nome_protocolo}: {str(e)}")
                )

        ProtocoloPadraoDietaEspecial.objects.filter(
            nome_protocolo="APLV (SUCO DE FRUTA) TERC."
        ).update(nome_protocolo="APLV (SUCO DE FRUTA)")
        self.stdout.write(
            self.style.SUCCESS(
                "APLV (SUCO DE FRUTA) TERC. atualizado para APLV (SUCO DE FRUTA"
            )
        )

        protocolo_nan = ProtocoloPadraoDietaEspecial.objects.get(
            nome_protocolo="INTOLERÂNCIA ALIMENTAR - FÓRMULA (NAN SUPREME)"
        )
        SolicitacaoDietaEspecial.objects.filter(
            protocolo_padrao__nome_protocolo="INTOLERÂNCIA ALIMENTAR – FÓRMULA (NAN SUPREME)"
        ).update(protocolo_padrao=protocolo_nan)
        ProtocoloPadraoDietaEspecial.objects.filter(
            nome_protocolo="INTOLERÂNCIA ALIMENTAR – FÓRMULA (NAN SUPREME)"
        ).delete()
        self.stdout.write(
            self.style.SUCCESS(
                "INTOLERÂNCIA ALIMENTAR – FÓRMULA (NAN SUPREME) excluido com sucesso"
            )
        )

    def exclui_protocolos_nao_liberados(self):
        self.stdout.write(
            self.style.SUCCESS("*** Excluindo protolos não liberados ***")
        )
        for protocolo in ProtocoloPadraoDietaEspecial.objects.filter(
            status="NAO_LIBERADO"
        ):
            try:
                if protocolo.solicitacoes_dietas_especiais.exists():
                    self.stdout.write(
                        self.style.ERROR(
                            f"{protocolo.nome_protocolo} possui dietas especiais. Não pode ser excluído."
                        )
                    )
                else:
                    protocolo.delete()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{protocolo.nome_protocolo} excluido com " "sucesso"
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"EXCEPTION ERROR {protocolo.nome_protocolo}: {str(e)}"
                    )
                )

    def inativa_solicitacoes_de_alunos(self):
        self.stdout.write(
            self.style.SUCCESS("*** Inativa dietas especificas de alunos ***")
        )
        protocolos_a_inativar = [
            "DIETA ENTERAL - LORENA PEREIRA DE CAMPOS",
            "DIETA ENTERAL - MATHEUS GONCALVES MARTINS",
            "DIETA PASTOSA -  ANA VICTÓRIA SOUSA LIMA",
            "DIETA PASTOSA - ISIS YU NA CHOI",
            "DIETA PASTOSA HOMOGENEA - ISIS YU NA CHOI",
            "DIETA PASTOSA HOMOGÊNEA - RICHARD LEAL"
            "SÍNDROME DE PALLISTER-KILLIAN - GIOVANNA GONÇALVES",
        ]
        qtd = ProtocoloPadraoDietaEspecial.objects.filter(
            nome_protocolo__in=protocolos_a_inativar
        ).update(ativo=False)
        self.stdout.write(self.style.SUCCESS(f"{qtd} protocolos inativados"))
