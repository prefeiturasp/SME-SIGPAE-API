import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django_prometheus.models import ExportModelOperationsMixin

from ..dados_comuns.behaviors import (  # noqa I101
    CanceladoIndividualmente,
    CriadoEm,
    CriadoPor,
    Descritivel,
    Logs,
    MatriculadosQuandoCriado,
    Motivo,
    Nomeavel,
    SolicitacaoForaDoPrazo,
    TemChaveExterna,
    TemData,
    TemFaixaEtariaEQuantidade,
    TemIdentificadorExternoAmigavel,
    TemObservacao,
    TempoPasseio,
    TemPrioridade,
    TemTerceirizadaConferiuGestaoAlimentacao,
)
from ..dados_comuns.fluxo_status import (
    FluxoAprovacaoPartindoDaDiretoriaRegional,
    FluxoAprovacaoPartindoDaEscola,
)
from ..dados_comuns.models import LogSolicitacoesUsuario, TemplateMensagem
from .managers import (
    SolicitacaoUnificadaDestaSemanaManager,
    SolicitacaoUnificadaDesteMesManager,
    SolicitacaoUnificadaVencidaManager,
    SolicitacoesKitLancheAvulsaDestaSemanaManager,
    SolicitacoesKitLancheAvulsaDesteMesManager,
    SolicitacoesKitLancheAvulsaVencidaDiasManager,
    SolicitacoesKitLancheCemeiDestaSemanaManager,
    SolicitacoesKitLancheCemeiDesteMesManager,
)


class ItemKitLanche(
    ExportModelOperationsMixin("item_kit_lanche"), Nomeavel, TemChaveExterna
):
    """Que compõe o KitLanche.

    - Barra de Cereal (20 a 25 g embalagem individual)
    - Néctar UHT ou Suco Tropical UHT (200 ml)
    - Biscoito Integral Salgado (mín. de 25g embalagem individual)
    - etc.
    """

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Item do kit lanche"
        verbose_name_plural = "Item do kit lanche"


class KitLanche(ExportModelOperationsMixin("kit_lanche"), Nomeavel, TemChaveExterna):
    """kit1, kit2, kit3."""

    ATIVO = "ATIVO"
    INATIVO = "INATIVO"

    STATUS_CHOICES = (
        (ATIVO, "Ativo"),
        (INATIVO, "Inativo"),
    )

    descricao = models.TextField(default="")
    edital = models.ForeignKey(
        "terceirizada.Edital",
        on_delete=models.DO_NOTHING,
        related_name="edital_kit_lanche",
        default=None,
        null=True,
    )
    status = models.CharField(choices=STATUS_CHOICES, max_length=10, default=ATIVO)
    tipos_unidades = models.ManyToManyField(
        "escola.TipoUnidadeEscolar", related_name="tipo_unidade_kit_lanche"
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Kit lanche"
        verbose_name_plural = "Kit lanches"
        ordering = ("nome",)


class SolicitacaoKitLanche(
    ExportModelOperationsMixin("kit_lanche_base"),
    TemData,
    Motivo,
    Descritivel,
    CriadoEm,
    TempoPasseio,
    TemChaveExterna,
):
    # TODO: implementar one to one, nas duas tabelas que apontam pra essa
    # https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.OneToOneField

    kits = models.ManyToManyField(KitLanche, blank=True)

    def __str__(self):
        return f"{self.motivo} criado em {self.criado_em}"

    class Meta:
        verbose_name = "Solicitação kit lanche base"
        verbose_name_plural = "Solicitações kit lanche base"


class SolicitacaoKitLancheAvulsaBase(
    TemChaveExterna,  # type: ignore
    FluxoAprovacaoPartindoDaEscola,
    TemIdentificadorExternoAmigavel,
    CriadoPor,
    TemPrioridade,
    Logs,
    SolicitacaoForaDoPrazo,
    TemTerceirizadaConferiuGestaoAlimentacao,
):
    # TODO: ao deletar este, deletar solicitacao_kit_lanche também que é uma tabela acessória
    # TODO: passar `local` para solicitacao_kit_lanche
    DESCRICAO = "Kit Lanche"
    local = models.CharField(max_length=160)
    evento = models.CharField(max_length=160, blank=True)
    solicitacao_kit_lanche = models.ForeignKey(
        SolicitacaoKitLanche, on_delete=models.DO_NOTHING
    )

    objects = models.Manager()  # Manager Padrão
    desta_semana = SolicitacoesKitLancheAvulsaDestaSemanaManager()
    deste_mes = SolicitacoesKitLancheAvulsaDesteMesManager()
    vencidos = SolicitacoesKitLancheAvulsaVencidaDiasManager()

    @property
    def quantidade_alimentacoes(self):
        if self.quantidade_alunos:
            return self.quantidade_alunos * self.solicitacao_kit_lanche.kits.count()

    @property
    def data(self):
        return self.solicitacao_kit_lanche.data

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        resposta_sim_nao = kwargs.get("resposta_sim_nao", False)
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.SOLICITACAO_KIT_LANCHE_AVULSA,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
            resposta_sim_nao=resposta_sim_nao,
        )

    @property
    def template_mensagem(self):
        template = TemplateMensagem.objects.get(
            tipo=TemplateMensagem.SOLICITACAO_KIT_LANCHE_AVULSA
        )
        template_troca = {
            "@id": self.id_externo,
            "@criado_em": str(self.solicitacao_kit_lanche.criado_em),
            "@criado_por": str(self.criado_por),
            "@status": str(self.status),
            # TODO: verificar a url padrão do pedido
            "@link": "http://teste.com",
        }
        corpo = template.template_html
        for chave, valor in template_troca.items():
            corpo = corpo.replace(chave, valor)
        return template.assunto, corpo

    class Meta:
        abstract = True


