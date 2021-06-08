from datetime import datetime

from django.db import models
from sequences import get_last_value, get_next_value

from ..dados_comuns.behaviors import (
    Ativavel,
    CriadoEm,
    CriadoPor,
    Logs,
    Nomeavel,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel
)
from ..dados_comuns.fluxo_status import (
    FluxoHomologacaoProduto,
    FluxoReclamacaoProduto,
    FluxoSolicitacaoCadastroProduto,
    HomologacaoProdutoWorkflow
)
from ..dados_comuns.models import AnexoLogSolicitacoesUsuario, LogSolicitacoesUsuario, TemplateMensagem
from ..dados_comuns.utils import convert_base64_to_contentfile
from ..escola.models import Escola

MAX_NUMERO_PROTOCOLO = 6


class ProtocoloDeDietaEspecial(Ativavel, CriadoEm, CriadoPor, TemChaveExterna):

    nome = models.CharField('Nome', blank=True, max_length=100, unique=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Protocolo de Dieta Especial'
        verbose_name_plural = 'Protocolos de Dieta Especial'


class Fabricante(Nomeavel, TemChaveExterna):

    def __str__(self):
        return self.nome


class Marca(Nomeavel, TemChaveExterna):

    def __str__(self):
        return self.nome


class TipoDeInformacaoNutricional(Nomeavel, TemChaveExterna):

    def __str__(self):
        return self.nome


class InformacaoNutricional(TemChaveExterna, Nomeavel):
    tipo_nutricional = models.ForeignKey(TipoDeInformacaoNutricional, on_delete=models.DO_NOTHING)
    medida = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Informação Nutricional'
        verbose_name_plural = 'Informações Nutricionais'


class ImagemDoProduto(TemChaveExterna):
    produto = models.ForeignKey('Produto', on_delete=models.CASCADE, blank=True)
    arquivo = models.FileField()
    nome = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Imagem do Produto'
        verbose_name_plural = 'Imagens do Produto'


class Produto(Ativavel, CriadoEm, CriadoPor, Nomeavel, TemChaveExterna, TemIdentificadorExternoAmigavel):
    eh_para_alunos_com_dieta = models.BooleanField('É para alunos com dieta especial', default=False)

    protocolos = models.ManyToManyField(ProtocoloDeDietaEspecial,
                                        related_name='protocolos',
                                        help_text='Protocolos do produto.',
                                        blank=True,
                                        )

    marca = models.ForeignKey(Marca, on_delete=models.DO_NOTHING)
    fabricante = models.ForeignKey(Fabricante, on_delete=models.DO_NOTHING)
    componentes = models.CharField('Componentes do Produto', blank=True, max_length=5000)

    tem_aditivos_alergenicos = models.BooleanField('Tem aditivos alergênicos', default=False)
    aditivos = models.TextField('Aditivos', blank=True)

    tipo = models.CharField('Tipo do Produto', blank=True, max_length=250)
    embalagem = models.CharField('Embalagem Primária', blank=True, max_length=500)
    prazo_validade = models.CharField('Prazo de validade', blank=True, max_length=100)
    info_armazenamento = models.CharField('Informações de Armazenamento',
                                          blank=True, max_length=500)
    outras_informacoes = models.TextField('Outras Informações', blank=True)
    numero_registro = models.CharField('Registro do órgão competente', blank=True, max_length=100)

    porcao = models.CharField('Porção nutricional', blank=True, max_length=50)
    unidade_caseira = models.CharField('Unidade nutricional', blank=True, max_length=50)

    @property
    def imagens(self):
        return self.imagemdoproduto_set.all()

    @property
    def informacoes_nutricionais(self):
        return self.informacoes_nutricionais.all()

    @property
    def homologacoes(self):
        return self.homologacoes.all()

    @property
    def ultima_homologacao(self):
        return self.homologacoes.first()

    @property
    def data_homologacao(self):
        homologacao = self.homologacoes.order_by('criado_em').last()
        log_homologacao = (
            homologacao.logs
            .filter(status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO)
            .order_by('criado_em')
            .last())
        return log_homologacao.criado_em

    @classmethod
    def filtrar_por_nome(cls, **kwargs):
        nome = kwargs.get('nome')
        return cls.objects.filter(nome__icontains=nome)

    @classmethod
    def filtrar_por_marca(cls, **kwargs):
        nome = kwargs.get('nome')
        return cls.objects.filter(marca__nome__icontains=nome)

    @classmethod
    def filtrar_por_fabricante(cls, **kwargs):
        nome = kwargs.get('nome')
        return cls.objects.filter(fabricante__nome__icontains=nome)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'


class NomeDeProdutoEdital(Ativavel, CriadoEm, CriadoPor, Nomeavel, TemChaveExterna, TemIdentificadorExternoAmigavel):

    class Meta:
        ordering = ('nome',)
        unique_together = ('nome',)
        verbose_name = 'Produto proveniente do Edital'
        verbose_name_plural = 'Produtos provenientes do Edital'

    def __str__(self):
        return self.nome

    def clean(self, *args, **kwargs):
        # Nome sempre em caixa alta.
        self.nome = self.nome.upper()
        return super(NomeDeProdutoEdital, self).clean(*args, **kwargs)


class LogNomeDeProdutoEdital(TemChaveExterna, TemIdentificadorExternoAmigavel, CriadoEm, CriadoPor):
    ACAO = (
        ('a', 'ativar'),
        ('i', 'inativar'),
    )
    acao = models.CharField('ação', max_length=1, choices=ACAO, null=True, blank=True)  # noqa DJ01
    nome_de_produto_edital = models.ForeignKey(
        NomeDeProdutoEdital,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ('-criado_em',)
        verbose_name = 'Log de Produto proveniente do Edital'
        verbose_name_plural = 'Log de Produtos provenientes do Edital'

    def __str__(self):
        return self.id_externo


class InformacoesNutricionaisDoProduto(TemChaveExterna):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='informacoes_nutricionais')
    informacao_nutricional = models.ForeignKey(InformacaoNutricional, on_delete=models.DO_NOTHING)
    quantidade_porcao = models.CharField(max_length=10)
    valor_diario = models.CharField(max_length=10)

    def __str__(self):
        nome_produto = self.produto.nome
        informacao_nutricional = self.informacao_nutricional.nome
        porcao = self.quantidade_porcao
        valor = self.valor_diario
        return f'{nome_produto} - {informacao_nutricional} => quantidade: {porcao} valor diario: {valor}'

    class Meta:
        verbose_name = 'Informação Nutricional do Produto'
        verbose_name_plural = 'Informações Nutricionais do Produto'


class HomologacaoDoProduto(TemChaveExterna, CriadoEm, CriadoPor, FluxoHomologacaoProduto,
                           Logs, TemIdentificadorExternoAmigavel, Ativavel):
    DESCRICAO = 'Homologação de Produto'
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='homologacoes')
    necessita_analise_sensorial = models.BooleanField(default=False)
    protocolo_analise_sensorial = models.CharField(max_length=8, blank=True)
    pdf_gerado = models.BooleanField(default=False)

    @property
    def data_cadastro(self):
        if self.status != self.workflow_class.RASCUNHO:
            log = self.logs.get(status_evento=LogSolicitacoesUsuario.INICIO_FLUXO)
            return log.criado_em.date()

    @property
    def template_mensagem(self):
        template = TemplateMensagem.objects.get(tipo=TemplateMensagem.HOMOLOGACAO_PRODUTO)
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

    @property
    def tempo_aguardando_acao_em_dias(self):
        if self.status in [
            HomologacaoProdutoWorkflow.CODAE_PENDENTE_HOMOLOGACAO,
            HomologacaoProdutoWorkflow.CODAE_QUESTIONADO,
            HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_SENSORIAL,
            HomologacaoProdutoWorkflow.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
            HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_RECLAMACAO,
            HomologacaoProdutoWorkflow.TERCEIRIZADA_RESPONDEU_RECLAMACAO
        ]:
            intervalo = datetime.today() - self.ultimo_log.criado_em
        else:
            try:
                penultimo_log = self.logs.order_by('-criado_em')[1]
                intervalo = self.ultimo_log.criado_em - penultimo_log.criado_em
            except IndexError:
                intervalo = datetime.today() - self.ultimo_log.criado_em
        return intervalo.days

    @property
    def ultimo_log(self):
        return self.log_mais_recente

    def gera_protocolo_analise_sensorial(self):
        id_sequecial = str(get_next_value('protocolo_analise_sensorial'))
        serial = ''
        for _ in range(MAX_NUMERO_PROTOCOLO - len(id_sequecial)):
            serial = serial + '0'
        serial = serial + str(id_sequecial)
        self.protocolo_analise_sensorial = f'AS{serial}'
        self.necessita_analise_sensorial = True
        self.save()

    @classmethod
    def retorna_numero_do_protocolo(cls):
        id_sequecial = get_last_value('protocolo_analise_sensorial')
        serial = ''
        if id_sequecial is None:
            id_sequecial = '1'
        else:
            id_sequecial = str(get_last_value('protocolo_analise_sensorial') + 1)
        for _ in range(MAX_NUMERO_PROTOCOLO - len(id_sequecial)):
            serial = serial + '0'
        serial = serial + str(id_sequecial)
        return f'AS{serial}'

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get('justificativa', '')
        return LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.HOMOLOGACAO_PRODUTO,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa
        )

    class Meta:
        ordering = ('-ativo', '-criado_em')
        verbose_name = 'Homologação de Produto'
        verbose_name_plural = 'Homologações de Produto'

    def __str__(self):
        return f'Homologação #{self.id_externo}'


