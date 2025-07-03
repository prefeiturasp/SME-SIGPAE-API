import datetime

import pytest
from django.utils import timezone
from faker import Faker
from model_mommy import mommy

from sme_sigpae_api.dados_comuns.constants import (
    DILOG_ABASTECIMENTO,
    DILOG_CRONOGRAMA,
    DILOG_QUALIDADE,
    DJANGO_ADMIN_PASSWORD,
)
from sme_sigpae_api.dados_comuns.fluxo_status import (
    FichaTecnicaDoProdutoWorkflow,
    LayoutDeEmbalagemWorkflow,
)
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.dados_comuns.utils import convert_base64_to_contentfile
from sme_sigpae_api.terceirizada.models import Terceirizada

from ..models import (
    AnaliseFichaTecnica,
    FichaTecnicaDoProduto,
    LayoutDeEmbalagem,
    TipoDeEmbalagemDeLayout,
    UnidadeMedida,
)

fake = Faker("pt_BR")


@pytest.fixture
def codae():
    return mommy.make("Codae")


@pytest.fixture
def modalidade():
    return mommy.make("Modalidade", nome="Pregão Eletrônico")

@pytest.fixture
def modalidade_chamada_publica():
    return mommy.make("Modalidade", nome="Chamada Pública")

@pytest.fixture
def modalidade_qualquer():
    # Representa qualquer modalidade diferente de "Pregão Eletrônico" e "Chamada Pública"
    return mommy.make("Modalidade", nome="Qualquer")

@pytest.fixture
def contrato(modalidade):
    return mommy.make(
        "Contrato",
        numero="0003/2022",
        processo="123",
        numero_pregao="123456789",
        modalidade=modalidade,
    )

@pytest.fixture
def contrato_chamada_publica(modalidade_chamada_publica):
    return mommy.make(
        "Contrato",
        numero="0004/2022",
        processo="124",
        numero_pregao="987654321",
        numero_chamada_publica="CP-2022-01",
        modalidade=modalidade_chamada_publica,
    )

@pytest.fixture
def contrato_qualquer(modalidade_qualquer):
    return mommy.make(
        "Contrato",
        numero="0002/2022",
        processo="222",
        numero_pregao="PE-2022-02",
        numero_chamada_publica="CP-2022-02",
        modalidade=modalidade_qualquer,
    )

@pytest.fixture
def empresa(contrato):
    return mommy.make(
        "Terceirizada",
        nome_fantasia="Alimentos SA",
        razao_social="Alimentos",
        contratos=[contrato],
        tipo_servico=Terceirizada.FORNECEDOR,
    )


@pytest.fixture
def cronograma():
    return mommy.make(
        "Cronograma",
        numero="001/2022A",
    )

@pytest.fixture
def cronograma_chamada_publica(contrato_chamada_publica):
    return mommy.make(
        "Cronograma",
        numero="003/2022A",
        contrato=contrato_chamada_publica,
    )


@pytest.fixture
def cronograma_rascunho(armazem, contrato, empresa):
    return mommy.make(
        "Cronograma",
        numero="002/2022A",
        contrato=contrato,
        armazem=armazem,
        empresa=empresa,
    )


@pytest.fixture
def cronograma_recebido(armazem, contrato, empresa):
    return mommy.make(
        "Cronograma",
        numero="002/2022A",
        contrato=contrato,
        empresa=empresa,
        armazem=armazem,
        status="ASSINADO_E_ENVIADO_AO_FORNECEDOR",
    )

@pytest.fixture
def cronograma_qualquer(contrato_qualquer):
    return mommy.make(
        "Cronograma",
        numero="002/2022A",
        contrato=contrato_qualquer,
    )

@pytest.fixture
def etapa(cronograma):
    return mommy.make(
        "EtapasDoCronograma",
        cronograma=cronograma,
        etapa=1,
        parte="Parte 1",
    )


@pytest.fixture
def etapa_com_quantidade_e_data(cronograma):
    return mommy.make(
        "EtapasDoCronograma",
        cronograma=cronograma,
        etapa=1,
        parte="Parte 1",
        data_programada=timezone.now().date(),
        quantidade=5.0,
    )


@pytest.fixture
def programacao(cronograma):
    return mommy.make(
        "ProgramacaoDoRecebimentoDoCronograma",
        cronograma=cronograma,
        data_programada="01/01/2022",
    )


