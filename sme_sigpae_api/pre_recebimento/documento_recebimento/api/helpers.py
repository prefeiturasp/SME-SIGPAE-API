from sme_sigpae_api.dados_comuns.utils import (
    convert_base64_to_contentfile,
)
from sme_sigpae_api.pre_recebimento.documento_recebimento.models import (
    ArquivoDoTipoDeDocumento,
    DataDeFabricaoEPrazo,
    TipoDeDocumentoDeRecebimento,
)


def cria_tipos_de_documentos(tipos_de_documentos, documento_de_recebimento=None):
    for documento in tipos_de_documentos:
        arquivos = documento.pop("arquivos_do_tipo_de_documento", [])
        tipo_de_documento = TipoDeDocumentoDeRecebimento.objects.create(
            documento_recebimento=documento_de_recebimento, **documento
        )
        for arq in arquivos:
            data = convert_base64_to_contentfile(arq.get("arquivo"))
            ArquivoDoTipoDeDocumento.objects.create(
                tipo_de_documento=tipo_de_documento,
                arquivo=data,
                nome=arq.get("nome", ""),
            )


def cria_datas_e_prazos_doc_recebimento(datas_e_prazos, doc_recebimento):
    datas_criadas = []
    for data in datas_e_prazos:
        datas_criadas.append(
            DataDeFabricaoEPrazo.objects.create(
                documento_recebimento=doc_recebimento, **data
            )
        )
    return datas_criadas



