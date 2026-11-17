from __future__ import annotations

from rest_framework import serializers

from ...aluno.api.serializers import FaixaEtariaSerializer
from ...escola.api.serializers import PeriodoEscolarSimplesSerializer
from ...models import (
    Escola,
    LogAlunosMatriculadosFaixaEtariaDia,
    LogAlunosMatriculadosPeriodoEscola,
)


class LogAlunosMatriculadosPeriodoEscolaSerializer(serializers.ModelSerializer):
    dia = serializers.SerializerMethodField()
    periodo_escolar = PeriodoEscolarSimplesSerializer()

    def get_dia(self, obj):
        return obj.criado_em.strftime("%d")

    class Meta:
        model = LogAlunosMatriculadosPeriodoEscola
        exclude = ("id", "uuid", "observacao")


class LogAlunosMatriculadosFaixaEtariaDiaSerializer(serializers.ModelSerializer):
    escola = serializers.SlugRelatedField(
        slug_field="nome", required=False, queryset=Escola.objects.all()
    )
    periodo_escolar = serializers.CharField(
        source="periodo_escolar.nome", required=False
    )
    dia = serializers.SerializerMethodField()
    faixa_etaria = FaixaEtariaSerializer()

    def get_dia(self, obj):
        day = str(obj.data.day)
        return day if len(day) == 2 else "0" + day

    class Meta:
        model = LogAlunosMatriculadosFaixaEtariaDia
        exclude = ("id", "uuid", "criado_em")
