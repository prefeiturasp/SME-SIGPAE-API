import xml.etree.ElementTree as ET
from datetime import datetime

import pytest
from faker import Faker
from model_bakery import baker
from spyne.util.dictdoc import get_object_as_dict

from sme_sigpae_api.dados_comuns.fluxo_status import SolicitacaoRemessaWorkFlow
from sme_sigpae_api.logistica.api.soup.models import (
    Alimento,
    ArqCancelamento,
    ArqSolicitacaoMOD,
    Guia,
    GuiCan,
    oWsAcessoModel,
)
from sme_sigpae_api.logistica.models.solicitacao import SolicitacaoRemessa
from sme_sigpae_api.terceirizada.models import Terceirizada

from ...escola import models
from ..models.guia import ConferenciaIndividualPorAlimento

fake = Faker("pt_BR")
Faker.seed(420)


@pytest.fixture
def distribuidor():
    return baker.make(
        "Usuario", email="distribuidor@admin.com", cpf="12345678910", is_superuser=True
    )


@pytest.fixture
def terceirizada():
    return baker.make(
        "Terceirizada",
        contatos=[baker.make("dados_comuns.Contato")],
        make_m2m=True,
        nome_fantasia="Alimentos SA",
    )


@pytest.fixture
def solicitacao(terceirizada):
    return baker.make(
        "SolicitacaoRemessa",
        cnpj="12345678901234",
        numero_solicitacao="559890",
        sequencia_envio=1212,
        quantidade_total_guias=2,
        distribuidor=terceirizada,
    )


@pytest.fixture
def lote():
    return baker.make(models.Lote, nome="lote", iniciais="lt")


@pytest.fixture
def escola(lote):
    return baker.make(
        models.Escola,
        nome="CEI DIRET ROBERTO ARANTES LANHOSO",
        codigo_eol="400221",
        lote=lote,
    )


@pytest.fixture
def escola_com_guia(lote, escola):
    return models.Escola.objects.get(uuid=str(escola.uuid))


@pytest.fixture
def guia(solicitacao, escola):
    return baker.make(
        "Guia",
        solicitacao=solicitacao,
        escola=escola,
        numero_guia="987654",
        data_entrega="2019-02-25",
        codigo_unidade="58880",
        nome_unidade="EMEI ALUISIO DE ALMEIDA",
        endereco_unidade="Rua Alvaro de Azevedo Antunes",
        numero_unidade="1200",
        bairro_unidade="VILA CAMPESINA",
        cep_unidade="03046059",
        cidade_unidade="OSASCO",
        estado_unidade="SP",
        contato_unidade="Carlos",
        telefone_unidade="944462050",
    )


@pytest.fixture
def guia_pendente_de_conferencia(solicitacao, escola):
    return baker.make(
        "Guia",
        solicitacao=solicitacao,
        escola=escola,
        numero_guia="9876543",
        data_entrega="2019-02-25",
        codigo_unidade="58880",
        nome_unidade="EMEI ALUISIO DE ALMEIDA",
        endereco_unidade="Rua Alvaro de Azevedo Antunes",
        numero_unidade="1200",
        bairro_unidade="VILA CAMPESINA",
        cep_unidade="03046059",
        cidade_unidade="OSASCO",
        estado_unidade="SP",
        contato_unidade="Carlos",
        telefone_unidade="944462050",
        status="PENDENTE_DE_CONFERENCIA",
    )


@pytest.fixture
def guia_com_escola_client_autenticado(solicitacao, escola_com_guia):
    return baker.make(
        "Guia",
        solicitacao=solicitacao,
        escola=escola_com_guia,
        numero_guia="98765432",
        data_entrega="2019-02-25",
        codigo_unidade="58880",
        nome_unidade="EMEI ALUISIO DE ALMEIDA",
        endereco_unidade="Rua Alvaro de Azevedo Antunes",
        numero_unidade="1200",
        bairro_unidade="VILA CAMPESINA",
        cep_unidade="03046059",
        cidade_unidade="OSASCO",
        estado_unidade="SP",
        contato_unidade="Carlos",
        telefone_unidade="944462050",
        status="PENDENTE_DE_CONFERENCIA",
    )


