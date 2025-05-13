from django.db import models
from django.db.models import Sum
from django_prometheus.models import ExportModelOperationsMixin

from sme_sigpae_api.cardapio.base.models import TipoAlimentacao
from sme_sigpae_api.cardapio.behaviors import EhAlteracaoCardapio
from sme_sigpae_api.dados_comuns.behaviors import (
    Ativavel,
    CanceladoIndividualmente,
    CriadoEm,
    CriadoPor,
    IntervaloDeDia,
    Logs,
    Nomeavel,
    SolicitacaoForaDoPrazo,
    TemChaveExterna,
    TemData,
    TemIdentificadorExternoAmigavel,
    TemObservacao,
    TemPrioridade,
    TemTerceirizadaConferiuGestaoAlimentacao,
)
from sme_sigpae_api.dados_comuns.fluxo_status import FluxoAprovacaoPartindoDaEscola
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario, TemplateMensagem


class AlteracaoCardapio(
    ExportModelOperationsMixin("alteracao_cardapio"),
    CriadoEm,
    CriadoPor,
    TemChaveExterna,
    IntervaloDeDia,
    TemObservacao,
    FluxoAprovacaoPartindoDaEscola,
    TemIdentificadorExternoAmigavel,
    Logs,
    TemPrioridade,
    SolicitacaoForaDoPrazo,
    EhAlteracaoCardapio,
    TemTerceirizadaConferiuGestaoAlimentacao,
):
    DESCRICAO = "Alteração do Tipo de Alimentação"

    eh_alteracao_com_lanche_repetida = models.BooleanField(default=False)

    @classmethod
    def com_lanche_do_mes_corrente(cls, escola_uuid):
        lanche = TipoAlimentacao.objects.filter(nome__icontains="lanche")
        alteracoes_da_escola = cls.do_mes_corrente.all().filter(
            escola__uuid=escola_uuid,
            substituicoes_periodo_escolar__tipos_alimentacao_para__in=lanche,
        )
        return alteracoes_da_escola

    @property
    def data(self):
        data = self.data_inicial
        if self.data_final < data:
            data = self.data_final
        return data

    @property
    def numero_alunos(self):
        return self.substituicoes.aggregate(Sum("qtd_alunos"))["qtd_alunos__sum"]

    @property
    def eh_unico_dia(self):
        return self.data_inicial == self.data_final

    @property
    def substituicoes(self):
        return self.substituicoes_periodo_escolar

    @property
    def inclusoes(self):
        return self.datas_intervalo

    @property
    def tipo(self):
        return "Alteração do Tipo de Alimentação"

    @property
    def path(self):
        return f"alteracao-do-tipo-de-alimentacao/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-normal"

    @property
    def template_mensagem(self):
        template = TemplateMensagem.objects.get(
            tipo=TemplateMensagem.ALTERACAO_CARDAPIO
        )
        template_troca = {  # noqa
            "@id": self.id,
            "@criado_em": str(self.criado_em),
            "@status": str(self.status),
            # TODO: verificar a url padrão do pedido
            "@link": "http://teste.com",
        }
        corpo = template.template_html
        return template.assunto, corpo

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        resposta_sim_nao = kwargs.get("resposta_sim_nao", False)
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.ALTERACAO_DE_CARDAPIO,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
            resposta_sim_nao=resposta_sim_nao,
        )

    @property
    def substituicoes_dict(self):
        substituicoes = []
        for obj in self.substituicoes_periodo_escolar.all():
            tipos_alimentacao_de = list(
                obj.tipos_alimentacao_de.values_list("nome", flat=True)
            )
            tipos_alimentacao_de = ", ".join(tipos_alimentacao_de)
            tipos_alimentacao_para = list(
                obj.tipos_alimentacao_para.values_list("nome", flat=True)
            )
            tipos_alimentacao_para = ", ".join(tipos_alimentacao_para)
            substituicoes.append(
                {
                    "periodo": obj.periodo_escolar.nome,
                    "alteracao_de": tipos_alimentacao_de,
                    "alteracao_para": tipos_alimentacao_para,
                }
            )
        return substituicoes

    @property
    def existe_dia_cancelado(self):
        return self.datas_intervalo.filter(cancelado=True).exists()

    @property
    def datas(self):
        return ", ".join(
            [
                data.strftime("%d/%m/%Y")
                for data in self.datas_intervalo.values_list("data", flat=True)
            ]
        )

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome,
            "terceirizada": self.rastro_terceirizada,
            "tipo_doc": "Alteração do tipo de Alimentação",
            "data_evento": self.data,
            "datas_intervalo": self.datas_intervalo,
            "numero_alunos": self.numero_alunos,
            "motivo": self.motivo.nome,
            "data_inicial": self.data_inicial,
            "data_final": self.data_final,
            "data_autorizacao": self.data_autorizacao,
            "observacao": self.observacao,
            "substituicoes": self.substituicoes_dict,
            "label_data": label_data,
            "data_log": data_log,
            "id_externo": self.id_externo,
            "status": self.status,
        }

    def __str__(self):
        return f"Alteração de cardápio de: {self.data_inicial} para {self.data_final}"

    class Meta:
        verbose_name = "Alteração de cardápio"
        verbose_name_plural = "Alterações de cardápio"


class SubstituicaoAlimentacaoNoPeriodoEscolar(
    ExportModelOperationsMixin("substituicao_alimentacao_periodo_escolar"),
    TemChaveExterna,
):
    alteracao_cardapio = models.ForeignKey(
        "AlteracaoCardapio",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="substituicoes_periodo_escolar",
    )
    qtd_alunos = models.PositiveSmallIntegerField(default=0)
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar",
        on_delete=models.PROTECT,
        related_name="substituicoes_periodo_escolar",
    )
    tipos_alimentacao_de = models.ManyToManyField(
        "TipoAlimentacao",
        related_name="substituicoes_alimentos_de",
        help_text="Tipos de alimentação substituídos na solicitação",
        blank=True,
    )
    tipos_alimentacao_para = models.ManyToManyField(
        "TipoAlimentacao",
        related_name="substituicoes_alimento_para",
        help_text="Substituições selecionada na solicitação",
        blank=True,
    )

    def __str__(self):
        return f"Substituições de alimentação: {self.uuid} da Alteração de Cardápio: {self.alteracao_cardapio.uuid}"

    class Meta:
        verbose_name = "Substituições de alimentação no período"
        verbose_name_plural = "Substituições de alimentação no período"


class MotivoAlteracaoCardapio(
    ExportModelOperationsMixin("motivo_alteracao_cardapio"),
    Nomeavel,
    TemChaveExterna,
    Ativavel,
):
    """Usado em conjunto com AlteracaoCardapio.

    Exemplos:
        - atividade diferenciada
        - aniversariante do mes
    """

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Motivo de alteração de cardápio"
        verbose_name_plural = "Motivos de alteração de cardápio"


class DataIntervaloAlteracaoCardapio(
    CanceladoIndividualmente,
    CriadoEm,
    TemData,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
):
    alteracao_cardapio = models.ForeignKey(
        "AlteracaoCardapio", on_delete=models.CASCADE, related_name="datas_intervalo"
    )

    def __str__(self):
        return (
            f"Data {self.data} da Alteração de cardápio #{self.alteracao_cardapio.id_externo} de "
            f"{self.alteracao_cardapio.data_inicial} - {self.alteracao_cardapio.data_inicial}"
        )

    class Meta:
        verbose_name = "Data do intervalo de Alteração de cardápio"
        verbose_name_plural = "Datas do intervalo de Alteração de cardápio"
        ordering = ("data",)
