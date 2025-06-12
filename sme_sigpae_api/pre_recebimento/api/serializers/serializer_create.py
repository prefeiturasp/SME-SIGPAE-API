from datetime import date

from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated
from xworkflows.base import InvalidTransitionError

from sme_sigpae_api.dados_comuns.api.serializers import (
    CamposObrigatoriosMixin,
    ContatoSerializer,
)
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.dados_comuns.utils import (
    convert_base64_to_contentfile,
    update_instance_from_dict,
)
from sme_sigpae_api.pre_recebimento.models import (
    AnaliseFichaTecnica,
    Cronograma,
    DataDeFabricaoEPrazo,
    DocumentoDeRecebimento,
    EtapasDoCronograma,
    ImagemDoTipoDeEmbalagem,
    InformacoesNutricionaisFichaTecnica,
    Laboratorio,
    LayoutDeEmbalagem,
    ProgramacaoDoRecebimentoDoCronograma,
    SolicitacaoAlteracaoCronograma,
    TipoDeDocumentoDeRecebimento,
    TipoDeEmbalagemDeLayout,
    TipoEmbalagemQld,
    UnidadeMedida,
)
from sme_sigpae_api.produto.models import Fabricante, Marca, NomeDeProdutoEdital
from sme_sigpae_api.terceirizada.models import Contrato, Terceirizada

from ...models.cronograma import FichaTecnicaDoProduto
from ..helpers import (
    atualiza_ficha_tecnica,
    cria_datas_e_prazos_doc_recebimento,
    cria_etapas_de_cronograma,
    cria_ficha_tecnica,
    cria_programacao_de_cronograma,
    cria_tipos_de_documentos,
    cria_tipos_de_embalagens,
    gerar_nova_analise_ficha_tecnica,
    limpar_campos_dependentes_ficha_tecnica,
)
from ..validators import (
    ServiceValidacaoCorrecaoFichaTecnica,
    contrato_pertence_a_empresa,
    valida_campos_dependentes_ficha_tecnica,
    valida_campos_nao_pereciveis_ficha_tecnica,
    valida_campos_pereciveis_ficha_tecnica,
    valida_ingredientes_alergenicos_ficha_tecnica,
)


