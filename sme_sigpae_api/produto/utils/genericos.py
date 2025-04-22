import operator
from datetime import datetime, timedelta
from functools import reduce

from django.db.models import Q
from django.template.loader import render_to_string
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination

from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.produto.models import ImagemDoProduto


def agrupa_por_terceirizada(queryset):  # noqa C901
    agrupado = []
    produtos_atual = []
    total_produtos = 0
    ultima_terceirizada = None

    sorted_queryset = sorted(
        queryset, key=lambda i: i.criado_por.vinculo_atual.instituicao.nome.lower()
    )

    for produto in sorted_queryset:
        if ultima_terceirizada is None:
            ultima_terceirizada = produto.criado_por.vinculo_atual.instituicao
            produtos_atual = [produto]
        elif ultima_terceirizada != produto.criado_por.vinculo_atual.instituicao:
            agrupado.append(
                {"terceirizada": ultima_terceirizada, "produtos": produtos_atual}
            )
            total_produtos += len(produtos_atual)
            ultima_terceirizada = produto.criado_por.vinculo_atual.instituicao
            produtos_atual = [produto]
        else:
            produtos_atual.append(produto)

    if len(produtos_atual) > 0:
        agrupado.append(
            {"terceirizada": ultima_terceirizada, "produtos": produtos_atual}
        )
        total_produtos += len(produtos_atual)

    return {"results": agrupado, "total_produtos": total_produtos}


def cria_filtro_produto_por_parametros_form(cleaned_data):  # noqa C901
    campos_a_pesquisar = {}
    for chave, valor in cleaned_data.items():
        if valor != "" and valor is not None:
            if chave == "uuid":
                campos_a_pesquisar["homologacao__uuid"] = valor
            if chave == "nome_fabricante":
                campos_a_pesquisar["fabricante__nome__icontains"] = valor
            elif chave == "nome_marca":
                campos_a_pesquisar["marca__nome__icontains"] = valor
            elif chave == "nome_produto":
                campos_a_pesquisar["nome__icontains"] = valor
            elif chave == "nome_edital":
                campos_a_pesquisar["vinculos__edital__numero__icontains"] = valor
            elif chave == "tipo":
                campos_a_pesquisar["vinculos__tipo_produto__icontains"] = valor
            elif chave == "nome_terceirizada":
                campos_a_pesquisar[
                    "homologacao__rastro_terceirizada__nome_fantasia__icontains"
                ] = valor
            elif chave == "data_inicial" and valor is not None:
                campos_a_pesquisar["homologacao__criado_em__gte"] = valor
            elif chave == "data_final" and valor is not None:
                campos_a_pesquisar["homologacao__criado_em__lt"] = valor + timedelta(
                    days=1
                )
            elif chave == "status" and len(valor) > 0:
                campos_a_pesquisar["homologacao__status__in"] = valor
            elif chave == "tem_aditivos_alergenicos":
                campos_a_pesquisar["tem_aditivos_alergenicos"] = valor
            elif chave == "eh_para_alunos_com_dieta":
                campos_a_pesquisar["eh_para_alunos_com_dieta"] = valor

    return campos_a_pesquisar


def cria_filtro_produto_por_parametros_form_homologado(cleaned_data):  # noqa C901
    campos_a_pesquisar = {}
    for chave, valor in cleaned_data.items():
        if valor != "" and valor is not None:
            if chave == "nome_fabricante":
                campos_a_pesquisar["fabricante__nome__icontains"] = valor
            elif chave == "nome_marca":
                campos_a_pesquisar["marca__nome__icontains"] = valor
            elif chave == "nome_produto":
                campos_a_pesquisar["nome__icontains"] = valor
            elif chave == "nome_edital":
                campos_a_pesquisar["vinculos__edital__numero__icontains"] = valor
            elif chave == "tipo":
                campos_a_pesquisar["vinculos__tipo_produto__icontains"] = valor
            elif chave == "nome_terceirizada":
                campos_a_pesquisar[
                    "homologacao__rastro_terceirizada__nome_fantasia__icontains"
                ] = valor
    return campos_a_pesquisar


