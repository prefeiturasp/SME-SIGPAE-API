from datetime import datetime

from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models
from django.db.models import QuerySet
from django_prometheus.models import ExportModelOperationsMixin

from ..dados_comuns.behaviors import (
    ArquivoCargaBase,
    Ativavel,
    CriadoEm,
    CriadoPor,
    Descritivel,
    Logs,
    Nomeavel,
    TemChaveExterna,
    TemData,
    TemIdentificadorExternoAmigavel,
    TemPrioridade,
)
from ..dados_comuns.fluxo_status import FluxoDietaEspecialPartindoDaEscola
from ..dados_comuns.models import LogSolicitacoesUsuario, TemplateMensagem
from ..dados_comuns.utils import convert_base64_to_contentfile
from ..escola.api.serializers import AlunoSerializer
from ..escola.constants import CEI_OU_EMEI, INFANTIL_OU_FUNDAMENTAL
from ..escola.models import Aluno, Escola
from .managers import AlimentoProprioManager

PENDENTES_EVENTO_DIETA_ESPECIAL = [
    LogSolicitacoesUsuario.INICIO_FLUXO,
    LogSolicitacoesUsuario.INICIO_FLUXO_INATIVACAO,
]

AUTORIZADO_EVENTO_DIETA_ESPECIAL = [
    LogSolicitacoesUsuario.CODAE_AUTORIZOU,
    LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
    LogSolicitacoesUsuario.CODAE_AUTORIZOU_INATIVACAO,
    LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
    LogSolicitacoesUsuario.INICIO_FLUXO,
]

NEGADOS_EVENTO_DIETA_ESPECIAL = [
    LogSolicitacoesUsuario.CODAE_NEGOU,
    LogSolicitacoesUsuario.CODAE_NEGOU_INATIVACAO,
    LogSolicitacoesUsuario.CODAE_NEGOU_CANCELAMENTO,
]

CANCELADOS_EVENTO_DIETA_ESPECIAL = [
    LogSolicitacoesUsuario.ESCOLA_CANCELOU,
    LogSolicitacoesUsuario.CANCELADO_ALUNO_MUDOU_ESCOLA,
    LogSolicitacoesUsuario.CANCELADO_ALUNO_NAO_PERTENCE_REDE,
    LogSolicitacoesUsuario.TERMINADA_AUTOMATICAMENTE_SISTEMA,
]

CANCELADOS_EVENTO_DIETA_ESPECIAL_TEMP = [
    LogSolicitacoesUsuario.CODAE_AUTORIZOU_INATIVACAO,
    LogSolicitacoesUsuario.TERMINADA_AUTOMATICAMENTE_SISTEMA,
    LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
    LogSolicitacoesUsuario.ESCOLA_CANCELOU,
]


