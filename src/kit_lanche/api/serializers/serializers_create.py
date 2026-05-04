from rest_framework import serializers

from ....dados_comuns.utils import update_instance_from_dict
from ....dados_comuns.validators import (
    campo_deve_ser_deste_tipo,
    campo_nao_pode_ser_nulo,
    deve_pedir_com_antecedencia,
    deve_ser_no_mesmo_ano_corrente,
    nao_pode_ser_no_passado,
)
from ....escola.models import Aluno, DiretoriaRegional, Escola, FaixaEtaria
from ...models import (
    EscolaQuantidade,
    FaixasQuantidadesKitLancheCEIdaCEMEI,
    KitLanche,
    SolicitacaoKitLanche,
    SolicitacaoKitLancheAvulsa,
    SolicitacaoKitLancheCEIdaCEMEI,
    SolicitacaoKitLancheCEMEI,
    SolicitacaoKitLancheEMEIdaCEMEI,
    SolicitacaoKitLancheUnificada,
)
from ..validators import (
    escola_quantidade_deve_ter_1_ou_mais_kits,
    escola_quantidade_nao_deve_ter_kits_e_tempo_passeio,
    escola_quantidade_pedido_nao_pode_ser_mais_que_alunos,
    solicitacao_deve_ter_0_kit,
    solicitacao_deve_ter_1_ou_mais_kits,
    valida_quantidade_kits_tempo_passeio,
    valida_tempo_passeio_lista_igual,
    valida_tempo_passeio_lista_nao_igual,
)


class SolicitacaoKitLancheCreationSerializer(serializers.ModelSerializer):
    kits = serializers.SlugRelatedField(
        slug_field="uuid", many=True, required=True, queryset=KitLanche.objects.all()
    )
    tempo_passeio_explicacao = serializers.CharField(
        source="get_tempo_passeio_display", required=False, read_only=True
    )

    def validate_data(self, data):
        nao_pode_ser_no_passado(data)
        deve_pedir_com_antecedencia(data)
        deve_ser_no_mesmo_ano_corrente(data)
        return data

    def validate(self, attrs):
        tempo_passeio = attrs.get("tempo_passeio")
        qtd_kits = len(attrs.get("kits"))
        valida_quantidade_kits_tempo_passeio(tempo_passeio, qtd_kits)
        return attrs

    def create(self, validated_data):
        kits = validated_data.pop("kits", [])
        solicitacao_kit_lanche = SolicitacaoKitLanche.objects.create(**validated_data)
        solicitacao_kit_lanche.kits.set(kits)
        return solicitacao_kit_lanche

    def update(self, instance, validated_data):
        kits = validated_data.pop("kits", [])
        update_instance_from_dict(instance, validated_data)
        instance.kits.set(kits)
        instance.save()

        return instance

    class Meta:
        model = SolicitacaoKitLanche
        exclude = ("id",)


class SolicitacaoKitLancheAvulsaCreationSerializer(serializers.ModelSerializer):
    solicitacao_kit_lanche = SolicitacaoKitLancheCreationSerializer(required=True)
    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=Escola.objects.all()
    )
    alunos_com_dieta_especial_participantes = serializers.SlugRelatedField(
        slug_field="uuid", many=True, queryset=Aluno.objects.all()
    )
    status_explicacao = serializers.CharField(
        source="status", required=False, read_only=True
    )

    def validate(self, attrs):
        quantidade_aluno_passeio = attrs.get("quantidade_alunos")
        data_evento = attrs.get("solicitacao_kit_lanche").get("data")
        campo_nao_pode_ser_nulo(
            quantidade_aluno_passeio,
            mensagem="O campo Quantidade de aluno não pode ser nulo",
        )
        campo_deve_ser_deste_tipo(
            quantidade_aluno_passeio,
            tipo=int,
            mensagem="Quantidade de aluno de ser do tipo int",
        )
        nao_pode_ser_no_passado(data_evento)
        deve_pedir_com_antecedencia(data_evento)
        deve_ser_no_mesmo_ano_corrente(data_evento)
        return attrs

    def create(self, validated_data):
        validated_data["criado_por"] = self.context["request"].user
        solicitacao_kit_lanche_json = validated_data.pop("solicitacao_kit_lanche")
        solicitacao_kit_lanche = SolicitacaoKitLancheCreationSerializer().create(
            solicitacao_kit_lanche_json
        )
        alunos_com_dieta = validated_data.pop("alunos_com_dieta_especial_participantes")
        solicitacao_kit_avulsa = SolicitacaoKitLancheAvulsa.objects.create(
            solicitacao_kit_lanche=solicitacao_kit_lanche, **validated_data
        )
        solicitacao_kit_avulsa.save()

        solicitacao_kit_avulsa.alunos_com_dieta_especial_participantes.set(
            alunos_com_dieta
        )

        return solicitacao_kit_avulsa

    def update(self, instance, validated_data):
        solicitacao_kit_lanche_json = validated_data.pop("solicitacao_kit_lanche")
        solicitacao_kit_lanche = instance.solicitacao_kit_lanche

        alunos_com_dieta = validated_data.pop("alunos_com_dieta_especial_participantes")

        SolicitacaoKitLancheCreationSerializer().update(
            solicitacao_kit_lanche, solicitacao_kit_lanche_json
        )

        update_instance_from_dict(instance, validated_data)

        instance.save()

        instance.alunos_com_dieta_especial_participantes.set(alunos_com_dieta)

        return instance

    class Meta:
        model = SolicitacaoKitLancheAvulsa
        exclude = ("id", "status")