class ProgramacaoDoRecebimentoDoCronogramaCreateSerializer(serializers.ModelSerializer):
    data_programada = serializers.CharField(required=False)
    tipo_carga = serializers.ChoiceField(
        choices=ProgramacaoDoRecebimentoDoCronograma.TIPO_CARGA_CHOICES,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = ProgramacaoDoRecebimentoDoCronograma
        exclude = ("id", "cronograma")


class EtapasDoCronogramaCreateSerializer(serializers.ModelSerializer):
    numero_empenho = serializers.CharField(required=False)
    etapa = serializers.IntegerField(required=False, allow_null=True)
    parte = serializers.CharField(required=False)
    data_programada = serializers.CharField(required=False)
    quantidade = serializers.FloatField(required=False)
    total_embalagens = serializers.FloatField(required=False)
    qtd_total_empenho = serializers.FloatField(required=False)

    class Meta:
        model = EtapasDoCronograma
        exclude = ("id", "cronograma")


class CronogramaCreateSerializer(serializers.ModelSerializer):
    armazem = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=Terceirizada.objects.filter(
            tipo_servico=Terceirizada.DISTRIBUIDOR_ARMAZEM
        ),
        allow_null=True,
    )
    empresa = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=Terceirizada.objects.filter(
            tipo_servico__in=[
                Terceirizada.FORNECEDOR,
                Terceirizada.FORNECEDOR_E_DISTRIBUIDOR,
            ]
        ),
    )
    contrato = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=Contrato.objects.all(),
        allow_null=True,
    )
    unidade_medida = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=UnidadeMedida.objects.all(),
        allow_null=True,
    )
    password = serializers.CharField(required=False)
    qtd_total_programada = serializers.FloatField(required=False)
    etapas = EtapasDoCronogramaCreateSerializer(many=True, required=False)
    programacoes_de_recebimento = ProgramacaoDoRecebimentoDoCronogramaCreateSerializer(
        many=True, required=False
    )
    cadastro_finalizado = serializers.BooleanField(required=False)
    ficha_tecnica = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=FichaTecnicaDoProduto.objects.all(),
        allow_null=True,
    )
    tipo_embalagem_secundaria = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=TipoEmbalagemQld.objects.all(),
        required=False,
        allow_null=True,
    )
    custo_unitario_produto = serializers.FloatField(required=False)

    def gera_proximo_numero_cronograma(self):
        ano = date.today().year
        ultimo_cronograma = Cronograma.objects.last()
        if ultimo_cronograma:
            return f"{str(int(ultimo_cronograma.numero[:3]) + 1).zfill(3)}/{ano}A"
        else:
            return f"001/{ano}A"

    def validate(self, attrs):
        user = self.context["request"].user
        cadastro_finalizado = attrs.get("cadastro_finalizado", None)
        if cadastro_finalizado and not user.verificar_autenticidade(
            attrs.pop("password", None)
        ):
            raise NotAuthenticated(
                "Assinatura do cronograma não foi validada. Verifique sua senha."
            )

        contrato = attrs.get("contrato", None)
        empresa = attrs.get("empresa", None)
        contrato_pertence_a_empresa(contrato, empresa)

        return super().validate(attrs)

    def create(self, validated_data):
        user = self.context["request"].user
        cadastro_finalizado = validated_data.pop("cadastro_finalizado", None)
        etapas = validated_data.pop("etapas", [])
        programacoes_de_recebimento = validated_data.pop(
            "programacoes_de_recebimento", []
        )
        numero_cronograma = self.gera_proximo_numero_cronograma()
        cronograma = Cronograma.objects.create(
            numero=numero_cronograma, **validated_data
        )
        cronograma.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CRONOGRAMA_CRIADO, usuario=user
        )

        cria_etapas_de_cronograma(etapas, cronograma)
        cria_programacao_de_cronograma(programacoes_de_recebimento, cronograma)

        if cadastro_finalizado:
            cronograma.inicia_fluxo(user=user)

        return cronograma

    def update(self, instance, validated_data):
        user = self.context["request"].user
        cadastro_finalizado = validated_data.pop("cadastro_finalizado", None)
        etapas = validated_data.pop("etapas", [])
        programacoes_de_recebimento = validated_data.pop(
            "programacoes_de_recebimento", []
        )

        instance.etapas.all().delete()
        instance.programacoes_de_recebimento.all().delete()

        update_instance_from_dict(instance, validated_data, save=True)

        cria_etapas_de_cronograma(etapas, instance)
        cria_programacao_de_cronograma(programacoes_de_recebimento, instance)

        if cadastro_finalizado:
            instance.inicia_fluxo(user=user)
        return instance

    class Meta:
        model = Cronograma
        exclude = ("id", "numero", "status")


class LaboratorioCreateSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(required=True)
    cnpj = serializers.CharField(required=True)
    cep = serializers.CharField(required=True)
    logradouro = serializers.CharField(required=True)
    numero = serializers.CharField(required=True)
    bairro = serializers.CharField(required=True)
    cidade = serializers.CharField(required=True)
    estado = serializers.CharField(required=True)
    credenciado = serializers.BooleanField(required=True)
    contatos = ContatoSerializer(many=True)

    def cria_contatos(self, contatos, laboratorio):
        for contato_json in contatos:
            contato = ContatoSerializer().create(validated_data=contato_json)
            laboratorio.contatos.add(contato)

    def create(self, validated_data):
        validated_data["nome"] = validated_data["nome"].upper()
        contatos = validated_data.pop("contatos", [])
        laboratorio = Laboratorio.objects.create(**validated_data)

        self.cria_contatos(contatos, laboratorio)
        return laboratorio

    def update(self, instance, validated_data):
        validated_data["nome"] = validated_data["nome"].upper()
        contatos = validated_data.pop("contatos", [])

        instance.contatos.all().delete()

        self.cria_contatos(contatos, instance)
        update_instance_from_dict(instance, validated_data, save=True)

        return instance

    class Meta:
        model = Laboratorio
        exclude = ("id",)


class TipoEmbalagemQldCreateSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(required=True)
    abreviacao = serializers.CharField(required=True)

    def create(self, validated_data):
        validated_data["nome"] = validated_data["nome"].upper()
        validated_data["abreviacao"] = validated_data["abreviacao"].upper()
        embalagem = TipoEmbalagemQld.objects.create(**validated_data)

        return embalagem

    def update(self, instance, validated_data):
        validated_data["nome"] = validated_data["nome"].upper()
        validated_data["abreviacao"] = validated_data["abreviacao"].upper()
        update_instance_from_dict(instance, validated_data, save=True)

        return instance

    class Meta:
        model = TipoEmbalagemQld
        exclude = ("id",)


