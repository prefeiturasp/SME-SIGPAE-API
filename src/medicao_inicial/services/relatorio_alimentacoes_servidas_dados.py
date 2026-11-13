"""
Consulta e estrutura intermediária do Relatório de Alimentações Servidas.
"""

from calendar import monthrange
from datetime import date, datetime

from django.db.models import BooleanField, Case, FloatField, Q, Sum, Value, When
from django.db.models.functions import Cast

from src.cardapio.base.models import TipoAlimentacao
from src.core.models import (
    DiretoriaRegional,
    GrupoUnidadeEscolar,
    TipoUnidadeEscolar,
)
from src.dados_comuns.constants import (
    FORMATO_DATA_BRASILEIRO,
    ORDEM_UNIDADES_GRUPO_CEMEI,
    ORDEM_UNIDADES_GRUPO_CIEJA_CMCT,
    ORDEM_UNIDADES_GRUPO_EMEBS,
    ORDEM_UNIDADES_GRUPO_EMEF,
    ORDEM_UNIDADES_GRUPO_EMEI,
    TIPOS_GESTAO,
)
from src.medicao_inicial.models import CategoriaMedicao, ValorMedicao
from src.medicao_inicial.services.relatorio_adesao import ORDEM_TIPOS_UNIDADE
from src.medicao_inicial.services.relatorio_alimentacoes_servidas import (
    par_mes_ano_inteiro,
    solicitacoes_aprovadas_no_escopo,
)
from src.medicao_inicial.utils import normalizar_nome_campo

TITULO_RELATORIO = "Relatório de Alimentações Servidas"

SECAO_REGULAR = "Alimentações Regulares"
SECAO_DIETA_TIPO_A = "Dieta Especial - Tipo A"
SECAO_DIETA_TIPO_B = "Dieta Especial - Tipo B"
SECOES = (SECAO_REGULAR, SECAO_DIETA_TIPO_A, SECAO_DIETA_TIPO_B)

SECAO_POR_CATEGORIA = {
    CategoriaMedicao.ALIMENTACAO: SECAO_REGULAR,
    CategoriaMedicao.SOLICITACOES_DE_ALIMENTACAO: SECAO_REGULAR,
    CategoriaMedicao.DIETA_ESPECIAL_TIPO_A: SECAO_DIETA_TIPO_A,
    CategoriaMedicao.DIETA_ESPECIAL_TIPO_A_ENTERAL_RESTRICAO_AMINOACIDOS: SECAO_DIETA_TIPO_A,
    CategoriaMedicao.DIETA_ESPECIAL_TIPO_B: SECAO_DIETA_TIPO_B,
}

ABREVIACOES_MESES = (
    "JAN",
    "FEV",
    "MAR",
    "ABR",
    "MAI",
    "JUN",
    "JUL",
    "AGO",
    "SET",
    "OUT",
    "NOV",
    "DEZ",
)
COLUNA_TOTAL_PERIODO = "TOTAL DO PERÍODO"

SEM_GRUPO = "Sem grupo"
VALOR_NUMERICO = r"^[0-9]+(\.[0-9]+)?$"

