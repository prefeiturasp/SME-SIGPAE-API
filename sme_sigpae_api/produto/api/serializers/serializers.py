import datetime

import environ
from rest_framework import serializers

from ....dados_comuns.api.serializers import (
    AnexoLogSolicitacoesUsuarioSerializer,
    ContatoSerializer,
    LogSolicitacoesSerializer,
    LogSolicitacoesUsuarioComAnexosSerializer,
    LogSolicitacoesUsuarioComVinculoSerializer,
    LogSolicitacoesUsuarioSerializer,
)
from ....dados_comuns.fluxo_status import ReclamacaoProdutoWorkflow
from ....dados_comuns.validators import objeto_nao_deve_ter_duplicidade
from ....dieta_especial.api import serializers as des
from ....dieta_especial.models import Alimento
from ....escola.api.serializers import (
    AlunoSimplesSerializer,
    DiretoriaRegionalSimplissimaSerializer,
    EscolaSimplissimaSerializer,
    TipoGestaoSerializer,
)
from ....escola.models import Escola
from ....perfil.api.serializers import UsuarioSerializer
from ....perfil.models import Usuario
from ....terceirizada.api.serializers.serializers import (
    EditalSerializer,
    TerceirizadaSimplesSerializer,
)
from ...models import (
    AnaliseSensorial,
    AnexoReclamacaoDeProduto,
    EmbalagemProduto,
    EspecificacaoProduto,
    Fabricante,
    HomologacaoProduto,
    ImagemDoProduto,
    InformacaoNutricional,
    InformacoesNutricionaisDoProduto,
    ItemCadastro,
    LogSolicitacoesUsuario,
    Marca,
    NomeDeProdutoEdital,
    Produto,
    ProdutoEdital,
    ProtocoloDeDietaEspecial,
    ReclamacaoDeProduto,
    RespostaAnaliseSensorial,
    SolicitacaoCadastroProdutoDieta,
    TipoDeInformacaoNutricional,
    UnidadeMedida,
)


class FabricanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fabricante
        exclude = ("id",)


class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        exclude = ("id",)


class ProtocoloDeDietaEspecialSerializer(serializers.ModelSerializer):
    nome = serializers.CharField()

    def validate_nome(self, nome):
        filtro = {"nome__iexact": nome}
        objeto_nao_deve_ter_duplicidade(
            ProtocoloDeDietaEspecial,
            "Protocolo de Dieta Especial com este Nome já existe.",
            **filtro,
        )
        return nome

    class Meta:
        model = ProtocoloDeDietaEspecial
        exclude = (
            "id",
            "ativo",
            "criado_em",
            "criado_por",
        )


class AnexoReclamacaoDeProdutoSerializer(serializers.ModelSerializer):
    arquivo = serializers.SerializerMethodField()

    def get_arquivo(self, obj):
        request = self.context.get("request")
        arquivo = obj.arquivo.url
        return request.build_absolute_uri(arquivo)

    class Meta:
        model = AnexoReclamacaoDeProduto
        fields = ("arquivo", "nome", "uuid")


class ImagemDoProdutoSerializer(serializers.ModelSerializer):
    arquivo = serializers.SerializerMethodField()

    def get_arquivo(self, obj):
        env = environ.Env()
        api_url = env.str("URL_ANEXO", default="http://localhost:8000")
        return f"{api_url}{obj.arquivo.url}"

    class Meta:
        model = ImagemDoProduto
        fields = ("arquivo", "nome", "uuid")


class TipoDeInformacaoNutricionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDeInformacaoNutricional
        exclude = ("id",)


class InformacaoNutricionalSerializer(serializers.ModelSerializer):
    tipo_nutricional = TipoDeInformacaoNutricionalSerializer()
    eh_dependente = serializers.BooleanField()

    class Meta:
        model = InformacaoNutricional
        exclude = ("id",)


class InformacoesNutricionaisDoProdutoSerializer(serializers.ModelSerializer):
    informacao_nutricional = InformacaoNutricionalSerializer()

    class Meta:
        model = InformacoesNutricionaisDoProduto
        exclude = ("id", "produto")


