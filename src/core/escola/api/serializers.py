from __future__ import annotations

import datetime

from rest_framework import serializers

from ....cardapio.base.models import TipoAlimentacao
from ....dados_comuns.mixins.serializer_context import (
    EscolaNomeHistoricoSerializerMixin,
)
from ....terceirizada.models import Edital
from ...api.serializers_base import TipoGestaoSerializer
from ...diretoria_regional.api.serializers import (
    DiretoriaRegionalParaFiltroSerializer,
    DiretoriaRegionalSimplissimaSerializer,
)
from ...lote.api.serializers import (
    LoteComContratosSerializer,
    LoteNomeSerializer,
    LoteReclamacaoSerializer,
    LoteSerializer,
    LoteSimplesSerializer,
)
from ...models import (
    AlunosMatriculadosPeriodoEscola,
    DiaCalendario,
    DiaSuspensaoAtividades,
    DiretoriaRegional,
    Escola,
    EscolaPeriodoEscolar,
    GrupoUnidadeEscolar,
    PeriodoEscolar,
    TipoUnidadeEscolar,
)


class TipoAlimentacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAlimentacao
        exclude = ("id",)


class PeriodoEscolarSerializer(serializers.ModelSerializer):
    tipos_alimentacao = TipoAlimentacaoSerializer(many=True)
    possui_alunos_regulares = serializers.SerializerMethodField()

    def get_possui_alunos_regulares(self, obj):
        if "escola" not in self.context:
            return None
        return obj.alunos_matriculados.filter(
            escola=self.context["escola"], tipo_turma="REGULAR"
        ).exists()

    class Meta:
        model = PeriodoEscolar
        exclude = ("id",)


class PeriodoEscolarSimplesSerializer(serializers.ModelSerializer):
    # TODO: tirar tipos de alimentacao daqui, tipos de alimentacao são
    # relacionados a TIPOUE + PERIODOESCOLAR
    possui_alunos_regulares = serializers.SerializerMethodField()

    def get_possui_alunos_regulares(self, obj):
        if "escola" not in self.context:
            return None
        return obj.alunos_matriculados.filter(
            escola=self.context["escola"], tipo_turma="REGULAR"
        ).exists()

    class Meta:
        model = PeriodoEscolar
        exclude = ("id", "tipos_alimentacao")


class TipoUnidadeEscolarPeriodoEscolarTipoAlimentacaoSerializer(serializers.Serializer):
    uuid = serializers.CharField(read_only=True)
    nome = serializers.CharField(read_only=True)


class TipoUnidadeEscolarPeriodoEscolarSerializer(serializers.Serializer):
    uuid = serializers.CharField(read_only=True)
    nome = serializers.CharField(read_only=True)
    tipos_alimentacao = TipoUnidadeEscolarPeriodoEscolarTipoAlimentacaoSerializer(
        read_only=True, many=True
    )
    posicao = serializers.IntegerField(read_only=True)
    tipo_turno = serializers.IntegerField(read_only=True)
    possui_alunos_regulares = serializers.SerializerMethodField()

    def get_possui_alunos_regulares(self, obj):
        if "escola" not in self.context:
            return None
        return obj.alunos_matriculados.filter(
            escola=self.context["escola"], tipo_turma="REGULAR"
        ).exists()


class TipoUnidadeEscolarSerializer(serializers.ModelSerializer):
    periodos_escolares = TipoUnidadeEscolarPeriodoEscolarSerializer(many=True)

    class Meta:
        model = TipoUnidadeEscolar
        exclude = ("id",)


class PeriodoEscolarParaFiltroSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoEscolar
        fields = ("uuid", "nome")


class DiaCalendarioSerializer(serializers.ModelSerializer):
    escola = serializers.CharField(source="escola.nome")
    dia = serializers.SerializerMethodField()
    periodo_escolar = PeriodoEscolarParaFiltroSerializer()

    def get_dia(self, obj):
        return obj.data.strftime("%d")

    class Meta:
        model = DiaCalendario
        exclude = ("id", "uuid")


class TipoUnidadeEscolarSerializerSimples(serializers.ModelSerializer):
    class Meta:
        model = TipoUnidadeEscolar
        exclude = ("id", "periodos_escolares")


class EscolaSimplissimaSerializer(
    EscolaNomeHistoricoSerializerMixin, serializers.ModelSerializer
):
    nome = serializers.SerializerMethodField()
    lote = LoteReclamacaoSerializer()
    tipo_gestao = serializers.CharField()
    diretoria_regional = DiretoriaRegionalSimplissimaSerializer()
    tipo_unidade = TipoUnidadeEscolarSerializer()

    class Meta:
        model = Escola
        fields = (
            "uuid",
            "nome",
            "codigo_eol",
            "codigo_codae",
            "diretoria_regional",
            "lote",
            "quantidade_alunos",
            "tipo_gestao",
            "tipo_unidade",
        )