@pytest.fixture
def armazem():
    return mommy.make(
        Terceirizada,
        nome_fantasia="Alimentos SA",
        tipo_servico=Terceirizada.DISTRIBUIDOR_ARMAZEM,
    )


@pytest.fixture
def laboratorio():
    return mommy.make("Laboratorio", nome="Labo Test")


@pytest.fixture
def tipo_emabalagem_qld():
    return mommy.make("TipoEmbalagemQld", nome="CAIXA", abreviacao="CX")


@pytest.fixture
def cronograma_solicitado_alteracao(armazem, contrato, empresa):
    return mommy.make(
        "Cronograma",
        numero="00222/2022A",
        contrato=contrato,
        empresa=empresa,
        armazem=armazem,
        status="SOLICITADO_ALTERACAO",
    )


@pytest.fixture
def solicitacao_cronograma_em_analise(cronograma):
    return mommy.make(
        "SolicitacaoAlteracaoCronograma",
        numero_solicitacao="00222/2022",
        cronograma=cronograma,
        status="EM_ANALISE",
    )


@pytest.fixture
def solicitacao_cronograma_ciente(cronograma):
    return mommy.make(
        "SolicitacaoAlteracaoCronograma",
        numero_solicitacao="00222/2022",
        cronograma=cronograma,
        status="CRONOGRAMA_CIENTE",
    )


@pytest.fixture
def solicitacao_cronograma_aprovado_dilog_abastecimento(
    cronograma_solicitado_alteracao,
):
    return mommy.make(
        "SolicitacaoAlteracaoCronograma",
        numero_solicitacao="00222/2022",
        cronograma=cronograma_solicitado_alteracao,
        status="APROVADO_DILOG_ABASTECIMENTO",
    )


@pytest.fixture
def cronograma_assinado_fornecedor(armazem, contrato, empresa):
    return mommy.make(
        "Cronograma",
        numero="002/2022A",
        contrato=contrato,
        empresa=empresa,
        armazem=armazem,
        status="ASSINADO_FORNECEDOR",
    )


@pytest.fixture
def cronograma_assinado_perfil_cronograma(armazem, contrato, empresa):
    return mommy.make(
        "Cronograma",
        numero="002/2022A",
        contrato=contrato,
        empresa=empresa,
        armazem=armazem,
        status="ASSINADO_E_ENVIADO_AO_FORNECEDOR",
    )


@pytest.fixture
def cronograma_assinado_perfil_dilog_abastecimento(armazem, contrato, empresa):
    return mommy.make(
        "Cronograma",
        numero="003/2022A",
        contrato=contrato,
        empresa=empresa,
        armazem=armazem,
        status="ASSINADO_DILOG_ABASTECIMENTO",
    )


@pytest.fixture
def cronograma_assinado_perfil_dilog(
    armazem,
    contrato,
    empresa,
    ficha_tecnica_factory,
):
    return mommy.make(
        "Cronograma",
        numero="004/2022A",
        contrato=contrato,
        empresa=empresa,
        armazem=armazem,
        status="ASSINADO_CODAE",
        ficha_tecnica=ficha_tecnica_factory(),
    )


@pytest.fixture
def produto_arroz():
    return mommy.make("NomeDeProdutoEdital", nome="Arroz")


@pytest.fixture
def produto_macarrao():
    return mommy.make("NomeDeProdutoEdital", nome="Macarrão")


@pytest.fixture
def produto_feijao():
    return mommy.make("NomeDeProdutoEdital", nome="Feijão")


@pytest.fixture
def produto_acucar():
    return mommy.make("NomeDeProdutoEdital", nome="Açucar")


