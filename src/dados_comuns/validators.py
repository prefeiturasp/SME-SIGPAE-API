import calendar
import datetime

from django.core.exceptions import ValidationError
from django.db import models
from rest_framework import serializers
from workalendar.america import BrazilSaoPauloCity

from ..cardapio.alteracao_tipo_alimentacao.models import (
    AlteracaoCardapio,
    DataIntervaloAlteracaoCardapio,
    SubstituicaoAlimentacaoNoPeriodoEscolar,
)
from ..cardapio.alteracao_tipo_alimentacao_cei.models import (
    AlteracaoCardapioCEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEI,
)
from ..cardapio.alteracao_tipo_alimentacao_cemei.models import AlteracaoCardapioCEMEI
from .constants import obter_dias_uteis_apos_hoje
from .utils import datetime_range, eh_dia_util, eh_fim_de_semana

calendario = BrazilSaoPauloCity()
ERROR_MSG_EXISTE_RPL_MES = (
    "Já existe uma solicitação de RPL para o mês e período selecionado!"
)
RPL_MOTIVO_NOME = "RPL - Refeição por Lanche"


def nao_pode_ser_no_passado(data: datetime.date):
    if data < datetime.date.today():
        raise serializers.ValidationError("Não pode ser no passado")
    return True


def deve_ser_no_passado(data: datetime.date):
    if data > datetime.date.today():
        raise serializers.ValidationError("Deve ser data anterior a hoje")
    return True


def deve_pedir_com_antecedencia(dia: datetime.date, dias: int = 2):
    prox_dia_util = obter_dias_uteis_apos_hoje(quantidade_dias=dias)
    if dia < prox_dia_util:
        raise serializers.ValidationError(
            f"Deve pedir com pelo menos {dias} dias úteis de antecedência"
        )
    return True


def valida_duplicidade_solicitacoes(attrs):
    status_permitidos = [
        "ESCOLA_CANCELOU",
        "DRE_NAO_VALIDOU_PEDIDO_ESCOLA",
        "CODAE_NEGOU_PEDIDO",
        "RASCUNHO",
    ]
    periodos_uuids = [sub["periodo_escolar"].uuid for sub in attrs["substituicoes"]]
    motivo = attrs["motivo"].uuid

    data_inicial_mes = attrs["data_inicial"].month
    data_inicial_ano = attrs["data_inicial"].year
    menor_data = datetime.datetime(data_inicial_ano, data_inicial_mes, 1)

    data_final_mes = attrs["data_final"].month
    data_final_ano = attrs["data_final"].year
    ultimo_dia_do_mes = calendar.monthrange(data_final_ano, data_final_mes)[1]
    maior_data = datetime.datetime(data_final_ano, data_final_mes, ultimo_dia_do_mes)

    substituicoes = SubstituicaoAlimentacaoNoPeriodoEscolar.objects.filter(
        periodo_escolar__uuid__in=periodos_uuids
    )
    alteracoes_pks = substituicoes.values_list("alteracao_cardapio", flat=True)
    solicitacoes = AlteracaoCardapio.objects.filter(
        motivo__uuid=motivo, pk__in=alteracoes_pks, escola=attrs["escola"]
    )

    solicitacoes = solicitacoes.filter(
        data_inicial__gte=menor_data, data_final__lte=maior_data
    )
    solicitacoes = solicitacoes.exclude(status__in=status_permitidos)

    if solicitacoes:
        raise serializers.ValidationError(ERROR_MSG_EXISTE_RPL_MES)
    return True


def valida_duplicidade_solicitacoes_cei(attrs, data):
    status_permitidos = [
        "ESCOLA_CANCELOU",
        "DRE_NAO_VALIDOU_PEDIDO_ESCOLA",
        "CODAE_NEGOU_PEDIDO",
        "RASCUNHO",
    ]
    periodos_uuids = [sub["periodo_escolar"] for sub in attrs["substituicoes"]]
    motivo = attrs["motivo"]

    mes = data.month
    ano = data.year
    ultimo_dia_do_mes = calendar.monthrange(ano, mes)[1]
    menor_data = datetime.datetime(ano, mes, 1)
    maior_data = datetime.datetime(ano, mes, ultimo_dia_do_mes)
    substituicoes = SubstituicaoAlimentacaoNoPeriodoEscolarCEI.objects.filter(
        periodo_escolar__uuid__in=periodos_uuids
    )
    alteracoes_pks = substituicoes.values_list("alteracao_cardapio", flat=True)
    solicitacoes = AlteracaoCardapioCEI.objects.filter(
        motivo__uuid=motivo, pk__in=alteracoes_pks, escola__uuid=attrs["escola"]
    )
    solicitacoes = solicitacoes.filter(data__gte=menor_data, data__lte=maior_data)
    solicitacoes = solicitacoes.exclude(status__in=status_permitidos)

    if solicitacoes:
        raise serializers.ValidationError(ERROR_MSG_EXISTE_RPL_MES)
    return True