class EscolaParaFiltrosDiretoriaRegionalReadOnlySerializer(serializers.Serializer):
    uuid = serializers.CharField(read_only=True)
    nome = serializers.CharField(read_only=True)


class EscolaParaFiltrosTipoUnidadeReadOnlySerializer(serializers.Serializer):
    uuid = serializers.CharField(read_only=True)
    iniciais = serializers.CharField(read_only=True)


class EscolaParaFiltrosLoteReadOnlySerializer(serializers.Serializer):
    uuid = serializers.CharField(read_only=True)
    nome = serializers.CharField(read_only=True)


class EscolaParaFiltrosPeriodoEscolarReadOnlySerializer(serializers.Serializer):
    uuid = serializers.CharField(read_only=True)
    nome = serializers.CharField(read_only=True)


class EscolaParaFiltrosReadOnlySerializer(serializers.Serializer):
    uuid = serializers.CharField(read_only=True)
    nome = serializers.CharField(read_only=True)
    codigo_eol = serializers.CharField(read_only=True)
    diretoria_regional = EscolaParaFiltrosDiretoriaRegionalReadOnlySerializer()
    tipo_unidade = EscolaParaFiltrosTipoUnidadeReadOnlySerializer()
    lote = EscolaParaFiltrosLoteReadOnlySerializer()


class EscolaEolSimplesSerializer(serializers.ModelSerializer):
    codigo_eol_escola = serializers.SerializerMethodField()
    tipo_gestao = serializers.SerializerMethodField()

    def get_codigo_eol_escola(self, obj):
        return f"{obj.codigo_eol} - {obj.nome}" if obj.codigo_eol else None

    def get_tipo_gestao(self, obj):
        return obj.tipo_gestao.nome if obj.tipo_gestao else None

    class Meta:
        model = Escola
        fields = ("codigo_eol", "codigo_eol_escola", "tipo_gestao", "uuid")


class DiretoriaRegionalSimplesSerializer(serializers.ModelSerializer):
    escolas = EscolaSimplissimaSerializer(many=True)
    quantidade_alunos = serializers.IntegerField()

    class Meta:
        model = DiretoriaRegional
        exclude = ("id",)


class EscolaSimplesSerializer(
    EscolaNomeHistoricoSerializerMixin, serializers.ModelSerializer
):
    tipo_unidade = TipoUnidadeEscolarSerializer()
    lote = LoteNomeSerializer()
    tipo_gestao = TipoGestaoSerializer()
    diretoria_regional = DiretoriaRegionalSimplissimaSerializer()
    periodos_escolares = serializers.SerializerMethodField()
    nome = serializers.SerializerMethodField()

    def get_periodos_escolares(self, obj):
        ano_hoje = datetime.datetime.now().year
        request = self.context.get("request")
        ano = request.query_params.get("ano", ano_hoje) if request else ano_hoje
        return PeriodoEscolarSerializer(obj.periodos_escolares(ano), many=True).data

    class Meta:
        model = Escola
        fields = (
            "uuid",
            "nome",
            "codigo_eol",
            "tipo_unidade",
            "quantidade_alunos",
            "quantidade_alunos_cei_da_cemei",
            "quantidade_alunos_emei_da_cemei",
            "periodos_escolares",
            "lote",
            "tipo_gestao",
            "diretoria_regional",
        )


class EscolaListagemSimplesSelializer(
    EscolaNomeHistoricoSerializerMixin, serializers.ModelSerializer
):
    nome = serializers.SerializerMethodField()

    class Meta:
        model = Escola
        fields = ("uuid", "nome", "codigo_eol", "quantidade_alunos")


class EscolaListagemSimplissimaComDRESelializer(
    EscolaNomeHistoricoSerializerMixin, serializers.ModelSerializer
):
    nome = serializers.SerializerMethodField()
    diretoria_regional = DiretoriaRegionalSimplissimaSerializer()
    lote = serializers.CharField(source="lote.uuid", required=False)
    lote_obj = LoteComContratosSerializer(source="lote", required=False)
    tipo_unidade = serializers.CharField(source="tipo_unidade.uuid", required=False)
    terceirizada = serializers.CharField(
        source="lote.terceirizada.nome_fantasia", required=False
    )
    quantidade_alunos = serializers.SerializerMethodField()

    def get_quantidade_alunos(self, obj):
        if hasattr(obj, "quantidade_alunos_regular"):
            return obj.quantidade_alunos_regular or 0
        return obj.quantidade_alunos

    class Meta:
        model = Escola
        fields = (
            "uuid",
            "nome",
            "diretoria_regional",
            "codigo_eol",
            "quantidade_alunos",
            "lote",
            "lote_obj",
            "tipo_unidade",
            "terceirizada",
        )


class EscolaCompletaSerializer(
    EscolaNomeHistoricoSerializerMixin, serializers.ModelSerializer
):
    nome = serializers.SerializerMethodField()
    diretoria_regional = DiretoriaRegionalSimplesSerializer()
    tipo_unidade = TipoUnidadeEscolarSerializer()
    tipo_gestao = TipoGestaoSerializer()
    periodos_escolares = PeriodoEscolarSerializer(many=True)
    lote = LoteSimplesSerializer()

    class Meta:
        model = Escola
        exclude = ("id",)