# Regras do endpoint ``totais-atendimento-consumo`` (consumo do financeiro).
ROTULO_REFEICAO_EJA = "Refeição EJA"
ROTULOS_POR_CAMPO = {
    "refeicao": "Refeição",
    "sobremesa": "Sobremesa",
    "lanche_4h": "Lanche 4h",
    "lanche": "Lanche 5h",
    "lanche_emergencial": "Lanche Emergencial",
    "kit_lanche": "Kit Lanche Passeio",
}
ORDEM_ROTULOS = (
    ROTULOS_POR_CAMPO["refeicao"],
    ROTULO_REFEICAO_EJA,
    ROTULOS_POR_CAMPO["sobremesa"],
    ROTULOS_POR_CAMPO["lanche_4h"],
    ROTULOS_POR_CAMPO["lanche"],
    ROTULOS_POR_CAMPO["lanche_emergencial"],
    ROTULOS_POR_CAMPO["kit_lanche"],
)
CAMPOS_FORA_DA_ALIMENTACAO = (
    "observacoes",
    "dietas_autorizadas",
    "matriculados",
    "frequencia",
    "numero_de_alunos",
    "participantes",
)
CAMPOS_DE_PAGAMENTO = (
    "refeicao",
    "2_refeicao_1_oferta",
    "sobremesa",
    "2_sobremesa_1_oferta",
)
CAMPOS_COMPARATIVOS = ("matriculados", "numero_de_alunos", "participantes")
OFERTAS_DE_PAGAMENTO = {
    "refeicao": (
        ("refeicao", "repeticao_refeicao"),
        ("2_refeicao_1_oferta", "repeticao_2_refeicao"),
    ),
    "sobremesa": (
        ("sobremesa", "repeticao_sobremesa"),
        ("2_sobremesa_1_oferta", "repeticao_2_sobremesa"),
    ),
}
CAMPOS_DE_PAGAMENTO_EMEF = tuple(
    nome for ofertas in OFERTAS_DE_PAGAMENTO.values() for par in ofertas for nome in par
)
UNIDADES_PAGAMENTO_EMEF = set(ORDEM_UNIDADES_GRUPO_EMEF) | set(
    ORDEM_UNIDADES_GRUPO_CIEJA_CMCT
)
UNIDADES_PAGAMENTO_SOMA = (
    set(ORDEM_UNIDADES_GRUPO_EMEI)
    | set(ORDEM_UNIDADES_GRUPO_CEMEI)
    | set(ORDEM_UNIDADES_GRUPO_EMEBS)
)
UNIDADES_EJA = set(ORDEM_UNIDADES_GRUPO_EMEF)
EH_NOITE = Case(
    When(medicao__periodo_escolar__nome__iexact="NOITE", then=Value(True)),
    default=Value(False),
    output_field=BooleanField(),
)

FILTROS_ESCOLA = (
    ("lotes", "escola__lote__uuid__in"),
    ("subprefeituras", "escola__subprefeitura__uuid__in"),
    ("tipos_unidades", "escola__tipo_unidade__uuid__in"),
    ("unidades_educacionais", "escola__uuid__in"),
)

_SOLICITACAO = "medicao__solicitacao_medicao_inicial"
CAMPO_TIPO_UNIDADE = f"{_SOLICITACAO}__escola__tipo_unidade_id"
CAMPO_RECREIO = f"{_SOLICITACAO}__recreio_nas_ferias_id"
CAMPO_MES = f"{_SOLICITACAO}__mes"
CAMPO_ANO = f"{_SOLICITACAO}__ano"


def meses_dos_filtros(filtros):
    """Pares (mes, ano) da lista validada, que já vem sem duplicados e ordenada."""
    return [par_mes_ano_inteiro(*mes_ano.split("_")) for mes_ano in filtros["meses"]]


def recreios_dos_filtros(filtros, usuario):
    """Recreios selecionados, com o título e os meses de suas solicitações.

    Uma consulta, já no escopo do usuário (os UUIDs foram validados). Sai em
    ordem cronológica: ``[{"id", "titulo", "meses": [(mes, ano), ...]}]``.
    """
    uuids = filtros.get("recreios_nas_ferias") or []
    if not uuids:
        return []
    linhas = (
        solicitacoes_aprovadas_no_escopo(usuario)
        .filter(recreio_nas_ferias__uuid__in=uuids)
        .values_list(
            "recreio_nas_ferias_id", "recreio_nas_ferias__titulo", "mes", "ano"
        )
        .distinct()
    )
    recreios = {}
    for recreio_id, titulo, mes, ano in linhas:
        par = par_mes_ano_inteiro(mes, ano)
        if par:
            recreios.setdefault(
                recreio_id, {"id": recreio_id, "titulo": titulo, "meses": []}
            )["meses"].append(par)
    for recreio in recreios.values():
        recreio["meses"].sort(key=_chave_cronologica)
    return sorted(
        recreios.values(),
        key=lambda r: (_chave_cronologica(r["meses"][0]), r["titulo"], r["id"]),
    )


def _chave_cronologica(par):
    mes, ano = par
    return ano, mes


