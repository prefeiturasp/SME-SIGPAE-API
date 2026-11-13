from __future__ import annotations

from django.db.models import Q, Sum

from ...cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
from ...cardapio.alteracao_tipo_alimentacao_cei.models import AlteracaoCardapioCEI
from ...cardapio.alteracao_tipo_alimentacao_cemei.models import AlteracaoCardapioCEMEI
from ...cardapio.inversao_dia_cardapio.models import InversaoCardapio
from ...cardapio.suspensao_alimentacao.models import GrupoSuspensaoAlimentacao
from ...dados_comuns.behaviors import (
    AcessoModuloMedicaoInicial,
    Nomeavel,
    TemChaveExterna,
    TemVinculos,
)
from ...dados_comuns.constants import (
    COORDENADOR_DIETA_ESPECIAL,
    COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
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
    SolicitacaoKitLancheUnificada,
)
from ..constants import ESCOLA_TIPO_GESTAO_NOME
from ..escola.models import AlunosMatriculadosPeriodoEscola, Escola


class Codae(
    Nomeavel,
    TemChaveExterna,
    TemVinculos,
    AcessoModuloMedicaoInicial,
):
    @property
    def vinculos_que_podem_ser_finalizados(self):
        return self.vinculos.filter(
            Q(data_inicial=None, data_final=None, ativo=False)
            | Q(  # noqa W504 esperando ativacao
                data_inicial__isnull=False, data_final=None, ativo=True
            )  # noqa W504 ativo
        ).exclude(
            perfil__nome__in=[
                COORDENADOR_DIETA_ESPECIAL,
                COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
            ]
        )

    @property
    def quantidade_alunos(self):
        quantidade_result = AlunosMatriculadosPeriodoEscola.objects.filter(
            escola__in=Escola.objects.all(), tipo_turma="REGULAR"
        ).aggregate(Sum("quantidade_alunos"))
        return quantidade_result.get("quantidade_alunos__sum") or 0

    @property
    def quantidade_alunos_terceirizada(self):
        quantidade_result = AlunosMatriculadosPeriodoEscola.objects.filter(
            escola__in=Escola.objects.all(),
            tipo_turma="REGULAR",
            escola__tipo_gestao__nome=ESCOLA_TIPO_GESTAO_NOME,
        ).aggregate(Sum("quantidade_alunos"))
        return quantidade_result.get("quantidade_alunos__sum") or 0

    @property
    def quantidade_alunos_parceira(self):
        quantidade_result = AlunosMatriculadosPeriodoEscola.objects.filter(
            escola__in=Escola.objects.all(),
            tipo_turma="REGULAR",
            escola__tipo_gestao__nome="PARCEIRA",
        ).aggregate(Sum("quantidade_alunos"))
        return quantidade_result.get("quantidade_alunos__sum") or 0

    def inversoes_cardapio_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, InversaoCardapio)
        return queryset.filter(
            status__in=[
                InversaoCardapio.workflow_class.DRE_VALIDADO,
                InversaoCardapio.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    def grupos_inclusoes_alimentacao_normal_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, GrupoInclusaoAlimentacaoNormal)
        return queryset.filter(
            status__in=[
                GrupoInclusaoAlimentacaoNormal.workflow_class.DRE_VALIDADO,
                GrupoInclusaoAlimentacaoNormal.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    def filtra_solicitacoes_minhas_escolas_a_validar_por_data(
        self, filtro_aplicado, model
    ):
        queryset = queryset_por_data(filtro_aplicado, model)
        return queryset.filter(
            escola__in=Escola.objects.all(),
            status=SolicitacaoKitLancheAvulsa.workflow_class.DRE_A_VALIDAR,
        )

    def inclusoes_alimentacao_de_cei_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, InclusaoAlimentacaoDaCEI)
        return queryset.filter(
            status__in=[
                InclusaoAlimentacaoDaCEI.workflow_class.DRE_VALIDADO,
                InclusaoAlimentacaoDaCEI.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    @property
    def inversoes_cardapio_autorizadas(self):
        return InversaoCardapio.objects.filter(
            status__in=[
                InversaoCardapio.workflow_class.CODAE_AUTORIZADO,
                InversaoCardapio.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ]
        )

    @property
    def inversoes_cardapio_reprovados(self):
        return InversaoCardapio.objects.filter(
            status__in=[InversaoCardapio.workflow_class.CODAE_NEGOU_PEDIDO]
        )

    def inclusoes_alimentacao_continua_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, InclusaoAlimentacaoContinua)
        return queryset.filter(
            status__in=[
                GrupoInclusaoAlimentacaoNormal.workflow_class.DRE_VALIDADO,
                GrupoInclusaoAlimentacaoNormal.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    def inclusoes_alimentacao_cemei_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, InclusaoDeAlimentacaoCEMEI)
        return queryset.filter(
            status__in=[
                InclusaoDeAlimentacaoCEMEI.workflow_class.DRE_VALIDADO,
                InclusaoDeAlimentacaoCEMEI.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    def alteracoes_cardapio_das_minhas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, AlteracaoCardapio)
        return queryset.filter(
            status__in=[
                AlteracaoCardapio.workflow_class.DRE_VALIDADO,
                AlteracaoCardapio.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    def alteracoes_cardapio_cei_das_minhas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, AlteracaoCardapioCEI)
        return queryset.filter(
            status__in=[
                AlteracaoCardapioCEI.workflow_class.DRE_VALIDADO,
                AlteracaoCardapioCEI.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    def alteracoes_cardapio_cemei_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, AlteracaoCardapioCEMEI)
        return queryset.filter(
            status__in=[
                AlteracaoCardapioCEMEI.workflow_class.DRE_VALIDADO,
                AlteracaoCardapioCEMEI.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    def suspensoes_cardapio_das_minhas_escolas(self, filtro_aplicado):
        return GrupoSuspensaoAlimentacao.objects.filter(
            ~Q(status__in=[GrupoSuspensaoAlimentacao.workflow_class.RASCUNHO])
        )

        #
        # Inversões de cardápio
        #

    def solicitacoes_unificadas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, SolicitacaoKitLancheUnificada)
        return queryset.filter(
            status__in=[
                SolicitacaoKitLancheUnificada.workflow_class.CODAE_A_AUTORIZAR,
                SolicitacaoKitLancheUnificada.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    @property
    def solicitacoes_unificadas_autorizadas(self):
        return SolicitacaoKitLancheUnificada.objects.filter(
            status__in=[
                SolicitacaoKitLancheUnificada.workflow_class.CODAE_AUTORIZADO,
                SolicitacaoKitLancheUnificada.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ]
        )

    @property
    def inclusoes_continuas_autorizadas(self):
        return InclusaoAlimentacaoContinua.objects.filter(
            status__in=[
                InclusaoAlimentacaoContinua.workflow_class.CODAE_AUTORIZADO,
                SolicitacaoKitLancheUnificada.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ]
        )

    @property
    def inclusoes_normais_autorizadas(self):
        return GrupoInclusaoAlimentacaoNormal.objects.filter(
            status__in=[
                GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
                GrupoInclusaoAlimentacaoNormal.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ]
        )

    @property
    def inclusoes_continuas_reprovadas(self):
        return InclusaoAlimentacaoContinua.objects.filter(
            status=InclusaoAlimentacaoContinua.workflow_class.CODAE_NEGOU_PEDIDO
        )

    @property
    def inclusoes_normais_reprovadas(self):
        return GrupoInclusaoAlimentacaoNormal.objects.filter(
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_NEGOU_PEDIDO
        )

    @property
    def solicitacao_kit_lanche_avulsa_autorizadas(self):
        return SolicitacaoKitLancheAvulsa.objects.filter(
            status__in=[
                SolicitacaoKitLancheAvulsa.workflow_class.CODAE_AUTORIZADO,
                SolicitacaoKitLancheAvulsa.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ]
        )

    def solicitacoes_kit_lanche_cemei_das_minhas_escolas_a_validar(
        self, filtro_aplicado
    ):
        queryset = queryset_por_data(filtro_aplicado, SolicitacaoKitLancheCEMEI)
        return queryset.filter(
            status__in=[
                SolicitacaoKitLancheCEMEI.workflow_class.DRE_VALIDADO,
                SolicitacaoKitLancheCEMEI.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    @property
    def solicitacao_kit_lanche_avulsa_reprovadas(self):
        return SolicitacaoKitLancheAvulsa.objects.filter(
            status=SolicitacaoKitLancheAvulsa.workflow_class.CODAE_NEGOU_PEDIDO
        )

    def solicitacoes_kit_lanche_das_minhas_escolas_a_validar(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, SolicitacaoKitLancheAvulsa)
        return queryset.filter(
            status__in=[
                SolicitacaoKitLancheAvulsa.workflow_class.DRE_VALIDADO,
                SolicitacaoKitLancheAvulsa.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    def solicitacoes_kit_lanche_cei_das_minhas_escolas_a_validar(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, SolicitacaoKitLancheCEIAvulsa)
        return queryset.filter(
            status__in=[
                SolicitacaoKitLancheCEIAvulsa.workflow_class.DRE_VALIDADO,
                SolicitacaoKitLancheCEIAvulsa.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    @property
    def alteracoes_cardapio_autorizadas(self):
        return AlteracaoCardapio.objects.filter(
            status__in=[
                AlteracaoCardapio.workflow_class.CODAE_AUTORIZADO,
                AlteracaoCardapio.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ]
        )

    @property
    def alteracoes_cardapio_reprovadas(self):
        return AlteracaoCardapio.objects.filter(
            status=AlteracaoCardapio.workflow_class.CODAE_NEGOU_PEDIDO
        )

    def delete(self, *args, **kwargs):
        # CODAE é uma entidade única do sistema: o registro não pode ser
        # excluído, por isso a exclusão é propositalmente ignorada.
        pass

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "CODAE"
        verbose_name_plural = "CODAE"
