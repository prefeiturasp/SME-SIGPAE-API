import os
from collections import defaultdict
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from openpyxl import Workbook

from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial


class Command(BaseCommand):
    help = (
        "Detecta alunos com mais de uma dieta especial autorizada e exporta para Excel."
    )

    def handle(self, *args, **options):
        self.stdout.write("Buscando solicitações de dieta especial autorizadas...")

        solicitacoes = (
            SolicitacaoDietaEspecial.objects.filter(
                ativo=True,
                status="CODAE_AUTORIZADO",
            )
            .select_related("aluno", "rastro_escola", "rastro_dre", "classificacao")
            .order_by("aluno__codigo_eol", "data_inicio")
        )

        duplicadas = self._detectar_duplicidades(solicitacoes)

        if not duplicadas:
            self.stdout.write(self.style.SUCCESS("Nenhuma duplicidade encontrada."))
            return

        self._exportar_para_excel(duplicadas)

    def _detectar_duplicidades(self, solicitacoes):
        """
        Retorna considerando apenas alunos que possuem pelo menos duas solicitações ativas autorizadas.
        """
        por_eol = self._agrupa_aluno_eol(solicitacoes)
        duplicadas = {eol: lista for eol, lista in por_eol.items() if len(lista) > 1}
        return duplicadas

    def _agrupa_aluno_eol(self, solicitacoes):
        """Agrupa queryset por codigo_eol do aluno"""
        por_eol = defaultdict(list)
        for s in solicitacoes:
            codigo_eol = getattr(s.aluno, "codigo_eol", None)
            if codigo_eol:
                por_eol[codigo_eol].append(s)
        return por_eol

    def _exportar_para_excel(self, duplicadas):
        output_dir = os.path.join(settings.MEDIA_ROOT, "exportacao_solicitacoes")
        os.makedirs(output_dir, exist_ok=True)

        data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(
            output_dir, f"solicitacoes_duplicadas_{data_atual}.xlsx"
        )

        wb = Workbook()
        ws = wb.active
        ws.title = "Duplicidades"

        ws.append(
            [
                "UUID Solicitação",
                "Código EOL",
                "Aluno",
                "DRE",
                "Unidade Escolar",
                "Classificação da Dieta",
                "Data Início",
                "Data Término",
                "Data Criação",
                "Data Último Log",
            ]
        )

        total = 0

        for eol in sorted(duplicadas.keys()):
            solicitacoes = duplicadas[eol]

            solicitacoes.sort(key=lambda s: s.data_ultimo_log or datetime.min)

            for s in solicitacoes:
                aluno = s.aluno
                aluno_nome = getattr(aluno, "nome", "-")
                codigo_eol = getattr(aluno, "codigo_eol", "-")
                dre_nome = getattr(s.rastro_dre, "nome", "-")
                ue_nome = getattr(s.rastro_escola, "nome", "-")
                classificacao = getattr(s.classificacao, "nome", "Sem classificação")

                criado_em = (
                    s.criado_em.strftime("%d/%m/%Y %H:%M")
                    if hasattr(s, "criado_em") and hasattr(s.criado_em, "strftime")
                    else str(getattr(s, "criado_em", "-"))
                )
                data_inicio = (
                    s.data_inicio.strftime("%d/%m/%Y")
                    if hasattr(s, "data_inicio") and hasattr(s.data_inicio, "strftime")
                    else str(getattr(s, "data_inicio", "-"))
                )
                data_termino = (
                    s.data_termino.strftime("%d/%m/%Y")
                    if hasattr(s, "data_termino")
                    and hasattr(s.data_termino, "strftime")
                    else str(getattr(s, "data_termino", "-"))
                )
                data_ultimo_log = (
                    s.data_ultimo_log.strftime("%d/%m/%Y %H:%M")
                    if hasattr(s, "data_ultimo_log")
                    and hasattr(s.data_ultimo_log, "strftime")
                    else str(getattr(s, "data_ultimo_log", "-"))
                )

                ws.append(
                    [
                        str(s.uuid),
                        codigo_eol,
                        aluno_nome,
                        dre_nome,
                        ue_nome,
                        classificacao,
                        data_inicio,
                        data_termino,
                        criado_em,
                        data_ultimo_log,
                    ]
                )
                total += 1

            ws.append([])

        wb.save(filename)

        self.stdout.write(
            self.style.SUCCESS(
                f"Planilha gerada com sucesso em: {filename} ({total} solicitações duplicadas encontradas)"
            )
        )
