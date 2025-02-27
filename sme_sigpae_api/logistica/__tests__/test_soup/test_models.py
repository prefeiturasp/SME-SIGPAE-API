import datetime

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.db import DataError, IntegrityError
from faker import Faker
from spyne.model.primitive import Date, Integer, String
from spyne.util.dictdoc import get_object_as_dict

from sme_sigpae_api.dados_comuns.fluxo_status import (
    GuiaRemessaWorkFlow,
    SolicitacaoRemessaWorkFlow,
)
from sme_sigpae_api.escola.models import Escola
from sme_sigpae_api.logistica.api.soup.models import (
    NS,
    Alimento,
    ArqCancelamento,
    ArqSolicitacaoMOD,
    ArrayOfAlimento,
    ArrayOfGuia,
    ArrayOfGuiCan,
    Guia,
    GuiCan,
    SoapResponse,
    oWsAcessoModel,
)
from sme_sigpae_api.logistica.models import Guia as model_guia
from sme_sigpae_api.logistica.models.solicitacao import SolicitacaoRemessa

fake = Faker("pt_BR")
pytestmark = pytest.mark.django_db


def test_soap_response():
    response = SoapResponse(str_status="200", str_menssagem="Operação bem-sucedida")
    assert response.StrStatus == "200"
    assert isinstance(response.StrStatus, str)

    assert response.StrMensagem == "Operação bem-sucedida"
    assert isinstance(response.StrMensagem, str)


def test_soap_response_atributos_da_classe():
    assert SoapResponse.StrStatus is String
    assert SoapResponse.StrMensagem is String

    assert SoapResponse.__namespace__ == NS
    assert SoapResponse.__type_name__ == "codresMOD"


def test_ows_acesso_model():
    response = oWsAcessoModel(StrId="123456", StrToken="oWsAcessoModel")
    assert response.StrId == "123456"
    assert isinstance(response.StrId, str)

    assert response.StrToken == "oWsAcessoModel"
    assert isinstance(response.StrToken, str)


def test_ows_acesso_model_atributos_da_classe():
    assert oWsAcessoModel.StrId is String
    assert oWsAcessoModel.StrToken is String

    assert oWsAcessoModel.__namespace__ == NS
    assert oWsAcessoModel.__type_name__ == "acessMOD"


def test_alimento(fake_alimento, soup_alimento):
    assert soup_alimento.StrCodSup == fake_alimento.get("StrCodSup")
    assert isinstance(soup_alimento.StrCodSup, int)

    assert soup_alimento.StrCodPapa == fake_alimento.get("StrCodPapa")
    assert isinstance(soup_alimento.StrCodPapa, str)

    assert soup_alimento.StrNomAli == fake_alimento.get("StrNomAli")
    assert isinstance(soup_alimento.StrNomAli, str)

    assert soup_alimento.StrTpEmbala == fake_alimento.get("StrTpEmbala")
    assert isinstance(soup_alimento.StrTpEmbala, str)

    assert soup_alimento.StrQtEmbala == fake_alimento.get("StrQtEmbala")
    assert isinstance(soup_alimento.StrQtEmbala, str)

    assert soup_alimento.StrDescEmbala == fake_alimento.get("StrDescEmbala")
    assert isinstance(soup_alimento.StrDescEmbala, str)

    assert soup_alimento.StrPesoEmbala == fake_alimento.get("StrPesoEmbala")
    assert isinstance(soup_alimento.StrPesoEmbala, str)

    assert soup_alimento.StrUnMedEmbala == fake_alimento.get("StrUnMedEmbala")
    assert isinstance(soup_alimento.StrUnMedEmbala, str)


def test_alimento_atributos_da_classe():
    assert Alimento.StrCodSup is String
    assert Alimento.StrCodPapa is String
    assert Alimento.StrNomAli is String
    assert Alimento.StrTpEmbala is String
    assert Alimento.StrQtEmbala is String
    assert Alimento.StrDescEmbala is String
    assert Alimento.StrPesoEmbala is String
    assert Alimento.StrUnMedEmbala is String

    assert Alimento.__namespace__ == NS
    assert Alimento.__type_name__ == "Alimento"