class ReclamacaoDeProdutoSerializer(serializers.ModelSerializer):
    escola = EscolaSimplissimaSerializer()
    anexos = serializers.SerializerMethodField()
    status_titulo = serializers.CharField(source="status.state.title")
    logs = serializers.SerializerMethodField()
    usuario = serializers.SerializerMethodField()

    def get_usuario(self, obj):
        return UsuarioSerializer(
            Usuario.objects.filter(
                registro_funcional=obj.reclamante_registro_funcional
            ).first(),
        ).data

    def get_anexos(self, obj):
        return AnexoReclamacaoDeProdutoSerializer(
            obj.anexos.all(), context=self.context, many=True
        ).data

    def get_logs(self, obj):
        return LogSolicitacoesUsuarioComAnexosSerializer(
            LogSolicitacoesUsuario.objects.filter(uuid_original=obj.uuid).order_by(
                "criado_em"
            ),
            many=True,
        ).data

    class Meta:
        model = ReclamacaoDeProduto
        fields = (
            "uuid",
            "reclamante_registro_funcional",
            "logs",
            "reclamante_cargo",
            "reclamante_nome",
            "reclamacao",
            "escola",
            "usuario",
            "anexos",
            "status",
            "status_titulo",
            "criado_em",
            "id_externo",
        )


class ReclamacaoDeProdutoSimplesSerializer(serializers.ModelSerializer):
    ultimo_log = LogSolicitacoesUsuarioSerializer()

    class Meta:
        model = ReclamacaoDeProduto
        fields = ("reclamacao", "criado_em", "ultimo_log")


class HomologacaoProdutoSimplesSerializer(serializers.ModelSerializer):
    reclamacoes = serializers.SerializerMethodField()
    rastro_terceirizada = TerceirizadaSimplesSerializer()
    logs = LogSolicitacoesUsuarioComVinculoSerializer(many=True)

    def get_reclamacoes(self, obj):
        return ReclamacaoDeProdutoSerializer(
            obj.reclamacoes.all(), context=self.context, many=True
        ).data

    class Meta:
        model = HomologacaoProduto
        fields = (
            "uuid",
            "status",
            "id_externo",
            "rastro_terceirizada",
            "logs",
            "criado_em",
            "reclamacoes",
        )


class AnaliseSensorialSerializer(serializers.ModelSerializer):
    terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = AnaliseSensorial
        exclude = ("id",)


class HomologacaoProdutoComUltimoLogSerializer(serializers.ModelSerializer):
    reclamacoes = serializers.SerializerMethodField()
    rastro_terceirizada = TerceirizadaSimplesSerializer()
    logs = LogSolicitacoesUsuarioComVinculoSerializer(many=True)
    ultimo_log = LogSolicitacoesUsuarioComVinculoSerializer()
    status_titulo = serializers.CharField(source="status.state.title")
    data_cadastro = serializers.DateField()
    ultima_analise = AnaliseSensorialSerializer()

    def get_reclamacoes(self, obj):
        return ReclamacaoDeProdutoSerializer(
            obj.reclamacoes.all(), context=self.context, many=True
        ).data

    class Meta:
        model = HomologacaoProduto
        fields = (
            "uuid",
            "status",
            "id_externo",
            "rastro_terceirizada",
            "logs",
            "criado_em",
            "reclamacoes",
            "ultimo_log",
            "ultima_analise",
            "tempo_aguardando_acao_em_dias",
            "status_titulo",
            "protocolo_analise_sensorial",
            "data_cadastro",
        )


class UnidadeMedidaSerialzer(serializers.ModelSerializer):
    class Meta:
        model = UnidadeMedida
        fields = ("uuid", "nome")


class EmbalagemProdutoSerialzer(serializers.ModelSerializer):
    class Meta:
        model = EmbalagemProduto
        fields = ("uuid", "nome")


class EspecificacaoProdutoSerializer(serializers.ModelSerializer):
    unidade_de_medida = UnidadeMedidaSerialzer()
    embalagem_produto = EmbalagemProdutoSerialzer()

    class Meta:
        model = EspecificacaoProduto
        exclude = ("id", "produto")


class ProdutoSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer()
    fabricante = FabricanteSerializer()
    imagens = serializers.ListField(child=ImagemDoProdutoSerializer(), required=True)
    id_externo = serializers.CharField()

    informacoes_nutricionais = serializers.SerializerMethodField()

    homologacao = HomologacaoProdutoComUltimoLogSerializer()

    ultima_homologacao = HomologacaoProdutoComUltimoLogSerializer()

    especificacoes = serializers.SerializerMethodField()

    vinculos_produto_edital = serializers.SerializerMethodField()

    def get_informacoes_nutricionais(self, obj):
        return InformacoesNutricionaisDoProdutoSerializer(
            InformacoesNutricionaisDoProduto.objects.filter(produto=obj), many=True
        ).data

    def get_especificacoes(self, obj):
        return EspecificacaoProdutoSerializer(
            EspecificacaoProduto.objects.filter(produto=obj), many=True
        ).data

    def get_vinculos_produto_edital(self, obj):
        return ProdutoEditalSerializer(
            ProdutoEdital.objects.filter(produto=obj), many=True
        ).data

    class Meta:
        model = Produto
        exclude = ("id", "protocolos")


class ProdutoSemAnexoSerializer(serializers.ModelSerializer):
    protocolos = ProtocoloDeDietaEspecialSerializer(many=True)
    marca = MarcaSerializer()
    fabricante = FabricanteSerializer()
    id_externo = serializers.CharField()

    informacoes_nutricionais = serializers.SerializerMethodField()

    homologacao = serializers.SerializerMethodField()

    ultima_homologacao = HomologacaoProdutoSimplesSerializer()

    def get_homologacao(self, obj):
        return HomologacaoProdutoSimplesSerializer(
            HomologacaoProduto.objects.filter(produto=obj), context=self.context
        ).data

    def get_informacoes_nutricionais(self, obj):
        return InformacoesNutricionaisDoProdutoSerializer(
            InformacoesNutricionaisDoProduto.objects.filter(produto=obj), many=True
        ).data

    class Meta:
        model = Produto
        exclude = ("id",)


class ProdutoSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = (
            "uuid",
            "nome",
        )


class NomeDeProdutoEditalSerializer(serializers.ModelSerializer):
    class Meta:
        model = NomeDeProdutoEdital
        fields = ("uuid", "nome")


class CadastroProdutosEditalSerializer(serializers.ModelSerializer):
    nome = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    criado_em = serializers.SerializerMethodField()

    def get_criado_em(self, obj):
        return obj.criado_em.strftime("%d/%m/%Y")

    def get_nome(self, obj):
        return obj.nome

    def get_status(self, obj):
        return "Ativo" if obj.ativo is True else "Inativo"

    class Meta:
        model = NomeDeProdutoEdital
        fields = ("uuid", "nome", "status", "criado_em")


class ProdutosSubstitutosSerializer(serializers.ModelSerializer):
    tipo = serializers.SerializerMethodField()

    def get_tipo(self, instance):
        return "p"

    class Meta:
        model = Produto
        fields = ("uuid", "nome", "tipo")


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
            raise Exception("Substituto não encontrado.")

    def to_representation(self, instance):
        serializer = self.get_serializer(instance.__class__)
        return serializer(instance, context=self.context).data


class MarcaSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = (
            "uuid",
            "nome",
        )


class FabricanteSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fabricante
        fields = (
            "uuid",
            "nome",
        )


class ProtocoloSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProtocoloDeDietaEspecial
        fields = (
            "uuid",
            "nome",
        )


class HomologacaoProdutoSerializer(serializers.ModelSerializer):
    produto = ProdutoSerializer()
    logs = LogSolicitacoesUsuarioComAnexosSerializer(many=True)
    rastro_terceirizada = TerceirizadaSimplesSerializer()
    ultima_analise = AnaliseSensorialSerializer()
    esta_homologado = serializers.SerializerMethodField()

    def get_esta_homologado(self, obj):
        return obj.esta_homologado()

    class Meta:
        model = HomologacaoProduto
        fields = (
            "uuid",
            "produto",
            "status",
            "id_externo",
            "logs",
            "rastro_terceirizada",
            "pdf_gerado",
            "protocolo_analise_sensorial",
            "ultima_analise",
            "esta_homologado",
            "tem_copia",
        )


class ProdutoBaseSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer()
    fabricante = FabricanteSerializer()
    id_externo = serializers.CharField()


class HomologacaoProdutoBase(serializers.ModelSerializer):
    qtde_reclamacoes = serializers.SerializerMethodField()
    qtde_questionamentos = serializers.SerializerMethodField()

    def get_qtde_reclamacoes(self, obj):
        return ReclamacaoDeProduto.objects.filter(homologacao_produto=obj).count()

    def get_qtde_questionamentos(self, obj):
        return ReclamacaoDeProduto.objects.filter(
            homologacao_produto=obj,
            status=ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_TERCEIRIZADA,
        ).count()


class HomologacaoProdutoPainelGerencialSerializer(HomologacaoProdutoBase):
    nome_produto = serializers.SerializerMethodField()
    marca_produto = serializers.SerializerMethodField()
    fabricante_produto = serializers.SerializerMethodField()
    log_mais_recente = serializers.SerializerMethodField()
    nome_usuario_log_de_reclamacao = serializers.SerializerMethodField()
    tem_vinculo_produto_edital_suspenso = serializers.BooleanField()
    data_edital_suspenso_mais_recente = serializers.SerializerMethodField()
    editais = serializers.SerializerMethodField()
    produto_editais = serializers.SerializerMethodField()

    def get_log_mais_recente(self, obj):
        data = obj.log_mais_recente.criado_em if obj.log_mais_recente else obj.criado_em
        format_str = (
            "%d/%m/%Y %H:%M" if data.date() == datetime.date.today() else "%d/%m/%Y"
        )
        return data.strftime(format_str)

    def get_nome_usuario_log_de_reclamacao(self, obj) -> str:
        if obj.status.is_CODAE_QUESTIONOU_UE:
            status_dict = dict(LogSolicitacoesUsuario.STATUS_POSSIVEIS)
            status_reclamacao = status_dict.get(
                "Escola/Nutricionista reclamou do produto"
            )
            usr_log = next(
                (
                    log
                    for log in obj.logs.all()
                    if log.status_evento == status_reclamacao
                ),
                None,
            )
            return usr_log.usuario.nome if usr_log else ""
        return ""

    def get_nome_produto(self, obj):
        return obj.produto.nome

    def get_marca_produto(self, obj):
        return obj.produto.marca.nome

    def get_fabricante_produto(self, obj):
        return obj.produto.fabricante.nome

    def get_data_edital_suspenso_mais_recente(self, obj):
        workflow = self.context.get("workflow", "").upper()
        data = obj.data_edital_suspenso_mais_recente
        if (
            obj.status in ["CODAE_HOMOLOGADO", "CODAE_AUTORIZOU_RECLAMACAO"]
            and workflow in ["CODAE_SUSPENDEU", "CODAE_AUTORIZOU_RECLAMACAO"]
            and data
        ):
            if data.date() == datetime.date.today():
                return datetime.datetime.strftime(data, "%d/%m/%Y %H:%M")
            return datetime.datetime.strftime(data, "%d/%m/%Y")
        return None

    def get_editais(self, obj):
        workflow = self.context.get("workflow", "").upper()
        editais = None
        if workflow == "CODAE_HOMOLOGADO":
            editais = ", ".join(
                obj.produto.vinculos.filter(suspenso=False).values_list(
                    "edital__numero", flat=True
                )
            )
        if workflow in ["CODAE_SUSPENDEU", "CODAE_AUTORIZOU_RECLAMACAO"]:
            editais = ", ".join(
                obj.produto.vinculos.filter(suspenso=True).values_list(
                    "edital__numero", flat=True
                )
            )
        return editais

    def get_produto_editais(self, obj):
        return obj.produto.vinculos.all().values_list("edital__numero", flat=True)

    class Meta:
        model = HomologacaoProduto
        fields = (
            "uuid",
            "nome_produto",
            "marca_produto",
            "fabricante_produto",
            "status",
            "id_externo",
            "log_mais_recente",
            "nome_usuario_log_de_reclamacao",
            "qtde_reclamacoes",
            "qtde_questionamentos",
            "tem_vinculo_produto_edital_suspenso",
            "data_edital_suspenso_mais_recente",
            "editais",
            "produto_editais",
            "tem_copia",
        )