def valida_duplicidade_solicitacoes_cemei(attrs):
    status_permitidos = [
        "ESCOLA_CANCELOU",
        "DRE_NAO_VALIDOU_PEDIDO_ESCOLA",
        "CODAE_NEGOU_PEDIDO",
        "RASCUNHO",
    ]
    motivo = attrs["motivo"].uuid
    data = attrs["alterar_dia"]
    mes = data.month
    ano = data.year
    ultimo_dia_do_mes = calendar.monthrange(ano, mes)[1]
    menor_data = datetime.datetime(ano, mes, 1)
    maior_data = datetime.datetime(ano, mes, ultimo_dia_do_mes)
    solicitacoes_tipo = []

    if attrs["alunos_cei_e_ou_emei"] == "CEI":
        solicitacoes_tipo.append("CEI")
    elif attrs["alunos_cei_e_ou_emei"] == "EMEI":
        solicitacoes_tipo.append("EMEI")
    else:
        solicitacoes_tipo = ["TODOS", "CEI", "EMEI"]

    solicitacoes = AlteracaoCardapioCEMEI.objects.filter(
        motivo__uuid=motivo,
        alunos_cei_e_ou_emei__in=solicitacoes_tipo,
        escola__uuid=attrs["escola"].uuid,
    )

    solicitacoes = solicitacoes.filter(
        alterar_dia__gte=menor_data, alterar_dia__lte=maior_data
    )
    solicitacoes = solicitacoes.exclude(status__in=status_permitidos)
    if solicitacoes:
        raise serializers.ValidationError(ERROR_MSG_EXISTE_RPL_MES)
    return True


def escola_tem_dia_letivo_no_calendario(escola, data):
    """Verifica se a escola possui dia letivo no DiaCalendario para a data.

    A consulta considera qualquer registro de ``DiaCalendario`` da escola com
    ``dia_letivo=True`` para a data informada.

    Args:
        escola (Escola): Unidade educacional que está fazendo a solicitação.
        data (datetime.date): Data informada na solicitação.

    Returns:
        bool: ``True`` quando a escola possui ``DiaCalendario`` com
        ``dia_letivo=True`` para a data.
    """
    return escola.calendario.filter(data=data, dia_letivo=True).exists()


def unidade_tem_dia_letivo_sigpae(escola, data):
    """Verifica se a unidade educacional possui DiaLetivoSIGPAE para a data.

    A unidade é considerada contemplada pelo DiaLetivoSIGPAE quando:
        - está listada diretamente no ``escolas`` do DiaLetivoSIGPAE da data; OU
        - não existe nenhuma unidade listada no DiaLetivoSIGPAE da data, mas o
          ``lotes`` e o ``tipos_unidade_escolar`` daquele dia contemplam o lote
          e o tipo de unidade da escola.

    Args:
        escola (Escola): Unidade educacional que está fazendo a solicitação.
        data (datetime.date): Data informada na solicitação.

    Returns:
        bool: ``True`` quando a escola está contemplada por algum
        DiaLetivoSIGPAE da data.
    """
    from ..escola.dias_letivos.models import DiaLetivoSIGPAE

    dias_letivos = DiaLetivoSIGPAE.objects.filter(data=data)
    if dias_letivos.filter(escolas=escola).exists():
        return True
    return dias_letivos.filter(
        escolas=None,
        lotes=escola.lote,
        tipos_unidade_escolar=escola.tipo_unidade,
    ).exists()


