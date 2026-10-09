"""Filtros do Relatório de Alimentações Servidas.

Este módulo valida o conjunto de filtros da tela e calcula os meses de
referência permitidos. A exportação Excel lê a query string com
``filtros_exportacao_relatorio_alimentacoes_servidas``, que aplica esta
mesma validação. A consulta e o arquivo ficam em
``relatorio_alimentacoes_servidas_dados`` e
``relatorio_alimentacoes_servidas_excel``.

Query string da exportação
    Listas no formato do Axios, com a chave repetida e colchetes
    (``dres[]=a&dres[]=b``), como em ``relatorio-adesao/exportar-xlsx/``.
    A chave sem colchetes também é aceita. Parâmetro ausente significa
    "sem restrição" dentro dos demais filtros.

Meses de referência
    ``meses`` é uma lista obrigatória (``meses[]=11_2023&meses[]=12_2023``),
    cada item no formato ``MM_AAAA``. Duplicados são descartados e a lista
    validada sai em ordem cronológica. Cada mês precisa estar entre os meses
    permitidos para o usuário.

Meses permitidos
    Solicitações com status ``MEDICAO_APROVADA_PELA_CODAE``, no escopo do
    usuário. Recreio nas férias entra na conta quando a solicitação está
    aprovada. O front precisa chamar
    ``GET /medicao-inicial/solicitacao-medicao-inicial/meses-anos/?eh_relatorio_alimentacoes_servidas=true``.
    Sem esse parâmetro, ``status`` e ``eh_relatorio_adesao`` permanecem como estão.

Escopo
    DRE: somente a própria diretoria. Terceirizada (tipo de serviço
    TERCEIRIZADA): somente as DREs dos lotes com contrato vigente, o mesmo
    recorte de ``/diretorias-regionais-simplissima/``. Demais perfis
    autorizados: sem recorte institucional.

    ``/diretorias-regionais-simplissima/`` não passa a restringir o perfil DRE,
    porque outras telas consomem a lista completa. O recorte da DRE é garantido
    aqui na validação e nos endpoints de lote, escola e subprefeitura.

Período
    ``periodo_lancamento_de`` e ``periodo_lancamento_ate`` vão juntos ou ficam
    ambos vazios. Cada data precisa cair em algum dos meses selecionados
    (podem ser meses diferentes), com De anterior ou igual a Até.

Faixa etária
    Não existe vínculo de faixa com tipo de unidade. A faixa só é aceita quando
    os tipos informados pertencem ao Grupo 1 ou ao Grupo 2.

Tipo de alimentação
    Obrigatoriamente vazio no Grupo 1. Nos demais grupos, quando há tipos de
    unidade e vínculos ativos, o tipo precisa ser aplicável a esses tipos.
"""

from datetime import datetime

from rest_framework import serializers

from src.cardapio.base.models import TipoAlimentacao
from src.dados_comuns.constants import (
    ADMINISTRADOR_CODAE_GABINETE,
    ADMINISTRADOR_EMPRESA,
    ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
    ADMINISTRADOR_MEDICAO,
    ADMINISTRADOR_SUPERVISAO_NUTRICAO,
    COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
    COORDENADOR_SUPERVISAO_NUTRICAO,
    COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
    DINUTRE_DIRETORIA,
    FORMATO_DATA_BRASILEIRO,
    TIPOS_GESTAO,
    USUARIO_EMPRESA,
    USUARIO_RELATORIOS,
)
from src.escola.api.filters import (
    dres_no_escopo,
    instituicao_da_requisicao_usuario,
    uuids_de_lista,
)
from src.escola.models import (
    Codae,
    DiretoriaRegional,
    Escola,
    FaixaEtaria,
    GrupoUnidadeEscolar,
    Lote,
    Subprefeitura,
    TipoUnidadeEscolar,
)
from src.medicao_inicial.models import SolicitacaoMedicaoInicial
from src.terceirizada.models import Terceirizada

STATUS_MEDICAO_RELATORIO_ALIMENTACOES_SERVIDAS = "MEDICAO_APROVADA_PELA_CODAE"

PERFIS_CODAE_AUTORIZADOS = frozenset(
    {
        COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
        ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
        ADMINISTRADOR_MEDICAO,
        COORDENADOR_SUPERVISAO_NUTRICAO,
        ADMINISTRADOR_SUPERVISAO_NUTRICAO,
        COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
        ADMINISTRADOR_CODAE_GABINETE,
        USUARIO_RELATORIOS,
        DINUTRE_DIRETORIA,
    }
)

