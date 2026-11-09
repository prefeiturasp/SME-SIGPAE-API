from django.contrib.admin.sites import AdminSite

from src.pos_recebimento.admin import (
    LoteMemorandoOcorrenciaAdmin,
    LoteMemorandoOcorrenciaInline,
    MemorandoOcorrenciaAdmin,
)
from src.pos_recebimento.models import (
    LoteMemorandoOcorrencia,
    MemorandoOcorrencia,
)


def test_memorando_ocorrencia_admin_configurado():
    admin_instance = MemorandoOcorrenciaAdmin(
        model=MemorandoOcorrencia,
        admin_site=AdminSite(),
    )

    assert admin_instance.list_display == (
        "uuid",
        "escola",
        "categoria",
        "produto",
        "tipo_ocorrencia",
        "criado_em",
    )
    assert admin_instance.list_filter == ("categoria", "tipo_ocorrencia")
    assert admin_instance.inlines == (LoteMemorandoOcorrenciaInline,)
    assert admin_instance.readonly_fields == (
        "uuid",
        "criado_em",
        "alterado_em",
        "criado_por",
    )
    assert admin_instance.search_fields == (
        "escola__nome",
        "escola__codigo_eol",
        "produto",
        "uuid",
    )
    assert admin_instance.list_select_related == ("escola",)


def test_lote_memorando_ocorrencia_admin_configurado():
    admin_instance = LoteMemorandoOcorrenciaAdmin(
        model=LoteMemorandoOcorrencia,
        admin_site=AdminSite(),
    )

    assert admin_instance.list_display == (
        "memorando",
        "lote",
        "marca",
        "data_fabricacao",
        "data_validade",
        "quantidade_problema_devolucao",
        "ordem",
    )
    assert admin_instance.search_fields == ("memorando__uuid", "lote", "marca")
    assert admin_instance.list_select_related == ("memorando",)


def test_lote_memorando_ocorrencia_inline_configurado():
    inline = LoteMemorandoOcorrenciaInline(
        parent_model=MemorandoOcorrencia,
        admin_site=AdminSite(),
    )

    assert inline.model is LoteMemorandoOcorrencia
    assert inline.extra == 0
    assert inline.fields == (
        "lote",
        "marca",
        "data_fabricacao",
        "data_validade",
        "quantidade_problema_devolucao",
        "ordem",
    )
