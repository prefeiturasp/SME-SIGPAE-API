from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

from src.dados_comuns.behaviors import (
    Ativavel,
    Nomeavel,
    Posicao,
    TemChaveExterna,
)


class TipoAlimentacao(
    ExportModelOperationsMixin("tipo_alimentacao"), Nomeavel, TemChaveExterna, Posicao
):
    """Representa um tipo de alimentação que pode compor o cardápio escolar.

    Os registros deste modelo são reutilizados em vínculos com período escolar,
    configurações de horário por unidade educacional e solicitações que
    dependem do tipo de alimentação servido.

    Tipos cadastrados:
        - Desjejum
        - Colação
        - Almoço
        - Refeição
        - Sobremesa
        - Lanche
        - Lanche 4h
        - Lanche Emergencial

    Tipos de alimentação de CEI:
        - Desjejum
        - Colação
        - Almoço
        - Refeição da Tarde

    Tipos de alimentação de EMEF/EMEI/CIEJA, etc:
        - Refeição
        - Sobremesa
        - Lanche
        - Lanche 4h
        - Lanche Emergencial
    """

    LANCHE_EMERGENCIAL = "Lanche Emergencial"
    LANCHE_4H = "Lanche 4h"

    @property
    def substituicoes_periodo_escolar(self):
        return self.substituicoes_periodo_escolar

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Tipo de alimentação"
        verbose_name_plural = "Tipos de alimentação"
        ordering = ["posicao"]


class HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar(TemChaveExterna):
    """Define a faixa de horário de um tipo de alimentação em uma escola.

    O cadastro relaciona uma escola, um período escolar e um tipo de
    alimentação a uma janela de atendimento. Os vínculos opcionais preservam a
    compatibilidade com registros legados e permitem configurações parciais.
    """

    hora_inicial = models.TimeField(auto_now=False, auto_now_add=False)
    hora_final = models.TimeField(auto_now=False, auto_now_add=False)
    escola = models.ForeignKey(
        "escola.Escola", blank=True, null=True, on_delete=models.DO_NOTHING
    )
    tipo_alimentacao = models.ForeignKey(
        "cardapio.TipoAlimentacao", blank=True, null=True, on_delete=models.DO_NOTHING
    )
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar", blank=True, null=True, on_delete=models.DO_NOTHING
    )

    def __str__(self):
        return f"{self.tipo_alimentacao.nome} DE: {self.hora_inicial} ATE: {self.hora_final}"


class VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar(
    ExportModelOperationsMixin("vinculo_alimentacao_periodo_escolar_tipo_ue"),
    Ativavel,
    TemChaveExterna,
):
    """Relaciona tipos de alimentação permitidos a um período escolar e tipo de U.E.

    O vínculo funciona como uma regra de negócio do cardápio, definindo quais
    tipos de alimentação podem ser servidos para uma combinação específica de
    tipo de unidade escolar e período escolar.

    Exemplos:
        - Uma CEI no período da MANHA pode servir Desjejum, Colação e Almoço.
        - Uma EMEF no período INTEGRAL pode servir Refeição, Sobremesa, Lanche, Lanche 4h e Lanche Emergencial.
    """

    tipo_unidade_escolar = models.ForeignKey(
        "escola.TipoUnidadeEscolar", null=True, on_delete=models.DO_NOTHING
    )
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar", null=True, on_delete=models.DO_NOTHING
    )
    tipos_alimentacao = models.ManyToManyField(
        "TipoAlimentacao", related_name="vinculos", blank=True
    )

    def __str__(self):
        return f"{self.tipo_unidade_escolar.iniciais} - {self.periodo_escolar.nome}"

    class Meta:
        unique_together = [["periodo_escolar", "tipo_unidade_escolar"]]
        verbose_name = "Vínculo tipo alimentação"
        verbose_name_plural = "Vínculos tipo alimentação"


class MotivoDRENaoValida(
    ExportModelOperationsMixin("motivo_dre_nao_valida"), Nomeavel, TemChaveExterna
):
    """Armazena motivos usados pela DRE para não validar uma solicitação no módulo de Gestão de Alimentação.

    Os registros deste modelo são exibidos quando uma solicitação que passa
    pela Diretoria Regional de Educação é invalidada.

    Exemplos:
        - Em desacordo com o contrato
        - Preenchimento incorreto
        - Outro
    """

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Motivo de não validação da DRE"
        verbose_name_plural = "Motivos de não validação da DRE"
