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
from .constants import (
    FORMATO_DATA_BRASILEIRO,
    TIPOS_ALIMENTACAO,
    TIPOS_UNIDADE_ESCOLAR,
    obter_dias_uteis_apos_hoje,
)
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

    if attrs["alunos_cei_e_ou_emei"] == TIPOS_UNIDADE_ESCOLAR.CEI.value:
        solicitacoes_tipo.append(TIPOS_UNIDADE_ESCOLAR.CEI.value)
    elif attrs["alunos_cei_e_ou_emei"] == TIPOS_UNIDADE_ESCOLAR.EMEI.value:
        solicitacoes_tipo.append(TIPOS_UNIDADE_ESCOLAR.EMEI.value)
    else:
        solicitacoes_tipo = [
            "TODOS",
            TIPOS_UNIDADE_ESCOLAR.CEI.value,
            TIPOS_UNIDADE_ESCOLAR.EMEI.value,
        ]

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


def _inclusoes_alimentacao_autorizadas_base(escola, data, modelo):
    """Retorna as Inclusões de Alimentação autorizadas (não contínuas) na data.

    Args:
        escola (Escola): Unidade educacional que está fazendo a solicitação.
        data (datetime.date): Data informada na solicitação.
        modelo (Model): Modelo de inclusão de alimentação a ser consultado. Pode
            ser ``GrupoInclusaoAlimentacaoNormal``,
            ``InclusaoAlimentacaoDaCEI`` ou ``InclusaoDeAlimentacaoCEMEI``.

    Returns:
        QuerySet: Queryset das inclusões autorizadas para a data e escola.
    """
    from ..inclusao_alimentacao.models import (
        GrupoInclusaoAlimentacaoNormal,
        InclusaoAlimentacaoDaCEI,
        InclusaoDeAlimentacaoCEMEI,
    )

    if modelo is GrupoInclusaoAlimentacaoNormal:
        return modelo.objects.filter(
            escola=escola,
            status="CODAE_AUTORIZADO",
            inclusoes_normais__data=data,
            inclusoes_normais__cancelado=False,
        )

    if modelo is InclusaoAlimentacaoDaCEI:
        return modelo.objects.filter(
            escola=escola,
            status="CODAE_AUTORIZADO",
            dias_motivos_da_inclusao_cei__data=data,
            dias_motivos_da_inclusao_cei__cancelado=False,
        )

    if modelo is InclusaoDeAlimentacaoCEMEI:
        return modelo.objects.filter(
            escola=escola,
            status="CODAE_AUTORIZADO",
            dias_motivos_da_inclusao_cemei__data=data,
            dias_motivos_da_inclusao_cemei__cancelado=False,
        )

    return modelo.objects.none()


def _periodos_autorizados_inclusao(escola, data, modelo):
    """Retorna os nomes dos períodos escolares autorizados na inclusão.

    Args:
        escola (Escola): Unidade educacional que está fazendo a solicitação.
        data (datetime.date): Data informada na solicitação.
        modelo (Model): Modelo de inclusão de alimentação a ser consultado.

    Returns:
        set[str]: Conjunto com os nomes dos períodos escolares autorizados.
    """
    from ..inclusao_alimentacao.models import (
        GrupoInclusaoAlimentacaoNormal,
        InclusaoAlimentacaoDaCEI,
        InclusaoDeAlimentacaoCEMEI,
    )

    inclusoes = _inclusoes_alimentacao_autorizadas_base(escola, data, modelo)

    if modelo is GrupoInclusaoAlimentacaoNormal:
        return set(
            inclusoes.values_list(
                "quantidades_por_periodo__periodo_escolar__nome", flat=True
            ).distinct()
        )

    if modelo is InclusaoAlimentacaoDaCEI:
        return set(
            inclusoes.values_list(
                "quantidade_alunos_da_inclusao__periodo_externo__nome", flat=True
            ).distinct()
        )

    if modelo is InclusaoDeAlimentacaoCEMEI:
        periodos_cei = inclusoes.values_list(
            "quantidade_alunos_cei_da_inclusao_cemei__periodo_escolar__nome",
            flat=True,
        ).distinct()
        periodos_emei = inclusoes.values_list(
            "quantidade_alunos_emei_da_inclusao_cemei__periodo_escolar__nome",
            flat=True,
        ).distinct()
        return set(periodos_cei) | set(periodos_emei)

    return set()


