from rest_framework import serializers

from ....cardapio.base.api.serializers import TipoAlimentacaoSimplesSerializer
from ....dados_comuns.api.serializers import LogSolicitacoesUsuarioSerializer
from ....escola.api.serializers import (
    EscolaSimplesSerializer,
    EscolaSimplissimaSerializer,
    FaixaEtariaSerializer,
    PeriodoEscolarSerializer,
    PeriodoEscolarSimplesSerializer,
)
from ....escola.models import FaixaEtaria
from ....inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
    InclusaoAlimentacaoDaCEI,
    InclusaoAlimentacaoNormal,
    MotivoInclusaoContinua,
    MotivoInclusaoNormal,
    QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEI,
    QuantidadePorPeriodo,
)
from ....terceirizada.api.serializers.serializers import TerceirizadaSimplesSerializer
from ...models import (
    DiasMotivosInclusaoDeAlimentacaoCEI,
    DiasMotivosInclusaoDeAlimentacaoCEMEI,
    InclusaoDeAlimentacaoCEMEI,
    QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI,
    QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEI,
)


class MotivoInclusaoContinuaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotivoInclusaoContinua
        exclude = ("id",)


class MotivoInclusaoNormalSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotivoInclusaoNormal
        exclude = ("id",)


class QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEISerializer(
    serializers.ModelSerializer
):
    faixa_etaria = FaixaEtariaSerializer()
    periodo = PeriodoEscolarSimplesSerializer()
    periodo_externo = PeriodoEscolarSimplesSerializer()

    class Meta:
        model = QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEI
        exclude = ("id", "inclusao_alimentacao_da_cei")


class DiasMotivosInclusaoDeAlimentacaoCEISerializer(serializers.ModelSerializer):
    motivo = MotivoInclusaoNormalSerializer()

    class Meta:
        model = DiasMotivosInclusaoDeAlimentacaoCEI
        exclude = ("id",)


class InclusaoAlimentacaoDaCEIBaseSerializer(serializers.ModelSerializer):
    escola = EscolaSimplesSerializer()
    prioridade = serializers.CharField()
    periodo_escolar = PeriodoEscolarSimplesSerializer()
    tipos_alimentacao = TipoAlimentacaoSimplesSerializer(many=True, read_only=True)
    quantidade_alunos_por_faixas_etarias = (
        QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEISerializer(
            many=True, read_only=True
        )
    )
    dias_motivos_da_inclusao_cei = DiasMotivosInclusaoDeAlimentacaoCEISerializer(
        many=True
    )
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    id_externo = serializers.CharField()
    datas = serializers.CharField()

    def to_representation(self, instance):
        retorno = super().to_representation(instance)

        # Inclui o total de alunos nas faixas etárias num período
        faixas_etarias_da_solicitacao = FaixaEtaria.objects.filter(
            uuid__in=[
                f["faixa_etaria__uuid"]
                for f in instance.quantidade_alunos_por_faixas_etarias.values(
                    "faixa_etaria__uuid"
                )
            ]
        )

        qtde_alunos = instance.escola.alunos_por_periodo_e_faixa_etaria(
            instance.data, faixas_etarias_da_solicitacao
        )

        nome_periodo = "INTEGRAL"
        for faixa_etaria in retorno["quantidade_alunos_por_faixas_etarias"]:
            try:
                uuid_faixa_etaria = faixa_etaria["faixa_etaria"]["uuid"]
                faixa_etaria["total_alunos_no_periodo"] = qtde_alunos[nome_periodo][
                    uuid_faixa_etaria
                ]
            except KeyError:
                continue

        return retorno

    class Meta:
        model = InclusaoAlimentacaoDaCEI
        exclude = ("id",)


class InclusaoAlimentacaoDaCEISerializer(InclusaoAlimentacaoDaCEIBaseSerializer):
    solicitacoes_similares = InclusaoAlimentacaoDaCEIBaseSerializer(many=True)


class QuantidadePorPeriodoSerializer(serializers.ModelSerializer):
    periodo_escolar = PeriodoEscolarSerializer()
    tipos_alimentacao = TipoAlimentacaoSimplesSerializer(many=True, read_only=True)

    class Meta:
        model = QuantidadePorPeriodo
        exclude = ("id",)


class InclusaoAlimentacaoNormalSerializer(serializers.ModelSerializer):
    motivo = MotivoInclusaoNormalSerializer()

    class Meta:
        model = InclusaoAlimentacaoNormal
        exclude = ("id",)