PERFIS_EMPRESA_AUTORIZADOS = frozenset({ADMINISTRADOR_EMPRESA, USUARIO_EMPRESA})

MENSAGEM_MESES_OBRIGATORIO = "Selecione ao menos um mês de referência."
MENSAGEM_MES_FORMATO = "Cada mês de referência deve estar no formato MM_AAAA."
MENSAGEM_DATA_FORA_DOS_MESES = (
    "A data deve estar dentro de um mês de referência selecionado"
)


def usuario_autorizado_relatorio_alimentacoes_servidas(usuario):
    instituicao = instituicao_da_requisicao_usuario(usuario)
    perfil = _nome_perfil(usuario)
    if isinstance(instituicao, DiretoriaRegional):
        return True
    if _empresa_terceirizada_autorizada(instituicao, perfil):
        return True
    if isinstance(instituicao, Codae):
        return perfil in PERFIS_CODAE_AUTORIZADOS
    return False


def meses_anos_relatorio_alimentacoes_servidas(usuario):
    resultados = [_item_mes_ano(par) for par in meses_permitidos(usuario)]
    resultados.sort(key=lambda item: (item["ano"], item["mes"]), reverse=True)
    return resultados


def meses_permitidos(usuario):
    pares = set()
    solicitacoes = solicitacoes_aprovadas_no_escopo(usuario)
    for mes, ano in solicitacoes.values_list("mes", "ano").distinct():
        par = par_mes_ano_inteiro(mes, ano)
        if par:
            pares.add(par)
    return pares


def validar_filtros_relatorio_alimentacoes_servidas(dados, usuario):
    """Valida o payload do formulário e devolve os dados normalizados."""
    serializer = FiltrosRelatorioAlimentacoesServidasSerializer(
        data=dados, context={"usuario": usuario}
    )
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


CAMPOS_LISTA = (
    "meses",
    "dres",
    "lotes",
    "subprefeituras",
    "tipos_unidades",
    "unidades_educacionais",
    "tipos_alimentacao",
    "faixas_etarias",
)
CAMPOS_TEXTO = ("periodo_lancamento_de", "periodo_lancamento_ate")


def dados_da_query_string(query_params):
    """Converte a query string do front no payload do serializer."""
    dados = {
        campo: query_params.get(campo)
        for campo in CAMPOS_TEXTO
        if query_params.get(campo) is not None
    }
    for campo in CAMPOS_LISTA:
        uuids = uuids_de_lista(query_params, f"{campo}[]", campo)
        if uuids:
            dados[campo] = uuids
    return dados


def filtros_exportacao_relatorio_alimentacoes_servidas(query_params, usuario):
    """Valida a query string e devolve filtros serializáveis em JSON."""
    validados = validar_filtros_relatorio_alimentacoes_servidas(
        dados_da_query_string(query_params), usuario
    )
    return {
        campo: [str(item) for item in valor] if isinstance(valor, list) else valor
        for campo, valor in validados.items()
    }


def solicitacoes_aprovadas_no_escopo(usuario):
    queryset = SolicitacaoMedicaoInicial.objects.filter(
        status=STATUS_MEDICAO_RELATORIO_ALIMENTACOES_SERVIDAS
    )
    instituicao = instituicao_da_requisicao_usuario(usuario)
    return filtrar_solicitacoes_por_instituicao(queryset, instituicao)


def filtrar_solicitacoes_por_instituicao(queryset, instituicao):
    if isinstance(instituicao, DiretoriaRegional):
        return queryset.filter(escola__diretoria_regional=instituicao)
    if isinstance(instituicao, Terceirizada):
        return queryset.filter(escola__lote__terceirizada=instituicao)
    if isinstance(instituicao, Escola):
        return queryset.filter(escola=instituicao)
    if instituicao is None:
        return queryset.none()
    return queryset


def par_mes_ano_inteiro(mes, ano):
    try:
        return int(mes), int(ano)
    except (TypeError, ValueError):
        return None


def _item_mes_ano(par):
    mes, ano = par
    return {
        "mes": f"{mes:02d}",
        "ano": str(ano),
        "recreio_nas_ferias": None,
        "status": [STATUS_MEDICAO_RELATORIO_ALIMENTACOES_SERVIDAS],
    }


def _nome_perfil(usuario):
    vinculo = getattr(usuario, "vinculo_atual", None)
    if not vinculo or not getattr(vinculo, "perfil", None):
        return ""
    return vinculo.perfil.nome


def _empresa_terceirizada_autorizada(instituicao, perfil):
    if not isinstance(instituicao, Terceirizada):
        return False
    if not instituicao.eh_terceirizada:
        return False
    return perfil in PERFIS_EMPRESA_AUTORIZADOS