class SolicitacaoDietaEspecial(
    ExportModelOperationsMixin("dieta_especial"),
    TemChaveExterna,
    CriadoEm,
    CriadoPor,
    FluxoDietaEspecialPartindoDaEscola,
    TemPrioridade,
    Logs,
    TemIdentificadorExternoAmigavel,
    Ativavel,
):
    DESCRICAO_SOLICITACAO = {
        "CODAE_A_AUTORIZAR": "Solicitação de Inclusão",
        "CODAE_NEGOU_PEDIDO": "Negada a Inclusão",
        "CODAE_AUTORIZADO": "Autorizada",
        "ESCOLA_SOLICITOU_INATIVACAO": "Solicitação de Cancelamento",
        "CODAE_NEGOU_INATIVACAO": "Negada o Cancelamento",
        "CODAE_AUTORIZOU_INATIVACAO": "Cancelamento Autorizado",
        "ESCOLA_CANCELOU": "Cancelada pela Unidade Escolar",
    }

    TIPO_SOLICITACAO_CHOICES = [
        ("COMUM", "Comum"),
        ("ALUNO_NAO_MATRICULADO", "Aluno não matriculado"),
        ("ALTERACAO_UE", "Alteração U.E"),
        ("CANCELAMENTO_DIETA", "Cancelamento de dieta especial"),
    ]

    aluno = models.ForeignKey(
        "escola.Aluno",
        null=True,
        on_delete=models.PROTECT,
        related_name="dietas_especiais",
    )
    nome_completo_pescritor = models.CharField(
        "Nome completo do pescritor da receita",
        max_length=200,
        validators=[MinLengthValidator(6)],
        blank=True,
    )
    registro_funcional_pescritor = models.CharField(
        "Registro funcional do pescritor da receita",
        help_text="CRN/CRM/CRFa...",
        max_length=200,
        validators=[MinLengthValidator(4), MaxLengthValidator(6)],
        blank=True,
    )
    registro_funcional_nutricionista = models.CharField(
        "Registro funcional do nutricionista",
        help_text="CRN/CRM/CRFa...",
        max_length=200,
        validators=[MinLengthValidator(6)],
        blank=True,
    )
    # Preenchido pela Escola
    observacoes = models.TextField("Observações", blank=True)

    # Preenchido pela_ CODAE ao autorizar a dieta
    informacoes_adicionais = models.TextField("Informações Adicionais", blank=True)

    protocolo_padrao = models.ForeignKey(
        "ProtocoloPadraoDietaEspecial",
        on_delete=models.PROTECT,
        related_name="solicitacoes_dietas_especiais",
        blank=True,
        null=True,
    )

    nome_protocolo = models.TextField("Nome do Protocolo", blank=True)

    # Preenchido pela NutriCODAE ao autorizar a dieta
    orientacoes_gerais = models.TextField("Orientações Gerais", blank=True)

    # TODO: Confirmar se PROTECT é a melhor escolha para o campos abaixo
    classificacao = models.ForeignKey(
        "ClassificacaoDieta", blank=True, null=True, on_delete=models.PROTECT
    )
    alergias_intolerancias = models.ManyToManyField("AlergiaIntolerancia", blank=True)

    # TODO: Confirmar se PROTECT é a melhor escolha para o campos abaixo
    motivo_negacao = models.ForeignKey(
        "MotivoNegacao", on_delete=models.PROTECT, null=True
    )

    # TODO: Mover essa justificativa para o log de transição de status
    justificativa_negacao = models.TextField(blank=True)

    data_termino = models.DateField(
        null=True
    )  # , validators=[nao_pode_ser_no_passado] # noqa

    motivo_alteracao_ue = models.ForeignKey(
        "MotivoAlteracaoUE", blank=True, null=True, on_delete=models.CASCADE
    )

    escola_destino = models.ForeignKey(
        "escola.Escola", blank=True, null=True, on_delete=models.CASCADE
    )

    dieta_alterada = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.CASCADE
    )

    data_inicio = models.DateField(null=True, blank=True)

    tipo_solicitacao = models.CharField(
        max_length=30,
        choices=TIPO_SOLICITACAO_CHOICES,
        default="COMUM",
    )

    observacoes_alteracao = models.TextField("Observações Alteração", blank=True)

    caracteristicas_do_alimento = models.TextField(
        "Características dos alimentos", blank=True
    )

    conferido = models.BooleanField("Marcar como conferido?", default=False)

    eh_importado = models.BooleanField("Proveniente de importacao?", default=False)

    dieta_para_recreio_ferias = models.BooleanField(
        "Dieta para Recreio nas Férias", default=False
    )

    periodo_recreio_inicio = models.DateField(
        "Período do Recreio - De", null=True, blank=True
    )

    periodo_recreio_fim = models.DateField(
        "Período do Recreio - Até", null=True, blank=True
    )

    @classmethod
    def _get_quantidade_solicitacoes_que_ja_estiveram_nos_status(
        cls, solicitacoes: QuerySet, status: list
    ):
        uuids = set(list(solicitacoes.values_list("uuid", flat=True)))
        return len(
            set(
                LogSolicitacoesUsuario.objects.filter(
                    uuid_original__in=uuids, status_evento__in=status
                ).values_list("uuid_original", flat=True)
            )
        )

    @classmethod
    def quantidade_solicitacoes_que_ja_estiveram_pendentes(cls, solicitacoes):
        return cls._get_quantidade_solicitacoes_que_ja_estiveram_nos_status(
            solicitacoes, PENDENTES_EVENTO_DIETA_ESPECIAL
        )

    @classmethod
    def quantidade_solicitacoes_que_ja_estiveram_autorizadas(cls, solicitacoes):
        return cls._get_quantidade_solicitacoes_que_ja_estiveram_nos_status(
            solicitacoes, AUTORIZADO_EVENTO_DIETA_ESPECIAL
        )

    @classmethod
    def quantidade_solicitacoes_que_ja_estiveram_negadas(cls, solicitacoes):
        return cls._get_quantidade_solicitacoes_que_ja_estiveram_nos_status(
            solicitacoes, NEGADOS_EVENTO_DIETA_ESPECIAL
        )

    @classmethod
    def quantidade_solicitacoes_que_ja_estiveram_canceladas(cls, solicitacoes):
        solicitacoes = solicitacoes.filter(
            tipo_solicitacao__in=["ALTERACAO_UE", "COMUM"]
        )
        status = (
            CANCELADOS_EVENTO_DIETA_ESPECIAL_TEMP + CANCELADOS_EVENTO_DIETA_ESPECIAL
        )
        return cls._get_quantidade_solicitacoes_que_ja_estiveram_nos_status(
            solicitacoes, status
        )

    @classmethod
    def get_totais_gerencial_dietas(cls, queryset=None):
        queryset = (
            SolicitacaoDietaEspecial.objects.all() if queryset is None else queryset
        )

        total_solicitacoes = (
            SolicitacaoDietaEspecial.quantidade_solicitacoes_que_ja_estiveram_pendentes(
                queryset
            )
        )
        total_autorizadas = SolicitacaoDietaEspecial.quantidade_solicitacoes_que_ja_estiveram_autorizadas(
            queryset
        )
        total_negadas = (
            SolicitacaoDietaEspecial.quantidade_solicitacoes_que_ja_estiveram_negadas(
                queryset
            )
        )
        total_canceladas = SolicitacaoDietaEspecial.quantidade_solicitacoes_que_ja_estiveram_canceladas(
            queryset
        )

        return {
            "total_solicitacoes": total_solicitacoes,
            "total_autorizadas": total_autorizadas,
            "total_negadas": total_negadas,
            "total_canceladas": total_canceladas,
        }

    @classmethod
    def aluno_possui_dieta_especial_autorizada_alteracao_ue_recreio_ferias(
        cls, aluno, dieta_alterada, motivo_recreio_ferias
    ):
        return cls.objects.filter(
            aluno=aluno,
            dieta_alterada=dieta_alterada,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            tipo_solicitacao="ALTERACAO_UE",
            motivo_alteracao_ue=motivo_recreio_ferias,
        ).exists()

    @classmethod
    def aluno_possui_dieta_especial_pendente(cls, aluno):
        return cls.objects.filter(
            aluno=aluno, status=cls.workflow_class.CODAE_A_AUTORIZAR
        ).exists()

    @property
    def DESCRICAO(self):
        descricao = self.DESCRICAO_SOLICITACAO.get(self.status)
        return f"Dieta Especial - {descricao}" if descricao else "Dieta Especial"

    # Property necessária para retornar dados no serializer de criação de
    # Dieta Especial
    @property
    def aluno_json(self):
        return AlunoSerializer(self.aluno).data

    @property
    def anexos(self):
        return self.anexo_set.all()

    @property
    def numero_alunos(self):
        return ""

    @property
    def escola(self):
        return self.rastro_escola

    def cria_anexos_inativacao(self, anexos):
        assert isinstance(anexos, list), "anexos precisa ser uma lista"  # nosec
        assert len(anexos) > 0, "anexos não pode ser vazio"  # nosec
        for anexo in anexos:
            data = convert_base64_to_contentfile(anexo.get("base64"))
            Anexo.objects.create(
                solicitacao_dieta_especial=self,
                arquivo=data,
                nome=anexo.get("nome", ""),
                eh_laudo_alta=True,
            )

    @property
    def substituicoes(self):
        return self.substituicaoalimento_set.all()

    @property
    def str_dre_lote_escola(self):
        dre = "SEM DRE"
        lote = "SEM LOTE"
        escola = "SEM ESCOLA"
        if self.escola_destino:
            escola = f"{self.escola_destino.nome}"
            if self.escola_destino.diretoria_regional:
                dre = (
                    f'DRE {self.escola_destino.diretoria_regional.nome.split(" ")[-1]}'
                )
            if self.escola_destino.lote:
                lote = f"{self.escola_destino.lote.nome}"
        return f"{dre}  - {lote} - {escola}"

    @property
    def template_mensagem(self):
        template = TemplateMensagem.objects.get(tipo=TemplateMensagem.DIETA_ESPECIAL)
        template_troca = {
            "@id": self.id_externo,
            "@criado_em": str(self.criado_em),
            "@criado_por": str(self.criado_por),
            "@status": str(self.status),
            # TODO: verificar a url padrão do pedido
            "@link": "http://teste.com",
        }
        corpo = template.template_html
        for chave, valor in template_troca.items():
            corpo = corpo.replace(chave, valor)
        return template.assunto, corpo

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.DIETA_ESPECIAL,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
        )

    @property
    def display_nutricionista_with_registro_funcional(self):
        usuario = self.logs.get(
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            solicitacao_tipo=LogSolicitacoesUsuario.DIETA_ESPECIAL,
        ).usuario
        if usuario.registro_funcional:
            return f"Elaborado por {usuario.nome} - RF {usuario.registro_funcional}"
        return self.registro_funcional_nutricionista

    @property
    def data_ultimo_log(self):
        return (
            datetime.strftime(self.logs.last().criado_em, "%d/%m/%Y")
            if self.logs
            else None
        )

    def clean(self):
        super().clean()
        if self.dieta_para_recreio_ferias:
            if not self.periodo_recreio_inicio or not self.periodo_recreio_fim:
                raise ValidationError(
                    "Os campos de período são obrigatórios quando dieta para recreio nas férias está selecionada."
                )
            if self.periodo_recreio_fim < self.periodo_recreio_inicio:
                raise ValidationError(
                    "A data final não pode ser anterior à data inicial."
                )

    class Meta:
        ordering = ("-ativo", "-criado_em")
        verbose_name = "Solicitação de dieta especial"
        verbose_name_plural = "Solicitações de dieta especial"

    def __str__(self):
        if self.aluno:
            return f"{self.aluno.codigo_eol}: {self.aluno.nome}"
        return f"Solicitação #{self.id_externo}"