class HomologacaoProdutoComLogsDetalhadosSerializer(serializers.ModelSerializer):
    produto = ProdutoSemAnexoSerializer()
    logs = LogSolicitacoesUsuarioComAnexosSerializer(many=True)
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = HomologacaoProduto
        fields = (
            "uuid",
            "produto",
            "status",
            "id_externo",
            "logs",
            "rastro_terceirizada",
            "pdf_gerado",
            "protocolo_analise_sensorial",
        )


class RespostaAnaliseSensorialSerializer(serializers.ModelSerializer):
    class Meta:
        model = RespostaAnaliseSensorial
        fields = (
            "uuid",
            "responsavel_produto",
            "registro_funcional",
            "id_externo",
            "data",
            "hora",
            "observacao",
            "criado_em",
        )


class HomologacaoRelatorioAnaliseSensorialSerializer(serializers.ModelSerializer):
    log_resposta_analise = serializers.SerializerMethodField()
    log_solicitacao_analise = serializers.SerializerMethodField()
    rastro_terceirizada = TerceirizadaSimplesSerializer()
    resposta_analise = serializers.SerializerMethodField()

    def get_resposta_analise(self, obj):
        return RespostaAnaliseSensorialSerializer(
            RespostaAnaliseSensorial.objects.filter(homologacao_produto=obj)
            .order_by("criado_em")
            .last()
        ).data

    def get_log_resposta_analise(self, obj):
        return LogSolicitacoesUsuarioSerializer(
            LogSolicitacoesUsuario.objects.filter(
                uuid_original=obj.uuid,
                status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_ANALISE_SENSORIAL,
            )
            .order_by("criado_em")
            .last()
        ).data

    def get_log_solicitacao_analise(self, obj):
        return LogSolicitacoesUsuarioSerializer(
            LogSolicitacoesUsuario.objects.filter(
                uuid_original=obj.uuid,
                status_evento=LogSolicitacoesUsuario.CODAE_PEDIU_ANALISE_SENSORIAL,
                criado_em__lte=obj.respostas_analise.last().criado_em,
            )
            .order_by("criado_em")
            .last()
        ).data

    class Meta:
        model = HomologacaoProduto
        fields = (
            "uuid",
            "status",
            "id_externo",
            "log_resposta_analise",
            "log_solicitacao_analise",
            "rastro_terceirizada",
            "protocolo_analise_sensorial",
            "resposta_analise",
        )


class ProdutoRelatorioAnaliseSensorialSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer()
    fabricante = FabricanteSerializer()
    id_externo = serializers.CharField()
    ultima_homologacao = HomologacaoRelatorioAnaliseSensorialSerializer()

    class Meta:
        model = Produto
        exclude = ("id",)


class HomologacaoListagemSerializer(serializers.ModelSerializer):
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = HomologacaoProduto
        fields = ("uuid", "status", "id_externo", "rastro_terceirizada", "criado_em")


class ProdutoListagemSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer()
    fabricante = FabricanteSerializer()
    id_externo = serializers.CharField()
    ultima_homologacao = HomologacaoListagemSerializer()
    vinculos_produto_edital_ativos = serializers.SerializerMethodField()
    vinculos_produto_edital_suspensos = serializers.SerializerMethodField()
    produto_edital_tipo_produto = serializers.SerializerMethodField()

    def get_vinculos_produto_edital_ativos(self, obj):
        editais = obj.vinculos.filter(suspenso=False)
        return ", ".join(editais.values_list("edital__numero", flat=True))

    def get_vinculos_produto_edital_suspensos(self, obj):
        editais = obj.vinculos.filter(suspenso=True)
        return ", ".join(editais.values_list("edital__numero", flat=True))

    def get_produto_edital_tipo_produto(self, obj):
        nome_edital = self.context.get("nome_edital")
        try:
            if nome_edital:
                produto_edital = ProdutoEdital.objects.get(
                    produto=obj, edital__numero=nome_edital
                )
                return produto_edital.tipo_produto
            return None
        except ProdutoEdital.DoesNotExist:
            return None

    class Meta:
        model = Produto
        exclude = ("id",)


