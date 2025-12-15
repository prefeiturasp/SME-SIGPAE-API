import datetime
import json
from unittest.mock import Mock, patch

import pytest
from dateutil.relativedelta import relativedelta
from django.http import QueryDict
from django.test import TestCase
from freezegun import freeze_time
from model_bakery import baker
from pypdf import PdfWriter

from sme_sigpae_api.dados_comuns.models import CentralDeDownload, LogSolicitacoesUsuario
from sme_sigpae_api.escola.models import (
    AlunoPeriodoParcial,
    Escola,
    GrupoUnidadeEscolar,
    Lote,
)
from sme_sigpae_api.medicao_inicial.models import Responsavel, SolicitacaoMedicaoInicial
from sme_sigpae_api.medicao_inicial.services.relatorio_adesao import obtem_resultados
from sme_sigpae_api.medicao_inicial.tasks import (
    buscar_solicitacao_mes_anterior,
    copiar_alunos_periodo_parcial,
    copiar_responsaveis,
    cria_solicitacao_medicao_inicial_mes_atual,
    criar_nova_solicitacao,
    exporta_relatorio_adesao_para_pdf,
    exporta_relatorio_adesao_para_xlsx,
    exporta_relatorio_consolidado_xlsx,
    exporta_relatorio_controle_frequencia_para_pdf,
    gera_pdf_relatorio_solicitacao_medicao_por_escola_async,
    gera_pdf_relatorio_unificado_async,
    processa_relatorio_lançamentos,
    solicitacao_medicao_atual_existe,
)
from sme_sigpae_api.perfil.models.usuario import Usuario
from sme_sigpae_api.terceirizada.models import Terceirizada


class CriaSolicitacaoMedicaoInicialMesAtualTest(TestCase):
    @patch("sme_sigpae_api.medicao_inicial.tasks.Escola.objects.all")
    @patch(
        "sme_sigpae_api.medicao_inicial.tasks.SolicitacaoMedicaoInicial.objects.filter"
    )
    @patch("sme_sigpae_api.medicao_inicial.tasks.SolicitacaoMedicaoInicial.objects.get")
    @patch(
        "sme_sigpae_api.medicao_inicial.tasks.SolicitacaoMedicaoInicial.objects.create"
    )
    @patch("sme_sigpae_api.medicao_inicial.tasks.logger.info")
    def test_cria_solicitacao_medicao_inicial_mes_atual(
        self, mock_logger_info, mock_create, mock_get, mock_filter, mock_all
    ):
        data_hoje = datetime.date.today()
        data_mes_anterior = data_hoje + relativedelta(months=-1)
        escola_nome_mock = "escola1"
        mock_all.return_value = [Mock(nome=escola_nome_mock)]
        mock_filter.return_value.exists.return_value = False
        mock_get.side_effect = SolicitacaoMedicaoInicial.DoesNotExist

        cria_solicitacao_medicao_inicial_mes_atual()

        message = (
            f"x-x-x-x Não existe Solicitação de Medição Inicial para a escola {escola_nome_mock} no "
            f"mês anterior ({data_mes_anterior.month:02d}/{data_mes_anterior.year}) x-x-x-x"
        )
        mock_logger_info.assert_called_with(message)


class GeraPDFRelatorioSolicitacaoMedicaoPorEscolaAsyncTest(TestCase):
    @patch("sme_sigpae_api.medicao_inicial.tasks.gera_objeto_na_central_download")
    @patch("sme_sigpae_api.medicao_inicial.tasks.atualiza_central_download")
    @patch(
        "sme_sigpae_api.relatorios.relatorios.relatorio_solicitacao_medicao_por_escola"
    )
    @patch("sme_sigpae_api.medicao_inicial.tasks.SolicitacaoMedicaoInicial.objects.get")
    @patch("sme_sigpae_api.medicao_inicial.tasks.logger.info")
    def test_gera_pdf_relatorio_solicitacao_medicao_por_escola_async(
        self,
        mock_logger_info,
        mock_get,
        mock_relatorio,
        mock_atualiza,
        mock_gera_objeto,
    ):
        mock_gera_objeto.return_value = Mock()
        mock_relatorio.return_value = "arquivo_mock"
        uuid_mock = "123456-abcd-7890"

        gera_pdf_relatorio_solicitacao_medicao_por_escola_async(
            "user", "nome_arquivo", uuid_mock
        )


