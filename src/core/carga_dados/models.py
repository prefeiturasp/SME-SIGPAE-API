from __future__ import annotations

from django.db import models

from src.dados_comuns.constants import StringsVerboseNameModels

from ...dados_comuns.behaviors import ArquivoCargaBase, CriadoEm, TemAlteradoEm


class PlanilhaEscolaDeParaCodigoEolCodigoCoade(CriadoEm, TemAlteradoEm):
    planilha = models.FileField(
        help_text="Deve ser inserido um arquivo excel em formato xlsx<br> "
        "O arquivo deve conter as colunas código eol e código codae.<br>"
        "O nome de cada coluna deve ser exatamente como a seguir:<br> "
        "<b>codigo_eol</b> e <b>codigo_unidade</b>"
    )
    codigos_codae_vinculados = models.BooleanField(
        StringsVerboseNameModels.CODIGOS_CODAE_VINCULADOS.value,
        default=False,
        editable=False,
    )

    class Meta:
        verbose_name = "Planilha De-Para: Código EOL x Código Codae"
        verbose_name_plural = "Planilhas De-Para: Código EOL x Código Codae"

    def __str__(self):
        return str(self.planilha)


class PlanilhaAtualizacaoTipoGestaoEscola(ArquivoCargaBase):
    class Meta:
        verbose_name = "Planilha Atualização Tipo Gestão Escola"
        verbose_name_plural = "Planilha Atualização Tipo Gestão Escola"

    def __str__(self):
        return str(self.conteudo)
