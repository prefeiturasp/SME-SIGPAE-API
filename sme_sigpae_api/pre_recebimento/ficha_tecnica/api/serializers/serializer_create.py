from rest_framework import serializers

from sme_sigpae_api.dados_comuns.utils import (
    update_instance_from_dict,
)
from sme_sigpae_api.pre_recebimento.base.models import (
    UnidadeMedida,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import (
    AnaliseFichaTecnica,
    FabricanteFichaTecnica,
    FichaTecnicaDoProduto,
    InformacoesNutricionaisFichaTecnica,
)
from sme_sigpae_api.produto.models import Fabricante, Marca, NomeDeProdutoEdital
from sme_sigpae_api.terceirizada.models import Terceirizada

from ..helpers import (
    atualiza_ficha_tecnica,
    cria_ficha_tecnica,
    gerar_nova_analise_ficha_tecnica,
    limpar_campos_dependentes_ficha_tecnica,
)
from ..validators import (
    ServiceValidacaoCorrecaoFichaTecnica,
    valida_campos_dependentes_ficha_tecnica,
    valida_campos_nao_pereciveis_ficha_tecnica,
    valida_campos_pereciveis_ficha_tecnica,
    valida_ingredientes_alergenicos_ficha_tecnica,
)


class InformacoesNutricionaisFichaTecnicaCreateSerializer(serializers.ModelSerializer):
    informacao_nutricional = serializers.UUIDField()

    class Meta:
        model = InformacoesNutricionaisFichaTecnica
        fields = (
            "informacao_nutricional",
            "quantidade_por_100g",
            "quantidade_porcao",
            "valor_diario",
        )


class FabricanteFichaTecnicaCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        self.fabricante_opcional = kwargs.pop("fabricante_opcional", False)
        super().__init__(*args, **kwargs)

        self.fields["fabricante"] = serializers.SlugRelatedField(
            slug_field="uuid",
            required=not self.fabricante_opcional,
            allow_null=self.fabricante_opcional,
            queryset=Fabricante.objects.all(),
        )

    cnpj = serializers.CharField(required=False, allow_blank=True)
    cep = serializers.CharField(required=False, allow_blank=True)
    endereco = serializers.CharField(required=False, allow_blank=True)
    numero = serializers.CharField(required=False, allow_blank=True)
    complemento = serializers.CharField(required=False, allow_blank=True)
    bairro = serializers.CharField(required=False, allow_blank=True)
    cidade = serializers.CharField(required=False, allow_blank=True)
    estado = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)
    telefone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = FabricanteFichaTecnica
        fields = (
            "fabricante",
            "cnpj",
            "cep",
            "endereco",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "estado",
            "email",
            "telefone",
        )


