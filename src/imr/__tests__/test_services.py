import io
import os
import tempfile
from datetime import date
from types import SimpleNamespace

import openpyxl
import pytest
from django.template.loader import render_to_string
from pypdf import PdfReader
from rest_framework import status

from src.imr.api.services import (
    RelatorioNotificacaoService,
    buscar_respostas_diretor,
    listar_ocorrencias_diretor,
)
from src.imr.models import (
    RespostaCampoTextoLongo,
    RespostaDatas,
    RespostaSimNao,
    RespostaTipoAlimentacao,
)
from src.relatorios.relatorios import exportar_relatorio_notificacao

pytestmark = pytest.mark.django_db


def test_modelo_excel_tipos_penalidade(client_admin_django):
    response = client_admin_django.get(
        "/admin/imr/importacaoplanilhatipopenalidade/exportar_planilha_importacao_tipos_penalidade",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        follow=True,
    )
    assert response.status_code == status.HTTP_200_OK

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
        temp_file.write(response.content)
        temp_file_path = temp_file.name

    assert os.path.exists(temp_file_path), "Falha ao criar o arquivo"

    workbook = openpyxl.load_workbook(temp_file_path)
    sheet = workbook.active

    first_row = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))
    assert first_row == (
        "Edital",
        "Número da Cláusula/Item",
        "Gravidade",
        "Obrigações (separadas por ;)",
        "Descrição da Cláusula/Item",
        "Status",
    )

    os.remove(temp_file_path)


def test_modelo_excel_tipos_ocorrencia(client_admin_django):
    response = client_admin_django.get(
        "/admin/imr/importacaoplanilhatipoocorrencia/exportar_planilha_importacao_tipos_ocorrencia",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        follow=True,
    )
    assert response.status_code == status.HTTP_200_OK

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
        temp_file.write(response.content)
        temp_file_path = temp_file.name

    assert os.path.exists(temp_file_path), "Falha ao criar o arquivo"

    workbook = openpyxl.load_workbook(temp_file_path)
    sheet = workbook.active

    first_row = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))
    assert first_row == (
        "Posição",
        "Perfis",
        "Edital",
        "Categoria da Ocorrência",
        "Título",
        "Descrição",
        "Penalidade",
        "É IMR?",
        "Pontuação (IMR)",
        "Tolerância",
        "% de Desconto",
        "Status",
        "Aceita múltiplas respostas?",
    )

    os.remove(temp_file_path)


def test_formata_quantidades_da_notificacao_como_inteiros(
    categoria_ocorrencia_factory,
    formulario_supervisao_factory,
    parametrizacao_ocorrencia_factory,
    resposta_campo_numerico_factory,
    resposta_campo_texto_simples_factory,
    tipo_ocorrencia_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    tipo_resposta_modelo_factory,
):
    formulario = formulario_supervisao_factory.create()
    categoria = categoria_ocorrencia_factory.create(
        nome=RelatorioNotificacaoService.CATEGORIA_QUANTIDADE_QUALIDADE
    )
    tipo_ocorrencia = tipo_ocorrencia_factory.create(categoria=categoria)
    tipo_resposta_texto = tipo_resposta_modelo_factory.create(
        nome="RespostaCampoTextoSimples"
    )
    tipo_pergunta_texto = tipo_pergunta_parametrizacao_ocorrencia_factory.create(
        tipo_resposta=tipo_resposta_texto
    )
    tipo_resposta_numerico = tipo_resposta_modelo_factory.create(
        nome="RespostaCampoNumerico"
    )
    tipo_pergunta_numerica = tipo_pergunta_parametrizacao_ocorrencia_factory.create(
        tipo_resposta=tipo_resposta_numerico
    )
    parametrizacoes = [
        parametrizacao_ocorrencia_factory.create(
            tipo_ocorrencia=tipo_ocorrencia,
            tipo_pergunta=tipo_pergunta_texto,
            posicao=posicao,
        )
        for posicao in range(1, 3)
    ]
    parametrizacoes += [
        parametrizacao_ocorrencia_factory.create(
            tipo_ocorrencia=tipo_ocorrencia,
            tipo_pergunta=tipo_pergunta_numerica,
            posicao=posicao,
        )
        for posicao in range(3, 6)
    ]

    for grupo in range(1, 3):
        resposta_campo_texto_simples_factory.create(
            formulario_base=formulario.formulario_base,
            parametrizacao=parametrizacoes[0],
            grupo=grupo,
            resposta=f"Equipamento {grupo}",
        )
        resposta_campo_texto_simples_factory.create(
            formulario_base=formulario.formulario_base,
            parametrizacao=parametrizacoes[1],
            grupo=grupo,
            resposta=f"Motivo {grupo}",
        )
        for indice, quantidade in enumerate((10.0, 20.0, 30.0), start=2):
            resposta_campo_numerico_factory.create(
                formulario_base=formulario.formulario_base,
                parametrizacao=parametrizacoes[indice],
                grupo=grupo,
                resposta=quantidade,
            )

    respostas = RelatorioNotificacaoService(formulario).formatar_respostas(
        categoria.nome
    )

    assert len(respostas) == 2
    assert respostas[0][0].resposta == "Equipamento 1"
    assert respostas[0][1].resposta == "Motivo 1"
    assert respostas[0][2:] == [10, 20, 30]
    assert respostas[1][0].resposta == "Equipamento 2"
    assert respostas[1][1].resposta == "Motivo 2"
    assert respostas[1][2:] == [10, 20, 30]


