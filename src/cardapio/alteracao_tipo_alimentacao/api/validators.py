from rest_framework import serializers

from src.cardapio.alteracao_tipo_alimentacao.models import (
    SubstituicaoAlimentacaoNoPeriodoEscolar,
)
from src.cardapio.alteracao_tipo_alimentacao_cemei.models import (
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI,
)
from src.cardapio.base.models import (
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)


def precisa_pertencer_a_um_tipo_de_alimentacao(
    tipos_alimentacao_de, tipo_alimentacao_para, tipo_unidade_escolar, periodo_escolar
):
    """Valida se os tipos de alimentacao pertencem ao contexto informado.

    Garante que todos os tipos de alimentacao de origem estejam habilitados
    para o periodo escolar e tipo de unidade da escola e que o tipo de destino
    nao esteja repetido entre os tipos substituidos.

    Args:
        tipos_alimentacao_de (Iterable[TipoAlimentacao]): Tipos de alimentacao
            que serao substituidos.
        tipo_alimentacao_para (TipoAlimentacao): Tipo de alimentacao de destino.
        tipo_unidade_escolar (str): Tipo de unidade da escola associado ao
            pedido.
        periodo_escolar (PeriodoEscolar): Periodo escolar ao qual a
            substituicao se aplica.

    Returns:
        bool: ``True`` quando a combinacao e valida.

    Raises:
        ValidationError: Quando algum tipo de origem nao pertence ao contexto
            de periodo/tipo de unidade ou quando o tipo de destino ja consta
            entre os tipos substituidos.
    """
    tipos_alimentacao = (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.get(
            periodo_escolar=periodo_escolar, tipo_unidade_escolar=tipo_unidade_escolar
        ).tipos_alimentacao.all()
    )
    for tipo_alimentacao in tipos_alimentacao_de:
        if tipo_alimentacao not in tipos_alimentacao:
            raise serializers.ValidationError(
                f"Tipo de alimentação {tipo_alimentacao.nome} não pertence ao período e tipo de unidade"
            )
    if tipo_alimentacao_para in tipos_alimentacao_de:
        raise serializers.ValidationError(
            f"Substituto {tipo_alimentacao_para.nome} está incluso na lista de alimentos substituídos"
        )
    return True


def _get_parametros_queryset(attrs, eh_cemei):
    """Extrai parametros usados na busca de duplicidade de solicitacoes.

    Normaliza os dados recebidos pelo serializer em uma estrutura unica para a
    consulta, considerando a variacao de chave usada nos cenarios CEMEI.

    Args:
        attrs (dict): Dados validados da solicitacao.
        eh_cemei (bool): Indica se a consulta deve usar a estrutura/modelo do
            fluxo CEMEI.

    Returns:
        tuple: Tupla no formato ``(escola, periodos_e_tipos, datas, modelo)``,
        onde ``periodos_e_tipos`` contem pares de UUID do periodo escolar e os
        UUIDs dos tipos de alimentacao de origem.
    """
    escola = attrs["escola"]
    substituicoes = attrs.get("substituicoes")
    if eh_cemei:
        substituicoes = attrs["substituicoes_cemei_emei_periodo_escolar"]
    periodos_e_tipos = []
    for sub in substituicoes:
        elem = (
            sub["periodo_escolar"].uuid,
            [item.uuid for item in sub["tipos_alimentacao_de"]],
        )
        periodos_e_tipos.append(elem)

    datas_intervalo = attrs["datas_intervalo"]
    datas = [item["data"] for item in datas_intervalo]

    modelo = SubstituicaoAlimentacaoNoPeriodoEscolar
    if eh_cemei:
        modelo = SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI

    return escola, periodos_e_tipos, datas, modelo


def valida_duplicidade_solicitacoes_lanche_emergencial(attrs, eh_cemei=False):
    """Valida se existe alguma solicitação ativa (não é rascunho, nem foi negada ou cancelada) de Lanche Emergencial para a mesma combinação de:
        - escola
        - data
        - periodo escolar
        - tipos de alimentacao de origem.

    Caso já exista alguma solicitação ativa que contenha a mesma combinação, a função levanta um ValidationError,
    impedindo a criação de uma nova solicitação de Lanche Emergencial para a mesma situação.

    Args:
        attrs (dict): Dados validados da solicitacao.
        eh_cemei (bool, optional): Define se a consulta deve usar o modelo de
            substituição do fluxo CEMEI. Default é ``False``.

    Returns:
        bool: ``True`` quando nao ha duplicidade bloqueante ou quando o motivo
        da solicitacao nao e Lanche Emergencial.

    Raises:
        ValidationError: Quando ja existe uma solicitacao ativa de Lanche
            Emergencial para a mesma combinacao de data e periodo.
    """
    motivo = attrs["motivo"]

    if motivo.nome != "Lanche Emergencial":
        return True

    escola, periodos_e_tipos, datas, modelo = _get_parametros_queryset(attrs, eh_cemei)

    registros = []

    for data in datas:
        for periodo, tipos_de_alimentacao in periodos_e_tipos:
            registros.extend(
                modelo.objects.filter(
                    alteracao_cardapio__escola__uuid=escola.uuid,
                    alteracao_cardapio__motivo__nome=motivo.nome,
                    alteracao_cardapio__datas_intervalo__data=data,
                    periodo_escolar__uuid=periodo,
                    tipos_alimentacao_de__uuid__in=tipos_de_alimentacao,
                )
            )

    status_permitidos = [
        "ESCOLA_CANCELOU",
        "DRE_NAO_VALIDOU_PEDIDO_ESCOLA",
        "CODAE_NEGOU_PEDIDO",
        "RASCUNHO",
    ]

    registros = [
        r for r in registros if r.alteracao_cardapio.status not in status_permitidos
    ]

    # Caso ainda haja algum registro que esteja dando match com a solicitação
    if registros:
        raise serializers.ValidationError(
            "Já existe uma solicitação de Lanche Emergencial para a mesma data e período selecionado!"
        )
    return True
