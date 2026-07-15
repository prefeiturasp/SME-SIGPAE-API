from django.core.management.base import BaseCommand

from src.produto.models import HomologacaoProduto, ProdutoEdital
from src.terceirizada.models import Edital


class Command(BaseCommand):
    help = "Vincular produtos homologados em produtoção ao edital número: Edital de Pregão n°78/SME/2016"

    def handle(self, *args, **options):
        self.stdout.write("Vinculando produtos")

        edital = Edital.objects.get(numero="Edital de Pregão n°78/SME/2016")
        info = ""

        for hom in HomologacaoProduto.objects.filter(
            status=HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO
        ):
            if hom.produto.eh_para_alunos_com_dieta:
                tipo_produto = "Dieta especial"
            else:
                tipo_produto = "Comum"

            if not ProdutoEdital.objects.filter(
                produto=hom.produto, edital=edital
            ).exists():
                pe = ProdutoEdital(
                    produto=hom.produto,
                    edital=edital,
                    tipo_produto=tipo_produto,
                    outras_informacoes=info,
                )
                pe.save()
        self.stdout.write("Processo finalizado")