def cria_filtro_homologacao_produto_por_parametros(cleaned_data):
    campos_a_pesquisar = {}
    filtro = {
        "nome_fabricante": "produto__fabricante__nome__icontains",
        "nome_marca": "produto__marca__nome__icontains",
        "nome_produto": "produto__nome__icontains",
        "nome_edital": "produto__vinculos__edital__numero__icontains",
        "tipo": "produto__vinculos__tipo_produto__icontains",
        "nome_terceirizada": "rastro_terceirizada__nome_fantasia__icontains",
    }
    for chave, valor in cleaned_data.items():
        if not valor or chave not in filtro.keys():
            continue
        campos_a_pesquisar[filtro[chave]] = valor
    return campos_a_pesquisar


def cria_filtro_aditivos(aditivos):
    lista_aditivos = aditivos.replace(", ", ",").split(",")
    return reduce(
        operator.and_, (Q(aditivos__icontains=aditivo) for aditivo in lista_aditivos)
    )


def converte_para_datetime(data):
    if data:
        return datetime.strptime(data, "%d/%m/%Y")
    return None


def get_filtros_data_range(data_analise_inicial, data_analise_final):
    filtros_data = {}
    if data_analise_inicial == data_analise_final:
        filtros_data["criado_em__date"] = data_analise_inicial
    else:
        filtros_data["criado_em__range"] = (
            data_analise_inicial,
            data_analise_final + timedelta(days=1),
        )
    return filtros_data


def get_filtros_data(data_inicial, data_final):
    if data_inicial and data_final:
        filtros_data = get_filtros_data_range(data_inicial, data_final)

    else:
        filtros_data = {}
        if data_inicial:
            filtros_data["criado_em__gte"] = data_inicial

        if data_final:
            filtros_data["criado_em__lte"] = data_final + timedelta(days=1)
    return filtros_data


class DashboardPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = "page_size"
    max_page_size = 6


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 100


class ItemCadastroPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class CadastroProdutosEditalPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


def compara_lista_imagens(anterior, proxima):  # noqa C901
    adicoes = []
    lista_de_paths_proxima = []

    [lista_de_paths_proxima.append(imagem_p.get("arquivo")) for imagem_p in proxima]

    lista_imagens_anterior = anterior

    for imagem_a in lista_imagens_anterior:
        url_imagem_a = imagem_a.arquivo.url
        imagem_a_continua_na_lista = any(
            url_imagem_a in path_image_p for path_image_p in lista_de_paths_proxima
        )
        if not imagem_a_continua_na_lista:
            uuid_imagem_a = imagem_a.uuid
            ImagemDoProduto.objects.get(uuid=uuid_imagem_a).delete()
            lista_imagens_anterior = lista_imagens_anterior.exclude(id=imagem_a.id)

    for imagem_p in proxima:
        for imagem_a in anterior:
            if imagem_a.nome == imagem_p["nome"]:
                break
        else:
            adicoes.append(imagem_p)
    retorno = {}

    if len(adicoes) > 0:
        retorno["adicoes"] = adicoes
    return retorno


def compara_lista_protocolos(anterior, proxima):  # noqa C901
    adicoes = []
    exclusoes = []

    for protocolo in anterior:
        if protocolo not in proxima:
            exclusoes.append(protocolo)

    for protocolo in proxima:
        if protocolo not in anterior:
            adicoes.append(protocolo)

    retorno = {}

    if len(adicoes) > 0:
        retorno["adicoes"] = adicoes
    if len(exclusoes) > 0:
        retorno["exclusoes"] = exclusoes

    return retorno


def compara_lista_informacoes_nutricionais(anterior, proxima):  # noqa C901
    adicoes = []
    modificacoes = []

    for info_nutricional in proxima:
        for info_anterior in anterior:
            if (
                info_anterior.informacao_nutricional.nome
                == info_nutricional["informacao_nutricional"].nome
            ):
                if (
                    "quantidade_porcao" in info_nutricional
                    and info_anterior.quantidade_porcao
                    != info_nutricional["quantidade_porcao"]
                ):
                    modificacoes.append(
                        {
                            "informacao_nutricional": info_anterior.informacao_nutricional,
                            "valor": "Quantidade porção",
                            "de": info_anterior.quantidade_porcao,
                            "para": info_nutricional["quantidade_porcao"],
                        }
                    )
                if (
                    "valor_diario" in info_nutricional
                    and info_anterior.valor_diario != info_nutricional["valor_diario"]
                ):
                    modificacoes.append(
                        {
                            "informacao_nutricional": info_anterior.informacao_nutricional,
                            "valor": "Valor diário",
                            "de": info_anterior.valor_diario,
                            "para": info_nutricional["valor_diario"],
                        }
                    )
                break
        else:
            adicoes.append(info_nutricional)

    retorno = {}

    if len(adicoes) > 0:
        retorno["adicoes"] = adicoes
    if len(modificacoes) > 0:
        retorno["modificacoes"] = modificacoes

    return retorno


