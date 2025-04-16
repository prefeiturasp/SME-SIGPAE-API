from django.conf import settings
from django.core.management.base import BaseCommand

from utility.carga_dados.cardapio.importa_dados import (
    cria_combo_do_vinculo_tipo_alimentacao_periodo_tipo_ue,
    cria_motivoalteracaocardapio,
    cria_motivosuspensao,
    cria_substituicao_do_combo_do_vinculo_tipo_alimentacao_periodo_tipo_ue,
    cria_tipo_alimentacao,
    cria_vinculo_tipo_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar,
)
from utility.carga_dados.dados_comuns.importa_dados import cria_contatos  # noqa
from utility.carga_dados.dados_comuns.importa_dados import cria_templatemensagem
from utility.carga_dados.dieta_especial.importa_dados import (
    cria_alergia_intolerancias,
    cria_alimento,
    cria_alimento_proprio,
    cria_classificacoes_dieta,
    cria_motivo_alteracao_ue,
    cria_motivo_negacao,
)
from utility.carga_dados.escola.importa_dados import (
    atualiza_tipo_gestao,
    cria_contatos_escola,
    cria_diretorias_regionais,
    cria_escola,
    cria_escola_com_periodo_escolar,
    cria_lotes,
    cria_periodo_escolar,
    cria_subprefeituras,
    cria_tipo_unidade_escolar,
    cria_tipos_gestao,
)
from utility.carga_dados.inclusao_alimentacao.importa_dados import (
    cria_motivo_inclusao_continua,
    cria_motivo_inclusao_normal,
)
from utility.carga_dados.kit_lanche.importa_dados import cria_kit_lanche  # noqa
from utility.carga_dados.kit_lanche.importa_dados import cria_kit_lanche_item
from utility.carga_dados.perfil.importa_dados import cria_perfis, cria_vinculos
from utility.carga_dados.produto.importa_dados import (
    cria_diagnosticos,
    cria_fabricante,
    cria_informacao_nutricional,
    cria_marca,
    cria_produto,
    cria_produto_marca,
    cria_tipo_informacao_nutricional,
)
from utility.carga_dados.terceirizada.importa_dados import (
    adiciona_contato_em_terceirizada,
    cria_contratos,
    cria_edital,
    cria_terceirizadas,
)
from utility.carga_dados.usuarios import cria_usuarios


class Command(BaseCommand):
    help = "Importa dados iniciais no banco de dados."

    def handle(self, *args, **options):
        self.stdout.write("Importando dados...")

        # A ordem dos métodos é importante!
        # Por isso um monte de if.
        cria_perfis()

        if settings.DEBUG:
            cria_usuarios()  # Dev

        cria_motivoalteracaocardapio()
        cria_motivosuspensao()
        cria_tipo_alimentacao()

        if settings.DEBUG:
            cria_contatos()
            cria_templatemensagem()

        cria_diretorias_regionais()
        cria_tipos_gestao()

        cria_terceirizadas()
        cria_lotes()

        if settings.DEBUG:
            cria_edital()
            cria_contratos()

        cria_subprefeituras()
        cria_motivo_inclusao_continua()
        cria_motivo_inclusao_normal()

        if settings.DEBUG:
            cria_kit_lanche_item()
            cria_kit_lanche()

        cria_tipo_informacao_nutricional()
        cria_informacao_nutricional()

        # Dieta Especial
        cria_alimento()
        cria_classificacoes_dieta()
        cria_motivo_negacao()
        cria_motivo_alteracao_ue()
        cria_alergia_intolerancias()

        # Produto
        cria_diagnosticos()

        # Escola
        arquivo = "csv/escola_dre_codae_EMEF_EMEFM_EMEBS_CIEJA.csv"
        cria_tipo_unidade_escolar(arquivo)
        cria_contatos_escola(arquivo)
        cria_escola(arquivo=arquivo, legenda="Escola EMEF, EMEFM, EMEBS, CIEJA")  # noqa

        arquivo = "csv/escola_dre_codae_EMEI.csv"
        cria_tipo_unidade_escolar(arquivo)
        cria_contatos_escola(arquivo)
        cria_escola(arquivo=arquivo, legenda="Escola EMEI")

        arquivo = "csv/escola_dre_codae_CEI.csv"
        cria_tipo_unidade_escolar(arquivo)
        cria_contatos_escola(arquivo)
        cria_escola(arquivo=arquivo, legenda="Escola CEI")

        atualiza_tipo_gestao(codigo_eol_escola="099791")

        if settings.DEBUG:
            cria_periodo_escolar()
            cria_escola_com_periodo_escolar()
            cria_vinculo_tipo_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar()  # noqa
            cria_combo_do_vinculo_tipo_alimentacao_periodo_tipo_ue()
            cria_substituicao_do_combo_do_vinculo_tipo_alimentacao_periodo_tipo_ue()  # noqa

            cria_vinculos()
            cria_marca()
            cria_fabricante()
            cria_produto()
            cria_produto_marca()
            adiciona_contato_em_terceirizada()

            cria_alimento_proprio()
