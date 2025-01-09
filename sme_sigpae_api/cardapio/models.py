from django.db import models
from django.db.models import Sum
from django_prometheus.models import ExportModelOperationsMixin

from ..dados_comuns.behaviors import (  # noqa I101
    Ativavel,
    CanceladoIndividualmente,
    CriadoEm,
    CriadoPor,
    Descritivel,
    IntervaloDeDia,
    Logs,
    LogSolicitacoesUsuario,
    MatriculadosQuandoCriado,
    Motivo,
    Nomeavel,
    Posicao,
    SolicitacaoForaDoPrazo,
    TemChaveExterna,
    TemData,
    TemFaixaEtariaEQuantidade,
    TemIdentificadorExternoAmigavel,
    TemObservacao,
    TemPrioridade,
    TemTerceirizadaConferiuGestaoAlimentacao,
)
from ..dados_comuns.fluxo_status import (
    FluxoAprovacaoPartindoDaEscola,
    FluxoInformativoPartindoDaEscola,
)
from ..dados_comuns.models import TemplateMensagem  # noqa I202
from .behaviors import EhAlteracaoCardapio, TemLabelDeTiposDeAlimentacao
from .managers import (
    AlteracoesCardapioCEIDestaSemanaManager,
    AlteracoesCardapioCEIDesteMesManager,
    AlteracoesCardapioCEMEIDestaSemanaManager,
    AlteracoesCardapioCEMEIDesteMesManager,
    GrupoSuspensaoAlimentacaoDestaSemanaManager,
    GrupoSuspensaoAlimentacaoDesteMesManager,
    InversaoCardapioDestaSemanaManager,
    InversaoCardapioDesteMesManager,
    InversaoCardapioVencidaManager,
)


class TipoAlimentacao(
    ExportModelOperationsMixin("tipo_alimentacao"), Nomeavel, TemChaveExterna, Posicao
):
    """Compõe parte do cardápio.

    Dejejum
    Colação
    Almoço
    Refeição
    Sobremesa
    Lanche 4 horas
    Lanche 5 horas
    Lanche 6 horas
    Lanche Emergencial
    """

    @property
    def substituicoes_periodo_escolar(self):
        return self.substituicoes_periodo_escolar

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Tipo de alimentação"
        verbose_name_plural = "Tipos de alimentação"
        ordering = ["posicao"]


class HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar(TemChaveExterna):
    hora_inicial = models.TimeField(auto_now=False, auto_now_add=False)
    hora_final = models.TimeField(auto_now=False, auto_now_add=False)
    escola = models.ForeignKey(
        "escola.Escola", blank=True, null=True, on_delete=models.DO_NOTHING
    )
    tipo_alimentacao = models.ForeignKey(
        "cardapio.TipoAlimentacao", blank=True, null=True, on_delete=models.DO_NOTHING
    )
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar", blank=True, null=True, on_delete=models.DO_NOTHING
    )

    def __str__(self):
        return f"{self.tipo_alimentacao.nome} DE: {self.hora_inicial} ATE: {self.hora_final}"


class ComboDoVinculoTipoAlimentacaoPeriodoTipoUE(
    ExportModelOperationsMixin("substituicoes_vinculo_alimentacao"),
    TemChaveExterna,
    TemLabelDeTiposDeAlimentacao,
):  # noqa E125
    tipos_alimentacao = models.ManyToManyField(
        "TipoAlimentacao",
        related_name="%(app_label)s_%(class)s_possibilidades",
        help_text="Tipos de alimentacao do combo.",
        blank=True,
    )
    vinculo = models.ForeignKey(
        "VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        null=True,
        on_delete=models.CASCADE,
        related_name="combos",
    )

    def pode_excluir(self):
        # TODO: incrementar esse método,  impedir exclusão se tiver
        # solicitações em cima desse combo também.
        return not self.substituicoes.exists()

    def __str__(self):
        tipos_alimentacao_nome = [
            nome for nome in self.tipos_alimentacao.values_list("nome", flat=True)
        ]  # noqa
        return f"TiposAlim.: {tipos_alimentacao_nome}"

    class Meta:
        verbose_name = "Combo do vínculo tipo alimentação"
        verbose_name_plural = "Combos do vínculo tipo alimentação"


class SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE(
    TemChaveExterna, TemLabelDeTiposDeAlimentacao
):  # noqa E125
    tipos_alimentacao = models.ManyToManyField(
        "TipoAlimentacao",
        related_name="%(app_label)s_%(class)s_possibilidades",
        help_text="Tipos de alimentacao das substituições dos combos.",
        blank=True,
    )
    combo = models.ForeignKey(
        "ComboDoVinculoTipoAlimentacaoPeriodoTipoUE",
        null=True,
        on_delete=models.CASCADE,
        related_name="substituicoes",
    )

    def pode_excluir(self):
        # TODO: incrementar esse método,  impedir exclusão se tiver
        # solicitações em cima dessa substituição do combo.
        return True

    def __str__(self):
        tipos_alimentacao_nome = [
            nome for nome in self.tipos_alimentacao.values_list("nome", flat=True)
        ]
        return f"TiposAlim.:{tipos_alimentacao_nome}"

    class Meta:
        verbose_name = "Substituição do combo do vínculo tipo alimentação"
        verbose_name_plural = "Substituições do  combos do vínculo tipo alimentação"


class VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar(
    ExportModelOperationsMixin("vinculo_alimentacao_periodo_escolar_tipo_ue"),
    Ativavel,
    TemChaveExterna,
):  # noqa E125
    """Vincular vários tipos de alimentação a um periodo e tipo de U.E.

    Dado o tipo_unidade_escolar (EMEI, EMEF...) e
    em seguida o periodo_escolar(MANHA, TARDE..),
    trazer os tipos de alimentação que podem ser servidos.
    Ex.: Para CEI(creche) pela manhã (período) faz sentido ter mingau e não café da tarde.
    """

    # TODO: Refatorar para usar EscolaPeriodoEscolar
    tipo_unidade_escolar = models.ForeignKey(
        "escola.TipoUnidadeEscolar", null=True, on_delete=models.DO_NOTHING
    )
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar", null=True, on_delete=models.DO_NOTHING
    )
    tipos_alimentacao = models.ManyToManyField(
        "TipoAlimentacao", related_name="vinculos", blank=True
    )

    def __str__(self):
        return f"{self.tipo_unidade_escolar.iniciais} - {self.periodo_escolar.nome}"

    class Meta:
        unique_together = [["periodo_escolar", "tipo_unidade_escolar"]]
        verbose_name = "Vínculo tipo alimentação"
        verbose_name_plural = "Vínculos tipo alimentação"


class Cardapio(
    ExportModelOperationsMixin("cardapio"),
    Descritivel,
    Ativavel,
    TemData,
    TemChaveExterna,
    CriadoEm,
):
    """Cardápio escolar.

    tem 1 data pra acontecer ex (26/06)
    tem 1 lista de tipos de alimentação (Dejejum, Colação, Almoço, LANCHE DE 4 HS OU 8 HS;
    LANCHE DE 5HS OU 6 HS; REFEIÇÃO).

    !!!OBS!!! PARA CEI varia por faixa de idade.
    """

    tipos_alimentacao = models.ManyToManyField(TipoAlimentacao)
    edital = models.ForeignKey(
        "terceirizada.Edital", on_delete=models.DO_NOTHING, related_name="editais"
    )

    @property  # type: ignore
    def tipos_unidade_escolar(self):
        return self.tipos_unidade_escolar

    def __str__(self):
        if self.descricao:
            return f"{self.data}  - {self.descricao}"
        return f"{self.data}"

    class Meta:
        verbose_name = "Cardápio"
        verbose_name_plural = "Cardápios"


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
        verbose_name_plural = "Inversão$ProjectFileDir$ de cardápios"


class MotivoSuspensao(
    ExportModelOperationsMixin("motivo_suspensao"), Nomeavel, TemChaveExterna
):
    """Trabalha em conjunto com SuspensaoAlimentacao.

    Exemplos:
        - greve
        - reforma
    """

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Motivo de suspensão de alimentação"
        verbose_name_plural = "Motivo de suspensão de alimentação"


class SuspensaoAlimentacao(
    ExportModelOperationsMixin("suspensao_alimentacao"),
    TemData,
    TemChaveExterna,
    CanceladoIndividualmente,
):
    """Trabalha em conjunto com GrupoSuspensaoAlimentacao."""

    prioritario = models.BooleanField(default=False)
    motivo = models.ForeignKey(MotivoSuspensao, on_delete=models.DO_NOTHING)
    outro_motivo = models.CharField("Outro motivo", blank=True, max_length=500)
    grupo_suspensao = models.ForeignKey(
        "GrupoSuspensaoAlimentacao",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="suspensoes_alimentacao",
    )

    def __str__(self):
        return f"{self.motivo}"

    class Meta:
        verbose_name = "Suspensão de alimentação"
        verbose_name_plural = "Suspensões de alimentação"


class QuantidadePorPeriodoSuspensaoAlimentacao(
    ExportModelOperationsMixin("quantidade_periodo"), TemChaveExterna
):
    CEI_OU_EMEI_CHOICES = [
        ("TODOS", "Todos"),
        ("CEI", "CEI"),
        ("EMEI", "EMEI"),
    ]
    numero_alunos = models.SmallIntegerField()
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar", on_delete=models.DO_NOTHING
    )
    grupo_suspensao = models.ForeignKey(
        "GrupoSuspensaoAlimentacao",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="quantidades_por_periodo",
    )
    # TODO: SUBSTITUIR POR COMBOS DO TIPO DE ALIMENTACAO
    tipos_alimentacao = models.ManyToManyField(TipoAlimentacao)
    alunos_cei_ou_emei = models.CharField(
        max_length=10, choices=CEI_OU_EMEI_CHOICES, blank=True
    )

    def __str__(self):
        return f"Quantidade de alunos: {self.numero_alunos}"

    class Meta:
        verbose_name = "Quantidade por período de suspensão de alimentação"
        verbose_name_plural = "Quantidade por período de suspensão de alimentação"


