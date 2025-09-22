from datetime import date, datetime

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from sme_sigpae_api.produto.utils.genericos import (
    changes_between,
    compara_lista_imagens,
    compara_lista_informacoes_nutricionais,
    compara_lista_protocolos,
    converte_para_datetime,
    cria_filtro_aditivos,
    cria_filtro_produto_por_parametros_form,
    get_filtros_data,
    get_filtros_data_range,
    mudancas_para_justificativa_html,
)

pytestmark = pytest.mark.django_db


def test_cria_filtro_produto_por_parametros_form_vazio():
    campos_filtrados = cria_filtro_produto_por_parametros_form({})
    assert campos_filtrados == {}


def test_cria_filtro_produto_por_parametros_form_parametros():
    parametros = {
        "nome_fabricante": "fabricante__nome__icontains",
        "nome_marca": "marca__nome__icontains",
        "nome_produto": "nome__icontains",
        "nome_terceirizada": "homologacao__rastro_terceirizada__nome_fantasia__icontains",
        "data_inicial": "homologacao__criado_em__gte",
        "status": "homologacao__status__in",
        "tem_aditivos_alergenicos": "tem_aditivos_alergenicos",
        "eh_para_alunos_com_dieta": "eh_para_alunos_com_dieta",
    }
    VALOR = "qualquer coisa"
    for parametro_form, parametro_filtro in parametros.items():
        form_data = {parametro_form: VALOR}
        campos_filtrados = cria_filtro_produto_por_parametros_form(form_data)
        assert campos_filtrados[parametro_filtro] == VALOR


def test_cria_filtro_produto_por_parametros_form_data_final():
    data = date(2020, 4, 30)
    campos_filtrados = cria_filtro_produto_por_parametros_form({"data_final": data})
    assert campos_filtrados["homologacao__criado_em__lt"] == date(2020, 5, 1)


def test_get_filtros_data_em_analise_sensorial_sem_data_final():
    data_analise_incial = date(2020, 8, 13)
    filtros_data = get_filtros_data(data_analise_incial, None)
    assert filtros_data["criado_em__gte"] == date(2020, 8, 13)


def test_converte_para_datetime():
    data_str = "13/08/2020"
    data_datetime = converte_para_datetime(data_str)
    data_datetime_aux = datetime.strptime(data_str, "%d/%m/%Y")
    assert data_datetime == data_datetime_aux


def test_filtros_data_range():
    data_analise_inicial = date(2020, 8, 13)
    data_analise_final = date(2020, 8, 13)
    data_range = get_filtros_data_range(data_analise_inicial, data_analise_final)
    assert data_range["criado_em__date"] == data_analise_inicial


def test_cria_filtro_aditivos():
    filtro = cria_filtro_aditivos("aditivo01, aditivo02")
    assert len(filtro) == 2


def test_compara_lista_informacoes_nutricionais(
    info_nutricional1,
    info_nutricional2,
    info_nutricional3,
    info_nutricional_produto1,
    info_nutricional_produto2,
    info_nutricional_produto3,
):
    anterior = [info_nutricional_produto1, info_nutricional_produto2]
    proxima = [
        {
            "informacao_nutricional": info_nutricional1,
            "quantidade_porcao": "1",
            "valor_diario": "9",
        },
        {
            "informacao_nutricional": info_nutricional2,
            "quantidade_porcao": "8",
            "valor_diario": "4",
        },
        {
            "informacao_nutricional": info_nutricional3,
            "quantidade_porcao": "5",
            "valor_diario": "6",
        },
    ]

    resultado = compara_lista_informacoes_nutricionais(anterior, proxima)

    assert len(resultado["adicoes"]) == 1
    adicao = resultado["adicoes"][0]
    assert adicao["informacao_nutricional"] == info_nutricional3
    assert adicao["quantidade_porcao"] == "5"
    assert adicao["valor_diario"] == "6"

    assert len(resultado["modificacoes"]) == 2

    modif1 = resultado["modificacoes"][0]
    assert modif1["informacao_nutricional"] == info_nutricional1
    assert modif1["valor"] == "Valor diário"
    assert modif1["de"] == "2"
    assert modif1["para"] == "9"

    modif2 = resultado["modificacoes"][1]
    assert modif2["informacao_nutricional"] == info_nutricional2
    assert modif2["valor"] == "Quantidade porção"
    assert modif2["de"] == "3"
    assert modif2["para"] == "8"


def test_compara_lista_protocolos(protocolo1, protocolo2, protocolo3):
    anterior = [protocolo1, protocolo2]
    proxima = [protocolo2, protocolo3]

    resultado = compara_lista_protocolos(anterior, proxima)

    assert len(resultado["adicoes"]) == 1
    assert resultado["adicoes"][0] == protocolo3

    assert len(resultado["exclusoes"]) == 1
    assert resultado["exclusoes"][0] == protocolo1