class FichaTecnicaRascunhoSerializer(serializers.ModelSerializer):
    produto = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=NomeDeProdutoEdital.objects.all(),
    )
    marca = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=Marca.objects.all(),
    )
    categoria = serializers.ChoiceField(
        choices=FichaTecnicaDoProduto.CATEGORIA_CHOICES,
        required=True,
    )
    pregao_chamada_publica = serializers.CharField(required=True)
    empresa = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=Terceirizada.objects.all(),
    )
    fabricante = FabricanteFichaTecnicaCreateSerializer(required=False)
    envasador_distribuidor = FabricanteFichaTecnicaCreateSerializer(required=False)
    prazo_validade = serializers.CharField(required=True, allow_blank=True)
    numero_registro = serializers.CharField(required=False, allow_blank=True)
    agroecologico = serializers.BooleanField(required=False)
    organico = serializers.BooleanField(required=False)
    mecanismo_controle = serializers.ChoiceField(
        choices=FichaTecnicaDoProduto.MECANISMO_CONTROLE_CHOICES,
        required=False,
        allow_blank=True,
    )
    componentes_produto = serializers.CharField(required=True, allow_blank=True)
    alergenicos = serializers.BooleanField(required=False)
    ingredientes_alergenicos = serializers.CharField(required=True, allow_blank=True)
    gluten = serializers.BooleanField(required=False)
    lactose = serializers.BooleanField(required=False)
    lactose_detalhe = serializers.CharField(required=True, allow_blank=True)
    porcao = serializers.CharField(required=False, allow_blank=True)
    unidade_medida_porcao = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=UnidadeMedida.objects.all(),
        allow_null=True,
    )
    valor_unidade_caseira = serializers.CharField(required=False, allow_blank=True)
    unidade_medida_caseira = serializers.CharField(required=True, allow_blank=True)
    informacoes_nutricionais = InformacoesNutricionaisFichaTecnicaCreateSerializer(
        many=True
    )
    prazo_validade_descongelamento = serializers.CharField(
        required=False, allow_blank=True
    )
    condicoes_de_conservacao = serializers.CharField(required=True, allow_blank=True)
    temperatura_congelamento = serializers.FloatField(required=False, allow_null=True)
    temperatura_veiculo = serializers.FloatField(required=False, allow_null=True)
    condicoes_de_transporte = serializers.CharField(required=False, allow_blank=True)
    embalagem_primaria = serializers.CharField(required=True, allow_blank=True)
    embalagem_secundaria = serializers.CharField(required=True, allow_blank=True)
    embalagens_de_acordo_com_anexo = serializers.BooleanField(required=False)
    material_embalagem_primaria = serializers.CharField(required=True, allow_blank=True)
    produto_eh_liquido = serializers.BooleanField(required=False)
    volume_embalagem_primaria = serializers.FloatField(required=False, allow_null=True)
    unidade_medida_volume_primaria = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=UnidadeMedida.objects.all(),
        allow_null=True,
    )
    peso_liquido_embalagem_primaria = serializers.FloatField(
        required=False, allow_null=True
    )
    unidade_medida_primaria = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=UnidadeMedida.objects.all(),
        allow_null=True,
    )
    peso_liquido_embalagem_secundaria = serializers.FloatField(
        required=False, allow_null=True
    )
    unidade_medida_secundaria = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=UnidadeMedida.objects.all(),
        allow_null=True,
    )
    peso_embalagem_primaria_vazia = serializers.FloatField(
        required=False, allow_null=True
    )
    unidade_medida_primaria_vazia = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=UnidadeMedida.objects.all(),
        allow_null=True,
    )
    peso_embalagem_secundaria_vazia = serializers.FloatField(
        required=False, allow_null=True
    )
    unidade_medida_secundaria_vazia = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=UnidadeMedida.objects.all(),
        allow_null=True,
    )
    variacao_percentual = serializers.FloatField(required=False, allow_null=True)
    sistema_vedacao_embalagem_secundaria = serializers.CharField(
        required=True, allow_blank=True
    )
    rotulo_legivel = serializers.BooleanField(required=False)
    nome_responsavel_tecnico = serializers.CharField(required=True, allow_blank=True)
    habilitacao = serializers.CharField(required=True, allow_blank=True)
    numero_registro_orgao = serializers.CharField(required=True, allow_blank=True)
    arquivo = serializers.CharField(required=True, allow_blank=True)
    modo_de_preparo = serializers.CharField(required=True, allow_blank=True)
    informacoes_adicionais = serializers.CharField(required=True, allow_blank=True)

    def validate_arquivo(self, value):
        if value and "pdf" not in value:
            raise serializers.ValidationError("Arquivo deve ser um PDF.")
        return value

    def create(self, validated_data):
        return cria_ficha_tecnica(validated_data)

    def update(self, instance, validated_data):
        return atualiza_ficha_tecnica(instance, validated_data)

    class Meta:
        model = FichaTecnicaDoProduto
        exclude = ("id",)


