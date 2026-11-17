from __future__ import annotations

import datetime
import logging
from datetime import date
from enum import Enum

from django.core.exceptions import MultipleObjectsReturned
from django.core.validators import MaxValueValidator, MinLengthValidator
from django.db import models
from rest_framework import status

from src.dados_comuns.constants import StringsVerboseNameModels

from ...dados_comuns.behaviors import (
    Ativavel,
    CriadoEm,
    Justificativa,
    Nomeavel,
    TemChaveExterna,
)
from ...dados_comuns.utils import quantidade_meses, subtrai_meses_de_data
from ..services import NovoSGPServicoLogado
from ..utils import faixa_to_string

logger = logging.getLogger("sigpae.EscolaModels")


class Responsavel(Nomeavel, TemChaveExterna, CriadoEm):
    cpf = models.CharField(  # noqa DJ01
        max_length=11,
        blank=True,
        null=True,
        unique=True,
        validators=[MinLengthValidator(11)],
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Responsável"
        verbose_name_plural = "Reponsáveis"


class FaixaEtaria(Ativavel, TemChaveExterna):
    inicio = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)])
    fim = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)])

    def data_pertence_a_faixa(self, data_pesquisada, data_referencia_arg=None):
        data_referencia = (
            date.today() if data_referencia_arg is None else data_referencia_arg
        )
        data_inicio = subtrai_meses_de_data(self.fim, data_referencia)
        data_fim = subtrai_meses_de_data(self.inicio, data_referencia)
        return data_inicio <= data_pesquisada < data_fim

    def __str__(self):
        return faixa_to_string(self.inicio, self.fim)