@pytest.fixture
def cronogramas_multiplos_status_com_log(
    armazem, contrato, empresa, ficha_tecnica_factory
):
    c1 = mommy.make(
        "Cronograma",
        numero="002/2023A",
        contrato=contrato,
        empresa=empresa,
        armazem=armazem,
        status="ASSINADO_FORNECEDOR",
        ficha_tecnica=ficha_tecnica_factory(),
    )
    c2 = mommy.make(
        "Cronograma",
        numero="003/2023A",
        contrato=contrato,
        empresa=empresa,
        armazem=armazem,
        status="ASSINADO_FORNECEDOR",
        ficha_tecnica=ficha_tecnica_factory(),
    )
    c3 = mommy.make(
        "Cronograma",
        numero="004/2023A",
        contrato=contrato,
        empresa=empresa,
        armazem=armazem,
        status="ASSINADO_DILOG_ABASTECIMENTO",
        ficha_tecnica=ficha_tecnica_factory(),
    )
    c4 = mommy.make(
        "Cronograma",
        numero="005/2023A",
        contrato=contrato,
        empresa=empresa,
        armazem=armazem,
        status="ASSINADO_DILOG_ABASTECIMENTO",
        ficha_tecnica=ficha_tecnica_factory(),
    )
    c5 = mommy.make(
        "Cronograma",
        numero="006/2023A",
        contrato=contrato,
        empresa=empresa,
        armazem=armazem,
        status="ASSINADO_FORNECEDOR",
        ficha_tecnica=ficha_tecnica_factory(),
    )
    c6 = mommy.make(
        "Cronograma",
        numero="007/2023A",
        contrato=contrato,
        empresa=empresa,
        armazem=armazem,
        status="ASSINADO_CODAE",
        ficha_tecnica=ficha_tecnica_factory(),
    )
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=c1.uuid,
        status_evento=59,  # CRONOGRAMA_ASSINADO_PELO_USUARIO_CRONOGRAMA
        solicitacao_tipo=19,
    )  # CRONOGRAMA
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=c2.uuid,
        status_evento=59,  # CRONOGRAMA_ASSINADO_PELO_USUARIO_CRONOGRAMA
        solicitacao_tipo=19,
    )  # CRONOGRAMA
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=c3.uuid,
        status_evento=69,  # CRONOGRAMA_ASSINADO_PELA_DILOG_ABASTECIMENTO
        solicitacao_tipo=19,
    )  # CRONOGRAMA
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=c4.uuid,
        status_evento=69,  # CRONOGRAMA_ASSINADO_PELA_DILOG_ABASTECIMENTO
        solicitacao_tipo=19,
    )  # CRONOGRAMA
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=c5.uuid,
        status_evento=59,  # CRONOGRAMA_ASSINADO_PELO_USUARIO_CRONOGRAMA
        solicitacao_tipo=19,
    )  # CRONOGRAMA
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=c6.uuid,
        status_evento=70,  # CRONOGRAMA_ASSINADO_PELA_CODAE
        solicitacao_tipo=19,
    )  # CRONOGRAMA


@pytest.fixture
def cronogramas_multiplos_status_com_log_cronograma_ciente(armazem, contrato, empresa):
    c1 = mommy.make(
        "Cronograma",
        numero="002/2023A",
        contrato=contrato,
        empresa=empresa,
        armazem=armazem,
        status="SOLICITADO_ALTERACAO",
    )
    c2 = mommy.make(
        "Cronograma",
        numero="003/2023A",
        contrato=contrato,
        empresa=empresa,
        armazem=armazem,
        status="SOLICITADO_ALTERACAO",
    )
    s1 = mommy.make(
        "SolicitacaoAlteracaoCronograma",
        numero_solicitacao="00222/2022",
        cronograma=c1,
        status="CRONOGRAMA_CIENTE",
    )
    s2 = mommy.make(
        "SolicitacaoAlteracaoCronograma",
        numero_solicitacao="00223/2022",
        cronograma=c2,
        status="CRONOGRAMA_CIENTE",
    )
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=s1.uuid,
        status_evento=71,  # CRONOGRAMA_CIENTE_SOLICITACAO_ALTERACAO
        solicitacao_tipo=20,
    )  # CRONOGRAMA
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=s2.uuid,
        status_evento=71,  # CRONOGRAMA_CIENTE_SOLICITACAO_ALTERACAO
        solicitacao_tipo=20,
    )  # CRONOGRAMA
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=c1.uuid,
        status_evento=71,  # CRONOGRAMA_CIENTE_SOLICITACAO_ALTERACAO
        solicitacao_tipo=19,
    )  # CRONOGRAMA
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=c2.uuid,
        status_evento=71,  # CRONOGRAMA_CIENTE_SOLICITACAO_ALTERACAO
        solicitacao_tipo=19,
    )  # CRONOGRAMA


