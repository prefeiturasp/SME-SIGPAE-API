from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from ...cardapio.base.models import TipoAlimentacao
from ...dados_comuns.api.serializers import ContatoSerializer, EnderecoSerializer
from ...dados_comuns.constants import FORMATO_DATA_BRASILEIRO
from ...perfil.api.serializers import PerfilSimplesSerializer
from ...perfil.models import Usuario, Vinculo
from ...terceirizada.api.serializers.serializers import ContratoSimplesSerializer
from ...terceirizada.models import Terceirizada
from ..aluno.api.serializers import (
    AlunoNaoMatriculadoSerializer,
    AlunoNomeUuidCodigoEolSerializer,
    AlunoPeriodoParcialSimplesSerializer,
    AlunoSerializer,
    AlunoSimplesSerializer,
    FaixaEtariaSerializer,
    ReponsavelSerializer,
)
from ..api.serializers_base import TipoGestaoSerializer
from ..codae.api.serializers import CODAESerializer
from ..diretoria_regional.api.serializers import (
    DiretoriaRegionalLookUpSerializer,
    DiretoriaRegionalParaFiltroSerializer,
    DiretoriaRegionalSimplissimaSerializer,
)
from ..escola.api.serializers import (
    AlunosMatriculadosPeriodoEscolaCompletoSerializer,
    AlunosMatriculadosPeriodoEscolaSerializer,
    DiaCalendarioSerializer,
    DiaSuspensaoAtividadesSerializer,
    DiretoriaRegionalCompletaSerializer,
    DiretoriaRegionalSimplesSerializer,
    EscolaAlunoPeriodoSerializer,
    EscolaCompletaSerializer,
    EscolaEolSimplesSerializer,
    EscolaFormIMRSelializer,
    EscolaListagemSimplesSelializer,
    EscolaListagemSimplissimaComDRESelializer,
    EscolaParaFiltrosDiretoriaRegionalReadOnlySerializer,
    EscolaParaFiltroSerializer,
    EscolaParaFiltrosLoteReadOnlySerializer,
    EscolaParaFiltrosPeriodoEscolarReadOnlySerializer,
    EscolaParaFiltrosReadOnlySerializer,
    EscolaParaFiltrosTipoUnidadeReadOnlySerializer,
    EscolaPeriodoEscolarSerializer,
    EscolaSimplesSerializer,
    EscolaSimplissimaSerializer,
    GrupoUnidadeEscolarSerializer,
    HistoricoEscolaSerializer,
    PeriodoEscolarParaFiltroSerializer,
    PeriodoEscolarSerializer,
    PeriodoEscolarSimplesSerializer,
    TipoAlimentacaoSerializer,
    TipoUnidadeEscolarPeriodoEscolarSerializer,
    TipoUnidadeEscolarPeriodoEscolarTipoAlimentacaoSerializer,
    TipoUnidadeEscolarSerializer,
    TipoUnidadeEscolarSerializerSimples,
    TipoUnidadeEscolarSimplesSerializer,
    TipoUnidadeParaFiltroSerializer,
)
from ..logs.api.serializers import (
    LogAlunosMatriculadosFaixaEtariaDiaSerializer,
    LogAlunosMatriculadosPeriodoEscolaSerializer,
)
from ..lote.api.serializers import (
    EscolaNomeCodigoEOLSerializer,
    LoteComContratosSerializer,
    LoteNomeSerializer,
    LoteParaFiltroSerializer,
    LoteReclamacaoSerializer,
    LoteSerializer,
    LoteSimplesSerializer,
)
from ..models import Codae, DiretoriaRegional, Escola
from ..subprefeitura.api.serializers import (
    SubprefeituraSerializer,
    SubprefeituraSerializerSimples,
)


class SubsticuicoesTipoAlimentacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAlimentacao
        exclude = (
            "id",
            "substituicoes",
        )


