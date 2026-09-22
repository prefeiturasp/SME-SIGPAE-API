import os

from django.apps import apps
from django.contrib.postgres.fields import ArrayField
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
    ValidationError,
)
from django.db import models

from src.dados_comuns.constants import StringsVerboseNameModels

from ..cardapio.base.models import TipoAlimentacao
from ..dados_comuns.behaviors import (
    ArquivoCargaBase,
    CriadoPor,
    Grupo,
    Logs,
    ModeloBase,
    Nomeavel,
    PerfilDiretorSupervisao,
    Posicao,
    StatusAtivoInativo,
    TemNomeMaior,
)
from ..dados_comuns.constants import FORMATO_DATA_BRASILEIRO, StringsCaminhoModelos
from ..dados_comuns.fluxo_status import FluxoFormularioSupervisao
from ..dados_comuns.models import LogSolicitacoesUsuario
from ..dados_comuns.validators import validate_file_size_10mb
from ..escola.models import Escola, FaixaEtaria, PeriodoEscolar
from ..medicao_inicial.models import SolicitacaoMedicaoInicial
from ..perfil.models import Usuario


class TipoGravidade(ModeloBase):
    tipo = models.CharField(StringsVerboseNameModels.TIPO_DE_GRAVIDADE.value)

    def __str__(self):
        return f"{self.tipo}"

    class Meta:
        verbose_name = StringsVerboseNameModels.TIPO_DE_GRAVIDADE.value
        verbose_name_plural = StringsVerboseNameModels.TIPOS_DE_GRAVIDADES.value


class TipoPenalidade(ModeloBase, CriadoPor, StatusAtivoInativo):
    edital = models.ForeignKey(
        StringsCaminhoModelos.MODEL_EDITAL.value,
        on_delete=models.PROTECT,
        related_name="tipos_penalidades",
    )
    numero_clausula = models.CharField(
        StringsVerboseNameModels.NUMERO_DA_CLAUSULA_ITEM.value, max_length=300
    )
    gravidade = models.ForeignKey(
        TipoGravidade, on_delete=models.PROTECT, related_name="tipos_penalidades"
    )
    descricao = models.TextField(
        StringsVerboseNameModels.DESCRICAO_DA_CLAUSULA_ITEM.value
    )

    def __str__(self):
        return f"Item: {self.numero_clausula} - Edital: {self.edital.numero}"

    class Meta:
        ordering = ("edital__numero", "numero_clausula")
        verbose_name = StringsVerboseNameModels.TIPO_DE_PENALIDADE.value
        verbose_name_plural = StringsVerboseNameModels.TIPOS_DE_PENALIDADES.value
        unique_together = ("edital", "numero_clausula")


class ObrigacaoPenalidade(ModeloBase):
    tipo_penalidade = models.ForeignKey(
        TipoPenalidade,
        verbose_name=StringsVerboseNameModels.TIPO_DE_PENALIDADE.value,
        on_delete=models.CASCADE,
        related_name="obrigacoes",
    )
    descricao = models.CharField(
        StringsVerboseNameModels.DESCRICAO_2.value, max_length=300
    )

    def __str__(self):
        return f"{self.descricao}"

    class Meta:
        verbose_name = StringsVerboseNameModels.OBRIGACAO_DA_PENALIDADE.value
        verbose_name_plural = StringsVerboseNameModels.OBRIGACOES_DAS_PENALIDADES.value


class ImportacaoPlanilhaTipoPenalidade(ArquivoCargaBase):
    """Importa dados de planilha de tipos de penalidade."""

    resultado = models.FileField(blank=True, default="")

    class Meta:
        verbose_name = (
            StringsVerboseNameModels.ARQUIVO_PARA_IMPORTACAO_ATUALIZACAO_DE_TIPOS_DE_PENALIDADE.value
        )
        verbose_name_plural = (
            StringsVerboseNameModels.ARQUIVOS_PARA_IMPORTACAO_ATUALIZACAO_DE_TIPOS_DE_PENALIDADE.value
        )

    def __str__(self) -> str:
        return str(self.conteudo)


class CategoriaOcorrencia(ModeloBase, Nomeavel, Posicao, PerfilDiretorSupervisao):
    SIM = "Sim"
    NAO = "Não"

    STATUS_CHOICES = (
        (True, SIM),
        (False, NAO),
    )
    gera_notificacao = models.BooleanField(
        StringsVerboseNameModels.GERA_NOTIFICACAO.value,
        choices=STATUS_CHOICES,
        default=False,
    )

    def __str__(self):
        return f"{self.nome}"

    class Meta:
        verbose_name = StringsVerboseNameModels.CATEGORIA_DAS_OCORRENCIAS.value
        verbose_name_plural = StringsVerboseNameModels.CATEGORIAS_DAS_OCORRENCIAS.value
        ordering = ("posicao", "nome")


class FormularioOcorrenciasBase(ModeloBase):
    usuario = models.ForeignKey(
        Usuario,
        verbose_name=StringsVerboseNameModels.USUARIO.value,
        on_delete=models.PROTECT,
        related_name="formularios_ocorrencias",
    )
    data = models.DateField()

    def __str__(self):
        return f"{self.usuario.nome} - {self.data}"

    def buscar_respostas(self, categoria=None):
        respostas_por_formulario = []
        tipos_perguntas = TipoPerguntaParametrizacaoOcorrencia.objects.all()
        for tipo_pergunta in tipos_perguntas:
            modelo_reposta = tipo_pergunta.get_model_tipo_resposta()
            if categoria:
                respostas = modelo_reposta.objects.filter(
                    formulario_base=self,
                    parametrizacao__tipo_ocorrencia__categoria__nome=categoria,
                )
                for resposta in respostas:
                    respostas_por_formulario.append(resposta)
            else:
                respostas = modelo_reposta.objects.filter(formulario_base=self)
                for resposta in respostas:
                    respostas_por_formulario.append(resposta)

        return respostas_por_formulario

    class Meta:
        verbose_name = StringsVerboseNameModels.FORMULARIO_BASE_OCORRENCIAS.value
        verbose_name_plural = (
            StringsVerboseNameModels.FORMULARIOS_BASE_OCORRENCIAS.value
        )