@pytest.fixture
def unidade_medida_logistica():
    return mommy.make(UnidadeMedida, nome="UNIDADE TESTE", abreviacao="ut")


@pytest.fixture
def unidades_medida_logistica():
    data = [
        {"nome": f"UNIDADE TESTE {i}", "abreviacao": f"ut{i}"} for i in range(1, 21)
    ]
    objects = [mommy.make(UnidadeMedida, **attrs) for attrs in data]
    return objects


@pytest.fixture
def unidades_medida_reais_logistica():
    data = [
        {"nome": "KILOGRAMA", "abreviacao": "kg"},
        {"nome": "LITRO", "abreviacao": "l"},
    ]
    objects = [mommy.make(UnidadeMedida, **attrs) for attrs in data]
    return objects


@pytest.fixture
def layout_de_embalagem(ficha_tecnica_perecivel_enviada_para_analise):
    return mommy.make(
        "LayoutDeEmbalagem",
        ficha_tecnica=ficha_tecnica_perecivel_enviada_para_analise,
        observacoes="teste",
    )


@pytest.fixture
def payload_layout_embalagem(
    ficha_tecnica_perecivel_enviada_para_analise,
    arquivo_base64,
):
    return {
        "ficha_tecnica": str(ficha_tecnica_perecivel_enviada_para_analise.uuid),
        "observacoes": "Imagine uma observação aqui.",
        "tipos_de_embalagens": [
            {
                "tipo_embalagem": "PRIMARIA",
                "imagens_do_tipo_de_embalagem": [
                    {"arquivo": arquivo_base64, "nome": "Anexo1.jpg"},
                    {"arquivo": arquivo_base64, "nome": "Anexo2.jpg"},
                ],
            },
            {
                "tipo_embalagem": "SECUNDARIA",
                "imagens_do_tipo_de_embalagem": [
                    {"arquivo": arquivo_base64, "nome": "Anexo1.jpg"}
                ],
            },
        ],
    }


@pytest.fixture
def tipo_de_embalagem_de_layout(layout_de_embalagem):
    return mommy.make(
        "TipoDeEmbalagemDeLayout",
        layout_de_embalagem=layout_de_embalagem,
        tipo_embalagem="PRIMARIA",
        status="APROVADO",
        complemento_do_status="Teste de aprovacao",
    )


@pytest.fixture
def lista_layouts_de_embalagem_enviados_para_analise(ficha_tecnica_factory, empresa):
    layouts_cronograma_assinado_dilog_abastecimento = [
        {
            "ficha_tecnica": ficha_tecnica_factory(
                status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
                empresa=empresa,
            ),
            "observacoes": f"Teste {i}",
            "status": LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE,
        }
        for i in range(1, 6)
    ]

    layouts_cronograma_assinado_dilog = [
        {
            "ficha_tecnica": ficha_tecnica_factory(
                status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
                empresa=empresa,
            ),
            "observacoes": f"Teste {i}",
            "status": LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE,
        }
        for i in range(6, 16)
    ]

    data = (
        layouts_cronograma_assinado_dilog
        + layouts_cronograma_assinado_dilog_abastecimento
    )

    objects = [mommy.make(LayoutDeEmbalagem, **attrs) for attrs in data]

    return objects


@pytest.fixture
def lista_layouts_de_embalagem_aprovados(ficha_tecnica_factory, empresa):
    layouts_cronograma_assinado_dilog_abastecimento = [
        {
            "ficha_tecnica": ficha_tecnica_factory(
                status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
                empresa=empresa,
            ),
            "observacoes": f"Teste {i}",
            "status": LayoutDeEmbalagemWorkflow.APROVADO,
        }
        for i in range(1, 6)
    ]

    layouts_cronograma_assinado_dilog = [
        {
            "ficha_tecnica": ficha_tecnica_factory(
                status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
                empresa=empresa,
            ),
            "observacoes": f"Teste {i}",
            "status": LayoutDeEmbalagemWorkflow.APROVADO,
        }
        for i in range(6, 16)
    ]

    data = (
        layouts_cronograma_assinado_dilog
        + layouts_cronograma_assinado_dilog_abastecimento
    )

    objects = [mommy.make(LayoutDeEmbalagem, **attrs) for attrs in data]

    return objects