def _inclusao_tem_refeicao_e_lanche_para_periodo(
    escola, data, modelo, periodo_nome, lanche_nome
):
    """Verifica se a inclusão possui Refeição e o lanche no período.

    Args:
        escola (Escola): Unidade educacional que está fazendo a solicitação.
        data (datetime.date): Data informada na solicitação.
        modelo (Model): Modelo de inclusão de alimentação a ser consultado.
        periodo_nome (str): Nome do período escolar da solicitação.
        lanche_nome (str): Nome do tipo de lanche solicitado (``"Lanche"`` ou
            ``"Lanche 4h"``).

    Returns:
        bool: ``True`` quando a inclusão autorizada possui Refeição e o lanche
        informado para o período.
    """
    from ..inclusao_alimentacao.models import (
        GrupoInclusaoAlimentacaoNormal,
        InclusaoAlimentacaoDaCEI,
        InclusaoDeAlimentacaoCEMEI,
    )

    inclusoes = _inclusoes_alimentacao_autorizadas_base(escola, data, modelo)

    if modelo is GrupoInclusaoAlimentacaoNormal:
        return (
            inclusoes.filter(
                quantidades_por_periodo__periodo_escolar__nome=periodo_nome,
                quantidades_por_periodo__tipos_alimentacao__nome=TIPOS_ALIMENTACAO.REFEICAO.value,
            )
            .filter(quantidades_por_periodo__tipos_alimentacao__nome=lanche_nome)
            .exists()
        )

    if modelo is InclusaoAlimentacaoDaCEI:
        return (
            inclusoes.filter(
                quantidade_alunos_da_inclusao__periodo_externo__nome=periodo_nome,
                tipos_alimentacao__nome=TIPOS_ALIMENTACAO.REFEICAO.value,
            )
            .filter(tipos_alimentacao__nome=lanche_nome)
            .exists()
        )

    if modelo is InclusaoDeAlimentacaoCEMEI:
        return (
            inclusoes.filter(
                quantidade_alunos_emei_da_inclusao_cemei__periodo_escolar__nome=periodo_nome,
                quantidade_alunos_emei_da_inclusao_cemei__tipos_alimentacao__nome=TIPOS_ALIMENTACAO.REFEICAO.value,
            )
            .filter(
                quantidade_alunos_emei_da_inclusao_cemei__tipos_alimentacao__nome=lanche_nome
            )
            .exists()
        )

    return False


def _formata_periodos_para_mensagem(periodos):
    """Formata uma coleção de nomes de períodos para exibição em mensagem.

    Args:
        periodos (Iterable[str]): Nomes dos períodos escolares.

    Returns:
        str: Nomes ordenados separados por vírgula e ``" e "`` antes do último.
    """
    periodos = sorted(p for p in periodos if p)
    if not periodos:
        return ""
    if len(periodos) == 1:
        return periodos[0]
    return ", ".join(periodos[:-1]) + " e " + periodos[-1]


def _valida_inclusao_alimentacao_rpl(escola, data, modelo, periodos_lanches):
    """Valida a solicitação RPL contra a inclusão de alimentação autorizada.

    Args:
        escola (Escola): Unidade educacional que está fazendo a solicitação.
        data (datetime.date): Data informada na solicitação.
        modelo (Model): Modelo de inclusão de alimentação a ser consultado.
        periodos_lanches (Iterable[dict]): Períodos e lanches da solicitação RPL.

    Returns:
        bool: ``True`` quando a inclusão autorizada atende a solicitação.

    Raises:
        serializers.ValidationError: Quando não há inclusão para a data, quando
        algum período não está autorizado ou quando a inclusão não possui
        Refeição e o lanche solicitado para o período.
    """
    periodos_autorizados = _periodos_autorizados_inclusao(escola, data, modelo)
    if not periodos_autorizados:
        raise serializers.ValidationError(
            f'Dia {data.strftime("%d/%m")} não é um dia letivo ou não existe uma '
            "inclusão de alimentação para a data"
        )
    for item in periodos_lanches or []:
        periodo = item.get("periodo")
        lanches = item.get("lanches") or []
        if periodo not in periodos_autorizados:
            raise serializers.ValidationError(
                f'Para o dia {data.strftime("%d/%m")}, a inclusão está '
                "autorizada somente nos períodos "
                f"{_formata_periodos_para_mensagem(periodos_autorizados)}."
            )
        for lanche in lanches:
            if not _inclusao_tem_refeicao_e_lanche_para_periodo(
                escola, data, modelo, periodo, lanche
            ):
                raise serializers.ValidationError(
                    f'Para o dia {data.strftime("%d/%m")}, a inclusão autorizada '
                    f"não possui Refeição e {lanche} autorizado para o periodo "
                    f"{periodo}."
                )
    return True