class SolicitacaoKitLancheAvulsa(
    ExportModelOperationsMixin("kit_lanche_avulsa"), SolicitacaoKitLancheAvulsaBase
):
    quantidade_alunos = models.BigIntegerField(blank=True, null=True)
    escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.DO_NOTHING,
        related_name="solicitacoes_kit_lanche_avulsa",
    )
    alunos_com_dieta_especial_participantes = models.ManyToManyField("escola.Aluno")

    @property
    def solicitacoes_similares(self):
        tempo_passeio = self.solicitacao_kit_lanche.tempo_passeio
        data_evento = self.solicitacao_kit_lanche.data
        all_objects = SolicitacaoKitLancheAvulsa.objects.filter(
            escola=self.escola
        ).exclude(status=SolicitacaoKitLancheAvulsa.workflow_class.RASCUNHO)
        solicitacoes_similares = all_objects.filter(
            solicitacao_kit_lanche__data=data_evento,
            solicitacao_kit_lanche__tempo_passeio=tempo_passeio,
        )
        solicitacoes_similares = solicitacoes_similares.exclude(uuid=self.uuid)
        return solicitacoes_similares

    @property
    def observacao(self):
        return self.solicitacao_kit_lanche.descricao

    @property
    def tipo(self):
        return "Kit Lanche Passeio"

    @property
    def path(self):
        return f"solicitacao-de-kit-lanche/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-normal"

    @property
    def numero_alunos(self):
        return self.quantidade_alunos

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome,
            "terceirizada": self.rastro_terceirizada.nome,
            "tipo_doc": "Kit Lanche Passeio",
            "data_evento": self.data,
            "numero_alunos": self.numero_alunos,
            "local_passeio": self.local,
            "evento": self.evento,
            "observacao": self.observacao,
            "data_autorizacao": self.data_autorizacao,
            "tempo_passeio": self.solicitacao_kit_lanche.get_tempo_passeio_display(),
            "kits": ", ".join(
                list(
                    self.solicitacao_kit_lanche.kits.all().values_list(
                        "nome", flat=True
                    )
                )
            ),
            "total_kits": self.quantidade_alimentacoes,
            "label_data": label_data,
            "data_log": data_log,
            "id_externo": self.id_externo,
        }

    def __str__(self):
        return f"{self.escola} SOLICITA PARA {self.quantidade_alunos} ALUNOS EM {self.local}"

    class Meta:
        verbose_name = "Solicitação de kit lanche avulsa"
        verbose_name_plural = "Solicitações de kit lanche avulsa"