def _validar_usuario(usuario):
    if usuario_autorizado_relatorio_alimentacoes_servidas(usuario):
        return
    raise serializers.ValidationError(
        {"usuario": "Usuário sem permissão para o relatório de alimentações servidas."}
    )


def _validar_meses(valores, usuario):
    """Devolve os pares (mes, ano) sem duplicados, em ordem cronológica."""
    if not valores:
        raise serializers.ValidationError({"meses": MENSAGEM_MESES_OBRIGATORIO})
    pares = {_interpretar_mes(*_partir_mes(valor)) for valor in valores}
    permitidos = meses_permitidos(usuario)
    if not pares <= permitidos:
        raise serializers.ValidationError(
            {"meses": "Mês de referência não permitido para consulta."}
        )
    return sorted(pares, key=lambda par: (par[1], par[0]))


def _partir_mes(valor):
    texto = "" if valor is None else str(valor)
    if "_" not in texto:
        raise serializers.ValidationError({"meses": MENSAGEM_MES_FORMATO})
    mes_txt, ano_txt = texto.split("_", 1)
    if len(mes_txt) != 2 or len(ano_txt) != 4:
        raise serializers.ValidationError({"meses": MENSAGEM_MES_FORMATO})
    return mes_txt, ano_txt


def _interpretar_mes(mes_txt, ano_txt):
    try:
        mes = int(mes_txt)
        ano = int(ano_txt)
    except ValueError:
        raise serializers.ValidationError({"meses": MENSAGEM_MES_FORMATO})
    if not 1 <= mes <= 12:
        raise serializers.ValidationError({"meses": MENSAGEM_MES_FORMATO})
    return mes, ano


def _lista(dados, chave):
    return dados.get(chave) or []


def _validar_regras(dados, usuario):
    _validar_usuario(usuario)
    meses = _validar_meses(dados.get("meses"), usuario)
    dres = _lista(dados, "dres")
    lotes = _lista(dados, "lotes")
    subprefeituras = _lista(dados, "subprefeituras")
    tipos_unidades = _lista(dados, "tipos_unidades")
    _validar_dres(dres, usuario)
    _validar_lotes(lotes, dres, usuario)
    _validar_subprefeituras(subprefeituras, dres, lotes)
    grupo = _validar_tipos_unidades(tipos_unidades)
    _validar_unidades(
        _lista(dados, "unidades_educacionais"),
        dres,
        lotes,
        subprefeituras,
        tipos_unidades,
        usuario,
    )
    _validar_tipos_alimentacao(
        _lista(dados, "tipos_alimentacao"), grupo, tipos_unidades
    )
    _validar_faixas(_lista(dados, "faixas_etarias"), grupo)
    _validar_periodo(dados, meses)
    return meses


def _validar_dres(dres, usuario):
    if not dres:
        raise serializers.ValidationError(
            {"dres": "Informe ao menos uma diretoria regional."}
        )
    queryset = DiretoriaRegional.objects.filter(uuid__in=dres)
    escopo = dres_no_escopo(usuario)
    if escopo is not None:
        queryset = queryset.filter(pk__in=escopo.values("pk"))
    if queryset.distinct().count() != len(set(dres)):
        raise serializers.ValidationError(
            {"dres": "Diretoria regional inválida ou fora do escopo do usuário."}
        )


def _validar_lotes(lotes, dres, usuario):
    if not lotes:
        return
    queryset = Lote.objects.filter(uuid__in=lotes, diretoria_regional__uuid__in=dres)
    queryset = _restringir_lotes(queryset, instituicao_da_requisicao_usuario(usuario))
    if queryset.distinct().count() != len(set(lotes)):
        raise serializers.ValidationError(
            {
                "lotes": (
                    "Lote inválido, de outra diretoria regional ou fora do escopo do usuário."
                )
            }
        )


def _restringir_lotes(queryset, instituicao):
    if isinstance(instituicao, Terceirizada):
        return queryset.filter(terceirizada=instituicao)
    if isinstance(instituicao, DiretoriaRegional):
        return queryset.filter(diretoria_regional=instituicao)
    return queryset


def _validar_subprefeituras(subprefeituras, dres, lotes):
    if subprefeituras and lotes:
        raise serializers.ValidationError(
            {"subprefeituras": "Subprefeitura não pode ser informada junto com lote."}
        )
    if not subprefeituras:
        return
    encontradas = Subprefeitura.objects.filter(
        uuid__in=subprefeituras, diretoria_regional__uuid__in=dres
    ).distinct()
    if encontradas.count() != len(set(subprefeituras)):
        raise serializers.ValidationError(
            {
                "subprefeituras": (
                    "Subprefeitura inválida ou não relacionada às diretorias regionais informadas."
                )
            }
        )


