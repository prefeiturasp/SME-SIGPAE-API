from django.db import models

from src.cardapio.inversao_dia_cardapio.managers.inversao_dia_cardapio_managers import (
    InversaoCardapioDestaSemanaManager,
    InversaoCardapioDesteMesManager,
    InversaoCardapioVencidaManager,
)
from src.dados_comuns.behaviors import (
    CriadoEm,
    CriadoPor,
    Logs,
    Motivo,
    SolicitacaoForaDoPrazo,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
    TemObservacao,
    TemPrioridade,
    TemTerceirizadaConferiuGestaoAlimentacao,
)
from src.dados_comuns.fluxo_status import FluxoAprovacaoPartindoDaEscola
from src.dados_comuns.models import LogSolicitacoesUsuario
from src.dados_comuns.prometheus_mixin import ExportModelOperationsMixin
from src.dados_comuns.utils import patch_docs

FORMATO_DATA_BR = "%d/%m/%Y"


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
    """Modelo responsável por armazenar Solicitações de Inversão do dia de Cardápio.

    Esse modelo serve para todos os tipos de unidade escolar.

    O objetivo da solicitação é inverter o cardápio disponibilizado no Prato Aberto sobre um tipo de alimentação
    em um dia específico.

    Por exemplo:
      - dia 15/03 será servido carne na Refeição.
      - dia 22/03 será servido peixe na Refeição.
      - caso exista uma Inversão de Cardápio solicitada para o dia 15/03 para o dia 22/03 de Refeição, o peixe será servido dia 15/03 e a carne será servida dia 22/03.

    Para CEMEIs, é necessário informar se a substituição é para alunos CEI, EMEI ou para ambos.
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
    escola = models.ForeignKey(
        "escola.Escola", blank=True, null=True, on_delete=models.DO_NOTHING
    )

    tipos_alimentacao = models.ManyToManyField(
        "TipoAlimentacao", help_text="Tipos de alimentacao.", blank=True
    )

    @classmethod
    def get_solicitacoes_rascunho(cls, usuario):
        """Retorna as solicitacoes de inversao com status RASCUNHO de um usuario.

        Args:
            usuario (django.contrib.auth.models.AbstractUser): Usuario autor das
                solicitacoes.

        Returns:
            django.db.models.QuerySet: Queryset contendo as solicitacoes da
                classe com status de rascunho criadas pelo usuario informado.
        """
        solicitacoes_unificadas = InversaoCardapio.objects.filter(
            criado_por=usuario, status=InversaoCardapio.workflow_class.RASCUNHO
        )
        return solicitacoes_unificadas

    @property
    def datas(self):
        """Retorna as datas de origem formatadas para exibicao em relatorios.

        Quando a solicitacao possui um segundo par de datas, a segunda data de
        origem e concatenada com quebra de linha em HTML.

        Returns:
            str: String com a primeira data formatada em ``dd/mm/YYYY`` e, se
                existir, a segunda data separada por ``<br />``.
        """
        datas = self.data_de.strftime(FORMATO_DATA_BR) if self.data_de else ""
        if self.data_de_inversao_2:
            datas += "<br />" + self.data_de_inversao_2.strftime(FORMATO_DATA_BR)
        return datas

    @property
    def data_de(self):
        """Retorna a primeira data para a troca de cardápio da inversao do cardápio.

        Returns:
            datetime.date | None: Data de origem principal, ou ``None`` quando
                nao informada.
        """
        return self.data_de_inversao or None

    @property
    def data_para(self):
        """Retorna a segunda data para a troca de cardápio da inversao do cardápio.

        Returns:
            datetime.date | None: Data de destino principal, ou ``None`` quando
                nao informada.
        """
        return self.data_para_inversao or None

    @property
    def data(self):
        """Retorna a menor data relevante entre a primeira e a segunda data da inversao.

        Returns:
            datetime.date | None: Menor data entre ``data_de`` e ``data_para``.
                Se apenas uma delas existir, retorna a data disponivel.
        """
        if self.data_de is None:
            return self.data_para
        if self.data_para is None:
            return self.data_de
        return self.data_para if self.data_para < self.data_de else self.data_de

    @property
    def tipo(self):
        """Retorna a descrição legível do tipo da solicitacao.

        Returns:
            str: String ``"Inversão de Dia de Cardápio"``.
        """
        return "Inversão de Dia de Cardápio"

    @property
    def path(self):
        """Retorna o caminho relativo do relatorio desta solicitação no frontend.

        Returns:
            str: URL relativa do frontend para a tela de relatorio da
                solicitacao.
        """
        return f"inversao-de-dia-de-cardapio/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-normal"

    @property
    def numero_alunos(self):
        """Retorna o total de alunos associado a solicitação.

        Neste tipo de solicitação não há consolidação de quantidade de alunos,
        por isso o valor retornado é sempre vazio.

        Necessário para integração da Inversão de Dia de Cardápio com o paineis_consolidados, que agrupa todos os tipos de solicitação.

        Returns:
            str: String vazia.
        """
        return ""

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        """Registra no log a transicao de status da solicitacao.

        Args:
            status_evento (int): Codigo do evento de status que sera
                registrado.
            usuario (django.contrib.auth.models.AbstractUser): Usuario
                responsavel pela transicao.
            **kwargs: Parametros opcionais do log.
                `justificativa` (str): Texto justificando a transicao.
                `resposta_sim_nao` (bool): Resposta booleana associada ao
                    evento, quando existir.

        Returns:
            None: O metodo apenas persiste o log da transicao.
        """
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
        """Monta o dicionário usado na geração do relatório da solicitação.

        Args:
            label_data (str): rótulo textual da data exibida no relatório.
            data_log (str): Data ou descrição temporal associada ao log do
                relatório.
            instituicao (object): Instituição solicitante. Mantido por
                compatibilidade de interface, sem uso direto no método.

        Returns:
            dict[str, object]: Dicionário com os dados consolidados da
                solicitação para renderização em relatórios.
        """
        data_de_inversao = ""
        data_de_inversao_2 = ""
        if self.data_de_inversao:
            data_de_inversao = self.data_de_inversao.strftime(FORMATO_DATA_BR)

        if self.data_de_inversao_2:
            data_de_inversao_2 = self.data_de_inversao_2.strftime(FORMATO_DATA_BR)
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome_historico(self.data),
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
        """Retorna a representação textual resumida da solicitação.

        Returns:
            str: Texto com a descrição da inversão e o primeiro par de datas
                envolvido.
        """
        return (
            f"{self.escola.codigo_eol} {self.escola.nome} - Inversão de Cardápio \nDe: {self.data_de_inversao} \n"
            f"Para: {self.data_para_inversao}"
        )

    class Meta:
        verbose_name = "Inversão de cardápio"
        verbose_name_plural = "Inversões de cardápio"


patch_docs(InversaoCardapio)
