from django.db import models
from django.db.models import Sum
from django_prometheus.models import ExportModelOperationsMixin

from src.cardapio.alteracao_tipo_alimentacao.behaviors import (
    EhAlteracaoCardapio,
)
from src.cardapio.alteracao_tipo_alimentacao_cei.managers.alteracao_tipo_alimentacao_cei_managers import (
    AlteracoesCardapioCEIDestaSemanaManager,
    AlteracoesCardapioCEIDesteMesManager,
)
from src.dados_comuns.behaviors import (
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
from src.dados_comuns.fluxo_status import FluxoAprovacaoPartindoDaEscola
from src.dados_comuns.models import LogSolicitacoesUsuario, TemplateMensagem
from src.dados_comuns.utils import patch_docs


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
    """Modelo responsável por armazenar Solicitações de Alteração do Tipo de Alimentação para escolas do tipo CEI.

    Representa uma solicitação formal de troca do tipo de alimentação servida em
    determinado(s) período(s) escolar(es), com data inicial e final delimitadas.
    Para as CEIs, as solicitações de alteração do tipo de alimentação são divididas por faixas etárias.

    **O que é uma Alteração do Tipo de Alimentação?**

    É uma solicitação de troca do tipo de alimentação servida em um determinado dia.

    **Quais os tipos de Alteração do Tipo de Alimentação possíveis?**

    - RPL (Refeição por Lanche)
        - substitui a refeição do dia por um lanche
        - cada escola só pode pedir uma RPL por mês
        - exemplo: no dia dos aniversariantes do mês, a escola pode solicitar uma RPL para substituir a refeição por um lanche especial.
        - na Medição Inicial, o lançamento de lanche neste dia é dobrado e a refeição é zerada.

    - LPR (Lanche por Refeição)
        - substitui o lanche do dia por uma refeição
        - não há limite de solicitações de LPR por mês
        - na Medição Inicial, o lançamento de lanche neste dia é zerado e a refeição é dobrada.
        - esta solicitação raramente é utilizada, pois as escolas preferem lanche que refeição.

    **Não há lanche emergencial para CEIs.**

    Tipos de unidade contempladas:
        - CEI DIRET
        - CEU CEI
        - CCI/CIPS

    Exceções não contempladas:
        - EMEF
        - EMEI
        - CEMEI
        etc.

    Attributes:
        DESCRICAO (str): Descrição legível do tipo de solicitação. Utilizado no dashboard de Gestão de Alimentação para identificar o tipo de cada solicitação. O valor é a string ``"Alteração do Tipo de Alimentação CEI"``.
    """

    DESCRICAO = "Alteração do Tipo de Alimentação CEI"

    objects = models.Manager()
    desta_semana = AlteracoesCardapioCEIDestaSemanaManager()
    deste_mes = AlteracoesCardapioCEIDesteMesManager()

    @property
    def numero_alunos(self):
        """Retorna o total de alunos somando todas as faixas etárias das substituições vinculadas.

        Returns:
            int | None: Soma da quantidade de alunos em todas as faixas etárias das
            ``SubstituicaoAlimentacaoNoPeriodoEscolarCEI`` desta alteração, ou
            ``None`` se não houver faixas etárias cadastradas.
        """
        return self.substituicoes.aggregate(Sum("faixas_etarias__quantidade"))[
            "faixas_etarias__quantidade__sum"
        ]

    @property
    def substituicoes(self):
        """Retorna um atalho para ``substituicoes_cei_periodo_escolar``.

        Returns:
            django.db.models.Manager: Manager reverso das substituições de
            alimentação CEI vinculadas.
        """
        return self.substituicoes_cei_periodo_escolar

    @property
    def tipo(self):
        """Retorna a descrição legível do tipo da solicitação.

        Returns:
            str: String ``"Alteração do Tipo de Alimentação"``.
        """
        return "Alteração do Tipo de Alimentação"

    @property
    def path(self):
        """Retorna o caminho relativo do relatório desta solicitação no frontend.

        Returns:
            str: URL relativa no formato
            ``"alteracao-do-tipo-de-alimentacao/relatorio?uuid=<uuid>&tipoSolicitacao=solicitacao-cei"``.
        """
        return f"alteracao-do-tipo-de-alimentacao/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-cei"

    @property
    def template_mensagem(self):
        """Retorna o assunto e o corpo HTML do template de mensagem de alteração de cardápio.

        Busca o ``TemplateMensagem`` do tipo ``ALTERACAO_CARDAPIO`` e retorna
        seus campos de assunto e conteúdo HTML.

        Returns:
            tuple[str, str]: Tupla ``(assunto, corpo_html)`` do template.

        Raises:
            TemplateMensagem.DoesNotExist: Caso não exista template do tipo
                ``ALTERACAO_CARDAPIO`` cadastrado.
        """
        template = TemplateMensagem.objects.get(
            tipo=TemplateMensagem.ALTERACAO_CARDAPIO
        )
        corpo = template.template_html
        return template.assunto, corpo

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        """Registra no log a transição de status da solicitação.

        Cria uma entrada em ``LogSolicitacoesUsuario`` associada a esta
        alteração de cardápio CEI.

        Args:
            status_evento (int): Código do evento de status.
            usuario (django.contrib.auth.models.AbstractUser): Usuário
                responsável pela transição.
            **kwargs: Parâmetros opcionais do log.
                `justificativa` (str): Texto justificando a transição.
                `resposta_sim_nao` (bool): Indica resposta booleana associada
                    ao log. O padrão é ``False``.

        Returns:
            None
        """
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
        """Retorna as substituições de alimentação CEI serializadas como lista de dicionários.

        Cada item inclui o período escolar, os tipos de alimentação substituídos,
        o tipo resultante e as faixas etárias com quantidades e matriculados.

        Returns:
            list[dict]: Lista de dicionários com os campos ``periodo``,
            ``tipos_alimentacao_de``, ``tipos_alimentacao_para``,
            ``faixas_etarias``, ``total_alunos`` e ``total_matriculados``.
        """
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
        """Serializa os dados da solicitação CEI para uso em relatórios.

        Retorna um dicionário com as informações relevantes da alteração de
        cardápio CEI, incluindo rastreamentos históricos, data, motivo e
        substituições por faixa etária.

        Args:
            label_data (str): Rótulo descritivo para o campo de data no
                relatório.
            data_log (datetime.date): Data do log de referência exibida no
                relatório.
            instituicao (object): Instituição solicitante, mantida por
                compatibilidade de assinatura.

        Returns:
            dict: Dicionário com os campos utilizados no relatório.
        """
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome_historico(self.data),
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
    ExportModelOperationsMixin("substituicao_cei_alimentacao_periodo_escolar"),
    TemChaveExterna,
):
    """Representa uma substituição de tipo de alimentação em um período escolar específico para CEI.

    Está vinculada a uma ``AlteracaoCardapioCEI`` e define quais tipos de
    alimentação serão substituídos e por qual tipo resultante em um determinado
    período escolar. As quantidades de alunos impactados são especificadas por
    faixa etária em ``FaixaEtariaSubstituicaoAlimentacaoCEI``.

    Exemplos:
        - no período INTEGRAL, substituir REFEIÇÃO por LANCHE para faixas etárias específicas.
        - no período MANHA, substituir LANCHE por REFEIÇÃO para faixas etárias determinadas.
    """

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
    """Representa a quantidade de alunos de uma faixa etária em uma substituição de alimentação CEI.

    Está vinculada a ``SubstituicaoAlimentacaoNoPeriodoEscolarCEI`` e detalha
    quantos alunos de cada faixa etária são afetados pela substituição,
    juntamente com o número de matriculados no momento da criação da
    solicitação.
    """

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


patch_docs(AlteracaoCardapioCEI)
