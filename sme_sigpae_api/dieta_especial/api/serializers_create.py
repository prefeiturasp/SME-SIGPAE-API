import datetime
import uuid
from copy import deepcopy

from rest_framework import serializers

from ...dados_comuns.constants import DEZ_MB
from ...dados_comuns.utils import (
    convert_base64_to_contentfile,
    convert_date_format,
    remove_multiplos_espacos,
    size,
    update_instance_from_dict,
)
from ...dados_comuns.validators import deve_ser_no_passado, deve_ter_extensao_valida
from ...escola.api.serializers import AlunoNaoMatriculadoSerializer
from ...escola.models import Aluno, Escola, Responsavel
from ...produto.api.serializers import serializers as ser
from ...produto.models import Produto
from ...terceirizada.models import Edital
from ..models import (
    Alimento,
    AlimentoSubstituto,
    Anexo,
    MotivoAlteracaoUE,
    ProtocoloPadraoDietaEspecial,
    SolicitacaoDietaEspecial,
    SubstituicaoAlimento,
    SubstituicaoAlimentoProtocoloPadrao,
)
from ..utils import log_create, log_update
from .validators import AlunoSerializerValidator, edital_ja_existe_protocolo


class AnexoCreateSerializer(serializers.ModelSerializer):
    arquivo = serializers.CharField()
    nome = serializers.CharField()

    def validate_nome(self, nome):
        deve_ter_extensao_valida(nome)
        return nome

    class Meta:
        model = Anexo
        fields = ("arquivo", "nome")


class SubstituicaoCreateSerializer(serializers.ModelSerializer):
    substitutos = ser.SubstitutosSerializer(many=True)

    class Meta:
        model = SubstituicaoAlimento
        fields = "__all__"


class SubstituicaoProtocoloPadraoCreateSerializer(serializers.ModelSerializer):
    substitutos = ser.SubstitutosSerializer(many=True)

    class Meta:
        model = SubstituicaoAlimentoProtocoloPadrao
        exclude = ("protocolo_padrao",)


class SubstituicaoAutorizarSerializer(serializers.ModelSerializer):
    substitutos = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=Produto.objects.all(), many=True
    )
    alimentos_substitutos = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=Alimento.objects.all(), many=True
    )

    class Meta:
        model = SubstituicaoAlimento
        fields = "__all__"


