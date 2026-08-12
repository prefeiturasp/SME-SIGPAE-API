from src.dados_comuns.fluxo_status import FichaDeRecebimentoWorkflow
from src.terceirizada.models import Terceirizada


class TermoRecebimentoDefinitivoService:
    """Regra de negócio do Pós-Recebimento referente ao modelo novo.

    As listagens de empresas, contratos, cronogramas e fiscais foram
    movidas para os services/viewsets dos seus respectivos módulos
    (terceirizada, pre_recebimento e perfil). Aqui permanece apenas a
    regra utilizada na criação do Termo de Recebimento Definitivo.
    """

    @staticmethod
    def empresa_tem_ficha_assinada(empresa):
        """Verifica se uma empresa possui ficha de recebimento assinada pela CODAE."""
        return Terceirizada.objects.filter(
            pk=empresa.pk,
            cronograma__etapas__ficha_recebimento__status=(
                FichaDeRecebimentoWorkflow.ASSINADA
            ),
        ).exists()