class TerceirizadaSerializer(serializers.ModelSerializer):
    tipo_alimento_display = serializers.CharField(source="get_tipo_alimento_display")
    tipo_empresa_display = serializers.CharField(source="get_tipo_empresa_display")
    tipo_servico_display = serializers.CharField(source="get_tipo_servico_display")
    nutricionistas = serializers.SerializerMethodField()
    contatos = ContatoSerializer(many=True)
    contratos = ContratoSimplesSerializer(many=True)
    lotes = LoteNomeSerializer(many=True)
    quantidade_alunos = serializers.IntegerField()
    id_externo = serializers.CharField()

    def get_nutricionistas(self, obj):
        if any(contato.eh_nutricionista for contato in obj.contatos.all()):
            return []
        else:
            content_type = ContentType.objects.get_for_model(Terceirizada)
            return UsuarioNutricionistaSerializer(
                Usuario.objects.filter(
                    vinculos__object_id=obj.id,
                    vinculos__content_type=content_type,
                    crn_numero__isnull=False,
                    super_admin_terceirizadas=False,
                )
                .filter(
                    Q(
                        vinculos__data_inicial=None,
                        vinculos__data_final=None,
                        vinculos__ativo=False,
                    )
                    | Q(
                        vinculos__data_inicial__isnull=False,
                        vinculos__data_final=None,
                        vinculos__ativo=True,
                    )
                    # noqa W504 ativo
                )
                .distinct(),
                many=True,
            ).data

    class Meta:
        model = Terceirizada
        exclude = ("id",)


