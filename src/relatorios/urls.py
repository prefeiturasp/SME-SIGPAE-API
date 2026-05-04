from django.urls import path

from . import relatorios

urlpatterns = [
    path(
        r"relatorio-kit-lanche-unificado",
        relatorios.relatorio_kit_lanche_unificado,
        name="generate_pdf",
    ),
    path(
        r"relatorio-alteracao-cardapio",
        relatorios.relatorio_alteracao_cardapio,
        name="generate_pdf",
    ),
    path(
        r"relatorio-dieta-especial",
        relatorios.relatorio_dieta_especial,
        name="generate_pdf",
    ),
    path(
        r"relatorio-dieta-especial-protocolo",
        relatorios.relatorio_dieta_especial_protocolo,
        name="generate_pdf",
    ),
    path(
        r"relatorio-inclusao",
        relatorios.relatorio_inclusao_alimentacao_normal,
        name="generate_pdf",
    ),
    path(
        r"relatorio-produto",
        relatorios.relatorio_produto_homologacao,
        name="generate_pdf",
    ),
]
