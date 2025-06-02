from rest_framework import serializers

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    SubstituicaoAlimentacaoNoPeriodoEscolar,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.models import (
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI,
)
from sme_sigpae_api.cardapio.base.models import (
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)


def precisa_pertencer_a_um_tipo_de_alimentacao(
    tipos_alimentacao_de, tipo_alimentacao_para, tipo_unidade_escolar, periodo_escolar
):
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