@pytest.fixture
def alimento(guia_com_escola_client_autenticado):
    return baker.make(
        "logistica.Alimento",
        guia=guia_com_escola_client_autenticado,
        codigo_suprimento="123456",
        codigo_papa="2345",
        nome_alimento="PATINHO",
    )


@pytest.fixture
def embalagem(alimento):
    return baker.make(
        "Embalagem",
        alimento=alimento,
        descricao_embalagem="CX",
        capacidade_embalagem=9.13,
        unidade_medida="KG",
        tipo_embalagem="FECHADA",
        qtd_volume=90,
        qtd_a_receber=0,
    )


@pytest.fixture
def solicitacao_de_alteracao_requisicao(solicitacao, distribuidor):
    return baker.make(
        "SolicitacaoDeAlteracaoRequisicao",
        requisicao=solicitacao,
        motivo="OUTROS",
        justificativa=fake.text(),
        justificativa_aceite=fake.text(),
        justificativa_negacao=fake.text(),
        usuario_solicitante=distribuidor,
        numero_solicitacao="00000001-ALT",
    )


@pytest.fixture
def conferencia_guia(guia_com_escola_client_autenticado):
    return baker.make(
        "ConferenciaGuia",
        guia=guia_com_escola_client_autenticado,
        data_recebimento=datetime.now(),
        hora_recebimento=datetime.now().time(),
        nome_motorista="José da Silva",
        placa_veiculo="77AB75A",
    )


@pytest.fixture
def conferencia_guia_normal(guia):
    return baker.make(
        "ConferenciaGuia",
        guia=guia,
        data_recebimento=datetime.now(),
        hora_recebimento=datetime.now().time(),
        nome_motorista="José da Silva",
        placa_veiculo="77AB75A",
    )


@pytest.fixture
def reposicao_guia(guia):
    return baker.make(
        "ConferenciaGuia",
        guia=guia,
        data_recebimento=datetime.now(),
        hora_recebimento=datetime.now().time(),
        nome_motorista="José da Silva",
        placa_veiculo="77AB75A",
        eh_reposicao=True,
    )


@pytest.fixture
def conferencia_guia_individual(conferencia_guia_normal):
    return baker.make(
        "ConferenciaIndividualPorAlimento",
        conferencia=conferencia_guia_normal,
        tipo_embalagem=ConferenciaIndividualPorAlimento.FECHADA,
        status_alimento=ConferenciaIndividualPorAlimento.STATUS_ALIMENTO_RECEBIDO,
        ocorrencia=[ConferenciaIndividualPorAlimento.OCORRENCIA_AUSENCIA_PRODUTO],
        nome_alimento="PATINHO",
        qtd_recebido=20,
    )


@pytest.fixture
def insucesso_entrega_guia(guia):
    return baker.make(
        "InsucessoEntregaGuia",
        guia=guia,
        hora_tentativa=datetime.now().time(),
        nome_motorista="José da Silva",
        placa_veiculo="77AB75A",
        justificativa="Unidade estava fechada.",
        motivo="UNIDADE_FECHADA",
    )


@pytest.fixture
def solicitacao_cancelamento_log(solicitacao):
    return baker.make(
        "LogSolicitacaoDeCancelamentoPeloPapa",
        requisicao=solicitacao,
        guias=["21236", "235264"],
        sequencia_envio="123456",
        foi_confirmada=False,
    )


