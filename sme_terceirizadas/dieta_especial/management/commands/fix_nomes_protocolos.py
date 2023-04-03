from django.core.management.base import BaseCommand

from sme_terceirizadas.dieta_especial.models import ProtocoloPadraoDietaEspecial, SolicitacaoDietaEspecial


class Command(BaseCommand):
    help = """
    Corrigir caracteres especiais nos nomes dos portocolos salvos e nas solicitações de Dieta Especial
    """

    def fix_nome_protocolo(self, queryset):
        for instance in queryset.filter(nome_protocolo__icontains='–'):
            instance.nome_protocolo = instance.nome_protocolo.replace('–', '-')
            instance.save()

    def handle(self, *args, **options):
        protocolos = ProtocoloPadraoDietaEspecial.objects.all()
        status = SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO
        solicitacoes = SolicitacaoDietaEspecial.objects.filter(eh_importado=True, ativo=True, status=status)
        self.fix_nome_protocolo(protocolos)
        self.fix_nome_protocolo(solicitacoes)