class SolicitacaoKitLancheCEIAvulsa(
    ExportModelOperationsMixin("kit_lanche_cei_avulsa"), SolicitacaoKitLancheAvulsaBase
):
    escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.DO_NOTHING,
        related_name="solicitacoes_kit_lanche_cei_avulsa",
    )
    alunos_com_dieta_especial_participantes = models.ManyToManyField("escola.Aluno")

    @property
    def observacao(self):
        return self.solicitacao_kit_lanche.descricao

    @property
    def tipo(self):
        return "Kit Lanche Passeio"

    @property
    def path(self):
        return f"solicitacao-de-kit-lanche/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-cei"

    @property
    def quantidade_alunos(self):
        return self.faixas_etarias.all().aggregate(models.Sum("quantidade"))[
            "quantidade__sum"
        ]

    @property
    def numero_alunos(self):
        return self.quantidade_alunos

    @property
    def total_matriculados_quando_criado(self):
        return sum(
            list(
                self.faixas_etarias.values_list("matriculados_quando_criado", flat=True)
            )
        )

    @property
    def get_faixas_etarias_dict(self):
        faixas_etarias = []
        for faixa in self.faixas_etarias.all():
            faixas_etarias.append(
                {
                    "faixa_etaria": faixa.faixa_etaria.__str__(),
                    "matriculados_quando_criado": faixa.matriculados_quando_criado,
                    "quantidade": faixa.quantidade,
                }
            )
        return faixas_etarias

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome,
            "terceirizada": self.rastro_terceirizada.nome,
            "tipo_doc": "Kit Lanche Passeio de CEI",
            "data_evento": self.data,
            "numero_alunos": self.numero_alunos,
            "local_passeio": self.local,
            "evento": self.evento,
            "observacao": self.observacao,
            "data_autorizacao": self.data_autorizacao,
            "tempo_passeio": self.solicitacao_kit_lanche.get_tempo_passeio_display(),
            "kits": ", ".join(
                list(
                    self.solicitacao_kit_lanche.kits.all().values_list(
                        "nome", flat=True
                    )
                )
            ),
            "total_kits": self.quantidade_alimentacoes,
            "total_alunos": self.quantidade_alunos,
            "label_data": label_data,
            "data_log": data_log,
            "faixas_etarias": self.get_faixas_etarias_dict,
            "total_matriculados": self.total_matriculados_quando_criado,
            "id_externo": self.id_externo,
        }

    @property
    def solicitacoes_similares(self):
        tempo_passeio = self.solicitacao_kit_lanche.tempo_passeio
        data_evento = self.solicitacao_kit_lanche.data
        all_objects = SolicitacaoKitLancheCEIAvulsa.objects.filter(
            escola=self.escola
        ).exclude(status=SolicitacaoKitLancheCEIAvulsa.workflow_class.RASCUNHO)
        solicitacoes_similares = all_objects.filter(
            solicitacao_kit_lanche__data=data_evento,
            solicitacao_kit_lanche__tempo_passeio=tempo_passeio,
        )
        solicitacoes_similares = solicitacoes_similares.exclude(uuid=self.uuid)
        return solicitacoes_similares

    def __str__(self):
        return f"{self.escola} SOLICITA EM {self.local}"

    class Meta:
        verbose_name = "Solicitação de kit lanche CEI avulsa"
        verbose_name_plural = "Solicitações de kit lanche CEI avulsa"


