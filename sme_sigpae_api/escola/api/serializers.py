import datetime

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from ...cardapio.base.models import TipoAlimentacao
from ...dados_comuns.api.serializers import ContatoSerializer, EnderecoSerializer
from ...paineis_consolidados import models
from ...perfil.api.serializers import PerfilSimplesSerializer, UsuarioSerializer
from ...perfil.models import Usuario, Vinculo
from ...terceirizada.api.serializers.serializers import (
    ContratoEditalSerializer,
    ContratoSimplesSerializer,
    TerceirizadaSimplesSerializer,
)
from ...terceirizada.models import Edital, Terceirizada
from ..models import (
    Aluno,
    AlunoPeriodoParcial,
    AlunosMatriculadosPeriodoEscola,
    Codae,
    DiaCalendario,
    DiaSuspensaoAtividades,
    DiretoriaRegional,
    Escola,
    EscolaPeriodoEscolar,
    FaixaEtaria,
    FaixaIdadeEscolar,
    GrupoUnidadeEscolar,
    LogAlunosMatriculadosFaixaEtariaDia,
    LogAlunosMatriculadosPeriodoEscola,
    Lote,
    PeriodoEscolar,
    Subprefeitura,
    TipoGestao,
    TipoUnidadeEscolar,
)


class FaixaEtariaSerializer(serializers.ModelSerializer):
    __str__ = serializers.CharField(required=False)

    class Meta:
        model = FaixaEtaria
        exclude = ("id", "ativo")


class SubsticuicoesTipoAlimentacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAlimentacao
        exclude = (
            "id",
            "substituicoes",
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


class AlunoPeriodoParcialSimplesSerializer(serializers.ModelSerializer):
    codigo_eol = serializers.CharField(source="aluno.codigo_eol")
    nome = serializers.CharField(source="aluno.nome")
    uuid = serializers.UUIDField(source="aluno.uuid")
    escola = serializers.UUIDField(source="escola.uuid")

    class Meta:
        model = AlunoPeriodoParcial
        fields = ("uuid", "nome", "codigo_eol", "escola", "data", "data_removido")


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


class TipoGestaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoGestao
        exclude = ("id",)


class SubprefeituraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subprefeitura
        exclude = ("id",)


class SubprefeituraSerializerSimples(serializers.ModelSerializer):
    class Meta:
        model = Subprefeitura
        fields = ("codigo_eol", "nome")


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
        exclude = ("id", "cardapios")


class LogAlunosMatriculadosPeriodoEscolaSerializer(serializers.ModelSerializer):
    dia = serializers.SerializerMethodField()
    periodo_escolar = PeriodoEscolarSimplesSerializer()

    def get_dia(self, obj):
        return obj.criado_em.strftime("%d")

    class Meta:
        model = LogAlunosMatriculadosPeriodoEscola
        exclude = ("id", "uuid", "observacao")


class DiaCalendarioSerializer(serializers.ModelSerializer):
    escola = serializers.CharField(source="escola.nome")
    dia = serializers.SerializerMethodField()

    def get_dia(self, obj):
        return obj.data.strftime("%d")

    class Meta:
        model = DiaCalendario
        exclude = ("id", "uuid")


class TipoUnidadeEscolarSerializerSimples(serializers.ModelSerializer):
    class Meta:
        model = TipoUnidadeEscolar
        exclude = ("id", "cardapios", "periodos_escolares")


class FaixaIdadeEscolarSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaixaIdadeEscolar
        exclude = ("id",)


class DiretoriaRegionalSimplissimaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiretoriaRegional
        fields = (
            "uuid",
            "nome",
            "codigo_eol",
            "iniciais",
            "acesso_modulo_medicao_inicial",
        )


class DiretoriaRegionalLookUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiretoriaRegional
        fields = ("uuid", "iniciais", "nome", "codigo_eol")


class LoteReclamacaoSerializer(serializers.ModelSerializer):
    terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = Lote
        fields = ("uuid", "nome", "terceirizada")


class EscolaSimplissimaSerializer(serializers.ModelSerializer):
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


class LoteNomeSerializer(serializers.ModelSerializer):
    contratos_do_lote = ContratoEditalSerializer(many=True)
    diretoria_regional = DiretoriaRegionalSimplissimaSerializer()
    tipo_gestao = serializers.CharField()
    terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = Lote
        fields = (
            "uuid",
            "nome",
            "tipo_gestao",
            "diretoria_regional",
            "terceirizada",
            "contratos_do_lote",
        )


class LoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lote
        fields = ("uuid", "nome")


class EscolaNomeCodigoEOLSerializer(serializers.ModelSerializer):
    lote = LoteSerializer()

    class Meta:
        model = Escola
        fields = ("uuid", "nome", "codigo_eol", "lote")


class LoteSimplesSerializer(serializers.ModelSerializer):
    diretoria_regional = DiretoriaRegionalSimplissimaSerializer()
    tipo_gestao = TipoGestaoSerializer()
    escolas = EscolaNomeCodigoEOLSerializer(many=True)
    terceirizada = TerceirizadaSimplesSerializer()
    subprefeituras = SubprefeituraSerializer(many=True)

    class Meta:
        model = Lote
        exclude = ("id",)


class EscolaSimplesSerializer(serializers.ModelSerializer):
    tipo_unidade = TipoUnidadeEscolarSerializer()
    lote = LoteNomeSerializer()
    tipo_gestao = TipoGestaoSerializer()
    diretoria_regional = DiretoriaRegionalSimplissimaSerializer()
    periodos_escolares = serializers.SerializerMethodField()

    def get_periodos_escolares(self, obj):
        ano_hoje = datetime.datetime.now().year
        ano = self.context.get("request").query_params.get("ano", ano_hoje)
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
            "tipos_contagem",
        )