class VinculoInstituicaoSerializer(serializers.ModelSerializer):
    instituicao = serializers.SerializerMethodField()
    perfil = PerfilSimplesSerializer()

    def get_periodos_escolares(self, obj):
        if isinstance(obj.instituicao, Escola):
            request = self.context.get("request")
            pega_atualmente = False
            if request is not None:
                pega_atualmente = (
                    request.query_params.get("pega_atualmente", "false").lower()
                    == "true"
                )
            return PeriodoEscolarSerializer(
                obj.instituicao.periodos_escolares(
                    pega_atualmente=pega_atualmente
                ).all(),
                many=True,
                context={"escola": obj.instituicao},
            ).data

    def get_lotes(self, obj):
        if isinstance(obj.instituicao, (Terceirizada, DiretoriaRegional)):
            return LoteNomeSerializer(obj.instituicao.lotes.all(), many=True).data
        elif isinstance(obj.instituicao, Escola) and obj.instituicao.lote:
            return LoteSerializer([obj.instituicao.lote], many=True).data
        else:
            return []

    def get_diretoria_regional(self, obj):
        if not isinstance(obj.instituicao, Escola):
            return None
        return DiretoriaRegionalSimplissimaSerializer(
            obj.instituicao.diretoria_regional
        ).data

    def get_codigo_eol(self, obj):
        if isinstance(obj.instituicao, Escola):
            return obj.instituicao.codigo_eol
        elif isinstance(obj.instituicao, DiretoriaRegional):
            return obj.instituicao.codigo_eol
        return None

    def get_tipo_unidade_escolar(self, obj):
        if not isinstance(obj.instituicao, Escola):
            return None
        return obj.instituicao.tipo_unidade.uuid

    def get_tipo_unidade_escolar_iniciais(self, obj):
        if not isinstance(obj.instituicao, Escola):
            return None
        return obj.instituicao.tipo_unidade.iniciais

    def get_tipo_gestao(self, obj):
        if not isinstance(obj.instituicao, Escola):
            return None
        if not obj.instituicao.tipo_gestao:
            raise ValidationError(
                "Escola não possui tipo de gestão. Favor contatar a CODAE."
            )
        return obj.instituicao.tipo_gestao.nome

    def get_tipo_gestao_uuid(self, obj):
        if not isinstance(obj.instituicao, Escola):
            return None
        if not obj.instituicao.tipo_gestao:
            raise ValidationError(
                "Escola não possui tipo de gestão. Favor contatar a CODAE."
            )
        return obj.instituicao.tipo_gestao.uuid

    def get_endereco(self, obj):
        if not isinstance(obj.instituicao, Escola):
            return None
        return EnderecoSerializer(obj.instituicao.endereco).data

    def get_contato(self, obj):
        if not isinstance(obj.instituicao, Escola):
            return None
        return ContatoSerializer(obj.instituicao.contato).data

    def get_modulo_gestao(self, obj):
        if not isinstance(obj.instituicao, Escola):
            return None
        return obj.instituicao.modulo_gestao

    def get_eh_cei(self, obj):
        if not isinstance(obj.instituicao, Escola):
            return None
        return obj.instituicao.eh_cei

    def get_eh_cemei(self, obj):
        if not isinstance(obj.instituicao, Escola):
            return None
        return obj.instituicao.eh_cemei

    def get_eh_emebs(self, obj):
        if not isinstance(obj.instituicao, Escola):
            return None
        return obj.instituicao.eh_emebs

    def get_tipo_servico(self, obj):
        if not isinstance(obj.instituicao, Terceirizada):
            return None
        return obj.instituicao.tipo_servico

    def _add_diretoria_regional_data(self, instituicao_dict, obj):
        instituicao_dict["possui_escolas_com_acesso_ao_medicao_inicial"] = (
            obj.instituicao.possui_escolas_com_acesso_ao_medicao_inicial
        )
        instituicao_dict["quantidade_alunos_terceirizada"] = (
            obj.instituicao.quantidade_alunos_terceirizada
        )
        instituicao_dict["quantidade_alunos_parceira"] = (
            obj.instituicao.quantidade_alunos_parceira
        )

    def _add_codae_data(self, instituicao_dict, obj):
        instituicao_dict["quantidade_alunos_terceirizada"] = (
            obj.instituicao.quantidade_alunos_terceirizada
        )
        instituicao_dict["quantidade_alunos_parceira"] = (
            obj.instituicao.quantidade_alunos_parceira
        )

    def _add_escola_data(self, instituicao_dict, obj):
        instituicao_dict["possui_alunos_regulares"] = (
            obj.instituicao.possui_alunos_regulares
        )
        instituicao_dict["eh_cei"] = self.get_eh_cei(obj)
        instituicao_dict["eh_cemei"] = self.get_eh_cemei(obj)
        instituicao_dict["eh_emebs"] = self.get_eh_emebs(obj)
        instituicao_dict["modulo_gestao"] = self.get_modulo_gestao(obj)
        instituicao_dict["acesso_desde"] = (
            obj.instituicao.acesso_desde.strftime(FORMATO_DATA_BRASILEIRO)
            if obj.instituicao.acesso_desde
            else None
        )
        if obj.instituicao.eh_cemei:
            instituicao_dict["quantidade_alunos_cei_da_cemei"] = (
                obj.instituicao.quantidade_alunos_cei_da_cemei
            )
            instituicao_dict["quantidade_alunos_emei_da_cemei"] = (
                obj.instituicao.quantidade_alunos_emei_da_cemei
            )

    def _add_terceirizada_data(self, instituicao_dict, obj):
        instituicao_dict["tipo_servico"] = self.get_tipo_servico(obj)
        instituicao_dict["possui_escolas_com_acesso_ao_medicao_inicial"] = (
            obj.instituicao.possui_escolas_com_acesso_ao_medicao_inicial
        )
        instituicao_dict["quantidade_alunos_terceirizada"] = (
            obj.instituicao.quantidade_alunos_terceirizada
        )

    def get_instituicao(self, obj):
        instituicao_dict = {
            "nome": obj.instituicao.nome,
            "uuid": obj.instituicao.uuid,
            "codigo_eol": self.get_codigo_eol(obj),
            "quantidade_alunos": obj.instituicao.quantidade_alunos,
            "lotes": self.get_lotes(obj),
            "periodos_escolares": self.get_periodos_escolares(obj),
            "diretoria_regional": self.get_diretoria_regional(obj),
            "tipo_unidade_escolar": self.get_tipo_unidade_escolar(obj),
            "tipo_unidade_escolar_iniciais": self.get_tipo_unidade_escolar_iniciais(
                obj
            ),
            "tipo_gestao": self.get_tipo_gestao(obj),
            "tipo_gestao_uuid": self.get_tipo_gestao_uuid(obj),
            "endereco": self.get_endereco(obj),
            "contato": self.get_contato(obj),
        }
        if hasattr(obj.instituicao, "acesso_modulo_medicao_inicial"):
            instituicao_dict["acesso_modulo_medicao_inicial"] = (
                obj.instituicao.acesso_modulo_medicao_inicial
            )
        if isinstance(obj.instituicao, DiretoriaRegional):
            self._add_diretoria_regional_data(instituicao_dict, obj)
        if isinstance(obj.instituicao, Codae):
            self._add_codae_data(instituicao_dict, obj)
        if isinstance(obj.instituicao, Escola):
            self._add_escola_data(instituicao_dict, obj)
        if isinstance(obj.instituicao, Terceirizada):
            self._add_terceirizada_data(instituicao_dict, obj)
        return instituicao_dict

    class Meta:
        model = Vinculo
        fields = ("uuid", "instituicao", "perfil", "ativo")