def monta_colunas(meses, recreios=()):
    """Colunas de mês regular e de recreio, em ordem cronológica.

    A ``chave`` é ``(ano, mes, id do recreio ou None)``.
    """
    meses_com_recreio = {par for recreio in recreios for par in recreio["meses"]}
    itens = [
        ((ano, mes, 0, ""), _coluna_regular(mes, ano, (mes, ano) in meses_com_recreio))
        for mes, ano in meses
    ]
    for recreio in recreios:
        for mes, ano in recreio["meses"]:
            ordem = (ano, mes, 1, recreio["titulo"])
            itens.append((ordem, _coluna_recreio(mes, ano, recreio)))
    colunas = [coluna for _, coluna in sorted(itens, key=lambda item: item[0])]
    _diferencia_recreios_repetidos(colunas)
    return colunas


def _rotulo_mes(mes, ano):
    return f"{ABREVIACOES_MESES[mes - 1]} {ano}"


def _coluna_regular(mes, ano, ha_recreio_no_mes):
    rotulo = _rotulo_mes(mes, ano)
    if ha_recreio_no_mes:
        rotulo = f"REGULAR - {rotulo}"
    return {"chave": (ano, mes, None), "rotulo": rotulo}


def _coluna_recreio(mes, ano, recreio):
    return {
        "chave": (ano, mes, recreio["id"]),
        "rotulo": f"RECREIO NAS FÉRIAS - {_rotulo_mes(mes, ano)}",
        "titulo": recreio["titulo"],
    }


def _diferencia_recreios_repetidos(colunas):
    """Acrescenta o título quando dois recreios teriam o mesmo rótulo."""
    contagem = {}
    for coluna in colunas:
        contagem[coluna["rotulo"]] = contagem.get(coluna["rotulo"], 0) + 1
    for coluna in colunas:
        if contagem[coluna["rotulo"]] > 1 and "titulo" in coluna:
            coluna["rotulo"] = f"{coluna['rotulo']} ({coluna['titulo']})"


def rotulo_coluna_total(periodos):
    anos = {ano for _, ano in periodos}
    if len(anos) == 1:
        return f"TOTAL {anos.pop()}"
    return COLUNA_TOTAL_PERIODO


def linha_vazia(tamanho):
    return [0] * tamanho


def soma_colunas(linhas, tamanho):
    total = linha_vazia(tamanho)
    for valores in linhas:
        total = [atual + valor for atual, valor in zip(total, valores)]
    return total


TAMANHO_MAXIMO_NOME_ARQUIVO = 200  # ``CentralDeDownload.identificador``


def obtem_nome_arquivo_relatorio_alimentacoes_servidas(meses, recreios=()):
    """Nome do arquivo com meses e recreios em ordem cronológica.

    ``meses`` é a lista ``MM_AAAA`` validada e ``recreios`` sai de
    ``recreios_dos_filtros``. O nome cabe no ``identificador`` da Central de
    Downloads: se passar do limite, o final dos rótulos é cortado com "…".
    """
    itens = [((ano, mes, 0, ""), f"{mes:02d}/{ano}") for mes, ano in _pares(meses)]
    for recreio in recreios:
        for mes, ano in recreio["meses"]:
            rotulo = f"{recreio['titulo']} ({mes:02d}/{ano})"
            itens.append(((ano, mes, 1, recreio["titulo"]), rotulo))
    rotulos = ", ".join(rotulo for _, rotulo in sorted(itens, key=lambda i: i[0]))
    prefixo, sufixo = f"{TITULO_RELATORIO} - ", ".xlsx"
    limite = TAMANHO_MAXIMO_NOME_ARQUIVO - len(prefixo) - len(sufixo)
    if len(rotulos) > limite:
        rotulos = f"{rotulos[: limite - 1]}…"
    return f"{prefixo}{rotulos}{sufixo}"


def _pares(meses):
    return [par_mes_ano_inteiro(*mes_ano.split("_")) for mes_ano in meses]


