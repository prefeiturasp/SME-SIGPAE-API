from rest_framework import serializers

from src.escola.api.serializers import (
    PeriodoEscolarParaFiltroSerializer,
    TipoUnidadeParaFiltroSerializer,
)
from src.escola.models import Lote

from ..models import DiaLetivoSIGPAE


class LoteNomeIniciaisSerializer(serializers.ModelSerializer):
    """Serializador reduzido de Lote com uuid, nome e iniciais."""

    class Meta:
        model = Lote
        fields = ("uuid", "nome", "iniciais")


class DiaLetivoSerializer(serializers.ModelSerializer):
    """Serializador de leitura para dias letivos.

    Expõe os dados do dia letivo com as entidades relacionadas
    (lotes, tipos de unidade escolar, períodos escolares), além
    da contagem de unidades escolares e a lista de números dos
    editais associados às escolas do registro.
    """

    lotes = LoteNomeIniciaisSerializer(many=True)
    tipos_unidade_escolar = TipoUnidadeParaFiltroSerializer(many=True)
    periodos_escolares = PeriodoEscolarParaFiltroSerializer(many=True)
    unidades_escolares = serializers.SerializerMethodField()
    editais_numeros = serializers.SerializerMethodField()

    def get_unidades_escolares(self, obj: DiaLetivoSIGPAE):
        """Retorna os nomes das escolas vinculadas (até 3) ou o total."""
        escolas_qs = obj.escolas.all()
        count = len(escolas_qs)
        if count == 0:
            return None
        if 1 <= count <= 3:
            return ", ".join(e.nome for e in escolas_qs)
        return count

    def get_editais_numeros(self, obj: DiaLetivoSIGPAE):
        """Retorna os números dos editais dos contratos ativos dos lotes."""
        numeros = set()
        for lote in obj.lotes.all():
            self._collect_numeros_do_lote(numeros, lote)
        return list(numeros) if numeros else None

    @staticmethod
    def _collect_numeros_do_lote(numeros: set, lote) -> None:
        """Adiciona ao set os números dos editais dos contratos ativos do lote."""
        if lote is None:
            return
        for contrato in lote.contratos_do_lote.all():
            if contrato.encerrado or contrato.edital_id is None:
                continue
            numeros.add(contrato.edital.numero)

    class Meta:
        model = DiaLetivoSIGPAE
        fields = (
            "uuid",
            "data",
            "lotes",
            "tipos_unidade_escolar",
            "periodos_escolares",
            "unidades_escolares",
            "editais_numeros",
        )


class DiaLetivoDetailSerializer(serializers.ModelSerializer):
    lotes = serializers.SerializerMethodField()
    tipos_unidades = serializers.SerializerMethodField()
    unidades_educacionais = serializers.SerializerMethodField()
    periodos_escolares = serializers.SerializerMethodField()

    def get_lotes(self, obj: DiaLetivoSIGPAE):
        return [str(lote.uuid) for lote in obj.lotes.all()]

    def get_tipos_unidades(self, obj: DiaLetivoSIGPAE):
        return [str(tipo.uuid) for tipo in obj.tipos_unidade_escolar.all()]

    def get_unidades_educacionais(self, obj: DiaLetivoSIGPAE):
        return [str(escola.uuid) for escola in obj.escolas.all()]

    def get_periodos_escolares(self, obj: DiaLetivoSIGPAE):
        return [str(periodo.uuid) for periodo in obj.periodos_escolares.all()]

    class Meta:
        model = DiaLetivoSIGPAE
        fields = (
            "uuid",
            "data",
            "lotes",
            "tipos_unidades",
            "unidades_educacionais",
            "periodos_escolares",
        )


class DiaLetivoCalendarioSerializer(serializers.ModelSerializer):
    periodos_escolares = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='nome'
    )

    class Meta:
        model = DiaLetivoSIGPAE
        fields = ("data","periodos_escolares")
