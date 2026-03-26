from django.db import models

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.managers.alteracao_tipo_alimentacao_managers import (
    AlteracoesCardapioDestaSemanaManager,
    AlteracoesCardapioDesteMesManager,
    AlteracoesCardapioDoMesCorrenteManager,
    AlteracoesCardapioVencidaManager,
)


class EhAlteracaoCardapio(models.Model):
    """Classe abstrata com campos e consultas comuns das solicitações de alteração de cardápio.

    Centraliza os relacionamentos compartilhados entre os modelos de alteração de
    cardápio e expõe managers especializados para consultas por período, além de
    um método utilitário para recuperar rascunhos de um usuário.

    Attributes:
        objects (django.db.models.Manager): Manager padrão do Django.
        desta_semana (AlteracoesCardapioDestaSemanaManager): Manager para
            solicitações cuja data esteja na semana atual.
        deste_mes (AlteracoesCardapioDesteMesManager): Manager para
            solicitações cuja data esteja no mês atual.
        vencidos (AlteracoesCardapioVencidaManager): Manager para solicitações
            com período já encerrado.
        do_mes_corrente (AlteracoesCardapioDoMesCorrenteManager): Manager para
            solicitações do mês corrente, conforme regra de negócio do módulo.
    """

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
        """Retorna os rascunhos criados por um usuário.

        Args:
            usuario (perfil.Usuario): Usuário autor dos rascunhos.

        Returns:
            django.db.models.QuerySet: Conjunto de solicitações em status
            ``RASCUNHO`` criadas pelo usuário informado.
        """

        return cls.objects.filter(
            criado_por=usuario, status=cls.workflow_class.RASCUNHO
        )

    class Meta:
        abstract = True
