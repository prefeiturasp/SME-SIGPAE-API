from django.db import models

from src.cardapio.base.models import TipoAlimentacao
from src.dados_comuns.behaviors import (
    CriadoEm,
    Nomeavel,
    TemAlteradoEm,
    TemChaveExterna,
)
from src.dados_comuns.constants import (
    GRUPO_RECREIO_NAS_FERIAS,
    TIPOS_UNIDADE_ESCOLAR,
    StringsVerboseNameModels,
)
from src.escola.models import Escola, Lote


class RecreioNasFerias(TemChaveExterna, CriadoEm, TemAlteradoEm):
    titulo = models.CharField(max_length=200)
    data_inicio = models.DateField()
    data_fim = models.DateField()

    class Meta:
        ordering = ["-alterado_em"]
        verbose_name = GRUPO_RECREIO_NAS_FERIAS
        verbose_name_plural = StringsVerboseNameModels.RECREIOS_NAS_FERIAS.value

    def __str__(self):
        return f"{self.titulo} - (de {self.data_inicio.strftime('%d/%m/%Y')} à {self.data_fim.strftime('%d/%m/%Y')}) - {self.unidades_participantes.count()} unidades participantes"


class RecreioNasFeriasUnidadeParticipante(TemChaveExterna, CriadoEm, TemAlteradoEm):
    OPCOES_CEI_OU_EMEI = (
        ("N/A", "N/A"),
        (TIPOS_UNIDADE_ESCOLAR.CEI.value, TIPOS_UNIDADE_ESCOLAR.CEI.value),
        (TIPOS_UNIDADE_ESCOLAR.EMEI.value, TIPOS_UNIDADE_ESCOLAR.EMEI.value),
    )

    recreio_nas_ferias = models.ForeignKey(
        RecreioNasFerias,
        on_delete=models.CASCADE,
        related_name="unidades_participantes",
    )
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT)
    unidade_educacional = models.ForeignKey(Escola, on_delete=models.PROTECT)
    num_inscritos = models.PositiveIntegerField(default=0)
    num_colaboradores = models.PositiveIntegerField(default=0)
    liberar_medicao = models.BooleanField(default=False)
    cei_ou_emei = models.CharField(
        max_length=4, choices=OPCOES_CEI_OU_EMEI, default="N/A"
    )

    def __str__(self):
        return f"{self.unidade_educacional} - {self.recreio_nas_ferias.titulo}"

    class Meta:
        verbose_name = (
            StringsVerboseNameModels.RECREIO_NAS_FERIAS_UNIDADE_PARTICIPANTE.value
        )
        verbose_name_plural = (
            StringsVerboseNameModels.RECREIOS_NAS_FERIAS_UNIDADES_PARTICIPANTES.value
        )


class CategoriaAlimentacao(TemChaveExterna, CriadoEm, TemAlteradoEm, Nomeavel):
    """
    Categorias de alimentação para Recreio nas Férias
    Ex: Inscritos, Colaboradores, Infantil
    """

    class Meta:
        verbose_name = StringsVerboseNameModels.CATEGORIA_DE_ALIMENTACAO.value
        verbose_name_plural = StringsVerboseNameModels.CATEGORIAS_DE_ALIMENTACAO.value
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class RecreioNasFeriasUnidadeTipoAlimentacao(TemChaveExterna, CriadoEm, TemAlteradoEm):
    recreio_ferias_unidade = models.ForeignKey(
        RecreioNasFeriasUnidadeParticipante,
        on_delete=models.CASCADE,
        related_name="tipos_alimentacao",
    )
    tipo_alimentacao = models.ForeignKey(TipoAlimentacao, on_delete=models.PROTECT)
    categoria = models.ForeignKey(CategoriaAlimentacao, on_delete=models.PROTECT)

    class Meta:
        unique_together = ["recreio_ferias_unidade", "tipo_alimentacao", "categoria"]
        verbose_name = StringsVerboseNameModels.TIPO_DE_ALIMENTACAO_DA_UNIDADE.value
        verbose_name_plural = (
            StringsVerboseNameModels.TIPOS_DE_ALIMENTACAO_DAS_UNIDADES.value
        )

    def __str__(self):
        return f"{self.categoria} - {self.tipo_alimentacao}"
