from rest_framework import serializers

from sme_sigpae_api.produto.utils.genericos import (
    changes_between,
    mudancas_para_justificativa_html,
)

from ....dados_comuns.constants import DEZ_MB
from ....dados_comuns.models import LogSolicitacoesUsuario
from ....dados_comuns.utils import (
    convert_base64_to_contentfile,
    update_instance_from_dict,
)
from ....dados_comuns.validators import deve_ter_extensao_valida
from ....dieta_especial.models import SolicitacaoDietaEspecial
from ....escola.models import Aluno, Escola
from ....terceirizada.models import Edital, Terceirizada
from ...models import (
    AnexoReclamacaoDeProduto,
    AnexoRespostaAnaliseSensorial,
    EmbalagemProduto,
    EspecificacaoProduto,
    Fabricante,
    HomologacaoProduto,
    ImagemDoProduto,
    InformacaoNutricional,
    InformacoesNutricionaisDoProduto,
    Marca,
    NomeDeProdutoEdital,
    Produto,
    ProdutoEdital,
    ProtocoloDeDietaEspecial,
    ReclamacaoDeProduto,
    RespostaAnaliseSensorial,
    SolicitacaoCadastroProdutoDieta,
    UnidadeMedida,
)


class ImagemDoProdutoSerializerCreate(serializers.ModelSerializer):
    arquivo = serializers.CharField()
    nome = serializers.CharField()

    def validate_nome(self, nome):
        deve_ter_extensao_valida(nome)
        return nome

    class Meta:
        model = ImagemDoProduto
        exclude = (
            "id",
            "produto",
        )


class InformacoesNutricionaisDoProdutoSerializerCreate(serializers.ModelSerializer):
    informacao_nutricional = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=InformacaoNutricional.objects.all()
    )

    quantidade_porcao = serializers.CharField(required=True)
    valor_diario = serializers.CharField(required=False)

    class Meta:
        model = InformacoesNutricionaisDoProduto
        exclude = (
            "id",
            "produto",
        )


class EspecificacaoProdutoCreateSerializer(serializers.ModelSerializer):
    unidade_de_medida = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=UnidadeMedida.objects.all(),
        allow_null=True,
    )
    embalagem_produto = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=EmbalagemProduto.objects.all(),
        allow_null=True,
    )

    class Meta:
        model = EspecificacaoProduto
        exclude = (
            "id",
            "produto",
        )


