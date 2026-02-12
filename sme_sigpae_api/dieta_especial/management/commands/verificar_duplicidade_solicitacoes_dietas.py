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

    def _formatar_data(self, obj, campo, formato="%d/%m/%Y"):
        """Formata uma data do objeto ou retorna '-' se não existir."""
        valor = getattr(obj, campo, None)
        if valor and hasattr(valor, "strftime"):
            return valor.strftime(formato)
        return str(valor) if valor else "-"

    def _extrair_dados_solicitacao(self, solicitacao):
        """Extrai e formata todos os dados de uma solicitação para o Excel."""
        aluno = solicitacao.aluno
        return [
            str(solicitacao.uuid),
            getattr(aluno, "codigo_eol", "-"),
            getattr(aluno, "nome", "-"),
            getattr(solicitacao.rastro_dre, "nome", "-"),
            getattr(solicitacao.rastro_escola, "nome", "-"),
            getattr(solicitacao.classificacao, "nome", "Sem classificação"),
            self._formatar_data(solicitacao, "data_inicio"),
            self._formatar_data(solicitacao, "data_termino"),
            self._formatar_data(solicitacao, "criado_em", "%d/%m/%Y %H:%M"),
            self._formatar_data(solicitacao, "data_ultimo_log", "%d/%m/%Y %H:%M"),
        ]

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
                dados = self._extrair_dados_solicitacao(s)
                ws.append(dados)
                total += 1

            ws.append([])

        wb.save(filename)

        self.stdout.write(
            self.style.SUCCESS(
                f"Planilha gerada com sucesso em: {filename} ({total} solicitações duplicadas encontradas)"
            )
        )