def test_retorna_dados_do_cabecalho_sem_horario(
    contrato_factory,
    escola_factory,
    formulario_supervisao_factory,
    lote_factory,
):
    lote = lote_factory.create(nome="LOTE 01")
    escola = escola_factory.create(
        codigo_eol="019432",
        lote=lote,
        nome="CEMEI PARQUE DO LAGO",
    )
    contrato = contrato_factory.create(numero="EDITAL IMR")
    contrato.lotes.add(lote)
    formulario = formulario_supervisao_factory.create(
        escola=escola,
        formulario_base__data=date(2026, 8, 5),
    )

    dados = RelatorioNotificacaoService(formulario).retornar_dados_formatados(
        RelatorioNotificacaoService.CATEGORIA_QUANTIDADE_QUALIDADE
    )

    assert dados["unidade"] == "019432 - CEMEI PARQUE DO LAGO"
    assert dados["data_visita"] == "05/08/2026"
    assert dados["edital"] == "Edital nº EDITAL IMR"
    assert "hora_geracao" not in dados


@pytest.fixture
def dados_relatorio_notificacao():
    return {
        "data_geracao": "27/08/2026",
        "data_visita": "05/08/2026",
        "diretoria_regional": "DRE TESTE",
        "edital": "Edital nº EDITAL IMR",
        "lote": "LOTE 01",
        "maior_frequencia_no_periodo": 100,
        "respostas": [["Equipamento", "Motivo", 10, 20, 30]],
        "terceirizada": "EMPRESA TESTE",
        "total_matriculados_por_data": 120,
        "unidade": "019432 - CEMEI PARQUE DO LAGO",
        "usuario": SimpleNamespace(
            nome="NUTRICIONISTA SUPERVISORA",
            registro_funcional="1234567",
        ),
    }


def test_renderiza_conteudo_da_notificacao_quantidade_qualidade(
    dados_relatorio_notificacao,
):
    html = render_to_string(
        "IMR/relatorio_de_notificacao/quantidade_qualidade/pdf.html",
        {"dados": dados_relatorio_notificacao},
    )

    assert "logo-color.svg" in html
    assert (
        "NOTIFICAÇÃO PARA REPOSIÇÃO DE UTENSÍLIOS DE MESA, MOBILIÁRIOS E "
        "EQUIPAMENTOS"
    ) in html
    assert "Data da visita:" in html
    assert "05/08/2026" in html
    assert 'class="prazo-atendimento"' in html
    assert "A empresa deve atender a solicitação no prazo de até" in html
    assert "<u>TRÊS</u>" in html
    assert "Quantidade em boas condições para uso na unidade" in html
    assert "Quantidade para reposição" in html
    assert "Quantidade para retirada" in html
    assert "Data da conferência:" in html
    assert "Responsável pela U.E." in html
    assert "Entrega da presente notificação à Empresa:" in html
    assert "Assinatura Nutricionista RT da Empresa" in html
    assert "Documento gerado eletronicamente em 27/08/2026" in html
    assert "em 27/08/2026." in html
    assert "27/08/2026, às" not in html
    assert "10.0" not in html


