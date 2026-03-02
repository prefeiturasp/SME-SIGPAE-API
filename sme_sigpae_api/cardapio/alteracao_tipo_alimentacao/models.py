from django.db import models
from django.db.models import Sum
from django_prometheus.models import ExportModelOperationsMixin

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.behaviors import (
    EhAlteracaoCardapio,
)
from sme_sigpae_api.cardapio.base.models import TipoAlimentacao
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
    """Modelo responsável por armazenar Solicitações de Alteração do Tipo de Alimentação genéricas.

    Representa uma solicitação formal de troca do tipo de alimentação servida em
    determinado(s) período(s) escolar(es), com data inicial e final delimitadas.

    Tipos de unidade contempladas:
        - EMEF
        - EMEI
        - CIEJA
        - EMEBS

    Exceções **não** contempladas:
        - CEI
        - CEMEI

    :cvar DESCRICAO: Descrição legível do tipo de solicitação.
    :vartype DESCRICAO: str
    :cvar eh_alteracao_com_lanche_repetida: Indica se a alteração envolve lanche repetido
        no mesmo mês.
    :vartype eh_alteracao_com_lanche_repetida: bool
    """

    DESCRICAO = "Alteração do Tipo de Alimentação"

    eh_alteracao_com_lanche_repetida = models.BooleanField(default=False)

    @classmethod
    def com_lanche_do_mes_corrente(cls, escola_uuid):
        """Retorna alterações de cardápio do mês corrente que incluam lanche como tipo de destino.

        Filtra as alterações da escola informada cujo período de substituição contemple
        algum tipo de alimentação com ``"lanche"`` no nome.

        :param escola_uuid: UUID da escola a ser filtrada.
        :type escola_uuid: uuid.UUID
        :returns: QuerySet de :class:`AlteracaoCardapio` do mês corrente contendo lanche.
        :rtype: django.db.models.QuerySet
        """
        lanche = TipoAlimentacao.objects.filter(nome__icontains="lanche")
        alteracoes_da_escola = cls.do_mes_corrente.all().filter(
            escola__uuid=escola_uuid,
            substituicoes_periodo_escolar__tipos_alimentacao_para__in=lanche,
        )
        return alteracoes_da_escola

    @property
    def data(self):
        """Retorna a data mais antiga do intervalo (inicial ou final).

        :returns: Data de início da alteração, ou a data final caso seja anterior.
        :rtype: datetime.date
        """
        data = self.data_inicial
        if self.data_final < data:
            data = self.data_final
        return data

    @property
    def numero_alunos(self):
        """Retorna o total de alunos somando todas as substituições vinculadas.

        :returns: Soma da quantidade de alunos em todas as
            :class:`SubstituicaoAlimentacaoNoPeriodoEscolar` desta alteração, ou
            ``None`` se não houver substituições.
        :rtype: int or None
        """
        return self.substituicoes.aggregate(Sum("qtd_alunos"))["qtd_alunos__sum"]

    @property
    def eh_unico_dia(self):
        """Verifica se a alteração ocorre em um único dia.

        :returns: ``True`` se ``data_inicial`` e ``data_final`` forem iguais,
            ``False`` caso contrário.
        :rtype: bool
        """
        return self.data_inicial == self.data_final

    @property
    def substituicoes(self):
        """Atalho para o relacionamento ``substituicoes_periodo_escolar``.

        :returns: Manager reverso das substituições de alimentação vinculadas.
        :rtype: django.db.models.Manager
        """
        return self.substituicoes_periodo_escolar

    @property
    def inclusoes(self):
        """Atalho para o relacionamento ``datas_intervalo``.

        :returns: Manager reverso das datas do intervalo vinculadas.
        :rtype: django.db.models.Manager
        """
        return self.datas_intervalo

    @property
    def tipo(self):
        """Retorna a descrição legível do tipo da solicitação.

        :returns: String ``"Alteração do Tipo de Alimentação"``.
        :rtype: str
        """
        return "Alteração do Tipo de Alimentação"

    @property
    def path(self):
        """Retorna o caminho relativo do relatório desta solicitação no frontend.

        :returns: URL relativa no formato
            ``"alteracao-do-tipo-de-alimentacao/relatorio?uuid=<uuid>&tipoSolicitacao=solicitacao-normal"``.
        :rtype: str
        """
        return f"alteracao-do-tipo-de-alimentacao/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-normal"

    @property
    def template_mensagem(self):
        """Retorna o assunto e o corpo HTML do template de mensagem de alteração de cardápio.

        Busca o :class:`~sme_sigpae_api.dados_comuns.models.TemplateMensagem` do tipo
        ``ALTERACAO_CARDAPIO`` e retorna seus campos de assunto e conteúdo HTML.

        :returns: Tupla ``(assunto, corpo_html)`` do template.
        :rtype: tuple[str, str]
        :raises TemplateMensagem.DoesNotExist: Caso não exista template do tipo
            ``ALTERACAO_CARDAPIO`` cadastrado.
        """
        template = TemplateMensagem.objects.get(
            tipo=TemplateMensagem.ALTERACAO_CARDAPIO
        )
        corpo = template.template_html
        return template.assunto, corpo

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        """Registra no log a transição de status da solicitação.

        Cria uma entrada em :class:`~sme_sigpae_api.dados_comuns.models.LogSolicitacoesUsuario`
        associada a esta alteração de cardápio.

        :param status_evento: Código do evento de status (constante de
            :class:`~sme_sigpae_api.dados_comuns.models.LogSolicitacoesUsuario`).
        :type status_evento: int
        :param usuario: Usuário responsável pela transição.
        :type usuario: django.contrib.auth.models.AbstractUser
        :param justificativa: Texto justificando a transição (opcional).
        :type justificativa: str
        :param resposta_sim_nao: Indica resposta booleana associada ao log (opcional,
            padrão ``False``).
        :type resposta_sim_nao: bool
        :returns: None
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
    def substituicoes_dict(self):
        """Retorna as substituições de alimentação serializadas como lista de dicionários.

        Cada item da lista representa uma :class:`SubstituicaoAlimentacaoNoPeriodoEscolar`
        com os campos ``periodo``, ``alteracao_de`` e ``alteracao_para``.

        :returns: Lista de dicionários no formato::

            [
                {
                    "periodo": "MANHA",
                    "alteracao_de": "Lanche, Refeição",
                    "alteracao_para": "Lanche Emergencial",
                },
                ...
            ]

        :rtype: list[dict]
        """
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
        """Verifica se ao menos uma data do intervalo foi cancelada individualmente.

        :returns: ``True`` se existir alguma
            :class:`DataIntervaloAlteracaoCardapio` com ``cancelado=True``,
            ``False`` caso contrário.
        :rtype: bool
        """
        return self.datas_intervalo.filter(cancelado=True).exists()

    @property
    def datas(self):
        """Retorna todas as datas do intervalo formatadas e concatenadas em uma string.

        :returns: Datas no formato ``"DD/MM/YYYY"`` separadas por vírgula e espaço,
            ex.: ``"01/03/2026, 02/03/2026"``.
        :rtype: str
        """
        return ", ".join(
            [
                data.strftime("%d/%m/%Y")
                for data in self.datas_intervalo.values_list("data", flat=True)
            ]
        )

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        """Serializa os dados da solicitação para uso em relatórios.

        Retorna um dicionário com todas as informações relevantes da alteração de
        cardápio, incluindo rastreamentos históricos, datas, motivo e substituições.

        :param label_data: Rótulo descritivo para o campo de data no relatório.
        :type label_data: str
        :param data_log: Data do log de referência exibida no relatório.
        :type data_log: datetime.date
        :param instituicao: Instituição solicitante (não utilizado diretamente na
            construção do dict, mantido por compatibilidade de assinatura).
        :type instituicao: object
        :returns: Dicionário com os campos do relatório::

            {
                "lote": str,
                "unidade_educacional": str,
                "terceirizada": object,
                "tipo_doc": str,
                "data_evento": datetime.date,
                "datas_intervalo": QuerySet,
                "numero_alunos": int,
                "motivo": str,
                "data_inicial": datetime.date,
                "data_final": datetime.date,
                "data_autorizacao": datetime.date,
                "observacao": str,
                "substituicoes": list[dict],
                "label_data": str,
                "data_log": datetime.date,
                "id_externo": str,
                "status": str,
            }

        :rtype: dict
        """
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome_historico(self.data),
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
    """Representa uma substituição de tipo de alimentação em um período escolar específico.

    Está vinculada a uma :class:`AlteracaoCardapio` e define quais tipos de alimentação
    serão trocados (``tipos_alimentacao_de``) por quais outros (``tipos_alimentacao_para``)
    em um determinado período escolar, bem como a quantidade de alunos afetados.

    :cvar alteracao_cardapio: Alteração de cardápio à qual esta substituição pertence.
    :vartype alteracao_cardapio: AlteracaoCardapio
    :cvar qtd_alunos: Quantidade de alunos impactados pela substituição.
    :vartype qtd_alunos: int
    :cvar periodo_escolar: Período escolar onde a substituição ocorre.
    :vartype periodo_escolar: escola.PeriodoEscolar
    :cvar tipos_alimentacao_de: Tipos de alimentação originais a serem substituídos.
    :vartype tipos_alimentacao_de: ManyToManyField[TipoAlimentacao]
    :cvar tipos_alimentacao_para: Tipos de alimentação que substituirão os originais.
    :vartype tipos_alimentacao_para: ManyToManyField[TipoAlimentacao]
    """

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
    """Representa o motivo pelo qual uma :class:`AlteracaoCardapio` foi solicitada.

    Utilizado em conjunto com :class:`AlteracaoCardapio` para categorizar a razão
    da troca de tipo de alimentação.

    Exemplos de motivos:
        - Atividade diferenciada
        - Aniversariante do mês

    :cvar nome: Nome descritivo do motivo (herdado de
        :class:`~sme_sigpae_api.dados_comuns.behaviors.Nomeavel`).
    :vartype nome: str
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
    """Representa uma data específica pertencente ao intervalo de uma :class:`AlteracaoCardapio`.

    Permite que cada dia do intervalo seja tratado individualmente, possibilitando
    cancelamentos pontuais sem invalidar toda a solicitação.

    :cvar alteracao_cardapio: Alteração de cardápio à qual esta data pertence.
    :vartype alteracao_cardapio: AlteracaoCardapio
    :cvar data: Data do intervalo (herdada de
        :class:`~sme_sigpae_api.dados_comuns.behaviors.TemData`).
    :vartype data: datetime.date
    :cvar cancelado: Indica se esta data foi cancelada individualmente (herdado de
        :class:`~sme_sigpae_api.dados_comuns.behaviors.CanceladoIndividualmente`).
    :vartype cancelado: bool
    """

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
