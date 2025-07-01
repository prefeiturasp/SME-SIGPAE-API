import datetime
import unicodedata
from calendar import monthcalendar, setfirstweekday

import numpy
from django.db import models

from ..dados_comuns.behaviors import (
    Ativavel,
    CriadoEm,
    CriadoPor,
    Logs,
    Nomeavel,
    Posicao,
    TemAlteradoEm,
    TemAno,
    TemChaveExterna,
    TemData,
    TemDia,
    TemIdentificadorExternoAmigavel,
    TemMes,
    TemSemana,
)
from ..dados_comuns.fluxo_status import (
    FluxoRelatorioFinanceiroMedicaoInicial,
    FluxoSolicitacaoMedicaoInicial,
    LogSolicitacoesUsuario,
)
from ..escola.constants import INFANTIL_OU_FUNDAMENTAL
from ..escola.models import PeriodoEscolar, TipoUnidadeEscolar
from ..perfil.models import Usuario
from ..terceirizada.models import Edital


class DiaSobremesaDoce(TemData, TemChaveExterna, CriadoEm, CriadoPor):
    tipo_unidade = models.ForeignKey(TipoUnidadeEscolar, on_delete=models.CASCADE)
    edital = models.ForeignKey(Edital, on_delete=models.CASCADE, blank=True, null=True)

    @property
    def tipo_unidades(self):
        return None

    @property
    def cadastros_calendario(self):
        return None

    def __str__(self):
        return f'{self.data.strftime("%d/%m/%Y")} - {self.tipo_unidade.iniciais} - Edital {self.edital}'

    class Meta:
        verbose_name = "Dia de sobremesa doce"
        verbose_name_plural = "Dias de sobremesa doce"
        unique_together = (
            "tipo_unidade",
            "data",
            "edital",
        )
        ordering = ("data",)