class ReclamacaoDeProduto(FluxoReclamacaoProduto, TemChaveExterna, CriadoEm, CriadoPor,
                          Logs, TemIdentificadorExternoAmigavel):
    homologacao_de_produto = models.ForeignKey('HomologacaoDoProduto', on_delete=models.CASCADE,
                                               related_name='reclamacoes')
    reclamante_registro_funcional = models.CharField('RF/CRN/CRF', max_length=50)
    reclamante_cargo = models.CharField('Cargo', max_length=100)
    reclamante_nome = models.CharField('Nome', max_length=255)
    reclamacao = models.TextField('Reclamação')
    escola = models.ForeignKey(Escola, null=True, on_delete=models.PROTECT, related_name='reclamacoes')
    produto_lote = models.TextField(max_length=255, blank=True, default='')
    produto_data_validade = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True)
    produto_data_fabricacao = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True)

    def salvar_log_transicao(self, status_evento, **kwargs):
        justificativa = kwargs.get('justificativa', '')
        user = kwargs['user']
        if user:
            log_transicao = LogSolicitacoesUsuario.objects.create(
                descricao=str(self),
                status_evento=status_evento,
                solicitacao_tipo=LogSolicitacoesUsuario.RECLAMACAO_PRODUTO,
                usuario=user,
                uuid_original=self.uuid,
                justificativa=justificativa
            )
            for anexo in kwargs.get('anexos', []):
                arquivo = convert_base64_to_contentfile(anexo.pop('base64'))
                AnexoLogSolicitacoesUsuario.objects.create(
                    log=log_transicao,
                    arquivo=arquivo,
                    nome=anexo['nome']
                )
        return log_transicao

    @property
    def ultimo_log(self):
        return self.log_mais_recente

    def __str__(self):
        return f'Reclamação {self.uuid} feita por {self.reclamante_nome} em {self.criado_em}'


