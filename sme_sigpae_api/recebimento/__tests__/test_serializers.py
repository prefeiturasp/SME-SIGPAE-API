import pytest

from sme_sigpae_api.recebimento.api.serializers.serializers import (
    ArquivoFichaRecebimentoSerializer,
    DadosCronogramaSerializer,
    FichaDeRecebimentoDetalharSerializer,
    OcorrenciaFichaRecebimentoSerializer,
    QuestaoFichaRecebimentoDetailSerializer,
    QuestaoFichaRecebimentoSerializer,
    QuestoesPorProdutoDetalheSerializer,
    VeiculoFichaDeRecebimentoSerializer,
)
from sme_sigpae_api.recebimento.models import QuestaoFichaRecebimento

pytestmark = pytest.mark.django_db


def test_questoes_por_produto_detalhe_serializer(questoes_por_produto):
    serializer = QuestoesPorProdutoDetalheSerializer(instance=questoes_por_produto)
    data = serializer.data

    assert "questoes_primarias" in data
    assert isinstance(data["questoes_primarias"], list)
    assert len(data["questoes_primarias"]) == 1
    assert "uuid" in data["questoes_primarias"][0]
    assert isinstance(data["questoes_primarias"][0]["uuid"], str)
    assert "questao" in data["questoes_primarias"][0]
    assert isinstance(data["questoes_primarias"][0]["questao"], str)

    assert "questoes_secundarias" in data
    assert isinstance(data["questoes_secundarias"], list)
    assert len(data["questoes_secundarias"]) == 1
    assert "uuid" in data["questoes_secundarias"][0]
    assert isinstance(data["questoes_secundarias"][0]["uuid"], str)
    assert "questao" in data["questoes_secundarias"][0]
    assert isinstance(data["questoes_secundarias"][0]["questao"], str)


def test_questao_ficha_recebimentos_serializer(questao_ficha_recebimento):
    serializer = QuestaoFichaRecebimentoSerializer(instance=questao_ficha_recebimento)
    data = serializer.data

    assert "id" not in data
    assert "uuid" in data
    assert isinstance(data["uuid"], str)
    assert "criado_em" in data
    assert isinstance(data["criado_em"], str)
    assert "alterado_em" in data
    assert isinstance(data["alterado_em"], str)
    assert "ficha_recebimento" in data
    assert isinstance(data["ficha_recebimento"], int)
    assert "questao_conferencia" in data
    assert isinstance(data["questao_conferencia"], int)
    assert "resposta" in data
    assert isinstance(data["resposta"], bool)
    assert "tipo_questao" in data
    assert isinstance(data["tipo_questao"], str)
    assert data["tipo_questao"] in [
        QuestaoFichaRecebimento.TIPO_QUESTAO_PRIMARIA,
        QuestaoFichaRecebimento.TIPO_QUESTAO_SECUNDARIA,
    ]


def test_veiculo_ficha_recebimento_serializer(veiculo_ficha_recebimento):
    serializer = VeiculoFichaDeRecebimentoSerializer(instance=veiculo_ficha_recebimento)
    data = serializer.data

    assert "id" not in data
    assert "ficha_recebimento" not in data
    assert "numero" in data
    assert data["numero"] == "Veículo 001"
    assert "temperatura_recebimento" in data
    assert "temperatura_produto" in data
    assert "placa" in data
    assert "lacre" in data
    assert "numero_sif_sisbi_sisp" in data
    assert "numero_nota_fiscal" in data
    assert "quantidade_nota_fiscal" in data
    assert "embalagens_nota_fiscal" in data
    assert "quantidade_recebida" in data
    assert "embalagens_recebidas" in data
    assert "estado_higienico_adequado" in data

    assert data["numero"] == "Veículo 001"
    assert data["temperatura_recebimento"] == "25"
    assert data["temperatura_produto"] == "24"
    assert data["placa"] == "ABC1234"
    assert data["lacre"] == "LCR123456"
    assert data["numero_sif_sisbi_sisp"] == "123"
    assert data["numero_nota_fiscal"] == "NF123"
    assert data["quantidade_nota_fiscal"] == "10"
    assert data["embalagens_nota_fiscal"] == "5"
    assert data["quantidade_recebida"] == "10"
    assert data["embalagens_recebidas"] == "5"
    assert data["estado_higienico_adequado"] == True
    assert data["termografo"] == False