def test_listagem_separa_tipos_e_grupos_do_mesmo_formulario(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
    resposta_campo_texto_simples_factory,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    resposta_campo_texto_simples_factory.create(
        formulario_base=formulario.formulario_base,
        parametrizacao=contexto.parametrizacao,
        grupo=2,
        resposta="Avental",
    )
    outro_tipo = tipo_ocorrencia_factory.create(
        edital=contexto.tipo.edital,
        penalidade=contexto.tipo.penalidade,
        categoria=contexto.tipo.categoria,
        titulo="HIGIENIZAÇÃO DAS MÃOS",
        perfis=["DIRETOR"],
    )
    outra_parametrizacao = parametrizacao_ocorrencia_factory.create(
        tipo_ocorrencia=outro_tipo,
        tipo_pergunta=contexto.parametrizacao.tipo_pergunta,
        titulo="Qual material faltou?",
        posicao=1,
    )
    resposta_campo_texto_simples_factory.create(
        formulario_base=formulario.formulario_base,
        parametrizacao=outra_parametrizacao,
        grupo=1,
        resposta="Sabonete",
    )

    dados = listar_ocorrencias_diretor([formulario])

    assert len(dados) == 3
    linhas = {
        (linha["tipo_ocorrencia"], linha["grupo"]): linha
        for linha in dados
    }
    assert set(linhas) == {
        (contexto.tipo.uuid, 1),
        (contexto.tipo.uuid, 2),
        (outro_tipo.uuid, 1),
    }
    assert linhas[(contexto.tipo.uuid, 1)]["respostas"][0]["resposta"] == "Touca"
    assert linhas[(contexto.tipo.uuid, 2)]["respostas"][0]["resposta"] == "Avental"
    assert linhas[(outro_tipo.uuid, 1)]["respostas"][0]["resposta"] == "Sabonete"
    assert all(len(linha["respostas"]) == 1 for linha in linhas.values())
    assert {linha["uuid"] for linha in linhas.values()} == {formulario.uuid}


def test_listagem_ordena_ocorrencias_pela_data_decrescente(
    criar_ocorrencia_diretor,
):
    formularios = [
        criar_ocorrencia_diretor(data=date(2026, 9, dia))
        for dia in (10, 18, 2)
    ]

    dados = listar_ocorrencias_diretor(formularios)

    assert [linha["data"] for linha in dados] == [
        date(2026, 9, 18),
        date(2026, 9, 10),
        date(2026, 9, 2),
    ]


@pytest.mark.parametrize(
    "modelo,nome_pergunta,valor,texto_esperado",
    [
        (
            RespostaCampoTextoLongo,
            "Campo de Texto Longo",
            "Primeira linha\nSegunda linha",
            "Primeira linha\nSegunda linha",
        ),
        (RespostaSimNao, "Opções Sim/Não", "Não", "Não"),
        (
            RespostaDatas,
            "Seletor de Datas",
            [date(2026, 9, 2), date(2026, 9, 3)],
            "02/09/2026, 03/09/2026",
        ),
    ],
    ids=["texto-longo", "sim-nao", "datas"],
)
def test_listagem_formata_diferentes_tipos_de_resposta(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
    modelo,
    nome_pergunta,
    valor,
    texto_esperado,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    pergunta = tipo_pergunta_parametrizacao_ocorrencia_factory.create(
        nome=nome_pergunta, tipo_resposta__nome=modelo.__name__
    )
    parametrizacao = parametrizacao_ocorrencia_factory.create(
        tipo_ocorrencia=contexto.tipo,
        tipo_pergunta=pergunta,
        titulo="Detalhes da ocorrência",
        posicao=2,
    )
    modelo.objects.create(
        formulario_base=formulario.formulario_base,
        parametrizacao=parametrizacao,
        grupo=1,
        resposta=valor,
    )

    dados = listar_ocorrencias_diretor([formulario])

    assert len(dados) == 1
    respostas = dados[0]["respostas"]
    assert len(respostas) == 2
    assert respostas[1]["parametrizacao"] == parametrizacao.uuid
    assert respostas[1]["resposta"] == texto_esperado


def test_listagem_exibe_nome_da_resposta_relacionada(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    tipo_alimentacao_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    alimentacao = tipo_alimentacao_factory.create(nome="Lanche")
    pergunta = tipo_pergunta_parametrizacao_ocorrencia_factory.create(
        nome="Seletor de Tipo de Alimentação",
        tipo_resposta__nome="RespostaTipoAlimentacao",
    )
    parametrizacao = parametrizacao_ocorrencia_factory.create(
        tipo_ocorrencia=contexto.tipo,
        tipo_pergunta=pergunta,
        titulo="Tipo de alimentação não fornecida",
        posicao=2,
    )
    RespostaTipoAlimentacao.objects.create(
        formulario_base=formulario.formulario_base,
        parametrizacao=parametrizacao,
        grupo=1,
        resposta=alimentacao,
    )

    respostas = buscar_respostas_diretor([formulario.formulario_base_id])
    detalhes = {
        detalhe["parametrizacao"]: detalhe
        for _, _, detalhe in respostas
    }

    assert len(respostas) == 2
    assert detalhes[parametrizacao.uuid]["resposta"] == "Lanche"


@pytest.mark.parametrize("descricao", ["Item indisponível nesta unidade.", ""])
def test_listagem_inclui_ocorrencia_nao_se_aplica(
    contexto_listagem_diretor,
    formulario_diretor_factory,
    ocorrencia_nao_se_aplica_factory,
    descricao,
):
    contexto = contexto_listagem_diretor
    formulario = formulario_diretor_factory.create(
        solicitacao_medicao_inicial=contexto.medicao,
        formulario_base__usuario=contexto.usuario,
        formulario_base__data=date(2026, 9, 10),
    )
    resposta_nao_se_aplica = ocorrencia_nao_se_aplica_factory.create(
        formulario_base=formulario.formulario_base,
        tipo_ocorrencia=contexto.tipo,
        grupo=1,
        descricao=descricao,
    )

    dados = listar_ocorrencias_diretor([formulario])

    assert len(dados) == 1
    assert dados[0]["uuid"] == formulario.uuid
    assert dados[0]["respostas"] == [
        {
            "uuid": resposta_nao_se_aplica.uuid,
            "parametrizacao": None,
            "titulo": "Não se aplica",
            "posicao": None,
            "resposta": descricao or "Não se aplica",
        }
    ]
