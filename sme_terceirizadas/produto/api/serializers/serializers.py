import datetime

from rest_framework import serializers

from ....dados_comuns.api.serializers import (
    ContatoSerializer,
    LogSolicitacoesSerializer,
    LogSolicitacoesUsuarioComAnexosSerializer,
    LogSolicitacoesUsuarioComVinculoSerializer,
    LogSolicitacoesUsuarioSerializer
)
from ....dados_comuns.fluxo_status import ReclamacaoProdutoWorkflow
from ....dados_comuns.validators import objeto_nao_deve_ter_duplicidade
from ....dieta_especial.api import serializers as des
from ....dieta_especial.models import Alimento
from ....escola.api.serializers import (
    AlunoSimplesSerializer,
    DiretoriaRegionalSimplissimaSerializer,
    EscolaSimplissimaSerializer,
    TipoGestaoSerializer
)
from ....escola.models import Escola
from ....terceirizada.api.serializers.serializers import TerceirizadaSimplesSerializer
from ...models import (
    AnexoReclamacaoDeProduto,
    Fabricante,
    HomologacaoDoProduto,
    ImagemDoProduto,
    InformacaoNutricional,
    InformacoesNutricionaisDoProduto,
    LogSolicitacoesUsuario,
    Marca,
    NomeDeProdutoEdital,
    Produto,
    ProtocoloDeDietaEspecial,
    ReclamacaoDeProduto,
    RespostaAnaliseSensorial,
    SolicitacaoCadastroProdutoDieta,
    TipoDeInformacaoNutricional
)


class FabricanteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Fabricante
        exclude = ('id',)


class MarcaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Marca
        exclude = ('id',)


class ProtocoloDeDietaEspecialSerializer(serializers.ModelSerializer):
    nome = serializers.CharField()

    def validate_nome(self, nome):
        filtro = {'nome__iexact': nome}
        objeto_nao_deve_ter_duplicidade(ProtocoloDeDietaEspecial,
                                        'Protocolo de Dieta Especial com este Nome já existe.',
                                        **filtro)
        return nome

    class Meta:
        model = ProtocoloDeDietaEspecial
        exclude = ('id', 'ativo', 'criado_em', 'criado_por',)


class AnexoReclamacaoDeProdutoSerializer(serializers.ModelSerializer):
    arquivo = serializers.SerializerMethodField()

    def get_arquivo(self, obj):
        request = self.context.get('request')
        arquivo = obj.arquivo.url
        return request.build_absolute_uri(arquivo)

    class Meta:
        model = AnexoReclamacaoDeProduto
        fields = ('arquivo', 'nome', 'uuid')


class ImagemDoProdutoSerializer(serializers.ModelSerializer):
    arquivo = serializers.SerializerMethodField()

    def get_arquivo(self, obj):
        request = self.context.get('request')
        arquivo = obj.arquivo.url
        return request.build_absolute_uri(arquivo)

    class Meta:
        model = ImagemDoProduto
        fields = ('arquivo', 'nome', 'uuid')


class TipoDeInformacaoNutricionalSerializer(serializers.ModelSerializer):

    class Meta:
        model = TipoDeInformacaoNutricional
        exclude = ('id',)


class InformacaoNutricionalSerializer(serializers.ModelSerializer):
    tipo_nutricional = TipoDeInformacaoNutricionalSerializer()

    class Meta:
        model = InformacaoNutricional
        exclude = ('id',)


class InformacoesNutricionaisDoProdutoSerializer(serializers.ModelSerializer):
    informacao_nutricional = InformacaoNutricionalSerializer()

    class Meta:
        model = InformacoesNutricionaisDoProduto
        exclude = ('id', 'produto')


class ReclamacaoDeProdutoSerializer(serializers.ModelSerializer):
    escola = EscolaSimplissimaSerializer()
    anexos = serializers.SerializerMethodField()
    status_titulo = serializers.CharField(source='status.state.title')
    logs = serializers.SerializerMethodField()

    def get_anexos(self, obj):
        return AnexoReclamacaoDeProdutoSerializer(
            obj.anexos.all(),
            context=self.context,
            many=True
        ).data

    def get_logs(self, obj):
        return LogSolicitacoesUsuarioSerializer(
            LogSolicitacoesUsuario.objects.filter(
                uuid_original=obj.uuid).order_by('criado_em'),
            many=True
        ).data

    class Meta:
        model = ReclamacaoDeProduto
        fields = ('uuid', 'reclamante_registro_funcional', 'logs', 'reclamante_cargo', 'reclamante_nome',
                  'reclamacao', 'escola', 'anexos', 'status', 'status_titulo', 'criado_em', 'id_externo')