class ProdutoEditalSerializer(serializers.ModelSerializer):
    marca = serializers.SerializerMethodField()
    fabricante = serializers.SerializerMethodField()
    produto = ProdutoSimplesSerializer()
    edital = EditalSerializer()
    suspenso_por = UsuarioSerializer()

    def get_marca(self, obj):
        return MarcaSerializer(obj.produto.marca).data

    def get_fabricante(self, obj):
        return FabricanteSerializer(obj.produto.fabricante).data

    class Meta:
        model = ProdutoEdital
        exclude = (
            "id",
            "criado_em",
        )


class UltimoLogRelatorioSituacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogSolicitacoesUsuario
        fields = ("criado_em",)


class HomologacaoRelatorioSituacaoSerializer(serializers.ModelSerializer):
    ultimo_log = UltimoLogRelatorioSituacaoSerializer()
    status_titulo = serializers.CharField(source="status.state.title")
    justificativa = serializers.SerializerMethodField()

    def get_justificativa(self, obj):
        if LogSolicitacoesUsuario.objects.filter(uuid_original=obj.uuid).exists():
            log_solicitacao = LogSolicitacoesUsuario.objects.filter(
                uuid_original=obj.uuid
            ).first()
            return log_solicitacao.justificativa
        return None

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related("ultimo_log")

        return queryset

    class Meta:
        model = HomologacaoProduto
        fields = ("ultimo_log", "status", "status_titulo", "justificativa")


class ProdutoRelatorioSituacaoSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer()
    fabricante = FabricanteSerializer()
    ultima_homologacao = HomologacaoRelatorioSituacaoSerializer()

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related("marca", "fabricante", "ultima_homogacao")

        return queryset

    class Meta:
        model = Produto
        fields = (
            "nome",
            "marca",
            "fabricante",
            "criado_em",
            "ultima_homologacao",
            "eh_para_alunos_com_dieta",
            "tem_aditivos_alergenicos",
        )


class EscolaSolicitacaoCadastroProdutoDietaSerializer(serializers.ModelSerializer):
    tipo_gestao = TipoGestaoSerializer()
    lote = serializers.CharField(source="lote.nome")
    diretoria_regional = DiretoriaRegionalSimplissimaSerializer()
    contato = ContatoSerializer()

    class Meta:
        model = Escola
        fields = ("tipo_gestao", "lote", "diretoria_regional", "contato", "nome")


class SolicitacaoCadastroProdutoDietaSimplesSerializer(serializers.ModelSerializer):
    status_title = serializers.CharField(source="status.state.title")

    class Meta:
        model = SolicitacaoCadastroProdutoDieta
        fields = (
            "uuid",
            "criado_em",
            "nome_produto",
            "marca_produto",
            "fabricante_produto",
            "status",
            "status_title",
            "data_previsao_cadastro",
        )


class SolicitacaoCadastroProdutoDietaSerializer(serializers.ModelSerializer):
    aluno = AlunoSimplesSerializer()
    escola = EscolaSolicitacaoCadastroProdutoDietaSerializer()
    status_title = serializers.CharField(source="status.state.title")

    class Meta:
        model = SolicitacaoCadastroProdutoDieta
        fields = (
            "uuid",
            "criado_em",
            "aluno",
            "escola",
            "nome_produto",
            "marca_produto",
            "fabricante_produto",
            "info_produto",
            "status",
            "status_title",
            "data_previsao_cadastro",
            "justificativa_previsao_cadastro",
        )