class ProdutoSerializerCreate(serializers.ModelSerializer):
    protocolos = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=ProtocoloDeDietaEspecial.objects.all(),
        many=True,
    )
    marca = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=Marca.objects.all(), allow_null=True
    )
    fabricante = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=Fabricante.objects.all(),
        allow_null=True,
    )

    imagens = ImagemDoProdutoSerializerCreate(many=True)
    informacoes_nutricionais = InformacoesNutricionaisDoProdutoSerializerCreate(
        many=True
    )
    cadastro_finalizado = serializers.BooleanField(required=False)
    cadastro_atualizado = serializers.BooleanField(required=False)
    especificacoes = EspecificacaoProdutoCreateSerializer(many=True)

    def create(self, validated_data):  # noqa C901
        validated_data["criado_por"] = self.context["request"].user
        imagens = validated_data.pop("imagens", [])
        informacoes_nutricionais = validated_data.pop("informacoes_nutricionais", [])
        cadastro_finalizado = validated_data.pop("cadastro_finalizado", False)
        especificacoes_produto = validated_data.pop("especificacoes", [])

        # duplicidade de produtos por causa da linha 112
        produto = Produto.objects.create(**validated_data)

        for imagem in imagens:
            data = convert_base64_to_contentfile(imagem.get("arquivo"))
            ImagemDoProduto.objects.create(
                produto=produto, arquivo=data, nome=imagem.get("nome", "")
            )

        for informacao in informacoes_nutricionais:
            InformacoesNutricionaisDoProduto.objects.create(
                produto=produto,
                informacao_nutricional=informacao.get("informacao_nutricional", ""),
                quantidade_porcao=informacao.get("quantidade_porcao", ""),
                valor_diario=informacao.get("valor_diario", ""),
            )

        for especificacao in especificacoes_produto:
            EspecificacaoProduto.objects.create(
                produto=produto,
                volume=especificacao.get("volume", ""),
                unidade_de_medida=especificacao.get("unidade_de_medida", ""),
                embalagem_produto=especificacao.get("embalagem_produto", ""),
            )

        try:
            homologacao = produto.homologacao
        except HomologacaoProduto.DoesNotExist:
            homologacao = HomologacaoProduto(
                rastro_terceirizada=self.context[
                    "request"
                ].user.vinculo_atual.instituicao,
                produto=produto,
                criado_por=self.context["request"].user,
            )
            homologacao.save()
        if cadastro_finalizado:
            homologacao.inicia_fluxo(user=self.context["request"].user)
        return produto

    def update(self, instance, validated_data):  # noqa C901
        if type(validated_data.get("marca")) == str:
            validated_data["marca"] = Marca.objects.get(
                uuid=validated_data.get("marca")
            )
        if type(validated_data.get("fabricante")) == str:
            validated_data["fabricante"] = Fabricante.objects.get(
                uuid=validated_data.get("fabricante")
            )
        for informacao in validated_data.get("informacoes_nutricionais", []):
            if type(informacao.get("informacao_nutricional")) == str:
                informacao["informacao_nutricional"] = (
                    InformacaoNutricional.objects.get(
                        uuid=informacao.get("informacao_nutricional")
                    )
                )
        for especificacao in validated_data.get("especificacoes", []):
            if type(especificacao.get("unidade_de_medida")) == str:
                especificacao["unidade_de_medida"] = UnidadeMedida.objects.get(
                    uuid=especificacao.get("unidade_de_medida")
                )
            if type(especificacao.get("embalagem_produto")) == str:
                especificacao["embalagem_produto"] = EmbalagemProduto.objects.get(
                    uuid=especificacao.get("embalagem_produto")
                )
        usuario = self.context["request"].user
        mudancas = changes_between(instance, validated_data, usuario)
        justificativa = mudancas_para_justificativa_html(
            mudancas, instance._meta.get_fields()
        )
        informacoes_nutricionais = validated_data.pop("informacoes_nutricionais", [])
        especificacoes_produto = validated_data.pop("especificacoes", [])
        imagens = validated_data.pop("imagens", [])

        update_instance_from_dict(instance, validated_data, save=True)

        instance.informacoes_nutricionais.all().delete()
        instance.especificacoes.all().delete()

        for imagem in imagens:
            if imagem.get("arquivo", "").startswith("http"):
                continue
            ImagemDoProduto.objects.update_or_create(
                produto=instance,
                nome=imagem.get("nome", ""),
                defaults={
                    "arquivo": convert_base64_to_contentfile(imagem.get("arquivo"))
                },
            )

        for informacao in informacoes_nutricionais:
            InformacoesNutricionaisDoProduto.objects.create(
                produto=instance,
                informacao_nutricional=informacao.get("informacao_nutricional", ""),
                quantidade_porcao=informacao.get("quantidade_porcao", ""),
                valor_diario=informacao.get("valor_diario", ""),
            )

        for especificacao in especificacoes_produto:
            EspecificacaoProduto.objects.create(
                produto=instance,
                volume=especificacao.get("volume", ""),
                unidade_de_medida=especificacao.get("unidade_de_medida", ""),
                embalagem_produto=especificacao.get("embalagem_produto", ""),
            )

        status_validos = [
            "CODAE_NAO_HOMOLOGADO",
            "CODAE_HOMOLOGADO",
            "CODAE_SUSPENDEU",
            "TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO",
            "CODAE_QUESTIONADO",
        ]

        usuario = self.context["request"].user
        if (
            validated_data.get("cadastro_finalizado", False)
            or instance.homologacao.status in status_validos
        ):
            homologacao = instance.homologacao
            homologacao.inicia_fluxo(user=usuario, justificativa=justificativa)

        instance.save()
        return instance

    class Meta:
        model = Produto
        exclude = (
            "id",
            "criado_por",
            "ativo",
        )


class AnexoCreateSerializer(serializers.Serializer):
    base64 = serializers.CharField(max_length=DEZ_MB, write_only=True)
    nome = serializers.CharField(max_length=255)


class ReclamacaoDeProdutoSerializerCreate(serializers.ModelSerializer):
    anexos = AnexoCreateSerializer(many=True, required=False)
    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Escola.objects.all()
    )

    def create(self, validated_data):  # noqa C901
        anexos = validated_data.pop("anexos", [])

        reclamacao = ReclamacaoDeProduto.objects.create(**validated_data)

        for anexo in anexos:
            arquivo = convert_base64_to_contentfile(anexo.pop("base64"))
            AnexoReclamacaoDeProduto.objects.create(
                reclamacao_de_produto=reclamacao, arquivo=arquivo, nome=anexo["nome"]
            )

        return reclamacao

    class Meta:
        model = ReclamacaoDeProduto
        exclude = ("id", "uuid", "criado_em")