def test_gui_can():
    response = GuiCan(StrNumGui=200)
    assert response.StrNumGui == 200
    assert isinstance(response.StrNumGui, int)


def test_gui_can_atributos_da_classe():
    assert GuiCan.StrNumGui is Integer
    assert GuiCan.__namespace__ == NS


def test_guia(fake_guia, soup_guia):
    assert soup_guia.StrNumGui == fake_guia.get("StrNumGui")
    assert isinstance(soup_guia.StrNumGui, int)

    assert soup_guia.DtEntrega == fake_guia.get("DtEntrega")
    assert isinstance(soup_guia.DtEntrega, datetime.date)

    assert soup_guia.StrCodUni == fake_guia.get("StrCodUni")
    assert isinstance(soup_guia.StrCodUni, str)

    assert soup_guia.StrNomUni == fake_guia.get("StrNomUni")
    assert isinstance(soup_guia.StrNomUni, str)

    assert soup_guia.StrEndUni == fake_guia.get("StrEndUni")
    assert isinstance(soup_guia.StrEndUni, str)

    assert soup_guia.StrNumUni == fake_guia.get("StrNumUni")
    assert isinstance(soup_guia.StrNumUni, str)

    assert soup_guia.StrBaiUni == fake_guia.get("StrBaiUni")
    assert isinstance(soup_guia.StrBaiUni, str)

    assert soup_guia.StrCepUni == fake_guia.get("StrCepUni")
    assert isinstance(soup_guia.StrCepUni, str)

    assert soup_guia.StrCidUni == fake_guia.get("StrCidUni")
    assert isinstance(soup_guia.StrCidUni, str)

    assert soup_guia.StrEstUni == fake_guia.get("StrEstUni")
    assert isinstance(soup_guia.StrEstUni, str)

    assert soup_guia.StrConUni == fake_guia.get("StrConUni")
    assert isinstance(soup_guia.StrConUni, str)

    assert soup_guia.StrTelUni == fake_guia.get("StrTelUni")
    assert isinstance(soup_guia.StrTelUni, str)

    assert soup_guia.alimentos == fake_guia.get("alimentos")
    assert isinstance(soup_guia.alimentos, list)
    assert len(soup_guia.alimentos) == 1


def test_guia_atributos_da_classe():
    assert Guia.StrNumGui is Integer
    assert Guia.DtEntrega is Date
    assert Guia.StrCodUni is String
    assert Guia.StrNomUni is String
    assert Guia.StrEndUni is String
    assert Guia.StrNumUni is String
    assert Guia.StrBaiUni is String
    assert Guia.StrCepUni is String
    assert Guia.StrCidUni is String
    assert Guia.StrEstUni is String
    assert Guia.StrConUni is String
    assert Guia.StrTelUni is String
    assert Guia.alimentos is ArrayOfAlimento

    assert GuiCan.__namespace__ == NS


def test_arq_solicitacao_mod(fake_arq_solicitacao_mod, soup_arq_solicitacao_mod):
    assert soup_arq_solicitacao_mod.StrCnpj == fake_arq_solicitacao_mod.get("StrCnpj")
    assert isinstance(soup_arq_solicitacao_mod.StrCnpj, str)

    assert soup_arq_solicitacao_mod.StrNumSol == fake_arq_solicitacao_mod.get(
        "StrNumSol"
    )
    assert isinstance(soup_arq_solicitacao_mod.StrNumSol, int)

    assert soup_arq_solicitacao_mod.IntSeqenv == fake_arq_solicitacao_mod.get(
        "IntSeqenv"
    )
    assert isinstance(soup_arq_solicitacao_mod.IntSeqenv, int)

    assert soup_arq_solicitacao_mod.IntTotVol == fake_arq_solicitacao_mod.get(
        "IntTotVol"
    )
    assert isinstance(soup_arq_solicitacao_mod.IntTotVol, int)

    assert soup_arq_solicitacao_mod.guias == fake_arq_solicitacao_mod.get("guias")
    assert isinstance(soup_arq_solicitacao_mod.guias, list)
    assert len(soup_arq_solicitacao_mod.guias) == 1

    assert soup_arq_solicitacao_mod.IntQtGuia == fake_arq_solicitacao_mod.get(
        "IntQtGuia"
    )
    assert isinstance(soup_arq_solicitacao_mod.IntQtGuia, int)