class TipoOcorrenciaParaNutriSupervisor(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                status=True,
                perfis__contains=[PerfilDiretorSupervisao.SUPERVISAO],
                categoria__perfis__contains=[PerfilDiretorSupervisao.SUPERVISAO],
            )
        )


class TipoOcorrenciaParaDiretor(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                status=True,
                perfis__contains=[PerfilDiretorSupervisao.DIRETOR],
                categoria__perfis__contains=[PerfilDiretorSupervisao.DIRETOR],
            )
        )


class TipoOcorrencia(
    ModeloBase, CriadoPor, Posicao, PerfilDiretorSupervisao, StatusAtivoInativo
):
    SIM = "Sim"
    NAO = "Não"

    CHOICES = (
        (True, SIM),
        (False, NAO),
    )

    edital = models.ForeignKey(
        StringsCaminhoModelos.MODEL_EDITAL.value,
        on_delete=models.PROTECT,
        related_name="tipos_ocorrencia",
    )
    categoria = models.ForeignKey(
        CategoriaOcorrencia,
        verbose_name=StringsVerboseNameModels.CATEGORIA_DA_OCORRENCIA.value,
        on_delete=models.PROTECT,
        related_name="tipos_ocorrencia",
    )
    titulo = models.CharField(StringsVerboseNameModels.TITULO.value, max_length=100)
    descricao = models.TextField(StringsVerboseNameModels.DESCRICAO_2.value)
    penalidade = models.ForeignKey(
        TipoPenalidade,
        verbose_name=StringsVerboseNameModels.PENALIDADE_DO_ITEM.value,
        on_delete=models.PROTECT,
        related_name="tipos_ocorrencia",
    )
    eh_imr = models.BooleanField(StringsVerboseNameModels.E_IMR.value, default=False)
    pontuacao = models.PositiveSmallIntegerField(
        StringsVerboseNameModels.PONTUACAO_IMR.value, blank=True, null=True
    )
    tolerancia = models.PositiveSmallIntegerField(
        StringsVerboseNameModels.TOLERANCIA.value, blank=True, null=True
    )
    porcentagem_desconto = models.FloatField(
        StringsVerboseNameModels.DE_DESCONTO_2.value,
        null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=(
            "Caso a opção de É IMR? esteja marcada a % de desconto incidirá sobre a reincidência dos apontamentos. "
            "Se não for marcada a opção de É IMR?, a % de desconto será referente a multa da penalidade."
        ),
    )
    aceita_multiplas_respostas = models.BooleanField(
        StringsVerboseNameModels.ACEITA_MULTIPLAS_RESPOSTAS.value,
        choices=CHOICES,
        default=False,
    )

    objects = models.Manager()
    para_diretores = TipoOcorrenciaParaDiretor()
    para_nutrisupervisores = TipoOcorrenciaParaNutriSupervisor()

    def get_resposta(self, formulario_base: FormularioOcorrenciasBase) -> str:
        if self.ocorrencias_nao_se_aplica.filter(
            formulario_base=formulario_base
        ).exists():
            return "Não se aplica"

        respostas = TipoRespostaModelo.objects.all()
        if any(
            resposta
            for resposta in respostas
            if resposta.model.objects.filter(
                formulario_base=formulario_base, parametrizacao__tipo_ocorrencia=self
            ).exists()
        ):
            return "Não"

        return "Sim"

    def quantidade_grupos(self, formulario_base: FormularioOcorrenciasBase) -> int:
        quantidade_grupos = 1
        respostas = TipoRespostaModelo.objects.all()
        for resposta in respostas:
            grupos = resposta.model.objects.filter(
                formulario_base=formulario_base
            ).values_list("grupo", flat=True)
            if grupos:
                return max(grupos)
        return quantidade_grupos

    def __str__(self):
        return f"{self.edital.numero} - {self.titulo}"

    class Meta:
        verbose_name = StringsVerboseNameModels.TIPO_DE_OCORRENCIA.value
        verbose_name_plural = StringsVerboseNameModels.TIPOS_DE_OCORRENCIA.value
        unique_together = ("edital", "categoria", "penalidade", "titulo")
        ordering = ("categoria__posicao", "posicao", "titulo")

    def valida_eh_imr(self, dict_error):
        if self.eh_imr and (not self.pontuacao or not self.tolerancia):
            if not self.pontuacao:
                dict_error["pontuacao"] = "Pontuação deve ser preenchida se for IMR."
            if not self.tolerancia:
                dict_error["tolerancia"] = "Tolerância deve ser preenchida se for IMR."
        return dict_error

    def valida_nao_eh_imr(self, dict_error):
        if not self.eh_imr and (self.pontuacao or self.tolerancia):
            if self.pontuacao:
                dict_error["pontuacao"] = "Pontuação só deve ser preenchida se for IMR."
            if self.tolerancia:
                dict_error["tolerancia"] = (
                    "Tolerância só deve ser preenchida se for IMR."
                )
        return dict_error

    def clean(self):
        super().clean()
        dict_error = {}
        dict_error = self.valida_eh_imr(dict_error)
        dict_error = self.valida_nao_eh_imr(dict_error)
        raise ValidationError(dict_error)

    def apagar_respostas(self):
        tipos_perguntas = TipoPerguntaParametrizacaoOcorrencia.objects.all()
        for tipo_pergunta in tipos_perguntas:
            modelo_reposta = tipo_pergunta.get_model_tipo_resposta()
            modelo_reposta.objects.filter(parametrizacao__tipo_ocorrencia=self).delete()

    def apagar_ocorrencias_nao_se_aplica(self):
        self.ocorrencias_nao_se_aplica.all().delete()