class SolicitacaoDietaEspecialCreateSerializer(serializers.ModelSerializer):
    anexos = serializers.ListField(child=AnexoCreateSerializer(), required=True)
    aluno_json = serializers.JSONField(required=False)
    aluno_nao_matriculado_data = AlunoNaoMatriculadoSerializer(required=False)
    aluno_nao_matriculado = serializers.BooleanField(default=False)

    def validate_anexos(self, anexos):
        for anexo in anexos:
            filesize = size(anexo["arquivo"])
            if filesize > DEZ_MB:
                msg = "O tamanho máximo de um arquivo é 10MB"
                raise serializers.ValidationError(msg)
        if not anexos:
            raise serializers.ValidationError("Anexos não pode ser vazio")
        return anexos

    def validate_aluno_json(self, aluno_json):
        for value in ["codigo_eol", "nome", "data_nascimento"]:
            if value not in aluno_json:
                raise serializers.ValidationError(f"deve ter atributo {value}")
        validator = AlunoSerializerValidator(data=aluno_json)
        if validator.is_valid():
            return aluno_json
        else:
            raise serializers.ValidationError(f"{validator.errors}")

    def create(self, validated_data):  # noqa C901
        validated_data["criado_por"] = self.context["request"].user

        anexos = validated_data.pop("anexos", [])
        aluno_data = validated_data.pop("aluno_json", None)
        aluno_nao_matriculado_data = validated_data.pop(
            "aluno_nao_matriculado_data", None
        )
        aluno_nao_matriculado = validated_data.pop("aluno_nao_matriculado")

        escola_destino = None
        tipo_solicitacao = None

        if aluno_nao_matriculado:
            codigo_eol_escola = aluno_nao_matriculado_data.pop("codigo_eol_escola")
            responsavel_data = aluno_nao_matriculado_data.pop("responsavel")
            cpf_aluno = aluno_nao_matriculado_data.get("cpf")
            nome_aluno = aluno_nao_matriculado_data.get("nome")
            data_nascimento = aluno_nao_matriculado_data.get("data_nascimento")

            escola = Escola.objects.get(codigo_eol=codigo_eol_escola)
            escola_destino = escola

            aluno = None

            if cpf_aluno:
                aluno = Aluno.objects.filter(cpf=cpf_aluno).last()
            if not aluno:
                aluno = Aluno.objects.filter(
                    nome__iexact=nome_aluno,
                    responsaveis__cpf=responsavel_data.get("cpf"),
                ).last()
            if not aluno:
                aluno = Aluno.objects.create(
                    nome=nome_aluno, data_nascimento=data_nascimento, cpf=cpf_aluno
                )

            if SolicitacaoDietaEspecial.aluno_possui_dieta_especial_pendente(aluno):
                msg = "Aluno já possui Solicitação de Dieta Especial pendente"
                raise serializers.ValidationError(msg)

            aluno.escola = validated_data["criado_por"].vinculo_atual.instituicao
            aluno.nao_matriculado = True
            aluno.save()

            responsavel, _ = Responsavel.objects.get_or_create(
                cpf=responsavel_data.get("cpf"),
                defaults={"nome": responsavel_data.get("nome")},
            )
            aluno.responsaveis.add(responsavel)
            tipo_solicitacao = "ALUNO_NAO_MATRICULADO"

        else:
            aluno = self._get_or_create_aluno(aluno_data)

            if SolicitacaoDietaEspecial.aluno_possui_dieta_especial_pendente(aluno):
                msg = "Aluno já possui Solicitação de Dieta Especial pendente"
                raise serializers.ValidationError(msg)

            aluno.escola = validated_data["criado_por"].vinculo_atual.instituicao
            escola_destino = aluno.escola
            aluno.save()
            tipo_solicitacao = "COMUM"

        solicitacao = SolicitacaoDietaEspecial.objects.create(**validated_data)
        solicitacao.aluno = aluno
        solicitacao.ativo = False
        solicitacao.escola_destino = escola_destino
        solicitacao.tipo_solicitacao = tipo_solicitacao
        solicitacao.save()

        for anexo in anexos:
            data = convert_base64_to_contentfile(anexo.get("arquivo"))
            Anexo.objects.create(
                solicitacao_dieta_especial=solicitacao,
                arquivo=data,
                nome=anexo.get("nome", ""),
            )

        solicitacao.inicia_fluxo(user=self.context["request"].user)
        return solicitacao

    def _get_or_create_aluno(self, aluno_data):
        escola = self.context["request"].user.vinculo_atual.instituicao
        codigo_eol_aluno = aluno_data.get("codigo_eol")
        nome_aluno = aluno_data.get("nome")
        data_nascimento_aluno = convert_date_format(
            date=aluno_data.get("data_nascimento"),
            from_format="%d/%m/%Y",
            to_format="%Y-%m-%d",
        )
        deve_ser_no_passado(
            datetime.datetime.strptime(data_nascimento_aluno, "%Y-%m-%d").date()
        )
        try:
            aluno = Aluno.objects.get(codigo_eol=codigo_eol_aluno)
        except Aluno.DoesNotExist:
            aluno = Aluno(
                codigo_eol=codigo_eol_aluno,
                nome=nome_aluno,
                data_nascimento=data_nascimento_aluno,
                escola=escola,
            )
            aluno.save()
        return aluno

    class Meta:
        model = SolicitacaoDietaEspecial
        fields = (
            "aluno_json",
            "uuid",
            "nome_completo_pescritor",
            "registro_funcional_pescritor",
            "observacoes",
            "criado_em",
            "anexos",
            "aluno_nao_matriculado",
            "aluno_nao_matriculado_data",
            "dieta_para_recreio_ferias",
            "periodo_recreio_inicio",
            "periodo_recreio_fim",
        )

    def validate(self, data):
        if data.get("dieta_para_recreio_ferias"):
            if not data.get("periodo_recreio_inicio") or not data.get(
                "periodo_recreio_fim"
            ):
                raise serializers.ValidationError(
                    "Os campos de período são obrigatórios quando dieta para recreio nas férias está selecionada."
                )
            if data["periodo_recreio_fim"] < data["periodo_recreio_inicio"]:
                raise serializers.ValidationError(
                    "A data final não pode ser anterior à data inicial."
                )
        return data


