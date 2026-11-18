from __future__ import annotations

from rest_framework import serializers

from ....dados_comuns.utils import update_instance_from_dict
from ....perfil.models import Usuario
from ....terceirizada.models import Edital
from ...models import (
    DiaSuspensaoAtividades,
    Escola,
    EscolaPeriodoEscolar,
    LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar,
    PeriodoEscolar,
    TipoUnidadeEscolar,
)


class EscolaPeriodoEscolarCreateSerializer(serializers.ModelSerializer):
    escola = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Escola.objects.all()
    )
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", queryset=PeriodoEscolar.objects.all()
    )
    quantidade_alunos = serializers.IntegerField()
    quantidade_alunos_anterior = serializers.IntegerField(required=False)
    justificativa = serializers.CharField(required=False)

    def update(self, instance, validated_data):
        escola = validated_data.get("escola")
        periodo_escolar = validated_data.get("periodo_escolar")
        quantidade_alunos_para = validated_data.get("quantidade_alunos")
        quantidade_alunos_de = validated_data.pop("quantidade_alunos_anterior")
        justificativa = validated_data.pop("justificativa")
        criado_por = self.context["request"].user

        log = LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar(
            escola=escola,
            periodo_escolar=periodo_escolar,
            quantidade_alunos_para=quantidade_alunos_para,
            quantidade_alunos_de=quantidade_alunos_de,
            criado_por=criado_por,
            justificativa=justificativa,
        )
        log.save()
        update_instance_from_dict(instance, validated_data, save=True)
        return instance

    class Meta:
        model = EscolaPeriodoEscolar
        exclude = ("id",)


class DiaSuspensaoAtividadesCreateSerializer(serializers.ModelSerializer):
    tipo_unidade = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=TipoUnidadeEscolar.objects.all(),
        required=True,
    )

    criado_por = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Usuario.objects.all(), required=True
    )

    class Meta:
        model = DiaSuspensaoAtividades
        exclude = ("id",)


class CadastroCalendarioCreateSerializer(serializers.ModelSerializer):
    tipo_unidades = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=TipoUnidadeEscolar.objects.all(),
        required=True,
        many=True,
    )
    editais = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Edital.objects.all(),
        required=True,
        many=True,
    )

    class Meta:
        model = DiaSuspensaoAtividades
        fields = ("tipo_unidades", "editais")


class DiaSuspensaoAtividadesCreateManySerializer(serializers.ModelSerializer):
    cadastros_calendario = CadastroCalendarioCreateSerializer(many=True, required=True)

    def create(self, validated_data):
        """Cria ou atualiza dias de suspensao de atividades"""
        DiaSuspensaoAtividades.objects.filter(data=validated_data["data"]).delete()
        dia_calendario = None
        for cadastro in validated_data["cadastros_calendario"]:
            for tipo_unidade in cadastro["tipo_unidades"]:
                for edital in cadastro["editais"]:
                    if not DiaSuspensaoAtividades.objects.filter(
                        data=validated_data["data"],
                        tipo_unidade=tipo_unidade,
                        edital=edital,
                    ):
                        dia_sobremesa_doce = DiaSuspensaoAtividades(
                            criado_por=self.context["request"].user,
                            data=validated_data["data"],
                            tipo_unidade=tipo_unidade,
                            edital=edital,
                        )
                        dia_sobremesa_doce.save()
        return dia_calendario

    class Meta:
        model = DiaSuspensaoAtividades
        fields = ("data", "uuid", "cadastros_calendario")
