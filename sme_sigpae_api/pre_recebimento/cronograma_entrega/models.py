from sme_sigpae_api.dados_comuns.behaviors import Logs, ModeloBase, TemIdentificadorExternoAmigavel
from sme_sigpae_api.dados_comuns.fluxo_status import CronogramaAlteracaoWorkflow, FluxoAlteracaoCronograma, FluxoCronograma
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.pre_recebimento.base.models import UnidadeMedida
from sme_sigpae_api.terceirizada.models import Contrato, Terceirizada
from django.db import models
from sme_sigpae_api.pre_recebimento.qualidade.models import TipoEmbalagemQld
from django.db.models import OuterRef
from django.db.models.signals import post_save
from django.dispatch import receiver


class Cronograma(ModeloBase, TemIdentificadorExternoAmigavel, Logs, FluxoCronograma):
    numero = models.CharField(
        "Número do Cronograma", blank=True, max_length=250, unique=True
    )
    contrato = models.ForeignKey(
        Contrato, on_delete=models.CASCADE, blank=True, null=True
    )
    empresa = models.ForeignKey(
        Terceirizada, on_delete=models.CASCADE, blank=True, null=True
    )
    qtd_total_programada = models.FloatField(
        "Qtd Total Programada", blank=True, null=True
    )
    unidade_medida = models.ForeignKey(
        UnidadeMedida, on_delete=models.PROTECT, blank=True, null=True
    )
    armazem = models.ForeignKey(
        Terceirizada,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="cronogramas",
    )
    ficha_tecnica = models.ForeignKey(
        "FichaTecnicaDoProduto",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    tipo_embalagem_secundaria = models.ForeignKey(
        TipoEmbalagemQld,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    custo_unitario_produto = models.FloatField(
        "Custo Unitário do Produto", blank=True, null=True
    )
    observacoes = models.TextField("Observações", blank=True)

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.CRONOGRAMA,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
        )

    def __str__(self):
        return f"Cronograma: {self.numero} - Status: {self.get_status_display()}"

    class Meta:
        verbose_name = "Cronograma"
        verbose_name_plural = "Cronogramas"


class EtapasDoCronograma(ModeloBase):
    cronograma = models.ForeignKey(
        Cronograma,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="etapas",
    )
    numero_empenho = models.CharField("Número do Empenho", blank=True, max_length=50)
    qtd_total_empenho = models.FloatField(
        "Qtde. Total do Empenho", blank=True, null=True
    )
    etapa = models.IntegerField(blank=True, null=True, verbose_name="Etapa")
    parte = models.CharField(blank=True, max_length=15)
    data_programada = models.DateField("Data Programada", blank=True, null=True)
    quantidade = models.FloatField(blank=True, null=True)
    total_embalagens = models.FloatField("Total de Embalagens", blank=True, null=True)

    def __str__(self):
        if self.etapa is not None and self.parte and self.cronograma:
            return f"Etapa {self.etapa} - {self.parte} - Cronograma {self.cronograma.numero}"

        if self.cronograma:
            return f"Etapa do Cronograma {self.cronograma.numero}"

        return "Etapa sem Cronograma"

    class Meta:
        verbose_name = "Etapa do Cronograma"
        verbose_name_plural = "Etapas dos Cronogramas"

    @classmethod
    def etapas_to_json(cls):
        result = []
        for numero in range(1, 101):
            choice = {"uuid": numero, "value": f"Etapa {numero}"}
            result.append(choice)
        return result


class ProgramacaoDoRecebimentoDoCronograma(ModeloBase):
    PALETIZADA = "PALETIZADA"
    ESTIVADA_BATIDA = "ESTIVADA_BATIDA"

    TIPO_CARGA_CHOICES = (
        (PALETIZADA, "Paletizada"),
        (ESTIVADA_BATIDA, "Estivada / Batida"),
    )

    cronograma = models.ForeignKey(
        Cronograma,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="programacoes_de_recebimento",
    )
    data_programada = models.CharField(blank=True, max_length=50)
    tipo_carga = models.CharField(choices=TIPO_CARGA_CHOICES, max_length=20, blank=True)

    def __str__(self):
        if self.data_programada:
            return self.data_programada
        else:
            return str(self.id)

    class Meta:
        verbose_name = "Programação do Recebimento do Cromograma"
        verbose_name_plural = "Programações dos Recebimentos dos Cromogramas"


class SolicitacaoAlteracaoCronogramaQuerySet(models.QuerySet):
    def em_analise(self):
        return self.filter(status=CronogramaAlteracaoWorkflow.EM_ANALISE)

    def filtrar_por_status(self, status, filtros=None, init=None, end=None):
        log = (
            LogSolicitacoesUsuario.objects.filter(uuid_original=OuterRef("uuid"))
            .order_by("-criado_em")
            .values("criado_em")[:1]
        )
        if not isinstance(status, list):
            status = [status]
        qs = (
            self.filter(status__in=status)
            .annotate(log_criado_em=log)
            .order_by("-log_criado_em")
        )
        if filtros:
            qs = self._filtrar_por_atributos_adicionais(qs, filtros)

        if init is not None and end is not None:
            return qs[init:end]
        return qs

    def _filtrar_por_atributos_adicionais(self, qs, filtros):
        if filtros:
            if "nome_fornecedor" in filtros:
                qs = qs.filter(
                    cronograma__empresa__nome_fantasia__icontains=filtros[
                        "nome_fornecedor"
                    ]
                )
            if "numero_cronograma" in filtros:
                qs = qs.filter(
                    cronograma__numero__icontains=filtros["numero_cronograma"]
                )
            if "nome_produto" in filtros:
                qs = qs.filter(
                    cronograma__ficha_tecnica__produto__nome__icontains=filtros[
                        "nome_produto"
                    ]
                )
        return qs


class SolicitacaoAlteracaoCronograma(
    ModeloBase, TemIdentificadorExternoAmigavel, FluxoAlteracaoCronograma, Logs
):
    cronograma = models.ForeignKey(
        Cronograma, on_delete=models.PROTECT, related_name="solicitacoes_de_alteracao"
    )
    qtd_total_programada = models.FloatField(
        "Qtd Total Programada", blank=True, null=True
    )
    etapas_antigas = models.ManyToManyField(
        EtapasDoCronograma, related_name="etapas_antigas"
    )
    etapas_novas = models.ManyToManyField(
        EtapasDoCronograma, related_name="etapas_novas"
    )
    programacoes_novas = models.ManyToManyField(
        ProgramacaoDoRecebimentoDoCronograma,
        related_name="programacoes_novas",
        blank=True,
    )
    justificativa = models.TextField(
        "Justificativa de solicitação pelo fornecedor", blank=True
    )
    usuario_solicitante = models.ForeignKey(
        "perfil.Usuario", on_delete=models.DO_NOTHING
    )
    numero_solicitacao = models.CharField(
        "Número da solicitação", blank=True, max_length=50, unique=True
    )

    objects = SolicitacaoAlteracaoCronogramaQuerySet.as_manager()

    def gerar_numero_solicitacao(self):
        self.numero_solicitacao = f"{str(self.pk).zfill(8)}-ALT"

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        log_transicao = LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.SOLICITACAO_DE_ALTERACAO_CRONOGRAMA,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
        )
        return log_transicao

    def cronograma_confirma_ciencia(self, justificativa, usuario, etapas, programacoes):
        from .api.helpers import (
            cria_etapas_de_cronograma,
            cria_programacao_de_cronograma,
        )

        self.etapas_novas.all().delete()
        etapas_criadas = cria_etapas_de_cronograma(etapas)
        self.etapas_novas.set(etapas_criadas)
        programacoes_criadas = cria_programacao_de_cronograma(programacoes)
        self.programacoes_novas.set(programacoes_criadas)
        self.cronograma_ciente(user=usuario, justificativa=justificativa)
        self.save()

    def __str__(self):
        return f"Solicitação de alteração do cronograma: {self.numero_solicitacao}"

    class Meta:
        verbose_name = "Solicitação de Alteração de Cronograma"
        verbose_name_plural = "Solicitações de Alteração de Cronograma"


@receiver(post_save, sender=SolicitacaoAlteracaoCronograma)
def gerar_numero_solicitacao(sender, instance, created, **kwargs):
    if created:
        instance.gerar_numero_solicitacao()
        instance.save()