class Anexo(ExportModelOperationsMixin("anexo"), models.Model):
    solicitacao_dieta_especial = models.ForeignKey(
        SolicitacaoDietaEspecial, on_delete=models.CASCADE
    )
    nome = models.CharField(max_length=100, blank=True)
    arquivo = models.FileField()
    eh_laudo_alta = models.BooleanField(default=False)

    def __str__(self):
        return self.nome


class AlergiaIntolerancia(Descritivel):
    def __str__(self):
        return self.descricao


class ClassificacaoDieta(Descritivel, Nomeavel):
    def __str__(self):
        return self.nome


class MotivoAlteracaoUE(Descritivel, Nomeavel, TemChaveExterna):
    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Motivo Alteração U.E"
        verbose_name_plural = "Motivo Alteração U.E"


class MotivoNegacao(Descritivel):
    CANCELAMENTO = "CANCELAMENTO"
    INCLUSAO = "INCLUSAO"

    PROCESSO_CHOICES = (
        (CANCELAMENTO, "Solicitação de Cancelamento"),
        (INCLUSAO, "Solicitação de Inclusão"),
    )

    processo = models.CharField(
        choices=PROCESSO_CHOICES, default=INCLUSAO, blank=False, max_length=20
    )

    def __str__(self):
        return self.descricao


