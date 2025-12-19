import pytest

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    MotivoAlteracaoCardapio,
)
from sme_sigpae_api.cardapio.base.models import (
    ComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao.models import MotivoSuspensao
from sme_sigpae_api.dados_comuns.models import Contato, TemplateMensagem
from sme_sigpae_api.dieta_especial.models import (
    AlergiaIntolerancia,
    Alimento,
    AlimentoProprio,
    ClassificacaoDieta,
    MotivoAlteracaoUE,
    MotivoNegacao,
)
from sme_sigpae_api.escola.models import (
    DiretoriaRegional,
    Escola,
    EscolaPeriodoEscolar,
    Lote,
    PeriodoEscolar,
    Subprefeitura,
    TipoGestao,
    TipoUnidadeEscolar,
)
from sme_sigpae_api.inclusao_alimentacao.models import (
    MotivoInclusaoContinua,
    MotivoInclusaoNormal,
)
from sme_sigpae_api.kit_lanche.models import ItemKitLanche, KitLanche
from sme_sigpae_api.perfil.models import Perfil, Usuario
from sme_sigpae_api.perfil.models.perfil import Vinculo
from sme_sigpae_api.produto.models import (
    Fabricante,
    InformacaoNutricional,
    Marca,
    Produto,
    ProtocoloDeDietaEspecial,
    TipoDeInformacaoNutricional,
)
from sme_sigpae_api.terceirizada.models import Contrato, Edital, Terceirizada
from utility.carga_dados.cardapio.importa_dados import (
    cria_combo_do_vinculo_tipo_alimentacao_periodo_tipo_ue,
    cria_motivoalteracaocardapio,
    cria_motivosuspensao,
    cria_substituicao_do_combo_do_vinculo_tipo_alimentacao_periodo_tipo_ue,
    cria_tipo_alimentacao,
    cria_vinculo_tipo_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar,
)
from utility.carga_dados.dados_comuns.importa_dados import (
    cria_contatos,
    cria_templatemensagem,
)
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
from utility.carga_dados.kit_lanche.importa_dados import (
    cria_kit_lanche,
    cria_kit_lanche_item,
)
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

pytestmark = pytest.mark.django_db(transaction=True)


def test_criar_perfis():
    assert Perfil.objects.count() == 0
    cria_perfis()
    assert Perfil.objects.count() == 28


def test_cria_usuarios():
    assert Usuario.objects.count() == 0
    cria_usuarios()
    assert Usuario.objects.count() == 41


def test_cria_motivoalteracaocardapio():
    assert MotivoAlteracaoCardapio.objects.count() == 0
    cria_motivoalteracaocardapio()
    assert MotivoAlteracaoCardapio.objects.count() == 3


def test_cria_motivosuspensao():
    assert MotivoSuspensao.objects.count() == 0
    cria_motivosuspensao()
    assert MotivoSuspensao.objects.count() == 3


def test_cria_tipo_alimentacao():
    assert TipoAlimentacao.objects.count() == 0
    cria_tipo_alimentacao()
    assert TipoAlimentacao.objects.count() == 8


def test_cria_contatos():
    assert Contato.objects.count() == 0
    cria_contatos()
    assert Contato.objects.count() == 1


def test_cria_templatemensagem():
    assert TemplateMensagem.objects.count() == 0
    cria_templatemensagem()
    assert TemplateMensagem.objects.count() == 8


def test_cria_diretorias_regionais():
    assert DiretoriaRegional.objects.count() == 0
    cria_diretorias_regionais()
    assert DiretoriaRegional.objects.count() == 13


def test_cria_tipos_gestao():
    assert TipoGestao.objects.count() == 0
    cria_tipos_gestao()
    assert TipoGestao.objects.count() == 4


def test_cria_terceirizadas():
    assert Terceirizada.objects.count() == 0
    cria_terceirizadas()
    assert Terceirizada.objects.count() == 5


def test_cria_lotes():
    assert Lote.objects.count() == 0
    cria_diretorias_regionais()
    cria_tipos_gestao()
    cria_terceirizadas()
    cria_lotes()
    assert Lote.objects.count() == 18


def test_cria_edital():
    assert Edital.objects.count() == 0
    cria_edital()
    assert Edital.objects.count() == 1


def test_cria_contratos(lotes):
    assert Contrato.objects.count() == 0
    cria_edital()
    cria_contratos()
    assert Contrato.objects.count() == 5


def test_cria_subprefeituras(lotes):
    assert Subprefeitura.objects.count() == 0
    cria_subprefeituras()
    assert Subprefeitura.objects.count() == 32


def test_cria_motivo_inclusao_continua():
    quantidade_atual_motivos = MotivoInclusaoContinua.objects.count()
    cria_motivo_inclusao_continua()
    assert MotivoInclusaoContinua.objects.count() == quantidade_atual_motivos + 4


def test_cria_motivo_inclusao_normal():
    quantidade_atual_motivos = MotivoInclusaoNormal.objects.count()
    cria_motivo_inclusao_normal()
    assert MotivoInclusaoNormal.objects.count() == quantidade_atual_motivos + 3


def test_cria_kit_lanche_item():
    assert ItemKitLanche.objects.count() == 0
    cria_kit_lanche_item()
    assert ItemKitLanche.objects.count() == 7


def test_cria_kit_lanche():
    assert KitLanche.objects.count() == 0
    cria_kit_lanche()
    assert KitLanche.objects.count() == 10


def test_cria_tipo_informacao_nutricional():
    assert TipoDeInformacaoNutricional.objects.count() == 0
    cria_tipo_informacao_nutricional()
    assert TipoDeInformacaoNutricional.objects.count() == 6


def test_cria_informacao_nutricional():
    assert InformacaoNutricional.objects.count() == 0
    cria_tipo_informacao_nutricional()
    cria_informacao_nutricional()
    assert InformacaoNutricional.objects.count() == 43


def test_cria_alimento():
    assert Alimento.objects.count() == 0
    cria_alimento()
    assert Alimento.objects.count() == 243


def test_cria_classificacoes_dieta():
    assert ClassificacaoDieta.objects.count() == 0
    cria_classificacoes_dieta()
    assert ClassificacaoDieta.objects.count() == 4


def test_cria_motivo_negacao():
    assert MotivoNegacao.objects.count() == 0
    cria_motivo_negacao()
    assert MotivoNegacao.objects.count() == 14


def test_cria_motivo_alteracao_ue():
    assert MotivoAlteracaoUE.objects.count() == 0
    cria_motivo_alteracao_ue()
    assert MotivoAlteracaoUE.objects.count() == 2


def test_cria_alergia_intolerancias():
    assert AlergiaIntolerancia.objects.count() == 0
    cria_alergia_intolerancias()
    assert AlergiaIntolerancia.objects.count() == 322


def test_cria_diagnosticos():
    assert ProtocoloDeDietaEspecial.objects.count() == 0
    cria_usuarios()
    cria_diagnosticos()
    assert ProtocoloDeDietaEspecial.objects.count() == 322


def test_cria_tipo_unidade_escolar():
    assert TipoUnidadeEscolar.objects.count() == 0
    arquivo = "csv/escola_dre_codae_EMEF_EMEFM_EMEBS_CIEJA.csv"
    cria_tipo_unidade_escolar(arquivo)
    assert TipoUnidadeEscolar.objects.count() == 6


def test_cria_contatos_escola():
    assert Contato.objects.count() == 0
    arquivo = "csv/escola_dre_codae_EMEF_EMEFM_EMEBS_CIEJA.csv"
    cria_contatos_escola(arquivo)
    assert Contato.objects.count() == 394


def test_cria_escola(lotes):
    assert Escola.objects.count() == 0
    arquivo = "csv/escola_dre_codae_EMEF_EMEFM_EMEBS_CIEJA.csv"
    cria_contatos_escola(arquivo)
    cria_escola(arquivo=arquivo, legenda="Escola EMEF, EMEFM, EMEBS, CIEJA")
    assert Escola.objects.count() == 398


def test_atualiza_tipo_gestao(lotes):
    codigo_eol_escola = "099791"
    assert Escola.objects.filter(codigo_eol=codigo_eol_escola).first() is None

    arquivo = "csv/escola_dre_codae_EMEF_EMEFM_EMEBS_CIEJA.csv"
    cria_contatos_escola(arquivo)
    cria_escola(arquivo=arquivo, legenda="Escola EMEF, EMEFM, EMEBS, CIEJA")

    assert Escola.objects.get(codigo_eol=codigo_eol_escola) is not None
    atualiza_tipo_gestao(codigo_eol_escola=codigo_eol_escola)
    assert (
        Escola.objects.get(codigo_eol=codigo_eol_escola, tipo_gestao__nome="MISTA")
        is not None
    )


def test_cria_periodo_escolar():
    assert PeriodoEscolar.objects.count() == 0
    cria_tipo_alimentacao()
    cria_periodo_escolar()
    assert PeriodoEscolar.objects.count() == 7


def test_cria_escola_com_periodo_escolar(lotes):
    assert EscolaPeriodoEscolar.objects.count() == 0
    arquivo = "csv/escola_dre_codae_EMEF_EMEFM_EMEBS_CIEJA.csv"
    cria_contatos_escola(arquivo)
    cria_escola(arquivo=arquivo, legenda="Escola EMEF, EMEFM, EMEBS, CIEJA")
    cria_tipo_alimentacao()
    cria_periodo_escolar()

    cria_escola_com_periodo_escolar()
    assert EscolaPeriodoEscolar.objects.count() == 2786


def test_cria_vinculo_tipo_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar():
    assert (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.count() == 0
    )
    arquivo = "csv/escola_dre_codae_EMEF_EMEFM_EMEBS_CIEJA.csv"
    cria_tipo_unidade_escolar(arquivo)
    cria_tipo_alimentacao()
    cria_periodo_escolar()
    cria_vinculo_tipo_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar()
    assert (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.count() == 42
    )


def test_cria_combo_do_vinculo_tipo_alimentacao_periodo_tipo_ue():
    assert ComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.count() == 0
    arquivo = "csv/escola_dre_codae_EMEF_EMEFM_EMEBS_CIEJA.csv"
    cria_tipo_unidade_escolar(arquivo)
    cria_tipo_alimentacao()
    cria_periodo_escolar()
    cria_vinculo_tipo_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar()
    vinculos = (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.count()
    )
    cria_combo_do_vinculo_tipo_alimentacao_periodo_tipo_ue()
    minimo = 7 * vinculos
    maximo = 12 * vinculos
    assert minimo < ComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.count() < maximo


def test_cria_substituicao_do_combo_do_vinculo_tipo_alimentacao_periodo_tipo_ue():
    assert SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.count() == 0
    arquivo = "csv/escola_dre_codae_EMEF_EMEFM_EMEBS_CIEJA.csv"
    cria_tipo_unidade_escolar(arquivo)
    cria_tipo_alimentacao()
    cria_periodo_escolar()
    cria_vinculo_tipo_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar()
    cria_combo_do_vinculo_tipo_alimentacao_periodo_tipo_ue()

    combos = ComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.count()
    cria_substituicao_do_combo_do_vinculo_tipo_alimentacao_periodo_tipo_ue()
    assert (
        SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.count()
        == combos
    )


def test_cria_vinculos(lotes):
    assert Vinculo.objects.count() == 0
    cria_perfis()
    cria_usuarios()

    arquivo = "csv/escola_dre_codae_EMEF_EMEFM_EMEBS_CIEJA.csv"
    cria_contatos_escola(arquivo)
    cria_escola(arquivo=arquivo, legenda="Escola EMEF, EMEFM, EMEBS, CIEJA")

    arquivo = "csv/escola_dre_codae_EMEI.csv"
    cria_contatos_escola(arquivo)
    cria_escola(arquivo=arquivo, legenda="Escola EMEI")

    arquivo = "csv/escola_dre_codae_CEI.csv"
    cria_contatos_escola(arquivo)
    cria_escola(arquivo=arquivo, legenda="Escola CEI")

    cria_vinculos()
    assert Vinculo.objects.count() == 30


def test_cria_marca():
    assert Marca.objects.count() == 0
    cria_marca()
    assert Marca.objects.count() == 193


def test_cria_fabricante():
    assert Fabricante.objects.count() == 0
    cria_fabricante()
    assert Fabricante.objects.count() == 193


def test_cria_produto(lotes):
    assert Produto.objects.count() == 0
    cria_perfis()
    cria_usuarios()

    arquivo = "csv/escola_dre_codae_EMEF_EMEFM_EMEBS_CIEJA.csv"
    cria_contatos_escola(arquivo)
    cria_escola(arquivo=arquivo, legenda="Escola EMEF, EMEFM, EMEBS, CIEJA")

    arquivo = "csv/escola_dre_codae_EMEI.csv"
    cria_contatos_escola(arquivo)
    cria_escola(arquivo=arquivo, legenda="Escola EMEI")

    arquivo = "csv/escola_dre_codae_CEI.csv"
    cria_contatos_escola(arquivo)
    cria_escola(arquivo=arquivo, legenda="Escola CEI")
    cria_vinculos()

    cria_marca()
    cria_fabricante()
    cria_produto()
    assert Produto.objects.count() == 63


def test_cria_produto_marca(lotes):
    assert Produto.objects.count() == 0
    cria_perfis()
    cria_usuarios()

    arquivo = "csv/escola_dre_codae_EMEF_EMEFM_EMEBS_CIEJA.csv"
    cria_contatos_escola(arquivo)
    cria_escola(arquivo=arquivo, legenda="Escola EMEF, EMEFM, EMEBS, CIEJA")

    arquivo = "csv/escola_dre_codae_EMEI.csv"
    cria_contatos_escola(arquivo)
    cria_escola(arquivo=arquivo, legenda="Escola EMEI")

    arquivo = "csv/escola_dre_codae_CEI.csv"
    cria_contatos_escola(arquivo)
    cria_escola(arquivo=arquivo, legenda="Escola CEI")
    cria_vinculos()

    cria_marca()
    cria_fabricante()
    cria_produto_marca()
    assert Produto.objects.count() == 212


def test_adiciona_contato_em_terceirizada(lotes):
    for t in Terceirizada.objects.all():
        assert t.contatos.count() == 0

    arquivo = "csv/escola_dre_codae_EMEF_EMEFM_EMEBS_CIEJA.csv"
    cria_contatos_escola(arquivo)
    arquivo = "csv/escola_dre_codae_EMEI.csv"
    cria_contatos_escola(arquivo)
    arquivo = "csv/escola_dre_codae_CEI.csv"
    cria_contatos_escola(arquivo)

    adiciona_contato_em_terceirizada()
    for t in Terceirizada.objects.all():
        assert t.contatos.count() == 2


def test_cria_alimento_proprio():
    assert AlimentoProprio.objects.count() == 0
    cria_marca()
    cria_alimento_proprio()
    assert AlimentoProprio.objects.count() == 9
