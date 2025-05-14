from django.db import models

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.managers.alteracao_tipo_alimentacao_managers import (
    AlteracoesCardapioDestaSemanaManager,
    AlteracoesCardapioDesteMesManager,
    AlteracoesCardapioDoMesCorrenteManager,
    AlteracoesCardapioVencidaManager,
)


class EhAlteracaoCardapio(models.Model):
    objects = models.Manager()  # Manager Padrão
    desta_semana = AlteracoesCardapioDestaSemanaManager()
    deste_mes = AlteracoesCardapioDesteMesManager()
    vencidos = AlteracoesCardapioVencidaManager()
    do_mes_corrente = AlteracoesCardapioDoMesCorrenteManager()

    escola = models.ForeignKey(
        "escola.Escola", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    motivo = models.ForeignKey(
        "MotivoAlteracaoCardapio", on_delete=models.PROTECT, blank=True, null=True
    )

    @classmethod
    def get_rascunhos_do_usuario(cls, usuario):
        return cls.objects.filter(
            criado_por=usuario, status=cls.workflow_class.RASCUNHO
        )

    class Meta:
        abstract = True