@pytest.fixture
def lista_layouts_de_embalagem_solicitado_correcao(ficha_tecnica_factory, empresa):
    layouts_cronograma_assinado_dilog_abastecimento = [
        {
            "ficha_tecnica": ficha_tecnica_factory(
                status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
                empresa=empresa,
            ),
            "observacoes": f"Teste {i}",
            "status": LayoutDeEmbalagemWorkflow.SOLICITADO_CORRECAO,
        }
        for i in range(1, 6)
    ]

    layouts_cronograma_assinado_dilog = [
        {
            "ficha_tecnica": ficha_tecnica_factory(
                status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
                empresa=empresa,
            ),
            "observacoes": f"Teste {i}",
            "status": LayoutDeEmbalagemWorkflow.SOLICITADO_CORRECAO,
        }
        for i in range(6, 16)
    ]

    data = (
        layouts_cronograma_assinado_dilog
        + layouts_cronograma_assinado_dilog_abastecimento
    )

    objects = [mommy.make(LayoutDeEmbalagem, **attrs) for attrs in data]

    return objects


@pytest.fixture
def lista_layouts_de_embalagem_com_tipo_embalagem(ficha_tecnica_factory, empresa):
    dados_layouts = [
        {
            "ficha_tecnica": ficha_tecnica_factory(
                status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
                empresa=empresa,
            ),
            "observacoes": f"Teste {i}",
            "status": LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE,
        }
        for i in range(1, 3)
    ]

    layouts = [mommy.make(LayoutDeEmbalagem, **attrs) for attrs in dados_layouts]

    mommy.make(
        TipoDeEmbalagemDeLayout,
        layout_de_embalagem=layouts[0],
        tipo_embalagem=TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_PRIMARIA,
    )
    mommy.make(
        TipoDeEmbalagemDeLayout,
        layout_de_embalagem=layouts[0],
        tipo_embalagem=TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_SECUNDARIA,
    )
    mommy.make(
        TipoDeEmbalagemDeLayout,
        layout_de_embalagem=layouts[0],
        tipo_embalagem=TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_TERCIARIA,
    )

    mommy.make(
        TipoDeEmbalagemDeLayout,
        layout_de_embalagem=layouts[1],
        tipo_embalagem=TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_PRIMARIA,
    )
    mommy.make(
        TipoDeEmbalagemDeLayout,
        layout_de_embalagem=layouts[1],
        tipo_embalagem=TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_SECUNDARIA,
    )

    return layouts


@pytest.fixture
def lista_layouts_de_embalagem(
    lista_layouts_de_embalagem_enviados_para_analise,
    lista_layouts_de_embalagem_aprovados,
    lista_layouts_de_embalagem_solicitado_correcao,
):
    return (
        lista_layouts_de_embalagem_enviados_para_analise
        + lista_layouts_de_embalagem_aprovados
        + lista_layouts_de_embalagem_solicitado_correcao
    )


@pytest.fixture
def layout_de_embalagem_para_correcao(ficha_tecnica_factory, empresa):
    layout = mommy.make(
        LayoutDeEmbalagem,
        ficha_tecnica=ficha_tecnica_factory(
            status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
            empresa=empresa,
        ),
        observacoes="Imagine uma observação aqui.",
        status=LayoutDeEmbalagemWorkflow.SOLICITADO_CORRECAO,
    )
    mommy.make(
        TipoDeEmbalagemDeLayout,
        layout_de_embalagem=layout,
        tipo_embalagem=TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_PRIMARIA,
        status=TipoDeEmbalagemDeLayout.STATUS_REPROVADO,
    )
    mommy.make(
        TipoDeEmbalagemDeLayout,
        layout_de_embalagem=layout,
        tipo_embalagem=TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_SECUNDARIA,
        status=TipoDeEmbalagemDeLayout.STATUS_APROVADO,
    )

    return layout