class ImportacaoPlanilhaTipoOcorrencia(ArquivoCargaBase):
    """Importa dados de planilha de tipos de ocorrência."""

    resultado = models.FileField(blank=True, default="")

    class Meta:
        verbose_name = (
            StringsVerboseNameModels.ARQUIVO_PARA_IMPORTACAO_ATUALIZACAO_DE_TIPOS_DE_OCORRENCIA.value
        )
        verbose_name_plural = (
            StringsVerboseNameModels.ARQUIVOS_PARA_IMPORTACAO_ATUALIZACAO_DE_TIPOS_DE_OCORRENCIA.value
        )

    def __str__(self) -> str:
        return str(self.conteudo)


class TipoRespostaModelo(ModeloBase, Nomeavel):
    def __str__(self):
        return f"{self.nome}"

    @property
    def model(self):
        return apps.get_model("imr", self.nome)

    class Meta:
        verbose_name = StringsVerboseNameModels.TIPO_DE_RESPOSTA_MODELO.value
        verbose_name_plural = StringsVerboseNameModels.TIPOS_DE_RESPOSTA_MODELO.value


class TipoPerguntaParametrizacaoOcorrencia(ModeloBase, Nomeavel):
    tipo_resposta = models.OneToOneField(
        TipoRespostaModelo,
        verbose_name=StringsVerboseNameModels.TIPO_DE_RESPOSTA.value,
        on_delete=models.CASCADE,
    )

    def get_model_tipo_resposta(self):
        return apps.get_model("imr", self.tipo_resposta.nome)

    def __str__(self):
        return f"{self.nome}"

    class Meta:
        verbose_name = (
            StringsVerboseNameModels.TIPO_DE_PERGUNTA_PARA_PARAMETRIZACAO_DE_TIPO_DE_OCORRENCIA.value
        )
        verbose_name_plural = (
            StringsVerboseNameModels.TIPOS_DE_PERGUNTA_PARA_PARAMETRIZACAO_DE_TIPO_DE_OCORRENCIA.value
        )


class ParametrizacaoOcorrencia(ModeloBase, Posicao):
    titulo = models.CharField(StringsVerboseNameModels.TITULO.value, max_length=100)
    tipo_ocorrencia = models.ForeignKey(
        TipoOcorrencia, on_delete=models.PROTECT, related_name="parametrizacoes"
    )
    tipo_pergunta = models.ForeignKey(
        TipoPerguntaParametrizacaoOcorrencia,
        on_delete=models.PROTECT,
        related_name="parametrizacoes",
    )

    def get_resposta_str(
        self, formulario_base: FormularioOcorrenciasBase, grupo: int
    ) -> str:
        resposta_obj = self.tipo_pergunta.tipo_resposta.model.objects.get(
            parametrizacao=self, formulario_base=formulario_base, grupo=grupo
        )
        return resposta_obj.resposta_str

    def __str__(self):
        return f"{self.tipo_ocorrencia.__str__()} {self.tipo_pergunta} - {self.posicao} - {self.titulo}"

    class Meta:
        verbose_name = (
            StringsVerboseNameModels.PARAMETRIZACAO_DE_TIPO_DE_OCORRENCIA.value
        )
        verbose_name_plural = (
            StringsVerboseNameModels.PARAMETRIZACOES_DE_TIPO_DE_OCORRENCIA.value
        )
        ordering = (
            "tipo_ocorrencia__categoria__posicao",
            "tipo_ocorrencia__posicao",
            "posicao",
        )


class PeriodoVisita(ModeloBase, Nomeavel):
    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = StringsVerboseNameModels.PERIODO_DE_VISITA.value
        verbose_name_plural = StringsVerboseNameModels.PERIODOS_DE_VISITA.value


class AnexosFormularioBase(ModeloBase):
    anexo = models.FileField(
        StringsVerboseNameModels.ANEXO.value,
        upload_to="IMR",
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "PDF",
                    "XLS",
                    "XLSX",
                    "XLSM",
                    "DOC",
                    "DOCX",
                    "PNG",
                    "JPG",
                    "JPEG",
                ]
            ),
            validate_file_size_10mb,
        ],
    )
    nome = models.CharField(max_length=200, null=True, blank=True)
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase, on_delete=models.CASCADE, related_name="anexos"
    )

    def __str__(self):
        return f"{self.anexo.name} - {self.formulario_base.__str__()}"

    def delete(self, *args, **kwargs):
        if self.anexo:
            if os.path.isfile(self.anexo.path):
                os.remove(self.anexo.path)
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = StringsVerboseNameModels.ANEXO_FORMULARIO_BASE.value
        verbose_name_plural = StringsVerboseNameModels.ANEXOS_FORMULARIO_BASE.value