class EscolaListagemSimplesSelializer(serializers.ModelSerializer):
    class Meta:
        model = Escola
        fields = ("uuid", "nome", "codigo_eol", "quantidade_alunos")


class LoteComContratosSerializer(serializers.ModelSerializer):
    contratos_do_lote = ContratoEditalSerializer(many=True)

    class Meta:
        model = Lote
        fields = ("uuid", "nome", "contratos_do_lote")


class EscolaListagemSimplissimaComDRESelializer(serializers.ModelSerializer):
    diretoria_regional = DiretoriaRegionalSimplissimaSerializer()
    lote = serializers.CharField(source="lote.uuid", required=False)
    lote_obj = LoteComContratosSerializer(source="lote", required=False)
    tipo_unidade = serializers.CharField(source="tipo_unidade.uuid", required=False)
    terceirizada = serializers.CharField(
        source="lote.terceirizada.nome_fantasia", required=False
    )

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


class EscolaCompletaSerializer(serializers.ModelSerializer):
    diretoria_regional = DiretoriaRegionalSimplesSerializer()
    idades = FaixaIdadeEscolarSerializer(many=True)
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


class TipoContagemSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    nome = serializers.CharField()


class VinculoInstituicaoSerializer(serializers.ModelSerializer):
    instituicao = serializers.SerializerMethodField()
    perfil = PerfilSimplesSerializer()

    def get_periodos_escolares(self, obj):
        if isinstance(obj.instituicao, Escola):
            return PeriodoEscolarSerializer(
                obj.instituicao.periodos_escolares().all(),
                many=True,
                context={"escola": obj.instituicao},
            ).data
        else:
            return []

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

    def get_tipos_contagem(self, obj):
        if not isinstance(obj.instituicao, Escola):
            return None
        return TipoContagemSerializer(obj.instituicao.tipos_contagem, many=True).data

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
            "tipos_contagem": self.get_tipos_contagem(obj),
            "endereco": self.get_endereco(obj),
            "contato": self.get_contato(obj),
        }
        if hasattr(obj.instituicao, "acesso_modulo_medicao_inicial"):
            instituicao_dict["acesso_modulo_medicao_inicial"] = (
                obj.instituicao.acesso_modulo_medicao_inicial
            )
        if isinstance(obj.instituicao, DiretoriaRegional):
            instituicao_dict["possui_escolas_com_acesso_ao_medicao_inicial"] = (
                obj.instituicao.possui_escolas_com_acesso_ao_medicao_inicial
            )
        if isinstance(obj.instituicao, Escola):
            instituicao_dict["possui_alunos_regulares"] = (
                obj.instituicao.possui_alunos_regulares
            )
            instituicao_dict["eh_cei"] = self.get_eh_cei(obj)
            instituicao_dict["eh_cemei"] = self.get_eh_cemei(obj)
            instituicao_dict["eh_emebs"] = self.get_eh_emebs(obj)
            instituicao_dict["modulo_gestao"] = self.get_modulo_gestao(obj)
            if obj.instituicao.eh_cemei:
                instituicao_dict["quantidade_alunos_cei_da_cemei"] = (
                    obj.instituicao.quantidade_alunos_cei_da_cemei
                )
                instituicao_dict["quantidade_alunos_emei_da_cemei"] = (
                    obj.instituicao.quantidade_alunos_emei_da_cemei
                )
        if isinstance(obj.instituicao, Terceirizada):
            instituicao_dict["tipo_servico"] = self.get_tipo_servico(obj)
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
        )  # noqa


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