class AlteracaoUESerializer(serializers.ModelSerializer):
    escola_destino = serializers.SlugRelatedField(
        slug_field="codigo_eol", required=True, queryset=Escola.objects.all()
    )

    dieta_alterada = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=SolicitacaoDietaEspecial.objects.all(),
    )

    motivo_alteracao = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=MotivoAlteracaoUE.objects.all()
    )

    class Meta:
        model = SolicitacaoDietaEspecial
        fields = (
            "escola_destino",
            "dieta_alterada",
            "data_inicio",
            "data_termino",
            "motivo_alteracao",
            "observacoes_alteracao",
        )

    def create(self, validated_data):  # noqa C901
        dieta_alterada = validated_data.get("dieta_alterada")
        escola_destino = validated_data.get("escola_destino")
        motivo_alteracao = validated_data.get("motivo_alteracao")
        data_inicio = validated_data.get("data_inicio")
        data_termino = validated_data.get("data_termino")
        observacoes_alteracao = validated_data.get("observacoes_alteracao", "")

        try:
            motivo_recreio_ferias = MotivoAlteracaoUE.objects.get(nome="Dieta Especial - Recreio nas Férias")
        except MotivoAlteracaoUE.DoesNotExist:
            raise serializers.ValidationError(
                "Motivo 'Dieta Especial - Recreio nas Férias' não encontrado."
            )

        if motivo_alteracao == motivo_recreio_ferias and SolicitacaoDietaEspecial.aluno_possui_dieta_especial_autorizada_alteracao_ue_recreio_ferias(
            dieta_alterada.aluno, dieta_alterada, motivo_recreio_ferias
        ):
            raise serializers.ValidationError(
                "Já foi realizada uma alteração de UE para o aluno por motivo de Recreio nas Férias"
            )

        if SolicitacaoDietaEspecial.aluno_possui_dieta_especial_pendente(
            dieta_alterada.aluno
        ):
            raise serializers.ValidationError(
                "Aluno já possui Solicitação de Dieta Especial pendente"
            )

        substituicoes = SubstituicaoAlimento.objects.filter(
            solicitacao_dieta_especial=dieta_alterada
        )
        anexos = Anexo.objects.filter(solicitacao_dieta_especial=dieta_alterada)

        solicitacao_alteracao = deepcopy(dieta_alterada)
        solicitacao_alteracao.id = None
        solicitacao_alteracao.status = None
        solicitacao_alteracao.ativo = False
        solicitacao_alteracao.uuid = uuid.uuid4()
        solicitacao_alteracao.tipo_solicitacao = "ALTERACAO_UE"
        solicitacao_alteracao.motivo_alteracao_ue = motivo_alteracao
        solicitacao_alteracao.escola_destino = escola_destino
        solicitacao_alteracao.dieta_alterada = dieta_alterada
        solicitacao_alteracao.data_termino = data_termino
        solicitacao_alteracao.data_inicio = data_inicio
        solicitacao_alteracao.observacoes_alteracao = observacoes_alteracao
        solicitacao_alteracao.save()
        solicitacao_alteracao.alergias_intolerancias.add(
            *dieta_alterada.alergias_intolerancias.all()
        )

        solicitacao_alteracao.inicia_fluxo(user=self.context["request"].user)

        for substituicao in substituicoes:
            substituicao_alteracao = deepcopy(substituicao)
            substituicao_alteracao.id = None
            substituicao_alteracao.solicitacao_dieta_especial = solicitacao_alteracao
            substituicao_alteracao.save()
            substituicao_alteracao.substitutos.add(*substituicao.substitutos.all())
            substituicao_alteracao.alimentos_substitutos.add(
                *substituicao.alimentos_substitutos.all()
            )

        for anexo in anexos:
            anexo_alteracao = deepcopy(anexo)
            anexo_alteracao.id = None
            anexo_alteracao.solicitacao_dieta_especial = solicitacao_alteracao
            anexo_alteracao.save()

        return solicitacao_alteracao


