import uuid
from datetime import datetime

from django.core.validators import MinLengthValidator
from django.db import models
from django_prometheus.models import ExportModelOperationsMixin


class LogSolicitacoesUsuario(
    ExportModelOperationsMixin("log_solicitacoes"), models.Model
):
    """Eventos de dados importantes para acompanhamento.

    Ex.: Fulano X  executou a atividade Y no objeto W no dia DDDDMMAA
    """

    (  # COMUNS AOS DOIS FLUXOS (PARTINDO DA ESCOLA E DA DRE)
        INICIO_FLUXO,
        CODAE_AUTORIZOU,
        TERCEIRIZADA_TOMOU_CIENCIA,
        TERCEIRIZADA_RECUSOU,
        CODAE_NEGOU,
        # ESPECIFICA DO PARTINDO DA DRE
        CODAE_PEDIU_REVISAO,
        DRE_REVISOU,
        # ESPECIFICA DO PARTINDO DA ESCOLA
        DRE_VALIDOU,
        DRE_PEDIU_REVISAO,
        DRE_NAO_VALIDOU,
        ESCOLA_REVISOU,
        CODAE_QUESTIONOU,
        TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
        # "BURLADO DO FLUXO", PODE SER CHAMADO A QUALQUER MOMENTO COM AS DEVIDAS RESTRIÇÕES
        ESCOLA_CANCELOU,
        CODAE_NEGOU_CANCELAMENTO,
        DRE_CANCELOU,
        # ESPECIFICA DIETA ESPECIAL
        INICIO_FLUXO_INATIVACAO,
        CODAE_AUTORIZOU_INATIVACAO,
        CODAE_NEGOU_INATIVACAO,
        TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
        TERMINADA_AUTOMATICAMENTE_SISTEMA,
        # ESPECIFICA HOMOLOGACAO DE PRODUTO
        CODAE_PENDENTE_HOMOLOGACAO,
        CODAE_HOMOLOGADO,
        CODAE_NAO_HOMOLOGADO,
        CODAE_PEDIU_ANALISE_SENSORIAL,
        CODAE_CANCELOU_ANALISE_SENSORIAL,
        TERCEIRIZADA_CANCELOU,
        CODAE_SUSPENDEU,
        ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
        CODAE_PEDIU_ANALISE_RECLAMACAO,
        CODAE_AUTORIZOU_RECLAMACAO,
        INATIVA,
        TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO,
        # ESPECIFICA RECLAMAÇÃO DE PRODUTO
        TERCEIRIZADA_RESPONDEU_RECLAMACAO,
        TERCEIRIZADA_RESPONDEU_ANALISE_SENSORIAL,
        CODAE_QUESTIONOU_UE,
        UE_RESPONDEU_RECLAMACAO,
        NUTRISUPERVISOR_RESPONDEU_RECLAMACAO,
        CODAE_QUESTIONOU_NUTRISUPERVISOR,
        CODAE_RECUSOU_RECLAMACAO,
        CODAE_QUESTIONOU_TERCEIRIZADA,
        CODAE_RESPONDEU_RECLAMACAO,
        # ESPECIFICA SOLICITAÇÂO CADASTRO PRODUTO
        TERCEIRIZADA_ATENDE_SOLICITACAO_CADASTRO,
        # ESPECIFICA SOLICITAÇÃO DE REMESSA
        INICIO_FLUXO_SOLICITACAO,
        DILOG_ENVIA_SOLICITACAO,
        DISTRIBUIDOR_CONFIRMA_SOLICITACAO,
        DISTRIBUIDOR_SOLICITA_ALTERACAO_SOLICITACAO,
        PAPA_CANCELA_SOLICITACAO,
        PAPA_AGUARDA_CONFIRMACAO_CANCELAMENTO_SOLICITACAO,
        DISTRIBUIDOR_CONFIRMA_CANCELAMENTO,
        # ESPECIFICA SOLICITAÇÃO DE ALTERACAO
        DILOG_ACEITA_ALTERACAO,
        DILOG_NEGA_ALTERACAO,
        CANCELADO_ALUNO_MUDOU_ESCOLA,
        CANCELADO_ALUNO_NAO_PERTENCE_REDE,
        # MEDICAO INICIAL
        MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
        MEDICAO_ENVIADA_PELA_UE,
        # CRONOGRAMA
        CRONOGRAMA_CRIADO,
        CRONOGRAMA_ENVIADO_AO_FORNECEDOR,
        CRONOGRAMA_ASSINADO_PELO_FORNECEDOR,
        FORNECEDOR_SOLICITA_ALTERACAO_CRONOGRAMA,
        SUSPENSO_EM_ALGUNS_EDITAIS,
        ATIVO_EM_ALGUNS_EDITAIS,
        CRONOGRAMA_ASSINADO_PELO_USUARIO_CRONOGRAMA,
        CODAE_ATUALIZOU_PROTOCOLO,
        # MEDICAO INICIAL - CONTINUACAO
        MEDICAO_CORRECAO_SOLICITADA,
        MEDICAO_CORRIGIDA_PELA_UE,
        MEDICAO_APROVADA_PELA_DRE,
        MEDICAO_APROVADA_PELA_CODAE,
        CRONOGRAMA_ASSINADO_PELO_DILOG_ABASTECIMENTO,
        CRONOGRAMA_ASSINADO_PELA_CODAE,
        VINCULO_DO_EDITAL_AO_PRODUTO,
        CRONOGRAMA_CIENTE_SOLICITACAO_ALTERACAO,
        FORNECEDOR_CIENTE_SOLICITACAO_ALTERACAO,
        APROVADO_DILOG_ABASTECIMENTO_SOLICITACAO_ALTERACAO,
        REPROVADO_DILOG_ABASTECIMENTO_SOLICITACAO_ALTERACAO,
        APROVADO_DILOG_SOLICITACAO_ALTERACAO,
        REPROVADO_DILOG_SOLICITACAO_ALTERACAO,
        CODAE_CANCELOU_SOLICITACAO_CORRECAO,
        TERCEIRIZADA_CANCELOU_SOLICITACAO_CORRECAO,
        SOLICITACAO_ALTERACAO_CRONOGRAMA_EM_ANALISE,
        NOTIFICACAO_CRIADA,
        NOTIFICACAO_ENVIADA_FISCAL,
        MEDICAO_CORRECAO_SOLICITADA_CODAE,
        MEDICAO_CORRIGIDA_PARA_CODAE,
        NOTIFICACAO_SOLICITADA_ALTERACAO,
        NOTIFICACAO_ASSINADA_FISCAL,
        CODAE_ALTERA_CRONOGRAMA,
        ALTERACAO_CRONOGRAMA_ENVIADA_AO_FORNECEDOR,
        LAYOUT_ENVIADO_PARA_ANALISE,
        LAYOUT_SOLICITADO_CORRECAO,
        LAYOUT_APROVADO,
        LAYOUT_CORRECAO_REALIZADA,
        LAYOUT_ATUALIZADO,
        DOCUMENTO_ENVIADO_PARA_ANALISE,
        DOCUMENTO_ENVIADO_PARA_CORRECAO,
        DOCUMENTO_APROVADO,
        DOCUMENTO_CORRECAO_REALIZADA,
        FICHA_TECNICA_ENVIADA_PARA_ANALISE,
        FICHA_TECNICA_APROVADA,
        FICHA_TECNICA_ENVIADA_PARA_CORRECAO,
        RELATORIO_ENVIADO_PARA_CODAE,
        MEDICAO_SEM_LANCAMENTOS,
        FICHA_RECEBIMENTO_ASSINADA,
    ) = range(103)

    STATUS_POSSIVEIS = (
        (INICIO_FLUXO, "Solicitação Realizada"),
        (CODAE_AUTORIZOU, "CODAE autorizou"),
        (TERCEIRIZADA_TOMOU_CIENCIA, "Terceirizada tomou ciência"),
        (TERCEIRIZADA_RECUSOU, "Terceirizada recusou"),
        (CODAE_NEGOU, "CODAE negou"),
        (CODAE_PEDIU_REVISAO, "CODAE pediu revisão"),
        (DRE_REVISOU, "DRE revisou"),
        (DRE_VALIDOU, "DRE validou"),
        (DRE_PEDIU_REVISAO, "DRE pediu revisão"),
        (DRE_NAO_VALIDOU, "DRE não validou"),
        (ESCOLA_REVISOU, "Escola revisou"),
        (ESCOLA_CANCELOU, "Escola cancelou"),
        (CODAE_NEGOU_CANCELAMENTO, "CODAE negou cancelamento"),
        (DRE_CANCELOU, "DRE cancelou"),
        (CODAE_QUESTIONOU, "Questionamento pela CODAE"),
        (
            TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            "Terceirizada respondeu questionamento",
        ),  # noqa
        (INICIO_FLUXO_INATIVACAO, "Escola solicitou cancelamento"),
        (CODAE_AUTORIZOU_INATIVACAO, "CODAE autorizou cancelamento"),
        (CODAE_NEGOU_INATIVACAO, "CODAE negou cancelamento"),
        (
            TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
            "Terceirizada tomou ciência do cancelamento",
        ),  # noqa
        (
            TERMINADA_AUTOMATICAMENTE_SISTEMA,
            "Cancelada por atingir data de término",
        ),  # noqa
        (CODAE_PENDENTE_HOMOLOGACAO, "Pendente homologação da CODAE"),
        (CODAE_HOMOLOGADO, "CODAE homologou"),
        (CODAE_NAO_HOMOLOGADO, "CODAE não homologou"),
        (CODAE_PEDIU_ANALISE_SENSORIAL, "CODAE pediu análise sensorial"),
        (CODAE_CANCELOU_ANALISE_SENSORIAL, "CODAE cancelou análise sensorial"),
        (TERCEIRIZADA_CANCELOU, "Terceirizada cancelou homologação"),
        (INATIVA, "Homologação inativa"),
        (
            TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO,
            "Terceirizada cancelou solicitação de homologação de produto",
        ),
        (CODAE_SUSPENDEU, "CODAE suspendeu o produto"),
        (
            ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
            "Escola/Nutricionista reclamou do produto",
        ),  # noqa
        (CODAE_PEDIU_ANALISE_RECLAMACAO, "CODAE pediu análise da reclamação"),
        (CODAE_AUTORIZOU_RECLAMACAO, "CODAE autorizou reclamação"),
        (CODAE_RECUSOU_RECLAMACAO, "CODAE recusou reclamação"),
        (
            CODAE_QUESTIONOU_TERCEIRIZADA,
            "CODAE questionou terceirizada sobre reclamação",
        ),  # noqa
        (CODAE_QUESTIONOU_UE, "CODAE questionou U.E. sobre reclamação"),  # noqa
        (CODAE_RESPONDEU_RECLAMACAO, "CODAE respondeu ao reclamante da reclamação"),
        (
            CODAE_QUESTIONOU_NUTRISUPERVISOR,
            "CODAE questionou nutrisupervisor sobre reclamação",
        ),
        (TERCEIRIZADA_RESPONDEU_RECLAMACAO, "Terceirizada respondeu a reclamação"),
        (UE_RESPONDEU_RECLAMACAO, "U.E. respondeu a reclamação"),
        (
            NUTRISUPERVISOR_RESPONDEU_RECLAMACAO,
            "Nutrisupervisor respondeu a reclamação",
        ),
        (
            TERCEIRIZADA_RESPONDEU_ANALISE_SENSORIAL,
            "Terceirizada respondeu a análise",
        ),  # noqa
        (INICIO_FLUXO_SOLICITACAO, "Papa enviou a requisição"),
        (DILOG_ENVIA_SOLICITACAO, "Dilog Enviou a requisição"),
        (
            DISTRIBUIDOR_CONFIRMA_SOLICITACAO,
            "Distribuidor confirmou requisição",
        ),  # noqa
        (
            DISTRIBUIDOR_SOLICITA_ALTERACAO_SOLICITACAO,
            "Distribuidor pede alteração da requisição",
        ),  # noqa
        (PAPA_CANCELA_SOLICITACAO, "Papa cancelou a requisição"),
        (
            PAPA_AGUARDA_CONFIRMACAO_CANCELAMENTO_SOLICITACAO,
            "Papa aguarda confirmação do cancelamento da solicitação",
        ),
        (
            DISTRIBUIDOR_CONFIRMA_CANCELAMENTO,
            "Distribuidor confirmou cancelamento e Papa cancelou a requisição",
        ),
        (DILOG_ACEITA_ALTERACAO, "Dilog Aceita Alteração"),
        (DILOG_NEGA_ALTERACAO, "Dilog Nega Alteração"),
        (
            CANCELADO_ALUNO_MUDOU_ESCOLA,
            "Cancelamento por alteração de unidade educacional",
        ),
        (
            CANCELADO_ALUNO_NAO_PERTENCE_REDE,
            "Cancelamento para aluno não matriculado na rede municipal",
        ),
        (
            MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
            "Em aberto para preenchimento pela UE",
        ),
        (MEDICAO_ENVIADA_PELA_UE, "Enviado pela UE"),
        (MEDICAO_CORRECAO_SOLICITADA, "Correção solicitada"),
        (MEDICAO_CORRIGIDA_PELA_UE, "Corrigido para DRE"),
        (MEDICAO_APROVADA_PELA_DRE, "Aprovado pela DRE"),
        (MEDICAO_APROVADA_PELA_CODAE, "Aprovado pela CODAE"),
        (CRONOGRAMA_CRIADO, "Cronograma Criado"),
        (CRONOGRAMA_ENVIADO_AO_FORNECEDOR, "Assinado e Enviado ao Fornecedor"),
        (CRONOGRAMA_ASSINADO_PELO_FORNECEDOR, "Assinado Fornecedor"),
        (FORNECEDOR_SOLICITA_ALTERACAO_CRONOGRAMA, "Solicitada Alteração"),
        (SUSPENSO_EM_ALGUNS_EDITAIS, "Suspenso em alguns editais"),
        (ATIVO_EM_ALGUNS_EDITAIS, "Ativo em alguns editais"),
        (CRONOGRAMA_ASSINADO_PELO_USUARIO_CRONOGRAMA, "Assinado Cronograma"),
        (CODAE_ATUALIZOU_PROTOCOLO, "CODAE Atualizou o protocolo"),
        (CRONOGRAMA_ASSINADO_PELO_DILOG_ABASTECIMENTO, "Assinado Abastecimento"),
        (CRONOGRAMA_ASSINADO_PELA_CODAE, "Assinado CODAE"),
        (VINCULO_DO_EDITAL_AO_PRODUTO, "Vínculo do Edital ao Produto"),
        (CRONOGRAMA_CIENTE_SOLICITACAO_ALTERACAO, "Cronograma Ciente"),
        (FORNECEDOR_CIENTE_SOLICITACAO_ALTERACAO, "Fornecedor Ciente"),
        (
            APROVADO_DILOG_ABASTECIMENTO_SOLICITACAO_ALTERACAO,
            "Aprovado Abastecimento",
        ),
        (
            REPROVADO_DILOG_ABASTECIMENTO_SOLICITACAO_ALTERACAO,
            "Reprovado Abastecimento",
        ),
        (APROVADO_DILOG_SOLICITACAO_ALTERACAO, "Aprovado DILOG"),
        (REPROVADO_DILOG_SOLICITACAO_ALTERACAO, "Reprovado DILOG"),
        (CODAE_CANCELOU_SOLICITACAO_CORRECAO, "CODAE cancelou solicitação de correção"),
        (
            TERCEIRIZADA_CANCELOU_SOLICITACAO_CORRECAO,
            "Terceirizada cancelou solicitação de correção",
        ),
        (SOLICITACAO_ALTERACAO_CRONOGRAMA_EM_ANALISE, "Em Análise"),
        (NOTIFICACAO_CRIADA, "Notificação criada"),
        (NOTIFICACAO_ENVIADA_FISCAL, "Notificação enviada para o fiscal"),
        (MEDICAO_CORRECAO_SOLICITADA_CODAE, "Correção solicitada pela CODAE"),
        (MEDICAO_CORRIGIDA_PARA_CODAE, "Corrigido para CODAE"),
        (CODAE_ALTERA_CRONOGRAMA, "Alteração CODAE"),
        (ALTERACAO_CRONOGRAMA_ENVIADA_AO_FORNECEDOR, "Alteração enviada ao fornecedor"),
        (LAYOUT_ENVIADO_PARA_ANALISE, "Layout enviado para análise"),
        (LAYOUT_SOLICITADO_CORRECAO, "Layout solicitado correção"),
        (LAYOUT_APROVADO, "Layout aprovado"),
        (LAYOUT_CORRECAO_REALIZADA, "Layout correção realizada"),
        (LAYOUT_ATUALIZADO, "Layout atualizado"),
        (DOCUMENTO_ENVIADO_PARA_ANALISE, "Documento enviado para análise"),
        (DOCUMENTO_ENVIADO_PARA_CORRECAO, "Documento enviado para correção"),
        (DOCUMENTO_APROVADO, "Documento aprovado"),
        (DOCUMENTO_CORRECAO_REALIZADA, "Documento correção realizada"),
        (FICHA_TECNICA_ENVIADA_PARA_ANALISE, "Ficha Técnica enviada para análise"),
        (FICHA_TECNICA_APROVADA, "Ficha Técnica aprovada"),
        (FICHA_TECNICA_ENVIADA_PARA_CORRECAO, "Ficha Técnica enviada para correção"),
        (RELATORIO_ENVIADO_PARA_CODAE, "Relatório enviado para CODAE"),
        (MEDICAO_SEM_LANCAMENTOS, "Medição sem lançamentos"),
        (FICHA_RECEBIMENTO_ASSINADA, "Ficha de Recebimento assinada"),
    )
    (  # DA ESCOLA
        SOLICITACAO_KIT_LANCHE_AVULSA,
        ALTERACAO_DE_CARDAPIO,
        SUSPENSAO_DE_CARDAPIO,
        INVERSAO_DE_CARDAPIO,
        INCLUSAO_ALIMENTACAO_NORMAL,
        INCLUSAO_ALIMENTACAO_CEI,
        SUSPENSAO_ALIMENTACAO_CEI,
        INCLUSAO_ALIMENTACAO_CONTINUA,
        DIETA_ESPECIAL,
        # DA DRE
        SOLICITACAO_KIT_LANCHE_UNIFICADA,
        # DA TERCEIRIZADA
        HOMOLOGACAO_PRODUTO,
        # PRODUTOS
        RECLAMACAO_PRODUTO,
        # DA LOGISTICA ABASTECIMENTO
        SOLICITACAO_REMESSA_PAPA,
        SOLICITACAO_DE_ALTERACAO_REQUISICAO,
        ABASTECIMENTO_GUIA_DE_REMESSA,
        MEDICAO_INICIAL,
        INCLUSAO_ALIMENTACAO_CEMEI,
        SOLICITACAO_KIT_LANCHE_CEMEI,
        CRONOGRAMA,
        SOLICITACAO_DE_ALTERACAO_CRONOGRAMA,
        NOTIFICACAO_OCORRENCIA_GUIA,
        LAYOUT_DE_EMBALAGEM,
        DOCUMENTO_DE_RECEBIMENTO,
        FICHA_TECNICA_DO_PRODUTO,
        FORMULARIO_SUPERVISAO,
    ) = range(25)

    TIPOS_SOLICITACOES = (
        (SOLICITACAO_KIT_LANCHE_AVULSA, "Solicitação de kit lanche avulsa"),
        (ALTERACAO_DE_CARDAPIO, "Alteração do tipo de alimentação"),
        (SUSPENSAO_DE_CARDAPIO, "Suspensão de cardápio"),
        (INVERSAO_DE_CARDAPIO, "Inversão de cardápio"),
        (INCLUSAO_ALIMENTACAO_NORMAL, "Inclusão de alimentação normal"),
        (INCLUSAO_ALIMENTACAO_CEI, "Inclusão de alimentação da CEI"),
        (SUSPENSAO_ALIMENTACAO_CEI, "Suspensão de alimentação da CEI"),
        (INCLUSAO_ALIMENTACAO_CONTINUA, "Inclusão de alimentação contínua"),
        (DIETA_ESPECIAL, "Dieta Especial"),
        (SOLICITACAO_KIT_LANCHE_UNIFICADA, "Solicitação de kit lanche unificada"),
        (HOMOLOGACAO_PRODUTO, "Homologação de Produto"),
        (RECLAMACAO_PRODUTO, "Reclamação de Produto"),
        (SOLICITACAO_REMESSA_PAPA, "Solicitação de remessa"),
        (SOLICITACAO_DE_ALTERACAO_REQUISICAO, "Solicitação de Ateração de requisição"),
        (ABASTECIMENTO_GUIA_DE_REMESSA, "Abastecimento de guia de remessa"),
        (MEDICAO_INICIAL, "Solicitação de medição inicial"),
        (INCLUSAO_ALIMENTACAO_CEMEI, "Inclusão de Alimentação CEMEI"),
        (SOLICITACAO_KIT_LANCHE_CEMEI, "Solicitação de kit lanche CEMEI"),
        (CRONOGRAMA, "Cronograma"),
        (SOLICITACAO_DE_ALTERACAO_CRONOGRAMA, "Solicitação de alteração do cronograma"),
        (NOTIFICACAO_OCORRENCIA_GUIA, "Notificação de guia com ocorrência"),
        (LAYOUT_DE_EMBALAGEM, "Layout de embalagem"),
        (DOCUMENTO_DE_RECEBIMENTO, "Documento de recebimento"),
        (FICHA_TECNICA_DO_PRODUTO, "Ficha técnica do produto"),
        (FORMULARIO_SUPERVISAO, "Formulário Supervisão"),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    criado_em = models.DateTimeField("Criado em", editable=False, auto_now_add=True)
    descricao = models.TextField("Descricao", blank=True)
    justificativa = models.TextField("Justificativa", blank=True)
    resposta_sim_nao = models.BooleanField("Resposta - Sim ou Não", default=False)
    status_evento = models.PositiveSmallIntegerField(choices=STATUS_POSSIVEIS)
    solicitacao_tipo = models.PositiveSmallIntegerField(choices=TIPOS_SOLICITACOES)
    uuid_original = models.UUIDField()
    usuario = models.ForeignKey("perfil.Usuario", on_delete=models.DO_NOTHING)

    class Meta:
        ordering = ("-criado_em",)

    @property
    def status_evento_explicacao(self):
        return self.get_status_evento_display()

    @property
    def get_anexos(self):
        return AnexoLogSolicitacoesUsuario.objects.filter(log=self)

    def __str__(self):
        data = datetime.strftime(self.criado_em, "%Y-%m-%d %H:%M:%S")
        return (
            f"{self.usuario} executou {self.get_status_evento_display()} "
            f"em {self.get_solicitacao_tipo_display()} no dia {data}"
        )


class AnexoLogSolicitacoesUsuario(
    ExportModelOperationsMixin("log_solicitacoes_anexo"), models.Model
):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    log = models.ForeignKey(
        LogSolicitacoesUsuario, related_name="anexos", on_delete=models.DO_NOTHING
    )
    nome = models.CharField(max_length=255, blank=True)
    arquivo = models.FileField()

    def __str__(self):
        return f"Anexo {self.uuid} - {self.nome}"


class Endereco(ExportModelOperationsMixin("endereco"), models.Model):
    logradouro = models.CharField(max_length=255, validators=[MinLengthValidator(5)])
    numero = models.IntegerField(null=True)
    complemento = models.CharField(max_length=50, blank=True)
    bairro = models.CharField(max_length=50)
    cep = models.IntegerField()


class Contato(ExportModelOperationsMixin("contato"), models.Model):
    nome = models.CharField("Nome", max_length=160, blank=True)
    telefone = models.CharField(
        max_length=13, validators=[MinLengthValidator(8)], blank=True
    )
    telefone2 = models.CharField(
        max_length=10, validators=[MinLengthValidator(8)], blank=True
    )
    celular = models.CharField(
        max_length=11, validators=[MinLengthValidator(8)], blank=True
    )
    email = models.EmailField(blank=True)
    eh_nutricionista = models.BooleanField("É nutricionista?", default=False)
    crn_numero = models.CharField("Nutricionista crn", max_length=160, blank=True)

    def __str__(self):
        if self.nome and self.telefone:
            return f"{self.nome}, {self.telefone}, {self.email}"
        elif self.telefone:
            return f"{self.telefone}, {self.email}"
        elif self.telefone2:
            return f"{self.telefone2}, {self.email}"
        else:
            return f"{self.email}"


class TemplateMensagem(ExportModelOperationsMixin("template_mensagem"), models.Model):
    """Tem um texto base e troca por campos do objeto que entra como parâmetro.

    Ex:
    Olá @nome, a Alteração de cardápio #@identificador solicitada por @requerinte está em situação @status.
    """

    ALTERACAO_CARDAPIO = 0
    INCLUSAO_ALIMENTACAO = 1
    INCLUSAO_ALIMENTACAO_CONTINUA = 2
    SUSPENSAO_ALIMENTACAO = 3
    SOLICITACAO_KIT_LANCHE_AVULSA = 4
    SOLICITACAO_KIT_LANCHE_UNIFICADA = 5
    INVERSAO_CARDAPIO = 6
    DIETA_ESPECIAL = 7
    HOMOLOGACAO_PRODUTO = 8

    CHOICES = (
        (ALTERACAO_CARDAPIO, "Alteração do tipo de Alimentação"),
        (INCLUSAO_ALIMENTACAO, "Inclusão de alimentação"),
        (INCLUSAO_ALIMENTACAO_CONTINUA, "Inclusão de alimentação contínua"),
        (SUSPENSAO_ALIMENTACAO, "Suspensão de alimentação"),
        (SOLICITACAO_KIT_LANCHE_AVULSA, "Solicitação de kit lanche avulsa"),
        (SOLICITACAO_KIT_LANCHE_UNIFICADA, "Solicitação de kit lanche unificada"),
        (INVERSAO_CARDAPIO, "Inversão de cardápio"),
        (DIETA_ESPECIAL, "Dieta Especial"),
        (HOMOLOGACAO_PRODUTO, "Homologação de Produto"),
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    tipo = models.PositiveSmallIntegerField(choices=CHOICES, unique=True)
    assunto = models.CharField("Assunto", max_length=256, blank=True)
    template_html = models.TextField("Template", blank=True)

    def __str__(self):
        return f"{self.get_tipo_display()}"

    class Meta:
        verbose_name = "Template de mensagem"
        verbose_name_plural = "Template de mensagem"


class CategoriaPerguntaFrequente(ExportModelOperationsMixin("cat_faq"), models.Model):
    nome = models.CharField("Nome", blank=True, max_length=100)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return self.nome


class PerguntaFrequente(ExportModelOperationsMixin("faq"), models.Model):
    categoria = models.ForeignKey(
        "CategoriaPerguntaFrequente", on_delete=models.PROTECT
    )  # noqa
    pergunta = models.TextField("Pergunta")
    resposta = models.TextField("Resposta")
    criado_em = models.DateTimeField(
        "Criado em", editable=False, auto_now_add=True
    )  # noqa
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return self.pergunta


class NotificacaoException(Exception):
    pass


class Notificacao(models.Model):
    # Tipos de Notificação
    TIPO_NOTIFICACAO_ALERTA = "ALERTA"
    TIPO_NOTIFICACAO_AVISO = "AVISO"
    TIPO_NOTIFICACAO_PENDENCIA = "PENDENCIA"

    TIPO_NOTIFICACAO_NOMES = {
        TIPO_NOTIFICACAO_ALERTA: "Alerta",
        TIPO_NOTIFICACAO_AVISO: "Aviso",
        TIPO_NOTIFICACAO_PENDENCIA: "Pendência",
    }

    TIPO_NOTIFICACAO_CHOICES = (
        (TIPO_NOTIFICACAO_ALERTA, TIPO_NOTIFICACAO_NOMES[TIPO_NOTIFICACAO_ALERTA]),
        (TIPO_NOTIFICACAO_AVISO, TIPO_NOTIFICACAO_NOMES[TIPO_NOTIFICACAO_AVISO]),
        (
            TIPO_NOTIFICACAO_PENDENCIA,
            TIPO_NOTIFICACAO_NOMES[TIPO_NOTIFICACAO_PENDENCIA],
        ),
    )

    # Categorias de Notificação
    CATEGORIA_NOTIFICACAO_REQUISICAO_DE_ENTREGA = "REQUISICAO_DE_ENTREGA"
    CATEGORIA_NOTIFICACAO_ALTERACAO_REQUISICAO_ENTREGA = "ALTERACAO_REQUISICAO_ENTREGA"
    CATEGORIA_NOTIFICACAO_GUIA_DE_REMESSA = "GUIA_DE_REMESSA"
    CATEGORIA_NOTIFICACAO_CRONOGRAMA = "CRONOGRAMA"
    CATEGORIA_NOTIFICACAO_SOLICITACAO_ALTERACAO_CRONOGRAMA = (
        "SOLICITACAO_ALTERACAO_CRONOGRAMA"
    )
    CATEGORIA_NOTIFICACAO_ALTERACAO_CRONOGRAMA = "ALTERACAO_CRONOGRAMA"
    CATEGORIA_NOTIFICACAO_LAYOUT_DE_EMBALAGENS = "LAYOUT_DE_EMBALAGENS"
    CATEGORIA_NOTIFICACAO_DOCUMENTOS_DE_RECEBIMENTO = "DOCUMENTOS_DE_RECEBIMENTO"

    CATEGORIA_NOTIFICACAO_NOMES = {
        CATEGORIA_NOTIFICACAO_REQUISICAO_DE_ENTREGA: "Requisição de entrega",
        CATEGORIA_NOTIFICACAO_ALTERACAO_REQUISICAO_ENTREGA: "Alteração de requisição de entrega",
        CATEGORIA_NOTIFICACAO_GUIA_DE_REMESSA: "Guia de Remessa",
        CATEGORIA_NOTIFICACAO_CRONOGRAMA: "Assinatura do Cronograma",
        CATEGORIA_NOTIFICACAO_SOLICITACAO_ALTERACAO_CRONOGRAMA: "Solicitação de Alteração do Cronograma",
        CATEGORIA_NOTIFICACAO_ALTERACAO_CRONOGRAMA: "Alteração do Cronograma",
        CATEGORIA_NOTIFICACAO_LAYOUT_DE_EMBALAGENS: "Layout de Embalagens",
        CATEGORIA_NOTIFICACAO_DOCUMENTOS_DE_RECEBIMENTO: "Documentos de Recebimento",
    }

    CATEGORIA_NOTIFICACAO_CHOICES = (
        (
            CATEGORIA_NOTIFICACAO_REQUISICAO_DE_ENTREGA,
            CATEGORIA_NOTIFICACAO_NOMES[CATEGORIA_NOTIFICACAO_REQUISICAO_DE_ENTREGA],
        ),
        (
            CATEGORIA_NOTIFICACAO_ALTERACAO_REQUISICAO_ENTREGA,
            CATEGORIA_NOTIFICACAO_NOMES[
                CATEGORIA_NOTIFICACAO_ALTERACAO_REQUISICAO_ENTREGA
            ],
        ),
        (
            CATEGORIA_NOTIFICACAO_GUIA_DE_REMESSA,
            CATEGORIA_NOTIFICACAO_NOMES[CATEGORIA_NOTIFICACAO_GUIA_DE_REMESSA],
        ),
        (
            CATEGORIA_NOTIFICACAO_CRONOGRAMA,
            CATEGORIA_NOTIFICACAO_NOMES[CATEGORIA_NOTIFICACAO_CRONOGRAMA],
        ),
        (
            CATEGORIA_NOTIFICACAO_SOLICITACAO_ALTERACAO_CRONOGRAMA,
            CATEGORIA_NOTIFICACAO_NOMES[
                CATEGORIA_NOTIFICACAO_SOLICITACAO_ALTERACAO_CRONOGRAMA
            ],
        ),
        (
            CATEGORIA_NOTIFICACAO_ALTERACAO_CRONOGRAMA,
            CATEGORIA_NOTIFICACAO_NOMES[CATEGORIA_NOTIFICACAO_ALTERACAO_CRONOGRAMA],
        ),
        (
            CATEGORIA_NOTIFICACAO_LAYOUT_DE_EMBALAGENS,
            CATEGORIA_NOTIFICACAO_NOMES[CATEGORIA_NOTIFICACAO_LAYOUT_DE_EMBALAGENS],
        ),
        (
            CATEGORIA_NOTIFICACAO_DOCUMENTOS_DE_RECEBIMENTO,
            CATEGORIA_NOTIFICACAO_NOMES[
                CATEGORIA_NOTIFICACAO_DOCUMENTOS_DE_RECEBIMENTO
            ],
        ),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    tipo = models.CharField(
        "Tipo",
        max_length=15,
        choices=TIPO_NOTIFICACAO_CHOICES,
        default=TIPO_NOTIFICACAO_AVISO,
    )

    categoria = models.CharField(
        "Categoria",
        max_length=50,
        choices=CATEGORIA_NOTIFICACAO_CHOICES,
    )

    titulo = models.CharField("Título", max_length=200, default="", blank=True)

    descricao = models.TextField("Descrição", max_length=5000, default="", blank=True)

    hora = models.TimeField("Hora", editable=False, auto_now_add=True)

    lido = models.BooleanField("Foi Lido?", default=False)

    resolvido = models.BooleanField("Foi resolvido?", default=False)

    usuario = models.ForeignKey(
        "perfil.Usuario", on_delete=models.CASCADE, default="", null=True, blank=True
    )

    criado_em = models.DateTimeField("Criado em", editable=False, auto_now_add=True)

    link = models.CharField("Link", max_length=100, default="", blank=True)

    requisicao = models.ForeignKey(
        "logistica.SolicitacaoRemessa",
        on_delete=models.CASCADE,
        related_name="notificacoes_da_requisicao",
        blank=True,
        null=True,
    )

    solicitacao_alteracao = models.ForeignKey(
        "logistica.SolicitacaoDeAlteracaoRequisicao",
        on_delete=models.CASCADE,
        related_name="notificacoes_da_solicitacao_alteracao",
        blank=True,
        null=True,
    )

    guia = models.ForeignKey(
        "logistica.Guia",
        on_delete=models.CASCADE,
        related_name="notificacoes_da_guia",
        blank=True,
        null=True,
    )

    cronograma = models.ForeignKey(
        "pre_recebimento.Cronograma",
        on_delete=models.CASCADE,
        related_name="notificacoes_do_cronograma",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"

    def __str__(self):
        return self.titulo

    @classmethod
    def notificar(  # noqa: C901
        cls,
        tipo,
        categoria,
        titulo,
        descricao,
        usuario,
        link,
        requisicao=None,
        solicitacao_alteracao=None,
        guia=None,
        renotificar=True,
        cronograma=None,
    ):
        if tipo not in cls.TIPO_NOTIFICACAO_NOMES.keys():
            raise NotificacaoException(f"Tipo {tipo} não é um tipo válido.")

        if categoria not in cls.CATEGORIA_NOTIFICACAO_NOMES.keys():
            raise NotificacaoException(
                f"Categoria {categoria} não é uma categoria válida."
            )

        if not titulo:
            raise NotificacaoException("O título não pode ser vazio.")

        if not usuario:
            raise NotificacaoException("É necessário definir o usuário destinatário.")

        if not renotificar:
            notificacao_existente = cls.objects.filter(
                tipo=tipo,
                categoria=categoria,
                requisicao=requisicao,
                guia=guia,
                titulo=titulo,
                usuario=usuario,
            )

        if renotificar or not notificacao_existente:
            cls.objects.create(
                tipo=tipo,
                categoria=categoria,
                titulo=titulo,
                descricao=descricao,
                usuario=usuario,
                link=link,
                requisicao=requisicao,
                solicitacao_alteracao=solicitacao_alteracao,
                guia=guia,
            )

    @classmethod
    def resolver_pendencia(
        cls, titulo, requisicao=None, solicitacao_alteracao=None, guia=None
    ):
        if not titulo:
            raise NotificacaoException("O título não pode ser vazio.")
        if not requisicao and not solicitacao_alteracao and not guia:
            raise NotificacaoException(
                "É preciso informar uma requisição, solicitação de alteração ou guia para "
                "resolver uma pendência."
            )

        pendencias = cls.objects.filter(
            tipo=Notificacao.TIPO_NOTIFICACAO_PENDENCIA,
            titulo=titulo,
            requisicao=requisicao,
            solicitacao_alteracao=solicitacao_alteracao,
            guia=guia,
            resolvido=False,
        )
        pendencias.update(resolvido=True, lido=True)


class CentralDeDownload(models.Model):
    # Status Choice
    STATUS_EM_PROCESSAMENTO = "EM_PROCESSAMENTO"
    STATUS_CONCLUIDO = "CONCLUIDO"
    STATUS_ERRO = "ERRO"

    STATUS_NOMES = {
        STATUS_EM_PROCESSAMENTO: "Em processamento",
        STATUS_CONCLUIDO: "Concluído",
        STATUS_ERRO: "Erro",
    }

    STATUS_CHOICES = (
        (STATUS_EM_PROCESSAMENTO, STATUS_NOMES[STATUS_EM_PROCESSAMENTO]),
        (STATUS_CONCLUIDO, STATUS_NOMES[STATUS_CONCLUIDO]),
        (STATUS_ERRO, STATUS_NOMES[STATUS_ERRO]),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    identificador = models.CharField("Nome do arquivo", max_length=200, default="")
    arquivo = models.FileField(
        blank=True, verbose_name="Arquivo", upload_to="cental_downloads"
    )
    status = models.CharField(
        "status", max_length=20, choices=STATUS_CHOICES, default=STATUS_EM_PROCESSAMENTO
    )
    msg_erro = models.CharField("Mensagem erro", max_length=300, blank=True)
    visto = models.BooleanField("Foi visto?", default=False)
    usuario = models.ForeignKey(
        "perfil.Usuario", on_delete=models.CASCADE, default="", null=True, blank=True
    )
    criado_em = models.DateTimeField("Criado em", editable=False, auto_now_add=True)

    class Meta:
        verbose_name = "Central de Download"
        verbose_name_plural = "Central de Downloads"

    def __str__(self):
        return self.identificador

    def delete(self, using=None, keep_parents=False):
        if self.arquivo:
            self.arquivo.storage.delete(self.arquivo.name)
        super().delete()


class SolicitacaoAberta(models.Model):
    uuid_solicitacao = models.CharField(max_length=50)
    usuario = models.ForeignKey("perfil.Usuario", on_delete=models.DO_NOTHING)
    datetime_ultimo_acesso = models.DateTimeField()

    def __str__(self):
        retorno = f'Solicitação "#{str(self.uuid_solicitacao).upper()[:5]}"'
        retorno += f' está aberta e em edição pelo usuário "{self.usuario}"'
        return retorno