class EscolaQuantidadeCreationSerializer(serializers.ModelSerializer):
    kits = serializers.SlugRelatedField(
        slug_field="uuid", many=True, required=True, queryset=KitLanche.objects.all()
    )
    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=Escola.objects.all()
    )

    tempo_passeio_explicacao = serializers.CharField(
        source="get_tempo_passeio_display", required=False, read_only=True
    )

    solicitacao_unificada = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=SolicitacaoKitLancheUnificada.objects.all(),
    )

    def validate(self, attrs):
        qtd_kits = len(attrs.get("kits"))
        tempo_passeio = attrs.get("tempo_passeio")
        valida_quantidade_kits_tempo_passeio(tempo_passeio, qtd_kits)
        return attrs

    def create(self, validated_data):
        kits = validated_data.pop("kits", [])
        escola_quantiade = EscolaQuantidade.objects.create(**validated_data)
        escola_quantiade.kits.set(kits)
        return escola_quantiade

    def update(self, instance, validated_data):
        kits = validated_data.pop("kits", [])
        update_instance_from_dict(instance, validated_data)
        instance.kits.set(kits)
        instance.save()
        return instance

    class Meta:
        model = EscolaQuantidade
        exclude = ("id",)


class SolicitacaoKitLancheUnificadaCreationSerializer(serializers.ModelSerializer):
    solicitacao_kit_lanche = SolicitacaoKitLancheCreationSerializer(required=False)
    diretoria_regional = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=DiretoriaRegional.objects.all()
    )
    escolas_quantidades = EscolaQuantidadeCreationSerializer(many=True, required=False)
    status_explicacao = serializers.CharField(
        source="status", required=False, read_only=True
    )

    def create(self, validated_data):
        lista_igual = validated_data.get("lista_kit_lanche_igual", True)
        solicitacao_kit_lanche = validated_data.pop("solicitacao_kit_lanche")
        escolas_quantidades = validated_data.pop("escolas_quantidades")
        validated_data["criado_por"] = self.context["request"].user

        solicitacao_base = SolicitacaoKitLancheCreationSerializer().create(
            solicitacao_kit_lanche
        )

        if not lista_igual:
            solicitacao_base.kits.set([])

        lista_quantidade_escola = self._gera_escolas_quantidades(escolas_quantidades)

        solicitacao_kit_unificada = SolicitacaoKitLancheUnificada.objects.create(
            solicitacao_kit_lanche=solicitacao_base, **validated_data
        )

        solicitacao_kit_unificada.escolas_quantidades.set(lista_quantidade_escola)
        return solicitacao_kit_unificada

    def update(self, instance, validated_data):
        lista_igual = validated_data.get("lista_kit_lanche_igual", True)
        escolas_quantidades = validated_data.pop("escolas_quantidades")
        solicitacao_kit_lanche_json = validated_data.pop("solicitacao_kit_lanche")

        solicitacao_kit_lanche = instance.solicitacao_kit_lanche
        instance.escolas_quantidades.all().delete()

        if not lista_igual:
            solicitacao_kit_lanche.kits.set([])

        SolicitacaoKitLancheCreationSerializer().update(
            solicitacao_kit_lanche, solicitacao_kit_lanche_json
        )

        lista_quantidade_escola = self._gera_escolas_quantidades(escolas_quantidades)

        instance.escolas_quantidades.set(lista_quantidade_escola)

        update_instance_from_dict(instance, validated_data)
        instance.save()
        return instance

    def validate(self, data):
        self._valida_dados_base(data)
        self._valida_escolas_quantidades(data)

        return data

    def _valida_dados_base(self, data):
        solicitacao_kit_lanche = data.get("solicitacao_kit_lanche")
        kits_base = solicitacao_kit_lanche.get("kits", [])
        lista_igual = data.get("lista_kit_lanche_igual", True)
        tempo_passeio_base = solicitacao_kit_lanche.get("tempo_passeio", None)

        if lista_igual:
            valida_tempo_passeio_lista_igual(tempo_passeio_base)
            solicitacao_deve_ter_1_ou_mais_kits(len(kits_base))
        else:
            valida_tempo_passeio_lista_nao_igual(tempo_passeio_base)
            solicitacao_deve_ter_0_kit(len(kits_base))

    def _valida_escolas_quantidades(self, data):
        escolas_quantidades = data.get("escolas_quantidades")
        lista_igual = data.get("lista_kit_lanche_igual", True)

        if lista_igual:
            cont = 0
            for escola_quantidade in escolas_quantidades:
                kits = escola_quantidade.get("kits")
                escola_quantidade_nao_deve_ter_kits_e_tempo_passeio(
                    num_kits=len(kits),
                    tempo_passeio=escola_quantidade.get("tempo_passeio"),
                    indice=cont,
                )
                escola_quantidade_pedido_nao_pode_ser_mais_que_alunos(
                    escola=escola_quantidade.get("escola"),
                    quantidade_alunos_pedido=escola_quantidade.get("quantidade_alunos"),
                    indice=cont,
                )
                cont += 1
        else:
            cont = 0
            for escola_quantidade in escolas_quantidades:
                kits = escola_quantidade.get("kits")
                escola_quantidade_deve_ter_1_ou_mais_kits(len(kits), indice=cont)
                cont += 1

    def _gera_escolas_quantidades(self, escolas_quantidades):
        escola_quantidade_lista = []
        for escola_quantidade_json in escolas_quantidades:
            escola_quantidade_object = EscolaQuantidadeCreationSerializer().create(
                escola_quantidade_json
            )
            escola_quantidade_lista.append(escola_quantidade_object)
        return escola_quantidade_lista

    def _atualiza_escolas_quantidades(
        self, escolas_quantidades, escolas_quantidades_lista
    ):
        # TODO: quando o o len dos dois for diferente, tratar esse diff...
        for index in range(len(escolas_quantidades)):
            EscolaQuantidadeCreationSerializer().update(
                instance=escolas_quantidades[index],
                validated_data=escolas_quantidades_lista[index],
            )

    class Meta:
        model = SolicitacaoKitLancheUnificada
        exclude = ("id", "status")


