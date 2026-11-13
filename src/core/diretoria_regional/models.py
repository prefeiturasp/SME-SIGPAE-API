from __future__ import annotations

from django.db.models import Q, Sum

from ...cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
from ...cardapio.alteracao_tipo_alimentacao_cei.models import AlteracaoCardapioCEI
from ...cardapio.alteracao_tipo_alimentacao_cemei.models import AlteracaoCardapioCEMEI
from ...cardapio.inversao_dia_cardapio.models import InversaoCardapio
from ...dados_comuns.behaviors import (
    AcessoModuloMedicaoInicial,
    Iniciais,
    Nomeavel,
    TemChaveExterna,
    TemCodigoEOL,
    TemVinculos,
)
from ...dados_comuns.utils import queryset_por_data
from ...inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
    InclusaoAlimentacaoDaCEI,
    InclusaoDeAlimentacaoCEMEI,
)
from ...kit_lanche.models import (
    SolicitacaoKitLancheAvulsa,
    SolicitacaoKitLancheCEIAvulsa,
    SolicitacaoKitLancheCEMEI,
)
from ..constants import ESCOLA_TIPO_GESTAO_NOME


class DiretoriaRegional(
    Nomeavel,
    Iniciais,
    TemChaveExterna,
    TemCodigoEOL,
    TemVinculos,
    AcessoModuloMedicaoInicial,
):
    @property
    def editais(self):
        return [
            str(uuid_)
            for uuid_ in set(
                list(
                    set(
                        self.escolas.filter(
                            lote__isnull=False,
                            lote__contratos_do_lote__edital__isnull=False,
                            lote__contratos_do_lote__encerrado=False,
                        ).values_list(
                            "lote__contratos_do_lote__edital__uuid", flat=True
                        )
                    )
                )
            )
        ]

    @property
    def vinculos_que_podem_ser_finalizados(self):
        return self.vinculos.filter(
            Q(data_inicial=None, data_final=None, ativo=False)
            | Q(  # noqa W504 esperando ativacao
                data_inicial__isnull=False, data_final=None, ativo=True
            )  # noqa W504 ativo
        )

    @property
    def quantidade_alunos(self):
        from ..escola.models import AlunosMatriculadosPeriodoEscola

        quantidade_result = AlunosMatriculadosPeriodoEscola.objects.filter(
            escola__in=self.escolas.all(), tipo_turma="REGULAR"
        ).aggregate(Sum("quantidade_alunos"))
        return quantidade_result.get("quantidade_alunos__sum") or 0

    @property
    def quantidade_alunos_terceirizada(self):
        from ..escola.models import AlunosMatriculadosPeriodoEscola

        quantidade_result = AlunosMatriculadosPeriodoEscola.objects.filter(
            escola__in=self.escolas.all(),
            tipo_turma="REGULAR",
            escola__tipo_gestao__nome=ESCOLA_TIPO_GESTAO_NOME,
        ).aggregate(Sum("quantidade_alunos"))
        return quantidade_result.get("quantidade_alunos__sum") or 0

    @property
    def quantidade_alunos_parceira(self):
        from ..escola.models import AlunosMatriculadosPeriodoEscola

        quantidade_result = AlunosMatriculadosPeriodoEscola.objects.filter(
            escola__in=self.escolas.all(),
            tipo_turma="REGULAR",
            escola__tipo_gestao__nome="PARCEIRA",
        ).aggregate(Sum("quantidade_alunos"))
        return quantidade_result.get("quantidade_alunos__sum") or 0

    #
    # Inclusões continuas e normais
    #

    @property
    def inclusoes_continuas_autorizadas(self):
        return InclusaoAlimentacaoContinua.objects.filter(
            escola__in=self.escolas.all(),
            status__in=[
                GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
                GrupoInclusaoAlimentacaoNormal.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
        )

    @property
    def inclusoes_normais_autorizadas(self):
        return GrupoInclusaoAlimentacaoNormal.objects.filter(
            escola__in=self.escolas.all(),
            status__in=[
                GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
                GrupoInclusaoAlimentacaoNormal.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
        )

    @property
    def inclusoes_continuas_reprovadas(self):
        return InclusaoAlimentacaoContinua.objects.filter(
            escola__in=self.escolas.all(),
            status=InclusaoAlimentacaoContinua.workflow_class.DRE_NAO_VALIDOU_PEDIDO_ESCOLA,
        )

    @property
    def inclusoes_normais_reprovadas(self):
        return GrupoInclusaoAlimentacaoNormal.objects.filter(
            escola__in=self.escolas.all(),
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.DRE_NAO_VALIDOU_PEDIDO_ESCOLA,
        )

    def filtra_solicitacoes_minhas_escolas_a_validar_por_data(
        self, filtro_aplicado, model
    ):
        queryset = queryset_por_data(filtro_aplicado, model)
        return queryset.filter(
            escola__in=self.escolas.all(),
            status=SolicitacaoKitLancheAvulsa.workflow_class.DRE_A_VALIDAR,
        )

    def solicitacoes_kit_lanche_das_minhas_escolas_a_validar(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, SolicitacaoKitLancheAvulsa
        )

    def solicitacoes_kit_lanche_cei_das_minhas_escolas_a_validar(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, SolicitacaoKitLancheCEIAvulsa
        )

    def solicitacoes_kit_lanche_cemei_das_minhas_escolas_a_validar(
        self, filtro_aplicado
    ):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, SolicitacaoKitLancheCEMEI
        )

    def alteracoes_cardapio_das_minhas_escolas_a_validar(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, AlteracaoCardapio
        )

    def alteracoes_cardapio_cei_das_minhas_escolas_a_validar(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, AlteracaoCardapioCEI
        )

    def inclusoes_alimentacao_continua_das_minhas_escolas(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, InclusaoAlimentacaoContinua
        )

    def grupos_inclusoes_alimentacao_normal_das_minhas_escolas(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, GrupoInclusaoAlimentacaoNormal
        )

    def inclusoes_alimentacao_de_cei_das_minhas_escolas(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, InclusaoAlimentacaoDaCEI
        )

    def inclusoes_alimentacao_cemei_das_minhas_escolas(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, InclusaoDeAlimentacaoCEMEI
        )

    #
    # Alterações de cardápio
    #

    @property
    def alteracoes_cardapio_pendentes_das_minhas_escolas(self):
        return AlteracaoCardapio.objects.filter(
            escola__in=self.escolas.all(),
            status=AlteracaoCardapio.workflow_class.DRE_A_VALIDAR,
        )

    @property
    def alteracoes_cardapio_autorizadas(self):
        return AlteracaoCardapio.objects.filter(
            escola__in=self.escolas.all(),
            status__in=[
                AlteracaoCardapio.workflow_class.CODAE_AUTORIZADO,
                AlteracaoCardapio.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
        )

    @property
    def solicitacao_kit_lanche_avulsa_autorizadas(self):
        return SolicitacaoKitLancheAvulsa.objects.filter(
            escola__in=self.escolas.all(),
            status__in=[
                SolicitacaoKitLancheAvulsa.workflow_class.CODAE_AUTORIZADO,
                SolicitacaoKitLancheAvulsa.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
        )

    @property
    def solicitacao_kit_lanche_avulsa_reprovados(self):
        return SolicitacaoKitLancheAvulsa.objects.filter(
            escola__in=self.escolas.all(),
            status=SolicitacaoKitLancheAvulsa.workflow_class.DRE_PEDIU_ESCOLA_REVISAR,
        )

    @property
    def alteracoes_cardapio_reprovadas(self):
        return AlteracaoCardapio.objects.filter(
            escola__in=self.escolas.all(),
            status=AlteracaoCardapio.workflow_class.DRE_NAO_VALIDOU_PEDIDO_ESCOLA,
        )

    def alteracoes_cardapio_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, AlteracaoCardapio)
        return queryset.filter(
            escola__in=self.escolas.all(),
            status=AlteracaoCardapio.workflow_class.DRE_A_VALIDAR,
        )

    def alteracoes_cardapio_cei_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, AlteracaoCardapioCEI)
        return queryset.filter(
            escola__in=self.escolas.all(),
            status=AlteracaoCardapioCEI.workflow_class.DRE_A_VALIDAR,
        )

    def alteracoes_cardapio_cemei_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, AlteracaoCardapioCEMEI)
        return queryset.filter(
            escola__in=self.escolas.all(),
            status=AlteracaoCardapioCEMEI.workflow_class.DRE_A_VALIDAR,
        )

    #
    # Inversões de cardápio
    #

    def inversoes_cardapio_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, InversaoCardapio)
        return queryset.filter(
            escola__in=self.escolas.all(),
            status=InversaoCardapio.workflow_class.DRE_A_VALIDAR,
        )

    @property
    def inversoes_cardapio_autorizadas(self):
        return InversaoCardapio.objects.filter(
            escola__in=self.escolas.all(),
            status__in=[
                InversaoCardapio.workflow_class.DRE_VALIDADO,
                InversaoCardapio.workflow_class.CODAE_AUTORIZADO,
                InversaoCardapio.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
        )

    @property
    def inversoes_cardapio_reprovados(self):
        return InversaoCardapio.objects.filter(
            escola__in=self.escolas.all(),
            status__in=[InversaoCardapio.workflow_class.DRE_NAO_VALIDOU_PEDIDO_ESCOLA],
        )

    @property
    def possui_escolas_com_acesso_ao_medicao_inicial(self):
        return (
            self.acesso_modulo_medicao_inicial
            or self.escolas.filter(acesso_modulo_medicao_inicial=True).exists()
        )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Diretoria regional"
        verbose_name_plural = "Diretorias regionais"
        ordering = ("nome",)