class SolicitacaoMedicaoInicial(
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
    CriadoEm,
    CriadoPor,
    TemMes,
    TemAno,
    FluxoSolicitacaoMedicaoInicial,
    Logs,
):
    """Solicitação de Medição Inicial."""

    escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.CASCADE,
        related_name="solicitacoes_medicao_inicial",
    )
    tipos_contagem_alimentacao = models.ManyToManyField(
        "TipoContagemAlimentacao", related_name="solicitacoes_medicao_inicial"
    )
    com_ocorrencias = models.BooleanField("Com ocorrências?", default=False)
    historico = models.JSONField(blank=True, null=True)
    ue_possui_alunos_periodo_parcial = models.BooleanField(
        "Possui alunos periodo parcial?", default=False
    )
    logs_salvos = models.BooleanField(
        "Logs de matriculados, dietas autorizadas, etc foram salvos?", default=False
    )
    dre_ciencia_correcao_data = models.DateTimeField(blank=True, null=True)
    dre_ciencia_correcao_usuario = models.ForeignKey(
        "perfil.Usuario",
        on_delete=models.SET_NULL,
        related_name="solicitacoes_medicao_ciencia_correcao",
        blank=True,
        null=True,
    )
    relatorio_financeiro = models.ForeignKey(
        "RelatorioFinanceiro",
        on_delete=models.SET_NULL,
        related_name="solicitacoes_medicao_inicial",
        blank=True,
        null=True,
    )

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
        )

    def cria_medicoes_dos_periodos(self) -> None:
        periodos_escolares = self.escola.periodos_escolares(self.ano)
        if not periodos_escolares:
            return
        for periodo_escolar in periodos_escolares:
            Medicao.objects.get_or_create(
                solicitacao_medicao_inicial=self, periodo_escolar=periodo_escolar
            )

    @property
    def escola_cei_com_inclusao_parcial_autorizada(self):
        if not self.escola.eh_cei:
            return False
        return self.escola.inclusao_alimentacao_inclusaoalimentacaodacei_rastro_escola.filter(
            status="CODAE_AUTORIZADO",
            quantidade_alunos_da_inclusao__periodo_externo__nome="INTEGRAL",
            quantidade_alunos_da_inclusao__periodo__nome__in=["TARDE", "MANHA"],
            dias_motivos_da_inclusao_cei__data__month=self.mes,
            dias_motivos_da_inclusao_cei__data__year=self.ano,
            dias_motivos_da_inclusao_cei__cancelado=False,
        ).exists()

    @property
    def todas_medicoes_e_ocorrencia_aprovados_por_medicao(self):
        ocorrencia_aprovada = True
        if self.tem_ocorrencia:
            ocorrencia_aprovada = (
                self.ocorrencia.status
                == self.ocorrencia.workflow_class.MEDICAO_APROVADA_PELA_CODAE
            )
        todas_medicoes_aprovadas = not self.medicoes.exclude(
            status="MEDICAO_APROVADA_PELA_CODAE"
        ).exists()
        return ocorrencia_aprovada and todas_medicoes_aprovadas

    @property
    def assinatura_ue(self):
        try:
            log_enviado_ue = self.logs.get(
                status_evento=LogSolicitacoesUsuario.MEDICAO_ENVIADA_PELA_UE
            )
            assinatura_escola = None
            if log_enviado_ue:
                razao_social = (
                    self.rastro_terceirizada.razao_social
                    if self.rastro_terceirizada
                    else ""
                )
                usuario_escola = log_enviado_ue.usuario
                data_enviado_ue = log_enviado_ue.criado_em.strftime("%d/%m/%Y às %H:%M")
                assinatura_escola = f"""Documento conferido e registrado eletronicamente por {usuario_escola.nome},
                                        {usuario_escola.cargo}, {usuario_escola.registro_funcional},
                                        {self.escola.nome} em {data_enviado_ue}. O registro eletrônico da Medição
                                        Inicial é comprovação e ateste do serviço prestado à Unidade Educacional,
                                        pela empresa {razao_social}."""
            return assinatura_escola
        except LogSolicitacoesUsuario.DoesNotExist:
            return None

    @property
    def assinatura_dre(self):
        log_aprovado_dre = self.logs.filter(
            status_evento=LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_DRE
        ).last()
        if not log_aprovado_dre:
            return None
        usuario_dre = self.dre_ciencia_correcao_usuario or log_aprovado_dre.usuario
        data_aprovado_dre = (
            self.dre_ciencia_correcao_data or log_aprovado_dre.criado_em
        ).strftime("%d/%m/%Y às %H:%M")
        assinatura_dre = f"""Documento conferido e aprovado eletronicamente por {usuario_dre.nome},
                             {usuario_dre.cargo}, {usuario_dre.registro_funcional},
                             {self.rastro_lote.diretoria_regional.nome} em {data_aprovado_dre}."""
        return assinatura_dre

    @property
    def tem_ocorrencia(self):
        return hasattr(self, "ocorrencia")

    @property
    def get_medicao_programas_e_projetos(self):
        try:
            return self.medicoes.get(grupo__nome="Programas e Projetos")
        except Medicao.DoesNotExist:
            return None

    @property
    def get_medicao_etec(self):
        try:
            return self.medicoes.get(grupo__nome="ETEC")
        except Medicao.DoesNotExist:
            return None

    def get_or_create_medicao_por_periodo_e_ou_grupo(self, periodo_e_ou_grupo: str):
        if GrupoMedicao.objects.filter(nome=periodo_e_ou_grupo).exists():
            grupo = GrupoMedicao.objects.get(nome=periodo_e_ou_grupo)
            medicao, created = Medicao.objects.get_or_create(
                solicitacao_medicao_inicial=self, grupo=grupo
            )
            return medicao
        else:
            periodo_escolar = PeriodoEscolar.objects.get(nome=periodo_e_ou_grupo)
            medicao, created = Medicao.objects.get_or_create(
                solicitacao_medicao_inicial=self, periodo_escolar=periodo_escolar
            )
            return medicao

    def get_medicao_por_periodo_e_ou_grupo(self, periodo_e_ou_grupo: str):
        try:
            if GrupoMedicao.objects.filter(nome=periodo_e_ou_grupo).exists():
                grupo = GrupoMedicao.objects.get(nome=periodo_e_ou_grupo)
                medicao = Medicao.objects.get(
                    solicitacao_medicao_inicial=self, grupo=grupo
                )
                return medicao
            else:
                periodo_escolar = PeriodoEscolar.objects.get(nome=periodo_e_ou_grupo)
                medicao = Medicao.objects.get(
                    solicitacao_medicao_inicial=self, periodo_escolar=periodo_escolar
                )
            return medicao
        except Medicao.DoesNotExist:
            return None

    class Meta:
        verbose_name = "Solicitação de medição inicial"
        verbose_name_plural = "Solicitações de medição inicial"
        unique_together = (
            "escola",
            "mes",
            "ano",
        )
        ordering = ("-ano", "-mes")

    def __str__(self):
        return f"Solicitação #{self.id_externo} -- Escola {self.escola.nome} -- {self.mes}/{self.ano}"


