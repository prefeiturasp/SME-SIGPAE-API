from django.db import models
from django.db.models import Sum

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.behaviors import (
    EhAlteracaoCardapio,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.managers.alteracao_tipo_alimentacao_cemei_managers import (
    AlteracoesCardapioCEMEIDestaSemanaManager,
    AlteracoesCardapioCEMEIDesteMesManager,
)
from sme_sigpae_api.dados_comuns.behaviors import (
    CanceladoIndividualmente,
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
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario


class AlteracaoCardapioCEMEI(
    CriadoEm,
    CriadoPor,
    TemChaveExterna,
    TemObservacao,
    FluxoAprovacaoPartindoDaEscola,
    TemIdentificadorExternoAmigavel,
    Logs,
    TemPrioridade,
    SolicitacaoForaDoPrazo,
    EhAlteracaoCardapio,
    TemTerceirizadaConferiuGestaoAlimentacao,
):
    DESCRICAO = "Alteração do Tipo de Alimentação CEMEI"

    TODOS = "TODOS"
    CEI = "CEI"
    EMEI = "EMEI"

    STATUS_CHOICES = ((TODOS, "Todos"), (CEI, "CEI"), (EMEI, "EMEI"))

    alunos_cei_e_ou_emei = models.CharField(
        choices=STATUS_CHOICES, max_length=10, default=TODOS
    )
    alterar_dia = models.DateField("Alterar dia", null=True, blank=True)
    data_inicial = models.DateField("Data inicial", null=True, blank=True)
    data_final = models.DateField("Data final", null=True, blank=True)

    objects = models.Manager()  # Manager Padrão
    desta_semana = AlteracoesCardapioCEMEIDestaSemanaManager()
    deste_mes = AlteracoesCardapioCEMEIDesteMesManager()

    @property
    def data(self):
        return self.alterar_dia or self.data_inicial

    @property
    def datas(self):
        return ", ".join(
            [
                data.strftime("%d/%m/%Y")
                for data in self.datas_intervalo.values_list("data", flat=True)
            ]
        )

    @property
    def existe_dia_cancelado(self):
        return self.datas_intervalo.filter(cancelado=True).exists()

    @property
    def inclusoes(self):
        return self.datas_intervalo

    @property
    def tipo(self):
        return "Alteração do Tipo de Alimentação"

    @property
    def path(self):
        return f"alteracao-do-tipo-de-alimentacao-cemei/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-cemei"

    @property
    def numero_alunos(self):
        total = 0
        total += (
            self.substituicoes_cemei_cei_periodo_escolar.aggregate(
                Sum("faixas_etarias__quantidade")
            )["faixas_etarias__quantidade__sum"]
            or 0
        )
        total += (
            self.substituicoes_cemei_emei_periodo_escolar.aggregate(Sum("qtd_alunos"))[
                "qtd_alunos__sum"
            ]
            or 0
        )
        return total

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

    def substituicoes_dict(self):
        substituicoes = []
        periodos_cei = self.substituicoes_cemei_cei_periodo_escolar.all()
        periodos_cei = periodos_cei.values_list("periodo_escolar__nome", flat=True)
        periodos_emei = self.substituicoes_cemei_emei_periodo_escolar.all()
        periodos_emei = periodos_emei.values_list("periodo_escolar__nome", flat=True)
        nomes_periodos = list(periodos_cei) + list(periodos_emei)
        nomes_periodos = list(set(nomes_periodos))
        for periodo in nomes_periodos:
            substituicoes_cei = self.substituicoes_cemei_cei_periodo_escolar.filter(
                periodo_escolar__nome=periodo
            )
            substituicoes_emei = self.substituicoes_cemei_emei_periodo_escolar.filter(
                periodo_escolar__nome=periodo
            )
            faixas_cei = {}
            faixa_emei = {}
            for sc in substituicoes_cei:
                tipos_alimentacao_de = list(
                    sc.tipos_alimentacao_de.values_list("nome", flat=True)
                )
                tipos_alimentacao_de = ", ".join(tipos_alimentacao_de)
                tipos_alimentacao_para = list(
                    sc.tipos_alimentacao_para.values_list("nome", flat=True)
                )
                tipos_alimentacao_para = ", ".join(tipos_alimentacao_para)
                total_alunos = 0
                total_matriculados = 0
                faixas_etarias = []
                for faixa in sc.faixas_etarias.all():
                    total_alunos += faixa.quantidade
                    total_matriculados += faixa.matriculados_quando_criado
                    faixa_etaria = faixa.faixa_etaria.__str__()
                    faixas_etarias.append(
                        {
                            "faixa_etaria": faixa_etaria,
                            "quantidade": faixa.quantidade,
                            "matriculados_quando_criado": faixa.matriculados_quando_criado,
                        }
                    )
                faixas_cei = {
                    "faixas_etarias": faixas_etarias,
                    "total_alunos": total_alunos,
                    "total_matriculados": total_matriculados,
                    "tipos_alimentacao_de": tipos_alimentacao_de,
                    "tipos_alimentacao_para": tipos_alimentacao_para,
                }
            for se in substituicoes_emei:
                tipos_alimentacao_de = list(
                    se.tipos_alimentacao_de.values_list("nome", flat=True)
                )
                tipos_alimentacao_de = ", ".join(tipos_alimentacao_de)
                tipos_alimentacao_para = list(
                    se.tipos_alimentacao_para.values_list("nome", flat=True)
                )
                tipos_alimentacao_para = ", ".join(tipos_alimentacao_para)
                faixa_emei["tipos_alimentacao_de"] = tipos_alimentacao_de
                faixa_emei["tipos_alimentacao_para"] = tipos_alimentacao_para
                faixa_emei["quantidade"] = se.qtd_alunos
                faixa_emei["matriculados_quando_criado"] = se.matriculados_quando_criado
            substituicoes.append(
                {
                    "periodo": periodo,
                    "faixas_cei": faixas_cei,
                    "faixas_emei": faixa_emei,
                }
            )
        return substituicoes

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome,
            "terceirizada": self.rastro_terceirizada,
            "tipo_doc": "Alteração do tipo de Alimentação CEMEI",
            "data_inicial": self.data_inicial,
            "data_final": self.data_final,
            "data_evento": self.data,
            "numero_alunos": self.numero_alunos,
            "motivo": self.motivo.nome,
            "substituicoes": self.substituicoes_dict(),
            "observacao": self.observacao,
            "data_autorizacao": self.data_autorizacao,
            "label_data": label_data,
            "data_log": data_log,
            "id_externo": self.id_externo,
            "datas_intervalo": self.datas_intervalo,
            "status": self.status,
        }

    def __str__(self):
        return f"Alteração de cardápio CEMEI de {self.data}"

    class Meta:
        verbose_name = "Alteração de cardápio CEMEI"
        verbose_name_plural = "Alterações de cardápio CEMEI"


class SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI(TemChaveExterna):
    alteracao_cardapio = models.ForeignKey(
        "AlteracaoCardapioCEMEI",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="substituicoes_cemei_cei_periodo_escolar",
    )
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar",
        on_delete=models.PROTECT,
        related_name="substituicoes_cemei_cei_periodo_escolar",
    )
    tipos_alimentacao_de = models.ManyToManyField(
        "TipoAlimentacao",
        related_name="substituicoes_cemei_cei_tipo_alimentacao_de",
        blank=True,
    )
    tipos_alimentacao_para = models.ManyToManyField(
        "TipoAlimentacao",
        related_name="substituicoes_cemei_cei_alimento_para",
        help_text="Substituições selecionada na solicitação",
        blank=True,
    )

    def __str__(self):
        return f"Substituições de alimentação CEMEI: {self.uuid} da Alteração de Cardápio: {self.alteracao_cardapio.uuid}"  # noqa E501

    class Meta:
        verbose_name = "Substituições de alimentação CEMEI CEI no período"
        verbose_name_plural = "Substituições de alimentação CEMEI CEI no período"


class SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI(
    TemChaveExterna, MatriculadosQuandoCriado
):
    alteracao_cardapio = models.ForeignKey(
        "AlteracaoCardapioCEMEI",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="substituicoes_cemei_emei_periodo_escolar",
    )
    qtd_alunos = models.PositiveSmallIntegerField(default=0)

    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar",
        on_delete=models.PROTECT,
        related_name="substituicoes_cemei_emei_periodo_escolar",
    )
    tipos_alimentacao_de = models.ManyToManyField(
        "TipoAlimentacao",
        related_name="substituicoes_cemei_emei_tipo_alimentacao_de",
        blank=True,
    )
    tipos_alimentacao_para = models.ManyToManyField(
        "TipoAlimentacao",
        related_name="substituicoes_cemei_emei_alimento_para",
        help_text="Substituições selecionada na solicitação",
        blank=True,
    )

    def __str__(self):
        return (
            f"Substituições de alimentação CEMEI EMEI: {self.uuid} "
            f"da Alteração de Cardápio: {self.alteracao_cardapio.uuid}"
        )

    class Meta:
        verbose_name = "Substituições de alimentação CEMEI EMEI no período"
        verbose_name_plural = "Substituições de alimentação CEMEI EMEI no período"


class FaixaEtariaSubstituicaoAlimentacaoCEMEICEI(
    TemChaveExterna, TemFaixaEtariaEQuantidade, MatriculadosQuandoCriado
):
    substituicao_alimentacao = models.ForeignKey(
        "SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI",
        on_delete=models.CASCADE,
        related_name="faixas_etarias",
    )

    def __str__(self):
        retorno = f"Faixa Etária de substituição de alimentação CEMEI CEI: {self.uuid}"
        retorno += f" da Substituição: {self.substituicao_alimentacao.uuid}"
        return retorno

    class Meta:
        verbose_name = "Faixa Etária de substituição de alimentação CEMEI CEI"
        verbose_name_plural = "Faixas Etárias de substituição de alimentação CEMEI CEI"


class DataIntervaloAlteracaoCardapioCEMEI(
    CanceladoIndividualmente,
    CriadoEm,
    TemData,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
):
    alteracao_cardapio_cemei = models.ForeignKey(
        "AlteracaoCardapioCEMEI",
        on_delete=models.CASCADE,
        related_name="datas_intervalo",
    )

    def __str__(self):
        return (
            f"Data {self.data} da Alteração de cardápio CEMEI #{self.alteracao_cardapio_cemei.id_externo} de "
            f"{self.alteracao_cardapio_cemei.data_inicial} - {self.alteracao_cardapio_cemei.data_inicial}"
        )

    class Meta:
        verbose_name = "Data do intervalo de Alteração de cardápio CEMEI"
        verbose_name_plural = "Datas do intervalo de Alteração de cardápio CEMEI"
        ordering = ("data",)
