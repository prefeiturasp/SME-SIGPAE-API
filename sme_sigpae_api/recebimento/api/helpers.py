from rest_framework import serializers

from sme_sigpae_api.dados_comuns.utils import (
    convert_base64_to_contentfile,
    update_instance_from_dict,
)
from sme_sigpae_api.recebimento.models import (
    ArquivoFichaRecebimento,
    FichaDeRecebimento,
    OcorrenciaFichaRecebimento,
    QuestaoFichaRecebimento,
    VeiculoFichaDeRecebimento,
)


def criar_veiculos(instance, dados_veiculos):
    for dados_veiculo in dados_veiculos:
        VeiculoFichaDeRecebimento.objects.create(
            ficha_recebimento=instance,
            **dados_veiculo,
        )


def criar_arquivos(instance, dados_arquivos):
    for dados_arquivo in dados_arquivos:
        arquivo = dados_arquivo.get("arquivo")
        if arquivo:
            arquivo_content = convert_base64_to_contentfile(arquivo)
            ArquivoFichaRecebimento.objects.create(
                ficha_recebimento=instance,
                arquivo=arquivo_content,
                nome=dados_arquivo.get("nome", ""),
            )


def criar_questoes(instance, dados_questoes):
    for dados_questao in dados_questoes:
        QuestaoFichaRecebimento.objects.create(
            ficha_recebimento=instance,
            **dados_questao,
        )


def criar_ocorrencias(instance, dados_ocorrencias):
    recusa_count = sum(
        1
        for ocorrencia in dados_ocorrencias
        if ocorrencia.get("tipo") == OcorrenciaFichaRecebimento.TIPO_RECUSA
    )

    if recusa_count > 1:
        raise serializers.ValidationError(
            {
                "ocorrencias": "Apenas uma ocorrência do tipo RECUSA é permitida por ficha de recebimento."
            }
        )

    for dados_ocorrencia in dados_ocorrencias:
        OcorrenciaFichaRecebimento.objects.create(
            ficha_recebimento=instance,
            **dados_ocorrencia,
        )


def criar_ficha(validated_data):
    """Cria uma nova ficha de recebimento com todos os relacionamentos."""
    dados_veiculos = validated_data.pop("veiculos", [])
    documentos_recebimento = validated_data.pop("documentos_recebimento", [])
    dados_arquivos = validated_data.pop("arquivos", [])
    dados_questoes = validated_data.pop("questoes", [])
    dados_ocorrencias = validated_data.pop("ocorrencias", [])

    # Cria a ficha de recebimento
    ficha = FichaDeRecebimento.objects.create(**validated_data)
    ficha.documentos_recebimento.set(documentos_recebimento)

    # Cria os relacionamentos
    criar_veiculos(ficha, dados_veiculos)
    criar_arquivos(ficha, dados_arquivos)
    criar_questoes(ficha, dados_questoes)
    criar_ocorrencias(ficha, dados_ocorrencias)

    return ficha


def atualizar_ficha(instance, validated_data):
    """Atualiza uma ficha de recebimento existente com todos os relacionamentos."""
    dados_veiculos = validated_data.pop("veiculos", [])
    documentos_recebimento = validated_data.pop("documentos_recebimento", [])
    dados_arquivos = validated_data.pop("arquivos", [])
    dados_questoes = validated_data.pop("questoes", [])
    dados_ocorrencias = validated_data.pop("ocorrencias", [])

    # Remove relacionamentos existentes
    instance.veiculos.all().delete()
    instance.documentos_recebimento.clear()
    instance.arquivos.all().delete()
    instance.questoes_conferencia.through.objects.filter(
        ficha_recebimento=instance
    ).delete()
    instance.ocorrencias.all().delete()

    # Atualiza os campos da ficha
    instance = update_instance_from_dict(instance, validated_data, save=True)

    # Atualiza os documentos de recebimento
    instance.documentos_recebimento.set(documentos_recebimento)

    # Recria os relacionamentos
    criar_veiculos(instance, dados_veiculos)
    criar_arquivos(instance, dados_arquivos)
    criar_questoes(instance, dados_questoes)
    criar_ocorrencias(instance, dados_ocorrencias)

    return instance
