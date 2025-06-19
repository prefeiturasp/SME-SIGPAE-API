import environ
from django.core import exceptions
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from spyne.model.complex import Array, ComplexModel
from spyne.model.primitive import Date, Integer, String
from spyne.util.dictdoc import get_object_as_dict

from ....dados_comuns.fluxo_status import GuiaRemessaWorkFlow as GuiaStatus
from ....dados_comuns.fluxo_status import SolicitacaoRemessaWorkFlow as StatusReq
from ....dados_comuns.models import LogSolicitacoesUsuario
from ....escola.models import Escola
from ....terceirizada.models import Terceirizada
from ...models.alimento import Alimento as AlimentoModel  # noqa I001
from ...models.alimento import Embalagem
from ...models.guia import Guia as GuiaModel
from ...models.solicitacao import (
    LogSolicitacaoDeCancelamentoPeloPapa,
    SolicitacaoRemessa,
)

env = environ.Env()

NS = f'{env("DJANGO_XMLNS")}'


class Alimento(ComplexModel):
    __namespace__ = NS
    __type_name__ = "Alimento"
    StrCodSup = String
    StrCodPapa = String
    StrNomAli = String
    StrTpEmbala = String
    StrQtEmbala = String
    StrDescEmbala = String
    StrPesoEmbala = String
    StrUnMedEmbala = String

    def build_alimento_obj(self, data):
        alimento_dict = {
            "codigo_suprimento": data.get("StrCodSup"),
            "codigo_papa": data.get("StrCodPapa"),
            "nome_alimento": data.get("StrNomAli"),
            "guia": data.get("guia"),
        }
        return AlimentoModel(**alimento_dict)

    def build_embalagem_obj(self, data):
        embalagem_dict = {
            "alimento": data.get("alimento"),
            "descricao_embalagem": data.get("StrDescEmbala"),
            "capacidade_embalagem": float(data.get("StrPesoEmbala").replace(",", ".")),
            "unidade_medida": data.get("StrUnMedEmbala"),
            "qtd_volume": data.get("StrQtEmbala"),
            "tipo_embalagem": (
                "FECHADA" if data.get("StrTpEmbala") == "A" else "FRACIONADA"
            ),
        }
        return Embalagem(**embalagem_dict)

    def create_embalagens(self, embalagens_data):
        embalagens_obj_list = []
        for data in embalagens_data:
            embalagem = self.build_embalagem_obj(data)
            embalagens_obj_list.append(embalagem)
        Embalagem.objects.bulk_create(embalagens_obj_list)
        return embalagens_obj_list

    def create_many(self, alimentos_data):
        alimento_obj_list = []
        embalagens_dict_list = []

        for data in alimentos_data:
            for obj in alimento_obj_list:
                if obj.nome_alimento == data["StrNomAli"] and obj.guia == data["guia"]:
                    alimento_obj = obj
                    break
            else:
                alimento_obj = self.build_alimento_obj(data)
                alimento_obj_list.append(alimento_obj)

            data["alimento"] = alimento_obj
            embalagens_dict_list.append(data)

        AlimentoModel.objects.bulk_create(alimento_obj_list)

        self.create_embalagens(embalagens_dict_list)

        return alimento_obj_list


class GuiCan(ComplexModel):
    __namespace__ = NS
    StrNumGui = Integer


ArrayOfAlimento = Array(Alimento)
ArrayOfAlimento.__type_name__ = "ArrayOfAlimento"


class Guia(ComplexModel):
    __namespace__ = NS
    StrNumGui = Integer
    DtEntrega = Date
    StrCodUni = String
    StrNomUni = String
    StrEndUni = String
    StrNumUni = String
    StrBaiUni = String
    StrCepUni = String
    StrCidUni = String
    StrEstUni = String
    StrConUni = String
    StrTelUni = String
    alimentos = ArrayOfAlimento

    def build_guia_obj(self, data, soliciacao):
        guia_dict = {
            "numero_guia": data.get("StrNumGui"),
            "data_entrega": data.get("DtEntrega"),
            "codigo_unidade": data.get("StrCodUni"),
            "nome_unidade": data.get("StrNomUni"),
            "endereco_unidade": data.get("StrEndUni"),
            "numero_unidade": data.get("StrNumUni"),
            "bairro_unidade": data.get("StrBaiUni"),
            "cep_unidade": data.get("StrCepUni"),
            "cidade_unidade": data.get("StrCidUni"),
            "estado_unidade": data.get("StrEstUni"),
            "contato_unidade": data.get("StrConUni"),
            "telefone_unidade": data.get("StrTelUni"),
            "solicitacao": soliciacao,
        }
        return GuiaModel(**guia_dict)

    def create_many(self, guias_data, solicitacao):  # noqa C901
        guias_obj_list = []
        alimentos_dict_list = []

        for data in guias_data:
            alimentos_data = data.pop("alimentos", [])
            guia_obj = self.build_guia_obj(data, solicitacao)

            try:
                escola = Escola.objects.get(codigo_codae=guia_obj.codigo_unidade)
                guia_obj.escola = escola
            except ObjectDoesNotExist:
                guia_obj.escola = None

            guias_obj_list.append(guia_obj)

            for data in alimentos_data:
                data["guia"] = guia_obj
                alimentos_dict_list.append(data)
        try:
            GuiaModel.objects.bulk_create(guias_obj_list)

        except IntegrityError as e:
            if "unique constraint" in str(e):
                error = str(e)
                msg = error.split("Key")
                raise IntegrityError("Guia duplicada:" + msg[1])
            raise IntegrityError("Erro ao salvar Guia: " + str(e))

        Alimento().create_many(alimentos_dict_list)

        return guias_obj_list