class RespostaAnaliseSensorialSearilzerCreate(serializers.ModelSerializer):
    homologacao_produto = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=HomologacaoProduto.objects.all()
    )
    data = serializers.DateField()
    hora = serializers.TimeField()
    anexos = AnexoCreateSerializer(many=True, required=False)

    def create(self, validated_data):
        anexos = validated_data.pop("anexos", [])
        resposta = RespostaAnaliseSensorial.objects.create(**validated_data)

        for anexo in anexos:
            arquivo = convert_base64_to_contentfile(anexo.pop("base64"))
            AnexoRespostaAnaliseSensorial.objects.create(
                resposta_analise_sensorial=resposta, arquivo=arquivo, nome=anexo["nome"]
            )

        return resposta

    class Meta:
        model = RespostaAnaliseSensorial
        exclude = ("id", "uuid", "criado_por", "criado_em")


class SolicitacaoCadastroProdutoDietaSerializerCreate(serializers.ModelSerializer):
    aluno = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Aluno.objects.all()
    )
    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Escola.objects.all()
    )
    terceirizada = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Terceirizada.objects.all()
    )

    solicitacao_dieta_especial = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=SolicitacaoDietaEspecial.objects.all(),
    )

    class Meta:
        model = SolicitacaoCadastroProdutoDieta
        exclude = ("id", "uuid", "criado_por", "criado_em")

    def create(self, validated_data):
        usuario = self.context["request"].user
        solicitacao = SolicitacaoCadastroProdutoDieta.objects.create(
            **validated_data, criado_por=usuario
        )
        solicitacao._envia_email_solicitacao_realizada()
        return solicitacao


class ProdutoEditalCreateSerializer(serializers.Serializer):
    editais_origem_selecionados = serializers.ListField(required=False)
    editais_destino_selecionados = serializers.ListField(required=False)
    produtos_editais = serializers.ListField(required=False)
    tipo_produto = serializers.CharField(required=False)
    outras_informacoes = serializers.CharField(required=False)

    def checa_se_existe_edital_ou_se_altera_tipo_produto(
        self,
        editais,
        produto_edital,
        tipo_produto,
        outras_informacoes,
        editais_vinculados,
        lista_produtos_editais,
        editais_com_tipos_alterados,
        outro_tipo_produto,
    ):
        for edital in editais:
            if not ProdutoEdital.objects.filter(
                produto=produto_edital.produto, edital=edital
            ).exists():
                editais_vinculados.append(edital.numero)
                lista_produtos_editais.append(
                    ProdutoEdital(
                        produto=produto_edital.produto,
                        edital=edital,
                        tipo_produto=tipo_produto,
                        outras_informacoes=outras_informacoes,
                    )
                )
            elif ProdutoEdital.objects.filter(
                produto=produto_edital.produto,
                edital=edital,
                tipo_produto=outro_tipo_produto,
            ).exists():
                editais_com_tipos_alterados.append(edital.numero)

    def cria_vinculos_inexistentes(
        self,
        editais_vinculados,
        produto_edital,
        tipo_produto,
        outras_informacoes,
        homologacao_produto,
    ):
        if editais_vinculados:
            string_editais_vinculados = ", ".join(editais_vinculados)
            justificativa = "<p>Nome do Produto:</p>"
            justificativa += f"<p>{produto_edital.produto.nome}</p>"
            justificativa += "<br><p>Editais que foram vinculados:</p>"
            justificativa += f"<p>{string_editais_vinculados}</p>"
            justificativa += (
                "<br><p>Tipo de Produto em que o produto foi vinculado:</p>"
            )
            justificativa += f"<p>{tipo_produto}</p>"
            justificativa += "<br><p>Outras informações:</p>"
            justificativa += f"<p>{outras_informacoes}</p>"
            homologacao_produto.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.VINCULO_DO_EDITAL_AO_PRODUTO,
                usuario=self.context["request"].user,
                justificativa=justificativa,
            )

    def altera_vinculos_tipo_produto(
        self,
        editais_com_tipos_alterados,
        produto_edital,
        tipo_produto,
        outras_informacoes,
        homologacao_produto,
        outro_tipo_produto,
    ):
        if editais_com_tipos_alterados:
            ProdutoEdital.objects.filter(
                produto=produto_edital.produto,
                edital__numero__in=editais_com_tipos_alterados,
                tipo_produto=outro_tipo_produto,
            ).update(tipo_produto=tipo_produto)
            string_editais_alterados = ", ".join(editais_com_tipos_alterados)
            justificativa = "<p>Nome do Produto:</p>"
            justificativa += f"<p>{produto_edital.produto.nome}</p>"
            justificativa += "<br><p>Editais que foram vinculados:</p>"
            justificativa += f"<p>{string_editais_alterados}</p>"
            justificativa += "<br><p>Tipo de Produto alterado para:</p>"
            justificativa += f"<p>{tipo_produto}</p>"
            justificativa += "<br><p>Outras informações:</p>"
            justificativa += f"<p>{outras_informacoes}</p>"
            homologacao_produto.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.VINCULO_DO_EDITAL_AO_PRODUTO,
                usuario=self.context["request"].user,
                justificativa=justificativa,
            )

    def create(self, validated_data):
        editais_destino_selecionados = validated_data.get(
            "editais_destino_selecionados", []
        )
        produtos_editais = validated_data.get("produtos_editais", [])
        outras_informacoes = validated_data.get("outras_informacoes", "")
        tipo_produto = validated_data.get("tipo_produto", "")
        outro_tipo_produto = (
            "Comum" if tipo_produto == "Dieta especial" else "Dieta especial"
        )

        produtos = ProdutoEdital.objects.filter(uuid__in=produtos_editais)
        editais = Edital.objects.filter(uuid__in=editais_destino_selecionados)
        lista_produtos_editais = []
        try:
            for produto_edital in produtos:
                homologacao_produto = produto_edital.produto.homologacao
                editais_vinculados = []
                editais_com_tipos_alterados = []
                self.checa_se_existe_edital_ou_se_altera_tipo_produto(
                    editais,
                    produto_edital,
                    tipo_produto,
                    outras_informacoes,
                    editais_vinculados,
                    lista_produtos_editais,
                    editais_com_tipos_alterados,
                    outro_tipo_produto,
                )
                self.cria_vinculos_inexistentes(
                    editais_vinculados,
                    produto_edital,
                    tipo_produto,
                    outras_informacoes,
                    homologacao_produto,
                )
                self.altera_vinculos_tipo_produto(
                    editais_com_tipos_alterados,
                    produto_edital,
                    tipo_produto,
                    outras_informacoes,
                    homologacao_produto,
                    outro_tipo_produto,
                )

            resultado = ProdutoEdital.objects.bulk_create(lista_produtos_editais)
            for produto_edital in lista_produtos_editais:
                produto_edital.criar_data_hora_vinculo()
            return resultado
        except Exception as e:
            raise serializers.ValidationError(
                f"Erro ao criar Produto Proviniente do Edital.: {str(e)}"
            )

    class Meta:
        model = SolicitacaoCadastroProdutoDieta
        fields = (
            "editais_origem_selecionados",
            "editais_destino_selecionados",
            "produtos_editais",
            "outras_informacoes",
            "tipo_produto",
        )


