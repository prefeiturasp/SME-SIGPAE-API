from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from ....dados_comuns.api.serializers import ContatoSerializer
from ....dados_comuns.utils import update_instance_from_dict
from ....escola.models import DiretoriaRegional, Lote
from ...models import (
    Contrato,
    Edital,
    EmailTerceirizadaPorModulo,
    Modalidade,
    Modulo,
    Nutricionista,
    Terceirizada,
    VigenciaContrato,
)


def cria_contatos(contatos):
    contatos_list = []
    for contato_json in contatos:
        contato = ContatoSerializer().create(contato_json)
        contatos_list.append(contato)
    return contatos_list


class NutricionistaCreateSerializer(serializers.ModelSerializer):
    contatos = ContatoSerializer(many=True)

    def create(self, validated_data):
        contatos = validated_data.pop("contatos", [])
        nutricionista = Nutricionista.objects.create(**validated_data)
        for contato_json in contatos:
            contato = ContatoSerializer().create(validated_data=contato_json)
            nutricionista.contatos.add(contato)
        return nutricionista

    class Meta:
        model = Nutricionista
        exclude = ("id", "terceirizada")


class VigenciaContratoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VigenciaContrato
        exclude = ("id", "contrato")


class ContratoCreateSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=False)
    numero = serializers.CharField(validators=[])
    lotes = serializers.SlugRelatedField(
        slug_field="uuid", many=True, queryset=Lote.objects.all()
    )

    terceirizada = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Terceirizada.objects.all()
    )

    diretorias_regionais = serializers.SlugRelatedField(
        slug_field="uuid", many=True, queryset=DiretoriaRegional.objects.all()
    )

    vigencias = VigenciaContratoCreateSerializer(many=True)

    def create(self, validated_data):
        lotes_json = validated_data.pop("lotes", [])
        dres_json = validated_data.pop("diretorias_regionais", [])
        vigencias_array = validated_data.pop("vigencias", [])

        vigencias = []
        for vigencia_json in vigencias_array:
            vigencia = VigenciaContratoCreateSerializer().create(vigencia_json)
            vigencias.append(vigencia)

        contrato = Contrato.objects.create(**validated_data)
        contrato.vigencias.set(vigencias)
        contrato.lotes.set(lotes_json)
        contrato.diretorias_regionais.set(dres_json)

        return contrato

    def update(self, instance, validated_data):
        lotes_json = validated_data.pop("lotes", [])
        terceirizadas_json = validated_data.pop("terceirizadas", [])
        dres_json = validated_data.pop("diretorias_regionais", [])

        vigencias_array = validated_data.pop("vigencias", [])

        instance.vigencias.all().delete()

        vigencias = []
        for vigencia_json in vigencias_array:
            vigencia = VigenciaContratoCreateSerializer().create(vigencia_json)
            vigencias.append(vigencia)

        update_instance_from_dict(instance, validated_data, save=True)

        instance.contratos.set(vigencias)
        instance.lotes.set(lotes_json)
        instance.terceirizadas.set(terceirizadas_json)
        instance.diretorias_regionais.set(dres_json)

        return instance

    class Meta:
        model = Contrato
        exclude = ("id",)


class ContratoAbastecimentoCreateSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=False)
    vigencias = VigenciaContratoCreateSerializer(many=True, required=False)
    modalidade = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Modalidade.objects.all(),
        required=False,
        allow_null=True,
    )

    def create(self, validated_data):
        vigencias_array = validated_data.pop("vigencias")

        vigencias = []
        for vigencia_json in vigencias_array:
            vigencia = VigenciaContratoCreateSerializer().create(vigencia_json)
            vigencias.append(vigencia)

        contrato = Contrato.objects.create(**validated_data)
        contrato.vigencias.set(vigencias)

        return contrato

    def update(self, instance, validated_data):
        dados_vigencias = validated_data.pop("vigencias")

        for dados_vigencia in dados_vigencias:
            vigencia = instance.vigencias.last()
            vigencia.data_inicial = dados_vigencia.get(
                "data_inicial", vigencia.data_inicial
            )
            vigencia.data_final = dados_vigencia.get("data_final", vigencia.data_final)
            vigencia.save()

        return update_instance_from_dict(instance, validated_data, save=True)

    class Meta:
        model = Contrato
        exclude = ("id",)