@pytest.fixture
def notificacao_ocorrencia(terceirizada):
    notificacao = baker.make(
        "NotificacaoOcorrenciasGuia",
        numero="1234567890",
        processo_sei="9876543210",
        empresa=terceirizada,
    )

    baker.make(
        "PrevisaoContratualNotificacao",
        notificacao=notificacao,
        motivo_ocorrencia=ConferenciaIndividualPorAlimento.OCORRENCIA_ATRASO_ENTREGA,
        previsao_contratual="Previsao contratual teste 1",
    )

    baker.make(
        "PrevisaoContratualNotificacao",
        notificacao=notificacao,
        motivo_ocorrencia=ConferenciaIndividualPorAlimento.OCORRENCIA_EMBALAGEM_DANIFICADA,
        previsao_contratual="Previsao contratual teste 2",
    )

    return notificacao


@pytest.fixture
def notificacoes_ocorrencia(terceirizada):
    data = [
        {"numero": f"{i}", "processo_sei": f"{2*i}", "empresa": terceirizada}
        for i in range(1, 21)
    ]
    objects = [baker.make("NotificacaoOcorrenciasGuia", **attrs) for attrs in data]
    return objects


@pytest.fixture
def previsao_contratual(notificacao_ocorrencia):
    return baker.make(
        "PrevisaoContratualNotificacao",
        notificacao=notificacao_ocorrencia,
        motivo_ocorrencia=ConferenciaIndividualPorAlimento.OCORRENCIA_ATRASO_ENTREGA,
        previsao_contratual="Era pra ter sido entregue ontem.",
    )


@pytest.fixture
def previsoes_contratuais(notificacao_ocorrencia):
    data = [
        {
            "notificacao": notificacao_ocorrencia,
            "motivo_ocorrencia": ConferenciaIndividualPorAlimento.OCORRENCIA_CHOICES[i][
                0
            ],
            "previsao_contratual": f"PREVISÃO CONTRATUAL {i}",
        }
        for i in range(len(ConferenciaIndividualPorAlimento.OCORRENCIA_CHOICES))
    ]
    objects = [baker.make("NotificacaoOcorrenciasGuia", **attrs) for attrs in data]
    return objects


@pytest.fixture
def setup_solicitacao_remessa_envio():
    data = {
        "StrCnpj": fake.bothify(text="########0001##"),  # Gera um CNPJ fictício
        "StrNumSol": fake.bothify(
            text="####################"
        ),  # Gera o número da solicitação
        "IntSeqenv": 3,
        "IntQtGuia": 3,
        "IntTotVol": 3,
        "guias": [
            {
                "StrNumGui": fake.uuid4(),  # Gera um UUID para número da guia
                "DtEntrega": fake.date(pattern="%Y-%m-%d"),  # Gera uma data
                "StrCodUni": fake.bothify(text="UNI####"),  # Gera um código de unidade
                "StrNomUni": fake.company(),  # Gera um nome de unidade
                "StrEndUni": fake.street_address(),  # Gera um endereço de unidade
                "StrNumUni": fake.building_number(),  # Gera um número de unidade
                "StrBaiUni": fake.bairro(),  # Gera um bairro
                "StrCepUni": fake.postcode(),  # Gera um CEP
                "StrCidUni": fake.city(),  # Gera uma cidade
                "StrEstUni": fake.state_abbr(),  # Gera um estado
                "StrConUni": fake.name(),  # Gera um nome de contato
                "StrTelUni": fake.phone_number(),  # Gera um telefone
                "alimentos": [
                    {
                        "StrCodSup": fake.bothify(
                            text="SUP####"
                        ),  # Gera um código de suprimento
                        "StrCodPapa": fake.bothify(
                            text="PAPA####"
                        ),  # Gera um código do PAPA
                        "StrNomAli": fake.word(),  # Gera um nome de alimento
                        "StrEmbala": fake.word(),  # Gera um tipo de embalagem
                        "IntQtdVol": str(
                            fake.random_int(min=1, max=100)
                        ),  # Gera uma quantidade
                    }
                ],
            }
        ],
    }
    return data


def dict_to_xml(tag, d):
    elem = ET.Element(tag)
    for key, val in d.items():
        if isinstance(val, list):
            for sub_elem in val:
                elem.append(dict_to_xml(key, sub_elem))
        elif isinstance(val, dict):
            elem.append(dict_to_xml(key, val))
        else:
            child = ET.Element(key)
            child.text = str(val)
            elem.append(child)
    return elem