class OcorrenciaMedicaoInicial(TemChaveExterna, Logs, FluxoSolicitacaoMedicaoInicial):
    """Modelo para mapear a tabela Ocorrência e salvar objetos ocorrêcia da medição inicial."""

    nome_ultimo_arquivo = models.CharField(max_length=100)
    ultimo_arquivo = models.FileField()
    solicitacao_medicao_inicial = models.OneToOneField(
        SolicitacaoMedicaoInicial,
        on_delete=models.CASCADE,
        related_name="ocorrencia",
        blank=True,
        null=True,
    )

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        log_transicao = LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            justificativa=justificativa,
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
            usuario=usuario,
            uuid_original=self.uuid,
        )
        return log_transicao

    def deletar_log_correcao(self, status_evento, **kwargs):
        log = self.logs.last()
        if log and log.status_evento in status_evento:
            log.delete()

    def __str__(self):
        return f"Ocorrência {self.uuid} da Solicitação de Medição Inicial {self.solicitacao_medicao_inicial.uuid}"


class Responsavel(models.Model):
    nome = models.CharField("Nome", max_length=100)
    rf = models.CharField(max_length=10)
    solicitacao_medicao_inicial = models.ForeignKey(
        SolicitacaoMedicaoInicial, related_name="responsaveis", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"Responsável {self.nome} - {self.rf}"


class TipoContagemAlimentacao(Nomeavel, TemChaveExterna, Ativavel):
    class Meta:
        verbose_name = "Tipo de contagem das alimentações"
        verbose_name_plural = "Tipos de contagem das alimentações"

    def __str__(self):
        return self.nome


class GrupoMedicao(Nomeavel, TemChaveExterna, Ativavel):
    class Meta:
        verbose_name = "Grupo de medição"
        verbose_name_plural = "Grupos de medição"

    def __str__(self):
        return self.nome


class Medicao(
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
    FluxoSolicitacaoMedicaoInicial,
    CriadoEm,
    CriadoPor,
    Logs,
):
    solicitacao_medicao_inicial = models.ForeignKey(
        "SolicitacaoMedicaoInicial", on_delete=models.CASCADE, related_name="medicoes"
    )
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar", blank=True, null=True, on_delete=models.DO_NOTHING
    )
    grupo = models.ForeignKey(
        GrupoMedicao, blank=True, null=True, on_delete=models.PROTECT
    )
    alterado_em = models.DateTimeField("Alterado em", null=True, blank=True)

    @property
    def nome_periodo_grupo(self):
        if self.grupo and self.periodo_escolar:
            nome_periodo_grupo = (
                f"{self.grupo.nome} - " + f"{self.periodo_escolar.nome}"
            )
        elif self.grupo and not self.periodo_escolar:
            nome_periodo_grupo = f"{self.grupo.nome}"
        else:
            nome_periodo_grupo = f"{self.periodo_escolar.nome}"
        return nome_periodo_grupo

    def deletar_log_correcao(self, status_evento, **kwargs):
        log = self.logs.last()
        if log and log.status_evento in status_evento:
            log.delete()

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            justificativa=justificativa,
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
            usuario=usuario,
            uuid_original=self.uuid,
        )

    def possui_ao_menos_uma_observacao(self) -> bool:
        return (
            self.valores_medicao.filter(nome_campo="observacoes")
            .exclude(valor="")
            .exists()
        )

    def possui_algum_lancamento(self) -> bool:
        return (
            self.valores_medicao.exclude(valor__in=["", None])
            .exclude(
                nome_campo__in=[
                    "dietas_autorizadas",
                    "matriculados",
                    "numero_de_alunos",
                    "observacoes",
                ]
            )
            .exists()
        )

    class Meta:
        verbose_name = "Medição"
        verbose_name_plural = "Medições"

    def __str__(self):
        ano = f"{self.solicitacao_medicao_inicial.ano}"
        mes = f"{self.solicitacao_medicao_inicial.mes}"

        return f"Medição #{self.id_externo} -- {self.nome_periodo_grupo} -- {mes}/{ano}"


