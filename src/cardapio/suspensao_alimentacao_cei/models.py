from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

from src.cardapio.suspensao_alimentacao.models import MotivoSuspensao
from src.dados_comuns.behaviors import (
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
from src.dados_comuns.fluxo_status import FluxoInformativoPartindoDaEscola
from src.dados_comuns.models import LogSolicitacoesUsuario
from src.dados_comuns.utils import patch_docs


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
    """Solicitação de Suspensão de Alimentação de CEI.

    **Objetivo**: informar à empresa que atende a unidade educacional do tipo
    CEI que um dia previamente letivo não haverá aula por força maior.

    Diferentemente da suspensão padrão, esta solicitação é específica para
    unidades de CEI e utiliza um relacionamento M2M com períodos escolares
    em vez de uma tabela auxiliar de quantidades por período.
    """

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
        """Retorna as solicitações de suspensão de CEI com status INFORMADO.

        Returns:
            django.db.models.QuerySet: Queryset contendo as solicitações da
                classe com status de informado.
        """
        return cls.objects.filter(status=cls.workflow_class.INFORMADO)

    @classmethod
    def get_rascunhos_do_usuario(cls, usuario):
        """Retorna as solicitações de suspensão de CEI com status RASCUNHO de um usuário.

        Args:
            usuario (django.contrib.auth.models.AbstractUser): Usuário autor das
                solicitações.

        Returns:
            django.db.models.QuerySet: Queryset contendo as solicitações da
                classe com status de rascunho criadas pelo usuário informado.
        """
        return cls.objects.filter(
            criado_por=usuario, status=cls.workflow_class.RASCUNHO
        )

    @property
    def tipo(self):
        """Retorna a descrição textual do tipo da solicitação.

        Returns:
            str: String ``"Suspensão de Alimentação"``.
        """
        return "Suspensão de Alimentação"

    @property
    def path(self):
        """Retorna o caminho relativo do relatório desta solicitação no frontend.

        Returns:
            str: URL relativa do frontend para a tela de relatório da
                solicitação de suspensão de CEI.
        """
        return f"suspensao-de-alimentacao-cei/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-normal"

    def salvar_log_transicao(self, status_evento, usuario, justificativa=""):
        """Registra no log a transição de status da solicitação.

        Cria uma entrada em ``LogSolicitacoesUsuario`` associada a esta
        solicitação de suspensão de alimentação de CEI.

        Args:
            status_evento (int): Código do evento de status que será registrado.
            usuario (django.contrib.auth.models.AbstractUser): Usuário
                responsável pela transição.
            justificativa (str, optional): Texto justificando a transição.
                Padrão: ``""``.

        Returns:
            None: O método apenas persiste o log da transição.
        """
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
        """Retorna o total de alunos associado à solicitação.

        Neste tipo de solicitação não há consolidação de quantidade de alunos,
        por isso o valor retornado é sempre vazio.

        Necessário para integração com o paineis_consolidados, que agrupa
        todos os tipos de solicitação.

        Returns:
            str: String vazia.
        """
        return ""

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        """Monta o dicionário usado na geração do relatório da solicitação.

        Args:
            label_data (str): Rótulo textual da data exibida no relatório.
            data_log (datetime.date): Data do log de referência exibida no
                relatório.
            instituicao (object): Instituição solicitante. Mantido por
                compatibilidade de interface, sem uso direto no método.

        Returns:
            dict: Dicionário com os campos utilizados no relatório.
        """
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome_historico(self.data),
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
        """Retorna a representação textual resumida da solicitação.

        Returns:
            str: Identificador externo amigável da solicitação.
        """
        return f"{self.id_externo}"

    class Meta:
        verbose_name = "Suspensão de Alimentação de CEI"
        verbose_name_plural = "Suspensões de Alimentação de CEI"


patch_docs(SuspensaoAlimentacaoDaCEI)
