from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, Sum
from django_prometheus.models import ExportModelOperationsMixin

from ..cardapio.base.models import (
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from ..dados_comuns.behaviors import (
    CanceladoIndividualmente,
    CriadoEm,
    CriadoPor,
    Descritivel,
    DiasSemana,
    IntervaloDeDia,
    Logs,
    MatriculadosQuandoCriado,
    Nomeavel,
    SolicitacaoForaDoPrazo,
    TemChaveExterna,
    TemData,
    TemIdentificadorExternoAmigavel,
    TemPrioridade,
    TemTerceirizadaConferiuGestaoAlimentacao,
)
from ..dados_comuns.fluxo_status import FluxoAprovacaoPartindoDaEscola
from ..dados_comuns.models import LogSolicitacoesUsuario, TemplateMensagem
from ..escola.constants import (
    PERIODOS_CEMEI_EVENTO_ESPECIFICO,
    PERIODOS_ESPECIAIS_CEMEI,
)
from .managers import (
    GrupoInclusoesDeAlimentacaoNormalDestaSemanaManager,
    GrupoInclusoesDeAlimentacaoNormalDesteMesManager,
    GrupoInclusoesDeAlimentacaoNormalVencidosDiasManager,
    InclusaoDeAlimentacaoCemeiDestaSemanaManager,
    InclusaoDeAlimentacaoCemeiDesteMesManager,
    InclusaoDeAlimentacaoDeCeiDestaSemanaManager,
    InclusaoDeAlimentacaoDeCeiDesteMesManager,
    InclusaoDeAlimentacaoDeCeiVencidosDiasManager,
    InclusoesDeAlimentacaoContinuaDestaSemanaManager,
    InclusoesDeAlimentacaoContinuaDesteMesManager,
    InclusoesDeAlimentacaoContinuaVencidaDiasManager,
)


class QuantidadePorPeriodo(
    ExportModelOperationsMixin("quantidade_periodo"),
    DiasSemana,
    TemChaveExterna,
    CanceladoIndividualmente,
):
    numero_alunos = models.IntegerField(
        null=True,
        blank=True,
    )
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar", on_delete=models.DO_NOTHING
    )
    tipos_alimentacao = models.ManyToManyField("cardapio.TipoAlimentacao")
    observacao = models.CharField("Observação", blank=True, max_length=1000)
    grupo_inclusao_normal = models.ForeignKey(
        "GrupoInclusaoAlimentacaoNormal",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="quantidades_por_periodo",
    )
    inclusao_alimentacao_continua = models.ForeignKey(
        "InclusaoAlimentacaoContinua",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="quantidades_por_periodo",
    )

    def __str__(self):
        qtd = self.tipos_alimentacao.count()
        return f"{self.numero_alunos} alunos para {self.periodo_escolar} com {qtd} tipo(s) de alimentação"

    class Meta:
        verbose_name = "Quantidade por periodo"
        verbose_name_plural = "Quantidades por periodo"


class MotivoInclusaoContinua(
    ExportModelOperationsMixin("motivo_inclusao_continua"), Nomeavel, TemChaveExterna
):
    """Funciona em conjunto com InclusaoAlimentacaoContinua.

    - continuo -  mais educacao
    - continuo-sp integral
    - continuo - outro
    """

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Motivo de inclusao contínua"
        verbose_name_plural = "Motivos de inclusao contínua"


