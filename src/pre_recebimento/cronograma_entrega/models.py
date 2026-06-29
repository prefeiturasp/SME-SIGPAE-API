from django.db import models
from django.db.models import OuterRef, Sum
from django.db.models.signals import post_save
from django.dispatch import receiver

from src.dados_comuns.behaviors import (
    Logs,
    ModeloBase,
    TemIdentificadorExternoAmigavel,
)
from src.dados_comuns.fluxo_status import (
    CronogramaAlteracaoWorkflow,
    FluxoAlteracaoCronograma,
    FluxoCronograma,
)
from src.dados_comuns.models import LogSolicitacoesUsuario
from src.pre_recebimento.base.models import UnidadeMedida
from src.pre_recebimento.qualidade.models import TipoEmbalagemQld
from src.terceirizada.models import Contrato, Terceirizada


class Cronograma(ModeloBase, TemIdentificadorExternoAmigavel, Logs, FluxoCronograma):
    """Cronograma de entrega de produtos alimentícios para as escolas.

    Registra o planejamento de entregas de um produto vinculado a uma ficha técnica,
    contrato e empresa fornecedora. Passa por um fluxo de aprovação (FluxoCronograma):
    RASCUNHO, ASSINADO_E_ENVIADO_AO_FORNECEDOR, ASSINADO_FORNECEDOR,
    ASSINADO_DILOG_ABASTECIMENTO, ASSINADO_CODAE.

    Divide-se em dois tipos conforme a categoria do produto e o tipo de entrega:

    **Armazenável**
        Produtos comuns, armazenados em almoxarifado/distribuidor. Possui etapas
        com data específica (DD/MM/YYYY) e programações de recebimento. A numeração
        utiliza o sufixo ``A`` (ex.: ``001/2025A``).

    **FLV Ponto a Ponto**
        Produtos hortifrutigranjeiros (FLV) entregues diretamente pelo fornecedor
        às unidades escolares. Possui etapas mensais (MM/YYYY) e não possui
        armazém, embalagem secundária nem programações de recebimento. A numeração
        utiliza o sufixo ``P`` (ex.: ``001/2025P``).
    """

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
    numero_empenho = models.CharField("Número do Empenho", blank=True, max_length=50)
    qtd_total_empenho = models.FloatField(
        "Qtde. Total do Empenho", blank=True, null=True
    )
    observacoes = models.TextField("Observações", blank=True)

    @property
    def ponto_a_ponto(self) -> bool:
        if not self.ficha_tecnica:
            return False
        return bool(
            self.ficha_tecnica
            and self.ficha_tecnica.tipo_entrega == "PONTO_A_PONTO"
        )

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
    """Etapa individual de um cronograma de entrega.

    Cada etapa representa uma parcela programada dentro do cronograma,
    com data, quantidade, empenho e total de embalagens. Pode ser
    subdividida em partes.
    """

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
    parte = models.IntegerField(blank=True, null=True, verbose_name="Parte")
    data_programada = models.DateField("Data Programada", blank=True, null=True)
    quantidade = models.FloatField(blank=True, null=True)
    total_embalagens = models.FloatField("Total de Embalagens", blank=True, null=True)

    def __str__(self):
        etapa = f" {self.etapa}" if self.etapa is not None else ""
        parte = f"Parte {self.parte} - " if self.parte is not None else ""
        cronograma = (
            f"Cronograma {self.cronograma.numero}"
            if self.cronograma is not None
            else "sem Cronograma"
        )

        return f"Etapa{etapa} - {parte}{cronograma}"

    class Meta:
        verbose_name = "Etapa do Cronograma"
        verbose_name_plural = "Etapas dos Cronogramas"
        ordering = ["etapa", "parte"]
        indexes = [
            models.Index(fields=["etapa", "parte"]),
        ]

    @classmethod
    def etapas_to_json(cls):
        result = []
        for numero in range(1, 101):
            choice = {"uuid": numero, "value": f"Etapa {numero}"}
            result.append(choice)
        return result

    @property
    def quantidade_estimada_disponivel(self):
        """Calcula a quantidade remanescente disponível para este mês.

        Agrega a quantidade de TODAS as etapas do mesmo cronograma e mês,
        subtrai a soma de todas as programações semanais (ProgramacaoEntregaSemanal)
        vinculadas ao mesmo cronograma e mesmo mês.

        Todas as etapas do mesmo mês retornam o mesmo valor (o saldo agregado do mês),
        evitando dupla-contagem quando há múltiplas etapas no mesmo período.

        Retorna None se não for possível calcular (sem data ou sem cronograma),
        ou um float com o saldo restante.
        """
        if not self.data_programada or not self.cronograma:
            return None

        from src.pre_recebimento.cronograma_semanal.models import (
            ProgramacaoEntregaSemanal,
        )

        mes = self.data_programada.strftime("%m/%Y")

        # Soma da quantidade de TODAS as etapas deste cronograma e mês
        total_etapas = (
            EtapasDoCronograma.objects.filter(
                cronograma=self.cronograma,
                data_programada__month=self.data_programada.month,
                data_programada__year=self.data_programada.year,
            ).aggregate(total=Sum("quantidade"))["total"]
            or 0
        )

        # Soma de todas as programações semanais deste cronograma e mês
        total_entregue = (
            ProgramacaoEntregaSemanal.objects.filter(
                cronograma_semanal__cronograma_mensal=self.cronograma,
                mes_programado=mes,
            ).aggregate(total=Sum("quantidade"))["total"]
            or 0
        )

        return float(total_etapas) - float(total_entregue)


