import xml.etree.ElementTree as ET
from datetime import datetime

import pytest
from faker import Faker
from model_mommy import mommy

from sme_sigpae_api.logistica.api.soup.models import (
    Alimento,
    ArqCancelamento,
    ArqSolicitacaoMOD,
    Guia,
    GuiCan,
    oWsAcessoModel,
)
from sme_sigpae_api.terceirizada.models import Terceirizada

from ...escola import models
from ..models.guia import ConferenciaIndividualPorAlimento

fake = Faker("pt_BR")
Faker.seed(420)


@pytest.fixture
def distribuidor():
    return mommy.make(
        "Usuario", email="distribuidor@admin.com", cpf="12345678910", is_superuser=True
    )


@pytest.fixture
def terceirizada():
    return mommy.make(
        "Terceirizada",
        contatos=[mommy.make("dados_comuns.Contato")],
        make_m2m=True,
        nome_fantasia="Alimentos SA",
    )


@pytest.fixture
def solicitacao(terceirizada):
    return mommy.make(
        "SolicitacaoRemessa",
        cnpj="12345678901234",
        numero_solicitacao="559890",
        sequencia_envio=1212,
        quantidade_total_guias=2,
        distribuidor=terceirizada,
    )


@pytest.fixture
def lote():
    return mommy.make(models.Lote, nome="lote", iniciais="lt")


