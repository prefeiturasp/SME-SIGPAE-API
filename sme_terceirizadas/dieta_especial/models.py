from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

from ..dados_comuns.behaviors import (
    Ativavel,
    CriadoEm,
    CriadoPor,
    Descritivel,
    Logs,
    Nomeavel,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
    TemPrioridade
)
from ..dados_comuns.fluxo_status import FluxoDietaEspecialPartindoDaEscola
from ..dados_comuns.models import LogSolicitacoesUsuario, TemplateMensagem
from ..dados_comuns.utils import convert_base64_to_contentfile
from ..dados_comuns.validators import nao_pode_ser_no_passado
from ..escola.api.serializers import AlunoSerializer
from ..escola.models import Aluno, Escola
from .managers import AlimentoProprioManager


class SolicitacaoDietaEspecial(
    ExportModelOperationsMixin('dieta_especial'),
    TemChaveExterna,
    CriadoEm, CriadoPor,
    FluxoDietaEspecialPartindoDaEscola,
    TemPrioridade,
    Logs,
    TemIdentificadorExternoAmigavel,
    Ativavel
):
    DESCRICAO_SOLICITACAO = {
        'CODAE_A_AUTORIZAR': 'Solicitação de Inclusão',
        'CODAE_NEGOU_PEDIDO': 'Negada a Inclusão',
        'CODAE_AUTORIZADO': 'Autorizada',
        'ESCOLA_SOLICITOU_INATIVACAO': 'Solicitação de Cancelamento',
        'CODAE_NEGOU_INATIVACAO': 'Negada o Cancelamento',
        'CODAE_AUTORIZOU_INATIVACAO': 'Cancelamento Autorizado',
        'ESCOLA_CANCELOU': 'Cancelada pela Unidade Escolar',
    }

    TIPO_SOLICITACAO_CHOICES = [
        ('COMUM', 'Comum'),
        ('ALUNO_NAO_MATRICULADO', 'Aluno não matriculado'),
        ('ALTERACAO_UE', 'Alteração U.E'),
    ]

    aluno = models.ForeignKey(
        'escola.Aluno',
        null=True,
        on_delete=models.PROTECT,
        related_name='dietas_especiais'
    )
    nome_completo_pescritor = models.CharField(
        'Nome completo do pescritor da receita',
        max_length=200,
        validators=[MinLengthValidator(6)],
        blank=True
    )
    registro_funcional_pescritor = models.CharField(
        'Registro funcional do pescritor da receita',
        help_text='CRN/CRM/CRFa...',
        max_length=200,
        validators=[MinLengthValidator(4), MaxLengthValidator(6)],
        blank=True
    )
    registro_funcional_nutricionista = models.CharField(
        'Registro funcional do nutricionista',
        help_text='CRN/CRM/CRFa...',
        max_length=200,
        validators=[MinLengthValidator(6)],
        blank=True
    )
    # Preenchido pela Escola
    observacoes = models.TextField('Observações', blank=True)

    # Preenchido pela_ CODAE ao autorizar a dieta
    informacoes_adicionais = models.TextField(
        'Informações Adicionais',
        blank=True
    )

    protocolo_padrao = models.ForeignKey(
        'ProtocoloPadraoDietaEspecial',
        on_delete=models.PROTECT,
        related_name='solicitacoes_dietas_especiais',
        blank=True,
        null=True
    )

    nome_protocolo = models.TextField('Nome do Protocolo', blank=True)

    # Preenchido pela NutriCODAE ao autorizar a dieta
    orientacoes_gerais = models.TextField(
        'Orientações Gerais',
        blank=True
    )

    # TODO: Confirmar se PROTECT é a melhor escolha para o campos abaixo
    classificacao = models.ForeignKey(
        'ClassificacaoDieta',
        blank=True,
        null=True,
        on_delete=models.PROTECT
    )
    alergias_intolerancias = models.ManyToManyField(
        'AlergiaIntolerancia',
        blank=True
    )

    # TODO: Confirmar se PROTECT é a melhor escolha para o campos abaixo
    motivo_negacao = models.ForeignKey(
        'MotivoNegacao',
        on_delete=models.PROTECT,
        null=True
    )

    # TODO: Mover essa justificativa para o log de transição de status
    justificativa_negacao = models.TextField(blank=True)

    data_termino = models.DateField(
        null=True, validators=[nao_pode_ser_no_passado])

    motivo_alteracao_ue = models.ForeignKey(
        'MotivoAlteracaoUE',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    escola_destino = models.ForeignKey(
        'escola.Escola',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    dieta_alterada = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    data_inicio = models.DateField(
        null=True,
        blank=True
    )

    tipo_solicitacao = models.CharField(
        max_length=30,
        choices=TIPO_SOLICITACAO_CHOICES,
        default='COMUM',
    )

    observacoes_alteracao = models.TextField(
        'Observações Alteração',
        blank=True
    )

    caracteristicas_do_alimento = models.TextField(
        'Características dos alimentos',
        blank=True
    )

    @classmethod
    def aluno_possui_dieta_especial_pendente(cls, aluno):
        return cls.objects.filter(
            aluno=aluno,
            status=cls.workflow_class.CODAE_A_AUTORIZAR
        ).exists()

    @property
    def DESCRICAO(self):
        descricao = self.DESCRICAO_SOLICITACAO.get(self.status)
        return f'Dieta Especial - {descricao}' if descricao else 'Dieta Especial'

    # Property necessária para retornar dados no serializer de criação de
    # Dieta Especial
    @property
    def aluno_json(self):
        return AlunoSerializer(self.aluno).data

    @property
    def anexos(self):
        return self.anexo_set.all()

    @property
    def escola(self):
        return self.rastro_escola

    def cria_anexos_inativacao(self, anexos):
        assert isinstance(anexos, list), 'anexos precisa ser uma lista'
        assert len(anexos) > 0, 'anexos não pode ser vazio'
        for anexo in anexos:
            data = convert_base64_to_contentfile(anexo.get('base64'))
            Anexo.objects.create(
                solicitacao_dieta_especial=self,
                arquivo=data,
                nome=anexo.get('nome', ''),
                eh_laudo_alta=True
            )

    @property
    def substituicoes(self):
        return self.substituicaoalimento_set.all()

    @property
    def template_mensagem(self):
        template = TemplateMensagem.objects.get(
            tipo=TemplateMensagem.DIETA_ESPECIAL)
        template_troca = {
            '@id': self.id_externo,
            '@criado_em': str(self.criado_em),
            '@criado_por': str(self.criado_por),
            '@status': str(self.status),
            # TODO: verificar a url padrão do pedido
            '@link': 'http://teste.com',
        }
        corpo = template.template_html
        for chave, valor in template_troca.items():
            corpo = corpo.replace(chave, valor)
        return template.assunto, corpo

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get('justificativa', '')
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.DIETA_ESPECIAL,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa
        )

    class Meta:
        ordering = ('-ativo', '-criado_em')
        verbose_name = 'Solicitação de dieta especial'
        verbose_name_plural = 'Solicitações de dieta especial'

    def __str__(self):
        if self.aluno:
            return f'{self.aluno.codigo_eol}: {self.aluno.nome}'
        return f'Solicitação #{self.id_externo}'


class Anexo(ExportModelOperationsMixin('anexo'), models.Model):
    solicitacao_dieta_especial = models.ForeignKey(
        SolicitacaoDietaEspecial,
        on_delete=models.CASCADE
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
        verbose_name = 'Motivo Alteração U.E'
        verbose_name_plural = 'Motivo Alteração U.E'


class MotivoNegacao(Descritivel):

    def __str__(self):
        return self.descricao


class SolicitacoesDietaEspecialAtivasInativasPorAluno(models.Model):
    aluno = models.OneToOneField(
        Aluno,
        on_delete=models.DO_NOTHING,
        primary_key=True
    )
    ativas = models.IntegerField()
    inativas = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'dietas_ativas_inativas_por_aluno'


class Alimento(Nomeavel, TemChaveExterna, Ativavel):
    TIPO_CHOICES = (
        ('E', 'Edital'),
        ('P', 'Proprio')
    )
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES, default='E')
    marca = models.ForeignKey(
        'produto.Marca',
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    outras_informacoes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ('nome',)
        unique_together = ('nome', 'marca')

    def __str__(self):
        return self.nome


class AlimentoProprio(Alimento):
    objects = AlimentoProprioManager()

    class Meta:
        proxy = True
        verbose_name = 'alimento próprio CODAE'
        verbose_name_plural = 'alimentos próprios CODAE'

    def save(self, *args, **kwargs):
        self.tipo = 'P'
        super(AlimentoProprio, self).save(*args, **kwargs)


class SubstituicaoAlimento(models.Model):
    TIPO_CHOICES = [
        ('I', 'Isento'),
        ('S', 'Substituir')
    ]
    solicitacao_dieta_especial = models.ForeignKey(
        SolicitacaoDietaEspecial,
        on_delete=models.CASCADE
    )
    alimento = models.ForeignKey(
        Alimento,
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES, blank=True)
    substitutos = models.ManyToManyField(
        'produto.Produto',
        related_name='substitutos',
        blank=True,
        help_text='produtos substitutos'
    )
    alimentos_substitutos = models.ManyToManyField(
        Alimento,
        related_name='alimentos_substitutos',
        blank=True
    )


class TipoContagem(Nomeavel, TemChaveExterna):

    def __str__(self):
        return self.nome


class PlanilhaDietasAtivas(models.Model):
    """Importa dados de planilha de Dietas Ativas específicas.

    Requer uma planilha com o De Para entre Código Escola e Código EOL da Escola.
    """

    arquivo = models.FileField(blank=True, null=True, help_text='Arquivo com escolas e dietas')  # noqa DJ01
    arquivo_unidades_da_rede = models.FileField(blank=True, null=True, help_text='Arquivo unidades_da_rede...xlsx')  # noqa DJ01
    resultado = models.FileField(blank=True, null=True, help_text='Arquivo com o resultado')  # noqa DJ01
    tempfile = models.CharField(max_length=100, null=True, blank=True, help_text='JSON temporario')  # noqa DJ01
    criado_em = models.DateTimeField(
        'criado em',
        auto_now_add=True,
        auto_now=False
    )

    class Meta:
        ordering = ('-criado_em',)
        verbose_name = 'Planilha Dieta Ativa'
        verbose_name_plural = 'Planilhas Dietas Ativas'

    def __str__(self):
        return str(self.arquivo)


class LogDietasAtivasCanceladasAutomaticamente(CriadoEm):
    dieta = models.ForeignKey(
        'SolicitacaoDietaEspecial',
        on_delete=models.CASCADE,
        related_name='dietas_especiais',
    )
    codigo_eol_aluno = models.CharField(  # noqa DJ01
        'Código EOL aluno',
        max_length=7,
        validators=[MinLengthValidator(7)],
        null=True,
        blank=True
    )
    nome_aluno = models.CharField('Nome do Aluno', max_length=100, null=True, blank=True)  # noqa DJ01
    codigo_eol_escola_origem = models.CharField(  # noqa DJ01
        'Código EOL escola origem',
        max_length=6,
        validators=[MinLengthValidator(6)],
        null=True,
        blank=True
    )
    nome_escola_origem = models.CharField('Nome da Escola origem', max_length=160, null=True, blank=True)  # noqa DJ01
    codigo_eol_escola_destino = models.CharField(  # noqa DJ01
        'Código EOL escola destino',
        max_length=6,
        validators=[MinLengthValidator(6)],
        null=True,
        blank=True
    )
    nome_escola_destino = models.CharField('Nome da Escola destino', max_length=160, null=True, blank=True)  # noqa DJ01

    class Meta:
        ordering = ('-criado_em',)
        verbose_name = 'log dietas ativas canceladas automaticamente'
        verbose_name_plural = 'log dietas ativas canceladas automaticamente'

    def __str__(self):
        return str(self.pk)

    @property
    def escola_existe(self):
        escola_existe_no_sigpae = Escola.objects.filter(codigo_eol=self.codigo_eol_escola_destino).first()
        if escola_existe_no_sigpae:
            return True
        return False


class ProtocoloPadraoDietaEspecial(TemChaveExterna, CriadoEm, CriadoPor, TemIdentificadorExternoAmigavel):
    # Status Choice
    STATUS_LIBERADO = 'LIBERADO'
    STATUS_NAO_LIBERADO = 'NAO_LIBERADO'

    STATUS_NOMES = {
        STATUS_LIBERADO: 'Liberado',
        STATUS_NAO_LIBERADO: 'Não Liberado',
    }

    STATUS_CHOICES = (
        (STATUS_LIBERADO, STATUS_NOMES[STATUS_LIBERADO]),
        (STATUS_NAO_LIBERADO, STATUS_NOMES[STATUS_NAO_LIBERADO]),
    )

    nome_protocolo = models.TextField('Nome do Protocolo')

    orientacoes_gerais = models.TextField(
        'Orientações Gerais',
        blank=True
    )

    status = models.CharField(
        'Status da guia',
        max_length=25,
        choices=STATUS_CHOICES,
        default=STATUS_NAO_LIBERADO
    )

    class Meta:
        ordering = ('-criado_em',)
        verbose_name = 'Protocolo padrão de dieta especial'
        verbose_name_plural = 'Protocolos padrões de dieta especial'

    def __str__(self):
        return str(self.nome_protocolo)


class SubstituicaoAlimentoProtocoloPadrao(models.Model):
    TIPO_CHOICES = [
        ('I', 'Isento'),
        ('S', 'Substituir')
    ]
    protocolo_padrao = models.ForeignKey(
        ProtocoloPadraoDietaEspecial,
        on_delete=models.CASCADE,
        related_name='substituicoes'
    )
    alimento = models.ForeignKey(
        Alimento,
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES, blank=True)
    substitutos = models.ManyToManyField(
        'produto.Produto',
        related_name='substitutos_protocolo_padrao',
        blank=True,
        help_text='produtos substitutos'
    )
    alimentos_substitutos = models.ManyToManyField(
        Alimento,
        related_name='alimentos_substitutos_protocolo_padrao',
        blank=True
    )

    class Meta:
        verbose_name = 'Substituição de alimento para protocolo padrão de dieta'
        verbose_name_plural = 'Substituições de alimentos para protocolos padrões de dietas'

    def __str__(self):
        return f'substituição protocolo padrão: {self.protocolo_padrao}, tipo: {self.tipo}.'