@pytest.fixture
def layout_de_embalagem_aprovado(ficha_tecnica_factory, empresa):
    layout = mommy.make(
        LayoutDeEmbalagem,
        ficha_tecnica=ficha_tecnica_factory(
            status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
            empresa=empresa,
        ),
        observacoes="Imagine uma observação aqui.",
        status=LayoutDeEmbalagemWorkflow.APROVADO,
    )
    mommy.make(
        TipoDeEmbalagemDeLayout,
        layout_de_embalagem=layout,
        tipo_embalagem=TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_PRIMARIA,
        status=TipoDeEmbalagemDeLayout.STATUS_APROVADO,
    )
    mommy.make(
        TipoDeEmbalagemDeLayout,
        layout_de_embalagem=layout,
        tipo_embalagem=TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_SECUNDARIA,
        status=TipoDeEmbalagemDeLayout.STATUS_APROVADO,
    )
    mommy.make(
        LogSolicitacoesUsuario,
        uuid_original=layout.uuid,
        status_evento=LogSolicitacoesUsuario.LAYOUT_CORRECAO_REALIZADA,
        solicitacao_tipo=LogSolicitacoesUsuario.LAYOUT_DE_EMBALAGEM,
    )

    return layout


@pytest.fixture
def layout_de_embalagem_em_analise_com_correcao(ficha_tecnica_factory, empresa):
    layout = mommy.make(
        LayoutDeEmbalagem,
        ficha_tecnica=ficha_tecnica_factory(
            status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
            empresa=empresa,
        ),
        observacoes="Imagine uma observação aqui.",
        status=LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE,
    )
    mommy.make(
        TipoDeEmbalagemDeLayout,
        layout_de_embalagem=layout,
        tipo_embalagem=TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_PRIMARIA,
        status=TipoDeEmbalagemDeLayout.STATUS_EM_ANALISE,
    )
    mommy.make(
        TipoDeEmbalagemDeLayout,
        layout_de_embalagem=layout,
        tipo_embalagem=TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_SECUNDARIA,
        status=TipoDeEmbalagemDeLayout.STATUS_APROVADO,
    )
    mommy.make(
        TipoDeEmbalagemDeLayout,
        layout_de_embalagem=layout,
        tipo_embalagem=TipoDeEmbalagemDeLayout.TIPO_EMBALAGEM_TERCIARIA,
        status=TipoDeEmbalagemDeLayout.STATUS_EM_ANALISE,
    )
    mommy.make(
        LogSolicitacoesUsuario,
        uuid_original=layout.uuid,
        status_evento=LogSolicitacoesUsuario.LAYOUT_CORRECAO_REALIZADA,
        solicitacao_tipo=LogSolicitacoesUsuario.LAYOUT_DE_EMBALAGEM,
    )

    return layout


@pytest.fixture
def payload_ficha_tecnica_rascunho(
    produto_logistica_factory,
    empresa,
    marca_factory,
    fabricante_factory,
):
    return {
        "produto": str(produto_logistica_factory().uuid),
        "marca": str(marca_factory().uuid),
        "empresa": str(empresa.uuid),
        "fabricante": {
            "fabricante": str(fabricante_factory().uuid),
        },
        "envasador_distribuidor": {
            "fabricante": str(fabricante_factory().uuid),
        },
        "categoria": FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
        "pregao_chamada_publica": fake.pystr(max_chars=100),
        "prazo_validade": "",
        "numero_registro": "",
        "mecanismo_controle": "",
        "componentes_produto": "",
        "ingredientes_alergenicos": "",
        "lactose_detalhe": "",
        "porcao": "",
        "unidade_medida_porcao": "",
        "valor_unidade_caseira": "",
        "unidade_medida_caseira": "",
        "informacoes_nutricionais": [],
        "condicoes_de_conservacao": "",
        "embalagem_primaria": "",
        "embalagem_secundaria": "",
        "material_embalagem_primaria": "",
        "volume_embalagem_primaria": None,
        "unidade_medida_volume_primaria": "",
        "peso_liquido_embalagem_primaria": None,
        "unidade_medida_primaria": "",
        "peso_liquido_embalagem_secundaria": None,
        "unidade_medida_secundaria": "",
        "peso_embalagem_primaria_vazia": None,
        "unidade_medida_primaria_vazia": "",
        "peso_embalagem_secundaria_vazia": None,
        "unidade_medida_secundaria_vazia": "",
        "sistema_vedacao_embalagem_secundaria": "",
        "nome_responsavel_tecnico": "",
        "habilitacao": "",
        "numero_registro_orgao": "",
        "arquivo": "",
        "modo_de_preparo": "",
        "informacoes_adicionais": "",
    }