class FaixaEtariaSolicitacaoKitLancheCEIAvulsa(
    TemChaveExterna, TemFaixaEtariaEQuantidade, MatriculadosQuandoCriado
):
    solicitacao_kit_lanche_avulsa = models.ForeignKey(
        "SolicitacaoKitLancheCEIAvulsa",
        on_delete=models.CASCADE,
        related_name="faixas_etarias",
    )

    def __str__(self):
        retorno = f"Faixa Etária de solicitação de kit lanche CEI avulsa {self.uuid}"
        retorno += f" da solicitação: {self.solicitacao_kit_lanche_avulsa.uuid}"
        return retorno

    class Meta:
        verbose_name = "Faixa Etária de solicitação de kit lanche CEI avulsa"
        verbose_name_plural = "Faixas Etárias de solicitação de kit lanche CEI avulsa"


class SolicitacaoKitLancheUnificada(
    ExportModelOperationsMixin("kit_lanche_unificada"),
    CriadoPor,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
    SolicitacaoForaDoPrazo,
    FluxoAprovacaoPartindoDaDiretoriaRegional,
    Logs,
    TemPrioridade,
    TemTerceirizadaConferiuGestaoAlimentacao,
):
    """Uma DRE pede para as suas escolas.

    lista_kit_lanche_igual é a mesma lista de kit lanche pra todos.
    não lista_kit_lanche_igual: cada escola tem sua lista de kit lanche

    QUANDO É lista_kit_lanche_igual: ex: passeio pra escola x,y,z no ibira (local)
    no dia 26 onde a escola x vai ter 100 alunos, a y 50 e a z 77 alunos.
    onde todos vao comemorar o dia da arvore (motivo)
    """

    # TODO: ao deletar este, deletar solicitacao_kit_lanche também que é uma tabela acessória
    # TODO: passar `local` para solicitacao_kit_lanche
    DESCRICAO = "Kit Lanche Unificado"

    outro_motivo = models.TextField(blank=True)
    local = models.CharField(max_length=160)
    evento = models.CharField(max_length=160, blank=True)
    lista_kit_lanche_igual = models.BooleanField(default=True)

    diretoria_regional = models.ForeignKey(
        "escola.DiretoriaRegional", on_delete=models.DO_NOTHING
    )
    solicitacao_kit_lanche = models.ForeignKey(
        SolicitacaoKitLanche, on_delete=models.DO_NOTHING
    )

    objects = models.Manager()  # Manager Padrão
    desta_semana = SolicitacaoUnificadaDestaSemanaManager()
    deste_mes = SolicitacaoUnificadaDesteMesManager()
    vencidos = SolicitacaoUnificadaVencidaManager()

    def possui_escola_na_solicitacao(self, escola):
        return escola.nome in str(
            self.escolas_quantidades.all().values("escola__nome").distinct()
        )

    @property
    def data(self):
        return self.solicitacao_kit_lanche.data

    @property
    def tipo(self):
        return "Kit Lanche Unificado"

    @property
    def path(self):
        return f"solicitacao-unificada/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-normal"

    @property
    def observacao(self):
        return self.solicitacao_kit_lanche.descricao

    @property
    def lote_nome(self):
        """Solicitação unificada é somente de um lote.

        Vide o  self.dividir_por_lote()
        """
        try:
            escola_quantidade = self.escolas_quantidades.first()
            lote_nome = escola_quantidade.escola.lote.nome
        except ObjectDoesNotExist:
            lote_nome = "Não tem lote"
        return lote_nome

    @property
    def lote(self):
        """Solicitação unificada é somente de um lote.

        Vide o  self.dividir_por_lote()
        """
        escola_quantidade = self.escolas_quantidades.first()
        lote = escola_quantidade.escola.lote
        return lote

    @property
    def quantidade_alimentacoes(self):
        # TODO: remover essa ou total_kit_lanche
        return self.total_kit_lanche

    @classmethod
    def get_pedidos_rascunho(cls, usuario):
        solicitacoes_unificadas = SolicitacaoKitLancheUnificada.objects.filter(
            criado_por=usuario,
            status=SolicitacaoKitLancheUnificada.workflow_class.RASCUNHO,
        )
        return solicitacoes_unificadas

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        resposta_sim_nao = kwargs.get("resposta_sim_nao", False)
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.SOLICITACAO_KIT_LANCHE_UNIFICADA,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
            resposta_sim_nao=resposta_sim_nao,
        )

    @property
    def quantidade_de_lotes(self):
        return self.escolas_quantidades.distinct("escola__lote").count()

    def dividir_por_lote(self):
        if self.quantidade_de_lotes > 1:
            if self.quantidade_de_lotes == 2:
                return self.dividir_por_dois_lotes()
            else:
                return self.dividir_por_tres_ou_mais_lotes()
        else:
            return SolicitacaoKitLancheUnificada.objects.filter(id=self.id)

    # TODO: melhorar esse metodo assim que tivermos um entendimento melhor
    def dividir_por_dois_lotes(self) -> models.QuerySet:
        primeiro_id = self.id
        primeiro_lote = self.escolas_quantidades.first().escola.lote  # type: ignore
        escolas_quantidades_desse_lote = self.escolas_quantidades.filter(
            escola__lote=primeiro_lote
        )
        for escola_quantidade in escolas_quantidades_desse_lote:
            self.escolas_quantidades.remove(escola_quantidade)
        solicitacao_segundo_lote = self
        solicitacao_segundo_lote.pk = None
        solicitacao_segundo_lote.uuid = uuid.uuid4()
        solicitacao_segundo_lote.save()
        solicitacao_segundo_lote.escolas_quantidades.set(escolas_quantidades_desse_lote)
        return SolicitacaoKitLancheUnificada.objects.filter(
            id__in=[primeiro_id, solicitacao_segundo_lote.id]
        )

    # TODO: se esse caso existir algum dia, implementar
    def dividir_por_tres_ou_mais_lotes(self):
        return

    @property
    def template_mensagem(self):
        template = TemplateMensagem.objects.get(
            tipo=TemplateMensagem.SOLICITACAO_KIT_LANCHE_UNIFICADA
        )
        template_troca = {
            "@id": self.id_externo,
            "@criado_em": str(self.solicitacao_kit_lanche.criado_em),
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
    def total_kit_lanche(self):
        if self.lista_kit_lanche_igual:
            total_alunos = (
                SolicitacaoKitLancheUnificada.objects.annotate(
                    total_alunos=Coalesce(
                        models.Sum("escolas_quantidades__quantidade_alunos"), 0
                    )
                )
                .get(id=self.id)
                .total_alunos
            )
            total_kit_lanche = self.solicitacao_kit_lanche.kits.all().count()
            return total_alunos * total_kit_lanche
        else:
            total_kit_lanche = 0
            for escola_quantidade in self.escolas_quantidades.all():
                total_kit_lanche += escola_quantidade.total_kit_lanche
            return total_kit_lanche

    def total_kit_lanche_escola(self, escola_uuid):
        try:
            return self.escolas_quantidades.get(
                escola__uuid=escola_uuid
            ).total_kit_lanche
        except EscolaQuantidade.DoesNotExist:
            return 0

    @property
    def numero_alunos(self):
        return self.escolas_quantidades.aggregate(Sum("quantidade_alunos"))[
            "quantidade_alunos__sum"
        ]

    def get_escolas_quantidades_dict(self, instituicao=None):
        escolas_quantidades = []
        qs_escolas_quantidades = self.escolas_quantidades.all()
        if instituicao:
            qs_escolas_quantidades = qs_escolas_quantidades.filter(escola=instituicao)
        for escola_quantidade in qs_escolas_quantidades:
            escolas_quantidades.append(
                {
                    "uuid": escola_quantidade.uuid,
                    "codigo": escola_quantidade.escola.codigo_eol,
                    "unidade_escolar": escola_quantidade.escola.nome,
                    "quantidade": escola_quantidade.quantidade_alunos,
                    "tempo_passeio": escola_quantidade.get_tempo_passeio_display(),
                    "opcao_desejada": ", ".join(
                        list(
                            escola_quantidade.kits.all().values_list("nome", flat=True)
                        )
                    ),
                    "total_kits": escola_quantidade.total_kit_lanche,
                }
            )
        return escolas_quantidades

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        from sme_sigpae_api.escola.models import Escola

        dict_ = {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": (
                f"{self.escolas_quantidades.count()} Escolas"
                if self.escolas_quantidades.count() > 1
                else self.escolas_quantidades.get().escola.nome
            ),
            "terceirizada": "Várias Terceirizadas",
            "tipo_doc": "Kit Lanche Unificado",
            "data_evento": self.data,
            "numero_alunos": self.numero_alunos,
            "local_passeio": self.local,
            "evento": self.evento,
            "observacao": self.observacao,
            "data_autorizacao": self.data_autorizacao,
            "tempo_passeio": self.solicitacao_kit_lanche.get_tempo_passeio_display(),
            "total_kits": self.quantidade_alimentacoes,
            "label_data": label_data,
            "data_log": data_log,
            "escolas_quantidades": self.get_escolas_quantidades_dict(),
            "id_externo": self.id_externo,
        }

        if isinstance(instituicao, Escola):
            dict_["unidade_educacional"] = instituicao.nome
            dict_["terceirizada"] = instituicao.lote.terceirizada.nome_fantasia
            dict_["numero_alunos"] = self.escolas_quantidades.get(
                escola=instituicao
            ).quantidade_alunos
            dict_["total_kits"] = self.total_kit_lanche_escola(instituicao.uuid)
            dict_["escolas_quantidades"] = self.get_escolas_quantidades_dict(
                instituicao
            )

        return dict_

    @property
    def solicitacoes_similares(self):
        tempo_passeio = self.solicitacao_kit_lanche.tempo_passeio
        data_evento = self.solicitacao_kit_lanche.data
        all_objects = SolicitacaoKitLancheUnificada.objects.filter(
            diretoria_regional=self.diretoria_regional
        ).exclude(status=SolicitacaoKitLancheUnificada.workflow_class.RASCUNHO)
        solicitacoes_similares = all_objects.filter(
            solicitacao_kit_lanche__data=data_evento,
            solicitacao_kit_lanche__tempo_passeio=tempo_passeio,
        )
        solicitacoes_similares = solicitacoes_similares.exclude(uuid=self.uuid)
        return solicitacoes_similares

    def __str__(self):
        dre = self.diretoria_regional
        return f"{dre} pedindo passeio em {self.local} com kits iguais? {self.lista_kit_lanche_igual}"

    class Meta:
        verbose_name = "Solicitação kit lanche unificada"
        verbose_name_plural = "Solicitações de  kit lanche unificadas"