class GeraPDFRelatorioUnificadoMedicoesIniciaisAsyncTest(TestCase):
    @patch("sme_sigpae_api.medicao_inicial.tasks.gera_objeto_na_central_download")
    @patch("sme_sigpae_api.medicao_inicial.tasks.atualiza_central_download")
    @patch(
        "sme_sigpae_api.relatorios.relatorios.relatorio_consolidado_medicoes_iniciais_emef"
    )
    @patch(
        "sme_sigpae_api.relatorios.relatorios.relatorio_solicitacao_medicao_por_escola"
    )
    @patch("sme_sigpae_api.medicao_inicial.tasks.SolicitacaoMedicaoInicial.objects.get")
    @patch("sme_sigpae_api.medicao_inicial.tasks.logger.info")
    def test_gera_pdf_relatorio_unificado_async(
        self,
        mock_logger_info,
        mock_get,
        mock_relatorio_somatorio,
        mock_relatorio_lançamentos,
        mock_atualiza,
        mock_gera_objeto,
    ):
        mock_gera_objeto.return_value = Mock()
        mock_relatorio_lançamentos.return_value = "arquivo_mock"
        uuid_mock = "123456-abcd-7890"
        tipos_de_unidade = ["EMEF", "CEUEMEF", "EMEFM", "EMEBS", "CIEJA", "CEU Gestão"]

        gera_pdf_relatorio_unificado_async(
            "user", "nome_arquivo", uuid_mock, tipos_de_unidade
        )


@pytest.fixture
def solicitacao_mes_atual(escola_cei):
    data = datetime.date.today()
    return SolicitacaoMedicaoInicial.objects.create(
        escola=escola_cei, ano=data.year, mes=f"{data.month:02d}"
    )


@pytest.mark.django_db
def test_solicitacao_medicao_atual_existe(escola_cei, solicitacao_mes_atual):
    data = datetime.date.today()

    assert solicitacao_medicao_atual_existe(escola_cei, data) is True
    assert (
        solicitacao_medicao_atual_existe(escola_cei, data + relativedelta(months=-1))
        is False
    )


@pytest.mark.django_db
def test_buscar_solicitacao_mes_anterior(escola_cei):
    data = datetime.date.today() + relativedelta(months=-1)
    SolicitacaoMedicaoInicial.objects.create(
        escola=escola_cei, ano=data.year, mes=f"{data.month:02d}"
    )

    assert buscar_solicitacao_mes_anterior(escola_cei, data) is not None


@pytest.mark.django_db
def test_criar_nova_solicitacao(escola_cei, solicitacao_mes_atual):
    data_hoje = datetime.date.today()

    solicitacao = criar_nova_solicitacao(
        solicitacao_mes_atual, escola_cei, data_hoje + relativedelta(months=1)
    )
    assert solicitacao.escola == escola_cei


@pytest.mark.django_db
def test_copiar_responsaveis(escola_cei):
    solicitacao_origem = SolicitacaoMedicaoInicial.objects.create(
        escola=escola_cei, ano=2020, mes="01"
    )
    Responsavel.objects.create(
        solicitacao_medicao_inicial=solicitacao_origem,
        nome="Responsavel Teste",
        rf="12345",
    )

    solicitacao_destino = SolicitacaoMedicaoInicial.objects.create(
        escola=escola_cei, ano=2020, mes="02"
    )
    copiar_responsaveis(solicitacao_origem, solicitacao_destino)

    assert solicitacao_destino.responsaveis.count() == 1
    assert solicitacao_destino.responsaveis.first().nome == "Responsavel Teste"