@pytest.fixture
def payload_ficha_tecnica_pereciveis(
    payload_ficha_tecnica_rascunho,
    arquivo_pdf_base64,
    unidade_medida_logistica,
):
    payload = {
        **payload_ficha_tecnica_rascunho,
        "prazo_validade": fake.pystr(max_chars=150),
        "numero_registro": fake.pystr(max_chars=150),
        "agroecologico": True,
        "organico": True,
        "mecanismo_controle": FichaTecnicaDoProduto.MECANISMO_OPAC,
        "componentes_produto": fake.pystr(max_chars=250),
        "alergenicos": True,
        "ingredientes_alergenicos": fake.pystr(max_chars=150),
        "gluten": True,
        "lactose": True,
        "lactose_detalhe": fake.pystr(max_chars=150),
        "porcao": fake.pystr(max_chars=100),
        "unidade_medida_porcao": str(unidade_medida_logistica.uuid),
        "valor_unidade_caseira": fake.pystr(max_chars=100),
        "unidade_medida_caseira": str(unidade_medida_logistica.uuid),
        "prazo_validade_descongelamento": fake.pystr(max_chars=50),
        "condicoes_de_conservacao": fake.pystr(max_chars=150),
        "temperatura_congelamento": 0,
        "temperatura_veiculo": -fake.random_number() / 100,
        "condicoes_de_transporte": fake.pystr(max_chars=150),
        "embalagem_primaria": fake.pystr(max_chars=150),
        "embalagem_secundaria": fake.pystr(max_chars=150),
        "embalagens_de_acordo_com_anexo": True,
        "material_embalagem_primaria": fake.pystr(max_chars=150),
        "peso_liquido_embalagem_primaria": fake.random_number() / 100,
        "unidade_medida_primaria": str(unidade_medida_logistica.uuid),
        "peso_liquido_embalagem_secundaria": fake.random_number() / 100,
        "unidade_medida_secundaria": str(unidade_medida_logistica.uuid),
        "peso_embalagem_primaria_vazia": fake.random_number() / 100,
        "unidade_medida_primaria_vazia": str(unidade_medida_logistica.uuid),
        "peso_embalagem_secundaria_vazia": fake.random_number() / 100,
        "unidade_medida_secundaria_vazia": str(unidade_medida_logistica.uuid),
        "variacao_percentual": fake.random_number() / 100,
        "sistema_vedacao_embalagem_secundaria": fake.pystr(max_chars=150),
        "rotulo_legivel": True,
        "nome_responsavel_tecnico": fake.pystr(max_chars=100),
        "habilitacao": fake.pystr(max_chars=100),
        "numero_registro_orgao": fake.pystr(max_chars=50),
        "arquivo": arquivo_pdf_base64,
        "password": DJANGO_ADMIN_PASSWORD,
    }

    payload.pop("volume_embalagem_primaria")
    payload.pop("unidade_medida_volume_primaria")

    return payload


@pytest.fixture
def payload_ficha_tecnica_nao_pereciveis(
    payload_ficha_tecnica_pereciveis,
    unidade_medida_logistica,
):
    payload = {
        **payload_ficha_tecnica_pereciveis,
        "categoria": FichaTecnicaDoProduto.CATEGORIA_NAO_PERECIVEIS,
        "produto_eh_liquido": True,
        "volume_embalagem_primaria": fake.random_number() / 100,
        "unidade_medida_volume_primaria": str(unidade_medida_logistica.uuid),
    }

    payload.pop("prazo_validade_descongelamento")
    payload.pop("temperatura_congelamento")
    payload.pop("temperatura_veiculo")
    payload.pop("condicoes_de_transporte")
    payload.pop("variacao_percentual")

    return payload