class SolicitacaoCadastroProdutoDietaConfirmarSerializer(
    SolicitacaoCadastroProdutoDietaSerializer
):
    data_previsao_cadastro = serializers.DateField(required=True)
    justificativa_previsao_cadastro = serializers.CharField(
        allow_blank=True, required=False
    )

    class Meta:
        model = SolicitacaoCadastroProdutoDieta
        fields = ("data_previsao_cadastro", "justificativa_previsao_cadastro")


class ReclamacaoDeProdutoRelatorioSerializer(serializers.ModelSerializer):
    escola = EscolaSimplissimaSerializer()
    status_titulo = serializers.CharField(source="status.state.title")
    logs = LogSolicitacoesSerializer(many=True)
    usuario = serializers.SerializerMethodField()
    anexos = serializers.SerializerMethodField()

    def get_anexos(self, obj):
        return AnexoLogSolicitacoesUsuarioSerializer(obj.anexos, many=True).data

    def get_usuario(self, obj):
        return UsuarioSerializer(
            Usuario.objects.filter(
                registro_funcional=obj.reclamante_registro_funcional
            ).first(),
        ).data

    class Meta:
        model = ReclamacaoDeProduto
        fields = (
            "uuid",
            "reclamante_registro_funcional",
            "logs",
            "reclamante_cargo",
            "reclamante_nome",
            "reclamacao",
            "escola",
            "usuario",
            "status",
            "status_titulo",
            "criado_em",
            "id_externo",
            "anexos",
        )


class HomologacaoReclamacaoSerializer(serializers.ModelSerializer):
    reclamacoes = ReclamacaoDeProdutoRelatorioSerializer(many=True)
    status_titulo = serializers.CharField(source="status.state.title")
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = HomologacaoProduto
        fields = (
            "id",
            "uuid",
            "status",
            "id_externo",
            "criado_em",
            "reclamacoes",
            "status_titulo",
            "rastro_terceirizada",
        )


class ProdutoReclamacaoSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer()
    fabricante = FabricanteSerializer()
    id_externo = serializers.CharField()
    qtde_questionamentos = serializers.IntegerField(default=None)
    ultima_homologacao = HomologacaoReclamacaoSerializer()

    class Meta:
        model = Produto
        fields = (
            "uuid",
            "nome",
            "marca",
            "fabricante",
            "id_externo",
            "ultima_homologacao",
            "criado_em",
            "qtde_questionamentos",
        )


class ReclamacoesUltimaHomologacaoHomologadosPorParametrosSerializer(
    serializers.ModelSerializer
):
    escola = EscolaSimplissimaSerializer()
    status_titulo = serializers.CharField(source="status.state.title")
    logs = serializers.SerializerMethodField()

    def get_logs(self, obj):
        return LogSolicitacoesUsuarioSerializer(
            LogSolicitacoesUsuario.objects.filter(uuid_original=obj.uuid).order_by(
                "criado_em"
            ),
            many=True,
        ).data

    class Meta:
        model = ReclamacaoDeProduto
        fields = (
            "logs",
            "id_externo",
            "status_titulo",
            "reclamante_nome",
            "reclamante_registro_funcional",
            "escola",
            "criado_em",
            "reclamacao",
            "uuid",
            "reclamante_cargo",
            "status_titulo",
        )


class UltimaHomologacaoHomologadosPorParametrosSerializer(serializers.ModelSerializer):
    reclamacoes = serializers.SerializerMethodField()

    def get_reclamacoes(self, obj):
        return ReclamacoesUltimaHomologacaoHomologadosPorParametrosSerializer(
            obj.reclamacoes.all().order_by("-criado_em"),
            context=self.context,
            many=True,
        ).data

    class Meta:
        model = HomologacaoProduto
        fields = ("uuid", "reclamacoes")


class ProdutoHomologadosPorParametrosSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer()
    ultima_homologacao = UltimaHomologacaoHomologadosPorParametrosSerializer()

    class Meta:
        model = Produto
        fields = (
            "nome",
            "marca",
            "eh_para_alunos_com_dieta",
            "ultima_homologacao",
            "criado_em",
        )


class HomologacaoProdutoSuspensoSerializer(serializers.ModelSerializer):
    ultimo_log = LogSolicitacoesUsuarioComAnexosSerializer()
    logs = LogSolicitacoesUsuarioComAnexosSerializer(many=True)

    class Meta:
        model = HomologacaoProduto
        fields = ("uuid", "ultimo_log", "logs")