class DiretoriaRegionalCompletaSerializer(serializers.ModelSerializer):
    lotes = LoteSimplesSerializer(many=True)
    escolas = EscolaSimplesSerializer(many=True)

    class Meta:
        model = DiretoriaRegional
        exclude = ("id",)


class EscolaPeriodoEscolarSerializer(serializers.ModelSerializer):
    quantidade_alunos = serializers.IntegerField()
    escola = EscolaSimplissimaSerializer()
    periodo_escolar = PeriodoEscolarSimplesSerializer()

    class Meta:
        model = EscolaPeriodoEscolar
        fields = ("uuid", "quantidade_alunos", "escola", "periodo_escolar")


class AlunosMatriculadosPeriodoEscolaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlunosMatriculadosPeriodoEscola
        fields = ("periodo_escolar",)


class TipoUnidadeParaFiltroSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoUnidadeEscolar
        fields = ("uuid", "iniciais")


class EscolaParaFiltroSerializer(serializers.ModelSerializer):
    diretoria_regional = DiretoriaRegionalParaFiltroSerializer()
    tipo_unidade = TipoUnidadeParaFiltroSerializer()
    lote = LoteSerializer()

    class Meta:
        model = Escola
        fields = ("uuid", "nome", "diretoria_regional", "tipo_unidade", "lote")


class EscolaAlunoPeriodoSerializer(
    EscolaNomeHistoricoSerializerMixin, serializers.ModelSerializer
):
    nome = serializers.SerializerMethodField()
    diretoria_regional = DiretoriaRegionalParaFiltroSerializer()
    tipo_unidade = TipoUnidadeParaFiltroSerializer()
    lote = LoteSerializer()
    quantidade_alunos = serializers.SerializerMethodField()
    exibir_faixas = serializers.SerializerMethodField()

    def get_periodos_escolares(self, obj):
        return PeriodoEscolarSimplesSerializer(
            obj.periodos_escolares(), many=True, context={"escola": obj}
        ).data

    def get_quantidade_alunos(self, obj):
        return obj.quantidade_alunos

    def get_exibir_faixas(self, obj):
        return obj.eh_cei or obj.eh_cemei

    class Meta:
        model = Escola
        fields = (
            "uuid",
            "nome",
            "diretoria_regional",
            "tipo_unidade",
            "quantidade_alunos",
            "lote",
            "exibir_faixas",
            "eh_cei",
            "eh_cemei",
        )


class AlunosMatriculadosPeriodoEscolaCompletoSerializer(serializers.ModelSerializer):
    escola = EscolaAlunoPeriodoSerializer()
    periodo_escolar = PeriodoEscolarSimplesSerializer()
    alunos_por_faixa_etaria = serializers.SerializerMethodField()

    def get_alunos_por_faixa_etaria(self, obj):
        try:
            periodos_faixas = obj.escola.matriculados_por_periodo_e_faixa_etaria()
            return periodos_faixas[obj.periodo_escolar.nome]
        except Exception:
            return None

    class Meta:
        model = AlunosMatriculadosPeriodoEscola
        fields = (
            "periodo_escolar",
            "escola",
            "alunos_por_faixa_etaria",
            "quantidade_alunos",
            "tipo_turma",
        )


class TipoUnidadeEscolarSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoUnidadeEscolar
        fields = ("uuid", "iniciais")


class DiaSuspensaoAtividadesSerializer(serializers.ModelSerializer):
    tipo_unidade = TipoUnidadeEscolarSimplesSerializer()
    criado_por = serializers.SerializerMethodField()
    edital = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Edital.objects.all()
    )
    edital_numero = serializers.CharField(read_only=True)

    def get_criado_por(self, obj):
        return {"nome": obj.criado_por.nome}

    class Meta:
        model = DiaSuspensaoAtividades
        exclude = ("id",)


class GrupoUnidadeEscolarSerializer(serializers.ModelSerializer):
    tipos_unidades = TipoUnidadeEscolarSimplesSerializer(many=True)

    class Meta:
        model = GrupoUnidadeEscolar
        exclude = ("id",)


class EscolaFormIMRSelializer(serializers.ModelSerializer):
    lote = serializers.CharField(source="lote.nome", required=False)
    terceirizada = serializers.CharField(
        source="lote.terceirizada.nome_fantasia", required=False
    )
    edital = serializers.SerializerMethodField()

    def get_edital(self, obj):
        return obj.editais[-1] if obj.lote else None

    class Meta:
        model = Escola
        fields = ("uuid", "nome", "codigo_eol", "lote", "terceirizada", "edital")


class HistoricoEscolaSerializer(serializers.Serializer):
    nome = serializers.CharField()
    tipo_unidade = TipoUnidadeEscolarSimplesSerializer()