class ReclamacaoDeProdutoSimplesSerializer(serializers.ModelSerializer):
    ultimo_log = LogSolicitacoesUsuarioSerializer()

    class Meta:
        model = ReclamacaoDeProduto
        fields = ('reclamacao', 'criado_em', 'ultimo_log')


class HomologacaoProdutoSimplesSerializer(serializers.ModelSerializer):
    reclamacoes = serializers.SerializerMethodField()
    rastro_terceirizada = TerceirizadaSimplesSerializer()
    logs = LogSolicitacoesUsuarioComVinculoSerializer(many=True)

    def get_reclamacoes(self, obj):
        return ReclamacaoDeProdutoSerializer(
            obj.reclamacoes.all(), context=self.context,
            many=True
        ).data

    class Meta:
        model = HomologacaoDoProduto
        fields = ('uuid', 'status', 'id_externo', 'rastro_terceirizada', 'logs',
                  'criado_em', 'reclamacoes')


class HomologacaoProdutoComUltimoLogSerializer(serializers.ModelSerializer):
    reclamacoes = serializers.SerializerMethodField()
    rastro_terceirizada = TerceirizadaSimplesSerializer()
    logs = LogSolicitacoesUsuarioComVinculoSerializer(many=True)
    ultimo_log = LogSolicitacoesUsuarioComVinculoSerializer()
    status_titulo = serializers.CharField(source='status.state.title')
    data_cadastro = serializers.DateField()

    def get_reclamacoes(self, obj):
        return ReclamacaoDeProdutoSerializer(
            obj.reclamacoes.all(), context=self.context,
            many=True
        ).data

    class Meta:
        model = HomologacaoDoProduto
        fields = ('uuid', 'status', 'id_externo', 'rastro_terceirizada', 'logs',
                  'criado_em', 'reclamacoes', 'ultimo_log', 'tempo_aguardando_acao_em_dias',
                  'status_titulo', 'protocolo_analise_sensorial', 'data_cadastro')


class ProdutoSerializer(serializers.ModelSerializer):
    protocolos = ProtocoloDeDietaEspecialSerializer(many=True)
    marca = MarcaSerializer()
    fabricante = FabricanteSerializer()
    imagens = serializers.ListField(
        child=ImagemDoProdutoSerializer(), required=True
    )
    id_externo = serializers.CharField()

    informacoes_nutricionais = serializers.SerializerMethodField()

    homologacoes = serializers.SerializerMethodField()

    ultima_homologacao = HomologacaoProdutoComUltimoLogSerializer()

    def get_homologacoes(self, obj):
        return HomologacaoProdutoComUltimoLogSerializer(
            HomologacaoDoProduto.objects.filter(
                produto=obj
            ), context=self.context,
            many=True
        ).data

    def get_informacoes_nutricionais(self, obj):
        return InformacoesNutricionaisDoProdutoSerializer(
            InformacoesNutricionaisDoProduto.objects.filter(
                produto=obj
            ), many=True
        ).data

    class Meta:
        model = Produto
        exclude = ('id',)


class ProdutoSemAnexoSerializer(serializers.ModelSerializer):
    protocolos = ProtocoloDeDietaEspecialSerializer(many=True)
    marca = MarcaSerializer()
    fabricante = FabricanteSerializer()
    id_externo = serializers.CharField()

    informacoes_nutricionais = serializers.SerializerMethodField()

    homologacoes = serializers.SerializerMethodField()

    ultima_homologacao = HomologacaoProdutoSimplesSerializer()

    def get_homologacoes(self, obj):
        return HomologacaoProdutoSimplesSerializer(
            HomologacaoDoProduto.objects.filter(
                produto=obj
            ), context=self.context,
            many=True
        ).data

    def get_informacoes_nutricionais(self, obj):
        return InformacoesNutricionaisDoProdutoSerializer(
            InformacoesNutricionaisDoProduto.objects.filter(
                produto=obj
            ), many=True
        ).data

    class Meta:
        model = Produto
        exclude = ('id',)


class ProdutoSimplesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Produto
        fields = ('uuid', 'nome',)


