from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.validators import (
    precisa_pertencer_a_um_tipo_de_alimentacao,
    valida_duplicidade_solicitacoes_lanche_emergencial,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    AlteracaoCardapio,
    DataIntervaloAlteracaoCardapio,
    MotivoAlteracaoCardapio,
    SubstituicaoAlimentacaoNoPeriodoEscolar,
)
from sme_sigpae_api.cardapio.base.models import TipoAlimentacao
from sme_sigpae_api.dados_comuns.utils import update_instance_from_dict
from sme_sigpae_api.dados_comuns.validators import (
    deve_pedir_com_antecedencia,
    deve_ser_no_mesmo_ano_corrente,
    nao_pode_ser_no_passado,
    valida_datas_alteracao_cardapio,
    valida_duplicidade_solicitacoes,
)
from sme_sigpae_api.escola.models import DiaCalendario, Escola, PeriodoEscolar
from sme_sigpae_api.escola.utils import eh_dia_sem_atividade_escolar


class SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreateBase(
    serializers.ModelSerializer
):
    """Define os campos base para escrita de substituicoes por periodo.

    Recebe referencias por UUID para o periodo escolar e para os tipos de
    alimentacao de origem ao criar ou atualizar uma alteracao de cardapio.

    Viewsets que utilizam este serializer:
        - Nenhum diretamente.
        - Uso indireto em ``AlteracoesCardapioViewSet``, por meio de
          ``SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreate``
          aninhado em ``AlteracaoCardapioSerializerCreate`` nas actions
          ``create``, ``update`` e ``partial_update``.
    """

    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=PeriodoEscolar.objects.all()
    )

    tipos_alimentacao_de = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        many=True,
        queryset=TipoAlimentacao.objects.all(),
    )


class SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreate(
    SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreateBase
):
    """Serializa a escrita completa de substituicoes por periodo escolar.

    Complementa o serializer base com a alteracao de cardapio de destino e os
    tipos de alimentacao para os quais a refeicao sera convertida.

    Viewsets que utilizam este serializer:
        - Nenhum diretamente.
        - Uso indireto em ``AlteracoesCardapioViewSet``, aninhado em
          ``AlteracaoCardapioSerializerCreate`` nas actions ``create``,
          ``update`` e ``partial_update``.
    """

    alteracao_cardapio = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=AlteracaoCardapio.objects.all()
    )
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=PeriodoEscolar.objects.all()
    )

    tipos_alimentacao_para = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        many=True,
        queryset=TipoAlimentacao.objects.all(),
    )

    def create(self, validated_data):
        """Cria uma substituicao de alimentacao com relacionamentos many-to-many.

        Args:
            validated_data (dict): Dados validados pelo serializer, incluindo
                ``tipos_alimentacao_de`` e ``tipos_alimentacao_para``.

        Returns:
            SubstituicaoAlimentacaoNoPeriodoEscolar: Instancia criada com os
            tipos de alimentacao de origem e destino vinculados.
        """
        tipos_alimentacao_de = validated_data.pop("tipos_alimentacao_de")
        tipos_alimentacao_para = validated_data.pop("tipos_alimentacao_para")
        substituicao_alimentacao = (
            SubstituicaoAlimentacaoNoPeriodoEscolar.objects.create(**validated_data)
        )
        substituicao_alimentacao.tipos_alimentacao_de.set(tipos_alimentacao_de)
        substituicao_alimentacao.tipos_alimentacao_para.set(tipos_alimentacao_para)
        return substituicao_alimentacao

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolar
        exclude = ("id",)


class AlteracaoCardapioSerializerCreateBase(serializers.ModelSerializer):
    """Define os campos comuns de escrita para alteracoes de cardapio.

    Resolve referencias por UUID de escola e motivo e concentra a logica basica
    de criacao e atualizacao das substituicoes vinculadas.

    Viewsets que utilizam este serializer:
        - Nenhum diretamente.
        - Uso indireto em ``AlteracoesCardapioViewSet``, como classe base de
          ``AlteracaoCardapioSerializerCreate`` nas actions ``create``,
          ``update`` e ``partial_update``.
    """

    motivo = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=MotivoAlteracaoCardapio.objects.all()
    )
    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Escola.objects.all()
    )
    status_explicacao = serializers.CharField(
        source="status", required=False, read_only=True
    )

    def create(self, validated_data):
        """Cria uma alteracao de cardapio usando a estrategia base do serializer.

        Args:
            validated_data (dict): Dados validados da solicitacao, contendo a
                lista de ``substituicoes`` ja validada.

        Returns:
            AlteracaoCardapio: Instancia criada com as substituicoes vinculadas.
        """
        substituicoes = validated_data.pop("substituicoes")
        validated_data["criado_por"] = self.context["request"].user

        substituicoes_lista = []
        for substituicao in substituicoes:
            substituicoes_object = self.Meta.serializer_substituicao().create(
                substituicao
            )
            substituicoes_lista.append(substituicoes_object)
        alteracao_cardapio = self.Meta.model.objects.create(**validated_data)
        alteracao_cardapio.substituicoes.set(substituicoes_lista)

        return alteracao_cardapio

    def update(self, instance, validated_data):
        """Atualiza uma alteracao de cardapio recriando suas substituicoes.

        Args:
            instance (AlteracaoCardapio): Instancia a ser atualizada.
            validated_data (dict): Dados validados recebidos na requisicao.

        Returns:
            AlteracaoCardapio: Instancia atualizada e salva.
        """
        substituicoes_json = validated_data.pop("substituicoes")
        instance.substituicoes.all().delete()

        substituicoes_lista = []
        for substituicao_json in substituicoes_json:
            substituicoes_object = self.Meta.serializer_substituicao().create(
                substituicao_json
            )
            substituicoes_lista.append(substituicoes_object)

        update_instance_from_dict(instance, validated_data)
        instance.substituicoes.set(substituicoes_lista)
        instance.save()

        return instance