def monta_relatorio_alimentacoes_servidas(filtros, usuario):
    """Monta a estrutura usada pelo Excel a partir dos filtros validados."""
    meses = meses_dos_filtros(filtros)
    recreios = recreios_dos_filtros(filtros, usuario)
    colunas = monta_colunas(meses, recreios)
    periodos = [(mes, ano) for ano, mes, _ in (c["chave"] for c in colunas)]
    contexto = {
        "tamanho": len(colunas),
        "indices": {coluna["chave"]: indice for indice, coluna in enumerate(colunas)},
    }
    linhas, nomes = _consulta_do_relatorio(filtros, meses, recreios, usuario)
    contexto.update(nomes)
    grupos = {}
    for linha in linhas:
        _acumular(grupos, linha, contexto)
    grupos_ordenados = _ordenar_grupos(grupos)
    tamanho = contexto["tamanho"]
    return {
        "titulo": TITULO_RELATORIO,
        "meses": meses,
        "recreios": [
            {"titulo": recreio["titulo"], "meses": recreio["meses"]}
            for recreio in recreios
        ],
        "colunas": [coluna["rotulo"] for coluna in colunas],
        "coluna_total": rotulo_coluna_total(periodos),
        "periodo_lancamento_de": filtros.get("periodo_lancamento_de") or "",
        "periodo_lancamento_ate": filtros.get("periodo_lancamento_ate") or "",
        "dres": _nomes_dres(filtros["dres"]),
        "grupos": grupos_ordenados,
        "total_geral": total_geral(grupos_ordenados, tamanho),
    }


def _consulta_do_relatorio(filtros, meses, recreios, usuario):
    """Linhas do relatório e nomes usados para montá-lo (poucas consultas fixas).

    Consultas: alimentações agregadas, total de pagamento de EMEF/CIEJA/CMCT
    (se houver essas unidades) e os nomes.
    """
    valores = _valores_base(
        filtros, usuario, _q_meses_e_periodo(meses, recreios, filtros)
    )
    alimentacoes = list(_agregados_de_alimentacao(valores))
    nomes = _nomes_da_consulta(alimentacoes)
    nomes.update(_nomes_de_alimentacao(filtros, _tipos_de_unidade_do_grupo_1()))
    linhas = list(_linhas_de_alimentacao(alimentacoes, nomes))
    linhas.extend(_linhas_de_pagamento_emef(valores, alimentacoes, nomes))
    return linhas, nomes


def _valores_base(filtros, usuario, q_periodos):
    return ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial__in=_solicitacoes(filtros, usuario),
        categoria_medicao__nome__in=list(SECAO_POR_CATEGORIA),
        valor__regex=VALOR_NUMERICO,
    ).filter(q_periodos)


def _agregados_de_alimentacao(valores):
    return (
        valores.exclude(nome_campo__in=CAMPOS_FORA_DA_ALIMENTACAO)
        .annotate(eh_noite=EH_NOITE)
        .values(
            CAMPO_TIPO_UNIDADE,
            CAMPO_RECREIO,
            CAMPO_MES,
            CAMPO_ANO,
            "categoria_medicao__nome",
            "nome_campo",
            "eh_noite",
        )
        .annotate(total=Sum(Cast("valor", FloatField())))
        .order_by()
    )


def _nomes_de_alimentacao(filtros, tipos_do_grupo_1):
    """Rótulo por campo e campos permitidos por ``tipos_alimentacao``.

    ``campos_permitidos`` é ``None`` sem o filtro. As unidades do Grupo 1 não
    são restringidas por ele.
    """
    tipos = list(TipoAlimentacao.objects.values_list("uuid", "nome"))
    rotulos = {_campo_do_tipo(nome): nome for _, nome in tipos}
    rotulos.update(ROTULOS_POR_CAMPO)
    selecionados = {str(uuid) for uuid in filtros.get("tipos_alimentacao") or []}
    permitidos = None
    if selecionados:
        permitidos = {
            _campo_consolidado(_campo_do_tipo(nome))
            for uuid, nome in tipos
            if str(uuid) in selecionados
        }
    return {
        "rotulos": rotulos,
        "campos_permitidos": permitidos,
        "grupo_1": tipos_do_grupo_1,
    }


def _campo_do_tipo(nome):
    return normalizar_nome_campo(nome).lower()


def _campo_consolidado(nome_campo):
    """Campo consolidado como no endpoint ``totais-atendimento-consumo``."""
    if nome_campo.startswith("kit_lanche"):
        return "kit_lanche"
    for trecho in ("lanche_emergencial", "lanche_4h", "lanche"):
        if trecho in nome_campo:
            return trecho
    return nome_campo