class FaixasQuantidadesKitLancheCEIdaCEMEICreateSerializer(serializers.ModelSerializer):
    solicitacao_kit_lanche_cei_da_cemei = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=SolicitacaoKitLancheCEIdaCEMEI.objects.all(),
    )
    faixa_etaria = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=FaixaEtaria.objects.all()
    )

    class Meta:
        model = FaixasQuantidadesKitLancheCEIdaCEMEI
        exclude = ("id",)


class SolicitacaoKitLancheCEIdaCEMEICreateSerializer(serializers.ModelSerializer):
    kits = serializers.SlugRelatedField(
        slug_field="uuid", many=True, required=True, queryset=KitLanche.objects.all()
    )
    alunos_com_dieta_especial_participantes = serializers.SlugRelatedField(
        slug_field="uuid", many=True, required=False, queryset=Aluno.objects.all()
    )
    solicitacao_kit_lanche_cemei = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=SolicitacaoKitLancheCEMEI.objects.all(),
    )
    faixas_quantidades = FaixasQuantidadesKitLancheCEIdaCEMEICreateSerializer(many=True)

    class Meta:
        model = SolicitacaoKitLancheCEIdaCEMEI
        exclude = ("id",)


class SolicitacaoKitLancheEMEIdaCEMEICreateSerializer(serializers.ModelSerializer):
    kits = serializers.SlugRelatedField(
        slug_field="uuid", many=True, required=True, queryset=KitLanche.objects.all()
    )
    alunos_com_dieta_especial_participantes = serializers.SlugRelatedField(
        slug_field="uuid", many=True, required=False, queryset=Aluno.objects.all()
    )
    solicitacao_kit_lanche_cemei = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=SolicitacaoKitLancheCEMEI.objects.all(),
    )

    class Meta:
        model = SolicitacaoKitLancheEMEIdaCEMEI
        exclude = ("id",)


