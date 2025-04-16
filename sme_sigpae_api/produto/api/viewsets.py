import json
from collections import Counter
from datetime import datetime
from itertools import chain

import environ
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db import transaction
from django.db.models import CharField, Count, F, Prefetch, Q
from django.db.models.functions import Cast, Substr
from django.template.loader import render_to_string
from django_filters import rest_framework as filters
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_406_NOT_ACCEPTABLE
from xworkflows import InvalidTransitionError

from ...dados_comuns import constants
from ...dados_comuns.constants import (
    TIPO_USUARIO_CODAE_GABINETE,
    TIPO_USUARIO_DIRETORIA_REGIONAL,
    TIPO_USUARIO_GESTAO_ALIMENTACAO_TERCEIRIZADA,
    TIPO_USUARIO_NUTRIMANIFESTACAO,
    TIPO_USUARIO_NUTRISUPERVISOR,
    TIPO_USUARIO_ORGAO_FISCALIZADOR,
    TIPO_USUARIO_TERCEIRIZADA,
)
from ...dados_comuns.fluxo_status import (
    HomologacaoProdutoWorkflow,
    ReclamacaoProdutoWorkflow,
)
from ...dados_comuns.models import LogSolicitacoesUsuario
from ...dados_comuns.permissions import (
    PermissaoParaReclamarDeProduto,
    UsuarioCODAEGabinete,
    UsuarioCODAEGestaoAlimentacao,
    UsuarioCODAEGestaoProduto,
    UsuarioDinutreDiretoria,
    UsuarioDiretoriaRegional,
    UsuarioNutricionista,
    UsuarioOrgaoFiscalizador,
    UsuarioTerceirizadaProduto,
)
from ...dados_comuns.utils import url_configs
from ...dieta_especial.models import Alimento
from ...escola.models import DiretoriaRegional, Escola, Lote
from ...paineis_consolidados.api.viewsets import SolicitacoesViewSet
from ...relatorios.relatorios import (
    relatorio_produto_analise_sensorial,
    relatorio_produto_analise_sensorial_recebimento,
    relatorio_produto_homologacao,
    relatorio_produtos_em_analise_sensorial,
    relatorio_produtos_suspensos,
    relatorio_reclamacao,
)
from ...relatorios.utils import html_to_pdf_response
from ...terceirizada.api.serializers.serializers import EditalSimplesSerializer
from ...terceirizada.models import Contrato, Edital
from ..constants import (
    AVALIAR_RECLAMACAO_HOMOLOGACOES_STATUS,
    AVALIAR_RECLAMACAO_RECLAMACOES_STATUS,
    NOVA_RECLAMACAO_HOMOLOGACOES_STATUS,
    RESPONDER_RECLAMACAO_HOMOLOGACOES_STATUS,
    RESPONDER_RECLAMACAO_RECLAMACOES_STATUS,
)
from ..forms import ProdutoJaExisteForm
from ..models import (
    AnaliseSensorial,
    EmbalagemProduto,
    Fabricante,
    HomologacaoProduto,
    ImagemDoProduto,
    InformacaoNutricional,
    ItemCadastro,
    Marca,
    NomeDeProdutoEdital,
    Produto,
    ProdutoEdital,
    ProtocoloDeDietaEspecial,
    ReclamacaoDeProduto,
    RespostaAnaliseSensorial,
    SolicitacaoCadastroProdutoDieta,
    UnidadeMedida,
)
from ..tasks import (
    gera_pdf_relatorio_produtos_homologados_async,
    gera_xls_relatorio_produtos_homologados_async,
    gera_xls_relatorio_produtos_suspensos_async,
)
from ..utils import (
    CadastroProdutosEditalPagination,
    ItemCadastroPagination,
    StandardResultsSetPagination,
    converte_para_datetime,
    cria_filtro_aditivos,
    cria_filtro_homologacao_produto_por_parametros,
    get_filtros_data,
)
from .filters import (
    CadastroProdutosEditalFilter,
    FabricanteFilter,
    ItemCadastroFilter,
    MarcaFilter,
    ProdutoFilter,
    filtros_produto_reclamacoes,
)
from .serializers.serializers import (
    CadastroProdutosEditalSerializer,
    EmbalagemProdutoSerialzer,
    FabricanteSerializer,
    FabricanteSimplesSerializer,
    HomologacaoProdutoPainelGerencialSerializer,
    HomologacaoProdutoSerializer,
    ImagemDoProdutoSerializer,
    InformacaoNutricionalSerializer,
    ItensCadastroCreateSerializer,
    ItensCadastroSerializer,
    MarcaSerializer,
    MarcaSimplesSerializer,
    NomeDeProdutoEditalSerializer,
    ProdutoEditalSerializer,
    ProdutoHomologadosPorParametrosSerializer,
    ProdutoListagemSerializer,
    ProdutoReclamacaoSerializer,
    ProdutoRelatorioAnaliseSensorialSerializer,
    ProdutoRelatorioSituacaoSerializer,
    ProdutoSerializer,
    ProdutoSimplesSerializer,
    ProdutoSuspensoSerializer,
    ProtocoloDeDietaEspecialSerializer,
    ProtocoloSimplesSerializer,
    ReclamacaoDeProdutoSerializer,
    ReclamacaoDeProdutoSimplesSerializer,
    RelatorioProdutosSuspensosSerializer,
    SolicitacaoCadastroProdutoDietaSerializer,
    SubstitutosSerializer,
    UnidadeMedidaSerialzer,
    VinculosProdutosEditalAtivosSerializer,
)
from .serializers.serializers_create import (
    CadastroProdutosEditalCreateSerializer,
    ProdutoEditalCreateSerializer,
    ProdutoSerializerCreate,
    ReclamacaoDeProdutoSerializerCreate,
    RespostaAnaliseSensorialSearilzerCreate,
    SolicitacaoCadastroProdutoDietaSerializerCreate,
)

env = environ.Env()

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10


class CustomPagination(PageNumberPagination):
    page = DEFAULT_PAGE
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        return Response(
            {
                "previous": self.get_previous_link(),
                "next": self.get_next_link(),
                "count": self.page.paginator.count,
                "page_size": int(self.request.GET.get("page_size", self.page_size)),
                "results": data,
            }
        )


class ListaNomesUnicos:
    @action(detail=False, methods=["GET"], url_path="lista-nomes-unicos")
    def lista_nomes_unicos(self, request):
        query_set = self.filter_queryset(self.get_queryset()).values("nome").distinct()
        nomes_unicos = [i["nome"] for i in query_set]
        return Response({"results": nomes_unicos, "count": len(nomes_unicos)})


class InformacaoNutricionalBaseViewSet(viewsets.ReadOnlyModelViewSet):
    def possui_tipo_nutricional_na_lista(self, infos_nutricionais, nome):
        tem_tipo_nutricional = False
        if len(infos_nutricionais) > 0:
            for info_nutricional in infos_nutricionais:
                if info_nutricional["nome"] == nome:
                    tem_tipo_nutricional = True
        return tem_tipo_nutricional

    def adiciona_informacao_em_tipo_nutricional(self, infos_nutricionais, objeto):
        tipo_nutricional = objeto.tipo_nutricional.nome
        for item in infos_nutricionais:
            if item["nome"] == tipo_nutricional:
                item["informacoes_nutricionais"].append(
                    {"nome": objeto.nome, "uuid": objeto.uuid, "medida": objeto.medida}
                )
        return infos_nutricionais

    def _agrupa_informacoes_por_tipo(self, query_set):
        infos_nutricionais = []
        for objeto in query_set:
            tipo_nutricional = objeto.tipo_nutricional.nome
            if self.possui_tipo_nutricional_na_lista(
                infos_nutricionais, tipo_nutricional
            ):
                infos_nutricionais = self.adiciona_informacao_em_tipo_nutricional(
                    infos_nutricionais, objeto
                )
            else:
                info_nutricional = {
                    "nome": tipo_nutricional,
                    "informacoes_nutricionais": [
                        {
                            "nome": objeto.nome,
                            "uuid": objeto.uuid,
                            "medida": objeto.medida,
                        }
                    ],
                }
                infos_nutricionais.append(info_nutricional)
        return infos_nutricionais