@pytest.mark.django_db
def test_copiar_alunos_periodo_parcial(escola_cei, aluno):
    solicitacao_origem = SolicitacaoMedicaoInicial.objects.create(
        escola=escola_cei, ano=2020, mes="01"
    )

    AlunoPeriodoParcial.objects.create(
        solicitacao_medicao_inicial=solicitacao_origem, aluno=aluno, escola=escola_cei
    )

    solicitacao_destino = SolicitacaoMedicaoInicial.objects.create(
        escola=escola_cei, ano=2020, mes="02"
    )
    copiar_alunos_periodo_parcial(solicitacao_origem, solicitacao_destino)

    assert solicitacao_destino.alunos_periodo_parcial.count() == 1
    assert solicitacao_destino.alunos_periodo_parcial.first().aluno == aluno


@pytest.mark.django_db
def test_exporta_relatorio_adesao_para_xlsx(
    usuario,
    categoria_medicao,
    tipo_alimentacao_refeicao,
    make_solicitacao_medicao_inicial,
    make_medicao,
    make_valores_medicao,
    make_periodo_escolar,
):
    # arrange
    mes = "03"
    ano = "2024"
    periodo_lancamento_de = f"01/{mes}/{ano}"
    periodo_lancamento_ate = f"03/{mes}/{ano}"

    solicitacao = make_solicitacao_medicao_inicial(
        mes, ano, "MEDICAO_APROVADA_PELA_CODAE"
    )
    periodo_escolar = make_periodo_escolar("MANHA")
    medicao = make_medicao(solicitacao, periodo_escolar)

    valores = range(1, 6)
    dias = [str(x).rjust(2, "0") for x in range(1, 6)]

    for dia, valor in zip(dias, valores):
        make_valores_medicao(
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=str(valor).rjust(2, "0"),
            tipo_alimentacao=tipo_alimentacao_refeicao,
            dia=dia,
        )
        make_valores_medicao(
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=str(valor).rjust(2, "0"),
            nome_campo="frequencia",
            dia=dia,
        )

    nome_arquivo = "relatorio-adesao.xlsx"

    # act
    query_params = QueryDict(
        f"mes_ano={mes}_{ano}&periodo_lancamento_de={periodo_lancamento_de}&periodo_lancamento_ate={periodo_lancamento_ate}"
    )
    resultados = obtem_resultados(query_params)

    exporta_relatorio_adesao_para_xlsx(
        usuario,
        nome_arquivo,
        resultados,
        {
            "mes_ano": f"{mes}_{ano}",
            "periodo_lancamento_de": periodo_lancamento_de,
            "periodo_lancamento_ate": periodo_lancamento_ate,
        },
    )

    assert CentralDeDownload.objects.count() == 1
    arquivo = CentralDeDownload.objects.first()
    assert arquivo is not None and arquivo.usuario == usuario
    assert arquivo is not None and arquivo.identificador == nome_arquivo
    assert arquivo is not None and arquivo.status == CentralDeDownload.STATUS_CONCLUIDO


@pytest.mark.django_db
def test_exporta_relatorio_adesao_para_xlsx_sem_resultados(usuario):
    # arrange
    mes = "03"
    ano = "2024"

    nome_arquivo = "relatorio-adesao.xlsx"

    # act
    resultados = {}

    exporta_relatorio_adesao_para_xlsx(
        usuario, nome_arquivo, resultados, {"mes_ano": f"{mes}_{ano}"}
    )

    assert CentralDeDownload.objects.count() == 1
    arquivo = CentralDeDownload.objects.first()
    assert arquivo is not None and arquivo.usuario == usuario
    assert arquivo is not None and arquivo.identificador == nome_arquivo
    assert arquivo is not None and arquivo.status == CentralDeDownload.STATUS_CONCLUIDO


