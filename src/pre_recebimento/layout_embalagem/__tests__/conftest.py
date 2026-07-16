from io import BytesIO

import pytest
from django.utils import timezone
from model_bakery import baker

from src.dados_comuns.fluxo_status import (
    FichaTecnicaDoProdutoWorkflow,
    LayoutDeEmbalagemWorkflow,
)
from src.dados_comuns.models import LogSolicitacoesUsuario
from src.pre_recebimento.layout_embalagem.models import (
    ImagemDoTipoDeEmbalagem,
    LayoutDeEmbalagem,
    TipoDeEmbalagemDeLayout,
)
