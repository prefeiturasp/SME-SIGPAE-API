from __future__ import annotations

from django.db import models

from src.dados_comuns.constants import StringsVerboseNameModels

from ...dados_comuns.behaviors import (
    CriadoEm,
    CriadoPor,
    Justificativa,
    TemChaveExterna,
    TemData,
    TemFaixaEtariaEQuantidade,
    TemObservacao,
)
from ...dados_comuns.constants import CRIADO_EM, TIPOS_UNIDADE_ESCOLAR
from ..aluno.models import Aluno, TipoTurma
from ..constants import CEI_OU_EMEI, EMEI, INFANTIL_OU_FUNDAMENTAL
from ..escola.models import Escola, PeriodoEscolar


class LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar(
    TemChaveExterna, CriadoEm, Justificativa, CriadoPor
):
    escola = models.ForeignKey(
        Escola,
        related_name="log_alteracao_quantidade_alunos",
        on_delete=models.DO_NOTHING,
    )
    periodo_escolar = models.ForeignKey(
        PeriodoEscolar,
        related_name="log_alteracao_quantidade_alunos",
        on_delete=models.DO_NOTHING,
    )
    quantidade_alunos_de = models.PositiveSmallIntegerField(
        StringsVerboseNameModels.QUANTIDADE_DE_ALUNOS_ANTERIOR.value, default=0
    )
    quantidade_alunos_para = models.PositiveSmallIntegerField(
        StringsVerboseNameModels.QUANTIDADE_DE_ALUNOS_ALTERADA.value, default=0
    )

    def __str__(self):
        quantidade_anterior = self.quantidade_alunos_de
        quantidade_atual = self.quantidade_alunos_para
        escola = self.escola.nome
        return f"Alteração de: {quantidade_anterior} alunos, para: {quantidade_atual} alunos na escola: {escola}"

    class Meta:
        verbose_name = "Log Alteração quantidade de alunos"
        verbose_name_plural = "Logs de Alteração quantidade de alunos"
        ordering = ("criado_em",)


class LogRotinaDiariaAlunos(TemChaveExterna, CriadoEm):
    quantidade_alunos_antes = models.PositiveIntegerField(
        StringsVerboseNameModels.QUANTIDADE_DE_ALUNOS_ANTES.value, default=0
    )
    quantidade_alunos_atual = models.PositiveIntegerField(
        StringsVerboseNameModels.QUANTIDADE_DE_ALUNOS_ATUAL.value, default=0
    )

    def __str__(self):
        criado_em = self.criado_em.strftime("%Y-%m-%d %H:%M:%S")
        quant_antes = self.quantidade_alunos_antes
        quant_atual = self.quantidade_alunos_atual
        return f"Criado em {criado_em} - Quant. de alunos antes: {quant_antes}. Quant. de alunos atual: {quant_atual}"

    class Meta:
        verbose_name = "Log Rotina Diária quantidade de alunos"
        verbose_name_plural = "Logs Rotina Diária quantidade de alunos"
        ordering = ("-criado_em",)


