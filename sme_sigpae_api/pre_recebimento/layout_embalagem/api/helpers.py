from sme_sigpae_api.dados_comuns.utils import (
    convert_base64_to_contentfile,
)
from sme_sigpae_api.pre_recebimento.layout_embalagem.models import (
    ImagemDoTipoDeEmbalagem,
    TipoDeEmbalagemDeLayout,
)


def cria_tipos_de_embalagens(tipos_de_embalagens, layout_de_embalagem=None):
    for embalagem in tipos_de_embalagens:
        imagens = embalagem.pop("imagens_do_tipo_de_embalagem", [])
        tipo_de_embalagem = TipoDeEmbalagemDeLayout.objects.create(
            layout_de_embalagem=layout_de_embalagem, **embalagem
        )
        for img in imagens:
            data = convert_base64_to_contentfile(img.get("arquivo"))
            ImagemDoTipoDeEmbalagem.objects.create(
                tipo_de_embalagem=tipo_de_embalagem,
                arquivo=data,
                nome=img.get("nome", ""),
            )