def existe_inclusao_alimentacao_autorizada_com_refeicao_e_lanche(escola, data, modelo):
    """Verifica se existe uma Inclusão de Alimentação autorizada na data.

    Considera apenas inclusões que não sejam do tipo Inclusão Contínua e que
    tenham, simultaneamente, os tipos de alimentação Refeição e Lanche.

    Args:
        escola (Escola): Unidade educacional que está fazendo a solicitação.
        data (datetime.date): Data informada na solicitação.
        modelo (Model): Modelo de inclusão de alimentação a ser consultado. Pode
            ser ``GrupoInclusaoAlimentacaoNormal``,
            ``InclusaoAlimentacaoDaCEI`` ou ``InclusaoDeAlimentacaoCEMEI``.

    Returns:
        bool: ``True`` quando existe inclusão autorizada com refeição e lanche
        para a data informada.
    """
    from ..inclusao_alimentacao.models import (
        GrupoInclusaoAlimentacaoNormal,
        InclusaoAlimentacaoDaCEI,
        InclusaoDeAlimentacaoCEMEI,
    )

    if modelo is GrupoInclusaoAlimentacaoNormal:
        return (
            modelo.objects.filter(
                escola=escola,
                status="CODAE_AUTORIZADO",
                inclusoes_normais__data=data,
                inclusoes_normais__cancelado=False,
                quantidades_por_periodo__tipos_alimentacao__nome="Refeição",
            )
            .filter(quantidades_por_periodo__tipos_alimentacao__nome="Lanche")
            .exists()
        )

    if modelo is InclusaoAlimentacaoDaCEI:
        return (
            modelo.objects.filter(
                escola=escola,
                status="CODAE_AUTORIZADO",
                dias_motivos_da_inclusao_cei__data=data,
                dias_motivos_da_inclusao_cei__cancelado=False,
                tipos_alimentacao__nome="Refeição",
            )
            .filter(tipos_alimentacao__nome="Lanche")
            .exists()
        )

    if modelo is InclusaoDeAlimentacaoCEMEI:
        return (
            modelo.objects.filter(
                escola=escola,
                status="CODAE_AUTORIZADO",
                dias_motivos_da_inclusao_cemei__data=data,
                dias_motivos_da_inclusao_cemei__cancelado=False,
                quantidade_alunos_emei_da_inclusao_cemei__tipos_alimentacao__nome="Refeição",
            )
            .filter(
                quantidade_alunos_emei_da_inclusao_cemei__tipos_alimentacao__nome="Lanche"
            )
            .exists()
        )

    return False


def valida_dia_letivo_ou_inclusao_alimentacao_rpl(escola, data, modelo):
    """Valida a data de uma solicitação RPL para a unidade educacional.

    Permite o envio quando:
        - de segunda a sexta, a escola possui ``DiaCalendario`` com
          ``dia_letivo=True`` para a data; OU
        - a unidade possui DiaLetivoSIGPAE para a data; OU
        - existe uma Inclusão de Alimentação autorizada (não contínua) para a
          mesma data com refeição e lanche.

    A verificação de ``DiaCalendario`` é aplicada somente de segunda a sexta.
    Aos sábados e domingos, valem sempre as regras de DiaLetivoSIGPAE ou de
    inclusão de alimentação autorizada.

    Caso nenhuma das condições seja atendida, impede o envio da solicitação.

    Args:
        escola (Escola): Unidade educacional que está fazendo a solicitação.
        data (datetime.date): Data informada na solicitação.
        modelo (Model): Modelo de inclusão de alimentação a ser consultado.

    Returns:
        bool: ``True`` quando a data é válida para a solicitação RPL.

    Raises:
        serializers.ValidationError: Quando a data não é um dia letivo e não
        existe uma inclusão de alimentação para a data.
    """
    if not eh_fim_de_semana(data) and escola_tem_dia_letivo_no_calendario(escola, data):
        return True
    if unidade_tem_dia_letivo_sigpae(escola, data):
        return True
    if existe_inclusao_alimentacao_autorizada_com_refeicao_e_lanche(
        escola, data, modelo
    ):
        return True
    raise serializers.ValidationError(
        f'Dia {data.strftime("%d/%m")} não é um dia letivo ou não existe uma '
        "inclusão de alimentação para a data"
    )


