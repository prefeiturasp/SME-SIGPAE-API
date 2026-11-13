from __future__ import annotations

from rest_framework import serializers

from ....dados_comuns.constants import StringsSourceSerializers
from ....paineis_consolidados import models
from ...escola.api.serializers import EscolaSimplesSerializer
from ...models import Aluno, AlunoPeriodoParcial, Escola, FaixaEtaria


class FaixaEtariaSerializer(serializers.ModelSerializer):
    __str__ = serializers.CharField(required=False)

    class Meta:
        model = FaixaEtaria
        exclude = ("id", "ativo")


class AlunoPeriodoParcialSimplesSerializer(serializers.ModelSerializer):
    codigo_eol = serializers.CharField(source="aluno.codigo_eol")
    nome = serializers.CharField(source="aluno.nome")
    uuid = serializers.UUIDField(source="aluno.uuid")
    escola = serializers.UUIDField(source=StringsSourceSerializers.ESCOLA_UUID.value)

    class Meta:
        model = AlunoPeriodoParcial
        fields = ("uuid", "nome", "codigo_eol", "escola", "data", "data_removido")


class ReponsavelSerializer(serializers.Serializer):
    cpf = serializers.CharField()
    nome = serializers.CharField()


class AlunoSerializer(serializers.ModelSerializer):
    escola = EscolaSimplesSerializer(required=False)
    nome_escola = serializers.SerializerMethodField()
    nome_dre = serializers.SerializerMethodField()
    responsaveis = ReponsavelSerializer(many=True)
    possui_dieta_especial = serializers.SerializerMethodField()
    periodo = serializers.CharField(read_only=True)

    def get_nome_escola(self, obj):
        return f"{obj.escola.nome}" if obj.escola else None

    def get_nome_dre(self, obj):
        return f"{obj.escola.diretoria_regional.nome}" if obj.escola else None

    def get_possui_dieta_especial(self, obj):
        user = self.context["request"].user
        instituicao = user.vinculo_atual.instituicao
        if user.tipo_usuario == "escola":
            dietas_autorizadas = (
                models.SolicitacoesEscola.get_autorizados_dieta_especial(
                    escola_uuid=instituicao.uuid
                )
            )
            dietas_inativas = models.SolicitacoesEscola.get_inativas_dieta_especial(
                escola_uuid=instituicao.uuid
            )
            dietas_canceladas = models.SolicitacoesEscola.get_cancelados_dieta_especial(
                escola_uuid=instituicao.uuid
            )
        elif user.tipo_usuario == "diretoriaregional":
            dietas_autorizadas = models.SolicitacoesDRE.get_autorizados_dieta_especial(
                dre_uuid=instituicao.uuid
            )
            dietas_inativas = models.SolicitacoesDRE.get_inativas_dieta_especial(
                dre_uuid=instituicao.uuid
            )
            dietas_canceladas = models.SolicitacoesDRE.get_cancelados_dieta_especial(
                dre_uuid=instituicao.uuid
            )
        else:
            dietas_autorizadas = (
                models.SolicitacoesCODAE.get_autorizados_dieta_especial()
            )
            dietas_inativas = models.SolicitacoesCODAE.get_inativas_dieta_especial()
            dietas_canceladas = models.SolicitacoesCODAE.get_cancelados_dieta_especial()

        ids_dietas_autorizadas = dietas_autorizadas.values_list("id", flat=True)
        ids_dietas_inativas = dietas_inativas.values_list("id", flat=True)
        ids_dietas_canceladas = dietas_canceladas.values_list("id", flat=True)
        # Juntas as duas querysets.
        dietas_especiais = (
            ids_dietas_autorizadas | ids_dietas_inativas | ids_dietas_canceladas
        )

        return obj.dietas_especiais.filter(id__in=dietas_especiais).exists()

    class Meta:
        model = Aluno
        fields = (
            "uuid",
            "nome",
            "data_nascimento",
            "codigo_eol",
            "escola",
            "nome_escola",
            "nome_dre",
            "responsaveis",
            "cpf",
            "possui_dieta_especial",
            "serie",
            "periodo",
        )


class AlunoSimplesSerializer(serializers.ModelSerializer):
    escola = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Escola.objects.all()
    )

    class Meta:
        model = Aluno
        fields = ("uuid", "nome", "data_nascimento", "codigo_eol", "escola")


class AlunoNomeUuidCodigoEolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno
        fields = ("uuid", "nome", "codigo_eol")


class AlunoNaoMatriculadoSerializer(serializers.ModelSerializer):
    responsavel = ReponsavelSerializer()
    codigo_eol_escola = serializers.CharField()
    cpf = serializers.CharField(required=False)

    class Meta:
        model = Aluno
        fields = (
            "uuid",
            "responsavel",
            "codigo_eol_escola",
            "nome",
            "cpf",
            "data_nascimento",
        )
