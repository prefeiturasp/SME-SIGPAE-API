import pytest
from django.conf import settings
from django.utils import timezone
from freezegun import freeze_time
from model_bakery import baker

from sme_sigpae_api.pre_recebimento.base.api.serializers.serializer_create import (
    UnidadeMedidaCreateSerializer,
)
from sme_sigpae_api.pre_recebimento.base.api.serializers.serializers import (
    UnidadeMedidaSerialzer,
)
from sme_sigpae_api.pre_recebimento.base.models import UnidadeMedida
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.serializers.serializer_create import (
    CronogramaCreateSerializer,
    novo_numero_solicitacao,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.serializers.serializers import (
    CronogramaFichaDeRecebimentoSerializer,
    CronogramaRelatorioSerializer,
    CronogramaSimplesSerializer,
    EtapasDoCronogramaCalendarioSerializer,
    EtapasDoCronogramaFichaDeRecebimentoSerializer,
    EtapasDoCronogramaSerializer,
    InterrupcaoProgramadaEntregaCreateSerializer,
    InterrupcaoProgramadaEntregaSerializer,
    PainelCronogramaSerializer,
    SolicitacaoAlteracaoCronogramaSerializer,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import (
    Cronograma,
    InterrupcaoProgramadaEntrega,
)
from sme_sigpae_api.pre_recebimento.documento_recebimento.api.serializers.serializers import (
    DocRecebimentoDetalharSerializer,
    DocumentoDeRecebimentoSerializer,
    PainelDocumentoDeRecebimentoSerializer,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.serializers.serializers import (
    PainelFichaTecnicaSerializer,
)
from sme_sigpae_api.pre_recebimento.layout_embalagem.api.serializers.serializers import (
    PainelLayoutEmbalagemSerializer,
)

pytestmark = pytest.mark.django_db


def test_etapas_cronograma_serializer(etapa):
    serializer = EtapasDoCronogramaSerializer(etapa)
    assert serializer.data["data_programada"] is None

    etapa.data_programada = timezone.now().date()
    etapa.save()
    serializer = EtapasDoCronogramaSerializer(etapa)
    assert serializer.data["data_programada"] == etapa.data_programada.strftime(
        "%d/%m/%Y"
    )


def test_unidade_medida_serializer(unidade_medida_logistica):
    """Deve serializar corretamente a instância de Unidade de Medida."""
    serializer = UnidadeMedidaSerialzer(unidade_medida_logistica)

    drf_date_format = settings.REST_FRAMEWORK["DATETIME_FORMAT"]

    assert serializer.data["uuid"] == str(unidade_medida_logistica.uuid)
    assert serializer.data["nome"] == str(unidade_medida_logistica.nome)
    assert serializer.data["abreviacao"] == str(unidade_medida_logistica.abreviacao)
    assert serializer.data["criado_em"] == unidade_medida_logistica.criado_em.strftime(
        drf_date_format
    )


def test_unidade_medida_create_serializer_creation():
    """Deve criar corretamente uma instância de Unidade de Medida."""
    data = {"nome": "UNIDADE MEDIDA", "abreviacao": "um"}

    serializer = UnidadeMedidaCreateSerializer(data=data)
    qtd_unidades_medida_antes = UnidadeMedida.objects.count()

    assert serializer.is_valid() is True
    assert serializer.validated_data["nome"] == data["nome"]
    assert serializer.validated_data["abreviacao"] == data["abreviacao"]

    instance = serializer.save()

    assert UnidadeMedida.objects.count() == qtd_unidades_medida_antes + 1
    assert instance.uuid is not None
    assert instance.criado_em is not None


def test_unidade_medida_create_serializer_updating(unidade_medida_logistica):
    """Deve criar corretamente uma instância de Unidade de Medida."""
    data = {"nome": "UNIDADE MEDIDA ATUALIZADA", "abreviacao": "uma"}

    serializer = UnidadeMedidaCreateSerializer(
        data=data, instance=unidade_medida_logistica
    )

    assert serializer.is_valid() is True
    assert serializer.validated_data["nome"] == data["nome"]
    assert serializer.validated_data["abreviacao"] == data["abreviacao"]


def test_painel_cronograma_serializer(cronograma, cronogramas_multiplos_status_com_log):
    cronograma_completo = Cronograma.objects.filter(numero="002/2023A").first()
    cronograma_completo.ficha_tecnica.programa = "LEVE_LEITE"
    serializer = PainelCronogramaSerializer(cronograma_completo)

    assert cronograma_completo.empresa is not None
    assert serializer.data["empresa"] == str(cronograma_completo.empresa.nome_fantasia)
    assert cronograma_completo.ficha_tecnica.produto is not None
    assert serializer.data["produto"] == str(
        cronograma_completo.ficha_tecnica.produto.nome
    )
    assert cronograma_completo.log_mais_recente is not None
    assert serializer.data["log_mais_recente"].split(" ")[
        0
    ] == cronograma_completo.criado_em.strftime("%d/%m/%Y")

    assert serializer.data["programa_leve_leite"] == True

    cronograma_incompleto = cronograma
    serializer = PainelCronogramaSerializer(cronograma_incompleto)

    assert cronograma_incompleto.empresa is None
    assert cronograma_incompleto.ficha_tecnica is None
    assert cronograma_incompleto.log_mais_recente is None
    assert serializer.data[
        "log_mais_recente"
    ] == cronograma_incompleto.criado_em.strftime("%d/%m/%Y")

    assert "programa_leve_leite" in serializer.data
    assert serializer.data["programa_leve_leite"] is None


@freeze_time((timezone.now() + timezone.timedelta(2)))
def test_painel_cronograma_serializer_log_recente(cronogramas_multiplos_status_com_log):
    cronograma_completo = Cronograma.objects.filter(numero="002/2023A").first()
    serializer = PainelCronogramaSerializer(cronograma_completo)

    expected_date = (timezone.now() - timezone.timedelta(2)).strftime("%d/%m/%Y")
    assert serializer.data["log_mais_recente"] == expected_date


def test_gera_proximo_numero_cronograma_sem_ultimo_cronograma():
    numero = CronogramaCreateSerializer().gera_proximo_numero_cronograma()
    assert numero == f"001/{timezone.now().year}A"


def test_gera_proximo_numero_cronograma_com_ultimo_cronograma(cronograma):
    numero = CronogramaCreateSerializer().gera_proximo_numero_cronograma()

    ultimo_ano = int(cronograma.numero.split("/")[1][:4])
    ano_atual = timezone.now().year

    if ultimo_ano != ano_atual:
        assert numero == f"001/{ano_atual}A"
    else:
        ultimo_numero = int(cronograma.numero[:3])
        proximo_numero = str(ultimo_numero + 1).zfill(3)
        assert numero == f"{proximo_numero}/{ano_atual}A"


def test_novo_numero_solicitacao(solicitacao_cronograma_em_analise):
    solicitacao = solicitacao_cronograma_em_analise

    solicitacao.numero_solicitacao = ""
    solicitacao.save()

    novo_numero_solicitacao(solicitacao)
    assert solicitacao.numero_solicitacao == f"{str(solicitacao.pk).zfill(8)}-ALT"


def test_etapas_do_cronograma_calendario_serializer(
    etapa_com_quantidade_e_data,
    cronograma_assinado_perfil_dilog,
    unidade_medida_logistica,
):
    cronograma = cronograma_assinado_perfil_dilog
    etapa = etapa_com_quantidade_e_data
    cronograma.unidade_medida = unidade_medida_logistica
    etapa.cronograma = cronograma
    etapa.save()

    serializer = EtapasDoCronogramaCalendarioSerializer(etapa)

    assert serializer.data["uuid"] == str(etapa.uuid)
    assert serializer.data["nome_produto"] == cronograma.ficha_tecnica.produto.nome
    assert serializer.data["numero_cronograma"] == cronograma.numero
    assert serializer.data["nome_fornecedor"] == cronograma.empresa.nome_fantasia
    assert serializer.data["data_programada"] == etapa.data_programada.strftime(
        "%d/%m/%Y"
    )
    assert serializer.data["numero_empenho"] == etapa.numero_empenho
    assert serializer.data["etapa"] == f"Etapa {etapa.etapa}"
    assert serializer.data["parte"] == f"Parte {etapa.parte}"
    assert serializer.data["quantidade"] == etapa.quantidade
    assert serializer.data["status"] == cronograma.get_status_display()
    assert serializer.data["unidade_medida"] == cronograma.unidade_medida.abreviacao
    assert serializer.data["programa_leve_leite"] is not None


def test_doc_recebimento_serializer_pregao_chamada_publica(cronograma_chamada_publica):
    doc_recebimento = baker.make(
        "DocumentoDeRecebimento", cronograma=cronograma_chamada_publica
    )

    serializer = DocRecebimentoDetalharSerializer(doc_recebimento)

    print(cronograma_chamada_publica.contrato.numero_chamada_publica)
    print(serializer.data["pregao_chamada_publica"])

    assert (
        serializer.data["pregao_chamada_publica"]
        == cronograma_chamada_publica.contrato.numero_chamada_publica
    )
    assert serializer.data["pregao_chamada_publica"] == "CP-2022-01"


def test_doc_recebimento_serializer_pregao_eletronico(cronograma_recebido):
    doc_recebimento = baker.make(
        "DocumentoDeRecebimento", cronograma=cronograma_recebido
    )

    serializer = DocRecebimentoDetalharSerializer(doc_recebimento)

    assert (
        serializer.data["pregao_chamada_publica"]
        == cronograma_recebido.contrato.numero_pregao
    )
    assert serializer.data["pregao_chamada_publica"] == "123456789"


def test_doc_recebimento_serializer_qualquer_modalidade(cronograma_qualquer):
    doc_recebimento = baker.make(
        "DocumentoDeRecebimento", cronograma=cronograma_qualquer
    )

    serializer = DocRecebimentoDetalharSerializer(doc_recebimento)

    assert (
        serializer.data["pregao_chamada_publica"]
        == cronograma_qualquer.contrato.numero_chamada_publica
    )
    assert serializer.data["pregao_chamada_publica"] == "CP-2022-02"


def test_cronograma_ficha_recebimento_serializer():
    ficha_tecnica = baker.make(
        "FichaTecnicaDoProduto",
        material_embalagem_primaria="Vidro temperado",
        sistema_vedacao_embalagem_secundaria="Lacre termossoldado",
    )
    ficha_tecnica.programa = "LEVE_LEITE"
    cronograma = baker.make("Cronograma", ficha_tecnica=ficha_tecnica)

    serializer = CronogramaFichaDeRecebimentoSerializer(cronograma)

    assert serializer.data["programa_leve_leite"] is True


def test_cronograma_ficha_recebimento_serializer_embalagens():
    ficha_tecnica = baker.make(
        "FichaTecnicaDoProduto",
        material_embalagem_primaria="Vidro temperado",
        sistema_vedacao_embalagem_secundaria="Lacre termossoldado",
    )
    cronograma = baker.make("Cronograma", ficha_tecnica=ficha_tecnica)

    serializer = CronogramaFichaDeRecebimentoSerializer(cronograma)

    assert serializer.data["embalagem_primaria"] == "Vidro temperado"
    assert serializer.data["embalagem_secundaria"] == "Lacre termossoldado"


def test_cronograma_ficha_recebimento_serializer_embalagens_sem_ficha_tecnica():
    cronograma = baker.make("Cronograma", ficha_tecnica=None)

    serializer = CronogramaFichaDeRecebimentoSerializer(cronograma)

    assert serializer.data["embalagem_primaria"] is None
    assert serializer.data["embalagem_secundaria"] is None


def test_etapas_cronograma_ficha_recebimento_serializer(etapa_com_fichas_recebimento):
    etapa = etapa_com_fichas_recebimento
    serializer = EtapasDoCronogramaFichaDeRecebimentoSerializer(etapa)
    data = serializer.data

    assert data["uuid"] == str(etapa.uuid)
    assert data["numero_empenho"] == "EMP001"
    assert data["etapa"] == "Etapa 1"
    assert data["parte"] == "Parte 2"
    assert data["data_programada"] == etapa.data_programada.strftime("%d/%m/%Y")
    assert data["unidade_medida"] == etapa.cronograma.unidade_medida.abreviacao
    assert data["unidade_medida"] == etapa.cronograma.unidade_medida.abreviacao

    assert "500" in data["qtd_total_empenho"]
    assert "ut" in data["qtd_total_empenho"]
    assert "300" in data["quantidade"]
    assert "ut" in data["quantidade"]
    assert "10" in data["total_embalagens"]
    assert "CX" in data["total_embalagens"]

    assert data["houve_ocorrencia"] is True
    assert data["houve_reposicao"] is True

    fichas = data["fichas_recebimento"]
    assert len(fichas) == 3

    for ficha in fichas:
        assert "uuid" in ficha
        assert "houve_ocorrencia" in ficha
        assert "houve_reposicao" in ficha
        assert "situacao" in ficha
        assert ficha["situacao"] in ["Ocorrência", "Recebido"]

    fichas_com_ocorrencia = [f for f in fichas if f["houve_ocorrencia"]]
    assert len(fichas_com_ocorrencia) == 1
    assert fichas_com_ocorrencia[0]["situacao"] == "Ocorrência"

    fichas_sem_ocorrencia = [f for f in fichas if not f["houve_ocorrencia"]]
    assert len(fichas_sem_ocorrencia) == 2
    for ficha in fichas_sem_ocorrencia:
        assert ficha["situacao"] == "Recebido"


def test_etapas_cronograma_ficha_recebimento_serializer_sem_fichas(
    etapa_sem_fichas_recebimento,
):
    etapa = etapa_sem_fichas_recebimento
    serializer = EtapasDoCronogramaFichaDeRecebimentoSerializer(etapa)
    data = serializer.data

    assert data["etapa"] is None
    assert data["parte"] is None

    assert data["desvinculada_recebimento"] is True
    assert data["houve_ocorrencia"] is False
    assert data["houve_reposicao"] is False
    assert data["fichas_recebimento"] == []


def test_painel_documento_recebimento_serializer(documento_recebimento_leve_leite):
    """Testa se o PainelDocumentoDeRecebimentoSerializer retorna programa_leve_leite=True."""
    serializer = PainelDocumentoDeRecebimentoSerializer(
        documento_recebimento_leve_leite
    )
    data = serializer.data

    assert "programa_leve_leite" in data
    assert data["programa_leve_leite"] is True

    assert "numero_cronograma" in data
    assert (
        data["numero_cronograma"] == documento_recebimento_leve_leite.cronograma.numero
    )

    assert "nome_produto" in data
    if documento_recebimento_leve_leite.cronograma.ficha_tecnica:
        assert (
            data["nome_produto"]
            == documento_recebimento_leve_leite.cronograma.ficha_tecnica.produto.nome
        )

    assert "nome_empresa" in data
    if documento_recebimento_leve_leite.cronograma.empresa:
        assert (
            data["nome_empresa"]
            == documento_recebimento_leve_leite.cronograma.empresa.nome_fantasia
        )

    assert "status" in data
    assert data["status"] == documento_recebimento_leve_leite.get_status_display()

    assert "log_mais_recente" in data


def test_painel_ficha_tecnica_serializer(ficha_tecnica_leve_leite):
    serializer = PainelFichaTecnicaSerializer(ficha_tecnica_leve_leite)
    data = serializer.data

    assert "programa_leve_leite" in data
    assert data["programa_leve_leite"] is True

    assert "uuid" in data
    assert data["uuid"] == str(ficha_tecnica_leve_leite.uuid)

    assert "numero_ficha" in data
    assert data["numero_ficha"] == ficha_tecnica_leve_leite.numero

    assert "nome_produto" in data
    assert data["nome_produto"] == ficha_tecnica_leve_leite.produto.nome

    assert "nome_empresa" in data
    assert data["nome_empresa"] == ficha_tecnica_leve_leite.empresa.nome_fantasia

    assert "status" in data
    assert data["status"] == ficha_tecnica_leve_leite.get_status_display()

    assert "log_mais_recente" in data
    log_recente = data["log_mais_recente"]
    assert isinstance(log_recente, str)


def test_painel_ficha_tecnica_serializer_alimentacao_escolar(ficha_tecnica_leve_leite):
    nova_ficha = ficha_tecnica_leve_leite
    nova_ficha.programa = "ALIMENTACAO_ESCOLAR"
    nova_ficha.save()
    serializer = PainelFichaTecnicaSerializer(nova_ficha)
    data = serializer.data

    assert "programa_leve_leite" in data
    assert data["programa_leve_leite"] is False


def test_painel_layout_embalagem_serializer(layout_embalagem_leve_leite):
    serializer = PainelLayoutEmbalagemSerializer(layout_embalagem_leve_leite)
    data = serializer.data

    assert "programa_leve_leite" in data
    assert data["programa_leve_leite"] is True

    assert "uuid" in data
    assert data["uuid"] == str(layout_embalagem_leve_leite.uuid)

    assert "numero_ficha_tecnica" in data
    assert (
        data["numero_ficha_tecnica"] == layout_embalagem_leve_leite.ficha_tecnica.numero
    )

    assert "nome_produto" in data
    assert (
        data["nome_produto"] == layout_embalagem_leve_leite.ficha_tecnica.produto.nome
    )

    assert "nome_empresa" in data
    assert (
        data["nome_empresa"]
        == layout_embalagem_leve_leite.ficha_tecnica.empresa.nome_fantasia
    )

    assert "status" in data
    assert data["status"] == layout_embalagem_leve_leite.get_status_display()

    assert "log_mais_recente" in data
    log_recente = data["log_mais_recente"]
    assert isinstance(log_recente, str)


def test_ficha_tecnica_listagem_serializer_campo_programa(ficha_tecnica_factory):
    """Testa que o campo programa é serializado corretamente no FichaTecnicaListagemSerializer."""
    from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.serializers.serializers import (
        FichaTecnicaListagemSerializer,
    )
    from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import (
        FichaTecnicaDoProduto,
    )

    ficha = ficha_tecnica_factory(programa=FichaTecnicaDoProduto.LEVE_LEITE)
    serializer = FichaTecnicaListagemSerializer(ficha)

    assert "programa" in serializer.data
    assert serializer.data["programa"] == FichaTecnicaDoProduto.LEVE_LEITE


def test_ficha_tecnica_detalhar_serializer_campo_programa(ficha_tecnica_factory):
    """Testa que os campos programa e programa_display estão presentes no FichaTecnicaDetalharSerializer."""
    from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.serializers.serializers import (
        FichaTecnicaDetalharSerializer,
    )
    from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import (
        FichaTecnicaDoProduto,
    )

    ficha = ficha_tecnica_factory(programa=FichaTecnicaDoProduto.LEVE_LEITE)
    serializer = FichaTecnicaDetalharSerializer(ficha)

    assert "programa" in serializer.data
    assert "programa_display" in serializer.data
    assert serializer.data["programa"] == FichaTecnicaDoProduto.LEVE_LEITE
    assert serializer.data["programa_display"] == "Leve Leite"


def test_documento_recebimento_serializer(documento_recebimento_leve_leite):
    """Testa se o DocumentoDeRecebimentoSerializer retorna todos os campos corretamente."""
    doc = documento_recebimento_leve_leite
    serializer = DocumentoDeRecebimentoSerializer(doc)
    data = serializer.data

    assert data["uuid"] == str(doc.uuid)
    assert data["numero_cronograma"] == doc.cronograma.numero
    assert data["numero_laudo"] == doc.numero_laudo
    assert (
        data["pregao_chamada_publica"] == doc.cronograma.contrato.pregao_chamada_publica
    )
    assert data["nome_produto"] == doc.cronograma.ficha_tecnica.produto.nome
    assert data["programa_leve_leite"] is True
    assert data["status"] == doc.get_status_display()
    assert data["criado_em"] == doc.criado_em.strftime("%d/%m/%Y")

    # Teste com programa diferente
    doc.cronograma.ficha_tecnica.programa = "ALIMENTACAO_ESCOLAR"
    doc.cronograma.ficha_tecnica.save()
    serializer = DocumentoDeRecebimentoSerializer(doc)
    assert serializer.data["programa_leve_leite"] is False


def test_cronograma_simples_serializer(cronograma, contrato):
    """Testa se o CronogramaSimplesSerializer retorna todos os campos corretamente."""
    from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import (
        FichaTecnicaDoProduto,
    )

    ficha = baker.make(
        "FichaTecnicaDoProduto", programa=FichaTecnicaDoProduto.LEVE_LEITE
    )
    cronograma.ficha_tecnica = ficha
    cronograma.contrato = contrato
    cronograma.save()

    serializer = CronogramaSimplesSerializer(cronograma)
    data = serializer.data

    assert data["uuid"] == str(cronograma.uuid)
    assert data["numero"] == cronograma.numero
    assert data["pregao_chamada_publica"] == contrato.pregao_chamada_publica
    assert data["nome_produto"] == ficha.produto.nome
    assert data["programa_leve_leite"] is True

    # Teste com programa diferente
    ficha.programa = "ALIMENTACAO_ESCOLAR"
    ficha.save()
    serializer = CronogramaSimplesSerializer(cronograma)
    assert serializer.data["programa_leve_leite"] is False


def test_solicitacao_alteracao_cronograma_serializer_leve_leite(
    cronograma_leve_leite, cronograma_assinado_perfil_dilog
):
    solicitacao = baker.make(
        "SolicitacaoAlteracaoCronograma",
        cronograma=cronograma_leve_leite,
        status="EM_ANALISE",
    )

    serializer = SolicitacaoAlteracaoCronogramaSerializer(solicitacao)
    data = serializer.data

    assert "programa_leve_leite" in data
    assert data["programa_leve_leite"] is True

    assert "uuid" in data
    assert data["uuid"] == str(solicitacao.uuid)

    assert "numero_solicitacao" in data

    assert "fornecedor" in data
    assert data["fornecedor"] == str(cronograma_leve_leite.empresa)

    assert "cronograma" in data
    assert data["cronograma"] == cronograma_leve_leite.numero

    assert "status" in data
    assert data["status"] == solicitacao.get_status_display()

    assert "criado_em" in data

    if cronograma_assinado_perfil_dilog.ficha_tecnica:
        cronograma_assinado_perfil_dilog.ficha_tecnica.programa = "ALIMENTACAO_ESCOLAR"
        cronograma_assinado_perfil_dilog.ficha_tecnica.save()

    solicitacao2 = baker.make(
        "SolicitacaoAlteracaoCronograma",
        cronograma=cronograma_assinado_perfil_dilog,
        status="EM_ANALISE",
    )

    serializer2 = SolicitacaoAlteracaoCronogramaSerializer(solicitacao2)
    data2 = serializer2.data

    assert "programa_leve_leite" in data2
    assert data2["programa_leve_leite"] is False


def test_interrupcao_programada_entrega_serializer(interrupcao_programada_entrega):
    serializer = InterrupcaoProgramadaEntregaSerializer(interrupcao_programada_entrega)
    data = serializer.data

    assert data["uuid"] == str(interrupcao_programada_entrega.uuid)
    assert data["data"] == interrupcao_programada_entrega.data.strftime("%d/%m/%Y")
    assert data["motivo"] == interrupcao_programada_entrega.motivo
    assert data["motivo_display"] == interrupcao_programada_entrega.get_motivo_display()
    assert data["tipo_calendario"] == interrupcao_programada_entrega.tipo_calendario
    assert (
        data["tipo_calendario_display"]
        == interrupcao_programada_entrega.get_tipo_calendario_display()
    )
    assert data["descricao_motivo"] == interrupcao_programada_entrega.descricao_motivo


def test_interrupcao_programada_entrega_create_serializer_validacao_outros():
    """Teste para verificar a validação quando o motivo é OUTROS e não há descrição"""
    data = {
        "data": timezone.now().date(),
        "motivo": InterrupcaoProgramadaEntrega.MOTIVO_OUTROS,
        "descricao_motivo": "",  # Descrição vazia deve falhar
        "tipo_calendario": InterrupcaoProgramadaEntrega.TIPO_CALENDARIO_ARMAZENAVEL,
    }
    serializer = InterrupcaoProgramadaEntregaCreateSerializer(data=data)
    assert not serializer.is_valid()
    assert "descricao_motivo" in serializer.errors


def test_interrupcao_programada_entrega_create_serializer_sucesso():
    """Teste de criação com sucesso"""
    data = {
        "data": timezone.now().date(),
        "motivo": InterrupcaoProgramadaEntrega.MOTIVO_REUNIAO,
        "descricao_motivo": "",
        "tipo_calendario": InterrupcaoProgramadaEntrega.TIPO_CALENDARIO_PONTO_A_PONTO,
    }
    serializer = InterrupcaoProgramadaEntregaCreateSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()
    assert instance.motivo == InterrupcaoProgramadaEntrega.MOTIVO_REUNIAO


def test_cronograma_relatorio_serializer(cronograma_assinado_perfil_dilog):
    """Testa se o CronogramaRelatorioSerializer retorna todos os campos corretamente."""
    cronograma = cronograma_assinado_perfil_dilog
    serializer = CronogramaRelatorioSerializer(cronograma)
    data = serializer.data

    assert "uuid" in data
    assert "numero" in data
    assert "status" in data
    assert "qtd_total_programada" in data
    assert "etapas" in data
    assert "programa_leve_leite" in data

    assert "numero_contrato" in data
    assert "numero_processo" in data
    assert "produto" in data
    assert "empresa" in data
    assert "armazem" in data
    assert "marca" in data
    assert "custo_unitario_produto" in data

    assert data["uuid"] == str(cronograma.uuid)
    assert data["numero"] == cronograma.numero
    assert data["numero_contrato"] == cronograma.contrato.numero
    assert data["numero_processo"] == cronograma.contrato.processo
    assert data["produto"] == cronograma.ficha_tecnica.produto.nome
    assert data["empresa"] == cronograma.empresa.nome_fantasia
    assert data["armazem"] == cronograma.armazem.nome_fantasia
    assert data["marca"] == cronograma.ficha_tecnica.marca.nome
    assert isinstance(data["etapas"], list)
