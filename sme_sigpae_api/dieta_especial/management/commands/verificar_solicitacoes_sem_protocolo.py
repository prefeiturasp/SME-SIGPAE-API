import os
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from openpyxl import Workbook

from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial


class Command(BaseCommand):
    help = "Verifica solicitações de dieta especial autorizadas sem protocolo e exporta para Excel."

    def handle(self, *args, **options):
        self.stdout.write("Buscando solicitações autorizadas sem protocolo...")

        solicitacoes = (
            SolicitacaoDietaEspecial.objects.filter(
                ativo=True,
                status="CODAE_AUTORIZADO",
                protocolo_padrao__isnull=True,
            )
            .select_related("aluno", "rastro_escola", "rastro_dre", "classificacao")
            .order_by("criado_em")
        )

        total = solicitacoes.count()

        if total == 0:
            self.stdout.write(
                self.style.SUCCESS("Nenhuma solicitação sem protocolo encontrada.")
            )
            return

        output_dir = os.path.join(settings.MEDIA_ROOT, "exportacao_solicitacoes")
        os.makedirs(output_dir, exist_ok=True)

        data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(
            output_dir, f"solicitacoes_sem_protocolo_{data_atual}.xlsx"
        )

        wb = Workbook()
        ws = wb.active
        ws.title = "Sem Protocolo"

        ws.append(
            [
                "UUID Solicitação",
                "Código EOL",
                "Aluno",
                "DRE",
                "Unidade Escolar",
                "Classificação da Dieta",
                "Data Criação",
                "Data Último Log",
            ]
        )

        for solicitacao in solicitacoes:
            aluno = solicitacao.aluno
            aluno_nome = getattr(aluno, "nome", "-")
            codigo_eol = getattr(aluno, "codigo_eol", "-")

            dre_nome = getattr(solicitacao.rastro_dre, "nome", "-")
            ue_nome = getattr(solicitacao.rastro_escola, "nome", "-")

            classificacao = getattr(
                solicitacao.classificacao, "nome", "Sem classificação"
            )

            criado_em = (
                solicitacao.criado_em.strftime("%d/%m/%Y %H:%M")
                if hasattr(solicitacao, "criado_em")
                and hasattr(solicitacao.criado_em, "strftime")
                else str(getattr(solicitacao, "criado_em", "-"))
            )

            ws.append(
                [
                    str(solicitacao.uuid),
                    codigo_eol,
                    aluno_nome,
                    dre_nome,
                    ue_nome,
                    classificacao,
                    criado_em,
                    solicitacao.data_ultimo_log,
                ]
            )

        wb.save(filename)

        self.stdout.write(
            self.style.SUCCESS(
                f"Planilha gerada com sucesso em: {filename} ({total} solicitações encontradas)"
            )
        )
