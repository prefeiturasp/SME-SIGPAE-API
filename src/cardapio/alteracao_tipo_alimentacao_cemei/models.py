from django.db import models
from django.db.models import Sum

from src.cardapio.alteracao_tipo_alimentacao.behaviors import (
    EhAlteracaoCardapio,
)
from src.cardapio.alteracao_tipo_alimentacao_cemei.managers.alteracao_tipo_alimentacao_cemei_managers import (
    AlteracoesCardapioCEMEIDestaSemanaManager,
    AlteracoesCardapioCEMEIDesteMesManager,
)
from src.dados_comuns.behaviors import (
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
from src.dados_comuns.fluxo_status import FluxoAprovacaoPartindoDaEscola
from src.dados_comuns.models import LogSolicitacoesUsuario
from src.dados_comuns.utils import patch_docs


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
    """Modelo responsável por armazenar Solicitações de Alteração do Tipo de Alimentação para escolas do tipo CEMEI.

    Representa uma solicitação formal de troca do tipo de alimentação servida
    em determinado(s) período(s) escolar(es).

    Para os CEMEIs, a solicitação pode ir em um único dia (``alterar_dia``) ou em um intervalo de datas
    (``data_inicial`` / ``data_final``).

    As substituições são divididas por tipo de unidade interna:
      - CEI (com faixas etárias)
      - EMEI (com quantidade de alunos por período).

    **O que é uma Alteração do Tipo de Alimentação?**

    É uma solicitação de troca do tipo de alimentação servida em um determinado dia.

    **Quais os tipos de Alteração do Tipo de Alimentação possíveis?**

    - RPL (Refeição por Lanche)
        - substitui a refeição do dia por um lanche
        - cada escola só pode pedir uma RPL por mês
        - na Medição Inicial, o lançamento de lanche neste dia é dobrado e a refeição é zerada.

    - LPR (Lanche por Refeição)
        - substitui o lanche do dia por uma refeição
        - não há limite de solicitações de LPR por mês
        - na Medição Inicial, o lançamento de lanche neste dia é zerado e a refeição é dobrada.

    - Lanche Emergencial (Não disponível para CEI, apenas para EMEI)
        - substitui todas as alimentações do dia por lanche emergencial
        - única solicitação que pode ser feita sem o mínimo de 2 dias úteis de antecedência.

    Tipos de unidade contempladas:
        - CEMEI
        - CEU CEMEI

    Exceções não contempladas:
        - EMEF
        - EMEI
        - CEI
        etc.

    Attributes:
        DESCRICAO (str): Descrição legível do tipo de solicitação. Utilizado no dashboard de Gestão de Alimentação para identificar o tipo de cada solicitação. O valor é a string ``"Alteração do Tipo de Alimentação CEMEI"``.
        TODOS (str): Constante indicando que a solicitação abrange tanto alunos CEI quanto EMEI.
        CEI (str): Constante indicando que a solicitação afeta apenas alunos CEI.
        EMEI (str): Constante indicando que a solicitação afeta apenas alunos EMEI.
    """

    TODOS = "TODOS"
    CEI = "CEI"
    EMEI = "EMEI"

    DESCRICAO = "Alteração do Tipo de Alimentação CEMEI"

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
        """Retorna a data da solicitação, priorizando ``alterar_dia``.

        Para solicitações de dia único, retorna ``alterar_dia``.
        Para solicitações por intervalo, retorna ``data_inicial``.

        Returns:
            datetime.date | None: Data do evento ou ``None`` se nenhum campo
            estiver preenchido.
        """
        return self.alterar_dia or self.data_inicial

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

    @property
    def existe_dia_cancelado(self):
        """Verifica se ao menos uma data do intervalo foi cancelada individualmente.

        Returns:
            bool: ``True`` se existir alguma ``DataIntervaloAlteracaoCardapioCEMEI``
            com ``cancelado=True``, ``False`` caso contrário.
        """
        return self.datas_intervalo.filter(cancelado=True).exists()

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
            ``"alteracao-do-tipo-de-alimentacao-cemei/relatorio?uuid=<uuid>&tipoSolicitacao=solicitacao-cemei"``.
        """
        return f"alteracao-do-tipo-de-alimentacao-cemei/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-cemei"

    @property
    def numero_alunos(self):
        """Retorna o total de alunos somando as faixas etárias CEI e as quantidades EMEI.

        Returns:
            int: Soma da quantidade de alunos em todas as faixas etárias de
            ``SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI`` e das quantidades
            de ``SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI``.
        """
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

    def tipos_alimentacao_de(self, nome_periodo_escolar: str = None) -> list[str]:
        """Retorna uma lista com os tipos de alimentação substituídos nesta solicitação.

        Combina os tipos de alimentação de origem das substituições CEI
        (``SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI``) e EMEI
        (``SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI``), filtrando
        opcionalmente por período escolar.

        Args:
            nome_periodo_escolar (str, optional): Nome do período escolar para
                restringir o resultado. Se ``None``, considera todas as
                substituições. Padrão: ``None``.

        Returns:
            list[str]: Lista de nomes dos tipos de alimentação substituídos,
            sem garantia de ordem e podendo conter duplicatas.
        """
        tipos_alimentacao_de = []
        substituicoes_cei = self.substituicoes_cemei_cei_periodo_escolar.all()
        if nome_periodo_escolar:
            substituicoes_cei = substituicoes_cei.filter(
                periodo_escolar__nome=nome_periodo_escolar
            )
        tipos_alimentacao_de += list(
            substituicoes_cei.values_list("tipos_alimentacao_de__nome", flat=True)
        )

        substituicoes_emei = self.substituicoes_cemei_emei_periodo_escolar.all()
        if nome_periodo_escolar:
            substituicoes_emei = substituicoes_emei.filter(
                periodo_escolar__nome=nome_periodo_escolar
            )
        tipos_alimentacao_de += list(
            substituicoes_emei.values_list("tipos_alimentacao_de__nome", flat=True)
        )
        return tipos_alimentacao_de

    @property
    def periodos_escolares(self):
        """Retorna uma lista com os períodos escolares afetados por esta solicitação.

        Combina os períodos escolares das substituições CEI
        (``SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI``) e das
        substituições EMEI
        (``SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI``).

        Returns:
            list[str]: Lista de nomes dos períodos escolares afetados, sem
            garantia de ordem e podendo conter duplicatas.
        """
        periodos = []
        periodos += list(
            self.substituicoes_cemei_cei_periodo_escolar.values_list(
                "periodo_escolar__nome", flat=True
            )
        )
        periodos += list(
            self.substituicoes_cemei_emei_periodo_escolar.values_list(
                "periodo_escolar__nome", flat=True
            )
        )
        return periodos

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        """Registra no log a transição de status da solicitação.

        Cria uma entrada em ``LogSolicitacoesUsuario`` associada a esta
        alteração de cardápio CEMEI.

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

    def substituicoes_dict(self):
        """Retorna as substituições de alimentação CEMEI serializadas como lista de dicionários.

        Agrupa as substituições por período escolar, incluindo dados tanto das
        substituições CEI (por faixa etária) quanto das substituições EMEI
        (por quantidade de alunos).

        Returns:
            list[dict]: Lista de dicionários com os campos ``periodo``,
            ``faixas_cei`` e ``faixas_emei``.
        """
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
        """Serializa os dados da solicitação CEMEI para uso em relatórios.

        Retorna um dicionário com as informações relevantes da alteração de
        cardápio CEMEI, incluindo rastreamentos históricos, datas, motivo e
        substituições divididas por tipo de unidade interna (CEI e EMEI).

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
    """Representa uma substituição de tipo de alimentação por período escolar para a parte CEI do CEMEI.

    Está vinculada a uma ``AlteracaoCardapioCEMEI`` e define quais tipos de
    alimentação serão substituídos e por quais tipos resultantes em um
    determinado período escolar. As quantidades de alunos afetados são
    especificadas por faixa etária em
    ``FaixaEtariaSubstituicaoAlimentacaoCEMEICEI``.
    """

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
        return f"Substituições de alimentação CEMEI: {self.uuid} da Alteração de Cardápio: {self.alteracao_cardapio.uuid}"

    class Meta:
        verbose_name = "Substituições de alimentação CEMEI CEI no período"
        verbose_name_plural = "Substituições de alimentação CEMEI CEI no período"


class SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI(
    TemChaveExterna, MatriculadosQuandoCriado
):
    """Representa uma substituição de tipo de alimentação por período escolar para a parte EMEI do CEMEI.

    Está vinculada a uma ``AlteracaoCardapioCEMEI`` e define quais tipos de
    alimentação serão substituídos e por quais tipos resultantes em um
    determinado período escolar. A quantidade de alunos é informada como um
    número inteiro simples (``qtd_alunos``), diferente do CEI que usa faixas
    etárias.
    """

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
    """Representa a quantidade de alunos de uma faixa etária em uma substituição CEI do CEMEI.

    Está vinculada a ``SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI`` e
    detalha quantos alunos de cada faixa etária são afetados pela
    substituição, juntamente com o número de matriculados no momento da
    criação da solicitação.
    """

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
    """Representa uma data específica pertencente ao intervalo de uma ``AlteracaoCardapioCEMEI``.

    Permite que cada dia do intervalo seja tratado individualmente,
    possibilitando cancelamentos pontuais sem invalidar toda a solicitação.
    """

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


patch_docs(AlteracaoCardapioCEMEI)
