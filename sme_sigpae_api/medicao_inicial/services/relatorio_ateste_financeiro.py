from datetime import datetime
from decimal import Decimal

from num2words import num2words

from sme_sigpae_api.cardapio.base.api.serializers import (
    TipoUnidadeEscolarAgrupadoSerializer,
)
from sme_sigpae_api.cardapio.base.models import (
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from sme_sigpae_api.dados_comuns.utils import converte_numero_em_mes
from sme_sigpae_api.escola.models import FaixaEtaria
from sme_sigpae_api.medicao_inicial.utils import to_decimal_safe


# =========================================================
# HELPERS COMUNS
# =========================================================
def _buscar_valor_por_faixa(valores, faixa_uuid, tipo):
    if not valores:
        return Decimal("0")

    valor = next(
        (
            v.valor
            for v in valores
            if v.faixa_etaria
            and v.faixa_etaria.uuid == faixa_uuid
            and v.tipo_valor
            and v.tipo_valor.nome == tipo
        ),
        None,
    )

    return Decimal("0") if valor is None else to_decimal_safe(valor)


def _buscar_valor_por_tipo(valores, tipo_uuid, tipo_valor):
    if not valores:
        return Decimal("0")

    valor = next(
        (
            v.valor
            for v in valores
            if getattr(v, "tipo_alimentacao", None)
            and str(v.tipo_alimentacao.uuid) == str(tipo_uuid)
            and v.tipo_valor
            and v.tipo_valor.nome == tipo_valor
        ),
        None,
    )

    return Decimal("0") if valor is None else to_decimal_safe(valor)


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
        "quantidade": int(quantidade),
        "valor": valor,
        "valor_extenso": num2words(valor, lang="pt_BR", to="currency"),
    }


def _montar_cabecalho(relatorio_financeiro, tipos_unidades):
    iniciais = ", ".join([t.iniciais for t in tipos_unidades])

    grupo_com_unidades = (
        f"{relatorio_financeiro.grupo_unidade_escolar.nome} ({iniciais})"
    )

    data_referencia = (
        converte_numero_em_mes(int(relatorio_financeiro.mes)).upper()
        + f"/{relatorio_financeiro.ano}"
    )

    return {
        "data_geracao": datetime.now().strftime("%d/%m/%Y"),
        "hora_geracao": datetime.now().strftime("%H:%M"),
        "data_referencia": data_referencia,
        "grupo_unidade_escolar": grupo_com_unidades,
        "dre_lote": (
            f"{relatorio_financeiro.lote.nome.upper()} - "
            f"{relatorio_financeiro.lote.diretoria_regional.nome}"
        ),
    }


