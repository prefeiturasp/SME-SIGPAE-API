"""Helpers da API do módulo de recebimento.

Funções que criam e atualizam a ficha de recebimento com todos os seus
relacionamentos (veículos, documentos, arquivos, questões e ocorrências).
"""

from rest_framework import serializers

from src.dados_comuns.utils import (
    convert_base64_to_contentfile,
    update_instance_from_dict,
)
from src.recebimento.models import (
    ArquivoFichaRecebimento,
    DocumentoFichaDeRecebimento,
    FichaDeRecebimento,
    OcorrenciaFichaRecebimento,
    QuestaoFichaRecebimento,
    VeiculoFichaDeRecebimento,
)


def criar_veiculos(instance, dados_veiculos):
    """Cria os veículos de uma ficha de recebimento.

    Args:
        instance: Ficha de recebimento.
        dados_veiculos: Lista de dados dos veículos.
    """
    for dados_veiculo in dados_veiculos:
        VeiculoFichaDeRecebimento.objects.create(
            ficha_recebimento=instance,
            **dados_veiculo,
        )


def criar_arquivos(instance, dados_arquivos):
    """Cria os arquivos de uma ficha de recebimento.

    Os arquivos são recebidos em base64 e convertidos para ``ContentFile``.

    Args:
        instance: Ficha de recebimento.
        dados_arquivos: Lista de dados dos arquivos (``arquivo`` e ``nome``).
    """
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
    """Cria as respostas às questões de conferência da ficha.

    Args:
        instance: Ficha de recebimento.
        dados_questoes: Lista de respostas às questões.
    """
    for dados_questao in dados_questoes:
        QuestaoFichaRecebimento.objects.create(
            ficha_recebimento=instance,
            **dados_questao,
        )


def criar_documentos_ficha(instance, dados_documentos):
    """Cria os vínculos entre a ficha e os documentos de recebimento.

    Args:
        instance: Ficha de recebimento.
        dados_documentos: Lista de dados dos documentos
            (``documento_recebimento`` e ``quantidade_recebida``).
    """
    for dados_documento in dados_documentos:
        documento_obj = dados_documento["documento_recebimento"]
        quantidade = dados_documento["quantidade_recebida"]

        DocumentoFichaDeRecebimento.objects.create(
            ficha_recebimento=instance,
            documento_recebimento=documento_obj,
            quantidade_recebida=quantidade,
        )


def criar_ocorrencias(instance, dados_ocorrencias):
    """Cria as ocorrências da ficha de recebimento.

    Permite no máximo uma ocorrência do tipo ``RECUSA`` por ficha.

    Args:
        instance: Ficha de recebimento.
        dados_ocorrencias: Lista de dados das ocorrências.

    Raises:
        serializers.ValidationError: Se houver mais de uma ocorrência
            ``RECUSA``.
    """
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
    """Cria uma nova ficha de recebimento com todos os relacionamentos.

    Args:
        validated_data: Dados validados da ficha (sem os relacionamentos).

    Returns:
        A ficha de recebimento criada.
    """
    dados_veiculos = validated_data.pop("veiculos", [])
    documentos_recebimento = validated_data.pop("documentos_recebimento", [])
    dados_arquivos = validated_data.pop("arquivos", [])
    dados_questoes = validated_data.pop("questoes", [])
    dados_ocorrencias = validated_data.pop("ocorrencias", [])

    # Cria a ficha de recebimento
    ficha = FichaDeRecebimento.objects.create(**validated_data)

    # Cria os relacionamentos
    criar_veiculos(ficha, dados_veiculos)
    criar_documentos_ficha(ficha, documentos_recebimento)
    criar_arquivos(ficha, dados_arquivos)
    criar_questoes(ficha, dados_questoes)
    criar_ocorrencias(ficha, dados_ocorrencias)

    return ficha


def atualizar_ficha(instance, validated_data):
    """Atualiza uma ficha de recebimento existente com todos os relacionamentos.

    Remove os relacionamentos existentes e os recria a partir dos dados
    validados.

    Args:
        instance: Ficha de recebimento existente.
        validated_data: Dados validados da ficha (sem os relacionamentos).

    Returns:
        A ficha de recebimento atualizada.
    """
    dados_veiculos = validated_data.pop("veiculos", [])
    documentos_recebimento = validated_data.pop("documentos_recebimento", [])
    dados_arquivos = validated_data.pop("arquivos", [])
    dados_questoes = validated_data.pop("questoes", [])
    dados_ocorrencias = validated_data.pop("ocorrencias", [])

    # Remove relacionamentos existentes
    instance.veiculos.all().delete()
    instance.documentos_ficha.all().delete()
    instance.arquivos.all().delete()
    instance.questoes_conferencia.through.objects.filter(
        ficha_recebimento=instance
    ).delete()
    instance.ocorrencias.all().delete()

    # Atualiza os campos da ficha
    instance = update_instance_from_dict(instance, validated_data, save=True)

    # Recria os relacionamentos
    criar_veiculos(instance, dados_veiculos)
    criar_documentos_ficha(instance, documentos_recebimento)
    criar_arquivos(instance, dados_arquivos)
    criar_questoes(instance, dados_questoes)
    criar_ocorrencias(instance, dados_ocorrencias)

    return instance