def _validar_tipos_unidades(uuids):
    if not uuids:
        return None
    tipos = list(
        TipoUnidadeEscolar.objects.filter(uuid__in=uuids).prefetch_related(
            "grupounidadeescolar_set"
        )
    )
    if len(tipos) != len(set(uuids)):
        raise serializers.ValidationError(
            {"tipos_unidades": "Tipo de unidade inexistente."}
        )
    return _grupo_unico(tipos)


def _grupo_unico(tipos):
    intersecao = _intersecao_de_grupos(tipos)
    if not intersecao or len(intersecao) != 1:
        raise serializers.ValidationError(
            {"tipos_unidades": "Os tipos de unidade devem pertencer ao mesmo grupo."}
        )
    return next(iter(intersecao))


def _intersecao_de_grupos(tipos):
    intersecao = None
    for tipo in tipos:
        grupos = set(tipo.grupounidadeescolar_set.all())
        if not grupos:
            raise serializers.ValidationError(
                {"tipos_unidades": "Tipo de unidade sem grupo cadastrado."}
            )
        intersecao = _atualizar_intersecao(intersecao, grupos)
    return intersecao


def _atualizar_intersecao(intersecao, grupos):
    if intersecao is None:
        return grupos
    return intersecao & grupos


def _validar_unidades(uuids, dres, lotes, subprefeituras, tipos, usuario):
    if not uuids:
        return
    queryset = _queryset_unidades_compativeis(
        uuids, dres, lotes, subprefeituras, tipos, usuario
    )
    if queryset.distinct().count() != len(set(uuids)):
        raise serializers.ValidationError(
            {
                "unidades_educacionais": (
                    "Unidade educacional incompatível com os filtros informados."
                )
            }
        )


def _queryset_unidades_compativeis(uuids, dres, lotes, subprefeituras, tipos, usuario):
    queryset = Escola.objects.filter(
        uuid__in=uuids,
        tipo_gestao__nome=TIPOS_GESTAO.TERC_TOTAL.value,
        diretoria_regional__uuid__in=dres,
    )
    queryset = _aplicar_filtros_opcionais_escola(queryset, lotes, subprefeituras, tipos)
    instituicao = instituicao_da_requisicao_usuario(usuario)
    return _restringir_escolas(queryset, instituicao)


def _aplicar_filtros_opcionais_escola(queryset, lotes, subprefeituras, tipos):
    if lotes:
        queryset = queryset.filter(lote__uuid__in=lotes)
    if subprefeituras:
        queryset = queryset.filter(subprefeitura__uuid__in=subprefeituras)
    if tipos:
        queryset = queryset.filter(tipo_unidade__uuid__in=tipos)
    return queryset


def _restringir_escolas(queryset, instituicao):
    if isinstance(instituicao, DiretoriaRegional):
        return queryset.filter(diretoria_regional=instituicao)
    if isinstance(instituicao, Terceirizada):
        return queryset.filter(lote__terceirizada=instituicao)
    return queryset


def _eh_grupo_1(grupo):
    return bool(grupo) and grupo.nome == GrupoUnidadeEscolar.GRUPO_1


def _validar_tipos_alimentacao(uuids, grupo, tipos_unidades):
    if _eh_grupo_1(grupo):
        _recusar_alimentacao_no_grupo_1(uuids)
        return
    if not uuids:
        return
    _validar_tipos_alimentacao_existentes(uuids)
    _validar_tipos_alimentacao_aplicaveis(uuids, tipos_unidades)


def _recusar_alimentacao_no_grupo_1(uuids):
    if uuids:
        raise serializers.ValidationError(
            {"tipos_alimentacao": "Tipo de alimentação não é permitido para o Grupo 1."}
        )


def _validar_tipos_alimentacao_existentes(uuids):
    encontrados = TipoAlimentacao.objects.filter(uuid__in=uuids).distinct()
    if encontrados.count() != len(set(uuids)):
        raise serializers.ValidationError(
            {"tipos_alimentacao": "Tipo de alimentação inválido."}
        )


def _validar_tipos_alimentacao_aplicaveis(uuids, tipos_unidades):
    if not tipos_unidades:
        return
    aplicaveis = TipoAlimentacao.objects.filter(
        vinculos__tipo_unidade_escolar__uuid__in=tipos_unidades,
        vinculos__ativo=True,
    ).distinct()
    if not aplicaveis.exists():
        return
    compativeis = aplicaveis.filter(uuid__in=uuids).distinct()
    if compativeis.count() != len(set(uuids)):
        raise serializers.ValidationError(
            {
                "tipos_alimentacao": (
                    "Tipo de alimentação não aplicável aos tipos de unidade informados."
                )
            }
        )