class Aluno(TemChaveExterna):
    ETAPA_INFANTIL = 10

    CICLO_ALUNO_CEI = 1
    CICLO_ALUNO_EMEI = 2

    nome = models.CharField(
        StringsVerboseNameModels.NOME_COMPLETO_DO_ALUNO.value, max_length=100
    )
    codigo_eol = models.CharField(  # noqa DJ01
        StringsVerboseNameModels.CODIGO_EOL.value,
        max_length=7,
        unique=True,
        validators=[MinLengthValidator(7)],
        null=True,
        blank=True,
    )
    data_nascimento = models.DateField()
    escola = models.ForeignKey(
        "Escola", blank=True, null=True, on_delete=models.SET_NULL
    )
    periodo_escolar = models.ForeignKey(
        "PeriodoEscolar",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    cpf = models.CharField(  # noqa DJ01
        max_length=11,
        blank=True,
        null=True,
        unique=True,
        validators=[MinLengthValidator(11)],
    )
    nao_matriculado = models.BooleanField(default=False)
    serie = models.CharField(max_length=10, blank=True, null=True)  # noqa DJ01

    responsaveis = models.ManyToManyField(
        Responsavel, blank=True, related_name="alunos"
    )

    etapa = models.PositiveSmallIntegerField(blank=True, null=True)
    ciclo = models.PositiveSmallIntegerField(blank=True, null=True)
    desc_etapa = models.CharField(
        StringsVerboseNameModels.DESCRICAO_ETAPA.value, max_length=50, blank=True
    )
    desc_ciclo = models.CharField(
        StringsVerboseNameModels.DESCRICAO_CICLO.value, max_length=50, blank=True
    )

    def __str__(self):
        if self.nao_matriculado:
            return f"{self.nome} - Não Matriculado"
        return f"{self.nome} - {self.codigo_eol}"

    def faixa_etaria(self, data_comparacao=date.today()) -> FaixaEtaria:
        meses = quantidade_meses(data_comparacao, self.data_nascimento)
        ultima_faixa = FaixaEtaria.objects.filter(ativo=True).order_by("fim").last()
        if meses >= ultima_faixa.fim:
            faixa = ultima_faixa
        else:
            faixa = FaixaEtaria.objects.get(
                ativo=True, inicio__lte=meses, fim__gt=meses
            )
        return faixa

    @property
    def possui_dieta_especial_ativa(self):
        return self.dietas_especiais.filter(ativo=True).exists()

    @property
    def obter_dieta_especial_ativa(self):
        from src.dieta_especial.solicitacao_dieta_especial.models import (
            SolicitacaoDietaEspecial,
        )

        return self.dietas_especiais.filter(
            ativo=True, status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO
        )

    @property
    def foto_aluno_base64(self):
        try:
            novosgpservicologado = NovoSGPServicoLogado()
            response = novosgpservicologado.pegar_foto_aluno(self.codigo_eol)
            if response.status_code == status.HTTP_200_OK:
                download = response.json()["download"]
                return f'data:{download["item2"]};base64,{download["item1"]}'
            return None
        except Exception:
            return None

    @property
    def periodo(self):
        if (
            not self.codigo_eol
            or self.nao_matriculado
            or not self.escola
            or not self.escola.tipo_unidade
        ):
            return None

        if self.escola.eh_cei:
            return None

        if self.escola.eh_cemei and self.ciclo == self.CICLO_ALUNO_CEI:
            return None

        if not self.periodo_escolar:
            return None

        periodo = self.periodo_escolar.nome.upper()

        periodos_permitidos = {
            "MANHA",
            "TARDE",
            "INTEGRAL",
            "NOITE",
            "VESPERTINO",
            "INTERMEDIARIO",
        }

        if periodo not in periodos_permitidos:
            return None

        return self.periodo_escolar.nome

    def inativar_dieta_especial(self):
        try:
            from src.dieta_especial.solicitacao_dieta_especial.models import (
                SolicitacaoDietaEspecial,
            )

            dieta_especial = self.dietas_especiais.get(
                ativo=True,
                status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            )
            dieta_especial.ativo = False
            dieta_especial.save()
            return dieta_especial
        except MultipleObjectsReturned:
            logger.critical("Aluno não deve possuir mais de uma Dieta Especial ativa")

    def cria_historico(self, codigo_situacao, situacao, escola=None):
        historico = HistoricoMatriculaAluno(
            aluno=self,
            escola=escola or self.escola,
            data_inicio=datetime.date.today(),
            codigo_situacao=codigo_situacao,
            situacao=situacao,
            data_fim=(
                datetime.date.today() if codigo_situacao not in [1, 6, 10, 13] else None
            ),
        )
        historico.save()
        return historico

    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"


class MudancaFaixasEtarias(Justificativa, TemChaveExterna):
    faixas_etarias_ativadas = models.ManyToManyField(FaixaEtaria)


class TipoTurma(Enum):
    REGULAR = 1
    PROGRAMAS = 3

    @classmethod
    def choices(cls):
        return tuple((t.name, t.value) for t in cls)


class AlunoPeriodoParcial(TemChaveExterna, CriadoEm):
    """Relaciona alunos em período parcial com a unidade educacional e a solicitação de medição inicial."""

    escola = models.ForeignKey(
        "Escola",
        related_name="alunos_periodo_parcial",
        on_delete=models.PROTECT,
    )
    aluno = models.ForeignKey(
        Aluno, related_name="alunos_periodo_parcial", on_delete=models.PROTECT
    )
    solicitacao_medicao_inicial = models.ForeignKey(
        "medicao_inicial.SolicitacaoMedicaoInicial",
        related_name="alunos_periodo_parcial",
        on_delete=models.CASCADE,
    )
    data = models.DateField(
        StringsVerboseNameModels.ALUNO_NO_PERIODO_PARCIAL_A_PARTIR_DE.value, null=True
    )
    data_removido = models.DateField(
        StringsVerboseNameModels.ALUNO_NO_PERIODO_PARCIAL_A_PARTIR_DE.value, null=True
    )

    def __str__(self):
        retorno = f"{self.aluno.nome} para SMI {self.solicitacao_medicao_inicial.mes}/"
        retorno += f"{self.solicitacao_medicao_inicial.ano} da UE {self.escola.nome}"
        retorno += f" a partir de {self.data}" if self.data else ""
        retorno += f" até {self.data_removido}" if self.data_removido else ""
        return retorno

    class Meta:
        verbose_name = "Aluno no período parcial"
        verbose_name_plural = "Alunos no período parcial"
        unique_together = ("escola", "aluno", "solicitacao_medicao_inicial")
        ordering = ("criado_em",)


class HistoricoMatriculaAluno(TemChaveExterna):
    aluno = models.ForeignKey(
        "Aluno", on_delete=models.PROTECT, related_name="historico"
    )
    escola = models.ForeignKey(
        "Escola", on_delete=models.PROTECT, related_name="historico"
    )
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True)
    codigo_situacao = models.IntegerField()
    situacao = models.CharField(blank=True)

    class Meta:
        verbose_name = "Histórico de Matrícula do Aluno"
        verbose_name_plural = "Históricos de Matrículas dos Alunos"

    def __str__(self) -> str:
        return f"{self.aluno} - {self.escola} | De: {self.data_inicio} Ate: {self.data_fim}"