class SolicitacoesDietaEspecialAtivasInativasPorAluno(models.Model):
    aluno = models.OneToOneField(Aluno, on_delete=models.DO_NOTHING, primary_key=True)
    ativas = models.IntegerField()
    inativas = models.IntegerField()

    class Meta:
        managed = False
        db_table = "dietas_ativas_inativas_por_aluno"


class Alimento(Nomeavel, TemChaveExterna, Ativavel):
    TIPO_CHOICES = (("E", "Edital"), ("P", "Proprio"))
    SO_ALIMENTOS = "SO_ALIMENTOS"
    SO_SUBSTITUTOS = "SO_SUBSTITUTOS"
    AMBOS = "AMBOS"
    TIPO_LISTAGEM_PROTOCOLO = (
        (SO_ALIMENTOS, "Aparece somente na listagem de alimentos"),
        (SO_SUBSTITUTOS, "Aparece somente na listagem de alimentos substitutos"),
        (AMBOS, "Aparece nas listagem de alimentos e substitutos"),
    )

    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES, default="E")
    marca = models.ForeignKey(
        "produto.Marca", on_delete=models.PROTECT, blank=True, null=True
    )
    outras_informacoes = models.CharField(max_length=255, blank=True)
    tipo_listagem_protocolo = models.CharField(
        max_length=15, choices=TIPO_LISTAGEM_PROTOCOLO, default=SO_ALIMENTOS
    )

    class Meta:
        ordering = ("nome",)
        unique_together = ("nome", "marca")

    def __str__(self):
        return self.nome