def _linhas_de_alimentacao(agregados, nomes):
    for linha in agregados:
        resultado = _base_e_rotulo(linha, nomes)
        if resultado and _passa_filtro_de_alimentacao(resultado[0], linha, nomes):
            yield {**linha, "rotulo": resultado[1]}


def _base_e_rotulo(linha, nomes):
    """(campo base, rótulo) ou ``None`` quando não é alimentação servida."""
    campo = linha["nome_campo"]
    regular = SECAO_POR_CATEGORIA[linha["categoria_medicao__nome"]] == SECAO_REGULAR
    if regular and campo in CAMPOS_DE_PAGAMENTO:
        return _base_e_rotulo_de_pagamento(linha, nomes)
    base = _campo_consolidado(campo)
    if base == "refeicao" and _eh_refeicao_eja(linha, nomes):
        return base, ROTULO_REFEICAO_EJA
    rotulo = nomes["rotulos"].get(base)
    return (base, rotulo) if rotulo else None


def _base_e_rotulo_de_pagamento(linha, nomes):
    """Refeição e sobremesa regulares somadas (EMEI, CEMEI e EMEBS)."""
    iniciais = nomes["tipos_unidade"].get(linha[CAMPO_TIPO_UNIDADE], "")
    eh_alimentacao = linha["categoria_medicao__nome"] == CategoriaMedicao.ALIMENTACAO
    if iniciais not in UNIDADES_PAGAMENTO_SOMA or not eh_alimentacao:
        return None
    base = "refeicao" if "refeicao" in linha["nome_campo"] else "sobremesa"
    return base, ROTULOS_POR_CAMPO[base]


def _eh_refeicao_eja(linha, nomes):
    iniciais = nomes["tipos_unidade"].get(linha[CAMPO_TIPO_UNIDADE], "")
    return bool(linha["eh_noite"]) and iniciais in UNIDADES_EJA


def _passa_filtro_de_alimentacao(base, linha, nomes):
    permitidos = nomes["campos_permitidos"]
    if permitidos is None or linha[CAMPO_TIPO_UNIDADE] in nomes["grupo_1"]:
        return True
    return base in permitidos


def _linhas_de_pagamento_emef(valores, agregados, nomes):
    """Total de pagamento de refeição e sobremesa de EMEF e CIEJA/CMCT."""
    tipos_emef = {
        tipo_unidade_id
        for tipo_unidade_id in {linha[CAMPO_TIPO_UNIDADE] for linha in agregados}
        if nomes["tipos_unidade"].get(tipo_unidade_id) in UNIDADES_PAGAMENTO_EMEF
    }
    if not tipos_emef:
        return
    totais = _totais_de_pagamento_emef(_valores_de_pagamento_emef(valores, tipos_emef))
    for chave, por_campo in totais.items():
        for base, total in por_campo.items():
            linha = _linha_de_pagamento(chave, base, total, nomes)
            if _passa_filtro_de_alimentacao(base, linha, nomes):
                yield linha


def _linha_de_pagamento(chave, base, total, nomes):
    tipo_unidade_id, recreio_id, mes, ano, eh_noite = chave
    linha = {
        CAMPO_TIPO_UNIDADE: tipo_unidade_id,
        CAMPO_RECREIO: recreio_id,
        CAMPO_MES: mes,
        CAMPO_ANO: ano,
        "categoria_medicao__nome": CategoriaMedicao.ALIMENTACAO,
        "eh_noite": eh_noite,
        "total": total,
    }
    eja = base == "refeicao" and _eh_refeicao_eja(linha, nomes)
    linha["rotulo"] = ROTULO_REFEICAO_EJA if eja else ROTULOS_POR_CAMPO[base]
    return linha


def _valores_de_pagamento_emef(valores, tipos_emef):
    return (
        valores.filter(
            nome_campo__in=CAMPOS_DE_PAGAMENTO_EMEF + CAMPOS_COMPARATIVOS,
            **{f"{CAMPO_TIPO_UNIDADE}__in": tipos_emef},
        )
        .annotate(eh_noite=EH_NOITE)
        .values_list(
            "medicao_id",
            "dia",
            "nome_campo",
            "categoria_medicao__nome",
            "valor",
            CAMPO_TIPO_UNIDADE,
            CAMPO_RECREIO,
            CAMPO_MES,
            CAMPO_ANO,
            "eh_noite",
        )
        .iterator()
    )