def novo_numero_solicitacao(objeto):
    # Nova regra para sequência de numeração.
    objeto.numero_solicitacao = f"{str(objeto.pk).zfill(8)}-ALT"
    objeto.save()


class SolicitacaoDeAlteracaoCronogramaCreateSerializer(serializers.ModelSerializer):
    cronograma = serializers.UUIDField()
    etapas = serializers.JSONField(write_only=True)
    programacoes_de_recebimento = serializers.JSONField(write_only=True, required=False)

    def validate_cronograma(self, value):
        cronograma = Cronograma.objects.filter(uuid=value)
        if not cronograma:
            raise serializers.ValidationError("Cronograma não existe")
        if not cronograma.first().status == Cronograma.workflow_class.ASSINADO_CODAE:
            raise serializers.ValidationError(
                "Não é possivel criar Solicitação de alteração neste momento!"
            )
        return value

    def valida_campo_etapa(self, etapa, campo):
        if not etapa[campo]:
            raise serializers.ValidationError({campo: ["Este campo é obrigatório."]})

    def validate(self, attrs):
        for etapa in attrs["etapas"]:
            self.valida_campo_etapa(etapa, "etapa")
            self.valida_campo_etapa(etapa, "data_programada")
            self.valida_campo_etapa(etapa, "quantidade")
            self.valida_campo_etapa(etapa, "total_embalagens")
        return super().validate(attrs)

    def _criar_etapas(self, etapas):
        etapas_created = []
        for etapa in etapas:
            etapas_created.append(EtapasDoCronograma.objects.create(**etapa))
        return etapas_created

    def create(self, validated_data):
        user = self.context["request"].user
        uuid_cronograma = validated_data.pop("cronograma", None)
        etapas = validated_data.pop("etapas", [])
        programacoes = validated_data.pop("programacoes_de_recebimento", [])
        cronograma = Cronograma.objects.get(uuid=uuid_cronograma)
        alteracao_cronograma = SolicitacaoAlteracaoCronograma.objects.create(
            usuario_solicitante=user,
            cronograma=cronograma,
            **validated_data,
        )
        alteracao_cronograma.etapas_antigas.set(cronograma.etapas.all())
        etapas_created = cria_etapas_de_cronograma(etapas)
        alteracao_cronograma.etapas_novas.set(etapas_created)
        programacoes_criadas = cria_programacao_de_cronograma(programacoes)
        alteracao_cronograma.programacoes_novas.set(programacoes_criadas)
        self._alterna_estado_cronograma(cronograma, user, alteracao_cronograma)
        self._alterna_estado_solicitacao_alteracao_cronograma(
            alteracao_cronograma, user, validated_data
        )
        return alteracao_cronograma

    def _alterna_estado_cronograma(self, cronograma, user, alteracao_cronograma):
        try:
            if user.eh_fornecedor:
                cronograma.fornecedor_solicita_alteracao(
                    user=user, justificativa=alteracao_cronograma.uuid
                )
            else:
                cronograma.codae_realiza_alteracao(
                    user=user, justificativa=alteracao_cronograma.uuid
                )
        except InvalidTransitionError as e:
            raise serializers.ValidationError(
                f"Erro de transição de estado do cronograma: {e}"
            )

    def _alterna_estado_solicitacao_alteracao_cronograma(
        self, alteracao_cronograma, user, validated_data
    ):
        try:
            if user.eh_fornecedor:
                alteracao_cronograma.inicia_fluxo(
                    user=user, justificativa=validated_data.get("justificativa", "")
                )
            else:
                alteracao_cronograma.inicia_fluxo_codae(
                    user=user, justificativa=validated_data.get("justificativa", "")
                )
        except InvalidTransitionError as e:
            raise serializers.ValidationError(
                f"Erro de transição de estado da alteração: {e}"
            )

    class Meta:
        model = SolicitacaoAlteracaoCronograma
        exclude = ("id", "usuario_solicitante", "etapas_antigas", "etapas_novas")


class UnidadeMedidaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadeMedida
        fields = ("uuid", "nome", "abreviacao", "criado_em")
        read_only_fields = ("uuid", "criado_em")

    def validate_nome(self, value):
        if not value.isupper():
            raise serializers.ValidationError(
                "O campo deve conter apenas letras maiúsculas."
            )
        return value

    def validate_abreviacao(self, value):
        if not value.islower():
            raise serializers.ValidationError(
                "O campo deve conter apenas letras minúsculas."
            )
        return value