@pytest.mark.django_db
def test_exporta_relatorio_adesao_para_pdf(
    usuario,
    categoria_medicao,
    tipo_alimentacao_refeicao,
    make_solicitacao_medicao_inicial,
    make_medicao,
    make_valores_medicao,
    make_periodo_escolar,
):
    # arrange
    mes = "03"
    ano = "2024"
    periodo_lancamento_de = f"01/{mes}/{ano}"
    periodo_lancamento_ate = f"03/{mes}/{ano}"

    solicitacao = make_solicitacao_medicao_inicial(
        mes, ano, "MEDICAO_APROVADA_PELA_CODAE"
    )
    periodo_escolar = make_periodo_escolar("MANHA")
    medicao = make_medicao(solicitacao, periodo_escolar)

    valores = range(1, 6)
    dias = [str(x).rjust(2, "0") for x in range(1, 6)]

    for dia, valor in zip(dias, valores):
        make_valores_medicao(
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=str(valor).rjust(2, "0"),
            tipo_alimentacao=tipo_alimentacao_refeicao,
            dia=dia,
        )
        make_valores_medicao(
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=str(valor).rjust(2, "0"),
            nome_campo="frequencia",
            dia=dia,
        )

    nome_arquivo = "relatorio-adesao.pdf"

    # act
    query_params = query_params = QueryDict(
        f"mes_ano={mes}_{ano}&periodo_lancamento_de={periodo_lancamento_de}&periodo_lancamento_ate={periodo_lancamento_ate}"
    )
    resultados = obtem_resultados(query_params)

    exporta_relatorio_adesao_para_pdf(
        usuario,
        nome_arquivo,
        resultados,
        {
            "mes_ano": f"{mes}_{ano}",
            "periodo_lancamento_de": periodo_lancamento_de,
            "periodo_lancamento_ate": periodo_lancamento_ate,
        },
    )

    assert CentralDeDownload.objects.count() == 1
    arquivo = CentralDeDownload.objects.first()
    assert arquivo is not None and arquivo.usuario == usuario
    assert arquivo is not None and arquivo.identificador == nome_arquivo
    assert arquivo is not None and arquivo.status == CentralDeDownload.STATUS_CONCLUIDO


@pytest.mark.django_db
def test_exporta_relatorio_adesao_para_pdf_sem_resultados(usuario):
    # arrange
    mes = "03"
    ano = "2024"

    nome_arquivo = "relatorio-adesao.pdf"

    # act
    resultados = {}

    exporta_relatorio_adesao_para_pdf(
        usuario, nome_arquivo, resultados, {"mes_ano": f"{mes}_{ano}"}
    )

    assert CentralDeDownload.objects.count() == 1
    arquivo = CentralDeDownload.objects.first()
    assert arquivo is not None and arquivo.usuario == usuario
    assert arquivo is not None and arquivo.identificador == nome_arquivo
    assert arquivo is not None and arquivo.status == CentralDeDownload.STATUS_CONCLUIDO