class GrupoSuspensaoAlimentacao(
    ExportModelOperationsMixin("grupo_suspensao_alimentacao"),
    TemChaveExterna,
    CriadoPor,
    TemIdentificadorExternoAmigavel,
    CriadoEm,
    TemObservacao,
    FluxoInformativoPartindoDaEscola,
    Logs,
    TemPrioridade,
    TemTerceirizadaConferiuGestaoAlimentacao,
):
    """Serve para agrupar suspensões.

    Vide SuspensaoAlimentacao e QuantidadePorPeriodoSuspensaoAlimentacao
    """

    DESCRICAO = "Suspensão de Alimentação"
    escola = models.ForeignKey("escola.Escola", on_delete=models.DO_NOTHING)
    objects = models.Manager()  # Manager Padrão
    desta_semana = GrupoSuspensaoAlimentacaoDestaSemanaManager()
    deste_mes = GrupoSuspensaoAlimentacaoDesteMesManager()

    @classmethod
    def get_informados(cls):
        return cls.objects.filter(status=cls.workflow_class.INFORMADO)

    @classmethod
    def get_tomados_ciencia(cls):
        return cls.objects.filter(status=cls.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA)

    @classmethod
    def get_rascunhos_do_usuario(cls, usuario):
        return cls.objects.filter(
            criado_por=usuario, status=cls.workflow_class.RASCUNHO
        )

    @property  # type: ignore
    def quantidades_por_periodo(self):
        return self.quantidades_por_periodo

    @property  # type: ignore
    def suspensoes_alimentacao(self):
        return self.suspensoes_alimentacao

    @property
    def tipo(self):
        return "Suspensão de Alimentação"

    @property
    def path(self):
        return f"suspensao-de-alimentacao/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-normal"

    @property
    def data(self):
        query = self.suspensoes_alimentacao.order_by("data")
        return query.first().data

    @property
    def datas(self):
        return ", ".join(
            [
                data.strftime("%d/%m/%Y")
                for data in self.suspensoes_alimentacao.order_by("data").values_list(
                    "data", flat=True
                )
            ]
        )

    @property
    def numero_alunos(self):
        return self.quantidades_por_periodo.aggregate(Sum("numero_alunos"))[
            "numero_alunos__sum"
        ]

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        datas = list(
            self.suspensoes_alimentacao.order_by("data").values_list("data", flat=True)
        )
        datas = [d.strftime("%d/%m/%Y") for d in datas]
        datas = " ".join(datas)
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome,
            "terceirizada": self.rastro_terceirizada,
            "tipo_doc": "Suspensão de Alimentação",
            "data_evento": datas,
            "numero_alunos": self.numero_alunos,
            "label_data": label_data,
            "data_log": data_log,
            "dias_motivos": self.suspensoes_alimentacao,
            "quantidades_periodo": self.quantidades_por_periodo,
            "datas": self.datas,
            "observacao": self.observacao,
            "id_externo": self.id_externo,
        }

    def __str__(self):
        return f"{self.observacao}"

    @property
    def template_mensagem(self):
        template = TemplateMensagem.objects.get(
            tipo=TemplateMensagem.SUSPENSAO_ALIMENTACAO
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

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            justificativa=justificativa,
            solicitacao_tipo=LogSolicitacoesUsuario.SUSPENSAO_DE_CARDAPIO,
            usuario=usuario,
            uuid_original=self.uuid,
        )

    class Meta:
        verbose_name = "Grupo de suspensão de alimentação"
        verbose_name_plural = "Grupo de suspensão de alimentação"


class SuspensaoAlimentacaoNoPeriodoEscolar(
    ExportModelOperationsMixin("suspensao_periodo_escolar"), TemChaveExterna
):
    suspensao_alimentacao = models.ForeignKey(
        SuspensaoAlimentacao,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="suspensoes_periodo_escolar",
    )
    qtd_alunos = models.PositiveSmallIntegerField(default=0)
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar",
        on_delete=models.PROTECT,
        related_name="suspensoes_periodo_escolar",
    )
    tipos_alimentacao = models.ManyToManyField(
        "TipoAlimentacao", related_name="suspensoes_periodo_escolar"
    )

    def __str__(self):
        return f"Suspensão de alimentação da Alteração de Cardápio: {self.suspensao_alimentacao}"

    class Meta:
        verbose_name = "Suspensão de alimentação no período"
        verbose_name_plural = "Suspensões de alimentação no período"


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


class MotivoDRENaoValida(
    ExportModelOperationsMixin("motivo_dre_nao_valida"), Nomeavel, TemChaveExterna
):
    """Usado em conjunto com Solicitações que passam por validação da DRE.

    Exemplos:
        - Em desacordo com o contrato
        - Preenchimento incorreto
        - Outro

    """

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Motivo de não validação da DRE"
        verbose_name_plural = "Motivos de não validação da DRE"