class CategoriaMedicao(Nomeavel, Ativavel, TemChaveExterna):
    class Meta:
        verbose_name = "Categoria de medição"
        verbose_name_plural = "Categorias de medições"

    def __str__(self):
        return self.nome


class ValorMedicao(
    TemChaveExterna, TemIdentificadorExternoAmigavel, CriadoEm, TemDia, TemSemana
):
    INFANTIL = "INFANTIL"
    FUNDAMENTAL = "FUNDAMENTAL"
    NA = "N/A"

    valor = models.TextField("Valor do Campo")
    nome_campo = models.CharField(max_length=100)
    medicao = models.ForeignKey(
        "Medicao", on_delete=models.CASCADE, related_name="valores_medicao"
    )
    categoria_medicao = models.ForeignKey(
        "CategoriaMedicao", on_delete=models.CASCADE, related_name="valores_medicao"
    )
    tipo_alimentacao = models.ForeignKey(
        "cardapio.TipoAlimentacao", blank=True, null=True, on_delete=models.DO_NOTHING
    )
    faixa_etaria = models.ForeignKey(
        "escola.FaixaEtaria", blank=True, null=True, on_delete=models.DO_NOTHING
    )
    habilitado_correcao = models.BooleanField(default=False)
    infantil_ou_fundamental = models.CharField(
        max_length=11, choices=INFANTIL_OU_FUNDAMENTAL, default="N/A"
    )

    @classmethod
    def get_week_of_month(cls, year, month, day):
        setfirstweekday(0)
        x = numpy.array(monthcalendar(year, month))
        week_of_month = numpy.where(x == day)[0][0] + 1
        return week_of_month

    def __str__(self):
        categoria = f"{self.categoria_medicao.nome}"
        nome_campo = f"{self.nome_campo}"
        dia = f"{self.dia}"
        mes = f"{self.medicao.solicitacao_medicao_inicial.mes}"
        return f"#{self.id_externo} -- Categoria {categoria} -- Campo {nome_campo} -- Dia/Mês {dia}/{mes}"

    class Meta:
        verbose_name = "Valor da Medição"
        verbose_name_plural = "Valores das Medições"


class AlimentacaoLancamentoEspecial(Nomeavel, Ativavel, TemChaveExterna, Posicao):
    class Meta:
        verbose_name = "Alimentação de Lançamento Especial"
        verbose_name_plural = "Alimentações de Lançamentos Especiais"
        ordering = ["posicao"]

    @property
    def name(self):
        return (
            unicodedata.normalize("NFD", self.nome.replace(" ", "_"))
            .encode("ascii", "ignore")
            .decode("utf-8")
            .lower()
        )

    def __str__(self):
        return self.nome


class PermissaoLancamentoEspecial(
    CriadoPor, CriadoEm, TemAlteradoEm, TemChaveExterna, TemIdentificadorExternoAmigavel
):
    escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.CASCADE,
        related_name="permissoes_lancamento_especial",
    )
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar", blank=True, null=True, on_delete=models.DO_NOTHING
    )
    alimentacoes_lancamento_especial = models.ManyToManyField(
        AlimentacaoLancamentoEspecial
    )
    diretoria_regional = models.ForeignKey(
        "escola.DiretoriaRegional",
        related_name="permissoes_lancamento_especial",
        on_delete=models.DO_NOTHING,
    )
    data_inicial = models.DateField("Data inicial", null=True, blank=True)
    data_final = models.DateField("Data final", null=True, blank=True)

    @property
    def ativo(self):
        hoje = datetime.datetime.today().date()
        if self.data_inicial and self.data_final:
            return self.data_inicial <= hoje <= self.data_final
        if self.data_inicial and not self.data_final:
            return self.data_inicial <= hoje
        if not self.data_inicial and self.data_final:
            return hoje <= self.data_final
        if not self.data_inicial and not self.data_final:
            return True

    class Meta:
        verbose_name = "Permissão de Lançamento Especial"
        verbose_name_plural = "Permissões de Lançamentos Especiais"
        ordering = ["-alterado_em"]

    def __str__(self):
        return f"#{self.id_externo} - {self.periodo_escolar.nome} - {self.escola.nome} -- de {self.data_inicial} até {self.data_final or '-- '}"