def checa_campo(field_name, produto, validated_data):
    if (
        not produto.eh_para_alunos_com_dieta
        == validated_data["eh_para_alunos_com_dieta"]
    ):
        raise serializers.ValidationError(
            'Não é possível alterar o campo: "O produto se destina ao atendimento de alunos com dieta especial?"'
        )


def changes_between(produto, validated_data, usuario):  # noqa C901
    mudancas = {}

    for field in produto._meta.get_fields():
        if field.name == "informacoes_nutricionais":
            mudancas_info_nutricionais = compara_lista_informacoes_nutricionais(
                produto.informacoes_nutricionais.all(),
                validated_data["informacoes_nutricionais"],
            )
            if mudancas_info_nutricionais.keys():
                mudancas["informacoes_nutricionais"] = mudancas_info_nutricionais
        elif (
            field.name == "eh_para_alunos_com_dieta"
            and usuario.tipo_usuario == constants.TIPO_USUARIO_TERCEIRIZADA
            and produto.homologacao.status
            not in [
                "CODAE_QUESTIONADO",
                "CODAE_HOMOLOGADO",
                "ESCOLA_OU_NUTRICIONISTA_RECLAMOU",
                "TERCEIRIZADA_RESPONDEU_RECLAMACAO",
            ]
        ):
            kwargs = {
                "field_name": field.name,
                "produto": produto,
                "validated_data": validated_data,
            }
            checa_campo(**kwargs)
        elif field.is_relation:
            if field.many_to_one and field.name in validated_data:
                valor_original = getattr(produto, field.name)
                valor_novo = validated_data[field.name]
                if valor_original != valor_novo:
                    mudancas[field.name] = {"de": valor_original, "para": valor_novo}
        else:
            if field.name in validated_data:
                valor_original = getattr(produto, field.name)
                valor_novo = validated_data[field.name]
                if valor_original != valor_novo:
                    mudancas[field.name] = {"de": valor_original, "para": valor_novo}

    if "imagens" in validated_data:
        mudancas_imagens = compara_lista_imagens(
            produto.imagens.all(), validated_data["imagens"]
        )
        if mudancas_imagens.keys():
            mudancas["imagens"] = mudancas_imagens

    return mudancas


def mudancas_para_justificativa_html(mudancas, fields_produto):
    for field in fields_produto:
        if field.name in mudancas:
            if hasattr(field, "verbose_name"):
                mudancas[field.name]["nome_campo"] = field.verbose_name.capitalize()
            else:
                mudancas[field.name]["nome_campo"] = field.name.capitalize()

    return render_to_string(
        "produto/justificativa_mudancas_produto.html", {"mudancas": mudancas.items()}
    )


def cria_itens_cadastro():
    """Cria Itens Cadastro para Fabricantes e Marcas caso não existam."""
    from sme_sigpae_api.produto.models import Fabricante, ItemCadastro, Marca

    marcas = Marca.objects.all()
    for marca in marcas:
        cria_item_cadastro(object=marca, tipo=ItemCadastro.MARCA)

    fabricantes = Fabricante.objects.all()
    for fabricante in fabricantes:
        cria_item_cadastro(object=fabricante, tipo=ItemCadastro.FABRICANTE)


def cria_item_cadastro(object, tipo):
    from django.contrib.contenttypes.models import ContentType

    from sme_sigpae_api.produto.models import ItemCadastro

    try:
        content_type = ContentType.objects.get_for_model(object.__class__)
        ItemCadastro.objects.get(content_type__pk=content_type.pk, object_id=object.id)
    except ItemCadastro.DoesNotExist:
        item = ItemCadastro(content_object=object, tipo=tipo)
        item.save()


def data_para_ordenacao(hom):
    data = (
        hom.data_edital_suspenso_mais_recente
        if hom.data_edital_suspenso_mais_recente
        else hom.ultimo_log.criado_em
    )
    return data