class NomeDeProdutoEditalSerializer(serializers.ModelSerializer):

    class Meta:
        model = NomeDeProdutoEdital
        fields = ('uuid', 'nome',)


class ProdutosSubstitutosSerializer(serializers.ModelSerializer):
    tipo = serializers.SerializerMethodField()

    def get_tipo(self, instance):
        return 'p'

    class Meta:
        model = Produto
        fields = ('uuid', 'nome', 'tipo')


class SubstitutosSerializer(serializers.Serializer):
    # https://stackoverflow.com/a/41744814

    @classmethod
    def get_serializer(cls, model):
        if model == Alimento:
            return des.AlimentosSubstitutosSerializer
        elif model == Produto:
            return ProdutosSubstitutosSerializer

    def to_internal_value(self, data):
        alimento_obj = Alimento.objects.filter(uuid=data).first()
        if alimento_obj:
            return alimento_obj
        produto_obj = Produto.objects.filter(uuid=data).first()
        if produto_obj:
            return produto_obj
        else:
            raise Exception('Substituto não encontrado.')

    def to_representation(self, instance):
        serializer = self.get_serializer(instance.__class__)
        return serializer(instance, context=self.context).data


class MarcaSimplesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Marca
        fields = ('uuid', 'nome',)


class FabricanteSimplesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Fabricante
        fields = ('uuid', 'nome',)


class ProtocoloSimplesSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProtocoloDeDietaEspecial
        fields = ('uuid', 'nome',)


class HomologacaoProdutoSerializer(serializers.ModelSerializer):
    produto = ProdutoSerializer()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = HomologacaoDoProduto
        fields = ('uuid', 'produto', 'status', 'id_externo', 'logs', 'rastro_terceirizada', 'pdf_gerado',
                  'protocolo_analise_sensorial')


class ProdutoBaseSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer()
    fabricante = FabricanteSerializer()
    id_externo = serializers.CharField()


class HomologacaoProdutoBase(serializers.ModelSerializer):
    qtde_reclamacoes = serializers.SerializerMethodField()
    qtde_questionamentos = serializers.SerializerMethodField()

    def get_qtde_reclamacoes(self, obj):
        return ReclamacaoDeProduto.objects.filter(homologacao_de_produto=obj).count()

    def get_qtde_questionamentos(self, obj):
        return ReclamacaoDeProduto.objects.filter(
            homologacao_de_produto=obj,
            status=ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_TERCEIRIZADA).count()


class HomologacaoProdutoPainelGerencialSerializer(HomologacaoProdutoBase):
    nome_produto = serializers.SerializerMethodField()
    log_mais_recente = serializers.SerializerMethodField()

    def get_log_mais_recente(self, obj):
        if obj.log_mais_recente:
            if obj.log_mais_recente.criado_em.date() == datetime.date.today():
                return datetime.datetime.strftime(obj.log_mais_recente.criado_em, '%d/%m/%Y %H:%M')
            return datetime.datetime.strftime(obj.log_mais_recente.criado_em, '%d/%m/%Y')
        else:
            return datetime.datetime.strftime(obj.criado_em, '%d/%m/%Y')

    def get_nome_produto(self, obj):
        return obj.produto.nome

    class Meta:
        model = HomologacaoDoProduto
        fields = ('uuid', 'nome_produto', 'status', 'id_externo', 'log_mais_recente',
                  'qtde_reclamacoes', 'qtde_questionamentos')


class HomologacaoProdutoComLogsDetalhadosSerializer(serializers.ModelSerializer):
    produto = ProdutoSemAnexoSerializer()
    logs = LogSolicitacoesUsuarioComAnexosSerializer(many=True)
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = HomologacaoDoProduto
        fields = ('uuid', 'produto', 'status', 'id_externo', 'logs', 'rastro_terceirizada', 'pdf_gerado',
                  'protocolo_analise_sensorial')


class RespostaAnaliseSensorialSerializer(serializers.ModelSerializer):

    class Meta:
        model = RespostaAnaliseSensorial
        fields = ('uuid', 'responsavel_produto', 'registro_funcional', 'id_externo', 'data', 'hora',
                  'observacao', 'criado_em')


