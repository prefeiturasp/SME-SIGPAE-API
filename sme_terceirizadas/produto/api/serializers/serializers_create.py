from rest_framework import serializers

from ....dados_comuns.constants import DEZ_MB
from ....dados_comuns.utils import convert_base64_to_contentfile, update_instance_from_dict
from ....dados_comuns.validators import deve_ter_extensao_valida
from ....dieta_especial.models import SolicitacaoDietaEspecial
from ....escola.models import Aluno, Escola
from ....terceirizada.models import Terceirizada
from ...models import (
    AnexoReclamacaoDeProduto,
    AnexoRespostaAnaliseSensorial,
    Fabricante,
    HomologacaoDoProduto,
    ImagemDoProduto,
    InformacaoNutricional,
    InformacoesNutricionaisDoProduto,
    Marca,
    Produto,
    ProtocoloDeDietaEspecial,
    ReclamacaoDeProduto,
    RespostaAnaliseSensorial,
    SolicitacaoCadastroProdutoDieta
)
from ...utils import changes_between, mudancas_para_justificativa_html


class ImagemDoProdutoSerializerCreate(serializers.ModelSerializer):
    arquivo = serializers.CharField()
    nome = serializers.CharField()

    def validate_nome(self, nome):
        deve_ter_extensao_valida(nome)
        return nome

    class Meta:
        model = ImagemDoProduto
        exclude = ('id', 'produto',)


class InformacoesNutricionaisDoProdutoSerializerCreate(serializers.ModelSerializer):
    informacao_nutricional = serializers.SlugRelatedField(
        slug_field='uuid',
        required=True,
        queryset=InformacaoNutricional.objects.all()
    )

    quantidade_porcao = serializers.CharField(required=True)
    valor_diario = serializers.CharField(required=False)

    class Meta:
        model = InformacoesNutricionaisDoProduto
        exclude = ('id', 'produto',)


class ProdutoSerializerCreate(serializers.ModelSerializer):
    protocolos = serializers.SlugRelatedField(
        slug_field='uuid',
        required=True,
        queryset=ProtocoloDeDietaEspecial.objects.all(),
        many=True
    )
    marca = serializers.SlugRelatedField(
        slug_field='uuid',
        required=True,
        queryset=Marca.objects.all()
    )
    fabricante = serializers.SlugRelatedField(
        slug_field='uuid',
        required=True,
        queryset=Fabricante.objects.all()
    )

    imagens = ImagemDoProdutoSerializerCreate(many=True)
    informacoes_nutricionais = InformacoesNutricionaisDoProdutoSerializerCreate(many=True)
    cadastro_finalizado = serializers.BooleanField(required=False)
    cadastro_atualizado = serializers.BooleanField(required=False)

    def create(self, validated_data):  # noqa C901
        validated_data['criado_por'] = self.context['request'].user
        imagens = validated_data.pop('imagens', [])
        protocolos = validated_data.pop('protocolos', [])
        informacoes_nutricionais = validated_data.pop('informacoes_nutricionais', [])
        cadastro_finalizado = validated_data.pop('cadastro_finalizado', False)

        produto = Produto.objects.create(**validated_data)

        for imagem in imagens:
            data = convert_base64_to_contentfile(imagem.get('arquivo'))
            ImagemDoProduto.objects.create(
                produto=produto, arquivo=data, nome=imagem.get('nome', '')
            )

        for informacao in informacoes_nutricionais:
            InformacoesNutricionaisDoProduto.objects.create(
                produto=produto,
                informacao_nutricional=informacao.get('informacao_nutricional', ''),
                quantidade_porcao=informacao.get('quantidade_porcao', ''),
                valor_diario=informacao.get('valor_diario', '')
            )

        produto.protocolos.set(protocolos)
        if produto.homologacoes.exists():
            homologacao = produto.homologacoes.first()
        else:
            homologacao = HomologacaoDoProduto(
                rastro_terceirizada=self.context['request'].user.vinculo_atual.instituicao,
                produto=produto,
                criado_por=self.context['request'].user
            )
            homologacao.save()
        if cadastro_finalizado:
            homologacao.inicia_fluxo(user=self.context['request'].user)
        return produto

    def update(self, instance, validated_data):  # noqa C901
        mudancas = changes_between(instance, validated_data)
        justificativa = mudancas_para_justificativa_html(mudancas, instance._meta.get_fields())
        imagens = validated_data.pop('imagens', [])
        protocolos = validated_data.pop('protocolos', [])
        informacoes_nutricionais = validated_data.pop('informacoes_nutricionais', [])

        update_instance_from_dict(instance, validated_data, save=True)

        instance.informacoes_nutricionais.all().delete()

        if 'imagens' in mudancas and 'exclusoes' in mudancas['imagens']:
            for imagem in mudancas['imagens']['exclusoes']:
                imagem.delete()

        for imagem in imagens:
            if imagem.get('arquivo', '').startswith('http'):
                continue
            ImagemDoProduto.objects.update_or_create(
                produto=instance,
                nome=imagem.get('nome', ''),
                defaults={
                    'arquivo': convert_base64_to_contentfile(imagem.get('arquivo'))
                }
            )

        for informacao in informacoes_nutricionais:
            InformacoesNutricionaisDoProduto.objects.create(
                produto=instance,
                informacao_nutricional=informacao.get('informacao_nutricional', ''),
                quantidade_porcao=informacao.get('quantidade_porcao', ''),
                valor_diario=informacao.get('valor_diario', '')
            )

        instance.protocolos.set([])
        instance.protocolos.set(protocolos)
        usuario = self.context['request'].user
        if validated_data.get('cadastro_atualizado', False):
            ultima_homologacao = instance.homologacoes.first()
            ultima_homologacao.inativa_homologacao(user=usuario)
            homologacao = HomologacaoDoProduto(
                rastro_terceirizada=usuario.vinculo_atual.instituicao,
                produto=instance,
                criado_por=usuario
            )
            homologacao.save()
            homologacao.inicia_fluxo(user=usuario, justificativa=justificativa)
        if validated_data.get('cadastro_finalizado', False):
            homologacao = instance.homologacoes.first()
            homologacao.inicia_fluxo(user=usuario, justificativa=justificativa)
        return instance

    class Meta:
        model = Produto
        exclude = ('id', 'criado_por', 'ativo',)