@pytest.fixture
def setup_solicitacao_cancelamento():
    data = {
        "StrCnpj": fake.bothify(text="########0001##"),  # Gera um CNPJ fictício
        "StrNumSol": fake.bothify(
            text="####################"
        ),  # Gera o número da solicitação
        "IntSeqenv": 3,
        "IntQtGuia": 3,
        "IntTotVol": 3,
        "guias": [
            {
                "StrNumGui": fake.uuid4(),  # Gera um UUID para número da guia
                "DtEntrega": fake.date(pattern="%Y-%m-%d"),  # Gera uma data
                "StrCodUni": fake.bothify(text="UNI####"),  # Gera um código de unidade
                "StrNomUni": fake.company(),  # Gera um nome de unidade
                "StrEndUni": fake.street_address(),  # Gera um endereço de unidade
                "StrNumUni": fake.building_number(),  # Gera um número de unidade
                "StrBaiUni": fake.bairro(),  # Gera um bairro
                "StrCepUni": fake.postcode(),  # Gera um CEP
                "StrCidUni": fake.city(),  # Gera uma cidade
                "StrEstUni": fake.state_abbr(),  # Gera um estado
                "StrConUni": fake.name(),  # Gera um nome de contato
                "StrTelUni": fake.phone_number(),  # Gera um telefone
                "alimentos": [
                    {
                        "StrCodSup": fake.bothify(
                            text="SUP####"
                        ),  # Gera um código de suprimento
                        "StrCodPapa": fake.bothify(
                            text="PAPA####"
                        ),  # Gera um código do PAPA
                        "StrNomAli": fake.word(),  # Gera um nome de alimento
                        "StrEmbala": fake.word(),  # Gera um tipo de embalagem
                        "IntQtdVol": str(
                            fake.random_int(min=1, max=100)
                        ),  # Gera uma quantidade
                    }
                ],
            }
        ],
    }

    root = dict_to_xml("XmlParserSolicitacao", data)
    xml_data = ET.tostring(root, encoding="utf-8").decode("utf-8")
    return xml_data


@pytest.fixture
def setup_solicitacao_confirmar_cancelamento(solicitacao):
    data = {
        "logs": [
            {
                "descricao": fake.sentence(nb_words=6),  # Gera uma descrição aleatória
                "justificativa": fake.text(
                    max_nb_chars=50
                ),  # Gera uma justificativa aleatória
                "resposta_sim_nao": fake.boolean(),  # Gera um valor booleano
            }
        ],
        "guias": [
            {
                "alimentos": [
                    {
                        "marca": {
                            "nome": fake.company(),  # Gera um nome de marca
                        },
                        "nome": fake.word(),  # Gera o nome do alimento
                        "ativo": fake.boolean(),  # Gera um valor booleano para ativo
                        "tipo": fake.random_element(
                            elements=["E", "D", "C"]
                        ),  # Gera um tipo aleatório
                        "outras_informacoes": fake.text(
                            max_nb_chars=100
                        ),  # Gera informações adicionais
                        "tipo_listagem_protocolo": "SO_ALIMENTOS",  # Valor fixo
                    }
                ],
                "status": "AGUARDANDO_ENVIO",  # Valor fixo
                "numero_guia": fake.bothify(
                    text="####-#####"
                ),  # Gera um número de guia
                "data_entrega": fake.date(
                    pattern="%Y-%m-%d"
                ),  # Gera uma data de entrega
                "codigo_unidade": fake.bothify(
                    text="UNI###"
                ),  # Gera um código de unidade
                "nome_unidade": fake.company(),  # Gera um nome de unidade
                "endereco_unidade": fake.street_address(),  # Gera um endereço de unidade
                "numero_unidade": fake.building_number(),  # Gera um número de unidade
                "bairro_unidade": fake.city_suffix(),  # Gera um bairro
                "cep_unidade": fake.postcode(),  # Gera um CEP
                "cidade_unidade": fake.city(),  # Gera uma cidade
                "estado_unidade": fake.state_abbr(),  # Gera um estado
                "contato_unidade": fake.name(),  # Gera um nome de contato
                "telefone_unidade": fake.phone_number(),  # Gera um telefone
                "situacao": "ATIVA",  # Valor fixo
                "solicitacao": fake.random_int(
                    min=1, max=1000
                ),  # Gera um número aleatório para solicitação
                "escola": fake.random_int(
                    min=1, max=1000
                ),  # Gera um número aleatório para escola
                "notificacao": fake.random_int(
                    min=1, max=1000
                ),  # Gera um número aleatório para notificação
            }
        ],
        "status": "AGUARDANDO_ENVIO",  # Valor fixo
        "cnpj": fake.bothify(text="########0001##"),  # Gera um CNPJ fictício
        "numero_requisicao": solicitacao.numero_solicitacao,  # Gera um número de solicitação
        "quantidade_total_guias": fake.random_int(
            min=1, max=100
        ),  # Gera uma quantidade total de guias
        "sequencia_envio": fake.random_int(
            min=1, max=100
        ),  # Gera uma sequência de envio
        "situacao": "ATIVA",  # Valor fixo
        "distribuidor": fake.random_int(
            min=1, max=1000
        ),  # Gera um número aleatório para distribuidor
    }
    return data