class HomologacaoRelatorioAnaliseSensorialSerializer(serializers.ModelSerializer):
    log_resposta_analise = serializers.SerializerMethodField()
    log_solicitacao_analise = serializers.SerializerMethodField()
    rastro_terceirizada = TerceirizadaSimplesSerializer()
    resposta_analise = serializers.SerializerMethodField()

    def get_resposta_analise(self, obj):
        return RespostaAnaliseSensorialSerializer(
            RespostaAnaliseSensorial.objects.filter(homologacao_de_produto=obj).order_by('criado_em').last()).data

    def get_log_resposta_analise(self, obj):
        return LogSolicitacoesUsuarioSerializer(
            LogSolicitacoesUsuario.objects.filter(
                uuid_original=obj.uuid,
                status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_ANALISE_SENSORIAL
            ).order_by('criado_em').last()).data

    def get_log_solicitacao_analise(self, obj):
        return LogSolicitacoesUsuarioSerializer(
            LogSolicitacoesUsuario.objects.filter(
                uuid_original=obj.uuid,
                status_evento=LogSolicitacoesUsuario.CODAE_PEDIU_ANALISE_SENSORIAL,
                criado_em__lte=obj.respostas_analise.last().criado_em
            ).order_by('criado_em').last()).data

    class Meta:
        model = HomologacaoDoProduto
        fields = ('uuid', 'status', 'id_externo', 'log_resposta_analise', 'log_solicitacao_analise',
                  'rastro_terceirizada', 'protocolo_analise_sensorial', 'resposta_analise')


class ProdutoRelatorioAnaliseSensorialSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer()
    fabricante = FabricanteSerializer()
    id_externo = serializers.CharField()
    ultima_homologacao = HomologacaoRelatorioAnaliseSensorialSerializer()

    class Meta:
        model = Produto
        exclude = ('id',)


class HomologacaoListagemSerializer(serializers.ModelSerializer):
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = HomologacaoDoProduto
        fields = ('uuid', 'status', 'id_externo',
                  'rastro_terceirizada', 'criado_em')


class ProdutoListagemSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer()
    fabricante = FabricanteSerializer()
    id_externo = serializers.CharField()
    ultima_homologacao = HomologacaoListagemSerializer()

    class Meta:
        model = Produto
        exclude = ('id',)


class UltimoLogRelatorioSituacaoSerializer(serializers.ModelSerializer):

    class Meta:
        model = LogSolicitacoesUsuario
        fields = ('criado_em',)


class HomologacaoRelatorioSituacaoSerializer(serializers.ModelSerializer):
    ultimo_log = UltimoLogRelatorioSituacaoSerializer()
    status_titulo = serializers.CharField(source='status.state.title')

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('ultimo_log')

        return queryset

    class Meta:
        model = HomologacaoDoProduto
        fields = ('ultimo_log', 'status', 'status_titulo')


class ProdutoRelatorioSituacaoSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer()
    fabricante = FabricanteSerializer()
    ultima_homologacao = HomologacaoRelatorioSituacaoSerializer()

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related(
            'marca', 'fabricante', 'ultima_homogacao')

        return queryset

    class Meta:
        model = Produto
        fields = ('nome', 'marca', 'fabricante', 'criado_em', 'ultima_homologacao',
                  'eh_para_alunos_com_dieta', 'tem_aditivos_alergenicos')


class EscolaSolicitacaoCadastroProdutoDietaSerializer(serializers.ModelSerializer):
    tipo_gestao = TipoGestaoSerializer()
    lote = serializers.CharField(source='lote.nome')
    diretoria_regional = DiretoriaRegionalSimplissimaSerializer()
    contato = ContatoSerializer()

    class Meta:
        model = Escola
        fields = ('tipo_gestao', 'lote',
                  'diretoria_regional', 'contato', 'nome')


class SolicitacaoCadastroProdutoDietaSimplesSerializer(serializers.ModelSerializer):
    status_title = serializers.CharField(source='status.state.title')

    class Meta:
        model = SolicitacaoCadastroProdutoDieta
        fields = ('uuid', 'criado_em', 'nome_produto',
                  'marca_produto', 'fabricante_produto', 'status',
                  'status_title', 'data_previsao_cadastro')


class SolicitacaoCadastroProdutoDietaSerializer(serializers.ModelSerializer):
    aluno = AlunoSimplesSerializer()
    escola = EscolaSolicitacaoCadastroProdutoDietaSerializer()
    status_title = serializers.CharField(source='status.state.title')

    class Meta:
        model = SolicitacaoCadastroProdutoDieta
        fields = ('uuid', 'criado_em', 'aluno', 'escola', 'nome_produto',
                  'marca_produto', 'fabricante_produto', 'info_produto', 'status',
                  'status_title', 'data_previsao_cadastro', 'justificativa_previsao_cadastro')