class InclusaoAlimentacaoContinuaSerializer(serializers.ModelSerializer):
    prioridade = serializers.CharField()
    motivo = MotivoInclusaoContinuaSerializer()
    quantidades_periodo = QuantidadePorPeriodoSerializer(many=True)
    escola = EscolaSimplesSerializer()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    dias_semana_explicacao = serializers.CharField(
        source="dias_semana_display", required=False, read_only=True
    )
    id_externo = serializers.CharField()
    rastro_terceirizada = TerceirizadaSimplesSerializer()
    solicitacoes_similares = serializers.ListField(default=[])

    class Meta:
        model = InclusaoAlimentacaoContinua
        exclude = ("id",)


class InclusaoAlimentacaoContinuaSimplesSerializer(serializers.ModelSerializer):
    motivo = MotivoInclusaoContinuaSerializer()
    dias_semana_explicacao = serializers.CharField(
        source="dias_semana_display", required=False, read_only=True
    )
    prioridade = serializers.CharField()

    class Meta:
        model = InclusaoAlimentacaoContinua
        exclude = ("id", "escola", "criado_por")


class InclusaoAlimentacaoNormalSimplesSerializer(serializers.ModelSerializer):
    prioridade = serializers.CharField()

    class Meta:
        model = InclusaoAlimentacaoNormal
        exclude = ("id", "data")


class GrupoInclusaoAlimentacaoNormalBaseSerializer(serializers.ModelSerializer):
    prioridade = serializers.CharField()
    inclusoes = InclusaoAlimentacaoNormalSerializer(many=True)
    escola = EscolaSimplesSerializer()
    rastro_terceirizada = TerceirizadaSimplesSerializer()
    quantidades_periodo = QuantidadePorPeriodoSerializer(many=True)
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    id_externo = serializers.CharField()
    datas = serializers.CharField()

    class Meta:
        model = GrupoInclusaoAlimentacaoNormal
        exclude = ("id",)


class GrupoInclusaoAlimentacaoNormalSerializer(
    GrupoInclusaoAlimentacaoNormalBaseSerializer
):
    solicitacoes_similares = GrupoInclusaoAlimentacaoNormalBaseSerializer(many=True)


class GrupoInclusaoAlimentacaoNormalSimplesSerializer(serializers.ModelSerializer):
    prioridade = serializers.CharField()

    class Meta:
        model = GrupoInclusaoAlimentacaoNormal
        exclude = ("id", "criado_por", "escola")


class DiasMotivosInclusaoDeAlimentacaoCEMEISerializer(serializers.ModelSerializer):
    motivo = MotivoInclusaoNormalSerializer()

    class Meta:
        model = DiasMotivosInclusaoDeAlimentacaoCEMEI
        exclude = ("id",)


class QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEISerializer(
    serializers.ModelSerializer
):
    periodo_escolar = PeriodoEscolarSimplesSerializer()
    tipos_alimentacao = TipoAlimentacaoSimplesSerializer(many=True, read_only=True)

    class Meta:
        model = QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI
        exclude = ("id",)


class QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEISerializer(
    serializers.ModelSerializer
):
    periodo_escolar = PeriodoEscolarSimplesSerializer()
    faixa_etaria = FaixaEtariaSerializer()

    class Meta:
        model = QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEI
        exclude = ("id",)


class InclusaoDeAlimentacaoCEMEIBaseSerializer(serializers.ModelSerializer):
    escola = EscolaSimplissimaSerializer()
    dias_motivos_da_inclusao_cemei = DiasMotivosInclusaoDeAlimentacaoCEMEISerializer(
        many=True
    )
    quantidade_alunos_cei_da_inclusao_cemei = (
        QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEISerializer(
            many=True
        )
    )
    quantidade_alunos_emei_da_inclusao_cemei = (
        QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEISerializer(many=True)
    )
    id_externo = serializers.CharField()
    prioridade = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    datas = serializers.CharField()

    class Meta:
        model = InclusaoDeAlimentacaoCEMEI
        exclude = ("id",)


class InclusaoDeAlimentacaoCEMEISerializer(InclusaoDeAlimentacaoCEMEIBaseSerializer):
    solicitacoes_similares = InclusaoDeAlimentacaoCEMEIBaseSerializer(many=True)


class InclusaoDeAlimentacaoCEMEIRetrieveSerializer(serializers.ModelSerializer):
    escola = EscolaSimplesSerializer()
    dias_motivos_da_inclusao_cemei = DiasMotivosInclusaoDeAlimentacaoCEMEISerializer(
        many=True
    )
    quantidade_alunos_cei_da_inclusao_cemei = (
        QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEISerializer(
            many=True
        )
    )
    quantidade_alunos_emei_da_inclusao_cemei = (
        QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEISerializer(many=True)
    )
    id_externo = serializers.CharField()
    rastro_terceirizada = TerceirizadaSimplesSerializer()
    prioridade = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    solicitacoes_similares = InclusaoDeAlimentacaoCEMEIBaseSerializer(many=True)

    class Meta:
        model = InclusaoDeAlimentacaoCEMEI
        exclude = ("id",)