class AlimentoProprio(Alimento):
    objects = AlimentoProprioManager()

    class Meta:
        proxy = True
        verbose_name = "alimento próprio CODAE"
        verbose_name_plural = "alimentos próprios CODAE"

    def save(self, *args, **kwargs):
        self.tipo = "P"
        super(AlimentoProprio, self).save(*args, **kwargs)


class SubstituicaoAlimento(models.Model):
    TIPO_CHOICES = [("I", "Isento"), ("S", "Substituir")]
    solicitacao_dieta_especial = models.ForeignKey(
        SolicitacaoDietaEspecial, on_delete=models.CASCADE
    )
    alimento = models.ForeignKey(
        Alimento, on_delete=models.PROTECT, blank=True, null=True
    )
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES, blank=True)
    substitutos = models.ManyToManyField(
        "produto.Produto",
        related_name="substitutos",
        blank=True,
        help_text="produtos substitutos",
    )
    alimentos_substitutos = models.ManyToManyField(
        Alimento, related_name="alimentos_substitutos", blank=True
    )


class TipoContagem(Nomeavel, TemChaveExterna):
    def __str__(self):
        return self.nome


class PlanilhaDietasAtivas(models.Model):
    """Importa dados de planilha de Dietas Ativas específicas.

    Requer uma planilha com o De Para entre Código Escola e Código EOL da Escola.
    """

    arquivo = models.FileField(
        blank=True, null=True, help_text="Arquivo com escolas e dietas"
    )  # noqa DJ01
    arquivo_unidades_da_rede = models.FileField(
        blank=True, null=True, help_text="Arquivo unidades_da_rede...xlsx"
    )  # noqa DJ01
    resultado = models.FileField(
        blank=True, null=True, help_text="Arquivo com o resultado"
    )  # noqa DJ01
    tempfile = models.CharField(
        max_length=100, null=True, blank=True, help_text="JSON temporario"
    )  # noqa DJ01
    criado_em = models.DateTimeField("criado em", auto_now_add=True, auto_now=False)

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "Planilha Dieta Ativa"
        verbose_name_plural = "Planilhas Dietas Ativas"

    def __str__(self):
        return str(self.arquivo)


