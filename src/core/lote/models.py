from __future__ import annotations

import datetime
import uuid
from copy import deepcopy

from django.db import models, transaction
from django.db.models import Q, Sum

from src.dados_comuns.constants import StringsCaminhoModelos

from ...cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
from ...cardapio.alteracao_tipo_alimentacao_cemei.models import AlteracaoCardapioCEMEI
from ...cardapio.inversao_dia_cardapio.models import InversaoCardapio
from ...cardapio.suspensao_alimentacao.models import GrupoSuspensaoAlimentacao
from ...dados_comuns.behaviors import Iniciais, Nomeavel, TemChaveExterna
from ...dados_comuns.fluxo_status import (
    FluxoAprovacaoPartindoDaEscola,
    FluxoDietaEspecialPartindoDaEscola,
    FluxoInformativoPartindoDaEscola,
)
from ...dados_comuns.utils import (
    clonar_objeto,
    copiar_logs,
    cria_copias_fk,
    cria_copias_m2m,
)
from ...inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
    InclusaoAlimentacaoDaCEI,
    InclusaoDeAlimentacaoCEMEI,
)
from ..constants import ESCOLA_TIPO_GESTAO_NOME
from ..escola.models import AlunosMatriculadosPeriodoEscola, TipoGestao


class Lote(TemChaveExterna, Nomeavel, Iniciais):
    """Lote de escolas."""

    tipo_gestao = models.ForeignKey(
        TipoGestao,
        on_delete=models.DO_NOTHING,
        related_name="lotes",
        null=True,
        blank=True,
    )
    diretoria_regional = models.ForeignKey(
        StringsCaminhoModelos.MODEL_DIRETORIA_REGIONAL.value,
        on_delete=models.DO_NOTHING,
        related_name="lotes",
        null=True,
        blank=True,
    )
    terceirizada = models.ForeignKey(
        StringsCaminhoModelos.MODEL_TERCEIRIZADA.value,
        on_delete=models.DO_NOTHING,
        related_name="lotes",
        null=True,
        blank=True,
    )

    @property
    def escolas(self):
        return self.escolas

    @property
    def quantidade_alunos(self):
        quantidade_result = AlunosMatriculadosPeriodoEscola.objects.filter(
            escola__in=self.escolas.all(), tipo_turma="REGULAR"
        ).aggregate(Sum("quantidade_alunos"))
        return quantidade_result.get("quantidade_alunos__sum") or 0

    @property
    def quantidade_alunos_terceirizada(self):
        quantidade_result = AlunosMatriculadosPeriodoEscola.objects.filter(
            escola__in=self.escolas.all(),
            tipo_turma="REGULAR",
            escola__tipo_gestao__nome=ESCOLA_TIPO_GESTAO_NOME,
        ).aggregate(Sum("quantidade_alunos"))
        return quantidade_result.get("quantidade_alunos__sum") or 0

    def _transferir_solicitacoes_gestao_alimentacao(
        self, terceirizada, data_da_virada: datetime.date
    ) -> None:
        """
        Transfere Solicitações de Gestão de Alimentação pendentes de autorização ou autorizadas à serem atendidadas,
        ou seja, com datas futuras à transferência do lote para a empresa nova.
        """
        canceladas_ou_negadas = Q(
            status__in=[
                FluxoAprovacaoPartindoDaEscola.workflow_class.CODAE_NEGOU_PEDIDO,
                FluxoAprovacaoPartindoDaEscola.workflow_class.CANCELADO_AUTOMATICAMENTE,
                FluxoAprovacaoPartindoDaEscola.workflow_class.DRE_NAO_VALIDOU_PEDIDO_ESCOLA,
                FluxoAprovacaoPartindoDaEscola.workflow_class.ESCOLA_CANCELOU,
            ]
        )
        canceladas_suspensao = Q(
            status__in=[FluxoInformativoPartindoDaEscola.workflow_class.ESCOLA_CANCELOU]
        )
        self.inclusao_alimentacao_inclusaoalimentacaocontinua_rastro_lote.exclude(
            canceladas_ou_negadas | Q(data_inicial__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.inclusao_alimentacao_grupoinclusaoalimentacaonormal_rastro_lote.exclude(
            canceladas_ou_negadas | Q(inclusoes_normais__data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.inclusao_alimentacao_inclusaoalimentacaodacei_rastro_lote.exclude(
            canceladas_ou_negadas
            | Q(dias_motivos_da_inclusao_cei__data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.inclusao_alimentacao_inclusaodealimentacaocemei_rastro_lote.exclude(
            canceladas_ou_negadas
            | Q(dias_motivos_da_inclusao_cemei__data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.cardapio_alteracaocardapio_rastro_lote.exclude(
            canceladas_ou_negadas | Q(data_inicial__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.cardapio_alteracaocardapiocei_rastro_lote.exclude(
            canceladas_ou_negadas | Q(data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.cardapio_alteracaocardapiocemei_rastro_lote.exclude(
            canceladas_ou_negadas
            | Q(alterar_dia__lt=data_da_virada)
            | Q(data_inicial__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.kit_lanche_solicitacaokitlancheavulsa_rastro_lote.exclude(
            canceladas_ou_negadas | Q(solicitacao_kit_lanche__data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.kit_lanche_solicitacaokitlancheceiavulsa_rastro_lote.exclude(
            canceladas_ou_negadas | Q(solicitacao_kit_lanche__data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.kit_lanche_solicitacaokitlanchecemei_rastro_lote.exclude(
            canceladas_ou_negadas | Q(data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.cardapio_inversaocardapio_rastro_lote.exclude(
            canceladas_ou_negadas
            | Q(data_de_inversao__lt=data_da_virada)
            | Q(data_para_inversao__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.cardapio_gruposuspensaoalimentacao_rastro_lote.exclude(
            canceladas_suspensao | Q(suspensoes_alimentacao__data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.cardapio_suspensaoalimentacaodacei_rastro_lote.exclude(
            canceladas_suspensao | Q(data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)

    def _transferir_solicitacoes_gestao_alimentacao_com_datas_no_passado_e_no_presente(
        self, terceirizada_nova, data_virada: datetime.date
    ) -> None:
        """
        Realiza a transferência de todas as solicitações de Gestão de Alimentação autorizadas
        com datas remanescentes no passado/presente e futuro.
        """
        terceirizada_pre_transferencia = self.terceirizada

        for tipo, cfg in self.TRANSFERENCIAS_CONFIG.items():
            self._transferir_lote_generico_config(
                tipo, data_virada, terceirizada_pre_transferencia, terceirizada_nova
            )

    TRANSFERENCIAS_CONFIG = {
        # ---------------- Inclusões ----------------
        "inclusoes_continuas": {
            "query_attr": "inclusao_alimentacao_inclusaoalimentacaocontinua_rastro_lote",
            "model": InclusaoAlimentacaoContinua,
            "status_field": "status",
            "status_value": lambda cls: cls.workflow_class.CODAE_AUTORIZADO,
            "filtros_extra": {"data_final__gte": "data_virada"},
            "cria_fk_func": "_cria_objetos_fk_inclusao_continua_copia",
            "atualiza_original": "_atualiza_inclusao_continua_original",
            "atualiza_copia": "_atualiza_inclusao_continua_copia_para_nova_terceirizada",
        },
        "inclusoes_normais": {
            "query_attr": "inclusao_alimentacao_grupoinclusaoalimentacaonormal_rastro_lote",
            "model": GrupoInclusaoAlimentacaoNormal,
            "status_field": "status",
            "status_value": lambda cls: cls.workflow_class.CODAE_AUTORIZADO,
            "filtros_extra": {
                "inclusoes_normais__data__gte": "data_virada",
                "inclusoes_normais__cancelado": False,
            },
            "cria_fk_func": "_cria_objetos_fk_inclusao_normal_copia",
            "atualiza_original": "_atualiza_inclusao_normal_original",
            "atualiza_copia": "_atualiza_inclusao_normal_copia_para_nova_terceirizada",
        },
        "inclusoes_cei": {
            "query_attr": "inclusao_alimentacao_inclusaoalimentacaodacei_rastro_lote",
            "model": InclusaoAlimentacaoDaCEI,
            "status_field": "status",
            "status_value": lambda cls: cls.workflow_class.CODAE_AUTORIZADO,
            "filtros_extra": {
                "dias_motivos_da_inclusao_cei__data__gte": "data_virada",
                "dias_motivos_da_inclusao_cei__cancelado": False,
            },
            "cria_fk_func": "_cria_objetos_fk_inclusao_cei_copia",
            "atualiza_original": "_atualiza_inclusao_cei_original",
            "atualiza_copia": "_atualiza_inclusao_cei_copia_para_nova_terceirizada",
        },
        "inclusoes_cemei": {
            "query_attr": "inclusao_alimentacao_inclusaodealimentacaocemei_rastro_lote",
            "model": InclusaoDeAlimentacaoCEMEI,
            "status_field": "status",
            "status_value": lambda cls: cls.workflow_class.CODAE_AUTORIZADO,
            "filtros_extra": {
                "dias_motivos_da_inclusao_cemei__data__gte": "data_virada",
                "dias_motivos_da_inclusao_cemei__cancelado": False,
            },
            "cria_fk_func": "_cria_objetos_fk_inclusao_cemei_copia",
            "atualiza_original": "_atualiza_inclusao_cemei_original",
            "atualiza_copia": "_atualiza_inclusao_cemei_copia_para_nova_terceirizada",
        },
        # ---------------- Alterações ----------------
        "alteracoes": {
            "query_attr": "cardapio_alteracaocardapio_rastro_lote",
            "model": AlteracaoCardapio,
            "status_field": "status",
            "status_value": lambda cls: cls.workflow_class.CODAE_AUTORIZADO,
            "filtros_extra": {
                "datas_intervalo__data__gte": "data_virada",
                "datas_intervalo__cancelado": False,
            },
            "cria_fk_func": "_cria_objetos_fk_alteracao_copia",
            "atualiza_original": "_atualiza_alteracao_original",
            "atualiza_copia": "_atualiza_alteracao_copia_para_nova_terceirizada",
        },
        "alteracoes_cemei": {
            "query_attr": "cardapio_alteracaocardapiocemei_rastro_lote",
            "model": AlteracaoCardapioCEMEI,
            "status_field": "status",
            "status_value": lambda cls: cls.workflow_class.CODAE_AUTORIZADO,
            "filtros_extra": {
                "datas_intervalo__data__gte": "data_virada",
                "datas_intervalo__cancelado": False,
            },
            "cria_fk_func": "_cria_objetos_fk_alteracao_cemei_copia",
            "atualiza_original": "_atualiza_alteracao_original",
            "atualiza_copia": "_atualiza_alteracao_copia_para_nova_terceirizada",
        },
        # ---------------- Suspensões ----------------
        "suspensoes": {
            "query_attr": "cardapio_gruposuspensaoalimentacao_rastro_lote",
            "model": GrupoSuspensaoAlimentacao,
            "status_field": "status",
            "status_value": lambda cls: cls.workflow_class.INFORMADO,
            "filtros_extra": {
                "suspensoes_alimentacao__data__gte": "data_virada",
                "suspensoes_alimentacao__cancelado": False,
            },
            "cria_fk_func": "_cria_objetos_fk_suspensao_copia",
            "atualiza_original": "_atualiza_suspensao_original",
            "atualiza_copia": "_atualiza_suspensao_copia_para_nova_terceirizada",
        },
        # ---------------- Inversões ----------------
        "inversoes": {
            "query_attr": "cardapio_inversaocardapio_rastro_lote",
            "model": InversaoCardapio,
            "status_field": "status",
            "status_value": lambda cls: cls.workflow_class.CODAE_AUTORIZADO,
            "filtros_extra": [
                {"data_de_inversao__gte": "data_virada"},
                {"data_para_inversao__gte": "data_virada"},
                {"data_de_inversao_2__gte": "data_virada"},
                {"data_para_inversao_2__gte": "data_virada"},
            ],
            "cria_fk_func": "_cria_objetos_fk_inversao_copia",
            "atualiza_original": "_atualiza_inversao_original",
            "atualiza_copia": "_atualiza_inversao_copia_para_nova_terceirizada",
        },
    }

    def _transferir_lote_generico_config(
        self, tipo, data_virada, terceirizada_pre_transferencia, terceirizada_nova
    ):
        cfg = self.TRANSFERENCIAS_CONFIG[tipo]

        model_class = self._get_model_class(cfg)
        status_value = cfg["status_value"](model_class)

        queryset = self._get_queryset_base(
            cfg, terceirizada_pre_transferencia, status_value
        )
        queryset = self._aplicar_filtros_extra(queryset, cfg, data_virada)
        queryset = queryset.distinct()

        if not queryset.exists():
            return

        cria_fk_func = getattr(self, cfg["cria_fk_func"])
        atualiza_original_func = getattr(self, cfg["atualiza_original"])
        atualiza_copia_func = getattr(self, cfg["atualiza_copia"])

        for original in queryset:
            self._transferir_objeto_individual(
                original,
                model_class,
                data_virada,
                terceirizada_nova,
                cria_fk_func,
                atualiza_original_func,
                atualiza_copia_func,
            )

    def _get_model_class(self, cfg):
        """Obtém a classe de modelo a partir do nome definido na config."""
        return cfg["model"]

    def _get_queryset_base(self, cfg, terceirizada_pre_transferencia, status_value):
        """Retorna o queryset base filtrando por status e terceirizada."""
        return getattr(self, cfg["query_attr"]).filter(
            **{
                cfg["status_field"]: status_value,
                "rastro_terceirizada": terceirizada_pre_transferencia,
            }
        )

    def _aplicar_filtros_extra(self, queryset_base, cfg, data_virada):
        """Aplica filtros extras definidos na config.
        - Se for uma lista, aplica OR (com Q)
        - Se for dict, aplica AND normalmente
        """
        filtros_extra = cfg.get("filtros_extra", {})

        if isinstance(filtros_extra, list):
            q_obj = Q()
            for filtro in filtros_extra:
                resolved = self._resolver_filtros(filtro, data_virada)
                q_obj |= Q(**resolved)
            return queryset_base.filter(q_obj)

        resolved = self._resolver_filtros(filtros_extra, data_virada)
        return queryset_base.filter(**resolved)

    def _resolver_filtros(self, filtro_dict, data_virada):
        """Substitui valores simbólicos ('data_virada') por valores reais."""
        return {
            campo: (data_virada if valor == "data_virada" else valor)
            for campo, valor in filtro_dict.items()
        }

    def _transferir_objeto_individual(
        self,
        original,
        model_class,
        data_virada,
        terceirizada_nova,
        cria_fk_func,
        atualiza_original_func,
        atualiza_copia_func,
    ):
        """Duplica o objeto, cria relacionamentos e atualiza campos."""
        uuid_original = original.uuid
        copia = clonar_objeto(original)
        original = model_class.objects.get(uuid=uuid_original)

        cria_fk_func(copia, original)
        atualiza_original_func(original, data_virada)
        atualiza_copia_func(copia, data_virada, terceirizada_nova)

    def _criar_copias_fk(self, original, copia, campos_fk, relacao):
        for campo_fk in campos_fk:
            cria_copias_fk(original, campo_fk, relacao, copia)

    # Inclusão Contínua
    def _cria_objetos_fk_inclusao_continua_copia(self, copia, original):
        self._criar_copias_fk(
            original,
            copia,
            ["quantidades_por_periodo"],
            "inclusao_alimentacao_continua",
        )
        copiar_logs(original, copia)

    def _atualiza_inclusao_continua_original(self, original, data_virada):
        original.data_final = data_virada - datetime.timedelta(days=1)
        original.save()

    def _atualiza_inclusao_continua_copia_para_nova_terceirizada(
        self, copia, data_virada, terceirizada_nova
    ):
        copia.data_inicial = data_virada
        copia.rastro_terceirizada = terceirizada_nova
        copia.terceirizada_conferiu_gestao = False
        copia.save()

    # Inclusão Normal
    def _cria_objetos_fk_inclusao_normal_copia(self, copia, original):
        self._criar_copias_fk(
            original, copia, ["quantidades_por_periodo"], "grupo_inclusao_normal"
        )
        self._criar_copias_fk(original, copia, ["inclusoes_normais"], "grupo_inclusao")
        copiar_logs(original, copia)

    def _atualiza_inclusao_normal_original(self, original, data_virada):
        original.inclusoes_normais.filter(data__gte=data_virada).delete()

    def _atualiza_inclusao_normal_copia_para_nova_terceirizada(
        self, copia, data_virada, terceirizada_nova
    ):
        copia.inclusoes_normais.filter(data__lt=data_virada).delete()
        copia.rastro_terceirizada = terceirizada_nova
        copia.terceirizada_conferiu_gestao = False
        copia.save()

    # Inclusão CEI
    def _cria_objetos_fk_inclusao_cei_copia(self, copia, original):
        self._criar_copias_fk(
            original,
            copia,
            ["quantidade_alunos_da_inclusao"],
            "inclusao_alimentacao_da_cei",
        )
        self._criar_copias_fk(
            original, copia, ["dias_motivos_da_inclusao_cei"], "inclusao_cei"
        )
        copiar_logs(original, copia)

    def _atualiza_inclusao_cei_original(self, original, data_virada):
        original.dias_motivos_da_inclusao_cei.filter(data__gte=data_virada).delete()

    def _atualiza_inclusao_cei_copia_para_nova_terceirizada(
        self, copia, data_virada, terceirizada_nova
    ):
        copia.dias_motivos_da_inclusao_cei.filter(data__lt=data_virada).delete()
        copia.rastro_terceirizada = terceirizada_nova
        copia.terceirizada_conferiu_gestao = False
        copia.save()

    # Inclusão CEMEI
    def _cria_objetos_fk_inclusao_cemei_copia(self, copia, original):
        self._criar_copias_fk(
            original,
            copia,
            [
                "dias_motivos_da_inclusao_cemei",
                "quantidade_alunos_cei_da_inclusao_cemei",
                "quantidade_alunos_emei_da_inclusao_cemei",
            ],
            "inclusao_alimentacao_cemei",
        )
        copiar_logs(original, copia)

    def _atualiza_inclusao_cemei_original(self, original, data_virada):
        original.dias_motivos_da_inclusao_cemei.filter(data__gte=data_virada).delete()

    def _atualiza_inclusao_cemei_copia_para_nova_terceirizada(
        self, copia, data_virada, terceirizada_nova
    ):
        copia.dias_motivos_da_inclusao_cemei.filter(data__lt=data_virada).delete()
        copia.rastro_terceirizada = terceirizada_nova
        copia.terceirizada_conferiu_gestao = False
        copia.save()

    # Alterações
    def _cria_objetos_fk_alteracao_copia(self, copia, original):
        self._criar_copias_fk(
            original,
            copia,
            ["datas_intervalo", "substituicoes_periodo_escolar"],
            "alteracao_cardapio",
        )
        copiar_logs(original, copia)

    def _cria_objetos_fk_alteracao_cemei_copia(self, copia, original):
        self._criar_copias_fk(
            original,
            copia,
            [
                "substituicoes_cemei_cei_periodo_escolar",
                "substituicoes_cemei_emei_periodo_escolar",
            ],
            "alteracao_cardapio",
        )
        self._criar_copias_fk(
            original, copia, ["datas_intervalo"], "alteracao_cardapio_cemei"
        )
        for index, substituicao_cemei_cei in enumerate(
            original.substituicoes_cemei_cei_periodo_escolar.all().order_by("id")
        ):
            for faixa_etaria in substituicao_cemei_cei.faixas_etarias.all():
                faixa_etaria_copia = deepcopy(faixa_etaria)
                faixa_etaria_copia.id = None
                faixa_etaria_copia.uuid = uuid.uuid4()
                faixa_etaria_copia.substituicao_alimentacao = (
                    copia.substituicoes_cemei_cei_periodo_escolar.all().order_by("id")[
                        index
                    ]
                )
                faixa_etaria_copia.save()
        copiar_logs(original, copia)

    def _atualiza_alteracao_original(self, original, data_virada):
        original.datas_intervalo.filter(data__gte=data_virada).delete()
        data_pre_virada = data_virada - datetime.timedelta(days=1)
        original.data_final = data_pre_virada
        original.save()

    def _atualiza_alteracao_copia_para_nova_terceirizada(
        self, copia, data_virada, terceirizada_nova
    ):
        copia.datas_intervalo.filter(data__lt=data_virada).delete()
        copia.data_inicial = data_virada
        copia.rastro_terceirizada = terceirizada_nova
        copia.terceirizada_conferiu_gestao = False
        copia.save()

    # Suspensões
    def _cria_objetos_fk_suspensao_copia(self, copia, original):
        self._criar_copias_fk(
            original,
            copia,
            ["quantidades_por_periodo", "suspensoes_alimentacao"],
            "grupo_suspensao",
        )
        copiar_logs(original, copia)

    def _atualiza_suspensao_original(self, original, data_virada):
        original.suspensoes_alimentacao.filter(data__gte=data_virada).delete()

    def _atualiza_suspensao_copia_para_nova_terceirizada(
        self, copia, data_virada, terceirizada_nova
    ):
        copia.suspensoes_alimentacao.filter(data__lt=data_virada).delete()
        copia.rastro_terceirizada = terceirizada_nova
        copia.terceirizada_conferiu_gestao = False
        copia.save()

    # Inversões
    def _cria_objetos_fk_inversao_copia(self, copia, original):
        campos_m2m = ["tipos_alimentacao"]
        for campo_m2m in campos_m2m:
            cria_copias_m2m(original, campo_m2m, copia)
        copiar_logs(original, copia)

    def _atualiza_inversao_original(self, original, data_virada):
        return

    def _atualiza_inversao_copia_para_nova_terceirizada(
        self, copia, _, terceirizada_nova
    ):
        copia.rastro_terceirizada = terceirizada_nova
        copia.terceirizada_conferiu_gestao = False
        copia.save()

    def _transferir_dietas_especiais(self, terceirizada_nova) -> None:
        """
        Transfere dietas especiais ativas e autorizadas para a nova empresa do lote
        """
        canceladas_ou_negadas_ou_inativas = Q(
            status__in=[
                FluxoDietaEspecialPartindoDaEscola.workflow_class.CANCELADO_ALUNO_MUDOU_ESCOLA,
                FluxoDietaEspecialPartindoDaEscola.workflow_class.CODAE_NEGOU_PEDIDO,
                FluxoDietaEspecialPartindoDaEscola.workflow_class.ESCOLA_CANCELOU,
                FluxoDietaEspecialPartindoDaEscola.workflow_class.TERMINADA_AUTOMATICAMENTE_SISTEMA,
                FluxoDietaEspecialPartindoDaEscola.workflow_class.CANCELADO_ALUNO_NAO_PERTENCE_REDE,
                FluxoDietaEspecialPartindoDaEscola.workflow_class.CODAE_AUTORIZOU_INATIVACAO,
                FluxoDietaEspecialPartindoDaEscola.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
                FluxoDietaEspecialPartindoDaEscola.workflow_class.CANCELADO_ENCERRAMENTO_MATRICULA,
            ],
        )
        self.dieta_especial_solicitacaodietaespecial_rastro_lote.exclude(
            canceladas_ou_negadas_ou_inativas
        ).exclude(
            status=FluxoDietaEspecialPartindoDaEscola.workflow_class.CODAE_AUTORIZADO,
            ativo=False,
        ).update(
            rastro_terceirizada=terceirizada_nova, conferido=False
        )

    @transaction.atomic
    def transferir_lote(
        self, terceirizada_nova, data_da_virada=datetime.date.today()
    ) -> None:
        """
        Realiza a transferência das solicitações de Gestão de Alimentação e Dieta Especial para a nova
        empresa a assumir o fornecimento do lote.
        """
        self._transferir_solicitacoes_gestao_alimentacao(
            terceirizada_nova, data_da_virada
        )
        self._transferir_solicitacoes_gestao_alimentacao_com_datas_no_passado_e_no_presente(
            terceirizada_nova, data_da_virada
        )
        self._transferir_dietas_especiais(terceirizada_nova)

    def __str__(self):
        nome_dre = (
            self.diretoria_regional.nome
            if self.diretoria_regional
            else "sem DRE definida"
        )
        return f"{self.nome} - {nome_dre}"

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        ordering = ("nome",)