class NotificacoesAssinadasFormularioBase(ModeloBase):
    notificacao_assinada = models.FileField(
        StringsVerboseNameModels.NOTIFICACAO_ASSINADA.value,
        upload_to="IMR",
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "PDF",
                ]
            ),
            validate_file_size_10mb,
        ],
    )
    nome = models.CharField(max_length=200, null=True, blank=True)
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        on_delete=models.CASCADE,
        related_name="notificacoes_assinadas",
    )

    def __str__(self):
        return f"{self.notificacao_assinada.name} - {self.formulario_base.__str__()}"

    def delete(self, *args, **kwargs):
        if self.notificacao_assinada:
            if os.path.isfile(self.notificacao_assinada.path):
                os.remove(self.notificacao_assinada.path)
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = (
            StringsVerboseNameModels.NOTIFICACAO_ASSINADA_FORMULARIO_BASE.value
        )
        verbose_name_plural = (
            StringsVerboseNameModels.NOTIFICACOES_ASSINADAS_FORMULARIO_BASE.value
        )


class FormularioDiretor(ModeloBase):
    formulario_base = models.OneToOneField(
        FormularioOcorrenciasBase, on_delete=models.CASCADE
    )
    solicitacao_medicao_inicial = models.ForeignKey(
        SolicitacaoMedicaoInicial,
        verbose_name=StringsVerboseNameModels.SOLICITACAO_MEDICAO_INICIAL.value,
        on_delete=models.PROTECT,
        related_name="formularios_ocorrencias",
    )

    def __str__(self):
        return f"{self.solicitacao_medicao_inicial.escola.nome} - {self.formulario_base.data}"

    class Meta:
        verbose_name = StringsVerboseNameModels.FORMULARIO_DO_DIRETOR_OCORRENCIAS.value
        verbose_name_plural = (
            StringsVerboseNameModels.FORMULARIOS_DO_DIRETOR_OCORRENCIAS.value
        )


class FormularioSupervisao(ModeloBase, FluxoFormularioSupervisao, Logs):
    escola = models.ForeignKey(
        Escola, on_delete=models.PROTECT, related_name="formularios_supervisao"
    )
    formulario_base = models.OneToOneField(
        FormularioOcorrenciasBase, on_delete=models.CASCADE
    )
    periodo_visita = models.ForeignKey(
        PeriodoVisita,
        verbose_name=StringsVerboseNameModels.PERIODO_DA_VISITA.value,
        on_delete=models.PROTECT,
        related_name="formularios_supervisao",
        null=True,
        blank=True,
    )
    nome_nutricionista_empresa = models.CharField(
        StringsVerboseNameModels.NOME_DA_NUTRICIONISTA_RT_DA_EMPRESA.value,
        max_length=100,
        null=True,
        blank=True,
    )

    acompanhou_visita = models.BooleanField(
        StringsVerboseNameModels.ACOMPANHOU_A_VISITA.value, default=False
    )

    maior_frequencia_no_periodo = models.PositiveIntegerField(
        StringsVerboseNameModels.MAIOR_NO_DE_FREQUENTES_NO_PERIODO.value,
        null=True,
        blank=True,
    )

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.FORMULARIO_SUPERVISAO,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
        )

    def __str__(self):
        return f"{self.escola.nome} - {self.formulario_base.data}"

    class Meta:
        verbose_name = (
            StringsVerboseNameModels.FORMULARIO_DA_SUPERVISAO_OCORRENCIAS.value
        )
        verbose_name_plural = (
            StringsVerboseNameModels.FORMULARIOS_DA_SUPERVISAO_OCORRENCIAS.value
        )


class RespostaSimNao(ModeloBase, Grupo):
    SIM = "Sim"
    NAO = "Não"

    CHOICES = ((SIM, SIM), (NAO, NAO))
    resposta = models.CharField(
        StringsVerboseNameModels.OPCAO.value, choices=CHOICES, max_length=3
    )
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        verbose_name=StringsVerboseNameModels.FORMULARIO_DE_OCORRENCIAS.value,
        on_delete=models.CASCADE,
        related_name="respostas_sim_nao",
        null=True,
    )
    parametrizacao = models.ForeignKey(
        ParametrizacaoOcorrencia,
        on_delete=models.CASCADE,
        related_name="respostas_sim_nao",
    )

    @property
    def resposta_str(self) -> str:
        return self.resposta

    def __str__(self):
        return self.resposta

    class Meta:
        verbose_name = StringsVerboseNameModels.RESPOSTA_SIM_NAO_2.value
        verbose_name_plural = StringsVerboseNameModels.RESPOSTAS_SIM_NAO.value
        unique_together = ("formulario_base", "parametrizacao", "grupo")


class RespostaCampoNumerico(ModeloBase, Grupo):
    resposta = models.FloatField()
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        verbose_name=StringsVerboseNameModels.FORMULARIO_DE_OCORRENCIAS.value,
        on_delete=models.CASCADE,
        related_name="respostas_campo_numerico",
        null=True,
    )
    parametrizacao = models.ForeignKey(
        ParametrizacaoOcorrencia,
        on_delete=models.CASCADE,
        related_name="respostas_campo_numerico",
    )

    @property
    def resposta_str(self) -> str:
        return str(self.resposta)

    def __str__(self):
        return str(self.resposta)

    class Meta:
        verbose_name = StringsVerboseNameModels.RESPOSTA_CAMPO_NUMERICO.value
        verbose_name_plural = StringsVerboseNameModels.RESPOSTAS_CAMPO_NUMERICO.value
        unique_together = ("formulario_base", "parametrizacao", "grupo")