@pytest.fixture
def setup_solicitacao_confirmar_cancelamentos_sem_numero_requisicao(
    setup_solicitacao_confirmar_cancelamento,
):
    _ = setup_solicitacao_confirmar_cancelamento.pop("numero_requisicao")
    return setup_solicitacao_confirmar_cancelamento


@pytest.fixture
def setup_solicitacao_confirmar_cancelamentos_sem_guia(
    setup_solicitacao_confirmar_cancelamento,
):
    _ = setup_solicitacao_confirmar_cancelamento.pop("guias")
    return setup_solicitacao_confirmar_cancelamento


@pytest.fixture
def token_valido():
    usuario = baker.make("Usuario", username="testuser", is_active=True)
    token = baker.make("Token", user=usuario, key="oWsAcessoModel")
    model = oWsAcessoModel(StrId="123456", StrToken="oWsAcessoModel")

    return usuario, token, model


@pytest.fixture
def fake_alimento():
    return {
        "StrCodSup": fake.unique.random_number(digits=5, fix_len=True),
        "StrCodPapa": fake.bothify(text="PAPA####"),
        "StrNomAli": fake.word(),
        "StrTpEmbala": fake.word(),
        "StrQtEmbala": str(fake.random_int(min=1, max=100)),
        "StrDescEmbala": fake.sentence(),
        "StrPesoEmbala": str(
            fake.pydecimal(left_digits=3, right_digits=2, positive=True)
        ),
        "StrUnMedEmbala": fake.random_element(elements=["kg", "g", "ml", "L"]),
    }


@pytest.fixture
def soup_alimento(fake_alimento):
    return Alimento(**fake_alimento)


@pytest.fixture
def fake_guia(soup_alimento):
    return {
        "StrNumGui": fake.random_int(min=1000, max=9999),
        "DtEntrega": fake.date_object(),
        "StrCodUni": fake.bothify(text="UNI####"),
        "StrNomUni": fake.company(),
        "StrEndUni": fake.street_address(),
        "StrNumUni": str(fake.random_int(min=1, max=1000)),
        "StrBaiUni": fake.city_suffix(),
        "StrCepUni": fake.postcode(),
        "StrCidUni": fake.city(),
        "StrEstUni": fake.state_abbr(),
        "StrConUni": fake.name(),
        "StrTelUni": fake.phone_number(),
        "alimentos": [soup_alimento],
    }


@pytest.fixture
def soup_guia(fake_guia):
    return Guia(**fake_guia)