def deve_ser_dia_letivo_e_dia_da_semana(escola, data: datetime.date):
    """Valida que a data é um dia letivo da escola.

    Para dias de semana normais (Seg–Sex): passa sempre.
    Para sábados, domingos e feriados: exige que exista um registro
    DiaCalendario com dia_letivo=True para aquela escola e data.
    """
    SEXTA_FEIRA = 4

    eh_fim_de_semana = data.weekday() > SEXTA_FEIRA
    eh_feriado = calendario.is_holiday(data)

    if eh_fim_de_semana or eh_feriado:
        dia_letivo = escola.calendario.filter(
            data=data, dia_letivo=True, periodo_escolar=None
        ).exists()
        if not dia_letivo:
            raise serializers.ValidationError(
                f'Dia {data.strftime("%d/%m/%Y")} não é um dia letivo'
            )
    return True


def dia_util(data: datetime.date):
    if not eh_dia_util(data):
        raise serializers.ValidationError("Não é dia útil em São Paulo")
    return True


def verificar_se_existe(obj_model, **kwargs) -> bool:
    try:
        if not issubclass(obj_model, models.Model):
            raise TypeError('obj_model deve ser um "django models class"')
    except TypeError:
        raise TypeError('obj_model deve ser um "django models class"')
    existe = obj_model.objects.filter(**kwargs).exists()
    return existe


def objeto_nao_deve_ter_duplicidade(
    obj_model,
    mensagem="Objeto já existe",
    **kwargs,
):
    qtd = obj_model.objects.filter(**kwargs).count()
    if qtd:
        raise serializers.ValidationError(mensagem)


def nao_pode_ser_feriado(data: datetime.date, mensagem="Não pode ser no feriado"):
    if calendario.is_holiday(data):
        raise serializers.ValidationError(mensagem)


def campo_nao_pode_ser_nulo(valor, mensagem="Não pode ser nulo"):
    if not valor:
        raise serializers.ValidationError(mensagem)


def campo_deve_ser_deste_tipo(valor, tipo=str, mensagem="Deve ser do tipo texto"):
    if type(valor) is not tipo:
        raise serializers.ValidationError(mensagem)


def deve_ser_no_mesmo_ano_corrente(data_inversao: datetime.date):
    ano_corrente = datetime.date.today().year
    mes_corrente = datetime.date.today().month
    if ano_corrente != data_inversao.year and mes_corrente != 12:
        raise serializers.ValidationError(
            "Solicitação deve ser solicitada no ano corrente"
        )
    return True


def deve_ter_extensao_valida(nome: str):
    if nome.split(".")[len(nome.split(".")) - 1].lower() not in [
        "doc",
        "docx",
        "pdf",
        "png",
        "jpg",
        "jpeg",
    ]:
        raise serializers.ValidationError("Extensão inválida")
    return nome


def deve_ter_extensao_xls_xlsx_pdf(nome: str):
    if nome.split(".")[len(nome.split(".")) - 1].lower() not in ["xls", "xlsx", "pdf"]:
        raise serializers.ValidationError("Extensão inválida")
    return nome


def valida_datas_alteracao_cardapio(attrs):
    for data in datetime_range(attrs["data_inicial"], attrs["data_final"]):
        for substituicao in attrs["substituicoes"]:
            datas = DataIntervaloAlteracaoCardapio.objects.filter(
                data=data,
                cancelado=False,
                alteracao_cardapio__status__in=[
                    AlteracaoCardapio.workflow_class.DRE_A_VALIDAR,
                    AlteracaoCardapio.workflow_class.DRE_VALIDADO,
                    AlteracaoCardapio.workflow_class.CODAE_AUTORIZADO,
                ],
                alteracao_cardapio__escola=attrs["escola"],
                alteracao_cardapio__substituicoes_periodo_escolar__periodo_escolar=substituicao[
                    "periodo_escolar"
                ],
            )
            if datas.exists():
                raise serializers.ValidationError(
                    "Já existe uma solicitação de lanche emergencial para o dia e período selecionado!"
                )


def validate_file_size_10mb(value):
    """max_size: valor em megabytes."""
    filesize = value.size
    max_size = 10 * 1024 * 1024  # 10 MB
    if filesize > max_size:
        raise ValidationError("O arquivo deve ter no máximo 10MB.")
