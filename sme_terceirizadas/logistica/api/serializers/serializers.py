from rest_framework import serializers

from sme_terceirizadas.dados_comuns.api.serializers import LogSolicitacoesSerializer
from sme_terceirizadas.logistica.models import (
    Alimento,
    ConferenciaGuia,
    Embalagem,
    Guia,
    SolicitacaoDeAlteracaoRequisicao,
    SolicitacaoRemessa,
    TipoEmbalagem
)
from sme_terceirizadas.logistica.models.guia import ConferenciaIndividualPorAlimento, InsucessoEntregaGuia
from sme_terceirizadas.perfil.api.serializers import UsuarioVinculoSerializer


class EmbalagemSerializer(serializers.ModelSerializer):
    tipo_embalagem = serializers.SerializerMethodField()

    def get_tipo_embalagem(self, obj):
        return obj.get_tipo_embalagem_display()

    class Meta:
        model = Embalagem
        exclude = ('id',)


class AlimentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alimento
        exclude = ('id',)


class AlimentoLookUpSerializer(serializers.ModelSerializer):
    embalagens = EmbalagemSerializer(many=True)

    class Meta:
        model = Alimento
        fields = ('uuid', 'nome_alimento', 'embalagens')


class GuiaSerializer(serializers.ModelSerializer):
    alimentos = AlimentoSerializer(many=True)

    class Meta:
        model = Guia
        exclude = ('id',)


class GuiaLookUpSerializer(serializers.ModelSerializer):
    alimentos = AlimentoLookUpSerializer(many=True)
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return obj.get_status_display()

    class Meta:
        model = Guia
        fields = ('uuid', 'numero_guia', 'data_entrega', 'codigo_unidade', 'nome_unidade', 'endereco_unidade',
                  'numero_unidade', 'bairro_unidade', 'bairro_unidade', 'cep_unidade', 'cidade_unidade',
                  'estado_unidade', 'contato_unidade', 'telefone_unidade', 'alimentos', 'status')


class SolicitacaoRemessaSerializer(serializers.ModelSerializer):

    logs = LogSolicitacoesSerializer(many=True)
    guias = GuiaSerializer(many=True)

    class Meta:
        model = SolicitacaoRemessa
        exclude = ('id',)


class SolicitacaoRemessaLookUpSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    guias = GuiaLookUpSerializer(many=True)
    distribuidor_nome = serializers.SerializerMethodField()

    def get_distribuidor_nome(self, obj):
        return obj.distribuidor.razao_social

    def get_status(self, obj):
        return obj.get_status_display()

    class Meta:
        model = SolicitacaoRemessa
        fields = ('uuid', 'numero_solicitacao', 'distribuidor_nome', 'status', 'guias')


class SolicitacaoRemessaContagemGuiasSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    guias_pendentes = serializers.IntegerField()
    guias_insucesso = serializers.IntegerField()
    guias_recebidas = serializers.IntegerField()
    guias_parciais = serializers.IntegerField()
    guias_nao_recebidas = serializers.IntegerField()
    guias_reposicao_parcial = serializers.IntegerField()
    guias_reposicao_total = serializers.IntegerField()
    qtd_guias = serializers.IntegerField()
    distribuidor_nome = serializers.CharField()
    data_entrega = serializers.SerializerMethodField()

    def get_status(self, obj):
        return obj.get_status_display()

    def get_data_entrega(self, obj):
        return obj.data_entrega.strftime('%d/%m/%Y')

    class Meta:
        model = SolicitacaoRemessa
        exclude = ('id',)


class XmlAlimentoSerializer(serializers.Serializer):
    StrCodSup = serializers.CharField()
    StrCodPapa = serializers.CharField()
    StrNomAli = serializers.CharField()
    StrEmbala = serializers.CharField()
    IntQtdVol = serializers.CharField()


class XmlGuiaSerializer(serializers.Serializer):
    StrNumGui = serializers.CharField()
    DtEntrega = serializers.DateField()
    StrCodUni = serializers.CharField()
    StrNomUni = serializers.CharField()
    StrEndUni = serializers.CharField()
    StrNumUni = serializers.CharField()
    StrBaiUni = serializers.CharField()
    StrCepUni = serializers.CharField()
    StrCidUni = serializers.CharField()
    StrEstUni = serializers.CharField()
    StrConUni = serializers.CharField()
    StrTelUni = serializers.CharField()
    alimentos = XmlAlimentoSerializer(many=True)