class DiaParaCorrigir(
    TemChaveExterna, TemIdentificadorExternoAmigavel, TemDia, CriadoEm, CriadoPor
):
    medicao = models.ForeignKey(
        "Medicao", on_delete=models.CASCADE, related_name="dias_para_corrigir"
    )
    categoria_medicao = models.ForeignKey(
        "CategoriaMedicao", on_delete=models.CASCADE, related_name="dias_para_corrigir"
    )
    habilitado_correcao = models.BooleanField(default=True)
    infantil_ou_fundamental = models.CharField(
        max_length=11, choices=INFANTIL_OU_FUNDAMENTAL, default="N/A"
    )

    @classmethod
    def cria_dias_para_corrigir(
        cls, medicao: Medicao, usuario: Usuario, list_dias_para_corrigir: list
    ) -> None:
        if not list_dias_para_corrigir:
            return
        medicao.dias_para_corrigir.all().delete()
        list_dias_para_corrigir_a_criar = []
        for dia_para_corrigir in list_dias_para_corrigir:
            categoria_medicao = CategoriaMedicao.objects.get(
                uuid=dia_para_corrigir["categoria_medicao_uuid"]
            )
            dia_obj = DiaParaCorrigir(
                medicao=medicao,
                dia=dia_para_corrigir["dia"],
                categoria_medicao=categoria_medicao,
                criado_por=usuario,
                infantil_ou_fundamental=dia_para_corrigir.get(
                    "infantil_ou_fundamental", "N/A"
                ),
            )
            list_dias_para_corrigir_a_criar.append(dia_obj)
        DiaParaCorrigir.objects.bulk_create(list_dias_para_corrigir_a_criar)

    def __str__(self):
        escola = self.medicao.solicitacao_medicao_inicial.escola.nome
        periodo_ou_grupo = (
            self.medicao.grupo.nome
            if self.medicao.grupo
            else self.medicao.periodo_escolar.nome
        )
        mes = self.medicao.solicitacao_medicao_inicial.mes
        ano = self.medicao.solicitacao_medicao_inicial.ano
        return f"# {self.id_externo} - {escola} - {periodo_ou_grupo} - {self.dia}/{mes}/{ano} - {self.infantil_ou_fundamental}"

    class Meta:
        verbose_name = "Dia da Medição para corrigir"
        verbose_name_plural = "Dias da Medição para corrigir"


class Empenho(TemChaveExterna, CriadoEm, TemAlteradoEm):
    # Tipo de empenho
    TIPO_EMPENHO_CHOICES = (("PRINCIPAL", "Principal"), ("REAJUSTE", "Reajuste"))

    # Status
    STATUS_CHOICES = (("ATIVO", "Ativo"), ("INATIVO", "Inativo"))

    numero = models.CharField("Número do empenho", max_length=100, unique=True)
    contrato = models.ForeignKey(
        "terceirizada.Contrato", on_delete=models.PROTECT, related_name="empenhos"
    )
    edital = models.ForeignKey(
        "terceirizada.Edital", on_delete=models.PROTECT, related_name="empenhos"
    )
    tipo_empenho = models.CharField(
        choices=TIPO_EMPENHO_CHOICES, max_length=20, default="PRINCIPAL"
    )
    status = models.CharField(choices=STATUS_CHOICES, max_length=10, default="ATIVO")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Empenho: {self.numero}"

    class Meta:
        verbose_name = "Empenho"
        verbose_name_plural = "Empenhos"
        ordering = ["-alterado_em"]


class ClausulaDeDesconto(TemChaveExterna, CriadoEm, TemAlteradoEm):
    edital = models.ForeignKey(
        "terceirizada.Edital",
        on_delete=models.CASCADE,
        related_name="clausulas_desconto",
    )
    numero_clausula = models.CharField("Número da Cláusula", max_length=100)
    item_clausula = models.CharField("Item da Cláusula", max_length=100)
    porcentagem_desconto = models.DecimalField(max_digits=6, decimal_places=2)
    descricao = models.TextField("Descrição")

    def __str__(self):
        return f"Edital: {self.edital.numero} - Cláusula {self.numero_clausula} - Item {self.item_clausula}"

    class Meta:
        verbose_name = "Cláusula de Desconto"
        verbose_name_plural = "Cláusulas de Descontos"
        ordering = ["-alterado_em"]
        unique_together = ("edital", "numero_clausula", "item_clausula")