class AnexoCreateSerializer(serializers.Serializer):
    base64 = serializers.CharField(max_length=DEZ_MB, write_only=True)
    nome = serializers.CharField(max_length=255)


class ReclamacaoDeProdutoSerializerCreate(serializers.ModelSerializer):
    anexos = AnexoCreateSerializer(many=True, required=False)
    escola = serializers.SlugRelatedField(
        slug_field='uuid',
        required=True,
        queryset=Escola.objects.all()
    )

    def create(self, validated_data):  # noqa C901
        anexos = validated_data.pop('anexos', [])

        reclamacao = ReclamacaoDeProduto.objects.create(**validated_data)

        for anexo in anexos:
            arquivo = convert_base64_to_contentfile(anexo.pop('base64'))
            AnexoReclamacaoDeProduto.objects.create(
                reclamacao_de_produto=reclamacao,
                arquivo=arquivo,
                nome=anexo['nome']
            )

        return reclamacao

    class Meta:
        model = ReclamacaoDeProduto
        exclude = ('id', 'uuid', 'criado_em')


class RespostaAnaliseSensorialSearilzerCreate(serializers.ModelSerializer):
    homologacao_de_produto = serializers.SlugRelatedField(
        slug_field='uuid',
        required=True,
        queryset=HomologacaoDoProduto.objects.all()
    )
    data = serializers.DateField()
    hora = serializers.TimeField()
    anexos = AnexoCreateSerializer(many=True, required=False)

    def create(self, validated_data):
        anexos = validated_data.pop('anexos', [])
        resposta = RespostaAnaliseSensorial.objects.create(**validated_data)

        for anexo in anexos:
            arquivo = convert_base64_to_contentfile(anexo.pop('base64'))
            AnexoRespostaAnaliseSensorial.objects.create(
                resposta_analise_sensorial=resposta,
                arquivo=arquivo,
                nome=anexo['nome']
            )

        return resposta

    class Meta:
        model = RespostaAnaliseSensorial
        exclude = ('id', 'uuid', 'criado_por', 'criado_em')


class SolicitacaoCadastroProdutoDietaSerializerCreate(serializers.ModelSerializer):

    aluno = serializers.SlugRelatedField(
        slug_field='uuid',
        required=True,
        queryset=Aluno.objects.all()
    )
    escola = serializers.SlugRelatedField(
        slug_field='uuid',
        required=True,
        queryset=Escola.objects.all()
    )
    terceirizada = serializers.SlugRelatedField(
        slug_field='uuid',
        required=True,
        queryset=Terceirizada.objects.all()
    )

    solicitacao_dieta_especial = serializers.SlugRelatedField(
        slug_field='uuid',
        required=True,
        queryset=SolicitacaoDietaEspecial.objects.all()
    )

    class Meta:
        model = SolicitacaoCadastroProdutoDieta
        exclude = ('id', 'uuid', 'criado_por', 'criado_em')

    def create(self, validated_data):
        usuario = self.context['request'].user
        solicitacao = SolicitacaoCadastroProdutoDieta.objects.create(**validated_data, criado_por=usuario)
        solicitacao._envia_email_solicitacao_realizada()
        return solicitacao