class InclusaoAlimentacaoContinua(
    ExportModelOperationsMixin("inclusao_continua"),
    IntervaloDeDia,
    Descritivel,
    TemChaveExterna,
    FluxoAprovacaoPartindoDaEscola,
    CriadoPor,
    TemIdentificadorExternoAmigavel,
    CriadoEm,
    Logs,
    TemPrioridade,
    SolicitacaoForaDoPrazo,
    TemTerceirizadaConferiuGestaoAlimentacao,
):
    # TODO: noralizar campo de Descritivel: descricao -> observacao
    DESCRICAO = "Inclusão de Alimentação Contínua"

    outro_motivo = models.CharField("Outro motivo", blank=True, max_length=500)
    motivo = models.ForeignKey(MotivoInclusaoContinua, on_delete=models.DO_NOTHING)
    escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.DO_NOTHING,
        related_name="inclusoes_alimentacao_continua",
    )
    objects = models.Manager()  # Manager Padrão
    desta_semana = InclusoesDeAlimentacaoContinuaDestaSemanaManager()
    deste_mes = InclusoesDeAlimentacaoContinuaDesteMesManager()
    vencidos = InclusoesDeAlimentacaoContinuaVencidaDiasManager()

    @property
    def data(self):
        data = self.data_inicial
        if self.data_final < data:
            data = self.data_final
        return data

    @property
    def tipo(self):
        return "Inclusão de Alimentação"

    @property
    def path(self):
        return f"inclusao-de-alimentacao/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-continua"

    @property
    def observacoes(self):
        return ", ".join(
            self.quantidades_periodo.exclude(
                Q(observacao="") | Q(observacao__isnull=True)
            ).values_list("observacao", flat=True)
        )

    @property
    def numero_alunos(self):
        return self.quantidades_por_periodo.aggregate(Sum("numero_alunos"))[
            "numero_alunos__sum"
        ]

    @classmethod
    def get_solicitacoes_rascunho(cls, usuario):
        inclusoes_continuas = cls.objects.filter(
            criado_por=usuario,
            status=InclusaoAlimentacaoContinua.workflow_class.RASCUNHO,
        )
        return inclusoes_continuas

    @property
    def quantidades_periodo(self):
        return self.quantidades_por_periodo

    @property
    def inclusoes(self):
        return self.quantidades_por_periodo

    @property
    def template_mensagem(self):
        template = TemplateMensagem.objects.get(
            tipo=TemplateMensagem.INCLUSAO_ALIMENTACAO_CONTINUA
        )
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
            solicitacao_tipo=LogSolicitacoesUsuario.INCLUSAO_ALIMENTACAO_CONTINUA,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
            resposta_sim_nao=resposta_sim_nao,
        )

    @property
    def quantidades_periodo_simples_dict(self):
        qtd_periodo = []
        for quantidade_periodo in self.quantidades_periodo.all():
            dias_semana = ", ".join(
                [
                    quantidade_periodo.DIAS[dia][1]
                    for dia in quantidade_periodo.dias_semana
                ]
            )
            tipos_alimentacao = ", ".join(
                quantidade_periodo.tipos_alimentacao.all().values_list(
                    "nome", flat=True
                )
            )
            qtd_periodo.append(
                {
                    "periodo": quantidade_periodo.periodo_escolar.nome,
                    "dias_semana": dias_semana,
                    "tipos_alimentacao": tipos_alimentacao,
                    "numero_alunos": quantidade_periodo.numero_alunos,
                    "observacao": quantidade_periodo.observacao,
                    "cancelado": quantidade_periodo.cancelado,
                    "cancelado_justificativa": quantidade_periodo.cancelado_justificativa,
                }
            )
        return qtd_periodo

    @property
    def existe_periodo_cancelado(self):
        return self.quantidades_periodo.all().filter(cancelado=True).exists()

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome,
            "terceirizada": self.rastro_terceirizada,
            "tipo_doc": "Inclusão de Alimentação Contínua",
            "data_inicial": self.data_inicial,
            "data_final": self.data_final,
            "numero_alunos": self.numero_alunos,
            "motivo": self.motivo.nome,
            "outro_motivo": self.outro_motivo,
            "data_inclusao": self.data,
            "quantidades_periodo": self.quantidades_periodo_simples_dict,
            "label_data": label_data,
            "data_log": data_log,
            "id_externo": self.id_externo,
            "existe_periodo_cancelado": self.existe_periodo_cancelado,
            "status": self.status,
        }

    @property
    def solicitacoes_similares(self):
        return []

    def __str__(self):
        return f"de {self.data_inicial} até {self.data_final} para {self.escola}"

    class Meta:
        verbose_name = "Inclusão de alimentação contínua"
        verbose_name_plural = "Inclusões de alimentação contínua"
        ordering = ["data_inicial"]


class MotivoInclusaoNormal(
    ExportModelOperationsMixin("motivo_inclusao_normal"), Nomeavel, TemChaveExterna
):
    """Funciona em conjunto com InclusaoAlimentacaoNormal.

    - reposicao de aula
    - dia de familia
    - outro
    """

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Motivo de inclusao normal"
        verbose_name_plural = "Motivos de inclusao normais"


class InclusaoAlimentacaoNormal(
    ExportModelOperationsMixin("inclusao_normal"),
    TemData,
    TemChaveExterna,
    TemTerceirizadaConferiuGestaoAlimentacao,
    CanceladoIndividualmente,
):
    motivo = models.ForeignKey(MotivoInclusaoNormal, on_delete=models.DO_NOTHING)
    outro_motivo = models.CharField("Outro motivo", blank=True, max_length=500)
    evento = models.CharField("Descrição do Evento", blank=True, max_length=1500)
    grupo_inclusao = models.ForeignKey(
        "GrupoInclusaoAlimentacaoNormal",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="inclusoes_normais",
    )

    def __str__(self):
        if self.outro_motivo:
            return f"Dia {self.data} - Outro motivo: {self.outro_motivo}"
        return f"Dia {self.data} {self.motivo}"

    class Meta:
        verbose_name = "Inclusão de alimentação normal"
        verbose_name_plural = "Inclusões de alimentação normal"
        ordering = ("data",)


