from django.db import models

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.managers.alteracao_tipo_alimentacao_managers import (
    AlteracoesCardapioDestaSemanaManager,
    AlteracoesCardapioDesteMesManager,
    AlteracoesCardapioDoMesCorrenteManager,
    AlteracoesCardapioVencidaManager,
)


class TemLabelDeTiposDeAlimentacao(models.Model):
    @property
    def label(self):
        label = ""
        for tipo_alimentacao in self.tipos_alimentacao.all():
            if len(label) == 0:
                label += tipo_alimentacao.nome
            else:
                label += f" e {tipo_alimentacao.nome}"
        return label

    class Meta:
        abstract = True


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