class SolicitacaoKitLancheCEMEICreateSerializer(serializers.ModelSerializer):
    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=Escola.objects.all()
    )
    solicitacao_cei = SolicitacaoKitLancheCEIdaCEMEICreateSerializer(required=False)
    solicitacao_emei = SolicitacaoKitLancheEMEIdaCEMEICreateSerializer(required=False)

    @staticmethod
    def criar_solicitacao_cei(solicitacao_cei, instance):
        if not solicitacao_cei:
            return
        kits = solicitacao_cei.pop("kits")
        alunos_com_dieta_especial_participantes = solicitacao_cei.pop(
            "alunos_com_dieta_especial_participantes", []
        )
        faixas_quantidades = solicitacao_cei.pop("faixas_quantidades")
        solicitacao_cei["solicitacao_kit_lanche_cemei"] = instance
        solicitacao_kit_lanche_cei_da_cemei = (
            SolicitacaoKitLancheCEIdaCEMEI.objects.create(**solicitacao_cei)
        )
        solicitacao_kit_lanche_cei_da_cemei.kits.set(kits)
        solicitacao_kit_lanche_cei_da_cemei.alunos_com_dieta_especial_participantes.set(
            alunos_com_dieta_especial_participantes
        )

        faixas_quantidades = [
            dict(
                item,
                **{
                    "solicitacao_kit_lanche_cei_da_cemei": solicitacao_kit_lanche_cei_da_cemei
                }
            )
            for item in faixas_quantidades
        ]
        for faixa_quantidade in faixas_quantidades:
            FaixasQuantidadesKitLancheCEIdaCEMEI.objects.create(**faixa_quantidade)

    @staticmethod
    def criar_solicitacao_emei(solicitacao_emei, instance):
        if not solicitacao_emei:
            return
        kits = solicitacao_emei.pop("kits")
        alunos_com_dieta_especial_participantes = solicitacao_emei.pop(
            "alunos_com_dieta_especial_participantes", []
        )
        solicitacao_emei["solicitacao_kit_lanche_cemei"] = instance
        solicitacao_kit_lanche_emei_da_cemei = (
            SolicitacaoKitLancheEMEIdaCEMEI.objects.create(**solicitacao_emei)
        )
        solicitacao_kit_lanche_emei_da_cemei.kits.set(kits)
        solicitacao_kit_lanche_emei_da_cemei.alunos_com_dieta_especial_participantes.set(
            alunos_com_dieta_especial_participantes
        )

    def create(self, validated_data):
        if "status" in validated_data:
            validated_data.pop("status")

        validated_data["criado_por"] = self.context["request"].user
        solicitacao_cei = validated_data.pop("solicitacao_cei", None)
        solicitacao_emei = validated_data.pop("solicitacao_emei", [])
        solicitacao_kit_lanche_cemei = SolicitacaoKitLancheCEMEI.objects.create(
            **validated_data
        )

        self.criar_solicitacao_cei(solicitacao_cei, solicitacao_kit_lanche_cemei)
        self.criar_solicitacao_emei(solicitacao_emei, solicitacao_kit_lanche_cemei)

        return solicitacao_kit_lanche_cemei

    def update(self, instance, validated_data):
        if "status" in validated_data:
            validated_data.pop("status")

        if hasattr(instance, "solicitacao_cei"):
            solicitacao_cei = instance.solicitacao_cei
            solicitacao_cei.kits.clear()
            solicitacao_cei.alunos_com_dieta_especial_participantes.clear()
            solicitacao_cei.solicitacao_kit_lanche_cemei = None
            solicitacao_cei.delete()
        if hasattr(instance, "solicitacao_emei"):
            solicitacao_emei = instance.solicitacao_emei
            solicitacao_emei.kits.clear()
            solicitacao_emei.alunos_com_dieta_especial_participantes.clear()
            solicitacao_emei.solicitacao_kit_lanche_cemei = None
            solicitacao_emei.delete()

        solicitacao_cei = validated_data.pop("solicitacao_cei", None)
        solicitacao_emei = validated_data.pop("solicitacao_emei", None)

        update_instance_from_dict(instance, validated_data)
        instance.save()

        self.criar_solicitacao_cei(solicitacao_cei, instance)
        self.criar_solicitacao_emei(solicitacao_emei, instance)

        return instance

    class Meta:
        model = SolicitacaoKitLancheCEMEI
        exclude = ("id",)