# =========================================================
# CEI
# =========================================================
def _build_tabela_alimentacao_cei(
    tabelas, faixas_etarias, totais_consumo
):
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
            valor_unitario = _buscar_valor_por_faixa(
                valores_tabela, faixa.uuid, "UNITARIO"
            )
            valor_reajuste = _buscar_valor_por_faixa(
                valores_tabela, faixa.uuid, "REAJUSTE"
            )

            total_unitario = valor_unitario + valor_reajuste

            numero_atendimentos = totais_consumo.get(
                f"ALIMENTAÇÃO - {periodo}", {}
            ).get(str(faixa), 0)

            valor_total = total_unitario * to_decimal_safe(
                numero_atendimentos
            )

            total_atendimentos += numero_atendimentos
            valor_total_geral += valor_total

            linhas.append(
                {
                    "periodo": f"Período {periodo.capitalize()}",
                    "faixa": str(faixa),
                    "valor_unitario": valor_unitario,
                    "valor_reajuste": valor_reajuste,
                    "total_unitario": total_unitario,
                    "numero_atendimentos": int(numero_atendimentos),
                    "valor_total": valor_total,
                }
            )

    return {
        "linhas": linhas,
        "total_atendimentos": int(total_atendimentos),
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
            valor_unitario = _buscar_valor_por_faixa(
                valores_tabela, faixa.uuid, "UNITARIO"
            )
            valor_acrescimo = _buscar_valor_por_faixa(
                valores_tabela, faixa.uuid, "ACRESCIMO"
            )

            total_unitario = valor_unitario * (
                1 + (valor_acrescimo / 100)
            )

            numero_consumo = totais_consumo.get(
                f"DIETA ESPECIAL - {tipo_dieta} - {periodo}",
                {},
            ).get(str(faixa), 0)

            valor_total = total_unitario * to_decimal_safe(
                numero_consumo
            )

            total_consumo += numero_consumo
            valor_total_geral += valor_total

            linhas.append(
                {
                    "periodo": f"Período {periodo.capitalize()}",
                    "faixa": str(faixa),
                    "valor_unitario": valor_unitario,
                    "valor_acrescimo": valor_acrescimo,
                    "total_unitario": total_unitario,
                    "numero_consumo": int(numero_consumo),
                    "valor_total": valor_total,
                }
            )

    return {
        "linhas": linhas,
        "total_consumo": int(total_consumo),
        "valor_total": valor_total_geral,
    }


def build_relatorio_financeiro_grupo_cei(
    relatorio_financeiro,
    parametrizacao,
    totais_consumo,
):
    faixas_etarias = FaixaEtaria.objects.filter(ativo=True)
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

    consolidado = _build_consolidado_total(
        alimentacao, dieta_a, dieta_b
    )

    tipos = relatorio_financeiro.grupo_unidade_escolar.tipos_unidades.all()

    return {
        "alimentacao": alimentacao,
        "dieta_a": dieta_a,
        "dieta_b": dieta_b,
        "consolidado": consolidado,
        "cabecalho": _montar_cabecalho(
            relatorio_financeiro,
            tipos,
        ),
    }


# =========================================================
# EMEI
# =========================================================
def _obter_tipos_alimentacao_por_unidades(uuids_unidades):
    vinculos = (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
            ativo=True,
            tipo_unidade_escolar__ativo=True,
            tipo_unidade_escolar__uuid__in=uuids_unidades,
        )
        .select_related(
            "tipo_unidade_escolar",
            "periodo_escolar",
        )
        .prefetch_related("tipos_alimentacao")
    )

    dados_agrupados = (
        TipoUnidadeEscolarAgrupadoSerializer.agrupar_vinculos_por_tipo_ue(
            vinculos
        )
    )

    tipos_unicos = {}

    for tipo_ue in dados_agrupados:
        for vinculo in tipo_ue["vinculos"]:
            for tipo in vinculo.tipos_alimentacao.all():
                tipos_unicos[str(tipo.uuid)] = tipo.nome

    return [
        {"uuid": uuid, "nome": nome}
        for uuid, nome in tipos_unicos.items()
    ]


def _build_tabela_alimentacao_emei(
    tabelas, tipos_alimentacao, totais_consumo
):
    total_atendimentos = 0
    valor_total_geral = Decimal("0")
    linhas = []

    for periodo in ["INTEGRAL", "PARCIAL"]:
        tabela = next(
            (
                t for t in tabelas
                if t.nome == "Preço das Alimentações"
                and t.periodo_escolar
                and t.periodo_escolar.nome == periodo
            ),
            None,
        )

        valores_tabela = tabela.valores.all() if tabela else []

        for tipo in tipos_alimentacao:
            valor_unitario = _buscar_valor_por_tipo(
                valores_tabela,
                tipo["uuid"],
                "UNITARIO",
            )

            valor_reajuste = _buscar_valor_por_tipo(
                valores_tabela,
                tipo["uuid"],
                "REAJUSTE",
            )

            total_unitario = valor_unitario + valor_reajuste

            numero_atendimentos = totais_consumo.get(
                f"ALIMENTAÇÃO - {periodo}", {}
            ).get(tipo["nome"], 0)

            valor_total = total_unitario * to_decimal_safe(
                numero_atendimentos
            )

            total_atendimentos += numero_atendimentos
            valor_total_geral += valor_total

            linhas.append(
                {
                    "tipo": tipo["nome"],
                    "valor_unitario": valor_unitario,
                    "valor_reajuste": valor_reajuste,
                    "total_unitario": total_unitario,
                    "numero_atendimentos": int(numero_atendimentos),
                    "valor_total": valor_total,
                }
            )

    return {
        "linhas": linhas,
        "total_atendimentos": int(total_atendimentos),
        "valor_total": valor_total_geral,
    }