class ImagensViewset(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    lookup_field = "uuid"
    queryset = ImagemDoProduto.objects.all()
    serializer_class = ImagemDoProdutoSerializer


class HomologacaoProdutoPainelGerencialViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    serializer_class = HomologacaoProdutoPainelGerencialSerializer
    queryset = HomologacaoProduto.objects.all()
    pagination_class = CustomPagination

    def produtos_sem_agrupamento(self, nome_edital, qs_produtos, offset, limit):
        produtos_agrupados = []
        for hom_produto in qs_produtos[offset : offset + limit]:
            produto_edital = hom_produto.produto.vinculos.get(
                edital__numero=nome_edital
            )
            produtos_agrupados.append(
                {
                    "terceirizada": hom_produto.rastro_terceirizada.nome_fantasia,
                    "nome": hom_produto.produto.nome,
                    "marca": hom_produto.produto.marca.nome,
                    "edital": nome_edital,
                    "tipo": produto_edital.tipo_produto,
                    "tem_aditivos_alergenicos": hom_produto.produto.tem_aditivos_alergenicos,
                    "cadastro": hom_produto.produto.criado_em.strftime("%d/%m/%Y"),
                    "homologacao": produto_edital.datas_horas_vinculo.filter(
                        suspenso=False
                    )
                    .first()
                    .criado_em.strftime("%d/%m/%Y"),
                }
            )
        return produtos_agrupados

    def produtos_agrupados_nome_marca(self, nome_edital, queryset, offset, limit):
        produtos_agrupados = []
        produtos_editais = (
            ProdutoEdital.objects.filter(
                edital__numero=nome_edital,
                produto__id__in=queryset.values_list("id", flat=True),
            )
            .values("produto__nome", "produto__marca__nome", "edital__numero")
            .order_by("produto__nome", "produto__marca__nome")
        )
        for produto in produtos_editais:
            index = next(
                (
                    i
                    for i, produto_ in enumerate(produtos_agrupados)
                    if produto_["nome"] == produto["produto__nome"]
                ),
                -1,
            )
            if index != -1:
                produtos_agrupados[index][
                    "marca"
                ] += f' | {produto["produto__marca__nome"]}'
            else:
                produtos_agrupados.append(
                    {
                        "nome": produto["produto__nome"],
                        "marca": produto["produto__marca__nome"],
                        "edital": nome_edital,
                    }
                )
        return produtos_agrupados[offset : offset + limit]

    @action(
        detail=False,
        methods=["GET"],
        url_path="filtro-por-parametros-agrupado-terceirizada",
    )
    def filtro_por_parametros_agrupado_terceirizada(self, request):
        user = request.user
        query_set = self.get_queryset_solicitacoes_homologacao_por_status(
            request.query_params,
            user.vinculo_atual.perfil.nome,
            user.tipo_usuario,
            user.vinculo_atual.object_id,
            "codae_homologado",
        )
        limit = int(request.query_params.get("limit", 10))
        offset = int(request.query_params.get("offset", 0))
        uuids = [hom_prod.uuid for hom_prod in query_set]
        qs_produtos = Produto.objects.filter(homologacao__uuid__in=uuids)
        total_marcas = (
            qs_produtos.values_list("marca__nome", flat=True).distinct().count()
        )
        nome_edital = request.query_params.get("nome_edital")
        if request.query_params.get("agrupado_por_nome_e_marca") == "true":
            produtos_agrupados = self.produtos_agrupados_nome_marca(
                nome_edital, qs_produtos, offset, limit
            )
        else:
            produtos_agrupados = self.produtos_sem_agrupamento(
                nome_edital, query_set, offset, limit
            )

        return Response(
            {
                "results": produtos_agrupados,
                "count": len(query_set),
                "total_marcas": total_marcas,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["GET"], url_path="exportar-pdf")
    def exportar_pdf(self, request):
        agrupado_nome_marca = request.data.get("agrupado_por_nome_e_marca")
        user = request.user.get_username()

        gera_pdf_relatorio_produtos_homologados_async.delay(
            user=user,
            nome_arquivo=f'relatorio_produtos_homologados{"_nome_marca" if agrupado_nome_marca else ""}.pdf',
            data=request.query_params,
            perfil_nome=request.user.vinculo_atual.perfil.nome,
            tipo_usuario=request.user.tipo_usuario,
            object_id=request.user.vinculo_atual.object_id,
        )
        return Response(
            dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
            status=status.HTTP_200_OK,
        )

    def build_raw_sql_filtro_escola(
        self,
        raw_sql,
        status__in,
        common_status,
        tipo_usuario,
        filtros,
        escola_ou_dre_id,
    ):
        if tipo_usuario != constants.TIPO_USUARIO_ESCOLA:
            return raw_sql, filtros
        filtros["reclamacoes__escola__id"] = escola_ou_dre_id
        if "TERCEIRIZADA_RESPONDEU_RECLAMACAO" not in status__in:
            status__in.append("TERCEIRIZADA_RESPONDEU_RECLAMACAO")
        raw_sql += common_status
        if "TERCEIRIZADA_RESPONDEU_RECLAMACAO" not in raw_sql:
            raw_sql += "OR %(homologacao_produto)s.status = 'TERCEIRIZADA_RESPONDEU_RECLAMACAO')"
        raw_sql += f" AND escola_reclamacao.escola_id_escola = {escola_ou_dre_id} "
        return raw_sql, filtros

    def build_raw_sql_filtro_dre(
        self,
        raw_sql,
        status__in,
        common_status,
        tipo_usuario,
        filtros,
        escola_ou_dre_id,
    ):
        if tipo_usuario != constants.TIPO_USUARIO_DIRETORIA_REGIONAL:
            return raw_sql, filtros
        filtros["reclamacoes__escola__lote__diretoria_regional_id"] = escola_ou_dre_id
        raw_sql += f"AND escola_lote.diretoria_regional_id = {escola_ou_dre_id}"
        return raw_sql, filtros

    def trata_edital(self, raw_sql, edital, editais=None):
        if edital:
            raw_sql += f" AND produto_edital.edital_id_prod_edit = {edital.id} "
        elif editais:
            raw_sql += f" AND produto_edital.edital_id_prod_edit IN ({editais}) "
        return raw_sql

    def build_raw_sql_filtro_codae_pediu_analise_reclamacao(
        self,
        raw_sql,
        filtro_aplicado,
        perfil_nome,
        filtros,
        tipo_usuario,
        escola_ou_dre_id,
    ):
        if filtro_aplicado != "codae_pediu_analise_reclamacao":
            return raw_sql, filtros
        status__in = [
            "ESCOLA_OU_NUTRICIONISTA_RECLAMOU",
            "CODAE_PEDIU_ANALISE_RECLAMACAO",
            "CODAE_QUESTIONOU_UE",
        ]
        common_status = (
            "WHERE (%(homologacao_produto)s.status = 'ESCOLA_OU_NUTRICIONISTA_RECLAMOU' "
            "OR %(homologacao_produto)s.status = 'CODAE_QUESTIONOU_UE' "
            f"OR %(homologacao_produto)s.status = '{filtro_aplicado.upper()}' "
        )
        filtros_terceirizada_ou_codae_ou_dre = {
            "status__in": status__in
            + ["UE_RESPONDEU_QUESTIONAMENTO", "TERCEIRIZADA_RESPONDEU_RECLAMACAO"],
            "raw_sql": (
                common_status
                + "OR %(homologacao_produto)s.status = 'UE_RESPONDEU_QUESTIONAMENTO' "
                "OR %(homologacao_produto)s.status = 'TERCEIRIZADA_RESPONDEU_RECLAMACAO' "
                "OR %(homologacao_produto)s.status = 'CODAE_QUESTIONOU_NUTRISUPERVISOR' "
                "OR %(homologacao_produto)s.status = 'NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO') "
            ),
        }
        filtros_dict = {
            constants.COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA: filtros_terceirizada_ou_codae_ou_dre,
            constants.ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA: filtros_terceirizada_ou_codae_ou_dre,
            constants.COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO: filtros_terceirizada_ou_codae_ou_dre,
            constants.COGESTOR_DRE: filtros_terceirizada_ou_codae_ou_dre,
            constants.COORDENADOR_GESTAO_PRODUTO: filtros_terceirizada_ou_codae_ou_dre,
            constants.ADMINISTRADOR_GESTAO_PRODUTO: filtros_terceirizada_ou_codae_ou_dre,
            constants.ADMINISTRADOR_EMPRESA: filtros_terceirizada_ou_codae_ou_dre,
            constants.ADMINISTRADOR_CODAE_GABINETE: filtros_terceirizada_ou_codae_ou_dre,
            constants.COORDENADOR_SUPERVISAO_NUTRICAO: {
                "status__in": status__in + ["CODAE_QUESTIONOU_NUTRISUPERVISOR"],
                "raw_sql": (
                    common_status
                    + "OR %(homologacao_produto)s.status = 'CODAE_QUESTIONOU_NUTRISUPERVISOR') "
                ),
            },
        }

        if perfil_nome in [
            constants.COGESTOR_DRE,
            constants.COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
            constants.ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
            constants.COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
            constants.COORDENADOR_GESTAO_PRODUTO,
            constants.ADMINISTRADOR_GESTAO_PRODUTO,
            constants.ADMINISTRADOR_EMPRESA,
            constants.COORDENADOR_SUPERVISAO_NUTRICAO,
            constants.ADMINISTRADOR_CODAE_GABINETE,
        ]:
            filtros["status__in"] = filtros_dict[perfil_nome]["status__in"]
            raw_sql += filtros_dict[perfil_nome]["raw_sql"]
        raw_sql, filtros = self.build_raw_sql_filtro_escola(
            raw_sql, status__in, common_status, tipo_usuario, filtros, escola_ou_dre_id
        )
        raw_sql, filtros = self.build_raw_sql_filtro_dre(
            raw_sql, status__in, common_status, tipo_usuario, filtros, escola_ou_dre_id
        )
        if "WHERE" not in raw_sql:
            raw_sql += common_status + ") "

        return raw_sql, filtros

    def checa_se_remove_eh_copia(self, filtro_aplicado, raw_sql):
        if filtro_aplicado not in [
            "codae_pendente_homologacao",
            "codae_questionado",
            "codae_pediu_analise_sensorial",
        ]:
            raw_sql += "AND %(homologacao_produto)s.eh_copia = false "
        return raw_sql

    def build_raw_sql_filtro_aplicado(
        self,
        raw_sql,
        filtro_aplicado,
        filtros,
        tipo_usuario,
        escola_ou_dre_id,
    ):
        filtros_dict = {
            filtro_aplicado: {
                "status__in": [filtro_aplicado.upper()],
                "raw_sql": f"WHERE %(homologacao_produto)s.status = '{filtro_aplicado.upper()}' ",
            },
            "codae_homologado": {
                "status__in": [
                    HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO,
                    HomologacaoProdutoWorkflow.CODAE_QUESTIONADO,
                    HomologacaoProdutoWorkflow.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
                    HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_SENSORIAL,
                    HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_RECLAMACAO,
                    HomologacaoProdutoWorkflow.CODAE_QUESTIONOU_UE,
                    HomologacaoProdutoWorkflow.UE_RESPONDEU_QUESTIONAMENTO,
                    HomologacaoProdutoWorkflow.CODAE_QUESTIONOU_NUTRISUPERVISOR,
                    HomologacaoProdutoWorkflow.NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO,
                    HomologacaoProdutoWorkflow.TERCEIRIZADA_RESPONDEU_RECLAMACAO,
                ],
                "raw_sql": (
                    "WHERE (%(homologacao_produto)s.status = 'CODAE_HOMOLOGADO' "
                    "OR %(homologacao_produto)s.status = 'CODAE_QUESTIONADO' "
                    "OR %(homologacao_produto)s.status = 'ESCOLA_OU_NUTRICIONISTA_RECLAMOU' "
                    "OR %(homologacao_produto)s.status = 'CODAE_PEDIU_ANALISE_SENSORIAL' "
                    "OR %(homologacao_produto)s.status = 'CODAE_PEDIU_ANALISE_RECLAMACAO' "
                    "OR %(homologacao_produto)s.status = 'CODAE_QUESTIONOU_UE' "
                    "OR %(homologacao_produto)s.status = 'UE_RESPONDEU_QUESTIONAMENTO' "
                    "OR %(homologacao_produto)s.status = 'CODAE_QUESTIONOU_NUTRISUPERVISOR' "
                    "OR %(homologacao_produto)s.status = 'NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO' "
                    "OR %(homologacao_produto)s.status = 'TERCEIRIZADA_RESPONDEU_RECLAMACAO') "
                ),
            },
            "codae_nao_homologado": {
                "status__in": [
                    HomologacaoProdutoWorkflow.CODAE_NAO_HOMOLOGADO,
                    HomologacaoProdutoWorkflow.TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO,
                ],
                "raw_sql": (
                    "WHERE (%(homologacao_produto)s.status = 'TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO' "
                    f"OR %(homologacao_produto)s.status = '{filtro_aplicado.upper()}') "
                ),
            },
            "codae_suspendeu": {
                "status__in": [
                    HomologacaoProdutoWorkflow.CODAE_SUSPENDEU,
                    HomologacaoProdutoWorkflow.CODAE_AUTORIZOU_RECLAMACAO,
                    HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO,
                ],
                "raw_sql": (
                    "JOIN %(produto_edital)s ON %(homologacao_produto)s.produto_id = %(produto_edital)s.produto_id "
                    "WHERE (%(homologacao_produto)s.status IN ('CODAE_SUSPENDEU', 'CODAE_AUTORIZOU_RECLAMACAO') "
                    "OR (%(homologacao_produto)s.status = 'CODAE_HOMOLOGADO' "
                    "AND %(produto_edital)s.suspenso = True))"
                ),
            },
            "responder_questionamentos_da_codae": {
                "status__in": [
                    HomologacaoProdutoWorkflow.CODAE_QUESTIONOU_UE,
                    HomologacaoProdutoWorkflow.CODAE_QUESTIONOU_NUTRISUPERVISOR,
                    HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_RECLAMACAO,
                ],
                "raw_sql": (
                    "WHERE (%(homologacao_produto)s.status = 'CODAE_QUESTIONOU_UE' "
                    "OR %(homologacao_produto)s.status = 'CODAE_QUESTIONOU_NUTRISUPERVISOR' "
                    "OR %(homologacao_produto)s.status = 'CODAE_PEDIU_ANALISE_RECLAMACAO') "
                ),
            },
        }
        if filtro_aplicado and filtro_aplicado != "codae_pediu_analise_reclamacao":
            filtros["status__in"] = filtros_dict[filtro_aplicado]["status__in"]
            raw_sql += filtros_dict[filtro_aplicado]["raw_sql"]
            if filtro_aplicado == "responder_questionamentos_da_codae":
                raw_sql, filtros = self.build_raw_sql_filtro_dre(
                    raw_sql, None, None, tipo_usuario, filtros, escola_ou_dre_id
                )
        if filtro_aplicado == "codae_suspendeu":
            filtros["produto__vinculos__suspenso"] = True

        return raw_sql, filtros

    def build_raw_sql_produtos_por_status(
        self,
        filtro_aplicado,
        edital,
        perfil_nome,
        filtros,
        tipo_usuario,
        escola_ou_dre_id,
        editais=None,
    ):
        data = {
            "logs": LogSolicitacoesUsuario._meta.db_table,
            "homologacao_produto": HomologacaoProduto._meta.db_table,
            "reclamacoes_produto": ReclamacaoDeProduto._meta.db_table,
            "produto_edital": ProdutoEdital._meta.db_table,
            "escola": Escola._meta.db_table,
            "lote": Lote._meta.db_table,
        }

        raw_sql = (
            "SELECT %(homologacao_produto)s.* FROM %(homologacao_produto)s "
            "JOIN (SELECT uuid_original, status_evento, MAX(criado_em) AS log_criado_em FROM %(logs)s "
            "GROUP BY uuid_original, status_evento) "
            "AS most_recent_log "
            "ON %(homologacao_produto)s.uuid = most_recent_log.uuid_original "
        )
        if filtro_aplicado == "codae_homologado":
            raw_sql += f"AND most_recent_log.status_evento = {LogSolicitacoesUsuario.CODAE_HOMOLOGADO} "
        if edital:
            raw_sql += (
                "LEFT JOIN (SELECT DISTINCT id AS produto_edital_id, suspenso,"
                "produto_id as produto_id_prod_edit, edital_id as edital_id_prod_edit FROM %(produto_edital)s) "
                "AS produto_edital "
                "ON produto_edital.produto_id_prod_edit = %(homologacao_produto)s.produto_id AND "
                f"produto_edital.edital_id_prod_edit = {edital.id} AND produto_edital.suspenso = false "
            )
        elif editais:
            raw_sql += (
                "LEFT JOIN (SELECT DISTINCT id AS produto_edital_id, suspenso,"
                "produto_id as produto_id_prod_edit, edital_id as edital_id_prod_edit FROM %(produto_edital)s) "
                "AS produto_edital "
                "ON produto_edital.produto_id_prod_edit = %(homologacao_produto)s.produto_id AND "
                f"produto_edital.edital_id_prod_edit IN ({editais}) AND produto_edital.suspenso = false "
            )

        raw_sql += (
            "LEFT JOIN (SELECT DISTINCT ON (homologacao_produto_id) homologacao_produto_id, escola_id "
            "AS escola_reclamacao_id FROM %(reclamacoes_produto)s) AS homolog_com_reclamacao "
            "ON homolog_com_reclamacao.homologacao_produto_id = %(homologacao_produto)s.id "
            "LEFT JOIN (SELECT id AS escola_id_escola, lote_id FROM %(escola)s) "
            "AS escola_reclamacao "
            "ON escola_reclamacao.escola_id_escola = escola_reclamacao_id "
            "LEFT JOIN (SELECT id AS lote_id_lote, terceirizada_id, "
            "diretoria_regional_id FROM %(lote)s) AS escola_lote "
            "ON escola_lote.lote_id_lote = lote_id "
        )

        raw_sql, filtros = self.build_raw_sql_filtro_codae_pediu_analise_reclamacao(
            raw_sql,
            filtro_aplicado,
            perfil_nome,
            filtros,
            tipo_usuario,
            escola_ou_dre_id,
        )
        raw_sql, filtros = self.build_raw_sql_filtro_aplicado(
            raw_sql, filtro_aplicado, filtros, tipo_usuario, escola_ou_dre_id
        )
        raw_sql = self.trata_edital(raw_sql, edital, editais=editais)
        raw_sql = self.checa_se_remove_eh_copia(filtro_aplicado, raw_sql)
        raw_sql += "ORDER BY log_criado_em DESC"
        return raw_sql, data

    def checa_se_remove_eh_copia_queryset(self, filtro_aplicado, query_set):
        if filtro_aplicado not in [
            "codae_pendente_homologacao",
            "codae_questionado",
            "codae_pediu_analise_sensorial",
        ]:
            query_set = query_set.filter(eh_copia=False)
        return query_set

    def exclui_produtos_suspensos(
        self,
        query_set,
        produtos_editais_mais_de_uma_data_hora,
        edital,
        data_homologacao,
    ):
        homs_mais_de_uma_data_hora = query_set.filter(
            produto__vinculos__in=produtos_editais_mais_de_uma_data_hora
        ).distinct()
        for hom_produto in homs_mais_de_uma_data_hora:
            produto_edital = hom_produto.produto.vinculos.get(edital=edital)
            data_hora = produto_edital.data_hora_mais_proxima(data_homologacao)
            if data_hora.suspenso:
                query_set = query_set.exclude(uuid=hom_produto.uuid)
        return query_set

    def atualiza_queryset_de_homologados(
        self,
        query_set,
        titulo,
        request_data,
        filtros,
        filtro_aplicado,
        edital,
        contem_edital_associado,
        instituicao,
    ):
        if titulo:
            query_set = query_set.annotate(
                id_amigavel=Substr(Cast(F("uuid"), output_field=CharField()), 1, 5)
            ).filter(
                Q(id_amigavel__icontains=titulo) | Q(produto__nome__icontains=titulo)
            )
        filtros_params = cria_filtro_homologacao_produto_por_parametros(request_data)
        query_set_nao_homologados = (
            query_set.filter(
                status__in=[
                    "CODAE_NAO_HOMOLOGADO",
                    "CODAE_AUTORIZOU_RECLAMACAO",
                    "CODAE_SUSPENDEU",
                ]
            )
            .filter(**filtros_params)
            .distinct()
        )
        self.checa_se_remove_eh_copia_queryset(filtro_aplicado, query_set)
        query_set = query_set.filter(**filtros).filter(**filtros_params).distinct()

        if request_data.get("data_homologacao"):
            data_homologacao = datetime.strptime(
                request_data.get("data_homologacao"), "%d/%m/%Y"
            ).date()
            query_set = query_set | query_set_nao_homologados
            query_set = query_set.filter(
                produto__vinculos__edital=edital,
                produto__vinculos__datas_horas_vinculo__suspenso=False,
                produto__vinculos__datas_horas_vinculo__criado_em__date__lte=data_homologacao,
            )
            produtos_editais_mais_de_uma_data_hora = ProdutoEdital.objects.annotate(
                Count("datas_horas_vinculo")
            ).filter(datas_horas_vinculo__count__gt=1)
            query_set = self.exclui_produtos_suspensos(
                query_set,
                produtos_editais_mais_de_uma_data_hora,
                edital,
                data_homologacao,
            )
        elif edital:
            query_set = query_set.filter(
                produto__vinculos__edital=edital,
                produto__vinculos__suspenso=False,
            )
        elif contem_edital_associado:
            query_set = query_set.filter(
                produto__vinculos__edital__uuid__in=instituicao.editais,
                produto__vinculos__suspenso=False,
            )
        query_set = sorted(
            query_set,
            key=lambda x: x.produto.data_homologacao or x.produto.criado_em,
            reverse=True,
        )
        return query_set

    def get_queryset_solicitacoes_homologacao_por_status(
        self,
        request_data,
        perfil_nome,
        tipo_usuario,
        escola_ou_dre_id,
        filtro_aplicado,
        instituicao=None,
    ):
        filtros = {}
        page = request_data.get("page", False)
        nome_edital = request_data.get("nome_edital", None)
        contem_edital_associado = hasattr(instituicao, "editais")
        edital = None
        editais = None
        query_set = self.get_queryset()
        if nome_edital:
            edital = Edital.objects.get(numero=nome_edital)
        elif contem_edital_associado:
            id_editais = query_set.filter(
                produto__vinculos__edital__uuid__in=instituicao.editais,
            ).values_list("produto__vinculos__edital__id", flat=True)
            editais = ", ".join(f"'{edital}'" for edital in list(set(id_editais)))
        algum_filtro = (
            request_data.get("nome_terceirizada")
            or request_data.get("data_homologacao")
            or request_data.get("nome_produto")
            or request_data.get("nome_fabricante")
            or request_data.get("nome_marca")
            or request_data.get("tipo")
        )
        titulo = request_data.get("titulo_produto", None)

        raw_sql, data = self.build_raw_sql_produtos_por_status(
            filtro_aplicado,
            edital,
            perfil_nome,
            filtros,
            tipo_usuario,
            escola_ou_dre_id,
            editais=editais,
        )
        if page or (edital and not algum_filtro and not titulo):
            query_set = query_set.raw(raw_sql % data)
        else:
            query_set = self.atualiza_queryset_de_homologados(
                query_set,
                titulo,
                request_data,
                filtros,
                filtro_aplicado,
                edital,
                contem_edital_associado,
                instituicao,
            )
        return query_set

    @action(
        detail=False,
        methods=["GET", "POST"],
        url_path=f"filtro-por-status/{constants.FILTRO_STATUS_HOMOLOGACAO}",
    )
    def solicitacoes_homologacao_por_status(
        self, request, filtro_aplicado=constants.RASCUNHO
    ):  # noqa C901
        page = request.query_params.get("page", None)
        user = self.request.user
        query_set = self.get_queryset_solicitacoes_homologacao_por_status(
            request.query_params,
            user.vinculo_atual.perfil.nome,
            user.tipo_usuario,
            user.vinculo_atual.object_id,
            filtro_aplicado,
            instituicao=user.vinculo_atual.instituicao,
        )

        solicitacoes_viewset = SolicitacoesViewSet()
        query_set = solicitacoes_viewset.remove_duplicados_do_query_set(query_set)

        if page:
            page = self.paginate_queryset(query_set)
            serializer = HomologacaoProdutoPainelGerencialSerializer(
                page,
                context={"request": request, "workflow": filtro_aplicado.upper()},
                many=True,
            )
            return self.get_paginated_response(serializer.data)
        else:
            serializer = (
                HomologacaoProdutoPainelGerencialSerializer
                if filtro_aplicado != constants.RASCUNHO
                else HomologacaoProdutoSerializer
            )
            response = {
                "results": serializer(
                    query_set,
                    context={"request": request, "workflow": filtro_aplicado.upper()},
                    many=True,
                ).data
            }
            return Response(response)


class HomologacaoProdutoViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    serializer_class = HomologacaoProdutoSerializer
    queryset = HomologacaoProduto.objects.all()

    @action(
        detail=True,
        permission_classes=(UsuarioCODAEGestaoProduto,),
        methods=["patch"],
        url_path=constants.CODAE_HOMOLOGA,
    )
    def codae_homologa(self, request, uuid=None):  # noqa C901
        homologacao_produto = self.get_object()
        uri = reverse("Produtos-relatorio", args=[homologacao_produto.produto.uuid])
        editais = request.data.get("editais", [])
        if not editais:
            return Response(
                dict(detail="É necessario informar algum edital."),
                status=HTTP_406_NOT_ACCEPTABLE,
            )
        try:
            if homologacao_produto.eh_copia:
                homologacao_produto = (
                    homologacao_produto.equaliza_homologacoes_e_se_destroi()
                )
            homologacao_produto.codae_homologa(
                user=request.user, link_pdf=url_configs("API", {"uri": uri})
            )

            homologacao_produto.vincula_ou_desvincula_editais(
                editais, request.data.get("justificativa", ""), request.user
            )

            return Response(
                {
                    "uuid": homologacao_produto.uuid,
                    "status": str(homologacao_produto.status),
                },
                status=status.HTTP_200_OK,
            )
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=(UsuarioCODAEGestaoProduto,),
        methods=["patch"],
        url_path=constants.CODAE_NAO_HOMOLOGA,
    )
    def codae_nao_homologa(self, request, uuid=None):
        homologacao_produto = self.get_object()
        uri = reverse("Produtos-relatorio", args=[homologacao_produto.produto.uuid])
        try:
            justificativa = request.data.get("justificativa", "")
            homologacao_produto.codae_nao_homologa(
                user=request.user,
                justificativa=justificativa,
                link_pdf=url_configs("API", {"uri": uri}),
            )
            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=(UsuarioCODAEGestaoProduto,),
        methods=["patch"],
        url_path=constants.CODAE_QUESTIONA_PEDIDO,
    )
    def codae_questiona(self, request, uuid=None):
        homologacao_produto = self.get_object()
        uri = reverse("Produtos-relatorio", args=[homologacao_produto.produto.uuid])
        try:
            justificativa = request.data.get("justificativa", "")
            homologacao_produto.codae_questiona(
                user=request.user,
                justificativa=justificativa,
                link_pdf=url_configs("API", {"uri": uri}),
            )
            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,  # noqa C901
        permission_classes=(UsuarioCODAEGestaoProduto,),
        methods=["patch"],
        url_path=constants.CODAE_PEDE_ANALISE_SENSORIAL,
    )
    def codae_pede_analise_sensorial(self, request, uuid=None):
        from sme_sigpae_api.produto.models import AnaliseSensorial
        from sme_sigpae_api.terceirizada.models import Terceirizada

        homologacao_produto = self.get_object()
        uri = reverse("Produtos-relatorio", args=[homologacao_produto.produto.uuid])
        try:
            justificativa = request.data.get("justificativa", "")
            terceirizada_uuid = request.data.get("uuidTerceirizada", "")
            if not terceirizada_uuid:
                return Response({"detail": "O uuid da terceirizada é obrigatório"})

            terceirizada = Terceirizada.objects.filter(uuid=terceirizada_uuid).first()
            if not terceirizada:
                return Response(
                    {
                        "detail": f"Terceirizada para uuid {terceirizada_uuid} não encontrado."
                    }
                )

            AnaliseSensorial.objects.create(
                homologacao_produto=homologacao_produto, terceirizada=terceirizada
            )

            homologacao_produto.gera_protocolo_analise_sensorial()
            homologacao_produto.codae_pede_analise_sensorial(
                user=request.user,
                justificativa=justificativa,
                link_pdf=url_configs("API", {"uri": uri}),
            )

            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,  # noqa C901
        permission_classes=(UsuarioCODAEGestaoProduto,),
        methods=["patch"],
        url_path=constants.CODAE_CANCELA_ANALISE_SENSORIAL,
    )
    def codae_cancela_analise_sensorial(self, request, uuid=None):
        from sme_sigpae_api.produto.models import AnaliseSensorial

        homologacao_produto = self.get_object()
        _status = LogSolicitacoesUsuario.STATUS_POSSIVEIS
        status = {v: k for (k, v) in _status}
        try:
            justificativa = request.data.get("justificativa", "")
            logs = homologacao_produto.logs
            log_anterior_pedido_analise = logs[logs.count() - 2]
            homologacao_produto.codae_cancela_analise_sensorial(
                user=request.user,
                justificativa=justificativa,
            )

            if (
                log_anterior_pedido_analise.status_evento
                == status["Escola/Nutricionista reclamou do produto"]
            ):
                homologacao_produto.escola_ou_nutricionista_reclamou(
                    user=log_anterior_pedido_analise.usuario,
                    reclamacao={
                        "reclamacao": log_anterior_pedido_analise.justificativa
                    },
                    nao_enviar_email=True,
                )
                ultima_reclamacao = homologacao_produto.reclamacoes.last()
                ultima_reclamacao.codae_cancela_analise_sensorial(
                    user=log_anterior_pedido_analise.usuario,
                    anexos=ultima_reclamacao.anexos.all(),
                    justificativa=ultima_reclamacao.reclamacao,
                )
            elif (
                log_anterior_pedido_analise.status_evento
                == status["Solicitação Realizada"]
            ):
                homologacao_produto.inicia_fluxo(
                    user=log_anterior_pedido_analise.usuario
                )
            elif homologacao_produto.esta_homologado():
                homologacao_produto.codae_homologa(
                    user=log_anterior_pedido_analise.usuario,
                    anexos=log_anterior_pedido_analise.anexos.all(),
                    justificativa=log_anterior_pedido_analise.justificativa,
                    nao_enviar_email=True,
                )

            homologacao_produto.protocolo_analise_sensorial = ""
            uuid_ultima_analise = homologacao_produto.ultima_analise.uuid
            AnaliseSensorial.objects.get(uuid=uuid_ultima_analise).delete()
            homologacao_produto.save()

            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=(UsuarioCODAEGestaoProduto,),
        methods=["patch"],
        url_path=constants.CODAE_CANCELA_SOLICITACAO_CORRECAO,
    )
    def codae_cancela_solicitacao_correcao(self, request, uuid=None):
        homologacao_produto = self.get_object()
        uri = reverse("Produtos-relatorio", args=[homologacao_produto.produto.uuid])
        try:
            justificativa = request.data.get("justificativa", "")
            homologacao_produto.codae_cancela_solicitacao_correcao(
                user=request.user,
                justificativa=justificativa,
                link_pdf=url_configs("API", {"uri": uri}),
            )
            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=(IsAuthenticated,),
        methods=["patch"],
        url_path=constants.TERCEIRIZADA_CANCELA_SOLICITACAO_CORRECAO,
    )
    def terceiriazada_cancela_solicitacao_correcao(self, request, uuid=None):
        homologacao_produto = self.get_object()
        uri = reverse("Produtos-relatorio", args=[homologacao_produto.produto.uuid])
        try:
            justificativa = request.data.get("justificativa", "")
            homologacao_produto.terceirizada_cancela_solicitacao_correcao(
                user=request.user,
                justificativa=justificativa,
                link_pdf=url_configs("API", {"uri": uri}),
            )
            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,  # noqa C901
        permission_classes=[PermissaoParaReclamarDeProduto],
        methods=["patch"],
        url_path=constants.ESCOLA_OU_NUTRI_RECLAMA,
    )
    def escola_ou_nutricodae_reclama(self, request, uuid=None):
        homologacao_produto = self.get_object()
        data = request.data.copy()
        data["homologacao_produto"] = homologacao_produto.id
        data["criado_por"] = request.user.id
        try:
            serializer_reclamacao = ReclamacaoDeProdutoSerializerCreate(data=data)
            if not serializer_reclamacao.is_valid():
                return Response(serializer_reclamacao.errors)
            serializer_reclamacao.save()
            if (
                homologacao_produto.status
                == HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO
            ):
                homologacao_produto.escola_ou_nutricionista_reclamou(
                    user=request.user, reclamacao=serializer_reclamacao.data
                )
            return Response(serializer_reclamacao.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=[UsuarioCODAEGestaoProduto],
        methods=["patch"],
        url_path=constants.CODAE_PEDE_ANALISE_RECLAMACAO,
    )
    def codae_pede_analise_reclamacao(self, request, uuid=None):
        anexos = request.data.get("anexos", [])
        justificativa = request.data.get("justificativa", "")
        homologacao_produto = self.get_object()
        try:
            homologacao_produto.codae_pediu_analise_reclamacao(
                user=request.user, anexos=anexos, justificativa=justificativa
            )
            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=[UsuarioCODAEGestaoProduto],
        methods=["patch"],
        url_path=constants.CODAE_ACEITA_RECLAMACAO,
    )
    def codae_aceita_reclamacao(self, request, uuid=None):
        anexos = request.data.get("anexos", [])
        justificativa = request.data.get("justificativa", "")
        homologacao_produto = self.get_object()
        try:
            homologacao_produto.codae_autorizou_reclamacao(
                user=request.user,
                anexos=anexos,
                justificativa=justificativa,
                nao_enviar_email=True,
            )
            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=[UsuarioCODAEGestaoProduto],
        methods=["patch"],
        url_path=constants.CODAE_RECUSA_RECLAMACAO,
    )
    def codae_recusa_reclamacao(self, request, uuid=None):
        anexos = request.data.get("anexos", [])
        justificativa = request.data.get("justificativa", "")
        homologacao_produto = self.get_object()
        try:
            homologacao_produto.codae_homologa(
                user=request.user,
                anexos=anexos,
                justificativa=justificativa,
                nao_enviar_email=True,
            )
            serializer = self.get_serializer(homologacao_produto)
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    def cria_datas_horas_vinculos(
        self, editais_para_suspensao_ativacao, homologacao_produto
    ):
        for edital_uuid in editais_para_suspensao_ativacao:
            produto_edital = ProdutoEdital.objects.get(
                edital__uuid=edital_uuid, produto=homologacao_produto.produto
            )
            produto_edital.criar_data_hora_vinculo(suspenso=True)

    @action(
        detail=True,
        permission_classes=[UsuarioCODAEGestaoProduto],
        methods=["patch"],
        url_path=constants.SUSPENDER_PRODUTO,
    )
    def suspender(self, request, uuid=None):
        homologacao_produto = self.get_object()
        if homologacao_produto.eh_copia:
            homologacao_produto = (
                homologacao_produto.equaliza_homologacoes_e_se_destroi()
            )
        usuario = request.user
        justificativa = request.data.get("justificativa", "")
        editais_para_suspensao_ativacao = request.data.get(
            "editais_para_suspensao_ativacao", ""
        )
        vinculos_produto_edital = homologacao_produto.produto.vinculos.all()
        numeros_editais_para_justificativa = ", ".join(
            vinculos_produto_edital.filter(
                edital__uuid__in=editais_para_suspensao_ativacao
            ).values_list("edital__numero", flat=True)
        )
        justificativa += "<br><p>Editais suspensos:</p>"
        justificativa += f"<p>{numeros_editais_para_justificativa}</p>"

        try:
            vinculos_produto_edital.filter(
                edital__uuid__in=editais_para_suspensao_ativacao
            ).update(
                suspenso=True,
                suspenso_justificativa=justificativa,
                suspenso_em=datetime.now(),
                suspenso_por=usuario,
            )
            self.cria_datas_horas_vinculos(
                editais_para_suspensao_ativacao, homologacao_produto
            )
            if vinculos_produto_edital.filter(suspenso=False):
                homologacao_produto.salva_log_com_justificativa_e_anexos(
                    LogSolicitacoesUsuario.SUSPENSO_EM_ALGUNS_EDITAIS,
                    request,
                    justificativa,
                )
                if (
                    homologacao_produto.status
                    == HomologacaoProduto.workflow_class.CODAE_PENDENTE_HOMOLOGACAO
                ):
                    homologacao_produto.status = (
                        HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO
                    )
                    homologacao_produto.save()
            else:
                homologacao_produto.codae_suspende(request=request)
            return Response(
                self.get_serializer(homologacao_produto).data, status=status.HTTP_200_OK
            )
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    def update_vinculos(
        self,
        vinculos_produto_edital,
        editais_para_suspensao_ativacao,
        homologacao_produto,
    ):
        vinculos_produto_edital.filter(
            edital__uuid__in=editais_para_suspensao_ativacao
        ).update(
            suspenso=False,
            suspenso_justificativa="",
            suspenso_em=None,
            suspenso_por=None,
        )
        for edital_uuid in editais_para_suspensao_ativacao:
            if not vinculos_produto_edital.filter(edital__uuid=edital_uuid).exists():
                ProdutoEdital.objects.create(
                    produto=homologacao_produto.produto,
                    edital=Edital.objects.get(uuid=edital_uuid),
                    suspenso=False,
                )
            produto_edital = ProdutoEdital.objects.get(
                edital__uuid=edital_uuid, produto=homologacao_produto.produto
            )
            produto_edital.criar_data_hora_vinculo()

    def generate_justificativa(
        self, vinculos_produto_edital, editais_para_suspensao_ativacao
    ):
        numeros_editais_para_justificativa = ", ".join(
            vinculos_produto_edital.filter(
                edital__uuid__in=editais_para_suspensao_ativacao
            ).values_list("edital__numero", flat=True)
        )
        return f"<br><p>Editais ativos:</p><p>{numeros_editais_para_justificativa}</p>"

    @action(
        detail=True,
        permission_classes=[UsuarioCODAEGestaoProduto],
        methods=["patch"],
        url_path=constants.ATIVAR_PRODUTO,
    )
    def ativar(self, request, uuid=None):
        try:
            homologacao_produto = self.get_object()
            editais_para_suspensao_ativacao = request.data.get(
                "editais_para_suspensao_ativacao", ""
            )
            vinculos_produto_edital = homologacao_produto.produto.vinculos.all()

            self.update_vinculos(
                vinculos_produto_edital,
                editais_para_suspensao_ativacao,
                homologacao_produto,
            )
            justificativa = request.data.get(
                "justificativa", ""
            ) + self.generate_justificativa(
                vinculos_produto_edital, editais_para_suspensao_ativacao
            )

            if vinculos_produto_edital.filter(suspenso=True):
                homologacao_produto.salva_log_com_justificativa_e_anexos(
                    LogSolicitacoesUsuario.ATIVO_EM_ALGUNS_EDITAIS,
                    request,
                    justificativa,
                )
                if homologacao_produto.status in [
                    "CODAE_SUSPENDEU",
                    "CODAE_AUTORIZOU_RECLAMACAO",
                ]:
                    homologacao_produto.status = (
                        HomologacaoProduto.workflow_class.states.CODAE_HOMOLOGADO
                    )
                    homologacao_produto.save()
            else:
                homologacao_produto.codae_ativa(request=request)
            return Response("Homologação ativada")
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=[UsuarioTerceirizadaProduto],
        methods=["patch"],
        url_path=constants.TERCEIRIZADA_RESPONDE_RECLAMACAO,
    )
    def terceirizada_responde_reclamacao(self, request, uuid=None):
        homologacao_produto = self.get_object()
        try:
            homologacao_produto.terceirizada_responde_reclamacao(request=request)
            return Response("Reclamação respondida")
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["GET"], url_path="reclamacao")
    def reclamacao_homologao(self, request, uuid=None):
        homologacao_produto = self.get_object()
        reclamacao = homologacao_produto.reclamacoes.filter(
            status=ReclamacaoProdutoWorkflow.CODAE_ACEITOU
        ).first()
        serializer = ReclamacaoDeProdutoSimplesSerializer(reclamacao)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="numero_protocolo")
    def numero_relatorio_analise_sensorial(self, request):
        homologacao = HomologacaoProduto()
        protocolo = homologacao.retorna_numero_do_protocolo()
        return Response(protocolo)

    def retorna_datetime(self, data):
        data = datetime.strptime(data, "%d/%m/%Y")
        return data

    @action(
        detail=True,
        permission_classes=[UsuarioTerceirizadaProduto],
        methods=["post"],
        url_path=constants.GERAR_PDF,
    )
    def gerar_pdf_homologacao(self, request, uuid=None):
        homologacao_produto = self.get_object()
        homologacao_produto.pdf_gerado = True
        homologacao_produto.save()
        return Response("PDF Homologação gerado")

    @action(
        detail=True,
        permission_classes=[IsAuthenticated],
        methods=["get"],
        url_path=constants.GERAR_PDF_FICHA_IDENTIFICACAO_PRODUTO,
    )
    def gerar_pdf_ficha_identificacao_produto(self, request, uuid=None):
        SERVER_NAME = env.str("SERVER_NAME", default=None)
        homologacao_produto = self.get_object()
        img_ids = [
            img.id
            for img in homologacao_produto.produto.imagens
            if img.nome.split(".")[len(img.nome.split(".")) - 1]
            in ["png", "jpg", "jpeg"]
        ]  # noqa E501
        imagens = homologacao_produto.produto.imagens.filter(id__in=img_ids)
        documentos = homologacao_produto.produto.imagens.exclude(id__in=img_ids)
        html_string = render_to_string(
            "ficha_identificacao_produto.html",
            {
                "homologacao_produto": homologacao_produto,
                "contato_empresa": homologacao_produto.rastro_terceirizada.contatos.first(),
                "editais_vinculados": ", ".join(
                    vinc.edital.numero
                    for vinc in homologacao_produto.produto.vinculos.filter(
                        suspenso=False
                    )
                ),
                "editais_suspensos": ", ".join(
                    vinc.edital.numero
                    for vinc in homologacao_produto.produto.vinculos.filter(
                        suspenso=True
                    )
                ),
                "informacoes_nutricionais": homologacao_produto.produto.informacoes_nutricionais.all(),
                "especificacao_primaria": homologacao_produto.produto.especificacoes.first(),
                "URL": SERVER_NAME,
                "imagens": imagens,
                "documentos": documentos,
                "base_static_url": staticfiles_storage.location,
            },
        )
        return html_to_pdf_response(
            html_string,
            f"ficha_identificacao_produto_{homologacao_produto.id_externo}.pdf",
        )

    @action(
        detail=False,
        permission_classes=[UsuarioTerceirizadaProduto],
        methods=["get"],
        url_path=constants.AGUARDANDO_ANALISE_SENSORIAL,
    )
    def homolocoes_aguardando_analise_sensorial(self, request):
        homologacoes = HomologacaoProduto.objects.filter(
            status=HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_SENSORIAL
        )
        serializer = self.get_serializer(homologacoes, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        permission_classes=[UsuarioTerceirizadaProduto],
        methods=["patch"],
        url_path=constants.TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO,
    )
    def terceirizada_cancelou_solicitacao_homologacao(self, request, uuid=None):
        homologacao_produto = self.get_object()
        justificativa = request.data.get("justificativa", "")
        try:
            homologacao_produto.terceirizada_cancelou_solicitacao_homologacao(
                user=request.user, justificativa=justificativa
            )
            return Response(
                "Cancelamento de solicitação de homologação realizada com sucesso!"
            )
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    def destroy(self, request, *args, **kwargs):
        homologacao_produto = self.get_object()
        if homologacao_produto.pode_excluir:
            homologacao_produto.produto.delete()
            homologacao_produto.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                dict(detail="Você só pode excluir quando o status for RASCUNHO."),
                status=status.HTTP_403_FORBIDDEN,
            )

    @action(
        detail=True,
        permission_classes=[UsuarioCODAEGestaoProduto],
        methods=["get"],
        url_path=constants.VINCULOS_ATIVOS_PRODUTO_EDITAL,
    )
    def homologacao_produtos_vinculos_ativos_editais(self, request, uuid=None):
        homologacao_produto = self.get_object()
        produto = homologacao_produto.produto
        serializer = VinculosProdutosEditalAtivosSerializer(produto).data
        return Response(serializer)

    @action(
        detail=True,
        permission_classes=[UsuarioTerceirizadaProduto],
        methods=["patch"],
        url_path="alteracao-produto-homologado",
    )
    def alteracao_produto_homologado(self, request, uuid=None):
        homologacao_produto = self.get_object()
        copia_hom_produto = homologacao_produto.cria_copia()
        serializer = ProdutoSerializerCreate(context={"request": request})
        request.data["uuid"] = copia_hom_produto.produto.uuid
        copia_atualizada = serializer.update(copia_hom_produto.produto, request.data)
        return Response({"uuid": copia_atualizada.uuid}, status=status.HTTP_200_OK)


class ProdutoViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    serializer_class = ProdutoSerializer
    queryset = Produto.objects.all()
    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ProdutoFilter

    def filtra_editais_dieta_ou_comum(self, request, queryset):
        if request.query_params.get("eh_para_alunos_com_dieta", None):
            eh_para_alunos_com_dieta = (
                "Dieta especial"
                if request.query_params.get("eh_para_alunos_com_dieta") == "true"
                else "Comum"
            )
            edital = request.query_params.get("nome_edital", None)
            if edital:
                queryset = queryset.filter(
                    vinculos__edital__numero=edital,
                    vinculos__tipo_produto=eh_para_alunos_com_dieta,
                )
            else:
                queryset = queryset.filter(
                    vinculos__tipo_produto=eh_para_alunos_com_dieta
                )
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = (
            self.filter_queryset(
                self.get_queryset().filter(homologacao__eh_copia=False)
            )
            .select_related("marca", "fabricante")
            .order_by("criado_em")
        )
        if isinstance(request.user.vinculo_atual.instituicao, Escola):
            contratos = (
                request.user.vinculo_atual.instituicao.lote.contratos_do_lote.all()
            )
            editais = contratos.values_list("edital", flat=True)
            queryset = queryset.filter(vinculos__edital__in=editais)
        filter_status = request.query_params.getlist("status")
        if filter_status:
            if filter_status == ["CODAE_SUSPENDEU"]:
                suspensos = queryset.filter(
                    homologacao__status="CODAE_SUSPENDEU"
                ).distinct()
                parcialmente_suspensos_status_homologado = queryset.filter(
                    homologacao__status="CODAE_HOMOLOGADO", vinculos__suspenso=True
                ).distinct()
                queryset = parcialmente_suspensos_status_homologado | suspensos
            elif Counter(filter_status) == Counter(
                ["CODAE_SUSPENDEU", "CODAE_HOMOLOGADO"]
            ):
                homologados = [
                    q
                    for q in queryset.filter(
                        homologacao__status="CODAE_HOMOLOGADO"
                    ).distinct()
                ]
                suspensos = [
                    q
                    for q in queryset.filter(
                        homologacao__status="CODAE_SUSPENDEU"
                    ).distinct()
                ]
                parcialmente_suspensos_status_homologado = [
                    q
                    for q in queryset.filter(
                        homologacao__status="CODAE_HOMOLOGADO", vinculos__suspenso=True
                    ).distinct()
                ]
                queryset = (
                    homologados + suspensos + parcialmente_suspensos_status_homologado
                )
                queryset = sorted(queryset, key=lambda prod: prod.criado_em)
            else:
                queryset = queryset.filter(homologacao__status__in=filter_status)
        queryset = self.filtra_editais_dieta_ou_comum(request, queryset)
        page = self.paginate_queryset(queryset)
        nome_edital = request.query_params.get("nome_edital", None)
        if page is not None:
            serializer = ProdutoListagemSerializer(
                page,
                context={"status": filter_status, "nome_edital": nome_edital},
                many=True,
            )
            return self.get_paginated_response(serializer.data)
        serializer = ProdutoListagemSerializer(
            queryset,
            context={"status": filter_status, "nome_edital": nome_edital},
            many=True,
        )
        return Response(serializer.data)

    def paginated_response(self, queryset):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, context={"request": self.request}, many=True
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.get_paginated_response(
            queryset, context={"request": self.request}, many=True
        )
        return Response(serializer.data)

    def get_serializer_class(self):  # noqa C901
        if self.action in ["create", "update", "partial_update"]:
            return ProdutoSerializerCreate
        if self.action == "filtro_relatorio_em_analise_sensorial":
            return ProdutoRelatorioAnaliseSensorialSerializer
        if self.action == "filtro_relatorio_situacao_produto":
            return ProdutoRelatorioSituacaoSerializer
        if self.action == "filtro_homologados_por_parametros":
            return ProdutoHomologadosPorParametrosSerializer
        if self.action == "filtro_relatorio_produto_suspenso":
            return ProdutoSuspensoSerializer
        if self.action in [
            "filtro_reclamacoes",
            "filtro_reclamacoes_terceirizada",
            "filtro_avaliar_reclamacoes",
        ]:
            return ProdutoReclamacaoSerializer
        return ProdutoSerializer

    @action(detail=False, methods=["GET"], url_path="lista-nomes")
    def lista_produtos(self, request):
        query_set = Produto.objects.filter(ativo=True)
        filtrar_por = request.query_params.get("filtrar_por", None)
        if filtrar_por == "reclamacoes/":
            query_set = query_set.filter(
                homologacao__reclamacoes__isnull=False,
                homologacao__status__in=[
                    "CODAE_PEDIU_ANALISE_RECLAMACAO",
                    "TERCEIRIZADA_RESPONDEU_RECLAMACAO",
                    "ESCOLA_OU_NUTRICIONISTA_RECLAMOU",
                ],
            )
        response = {"results": ProdutoSimplesSerializer(query_set, many=True).data}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-nomes-unicos")
    def lista_nomes_unicos(self, request):
        query_set = (
            self.filter_queryset(self.get_queryset())
            .filter(ativo=True)
            .values("nome")
            .distinct()
        )
        nomes_unicos = [p["nome"] for p in query_set]
        return Response({"results": nomes_unicos, "count": len(nomes_unicos)})

    @action(detail=False, methods=["GET"], url_path="lista-nomes-nova-reclamacao")
    def lista_produtos_nova_reclamacao(self, request):
        query_set = (
            self.filter_queryset(self.get_queryset())
            .filter(
                ativo=True, homologacao__status__in=NOVA_RECLAMACAO_HOMOLOGACOES_STATUS
            )
            .only("nome")
            .values("nome")
            .order_by("nome")
            .distinct()
        )
        response = {"results": [{"uuid": "uuid", "nome": r["nome"]} for r in query_set]}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-nomes-avaliar-reclamacao")
    def lista_produtos_avaliar_reclamacao(self, request):
        query_set = (
            Produto.objects.filter(
                ativo=True,
                homologacao__status__in=AVALIAR_RECLAMACAO_HOMOLOGACOES_STATUS,
                homologacao__reclamacoes__status__in=AVALIAR_RECLAMACAO_RECLAMACOES_STATUS,
            )
            .only("nome")
            .values("nome")
            .order_by("nome")
            .distinct()
        )
        response = {"results": [{"uuid": "uuid", "nome": r["nome"]} for r in query_set]}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-nomes-responder-reclamacao")
    def lista_produtos_responder_reclamacao(self, request):
        user = request.user
        query_set = (
            Produto.objects.filter(
                ativo=True,
                homologacao__status__in=RESPONDER_RECLAMACAO_HOMOLOGACOES_STATUS,
                homologacao__reclamacoes__status__in=RESPONDER_RECLAMACAO_RECLAMACOES_STATUS,
                homologacao__rastro_terceirizada=user.vinculo_atual.instituicao,
            )
            .only("nome")
            .values("nome")
            .order_by("nome")
            .distinct()
        )
        response = {"results": [{"uuid": "uuid", "nome": r["nome"]} for r in query_set]}
        return Response(response)

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-nomes-responder-reclamacao-escola",
    )
    def lista_produtos_responder_reclamacao_escola(self, request):
        user = request.user
        status_homologacoes = [
            HomologacaoProdutoWorkflow.CODAE_QUESTIONOU_UE,
            HomologacaoProdutoWorkflow.UE_RESPONDEU_QUESTIONAMENTO,
        ]

        status_reclamacoes = [ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_UE]

        query_set = (
            Produto.objects.filter(
                ativo=True,
                homologacao__status__in=status_homologacoes,
                homologacao__reclamacoes__status__in=status_reclamacoes,
                homologacao__reclamacoes__escola=user.vinculo_atual.instituicao,
            )
            .only("nome")
            .values("nome")
            .order_by("nome")
            .distinct()
        )
        response = {"results": [{"uuid": "uuid", "nome": r["nome"]} for r in query_set]}
        return Response(response)

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-nomes-responder-reclamacao-nutrisupervisor",
    )
    def lista_produtos_responder_reclamacao_nutrisupervisor(self, request):
        user = request.user
        status_homologacoes = [
            HomologacaoProdutoWorkflow.CODAE_QUESTIONOU_NUTRISUPERVISOR,
            HomologacaoProdutoWorkflow.NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO,
        ]

        status_reclamacoes = [
            ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_NUTRISUPERVISOR,
            ReclamacaoProdutoWorkflow.RESPONDIDO_NUTRISUPERVISOR,
        ]

        query_set = (
            Produto.objects.filter(
                ativo=True,
                homologacao__status__in=status_homologacoes,
                homologacao__reclamacoes__status__in=status_reclamacoes,
                homologacao__reclamacoes__reclamante_registro_funcional=user.registro_funcional,
            )
            .only("nome")
            .values("nome")
            .order_by("nome")
            .distinct()
        )
        response = {"results": [{"uuid": "uuid", "nome": r["nome"]} for r in query_set]}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-substitutos")
    def lista_substitutos(self, request):
        # Retorna todos os alimentos + os produtos homologados.
        status = "CODAE_HOMOLOGADO"
        alimentos = Alimento.objects.filter(tipo="E")
        produtos = Produto.objects.filter(ativo=True, homologacao__status=status)
        alimentos.model = Produto
        query_set = list(chain(alimentos, produtos))
        response = {"results": SubstitutosSerializer(query_set, many=True).data}
        return Response(response)

    @action(
        detail=False,
        methods=["GET"],
        url_path="filtro-por-nome/(?P<produto_nome>[^/.]+)",
    )
    def filtro_por_nome(self, request, produto_nome=None):
        query_set = Produto.filtrar_por_nome(nome=produto_nome)
        page = self.paginate_queryset(query_set)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="filtro-por-fabricante/(?P<fabricante_nome>[^/.]+)",
    )
    def filtro_por_fabricante(self, request, fabricante_nome=None):
        query_set = Produto.filtrar_por_fabricante(nome=fabricante_nome)
        page = self.paginate_queryset(query_set)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="filtro-por-marca/(?P<marca_nome>[^/.]+)",
    )
    def filtro_por_marca(self, request, marca_nome=None):
        query_set = Produto.filtrar_por_marca(nome=marca_nome)
        page = self.paginate_queryset(query_set)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["GET"], url_path="todos-produtos")
    def filtro_consolidado(self, request):
        query_set = Produto.objects.all()
        response = {"results": self.get_serializer(query_set, many=True).data}
        return Response(response)

    @action(
        detail=True,
        url_path=constants.RELATORIO,
        methods=["get"],
        permission_classes=(AllowAny,),
    )
    def relatorio(self, request, uuid=None):
        return relatorio_produto_homologacao(request, produto=self.get_object())

    @action(
        detail=True,
        url_path=constants.RELATORIO_ANALISE,
        methods=["get"],
        permission_classes=(IsAuthenticated,),
    )
    def relatorio_analise_sensorial(self, request, uuid=None):
        return relatorio_produto_analise_sensorial(request, produto=self.get_object())

    @action(
        detail=True,
        url_path=constants.RELATORIO_RECEBIMENTO,
        methods=["get"],
        permission_classes=(IsAuthenticated,),
    )
    def relatorio_analise_sensorial_recebimento(self, request, uuid=None):
        return relatorio_produto_analise_sensorial_recebimento(
            request, produto=self.get_object()
        )

    @action(detail=False, methods=["POST"], url_path="exportar-xlsx")
    def exportar_xlsx(self, request):
        agrupado_nome_marca = request.data.get("agrupado_por_nome_e_marca")
        user = request.user.get_username()
        gera_xls_relatorio_produtos_homologados_async.delay(
            user=user,
            nome_arquivo=f'relatorio_produtos_homologados{"_nome_marca" if agrupado_nome_marca else ""}.xlsx',
            data=request.data,
            perfil_nome=request.user.vinculo_atual.perfil.nome,
            tipo_usuario=request.user.tipo_usuario,
            object_id=request.user.vinculo_atual.object_id,
        )
        return Response(
            dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["GET"], url_path="filtro-homologados-por-parametros")
    def filtro_homologados_por_parametros(self, request):
        logs_homologados = LogSolicitacoesUsuario.objects.filter(
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO
        ).values_list("uuid_original", flat=True)
        queryset = (
            self.filter_queryset(self.get_queryset())
            .filter(homologacao__uuid__in=logs_homologados)
            .order_by("nome", "marca__nome")
        )
        if "aditivos" in request.query_params:
            filtro_aditivos = cria_filtro_aditivos(request.query_params["aditivos"])
            queryset = queryset.filter(filtro_aditivos)
        return self.paginated_response(queryset)

    @action(
        detail=False,
        methods=["GET"],
        url_path="filtro-reclamacoes-terceirizada",
        permission_classes=[
            UsuarioTerceirizadaProduto
            | UsuarioDiretoriaRegional
            | UsuarioCODAEGestaoAlimentacao
            | UsuarioNutricionista
            | UsuarioOrgaoFiscalizador
            | UsuarioCODAEGabinete
            | UsuarioDinutreDiretoria
        ],
    )
    def filtro_reclamacoes_terceirizada(self, request):
        uuid = request.query_params.get("uuid")
        if (
            self.request.user.tipo_usuario
            in [
                TIPO_USUARIO_TERCEIRIZADA,
                TIPO_USUARIO_NUTRISUPERVISOR,
                TIPO_USUARIO_CODAE_GABINETE,
                TIPO_USUARIO_DIRETORIA_REGIONAL,
                TIPO_USUARIO_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                TIPO_USUARIO_NUTRIMANIFESTACAO,
                TIPO_USUARIO_ORGAO_FISCALIZADOR,
            ]
            and uuid
        ):
            queryset = Produto.objects.filter(homologacao__uuid=uuid).annotate(
                qtde_questionamentos=Count("homologacao__reclamacoes")
            )
        else:
            filtro_homologacao = {
                "homologacao__reclamacoes__status": ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_TERCEIRIZADA
            }
            filtro_reclamacao = {
                "status__in": [
                    ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_TERCEIRIZADA,
                    ReclamacaoProdutoWorkflow.RESPONDIDO_TERCEIRIZADA,
                ]
            }

            qtde_questionamentos = Count(
                "homologacao__reclamacoes",
                filter=Q(
                    homologacao__reclamacoes__status=ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_TERCEIRIZADA
                ),
            )

            queryset = (
                self.filter_queryset(self.get_queryset())
                .filter(**filtro_homologacao)
                .prefetch_related(
                    Prefetch(
                        "homologacao__reclamacoes",
                        queryset=ReclamacaoDeProduto.objects.filter(
                            **filtro_reclamacao
                        ),
                    )
                )
                .annotate(qtde_questionamentos=qtde_questionamentos)
                .order_by("criado_em")
                .distinct()
            )
        return self.paginated_response(queryset)

    @action(detail=False, methods=["GET"], url_path="filtro-reclamacoes-escola")
    def filtro_reclamacoes_escola(self, request):
        user = self.request.user
        filtro_homologacao = {
            "homologacao__reclamacoes__status": ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_UE,
            "homologacao__reclamacoes__escola": user.vinculo_atual.instituicao,
        }
        filtro_reclamacao = {
            "status__in": [
                ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_UE,
                ReclamacaoProdutoWorkflow.RESPONDIDO_UE,
            ],
            "escola": user.vinculo_atual.instituicao,
        }
        qtde_questionamentos = Count(
            "homologacao__reclamacoes",
            filter=Q(
                homologacao__reclamacoes__status=ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_UE
            ),
        )

        queryset = (
            self.filter_queryset(self.get_queryset())
            .filter(**filtro_homologacao)
            .prefetch_related(
                Prefetch(
                    "homologacao__reclamacoes",
                    queryset=ReclamacaoDeProduto.objects.filter(**filtro_reclamacao),
                )
            )
            .annotate(qtde_questionamentos=qtde_questionamentos)
            .order_by("criado_em")
            .distinct()
        )

        return self.paginated_response(queryset)

    @action(
        detail=False, methods=["GET"], url_path="filtro-reclamacoes-nutrisupervisor"
    )
    def filtro_reclamacoes_nutrisupervisor(self, request):
        user = self.request.user
        filtro_homologacao = {
            "homologacao__reclamacoes__status__in": [
                ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_NUTRISUPERVISOR,
                ReclamacaoProdutoWorkflow.RESPONDIDO_NUTRISUPERVISOR,
            ],
            "homologacao__reclamacoes__reclamante_registro_funcional": user.registro_funcional,
        }
        filtro_reclamacao = {
            "status__in": [
                ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_NUTRISUPERVISOR,
                ReclamacaoProdutoWorkflow.RESPONDIDO_NUTRISUPERVISOR,
            ],
            "reclamante_registro_funcional": user.registro_funcional,
        }
        qtde_questionamentos = Count(
            "homologacao__reclamacoes",
            filter=Q(
                homologacao__reclamacoes__status__in=[
                    ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_NUTRISUPERVISOR,
                    ReclamacaoProdutoWorkflow.RESPONDIDO_NUTRISUPERVISOR,
                ]
            ),
        )

        queryset = (
            self.filter_queryset(self.get_queryset())
            .filter(**filtro_homologacao)
            .prefetch_related(
                Prefetch(
                    "homologacao__reclamacoes",
                    queryset=ReclamacaoDeProduto.objects.filter(**filtro_reclamacao),
                )
            )
            .annotate(qtde_questionamentos=qtde_questionamentos)
            .order_by("criado_em")
            .distinct()
        )

        return self.paginated_response(queryset)

    def filtra_produtos_em_analise_sensorial(self, request, queryset):
        data_analise_inicial = converte_para_datetime(
            request.query_params.get("data_analise_inicial", None)
        )
        data_analise_final = converte_para_datetime(
            request.query_params.get("data_analise_final", None)
        )
        para_excluir = []
        if data_analise_inicial or data_analise_final:
            filtros_data = get_filtros_data(data_analise_inicial, data_analise_final)
            for produto in queryset:
                ultima_homologacao = produto.homologacao
                ultima_resposta = ultima_homologacao.respostas_analise.last()
                log_analise = (
                    ultima_homologacao.logs.filter(
                        status_evento=LogSolicitacoesUsuario.CODAE_PEDIU_ANALISE_SENSORIAL,
                        **filtros_data,
                    )
                    .filter(criado_em__lte=ultima_resposta.criado_em)
                    .order_by("criado_em")
                    .last()
                )

                if log_analise is None:
                    para_excluir.append(produto.id)
        return queryset.exclude(id__in=para_excluir).order_by(
            "nome", "homologacao__rastro_terceirizada__nome_fantasia"
        )

    def filtra_produtos_suspensos_por_data(self, request, queryset):
        data_suspensao_inicial = converte_para_datetime(
            request.query_params.get("data_suspensao_inicial", None)
        )
        data_suspensao_final = converte_para_datetime(
            request.query_params.get("data_suspensao_final", None)
        )
        para_excluir = []
        if data_suspensao_inicial or data_suspensao_final:
            filtros_data = get_filtros_data(
                data_suspensao_inicial, data_suspensao_final
            )
            for produto in queryset:
                ultima_homologacao = produto.homologacao
                ultimo_log = ultima_homologacao.ultimo_log
                log_suspensao = ultima_homologacao.logs.filter(
                    id=ultimo_log.id,
                    status_evento=LogSolicitacoesUsuario.CODAE_SUSPENDEU,
                    **filtros_data,
                ).first()
                if log_suspensao is None:
                    para_excluir.append(produto.id)
        return queryset.exclude(id__in=para_excluir)

    def exclui_produtos_ativos(
        self,
        query_set,
        produtos_editais_mais_de_uma_data_hora,
        nome_edital,
        data_suspensao,
    ):
        homs_mais_de_uma_data_hora = query_set.filter(
            produto__vinculos__in=produtos_editais_mais_de_uma_data_hora
        ).distinct()
        for hom_produto in homs_mais_de_uma_data_hora:
            produto_edital = hom_produto.produto.vinculos.get(
                edital__numero=nome_edital
            )
            data_hora = produto_edital.data_hora_mais_proxima(data_suspensao)
            if not data_hora.suspenso:
                query_set = query_set.exclude(uuid=hom_produto.uuid)
        return query_set

    def queryset_produtos_suspensos_por_edital_status(self, query_params):
        nome_edital = query_params.get("nome_edital", None)
        status = ["CODAE_SUSPENDEU", "CODAE_AUTORIZOU_RECLAMACAO", "CODAE_HOMOLOGADO"]
        homologacoes = HomologacaoProduto.objects.filter(
            status__in=status,
            produto__vinculos__edital__numero=nome_edital,
            produto__vinculos__suspenso=True,
        )
        return homologacoes

    def lista_filtros(self, query_params):
        nome_produto = query_params.get("nome_produto", None)
        nome_marca = query_params.get("nome_marca", None)
        nome_fabricante = query_params.get("nome_fabricante", None)
        tipo = query_params.get("tipo", None)
        filtros = []
        if nome_produto:
            filtros.append(nome_produto)
        if nome_marca:
            filtros.append(nome_marca)
        if nome_fabricante:
            filtros.append(nome_fabricante)
        if tipo == "Comum":
            filtros.append("Comum")
        if tipo == "Dieta especial":
            filtros.append("Dieta especial")
        return filtros

    def filtra_produtos_suspensos(self, homologacoes, query_params):
        nome_produto = query_params.get("nome_produto", None)
        nome_marca = query_params.get("nome_marca", None)
        nome_fabricante = query_params.get("nome_fabricante", None)
        tipo = query_params.get("tipo", None)
        if nome_produto:
            homologacoes = homologacoes.filter(produto__nome=nome_produto)
        if nome_marca:
            homologacoes = homologacoes.filter(produto__marca__nome=nome_marca)
        if nome_fabricante:
            homologacoes = homologacoes.filter(
                produto__fabricante__nome=nome_fabricante
            )
        if tipo == "Comum":
            homologacoes = homologacoes.filter(produto__eh_para_alunos_com_dieta=False)
        if tipo == "Dieta especial":
            homologacoes = homologacoes.filter(produto__eh_para_alunos_com_dieta=True)
        return homologacoes

    def filtrar_suspensos_por_data(self, homologacoes, query_params):
        nome_edital = query_params.get("nome_edital", None)
        if query_params.get("data_suspensao_final", None) == "null":
            data_final = None
        else:
            data_final = query_params.get("data_suspensao_final", None)

        if data_final:
            data_final = datetime.strptime(data_final, "%d/%m/%Y").date()
            homologacoes = homologacoes.filter(
                produto__vinculos__edital__numero=nome_edital,
                produto__vinculos__datas_horas_vinculo__suspenso=True,
                produto__vinculos__datas_horas_vinculo__criado_em__date__lte=data_final,
            )
            produtos_editais_mais_de_uma_data_hora = ProdutoEdital.objects.annotate(
                Count("datas_horas_vinculo")
            ).filter(datas_horas_vinculo__count__gt=1)
            homologacoes = self.exclui_produtos_ativos(
                homologacoes,
                produtos_editais_mais_de_uma_data_hora,
                nome_edital,
                data_final,
            )
        else:
            homologacoes = homologacoes.filter(
                produto__vinculos__edital__numero=nome_edital,
                produto__vinculos__suspenso=True,
            )
        return homologacoes

    @action(detail=False, methods=["GET"], url_path="relatorio-produto-suspenso-pdf")
    def relatorio_produto_suspenso_pdf(self, request):  # noqa C901
        nome_edital = request.query_params.get("nome_edital", None)
        data_final = request.query_params.get("data_suspensao_final", None)
        filtros = self.lista_filtros(request.query_params)
        homologacoes = self.queryset_produtos_suspensos_por_edital_status(
            request.query_params
        )
        homologacoes = self.filtra_produtos_suspensos(
            homologacoes, request.query_params
        )
        homologacoes = self.filtrar_suspensos_por_data(
            homologacoes, request.query_params
        )
        queryset = Produto.objects.filter(
            pk__in=homologacoes.values_list("produto", flat=True)
        )
        queryset = queryset.order_by("nome")
        uuids_produto = list(set(queryset.values_list("uuid", flat=True)))

        user = request.user.get_username()
        gera_xls_relatorio_produtos_suspensos_async.delay(
            produtos_uuids=uuids_produto,
            nome_arquivo="relatorio_produtos_suspensos.pdf",
            nome_edital=nome_edital,
            user=user,
            data_final=data_final,
            filtros=filtros,
        )
        return Response(
            dict(detail="Solicitação de geração de arquivo recebida com sucesso."),
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["GET"], url_path="filtro-relatorio-produto-suspenso")
    def filtro_relatorio_produto_suspenso(self, request):  # noqa C901
        nome_edital = request.query_params.get("nome_edital", None)
        homologacoes = self.queryset_produtos_suspensos_por_edital_status(
            request.query_params
        )
        homologacoes = self.filtra_produtos_suspensos(
            homologacoes, request.query_params
        )
        homologacoes = self.filtrar_suspensos_por_data(
            homologacoes, request.query_params
        )
        queryset = Produto.objects.filter(
            pk__in=homologacoes.values_list("produto", flat=True)
        )
        queryset = queryset.order_by("nome")
        page = self.paginate_queryset(queryset)
        serializer = RelatorioProdutosSuspensosSerializer(
            page, context={"edital_numero": nome_edital}, many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=False, url_path="relatorio-produto-suspenso", methods=["GET"])
    def relatorio_produto_suspenso(self, request):
        queryset = (
            self.filter_queryset(self.get_queryset())
            .select_related("marca", "fabricante")
            .order_by("nome")
        )
        queryset = self.filtra_produtos_suspensos_por_data(request, queryset)
        filtros = self.request.query_params.dict()
        return relatorio_produtos_suspensos(queryset, filtros)

    @action(
        detail=False,
        methods=["GET"],
        url_path="filtro-relatorio-em-analise-sensorial",
        permission_classes=[UsuarioTerceirizadaProduto | UsuarioCODAEGestaoProduto],
    )
    def filtro_relatorio_em_analise_sensorial(self, request):
        queryset = (
            self.filter_queryset(self.get_queryset())
            .filter(homologacao__respostas_analise__isnull=False)
            .prefetch_related(
                Prefetch(
                    "homologacao",
                    queryset=HomologacaoProduto.objects.all().exclude(
                        respostas_analise__exact=None
                    ),
                )
            )
            .distinct()
        )
        queryset = self.filtra_produtos_em_analise_sensorial(
            request, queryset
        ).select_related("marca", "fabricante")
        return self.paginated_response(queryset)

    @action(
        detail=False,
        methods=["GET"],
        url_path="relatorio-em-analise-sensorial",
        permission_classes=[UsuarioTerceirizadaProduto | UsuarioCODAEGestaoProduto],
    )
    def relatorio_em_analise_sensorial(self, request):
        queryset = (
            self.filter_queryset(self.get_queryset())
            .filter(homologacao__respostas_analise__isnull=False)
            .prefetch_related(
                Prefetch(
                    "homologacao",
                    queryset=HomologacaoProduto.objects.all().exclude(
                        respostas_analise__exact=None
                    ),
                )
            )
            .distinct()
        )
        queryset = self.filtra_produtos_em_analise_sensorial(
            request, queryset
        ).select_related("marca", "fabricante")
        filtros = self.request.query_params.dict()
        produtos = ProdutoRelatorioAnaliseSensorialSerializer(queryset, many=True).data
        return relatorio_produtos_em_analise_sensorial(produtos, filtros)

    @action(detail=False, methods=["GET"], url_path="filtro-reclamacoes")
    def filtro_reclamacoes(self, request):
        filtro_reclamacao, filtro_homologacao = filtros_produto_reclamacoes(request)
        queryset = (
            self.filter_queryset(self.get_queryset())
            .filter(**filtro_homologacao)
            .prefetch_related(
                Prefetch(
                    "homologacao__reclamacoes",
                    queryset=ReclamacaoDeProduto.objects.filter(**filtro_reclamacao),
                )
            )
            .order_by("nome")
            .select_related("marca", "fabricante")
            .distinct()
        )
        return self.paginated_response(queryset)

    @action(
        detail=False,
        methods=["GET"],
        url_path="filtro-avaliar-reclamacoes",
        permission_classes=[UsuarioCODAEGestaoProduto],
    )
    def filtro_avaliar_reclamacoes(self, request):
        status_reclamacao = self.request.query_params.getlist("status_reclamacao")
        queryset = (
            self.filter_queryset(self.get_queryset())
            .prefetch_related("homologacao__reclamacoes")
            .filter(homologacao__reclamacoes__status__in=status_reclamacao)
            .order_by("nome")
            .select_related("marca", "fabricante")
            .distinct()
        )
        return self.paginated_response(queryset)

    @action(detail=False, methods=["GET"], url_path="relatorio-reclamacao")
    def relatorio_reclamacao(self, request):
        filtro_reclamacao, filtro_homologacao = filtros_produto_reclamacoes(request)
        queryset = (
            self.filter_queryset(self.get_queryset())
            .filter(**filtro_homologacao)
            .prefetch_related(
                Prefetch(
                    "homologacao__reclamacoes",
                    queryset=ReclamacaoDeProduto.objects.filter(**filtro_reclamacao),
                )
            )
            .order_by("nome")
            .distinct()
        )
        filtros = self.request.query_params.dict()
        return relatorio_reclamacao(queryset, filtros)

    @action(detail=False, methods=["GET"], url_path="ja-existe")
    def ja_existe(self, request):
        form = ProdutoJaExisteForm(request.GET)

        if not form.is_valid():
            return Response(form.errors)

        queryset = (
            self.get_queryset()
            .filter(**form.cleaned_data)
            .exclude(homologacao__status=HomologacaoProdutoWorkflow.RASCUNHO)
        )

        return Response({"produto_existe": queryset.count() > 0})

    @action(detail=False, methods=["GET"], url_path="autocomplete-nomes")
    def autocomplete_nomes(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        return Response(
            {
                "count": queryset.count(),
                "results": [value[0] for value in queryset.values_list("nome")],
            }
        )


class ProdutosEditaisViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = ProdutoEdital.objects.all()
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ["create"]:
            return ProdutoEditalCreateSerializer
        return ProdutoEditalSerializer

    @action(detail=True, methods=["patch"], url_path="ativar-inativar-produto")
    def ativar_inativar_produto(self, request, uuid=None):
        try:
            vinculo = ProdutoEdital.objects.get(uuid=uuid)
            vinculo.ativo = not vinculo.ativo
            vinculo.save()
            serializer = self.get_serializer(vinculo)
            return Response(dict(data=serializer.data), status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                dict(
                    detail=f"Erro ao Ativar/inativar vínculo do produto com edital: {e}"
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["GET"], url_path="lista-nomes-unicos")
    def lista_nomes_unicos(self, request):
        produtos_editais = self.get_queryset()
        usuario = request.user

        if hasattr(usuario.vinculo_atual.instituicao, "editais"):
            produtos_editais = produtos_editais.filter(
                edital__uuid__in=usuario.vinculo_atual.instituicao.editais
            )

        nomes_unicos = (
            produtos_editais.exclude(edital__numero="Edital de Pregão nº 41/sme/2017")
            .values_list("edital__numero", flat=True)
            .distinct()
        )
        return Response(
            {"results": nomes_unicos, "count": len(nomes_unicos)},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="filtros")
    def filtros(self, request):
        try:
            vinculos = self.get_queryset()
            produtos = vinculos.distinct("produto__nome").values(
                "produto__nome", "produto__uuid"
            )
            editais = Edital.objects.all().values("numero", "uuid")
            return Response(
                dict(produtos=produtos, editais=editais), status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                dict(detail=f"Erro ao consultar filtros: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"], url_path="filtrar")  # noqa c901
    def filtrar(self, request):
        queryset = self.get_queryset().order_by("produto__nome")
        nome = request.query_params.get("nome", None)
        edital = request.query_params.get("edital", None)
        tipo_dieta = request.query_params.get("tipo", None)
        if nome:
            queryset = queryset.filter(produto__nome__in=[nome])
        if edital:
            queryset = queryset.filter(edital__numero__in=[edital])
        if tipo_dieta:
            queryset = queryset.filter(tipo_produto=tipo_dieta)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data})

    @action(
        detail=False, methods=["get"], url_path="lista-produtos-opcoes"
    )  # noqa c901
    def lista_produtos_opcoes(self, request):
        try:
            editais_uuid = request.query_params.get("editais", "")
            tipo_produto_edital_origem = request.query_params.get(
                "tipo_produto_edital_origem", ""
            )
            editais_uuid = editais_uuid.split(";")
            queryset = self.get_queryset().filter(edital__uuid__in=editais_uuid)
            if (
                tipo_produto_edital_origem.lower()
                == ProdutoEdital.TIPO_PRODUTO["Comum"].lower()
            ):
                queryset = queryset.filter(
                    tipo_produto__icontains=ProdutoEdital.TIPO_PRODUTO["Comum"]
                )
            else:
                queryset = queryset.exclude(
                    tipo_produto__icontains=ProdutoEdital.TIPO_PRODUTO["Comum"]
                )
            queryset = queryset.order_by("produto__nome", "produto__marca__nome")
            data = self.get_serializer(queryset, many=True).data
            return Response(data=data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                dict(detail=f"Erro ao consultar produtos: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["GET"], url_path="lista-editais-dre")
    def lista_editais_dre(self, request):
        user = request.user
        dre = DiretoriaRegional.objects.get(nome=user.vinculo_atual.instituicao.nome)
        pks = Contrato.objects.filter(diretorias_regionais__in=[dre]).values_list(
            "edital", flat=True
        )
        queryset = Edital.objects.filter(pk__in=pks).order_by("pk").distinct("pk")
        response = {"results": EditalSimplesSerializer(queryset, many=True).data}
        return Response(response)


class NomeDeProdutoEditalViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = NomeDeProdutoEdital.objects.filter(ativo=True).all()
        data = NomeDeProdutoEditalSerializer(queryset, many=True).data
        return Response({"results": data})


class CadastroProdutoEditalViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = NomeDeProdutoEdital.objects.all()
    pagination_class = CadastroProdutosEditalPagination
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CadastroProdutosEditalFilter

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CadastroProdutosEditalCreateSerializer
        return CadastroProdutosEditalSerializer

    def get_queryset(self):
        if self.action in ["list"]:
            return NomeDeProdutoEdital.objects.filter(
                tipo_produto=NomeDeProdutoEdital.TERCEIRIZADA
            )
        return NomeDeProdutoEdital.objects.all()

    @action(detail=False, methods=["GET"], url_path="lista-completa-logistica")
    def lista_completa_logistica(self, _):
        queryset = self.queryset.filter(tipo_produto=NomeDeProdutoEdital.LOGISTICA)
        return Response(
            {"results": CadastroProdutosEditalSerializer(queryset, many=True).data}
        )

    @action(detail=False, methods=["GET"], url_path="produtos-logistica")
    def produtos_logistica(self, _):
        queryset = NomeDeProdutoEdital.objects.filter(
            tipo_produto=NomeDeProdutoEdital.LOGISTICA
        )
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["GET"], url_path="lista-nomes")
    def lista_de_nomes(self, _):
        return Response(
            {
                "results": [
                    item.nome
                    for item in self.queryset.filter(
                        tipo_produto=NomeDeProdutoEdital.TERCEIRIZADA
                    )
                ]
            }
        )

    @action(detail=False, methods=["GET"], url_path="lista-nomes-logistica")
    def lista_de_nomes_logistica(self, _):
        return Response(
            {
                "results": [
                    item.nome
                    for item in self.queryset.filter(
                        tipo_produto=NomeDeProdutoEdital.LOGISTICA
                    )
                ]
            }
        )

    class Meta:
        model = NomeDeProdutoEdital


class ProtocoloDeDietaEspecialViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    serializer_class = ProtocoloDeDietaEspecialSerializer
    queryset = ProtocoloDeDietaEspecial.objects.all()

    @action(detail=False, methods=["GET"], url_path="lista-nomes")
    def lista_protocolos(self, request):
        query_set = ProtocoloDeDietaEspecial.objects.filter(ativo=True)
        response = {"results": ProtocoloSimplesSerializer(query_set, many=True).data}
        return Response(response)


class FabricanteViewSet(viewsets.ModelViewSet, ListaNomesUnicos):
    lookup_field = "uuid"
    serializer_class = FabricanteSerializer
    queryset = Fabricante.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = FabricanteFilter

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if "page" in request.query_params:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data})

    @action(detail=False, methods=["GET"], url_path="lista-nomes")
    def lista_fabricantes(self, request):
        query_set = Fabricante.objects.all()
        filtrar_por = request.query_params.get("filtrar_por", None)
        if filtrar_por == "reclamacoes/":
            query_set = query_set.filter(
                produto__homologacao__reclamacoes__isnull=False,
                produto__homologacao__status__in=[
                    "CODAE_PEDIU_ANALISE_RECLAMACAO",
                    "TERCEIRIZADA_RESPONDEU_RECLAMACAO",
                    "ESCOLA_OU_NUTRICIONISTA_RECLAMOU",
                ],
            )
        response = {"results": FabricanteSimplesSerializer(query_set, many=True).data}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-nomes-nova-reclamacao")
    def lista_fabricantes_nova_reclamacao(self, request):
        query_set = (
            self.filter_queryset(self.get_queryset())
            .filter(
                produto__ativo=True,
                produto__homologacao__status__in=NOVA_RECLAMACAO_HOMOLOGACOES_STATUS,
            )
            .distinct("nome")
        )
        response = {"results": FabricanteSimplesSerializer(query_set, many=True).data}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-nomes-avaliar-reclamacao")
    def lista_fabricantes_avaliar_reclamacao(self, request):
        query_set = Fabricante.objects.filter(
            produto__homologacao__status__in=AVALIAR_RECLAMACAO_HOMOLOGACOES_STATUS,
            produto__homologacao__reclamacoes__status__in=AVALIAR_RECLAMACAO_RECLAMACOES_STATUS,
        ).distinct()
        response = {"results": FabricanteSimplesSerializer(query_set, many=True).data}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-nomes-responder-reclamacao")
    def lista_fabricantes_responder_reclamacao(self, request):
        user = request.user
        query_set = Fabricante.objects.filter(
            produto__homologacao__status__in=RESPONDER_RECLAMACAO_HOMOLOGACOES_STATUS,
            produto__homologacao__reclamacoes__status__in=RESPONDER_RECLAMACAO_RECLAMACOES_STATUS,
            produto__homologacao__rastro_terceirizada=user.vinculo_atual.instituicao,
        ).distinct()
        if user.tipo_usuario == "terceirizada":
            query_set = query_set.filter(
                produto__homologacao__rastro_terceirizada=user.vinculo_atual.instituicao
            )
        response = {"results": FabricanteSimplesSerializer(query_set, many=True).data}
        return Response(response)

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-nomes-responder-reclamacao-escola",
    )
    def lista_fabricantes_responder_reclamacao_escola(self, request):
        user = request.user
        status_homologacoes = [
            HomologacaoProdutoWorkflow.CODAE_QUESTIONOU_UE,
            HomologacaoProdutoWorkflow.UE_RESPONDEU_QUESTIONAMENTO,
        ]

        status_reclamacoes = [ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_UE]

        query_set = Fabricante.objects.filter(
            produto__homologacao__status__in=status_homologacoes,
            produto__homologacao__reclamacoes__status__in=status_reclamacoes,
            produto__homologacao__reclamacoes__escola=user.vinculo_atual.instituicao,
        ).distinct()

        response = {"results": FabricanteSimplesSerializer(query_set, many=True).data}
        return Response(response)

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-nomes-responder-reclamacao-nutrisupervisor",
    )
    def lista_fabricantes_responder_reclamacao_nutrisupervisor(self, request):
        user = request.user
        status_homologacoes = [
            HomologacaoProdutoWorkflow.CODAE_QUESTIONOU_NUTRISUPERVISOR,
            HomologacaoProdutoWorkflow.NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO,
        ]

        status_reclamacoes = [
            ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_NUTRISUPERVISOR,
            ReclamacaoProdutoWorkflow.RESPONDIDO_NUTRISUPERVISOR,
        ]

        query_set = Fabricante.objects.filter(
            produto__homologacao__status__in=status_homologacoes,
            produto__homologacao__reclamacoes__status__in=status_reclamacoes,
            produto__homologacao__reclamacoes__reclamante_registro_funcional=user.registro_funcional,
        ).distinct()

        response = {"results": FabricanteSimplesSerializer(query_set, many=True).data}
        return Response(response)