class SolicitacaoCadastroProdutoDietaConfirmarSerializer(SolicitacaoCadastroProdutoDietaSerializer):
    data_previsao_cadastro = serializers.DateField(required=True)
    justificativa_previsao_cadastro = serializers.CharField(
        allow_blank=True, required=False)

    class Meta:
        model = SolicitacaoCadastroProdutoDieta
        fields = ('data_previsao_cadastro', 'justificativa_previsao_cadastro')


class ReclamacaoDeProdutoRelatorioSerializer(serializers.ModelSerializer):
    escola = EscolaSimplissimaSerializer()
    status_titulo = serializers.CharField(source='status.state.title')
    logs = LogSolicitacoesSerializer(many=True)

    class Meta:
        model = ReclamacaoDeProduto
        fields = ('uuid', 'reclamante_registro_funcional', 'logs', 'reclamante_cargo', 'reclamante_nome',
                  'reclamacao', 'escola', 'status', 'status_titulo', 'criado_em', 'id_externo')


class HomologacaoReclamacaoSerializer(serializers.ModelSerializer):
    reclamacoes = ReclamacaoDeProdutoRelatorioSerializer(many=True)
    status_titulo = serializers.CharField(source='status.state.title')
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = HomologacaoDoProduto
        fields = ('id', 'uuid', 'status', 'id_externo',
                  'criado_em', 'reclamacoes', 'status_titulo',
                  'rastro_terceirizada')


class ProdutoReclamacaoSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer()
    fabricante = FabricanteSerializer()
    id_externo = serializers.CharField()
    qtde_questionamentos = serializers.IntegerField(default=None)
    ultima_homologacao = HomologacaoReclamacaoSerializer()

    class Meta:
        model = Produto
        fields = ('uuid', 'nome', 'marca', 'fabricante', 'id_externo',
                  'ultima_homologacao', 'criado_em', 'qtde_questionamentos')


class ReclamacoesUltimaHomologacaoHomologadosPorParametrosSerializer(serializers.ModelSerializer):
    escola = EscolaSimplissimaSerializer()
    status_titulo = serializers.CharField(source='status.state.title')
    logs = serializers.SerializerMethodField()

    def get_logs(self, obj):
        return LogSolicitacoesUsuarioSerializer(
            LogSolicitacoesUsuario.objects.filter(
                uuid_original=obj.uuid).order_by('criado_em'),
            many=True
        ).data

    class Meta:
        model = ReclamacaoDeProduto
        fields = ('logs', 'id_externo', 'status_titulo', 'reclamante_nome', 'reclamante_registro_funcional',
                  'escola', 'criado_em', 'reclamacao', 'uuid', 'reclamante_cargo', 'status_titulo')


class UltimaHomologacaoHomologadosPorParametrosSerializer(serializers.ModelSerializer):
    reclamacoes = serializers.SerializerMethodField()

    def get_reclamacoes(self, obj):
        return ReclamacoesUltimaHomologacaoHomologadosPorParametrosSerializer(
            obj.reclamacoes.all(), context=self.context,
            many=True
        ).data

    class Meta:
        model = HomologacaoDoProduto
        fields = ('uuid', 'reclamacoes')


class ProdutoHomologadosPorParametrosSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer()
    ultima_homologacao = UltimaHomologacaoHomologadosPorParametrosSerializer()

    class Meta:
        model = Produto
        fields = ('nome', 'marca', 'eh_para_alunos_com_dieta',
                  'ultima_homologacao', 'criado_em')


class HomologacaoProdutoSuspensoSerializer(serializers.ModelSerializer):
    ultimo_log = LogSolicitacoesUsuarioComAnexosSerializer()

    class Meta:
        model = HomologacaoDoProduto
        fields = ('uuid', 'ultimo_log')


class ProdutoSuspensoSerializer(ProdutoBaseSerializer):
    ultima_homologacao = HomologacaoProdutoSuspensoSerializer()

    class Meta:
        model = Produto
        fields = ('id_externo', 'nome', 'marca', 'fabricante',
                  'ultima_homologacao', 'criado_em')