def _totais_de_pagamento_emef(valores):
    """Soma, por tipo de unidade, recreio, mês e período, dos totais diários."""
    por_dia = {}
    for medicao_id, dia, campo, categoria, valor, *chave in valores:
        registro = por_dia.setdefault((medicao_id, dia), (tuple(chave), {}))
        if campo in CAMPOS_COMPARATIVOS or categoria == CategoriaMedicao.ALIMENTACAO:
            registro[1].setdefault(campo, int(float(valor)))
    totais = {}
    for chave, campos in por_dia.values():
        destino = totais.setdefault(chave, {})
        for base, total in _pagamento_do_dia(campos, chave[1] is not None).items():
            destino[base] = destino.get(base, 0) + total
    return totais


def _pagamento_do_dia(campos, eh_recreio):
    """Menor valor entre o servido (com repetição) e o comparativo, por oferta."""
    comparativo = _comparativo(campos, eh_recreio)
    return {
        base: sum(
            min(sum(campos.get(nome, 0) for nome in oferta), comparativo)
            for oferta in ofertas
        )
        for base, ofertas in OFERTAS_DE_PAGAMENTO.items()
    }


def _comparativo(campos, eh_recreio):
    if eh_recreio:
        return campos.get("participantes", 0)
    if "matriculados" in campos:
        return campos["matriculados"]
    return campos.get("numero_de_alunos", 0)


def _q_meses_e_periodo(meses, recreios, filtros):
    """Uma condição por mês regular e por recreio/mês, recortada por De/Até.

    O mês regular só pega solicitações sem recreio; o recreio só pega as
    solicitações dele. Assim os dois nunca se somam.
    """
    periodo = _periodo(filtros)
    condicao = Q(pk__in=[])
    for mes, ano in meses:
        condicao |= _q_dias(mes, ano, periodo, **{f"{CAMPO_RECREIO}__isnull": True})
    for recreio in recreios:
        for mes, ano in recreio["meses"]:
            condicao |= _q_dias(mes, ano, periodo, **{CAMPO_RECREIO: recreio["id"]})
    return condicao


def _q_dias(mes, ano, periodo, **restricao):
    dias = _dias_do_mes_no_periodo(mes, ano, periodo)
    if not dias:
        return Q(pk__in=[])
    return Q(
        **restricao,
        **{CAMPO_MES: f"{mes:02d}", CAMPO_ANO: str(ano)},
        dia__gte=dias[0],
        dia__lte=dias[1],
    )


def _periodo(filtros):
    data_de = filtros.get("periodo_lancamento_de")
    data_ate = filtros.get("periodo_lancamento_ate")
    if not (data_de and data_ate):
        return None
    return _data(data_de), _data(data_ate)


def _data(valor):
    return datetime.strptime(valor, FORMATO_DATA_BRASILEIRO).date()


def _dias_do_mes_no_periodo(mes, ano, periodo):
    inicio = date(ano, mes, 1)
    fim = date(ano, mes, monthrange(ano, mes)[1])
    if periodo:
        inicio, fim = max(inicio, periodo[0]), min(fim, periodo[1])
    if inicio > fim:
        return None
    return f"{inicio.day:02d}", f"{fim.day:02d}"


def _solicitacoes(filtros, usuario):
    queryset = solicitacoes_aprovadas_no_escopo(usuario).filter(
        escola__tipo_gestao__nome=TIPOS_GESTAO.TERC_TOTAL.value,
        escola__diretoria_regional__uuid__in=filtros["dres"],
    )
    opcionais = {
        lookup: filtros[campo] for campo, lookup in FILTROS_ESCOLA if filtros.get(campo)
    }
    return queryset.filter(**opcionais)


def _tipos_de_unidade_do_grupo_1():
    """IDs dos tipos de unidade do Grupo 1 (uma consulta)."""
    return set(
        GrupoUnidadeEscolar.objects.filter(
            nome=GrupoUnidadeEscolar.GRUPO_1, tipos_unidades__isnull=False
        ).values_list("tipos_unidades__id", flat=True)
    )