class MarcaViewSet(viewsets.ModelViewSet, ListaNomesUnicos):
    lookup_field = "uuid"
    serializer_class = MarcaSerializer
    queryset = Marca.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = MarcaFilter

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if "page" in request.query_params:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data})

    @action(detail=False, methods=["GET"], url_path="lista-nomes")
    def lista_marcas(self, request):
        query_set = Marca.objects.all()
        filtrar_por = request.query_params.get("filtrar_por", None)
        if filtrar_por == "reclamacoes/":
            query_set = query_set.filter(
                produto__homologacao__reclamacoes__isnull=False,
                produto__homologacao__status__in=[
                    "CODAE_PEDIU_ANALISE_RECLAMACAO",
                    "TERCEIRIZADA_RESPONDEU_RECLAMACAO",
                    "ESCOLA_OU_NUTRICIONISTA_RECLAMOU",
                ],
            )
        response = {"results": MarcaSimplesSerializer(query_set, many=True).data}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-nomes-nova-reclamacao")
    def lista_marcas_nova_reclamacao(self, request):
        query_set = (
            self.filter_queryset(self.get_queryset())
            .filter(
                produto__ativo=True,
                produto__homologacao__status__in=NOVA_RECLAMACAO_HOMOLOGACOES_STATUS,
            )
            .distinct("nome")
        )
        response = {"results": MarcaSimplesSerializer(query_set, many=True).data}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-nomes-avaliar-reclamacao")
    def lista_marcas_avaliar_reclamacao(self, request):
        query_set = Marca.objects.filter(
            produto__homologacao__status__in=AVALIAR_RECLAMACAO_HOMOLOGACOES_STATUS,
            produto__homologacao__reclamacoes__status__in=AVALIAR_RECLAMACAO_RECLAMACOES_STATUS,
        ).distinct()
        response = {"results": MarcaSimplesSerializer(query_set, many=True).data}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-nomes-responder-reclamacao")
    def lista_marcas_responder_reclamacao(self, request):
        user = request.user
        query_set = Marca.objects.filter(
            produto__homologacao__status__in=RESPONDER_RECLAMACAO_HOMOLOGACOES_STATUS,
            produto__homologacao__reclamacoes__status__in=RESPONDER_RECLAMACAO_RECLAMACOES_STATUS,
            produto__homologacao__rastro_terceirizada=user.vinculo_atual.instituicao,
        ).distinct()
        response = {"results": MarcaSimplesSerializer(query_set, many=True).data}
        return Response(response)

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-nomes-responder-reclamacao-escola",
    )
    def lista_marcas_responder_reclamacao_escola(self, request):
        user = request.user
        status_homologacoes = [
            HomologacaoProdutoWorkflow.CODAE_QUESTIONOU_UE,
            HomologacaoProdutoWorkflow.UE_RESPONDEU_QUESTIONAMENTO,
        ]

        status_reclamacoes = [ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_UE]

        query_set = Marca.objects.filter(
            produto__homologacao__status__in=status_homologacoes,
            produto__homologacao__reclamacoes__status__in=status_reclamacoes,
            produto__homologacao__reclamacoes__escola=user.vinculo_atual.instituicao,
        ).distinct()
        response = {"results": MarcaSimplesSerializer(query_set, many=True).data}
        return Response(response)

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-nomes-responder-reclamacao-nutrisupervisor",
    )
    def lista_marcas_responder_reclamacao_nutrisupervisor(self, request):
        user = request.user
        status_homologacoes = [
            HomologacaoProdutoWorkflow.CODAE_QUESTIONOU_NUTRISUPERVISOR,
            HomologacaoProdutoWorkflow.NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO,
        ]

        status_reclamacoes = [
            ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_NUTRISUPERVISOR,
            ReclamacaoProdutoWorkflow.RESPONDIDO_NUTRISUPERVISOR,
        ]

        query_set = Marca.objects.filter(
            produto__homologacao__status__in=status_homologacoes,
            produto__homologacao__reclamacoes__status__in=status_reclamacoes,
            produto__homologacao__reclamacoes__reclamante_registro_funcional=user.registro_funcional,
        ).distinct()
        response = {"results": MarcaSimplesSerializer(query_set, many=True).data}
        return Response(response)