class EscolaQuantidade(
    ExportModelOperationsMixin("escola_quantidade"),
    TemChaveExterna,
    TempoPasseio,
    CanceladoIndividualmente,
):
    quantidade_alunos = models.PositiveSmallIntegerField()
    solicitacao_unificada = models.ForeignKey(
        SolicitacaoKitLancheUnificada,
        on_delete=models.CASCADE,
        related_name="escolas_quantidades",
        blank=True,
        null=True,
    )
    kits = models.ManyToManyField(KitLanche, blank=True)
    escola = models.ForeignKey("escola.Escola", on_delete=models.DO_NOTHING)

    @property
    def total_kit_lanche(self):
        return self.quantidade_alunos * self.kits.all().count()

    def __str__(self):
        kit_lanche_personalizado = bool(self.kits.count())
        tempo_passeio = self.get_tempo_passeio_display()
        return f"{tempo_passeio} para {self.quantidade_alunos} alunos, kits diferenciados? {kit_lanche_personalizado}"

    class Meta:
        verbose_name = "Escola quantidade"
        verbose_name_plural = "Escolas quantidades"


class SolicitacaoKitLancheCEMEI(
    TemChaveExterna,
    FluxoAprovacaoPartindoDaEscola,
    TemIdentificadorExternoAmigavel,
    CriadoPor,
    TemPrioridade,
    Logs,
    SolicitacaoForaDoPrazo,
    CriadoEm,
    TemObservacao,
    TemTerceirizadaConferiuGestaoAlimentacao,
):
    TODOS = "TODOS"
    CEI = "CEI"
    EMEI = "EMEI"

    STATUS_CHOICES = ((TODOS, "Todos"), (CEI, "CEI"), (EMEI, "EMEI"))

    DESCRICAO = "Kit Lanche CEMEI"
    local = models.CharField(max_length=160)
    evento = models.CharField(max_length=160, blank=True)
    data = models.DateField("Data")
    escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.DO_NOTHING,
        related_name="solicitacoes_kit_lanche_cemei",
    )
    alunos_cei_e_ou_emei = models.CharField(
        choices=STATUS_CHOICES, max_length=10, default=TODOS
    )

    objects = models.Manager()  # Manager Padrão
    desta_semana = SolicitacoesKitLancheCemeiDestaSemanaManager()
    deste_mes = SolicitacoesKitLancheCemeiDesteMesManager()

    @property
    def tem_solicitacao_cei(self):
        return hasattr(self, "solicitacao_cei")

    @property
    def tem_solicitacao_emei(self):
        return hasattr(self, "solicitacao_emei")

    @property
    def tipo(self):
        return "Kit Lanche Passeio"

    @property
    def path(self):
        return f"solicitacao-de-kit-lanche-cemei/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-cemei"

    @property
    def numero_alunos(self):
        total = 0
        if self.tem_solicitacao_cei:
            total += self.solicitacao_cei.quantidade_alunos
        if self.tem_solicitacao_emei:
            total += self.solicitacao_emei.quantidade_alunos
        return total

    @property
    def total_kits(self):
        total = 0
        if self.tem_solicitacao_cei:
            total += self.solicitacao_cei.quantidade_alimentacoes
        if self.tem_solicitacao_emei:
            total += self.solicitacao_emei.quantidade_alimentacoes
        return total

    @property
    def quantidade_alimentacoes(self):
        return self.total_kits

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        resposta_sim_nao = kwargs.get("resposta_sim_nao", False)
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.SOLICITACAO_KIT_LANCHE_CEMEI,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
            resposta_sim_nao=resposta_sim_nao,
        )

    @property
    def get_solicitacao_cei_dict(self):
        if not self.tem_solicitacao_cei:
            return {}
        alunos_cei = []
        total_matriculados = 0
        total_alunos = 0
        if self.solicitacao_cei.faixas_quantidades.all():
            for faixa in self.solicitacao_cei.faixas_quantidades.all():
                total_alunos += faixa.quantidade_alunos
                total_matriculados += faixa.matriculados_quando_criado
                alunos_cei.append(
                    {
                        "faixa_etaria": faixa.faixa_etaria.__str__(),
                        "quantidade": faixa.quantidade_alunos,
                        "matriculados_quando_criado": faixa.matriculados_quando_criado,
                    }
                )
        return {
            "tempo_passeio": self.solicitacao_cei.get_tempo_passeio_display(),
            "alunos_cei": alunos_cei,
            "kits": ", ".join(
                list(self.solicitacao_cei.kits.all().values_list("nome", flat=True))
            ),
            "total_alunos": total_alunos,
            "total_matriculados": total_matriculados,
        }

    @property
    def get_solicitacao_emei_dict(self):
        if not self.tem_solicitacao_emei:
            return {}
        return {
            "tempo_passeio": self.solicitacao_emei.get_tempo_passeio_display(),
            "kits": ", ".join(
                list(self.solicitacao_emei.kits.all().values_list("nome", flat=True))
            ),
            "matriculados_quando_criado": self.solicitacao_emei.matriculados_quando_criado,
            "quantidade_alunos": self.solicitacao_emei.quantidade_alunos,
        }

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome,
            "terceirizada": self.rastro_terceirizada.nome,
            "tipo_doc": "Kit Lanche Passeio de CEMEI",
            "data_evento": self.data,
            "numero_alunos": self.numero_alunos,
            "label_data": label_data,
            "data_log": data_log,
            "local_passeio": self.local,
            "evento": self.evento,
            "observacao": self.observacao,
            "data_autorizacao": self.data_autorizacao,
            "solicitacao_cei": self.get_solicitacao_cei_dict,
            "solicitacao_emei": self.get_solicitacao_emei_dict,
            "total_kits": self.total_kits,
            "id_externo": self.id_externo,
        }

    @property
    def solicitacoes_similares(self):
        filtros = {"data": self.data, "escola": self.escola}
        if self.tem_solicitacao_cei:
            filtros["solicitacao_cei__tempo_passeio"] = (
                self.solicitacao_cei.tempo_passeio
            )
        if self.tem_solicitacao_emei:
            filtros["solicitacao_emei__tempo_passeio"] = (
                self.solicitacao_emei.tempo_passeio
            )
        return SolicitacaoKitLancheCEMEI.objects.filter(**filtros).exclude(
            Q(uuid=self.uuid)
            | Q(status=SolicitacaoKitLancheCEMEI.workflow_class.RASCUNHO)
        )

    class Meta:
        verbose_name = "Solicitação Kit Lanche CEMEI"
        verbose_name_plural = "Solicitações Kit Lanche CEMEI"
        ordering = ("-criado_em",)


