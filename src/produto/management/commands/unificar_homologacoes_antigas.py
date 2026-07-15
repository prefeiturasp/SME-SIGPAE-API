from django.core.management import BaseCommand

from src.dados_comuns.fluxo_status import HomologacaoProdutoWorkflow
from src.produto.models import HomologacaoProduto, Produto


class Command(BaseCommand):
    help = "Unificar todas homologacoes em uma unica instancia do modelo HomologacaoProduto."

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("*** Iniciando processo de migracao de dados ***")
        )
        queryset = Produto.objects.exclude(homologacoes=None)
        for produto in queryset:
            self.stdout.write(
                self.style.SUCCESS(
                    "****************************************************************"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"*** Unificando homologacoes do produto: {produto.uuid} ***"
                )
            )
            self.stdout.write(self.style.SUCCESS(f"*** Nome: {produto.nome} ***"))
            self.stdout.write(
                self.style.SUCCESS(f"*** Marca: {produto.marca.nome} ***")
            )
            self.stdout.write(
                self.style.SUCCESS(f"*** Fabricante: {produto.fabricante.nome} ***")
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "****************************************************************"
                )
            )
            self.create_homologacao_produto(produto)
        self.stdout.write(
            self.style.SUCCESS("*** Finalizando processo de migracao de dados ***")
        )

    def get_pdf_gerado(self, homologacoes):
        if homologacoes.filter(pdf_gerado=True).count() > 0:
            return True
        else:
            return False

    def get_protocolo_analise_sensorial(self, homologacoes_com_protocolo):
        if homologacoes_com_protocolo.count() > 0:
            return homologacoes_com_protocolo.last().protocolo_analise_sensorial
        else:
            return ""

    def get_necessita_analise_sensorial(self, status):
        if status == HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_SENSORIAL:
            return True
        else:
            return False

    def relacionar_logs(self, uuid, logs):
        for log in logs:
            log.uuid_original = uuid
            log.save()

    def relacionar_reclamacoes(self, nova_homologacao, reclamacoes):
        for reclamacao in reclamacoes:
            reclamacao.homologacao_produto = nova_homologacao
            reclamacao.save()

    def relacionar_analises_sensoriais(self, nova_homologacao, analises_sensoriais):
        for analise_sensorial in analises_sensoriais:
            analise_sensorial.homologacao_produto = nova_homologacao
            analise_sensorial.save()

    def atribuir_relacionamentos(self, nova_homologacao, homologacoes):
        for homologacao in homologacoes:
            self.relacionar_logs(nova_homologacao.uuid, homologacao.logs.all())
            self.relacionar_reclamacoes(nova_homologacao, homologacao.reclamacoes.all())
            self.relacionar_analises_sensoriais(
                nova_homologacao, homologacao.analises_sensoriais.all()
            )

    def create_homologacao_produto(self, produto):
        homologacoes = produto.homologacoes.order_by("criado_em")
        primeira_homologacao = homologacoes.first()
        ultima_homologacao = homologacoes.last()

        homologacoes_com_protocolo = homologacoes.exclude(
            protocolo_analise_sensorial=""
        )

        pdf_gerado = self.get_pdf_gerado(homologacoes)
        protocolo_analise_sensorial = self.get_protocolo_analise_sensorial(
            homologacoes_com_protocolo
        )
        necessita_analise_sensorial = self.get_necessita_analise_sensorial(
            ultima_homologacao.status
        )

        nova_homologacao = HomologacaoProduto(
            produto=produto,
            pdf_gerado=pdf_gerado,
            rastro_terceirizada=primeira_homologacao.rastro_terceirizada,
            criado_por=primeira_homologacao.criado_por,
            ativo=ultima_homologacao.ativo,
            status=ultima_homologacao.status,
            necessita_analise_sensorial=necessita_analise_sensorial,
            protocolo_analise_sensorial=protocolo_analise_sensorial,
        )

        nova_homologacao.save()
        self.atribuir_relacionamentos(nova_homologacao, homologacoes)
