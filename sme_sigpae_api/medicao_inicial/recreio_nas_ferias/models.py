from django.db import models
from sme_sigpae_api.escola.models import Lote, Escola
from sme_sigpae_api.cardapio.base.models import TipoAlimentacao
from sme_sigpae_api.dados_comuns.behaviors import (
    CriadoEm,
    Nomeavel,
    TemChaveExterna,
    TemAlteradoEm,
)

class RecreioNasFerias(TemChaveExterna, CriadoEm, TemAlteradoEm):
    titulo = models.CharField(max_length=200)
    data_inicio = models.DateField()
    data_fim = models.DateField()

    def __str__(self):
        return self.titulo


class RecreioNasFeriasUnidadeParticipante(TemChaveExterna, CriadoEm, TemAlteradoEm):
    CEI_OU_EMEI = (
        ("N/A", "N/A"),
        ("CEI", "CEI"),
        ("EMEI", "EMEI")
    )

    recreio_nas_ferias = models.ForeignKey(
        RecreioNasFerias,
        on_delete=models.CASCADE,
        related_name='unidades_participantes'
    )
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT)
    unidade_educacional = models.ForeignKey(Escola, on_delete=models.PROTECT)
    num_inscritos = models.PositiveIntegerField(default=0)
    num_colaboradores = models.PositiveIntegerField(default=0)
    liberar_medicao = models.BooleanField(default=False)
    cei_ou_emei = models.CharField(max_length=4, choices=CEI_OU_EMEI, default="N/A")

    def __str__(self):
        return f"{self.unidade_educacional} - {self.recreio_nas_ferias}"


class CategoriaAlimentacao(TemChaveExterna, CriadoEm, TemAlteradoEm, Nomeavel):
    """
    Categorias de alimentação para Recreio nas Férias
    Ex: Inscritos, Colaboradores, Infantil
    """
    class Meta:
        verbose_name = 'Categoria de Alimentação'
        verbose_name_plural = 'Categorias de Alimentação'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class RecreioNasFeriasUnidadeTipoAlimentacao(TemChaveExterna, CriadoEm, TemAlteradoEm):
    recreio_ferias_unidade = models.ForeignKey(
        RecreioNasFeriasUnidadeParticipante,
        on_delete=models.CASCADE,
        related_name='tipos_alimentacao'
    )
    tipo_alimentacao = models.ForeignKey(TipoAlimentacao, on_delete=models.PROTECT)
    categoria = models.ForeignKey(CategoriaAlimentacao, on_delete=models.PROTECT)

    class Meta:
        unique_together = ['recreio_ferias_unidade', 'tipo_alimentacao', 'categoria']
        verbose_name = 'Tipo de Alimentação da Unidade'
        verbose_name_plural = 'Tipos de Alimentação das Unidades'

    def __str__(self):
        return f"{self.categoria} - {self.tipo_alimentacao}"