class ProtocoloPadraoDietaEspecialSerializerCreate(serializers.ModelSerializer):
    substituicoes = SubstituicaoProtocoloPadraoCreateSerializer(many=True)
    editais = serializers.ListField(child=serializers.CharField(), write_only=True)

    def create(self, validated_data):  # noqa C901
        substituicoes = validated_data.pop("substituicoes")
        editais = validated_data.pop("editais")
        nome_protocolo = remove_multiplos_espacos(
            validated_data["nome_protocolo"]
        ).upper()
        protocolos = Edital.objects.check_editais_already_has_nome_protocolo(
            editais, nome_protocolo
        )
        if protocolos:
            edital_ja_existe_protocolo(protocolos, len(editais))
        validated_data["nome_protocolo"] = nome_protocolo.upper()
        protocolo_padrao = ProtocoloPadraoDietaEspecial.objects.create(**validated_data)
        if editais and len(editais):
            protocolo_padrao.editais.set(Edital.objects.filter(uuid__in=editais))
        for substituicao in substituicoes:
            substitutos = substituicao.pop("substitutos", None)
            substituicao["protocolo_padrao"] = protocolo_padrao
            subst_obj = SubstituicaoAlimentoProtocoloPadrao.objects.create(
                **substituicao
            )
            if substitutos:
                for substituto in substitutos:
                    if isinstance(substituto, Alimento):
                        AlimentoSubstituto.objects.create(
                            substituicao_alimento_protocolo_padrao=subst_obj,
                            alimento=substituto,
                        )
                    if isinstance(substituto, Produto):
                        subst_obj.substitutos.add(substituto)

        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        log_create(protocolo_padrao, user=user)

        return protocolo_padrao

    def update(self, instance, validated_data):  # noqa C901
        new_editais = validated_data.get("editais")
        new_editais = Edital.objects.filter(uuid__in=new_editais)
        editais = validated_data.pop("editais")
        nome_protocolo = validated_data["nome_protocolo"]
        protocolos = Edital.objects.check_editais_already_has_nome_protocolo(
            editais, nome_protocolo
        )
        if nome_protocolo == self.instance.nome_protocolo:
            protocolos = protocolos.exclude(
                uuid__in=list(instance.editais.values_list("uuid", flat=True))
            )
        if protocolos:
            edital_ja_existe_protocolo(protocolos, len(editais))

        substituicoes = validated_data.pop("substituicoes")

        validated_data["nome_protocolo"] = nome_protocolo.upper()
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user

        log_update(
            instance,
            validated_data,
            instance.substituicoes,
            substituicoes,
            new_editais,
            instance.editais,
            user,
        )

        instance.editais.clear()
        if editais and len(editais):
            instance.editais.set(Edital.objects.filter(uuid__in=editais))

        instance.substituicoes.all().delete()
        update_instance_from_dict(instance, validated_data, save=True)

        for substituicao in substituicoes:
            substitutos = substituicao.pop("substitutos", None)
            substituicao["protocolo_padrao"] = instance
            subst_obj = SubstituicaoAlimentoProtocoloPadrao.objects.create(
                **substituicao
            )
            if substitutos:
                for substituto in substitutos:
                    if isinstance(substituto, Alimento):
                        AlimentoSubstituto.objects.create(
                            substituicao_alimento_protocolo_padrao=subst_obj,
                            alimento=substituto,
                        )
                    if isinstance(substituto, Produto):
                        subst_obj.substitutos.add(substituto)
        return instance

    class Meta:
        model = ProtocoloPadraoDietaEspecial
        fields = (
            "uuid",
            "nome_protocolo",
            "status",
            "orientacoes_gerais",
            "criado_em",
            "substituicoes",
            "editais",
        )