def test_arq_solicitacao_mod_atributos_da_classe():
    assert ArqSolicitacaoMOD.StrCnpj is String
    assert ArqSolicitacaoMOD.StrNumSol is Integer
    assert ArqSolicitacaoMOD.IntSeqenv is Integer
    assert ArqSolicitacaoMOD.IntQtGuia is Integer
    assert ArqSolicitacaoMOD.IntTotVol is Integer
    assert ArqSolicitacaoMOD.guias is ArrayOfGuia

    assert ArqSolicitacaoMOD.__namespace__ == NS
    assert ArqSolicitacaoMOD.__type_name__ == "SolicitacaoMOD"


def test_arq_cancelamento_mod(fake_arq_cancelamento, soup_arq_cancelamento):
    assert soup_arq_cancelamento.StrCnpj == fake_arq_cancelamento.get("StrCnpj")
    assert isinstance(soup_arq_cancelamento.StrCnpj, str)

    assert soup_arq_cancelamento.StrNumSol == fake_arq_cancelamento.get("StrNumSol")
    assert isinstance(soup_arq_cancelamento.StrNumSol, int)

    assert soup_arq_cancelamento.IntSeqenv == fake_arq_cancelamento.get("IntSeqenv")
    assert isinstance(soup_arq_cancelamento.IntSeqenv, int)

    assert soup_arq_cancelamento.guias == fake_arq_cancelamento.get("guias")
    assert isinstance(soup_arq_cancelamento.guias, list)
    assert len(soup_arq_cancelamento.guias) == 1

    assert soup_arq_cancelamento.IntQtGuia == fake_arq_cancelamento.get("IntQtGuia")
    assert isinstance(soup_arq_cancelamento.IntQtGuia, int)


def test_arq_cancelamento_atributos_da_classe():
    assert ArqCancelamento.StrCnpj is String
    assert ArqCancelamento.StrNumSol is Integer
    assert ArqCancelamento.IntSeqenv is Integer
    assert ArqCancelamento.IntQtGuia is Integer
    assert ArqCancelamento.guias is ArrayOfGuiCan

    assert ArqCancelamento.__namespace__ == NS
    assert ArqCancelamento.__type_name__ == "CancelamentoMOD"


def test_arq_solicitacao_mod_create(arq_solicitacao_mod, terceirizada_soup):
    assert SolicitacaoRemessa.objects.count() == 0
    response = arq_solicitacao_mod.create()
    assert response.situacao == SolicitacaoRemessa.ATIVA
    assert response.status == SolicitacaoRemessaWorkFlow.AGUARDANDO_ENVIO
    assert response.distribuidor == terceirizada_soup
    assert response.cnpj == arq_solicitacao_mod.StrCnpj
    assert SolicitacaoRemessa.objects.count() == 1


def test_arq_solicitacao_mod_create_sem_distribuidor(soup_arq_solicitacao_mod):
    with pytest.raises(
        ObjectDoesNotExist, match="Não existe distribuidor cadastrado com esse cnpj"
    ):
        soup_arq_solicitacao_mod.create()


def test_arq_solicitacao_mod_create_duplicada(arq_solicitacao_mod):
    arq_solicitacao_mod.create()
    with pytest.raises(IntegrityError, match="Solicitação duplicada:"):
        arq_solicitacao_mod.create()


def test_guia_create_many(soup_solicitacao_remessa):
    solicitacao, guias = soup_solicitacao_remessa
    guias_obj_list = Guia().create_many(guias, solicitacao)
    assert len(guias_obj_list) == 1
    guia = guias_obj_list[0]
    assert guia.situacao == model_guia.ATIVA
    assert guia.status == GuiaRemessaWorkFlow.AGUARDANDO_ENVIO
    assert guia.codigo_unidade == guias[0].get("StrCodUni")