class RespostaCampoTextoSimples(ModeloBase, Grupo):
    resposta = models.CharField(max_length=500)
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        verbose_name=StringsVerboseNameModels.FORMULARIO_DE_OCORRENCIAS.value,
        on_delete=models.CASCADE,
        related_name="respostas_campo_texto_simples",
        null=True,
    )
    parametrizacao = models.ForeignKey(
        ParametrizacaoOcorrencia,
        on_delete=models.CASCADE,
        related_name="respostas_campo_texto_simples",
    )

    @property
    def resposta_str(self) -> str:
        return self.resposta

    def __str__(self):
        return self.resposta

    class Meta:
        verbose_name = StringsVerboseNameModels.RESPOSTA_CAMPO_TEXTO_SIMPLES.value
        verbose_name_plural = (
            StringsVerboseNameModels.RESPOSTAS_CAMPO_TEXTO_SIMPLES.value
        )
        unique_together = ("formulario_base", "parametrizacao", "grupo")


class RespostaCampoTextoLongo(ModeloBase, Grupo):
    resposta = models.TextField()
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        verbose_name=StringsVerboseNameModels.FORMULARIO_DE_OCORRENCIAS.value,
        on_delete=models.CASCADE,
        related_name="respostas_campo_texto_longo",
        null=True,
    )
    parametrizacao = models.ForeignKey(
        ParametrizacaoOcorrencia,
        on_delete=models.CASCADE,
        related_name="respostas_campo_texto_longo",
    )

    @property
    def resposta_str(self) -> str:
        return self.resposta

    def __str__(self):
        return self.resposta

    class Meta:
        verbose_name = StringsVerboseNameModels.RESPOSTA_CAMPO_TEXTO_LONGO.value
        verbose_name_plural = StringsVerboseNameModels.RESPOSTAS_CAMPO_TEXTO_LONGO.value
        unique_together = ("formulario_base", "parametrizacao", "grupo")


class RespostaDatas(ModeloBase, Grupo):
    resposta = ArrayField(models.DateField())
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        verbose_name=StringsVerboseNameModels.FORMULARIO_DE_OCORRENCIAS.value,
        on_delete=models.CASCADE,
        related_name="respostas_datas",
        null=True,
    )
    parametrizacao = models.ForeignKey(
        ParametrizacaoOcorrencia,
        on_delete=models.CASCADE,
        related_name="respostas_datas",
    )

    @property
    def resposta_str(self) -> str:
        return self.__str__()

    def __str__(self):
        return ", ".join(
            [data.strftime(FORMATO_DATA_BRASILEIRO) for data in self.resposta]
        )

    class Meta:
        verbose_name = StringsVerboseNameModels.RESPOSTA_DATAS.value
        verbose_name_plural = StringsVerboseNameModels.RESPOSTAS_DATAS.value
        unique_together = ("formulario_base", "parametrizacao", "grupo")


class RespostaPeriodo(ModeloBase, Grupo):
    resposta = models.ForeignKey(
        PeriodoEscolar,
        on_delete=models.PROTECT,
        related_name="respostas_relatorio_imr",
    )
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        verbose_name=StringsVerboseNameModels.FORMULARIO_DE_OCORRENCIAS.value,
        on_delete=models.CASCADE,
        related_name="respostas_periodo",
        null=True,
    )
    parametrizacao = models.ForeignKey(
        ParametrizacaoOcorrencia,
        on_delete=models.CASCADE,
        related_name="respostas_periodo",
    )

    @property
    def resposta_str(self) -> str:
        return self.resposta.nome

    def __str__(self):
        return self.resposta.nome

    class Meta:
        verbose_name = StringsVerboseNameModels.RESPOSTA_PERIODO.value
        verbose_name_plural = StringsVerboseNameModels.RESPOSTAS_PERIODO.value
        unique_together = ("formulario_base", "parametrizacao", "grupo")


class RespostaFaixaEtaria(ModeloBase, Grupo):
    resposta = models.ForeignKey(
        FaixaEtaria,
        on_delete=models.PROTECT,
        related_name="respostas_relatorio_imr",
    )
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        verbose_name=StringsVerboseNameModels.FORMULARIO_DE_OCORRENCIAS.value,
        on_delete=models.CASCADE,
        related_name="respostas_faixa_etaria",
        null=True,
    )
    parametrizacao = models.ForeignKey(
        ParametrizacaoOcorrencia,
        on_delete=models.CASCADE,
        related_name="respostas_faixa_etaria",
    )

    @property
    def resposta_str(self) -> str:
        return self.resposta.__str__()

    def __str__(self):
        return self.resposta.__str__()

    class Meta:
        verbose_name = StringsVerboseNameModels.RESPOSTA_FAIXA_ETARIA.value
        verbose_name_plural = StringsVerboseNameModels.RESPOSTAS_FAIXA_ETARIA.value
        unique_together = ("formulario_base", "parametrizacao", "grupo")


class RespostaTipoAlimentacao(ModeloBase, Grupo):
    resposta = models.ForeignKey(
        TipoAlimentacao,
        on_delete=models.PROTECT,
        related_name="respostas_relatorio_imr",
    )
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        verbose_name=StringsVerboseNameModels.FORMULARIO_DE_OCORRENCIAS.value,
        on_delete=models.CASCADE,
        related_name="respostas_tipos_alimentacao",
        null=True,
    )
    parametrizacao = models.ForeignKey(
        ParametrizacaoOcorrencia,
        on_delete=models.CASCADE,
        related_name="respostas_tipos_alimentacao",
    )

    @property
    def resposta_str(self) -> str:
        return self.resposta.nome

    def __str__(self):
        return self.resposta.nome

    class Meta:
        verbose_name = StringsVerboseNameModels.RESPOSTA_TIPO_ALIMENTACAO.value
        verbose_name_plural = StringsVerboseNameModels.RESPOSTAS_TIPO_ALIMENTACAO.value
        unique_together = ("formulario_base", "parametrizacao", "grupo")


