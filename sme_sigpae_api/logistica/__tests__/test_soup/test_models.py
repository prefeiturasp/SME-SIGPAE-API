from faker import Faker
from spyne.model.primitive import String

from sme_sigpae_api.logistica.api.soup.models import (
    NS,
    Alimento,
    SoapResponse,
    oWsAcessoModel,
)

fake = Faker("pt_BR")


def test_soap_response():
    response = SoapResponse(str_status="200", str_menssagem="Operação bem-sucedida")
    assert response.StrStatus == "200"
    assert response.StrMensagem == "Operação bem-sucedida"
    assert isinstance(response.StrStatus, str)
    assert isinstance(response.StrMensagem, str)


def test_soap_response_atributos_da_classe():
    assert SoapResponse.StrStatus is String
    assert SoapResponse.StrMensagem is String
    assert SoapResponse.__namespace__ == NS
    assert SoapResponse.__type_name__ == "codresMOD"


def test_ows_acesso_model():
    response = oWsAcessoModel(StrId="123456", StrToken="oWsAcessoModel")
    assert response.StrId == "123456"
    assert response.StrToken == "oWsAcessoModel"
    assert isinstance(response.StrId, str)
    assert isinstance(response.StrToken, str)


def test_ows_acesso_model_atributos_da_classe():
    assert oWsAcessoModel.StrId is String
    assert oWsAcessoModel.StrToken is String
    assert oWsAcessoModel.__namespace__ == NS
    assert oWsAcessoModel.__type_name__ == "acessMOD"


def test_alimento():
    StrCodSup = fake.unique.random_number(digits=5, fix_len=True)
    StrCodPapa = fake.unique.random_number(digits=6, fix_len=True)
    StrNomAli = fake.word()
    StrTpEmbala = fake.word()
    StrQtEmbala = fake.random_int(min=1, max=100)
    StrDescEmbala = fake.sentence()
    StrPesoEmbala = fake.random_number(digits=3)
    StrUnMedEmbala = fake.random_element(elements=["kg", "g", "ml", "L"])

    response = Alimento(
        StrCodSup=StrCodSup,
        StrCodPapa=StrCodPapa,
        StrNomAli=StrNomAli,
        StrTpEmbala=StrTpEmbala,
        StrQtEmbala=StrQtEmbala,
        StrDescEmbala=StrDescEmbala,
        StrPesoEmbala=StrPesoEmbala,
        StrUnMedEmbala=StrUnMedEmbala,
    )
    assert isinstance(response.StrCodSup, str)
    assert isinstance(response.StrNomAli, str)
    assert isinstance(response.StrTpEmbala, str)
    assert isinstance(response.StrQtEmbala, str)  # Pode ser string ou int
    assert isinstance(response.StrDescEmbala, str)
    assert isinstance(response.StrPesoEmbala, str)  # Pode ser string ou int
    assert isinstance(response.StrUnMedEmbala, str)