class TipoDeEmbalagemDeLayoutCreateSerializer(serializers.ModelSerializer):
    tipo_embalagem = serializers.ChoiceField(
        choices=TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_CHOICES,
        required=True,
        allow_blank=True,
    )
    imagens_do_tipo_de_embalagem = serializers.JSONField(write_only=True)

    def validate(self, attrs):
        tipo_embalagem = attrs.get("tipo_embalagem", None)
        imagens = attrs.get("imagens_do_tipo_de_embalagem", None)
        tipos_obrigatorios = [
            TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_PRIMARIA,
            TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_SECUNDARIA,
        ]

        if tipo_embalagem in tipos_obrigatorios:
            for img in imagens:
                if not img["arquivo"] or not img["nome"]:
                    raise serializers.ValidationError(
                        {
                            f"Layout Embalagem {tipo_embalagem}": [
                                "Este campo é obrigatório."
                            ]
                        }
                    )
        return attrs

    class Meta:
        model = TipoDeEmbalagemDeLayout
        exclude = ("id", "layout_de_embalagem")


class LayoutDeEmbalagemCreateSerializer(serializers.ModelSerializer):
    ficha_tecnica = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=FichaTecnicaDoProduto.objects.all(),
        required=True,
    )
    tipos_de_embalagens = TipoDeEmbalagemDeLayoutCreateSerializer(
        many=True, required=False
    )
    observacoes = serializers.CharField(required=False)

    def validate_ficha_tecnica(self, value):
        if (
            value is not None
            and value.status == FichaTecnicaDoProduto.workflow_class.RASCUNHO
        ):
            raise serializers.ValidationError(
                "Não é possível vincular com Ficha Técnica em rascunho."
            )

        return value

    def create(self, validated_data):
        user = self.context["request"].user

        tipos_de_embalagens = validated_data.pop("tipos_de_embalagens", [])
        layout_de_embalagem = LayoutDeEmbalagem.objects.create(
            **validated_data,
        )
        cria_tipos_de_embalagens(tipos_de_embalagens, layout_de_embalagem)
        layout_de_embalagem.inicia_fluxo(user=user)

        return layout_de_embalagem

    def update(self, instance, validated_data):
        try:
            user = self.context["request"].user
            dados_correcao = validated_data.pop("tipos_de_embalagens", [])

            instance.tipos_de_embalagens.all().delete()
            cria_tipos_de_embalagens(dados_correcao, instance)

            instance.observacoes = validated_data.pop("observacoes", "")
            instance.fornecedor_atualiza(user=user)
            instance.save()

        except InvalidTransitionError as e:
            raise serializers.ValidationError(
                f"Erro de transição de estado. O status deste layout não permite correção: {e}"
            )

        return instance

    class Meta:
        model = LayoutDeEmbalagem
        exclude = ("id",)


class TipoDeEmbalagemDeLayoutAnaliseSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=False)

    def validate(self, attrs):
        uuid = attrs.get("uuid", None)
        tipo_embalagem = attrs.get("tipo_embalagem", None)
        status = attrs.get("status", None)

        if tipo_embalagem is TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_PRIMARIA:
            if not uuid or not status:
                raise serializers.ValidationError(
                    {
                        f"Layout Embalagem {tipo_embalagem}": [
                            "UUID obrigatório para o tipo de embalagem informado."
                        ]
                    }
                )
        return attrs

    class Meta:
        model = TipoDeEmbalagemDeLayout
        fields = ("uuid", "tipo_embalagem", "status", "complemento_do_status")
        extra_kwargs = {
            "tipo_embalagem": {"required": True},
            "status": {"required": False},
            "complemento_do_status": {"required": True},
        }