def test_questao_ficha_recebimento_detail_serializer(questao_ficha_recebimento):
    serializer = QuestaoFichaRecebimentoDetailSerializer(
        instance=questao_ficha_recebimento
    )
    data = serializer.data

    assert "id" not in data
    assert "ficha_recebimento" not in data
    assert "uuid" in data
    assert "questao_conferencia" in data
    assert isinstance(data["questao_conferencia"], dict)
    assert "uuid" in data["questao_conferencia"]
    assert "questao" in data["questao_conferencia"]
    assert "resposta" in data
    assert "tipo_questao" in data


def test_ocorrencia_ficha_recebimento_serializer(ocorrencia_ficha_recebimento):
    serializer = OcorrenciaFichaRecebimentoSerializer(
        instance=ocorrencia_ficha_recebimento
    )
    data = serializer.data

    assert "id" not in data
    assert "ficha_recebimento" not in data
    assert "uuid" in data
    assert "tipo" in data
    assert "relacao" in data
    assert "numero_nota" in data
    assert "quantidade" in data
    assert "descricao" in data
    assert "criado_em" in data
    assert "alterado_em" in data


def test_arquivo_ficha_recebimento_serializer(arquivo_ficha_recebimento):
    serializer = ArquivoFichaRecebimentoSerializer(instance=arquivo_ficha_recebimento)
    data = serializer.data

    assert "id" not in data
    assert "ficha_recebimento" not in data
    assert "nome" in data
    assert data["nome"] == "Arquivo Teste"
    assert "arquivo" in data


def test_dados_cronograma_serializer(ficha_recebimento):
    serializer = DadosCronogramaSerializer(instance=ficha_recebimento.etapa)
    data = serializer.data

    assert "uuid" in data
    assert "numero" in data
    assert "embalagem_primaria" in data
    assert "embalagem_secundaria" in data
    assert "peso_liquido_embalagem_primaria" in data
    assert "peso_liquido_embalagem_secundaria" in data
    assert "sistema_vedacao_embalagem_secundaria" in data


def test_ficha_recebimento_detalhar_serializer(ficha_recebimento):
    serializer = FichaDeRecebimentoDetalharSerializer(instance=ficha_recebimento)
    data = serializer.data

    assert "uuid" in data
    assert "status" in data
    assert "data_recebimento" in data
    assert "data_entrega" in data

    assert "etapa" in data
    assert isinstance(data["etapa"], dict)

    assert "dados_cronograma" in data
    assert isinstance(data["dados_cronograma"], dict)

    assert "veiculos" in data
    assert isinstance(data["veiculos"], list)

    assert "questoes" in data
    assert isinstance(data["questoes"], list)

    assert "ocorrencias" in data
    assert isinstance(data["ocorrencias"], list)

    assert "arquivos" in data
    assert isinstance(data["arquivos"], list)

    assert "documentos_recebimento" in data
    assert isinstance(data["documentos_recebimento"], list)

    assert "lote_fabricante_de_acordo" in data
    assert "numero_lote_armazenagem" in data
    assert "numero_paletes" in data
    assert "observacao" in data
    assert "observacoes_conferencia" in data

    assert "numero_paletes" in data
    assert isinstance(data["numero_paletes"], int)

    assert "peso_embalagem_primaria_1" in data
    assert isinstance(data["peso_embalagem_primaria_1"], float)

    assert "peso_embalagem_primaria_2" in data
    assert isinstance(data["peso_embalagem_primaria_2"], float)

    assert "peso_embalagem_primaria_3" in data
    assert isinstance(data["peso_embalagem_primaria_3"], float)

    assert "peso_embalagem_primaria_4" in data
    assert isinstance(data["peso_embalagem_primaria_4"], float)
