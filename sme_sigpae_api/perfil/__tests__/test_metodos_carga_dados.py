import pytest

from sme_sigpae_api.cardapio.models import (
    MotivoAlteracaoCardapio,
    MotivoSuspensao,
    TipoAlimentacao,
)
from sme_sigpae_api.dados_comuns.models import Contato, TemplateMensagem
from sme_sigpae_api.dieta_especial.models import (
    AlergiaIntolerancia,
    Alimento,
    ClassificacaoDieta,
    MotivoAlteracaoUE,
    MotivoNegacao,
)
from sme_sigpae_api.escola.models import (
    DiretoriaRegional,
    Escola,
    Lote,
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
from sme_sigpae_api.produto.models import (
    InformacaoNutricional,
    ProtocoloDeDietaEspecial,
    TipoDeInformacaoNutricional,
)
from sme_sigpae_api.terceirizada.models import Contrato, Edital, Terceirizada
from utility.carga_dados.cardapio.importa_dados import (
    cria_motivoalteracaocardapio,
    cria_motivosuspensao,
    cria_tipo_alimentacao,
)
from utility.carga_dados.dados_comuns.importa_dados import (
    cria_contatos,
    cria_templatemensagem,
)
from utility.carga_dados.dieta_especial.importa_dados import (
    cria_alergia_intolerancias,
    cria_alimento,
    cria_classificacoes_dieta,
    cria_motivo_alteracao_ue,
    cria_motivo_negacao,
)
from utility.carga_dados.escola.importa_dados import (
    atualiza_tipo_gestao,
    cria_contatos_escola,
    cria_diretorias_regionais,
    cria_escola,
    cria_lotes,
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
from utility.carga_dados.perfil.importa_dados import cria_perfis
from utility.carga_dados.produto.importa_dados import (
    cria_diagnosticos,
    cria_informacao_nutricional,
    cria_tipo_informacao_nutricional,
)
from utility.carga_dados.terceirizada.importa_dados import (
    cria_contratos,
    cria_edital,
    cria_terceirizadas,
)
from utility.carga_dados.usuarios import cria_usuarios

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def lotes():
    cria_diretorias_regionais()
    cria_tipos_gestao()
    cria_terceirizadas()
    cria_lotes()


def test_criar_perfis():
    assert Perfil.objects.all().count() == 0
    cria_perfis()
    assert Perfil.objects.all().count() == 27


def test_cria_usuarios():
    assert Usuario.objects.all().count() == 0
    cria_usuarios()
    assert Usuario.objects.all().count() == 41


def test_cria_motivoalteracaocardapio():
    assert MotivoAlteracaoCardapio.objects.all().count() == 0
    cria_motivoalteracaocardapio()
    assert MotivoAlteracaoCardapio.objects.all().count() == 3


def test_cria_motivosuspensao():
    assert MotivoSuspensao.objects.all().count() == 0
    cria_motivosuspensao()
    assert MotivoSuspensao.objects.all().count() == 3


def test_cria_tipo_alimentacao():
    assert TipoAlimentacao.objects.all().count() == 0
    cria_tipo_alimentacao()
    assert TipoAlimentacao.objects.all().count() == 8


def test_cria_contatos():
    assert Contato.objects.all().count() == 0
    cria_contatos()
    assert Contato.objects.all().count() == 1


def test_cria_templatemensagem():
    assert TemplateMensagem.objects.all().count() == 0
    cria_templatemensagem()
    assert TemplateMensagem.objects.all().count() == 8


def test_cria_diretorias_regionais():
    assert DiretoriaRegional.objects.all().count() == 0
    cria_diretorias_regionais()
    assert DiretoriaRegional.objects.all().count() == 13


def test_cria_tipos_gestao():
    assert TipoGestao.objects.all().count() == 0
    cria_tipos_gestao()
    assert TipoGestao.objects.all().count() == 4


def test_cria_terceirizadas():
    assert Terceirizada.objects.all().count() == 0
    cria_terceirizadas()
    assert Terceirizada.objects.all().count() == 5


def test_cria_lotes():
    assert Lote.objects.all().count() == 0
    cria_diretorias_regionais()
    cria_tipos_gestao()
    cria_terceirizadas()
    cria_lotes()
    assert Lote.objects.all().count() == 18


def test_cria_edital():
    assert Edital.objects.all().count() == 0
    cria_edital()
    assert Edital.objects.all().count() == 1


def test_cria_contratos(lotes):
    assert Contrato.objects.all().count() == 0
    cria_edital()
    cria_contratos()
    assert Contrato.objects.all().count() == 5


def test_cria_subprefeituras(lotes):
    assert Subprefeitura.objects.all().count() == 0
    cria_subprefeituras()
    assert Subprefeitura.objects.all().count() == 32


def test_cria_motivo_inclusao_continua():
    assert MotivoInclusaoContinua.objects.all().count() == 0
    cria_motivo_inclusao_continua()
    assert MotivoInclusaoContinua.objects.all().count() == 4


def test_cria_motivo_inclusao_normal():
    assert MotivoInclusaoNormal.objects.all().count() == 0
    cria_motivo_inclusao_normal()
    assert MotivoInclusaoNormal.objects.all().count() == 3


def test_cria_kit_lanche_item():
    assert ItemKitLanche.objects.all().count() == 0
    cria_kit_lanche_item()
    assert ItemKitLanche.objects.all().count() == 7


def test_cria_kit_lanche():
    assert KitLanche.objects.all().count() == 0
    cria_kit_lanche()
    assert KitLanche.objects.all().count() == 10


def test_cria_tipo_informacao_nutricional():
    assert TipoDeInformacaoNutricional.objects.all().count() == 0
    cria_tipo_informacao_nutricional()
    assert TipoDeInformacaoNutricional.objects.all().count() == 6


def test_cria_informacao_nutricional():
    assert InformacaoNutricional.objects.all().count() == 0
    cria_tipo_informacao_nutricional()
    cria_informacao_nutricional()
    assert InformacaoNutricional.objects.all().count() == 43


def test_cria_alimento():
    assert Alimento.objects.all().count() == 0
    cria_alimento()
    assert Alimento.objects.all().count() == 243


def test_cria_classificacoes_dieta():
    assert ClassificacaoDieta.objects.all().count() == 0
    cria_classificacoes_dieta()
    assert ClassificacaoDieta.objects.all().count() == 4


def test_cria_motivo_negacao():
    assert MotivoNegacao.objects.all().count() == 0
    cria_motivo_negacao()
    assert MotivoNegacao.objects.all().count() == 14


def test_cria_motivo_alteracao_ue():
    assert MotivoAlteracaoUE.objects.all().count() == 0
    cria_motivo_alteracao_ue()
    assert MotivoAlteracaoUE.objects.all().count() == 2


def test_cria_alergia_intolerancias():
    assert AlergiaIntolerancia.objects.all().count() == 0
    cria_alergia_intolerancias()
    assert AlergiaIntolerancia.objects.all().count() == 322


def test_cria_diagnosticos():
    assert ProtocoloDeDietaEspecial.objects.all().count() == 0
    cria_usuarios()
    cria_diagnosticos()
    assert ProtocoloDeDietaEspecial.objects.all().count() == 322


def test_cria_tipo_unidade_escolar():
    assert TipoUnidadeEscolar.objects.all().count() == 0
    arquivo = "csv/escola_dre_codae_EMEF_EMEFM_EMEBS_CIEJA.csv"
    cria_tipo_unidade_escolar(arquivo)
    assert TipoUnidadeEscolar.objects.all().count() == 6


def test_cria_contatos_escola():
    assert Contato.objects.all().count() == 0
    arquivo = "csv/escola_dre_codae_EMEF_EMEFM_EMEBS_CIEJA.csv"
    cria_contatos_escola(arquivo)
    assert Contato.objects.all().count() == 394


def test_cria_escola(lotes):
    assert Escola.objects.all().count() == 0
    arquivo = "csv/escola_dre_codae_EMEF_EMEFM_EMEBS_CIEJA.csv"
    cria_contatos_escola(arquivo)
    cria_escola(arquivo=arquivo, legenda="Escola EMEF, EMEFM, EMEBS, CIEJA")
    assert Escola.objects.all().count() == 398


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