class DatasIntervaloAlteracaoCardapioSerializerCreateSerializer(
    serializers.ModelSerializer
):
    """Serializa as datas individuais do intervalo na escrita da solicitacao.

    Recebe a referencia da alteracao de cardapio por UUID quando necessario e
    persiste cada ``DataIntervaloAlteracaoCardapio`` associada ao pedido.

    Viewsets que utilizam este serializer:
        - Nenhum diretamente.
        - Uso indireto em ``AlteracoesCardapioViewSet``, aninhado em
          ``AlteracaoCardapioSerializerCreate`` nas actions ``create``,
          ``update`` e ``partial_update``.
        - Uso indireto em ``AlteracoesCardapioViewSet``, aninhado em
          ``AlteracaoCardapioSerializer`` nas respostas detalhadas de leitura.
    """

    alteracao_cardapio = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=AlteracaoCardapio.objects.all()
    )

    def create(self, validated_data):
        """Cria um registro de data individual do intervalo da solicitacao.

        Args:
            validated_data (dict): Dados validados da data do intervalo.

        Returns:
            DataIntervaloAlteracaoCardapio: Instancia criada.
        """
        data_intervalo = DataIntervaloAlteracaoCardapio.objects.create(**validated_data)
        return data_intervalo

    class Meta:
        model = DataIntervaloAlteracaoCardapio
        exclude = ("id",)