class LayoutDeEmbalagemAnaliseSerializer(serializers.ModelSerializer):
    tipos_de_embalagens = TipoDeEmbalagemDeLayoutAnaliseSerializer(many=True)

    def validate_tipos_de_embalagens(self, value):
        self._validar_primeira_analise(value)

        return value

    def _validar_primeira_analise(self, value):
        if self.instance.eh_primeira_analise:
            if len(value) < self.instance.tipos_de_embalagens.count():
                raise serializers.ValidationError(
                    "Quantidade de Tipos de Embalagem recebida para primeira análise "
                    + "é menor que quantidade presente no Layout de Embalagem."
                )

    def update(self, instance, validated_data):
        try:
            user = self.context["request"].user
            dados_tipos_de_embalagens = validated_data.pop("tipos_de_embalagens", [])

            for dados in dados_tipos_de_embalagens:
                if dados["tipo_embalagem"] in [
                    TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_SECUNDARIA,
                    TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_TERCIARIA,
                ] and not dados.get("uuid", None):
                    TipoDeEmbalagemDeLayout.objects.create(
                        layout_de_embalagem=instance, **dados
                    )

                else:
                    tipo_de_embalagem = instance.tipos_de_embalagens.get(
                        uuid=dados["uuid"]
                    )
                    tipo_de_embalagem.status = dados["status"]
                    tipo_de_embalagem.complemento_do_status = dados[
                        "complemento_do_status"
                    ]
                    tipo_de_embalagem.save()

            (
                instance.codae_aprova(user=user)
                if instance.aprovado
                else instance.codae_solicita_correcao(user=user)
            )

        except InvalidTransitionError as e:
            raise serializers.ValidationError(
                f"Erro de transição de estado. O status deste layout não permite analise: {e}"
            )

        return instance

    class Meta:
        model = LayoutDeEmbalagem
        fields = ("tipos_de_embalagens",)


class TipoDeEmbalagemDeLayoutCorrecaoSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField()
    tipo_embalagem = serializers.ChoiceField(
        choices=TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_CHOICES,
        required=True,
        allow_blank=True,
    )
    imagens_do_tipo_de_embalagem = serializers.JSONField(write_only=True, required=True)

    def validate(self, attrs):
        uuid = attrs.get("uuid", None)
        tipo = attrs.get("tipo_embalagem", None)
        imagens = attrs.get("imagens_do_tipo_de_embalagem", None)
        embalagem = TipoDeEmbalagemDeLayout.objects.filter(uuid=uuid).last()

        if not embalagem:
            raise serializers.ValidationError(
                {f"Layout Embalagem {tipo}": ["UUID do tipo informado não existe."]}
            )
        if embalagem.status != TipoDeEmbalagemDeLayout.STATUS_REPROVADO:
            raise serializers.ValidationError(
                {
                    f"Layout Embalagem {tipo}": [
                        "O Tipo/UUID informado não pode ser corrigido pois não está reprovado."
                    ]
                }
            )
        for img in imagens:
            if not img["arquivo"] or not img["nome"]:
                raise serializers.ValidationError(
                    {f"Layout Embalagem {tipo}": ["arquivo/nome é obrigatório."]}
                )
        return attrs

    class Meta:
        model = TipoDeEmbalagemDeLayout
        exclude = ("id", "layout_de_embalagem")


class LayoutDeEmbalagemCorrecaoSerializer(serializers.ModelSerializer):
    tipos_de_embalagens = TipoDeEmbalagemDeLayoutCorrecaoSerializer(
        many=True, required=True
    )
    observacoes = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        try:
            user = self.context["request"].user
            dados_correcao = validated_data.pop("tipos_de_embalagens", [])

            for embalagem in dados_correcao:
                tipo_embalagem = instance.tipos_de_embalagens.get(
                    uuid=embalagem["uuid"]
                )
                tipo_embalagem.status = TipoDeEmbalagemDeLayout.STATUS_EM_ANALISE
                tipo_embalagem.imagens.all().delete()
                tipo_embalagem.save()
                imagens = embalagem.pop("imagens_do_tipo_de_embalagem", [])
                for img in imagens:
                    data = convert_base64_to_contentfile(img.get("arquivo"))
                    ImagemDoTipoDeEmbalagem.objects.create(
                        tipo_de_embalagem=tipo_embalagem,
                        arquivo=data,
                        nome=img.get("nome", ""),
                    )

            instance.observacoes = validated_data.pop("observacoes", "")
            instance.fornecedor_realiza_correcao(user=user)
            instance.save()

        except InvalidTransitionError as e:
            raise serializers.ValidationError(
                f"Erro de transição de estado. O status deste layout não permite correção: {e}"
            )

        return instance

    class Meta:
        model = LayoutDeEmbalagem
        fields = ("tipos_de_embalagens", "observacoes")