@pytest.mark.django_db
def test_exporta_relatorio_consolidado_xlsx(
    usuario,
    escola,
    escola_emefm,
    grupo_escolar,
    categoria_medicao,
    categoria_medicao_dieta_a,
    tipo_alimentacao_refeicao,
    make_medicao,
    make_valores_medicao,
    make_periodo_escolar,
):
    mes = "05"
    ano = "2023"
    status = "MEDICAO_APROVADA_PELA_CODAE"

    SolicitacaoMedicaoInicial.objects.create(
        escola=escola,
        ano=ano,
        mes=mes,
        status=status,
    )

    SolicitacaoMedicaoInicial.objects.create(
        escola=escola_emefm,
        ano=ano,
        mes=mes,
        status=status,
    )

    solicitacoes = SolicitacaoMedicaoInicial.objects.filter(
        mes=mes,
        ano=ano,
        escola__tipo_unidade__iniciais__in=["EMEF", "EMEFM"],
        escola__diretoria_regional=escola.diretoria_regional,
        status=status,
    )

    solicitacoes_uuids = list(solicitacoes.values_list("uuid", flat=True))

    periodo_escolar = make_periodo_escolar("MANHA")
    medicao = make_medicao(solicitacoes[0], periodo_escolar)
    valores = range(1, 6)
    for categoria in [categoria_medicao_dieta_a, categoria_medicao]:
        for x in valores:
            make_valores_medicao(
                medicao=medicao,
                categoria_medicao=categoria,
                valor=str(x).rjust(2, "0"),
                tipo_alimentacao=tipo_alimentacao_refeicao,
                nome_campo="refeicao",
            )
            make_valores_medicao(
                medicao=medicao,
                categoria_medicao=categoria,
                valor=str(x).rjust(2, "0"),
                nome_campo="frequencia",
            )

    grupo_unidade_escolar = GrupoUnidadeEscolar.objects.get(uuid=grupo_escolar)
    tipos_unidades = grupo_unidade_escolar.tipos_unidades.all()
    tipos_de_unidade_do_grupo = list(tipos_unidades.values_list("iniciais", flat=True))
    nome_arquivo = f"Relatório Consolidado das Medições Inicias - {escola.diretoria_regional.nome} - {grupo_unidade_escolar.nome} - {mes}/{ano}.xlsx"

    exporta_relatorio_consolidado_xlsx(
        user=usuario,
        nome_arquivo=nome_arquivo,
        solicitacoes=solicitacoes_uuids,
        tipos_de_unidade=tipos_de_unidade_do_grupo,
        query_params={
            "mes": mes,
            "ano": ano,
            "status": status,
            "dre": escola.diretoria_regional.uuid,
        },
    )

    assert CentralDeDownload.objects.count() == 1
    arquivo = CentralDeDownload.objects.first()
    assert arquivo is not None and arquivo.usuario == usuario
    assert arquivo is not None and arquivo.identificador == nome_arquivo
    assert arquivo is not None and arquivo.status == CentralDeDownload.STATUS_CONCLUIDO


@pytest.mark.django_db
def test_exporta_relatorio_controle_frequencia_para_pdf(
    usuario,
    escola_cei,
    make_periodo_escolar,
):
    periodo_escolar = make_periodo_escolar("MANHA")
    periodo_escolar_integral = make_periodo_escolar("INTEGRAL")

    nome_arquivo = "controle-frequencia.pdf"

    exporta_relatorio_controle_frequencia_para_pdf(
        user=usuario,
        nome_arquivo=nome_arquivo,
        query_params={
            "periodos": json.dumps([str(periodo_escolar.uuid)]),
            "mes_ano": "6_2024",
            "data_inicial": "2024-06-03",
            "data_final": "2024-06-27",
        },
        escola_uuid=escola_cei.uuid,
    )

    assert CentralDeDownload.objects.count() == 1
    arquivo = CentralDeDownload.objects.first()
    assert arquivo is not None and arquivo.usuario == usuario
    assert arquivo is not None and arquivo.identificador == nome_arquivo
    assert arquivo is not None and arquivo.status == CentralDeDownload.STATUS_CONCLUIDO


@pytest.mark.django_db
def test_gera_pdf_relatorio_unificado_async_cei(
    solicitacoes_cei_relatorio_unificado, usuario
):
    ids = [s.uuid for s in solicitacoes_cei_relatorio_unificado]
    tipos = ["CCI", "CCI/CIPS", "CEI", "CEI CEU", "CEI DIRET", "CEU CEI"]

    nome_arquivo = "relatorio_teste.pdf"
    usuario = usuario.get_username()

    gera_pdf_relatorio_unificado_async(
        user=usuario,
        nome_arquivo=nome_arquivo,
        ids_solicitacoes=ids,
        tipos_de_unidade=tipos,
    )

    registro = CentralDeDownload.objects.get(identificador=nome_arquivo)
    assert registro.status == CentralDeDownload.STATUS_CONCLUIDO
    assert registro.arquivo is not None