class GrupoInclusaoAlimentacaoNormal(
    ExportModelOperationsMixin("grupo_inclusao"),
    Descritivel,
    TemChaveExterna,
    FluxoAprovacaoPartindoDaEscola,
    CriadoEm,
    SolicitacaoForaDoPrazo,
    CriadoPor,
    TemIdentificadorExternoAmigavel,
    Logs,
    TemPrioridade,
    TemTerceirizadaConferiuGestaoAlimentacao,
):
    DESCRICAO = "Inclusão de Alimentação"

    escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.DO_NOTHING,
        related_name="grupos_inclusoes_normais",
    )

    objects = models.Manager()  # Manager Padrão
    desta_semana = GrupoInclusoesDeAlimentacaoNormalDestaSemanaManager()
    deste_mes = GrupoInclusoesDeAlimentacaoNormalDesteMesManager()
    vencidos = GrupoInclusoesDeAlimentacaoNormalVencidosDiasManager()

    @classmethod
    def get_solicitacoes_rascunho(cls, usuario):
        alimentacao_normal = cls.objects.filter(
            criado_por=usuario,
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.RASCUNHO,
        )
        return alimentacao_normal

    @property
    def template_mensagem(self):
        template = TemplateMensagem.objects.get(
            tipo=TemplateMensagem.INCLUSAO_ALIMENTACAO
        )
        template_troca = {
            "@id": self.id_externo,
            "@criado_por": str(self.criado_por),
            "@status": str(self.status),
            # TODO: verificar a url padrão do pedido
            "@link": "http://teste.com",
        }
        corpo = template.template_html
        for chave, valor in template_troca.items():
            corpo = corpo.replace(chave, valor)
        return template.assunto, corpo

    @property
    def data(self):
        inclusao_normal = self.inclusoes_normais.order_by("data").first()
        return inclusao_normal.data if inclusao_normal else ""

    @property
    def datas(self):
        return ", ".join(
            [
                data.strftime("%d/%m/%Y")
                for data in self.inclusoes_normais.order_by("data").values_list(
                    "data", flat=True
                )
            ]
        )

    @property
    def numero_alunos(self):
        return self.quantidades_por_periodo.aggregate(Sum("numero_alunos"))[
            "numero_alunos__sum"
        ]

    @property
    def tipo(self):
        return "Inclusão de Alimentação"

    @property
    def path(self):
        return f"inclusao-de-alimentacao/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-normal"

    @property
    def observacoes(self):
        return ", ".join(
            self.quantidades_periodo.exclude(
                Q(observacao="") | Q(observacao__isnull=True)
            ).values_list("observacao", flat=True)
        )

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        resposta_sim_nao = kwargs.get("resposta_sim_nao", False)
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.INCLUSAO_ALIMENTACAO_NORMAL,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
            resposta_sim_nao=resposta_sim_nao,
        )

    @property
    def inclusoes(self):
        return self.inclusoes_normais

    @property
    def quantidades_periodo(self):
        return self.quantidades_por_periodo

    def adiciona_inclusao_normal(self, inclusao: InclusaoAlimentacaoNormal):
        # TODO: padronizar grupo_inclusao ou grupo_inclusao_normal
        inclusao.grupo_inclusao = self
        inclusao.save()

    def adiciona_quantidade_periodo(self, quantidade_periodo: QuantidadePorPeriodo):
        # TODO: padronizar grupo_inclusao ou grupo_inclusao_normal
        quantidade_periodo.grupo_inclusao_normal = self
        quantidade_periodo.save()

    @property
    def inclusoes_simples_dict(self):
        inclusoes = []
        for inclusao in self.inclusoes_normais.all():
            inclusoes.append(
                {
                    "motivo": inclusao.motivo.nome,
                    "outro_motivo": inclusao.outro_motivo,
                    "evento": inclusao.evento,
                    "data": inclusao.data,
                    "cancelado": inclusao.cancelado,
                    "cancelado_justificativa": inclusao.cancelado_justificativa,
                }
            )
        return inclusoes

    @property
    def quantidades_periodo_simples_dict(self):
        quantidades_periodo = []
        for quantidade_periodo in self.quantidades_periodo.all():
            tipos_alimentacao = ", ".join(
                quantidade_periodo.tipos_alimentacao.all().values_list(
                    "nome", flat=True
                )
            )
            quantidades_periodo.append(
                {
                    "periodo": quantidade_periodo.periodo_escolar.nome,
                    "numero_alunos": quantidade_periodo.numero_alunos,
                    "tipos_alimentacao": tipos_alimentacao,
                }
            )
        return quantidades_periodo

    @property
    def existe_dia_cancelado(self):
        return self.inclusoes_normais.all().filter(cancelado=True).exists()

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome,
            "terceirizada": self.rastro_terceirizada,
            "tipo_doc": "Inclusão de Alimentação",
            "data_evento": self.data,
            "numero_alunos": self.numero_alunos,
            "dias_inclusao": self.data,
            "inclusoes": self.inclusoes_simples_dict,
            "quantidades_periodo": self.quantidades_periodo_simples_dict,
            "label_data": label_data,
            "data_log": data_log,
            "datas": self.datas,
            "id_externo": self.id_externo,
            "existe_dia_cancelado": self.existe_dia_cancelado,
            "status": self.status,
        }

    @property
    def solicitacoes_similares(self):
        MOTIVOS_PERMITIDOS = [
            "Dia da família",
            "Reposição de aula",
            "Outro",
        ]

        if (
            self.status == GrupoInclusaoAlimentacaoNormal.workflow_class.RASCUNHO
            or any(
                [
                    motivo not in MOTIVOS_PERMITIDOS
                    for motivo in self.inclusoes_normais.values_list(
                        "motivo__nome", flat=True
                    )
                ]
            )
        ):
            return []

        queryset = GrupoInclusaoAlimentacaoNormal.objects.filter(
            escola=self.escola,
        )
        queryset = queryset.filter(
            inclusoes_normais__motivo__nome__in=MOTIVOS_PERMITIDOS,
        )
        queryset = queryset.filter(
            inclusoes_normais__data__in=self.inclusoes_normais.values_list(
                "data", flat=True
            ),
        )

        return queryset.distinct().exclude(
            Q(id=self.id)
            | Q(status=GrupoInclusaoAlimentacaoNormal.workflow_class.RASCUNHO)
        )

    def __str__(self):
        return f"{self.escola} pedindo {self.inclusoes.count()} inclusoes"

    class Meta:
        verbose_name = "Grupo de inclusão de alimentação normal"
        verbose_name_plural = "Grupos de inclusão de alimentação normal"


class QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEI(
    TemChaveExterna, MatriculadosQuandoCriado
):
    inclusao_alimentacao_da_cei = models.ForeignKey(
        "InclusaoAlimentacaoDaCEI",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="quantidade_alunos_da_inclusao",
    )
    faixa_etaria = models.ForeignKey("escola.FaixaEtaria", on_delete=models.DO_NOTHING)
    quantidade_alunos = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )
    periodo = models.ForeignKey(
        "escola.PeriodoEscolar", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    periodo_externo = models.ForeignKey(
        "escola.PeriodoEscolar",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="periodo_externo",
    )

    def __str__(self):
        return f"De: {self.faixa_etaria.inicio} até: {self.faixa_etaria.fim} meses - {self.quantidade_alunos} alunos"

    class Meta:
        verbose_name = (
            "Quantidade de alunos por faixa etária da inclusao de alimentação"
        )
        verbose_name_plural = (
            "Quantidade de alunos por faixa etária da inclusao de alimentação"
        )


class InclusaoAlimentacaoDaCEI(
    Descritivel,
    TemChaveExterna,
    FluxoAprovacaoPartindoDaEscola,
    CriadoEm,
    SolicitacaoForaDoPrazo,
    CriadoPor,
    TemIdentificadorExternoAmigavel,
    Logs,
    TemPrioridade,
    TemTerceirizadaConferiuGestaoAlimentacao,
):
    DESCRICAO = "Inclusão de Alimentação Por CEI"

    escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.DO_NOTHING,
        related_name="grupos_inclusoes_por_cei",
    )
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    tipos_alimentacao = models.ManyToManyField("cardapio.TipoAlimentacao")

    objects = models.Manager()  # Manager Padrão
    desta_semana = InclusaoDeAlimentacaoDeCeiDestaSemanaManager()
    deste_mes = InclusaoDeAlimentacaoDeCeiDesteMesManager()
    vencidos = InclusaoDeAlimentacaoDeCeiVencidosDiasManager()

    @property
    def data(self):
        dia_motivo = self.dias_motivos_da_inclusao_cei.order_by("data").first()
        return dia_motivo.data if dia_motivo else ""

    @property
    def datas(self):
        return ", ".join(
            [
                data.strftime("%d/%m/%Y")
                for data in self.dias_motivos_da_inclusao_cei.order_by(
                    "data"
                ).values_list("data", flat=True)
            ]
        )

    @property
    def numero_alunos(self):
        return self.quantidade_alunos_da_inclusao.aggregate(Sum("quantidade_alunos"))[
            "quantidade_alunos__sum"
        ]

    @property
    def tipo(self):
        return "Inclusão de Alimentação"

    @property
    def path(self):
        return f"inclusao-de-alimentacao/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-cei"

    @property
    def observacao(self):
        return None

    @property
    def inclusoes(self):
        return self.dias_motivos_da_inclusao_cei

    @property
    def quantidade_alunos_por_faixas_etarias(self):
        return self.quantidade_alunos_da_inclusao

    def adiciona_inclusao_a_quantidade_por_faixa_etaria(
        self,
        quantidade_por_faixa_etaria: QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEI,
    ):
        quantidade_por_faixa_etaria.inclusao_alimentacao_da_cei = self
        quantidade_por_faixa_etaria.save()

    @classmethod
    def get_solicitacoes_rascunho(cls, usuario):
        alimentacao_normal = cls.objects.filter(
            criado_por=usuario, status=InclusaoAlimentacaoDaCEI.workflow_class.RASCUNHO
        )
        return alimentacao_normal

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        resposta_sim_nao = kwargs.get("resposta_sim_nao", False)
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.INCLUSAO_ALIMENTACAO_CEI,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
            resposta_sim_nao=resposta_sim_nao,
        )

    @property
    def quantidade_alunos_por_faixas_etarias_simples_dict(self):
        escola = self.rastro_escola
        qa = self.quantidade_alunos_por_faixas_etarias
        vinculos_class = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar
        inclusoes = []
        for periodo_externo in self.periodos_da_solicitacao(
            nivel_interno=False, nome_coluna="periodo_externo"
        ):
            inclusao = {"periodo_externo_nome": periodo_externo}
            vinculo = vinculos_class.objects.filter(
                periodo_escolar__nome=periodo_externo,
                ativo=True,
                tipo_unidade_escolar=escola.tipo_unidade,
            ).first()
            if vinculo:
                inclusao["tipos_alimentacao"] = ", ".join(
                    vinculo.tipos_alimentacao.values_list("nome", flat=True)
                )
            else:
                inclusao["tipos_alimentacao"] = ""
            if periodo_externo == "INTEGRAL":
                inclusao["periodos_internos"] = []
                for periodo_interno in self.periodos_da_solicitacao(
                    nivel_interno=True, nome_coluna="periodo"
                ):
                    p_faixas = qa.filter(
                        periodo__nome=periodo_interno,
                        periodo_externo__nome=periodo_externo,
                    )
                    total_inclusao = sum(
                        p_faixas.exclude(quantidade_alunos=None).values_list(
                            "quantidade_alunos", flat=True
                        )
                    )
                    total_matriculados = sum(
                        p_faixas.exclude(matriculados_quando_criado=None).values_list(
                            "matriculados_quando_criado", flat=True
                        )
                    )
                    p_faixas = [
                        {
                            "nome_faixa": x.faixa_etaria.__str__(),
                            "quantidade_alunos": x.quantidade_alunos,
                            "matriculados_quando_criado": x.matriculados_quando_criado,
                        }
                        for x in p_faixas
                    ]
                    inclusao["periodos_internos"].append(
                        {
                            "periodo_interno_nome": periodo_interno,
                            "quantidades_faixas": p_faixas,
                            "total_inclusao": total_inclusao,
                            "total_matriculados": total_matriculados,
                        }
                    )
            else:
                p_faixas = qa.filter(
                    periodo__nome=periodo_externo, periodo_externo__nome=periodo_externo
                )
                total_inclusao = sum(
                    p_faixas.values_list("quantidade_alunos", flat=True)
                )
                total_matriculados = sum(
                    p_faixas.values_list("matriculados_quando_criado", flat=True)
                )
                p_faixas = [
                    {
                        "nome_faixa": x.faixa_etaria.__str__(),
                        "quantidade_alunos": x.quantidade_alunos,
                        "matriculados_quando_criado": x.matriculados_quando_criado,
                    }
                    for x in p_faixas
                ]
                inclusao["quantidades_faixas"] = p_faixas
                inclusao["total_inclusao"] = total_inclusao
                inclusao["total_matriculados"] = total_matriculados
            inclusoes.append(inclusao)
        return inclusoes

    @property
    def dias_motivos_da_inclusao_cei_simples_dict(self):
        dias_motivos_da_inclusao_cei = []
        for inclusao_cei in self.dias_motivos_da_inclusao_cei.all():
            dias_motivos_da_inclusao_cei.append(
                {
                    "motivo": inclusao_cei.motivo.nome,
                    "data": inclusao_cei.data,
                    "cancelado": inclusao_cei.cancelado,
                    "cancelado_justificativa": inclusao_cei.cancelado_justificativa,
                }
            )
        return dias_motivos_da_inclusao_cei

    @property
    def existe_dia_cancelado(self):
        return self.dias_motivos_da_inclusao_cei.all().filter(cancelado=True).exists()

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        periodos_externos = self.quantidade_alunos_por_faixas_etarias.values_list(
            "periodo_externo__nome", flat=True
        ).distinct()
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome,
            "terceirizada": self.rastro_terceirizada,
            "tipo_doc": "Inclusão de Alimentação CEI",
            "data_evento": self.data,
            "datas": self.datas,
            "numero_alunos": self.numero_alunos,
            "dias_inclusao": self.datas,
            "dias_motivos_da_inclusao_cei": self.dias_motivos_da_inclusao_cei_simples_dict,
            "quantidade_alunos_por_faixas_etarias": self.quantidade_alunos_por_faixas_etarias_simples_dict,
            "label_data": label_data,
            "data_log": data_log,
            "periodos_externos": periodos_externos,
            "id_externo": self.id_externo,
            "existe_dia_cancelado": self.existe_dia_cancelado,
            "status": self.status,
        }

    def periodos_da_solicitacao(self, nivel_interno, nome_coluna):
        qa = self.quantidade_alunos_da_inclusao
        if nivel_interno:
            qa = qa.filter(periodo_externo__nome="INTEGRAL")
        return (
            qa.order_by(f"{nome_coluna}__posicao")
            .values_list(f"{nome_coluna}__nome", flat=True)
            .distinct()
        )

    @property
    def solicitacoes_similares(self):
        MOTIVOS_PERMITIDOS = [
            "Dia da família",
            "Reposição de aula",
            "Outro",
        ]

        if self.status == InclusaoAlimentacaoDaCEI.workflow_class.RASCUNHO or any(
            [
                motivo not in MOTIVOS_PERMITIDOS
                for motivo in self.inclusoes.values_list("motivo__nome", flat=True)
            ]
        ):
            return []

        queryset = InclusaoAlimentacaoDaCEI.objects.filter(escola=self.escola)
        queryset = queryset.filter(
            dias_motivos_da_inclusao_cei__motivo__nome__in=MOTIVOS_PERMITIDOS
        )
        queryset = queryset.filter(
            dias_motivos_da_inclusao_cei__data__in=self.inclusoes.values_list(
                "data", flat=True
            )
        )

        return queryset.distinct().exclude(
            Q(id=self.id) | Q(status=InclusaoAlimentacaoDaCEI.workflow_class.RASCUNHO)
        )

    def __str__(self):
        return f"Inclusao da CEI cód: {self.id_externo}"

    class Meta:
        verbose_name = "Inclusão de alimentação da CEI"
        verbose_name_plural = "Inclusões de alimentação da CEI"