class LogAlunosMatriculadosPeriodoEscola(TemChaveExterna, CriadoEm, TemObservacao):
    """Histórico da quantidade de Alunos por período."""

    escola = models.ForeignKey(
        Escola,
        related_name="logs_alunos_matriculados_por_periodo",
        on_delete=models.DO_NOTHING,
    )
    periodo_escolar = models.ForeignKey(
        PeriodoEscolar,
        related_name="logs_alunos_matriculados",
        on_delete=models.DO_NOTHING,
    )
    quantidade_alunos = models.PositiveSmallIntegerField(
        StringsVerboseNameModels.QUANTIDADE_DE_ALUNOS.value, default=0
    )

    tipo_turma = models.CharField(
        max_length=255,
        choices=TipoTurma.choices(),
        blank=True,
        default=TipoTurma.REGULAR.name,
    )
    cei_ou_emei = models.CharField(max_length=4, choices=CEI_OU_EMEI, default="N/A")
    infantil_ou_fundamental = models.CharField(
        max_length=11, choices=INFANTIL_OU_FUNDAMENTAL, default="N/A"
    )

    def cria_logs_emei_em_cemei(self):
        if (
            not self.escola.eh_cemei
            or self.tipo_turma != "REGULAR"
            or (self.periodo_escolar and self.periodo_escolar.nome != "INTEGRAL")
            or self.escola.quantidade_alunos_emei_por_periodo("INTEGRAL") == 0
        ):
            return
        if not LogAlunosMatriculadosPeriodoEscola.objects.filter(
            escola=self.escola,
            periodo_escolar=self.periodo_escolar,
            criado_em__year=self.criado_em.year,
            criado_em__month=self.criado_em.month,
            criado_em__day=self.criado_em.day,
            tipo_turma=self.tipo_turma,
            cei_ou_emei=EMEI,
        ).exists():
            log = LogAlunosMatriculadosPeriodoEscola.objects.create(
                escola=self.escola,
                periodo_escolar=self.periodo_escolar,
                quantidade_alunos=self.escola.quantidade_alunos_emei_por_periodo(
                    "INTEGRAL"
                ),
                tipo_turma=self.tipo_turma,
                cei_ou_emei=EMEI,
            )
            log.criado_em = self.criado_em
            log.save()

    def cria_logs_cei_em_cemei(self):
        if (
            not self.escola.eh_cemei
            or self.tipo_turma != "REGULAR"
            or self.periodo_escolar
            and self.periodo_escolar.nome != "INTEGRAL"
        ):
            return
        if not LogAlunosMatriculadosPeriodoEscola.objects.filter(
            escola=self.escola,
            periodo_escolar=self.periodo_escolar,
            criado_em__year=self.criado_em.year,
            criado_em__month=self.criado_em.month,
            criado_em__day=self.criado_em.day,
            tipo_turma=self.tipo_turma,
            cei_ou_emei=TIPOS_UNIDADE_ESCOLAR.CEI.value,
        ).exists():
            log = LogAlunosMatriculadosPeriodoEscola.objects.create(
                escola=self.escola,
                periodo_escolar=self.periodo_escolar,
                quantidade_alunos=self.escola.quantidade_alunos_cei_por_periodo(
                    "INTEGRAL"
                ),
                tipo_turma=self.tipo_turma,
                cei_ou_emei=TIPOS_UNIDADE_ESCOLAR.CEI.value,
            )
            log.criado_em = self.criado_em
            log.save()

    def cria_logs_emebs(self, infantil_ou_fundamental):
        if not self.escola.eh_emebs or self.tipo_turma != "REGULAR":
            return
        metodo_qtd_alunos = (
            f"quantidade_alunos_emebs_por_periodo_{infantil_ou_fundamental.lower()}"
        )
        if not LogAlunosMatriculadosPeriodoEscola.objects.filter(
            escola=self.escola,
            periodo_escolar=self.periodo_escolar,
            criado_em__year=self.criado_em.year,
            criado_em__month=self.criado_em.month,
            criado_em__day=self.criado_em.day,
            tipo_turma=self.tipo_turma,
            infantil_ou_fundamental=infantil_ou_fundamental,
        ).exists():
            log = LogAlunosMatriculadosPeriodoEscola.objects.create(
                escola=self.escola,
                periodo_escolar=self.periodo_escolar,
                quantidade_alunos=getattr(self.escola, metodo_qtd_alunos)(
                    self.periodo_escolar.nome
                ),
                tipo_turma=self.tipo_turma,
                infantil_ou_fundamental=infantil_ou_fundamental,
            )
            log.criado_em = self.criado_em
            log.save()

    @classmethod
    def criar(cls, escola, periodo_escolar, quantidade_alunos, data, tipo_turma):
        try:
            log = cls.objects.get(
                escola=escola,
                periodo_escolar=periodo_escolar,
                criado_em__year=data.year,
                criado_em__month=data.month,
                criado_em__day=data.day,
                tipo_turma=tipo_turma,
                cei_ou_emei="N/A",
                infantil_ou_fundamental="N/A",
            )
        except cls.DoesNotExist:
            log = cls.objects.create(
                escola=escola,
                periodo_escolar=periodo_escolar,
                quantidade_alunos=quantidade_alunos,
                tipo_turma=tipo_turma,
                cei_ou_emei="N/A",
                infantil_ou_fundamental="N/A",
            )
            log.criado_em = data
            log.save()
        log.cria_logs_emei_em_cemei()
        log.cria_logs_cei_em_cemei()
        log.cria_logs_emebs("INFANTIL")
        log.cria_logs_emebs("FUNDAMENTAL")

    def __str__(self):
        periodo_nome = self.periodo_escolar.nome

        return f"""Escola {self.escola.nome} do tipo {self.tipo_turma} no periodo da {periodo_nome}
        tem {self.quantidade_alunos} alunos no dia {self.criado_em}"""

    class Meta:
        verbose_name = "Log Alteração quantidade de alunos regular e programa"
        verbose_name_plural = (
            "Logs de Alteração quantidade de alunos regulares e de programas"
        )
        ordering = ("-criado_em",)