class TipoDeDocumentoDeRecebimentoCreateSerializer(serializers.ModelSerializer):
    tipo_documento = serializers.ChoiceField(
        choices=TipoDeDocumentoDeRecebimento.TIPO_DOC_CHOICES,
        required=True,
        allow_blank=False,
    )
    arquivos_do_tipo_de_documento = serializers.JSONField(write_only=True)
    descricao_documento = serializers.CharField(required=False)

    def validate(self, attrs):
        tipo_documento = attrs.get("tipo_documento", None)
        arquivos = attrs.get("arquivos_do_tipo_de_documento", None)
        tipos_obrigatorios = [
            TipoDeDocumentoDeRecebimento.TIPO_DOC_LAUDO,
        ]

        if tipo_documento in tipos_obrigatorios:
            for doc in arquivos:
                if not doc["arquivo"] or not doc["nome"]:
                    raise serializers.ValidationError(
                        {f"{tipo_documento}": ["Este campo é obrigatório."]}
                    )
        return attrs

    class Meta:
        model = TipoDeDocumentoDeRecebimento
        exclude = ("id", "documento_recebimento")


class DocumentoDeRecebimentoCreateSerializer(serializers.ModelSerializer):
    cronograma = serializers.UUIDField(required=True)
    tipos_de_documentos = TipoDeDocumentoDeRecebimentoCreateSerializer(
        many=True, required=False
    )
    numero_laudo = serializers.CharField(required=True)

    def validate_cronograma(self, value):
        cronograma = Cronograma.objects.filter(uuid=value)
        if not cronograma:
            raise serializers.ValidationError("Cronograma não existe")
        return value

    def create(self, validated_data):
        user = self.context["request"].user

        uuid_cronograma = validated_data.pop("cronograma", None)
        tipos_de_documentos = validated_data.pop("tipos_de_documentos", [])
        cronograma = Cronograma.objects.get(uuid=uuid_cronograma)
        documento_de_recebimento = DocumentoDeRecebimento.objects.create(
            cronograma=cronograma,
            **validated_data,
        )
        cria_tipos_de_documentos(tipos_de_documentos, documento_de_recebimento)
        documento_de_recebimento.inicia_fluxo(user=user)

        return documento_de_recebimento

    class Meta:
        model = DocumentoDeRecebimento
        exclude = ("id",)


class DataDeFabricaoEPrazoAnalisarRascunhoSerializer(serializers.ModelSerializer):
    data_fabricacao = serializers.DateField(required=False, allow_null=True)
    data_validade = serializers.DateField(required=False, allow_null=True)
    prazo_maximo_recebimento = serializers.ChoiceField(
        choices=DataDeFabricaoEPrazo.PRAZO_CHOICES, required=False, allow_blank=True
    )
    justificativa = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = DataDeFabricaoEPrazo
        fields = (
            "data_fabricacao",
            "data_validade",
            "prazo_maximo_recebimento",
            "justificativa",
        )


class DataDeFabricaoEPrazoAnalisarSerializer(
    DataDeFabricaoEPrazoAnalisarRascunhoSerializer
):
    def validate(self, attrs):
        prazo_maximo = attrs.get("prazo_maximo_recebimento", None)
        justificativa = attrs.get("justificativa", None)
        if prazo_maximo == DataDeFabricaoEPrazo.PRAZO_OUTRO and not justificativa:
            raise serializers.ValidationError(
                {
                    "justificativa": [
                        "Este campo é obrigatório quando o prazo maximo de recebimento é OUTRO."
                    ]
                }
            )
        return attrs

    class Meta(DataDeFabricaoEPrazoAnalisarRascunhoSerializer.Meta):
        extra_kwargs = {
            "data_fabricacao": {"required": True, "allow_null": False},
            "data_validade": {"required": True, "allow_null": False},
            "prazo_maximo_recebimento": {"required": True, "allow_blank": False},
        }


class DocumentoDeRecebimentoAnalisarRascunhoSerializer(serializers.ModelSerializer):
    laboratorio = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=Laboratorio.objects.all(),
        allow_null=True,
    )
    unidade_medida = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=UnidadeMedida.objects.all(),
        allow_null=True,
    )
    quantidade_laudo = serializers.FloatField(required=False, allow_null=True)
    saldo_laudo = serializers.FloatField(required=False, allow_null=True)
    numero_lote_laudo = serializers.CharField(required=False, allow_null=True)
    data_final_lote = serializers.DateField(required=False, allow_null=True)
    datas_fabricacao_e_prazos = DataDeFabricaoEPrazoAnalisarRascunhoSerializer(
        many=True, required=False
    )

    def update(self, instance, validated_data):
        datas_fabricacao_e_prazos = validated_data.pop("datas_fabricacao_e_prazos", [])
        update_instance_from_dict(instance, validated_data, save=True)
        instance.datas_fabricacao_e_prazos.all().delete()
        cria_datas_e_prazos_doc_recebimento(datas_fabricacao_e_prazos, instance)
        instance.save()
        return instance

    class Meta:
        model = DocumentoDeRecebimento
        fields = (
            "laboratorio",
            "quantidade_laudo",
            "unidade_medida",
            "numero_lote_laudo",
            "data_final_lote",
            "saldo_laudo",
            "datas_fabricacao_e_prazos",
        )