@pytest.mark.django_db
def test_gera_pdf_relatorio_unificado_async_cei_exception(
    solicitacoes_cei_relatorio_unificado, usuario
):
    ids = [s.uuid for s in solicitacoes_cei_relatorio_unificado]
    tipos = ["Não", "Existe"]

    nome_arquivo = "relatorio_teste.pdf"
    usuario = usuario.get_username()
    gera_pdf_relatorio_unificado_async(
        user=usuario,
        nome_arquivo=nome_arquivo,
        ids_solicitacoes=ids,
        tipos_de_unidade=tipos,
    )

    registro = CentralDeDownload.objects.get(identificador=nome_arquivo)
    assert registro.status == CentralDeDownload.STATUS_ERRO
    assert registro.arquivo is not None


@pytest.mark.django_db
def test_processa_relatorio_lancamentos(
    solicitacoes_cei_relatorio_unificado, pdf_real_monkeypatch
):
    from model_bakery import baker

    merger = PdfWriter()
    central = baker.make(CentralDeDownload)

    ids = [s.uuid for s in solicitacoes_cei_relatorio_unificado]
    tipos = ["CCI", "CCI/CIPS", "CEI", "CEI CEU", "CEI DIRET", "CEU CEI"]

    processa_relatorio_lançamentos(ids, tipos, merger, central)

    assert len(merger.pages) == len(solicitacoes_cei_relatorio_unificado)


@pytest.mark.django_db
def test_processa_relatorio_lancamentos_exception(
    solicitacoes_cei_relatorio_unificado, pdf_real_monkeypatch
):
    from model_bakery import baker

    merger = PdfWriter()
    central = baker.make(CentralDeDownload)

    ids = [s.uuid for s in solicitacoes_cei_relatorio_unificado]
    tipos = ["Não", "Existe"]
    with pytest.raises(ValueError, match="Unidades inválidas"):
        processa_relatorio_lançamentos(ids, tipos, merger, central)