class FichaTecnicaCreateSerializer(serializers.ModelSerializer):
    produto = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=NomeDeProdutoEdital.objects.all(),
    )
    marca = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=Marca.objects.all(),
    )
    categoria = serializers.ChoiceField(
        choices=FichaTecnicaDoProduto.CATEGORIA_CHOICES,
        required=True,
    )
    pregao_chamada_publica = serializers.CharField(required=True)
    empresa = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=Terceirizada.objects.all(),
    )
    fabricante = FabricanteFichaTecnicaCreateSerializer(required=False)
    envasador_distribuidor = FabricanteFichaTecnicaCreateSerializer(required=False)
    mecanismo_controle = serializers.ChoiceField(
        choices=FichaTecnicaDoProduto.MECANISMO_CONTROLE_CHOICES,
        required=False,
    )
    componentes_produto = serializers.CharField(required=True)
    alergenicos = serializers.BooleanField(required=True)
    ingredientes_alergenicos = serializers.CharField(required=False, allow_blank=True)
    gluten = serializers.BooleanField(required=True)
    lactose = serializers.BooleanField(required=True)
    lactose_detalhe = serializers.CharField(required=False, allow_blank=True)
    porcao = serializers.CharField(required=True)
    unidade_medida_porcao = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=UnidadeMedida.objects.all(),
    )
    valor_unidade_caseira = serializers.CharField(required=True)
    unidade_medida_caseira = serializers.CharField(required=True)
    informacoes_nutricionais = InformacoesNutricionaisFichaTecnicaCreateSerializer(
        many=True
    )
    prazo_validade_descongelamento = serializers.CharField(required=False)
    condicoes_de_conservacao = serializers.CharField(required=True)
    temperatura_congelamento = serializers.FloatField(required=False, allow_null=True)
    temperatura_veiculo = serializers.FloatField(required=False, allow_null=True)
    condicoes_de_transporte = serializers.CharField(required=False)
    embalagem_primaria = serializers.CharField(required=True)
    embalagem_secundaria = serializers.CharField(required=True)
    embalagens_de_acordo_com_anexo = serializers.BooleanField(required=True)
    material_embalagem_primaria = serializers.CharField(required=True)
    produto_eh_liquido = serializers.BooleanField(required=False)
    volume_embalagem_primaria = serializers.FloatField(required=False, allow_null=True)
    unidade_medida_volume_primaria = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=UnidadeMedida.objects.all(),
        allow_null=True,
    )
    peso_liquido_embalagem_primaria = serializers.FloatField(required=True)
    unidade_medida_primaria = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=UnidadeMedida.objects.all(),
    )
    peso_liquido_embalagem_secundaria = serializers.FloatField(required=True)
    unidade_medida_secundaria = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=UnidadeMedida.objects.all(),
    )
    peso_embalagem_primaria_vazia = serializers.FloatField(required=True)
    unidade_medida_primaria_vazia = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=UnidadeMedida.objects.all(),
    )
    peso_embalagem_secundaria_vazia = serializers.FloatField(required=True)
    unidade_medida_secundaria_vazia = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=UnidadeMedida.objects.all(),
    )
    variacao_percentual = serializers.FloatField(required=False)
    sistema_vedacao_embalagem_secundaria = serializers.CharField(required=True)
    rotulo_legivel = serializers.BooleanField(required=True)
    nome_responsavel_tecnico = serializers.CharField(required=True)
    habilitacao = serializers.CharField(required=True)
    numero_registro_orgao = serializers.CharField(required=True)
    arquivo = serializers.CharField(required=True)
    modo_de_preparo = serializers.CharField(required=False, allow_blank=True)
    informacoes_adicionais = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs.get("categoria") == FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS:
            valida_campos_pereciveis_ficha_tecnica(attrs)
        else:
            valida_campos_nao_pereciveis_ficha_tecnica(attrs)

        valida_campos_dependentes_ficha_tecnica(attrs)

        return attrs

    def validate_embalagens_de_acordo_com_anexo(self, value):
        if not value:
            raise serializers.ValidationError(
                "Checkbox indicando que as embalagens estão de acordo com o Anexo I precisa ser marcado."
            )
        return value

    def validate_rotulo_legivel(self, value):
        if not value:
            raise serializers.ValidationError(
                "Checkbox indicando que o rótulo contém as informações solicitadas no Anexo I precisa ser marcado."
            )
        return value

    def validate_arquivo(self, value):
        if value and "pdf" not in value:
            raise serializers.ValidationError("Arquivo deve ser um PDF.")
        return value

    def create(self, validated_data):
        instance = cria_ficha_tecnica(validated_data)

        user = self.context["request"].user
        instance.inicia_fluxo(user=user)

        return instance

    def update(self, instance, validated_data):
        instance = atualiza_ficha_tecnica(instance, validated_data)

        user = self.context["request"].user
        instance.inicia_fluxo(user=user)

        return instance

    class Meta:
        model = FichaTecnicaDoProduto
        exclude = ("id",)


class AnaliseFichaTecnicaRascunhoSerializer(serializers.ModelSerializer):
    criado_por = serializers.SlugRelatedField(
        slug_field="uuid",
        read_only=True,
    )
    ficha_tecnica = serializers.SlugRelatedField(
        slug_field="uuid",
        read_only=True,
    )
    fabricante_envasador_conferido = serializers.BooleanField(
        required=False,
        allow_null=True,
    )
    fabricante_envasador_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    detalhes_produto_conferido = serializers.BooleanField(
        required=False,
        allow_null=True,
    )
    detalhes_produto_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    informacoes_nutricionais_conferido = serializers.BooleanField(
        required=False,
        allow_null=True,
    )
    informacoes_nutricionais_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    conservacao_conferido = serializers.BooleanField(
        required=False,
        allow_null=True,
    )
    conservacao_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    temperatura_e_transporte_conferido = serializers.BooleanField(
        required=False,
        allow_null=True,
    )
    temperatura_e_transporte_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    armazenamento_conferido = serializers.BooleanField(
        required=False,
        allow_null=True,
    )
    armazenamento_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    embalagem_e_rotulagem_conferido = serializers.BooleanField(
        required=False,
        allow_null=True,
    )
    embalagem_e_rotulagem_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    responsavel_tecnico_conferido = serializers.BooleanField(
        required=False,
        allow_null=True,
    )
    responsavel_tecnico_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    modo_preparo_conferido = serializers.BooleanField(
        required=False,
        allow_null=True,
    )
    modo_preparo_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    outras_informacoes_conferido = serializers.BooleanField(
        required=False,
        allow_null=True,
    )

    def create(self, validated_data):
        return AnaliseFichaTecnica.objects.create(
            ficha_tecnica=self.context.get("ficha_tecnica"),
            criado_por=self.context.get("criado_por"),
            **validated_data,
        )

    def update(self, instance, validated_data):
        validated_data["criado_por"] = self.context.get("criado_por")
        return update_instance_from_dict(instance, validated_data, save=True)

    class Meta:
        model = AnaliseFichaTecnica
        exclude = ("id",)


