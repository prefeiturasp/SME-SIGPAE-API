import pytest

from sme_sigpae_api.dados_comuns.fluxo_status import ReclamacaoProdutoWorkflow
from sme_sigpae_api.produto.models import AnaliseSensorial

pytestmark = pytest.mark.django_db


def test_unidade_medida_serializer(unidade_medida):
    from sme_sigpae_api.produto.api.serializers.serializers import (
        UnidadeMedidaSerialzer,
    )

    serializer = UnidadeMedidaSerialzer(unidade_medida)

    assert serializer.data is not None
    assert serializer.data["uuid"] == str(unidade_medida.uuid)
    assert serializer.data["nome"] == str(unidade_medida.nome)


def test_embalagem_produto_serializer(embalagem_produto):
    from sme_sigpae_api.produto.api.serializers.serializers import (
        EmbalagemProdutoSerialzer,
    )

    serializer = EmbalagemProdutoSerialzer(embalagem_produto)

    assert serializer.data is not None
    assert serializer.data["uuid"] == str(embalagem_produto.uuid)
    assert serializer.data["nome"] == embalagem_produto.nome


def test_marca_serializer(marca1):
    from sme_sigpae_api.produto.api.serializers.serializers import MarcaSerializer

    serializer = MarcaSerializer(marca1)

    assert serializer.data is not None
    assert serializer.data["uuid"] == str(marca1.uuid)
    assert serializer.data["nome"] == marca1.nome


def test_fabricante_serializer(fabricante):
    from sme_sigpae_api.produto.api.serializers.serializers import FabricanteSerializer

    serializer = FabricanteSerializer(fabricante)

    assert serializer.data is not None
    assert serializer.data["uuid"] == str(fabricante.uuid)
    assert serializer.data["nome"] == fabricante.nome


def test_especificacao_produto_serializer(especificacao_produto1):
    from sme_sigpae_api.produto.api.serializers.serializers import (
        EspecificacaoProdutoSerializer,
    )

    serializer = EspecificacaoProdutoSerializer(especificacao_produto1)

    assert serializer.data is not None
    assert serializer.data["uuid"] == str(especificacao_produto1.uuid)
    assert serializer.data["volume"] == especificacao_produto1.volume


def test_produto_edital(produto_edital):
    from sme_sigpae_api.produto.api.serializers.serializers import (
        CadastroProdutosEditalSerializer,
    )

    serializer = CadastroProdutosEditalSerializer(produto_edital)

    assert serializer.data is not None
    assert serializer.data["uuid"] == str(produto_edital.uuid)
    assert serializer.data["nome"] == produto_edital.nome


def test_reclamaco_produto_serializer(reclamacao_respondido_terceirizada):
    from sme_sigpae_api.produto.api.serializers.serializers import (
        ReclamacaoDeProdutoSerializer,
    )

    serializer = ReclamacaoDeProdutoSerializer(reclamacao_respondido_terceirizada)

    assert serializer.data is not None
    assert serializer.data["uuid"] == str(reclamacao_respondido_terceirizada.uuid)
    assert (
        serializer.data["reclamante_registro_funcional"]
        == reclamacao_respondido_terceirizada.reclamante_registro_funcional
    )
    assert (
        serializer.data["reclamante_cargo"]
        == reclamacao_respondido_terceirizada.reclamante_cargo
    )
    assert (
        serializer.data["reclamante_nome"]
        == reclamacao_respondido_terceirizada.reclamante_nome
    )
    assert (
        serializer.data["status"] == ReclamacaoProdutoWorkflow.RESPONDIDO_TERCEIRIZADA
    )


def test_analise_sensorial_serializer(analise_sensorial):
    from sme_sigpae_api.produto.api.serializers.serializers import (
        AnaliseSensorialSerializer,
    )

    serializer = AnaliseSensorialSerializer(analise_sensorial)

    assert serializer.data is not None
    assert serializer.data["uuid"] == str(analise_sensorial.uuid)
    assert serializer.data["status"] == AnaliseSensorial.STATUS_AGUARDANDO_RESPOSTA


def test_homologacao_listagem_serializer_tem_copia(homologacao_e_copia):
    from sme_sigpae_api.produto.api.serializers.serializers import (
        HomologacaoListagemSerializer,
    )

    serializer = HomologacaoListagemSerializer(homologacao_e_copia)

    assert serializer.data["tem_copia"] is True

    homologacao_e_copia.eh_copia = True
    serializer = HomologacaoListagemSerializer(homologacao_e_copia)
    assert serializer.data["tem_copia"] is False


def test_homologacao_reclamacao_serializer(hom_produto_com_editais):
    from sme_sigpae_api.produto.api.serializers.serializers import (
        HomologacaoReclamacaoSerializer,
    )

    serializer = HomologacaoReclamacaoSerializer(hom_produto_com_editais)
    data = serializer.data
    data_formatada = hom_produto_com_editais.criado_em.strftime("%d/%m/%Y %H:%M:%S")

    assert data["uuid"] == str(hom_produto_com_editais.uuid)
    assert data["status"] == str(hom_produto_com_editais.status)
    assert data["id_externo"] == str(hom_produto_com_editais.id_externo)
    assert data["criado_em"] == data_formatada
    assert data["status_titulo"] == "Rascunho"
    assert "rastro_terceirizada" in data

    assert "reclamacoes" in data
    assert isinstance(data["reclamacoes"], list)

    assert "editais_reclamacoes" in data
    assert isinstance(data["editais_reclamacoes"], list)
