import datetime
import io
import zipfile
from unittest import mock

from django.core.management import CommandError, call_command
from django.test import TestCase

from sme_sigpae_api.dados_comuns.fixtures.factories.dados_comuns_factories import (
    LogSolicitacoesUsuarioFactory,
)
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.dieta_especial.fixtures.factories.dieta_especial_base_factory import (
    SolicitacaoDietaEspecialFactory,
)
from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    AlunoFactory,
    DiretoriaRegionalFactory,
    EscolaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
    TipoUnidadeEscolarFactory,
)
from sme_sigpae_api.perfil.fixtures.factories.perfil_base_factories import (
    UsuarioFactory,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)


class GeraProtocolosCommandTests(TestCase):
    def setup_generico(self):
        self.usuario = UsuarioFactory.create(id=1, nome="System Admin")
        self.periodo_integral = PeriodoEscolarFactory.create(nome="INTEGRAL")
        self.dre = DiretoriaRegionalFactory.create(nome="IPIRANGA", iniciais="IP")
        self.terceirizada = EmpresaFactory.create(nome_fantasia="EMPRESA LTDA")
        self.lote = LoteFactory.create(
            nome="LOTE 01", diretoria_regional=self.dre, terceirizada=self.terceirizada
        )
        self.tipo_unidade_emef = TipoUnidadeEscolarFactory.create(iniciais="EMEF")
        self.escola_emef = EscolaFactory.create(
            nome="EMEF PERICLES",
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade_emef,
            lote=self.lote,
            diretoria_regional=self.dre,
        )

    def setup_dieta_em_vigencia(self):
        self.aluno_1 = AlunoFactory.create(
            codigo_eol="7777777",
            periodo_escolar=self.periodo_integral,
            escola=self.escola_emef,
        )
        self.solicitacao_dieta_especial_em_vigencia = (
            SolicitacaoDietaEspecialFactory.create(
                aluno=self.aluno_1,
                ativo=True,
                status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
                escola_destino=self.escola_emef,
            )
        )
        data_inicio = datetime.date.today() - datetime.timedelta(days=1)
        data_termino = datetime.date.today() + datetime.timedelta(days=1)
        self.solicitacao_dieta_especial_em_vigencia.data_inicio = data_inicio
        self.solicitacao_dieta_especial_em_vigencia.data_termino = data_termino
        self.solicitacao_dieta_especial_em_vigencia.save()
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.solicitacao_dieta_especial_em_vigencia.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            usuario=self.usuario,
        )

    @mock.patch(
        "sme_sigpae_api.dieta_especial.management.commands.gera_zip_protocolos.envia_email_unico_com_anexo_inmemory"
    )
    @mock.patch(
        "sme_sigpae_api.dieta_especial.management.commands.gera_zip_protocolos.HTML"
    )
    @mock.patch(
        "sme_sigpae_api.dieta_especial.management.commands.gera_zip_protocolos.relatorio_dieta_especial_protocolo"
    )
    def test_gera_pdfs_com_sucesso(
        self, mock_relatorio, mock_html_cls, mock_envia_email
    ):
        self.setup_generico()
        self.setup_dieta_em_vigencia()

        mock_html_instance = mock.Mock()
        mock_html_cls.return_value = mock_html_instance
        mock_html_instance.write_pdf.side_effect = lambda buf: buf.write(b"PDFDATA")

        call_command(
            "gera_zip_protocolos",
            lote="LOTE 01",
            email="teste@dominio.com",
            inicio=0,
            fim=1,
        )

        mock_relatorio.assert_called_once_with(
            None, self.solicitacao_dieta_especial_em_vigencia
        )
        mock_html_cls.assert_called_once()
        mock_html_instance.write_pdf.assert_called_once()

        args, kwargs = mock_envia_email.call_args
        anexo_bytes = kwargs["anexo"]
        with zipfile.ZipFile(io.BytesIO(anexo_bytes), "r") as zipf:
            files = zipf.namelist()
            assert len(files) == 1

    def test_sem_dietas_lanca_erro(self):
        self.setup_generico()

        with self.assertRaises(CommandError):
            call_command(
                "gera_zip_protocolos",
                lote="LOTE 01",
                email="teste@dominio.com",
            )