class LogAtualizaDadosAluno(models.Model):
    criado_em = models.DateTimeField(CRIADO_EM, editable=False, auto_now_add=True)
    codigo_eol = models.CharField(
        StringsVerboseNameModels.CODIGO_EOL_DA_ESCOLA.value, max_length=50
    )
    status = models.PositiveSmallIntegerField(
        StringsVerboseNameModels.STATUS_DA_REQUISICAO.value, default=0
    )
    msg_erro = models.TextField(
        StringsVerboseNameModels.MENSAGEM_ERRO.value, blank=True
    )

    def __str__(self):
        retorno = f'Requisicao para Escola: "#{str(self.codigo_eol)}"'
        retorno += f' na data de: "{self.criado_em}"'
        return retorno


class LogAlunosMatriculadosFaixaEtariaDia(
    TemChaveExterna, CriadoEm, TemData, TemFaixaEtariaEQuantidade
):
    """Histórico da quantidade de Alunos por faixa etária, dia, período, escola."""

    escola = models.ForeignKey(
        Escola,
        related_name="logs_alunos_matriculados_por_faixa_etaria",
        on_delete=models.DO_NOTHING,
    )
    periodo_escolar = models.ForeignKey(
        PeriodoEscolar,
        related_name="logs_alunos_matriculados_por_faixa_etaria",
        on_delete=models.DO_NOTHING,
    )

    def __str__(self):
        periodo_nome = self.periodo_escolar.nome

        return f"""Escola {self.escola.nome} no periodo da {periodo_nome}
        tem {self.quantidade} aluno(s) no dia {self.data} faixa etária {self.faixa_etaria}"""

    class Meta:
        verbose_name = "Log quantidade de alunos por faixa etária, dia e período"
        verbose_name_plural = (
            "Logs quantidades de alunos por faixas etárias, dias e períodos"
        )
        ordering = ("criado_em",)


class LogAlunoPorDia(TemChaveExterna, CriadoEm):
    """Relaciona log LogAlunosMatriculadosFaixaEtariaDia e Aluno."""

    log_alunos_matriculados_faixa_dia = models.ForeignKey(
        LogAlunosMatriculadosFaixaEtariaDia,
        related_name="logs_alunos_por_dia",
        on_delete=models.PROTECT,
    )
    aluno = models.ForeignKey(
        Aluno, related_name="logs_alunos_por_dia", on_delete=models.PROTECT
    )

    class Meta:
        verbose_name = "Log aluno por dia"
        verbose_name_plural = "Logs alunos por dia"
        ordering = ("criado_em",)