class AnaliseFichaTecnicaCreateSerializer(serializers.ModelSerializer):
    fabricante_envasador_conferido = serializers.BooleanField()
    fabricante_envasador_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    detalhes_produto_conferido = serializers.BooleanField()
    detalhes_produto_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    informacoes_nutricionais_conferido = serializers.BooleanField()
    informacoes_nutricionais_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    conservacao_conferido = serializers.BooleanField()
    conservacao_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    temperatura_e_transporte_conferido = serializers.BooleanField(required=False)
    temperatura_e_transporte_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    armazenamento_conferido = serializers.BooleanField()
    armazenamento_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    embalagem_e_rotulagem_conferido = serializers.BooleanField()
    embalagem_e_rotulagem_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    responsavel_tecnico_conferido = serializers.BooleanField()
    responsavel_tecnico_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    modo_preparo_conferido = serializers.BooleanField()
    modo_preparo_correcoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    outras_informacoes_conferido = serializers.BooleanField()

    def validate(self, attrs):
        campos_dependentes = [
            "fabricante_envasador",
            "detalhes_produto",
            "informacoes_nutricionais",
            "conservacao",
            "temperatura_e_transporte",
            "armazenamento",
            "embalagem_e_rotulagem",
            "responsavel_tecnico",
            "modo_preparo",
        ]

        self._validate_campos_correcoes_preenchido(attrs, campos_dependentes)
        self._validate_campos_correcoes_vazio(attrs, campos_dependentes)

        return attrs

    def _validate_campos_correcoes_preenchido(self, attrs, campos_dependentes):
        for campo in campos_dependentes:
            if attrs.get(f"{campo}_conferido") is False and not attrs.get(
                f"{campo}_correcoes"
            ):
                raise serializers.ValidationError(
                    f"O valor de {campo}_correcoes não pode ser vazio quando {campo}_conferido for False."
                )

    def _validate_campos_correcoes_vazio(self, attrs, campos_dependentes):
        for campo in campos_dependentes:
            if attrs.get(f"{campo}_conferido") is True and attrs.get(
                f"{campo}_correcoes"
            ):
                raise serializers.ValidationError(
                    f"O valor de {campo}_correcoes deve ser vazio quando {campo}_conferido for True."
                )

    def create(self, validated_data):
        usuario = self.context.get("criado_por")
        analise = AnaliseFichaTecnica.objects.create(
            criado_por=usuario,
            ficha_tecnica=self.context.get("ficha_tecnica"),
            **validated_data,
        )

        self._avaliar_estado_ficha_tecnica(analise, usuario)

        return analise

    def update(self, instance, validated_data):
        usuario = self.context.get("criado_por")
        validated_data["criado_por"] = usuario
        analise = update_instance_from_dict(instance, validated_data, save=True)

        self._avaliar_estado_ficha_tecnica(analise, usuario)

        return analise

    def _avaliar_estado_ficha_tecnica(self, analise, usuario):
        (
            analise.ficha_tecnica.gpcodae_aprova(user=usuario)
            if analise.aprovada
            else analise.ficha_tecnica.gpcodae_envia_para_correcao(user=usuario)
        )

    class Meta:
        model = AnaliseFichaTecnica
        exclude = ("id", "ficha_tecnica")