def _valida_inclusao_alimentacao_cei_rpl(escola, data, modelo):
    """Valida a solicitação RPL de CEI contra a inclusão de alimentação.

    Para CEI, basta existir uma inclusão de alimentação autorizada para a data,
    sem verificar os tipos de alimentação incluídos nem os períodos.

    Args:
        escola (Escola): Unidade educacional que está fazendo a solicitação.
        data (datetime.date): Data informada na solicitação.
        modelo (Model): Modelo de inclusão de alimentação a ser consultado.

    Returns:
        bool: ``True`` quando existe uma inclusão autorizada para a data.

    Raises:
        serializers.ValidationError: Quando não há inclusão autorizada para a
        data.
    """
    if _inclusoes_alimentacao_autorizadas_base(escola, data, modelo).exists():
        return True
    raise serializers.ValidationError(
        f'Dia {data.strftime("%d/%m")} não é um dia letivo ou não existe uma '
        "inclusão de alimentação para a data"
    )


def _partes_inclusao_cemei_autorizadas(escola, data, modelo):
    """Retorna as partes (CEI/EMEI) cobertas pela inclusão CEMEI autorizada.

    Args:
        escola (Escola): Unidade educacional que está fazendo a solicitação.
        data (datetime.date): Data informada na solicitação.
        modelo (Model): Modelo de inclusão de alimentação a ser consultado.

    Returns:
        set[str]: Conjunto com as partes cobertas, podendo conter ``"CEI"`` e
        ``"EMEI"``.
    """
    inclusoes = _inclusoes_alimentacao_autorizadas_base(escola, data, modelo)
    partes = set()
    if inclusoes.filter(quantidade_alunos_cei_da_inclusao_cemei__isnull=False).exists():
        partes.add(TIPOS_UNIDADE_ESCOLAR.CEI.value)
    if inclusoes.filter(
        quantidade_alunos_emei_da_inclusao_cemei__isnull=False
    ).exists():
        partes.add(TIPOS_UNIDADE_ESCOLAR.EMEI.value)
    return partes


def _valida_parte_cemei_autorizada(data, parte, partes_autorizadas):
    """Valida se a parte solicitada está coberta pela inclusão CEMEI.

    Args:
        data (datetime.date): Data informada na solicitação.
        parte (str): Parte solicitada (``"CEI"`` ou ``"EMEI"``).
        partes_autorizadas (set[str]): Partes cobertas pela inclusão.

    Raises:
        serializers.ValidationError: Quando a parte solicitada não está coberta.
    """
    if parte not in partes_autorizadas:
        raise serializers.ValidationError(
            f"Inclusão autorizada para o dia {data.strftime('%d/%m')} somente para "
            f"{_formata_periodos_para_mensagem(partes_autorizadas)}"
        )


def _valida_inclusao_alimentacao_cemei_rpl(
    escola, data, modelo, alunos_cei_e_ou_emei, periodos_lanches_emei
):
    """Valida a solicitação RPL de CEMEI contra a inclusão de alimentação.

    Para a parte CEI, basta existir a inclusão; para a parte EMEI, valida
    Refeição e o lanche solicitado por período, como em EMEI/EMEF.

    Args:
        escola (Escola): Unidade educacional que está fazendo a solicitação.
        data (datetime.date): Data informada na solicitação.
        modelo (Model): Modelo de inclusão de alimentação a ser consultado.
        alunos_cei_e_ou_emei (str, optional): Escopo da solicitação (``"CEI"``,
            ``"EMEI"`` ou ``"TODOS"``). Quando nulo, considera ``"TODOS"``.
        periodos_lanches_emei (Iterable[dict]): Períodos e lanches das
            substituições EMEI da solicitação.

    Returns:
        bool: ``True`` quando a inclusão autorizada atende a solicitação.

    Raises:
        serializers.ValidationError: Quando não há inclusão, quando a parte
        solicitada não está coberta ou quando a parte EMEI não possui Refeição e
        o lanche solicitado.
    """
    partes_autorizadas = _partes_inclusao_cemei_autorizadas(escola, data, modelo)
    if not partes_autorizadas:
        raise serializers.ValidationError(
            f'Dia {data.strftime("%d/%m")} não é um dia letivo ou não existe uma '
            "inclusão de alimentação para a data"
        )
    alunos_cei_e_ou_emei = alunos_cei_e_ou_emei or "TODOS"
    if alunos_cei_e_ou_emei in (TIPOS_UNIDADE_ESCOLAR.CEI.value, "TODOS"):
        _valida_parte_cemei_autorizada(
            data, TIPOS_UNIDADE_ESCOLAR.CEI.value, partes_autorizadas
        )
    if alunos_cei_e_ou_emei in (TIPOS_UNIDADE_ESCOLAR.EMEI.value, "TODOS"):
        _valida_parte_cemei_autorizada(
            data, TIPOS_UNIDADE_ESCOLAR.EMEI.value, partes_autorizadas
        )
    if alunos_cei_e_ou_emei in (TIPOS_UNIDADE_ESCOLAR.EMEI.value, "TODOS"):
        _valida_inclusao_alimentacao_rpl(escola, data, modelo, periodos_lanches_emei)
    return True