def _nomes_da_consulta(alimentacoes):
    tipos_unidade_ids = {linha[CAMPO_TIPO_UNIDADE] for linha in alimentacoes}
    return {
        "tipos_unidade": dict(
            TipoUnidadeEscolar.objects.filter(id__in=tipos_unidade_ids).values_list(
                "id", "iniciais"
            )
        ),
        "grupos": _grupo_por_tipo_unidade(tipos_unidade_ids),
    }


def _grupo_por_tipo_unidade(tipos_unidade_ids):
    pares = (
        GrupoUnidadeEscolar.objects.filter(tipos_unidades__id__in=tipos_unidade_ids)
        .order_by("-nome")
        .values_list("tipos_unidades__id", "nome")
    )
    return dict(pares)


def _acumular(grupos, linha, contexto):
    tipo_unidade_id = linha[CAMPO_TIPO_UNIDADE]
    grupo = _grupo_da_linha(grupos, contexto["grupos"].get(tipo_unidade_id, SEM_GRUPO))
    grupo["tipos_unidades"].add(contexto["tipos_unidade"].get(tipo_unidade_id, ""))
    secao = grupo["alimentacoes"][SECAO_POR_CATEGORIA[linha["categoria_medicao__nome"]]]
    valores = secao.setdefault(linha["rotulo"], linha_vazia(contexto["tamanho"]))
    chave = (int(linha[CAMPO_ANO]), int(linha[CAMPO_MES]), linha[CAMPO_RECREIO])
    indice = contexto["indices"][chave]
    grupo["colunas"].add(indice)
    valores[indice] += _numero(linha["total"])


def _grupo_da_linha(grupos, nome):
    return grupos.setdefault(
        nome,
        {
            "nome": nome,
            "tipos_unidades": set(),
            "colunas": set(),
            "alimentacoes": {secao: {} for secao in SECOES},
        },
    )


def _numero(valor):
    valor = valor or 0
    return int(valor) if float(valor).is_integer() else valor


def _ordenar_grupos(grupos):
    return [_grupo_ordenado(grupos[nome]) for nome in sorted(grupos, key=_chave_grupo)]


def _chave_grupo(nome):
    return (nome == SEM_GRUPO, nome)


def _grupo_ordenado(grupo):
    return {
        "nome": grupo["nome"],
        "tipos_unidades": sorted(grupo["tipos_unidades"], key=_chave_tipo_unidade),
        "colunas": sorted(grupo["colunas"]),
        "alimentacoes": _ordenar_secoes(grupo["alimentacoes"], _chave_alimentacao),
    }


def _chave_tipo_unidade(iniciais):
    return (ORDEM_TIPOS_UNIDADE.get(iniciais, len(ORDEM_TIPOS_UNIDADE) + 1), iniciais)


def _chave_alimentacao(nome):
    ordem = ORDEM_ROTULOS.index(nome) if nome in ORDEM_ROTULOS else len(ORDEM_ROTULOS)
    return (ordem, nome)


def _ordenar_secoes(secoes, chave):
    return {
        secao: {rotulo: linhas[rotulo] for rotulo in sorted(linhas, key=chave)}
        for secao, linhas in secoes.items()
    }


def consolida_secoes(grupos, chave, tamanho):
    """Soma, por seção e rótulo, as linhas de todos os grupos."""
    consolidado = {secao: {} for secao in SECOES}
    for grupo in grupos:
        for secao, linhas in grupo[chave].items():
            _somar_linhas(consolidado[secao], linhas, tamanho)
    return consolidado


def _somar_linhas(destino, linhas, tamanho):
    for rotulo, valores in linhas.items():
        atual = destino.get(rotulo, linha_vazia(tamanho))
        destino[rotulo] = soma_colunas([atual, valores], tamanho)


def total_geral(grupos, tamanho):
    """Total por categoria, somando os tipos de alimentação."""
    alimentacoes = consolida_secoes(grupos, "alimentacoes", tamanho)
    return {
        secao: soma_colunas(list(alimentacoes[secao].values()), tamanho)
        for secao in SECOES
    }


def _nomes_dres(dres):
    return list(
        DiretoriaRegional.objects.filter(uuid__in=dres)
        .order_by("nome")
        .values_list("nome", flat=True)
    )