class TerceirizadaCreateSerializer(serializers.ModelSerializer):
    lotes = serializers.SlugRelatedField(
        slug_field="uuid", many=True, queryset=Lote.objects.all()
    )
    contatos = ContatoSerializer(many=True)

    def create(self, validated_data):
        lotes = validated_data.pop("lotes", [])
        contatos = validated_data.pop("contatos", [])
        terceirizada = Terceirizada.objects.create(**validated_data)

        checar_terceirizadas_inativacao = self.checar_terceirizadas_para_inativacao(
            terceirizada, lotes
        )

        terceirizada.lotes.set(lotes)

        """ Inativa terceirizadas que nao tem lote """
        Terceirizada.objects.filter(
            uuid__in=checar_terceirizadas_inativacao, lotes__isnull=True
        ).update(ativo=False)

        contatos_list = cria_contatos(contatos)
        terceirizada.contatos.set(contatos_list)

        return terceirizada

    def update(self, instance, validated_data):
        # TODO: Analisar complexidade
        # TODO: voltar aqui quando uma terceirizada tiver seu painel admin para criar suas nutris
        # aqui está tratando nutris como um dado escravo da Terceirizada

        lotes_array = validated_data.pop("lotes", [])
        contatos = validated_data.pop("contatos", [])

        instance.contatos.clear()

        if instance.lotes.exclude(id__in=[lote.id for lote in lotes_array]).exists():
            raise ValidationError(
                "Não pode remover um lote de uma empresa. É preciso atribuí-lo a outra empresa."
            )

        checar_terceirizadas_inativacao = self.checar_terceirizadas_para_inativacao(
            instance, lotes_array
        )

        update_instance_from_dict(instance, validated_data, save=True)

        contatos_list = cria_contatos(contatos)
        instance.contatos.set(contatos_list)
        instance.lotes.set(lotes_array)

        """ Inativa terceirizadas que nao tem lote """
        Terceirizada.objects.filter(
            uuid__in=checar_terceirizadas_inativacao, lotes__isnull=True
        ).update(ativo=False)

        return instance

    def checar_terceirizadas_para_inativacao(self, terceirizada, lotes):
        checar_terceirizadas_inativacao = []
        for lote in [
            lote
            for lote in lotes
            if lote not in terceirizada.lotes.all() and lote.terceirizada
        ]:
            checar_terceirizadas_inativacao.append(lote.terceirizada.uuid)
            lote.transferir_solicitacoes_gestao_alimentacao(terceirizada)
            lote.transferir_dietas_especiais(terceirizada)

        return checar_terceirizadas_inativacao

    class Meta:
        model = Terceirizada
        exclude = ("id",)


class EmpresaNaoTerceirizadaCreateSerializer(serializers.ModelSerializer):
    contatos = ContatoSerializer(required=False, many=True)
    contratos = ContratoAbastecimentoCreateSerializer(many=True, required=False)

    def create(self, validated_data):
        contatos = validated_data.pop("contatos", [])
        contratos_array = validated_data.pop("contratos", [])

        empresa = Terceirizada.objects.create(**validated_data)

        if contatos:
            contatos_list = cria_contatos(contatos)
            empresa.contatos.set(contatos_list)

        contratos = []
        for contrato_json in contratos_array:
            contrato = ContratoAbastecimentoCreateSerializer().create(contrato_json)
            contratos.append(contrato)

        empresa.contratos.set(contratos)

        return empresa

    def update(self, instance, validated_data):
        contatos = validated_data.pop("contatos", [])
        dados_contratos = validated_data.pop("contratos", [])

        for dados_contrato in dados_contratos:
            encerrado = dados_contrato.pop("encerrado")
            modalidade = dados_contrato.get("modalidade")
            dados_contrato["modalidade"] = modalidade.uuid if modalidade else None
            if not encerrado:
                uuid_contrato = dados_contrato.get("uuid")
                if uuid_contrato is not None:
                    contrato = instance.contratos.filter(uuid=uuid_contrato).last()
                    serializer = ContratoAbastecimentoCreateSerializer(
                        instance=contrato, data=dados_contrato, partial=True
                    )
                else:
                    serializer = ContratoAbastecimentoCreateSerializer(
                        data=dados_contrato
                    )

                if serializer.is_valid(raise_exception=True):
                    contrato = serializer.save()
                    instance.contratos.add(contrato)

        instance.contatos.all().delete()
        update_instance_from_dict(instance, validated_data, save=True)
        contatos_list = cria_contatos(contatos)
        instance.contatos.set(contatos_list)

        return instance

    class Meta:
        model = Terceirizada
        exclude = ("id",)


class EditalContratosCreateSerializer(serializers.ModelSerializer):
    contratos = ContratoCreateSerializer(many=True)

    def create(self, validated_data):
        contratos_array = validated_data.pop("contratos")

        contratos = []
        for contrato_json in contratos_array:
            contrato = ContratoCreateSerializer().create(contrato_json)
            contratos.append(contrato)

        edital = Edital.objects.create(**validated_data)
        edital.contratos.set(contratos)
        return edital

    def update(self, instance, validated_data):
        contrato_array = validated_data.pop("contratos")

        contratos = []
        for contrato_json in contrato_array:
            lotes = contrato_json.pop("lotes")
            diretorias_regionais = contrato_json.pop("diretorias_regionais")
            vigencias_array = contrato_json.pop("vigencias")

            if "uuid" in contrato_json:
                contrato, _ = Contrato.objects.update_or_create(
                    uuid=contrato_json.pop("uuid"),
                    defaults=contrato_json,
                )
            else:
                contrato = ContratoCreateSerializer().create(contrato_json)
            contrato.vigencias.all().delete()

            vigencias = []
            for vigencia_json in vigencias_array:
                vigencia = VigenciaContratoCreateSerializer().create(vigencia_json)
                vigencias.append(vigencia)

            contrato.vigencias.set(vigencias)

            contrato.lotes.set(lotes)
            contrato.diretorias_regionais.set(diretorias_regionais)
            contrato.vigencias.set(vigencias)
            contratos.append(contrato)

        update_instance_from_dict(instance, validated_data, save=True)

        instance.contratos.set(contratos)

        return instance

    class Meta:
        model = Edital
        exclude = ("id",)


class CreateEmailTerceirizadaPorModuloSerializer(serializers.ModelSerializer):
    terceirizada = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Terceirizada.objects.all()
    )
    modulo = serializers.SlugRelatedField(
        slug_field="nome", required=True, queryset=Modulo.objects.all()
    )
    criado_por = serializers.CharField(required=False)

    def create(self, validated_data):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        validated_data["criado_por"] = user
        EmailTerceirizada = EmailTerceirizadaPorModulo.objects.create(**validated_data)
        return EmailTerceirizada

    class Meta:
        model = EmailTerceirizadaPorModulo
        exclude = ("id",)