class DocumentoDeRecebimentoAnalisarSerializer(
    CamposObrigatoriosMixin, DocumentoDeRecebimentoAnalisarRascunhoSerializer
):
    def __init__(self, *args, **kwargs):
        """Exceção ao demais campos, correcao_solicitada não é obrigatório."""
        super().__init__(*args, **kwargs)
        self.fields["correcao_solicitada"] = serializers.CharField(required=False)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        datas_fabricacao_e_prazos = validated_data.pop("datas_fabricacao_e_prazos", [])
        tem_solicitacao_correcao = validated_data.get("correcao_solicitada", None)
        update_instance_from_dict(instance, validated_data, save=True)
        instance.datas_fabricacao_e_prazos.all().delete()
        cria_datas_e_prazos_doc_recebimento(datas_fabricacao_e_prazos, instance)
        try:
            if tem_solicitacao_correcao:
                instance.qualidade_solicita_correcao(
                    user=user, justificativa=tem_solicitacao_correcao
                )
            else:
                instance.qualidade_aprova_analise(user=user)
        except InvalidTransitionError as e:
            raise serializers.ValidationError(
                f"Erro de transição de estado. O status atual não permite análise: {e}"
            )
        instance.save()
        return instance

    class Meta(DocumentoDeRecebimentoAnalisarRascunhoSerializer.Meta):
        fields = DocumentoDeRecebimentoAnalisarRascunhoSerializer.Meta.fields + (
            "correcao_solicitada",
        )


class TipoDeDocumentoDeRecebimentoCorrecaoSerializer(serializers.ModelSerializer):
    tipo_documento = serializers.ChoiceField(
        choices=TipoDeDocumentoDeRecebimento.TIPO_DOC_CHOICES,
        required=True,
        allow_blank=True,
    )

    arquivos_do_tipo_de_documento = serializers.JSONField(
        write_only=True, required=True
    )

    def validate(self, attrs):
        tipo = attrs.get("tipo_documento")
        arquivos_do_tipo_de_documento = attrs.get("arquivos_do_tipo_de_documento")
        descricao_documento = attrs.get("descricao_documento")

        if tipo == TipoDeDocumentoDeRecebimento.TIPO_DOC_OUTROS:
            if not descricao_documento:
                raise serializers.ValidationError(
                    {
                        "tipo_documento": [
                            "O campo descricao_documento é obrigatório para documentos do tipo Outros."
                        ]
                    }
                )

        for arquivo in arquivos_do_tipo_de_documento:
            if not arquivo.get("arquivo") or not arquivo.get("nome"):
                raise serializers.ValidationError(
                    {
                        "arquivos_do_tipo_de_documento": [
                            "Os campos arquivo e nome são obrigatórios."
                        ]
                    }
                )

        return attrs

    class Meta:
        model = TipoDeDocumentoDeRecebimento
        fields = (
            "tipo_documento",
            "descricao_documento",
            "arquivos_do_tipo_de_documento",
        )


class DocumentoDeRecebimentoCorrecaoSerializer(serializers.ModelSerializer):
    tipos_de_documentos = TipoDeDocumentoDeRecebimentoCorrecaoSerializer(
        many=True, required=True
    )

    def validate(self, attrs):
        tipos_documentos_recebidos = [
            dados["tipo_documento"] for dados in attrs["tipos_de_documentos"]
        ]
        if (
            TipoDeDocumentoDeRecebimento.TIPO_DOC_LAUDO
            not in tipos_documentos_recebidos
        ):
            raise serializers.ValidationError(
                {
                    "tipos_de_documentos": "É obrigatório pelo menos um documento do tipo Laudo."
                }
            )

        choices_tipos_documentos = set(
            [choice[0] for choice in TipoDeDocumentoDeRecebimento.TIPO_DOC_CHOICES]
        )
        if len(choices_tipos_documentos.intersection(tipos_documentos_recebidos)) < 2:
            raise serializers.ValidationError(
                {
                    "tipos_de_documentos": (
                        "É obrigatório pelo menos um documento do tipo Laudo"
                        + " e um documento de algum dos tipos"
                        + f' {", ".join(choices_tipos_documentos)}.'
                    )
                }
            )

        return attrs

    def update(self, instance, validated_data):
        try:
            user = self.context["request"].user

            dados_tipos_documentos_corrigidos = validated_data.pop(
                "tipos_de_documentos", []
            )

            for tipo_documento_antigo in instance.tipos_de_documentos.all():
                tipo_documento_antigo.arquivos.all().delete()
                tipo_documento_antigo.delete()

            cria_tipos_de_documentos(dados_tipos_documentos_corrigidos, instance)

            instance.fornecedor_realiza_correcao(user=user)
            instance.save()

            return instance

        except InvalidTransitionError as e:
            raise serializers.ValidationError(
                f"Erro de transição de estado. O status deste documento de recebimento não permite correção: {e}"
            )

    class Meta:
        model = DocumentoDeRecebimento
        fields = ("tipos_de_documentos",)


