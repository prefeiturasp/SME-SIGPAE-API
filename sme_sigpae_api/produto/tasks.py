import io
import logging

from celery import shared_task

from sme_sigpae_api.dados_comuns.utils import (
    atualiza_central_download,
    atualiza_central_download_com_erro,
    build_xlsx_generico,
    gera_objeto_na_central_download,
)
from sme_sigpae_api.produto.models import HomologacaoProduto, Produto
from sme_sigpae_api.relatorios.relatorios import (
    produtos_suspensos_por_edital,
    relatorio_marcas_por_produto_homologacao,
    relatorio_produtos_agrupado_terceirizada,
)

logger = logging.getLogger(__name__)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gera_xls_relatorio_produtos_homologados_async(
    user, nome_arquivo, data, perfil_nome, tipo_usuario, object_id
):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        from sme_sigpae_api.produto.api.viewsets import (
            HomologacaoProdutoPainelGerencialViewSet,
        )

        agrupado_nome_marca = data.get("agrupado_por_nome_e_marca")
        output = io.BytesIO()

        hom_produto_painel_viewset = HomologacaoProdutoPainelGerencialViewSet()
        queryset = (
            hom_produto_painel_viewset.get_queryset_solicitacoes_homologacao_por_status(
                data, perfil_nome, tipo_usuario, object_id, "codae_homologado"
            )
        )
        uuids = [hom_prod.uuid for hom_prod in queryset]
        qs_produtos = Produto.objects.filter(homologacao__uuid__in=uuids)
        total_marcas = (
            qs_produtos.values_list("marca__nome", flat=True).distinct().count()
        )
        total_produtos = len(queryset)

        if agrupado_nome_marca:
            titulos_colunas = ["Produto", "Marca", "Edital"]
            produtos_agrupados = (
                hom_produto_painel_viewset.produtos_agrupados_nome_marca(
                    data.get("nome_edital"), qs_produtos, 0, len(queryset)
                )
            )
        else:
            titulos_colunas = [
                "Terceirizada",
                "Produto",
                "Marca",
                "Edital",
                "Tipo",
                "Cadastro",
                "Homologação",
            ]
            produtos_agrupados = hom_produto_painel_viewset.produtos_sem_agrupamento(
                data.get("nome_edital"), queryset, 0, len(queryset)
            )

        subtitulo = f'Total de Produtos: {total_produtos} | Total de Marcas: {total_marcas} | {data.get("nome_edital")}'
        build_xlsx_generico(
            output,
            queryset_serializada=produtos_agrupados,
            titulo=f'Relatório de Produtos Homologados{" por Nome e Marca" if agrupado_nome_marca else ""}',
            subtitulo=subtitulo,
            titulo_sheet=f'{"Visão Agrupada" if agrupado_nome_marca else "Produtos Homologados"}',
            titulos_colunas=titulos_colunas,
        )
        atualiza_central_download(obj_central_download, nome_arquivo, output.read())
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gera_pdf_relatorio_produtos_homologados_async(
    user, nome_arquivo, data, perfil_nome, tipo_usuario, object_id
):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        from sme_sigpae_api.produto.api.viewsets import (
            HomologacaoProdutoPainelGerencialViewSet,
        )

        agrupado_nome_marca = data.get("agrupado_por_nome_e_marca") == "true"

        hom_produto_painel_viewset = HomologacaoProdutoPainelGerencialViewSet()
        queryset = (
            hom_produto_painel_viewset.get_queryset_solicitacoes_homologacao_por_status(
                data, perfil_nome, tipo_usuario, object_id, "codae_homologado"
            )
        )
        uuids = [hom_prod.uuid for hom_prod in queryset]
        qs_homs = HomologacaoProduto.objects.filter(uuid__in=uuids).order_by(
            "rastro_terceirizada__nome_fantasia", "produto__nome"
        )
        qs_produtos = Produto.objects.filter(homologacao__uuid__in=uuids)
        total_marcas = (
            qs_produtos.values_list("marca__nome", flat=True).distinct().count()
        )
        total_produtos = len(queryset)

        filtros_dict = [
            (
                "Agrupado por nome e marca",
                "Sim" if data.get("agrupado_por_nome_e_marca") == "true" else "Não",
            ),
            ("Edital", data.get("nome_edital")),
            ("Marca do Produto", data.get("nome_marca")),
            ("Fabricante do Produto", data.get("nome_fabricante")),
            ("Nome do Produto", data.get("nome_produto")),
            ("Nome da Terceirizada", data.get("nome_terceirizada")),
            ("Homologados até", data.get("data_homologacao")),
            ("Tipo", data.get("tipo")),
        ]

        filtros = dict(f for f in filtros_dict if f[1] is not None)

        mapping = {
            "escola": "Escola",
            "terceirizada": "Terceirizada",
        }

        tipo_usuario = mapping.get(tipo_usuario, "Outros")

        dados = dict(data)
        dados["quantidade_marcas"] = total_marcas
        dados["quantidade_homologados"] = total_produtos
        dados["tipo_usuario"] = tipo_usuario

        if agrupado_nome_marca:
            produtos_agrupados = (
                hom_produto_painel_viewset.produtos_agrupados_nome_marca(
                    data.get("nome_edital"), qs_produtos, 0, len(queryset)
                )
            )

            arquivo = relatorio_marcas_por_produto_homologacao(
                produtos=produtos_agrupados, dados=dados, filtros=filtros
            )
        else:
            produtos_agrupados = hom_produto_painel_viewset.produtos_sem_agrupamento(
                data.get("nome_edital"), qs_homs, 0, len(queryset)
            )

            arquivo = relatorio_produtos_agrupado_terceirizada(
                tipo_usuario, produtos_agrupados, dados, filtros
            )

        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gera_xls_relatorio_produtos_suspensos_async(
    produtos_uuids, nome_arquivo, nome_edital, user, data_final, filtros
):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    if filtros:
        filtros = ", ".join(filtros)
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        produtos = Produto.objects.filter(uuid__in=produtos_uuids).order_by("nome")
        lista_produtos = []
        for produto in produtos:
            produto_edital = produto.vinculos.get(edital__numero=nome_edital)
            data_suspensao = (
                produto_edital.datas_horas_vinculo.last().criado_em.strftime("%d/%m/%Y")
            )
            data_cadastro = produto.homologacao.logs.first().criado_em.strftime(
                "%d/%m/%Y"
            )
            lista_produtos.append(
                {
                    "nome": produto.nome,
                    "marca": produto.marca.nome,
                    "tipo": (
                        "Dieta especial"
                        if produto.eh_para_alunos_com_dieta
                        else "Comum"
                    ),
                    "edital": nome_edital,
                    "cadastro": data_cadastro,
                    "suspensao": data_suspensao,
                    "justificativa": produto_edital.suspenso_justificativa,
                }
            )

        arquivo = produtos_suspensos_por_edital(
            lista_produtos, data_final, nome_edital, filtros
        )
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")