class ProdutoSuspensoSerializer(ProdutoBaseSerializer):
    ultima_homologacao = HomologacaoProdutoSuspensoSerializer()
    vinculos_produto_edital = serializers.SerializerMethodField()

    def get_vinculos_produto_edital(self, obj):
        return ProdutoEditalSerializer(
            ProdutoEdital.objects.filter(produto=obj, suspenso=True), many=True
        ).data

    class Meta:
        model = Produto
        fields = (
            "id_externo",
            "nome",
            "marca",
            "fabricante",
            "eh_para_alunos_com_dieta",
            "ultima_homologacao",
            "criado_em",
            "vinculos_produto_edital",
        )


class VinculosProdutosEditalAtivosSerializer(ProdutoBaseSerializer):
    vinculos_produto_edital = serializers.SerializerMethodField()

    def get_vinculos_produto_edital(self, obj):
        return ProdutoEditalSerializer(
            ProdutoEdital.objects.filter(produto=obj, suspenso=False), many=True
        ).data

    class Meta:
        model = Produto
        fields = ("vinculos_produto_edital",)


class ItensCadastroSerializer(serializers.ModelSerializer):
    nome = serializers.SerializerMethodField()
    tipo_display = serializers.SerializerMethodField()

    def get_nome(self, obj):
        return obj.content_object.nome

    def get_tipo_display(self, obj):
        return obj.get_tipo_display()

    class Meta:
        model = ItemCadastro
        fields = ("uuid", "nome", "tipo", "tipo_display")


class ItensCadastroCreateSerializer(serializers.Serializer):
    nome = serializers.CharField(required=True, write_only=True)
    tipo = serializers.CharField(required=True)

    def create(self, validated_data):
        nome = validated_data["nome"]
        tipo = validated_data["tipo"]

        if (nome.upper(), tipo) in (
            (item.content_object.nome.upper(), item.tipo)
            for item in ItemCadastro.objects.all()
        ):
            raise serializers.ValidationError("Item já cadastrado.")

        try:
            item = ItemCadastro.criar(nome, tipo)
            return item
        except Exception:
            raise serializers.ValidationError("Erro ao criar ItemCadastro.")

    def update(self, instance, validated_data):  # noqa C901
        nome = validated_data["nome"]
        tipo = validated_data["tipo"]

        if (nome.upper(), tipo) in (
            (item.content_object.nome.upper(), item.tipo)
            for item in ItemCadastro.objects.all()
        ):
            raise serializers.ValidationError("Item já cadastrado.")

        try:
            if instance.tipo != tipo:
                modelo_antigo = instance.content_object
                modelo_novo = ItemCadastro.cria_modelo(nome, tipo)
                instance.tipo = tipo
                instance.content_object = modelo_novo
                instance.save()

                modelo_antigo.delete()
            else:
                modelo = instance.content_object
                modelo.nome = nome.upper()
                modelo.save()
        except Exception as e:
            raise serializers.ValidationError(f"Erro ao criar ItemCadastro. {str(e)}")
        return instance


class RelatorioProdutosSuspensosSerializer(serializers.ModelSerializer):
    marca = serializers.CharField(source="marca.nome")
    fabricante = serializers.CharField(source="fabricante.nome")
    edital = serializers.SerializerMethodField()
    data_cadastro = serializers.SerializerMethodField()

    def get_edital(self, obj):
        produto_edital = obj.vinculos.get(edital__numero=self.context["edital_numero"])
        return {
            "nome": produto_edital.edital.numero,
            "tipo": produto_edital.tipo_produto,
            "data_suspensao": produto_edital.datas_horas_vinculo.last().criado_em.strftime(
                "%d/%m/%Y"
            ),
        }

    def get_data_cadastro(self, obj):
        return obj.homologacao.logs.first().criado_em.strftime("%d/%m/%Y")

    class Meta:
        model = Produto
        fields = ("uuid", "nome", "marca", "fabricante", "edital", "data_cadastro")