class RespostaSimNaoNaoSeAplica(ModeloBase, Grupo):
    SIM = "Sim"
    NAO = "Não"
    NAO_SE_APLICA = "Não se aplica"

    CHOICES = ((SIM, SIM), (NAO, NAO), (NAO_SE_APLICA, NAO_SE_APLICA))
    resposta = models.CharField(
        StringsVerboseNameModels.OPCAO.value, choices=CHOICES, max_length=13
    )
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        verbose_name=StringsVerboseNameModels.FORMULARIO_DE_OCORRENCIAS.value,
        on_delete=models.CASCADE,
        related_name="respostas_sim_nao_nao_se_aplica",
        null=True,
    )
    parametrizacao = models.ForeignKey(
        ParametrizacaoOcorrencia,
        on_delete=models.CASCADE,
        related_name="respostas_sim_nao_nao_se_aplica",
    )

    @property
    def resposta_str(self) -> str:
        return self.resposta

    def __str__(self):
        return self.resposta

    class Meta:
        verbose_name = StringsVerboseNameModels.RESPOSTA_SIM_NAO_NAO_SE_APLICA.value
        verbose_name_plural = (
            StringsVerboseNameModels.RESPOSTAS_SIM_NAO_NAO_SE_APLICA.value
        )
        unique_together = ("formulario_base", "parametrizacao", "grupo")


class OcorrenciaNaoSeAplica(ModeloBase, Grupo):
    descricao = models.TextField(StringsVerboseNameModels.DESCRICAO_2.value, blank=True)
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        verbose_name=StringsVerboseNameModels.FORMULARIO_DE_OCORRENCIAS.value,
        on_delete=models.CASCADE,
        related_name="respostas_nao_se_aplica",
        null=True,
    )
    tipo_ocorrencia = models.ForeignKey(
        TipoOcorrencia,
        on_delete=models.CASCADE,
        related_name="ocorrencias_nao_se_aplica",
    )

    def __str__(self):
        return self.descricao

    class Meta:
        verbose_name = StringsVerboseNameModels.OCORRENCIA_NAO_SE_APLICA.value
        verbose_name_plural = StringsVerboseNameModels.OCORRENCIAS_NAO_SE_APLICA.value
        unique_together = ("formulario_base", "tipo_ocorrencia", "grupo")


class FaixaPontuacaoIMR(ModeloBase):
    pontuacao_minima = models.PositiveSmallIntegerField(
        StringsVerboseNameModels.PONTUACAO_MINIMA.value
    )
    pontuacao_maxima = models.PositiveSmallIntegerField(
        StringsVerboseNameModels.PONTUACAO_MAXIMA.value, blank=True, null=True
    )
    porcentagem_desconto = models.FloatField(
        StringsVerboseNameModels.DE_DESCONTO.value,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Desconto no faturamento do dia",
    )

    def clean(self):
        super().clean()
        if self.pontuacao_maxima and self.pontuacao_minima > self.pontuacao_maxima:
            raise ValidationError(
                {"pontuacao_minima": "Pontuação mínima não pode ser maior que a máxima"}
            )
        faixas = list(
            FaixaPontuacaoIMR.objects.exclude(uuid=self.uuid).values_list(
                "pontuacao_minima", "pontuacao_maxima"
            )
        )
        dict_error = {}
        if any(
            faixa[0] <= self.pontuacao_minima <= (faixa[1] or faixa[0])
            for faixa in faixas
        ):
            dict_error["pontuacao_minima"] = (
                "Esta pontuação mínima já se encontra dentro de outra faixa."
            )
        if self.pontuacao_maxima and any(
            faixa[0] <= self.pontuacao_maxima <= (faixa[1] or faixa[0])
            for faixa in faixas
        ):
            dict_error["pontuacao_maxima"] = (
                "Esta pontuação máxima já se encontra dentro de outra faixa."
            )
        raise ValidationError(dict_error)

    def __str__(self):
        return (
            f"{self.pontuacao_minima} - {self.pontuacao_maxima or 'sem pontuação máxima'}"
            f" - {self.porcentagem_desconto}"
        )

    class Meta:
        verbose_name = StringsVerboseNameModels.FAIXA_DE_PONTUACAO_IMR.value
        verbose_name_plural = StringsVerboseNameModels.FAIXAS_DE_PONTUACAO_IMR.value
        ordering = ("pontuacao_minima",)


class UtensilioMesa(ModeloBase, Nomeavel, StatusAtivoInativo):
    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = StringsVerboseNameModels.UTENSILIO_DE_MESA.value
        verbose_name_plural = StringsVerboseNameModels.UTENSILIOS_DE_MESA.value
        ordering = ("nome",)


class EditalUtensilioMesa(ModeloBase):
    edital = models.ForeignKey(
        StringsCaminhoModelos.MODEL_EDITAL.value,
        on_delete=models.PROTECT,
    )

    utensilios_mesa = models.ManyToManyField(
        "UtensilioMesa",
        verbose_name=StringsVerboseNameModels.UTENSILIOS_DE_MESA.value,
        blank=True,
    )

    def __str__(self):
        return f"Edital: {self.edital} - {self.utensilios_mesa.count()} utensílios"

    class Meta:
        verbose_name = StringsVerboseNameModels.UTENSILIO_DE_MESA_POR_EDITAL.value
        verbose_name_plural = (
            StringsVerboseNameModels.UTENSILIOS_DE_MESA_POR_EDITAL.value
        )


class UtensilioCozinha(ModeloBase, Nomeavel, StatusAtivoInativo):
    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = StringsVerboseNameModels.UTENSILIO_DE_COZINHA.value
        verbose_name_plural = StringsVerboseNameModels.UTENSILIOS_DE_COZINHA.value
        ordering = ("nome",)


