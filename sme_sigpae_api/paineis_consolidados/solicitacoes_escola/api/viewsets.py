import datetime
import unicodedata

from dateutil.relativedelta import relativedelta
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from sme_sigpae_api.cardapio.api.serializers.serializers import (
    VinculoTipoAlimentoPeriodoSerializer,
)
from sme_sigpae_api.cardapio.base.models import (
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from sme_sigpae_api.dados_comuns.permissions import PermissaoParaRecuperarDietaEspecial
from sme_sigpae_api.escola.models import Escola, PeriodoEscolar
from sme_sigpae_api.inclusao_alimentacao.models import GrupoInclusaoAlimentacaoNormal
from sme_sigpae_api.kit_lanche.models import SolicitacaoKitLancheUnificada
from sme_sigpae_api.medicao_inicial.models import SolicitacaoMedicaoInicial
from sme_sigpae_api.paineis_consolidados.api.constants import (
    AGUARDANDO_INICIO_VIGENCIA_DIETA_ESPECIAL,
    ALTERACOES_ALIMENTACAO_AUTORIZADAS,
    AUTORIZADAS_TEMPORARIAMENTE_DIETA_ESPECIAL,
    AUTORIZADOS,
    AUTORIZADOS_DIETA_ESPECIAL,
    CANCELADOS,
    CANCELADOS_DIETA_ESPECIAL,
    CEU_GESTAO_PERIODOS_COM_SOLICITACOES_AUTORIZADAS,
    FILTRO_ESCOLA_UUID,
    INATIVAS_DIETA_ESPECIAL,
    INATIVAS_TEMPORARIAMENTE_DIETA_ESPECIAL,
    INCLUSOES_AUTORIZADAS,
    INCLUSOES_ETEC_AUTORIZADAS,
    KIT_LANCHES_AUTORIZADAS,
    NEGADOS,
    NEGADOS_DIETA_ESPECIAL,
    PENDENTES_AUTORIZACAO,
    PENDENTES_AUTORIZACAO_DIETA_ESPECIAL,
    SUSPENSOES_AUTORIZADAS,
)
from sme_sigpae_api.paineis_consolidados.api.serializers import SolicitacoesSerializer
from sme_sigpae_api.paineis_consolidados.api.viewsets import SolicitacoesViewSet
from sme_sigpae_api.paineis_consolidados.models import SolicitacoesEscola
from sme_sigpae_api.paineis_consolidados.utils.utils import (
    formata_resultado_inclusoes_etec_autorizadas,
    get_numero_alunos_alteracao_alimentacao,
    tratar_append_return_dict,
    tratar_data_evento_final_no_mes,
    tratar_dias_duplicados,
    tratar_inclusao_continua,
    tratar_periodo_parcial,
    tratar_periodo_parcial_cemei,
)


class EscolaSolicitacoesViewSet(SolicitacoesViewSet):
    lookup_field = "uuid"
    queryset = SolicitacoesEscola.objects.all()
    permission_classes = (
        IsAuthenticated,
        PermissaoParaRecuperarDietaEspecial,
    )
    serializer_class = SolicitacoesSerializer

    @action(detail=False, methods=["GET"], url_path=f"{PENDENTES_AUTORIZACAO}")
    def pendentes_autorizacao(self, request):
        escola_uuid = request.user.vinculo_atual.instituicao.uuid
        query_set = SolicitacoesEscola.get_pendentes_autorizacao(
            escola_uuid=escola_uuid
        )
        query_set = SolicitacoesEscola.busca_filtro(query_set, request.query_params)
        return self._retorno_base(query_set)

    @action(detail=False, methods=["GET"], url_path=f"{AUTORIZADOS}")
    def autorizados(self, request):
        escola_uuid = request.user.vinculo_atual.instituicao.uuid
        query_set = SolicitacoesEscola.get_autorizados(escola_uuid=escola_uuid)
        query_set = SolicitacoesEscola.busca_filtro(query_set, request.query_params)
        return self._retorno_base(query_set)

    @action(detail=False, methods=["GET"], url_path=f"{NEGADOS}")
    def negados(self, request):
        escola_uuid = request.user.vinculo_atual.instituicao.uuid
        query_set = SolicitacoesEscola.get_negados(escola_uuid=escola_uuid)
        query_set = SolicitacoesEscola.busca_filtro(query_set, request.query_params)
        return self._retorno_base(query_set)

    @action(detail=False, methods=["GET"], url_path=f"{CANCELADOS}")
    def cancelados(self, request):
        escola_uuid = request.user.vinculo_atual.instituicao.uuid
        query_set = SolicitacoesEscola.get_cancelados(escola_uuid=escola_uuid)
        query_set = SolicitacoesEscola.busca_filtro(query_set, request.query_params)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{PENDENTES_AUTORIZACAO_DIETA_ESPECIAL}/{FILTRO_ESCOLA_UUID}",
    )
    def pendentes_autorizacao_dieta_especial(self, request, escola_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesEscola.get_pendentes_dieta_especial(
            escola_uuid=escola_uuid
        )
        query_set = SolicitacoesEscola.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{AUTORIZADOS_DIETA_ESPECIAL}/{FILTRO_ESCOLA_UUID}",
    )
    def autorizados_dieta_especial(self, request, escola_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesEscola.get_autorizados_dieta_especial(
            escola_uuid=escola_uuid
        )
        query_set = SolicitacoesEscola.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{AUTORIZADAS_TEMPORARIAMENTE_DIETA_ESPECIAL}/{FILTRO_ESCOLA_UUID}",
    )
    def autorizadas_temporariamente_dieta_especial(self, request, escola_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesEscola.get_autorizadas_temporariamente_dieta_especial(
            escola_uuid=escola_uuid
        )
        query_set = SolicitacoesEscola.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{AGUARDANDO_INICIO_VIGENCIA_DIETA_ESPECIAL}/{FILTRO_ESCOLA_UUID}",
    )
    def aguardando_inicio_vigencia_dieta_especial(self, request, escola_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesEscola.get_aguardando_vigencia_dieta_especial(
            escola_uuid=escola_uuid
        )
        query_set = SolicitacoesEscola.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{INATIVAS_TEMPORARIAMENTE_DIETA_ESPECIAL}/{FILTRO_ESCOLA_UUID}",
    )
    def inativas_temporariamente_dieta_especial(self, request, escola_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesEscola.get_inativas_temporariamente_dieta_especial(
            escola_uuid=escola_uuid
        )
        query_set = SolicitacoesEscola.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{INATIVAS_DIETA_ESPECIAL}/{FILTRO_ESCOLA_UUID}",
        permission_classes=(
            IsAuthenticated,
            PermissaoParaRecuperarDietaEspecial,
        ),
    )
    def inativas_dieta_especial(self, request, escola_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesEscola.get_inativas_dieta_especial(
            escola_uuid=escola_uuid
        )
        query_set = SolicitacoesEscola.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{NEGADOS_DIETA_ESPECIAL}/{FILTRO_ESCOLA_UUID}",
    )
    def negados_dieta_especial(self, request, escola_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesEscola.get_negados_dieta_especial(
            escola_uuid=escola_uuid
        )
        query_set = SolicitacoesEscola.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{CANCELADOS_DIETA_ESPECIAL}/{FILTRO_ESCOLA_UUID}",
    )
    def cancelados_dieta_especial(self, request, escola_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesEscola.get_cancelados_dieta_especial(
            escola_uuid=escola_uuid
        )
        query_set = SolicitacoesEscola.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=("get",),
        url_path=f"{CEU_GESTAO_PERIODOS_COM_SOLICITACOES_AUTORIZADAS}",
    )
    def ceu_gestao_periodos_com_solicitacoes_autorizadas(self, request):
        escola_uuid = request.query_params.get("escola_uuid")
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")

        uuids_inclusoes_normais = GrupoInclusaoAlimentacaoNormal.objects.filter(
            status="CODAE_AUTORIZADO",
            escola__uuid=escola_uuid,
            inclusoes_normais__cancelado=False,
            inclusoes_normais__data__month=mes,
            inclusoes_normais__data__year=ano,
            inclusoes_normais__data__lt=datetime.date.today(),
        ).values_list("uuid", flat=True)

        periodos_escolares_inclusoes = PeriodoEscolar.objects.filter(
            quantidadeporperiodo__grupo_inclusao_normal__uuid__in=uuids_inclusoes_normais
        ).distinct()
        escola = Escola.objects.get(uuid=escola_uuid)
        vinculos = (
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
                periodo_escolar__in=periodos_escolares_inclusoes,
                ativo=True,
                tipo_unidade_escolar=escola.tipo_unidade,
            ).order_by("periodo_escolar__posicao")
        )

        return Response(
            VinculoTipoAlimentoPeriodoSerializer(vinculos, many=True).data,
            status=status.HTTP_200_OK,
        )

    def filtra_inclusoes(self, request):
        escola_uuid = request.query_params.get("escola_uuid")
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")
        primeiro_dia_mes = datetime.date(int(ano), int(mes), 1)
        hoje = datetime.date.today()

        query_set = SolicitacoesEscola.get_autorizados(escola_uuid=escola_uuid)
        query_set = SolicitacoesEscola.busca_filtro(query_set, request.query_params)
        query_set = query_set.filter(
            Q(data_evento__month=mes, data_evento__year=ano)
            | Q(data_evento__lt=primeiro_dia_mes, data_evento_2__gte=primeiro_dia_mes)
        )
        query_set = query_set.filter(data_evento__lt=hoje)
        query_set = self.remove_duplicados_do_query_set(query_set)

        return query_set, mes, ano, escola_uuid

    def inclusoes_cei(self, query_set, mes, ano, periodos_escolares, return_dict):
        inclusoes_cei = [
            inclusao
            for inclusao in query_set
            if inclusao.tipo_doc == "INC_ALIMENTA_CEI"
        ]
        for inclusao in inclusoes_cei:
            inc = inclusao.get_raw_model.objects.get(uuid=inclusao.uuid)
            periodos_internos = []
            periodos_externos = []

            mapeamento_periodos = {
                "PARCIAL": (["INTEGRAL"], ["MANHA", "TARDE"]),
                "INTEGRAL": (["INTEGRAL"], ["INTEGRAL"]),
                "MANHA": (["MANHA"], ["MANHA"]),
                "TARDE": (["TARDE"], ["TARDE"]),
            }

            for periodo in periodos_escolares:
                if periodo in mapeamento_periodos:
                    periodos_externos, periodos_internos = mapeamento_periodos[periodo]
                    break

            dias_motivos = inc.dias_motivos_da_inclusao_cei.filter(
                data__month=mes, data__year=ano, cancelado=False
            )
            quantidade_por_faixa = inc.quantidade_alunos_da_inclusao.filter(
                periodo__nome__in=periodos_internos,
                periodo_externo__nome__in=periodos_externos,
            )
            if quantidade_por_faixa:
                for dia_motivo in dias_motivos:
                    faixas_etarias_uuids = quantidade_por_faixa.values_list(
                        "faixa_etaria__uuid", flat=True
                    )
                    return_dict.append(
                        {
                            "dia": dia_motivo.data.day,
                            "faixas_etarias": faixas_etarias_uuids.distinct(),
                        }
                    )
        return return_dict

    def get_qtd_alunos_cei_cemei_por_periodo(self, inc, periodo, sol_medicao_inicial):
        eh_parcial_integral = False
        if periodo == "PARCIAL":
            qtd_alunos_cei_cemei_por_periodo = (
                inc.quantidade_alunos_cei_da_inclusao_cemei.filter(
                    periodo_escolar__nome__in=["MANHA", "TARDE"]
                )
            )
            if not qtd_alunos_cei_cemei_por_periodo.exists():
                qtd_alunos_cei_cemei_por_periodo = (
                    inc.quantidade_alunos_cei_da_inclusao_cemei.filter(
                        periodo_escolar__nome="INTEGRAL"
                    )
                )
                eh_parcial_integral = True
        else:
            if (
                periodo == "INTEGRAL"
                and sol_medicao_inicial
                and not sol_medicao_inicial.ue_possui_alunos_periodo_parcial
            ):
                qtd_alunos_cei_cemei_por_periodo = (
                    inc.quantidade_alunos_cei_da_inclusao_cemei.filter(
                        periodo_escolar__nome__in=[
                            "INTEGRAL",
                            "MANHA",
                            "TARDE",
                        ]
                    )
                )
            else:
                qtd_alunos_cei_cemei_por_periodo = (
                    inc.quantidade_alunos_cei_da_inclusao_cemei.filter(
                        periodo_escolar__nome=periodo
                    )
                )
        return qtd_alunos_cei_cemei_por_periodo, eh_parcial_integral

    def atualizar_return_dict(
        self, return_dict, dias_motivos_cemei, faixas_etarias_uuids, eh_parcial_integral
    ):
        return_dict_map = {r["dia"]: r for r in return_dict}

        for dia_motivo_cemei in dias_motivos_cemei:
            dia = dia_motivo_cemei.data.day
            if dia in return_dict_map:
                if (
                    return_dict_map[dia]["eh_parcial_integral"]
                    and not eh_parcial_integral
                ):
                    return_dict_map[dia] = {
                        "dia": dia,
                        "faixas_etarias": faixas_etarias_uuids,
                        "eh_parcial_integral": eh_parcial_integral,
                    }
            else:
                return_dict_map[dia] = {
                    "dia": dia,
                    "faixas_etarias": faixas_etarias_uuids,
                    "eh_parcial_integral": eh_parcial_integral,
                }

        return list(return_dict_map.values())

    def inclusoes_cemei_nao_infantil(
        self, periodo, inc, sol_medicao_inicial, dias_motivos_cemei, return_dict
    ):
        if (
            "Infantil" in periodo
            or not inc.quantidade_alunos_cei_da_inclusao_cemei.exists()
        ):
            return return_dict

        (
            qtd_alunos_cei_cemei_por_periodo,
            eh_parcial_integral,
        ) = self.get_qtd_alunos_cei_cemei_por_periodo(inc, periodo, sol_medicao_inicial)
        if not qtd_alunos_cei_cemei_por_periodo.exists():
            return return_dict

        faixas_etarias_uuids = list(
            qtd_alunos_cei_cemei_por_periodo.values_list(
                "faixa_etaria__uuid", flat=True
            ).distinct()
        )

        return_dict = self.atualizar_return_dict(
            return_dict, dias_motivos_cemei, faixas_etarias_uuids, eh_parcial_integral
        )

        return return_dict

    def inclusoes_cemei_infantil(
        self, periodo, inc, dias_motivos_cemei, mes, ano, inclusao, return_dict
    ):
        if " " in periodo:
            periodo = periodo.split(" ")[1]
        if not inc.quantidade_alunos_emei_da_inclusao_cemei.filter(
            periodo_escolar__nome=periodo
        ).exists():
            return return_dict
        for dia_motivo_cemei in dias_motivos_cemei:
            tratar_append_return_dict(
                dia_motivo_cemei.data.day,
                mes,
                ano,
                inc.quantidade_alunos_emei_da_inclusao_cemei.get(
                    periodo_escolar__nome=periodo
                ),
                inclusao,
                return_dict,
            )
        return return_dict

    def inclusoes_cemei(
        self,
        query_set,
        mes,
        ano,
        periodos_escolares,
        escola_uuid,
        cemei_cei,
        cemei_emei,
        return_dict,
    ):
        sol_medicao_inicial = SolicitacaoMedicaoInicial.objects.filter(
            escola__uuid=escola_uuid, mes=mes, ano=ano
        ).first()
        inclusoes_cemei = [
            inclusao
            for inclusao in query_set
            if inclusao.tipo_doc == "INC_ALIMENTA_CEMEI"
        ]
        for inclusao in inclusoes_cemei:
            inc = inclusao.get_raw_model.objects.get(uuid=inclusao.uuid)
            dias_motivos_cemei = inc.dias_motivos_da_inclusao_cemei.filter(
                data__month=mes, data__year=ano
            )
            for periodo in periodos_escolares:
                if cemei_cei:
                    return_dict = self.inclusoes_cemei_nao_infantil(
                        periodo,
                        inc,
                        sol_medicao_inicial,
                        dias_motivos_cemei,
                        return_dict,
                    )
                if cemei_emei:
                    return_dict = self.inclusoes_cemei_infantil(
                        periodo,
                        inc,
                        dias_motivos_cemei,
                        mes,
                        ano,
                        inclusao,
                        return_dict,
                    )
        return return_dict

    def tratar_inclusoes_normais(self, inc, mes, ano, periodo, inclusao, return_dict):
        for inclusao_normal in inc.inclusoes_normais.filter(
            data__month=mes, data__year=ano, cancelado=False
        ):
            tratar_append_return_dict(
                inclusao_normal.data.day, mes, ano, periodo, inclusao, return_dict
            )
        return return_dict

    def inclusoes_normal_continua(
        self, query_set, periodos_escolares, mes, ano, return_dict
    ):
        inclusoes_normal_continua = [
            inclusao
            for inclusao in query_set
            if inclusao.tipo_doc in ["INC_ALIMENTA", "INC_ALIMENTA_CONTINUA"]
        ]

        for inclusao in inclusoes_normal_continua:
            inc = inclusao.get_raw_model.objects.get(uuid=inclusao.uuid)

            for periodo in inc.quantidades_periodo.all():
                if (
                    periodo.periodo_escolar.nome not in periodos_escolares
                    or periodo.cancelado
                ):
                    continue

                if inclusao.tipo_doc == "INC_ALIMENTA_CONTINUA":
                    tratar_inclusao_continua(mes, ano, periodo, inclusao, return_dict)
                else:
                    return_dict = self.tratar_inclusoes_normais(
                        inc, mes, ano, periodo, inclusao, return_dict
                    )
        return return_dict

    @action(detail=False, methods=["GET"], url_path=f"{INCLUSOES_AUTORIZADAS}")
    def inclusoes_autorizadas(self, request):
        query_set, mes, ano, escola_uuid = self.filtra_inclusoes(request)
        periodos_escolares = request.query_params.getlist("periodos_escolares[]")
        cemei_cei = request.query_params.get("cemei_cei", False) == "true"
        cemei_emei = request.query_params.get("cemei_emei", False) == "true"

        return_dict = []
        return_dict = self.inclusoes_cei(
            query_set, mes, ano, periodos_escolares, return_dict
        )
        return_dict = self.inclusoes_cemei(
            query_set,
            mes,
            ano,
            periodos_escolares,
            escola_uuid,
            cemei_cei,
            cemei_emei,
            return_dict,
        )
        return_dict = self.inclusoes_normal_continua(
            query_set, periodos_escolares, mes, ano, return_dict
        )

        data = {"results": return_dict}

        return Response(data)

    @action(detail=False, methods=["GET"], url_path=f"{SUSPENSOES_AUTORIZADAS}")
    def suspensoes_autorizadas(self, request):
        escola_uuid = request.query_params.get("escola_uuid")
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")
        nome_periodo_escolar = request.query_params.get("nome_periodo_escolar")

        query_set = SolicitacoesEscola.get_autorizados(escola_uuid=escola_uuid)
        query_set = SolicitacoesEscola.busca_filtro(query_set, request.query_params)
        query_set = query_set.filter(data_evento__month=mes, data_evento__year=ano)
        query_set = query_set.filter(data_evento__lt=datetime.date.today())
        query_set = self.remove_duplicados_do_query_set(query_set)
        return_dict = []

        for suspensao in query_set:
            susp = suspensao.get_raw_model.objects.get(uuid=suspensao.uuid)
            if susp.DESCRICAO == "Suspensão de Alimentação de CEI":
                nome_periodo_escolar = tratar_periodo_parcial(nome_periodo_escolar)
                if nome_periodo_escolar in susp.periodos_escolares.all().values_list(
                    "nome", flat=True
                ):
                    return_dict.append(
                        {
                            "dia": f"{susp.data.day:02d}",
                            "periodo": nome_periodo_escolar,
                            "motivo": susp.motivo.nome,
                            "inclusao_id_externo": susp.id_externo,
                        }
                    )
            else:
                nome_periodo_escolar = tratar_periodo_parcial_cemei(
                    nome_periodo_escolar, susp
                )
                s_quant_por_periodo = susp.quantidades_por_periodo.filter(
                    periodo_escolar__nome=nome_periodo_escolar
                )
                for s_quant_periodo in s_quant_por_periodo:
                    for suspensao in susp.suspensoes_alimentacao.filter(
                        cancelado=False
                    ):
                        tipos_alimentacao = s_quant_periodo.tipos_alimentacao.all()
                        alimentacoes = [
                            unicodedata.normalize(
                                "NFD", alimentacao.nome.replace(" ", "_")
                            )
                            .encode("ascii", "ignore")
                            .decode("utf-8")
                            .lower()
                            for alimentacao in tipos_alimentacao
                        ]
                        return_dict.append(
                            {
                                "dia": f"{suspensao.data.day:02d}",
                                "periodo": nome_periodo_escolar,
                                "alimentacoes": alimentacoes,
                                "numero_alunos": s_quant_periodo.numero_alunos,
                                "inclusao_id_externo": susp.id_externo,
                            }
                        )

        data = {"results": return_dict}

        return Response(data)

    def trata_lanche_emergencial_queryset(self, eh_lanche_emergencial, query_set):
        if eh_lanche_emergencial == "true":
            query_set = query_set.filter(motivo__icontains="Emergencial")
        else:
            query_set = query_set.exclude(motivo__icontains="Emergencial")
        return query_set

    def get_alteracao_obj(self, alteracao, nome_periodo_escolar):
        alt = None
        if alteracao.escola.eh_cemei:
            if "Infantil" not in nome_periodo_escolar:
                return alt
            nome_periodo_escolar = nome_periodo_escolar.split(" ")[1]
            if alteracao.substituicoes_cemei_emei_periodo_escolar.filter(
                periodo_escolar__nome=nome_periodo_escolar
            ).exists():
                alt = alteracao.substituicoes_cemei_emei_periodo_escolar.get(
                    periodo_escolar__nome=nome_periodo_escolar
                )
        elif alteracao.substituicoes_periodo_escolar.filter(
            periodo_escolar__nome=nome_periodo_escolar
        ).exists():
            alt = alteracao.substituicoes_periodo_escolar.get(
                periodo_escolar__nome=nome_periodo_escolar
            )
        return alt

    def alteracoes_lanche_emergencial(
        self,
        eh_lanche_emergencial,
        alteracao,
        alteracao_alimentacao,
        mes,
        ano,
        return_dict,
    ):
        if eh_lanche_emergencial == "true":
            for data_evento in alteracao.datas_intervalo.filter(
                data__month=mes, data__year=ano, cancelado=False
            ):
                return_dict.append(
                    {
                        "dia": f"{data_evento.data.day:02d}",
                        "numero_alunos": get_numero_alunos_alteracao_alimentacao(
                            alteracao
                        ),
                        "inclusao_id_externo": alteracao.id_externo,
                        "motivo": alteracao_alimentacao.motivo,
                    }
                )
        return return_dict

    def alteracoes_RPL_LPR(
        self,
        eh_lanche_emergencial,
        alteracao,
        alteracao_alimentacao,
        nome_periodo_escolar,
        mes,
        ano,
        return_dict,
    ):
        if eh_lanche_emergencial != "true":
            alt = self.get_alteracao_obj(alteracao, nome_periodo_escolar)
            if alt:
                for data_evento in alteracao.datas_intervalo.filter(
                    data__month=mes, data__year=ano, cancelado=False
                ):
                    return_dict.append(
                        {
                            "dia": f"{data_evento.data.day:02d}",
                            "periodo": nome_periodo_escolar,
                            "numero_alunos": alt.qtd_alunos,
                            "inclusao_id_externo": alteracao.id_externo,
                            "motivo": alteracao_alimentacao.motivo,
                        }
                    )
        return return_dict

    @action(
        detail=False, methods=["GET"], url_path=f"{ALTERACOES_ALIMENTACAO_AUTORIZADAS}"
    )
    def alteracoes_alimentacoes_autorizadas(self, request):
        escola_uuid = request.query_params.get("escola_uuid")
        escola = Escola.objects.get(uuid=escola_uuid)

        if escola.eh_cei:
            return Response({"results": []}, status=status.HTTP_200_OK)

        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")
        nome_periodo_escolar = request.query_params.get("nome_periodo_escolar")
        eh_lanche_emergencial = request.query_params.get("eh_lanche_emergencial", "")

        query_set = SolicitacoesEscola.get_autorizados(escola_uuid=escola_uuid)
        query_set = SolicitacoesEscola.busca_filtro(query_set, request.query_params)
        query_set = query_set.filter(data_evento__month=mes, data_evento__year=ano)
        query_set = query_set.filter(data_evento__lt=datetime.date.today())
        query_set = self.trata_lanche_emergencial_queryset(
            eh_lanche_emergencial, query_set
        )
        query_set = self.remove_duplicados_do_query_set(query_set)
        return_dict = []

        for alteracao_alimentacao in query_set:
            alteracao = alteracao_alimentacao.get_raw_model.objects.get(
                uuid=alteracao_alimentacao.uuid
            )
            return_dict = self.alteracoes_lanche_emergencial(
                eh_lanche_emergencial,
                alteracao,
                alteracao_alimentacao,
                mes,
                ano,
                return_dict,
            )
            return_dict = self.alteracoes_RPL_LPR(
                eh_lanche_emergencial,
                alteracao,
                alteracao_alimentacao,
                nome_periodo_escolar,
                mes,
                ano,
                return_dict,
            )

        data = {"results": return_dict}

        return Response(data)

    @action(detail=False, methods=["GET"], url_path=f"{KIT_LANCHES_AUTORIZADAS}")
    def kit_lanches_autorizadas(self, request):
        escola_uuid = request.query_params.get("escola_uuid")
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")

        query_set = SolicitacoesEscola.get_autorizados(escola_uuid=escola_uuid)
        query_set = SolicitacoesEscola.busca_filtro(query_set, request.query_params)
        query_set = query_set.filter(data_evento__month=mes, data_evento__year=ano)
        query_set = query_set.filter(data_evento__lt=datetime.date.today())
        query_set = self.remove_duplicados_do_query_set(query_set)
        return_dict = []

        for kit_lanche in query_set:
            kit_lanche = kit_lanche.get_raw_model.objects.get(uuid=kit_lanche.uuid)
            if kit_lanche:
                if kit_lanche.DESCRICAO == "Kit Lanche CEMEI":
                    dia = f"{kit_lanche.data.day:02d}"
                    numero_alunos = kit_lanche.total_kits
                else:
                    dia = f"{kit_lanche.solicitacao_kit_lanche.data.day:02d}"
                    numero_alunos = (
                        kit_lanche.total_kit_lanche_escola(escola_uuid)
                        if isinstance(kit_lanche, SolicitacaoKitLancheUnificada)
                        else kit_lanche.quantidade_alimentacoes
                    )
                return_dict.append(
                    {
                        "dia": dia,
                        "numero_alunos": numero_alunos,
                        "kit_lanche_id_externo": kit_lanche.id_externo,
                    }
                )

        data = {"results": return_dict}

        return Response(data)

    @action(detail=False, methods=["GET"], url_path=f"{INCLUSOES_ETEC_AUTORIZADAS}")
    def inclusoes_etec_autorizadas(self, request):
        escola_uuid = request.query_params.get("escola_uuid")
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")
        date = datetime.date(int(ano), int(mes), 1)

        query_set = SolicitacoesEscola.get_autorizados(escola_uuid=escola_uuid)
        query_set = SolicitacoesEscola.busca_filtro(query_set, request.query_params)
        query_set = query_set.filter(
            Q(data_evento__month=mes, data_evento__year=ano)
            | Q(data_evento__lt=date, data_evento_2__gte=date)
        )
        query_set = query_set.filter(
            data_evento__lt=datetime.date.today(), motivo="ETEC"
        )
        query_set = self.remove_duplicados_do_query_set(query_set)

        return_dict = []

        def append(dia, inclusao):
            resultado = formata_resultado_inclusoes_etec_autorizadas(
                dia, mes, ano, inclusao
            )
            return_dict.append(resultado) if resultado else None

        for sol_escola in query_set:
            inclusao = sol_escola.get_raw_model.objects.get(uuid=sol_escola.uuid)
            dia = sol_escola.data_evento.day
            big_range = False
            data_evento_final_no_mes = None
            if sol_escola.data_evento.month != int(
                mes
            ) and sol_escola.data_evento_2.month != int(mes):
                big_range = True
                i = datetime.date(int(ano), int(mes), 1)
                data_evento_final_no_mes = (i + relativedelta(day=31)).day
                dia = datetime.date(int(ano), int(mes), 1).day
            elif sol_escola.data_evento.month != int(mes):
                big_range = True
                data_evento_final_no_mes = sol_escola.data_evento_2.day
                dia = datetime.date(int(ano), int(mes), 1).day
            else:
                data_evento_final_no_mes = sol_escola.data_evento_2.day
            data_evento_final_no_mes = tratar_data_evento_final_no_mes(
                data_evento_final_no_mes, sol_escola, big_range
            )
            while dia <= data_evento_final_no_mes:
                append(dia, inclusao)
                dia += 1
        data = {"results": tratar_dias_duplicados(return_dict)}

        return Response(data)