class DiasMotivosInclusaoDeAlimentacaoCEI(
    TemData, TemChaveExterna, CanceladoIndividualmente
):
    inclusao_cei = models.ForeignKey(
        "InclusaoAlimentacaoDaCEI",
        on_delete=models.CASCADE,
        related_name="dias_motivos_da_inclusao_cei",
    )
    motivo = models.ForeignKey(MotivoInclusaoNormal, on_delete=models.DO_NOTHING)
    outro_motivo = models.CharField("Outro motivo", blank=True, max_length=500)

    def __str__(self):
        if self.outro_motivo:
            return f"Dia {self.data} - Outro motivo: {self.outro_motivo}"
        return f"Dia {self.data} {self.motivo}"

    class Meta:
        verbose_name = "Dia e motivo inclusão de alimentação CEI"
        verbose_name_plural = "Dias e motivos inclusão de alimentação CEI"
        ordering = ("data",)


class InclusaoDeAlimentacaoCEMEI(
    Descritivel,
    TemChaveExterna,
    FluxoAprovacaoPartindoDaEscola,
    CriadoEm,
    Logs,
    SolicitacaoForaDoPrazo,
    CriadoPor,
    TemIdentificadorExternoAmigavel,
    TemPrioridade,
    TemTerceirizadaConferiuGestaoAlimentacao,
):
    DESCRICAO = "Inclusão de Alimentação CEMEI"

    escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.DO_NOTHING,
        related_name="inclusoes_de_alimentacao_cemei",
    )

    objects = models.Manager()  # Manager Padrão
    desta_semana = InclusaoDeAlimentacaoCemeiDestaSemanaManager()
    deste_mes = InclusaoDeAlimentacaoCemeiDesteMesManager()

    @property
    def data(self):
        dia_motivo = self.dias_motivos_da_inclusao_cemei.order_by("data").first()
        return dia_motivo.data if dia_motivo else ""

    @property
    def datas(self):
        return ", ".join(
            [
                data.strftime("%d/%m/%Y")
                for data in self.dias_motivos_da_inclusao_cemei.order_by(
                    "data"
                ).values_list("data", flat=True)
            ]
        )

    @property
    def observacao(self):
        return None

    @property
    def tipo(self):
        return "Inclusão de Alimentação"

    @property
    def path(self):
        return f"inclusao-de-alimentacao-cemei/relatorio?uuid={self.uuid}"

    @property
    def numero_alunos(self):
        total = 0
        total += (
            self.quantidade_alunos_emei_da_inclusao_cemei.aggregate(
                Sum("quantidade_alunos")
            )["quantidade_alunos__sum"]
            or 0
        )
        total += (
            self.quantidade_alunos_cei_da_inclusao_cemei.aggregate(
                Sum("quantidade_alunos")
            )["quantidade_alunos__sum"]
            or 0
        )
        return total

    @property
    def inclusoes(self):
        return self.dias_motivos_da_inclusao_cemei

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        resposta_sim_nao = kwargs.get("resposta_sim_nao", False)
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.INCLUSAO_ALIMENTACAO_CEMEI,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
            resposta_sim_nao=resposta_sim_nao,
        )

    @property
    def dias_motivos_da_inclusao_cemei_simples_dict(self):
        dias_motivos_da_inclusao_cemei = []
        for inclusao_cemei in self.dias_motivos_da_inclusao_cemei.all():
            dias_motivos_da_inclusao_cemei.append(
                {
                    "motivo": inclusao_cemei.motivo.nome,
                    "data": inclusao_cemei.data,
                    "cancelado": inclusao_cemei.cancelado,
                    "cancelado_justificativa": inclusao_cemei.cancelado_justificativa,
                    "descricao_evento": inclusao_cemei.descricao_evento,
                }
            )
        return dias_motivos_da_inclusao_cemei

    @property
    def existe_dia_cancelado(self):
        return self.dias_motivos_da_inclusao_cemei.all().filter(cancelado=True).exists()

    def eh_evento_especifico(self):
        if self.dias_motivos_da_inclusao_cemei.filter(motivo__nome="Evento Específico"):
            return True
        return False

    def checa_tipos_alimentacao_emei(self, quantidades_emei, tipos_alimentacao_emei):
        if quantidades_emei and quantidades_emei[0].tipos_alimentacao.all():
            tipos_alimentacao_emei = ", ".join(
                quantidades_emei[0]
                .tipos_alimentacao.all()
                .values_list("nome", flat=True)
            )
        return tipos_alimentacao_emei

    @property
    def quantidades_alunos_simples_dict(self):
        dias_motivos_da_inclusao = []
        eh_evento_especifico = self.eh_evento_especifico()
        periodos_cei = self.quantidade_alunos_cei_da_inclusao_cemei.all()
        periodos_cei = periodos_cei.values_list(
            "periodo_escolar__nome", flat=True
        ).distinct()
        periodos_emei = self.quantidade_alunos_emei_da_inclusao_cemei.all()
        periodos_emei = periodos_emei.values_list(
            "periodo_escolar__nome", flat=True
        ).distinct()
        periodos = list(periodos_cei) + list(periodos_emei)
        periodos = list(set(periodos))
        escola = self.rastro_escola
        vinculos = (
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                periodo_escolar__in=escola.periodos_escolares(), ativo=True
            ).order_by("periodo_escolar__posicao")
        )
        vinculos = (
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                periodo_escolar__nome__in=PERIODOS_ESPECIAIS_CEMEI,
                tipo_unidade_escolar__iniciais__in=["CEI DIRET", "EMEI"],
            )
        )

        if eh_evento_especifico:
            vinculos = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                periodo_escolar__nome__in=PERIODOS_CEMEI_EVENTO_ESPECIFICO,
                tipo_unidade_escolar__iniciais__in=["CEI DIRET", "EMEI"],
            )

        for periodo in periodos:
            tipos_alimentacao_cei = vinculos.filter(
                periodo_escolar__nome=periodo,
                tipo_unidade_escolar__iniciais="CEI DIRET",
            )

            tipos_alimentacao_cei = tipos_alimentacao_cei.values_list(
                "tipos_alimentacao__nome", flat=True
            )
            tipos_alimentacao_cei = [ta for ta in tipos_alimentacao_cei if ta]
            tipos_alimentacao_cei = ", ".join(tipos_alimentacao_cei)

            tipos_alimentacao_emei = vinculos.filter(
                periodo_escolar__nome=periodo, tipo_unidade_escolar__iniciais="EMEI"
            )
            if eh_evento_especifico and not self.escola.periodos_escolares().filter(
                nome=periodo
            ):
                tipos_alimentacao_emei = vinculos.filter(
                    periodo_escolar__nome="INTEGRAL",
                    tipo_unidade_escolar__iniciais="EMEI",
                )

            tipos_alimentacao_emei = tipos_alimentacao_emei.values_list(
                "tipos_alimentacao__nome", flat=True
            )
            tipos_alimentacao_emei = [ta for ta in tipos_alimentacao_emei if ta]
            tipos_alimentacao_emei = ", ".join(tipos_alimentacao_emei)

            quantidades_cei = self.quantidade_alunos_cei_da_inclusao_cemei.filter(
                periodo_escolar__nome=periodo
            )
            quantidades_emei = self.quantidade_alunos_emei_da_inclusao_cemei.filter(
                periodo_escolar__nome=periodo
            )
            tipos_alimentacao_emei = self.checa_tipos_alimentacao_emei(
                quantidades_emei, tipos_alimentacao_emei
            )
            quantidades_cei_list = []
            quantidades_emei_list = []
            total_matriculados_cei = 0
            total_alunos_cei = 0
            for qc in quantidades_cei:
                total_matriculados_cei += qc.matriculados_quando_criado
                total_alunos_cei += qc.quantidade_alunos
                quantidades_cei_list.append(
                    {
                        "faixa_etaria": qc.faixa_etaria.__str__,
                        "quantidade_alunos": qc.quantidade_alunos,
                        "matriculados_quando_criado": qc.matriculados_quando_criado,
                    }
                )
            for qe in quantidades_emei:
                quantidades_emei_list.append(
                    {
                        "quantidade_alunos": qe.quantidade_alunos,
                        "matriculados_quando_criado": qe.matriculados_quando_criado,
                    }
                )
            dias_motivos_da_inclusao.append(
                {
                    "periodo": periodo,
                    "tipos_alimentacao_cei": tipos_alimentacao_cei,
                    "quantidades_cei": quantidades_cei_list,
                    "total_matriculados_cei": total_matriculados_cei,
                    "total_alunos_cei": total_alunos_cei,
                    "tipos_alimentacao_emei": tipos_alimentacao_emei,
                    "quantidades_emei": quantidades_emei,
                }
            )
        return dias_motivos_da_inclusao

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        eh_evento_especifico = self.dias_motivos_da_inclusao_cemei.filter(
            motivo__nome="Evento Específico"
        ).exists()
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome,
            "terceirizada": self.rastro_terceirizada,
            "tipo_doc": "Inclusão de Alimentação CEMEI",
            "data_evento": self.data,
            "numero_alunos": self.numero_alunos,
            "dias_motivos_da_inclusao_cemei": self.dias_motivos_da_inclusao_cemei_simples_dict,
            "quantidades_alunos": self.quantidades_alunos_simples_dict,
            "label_data": label_data,
            "data_log": data_log,
            "datas": self.datas,
            "id_externo": self.id_externo,
            "existe_dia_cancelado": self.existe_dia_cancelado,
            "status": self.status,
            "eh_evento_especifico": eh_evento_especifico,
        }

    @property
    def solicitacoes_similares(self):
        MOTIVOS_PERMITIDOS = [
            "Dia da família",
            "Reposição de aula",
            "Outro",
        ]

        if self.status == InclusaoDeAlimentacaoCEMEI.workflow_class.RASCUNHO or any(
            [
                motivo not in MOTIVOS_PERMITIDOS
                for motivo in self.inclusoes.values_list("motivo__nome", flat=True)
            ]
        ):
            return []

        queryset = InclusaoDeAlimentacaoCEMEI.objects.filter(escola=self.escola)
        queryset = queryset.filter(
            dias_motivos_da_inclusao_cemei__motivo__nome__in=MOTIVOS_PERMITIDOS
        )
        queryset = queryset.filter(
            dias_motivos_da_inclusao_cemei__data__in=self.inclusoes.values_list(
                "data", flat=True
            )
        )

        return queryset.distinct().exclude(
            Q(id=self.id) | Q(status=InclusaoDeAlimentacaoCEMEI.workflow_class.RASCUNHO)
        )

    def __str__(self):
        return f"Inclusão de Alimentação CEMEI cód: {self.id_externo}"

    class Meta:
        verbose_name = "Inclusão de alimentação CEMEI"
        verbose_name_plural = "Inclusões de alimentação CEMEI"


class QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEI(
    TemChaveExterna, MatriculadosQuandoCriado
):
    inclusao_alimentacao_cemei = models.ForeignKey(
        "InclusaoDeAlimentacaoCEMEI",
        on_delete=models.CASCADE,
        related_name="quantidade_alunos_cei_da_inclusao_cemei",
    )
    faixa_etaria = models.ForeignKey("escola.FaixaEtaria", on_delete=models.DO_NOTHING)
    quantidade_alunos = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar", on_delete=models.DO_NOTHING
    )

    def __str__(self):
        return f"De: {self.faixa_etaria.inicio} até: {self.faixa_etaria.fim} meses - {self.quantidade_alunos} alunos"

    class Meta:
        verbose_name = (
            "Quantidade de alunos por faixa etária da inclusao de alimentação CEMEI"
        )
        verbose_name_plural = (
            "Quantidade de alunos por faixa etária da inclusao de alimentação CEMEI"
        )


class QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI(
    TemChaveExterna, MatriculadosQuandoCriado
):
    inclusao_alimentacao_cemei = models.ForeignKey(
        "InclusaoDeAlimentacaoCEMEI",
        on_delete=models.CASCADE,
        related_name="quantidade_alunos_emei_da_inclusao_cemei",
    )
    quantidade_alunos = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar", on_delete=models.DO_NOTHING
    )
    tipos_alimentacao = models.ManyToManyField("cardapio.TipoAlimentacao")

    def __str__(self):
        return f"{self.periodo_escolar.nome} - {self.quantidade_alunos} alunos"

    class Meta:
        verbose_name = "Quantidade de alunos EMEI por inclusao de alimentação CEMEI"
        verbose_name_plural = (
            "Quantidade de alunos EMEI por inclusao de alimentação CEMEI"
        )


class DiasMotivosInclusaoDeAlimentacaoCEMEI(
    TemData, TemChaveExterna, CanceladoIndividualmente
):
    inclusao_alimentacao_cemei = models.ForeignKey(
        "InclusaoDeAlimentacaoCEMEI",
        on_delete=models.CASCADE,
        related_name="dias_motivos_da_inclusao_cemei",
    )
    motivo = models.ForeignKey(MotivoInclusaoNormal, on_delete=models.DO_NOTHING)
    outro_motivo = models.CharField("Outro motivo", blank=True, max_length=500)
    descricao_evento = models.CharField(
        "Descrição do Evento", blank=True, max_length=1500
    )

    def __str__(self):
        if self.outro_motivo:
            return f"Dia {self.data} - Outro motivo: {self.outro_motivo}"
        return f"Dia {self.data} {self.motivo}"

    class Meta:
        verbose_name = "Diaa e motivo inclusão de alimentação CEMEI"
        verbose_name_plural = "Dias e motivos inclusçao de alimentação CEMEI"
        ordering = ("data",)
