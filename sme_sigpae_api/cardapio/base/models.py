from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

from sme_sigpae_api.cardapio.base.behaviors import TemLabelDeTiposDeAlimentacao
from sme_sigpae_api.dados_comuns.behaviors import (
    Ativavel,
    CriadoEm,
    Descritivel,
    Nomeavel,
    Posicao,
    TemChaveExterna,
    TemData,
)


class TipoAlimentacao(
    ExportModelOperationsMixin("tipo_alimentacao"), Nomeavel, TemChaveExterna, Posicao
):
    """Compõe parte do cardápio.

    Dejejum
    Colação
    Almoço
    Refeição
    Sobremesa
    Lanche 4 horas
    Lanche 5 horas
    Lanche 6 horas
    Lanche Emergencial
    """

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


class ComboDoVinculoTipoAlimentacaoPeriodoTipoUE(
    ExportModelOperationsMixin("substituicoes_vinculo_alimentacao"),
    TemChaveExterna,
    TemLabelDeTiposDeAlimentacao,
):  # noqa E125
    tipos_alimentacao = models.ManyToManyField(
        "TipoAlimentacao",
        related_name="%(app_label)s_%(class)s_possibilidades",
        help_text="Tipos de alimentacao do combo.",
        blank=True,
    )
    vinculo = models.ForeignKey(
        "VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        null=True,
        on_delete=models.CASCADE,
        related_name="combos",
    )

    def pode_excluir(self):
        # TODO: incrementar esse método,  impedir exclusão se tiver
        # solicitações em cima desse combo também.
        return not self.substituicoes.exists()

    def __str__(self):
        tipos_alimentacao_nome = [
            nome for nome in self.tipos_alimentacao.values_list("nome", flat=True)
        ]  # noqa
        return f"TiposAlim.: {tipos_alimentacao_nome}"

    class Meta:
        verbose_name = "Combo do vínculo tipo alimentação"
        verbose_name_plural = "Combos do vínculo tipo alimentação"


class SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE(
    TemChaveExterna, TemLabelDeTiposDeAlimentacao
):  # noqa E125
    tipos_alimentacao = models.ManyToManyField(
        "TipoAlimentacao",
        related_name="%(app_label)s_%(class)s_possibilidades",
        help_text="Tipos de alimentacao das substituições dos combos.",
        blank=True,
    )
    combo = models.ForeignKey(
        "ComboDoVinculoTipoAlimentacaoPeriodoTipoUE",
        null=True,
        on_delete=models.CASCADE,
        related_name="substituicoes",
    )

    def pode_excluir(self):
        # TODO: incrementar esse método,  impedir exclusão se tiver
        # solicitações em cima dessa substituição do combo.
        return True

    def __str__(self):
        tipos_alimentacao_nome = [
            nome for nome in self.tipos_alimentacao.values_list("nome", flat=True)
        ]
        return f"TiposAlim.:{tipos_alimentacao_nome}"

    class Meta:
        verbose_name = "Substituição do combo do vínculo tipo alimentação"
        verbose_name_plural = "Substituições do  combos do vínculo tipo alimentação"


class VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar(
    ExportModelOperationsMixin("vinculo_alimentacao_periodo_escolar_tipo_ue"),
    Ativavel,
    TemChaveExterna,
):  # noqa E125
    """Vincular vários tipos de alimentação a um periodo e tipo de U.E.

    Dado o tipo_unidade_escolar (EMEI, EMEF...) e
    em seguida o periodo_escolar(MANHA, TARDE..),
    trazer os tipos de alimentação que podem ser servidos.
    Ex.: Para CEI(creche) pela manhã (período) faz sentido ter mingau e não café da tarde.
    """

    # TODO: Refatorar para usar EscolaPeriodoEscolar
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


class Cardapio(
    ExportModelOperationsMixin("cardapio"),
    Descritivel,
    Ativavel,
    TemData,
    TemChaveExterna,
    CriadoEm,
):
    """Cardápio escolar.

    tem 1 data pra acontecer ex (26/06)
    tem 1 lista de tipos de alimentação (Dejejum, Colação, Almoço, LANCHE DE 4 HS OU 8 HS;
    LANCHE DE 5HS OU 6 HS; REFEIÇÃO).

    !!!OBS!!! PARA CEI varia por faixa de idade.
    """

    tipos_alimentacao = models.ManyToManyField(TipoAlimentacao)
    edital = models.ForeignKey(
        "terceirizada.Edital", on_delete=models.DO_NOTHING, related_name="editais"
    )

    @property  # type: ignore
    def tipos_unidade_escolar(self):
        return self.tipos_unidade_escolar

    def __str__(self):
        if self.descricao:
            return f"{self.data}  - {self.descricao}"
        return f"{self.data}"

    class Meta:
        verbose_name = "Cardápio"
        verbose_name_plural = "Cardápios"


class MotivoDRENaoValida(
    ExportModelOperationsMixin("motivo_dre_nao_valida"), Nomeavel, TemChaveExterna
):
    """Usado em conjunto com Solicitações que passam por validação da DRE.

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