class DocumentoDeRecebimentoAtualizacaoSerializer(serializers.ModelSerializer):
    tipos_de_documentos = TipoDeDocumentoDeRecebimentoCorrecaoSerializer(
        many=True, required=True
    )

    def update(self, instance, validated_data):
        try:
            user = self.context["request"].user

            dados_tipos_documentos_corrigidos = validated_data.pop(
                "tipos_de_documentos", []
            )

            for tipo_documento_antigo in instance.tipos_de_documentos.exclude(
                tipo_documento=TipoDeDocumentoDeRecebimento.TIPO_DOC_LAUDO
            ):
                tipo_documento_antigo.arquivos.all().delete()
                tipo_documento_antigo.delete()

            cria_tipos_de_documentos(dados_tipos_documentos_corrigidos, instance)

            instance.fornecedor_atualiza(user=user)
            instance.save()

            return instance

        except InvalidTransitionError as e:
            raise serializers.ValidationError(
                f"Erro de transição de estado. O status deste documento de recebimento não permite atualização: {e}"
            )

    class Meta:
        model = DocumentoDeRecebimento
        fields = ("tipos_de_documentos",)


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
    fabricante = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=Fabricante.objects.all(),
        allow_null=True,
    )
    cnpj_fabricante = serializers.CharField(required=True, allow_blank=True)
    cep_fabricante = serializers.CharField(required=True, allow_blank=True)
    endereco_fabricante = serializers.CharField(required=True, allow_blank=True)
    numero_fabricante = serializers.CharField(required=True, allow_blank=True)
    complemento_fabricante = serializers.CharField(required=True, allow_blank=True)
    bairro_fabricante = serializers.CharField(required=True, allow_blank=True)
    cidade_fabricante = serializers.CharField(required=True, allow_blank=True)
    estado_fabricante = serializers.CharField(required=True, allow_blank=True)
    email_fabricante = serializers.CharField(required=True, allow_blank=True)
    telefone_fabricante = serializers.CharField(required=True, allow_blank=True)
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
    fabricante = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=Fabricante.objects.all(),
    )
    cnpj_fabricante = serializers.CharField(required=False, allow_blank=True)
    cep_fabricante = serializers.CharField(required=False, allow_blank=True)
    endereco_fabricante = serializers.CharField(required=False, allow_blank=True)
    numero_fabricante = serializers.CharField(required=False, allow_blank=True)
    complemento_fabricante = serializers.CharField(required=False, allow_blank=True)
    bairro_fabricante = serializers.CharField(required=False, allow_blank=True)
    cidade_fabricante = serializers.CharField(required=False, allow_blank=True)
    estado_fabricante = serializers.CharField(required=False, allow_blank=True)
    email_fabricante = serializers.CharField(required=False, allow_blank=True)
    telefone_fabricante = serializers.CharField(required=False, allow_blank=True)
    prazo_validade = serializers.CharField(required=True)
    numero_registro = serializers.CharField(required=False, allow_blank=True)
    agroecologico = serializers.BooleanField(required=False)
    organico = serializers.BooleanField(required=False)
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
    modo_preparo_conferido = serializers.BooleanField(
        required=False,
        allow_null=True,
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
    modo_preparo_conferido = serializers.BooleanField()
    outras_informacoes_conferido = serializers.BooleanField()

    def validate(self, attrs):
        campos_dependentes = [
            "detalhes_produto",
            "informacoes_nutricionais",
            "conservacao",
            "temperatura_e_transporte",
            "armazenamento",
            "embalagem_e_rotulagem",
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
    fabricante = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        allow_null=True,
        queryset=Fabricante.objects.all(),
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