class CorrecaoFichaTecnicaSerializer(serializers.ModelSerializer):
    produto = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        allow_null=True,
        queryset=NomeDeProdutoEdital.objects.all(),
    )
    marca = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        allow_null=True,
        queryset=Marca.objects.all(),
    )
    empresa = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        allow_null=True,
        queryset=Terceirizada.objects.all(),
    )
    fabricante = FabricanteFichaTecnicaCreateSerializer(
        required=False, allow_null=True, fabricante_opcional=True
    )
    envasador_distribuidor = FabricanteFichaTecnicaCreateSerializer(
        required=False, allow_null=True, fabricante_opcional=True
    )
    informacoes_nutricionais = InformacoesNutricionaisFichaTecnicaCreateSerializer(
        many=True,
        required=False,
    )
    unidade_medida_porcao = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        allow_null=True,
        queryset=UnidadeMedida.objects.all(),
    )
    unidade_medida_volume_primaria = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        allow_null=True,
        queryset=UnidadeMedida.objects.all(),
    )
    unidade_medida_primaria = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        allow_null=True,
        queryset=UnidadeMedida.objects.all(),
    )
    unidade_medida_secundaria = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        allow_null=True,
        queryset=UnidadeMedida.objects.all(),
    )
    unidade_medida_primaria_vazia = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        allow_null=True,
        queryset=UnidadeMedida.objects.all(),
    )
    unidade_medida_secundaria_vazia = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        allow_null=True,
        queryset=UnidadeMedida.objects.all(),
    )
    arquivo = serializers.CharField(required=False, allow_blank=False)

    def validate(self, attrs):
        service_validacao = ServiceValidacaoCorrecaoFichaTecnica(self.instance, attrs)

        service_validacao.valida_status_enviada_para_correcao()
        service_validacao.valida_campos_obrigatorios_por_collapse()
        service_validacao.valida_campos_nao_permitidos_por_collapse()

        valida_campos_dependentes_ficha_tecnica(attrs)

        return attrs

    def update(self, instance, validated_data):
        user = self.context["request"].user
        instance = atualiza_ficha_tecnica(instance, validated_data)
        instance = limpar_campos_dependentes_ficha_tecnica(instance, validated_data)

        instance.fornecedor_corrige(user=user)

        gerar_nova_analise_ficha_tecnica(instance)

        return instance

    class Meta:
        model = FichaTecnicaDoProduto
        fields = "__all__"
        extra_kwargs = {
            field: {"required": False}
            for field in FichaTecnicaDoProduto._meta.get_fields()
        }


class FichaTecnicaAtualizacaoSerializer(serializers.ModelSerializer):
    fabricante = FabricanteFichaTecnicaCreateSerializer(
        required=False, allow_null=True, fabricante_opcional=True
    )
    envasador_distribuidor = FabricanteFichaTecnicaCreateSerializer(
        required=False, allow_null=True, fabricante_opcional=True
    )
    componentes_produto = serializers.CharField(required=False, allow_blank=False)
    alergenicos = serializers.BooleanField(required=False)
    ingredientes_alergenicos = serializers.CharField(required=False, allow_blank=False)
    gluten = serializers.BooleanField(required=False)

    porcao = serializers.CharField(required=False, allow_blank=False)
    unidade_medida_porcao = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=UnidadeMedida.objects.all(),
    )
    valor_unidade_caseira = serializers.CharField(required=False, allow_blank=False)
    unidade_medida_caseira = serializers.CharField(required=False, allow_blank=False)
    informacoes_nutricionais = InformacoesNutricionaisFichaTecnicaCreateSerializer(
        many=True,
        required=False,
    )

    condicoes_de_conservacao = serializers.CharField(required=False, allow_blank=False)

    embalagem_primaria = serializers.CharField(required=False, allow_blank=False)
    embalagem_secundaria = serializers.CharField(required=False, allow_blank=False)

    nome_responsavel_tecnico = serializers.CharField(required=False, allow_blank=False)
    habilitacao = serializers.CharField(required=False, allow_blank=False)
    numero_registro_orgao = serializers.CharField(required=False, allow_blank=False)
    arquivo = serializers.CharField(required=False, allow_blank=False)

    modo_de_preparo = serializers.CharField(required=False, allow_blank=False)

    informacoes_adicionais = serializers.CharField(required=False, allow_blank=False)

    def validate(self, attrs):
        valida_ingredientes_alergenicos_ficha_tecnica(attrs)

        return attrs

    def validate_arquivo(self, value):
        if value and "pdf" not in value:
            raise serializers.ValidationError("Arquivo deve ser um PDF.")
        return value

    def update(self, instance, validated_data):
        gerar_nova_analise_ficha_tecnica(instance, validated_data)

        instance = atualiza_ficha_tecnica(instance, validated_data)

        user = self.context["request"].user
        instance.fornecedor_atualiza(user=user)

        return instance

    class Meta:
        model = FichaTecnicaDoProduto
        exclude = ("id", "produto")