class AlteracaoCardapioSerializerCreate(AlteracaoCardapioSerializerCreateBase):
    """Serializa a criacao e atualizacao completas de alteracoes de cardapio.

    Valida datas e regras de negocio, resolve relacionamentos por UUID e cria
    as substituicoes e datas do intervalo associadas ao pedido.

    Viewsets que utilizam este serializer:
        - ``AlteracoesCardapioViewSet``: retornado por
          ``get_serializer_class()`` nas actions ``create``, ``update`` e
          ``partial_update``.
    """

    substituicoes = SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreate(many=True)
    datas_intervalo = DatasIntervaloAlteracaoCardapioSerializerCreateSerializer(
        required=False, many=True
    )

    def validate(self, attrs):
        """Aplica as validacoes de negocio da solicitacao de alteracao.

        Args:
            attrs (dict): Dados normalizados pelo serializer antes da criacao
                ou atualizacao da instancia.

        Returns:
            dict: Os mesmos atributos recebidos, apos passarem pelas
            validacoes de consistencia e regras de negocio.

        Raises:
            ValidationError: Quando datas, motivo ou substituicoes violam as
                regras do dominio.
        """
        escola = attrs.get("escola")
        substituicoes = attrs.get("substituicoes")
        for substicuicao in substituicoes:
            tipos_alimentacao_de = substicuicao.get("tipos_alimentacao_de")
            tipo_alimentacao_para = substicuicao.get("tipo_alimentacao_para")
            periodo_escolar = substicuicao.get("periodo_escolar")
            precisa_pertencer_a_um_tipo_de_alimentacao(
                tipos_alimentacao_de,
                tipo_alimentacao_para,
                escola.tipo_unidade,
                periodo_escolar,
            )
        valida_datas_alteracao_cardapio(attrs)
        nao_pode_ser_no_passado(attrs["data_inicial"])
        if attrs["motivo"].nome != "Lanche Emergencial":
            deve_pedir_com_antecedencia(attrs["data_inicial"])
        if attrs["motivo"].nome == "RPL - Refeição por Lanche":
            valida_duplicidade_solicitacoes(attrs)
        deve_ser_no_mesmo_ano_corrente(attrs["data_inicial"])

        return attrs

    def datas_nos_meses_de_ferias(self, datas_intervalo):
        """Verifica se o intervalo toca algum mes considerado de ferias.

        Meses de férias:
          - Janeiro: período de férias escolares de verão.
          - Julho: período de férias escolares de inverno.
          - Dezembro: período de férias escolares de verão e festas de fim de ano.

        Args:
            datas_intervalo (list[dict]): Lista de itens com a chave ``data``.

        Returns:
            bool: ``True`` quando a primeira ou a ultima data do intervalo esta
            em janeiro, julho ou dezembro.
        """
        JANEIRO = 1
        JULHO = 7
        DEZEMBRO = 12

        MESES_DE_FERIAS = [JANEIRO, JULHO, DEZEMBRO]
        return (
            datas_intervalo[0]["data"].month in MESES_DE_FERIAS
            or datas_intervalo[-1]["data"].month in MESES_DE_FERIAS
        )

    def criar_datas_intervalo(self, datas_intervalo, instance):
        """Cria as datas individuais do intervalo vinculadas a uma solicitacao.

        Para pedidos de Lanche Emergencial, aplica validacoes extras para dias
        letivos e ignora dias sem atividade escolar fora dos meses de ferias.

        Args:
            datas_intervalo (list[dict]): Datas validadas a serem persistidas.
            instance (AlteracaoCardapio): Solicitacao dona das datas.

        Returns:
            None

        Raises:
            ValidationError: Quando uma solicitacao de Lanche Emergencial nao
                possui ao menos um dia letivo fora dos meses de ferias.
        """
        datas_intervalo = [
            dict(item, **{"alteracao_cardapio": instance}) for item in datas_intervalo
        ]
        if not instance.eh_alteracao_lanche_emergencial():
            for data_intervalo in datas_intervalo:
                DataIntervaloAlteracaoCardapio.objects.create(**data_intervalo)
        else:
            if not DiaCalendario.pelo_menos_um_dia_letivo(
                instance.escola,
                [data_intervalo["data"] for data_intervalo in datas_intervalo],
                instance,
            ) and not self.datas_nos_meses_de_ferias(datas_intervalo):
                raise ValidationError(
                    "Não é possível solicitar Lanche Emergencial para dia(s) não letivo(s)"
                )
            for data_intervalo in datas_intervalo:
                if eh_dia_sem_atividade_escolar(
                    instance.escola, data_intervalo["data"], instance
                ) and not self.datas_nos_meses_de_ferias(datas_intervalo):
                    continue
                DataIntervaloAlteracaoCardapio.objects.create(**data_intervalo)

    def criar_substituicoes(self, substituicoes, instance):
        """Cria as substituicoes de alimentacao vinculadas a uma solicitacao.

        Args:
            substituicoes (list[dict]): Itens validados com periodo escolar e
                tipos de alimentacao de origem e destino.
            instance (AlteracaoCardapio): Solicitacao dona das substituicoes.

        Returns:
            None
        """
        substituicoes = [
            dict(item, **{"alteracao_cardapio": instance}) for item in substituicoes
        ]
        for substituicao in substituicoes:
            tipos_alimentacao_de = substituicao.pop("tipos_alimentacao_de")
            tipos_alimentacao_para = substituicao.pop("tipos_alimentacao_para")
            substituicao_alimentacao = (
                SubstituicaoAlimentacaoNoPeriodoEscolar.objects.create(**substituicao)
            )
            substituicao_alimentacao.tipos_alimentacao_de.set(tipos_alimentacao_de)
            substituicao_alimentacao.tipos_alimentacao_para.set(tipos_alimentacao_para)

    def create(self, validated_data):
        """Cria uma alteracao de cardapio completa com datas e substituicoes.

        Args:
            validated_data (dict): Dados validados da solicitacao, incluindo
                listas aninhadas de ``substituicoes`` e ``datas_intervalo``.

        Returns:
            AlteracaoCardapio: Instancia criada com seus relacionamentos.

        Raises:
            ValidationError: Quando houver duplicidade indevida de solicitacao
                de Lanche Emergencial.
        """
        valida_duplicidade_solicitacoes_lanche_emergencial(validated_data)
        validated_data["criado_por"] = self.context["request"].user
        substituicoes = validated_data.pop("substituicoes")
        datas_intervalo = validated_data.pop("datas_intervalo", [])
        alteracao_cardapio = AlteracaoCardapio.objects.create(**validated_data)

        self.criar_substituicoes(substituicoes, alteracao_cardapio)
        self.criar_datas_intervalo(datas_intervalo, alteracao_cardapio)

        return alteracao_cardapio

    def update(self, instance, validated_data):
        """Atualiza uma alteracao de cardapio recriando datas e substituicoes.

        Args:
            instance (AlteracaoCardapio): Instancia existente a ser atualizada.
            validated_data (dict): Dados validados da requisicao.

        Returns:
            AlteracaoCardapio: Instancia atualizada com seus relacionamentos
            recriados.

        Raises:
            ValidationError: Quando houver duplicidade indevida de solicitacao
                de Lanche Emergencial.
        """
        valida_duplicidade_solicitacoes_lanche_emergencial(validated_data)
        instance.substituicoes.all().delete()
        instance.datas_intervalo.all().delete()

        validated_data["criado_por"] = self.context["request"].user
        substituicoes = validated_data.pop("substituicoes")
        datas_intervalo = validated_data.pop("datas_intervalo", [])
        update_instance_from_dict(instance, validated_data)
        instance.save()

        self.criar_substituicoes(substituicoes, instance)
        self.criar_datas_intervalo(datas_intervalo, instance)

        return instance

    class Meta:
        model = AlteracaoCardapio
        serializer_substituicao = (
            SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreate
        )
        exclude = ("id", "status")