class CriaSolicitacaoMedicaoInicialMesAtualUsuarioAdmin(TestCase):
    def setUp(self):

        self.terceirizada = baker.make(Terceirizada)
        self.lote = baker.make(Lote, terceirizada=self.terceirizada)
        self.escola = baker.make(Escola, nome="Escola Teste", lote=self.lote)

        self.usuario_admin = baker.make(
            Usuario, email="system@admin.com", nome="System Admin", is_active=True
        )

    @freeze_time("2024-03-15")
    def test_cria_solicitacao_medicao_inicial_com_log(self):
        """
        Testa a criação completa de uma solicitação de medição inicial
        e verifica se o log é criado corretamente com o usuário admin
        """

        data_atual = datetime.date(2024, 3, 15)
        data_mes_anterior = data_atual + relativedelta(months=-1)

        solicitacao_mes_anterior = baker.make(
            SolicitacaoMedicaoInicial,
            escola=self.escola,
            ano=data_mes_anterior.year,
            mes=f"{data_mes_anterior.month:02d}",
            criado_por=self.usuario_admin,
            ue_possui_alunos_periodo_parcial=True,
            status=SolicitacaoMedicaoInicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
        )

        tipos_contagem = baker.make(
            "medicao_inicial.TipoContagemAlimentacao", _quantity=3
        )
        solicitacao_mes_anterior.tipos_contagem_alimentacao.set(tipos_contagem)

        responsaveis = baker.make(
            Responsavel,
            solicitacao_medicao_inicial=solicitacao_mes_anterior,
            _quantity=2,
            nome=lambda: f"Responsavel {Responsavel.objects.count() + 1}",
            rf=lambda: f"RF{Responsavel.objects.count() + 1000}",
        )

        alunos = baker.make(
            AlunoPeriodoParcial,
            solicitacao_medicao_inicial=solicitacao_mes_anterior,
            escola=self.escola,
            data=datetime.date(data_mes_anterior.year, data_mes_anterior.month, 1),
            data_removido=None,
            _quantity=2,
        )

        self.assertEqual(SolicitacaoMedicaoInicial.objects.count(), 1)
        self.assertEqual(LogSolicitacoesUsuario.objects.count(), 0)

        cria_solicitacao_medicao_inicial_mes_atual()

        self.assertEqual(SolicitacaoMedicaoInicial.objects.count(), 2)

        nova_solicitacao = SolicitacaoMedicaoInicial.objects.filter(
            escola=self.escola, ano=data_atual.year, mes=f"{data_atual.month:02d}"
        ).first()

        self.assertIsNotNone(nova_solicitacao)

        self.assertEqual(nova_solicitacao.criado_por, self.usuario_admin)
        self.assertEqual(nova_solicitacao.ue_possui_alunos_periodo_parcial, True)

        self.assertEqual(
            nova_solicitacao.tipos_contagem_alimentacao.count(),
            solicitacao_mes_anterior.tipos_contagem_alimentacao.count(),
        )

        self.assertEqual(nova_solicitacao.responsaveis.count(), 2)

        self.assertEqual(
            nova_solicitacao.alunos_periodo_parcial.filter(
                data_removido__isnull=True
            ).count(),
            2,
        )

        logs = LogSolicitacoesUsuario.objects.all()
        self.assertEqual(logs.count(), 1)

        log = logs.first()

        self.assertEqual(log.usuario, self.usuario_admin)
        self.assertEqual(
            log.status_evento,
            LogSolicitacoesUsuario.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
        )
        self.assertEqual(log.solicitacao_tipo, LogSolicitacoesUsuario.MEDICAO_INICIAL)
        self.assertEqual(log.uuid_original, nova_solicitacao.uuid)

        self.assertEqual(
            nova_solicitacao.status,
            SolicitacaoMedicaoInicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
        )

    @freeze_time("2024-03-15")
    def test_cria_solicitacao_sem_solicitacao_anterior(self):
        """
        Testa o cenário onde não existe solicitação do mês anterior
        """
        cria_solicitacao_medicao_inicial_mes_atual()

        self.assertEqual(SolicitacaoMedicaoInicial.objects.count(), 0)
        self.assertEqual(LogSolicitacoesUsuario.objects.count(), 0)

    @freeze_time("2024-03-15")
    def test_cria_solicitacao_sem_alunos_periodo_parcial(self):
        data_atual = datetime.date(2024, 3, 15)
        data_mes_anterior = data_atual + relativedelta(months=-1)

        solicitacao_mes_anterior = baker.make(
            SolicitacaoMedicaoInicial,
            escola=self.escola,
            ano=data_mes_anterior.year,
            mes=f"{data_mes_anterior.month:02d}",
            criado_por=self.usuario_admin,
            ue_possui_alunos_periodo_parcial=False,  # Importante: False
        )

        tipos_contagem = baker.make(
            "medicao_inicial.TipoContagemAlimentacao", _quantity=2
        )
        solicitacao_mes_anterior.tipos_contagem_alimentacao.set(tipos_contagem)

        cria_solicitacao_medicao_inicial_mes_atual()

        nova_solicitacao = SolicitacaoMedicaoInicial.objects.filter(
            escola=self.escola, ano=data_atual.year, mes=f"{data_atual.month:02d}"
        ).first()

        self.assertIsNotNone(nova_solicitacao)
        self.assertEqual(nova_solicitacao.ue_possui_alunos_periodo_parcial, False)
        self.assertEqual(nova_solicitacao.alunos_periodo_parcial.count(), 0)
        self.assertEqual(LogSolicitacoesUsuario.objects.count(), 1)
        log = LogSolicitacoesUsuario.objects.first()
        self.assertEqual(log.usuario, self.usuario_admin)

    @freeze_time("2024-03-15")
    def test_cria_solicitacao_para_multiplas_escolas(self):
        """
        Testa criação de solicitações para múltiplas escolas
        """
        data_atual = datetime.date(2024, 3, 15)
        data_mes_anterior = data_atual + relativedelta(months=-1)

        escolas = []
        for i in range(3):
            escola = baker.make(Escola, nome=f"Escola {i}", lote=self.lote)
            escolas.append(escola)

            solicitacao = baker.make(
                SolicitacaoMedicaoInicial,
                escola=escola,
                ano=data_mes_anterior.year,
                mes=f"{data_mes_anterior.month:02d}",
                criado_por=self.usuario_admin,
                ue_possui_alunos_periodo_parcial=False,
            )

            tipos = baker.make("medicao_inicial.TipoContagemAlimentacao", _quantity=2)
            solicitacao.tipos_contagem_alimentacao.set(tipos)

        cria_solicitacao_medicao_inicial_mes_atual()

        self.assertEqual(SolicitacaoMedicaoInicial.objects.count(), 6)

        logs = LogSolicitacoesUsuario.objects.all()
        self.assertEqual(logs.count(), 3)

        for log in logs:
            self.assertEqual(log.usuario, self.usuario_admin)
            self.assertEqual(
                log.status_evento,
                LogSolicitacoesUsuario.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
            )

    @freeze_time("2024-03-15")
    def test_cria_solicitacao_com_solicitacao_atual_existente(self):
        """
        Testa que não cria nova solicitação se já existe uma para o mês atual
        """
        data_atual = datetime.date(2024, 3, 15)
        data_mes_anterior = data_atual + relativedelta(months=-1)

        solicitacao_mes_anterior = baker.make(
            SolicitacaoMedicaoInicial,
            escola=self.escola,
            ano=data_mes_anterior.year,
            mes=f"{data_mes_anterior.month:02d}",
            criado_por=self.usuario_admin,
        )

        baker.make(
            SolicitacaoMedicaoInicial,
            escola=self.escola,
            ano=data_atual.year,
            mes=f"{data_atual.month:02d}",
            criado_por=self.usuario_admin,
        )

        count_inicial = SolicitacaoMedicaoInicial.objects.count()
        cria_solicitacao_medicao_inicial_mes_atual()
        self.assertEqual(SolicitacaoMedicaoInicial.objects.count(), count_inicial)
        self.assertEqual(LogSolicitacoesUsuario.objects.count(), 0)

    @freeze_time("2024-03-15")
    def test_cria_solicitacao_com_rastro(self):
        """
        Testa se o rastro (lote e terceirizada) é salvo corretamente
        """
        data_atual = datetime.date(2024, 3, 15)
        data_mes_anterior = data_atual + relativedelta(months=-1)

        solicitacao_mes_anterior = baker.make(
            SolicitacaoMedicaoInicial,
            escola=self.escola,
            ano=data_mes_anterior.year,
            mes=f"{data_mes_anterior.month:02d}",
            criado_por=self.usuario_admin,
        )

        cria_solicitacao_medicao_inicial_mes_atual()

        nova_solicitacao = SolicitacaoMedicaoInicial.objects.filter(
            escola=self.escola, ano=data_atual.year, mes=f"{data_atual.month:02d}"
        ).first()

        self.assertIsNotNone(nova_solicitacao)

        self.assertEqual(nova_solicitacao.rastro_lote, self.escola.lote)
        self.assertEqual(
            nova_solicitacao.rastro_terceirizada, self.escola.lote.terceirizada
        )
