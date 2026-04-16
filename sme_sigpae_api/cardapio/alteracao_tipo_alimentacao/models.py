from django.db import models
from django.db.models import Sum
from django_prometheus.models import ExportModelOperationsMixin

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.behaviors import (
    EhAlteracaoCardapio,
)
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

    - Lanche Emergencial
        - substitui todas as alimentações do dia por lanche emergencial (no passado, era chamado de Merenda Seca)
        - única solicitação que pode ser feita sem o mínimo de 2 dias úteis de antecedência
        - normalmente requerida quando acontece algum imprevisto que inviabiliza a preparação da refeição, como falta de energia ou água, ou atraso na entrega dos alimentos.

    Tipos de unidade contempladas:
        - EMEF
        - EMEI
        - CIEJA
        - EMEBS

    Exceções não contempladas:
        - CEI
        - CEMEI

    Attributes:
        DESCRICAO (str): Descrição legível do tipo de solicitação. Utilizado no dashboard de Gestão de Alimentação para identificar o tipo de cada solicitação. O valor é a string ``"Alteração do Tipo de Alimentação"``.
    """

    DESCRICAO = "Alteração do Tipo de Alimentação"

    @property
    def data(self):
        """Retorna a data mais antiga do intervalo (inicial ou final).

        Returns:
            datetime.date: Data de início da alteração, ou a data final caso seja
            anterior.
        """
        data = self.data_inicial
        if self.data_final < data:
            data = self.data_final
        return data

    @property
    def numero_alunos(self):
        """Retorna o total de alunos somando todas as substituições vinculadas.

        Returns:
            int | None: Soma da quantidade de alunos em todas as
            ``SubstituicaoAlimentacaoNoPeriodoEscolar`` desta alteração, ou
            ``None`` se não houver substituições.
        """
        return self.substituicoes.aggregate(Sum("qtd_alunos"))["qtd_alunos__sum"]

    @property
    def tipos_alimentacao_de(self) -> list[str]:
        """Retorna uma lista com os tipos de alimentação substituídos nesta solicitação.

        Retorna uma lista com os nomes dos tipos de alimentação que estão sendo
        substituídos nesta solicitação, considerando todas as substituições
        vinculadas.

        Returns:
            list[str]: Lista de nomes dos tipos de alimentação substituídos.
        """
        tipos = []
        for substituicao in self.substituicoes.all():
            tipos.extend(
                substituicao.tipos_alimentacao_de.values_list("nome", flat=True)
            )
        return tipos

    @property
    def periodos_escolares(self) -> list[str]:
        """Retorna uma lista com os períodos escolares afetados por esta solicitação.

        Retorna uma lista com os nomes dos períodos escolares que estão sendo
        afetados nesta solicitação, considerando todas as substituições
        vinculadas.

        Returns:
            list[str]: Lista de nomes dos períodos escolares afetados.
        """
        return list(
            self.substituicoes.values_list(
                "periodo_escolar__nome", flat=True
            ).distinct()
        )

    @property
    def substituicoes(self):
        """Retorna um atalho para ``substituicoes_periodo_escolar``.

        Returns:
            django.db.models.Manager: Manager reverso das substituições de
            alimentacao vinculadas.
        """
        return self.substituicoes_periodo_escolar

    @property
    def inclusoes(self):
        """Retorna um atalho para ``datas_intervalo``.

        Returns:
            django.db.models.Manager: Manager reverso das datas do intervalo
            vinculadas.
        """
        return self.datas_intervalo

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
            ``"alteracao-do-tipo-de-alimentacao/relatorio?uuid=<uuid>&tipoSolicitacao=solicitacao-normal"``.
        """
        return f"alteracao-do-tipo-de-alimentacao/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-normal"

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
        alteração de cardápio.

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
    def substituicoes_dict(self):
        """Retorna as substituições de alimentação serializadas como lista de dicionários.

        Cada item da lista representa uma
        ``SubstituicaoAlimentacaoNoPeriodoEscolar`` com os campos ``periodo``,
        ``alteracao_de`` e ``alteracao_para``.

        Returns:
            list[dict]: Lista de dicionários no formato
            ``{"periodo": str, "alteracao_de": str, "alteracao_para": str}``.
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

        Returns:
            bool: ``True`` se existir alguma ``DataIntervaloAlteracaoCardapio``
            com ``cancelado=True``, ``False`` caso contrário.
        """
        return self.datas_intervalo.filter(cancelado=True).exists()

    @property
    def datas(self):
        """Retorna todas as datas do intervalo formatadas e concatenadas em uma string.

        Returns:
            str: Datas no formato ``"DD/MM/YYYY"`` separadas por vírgula e
            espaço, por exemplo ``"01/03/2026, 02/03/2026"``.
        """
        return ", ".join(
            [
                data.strftime("%d/%m/%Y")
                for data in self.datas_intervalo.values_list("data", flat=True)
            ]
        )

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        """Serializa os dados da solicitação para uso em relatórios.

        Retorna um dicionário com as informações relevantes da alteração de
        cardápio, incluindo rastreamentos históricos, datas, motivo e
        substituições.

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

    Está vinculada a uma ``AlteracaoCardapio`` e define quais tipos de
    alimentação serão trocados por quais outros em um determinado período
    escolar, bem como a quantidade de alunos afetados.

    Exemplos:
        - no período INTEGRAL, ao selecionar motivo Lanche Emergencial, substituir REFEIÇÃO por LANCHE EMERGENCIAL para 50 alunos.
        - no período MANHA, ao selecionar motivo LPR, substituir LANCHE por REFEIÇÃO para 30 alunos.
        - no período TARDE, ao selecionar motivo RPL, substituir REFEIÇÃO por LANCHE para 20 alunos.
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
    """Representa o motivo pelo qual uma ``AlteracaoCardapio`` foi solicitada.

    Utilizado para categorizar a razão da troca de tipo de alimentação.

    Motivos possíveis:
        - Lanche Emergencial
        - RPL (Refeição por Lanche)
        - LPR (Lanche por Refeição)

    Os motivos são compartilhados entre as Alterações do Tipo de Alimentação:
        - Alteração Padrão (EMEF, EMEI, CIEJA, EMEBS, etc.)
        - Alteração CEI (CEI DIRET, CEU CEI, CCI/CIPS)
        - Alteração CEMEI (CEMEI, CEU CEMEI)
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
    """Representa uma data específica pertencente ao intervalo de uma ``AlteracaoCardapio``.

    Permite que cada dia do intervalo seja tratado individualmente,
    possibilitando cancelamentos pontuais sem invalidar toda a solicitação.
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


def _patch_docs():
    AlteracaoCardapio.inicia_fluxo.__doc__ = """
        Inicia o fluxo da solicitação de Gestão de Alimentação (envia a solicitação para DRE validar).

        Só é possível iniciar uma solicitação que esteja em **RASCUNHO**.

        Este método é herdado de django_xworkflows.

        Possui um hook (``_inicia_fluxo_hook``) para, após o início do fluxo:
          - definir o campo ``foi_solicitado_fora_do_prazo`` com base na prioridade da solicitação.
          - salvar os rastros históricos da solicitação (escola, DRE, lote e terceirizada).
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
        """

    AlteracaoCardapio.codae_autoriza.__doc__ = """
        Autoriza a solicitação de Gestão de Alimentação como CODAE pedida com mais de 5 dias úteis de antecedência.
        Só é possível autorizar uma solicitação que foi validada pela Diretoria Regional.

        Exceção:
          - Alteração do Tipo de Alimentação - Lanche Emergencial

        Este método é herdado de django_xworkflows.

        Possui um hook (``_codae_autoriza_hook``) para, após a autorização:
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
          - enviar e-mail para as partes interessadas notificando sobre a autorização.
        """

    AlteracaoCardapio.codae_autoriza_questionamento.__doc__ = """
        CODAE autoriza a solicitação de Gestão de Alimentação pedida com menos de 5 dias úteis de antecedência, mediante resposta positiva do questionamento para a empresa terceirizada que atende a escola.
        Só é possível autorizar uma solicitação que foi validada pela Diretoria Regional.

        Uma solicitação pode ser autorizada se:
          - teve uma resposta positiva do questionamento pela empresa terceirizada que atende a escola, ou seja, resposta_sim_nao=True no log de questionamento.

        Este método é herdado de django_xworkflows.

        Possui um hook (``_codae_autoriza_hook``) para, após a autorização:
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
          - enviar e-mail para as partes interessadas notificando sobre a autorização.
        """

    AlteracaoCardapio.codae_nega.__doc__ = """
        CODAE nega a solicitação de Gestão de Alimentação.
        Só é possível negar uma solicitação que foi validada pela Diretoria Regional.

        Uma solicitação pode ser negada se, por exemplo:
          - infringir alguma regra do edital
          - tiver algum dado incorreto ou inconsistente (por exemplo, um Kit Lanche não pode ser solicitado para um "passeio" nas dependências da escola. É apenas para passeios externos.)

        Este método é herdado de django_xworkflows.

        Possui um hook (``_codae_recusou_hook``) para, após a negação:
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
          - enviar e-mail para as partes interessadas notificando sobre a negação.
        """

    AlteracaoCardapio.codae_nega_questionamento.__doc__ = """
        CODAE nega a solicitação de Gestão de Alimentação pedida com menos de 5 dias úteis de antecedência.
        Só é possível negar uma solicitação que foi validada pela Diretoria Regional.

        Uma solicitação pode ser negada se:
          - não tiver uma resposta positiva do questionamento pela empresa terceirizada que atende a escola, ou seja, resposta_sim_nao=False no log de questionamento.

        Este método é herdado de django_xworkflows.

        Possui um hook (``_codae_recusou_hook``) para, após a negação:
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
          - enviar e-mail para as partes interessadas notificando sobre a negação.
        """

    AlteracaoCardapio.codae_questiona.__doc__ = """
        CODAE questiona a empresa terceirizada se é possível atender a solicitação de Gestão de Alimentação pedida com menos de 5 dias úteis de antecedência.
        Só é possível questionar uma solicitação que foi validada pela Diretoria Regional.

        Uma solicitação pedida com menos de 5 dias úteis de antecedência não pode ser autorizada imediatamente, pois a empresa terceirizada que atende a escola precisa confirmar se é possível atender a solicitação nesse prazo. Portanto, o CODAE questiona a solicitação para obter essa confirmação.

        Exceção (pode ser autorizado imediatamente, sem questionamento):
          - Alteração do Tipo de Alimentação - Lanche Emergencial

        Este método é herdado de django_xworkflows.

        Possui um hook (``_codae_questiona_hook``) para, após o questionamento:
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
        """

    AlteracaoCardapio.dre_nao_valida.__doc__ = """
        DRE não valida a solicitação de Gestão de Alimentação.

        Este método é herdado de django_xworkflows.

        Possui um hook (``_dre_nao_valida_hook``) para, após a não validação:
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
          - enviar e-mail para as partes interessadas notificando sobre a não validação.
        """

    AlteracaoCardapio.dre_pede_revisao.__doc__ = """
        Deprecado.

        Este método é herdado de django_xworkflows.
        """

    AlteracaoCardapio.dre_valida.__doc__ = """
        DRE valida a solicitação de Gestão de Alimentação.

        Este método é herdado de django_xworkflows.

        Possui um hook (``_dre_valida_hook``) para, após a validação:
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
        """

    AlteracaoCardapio.escola_revisa.__doc__ = """
        Deprecado.

        Este método é herdado de django_xworkflows.
        """

    AlteracaoCardapio.terceirizada_toma_ciencia.__doc__ = """
        Deprecado.

        Este método é herdado de django_xworkflows.

        Antigamente, este método era utilizado para registrar a ciência da empresa terceirizada sobre a solicitação.

        O status final do fluxo era **TERCEIRIZADA_TOMOU_CIENCIA**.

        Atualmente:
          - o status final é **CODAE_AUTORIZADO**.
          - o status TERCEIRIZADA_TOMOU_CIENCIA foi deprecado.
          - a empresa toma ciência sem alterar o status da solicitação, através do campo ``terceirizada_conferiu_gestao``.

        """

    AlteracaoCardapio.terceirizada_responde_questionamento.__doc__ = """
        A empresa terceirizada responde ao questionamento da CODAE sobre a possibilidade de atendimento da solicitação.

        Só é possível responder um questionamento quando a solicitação está em **CODAE_QUESTIONADO**.

        Caso a empresa responda que **sim** (resposta_sim_nao=True), a solicitação pode ser autorizada normalmente pela CODAE, mesmo tendo sido pedida com menos de 5 dias úteis de antecedência.

        Caso a empresa responda que **não** (resposta_sim_nao=False), a solicitação deve ser negada pela CODAE, pois a empresa, pelo contrato, tem o direito de negar solicitações pedidas com menos de 5 dias úteis de antecedência.

        Este método é herdado de django_xworkflows.

        Possui um hook (``_terceirizada_responde_questionamento_hook``) para, após a resposta:
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
          - registrar no log a justificativa informada e a resposta booleana em ``resposta_sim_nao``.
        """


_patch_docs()