@pytest.fixture
def ficha_tecnica_perecivel_enviada_para_analise(
    payload_ficha_tecnica_pereciveis,
    produto_logistica_factory,
    empresa,
    marca_factory,
    fabricante_ficha_tecnica_factory,
    arquivo_pdf_base64,
    unidade_medida_logistica,
):
    fabricante = fabricante_ficha_tecnica_factory()
    envasador = fabricante_ficha_tecnica_factory()
    dados = {
        **payload_ficha_tecnica_pereciveis,
        "produto": produto_logistica_factory(),
        "marca": marca_factory(),
        "empresa": empresa,
        "fabricante": fabricante,
        "envasador_distribuidor": envasador,
        "categoria": FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
        "unidade_medida_porcao": unidade_medida_logistica,
        "unidade_medida_primaria": unidade_medida_logistica,
        "unidade_medida_secundaria": unidade_medida_logistica,
        "unidade_medida_primaria_vazia": unidade_medida_logistica,
        "unidade_medida_secundaria_vazia": unidade_medida_logistica,
        "arquivo": convert_base64_to_contentfile(arquivo_pdf_base64),
        "status": FichaTecnicaDoProduto.workflow_class.ENVIADA_PARA_ANALISE,
    }

    dados.pop("informacoes_nutricionais")
    dados.pop("password")

    return FichaTecnicaDoProduto.objects.create(**dados)


@pytest.fixture
def payload_analise_ficha_tecnica():
    return {
        "detalhes_produto_conferido": True,
        "detalhes_produto_correcoes": "",
        "informacoes_nutricionais_conferido": True,
        "informacoes_nutricionais_correcoes": "",
        "conservacao_conferido": True,
        "conservacao_correcoes": "",
        "temperatura_e_transporte_conferido": True,
        "temperatura_e_transporte_correcoes": "",
        "armazenamento_conferido": True,
        "armazenamento_correcoes": "",
        "embalagem_e_rotulagem_conferido": True,
        "embalagem_e_rotulagem_correcoes": "",
        "responsavel_tecnico_conferido": True,
        "modo_preparo_conferido": True,
        "outras_informacoes_conferido": True,
    }


@pytest.fixture
def payload_atualizacao_ficha_tecnica(unidade_medida_logistica, arquivo_pdf_base64):
    return {
        "componentes_produto": fake.pystr(max_chars=250),
        "alergenicos": True,
        "ingredientes_alergenicos": fake.pystr(max_chars=150),
        "gluten": True,
        "porcao": fake.pystr(max_chars=100),
        "unidade_medida_porcao": str(unidade_medida_logistica.uuid),
        "valor_unidade_caseira": fake.pystr(max_chars=100),
        "unidade_medida_caseira": str(unidade_medida_logistica.uuid),
        "informacoes_nutricionais": [],
        "condicoes_de_conservacao": fake.pystr(max_chars=150),
        "embalagem_primaria": fake.pystr(max_chars=150),
        "embalagem_secundaria": fake.pystr(max_chars=150),
        "nome_responsavel_tecnico": fake.pystr(max_chars=100),
        "habilitacao": fake.pystr(max_chars=100),
        "numero_registro_orgao": fake.pystr(max_chars=50),
        "arquivo": arquivo_pdf_base64,
        "modo_de_preparo": fake.pystr(max_chars=50),
        "informacoes_adicionais": fake.pystr(max_chars=50),
    }


@pytest.fixture
def analise_ficha_tecnica(
    ficha_tecnica_perecivel_enviada_para_analise,
    payload_analise_ficha_tecnica,
):
    return AnaliseFichaTecnica.objects.create(
        ficha_tecnica=ficha_tecnica_perecivel_enviada_para_analise,
        **payload_analise_ficha_tecnica,
    )


@pytest.fixture
def client_autenticado_vinculo_dilog_cronograma(client, django_user_model, codae):
    email = "test@test.com"
    password = DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_dilog_cronograma = mommy.make(
        "Perfil",
        nome=DILOG_CRONOGRAMA,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )

    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_dilog_cronograma,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    client.login(username=email, password=password)
    return client, user


@pytest.fixture
def client_autenticado_vinculo_dilog_qualidade(client, django_user_model, codae):
    email = "test@test.com"
    password = DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_dilog_qualidade = mommy.make(
        "Perfil",
        nome=DILOG_QUALIDADE,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )

    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_dilog_qualidade,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    client.login(username=email, password=password)
    return client, user


@pytest.fixture
def client_autenticado_dilog_abastecimento(client, django_user_model):
    email = "dilogabastecimento@test.com"
    password = DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional=str(fake.unique.random_int(min=100000, max=999999)),
    )
    perfil_dilog_abastecimento = mommy.make(
        "Perfil", nome=DILOG_ABASTECIMENTO, ativo=True
    )
    codae = mommy.make("Codae")
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_dilog_abastecimento,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client