class ProgramacaoDoRecebimentoDoCronograma(ModeloBase):
    """Programação de recebimento associada a um cronograma.

    Define as datas programadas e o tipo de carga (paletizada ou
    estivada/batida) para o recebimento dos produtos.
    """

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
    """QuerySet personalizado para SolicitacaoAlteracaoCronograma.

    Fornece métodos de filtro por status com ordenação pelo log
    mais recente e filtros por fornecedor, cronograma e produto.
    """

    def em_analise(self):
        return self.filter(status=CronogramaAlteracaoWorkflow.EM_ANALISE)

    def filtrar_por_status(self, status, filtros=None, init=None, end=None):
        """Filtra solicitações por status, ordenando pelo log mais recente.

        Aceita filtros opcionais por nome_fornecedor, numero_cronograma
        e nome_produto, além de parâmetros init/end para paginação.
        """
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
    """Solicitação de alteração de um cronograma já assinado.

    Permite que fornecedores ou CODAE solicitem alterações nas etapas
    e programações de recebimento de um cronograma. Passa por um fluxo
    de aprovação próprio (FluxoAlteracaoCronograma).
    """

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
        """Gera o número único da solicitação de alteração.

        O formato é ``XXXXXXXX-ALT``, onde ``XXXXXXXX`` é o PK
        preenchido com zeros à esquerda.
        """
        self.numero_solicitacao = f"{str(self.pk).zfill(8)}-ALT"

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        """Registra no log a transição de status da solicitação.

        Cria um LogSolicitacoesUsuario com os dados da transição.
        """
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
        """Registra a ciência do cronograma sobre a alteração proposta.

        Substitui as etapas novas pelas recebidas, salva as programações
        de recebimento e avança o fluxo para CRONOGRAMA_CIENTE.
        """
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
    """Sinal post_save que gera o número da solicitação de alteração.

    Executado automaticamente após a criação de uma
    SolicitacaoAlteracaoCronograma, atribuindo o número no formato
    XXXXXXXX-ALT.
    """
    if created:
        instance.gerar_numero_solicitacao()
        instance.save()


class InterrupcaoProgramadaEntrega(ModeloBase):
    """Interrupção programada em que não há recebimento de entregas.

    Utilizada pelo calendário de cronogramas para bloquear datas específicas
    em que as entregas não podem ocorrer (feriados, emendas de feriado,
    reuniões, inventários, etc.).

    A interrupção é separada por tipo de calendário:
    - ``ARMAZENAVEL``: Bloqueia o calendário de cronogramas armazenáveis.
    - ``PONTO_A_PONTO``: Bloqueia o calendário de cronogramas FLV.

    A combinação ``data`` + ``tipo_calendario`` é única, garantindo que
    não haja duplicidade de registros para o mesmo dia e tipo.
    """

    MOTIVO_EMENDA = "EMENDA"
    MOTIVO_REUNIAO = "REUNIAO"
    MOTIVO_INVENTARIO = "INVENTARIO"
    MOTIVO_FERIADO = "FERIADO"
    MOTIVO_OUTROS = "OUTROS"

    MOTIVO_CHOICES = (
        (MOTIVO_EMENDA, "Emenda"),
        (MOTIVO_REUNIAO, "Reunião"),
        (MOTIVO_INVENTARIO, "Inventário"),
        (MOTIVO_FERIADO, "Feriado"),
        (MOTIVO_OUTROS, "Outros"),
    )

    TIPO_CALENDARIO_ARMAZENAVEL = "ARMAZENAVEL"
    TIPO_CALENDARIO_PONTO_A_PONTO = "PONTO_A_PONTO"

    TIPO_CALENDARIO_CHOICES = (
        (TIPO_CALENDARIO_ARMAZENAVEL, "Armazenável"),
        (TIPO_CALENDARIO_PONTO_A_PONTO, "Ponto a Ponto"),
    )

    data = models.DateField("Data da Interrupção")
    motivo = models.CharField(
        "Motivo da Interrupção", max_length=20, choices=MOTIVO_CHOICES
    )
    descricao_motivo = models.TextField(
        "Descrição do Motivo",
        blank=True,
        help_text="Obrigatório quando motivo = OUTROS",
    )
    tipo_calendario = models.CharField(
        "Tipo de Calendário",
        max_length=20,
        choices=TIPO_CALENDARIO_CHOICES,
        default=TIPO_CALENDARIO_ARMAZENAVEL,
    )

    class Meta:
        verbose_name = "Interrupção Programada de Entrega"
        verbose_name_plural = "Interrupções Programadas de Entregas"
        unique_together = [("data", "tipo_calendario")]

    def __str__(self):
        return f"Interrupção {self.get_motivo_display()} - {self.data:%d/%m/%Y}"
