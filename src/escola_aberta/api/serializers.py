from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from src.cardapio.base.models import TipoAlimentacao
from src.dados_comuns.utils import parse_date
from src.escola.models import Escola, Lote

from ..models import (
    EscolaAberta,
    EscolaAbertaUnidadeParticipante,
)


class RecorrenciaSerializer(serializers.Serializer):
    data_inicial = serializers.CharField()
    data_final = serializers.CharField()
    dias_semana = serializers.ListField(child=serializers.CharField())

    def validate_data_inicial(self, value):
        return parse_date(value)

    def validate_data_final(self, value):
        return parse_date(value)

    def validate(self, attrs):
        if attrs["data_inicial"] > attrs["data_final"]:
            raise ValidationError("data_inicial não pode ser maior que data_final")
        if not attrs["dias_semana"]:
            raise ValidationError("Selecione ao menos um dia da semana")
        try:
            dias = [int(d) for d in attrs["dias_semana"]]
        except (ValueError, TypeError):
            raise ValidationError("dias_semana deve conter valores entre 0 e 6")
        if any(d < 0 or d > 6 for d in dias):
            raise ValidationError("dias_semana deve conter valores entre 0 e 6")
        attrs["dias_semana"] = sorted({str(d) for d in dias})
        return attrs


class EscolaAbertaUnidadeParticipanteCreateSerializer(serializers.Serializer):
    lote = serializers.UUIDField()
    unidade_educacional = serializers.UUIDField()
    tipos_alimentacao = serializers.ListField(
        child=serializers.UUIDField(), allow_empty=False
    )
    num_participantes = serializers.IntegerField(
        required=True, allow_null=False, min_value=1
    )


class EscolaAbertaCreateSerializer(serializers.Serializer):
    recorrencias = RecorrenciaSerializer()
    unidades_participantes = EscolaAbertaUnidadeParticipanteCreateSerializer(
        many=True, allow_empty=False
    )

    def validate_unidades_participantes(self, value):
        uuids = [u["unidade_educacional"] for u in value]
        if len(uuids) != len(set(uuids)):
            raise ValidationError("Há unidades educacionais repetidas")
        return value

    def validate(self, attrs):
        escolas_uuids = [
            u["unidade_educacional"] for u in attrs["unidades_participantes"]
        ]
        rec = attrs["recorrencias"]

        qs = EscolaAbertaUnidadeParticipante.objects.filter(
            unidade_educacional__uuid__in=escolas_uuids,
            escola_aberta__data_inicial__lte=rec["data_final"],
            escola_aberta__data_final__gte=rec["data_inicial"],
            escola_aberta__dias_semana__overlap=rec["dias_semana"],
        )
        if self.instance:
            qs = qs.exclude(escola_aberta=self.instance)

        if qs.exists():
            raise ValidationError(
                {
                    "non_field_errors": [
                        "Já existe um cadastro com esta combinação de UE, período de realização e dia da semana"
                    ]
                }
            )
        return attrs

    def _carregar_referencias(self, unidades):
        lotes_uuids = {u["lote"] for u in unidades}
        escolas_uuids = {u["unidade_educacional"] for u in unidades}
        alimentos_uuids = {a for u in unidades for a in u["tipos_alimentacao"]}

        lotes = {x.uuid: x for x in Lote.objects.filter(uuid__in=lotes_uuids)}
        escolas = {x.uuid: x for x in Escola.objects.filter(uuid__in=escolas_uuids)}
        alimentos = {
            x.uuid: x for x in TipoAlimentacao.objects.filter(uuid__in=alimentos_uuids)
        }
        if len(lotes) != len(lotes_uuids):
            raise ValidationError("Um ou mais lotes não foram encontrados")
        if len(escolas) != len(escolas_uuids):
            raise ValidationError("Uma ou mais unidades educacionais não foram encontradas")
        if len(alimentos) != len(alimentos_uuids):
            raise ValidationError("Um ou mais tipos de alimentação não foram encontrados")
        return lotes, escolas, alimentos

    def _criar_unidades(self, escola_aberta, unidades):
        lotes, escolas, alimentos = self._carregar_referencias(unidades)
        for u in unidades:
            unidade = EscolaAbertaUnidadeParticipante.objects.create(
                escola_aberta=escola_aberta,
                lote=lotes[u["lote"]],
                unidade_educacional=escolas[u["unidade_educacional"]],
                num_participantes=u["num_participantes"],
            )
            unidade.tipos_alimentacao.set(
                [alimentos[a] for a in set(u["tipos_alimentacao"])]
            )

    def create(self, validated_data):
        rec = validated_data["recorrencias"]
        unidades = validated_data["unidades_participantes"]
        user = self.context["request"].user

        with transaction.atomic():
            escola_aberta = EscolaAberta.objects.create(
                criado_por=user,
                data_inicial=rec["data_inicial"],
                data_final=rec["data_final"],
                dias_semana=rec["dias_semana"],
            )
            self._criar_unidades(escola_aberta, unidades)
        return escola_aberta

    def update(self, instance, validated_data):
        rec = validated_data["recorrencias"]
        unidades = validated_data["unidades_participantes"]

        with transaction.atomic():
            instance.data_inicial = rec["data_inicial"]
            instance.data_final = rec["data_final"]
            instance.dias_semana = rec["dias_semana"]
            instance.save()

            instance.unidades_participantes.all().delete()
            self._criar_unidades(instance, unidades)
        return instance


class EscolaAbertaUnidadeParticipanteReadSerializer(serializers.ModelSerializer):
    lote = serializers.UUIDField(source="lote.uuid")
    lote_nome = serializers.SerializerMethodField()
    unidade_educacional = serializers.UUIDField(source="unidade_educacional.uuid")
    unidade_educacional_nome = serializers.CharField(source="unidade_educacional.nome")
    tipos_alimentacao = serializers.SerializerMethodField()

    def get_lote_nome(self, obj):
        lote = obj.lote
        iniciais = lote.diretoria_regional.iniciais
        return f"{lote.nome} - {iniciais}" if iniciais else lote.nome

    def get_tipos_alimentacao(self, obj):
        return [{"uuid": t.uuid, "nome": t.nome} for t in obj.tipos_alimentacao.all()]

    class Meta:
        model = EscolaAbertaUnidadeParticipante
        fields = (
            "uuid",
            "lote",
            "lote_nome",
            "unidade_educacional",
            "unidade_educacional_nome",
            "num_participantes",
            "tipos_alimentacao",
        )


class EscolaAbertaReadSerializer(serializers.ModelSerializer):
    data_inicial = serializers.DateField(format="%d/%m/%Y")
    data_final = serializers.DateField(format="%d/%m/%Y")
    unidades_participantes = EscolaAbertaUnidadeParticipanteReadSerializer(many=True)

    class Meta:
        model = EscolaAberta
        fields = (
            "uuid",
            "data_inicial",
            "data_final",
            "dias_semana",
            "unidades_participantes",
            "criado_em",
        )
