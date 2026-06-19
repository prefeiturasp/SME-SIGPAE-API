from datetime import datetime, timedelta

from django.db.models import Count
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from src.escola.models import Escola, Lote, PeriodoEscolar, TipoUnidadeEscolar

from ..models import DiaLetivoSIGPAE


def parse_date(value):
    """Converte uma string no formato DD/MM/YYYY para um objeto date.

    Args:
        value: String contendo a data no formato DD/MM/YYYY.

    Returns:
        datetime.date correspondente à string informada.

    Raises:
        ValidationError: Se a string não estiver no formato esperado.
    """
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError:
        raise ValidationError(f"Formato de data inválido: {value}. Use DD/MM/YYYY")


def python_weekday_to_business(weekday):
    """Converte o weekday do Python (0=Monday) para o formato de negócio.

    Atualmente, retorna o mesmo valor sem conversão. Serve como ponto
    de extensão para futuros mapeamentos de dias da semana.

    Args:
        weekday: Inteiro representando o dia da semana (0=Monday).

    Returns:
        Inteiro representando o dia da semana no formato de negócio.
    """
    return weekday


class RecorrenciaSerializer(serializers.Serializer):
    """Serializador para validar os dados de recorrência de dias letivos.

    Define o intervalo de datas, os períodos escolares e os dias da
    semana em que os dias letivos devem ser criados.
    """

    data_inicial = serializers.CharField()
    data_final = serializers.CharField()
    periodos_escolares = serializers.ListField(child=serializers.UUIDField())
    dias_semana = serializers.ListField(child=serializers.CharField())

    def validate_data_inicial(self, value):
        """Valida e converte a data inicial para o formato date."""
        return parse_date(value)

    def validate_data_final(self, value):
        """Valida e converte a data final para o formato date."""
        return parse_date(value)

    def validate(self, attrs):
        """Valida regras de negócio da recorrência.

        Verifica se data_inicial não é maior que data_final e se todos
        os valores em dias_semana estão no intervalo válido (0 a 6).

        Raises:
            ValidationError: Se alguma validação falhar.
        """
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
    """Serializador para criação em lote de dias letivos.

    Recebe uma ou mais recorrências e as entidades relacionadas (lotes,
    tipos de unidades e unidades educacionais) para gerar os registros
    de dias letivos no banco.
    """

    recorrencias = RecorrenciaSerializer(many=True)
    lotes = serializers.ListField(child=serializers.UUIDField())
    tipos_unidades = serializers.ListField(child=serializers.UUIDField())
    unidades_educacionais = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )

    def validate_lotes(self, value):
        """Valida se o campo lotes não está vazio."""
        if not value:
            raise ValidationError("lotes é obrigatório")
        return value

    def validate_tipos_unidades(self, value):
        """Valida se o campo tipos_unidades não está vazio."""
        if not value:
            raise ValidationError("tipos_unidades é obrigatório")
        return value

    def validate_recorrencias(self, value):
        """Valida se o campo recorrencias não está vazio."""
        if not value:
            raise ValidationError("recorrencias é obrigatório")
        return value

    def create(self, validated_data):
        """Cria os dias letivos recursivamente conforme as recorrências.

        Itera sobre cada recorrência, percorrendo o intervalo de datas
        e criando registros de DiaLetivoSIGPAE para os dias da semana
        especificados. Realiza validação de duplicatas antes de criar.

        Returns:
            Lista de instâncias de DiaLetivoSIGPAE criadas.
        """
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
        """Verifica se já existe DiaLetivo duplicado para os parâmetros informados.

        Para cada período, verifica se já existe um registro com a mesma
        data, período e escola (ou sem escola vinculada, dependendo da
        lista de escolas fornecida).

        Args:
            data: Data do dia letivo a ser verificada.
            periodos: Lista de instâncias de PeriodoEscolar.
            escolas: Lista de instâncias de Escola (pode ser vazia).

        Raises:
            ValidationError: Se encontrar um registro duplicado.
        """
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