def valida_dia_letivo_ou_inclusao_alimentacao_rpl(
    escola, data, modelo, periodos_lanches=None, alunos_cei_e_ou_emei=None
):
    """Valida a data de uma solicitação RPL para a unidade educacional.

    Permite o envio quando:
        - de segunda a sexta, a escola possui ``DiaCalendario`` com
          ``dia_letivo=True`` para a data; OU
        - a unidade possui DiaLetivoSIGPAE para a data; OU
        - existe uma Inclusão de Alimentação autorizada (não contínua) para a
          mesma data que possua, período a período, Refeição e o tipo de lanche
          solicitado (Lanche ou Lanche 4h).

    A verificação de ``DiaCalendario`` é aplicada somente de segunda a sexta.
    Aos sábados e domingos, valem sempre as regras de DiaLetivoSIGPAE ou de
    inclusão de alimentação autorizada.

    Args:
        escola (Escola): Unidade educacional que está fazendo a solicitação.
        data (datetime.date): Data informada na solicitação.
        modelo (Model): Modelo de inclusão de alimentação a ser consultado.
        periodos_lanches (Iterable[dict], optional): Itens no formato
            ``{"periodo": str, "lanches": list[str]}``, representando os
            períodos da solicitação RPL e os tipos de lanche substituídos em
            cada período. Para CEMEI, contém somente as substituições EMEI.
        alunos_cei_e_ou_emei (str, optional): Escopo da solicitação CEMEI
            (``"CEI"``, ``"EMEI"`` ou ``"TODOS"``).

    Returns:
        bool: ``True`` quando a data é válida para a solicitação RPL.

    Raises:
        serializers.ValidationError: Quando a data não é um dia letivo e não
        existe uma inclusão de alimentação para a data, quando algum período não
        está autorizado na inclusão ou quando a inclusão não possui Refeição e o
        lanche solicitado para o período.
    """
    from ..inclusao_alimentacao.models import (
        InclusaoAlimentacaoDaCEI,
        InclusaoDeAlimentacaoCEMEI,
    )

    if not eh_fim_de_semana(data) and escola_tem_dia_letivo_no_calendario(escola, data):
        return True
    if escola.esta_em_dia_letivo_sigpae(data):
        return True
    if modelo is InclusaoAlimentacaoDaCEI:
        return _valida_inclusao_alimentacao_cei_rpl(escola, data, modelo)
    if modelo is InclusaoDeAlimentacaoCEMEI:
        return _valida_inclusao_alimentacao_cemei_rpl(
            escola, data, modelo, alunos_cei_e_ou_emei, periodos_lanches
        )
    return _valida_inclusao_alimentacao_rpl(escola, data, modelo, periodos_lanches)


def deve_ser_dia_letivo_e_dia_da_semana(escola, data: datetime.date):
    """Valida que a data é um dia letivo da escola.

    Para dias de semana normais (Seg–Sex): passa sempre.
    Para sábados, domingos e feriados: exige que exista um registro
    DiaCalendario com dia_letivo=True para aquela escola e data, ou um
    DiaLetivoSIGPAE contemplando a escola naquela data.
    """
    SEXTA_FEIRA = 4

    eh_fim_de_semana = data.weekday() > SEXTA_FEIRA
    eh_feriado = calendario.is_holiday(data)

    if eh_fim_de_semana or eh_feriado:
        dia_letivo = escola.calendario.filter(
            data=data, dia_letivo=True, periodo_escolar=None
        ).exists()
        if not dia_letivo and not escola.esta_em_dia_letivo_sigpae(data):
            raise serializers.ValidationError(
                f"Dia {data.strftime(FORMATO_DATA_BRASILEIRO)} não é um dia letivo"
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
                alteracao_cardapio__motivo__nome=TIPOS_ALIMENTACAO.LANCHE_EMERGENCIAL.value,
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