def _grupo_permite_faixa(grupo):
    if not grupo:
        return False
    return grupo.nome in (GrupoUnidadeEscolar.GRUPO_1, GrupoUnidadeEscolar.GRUPO_2)


def _validar_faixas(uuids, grupo):
    if uuids and not _grupo_permite_faixa(grupo):
        raise serializers.ValidationError(
            {
                "faixas_etarias": (
                    "Faixa etária só é permitida para o Grupo 1 ou o Grupo 2."
                )
            }
        )
    if not uuids:
        return
    ativas = FaixaEtaria.objects.filter(uuid__in=uuids, ativo=True).distinct()
    if ativas.count() != len(set(uuids)):
        raise serializers.ValidationError({"faixas_etarias": "Faixa etária inválida."})


def _validar_periodo(dados, meses):
    data_de = dados.get("periodo_lancamento_de") or ""
    data_ate = dados.get("periodo_lancamento_ate") or ""
    if bool(data_de) != bool(data_ate):
        raise serializers.ValidationError(
            {
                "periodo_lancamento_de": (
                    "Ambos 'periodo_lancamento_de' e 'periodo_lancamento_ate' "
                    "devem ser informados juntos"
                )
            }
        )
    if not data_de:
        return
    inicio = _parse_data(data_de, "periodo_lancamento_de")
    fim = _parse_data(data_ate, "periodo_lancamento_ate")
    _validar_ordem_periodo(inicio, fim)
    _validar_data_nos_meses(inicio, meses, "periodo_lancamento_de")
    _validar_data_nos_meses(fim, meses, "periodo_lancamento_ate")


def _validar_ordem_periodo(data_de, data_ate):
    if data_de > data_ate:
        raise serializers.ValidationError(
            {
                "periodo_lancamento_de": (
                    "'periodo_lancamento_de' deve ser anterior a 'periodo_lancamento_ate'"
                )
            }
        )


def _parse_data(valor, campo):
    try:
        return datetime.strptime(valor, FORMATO_DATA_BRASILEIRO).date()
    except ValueError:
        raise serializers.ValidationError(
            {
                campo: (
                    f"Formato de data inválido para '{campo}'. Use o formato dd/mm/yyyy"
                )
            }
        )


def _validar_data_nos_meses(data, meses, campo):
    if (data.month, data.year) not in meses:
        raise serializers.ValidationError({campo: MENSAGEM_DATA_FORA_DOS_MESES})


_ERRO_UUID = {"invalid": "Informe um UUID válido."}


def _campo_uuids(obrigatorio=False):
    campo = {
        "child": serializers.UUIDField(error_messages=_ERRO_UUID),
        "allow_empty": not obrigatorio,
    }
    if obrigatorio:
        campo["error_messages"] = {
            "required": "Informe ao menos uma diretoria regional.",
            "empty": "Informe ao menos uma diretoria regional.",
        }
        return serializers.ListField(**campo)
    campo["required"] = False
    campo["default"] = list
    return serializers.ListField(**campo)


class FiltrosRelatorioAlimentacoesServidasSerializer(serializers.Serializer):
    """Valida o formulário do Relatório de Alimentações Servidas.

    Usado por ``relatorio-alimentacoes-servidas/exportar-xlsx/`` por meio de
    ``validar_filtros_relatorio_alimentacoes_servidas``, com o usuário em
    ``context['usuario']``.
    """

    meses = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
        error_messages={
            "required": MENSAGEM_MESES_OBRIGATORIO,
            "empty": MENSAGEM_MESES_OBRIGATORIO,
            "not_a_list": MENSAGEM_MESES_OBRIGATORIO,
        },
    )
    dres = _campo_uuids(obrigatorio=True)
    lotes = _campo_uuids()
    subprefeituras = _campo_uuids()
    tipos_unidades = _campo_uuids()
    unidades_educacionais = _campo_uuids()
    tipos_alimentacao = _campo_uuids()
    faixas_etarias = _campo_uuids()
    periodo_lancamento_de = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    periodo_lancamento_ate = serializers.CharField(
        required=False, allow_blank=True, default=""
    )

    def validate(self, attrs):
        meses = _validar_regras(attrs, self.context.get("usuario"))
        attrs["meses"] = [f"{mes:02d}_{ano}" for mes, ano in meses]
        return attrs