class LogDietasAtivasCanceladasAutomaticamente(CriadoEm):
    dieta = models.ForeignKey(
        "SolicitacaoDietaEspecial",
        on_delete=models.CASCADE,
        related_name="dietas_especiais",
    )
    codigo_eol_aluno = models.CharField(  # noqa DJ01
        "Código EOL aluno",
        max_length=7,
        validators=[MinLengthValidator(7)],
        null=True,
        blank=True,
    )
    nome_aluno = models.CharField(
        "Nome do Aluno", max_length=100, null=True, blank=True
    )  # noqa DJ01
    codigo_eol_escola_origem = models.CharField(  # noqa DJ01
        "Código EOL escola origem",
        max_length=6,
        validators=[MinLengthValidator(6)],
        null=True,
        blank=True,
    )
    nome_escola_origem = models.CharField(
        "Nome da Escola origem", max_length=160, null=True, blank=True
    )  # noqa DJ01
    codigo_eol_escola_destino = models.CharField(  # noqa DJ01
        "Código EOL escola destino",
        max_length=6,
        validators=[MinLengthValidator(6)],
        null=True,
        blank=True,
    )
    nome_escola_destino = models.CharField(
        "Nome da Escola destino", max_length=160, null=True, blank=True
    )  # noqa DJ01

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "log dietas ativas canceladas automaticamente"
        verbose_name_plural = "log dietas ativas canceladas automaticamente"

    def __str__(self):
        return str(self.pk)

    @property
    def escola_existe(self):
        escola_existe_no_sigpae = Escola.objects.filter(
            codigo_eol=self.codigo_eol_escola_destino
        ).first()
        if escola_existe_no_sigpae:
            return True
        return False


class AlimentoSubstituto(models.Model):
    substituicao_alimento_protocolo_padrao = models.ForeignKey(
        "SubstituicaoAlimentoProtocoloPadrao", on_delete=models.SET_NULL, null=True
    )
    alimento = models.ForeignKey(
        Alimento, on_delete=models.SET_NULL, null=True, blank=True
    )


class ProtocoloPadraoDietaEspecial(
    TemChaveExterna, CriadoEm, CriadoPor, TemIdentificadorExternoAmigavel, Ativavel
):
    # Mantive para termos um histórico acessível pelo admin
    history = AuditlogHistoryField()

    # Status Choice
    STATUS_LIBERADO = "LIBERADO"
    STATUS_NAO_LIBERADO = "NAO_LIBERADO"

    STATUS_NOMES = {
        STATUS_LIBERADO: "Liberado",
        STATUS_NAO_LIBERADO: "Não Liberado",
    }

    STATUS_CHOICES = (
        (STATUS_LIBERADO, STATUS_NOMES[STATUS_LIBERADO]),
        (STATUS_NAO_LIBERADO, STATUS_NOMES[STATUS_NAO_LIBERADO]),
    )

    nome_protocolo = models.TextField("Nome do Protocolo")

    orientacoes_gerais = models.TextField("Orientações Gerais", blank=True)

    status = models.CharField(
        "Status da guia",
        max_length=25,
        choices=STATUS_CHOICES,
        default=STATUS_NAO_LIBERADO,
    )

    outras_informacoes = models.TextField("Outras Informações", blank=True)

    editais = models.ManyToManyField(
        "terceirizada.Edital", related_name="protocolos_padroes_dieta_especial"
    )

    historico = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ("nome_protocolo",)
        verbose_name = "Protocolo padrão de dieta especial"
        verbose_name_plural = "Protocolos padrões de dieta especial"

    def __str__(self):
        return str(self.nome_protocolo)


class SubstituicaoAlimentoProtocoloPadrao(models.Model):
    history = AuditlogHistoryField()

    TIPO_CHOICES = [("I", "Isento"), ("S", "Substituir")]
    protocolo_padrao = models.ForeignKey(
        ProtocoloPadraoDietaEspecial,
        on_delete=models.CASCADE,
        related_name="substituicoes",
    )
    alimento = models.ForeignKey(
        Alimento, on_delete=models.PROTECT, blank=True, null=True
    )
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES, blank=True)
    substitutos = models.ManyToManyField(
        "produto.Produto",
        related_name="substitutos_protocolo_padrao",
        blank=True,
        help_text="produtos substitutos",
    )
    alimentos_substitutos = models.ManyToManyField(
        Alimento,
        related_name="alimentos_substitutos_protocolo_padrao",
        blank=True,
        through="AlimentoSubstituto",
    )

    class Meta:
        verbose_name = "Substituição de alimento para protocolo padrão de dieta"
        verbose_name_plural = (
            "Substituições de alimentos para protocolos padrões de dietas"
        )

    def __str__(self):
        return f"substituição protocolo padrão: {self.protocolo_padrao}, tipo: {self.tipo}."