@pytest.fixture
def fake_arq_solicitacao_mod(soup_guia):
    return {
        "StrCnpj": fake.cnpj(),
        "StrNumSol": fake.random_int(min=1000, max=9999),
        "IntSeqenv": fake.random_int(min=1, max=10),
        "IntTotVol": fake.random_int(min=1, max=50),
        "IntQtGuia": 1,
        "guias": [soup_guia],
    }


@pytest.fixture
def soup_arq_solicitacao_mod(fake_arq_solicitacao_mod):
    return ArqSolicitacaoMOD(**fake_arq_solicitacao_mod)


@pytest.fixture
def soup_guican():
    return GuiCan(StrNumGui=fake.random_int(min=1000, max=9999))


@pytest.fixture
def fake_arq_cancelamento(fake_arq_solicitacao_mod):
    guia = fake_arq_solicitacao_mod["guias"][0]
    return {
        "StrCnpj": fake_arq_solicitacao_mod["StrCnpj"],
        "StrNumSol": fake_arq_solicitacao_mod["StrNumSol"],
        "IntSeqenv": fake_arq_solicitacao_mod["IntSeqenv"],
        "IntQtGuia": fake_arq_solicitacao_mod["IntQtGuia"],
        "guias": [GuiCan(StrNumGui=guia.StrNumGui)],
    }


@pytest.fixture
def soup_arq_cancelamento(fake_arq_cancelamento):
    return ArqCancelamento(**fake_arq_cancelamento)


@pytest.fixture
def terceirizada_soup():
    cnpj = fake.cnpj().replace(".", "").replace("/", "").replace("-", "")
    return baker.make(
        "Terceirizada", cnpj=cnpj, tipo_servico=Terceirizada.DISTRIBUIDOR_ARMAZEM
    )


@pytest.fixture
def arq_solicitacao_mod(fake_arq_solicitacao_mod, soup_guia, terceirizada_soup):
    codigo_codae = fake.random_int(min=1000, max=9999)
    soup_guia.StrCodUni = codigo_codae
    baker.make("Escola", codigo_codae=codigo_codae)
    arquivo_solicitacao = ArqSolicitacaoMOD(
        StrCnpj=terceirizada_soup.cnpj,
        StrNumSol=fake_arq_solicitacao_mod.get("StrNumSol"),
        IntSeqenv=fake_arq_solicitacao_mod.get("IntSeqenv"),
        IntTotVol=fake_arq_solicitacao_mod.get("IntTotVol"),
        guias=[soup_guia],
        IntQtGuia=fake_arq_solicitacao_mod.get("IntQtGuia"),
    )
    return arquivo_solicitacao


@pytest.fixture
def arq_cancelamento_mod(soup_arq_cancelamento, solicitacao):
    solicitacao.numero_solicitacao = soup_arq_cancelamento.StrNumSol
    solicitacao.save()
    return soup_arq_cancelamento


@pytest.fixture
def soup_solicitacao_remessa(arq_solicitacao_mod):
    data = get_object_as_dict(arq_solicitacao_mod)
    guias = data.pop("guias", [])
    data.pop("IntTotVol", None)
    return SolicitacaoRemessa.objects.create_solicitacao(**data), guias


@pytest.fixture
def dicioanario_alimentos(soup_solicitacao_remessa):
    solicitacao, guias = soup_solicitacao_remessa
    guia = guias[0]
    alimentos_data = guia.pop("alimentos", [])[0]
    guia_obj = Guia().build_guia_obj(guia, solicitacao)
    escola = models.Escola.objects.get(codigo_codae=guia_obj.codigo_unidade)
    guia_obj.escola = escola
    guia_obj.save()
    alimentos_data["guia"] = guia_obj
    return alimentos_data


@pytest.fixture
def mock_ctx():
    class MockContext:
        out_string = [b"<tns:Test>soap11env:Body</tns:Test>"]

    ctx = MockContext()
    return ctx
