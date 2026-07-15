from django.core.management import BaseCommand

from src.dados_comuns.models import LogSolicitacoesUsuario
from src.produto.models import HomologacaoProduto, Produto, ProdutoEdital


class Command(BaseCommand):
    help = "Cria objetos DataHoraVinculoProdutoEdital para todos os produtos"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Iniciando processo de criação dos dados"))
        produtos = Produto.objects.filter(vinculos__isnull=False).distinct()
        self.stdout.write(
            self.style.SUCCESS(
                f"Criando objetos DataHora de {produtos.count()} produtos simples..."
            )
        )
        self.cria_datas_horas_dos_vinculos_do_produto(produtos)
        self.stdout.write(
            self.style.SUCCESS(
                f"DataHora de {produtos.count()} produtos simples finalizado."
            )
        )
        self.stdout.write(
            self.style.SUCCESS("Verificando quantidade de produtos complexos...")
        )
        hom_produtos_complexos_uuids = self.produtos_complexos()
        self.stdout.write(
            self.style.SUCCESS(
                "Criando objetos DataHora de "
                f"{len(hom_produtos_complexos_uuids)} produtos complexos..."
            )
        )
        self.lida_com_produtos_complexos(hom_produtos_complexos_uuids)
        self.stdout.write(
            self.style.SUCCESS(
                f"DataHora de {len(hom_produtos_complexos_uuids)} "
                "produtos complexos finalizado."
            )
        )
        uuids_suspensos_editais = LogSolicitacoesUsuario.objects.filter(
            status_evento=LogSolicitacoesUsuario.SUSPENSO_EM_ALGUNS_EDITAIS
        ).values_list("uuid_original", flat=True)
        self.stdout.write(
            self.style.SUCCESS(
                "Criando objetos DataHora de "
                f"{len(uuids_suspensos_editais)} produtos com log de editais suspensos..."
            )
        )
        self.lida_com_log_editais_suspensos(uuids_suspensos_editais)
        self.stdout.write(
            self.style.SUCCESS(
                f"DataHora de {len(uuids_suspensos_editais)} produtos finalizado."
            )
        )
        self.stdout.write(
            self.style.SUCCESS("Finalizando processo de migracao de dados")
        )

    def cria_datas_horas_dos_vinculos_do_produto(self, produtos):
        for index, produto in enumerate(produtos):
            for produto_edital in produto.vinculos.all():
                data_hora = produto_edital.criar_data_hora_vinculo()
                data_hora.criado_em = produto_edital.criado_em
                data_hora.save()
                if produto_edital.edital.numero == "Edital de Pregão n°78/SME/2016":
                    data_hora.criado_em = produto_edital.produto.data_homologacao
                    data_hora.save()
            if index % 100 == 0 and index:
                self.stdout.write(self.style.SUCCESS(f"Já foram {index}..."))

    def produtos_complexos(self):
        produtos = Produto.objects.filter(vinculos__isnull=False).distinct()
        prods_log_editais = []
        for produto in produtos:
            hom = produto.homologacao
            for log in hom.logs.all():
                if (
                    "suspen" in log.get_status_evento_display()
                    or "não homol" in log.get_status_evento_display()
                    or "autorizou reclamação" in log.get_status_evento_display()
                ):
                    prods_log_editais.append(hom.uuid)
                    continue
        return prods_log_editais

    def lida_com_produtos_complexos(self, hom_produtos_complexos_uuids):
        hom_produtos = HomologacaoProduto.objects.filter(
            uuid__in=hom_produtos_complexos_uuids
        )
        for hom_produto in hom_produtos:
            for log in hom_produto.logs.all():
                if log.status_evento in [
                    LogSolicitacoesUsuario.CODAE_AUTORIZOU_RECLAMACAO,
                    LogSolicitacoesUsuario.CODAE_NAO_HOMOLOGADO,
                    LogSolicitacoesUsuario.CODAE_AUTORIZOU_RECLAMACAO,
                    LogSolicitacoesUsuario.CODAE_SUSPENDEU,
                ]:
                    for produto_edital in hom_produto.produto.vinculos.all():
                        data_hora_vinculo = produto_edital.criar_data_hora_vinculo(
                            suspenso=True
                        )
                        data_hora_vinculo.criado_em = log.criado_em
                        data_hora_vinculo.save()

    def lida_com_log_editais_suspensos(self, uuids_suspensos_editais):
        hom_produtos = HomologacaoProduto.objects.filter(
            uuid__in=uuids_suspensos_editais
        )
        for hom_produto in hom_produtos:
            for log in hom_produto.logs.all():
                if log.get_status_evento_display() == "Suspenso em alguns editais":
                    editais = log.justificativa.split("<p>Editais suspensos:</p>")[1][
                        3:-4
                    ].split(", ")
                    for edital in editais:
                        produto_edital = ProdutoEdital.objects.get(
                            produto=hom_produto.produto, edital__numero=edital
                        )
                        dh = produto_edital.criar_data_hora_vinculo(suspenso=True)
                        dh.criado_em = log.criado_em
                        dh.save()