class SolicitacaoKitLancheCEIdaCEMEI(TemChaveExterna, TempoPasseio):
    kits = models.ManyToManyField(KitLanche, blank=True)
    alunos_com_dieta_especial_participantes = models.ManyToManyField("escola.Aluno")
    solicitacao_kit_lanche_cemei = models.OneToOneField(
        SolicitacaoKitLancheCEMEI,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="solicitacao_cei",
    )

    @property
    def quantidade_alimentacoes(self):
        return (
            sum(self.faixas_quantidades.values_list("quantidade_alunos", flat=True))
            * self.kits.count()
        )

    @property
    def quantidade_alunos(self):
        return sum(self.faixas_quantidades.values_list("quantidade_alunos", flat=True))

    @property
    def quantidade_matriculados(self):
        return sum(
            self.faixas_quantidades.values_list("matriculados_quando_criado", flat=True)
        )

    @property
    def nomes_kits(self):
        return ", ".join(list(self.kits.values_list("nome", flat=True)))

    @property
    def tem_alunos_com_dieta(self):
        return self.alunos_com_dieta_especial_participantes.exists()

    class Meta:
        verbose_name = "Solicitação Kit Lanche CEI da EMEI"
        verbose_name_plural = "Solicitações Kit Lanche CEI da EMEI"


