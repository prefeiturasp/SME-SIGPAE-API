from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

from sme_sigpae_api.cardapio.suspensao_alimentacao.models import MotivoSuspensao
from sme_sigpae_api.dados_comuns.behaviors import (
    CriadoEm,
    CriadoPor,
    Logs,
    TemChaveExterna,
    TemData,
    TemIdentificadorExternoAmigavel,
    TemObservacao,
    TemPrioridade,
    TemTerceirizadaConferiuGestaoAlimentacao,
)
from sme_sigpae_api.dados_comuns.fluxo_status import FluxoInformativoPartindoDaEscola
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario, TemplateMensagem


class SuspensaoAlimentacaoDaCEI(
    ExportModelOperationsMixin("suspensao_alimentacao_de_cei"),
    TemData,
    TemChaveExterna,
    CriadoPor,
    TemIdentificadorExternoAmigavel,
    CriadoEm,
    FluxoInformativoPartindoDaEscola,
    Logs,
    TemObservacao,
    TemPrioridade,
    TemTerceirizadaConferiuGestaoAlimentacao,
):
    DESCRICAO = "Suspensão de Alimentação de CEI"
    escola = models.ForeignKey("escola.Escola", on_delete=models.DO_NOTHING)
    motivo = models.ForeignKey(MotivoSuspensao, on_delete=models.DO_NOTHING)
    outro_motivo = models.CharField("Outro motivo", blank=True, max_length=500)
    periodos_escolares = models.ManyToManyField(
        "escola.PeriodoEscolar",
        related_name="%(app_label)s_%(class)s_periodos",
        help_text="Periodos escolares da suspensão",
        blank=True,
    )

    @classmethod
    def get_informados(cls):
        return cls.objects.filter(status=cls.workflow_class.INFORMADO)

    @classmethod
    def get_rascunhos_do_usuario(cls, usuario):
        return cls.objects.filter(
            criado_por=usuario, status=cls.workflow_class.RASCUNHO
        )

    @property
    def tipo(self):
        return "Suspensão de Alimentação"

    @property
    def path(self):
        return f"suspensao-de-alimentacao-cei/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-normal"

    @property
    def template_mensagem(self):
        template = TemplateMensagem.objects.get(
            tipo=TemplateMensagem.ALTERACAO_CARDAPIO
        )
        template_troca = {  # noqa
            "@id": self.id,
            "@criado_em": str(self.criado_em),
            "@criado_por": str(self.criado_por),
            "@status": str(self.status),
            # TODO: verificar a url padrão do pedido
            "@link": "http://teste.com",
        }
        corpo = template.template_html
        return template.assunto, corpo

    def salvar_log_transicao(self, status_evento, usuario, justificativa=""):
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.SUSPENSAO_ALIMENTACAO_CEI,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
        )

    @property
    def numero_alunos(self):
        return ""

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome,
            "terceirizada": self.rastro_terceirizada,
            "tipo_doc": "Suspensão de Alimentação de CEI",
            "data_evento": self.data,
            "numero_alunos": self.numero_alunos,
            "motivo": self.motivo,
            "periodos_escolares": self.periodos_escolares,
            "label_data": label_data,
            "data_log": data_log,
            "id_externo": self.id_externo,
        }

    def __str__(self):
        return f"{self.id_externo}"

    class Meta:
        verbose_name = "Suspensão de Alimentação de CEI"
        verbose_name_plural = "Suspensões de Alimentação de CEI"