def test_guia_create_many_sem_escola(soup_solicitacao_remessa):
    solicitacao, guias = soup_solicitacao_remessa
    guias[0]["StrCodUni"] = "naoExiste"
    guias_obj_list = Guia().create_many(guias, solicitacao)
    assert len(guias_obj_list) == 1
    guia = guias_obj_list[0]
    assert guia.situacao == model_guia.ATIVA
    assert guia.status == GuiaRemessaWorkFlow.AGUARDANDO_ENVIO
    assert guia.codigo_unidade == guias[0].get("StrCodUni")
    assert guia.escola is None


def test_guia_create_many_duplicada(soup_solicitacao_remessa):
    solicitacao, guias = soup_solicitacao_remessa
    Guia().create_many(guias, solicitacao)
    with pytest.raises(IntegrityError, match="Guia duplicada:"):
        Guia().create_many(guias, solicitacao)


def test_guia_build_guia_obj(soup_solicitacao_remessa):
    solicitacao, guias = soup_solicitacao_remessa
    guia = guias[0]
    guia_obj = Guia().build_guia_obj(guia, solicitacao)
    assert guia_obj.situacao == model_guia.ATIVA
    assert guia_obj.status == GuiaRemessaWorkFlow.AGUARDANDO_ENVIO
    assert guia_obj.codigo_unidade == guia.get("StrCodUni")


def test_alimento_create_many(dicioanario_alimentos):
    lista_alimentos = Alimento().create_many([dicioanario_alimentos])
    assert isinstance(lista_alimentos, list)
    assert len(lista_alimentos) == 1
    alimento = lista_alimentos[0]
    assert alimento.guia == dicioanario_alimentos.get("guia")
    assert alimento.codigo_papa == dicioanario_alimentos.get("StrCodPapa")
    assert alimento.nome_alimento == dicioanario_alimentos.get("StrNomAli")
    assert alimento.codigo_suprimento == dicioanario_alimentos.get("StrCodSup")


def test_build_alimento_obj(dicioanario_alimentos):
    alimento = Alimento().build_alimento_obj(dicioanario_alimentos)
    assert alimento.guia == dicioanario_alimentos.get("guia")
    assert alimento.codigo_papa == dicioanario_alimentos.get("StrCodPapa")
    assert alimento.nome_alimento == dicioanario_alimentos.get("StrNomAli")
    assert alimento.codigo_suprimento == dicioanario_alimentos.get("StrCodSup")


def test_create_embalagens(dicioanario_alimentos):
    alimento_obj = Alimento().build_alimento_obj(dicioanario_alimentos)
    alimento_obj.save()
    dicioanario_alimentos["alimento"] = alimento_obj

    lista_embalagem = Alimento().create_embalagens([dicioanario_alimentos])
    assert isinstance(lista_embalagem, list)
    assert len(lista_embalagem) == 1
    embalagem = lista_embalagem[0]
    assert embalagem.alimento == alimento_obj
    assert embalagem.descricao_embalagem == dicioanario_alimentos.get("StrDescEmbala")
    assert embalagem.capacidade_embalagem == float(
        dicioanario_alimentos.get("StrPesoEmbala")
    )
    assert embalagem.unidade_medida == dicioanario_alimentos.get("StrUnMedEmbala")
    assert embalagem.qtd_volume == dicioanario_alimentos.get("StrQtEmbala")


def test_build_embalagem_obj(dicioanario_alimentos):
    alimento_obj = Alimento().build_alimento_obj(dicioanario_alimentos)
    alimento_obj.save()
    dicioanario_alimentos["alimento"] = alimento_obj

    embalagem = Alimento().build_embalagem_obj(dicioanario_alimentos)
    assert embalagem.alimento == alimento_obj
    assert embalagem.descricao_embalagem == dicioanario_alimentos.get("StrDescEmbala")
    assert embalagem.capacidade_embalagem == float(
        dicioanario_alimentos.get("StrPesoEmbala")
    )
    assert embalagem.unidade_medida == dicioanario_alimentos.get("StrUnMedEmbala")
    assert embalagem.qtd_volume == dicioanario_alimentos.get("StrQtEmbala")