class InformacaoNutricionalViewSet(InformacaoNutricionalBaseViewSet):
    lookup_field = "uuid"
    serializer_class = InformacaoNutricionalSerializer
    queryset = InformacaoNutricional.objects.all()

    @action(detail=False, methods=["GET"], url_path="agrupadas")
    def informacoes_nutricionais_agrupadas(self, request):
        query_set = InformacaoNutricional.objects.all().order_by("id")
        response = {"results": self._agrupa_informacoes_por_tipo(query_set)}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="ordenadas")
    def informacoes_nutricionais_ordenadas(self, request):
        query_set = InformacaoNutricional.ordenadas()
        response = {
            "results": InformacaoNutricionalSerializer(query_set, many=True).data
        }
        return Response(response)


class RespostaAnaliseSensorialViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    serializer_class = RespostaAnaliseSensorialSearilzerCreate
    queryset = RespostaAnaliseSensorial.objects.all()

    @action(
        detail=False,
        permission_classes=[UsuarioTerceirizadaProduto],
        methods=["post"],
        url_path=constants.TERCEIRIZADA_RESPONDE_ANALISE_SENSORIAL,
    )
    def terceirizada_responde(self, request):  # noqa C901
        data = request.data.copy()
        uuid_homologacao = data.pop("homologacao_de_produto", None)
        data["homologacao_produto"] = uuid_homologacao
        json_data = json.dumps(data["anexos"])
        anexos = json.loads(json_data)
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        homologacao = HomologacaoProduto.objects.get(uuid=uuid_homologacao)
        data["homologacao_produto"] = homologacao

        try:
            serializer.create(data)
            justificativa = request.data.get("justificativa", "")
            if not justificativa:
                justificativa = data.get("observacao", "")

            reclamacao = homologacao.reclamacoes.filter(
                status=ReclamacaoProdutoWorkflow.AGUARDANDO_ANALISE_SENSORIAL
            ).first()
            if reclamacao:
                # Respondendo análise sensorial vindo de uma Homologação de produto em processo de reclamação.
                reclamacao.terceirizada_responde_analise_sensorial(
                    user=request.user, justificativa=justificativa
                )
                # Assim a homologação volta a aparecer no card de aguardando análise reclamações.
                homologacao.terceirizada_responde_analise_sensorial_da_reclamacao(
                    user=request.user, justificativa=justificativa, anexos=anexos
                )
            else:
                homologacao.terceirizada_responde_analise_sensorial(
                    user=request.user, justificativa=justificativa, anexos=anexos
                )
            serializer.save()

            analise_sensorial = homologacao.ultima_analise
            if analise_sensorial:
                analise_sensorial.status = AnaliseSensorial.STATUS_RESPONDIDA
                analise_sensorial.save()

            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )


class ReclamacaoProdutoViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    serializer_class = ReclamacaoDeProdutoSerializer
    queryset = ReclamacaoDeProduto.objects.all()

    def muda_status_com_justificativa_e_anexo(self, request, metodo_transicao):
        anexos = request.data.get("anexos", [])
        justificativa = request.data.get("justificativa", "")
        try:
            metodo_transicao(
                user=request.user, anexos=anexos, justificativa=justificativa
            )
            serializer = self.get_serializer(self.get_object())
            return Response(serializer.data)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    def update_analise_sensorial_status(self, analises_sensoriais, status):
        if analises_sensoriais:
            for analise_sensorial in analises_sensoriais:
                analise_sensorial.status = status
                analise_sensorial.save()

    def quantidade_reclamacoes_ativas(self, reclamacao_produto):
        quantidade_reclamacoes_ativas = (
            reclamacao_produto.homologacao_produto.reclamacoes.filter(
                status__in=[
                    ReclamacaoProdutoWorkflow.AGUARDANDO_AVALIACAO,
                    ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_TERCEIRIZADA,
                    ReclamacaoProdutoWorkflow.RESPONDIDO_TERCEIRIZADA,
                    ReclamacaoProdutoWorkflow.AGUARDANDO_ANALISE_SENSORIAL,
                    ReclamacaoProdutoWorkflow.ANALISE_SENSORIAL_RESPONDIDA,
                ]
            )
        )
        return quantidade_reclamacoes_ativas.count()

    @action(
        detail=True,
        permission_classes=[UsuarioCODAEGestaoProduto],
        methods=["patch"],
        url_path=constants.CODAE_ACEITA,
    )
    def codae_aceita(self, request, uuid=None):
        reclamacao_produto = self.get_object()
        usuario = request.user
        editais_para_suspensao = request.data.get("editais_para_suspensao", "")
        anexos = request.data.get("anexos", [])
        justificativa = request.data.get("justificativa", "")
        vinculos_produto_edital = (
            reclamacao_produto.homologacao_produto.produto.vinculos.all()
        )
        numeros_editais_para_justificativa = ", ".join(
            vinculos_produto_edital.values_list("edital__numero", flat=True)
        )
        justificativa += "<br><p>Editais suspensos:</p>"
        justificativa += f"<p>{numeros_editais_para_justificativa}</p>"
        try:
            vinculos_produto_edital.filter(
                edital__uuid__in=editais_para_suspensao
            ).update(
                suspenso=True,
                suspenso_justificativa=justificativa,
                suspenso_em=datetime.now(),
                suspenso_por=usuario,
            )
            for edital_uuid in editais_para_suspensao:
                produto_edital = ProdutoEdital.objects.get(
                    edital__uuid=edital_uuid,
                    produto=reclamacao_produto.homologacao_produto.produto,
                )
                produto_edital.criar_data_hora_vinculo(suspenso=True)
            analises_sensoriais = (
                reclamacao_produto.homologacao_produto.analises_sensoriais.filter(
                    status=AnaliseSensorial.STATUS_AGUARDANDO_RESPOSTA
                ).all()
            )

            if vinculos_produto_edital.filter(suspenso=False):
                resposta = self.muda_status_com_justificativa_e_anexo(
                    request, reclamacao_produto.codae_recusa
                )

                reclamacoes_ativas = self.quantidade_reclamacoes_ativas(
                    reclamacao_produto
                )

                if reclamacoes_ativas == 0:
                    reclamacao_produto.homologacao_produto.codae_recusou_reclamacao(
                        user=request.user,
                        justificativa=justificativa,
                        request=request,
                        suspensao_parcial=True,
                    )
                analises_sensoriais = (
                    reclamacao_produto.homologacao_produto.analises_sensoriais.filter(
                        status=AnaliseSensorial.STATUS_AGUARDANDO_RESPOSTA
                    ).all()
                )

                self.update_analise_sensorial_status(
                    analises_sensoriais, AnaliseSensorial.STATUS_RESPONDIDA
                )
                return resposta
            else:
                reclamacao_produto.homologacao_produto.codae_autorizou_reclamacao(
                    user=request.user, anexos=anexos, justificativa=justificativa
                )
                self.update_analise_sensorial_status(
                    analises_sensoriais, AnaliseSensorial.STATUS_RESPONDIDA
                )
                return self.muda_status_com_justificativa_e_anexo(
                    request, reclamacao_produto.codae_aceita
                )
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        permission_classes=[UsuarioCODAEGestaoProduto],
        methods=["patch"],
        url_path=constants.CODAE_RECUSA,
    )
    def codae_recusa(self, request, uuid=None):
        from sme_sigpae_api.produto.models import AnaliseSensorial

        reclamacao_produto = self.get_object()
        resposta = self.muda_status_com_justificativa_e_anexo(
            request, reclamacao_produto.codae_recusa
        )
        reclamacoes_ativas = self.quantidade_reclamacoes_ativas(reclamacao_produto)
        if reclamacoes_ativas == 0:
            reclamacao_produto.homologacao_produto.codae_recusou_reclamacao(
                user=request.user,
                justificativa=request.data.get("justificativa")
                or "Recusa automática por não haver mais reclamações",
            )

        analises_sensoriais = (
            reclamacao_produto.homologacao_produto.analises_sensoriais.filter(
                status=AnaliseSensorial.STATUS_AGUARDANDO_RESPOSTA
            ).all()
        )
        self.update_analise_sensorial_status(
            analises_sensoriais, AnaliseSensorial.STATUS_RESPONDIDA
        )
        return resposta

    @action(
        detail=True,
        permission_classes=[UsuarioCODAEGestaoProduto],
        methods=["patch"],
        url_path=constants.CODAE_QUESTIONA_TERCEIRIZADA,
    )
    def codae_questiona_terceirizada(self, request, uuid=None):
        reclamacao_produto = self.get_object()
        homologacao_produto = reclamacao_produto.homologacao_produto
        anexos = request.data.get("anexos", [])
        justificativa = request.data.get("justificativa", "")
        status_homologacao = homologacao_produto.status
        if (
            status_homologacao
            != HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_RECLAMACAO
        ):
            homologacao_produto.codae_pediu_analise_reclamacao(
                user=request.user,
                anexos=anexos,
                justificativa=justificativa,
                reclamacao=reclamacao_produto,
            )
            homologacao_produto.rastro_terceirizada = (
                reclamacao_produto.escola.lote.terceirizada
            )
            homologacao_produto.save()
        return self.muda_status_com_justificativa_e_anexo(
            request, reclamacao_produto.codae_questiona_terceirizada
        )

    @action(
        detail=True,
        permission_classes=[UsuarioCODAEGestaoProduto],
        methods=["patch"],
        url_path=constants.CODAE_QUESTIONA_UE,
    )
    def codae_questiona_ue(self, request, uuid=None):
        reclamacao_produto = self.get_object()
        homologacao_produto = reclamacao_produto.homologacao_produto
        anexos = request.data.get("anexos", [])
        justificativa = request.data.get("justificativa", "")
        status_homologacao = homologacao_produto.status
        if status_homologacao != HomologacaoProdutoWorkflow.CODAE_QUESTIONOU_UE:
            homologacao_produto.codae_questiona_ue(
                user=request.user,
                anexos=anexos,
                justificativa=justificativa,
                reclamacao=reclamacao_produto,
            )
            homologacao_produto.save()

        return self.muda_status_com_justificativa_e_anexo(
            request, reclamacao_produto.codae_questiona_ue
        )

    @action(
        detail=True,
        permission_classes=[UsuarioCODAEGestaoProduto],
        methods=["patch"],
        url_path=constants.CODAE_QUESTIONA_NUTRISUPERVISOR,
    )
    def codae_questiona_nutrisupervisor(self, request, uuid=None):
        reclamacao_produto = self.get_object()
        homologacao_produto = reclamacao_produto.homologacao_produto
        anexos = request.data.get("anexos", [])
        justificativa = request.data.get("justificativa", "")
        status_homologacao = homologacao_produto.status
        if (
            status_homologacao
            != HomologacaoProdutoWorkflow.CODAE_QUESTIONOU_NUTRISUPERVISOR
        ):
            homologacao_produto.codae_questiona_nutrisupervisor(
                user=request.user,
                anexos=anexos,
                justificativa=justificativa,
                reclamacao=reclamacao_produto,
            )
            homologacao_produto.save()

        return self.muda_status_com_justificativa_e_anexo(
            request, reclamacao_produto.codae_questiona_nutrisupervisor
        )

    @action(
        detail=True,
        permission_classes=[UsuarioCODAEGestaoProduto],
        methods=["patch"],
        url_path=constants.CODAE_RESPONDE,
    )
    def codae_responde(self, request, uuid=None):
        reclamacao_produto = self.get_object()
        return self.muda_status_com_justificativa_e_anexo(
            request, reclamacao_produto.codae_responde
        )

    @action(detail=True, methods=["patch"], url_path=constants.TERCEIRIZADA_RESPONDE)
    def terceirizada_responde(self, request, uuid=None):
        reclamacao_produto = self.get_object()
        anexos = request.data.get("anexos", [])
        justificativa = request.data.get("justificativa", "")
        resposta = self.muda_status_com_justificativa_e_anexo(
            request, reclamacao_produto.terceirizada_responde
        )
        questionamentos_ativas = (
            reclamacao_produto.homologacao_produto.reclamacoes.filter(
                status__in=[
                    ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_TERCEIRIZADA,
                ]
            )
        )
        if questionamentos_ativas.count() == 0:
            reclamacao_produto.homologacao_produto.terceirizada_responde_reclamacao(
                user=request.user,
                anexos=anexos,
                justificativa=justificativa,
                request=request,
            )
        return resposta

    @action(detail=True, methods=["patch"], url_path=constants.ESCOLA_RESPONDE)
    def escola_responde(self, request, uuid=None):
        reclamacao_produto = self.get_object()
        anexos = request.data.get("anexos", [])
        justificativa = request.data.get("justificativa", "")
        resposta = self.muda_status_com_justificativa_e_anexo(
            request, reclamacao_produto.ue_responde
        )
        questionamentos_ativos = (
            reclamacao_produto.homologacao_produto.reclamacoes.filter(
                status__in=[
                    ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_UE,
                ]
            )
        )
        if questionamentos_ativos.count() == 0:
            reclamacao_produto.homologacao_produto.ue_respondeu_questionamento(
                user=request.user,
                anexos=anexos,
                justificativa=justificativa,
                request=request,
            )
        return resposta

    @action(detail=True, methods=["patch"], url_path=constants.NUTRISUPERVISOR_RESPONDE)
    def nutrisupervisor_responde(self, request, uuid=None):
        reclamacao_produto = self.get_object()
        anexos = request.data.get("anexos", [])
        justificativa = request.data.get("justificativa", "")
        resposta = self.muda_status_com_justificativa_e_anexo(
            request, reclamacao_produto.nutrisupervisor_responde
        )
        questionamentos_ativos = (
            reclamacao_produto.homologacao_produto.reclamacoes.filter(
                status__in=[
                    ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_NUTRISUPERVISOR,
                ]
            )
        )
        if questionamentos_ativos.count() == 0:
            reclamacao_produto.homologacao_produto.nutrisupervisor_respondeu_questionamento(
                user=request.user,
                anexos=anexos,
                justificativa=justificativa,
                request=request,
            )
        return resposta

    @action(
        detail=True,  # noqa C901
        permission_classes=(UsuarioCODAEGestaoProduto,),
        methods=["patch"],
        url_path=constants.CODAE_PEDE_ANALISE_SENSORIAL,
    )
    def codae_pede_analise_sensorial(self, request, uuid=None):
        from sme_sigpae_api.produto.models import AnaliseSensorial
        from sme_sigpae_api.terceirizada.models import Terceirizada

        reclamacao_produto = self.get_object()
        homologacao_produto = reclamacao_produto.homologacao_produto
        uri = reverse("Produtos-relatorio", args=[homologacao_produto.produto.uuid])
        try:
            anexos = request.data.get("anexos", [])
            justificativa = request.data.get("justificativa", "")
            terceirizada_uuid = request.data.get("uuidTerceirizada", "")
            if not terceirizada_uuid:
                return Response({"detail": "O uuid da terceirizada é obrigatório"})

            terceirizada = Terceirizada.objects.filter(uuid=terceirizada_uuid).first()
            if not terceirizada:
                return Response(
                    {
                        "detail": f"Terceirizada para uuid {terceirizada_uuid} não encontrado."
                    }
                )

            AnaliseSensorial.objects.create(
                homologacao_produto=homologacao_produto, terceirizada=terceirizada
            )

            homologacao_produto.gera_protocolo_analise_sensorial()
            homologacao_produto.codae_pede_analise_sensorial(
                user=request.user,
                justificativa=justificativa,
                link_pdf=url_configs("API", {"uri": uri}),
            )

            reclamacao_produto.codae_pede_analise_sensorial(
                user=request.user, anexos=anexos, justificativa=justificativa
            )

            serializer = self.get_serializer(self.get_object())
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvalidTransitionError as e:
            return Response(
                dict(detail=f"Erro de transição de estado: {e}"),
                status=status.HTTP_400_BAD_REQUEST,
            )