class ParametrizacaoFinanceira(TemChaveExterna, CriadoEm, TemAlteradoEm):
    edital = models.ForeignKey(
        "terceirizada.Edital",
        related_name="parametrizacoes_financeiras",
        on_delete=models.PROTECT,
    )
    lote = models.ForeignKey(
        "escola.Lote",
        related_name="parametrizacoes_financeiras",
        on_delete=models.PROTECT,
    )
    tipos_unidades = models.ManyToManyField(
        "escola.TipoUnidadeEscolar", related_name="parametrizacoes_financeiras"
    )
    legenda = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Edital {self.edital} | Lote {self.lote} | DRE {self.lote.diretoria_regional} | Tipos de Unidades {', '.join(self.tipos_unidades.values_list('iniciais', flat=True))}"

    class Meta:
        verbose_name = "Parametrização Financeira"
        verbose_name_plural = "Parametrizações Financeiras"
        ordering = ["-alterado_em"]


class ParametrizacaoFinanceiraTabela(TemChaveExterna, CriadoEm, TemAlteradoEm):
    nome = models.CharField()
    parametrizacao_financeira = models.ForeignKey(
        ParametrizacaoFinanceira, on_delete=models.CASCADE, related_name="tabelas"
    )

    def __str__(self):
        return f"Tabela {self.nome}"

    class Meta:
        verbose_name = "Parametrização Financeira Tabela"
        verbose_name_plural = "Parametrizações Financeiras Tabelas"
        unique_together = ("nome", "parametrizacao_financeira")


class ParametrizacaoFinanceiraTabelaValor(TemChaveExterna, CriadoEm, TemAlteradoEm):
    """
    Ex.: valor_colunas: {
        "tipo_alimentacao": "REFEICAO - EJA",
        "valor_unitario": 10,
        "valor_reajuste": 15
    }
    """

    tabela = models.ForeignKey(
        ParametrizacaoFinanceiraTabela, on_delete=models.CASCADE, related_name="valores"
    )
    faixa_etaria = models.ForeignKey(
        "escola.FaixaEtaria",
        on_delete=models.PROTECT,
        related_name="parametrizacoes_valores",
        null=True,
        blank=True,
    )
    tipo_alimentacao = models.ForeignKey(
        "cardapio.TipoAlimentacao",
        on_delete=models.PROTECT,
        related_name="parametrizacoes_valores",
        null=True,
        blank=True,
    )
    grupo = models.CharField(null=True, blank=True)
    valor_colunas = models.JSONField()

    def __str__(self):
        descricao = (
            f"{self.tipo_alimentacao} {self.grupo}"
            if self.faixa_etaria is None
            else f"{self.faixa_etaria}"
        )
        return f"Tabela {self.tabela} | {descricao}"

    class Meta:
        verbose_name = "Parametrização Financeira Tabela Valor"
        verbose_name_plural = "Parametrizações Financeiras Tabelas Valores"
        unique_together = ("tabela", "tipo_alimentacao", "grupo")


class RelatorioFinanceiro(
    TemMes,
    TemAno,
    FluxoRelatorioFinanceiroMedicaoInicial,
    TemChaveExterna,
    CriadoEm,
    TemAlteradoEm,
):
    grupo_unidade_escolar = models.ForeignKey(
        "escola.GrupoUnidadeEscolar",
        on_delete=models.PROTECT,
        related_name="relatorios_financeiros",
    )
    lote = models.ForeignKey(
        "escola.Lote",
        related_name="relatorios_financeiros",
        on_delete=models.PROTECT,
    )

    def __str__(self):
        unidades = ", ".join(
            self.grupo_unidade_escolar.tipos_unidades.all().values_list(
                "iniciais", flat=True
            )
        )
        return f"{self.mes} / {self.ano} | Unidades {unidades} | Lote {self.lote} | Status {self.status}"

    class Meta:
        verbose_name = "Relatório Financeiro"
        verbose_name_plural = "Relatórios Financeiros"
        ordering = ["-alterado_em"]
        unique_together = ("grupo_unidade_escolar", "lote", "mes", "ano")