def test_compara_lista_imagens(produto, imagem_produto1, imagem_produto2):
    anterior = produto.imagens.all()
    proxima = [
        {"arquivo": imagem_produto1.arquivo, "nome": imagem_produto1.nome},
        {
            "arquivo": SimpleUploadedFile(
                "doc-novo.pdf", bytes("CONTEUDO TESTE TESTE TESTE", encoding="utf-8")
            ),
            "nome": "doc-novo",
        },
    ]

    resultado = compara_lista_imagens(anterior, proxima)

    assert len(resultado["adicoes"]) == 1
    assert resultado["adicoes"][0]["nome"] == "doc-novo"


def test_changes_between(
    produto,
    info_nutricional1,
    info_nutricional2,
    info_nutricional3,
    info_nutricional_produto1,
    info_nutricional_produto2,
    imagem_produto1,
    imagem_produto2,
    marca2,
    usuario,
):
    validated_data = {
        "nome": produto.nome,
        "eh_para_alunos_com_dieta": True,
        "componentes": "Componente3, Componente4",
        "tem_aditivos_alergenicos": False,
        "tipo": "Tipo1",
        "embalagem": "Embalagem X",
        "prazo_validade": "Alguns dias",
        "info_armazenamento": "Bote na geladeira",
        "outras_informacoes": "Produto do bom",
        "numero_registro": "123123123",
        "porcao": "5 cuias",
        "unidade_caseira": "Unidade3",
        "marca": marca2,
        "informacoes_nutricionais": [
            {
                "informacao_nutricional": info_nutricional1,
                "quantidade_porcao": "1",
                "valor_diario": "9",
            },
            {
                "informacao_nutricional": info_nutricional2,
                "quantidade_porcao": "8",
                "valor_diario": "4",
            },
            {
                "informacao_nutricional": info_nutricional3,
                "quantidade_porcao": "5",
                "valor_diario": "6",
            },
        ],
        "imagens": [
            {"arquivo": imagem_produto1.arquivo, "nome": imagem_produto1.nome},
            {
                "arquivo": SimpleUploadedFile(
                    "doc-novo.pdf",
                    bytes("CONTEUDO TESTE TESTE TESTE", encoding="utf-8"),
                ),
                "nome": "doc-novo",
            },
        ],
    }
    changes = changes_between(produto, validated_data, usuario)

    assert changes["componentes"] == {
        "de": "Componente1, Componente2",
        "para": "Componente3, Componente4",
    }
    assert changes["info_armazenamento"] == {
        "de": "Guardem bem",
        "para": "Bote na geladeira",
    }
    assert changes["marca"] == {"de": produto.marca, "para": validated_data["marca"]}

    assert len(changes["informacoes_nutricionais"]["adicoes"]) == 1
    adicao = changes["informacoes_nutricionais"]["adicoes"][0]
    assert adicao["informacao_nutricional"] == info_nutricional3
    assert adicao["quantidade_porcao"] == "5"
    assert adicao["valor_diario"] == "6"

    assert len(changes["informacoes_nutricionais"]["modificacoes"]) == 2

    modif1 = changes["informacoes_nutricionais"]["modificacoes"][0]
    assert modif1["informacao_nutricional"] == info_nutricional1
    assert modif1["valor"] == "Valor diário"
    assert modif1["de"] == "2"
    assert modif1["para"] == "9"

    modif2 = changes["informacoes_nutricionais"]["modificacoes"][1]
    assert modif2["informacao_nutricional"] == info_nutricional2
    assert modif2["valor"] == "Quantidade porção"
    assert modif2["de"] == "3"
    assert modif2["para"] == "8"

    assert len(changes["imagens"]["adicoes"]) == 1
    assert changes["imagens"]["adicoes"][0]["nome"] == "doc-novo"


def test_mudancas_para_justificativa(
    info_nutricional1,
    info_nutricional2,
    info_nutricional3,
    protocolo2,
    protocolo3,
    imagem_produto1,
    marca1,
    marca2,
    produto,
):
    mudancas = {
        "informacoes_nutricionais": {
            "adicoes": [
                {
                    "informacao_nutricional": info_nutricional1,
                    "quantidade_porcao": "5",
                    "valor_diario": "6",
                }
            ],
            "modificacoes": [
                {
                    "informacao_nutricional": info_nutricional2,
                    "valor": "valor_diario",
                    "de": "2",
                    "para": "9",
                },
                {
                    "informacao_nutricional": info_nutricional3,
                    "valor": "quantidade_porcao",
                    "de": "3",
                    "para": "8",
                },
            ],
        },
        "eh_para_alunos_com_dieta": {"de": True, "para": False},
        "marca": {"de": marca1, "para": marca2},
        "componentes": {
            "de": "Componente1, Componente2",
            "para": "Componente3, Componente4",
        },
        "info_armazenamento": {"de": "Guardem bem", "para": "Bote na geladeira"},
        "protocolos": {"adicoes": [protocolo3], "exclusoes": [protocolo2]},
        "imagens": {"adicoes": [{"nome": "Imagem3"}], "exclusoes": [imagem_produto1]},
    }

    justificativa = mudancas_para_justificativa_html(
        mudancas, produto._meta.get_fields()
    )

    assert len(justificativa) == 1313