@pytest.fixture
def escola(lote):
    return mommy.make(
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
    return mommy.make(
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
    return mommy.make(
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
    return mommy.make(
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
    return mommy.make(
        "logistica.Alimento",
        guia=guia_com_escola_client_autenticado,
        codigo_suprimento="123456",
        codigo_papa="2345",
        nome_alimento="PATINHO",
    )


@pytest.fixture
def embalagem(alimento):
    return mommy.make(
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
    return mommy.make(
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
    return mommy.make(
        "ConferenciaGuia",
        guia=guia_com_escola_client_autenticado,
        data_recebimento=datetime.now(),
        hora_recebimento=datetime.now().time(),
        nome_motorista="José da Silva",
        placa_veiculo="77AB75A",
    )


@pytest.fixture
def conferencia_guia_normal(guia):
    return mommy.make(
        "ConferenciaGuia",
        guia=guia,
        data_recebimento=datetime.now(),
        hora_recebimento=datetime.now().time(),
        nome_motorista="José da Silva",
        placa_veiculo="77AB75A",
    )


@pytest.fixture
def reposicao_guia(guia):
    return mommy.make(
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
    return mommy.make(
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
    return mommy.make(
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
    return mommy.make(
        "LogSolicitacaoDeCancelamentoPeloPapa",
        requisicao=solicitacao,
        guias=["21236", "235264"],
        sequencia_envio="123456",
        foi_confirmada=False,
    )


@pytest.fixture
def notificacao_ocorrencia(terceirizada):
    notificacao = mommy.make(
        "NotificacaoOcorrenciasGuia",
        numero="1234567890",
        processo_sei="9876543210",
        empresa=terceirizada,
    )

    mommy.make(
        "PrevisaoContratualNotificacao",
        notificacao=notificacao,
        motivo_ocorrencia=ConferenciaIndividualPorAlimento.OCORRENCIA_ATRASO_ENTREGA,
        previsao_contratual="Previsao contratual teste 1",
    )

    mommy.make(
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
    objects = [mommy.make("NotificacaoOcorrenciasGuia", **attrs) for attrs in data]
    return objects


@pytest.fixture
def previsao_contratual(notificacao_ocorrencia):
    return mommy.make(
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
    objects = [mommy.make("NotificacaoOcorrenciasGuia", **attrs) for attrs in data]
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
    usuario = mommy.make("Usuario", username="testuser", is_active=True)
    token = mommy.make("Token", user=usuario, key="oWsAcessoModel")
    model = oWsAcessoModel(StrId="123456", StrToken="oWsAcessoModel")

    return usuario, token, model


@pytest.fixture
def fake_alimento():
    StrCodSup = fake.unique.random_number(digits=5, fix_len=True)
    StrCodPapa = fake.bothify(text="PAPA####")
    StrNomAli = fake.word()
    StrTpEmbala = fake.word()
    StrQtEmbala = str(fake.random_int(min=1, max=100))
    StrDescEmbala = fake.sentence()
    StrPesoEmbala = str(fake.pydecimal(left_digits=3, right_digits=2, positive=True))
    StrUnMedEmbala = fake.random_element(elements=["kg", "g", "ml", "L"])
    return {
        "StrCodSup": StrCodSup,
        "StrCodPapa": StrCodPapa,
        "StrNomAli": StrNomAli,
        "StrTpEmbala": StrTpEmbala,
        "StrQtEmbala": StrQtEmbala,
        "StrDescEmbala": StrDescEmbala,
        "StrPesoEmbala": StrPesoEmbala,
        "StrUnMedEmbala": StrUnMedEmbala,
    }


@pytest.fixture
def soup_alimento(fake_alimento):
    alimento = Alimento(
        StrCodSup=fake_alimento.get("StrCodSup"),
        StrCodPapa=fake_alimento.get("StrCodPapa"),
        StrNomAli=fake_alimento.get("StrNomAli"),
        StrTpEmbala=fake_alimento.get("StrTpEmbala"),
        StrQtEmbala=fake_alimento.get("StrQtEmbala"),
        StrDescEmbala=fake_alimento.get("StrDescEmbala"),
        StrPesoEmbala=fake_alimento.get("StrPesoEmbala"),
        StrUnMedEmbala=fake_alimento.get("StrUnMedEmbala"),
    )
    return alimento


@pytest.fixture
def fake_guia(soup_alimento):
    StrNumGui = fake.random_int(min=1000, max=9999)
    DtEntrega = fake.date_object()
    StrCodUni = fake.bothify(text="UNI####")
    StrNomUni = fake.company()
    StrEndUni = fake.street_address()
    StrNumUni = str(fake.random_int(min=1, max=1000))
    StrBaiUni = fake.city()
    StrCepUni = fake.postcode()
    StrCidUni = fake.city()
    StrEstUni = fake.state_abbr()
    StrConUni = fake.name()
    StrTelUni = fake.phone_number()
    alimentos = [soup_alimento for _ in range(3)]
    return {
        "StrNumGui": StrNumGui,
        "DtEntrega": DtEntrega,
        "StrCodUni": StrCodUni,
        "StrNomUni": StrNomUni,
        "StrEndUni": StrEndUni,
        "StrNumUni": StrNumUni,
        "StrBaiUni": StrBaiUni,
        "StrCepUni": StrCepUni,
        "StrCidUni": StrCidUni,
        "StrEstUni": StrEstUni,
        "StrConUni": StrConUni,
        "StrTelUni": StrTelUni,
        "alimentos": alimentos,
    }


@pytest.fixture
def soup_guia(fake_guia):
    guia = Guia(
        StrNumGui=fake_guia.get("StrNumGui"),
        DtEntrega=fake_guia.get("DtEntrega"),
        StrCodUni=fake_guia.get("StrCodUni"),
        StrNomUni=fake_guia.get("StrNomUni"),
        StrEndUni=fake_guia.get("StrEndUni"),
        StrNumUni=fake_guia.get("StrNumUni"),
        StrBaiUni=fake_guia.get("StrBaiUni"),
        StrCepUni=fake_guia.get("StrCepUni"),
        StrCidUni=fake_guia.get("StrCidUni"),
        StrEstUni=fake_guia.get("StrEstUni"),
        StrConUni=fake_guia.get("StrConUni"),
        StrTelUni=fake_guia.get("StrTelUni"),
        alimentos=fake_guia.get("alimentos"),
    )
    return guia


@pytest.fixture
def fake_arq_solicitacao_mod(soup_guia):
    guias = [soup_guia for _ in range(3)]
    StrCnpj = fake.cnpj()
    StrNumSol = fake.random_int(min=1000, max=9999)
    IntSeqenv = fake.random_int(min=1, max=10)
    IntTotVol = fake.random_int(min=1, max=50)
    guias = guias
    IntQtGuia = len(guias)

    return {
        "StrCnpj": StrCnpj,
        "StrNumSol": StrNumSol,
        "IntSeqenv": IntSeqenv,
        "IntTotVol": IntTotVol,
        "guias": guias,
        "IntQtGuia": IntQtGuia,
    }


@pytest.fixture
def soup_arq_solicitacao_mod(fake_arq_solicitacao_mod):
    arquivo_solicitacao = ArqSolicitacaoMOD(
        StrCnpj=fake_arq_solicitacao_mod.get("StrCnpj"),
        StrNumSol=fake_arq_solicitacao_mod.get("StrNumSol"),
        IntSeqenv=fake_arq_solicitacao_mod.get("IntSeqenv"),
        IntTotVol=fake_arq_solicitacao_mod.get("IntTotVol"),
        guias=fake_arq_solicitacao_mod.get("guias"),
        IntQtGuia=fake_arq_solicitacao_mod.get("IntQtGuia"),
    )
    return arquivo_solicitacao


@pytest.fixture
def soup_guican():
    return GuiCan(StrNumGui=fake.random_int(min=1000, max=9999))


@pytest.fixture
def fake_arq_cancelamento(soup_guican):
    guias = [soup_guican for _ in range(3)]
    StrCnpj = fake.cnpj()
    StrNumSol = fake.random_int(min=1000, max=9999)
    IntSeqenv = fake.random_int(min=1, max=10)
    guias = guias
    IntQtGuia = len(guias)

    return {
        "StrCnpj": StrCnpj,
        "StrNumSol": StrNumSol,
        "IntSeqenv": IntSeqenv,
        "guias": guias,
        "IntQtGuia": IntQtGuia,
    }


@pytest.fixture
def soup_arq_cancelamento(fake_arq_cancelamento):
    arquivo_cancelamento = ArqCancelamento(
        StrCnpj=fake_arq_cancelamento.get("StrCnpj"),
        StrNumSol=fake_arq_cancelamento.get("StrNumSol"),
        IntSeqenv=fake_arq_cancelamento.get("IntSeqenv"),
        guias=fake_arq_cancelamento.get("guias"),
        IntQtGuia=fake_arq_cancelamento.get("IntQtGuia"),
    )
    return arquivo_cancelamento


@pytest.fixture
def terceirizada_soup():
    cnpj = fake.cnpj().replace(".", "").replace("/", "").replace("-", "")
    return mommy.make(
        "Terceirizada", cnpj=cnpj, tipo_servico=Terceirizada.DISTRIBUIDOR_ARMAZEM
    )


@pytest.fixture
def arq_solicitacao_mod(fake_arq_solicitacao_mod, soup_guia, terceirizada_soup):
    codigo_codae = fake.random_int(min=1000, max=9999)
    soup_guia.StrCodUni = codigo_codae

    arquivo_solicitacao = ArqSolicitacaoMOD(
        StrCnpj=terceirizada_soup.cnpj,
        StrNumSol=fake_arq_solicitacao_mod.get("StrNumSol"),
        IntSeqenv=fake_arq_solicitacao_mod.get("IntSeqenv"),
        IntTotVol=fake_arq_solicitacao_mod.get("IntTotVol"),
        guias=[soup_guia],
        IntQtGuia=fake_arq_solicitacao_mod.get("IntQtGuia"),
    )

    escola = mommy.make("Escola", codigo_codae=codigo_codae)
    return arquivo_solicitacao