class EditalUtensilioCozinha(ModeloBase):
    edital = models.ForeignKey(
        StringsCaminhoModelos.MODEL_EDITAL.value,
        on_delete=models.PROTECT,
    )

    utensilios_cozinha = models.ManyToManyField(
        "UtensilioCozinha",
        verbose_name=StringsVerboseNameModels.UTENSILIOS_DE_COZINHA.value,
        blank=True,
    )

    def __str__(self):
        return f"Edital: {self.edital} - {self.utensilios_cozinha.count()} utensílios"

    class Meta:
        verbose_name = StringsVerboseNameModels.UTENSILIO_DE_COZINHA_POR_EDITAL.value
        verbose_name_plural = (
            StringsVerboseNameModels.UTENSILIOS_DE_COZINHA_POR_EDITAL.value
        )


class Equipamento(ModeloBase, Nomeavel, StatusAtivoInativo):
    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = StringsVerboseNameModels.EQUIPAMENTO.value
        verbose_name_plural = StringsVerboseNameModels.EQUIPAMENTOS.value
        ordering = ("nome",)


class EditalEquipamento(ModeloBase):
    edital = models.ForeignKey(
        StringsCaminhoModelos.MODEL_EDITAL.value,
        on_delete=models.PROTECT,
    )

    equipamentos = models.ManyToManyField(
        "Equipamento",
        verbose_name=StringsVerboseNameModels.EQUIPAMENTOS.value,
        blank=True,
    )

    def __str__(self):
        return f"Edital: {self.edital} - {self.equipamentos.count()} equipamentos"

    class Meta:
        verbose_name = StringsVerboseNameModels.EQUIPAMENTO_POR_EDITAL.value
        verbose_name_plural = StringsVerboseNameModels.EQUIPAMENTOS_POR_EDITAL.value


class Mobiliario(ModeloBase, Nomeavel, StatusAtivoInativo):
    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = StringsVerboseNameModels.MOBILIARIO.value
        verbose_name_plural = StringsVerboseNameModels.MOBILIARIOS.value
        ordering = ("nome",)


class EditalMobiliario(ModeloBase):
    edital = models.ForeignKey(
        StringsCaminhoModelos.MODEL_EDITAL.value,
        on_delete=models.PROTECT,
    )

    mobiliarios = models.ManyToManyField(
        "Mobiliario",
        verbose_name=StringsVerboseNameModels.MOBILIARIOS.value,
        blank=True,
    )

    def __str__(self):
        return f"Edital: {self.edital} - {self.mobiliarios.count()} mobiliários"

    class Meta:
        verbose_name = StringsVerboseNameModels.MOBILIARIO_POR_EDITAL.value
        verbose_name_plural = StringsVerboseNameModels.MOBILIARIOS_POR_EDITAL.value


class ReparoEAdaptacao(ModeloBase, Nomeavel, StatusAtivoInativo):
    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = StringsVerboseNameModels.REPARO_E_ADAPTACAO.value
        verbose_name_plural = StringsVerboseNameModels.REPAROS_E_ADAPTACOES.value
        ordering = ("nome",)


class EditalReparoEAdaptacao(ModeloBase):
    edital = models.ForeignKey(
        StringsCaminhoModelos.MODEL_EDITAL.value,
        on_delete=models.PROTECT,
    )

    reparos_e_adaptacoes = models.ManyToManyField(
        "ReparoEAdaptacao",
        verbose_name=StringsVerboseNameModels.REPAROS_E_ADAPTACOES.value,
        blank=True,
    )

    def __str__(self):
        return f"Edital: {self.edital} - {self.reparos_e_adaptacoes.count()} reparos e adaptações"

    class Meta:
        verbose_name = StringsVerboseNameModels.REPARO_E_ADAPTACAO_POR_EDITAL.value
        verbose_name_plural = (
            StringsVerboseNameModels.REPAROS_E_ADAPTACOES_POR_EDITAL.value
        )


class Insumo(ModeloBase, TemNomeMaior, StatusAtivoInativo):
    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = StringsVerboseNameModels.INSUMO.value
        verbose_name_plural = StringsVerboseNameModels.INSUMOS.value
        ordering = ("nome",)


class EditalInsumo(ModeloBase):
    edital = models.ForeignKey(
        StringsCaminhoModelos.MODEL_EDITAL.value,
        on_delete=models.PROTECT,
    )

    insumos = models.ManyToManyField(
        "Insumo",
        verbose_name=StringsVerboseNameModels.INSUMOS.value,
        blank=True,
    )

    def __str__(self):
        return f"Edital: {self.edital} - {self.insumos.count()} insumos"

    class Meta:
        verbose_name = StringsVerboseNameModels.INSUMO_POR_EDITAL.value
        verbose_name_plural = StringsVerboseNameModels.INSUMOS_POR_EDITAL.value


class RespostaUtensilioMesa(ModeloBase, Grupo):
    resposta = models.ForeignKey(
        UtensilioMesa,
        on_delete=models.PROTECT,
        related_name="respostas_relatorio_imr",
    )
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        verbose_name=StringsVerboseNameModels.FORMULARIO_DE_OCORRENCIAS.value,
        on_delete=models.CASCADE,
        related_name="respostas_utensilios_mesa",
        null=True,
    )
    parametrizacao = models.ForeignKey(
        ParametrizacaoOcorrencia,
        on_delete=models.CASCADE,
        related_name="respostas_utensilios_mesa",
    )

    @property
    def resposta_str(self) -> str:
        return self.resposta.nome

    def __str__(self):
        return self.resposta.nome

    class Meta:
        verbose_name = StringsVerboseNameModels.RESPOSTA_UTENSILIO_DE_MESA.value
        verbose_name_plural = StringsVerboseNameModels.RESPOSTAS_UTENSILIO_DE_MESA.value
        unique_together = ("formulario_base", "parametrizacao", "grupo")