class AnexoReclamacaoDeProduto(TemChaveExterna):
    reclamacao_de_produto = models.ForeignKey(ReclamacaoDeProduto, related_name='anexos', on_delete=models.CASCADE)
    nome = models.CharField(max_length=255, blank=True)
    arquivo = models.FileField()

    def __str__(self):
        return f'Anexo {self.uuid} - {self.nome}'


class RespostaAnaliseSensorial(TemChaveExterna, TemIdentificadorExternoAmigavel, CriadoEm, CriadoPor):
    homologacao_de_produto = models.ForeignKey('HomologacaoDoProduto', on_delete=models.CASCADE,
                                               related_name='respostas_analise')
    responsavel_produto = models.CharField(max_length=150)
    registro_funcional = models.CharField(max_length=10)
    data = models.DateField(auto_now=False, auto_now_add=False)
    hora = models.TimeField(auto_now=False, auto_now_add=False)
    observacao = models.TextField(blank=True)

    @property
    def numero_protocolo(self):
        return self.homologacao_de_produto.protocolo_analise_sensorial

    def __str__(self):
        return f'Resposta {self.id_externo} de protocolo {self.numero_protocolo} criada em: {self.criado_em}'


class AnexoRespostaAnaliseSensorial(TemChaveExterna):
    resposta_analise_sensorial = models.ForeignKey(RespostaAnaliseSensorial, related_name='anexos',
                                                   on_delete=models.CASCADE)
    nome = models.CharField(max_length=255, blank=True)
    arquivo = models.FileField()

    def __str__(self):
        return f'Anexo {self.uuid} - {self.nome}'


class SolicitacaoCadastroProdutoDieta(FluxoSolicitacaoCadastroProduto, TemChaveExterna,
                                      TemIdentificadorExternoAmigavel, CriadoEm,
                                      CriadoPor):
    solicitacao_dieta_especial = models.ForeignKey('dieta_especial.SolicitacaoDietaEspecial', on_delete=models.CASCADE,
                                                   related_name='solicitacoes_cadastro_produto')
    aluno = models.ForeignKey('escola.Aluno', on_delete=models.CASCADE,
                              related_name='solicitacoes_cadastro_produto', null=True)
    escola = models.ForeignKey('escola.Escola', on_delete=models.CASCADE,
                               related_name='solicitacoes_cadastro_produto', null=True)
    terceirizada = models.ForeignKey('terceirizada.Terceirizada', on_delete=models.CASCADE,
                                     related_name='solicitacoes_cadastro_produto', null=True)
    nome_produto = models.CharField(max_length=150)
    marca_produto = models.CharField(max_length=150, blank=True)
    fabricante_produto = models.CharField(max_length=150, blank=True)
    info_produto = models.TextField()
    data_previsao_cadastro = models.DateField(null=True)
    justificativa_previsao_cadastro = models.TextField(blank=True)

    def __str__(self):
        return f'Solicitacao cadastro produto {self.nome_produto}'
