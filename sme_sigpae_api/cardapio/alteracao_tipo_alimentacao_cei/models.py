from django.db import models
from django.db.models import Sum
from django_prometheus.models import ExportModelOperationsMixin

from sme_sigpae_api.cardapio.behaviors import EhAlteracaoCardapio
from sme_sigpae_api.cardapio.managers import (
    AlteracoesCardapioCEIDestaSemanaManager,
    AlteracoesCardapioCEIDesteMesManager,
)
from sme_sigpae_api.dados_comuns.behaviors import (
    CriadoEm,
    CriadoPor,
    Logs,
    MatriculadosQuandoCriado,
    SolicitacaoForaDoPrazo,
    TemChaveExterna,
    TemData,
    TemFaixaEtariaEQuantidade,
    TemIdentificadorExternoAmigavel,
    TemObservacao,
    TemPrioridade,
    TemTerceirizadaConferiuGestaoAlimentacao,
)
from sme_sigpae_api.dados_comuns.fluxo_status import FluxoAprovacaoPartindoDaEscola
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario, TemplateMensagem


class AlteracaoCardapioCEI(
    ExportModelOperationsMixin("alteracao_cardapio_cei"),
    CriadoEm,
    CriadoPor,
    TemChaveExterna,
    TemData,
    TemObservacao,
    FluxoAprovacaoPartindoDaEscola,
    TemIdentificadorExternoAmigavel,
    Logs,
    TemPrioridade,
    SolicitacaoForaDoPrazo,
    EhAlteracaoCardapio,
    TemTerceirizadaConferiuGestaoAlimentacao,
):
    DESCRICAO = "Alteração do Tipo de Alimentação CEI"

    eh_alteracao_com_lanche_repetida = models.BooleanField(default=False)

    objects = models.Manager()  # Manager Padrão
    desta_semana = AlteracoesCardapioCEIDestaSemanaManager()
    deste_mes = AlteracoesCardapioCEIDesteMesManager()

    @property
    def numero_alunos(self):
        return self.substituicoes.aggregate(Sum("faixas_etarias__quantidade"))[
            "faixas_etarias__quantidade__sum"
        ]

    @property
    def substituicoes(self):
        return self.substituicoes_cei_periodo_escolar

    @property
    def tipo(self):
        return "Alteração do Tipo de Alimentação"

    @property
    def path(self):
        return f"alteracao-do-tipo-de-alimentacao/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-cei"

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
    def susbstituicoes_dict(self):
        substituicoes = []
        for obj in self.substituicoes_cei_periodo_escolar.all():
            periodo = obj.periodo_escolar.nome
            tipos_alimentacao_de = list(
                obj.tipos_alimentacao_de.values_list("nome", flat=True)
            )
            tipos_alimentacao_de = ", ".join(tipos_alimentacao_de)
            faixas_etarias = []
            total_alunos = 0
            total_matriculados = 0
            for faixa in obj.faixas_etarias.all():
                total_alunos += faixa.quantidade
                total_matriculados += faixa.matriculados_quando_criado
                faixas_etarias.append(
                    {
                        "faixa_etaria": faixa.faixa_etaria.__str__(),
                        "matriculados_quando_criado": faixa.matriculados_quando_criado,
                        "quantidade": faixa.quantidade,
                    }
                )
            substituicoes.append(
                {
                    "periodo": periodo,
                    "tipos_alimentacao_de": tipos_alimentacao_de,
                    "tipos_alimentacao_para": obj.tipo_alimentacao_para.nome,
                    "faixas_etarias": faixas_etarias,
                    "total_alunos": total_alunos,
                    "total_matriculados": total_matriculados,
                }
            )
        return substituicoes

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome,
            "terceirizada": self.rastro_terceirizada,
            "tipo_doc": "Alteração do Tipo de Alimentação CEI",
            "data_evento": self.data,
            "numero_alunos": self.numero_alunos,
            "motivo": self.motivo.nome,
            "data_autorizacao": self.data_autorizacao,
            "susbstituicoes": self.susbstituicoes_dict,
            "observacao": self.observacao,
            "label_data": label_data,
            "data_log": data_log,
            "id_externo": self.id_externo,
        }

    def __str__(self):
        return f"Alteração de cardápio CEI de {self.data}"

    class Meta:
        verbose_name = "Alteração de cardápio CEI"
        verbose_name_plural = "Alterações de cardápio CEI"


class SubstituicaoAlimentacaoNoPeriodoEscolarCEI(
    ExportModelOperationsMixin(
        "substituicao_cei_alimentacao_periodo_escolar"
    ),  # noqa E501
    TemChaveExterna,
):
    alteracao_cardapio = models.ForeignKey(
        "AlteracaoCardapioCEI",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="substituicoes_cei_periodo_escolar",
    )
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar",
        on_delete=models.PROTECT,
        related_name="substituicoes_cei_periodo_escolar",
    )
    tipos_alimentacao_de = models.ManyToManyField(
        "TipoAlimentacao",
        related_name="substituicoes_cei_tipo_alimentacao_de",
        blank=True,
    )
    tipo_alimentacao_para = models.ForeignKey(
        "TipoAlimentacao",
        on_delete=models.PROTECT,
        related_name="substituicoes_cei_tipo_alimentacao_para",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"Substituições de alimentação CEI: {self.uuid} da Alteração de Cardápio: {self.alteracao_cardapio.uuid}"

    class Meta:
        verbose_name = "Substituições de alimentação CEI no período"
        verbose_name_plural = "Substituições de alimentação CEI no período"


class FaixaEtariaSubstituicaoAlimentacaoCEI(
    ExportModelOperationsMixin("faixa_etaria_substituicao_alimentacao_cei"),
    TemChaveExterna,
    TemFaixaEtariaEQuantidade,
    MatriculadosQuandoCriado,
):
    substituicao_alimentacao = models.ForeignKey(
        "SubstituicaoAlimentacaoNoPeriodoEscolarCEI",
        on_delete=models.CASCADE,
        related_name="faixas_etarias",
    )

    def __str__(self):
        retorno = f"Faixa Etária de substituição de alimentação CEI: {self.uuid}"
        retorno += f" da Substituição: {self.substituicao_alimentacao.uuid}"
        return retorno

    class Meta:
        verbose_name = "Faixa Etária de substituição de alimentação CEI"
        verbose_name_plural = "Faixas Etárias de substituição de alimentação CEI"