auditlog.register(ProtocoloPadraoDietaEspecial)
auditlog.register(SubstituicaoAlimentoProtocoloPadrao)
auditlog.register(SubstituicaoAlimentoProtocoloPadrao.alimentos_substitutos.through)
auditlog.register(AlimentoSubstituto)


class ArquivoCargaDietaEspecial(ArquivoCargaBase):
    resultado = models.FileField(blank=True, default="")

    class Meta:
        verbose_name = "Arquivo para importação de solicitações de Dieta Especial"
        verbose_name_plural = (
            "Arquivos para importação de solicitações de Dieta Especial"
        )

    def __str__(self) -> str:
        return str(self.conteudo)


class ArquivoCargaAlimentosSubstitutos(ArquivoCargaBase):
    class Meta:
        verbose_name = "Arquivo para importação de Alimentos e Alimentos substitutos"
        verbose_name_plural = (
            "Arquivos para importação de Alimentos e Alimentos substitutos"
        )

    def __str__(self) -> str:
        return str(self.conteudo)


class ArquivoCargaUsuariosEscola(ArquivoCargaBase):
    """Essa classe foi colocada aqui pois os usuários seriam usados para a dieta especial."""

    resultado = models.FileField(blank=True, default="")

    class Meta:
        verbose_name = (
            "Arquivo para importação de usuários Diretor e Assistente Diretor"
        )
        verbose_name_plural = (
            "Arquivos para importação de usuários Diretor e Assistente Diretor"
        )

    def __str__(self) -> str:
        return str(self.conteudo)


class LogQuantidadeDietasAutorizadas(TemChaveExterna, TemData, CriadoEm):
    escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.CASCADE,
        related_name="logs_dietas_autorizadas",
    )
    quantidade = models.PositiveIntegerField()
    classificacao = models.ForeignKey(
        "ClassificacaoDieta",
        on_delete=models.CASCADE,
        related_name="logs_dietas_autorizadas",
    )
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="logs_dietas_autorizadas",
    )
    cei_ou_emei = models.CharField(max_length=4, choices=CEI_OU_EMEI, default="N/A")
    infantil_ou_fundamental = models.CharField(
        max_length=11, choices=INFANTIL_OU_FUNDAMENTAL, default="N/A"
    )

    def __str__(self) -> str:
        return (
            f'{self.escola.nome} - {self.data.strftime("%d/%m/%Y")} - {self.classificacao.nome}'
            f'{(" - " + self.periodo_escolar.nome) if self.periodo_escolar else ""}'
            f" - {self.quantidade} dieta(s)"
        )

    class Meta:
        verbose_name = "Log da quantidade de dietas autorizadas por unidade escolar"
        verbose_name_plural = (
            "Logs da quantidade de dietas autorizadas por unidade escolar"
        )
        ordering = ("-data", "escola__nome")


class LogQuantidadeDietasAutorizadasCEI(TemChaveExterna, TemData, CriadoEm):
    escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.CASCADE,
        related_name="logs_dietas_autorizadas_cei",
    )
    quantidade = models.PositiveIntegerField()
    classificacao = models.ForeignKey(
        "ClassificacaoDieta",
        on_delete=models.CASCADE,
        related_name="logs_dietas_autorizadas_cei",
    )
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar",
        related_name="logs_dietas_autorizadas_cei",
        on_delete=models.CASCADE,
    )
    faixa_etaria = models.ForeignKey(
        "escola.FaixaEtaria", null=True, on_delete=models.DO_NOTHING
    )

    def __str__(self) -> str:
        return (
            f'{self.escola.nome} - {self.data.strftime("%d/%m/%Y")} - {self.periodo_escolar.nome} - '
            f"{self.classificacao.nome} - {self.quantidade} dieta(s) -- {self.faixa_etaria}"
        )

    class Meta:
        verbose_name = "Log da quantidade de dietas autorizadas por unidade escolar CEI"
        verbose_name_plural = (
            "Logs da quantidade de dietas autorizadas por unidade escolar CEI"
        )
        ordering = ("-data", "escola__nome")