class FaixasQuantidadesKitLancheCEIdaCEMEI(TemChaveExterna, MatriculadosQuandoCriado):
    solicitacao_kit_lanche_cei_da_cemei = models.ForeignKey(
        SolicitacaoKitLancheCEIdaCEMEI,
        on_delete=models.CASCADE,
        related_name="faixas_quantidades",
    )
    quantidade_alunos = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )
    faixa_etaria = models.ForeignKey("escola.FaixaEtaria", on_delete=models.PROTECT)

    class Meta:
        ordering = ("faixa_etaria__inicio",)
        verbose_name = (
            "Faixa e quantidade de alunos da CEI da solicitação kit lanche CEMEI"
        )
        verbose_name_plural = (
            "Faixas e quantidade de alunos da CEI das solicitações kit lanche CEMEI"
        )


class SolicitacaoKitLancheEMEIdaCEMEI(
    TemChaveExterna, TempoPasseio, MatriculadosQuandoCriado
):
    kits = models.ManyToManyField(KitLanche, blank=True)
    quantidade_alunos = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )
    alunos_com_dieta_especial_participantes = models.ManyToManyField("escola.Aluno")
    solicitacao_kit_lanche_cemei = models.OneToOneField(
        SolicitacaoKitLancheCEMEI,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="solicitacao_emei",
    )

    @property
    def nomes_kits(self):
        return ", ".join(list(self.kits.values_list("nome", flat=True)))

    @property
    def quantidade_alimentacoes(self):
        return self.quantidade_alunos * self.kits.count()

    @property
    def tem_alunos_com_dieta(self):
        return self.alunos_com_dieta_especial_participantes.exists()

    class Meta:
        verbose_name = "Solicitação Kit Lanche CEI da EMEI"
        verbose_name_plural = "Solicitações Kit Lanche CEI da EMEI"
