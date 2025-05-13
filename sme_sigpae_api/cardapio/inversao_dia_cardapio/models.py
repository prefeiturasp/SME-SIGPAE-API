from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

from sme_sigpae_api.cardapio.base.models import Cardapio
from sme_sigpae_api.cardapio.managers import (
    InversaoCardapioDestaSemanaManager,
    InversaoCardapioDesteMesManager,
    InversaoCardapioVencidaManager,
)
from sme_sigpae_api.dados_comuns.behaviors import (
    CriadoEm,
    CriadoPor,
    Logs,
    Motivo,
    SolicitacaoForaDoPrazo,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
    TemObservacao,
    TemPrioridade,
    TemTerceirizadaConferiuGestaoAlimentacao,
)
from sme_sigpae_api.dados_comuns.fluxo_status import FluxoAprovacaoPartindoDaEscola
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario, TemplateMensagem


class InversaoCardapio(
    ExportModelOperationsMixin("inversao_cardapio"),
    CriadoEm,
    CriadoPor,
    TemObservacao,
    Motivo,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
    FluxoAprovacaoPartindoDaEscola,
    TemPrioridade,
    Logs,
    SolicitacaoForaDoPrazo,
    TemTerceirizadaConferiuGestaoAlimentacao,
):
    """Troca um cardápio de um dia por outro.

    servir o cardápio do dia 30 no dia 15, automaticamente o
    cardápio do dia 15 será servido no dia 30
    """

    DESCRICAO = "Inversão de Cardápio"
    objects = models.Manager()  # Manager Padrão
    desta_semana = InversaoCardapioDestaSemanaManager()
    deste_mes = InversaoCardapioDesteMesManager()
    vencidos = InversaoCardapioVencidaManager()
    data_de_inversao = models.DateField("Data de inversão", blank=True, null=True)
    data_para_inversao = models.DateField("Data para inversão", blank=True, null=True)
    data_de_inversao_2 = models.DateField("Data de inversão", blank=True, null=True)
    data_para_inversao_2 = models.DateField("Data para inversão", blank=True, null=True)
    alunos_da_cemei = models.CharField(
        "Alunos da CEMEI", blank=True, default="", max_length=50
    )
    alunos_da_cemei_2 = models.CharField(
        "Alunos da CEMEI", blank=True, default="", max_length=50
    )

    cardapio_de = models.ForeignKey(
        Cardapio,
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="cardapio_de",
    )
    cardapio_para = models.ForeignKey(
        Cardapio,
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="cardapio_para",
    )
    escola = models.ForeignKey(
        "escola.Escola", blank=True, null=True, on_delete=models.DO_NOTHING
    )

    tipos_alimentacao = models.ManyToManyField(
        "TipoAlimentacao", help_text="Tipos de alimentacao.", blank=True
    )

    @classmethod
    def get_solicitacoes_rascunho(cls, usuario):
        solicitacoes_unificadas = InversaoCardapio.objects.filter(
            criado_por=usuario, status=InversaoCardapio.workflow_class.RASCUNHO
        )
        return solicitacoes_unificadas

    @property
    def datas(self):
        if self.cardapio_de:
            datas = self.cardapio_de.data.strftime("%d/%m/%Y")
        else:
            datas = self.data_de_inversao.strftime("%d/%m/%Y")
        if self.data_de_inversao_2:
            datas += "<br />" + self.data_de_inversao_2.strftime("%d/%m/%Y")
        return datas

    @property
    def data_de(self):
        return (
            self.cardapio_de.data if self.cardapio_de else self.data_de_inversao or None
        )

    @property
    def data_para(self):
        return (
            self.cardapio_para.data
            if self.cardapio_para
            else self.data_para_inversao or None
        )

    @property
    def data(self):
        return self.data_para if self.data_para < self.data_de else self.data_de

    @property
    def tipo(self):
        return "Inversão de Dia de Cardápio"

    @property
    def path(self):
        return f"inversao-de-dia-de-cardapio/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-normal"

    @property
    def numero_alunos(self):
        return ""

    @property
    def template_mensagem(self):
        template = TemplateMensagem.objects.get(tipo=TemplateMensagem.INVERSAO_CARDAPIO)
        template_troca = {
            "@id": self.id_externo,
            "@criado_em": str(self.criado_em),
            "@criado_por": str(self.criado_por),
            "@status": str(self.status),
            # TODO: verificar a url padrão do pedido
            "@link": "http://teste.com",
        }
        corpo = template.template_html
        for chave, valor in template_troca.items():
            corpo = corpo.replace(chave, valor)
        return template.assunto, corpo

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        resposta_sim_nao = kwargs.get("resposta_sim_nao", False)
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.INVERSAO_DE_CARDAPIO,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
            resposta_sim_nao=resposta_sim_nao,
        )

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        data_de_inversao = ""
        data_de_inversao_2 = ""
        if self.data_de_inversao:
            data_de_inversao = self.data_de_inversao.strftime("%d/%m/%Y")

        if self.data_de_inversao_2:
            data_de_inversao_2 = self.data_de_inversao_2.strftime("%d/%m/%Y")
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome,
            "terceirizada": self.rastro_terceirizada,
            "tipo_doc": "Inversão de dia de Cardápio",
            "data_evento": f"{data_de_inversao} {data_de_inversao_2}",
            "numero_alunos": self.numero_alunos,
            "data_de_inversao": self.data_de_inversao,
            "data_inicial": self.data_de_inversao,
            "data_final": self.data_para_inversao,
            "data_para_inversao": self.data_para_inversao,
            "data_de_inversao_2": self.data_de_inversao_2,
            "data_para_inversao_2": self.data_para_inversao_2,
            "data_de": self.data_de,
            "data_para": self.data_para,
            "label_data": label_data,
            "data_log": data_log,
            "motivo": self.motivo,
            "observacao": self.observacao,
            "tipos_alimentacao": ", ".join(
                self.tipos_alimentacao.values_list("nome", flat=True)
            ),
            "datas": self.datas,
            "id_externo": self.id_externo,
        }

    def __str__(self):
        return (
            f"Inversão de Cardápio \nDe: {self.cardapio_de or self.data_de_inversao} \n"
            f"Para: {self.cardapio_para or self.data_para_inversao}"
        )

    class Meta:
        verbose_name = "Inversão de cardápio"
        verbose_name_plural = "Inversões de cardápio"