ArrayOfGuia = Array(Guia)
ArrayOfGuia.__type_name__ = "ArrayOfGuia"
ArrayOfGuiCan = Array(GuiCan)
ArrayOfGuiCan.__type_name__ = "ArrayOfGuiCan"


class ArqSolicitacaoMOD(ComplexModel):
    __namespace__ = NS
    __type_name__ = "SolicitacaoMOD"
    StrCnpj = String
    StrNumSol = Integer
    IntSeqenv = Integer
    guias = ArrayOfGuia
    IntQtGuia = Integer
    IntTotVol = Integer

    @transaction.atomic  # noqa C901
    def create(self):
        data = get_object_as_dict(self)
        distribuidor = None
        cnpj = data.get("StrCnpj")
        guias = data.pop("guias", [])
        data.pop("IntTotVol", None)

        try:
            distribuidor = Terceirizada.objects.get(
                cnpj=cnpj, tipo_servico=Terceirizada.DISTRIBUIDOR_ARMAZEM
            )
            data["distribuidor"] = distribuidor
        except exceptions.ObjectDoesNotExist:
            raise exceptions.ObjectDoesNotExist(
                "Não existe distribuidor cadastrado com esse cnpj"
            )

        try:
            solicitacao = SolicitacaoRemessa.objects.create_solicitacao(**data)

        except IntegrityError as e:
            if "unique constraint" in str(e):
                error = str(e)
                msg = error.split("Key")
                raise IntegrityError("Solicitação duplicada:" + msg[1])
            raise IntegrityError("Erro ao salvar Solicitação: " + str(e))

        Guia().create_many(guias, solicitacao)

        return solicitacao


class ArqCancelamento(ComplexModel):
    __namespace__ = NS
    __type_name__ = "CancelamentoMOD"
    StrCnpj = String
    StrNumSol = Integer
    IntSeqenv = Integer
    guias = ArrayOfGuiCan
    IntQtGuia = Integer

    @transaction.atomic
    def cancel(self, user):  # noqa C901
        cancelamento_dict = get_object_as_dict(self)
        num_solicitacao = cancelamento_dict.get("StrNumSol")
        seq_envio = cancelamento_dict.get("IntSeqenv")
        guias = cancelamento_dict.get("guias")
        confirma_cancelamento_no_papa = False

        if isinstance(guias, list):
            guias_payload = [x["StrNumGui"] for x in guias]
        else:
            guias_payload = [x["StrNumGui"] for x in guias.values()]
        try:
            solicitacao = SolicitacaoRemessa.objects.get(
                numero_solicitacao=num_solicitacao
            )

        except exceptions.ObjectDoesNotExist:
            raise exceptions.ObjectDoesNotExist(
                f"Solicitacão {num_solicitacao} não encontrada."
            )

        guias_existentes = list(solicitacao.guias.values_list("numero_guia", flat=True))

        # Registra solicitação de cancelamento
        solicitacao_cancelamento = (
            LogSolicitacaoDeCancelamentoPeloPapa.registrar_solicitacao(
                requisicao=solicitacao, guias=guias_payload, sequencia_envio=seq_envio
            )
        )
        # Não depende de confirmação do distribuidor no sigpae
        if solicitacao.status in (
            StatusReq.AGUARDANDO_ENVIO,
            StatusReq.DILOG_ENVIA,
            StatusReq.DILOG_ACEITA_ALTERACAO,
        ):
            solicitacao.guias.filter(numero_guia__in=guias_payload).update(
                status=GuiaStatus.CANCELADA
            )
            existe_guia_nao_cancelada = solicitacao.guias.exclude(
                status=GuiaStatus.CANCELADA
            ).exists()

            if (
                set(guias_existentes) == set(guias_payload)
                or not existe_guia_nao_cancelada
            ):
                solicitacao.cancela_solicitacao(user=user)
            else:
                solicitacao.salvar_log_transicao(
                    status_evento=LogSolicitacoesUsuario.PAPA_CANCELA_SOLICITACAO,
                    usuario=user,
                    justificativa=f"Guias canceladas: {guias_payload}",
                )

            solicitacao_cancelamento.confirmar_cancelamento()
            confirma_cancelamento_no_papa = True

        # Depende de confirmação do distribuidor no sigpae
        elif solicitacao.status in (
            StatusReq.DISTRIBUIDOR_CONFIRMA,
            StatusReq.DISTRIBUIDOR_SOLICITA_ALTERACAO,
        ):
            solicitacao.guias.filter(numero_guia__in=guias_payload).update(
                status=GuiaStatus.AGUARDANDO_CANCELAMENTO
            )
            existe_guia_valida = solicitacao.guias.exclude(
                status__in=(GuiaStatus.AGUARDANDO_CANCELAMENTO, GuiaStatus.CANCELADA)
            ).exists()

            if set(guias_existentes) == set(guias_payload) or not existe_guia_valida:
                solicitacao.aguarda_confirmacao_de_cancelamento(user=user)
            else:
                solicitacao.salvar_log_transicao(
                    status_evento=LogSolicitacoesUsuario.PAPA_AGUARDA_CONFIRMACAO_CANCELAMENTO_SOLICITACAO,
                    usuario=user,
                    justificativa=f"Guias canceladas: {guias_payload}",
                )

        return confirma_cancelamento_no_papa


class oWsAcessoModel(ComplexModel):
    __namespace__ = NS
    __type_name__ = "acessMOD"
    StrId = String
    StrToken = String


class SoapResponse(ComplexModel):
    __namespace__ = NS
    __type_name__ = "codresMOD"

    def __init__(self, str_status, str_menssagem):
        """Objeto de response adaptado para o webserver soap."""
        self.StrStatus = str_status
        self.StrMensagem = str_menssagem

    StrStatus = String
    StrMensagem = String
