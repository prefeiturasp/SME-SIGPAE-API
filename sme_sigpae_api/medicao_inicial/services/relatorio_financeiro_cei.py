
from datetime import datetime
from decimal import Decimal
from sme_sigpae_api.medicao_inicial.utils import to_decimal_safe


def _buscar_valor(valores, faixa_uuid, tipo):
    if not valores:
        return Decimal("0")

    valor = next(
        (v.valor for v in valores if v.faixa_etaria.uuid == faixa_uuid and v.tipo_valor.nome == tipo),
        None,
    )

    return Decimal("0") if valor is None else to_decimal_safe(valor)


def _build_tabela_alimentacao_cei(tabelas, faixas_etarias, totais_consumo):
    total_atendimentos = 0
    valor_total_geral = Decimal("0")
    linhas = []

    for periodo in ["INTEGRAL", "PARCIAL"]:
        tabela = next(
            (
                t
                for t in tabelas
                if t.nome == "Preço das Alimentações"
                and t.periodo_escolar.nome == periodo
            ),
            None,
        )

        valores_tabela = tabela.valores.all() if tabela else []

        for faixa in faixas_etarias:
            valor_unitario = _buscar_valor(valores_tabela, faixa.uuid, "UNITARIO")
            valor_reajuste = _buscar_valor(valores_tabela, faixa.uuid, "REAJUSTE")

            total_unitario = valor_unitario + valor_reajuste

            numero_atendimentos = totais_consumo.get(
                f"ALIMENTAÇÃO - {periodo}", {}
            ).get(faixa.__str__(), 0)

            valor_total = total_unitario * to_decimal_safe(numero_atendimentos)

            total_atendimentos += numero_atendimentos
            valor_total_geral += valor_total

            linhas.append({
                "periodo": f"Período {periodo.capitalize()}",
                "faixa": f"{faixa.__str__()}",
                "valor_unitario": valor_unitario,
                "valor_reajuste": valor_reajuste,
                "total_unitario": total_unitario,
                "numero_atendimentos": int(numero_atendimentos),
                "valor_total": valor_total,
            })

    return {
        "linhas": linhas,
        "total_atendimentos": total_atendimentos,
        "valor_total": valor_total_geral,
    }


def _build_tabela_dieta_cei(
    tabelas, faixas_etarias, totais_consumo, tipo_dieta
):
    total_consumo = 0
    valor_total_geral = Decimal("0")
    linhas = []

    for periodo in ["INTEGRAL", "PARCIAL"]:
        tabela = next(
            (
                t
                for t in tabelas
                if tipo_dieta in t.nome.upper()
                and t.periodo_escolar.nome == periodo
            ),
            None,
        )

        valores_tabela = tabela.valores.all() if tabela else []

        for faixa in faixas_etarias:
            valor_unitario = _buscar_valor(valores_tabela, faixa.uuid, "UNITARIO")
            valor_acrescimo = _buscar_valor(valores_tabela, faixa.uuid, "ACRESCIMO")

            total_unitario = valor_unitario * (1 + (valor_acrescimo / 100))

            numero_consumo = totais_consumo.get(
                f"DIETA ESPECIAL - {tipo_dieta} - {periodo}",
                {},
            ).get(faixa.__str__(), 0)

            valor_total = total_unitario * to_decimal_safe(numero_consumo)

            total_consumo += numero_consumo
            valor_total_geral += valor_total

            linhas.append({
                "periodo": f"Período {periodo.capitalize()}",
                "faixa": f"{faixa.__str__()}",
                "valor_unitario": valor_unitario,
                "valor_acrescimo": valor_acrescimo,
                "total_unitario": total_unitario,
                "numero_consumo": int(numero_consumo),
                "valor_total": valor_total,
            })

    return {
        "linhas": linhas,
        "total_consumo": total_consumo,
        "valor_total": valor_total_geral,
    }


def _build_consolidado_total(alimentacao, dieta_a, dieta_b):
    quantidade = (
        alimentacao["total_atendimentos"]
        + dieta_a["total_consumo"]
        + dieta_b["total_consumo"]
    )

    valor = (
        alimentacao["valor_total"]
        + dieta_a["valor_total"]
        + dieta_b["valor_total"]
    )

    return {
        "quantidade": quantidade,
        "valor": valor,
        "valor_extenso": "TESTE",
    }


def build_relatorio_financeiro_grupo_cei(
    relatorio_financeiro,
    parametrizacao,
    faixas_etarias,
    totais_consumo
):
    tabelas = parametrizacao.tabelas.all()

    alimentacao = _build_tabela_alimentacao_cei(
        tabelas, faixas_etarias, totais_consumo
    )

    dieta_a = _build_tabela_dieta_cei(
        tabelas, faixas_etarias, totais_consumo, "TIPO A"
    )

    dieta_b = _build_tabela_dieta_cei(
        tabelas, faixas_etarias, totais_consumo, "TIPO B"
    )

    consolidado = _build_consolidado_total(alimentacao, dieta_a, dieta_b)

    tipos = relatorio_financeiro.grupo_unidade_escolar.tipos_unidades.all()
    iniciais = ", ".join([t.iniciais for t in tipos])
    grupo_com_unidades = f"{relatorio_financeiro.grupo_unidade_escolar.nome} ({iniciais})"

    return {
        "alimentacao": alimentacao,
        "dieta_a": dieta_a,
        "dieta_b": dieta_b,
        "consolidado": consolidado,
        "cabecalho": {
            "data_geracao": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "data_referencia": f"{relatorio_financeiro.mes}/{relatorio_financeiro.ano}",
            "grupo_unidade_escolar": grupo_com_unidades,
            "dre_lote": f"{relatorio_financeiro.lote.nome.upper()} - {relatorio_financeiro.lote.diretoria_regional.nome}",
        }
    }
