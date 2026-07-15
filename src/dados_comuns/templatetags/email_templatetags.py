from django import template

register = template.Library()


@register.filter
def traduz_movimentacao(movimentacao_realizada):
    return {
        "DRE_VALIDADO": "foi validada",
        "DRE_NAO_VALIDOU_PEDIDO_ESCOLA": "não foi validada",
        "CODAE_AUTORIZADO": "foi autorizada",
        "CODAE_NEGOU_PEDIDO": "foi negada",
        "ESCOLA_CANCELOU": "foi cancelada",
        "DRE_CANCELOU": "foi cancelada pela DRE",
    }[movimentacao_realizada]