class CODAESerializer(serializers.ModelSerializer):
    quantidade_alunos = serializers.IntegerField()

    class Meta:
        model = Codae
        fields = "__all__"


class EscolaPeriodoEscolarSerializer(serializers.ModelSerializer):
    quantidade_alunos = serializers.IntegerField()
    escola = EscolaSimplissimaSerializer()
    periodo_escolar = PeriodoEscolarSimplesSerializer()

    class Meta:
        model = EscolaPeriodoEscolar
        fields = ("uuid", "quantidade_alunos", "escola", "periodo_escolar")


class ReponsavelSerializer(serializers.Serializer):
    cpf = serializers.CharField()
    nome = serializers.CharField()


class AlunoSerializer(serializers.ModelSerializer):
    escola = EscolaSimplesSerializer(required=False)
    nome_escola = serializers.SerializerMethodField()
    nome_dre = serializers.SerializerMethodField()
    responsaveis = ReponsavelSerializer(many=True)
    possui_dieta_especial = serializers.SerializerMethodField()

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
        elif user.tipo_usuario == "diretoriaregional":
            dietas_autorizadas = models.SolicitacoesDRE.get_autorizados_dieta_especial(
                dre_uuid=instituicao.uuid
            )
            dietas_inativas = models.SolicitacoesDRE.get_inativas_dieta_especial(
                dre_uuid=instituicao.uuid
            )
        else:
            dietas_autorizadas = (
                models.SolicitacoesCODAE.get_autorizados_dieta_especial()
            )
            dietas_inativas = models.SolicitacoesCODAE.get_inativas_dieta_especial()

        ids_dietas_autorizadas = dietas_autorizadas.values_list("id", flat=True)
        ids_dietas_inativas = dietas_inativas.values_list("id", flat=True)
        # Juntas as duas querysets.
        dietas_especiais = ids_dietas_autorizadas | ids_dietas_inativas

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
        )


class AlunoSimplesSerializer(serializers.ModelSerializer):
    escola = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Escola.objects.all()
    )

    class Meta:
        model = Aluno
        fields = ("uuid", "nome", "data_nascimento", "codigo_eol", "escola")


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


class AlunosMatriculadosPeriodoEscolaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlunosMatriculadosPeriodoEscola
        fields = ("periodo_escolar",)


class DiretoriaRegionalParaFiltroSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiretoriaRegional
        fields = ("uuid", "nome")


class LoteParaFiltroSerializer(serializers.ModelSerializer):
    diretoria_regional = DiretoriaRegionalParaFiltroSerializer()

    class Meta:
        model = Lote
        fields = ("uuid", "nome", "diretoria_regional")


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


class PeriodoEscolarParaFiltroSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoEscolar
        fields = ("uuid", "nome")


class EscolaAlunoPeriodoSerializer(serializers.ModelSerializer):
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


class DiaSuspensaoAtividadesSerializer(serializers.ModelSerializer):
    tipo_unidade = TipoUnidadeEscolarSerializer()
    criado_por = UsuarioSerializer()
    edital = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Edital.objects.all()
    )
    edital_numero = serializers.CharField(read_only=True)

    class Meta:
        model = DiaSuspensaoAtividades
        exclude = ("id",)


class TipoUnidadeEscolarSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoUnidadeEscolar
        fields = ("uuid", "iniciais")


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