class RespostaUtensilioCozinha(ModeloBase, Grupo):
    resposta = models.ForeignKey(
        UtensilioCozinha,
        on_delete=models.PROTECT,
        related_name="respostas_relatorio_imr",
    )
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        verbose_name=StringsVerboseNameModels.FORMULARIO_DE_OCORRENCIAS.value,
        on_delete=models.CASCADE,
        related_name="respostas_utensilios_cozinha",
        null=True,
    )
    parametrizacao = models.ForeignKey(
        ParametrizacaoOcorrencia,
        on_delete=models.CASCADE,
        related_name="respostas_utensilios_cozinha",
    )

    @property
    def resposta_str(self) -> str:
        return self.resposta.nome

    def __str__(self):
        return self.resposta.nome

    class Meta:
        verbose_name = StringsVerboseNameModels.RESPOSTA_UTENSILIO_DE_COZINHA.value
        verbose_name_plural = (
            StringsVerboseNameModels.RESPOSTAS_UTENSILIO_DE_COZINHA.value
        )
        unique_together = ("formulario_base", "parametrizacao", "grupo")


class RespostaEquipamento(ModeloBase, Grupo):
    resposta = models.ForeignKey(
        Equipamento,
        on_delete=models.PROTECT,
        related_name="respostas_relatorio_imr",
    )
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        verbose_name=StringsVerboseNameModels.FORMULARIO_DE_OCORRENCIAS.value,
        on_delete=models.CASCADE,
        related_name="respostas_equipamentos",
        null=True,
    )
    parametrizacao = models.ForeignKey(
        ParametrizacaoOcorrencia,
        on_delete=models.CASCADE,
        related_name="respostas_equipamentos",
    )

    @property
    def resposta_str(self) -> str:
        return self.resposta.nome

    def __str__(self):
        return self.resposta.nome

    class Meta:
        verbose_name = StringsVerboseNameModels.RESPOSTA_EQUIPAMENTO.value
        verbose_name_plural = StringsVerboseNameModels.RESPOSTAS_EQUIPAMENTO.value
        unique_together = ("formulario_base", "parametrizacao", "grupo")


class RespostaMobiliario(ModeloBase, Grupo):
    resposta = models.ForeignKey(
        Mobiliario,
        on_delete=models.PROTECT,
        related_name="respostas_relatorio_imr",
    )
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        verbose_name=StringsVerboseNameModels.FORMULARIO_DE_OCORRENCIAS.value,
        on_delete=models.CASCADE,
        related_name="respostas_mobiliarios",
        null=True,
    )
    parametrizacao = models.ForeignKey(
        ParametrizacaoOcorrencia,
        on_delete=models.CASCADE,
        related_name="respostas_mobiliarios",
    )

    @property
    def resposta_str(self) -> str:
        return self.resposta.nome

    def __str__(self):
        return self.resposta.nome

    class Meta:
        verbose_name = StringsVerboseNameModels.RESPOSTA_MOBILIARIO.value
        verbose_name_plural = StringsVerboseNameModels.RESPOSTAS_MOBILIARIO.value
        unique_together = ("formulario_base", "parametrizacao", "grupo")


class RespostaReparoEAdaptacao(ModeloBase, Grupo):
    resposta = models.ForeignKey(
        ReparoEAdaptacao,
        on_delete=models.PROTECT,
        related_name="respostas_relatorio_imr",
    )
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        verbose_name=StringsVerboseNameModels.FORMULARIO_DE_OCORRENCIAS.value,
        on_delete=models.CASCADE,
        related_name="respostas_reparos_e_adaptacoes",
        null=True,
    )
    parametrizacao = models.ForeignKey(
        ParametrizacaoOcorrencia,
        on_delete=models.CASCADE,
        related_name="respostas_reparos_e_adaptacoes",
    )

    @property
    def resposta_str(self) -> str:
        return self.resposta.nome

    def __str__(self):
        return self.resposta.nome

    class Meta:
        verbose_name = StringsVerboseNameModels.RESPOSTA_REPARO_E_ADAPTACAO.value
        verbose_name_plural = (
            StringsVerboseNameModels.RESPOSTAS_REPARO_E_ADAPTACAO.value
        )
        unique_together = ("formulario_base", "parametrizacao", "grupo")


class RespostaInsumo(ModeloBase, Grupo):
    resposta = models.ForeignKey(
        Insumo,
        on_delete=models.PROTECT,
        related_name="respostas_relatorio_imr",
    )
    formulario_base = models.ForeignKey(
        FormularioOcorrenciasBase,
        verbose_name=StringsVerboseNameModels.FORMULARIO_DE_OCORRENCIAS.value,
        on_delete=models.CASCADE,
        related_name="respostas_insumos",
        null=True,
    )
    parametrizacao = models.ForeignKey(
        ParametrizacaoOcorrencia,
        on_delete=models.CASCADE,
        related_name="respostas_insumos",
    )

    @property
    def resposta_str(self) -> str:
        return self.resposta.nome

    def __str__(self):
        return self.resposta.nome

    class Meta:
        verbose_name = StringsVerboseNameModels.RESPOSTA_INSUMO.value
        verbose_name_plural = StringsVerboseNameModels.RESPOSTAS_INSUMO.value
        unique_together = ("formulario_base", "parametrizacao", "grupo")