class SolicitacaoCadastroProdutoDietaFilter(filters.FilterSet):
    nome_produto = filters.CharFilter(
        field_name="nome_produto", lookup_expr="icontains"
    )
    data_inicial = filters.DateFilter(field_name="criado_em", lookup_expr="date__gte")
    data_final = filters.DateFilter(field_name="criado_em", lookup_expr="date__lte")
    status = filters.CharFilter(field_name="status")

    class Meta:
        model = SolicitacaoCadastroProdutoDieta
        fields = ["nome_produto", "data_inicial", "data_final", "status"]


class SolicitacaoCadastroProdutoDietaViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = SolicitacaoCadastroProdutoDieta.objects.all().order_by("-criado_em")
    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = SolicitacaoCadastroProdutoDietaFilter

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SolicitacaoCadastroProdutoDietaSerializerCreate
        return SolicitacaoCadastroProdutoDietaSerializer

    @action(detail=False, methods=["GET"], url_path="nomes-produtos")
    def nomes_produtos(self, request):
        return Response(
            [
                s.nome_produto
                for s in SolicitacaoCadastroProdutoDieta.objects.only("nome_produto")
            ]
        )

    @transaction.atomic
    @action(detail=True, methods=["patch"], url_path="confirma-previsao")
    def confirma_previsao(self, request, uuid=None):
        solicitacao = self.get_object()
        serializer = self.get_serializer()
        try:
            serializer.update(solicitacao, request.data)
            solicitacao.terceirizada_atende_solicitacao(user=request.user)
            return Response(
                {"detail": "Confirmação de previsão de cadastro realizada com sucesso"}
            )
        except InvalidTransitionError as e:
            return Response(
                {"detail": f"Erro na transição de estado {e}"},
                status=HTTP_400_BAD_REQUEST,
            )
        except serializers.ValidationError as e:
            return Response(
                {"detail": f"Dados inválidos {e}"}, status=HTTP_400_BAD_REQUEST
            )


class ItensCadastroViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = ItemCadastro.objects.all().order_by("-criado_em")
    pagination_class = ItemCadastroPagination
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ItemCadastroFilter

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ItensCadastroCreateSerializer
        return ItensCadastroSerializer

    @action(detail=False, methods=["GET"], url_path="tipos")
    def tipos(self, _):
        return Response(
            [
                {"tipo": choice[0], "tipo_display": choice[1]}
                for choice in ItemCadastro.CHOICES
            ]
        )

    @action(detail=False, methods=["GET"], url_path="lista-nomes")
    def lista_de_nomes(self, _):
        return Response(
            {"results": [item.content_object.nome for item in self.queryset.all()]}
        )

    def destroy(self, request, *args, **kwargs):
        instance: ItemCadastro = self.get_object()

        if instance.deleta_modelo():
            return Response(status=status.HTTP_204_NO_CONTENT)

        msg = "Não será possível realizar a exclusão. Este item contém relacionamentos com Cadastro de Produtos."
        return Response(data={"detail": msg}, status=status.HTTP_403_FORBIDDEN)

    class Meta:
        model = ItemCadastro


class UnidadesDeMedidaViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    serializer_class = UnidadeMedidaSerialzer
    queryset = UnidadeMedida.objects.all()
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if "page" in request.query_params:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data})


class EmbalagemProdutoViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    serializer_class = EmbalagemProdutoSerialzer
    queryset = EmbalagemProduto.objects.all()
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if "page" in request.query_params:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data})
