from datetime import datetime, timedelta

from django.db.models import Count
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from src.escola.models import Escola, Lote, PeriodoEscolar, TipoUnidadeEscolar

from ..models import DiaLetivoSIGPAE


def parse_date(value):
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError:
        raise ValidationError(f"Formato de data inválido: {value}. Use DD/MM/YYYY")


def python_weekday_to_business(weekday):
    return weekday


class RecorrenciaSerializer(serializers.Serializer):
    data_inicial = serializers.CharField()
    data_final = serializers.CharField()
    periodos_escolares = serializers.ListField(child=serializers.UUIDField())
    dias_semana = serializers.ListField(child=serializers.CharField())

    def validate_data_inicial(self, value):
        return parse_date(value)

    def validate_data_final(self, value):
        return parse_date(value)

    def validate(self, attrs):
        if attrs["data_inicial"] > attrs["data_final"]:
            raise ValidationError("data_inicial não pode ser maior que data_final")
        for dia in attrs["dias_semana"]:
            try:
                dia_int = int(dia)
                if dia_int < 0 or dia_int > 6:
                    raise ValueError
            except (ValueError, TypeError):
                raise ValidationError(
                    f"dias_semana deve conter valores entre 0 e 6. "
                    f"Valor inválido: {dia}"
                )
        return attrs


class DiaLetivoCreateSerializer(serializers.Serializer):
    recorrencias = RecorrenciaSerializer(many=True)
    lotes = serializers.ListField(child=serializers.UUIDField())
    tipos_unidades = serializers.ListField(child=serializers.UUIDField())
    unidades_educacionais = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )

    def validate_lotes(self, value):
        if not value:
            raise ValidationError("lotes é obrigatório")
        return value

    def validate_tipos_unidades(self, value):
        if not value:
            raise ValidationError("tipos_unidades é obrigatório")
        return value

    def validate_recorrencias(self, value):
        if not value:
            raise ValidationError("recorrencias é obrigatório")
        return value

    def create(self, validated_data):
        recorrencias = validated_data["recorrencias"]
        lotes_uuids = validated_data["lotes"]
        tipos_unidades_uuids = validated_data["tipos_unidades"]
        unidades_educacionais_uuids = validated_data.get("unidades_educacionais", [])

        lotes = list(Lote.objects.filter(uuid__in=lotes_uuids))
        tipos_unidades = list(
            TipoUnidadeEscolar.objects.filter(uuid__in=tipos_unidades_uuids)
        )
        escolas = (
            list(Escola.objects.filter(uuid__in=unidades_educacionais_uuids))
            if unidades_educacionais_uuids
            else []
        )

        created = []

        for rec in recorrencias:
            data_inicial = rec["data_inicial"]
            data_final = rec["data_final"]
            periodos_uuids = rec["periodos_escolares"]
            dias_semana = [int(d) for d in rec["dias_semana"]]

            periodos = list(PeriodoEscolar.objects.filter(uuid__in=periodos_uuids))

            current = data_inicial
            while current <= data_final:
                dia_semana = python_weekday_to_business(current.weekday())

                if dia_semana in dias_semana:
                    self._check_duplicates(current, periodos, escolas)

                    dia_letivo = DiaLetivoSIGPAE.objects.create(
                        data=current,
                        criado_por=self.context["request"].user,
                    )
                    dia_letivo.lotes.set(lotes)
                    dia_letivo.tipos_unidade_escolar.set(tipos_unidades)
                    dia_letivo.periodos_escolares.set(periodos)
                    if escolas:
                        dia_letivo.escolas.set(escolas)
                    created.append(dia_letivo)

                current += timedelta(days=1)

        return created

    def _check_duplicates(self, data, periodos, escolas):
        for periodo in periodos:
            if escolas:
                for escola in escolas:
                    if DiaLetivoSIGPAE.objects.filter(
                        data=data,
                        periodos_escolares=periodo,
                        escolas=escola,
                    ).exists():
                        raise ValidationError(
                            f"Já existe um DiaLetivo cadastrado para a data "
                            f"{data.strftime('%d/%m/%Y')}, "
                            f"escola {escola.nome} e "
                            f"período escolar {periodo.nome}"
                        )
            else:
                if (
                    DiaLetivoSIGPAE.objects.filter(
                        data=data,
                        periodos_escolares=periodo,
                    )
                    .annotate(escola_count=Count("escolas"))
                    .filter(escola_count=0)
                    .exists()
                ):
                    raise ValidationError(
                        f"Já existe um DiaLetivo cadastrado para a data "
                        f"{data.strftime('%d/%m/%Y')} e "
                        f"período escolar {periodo.nome}"
                    )