class XmlParserSolicitacaoSerializer(serializers.Serializer):
    StrCnpj = serializers.CharField(max_length=14)
    StrNumSol = serializers.CharField(max_length=30)
    guias = XmlGuiaSerializer(many=True)


class TipoEmbalagemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEmbalagem
        exclude = ('id',)


class SolicitacaoRemessaSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitacaoRemessa
        fields = ('uuid', 'numero_solicitacao')


class ConferenciaIndividualPorAlimentoSerializer(serializers.ModelSerializer):
    conferencia = serializers.SlugRelatedField(
        slug_field='uuid',
        required=False,
        queryset=ConferenciaGuia.objects.all()
    )
    status_alimento = serializers.SerializerMethodField()
    tipo_embalagem = serializers.SerializerMethodField()
    ocorrencia = serializers.SerializerMethodField()

    def get_status_alimento(self, obj):
        return obj.get_status_alimento_display()

    def get_tipo_embalagem(self, obj):
        return obj.get_tipo_embalagem_display()

    def get_ocorrencia(self, obj):
        return obj.get_ocorrencia_display()

    class Meta:
        model = ConferenciaIndividualPorAlimento
        exclude = ('id',)


class ConferenciaComOcorrenciaSerializer(serializers.ModelSerializer):
    criado_por = UsuarioVinculoSerializer()
    conferencia_dos_alimentos = ConferenciaIndividualPorAlimentoSerializer(many=True)

    class Meta:
        model = ConferenciaGuia
        exclude = ('id',)


class GuiaDaRemessaComAlimentoSerializer(serializers.ModelSerializer):
    alimentos = AlimentoLookUpSerializer(many=True)
    conferencias = ConferenciaComOcorrenciaSerializer(many=True)
    status = serializers.CharField(source='get_status_display')

    class Meta:
        model = Guia
        exclude = ('id',)


class GuiaDaRemessaSerializer(serializers.ModelSerializer):
    numero_requisicao = serializers.CharField()
    alimentos = AlimentoLookUpSerializer(many=True)
    status = serializers.CharField(source='get_status_display')

    class Meta:
        model = Guia
        exclude = ('id',)


class GuiaDaRemessaComDistribuidorSerializer(serializers.ModelSerializer):
    nome_distribuidor = serializers.CharField()
    alimentos = AlimentoLookUpSerializer(many=True)
    status = serializers.CharField(source='get_status_display')

    class Meta:
        model = Guia
        exclude = ('id',)


class GuiaDaRemessaSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guia
        fields = ('uuid', 'numero_guia')


class InfoUnidadesSimplesDaGuiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guia
        fields = ('codigo_unidade', 'nome_unidade')


class AlimentoDaGuiaDaRemessaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alimento
        exclude = ('id',)


class AlimentoDaGuiaDaRemessaSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alimento
        fields = ('uuid', 'nome_alimento')


class SolicitacaoDeAlteracaoSerializer(serializers.ModelSerializer):
    motivo = serializers.CharField(source='get_motivo_display')
    requisicao = SolicitacaoRemessaSimplesSerializer(read_only=True, many=False)
    nome_distribuidor = serializers.CharField()
    qtd_guias = serializers.IntegerField()
    status = serializers.SerializerMethodField()
    criado_em = serializers.SerializerMethodField()
    data_entrega = serializers.SerializerMethodField()
    numero_requisicao = serializers.SerializerMethodField()

    def get_criado_em(self, obj):
        return obj.criado_em.strftime('%d/%m/%Y')

    def get_data_entrega(self, obj):
        return obj.data_entrega.strftime('%d/%m/%Y')

    def get_status(self, obj):
        return obj.get_status_display()

    def get_numero_requisicao(self, obj):
        return obj.requisicao.numero_solicitacao

    class Meta:
        model = SolicitacaoDeAlteracaoRequisicao
        exclude = ('id',)


class SolicitacaoDeAlteracaoSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitacaoDeAlteracaoRequisicao
        fields = ('uuid', 'numero_solicitacao')


class ConferenciaDaGuiaSerializer(serializers.ModelSerializer):
    criado_por = UsuarioVinculoSerializer()

    class Meta:
        model = ConferenciaGuia
        exclude = ('id',)


class InsucessoDeEntregaGuiaSerializer(serializers.ModelSerializer):
    guia = GuiaDaRemessaSimplesSerializer()
    criado_por = UsuarioVinculoSerializer()
    motivo = serializers.CharField(source='get_motivo_display')

    class Meta:
        model = InsucessoEntregaGuia
        exclude = ('id',)