class CadastroProdutosEditalCreateSerializer(serializers.Serializer):
    nome = serializers.CharField(required=True, write_only=True)
    ativo = serializers.CharField(required=True)
    tipo_produto = serializers.ChoiceField(
        choices=NomeDeProdutoEdital.TIPO_PRODUTO_CHOICES, required=False
    )

    def create(self, validated_data):
        nome = validated_data["nome"]
        status = validated_data.pop("ativo")
        tipo_produto = validated_data.pop("tipo_produto", None)
        if not tipo_produto:
            tipo_produto = NomeDeProdutoEdital.TERCEIRIZADA
        ativo = False if status == "Inativo" else True
        validated_data["criado_por"] = self.context["request"].user
        lista_produtos = NomeDeProdutoEdital.objects.filter(tipo_produto=tipo_produto)

        if nome.upper() in (produto.nome.upper() for produto in lista_produtos):
            raise serializers.ValidationError("Item já cadastrado.")
        try:
            produto = NomeDeProdutoEdital(
                nome=nome,
                ativo=ativo,
                tipo_produto=tipo_produto,
                criado_por=self.context["request"].user,
            )
            produto.save()
            return produto
        except Exception:
            raise serializers.ValidationError(
                "Erro ao criar Produto Proviniente do Edital."
            )

    def update(self, instance, validated_data):  # noqa C901
        nome = validated_data["nome"]
        status = validated_data.pop("ativo")
        ativo = False if status == "Inativo" else True
        lista_produtos = NomeDeProdutoEdital.objects.filter(
            tipo_produto=instance.tipo_produto
        )

        if (nome.upper(), ativo) in (
            (produto.nome.upper(), produto.ativo) for produto in lista_produtos.exclude(uuid=instance.uuid)
        ):
            raise serializers.ValidationError("Item já cadastrado.")

        try:
            instance.nome = nome.upper()
            instance.ativo = ativo
            instance.save()
        except Exception as e:
            raise serializers.ValidationError(
                f"Erro ao editar Produto Proviniente do Edital. {str(e)}"
            )
        return instance