def _build_tabela_dieta_emei(
    tabelas, tipos_alimentacao, totais_consumo, tipo_dieta
):
    total_consumo = 0
    valor_total_geral = Decimal("0")
    linhas = []

    for periodo in ["INTEGRAL", "PARCIAL"]:
        tabela = next(
            (
                t for t in tabelas
                if t.nome == "Preço das Alimentações"
                and t.periodo_escolar
                and t.periodo_escolar.nome == periodo
            ),
            None,
        )

        valores_tabela = tabela.valores.all() if tabela else []

        for tipo in tipos_alimentacao:
            valor_unitario = _buscar_valor_por_tipo(
                valores_tabela,
                tipo["uuid"],
                "UNITARIO",
            )

            valor_acrescimo = _buscar_valor_por_tipo(
                valores_tabela,
                tipo["uuid"],
                "ACRESCIMO",
            )

            total_unitario = valor_unitario * (
                1 + (valor_acrescimo / 100)
            )

            numero_consumo = totais_consumo.get(
                f"DIETA ESPECIAL - {tipo_dieta} - {periodo}",
                {},
            ).get(tipo["nome"], 0)

            valor_total = total_unitario * to_decimal_safe(
                numero_consumo
            )

            total_consumo += numero_consumo
            valor_total_geral += valor_total

            linhas.append(
                {
                    "tipo": tipo["nome"],
                    "valor_unitario": valor_unitario,
                    "valor_acrescimo": valor_acrescimo,
                    "total_unitario": total_unitario,
                    "numero_consumo": int(numero_consumo),
                    "valor_total": valor_total,
                }
            )

    return {
        "linhas": linhas,
        "total_consumo": int(total_consumo),
        "valor_total": valor_total_geral,
    }


def build_relatorio_financeiro_grupo_emei(
    relatorio_financeiro,
    parametrizacao,
    totais_consumo,
):
    print('TOTAIS CONSUMO: ', totais_consumo)
    tipos_unidades = (
        relatorio_financeiro.grupo_unidade_escolar.tipos_unidades.all()
    )

    tipos_alimentacao = _obter_tipos_alimentacao_por_unidades(
        tipos_unidades.values_list("uuid", flat=True)
    )
    print('TIPOS ALIMENTACAO: ', tipos_alimentacao)

    tabelas = parametrizacao.tabelas.all()

    alimentacao = _build_tabela_alimentacao_emei(
        tabelas,
        tipos_alimentacao,
        totais_consumo,
    )

    dieta_a = _build_tabela_dieta_emei(
        tabelas,
        tipos_alimentacao,
        totais_consumo,
        "TIPO A",
    )

    dieta_b = _build_tabela_dieta_emei(
        tabelas,
        tipos_alimentacao,
        totais_consumo,
        "TIPO B",
    )

    consolidado = _build_consolidado_total(
        alimentacao,
        dieta_a,
        dieta_b,
    )

    return {
        "alimentacao": alimentacao,
        "dieta_a": dieta_a,
        "dieta_b": dieta_b,
        "consolidado": consolidado,
        "cabecalho": _montar_cabecalho(
            relatorio_financeiro,
            tipos_unidades,
        ),
    }