class UsuarioNutricionistaSerializer(serializers.ModelSerializer):
    vinculo_atual = VinculoInstituicaoSerializer(required=False)
    contatos = ContatoSerializer(many=True)

    class Meta:
        model = Usuario
        fields = (
            "nome",
            "contatos",
            "crn_numero",
            "super_admin_terceirizadas",
            "vinculo_atual",
        )


class UsuarioDetalheSerializer(serializers.ModelSerializer):
    tipo_usuario = serializers.CharField()
    vinculo_atual = VinculoInstituicaoSerializer()

    class Meta:
        model = Usuario
        fields = (
            "uuid",
            "cpf",
            "nome",
            "email",
            "tipo_email",
            "registro_funcional",
            "tipo_usuario",
            "date_joined",
            "vinculo_atual",
            "crn_numero",
            "cargo",
            "aceitou_termos",
        )


__all__ = [
    "AlunoNaoMatriculadoSerializer",
    "AlunoNomeUuidCodigoEolSerializer",
    "AlunoPeriodoParcialSimplesSerializer",
    "AlunoSerializer",
    "AlunoSimplesSerializer",
    "AlunosMatriculadosPeriodoEscolaCompletoSerializer",
    "AlunosMatriculadosPeriodoEscolaSerializer",
    "CODAESerializer",
    "DiaCalendarioSerializer",
    "DiaSuspensaoAtividadesSerializer",
    "DiretoriaRegionalCompletaSerializer",
    "DiretoriaRegionalLookUpSerializer",
    "DiretoriaRegionalParaFiltroSerializer",
    "DiretoriaRegionalSimplesSerializer",
    "EscolaAlunoPeriodoSerializer",
    "EscolaCompletaSerializer",
    "EscolaEolSimplesSerializer",
    "EscolaFormIMRSelializer",
    "EscolaListagemSimplesSelializer",
    "EscolaListagemSimplissimaComDRESelializer",
    "EscolaNomeCodigoEOLSerializer",
    "EscolaParaFiltroSerializer",
    "EscolaParaFiltrosDiretoriaRegionalReadOnlySerializer",
    "EscolaParaFiltrosLoteReadOnlySerializer",
    "EscolaParaFiltrosPeriodoEscolarReadOnlySerializer",
    "EscolaParaFiltrosReadOnlySerializer",
    "EscolaParaFiltrosTipoUnidadeReadOnlySerializer",
    "EscolaPeriodoEscolarSerializer",
    "EscolaSimplesSerializer",
    "EscolaSimplissimaSerializer",
    "FaixaEtariaSerializer",
    "GrupoUnidadeEscolarSerializer",
    "HistoricoEscolaSerializer",
    "LogAlunosMatriculadosFaixaEtariaDiaSerializer",
    "LogAlunosMatriculadosPeriodoEscolaSerializer",
    "LoteComContratosSerializer",
    "LoteParaFiltroSerializer",
    "LoteReclamacaoSerializer",
    "LoteSimplesSerializer",
    "PeriodoEscolarParaFiltroSerializer",
    "PeriodoEscolarSimplesSerializer",
    "ReponsavelSerializer",
    "SubprefeituraSerializer",
    "SubprefeituraSerializerSimples",
    "TipoAlimentacaoSerializer",
    "TipoGestaoSerializer",
    "TipoUnidadeEscolarPeriodoEscolarSerializer",
    "TipoUnidadeEscolarPeriodoEscolarTipoAlimentacaoSerializer",
    "TipoUnidadeEscolarSerializer",
    "TipoUnidadeEscolarSerializerSimples",
    "TipoUnidadeEscolarSimplesSerializer",
    "TipoUnidadeParaFiltroSerializer",
]
