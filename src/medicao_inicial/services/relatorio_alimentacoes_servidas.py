"""Filtros do Relatório de Alimentações Servidas."""

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
    StringsValidationErrors,
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
    return _pares_mes_ano(solicitacoes_aprovadas_no_escopo(usuario))


def meses_regulares_permitidos(usuario):
    """Meses com solicitação regular (sem recreio) aprovada no escopo do usuário."""
    solicitacoes = solicitacoes_aprovadas_no_escopo(usuario)
    return _pares_mes_ano(solicitacoes.filter(recreio_nas_ferias__isnull=True))


def recreios_permitidos(usuario):
    """UUID do recreio -> meses/anos das solicitações aprovadas no escopo."""
    solicitacoes = solicitacoes_aprovadas_no_escopo(usuario).filter(
        recreio_nas_ferias__isnull=False
    )
    recreios = {}
    linhas = solicitacoes.values_list("recreio_nas_ferias__uuid", "mes", "ano")
    for uuid, mes, ano in linhas.distinct():
        par = par_mes_ano_inteiro(mes, ano)
        if par:
            recreios.setdefault(str(uuid), set()).add(par)
    return recreios


def _pares_mes_ano(solicitacoes):
    pares = set()
    for mes, ano in solicitacoes.values_list("mes", "ano").distinct():
        par = par_mes_ano_inteiro(mes, ano)
        if par:
            pares.add(par)
    return pares


def validar_filtros_relatorio_alimentacoes_servidas(dados, usuario):
    """Valida o payload dos filtros e devolve os dados normalizados."""
    serializer = FiltrosRelatorioAlimentacoesServidasSerializer(
        data=dados, context={"usuario": usuario}
    )
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


CAMPOS_LISTA = (
    "meses",
    "recreios_nas_ferias",
    "dres",
    "lotes",
    "subprefeituras",
    "tipos_unidades",
    "unidades_educacionais",
    "tipos_alimentacao",
)
CAMPOS_TEXTO = ("periodo_lancamento_de", "periodo_lancamento_ate")


def dados_da_query_string(query_params):
    """Monta o payload do serializer com as listas ``campo[]`` e as datas.

    A chave sem colchetes também é aceita; parâmetro ausente fica fora do payload.
    """
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


def _validar_meses_e_recreios(dados, usuario):
    """Devolve (meses, recreios, meses_do_periodo) já validados e sem duplicados.

    Exige ao menos um mês ou um recreio.
    """
    valores_meses = dados.get("meses") or []
    valores_recreios = dados.get("recreios_nas_ferias") or []
    if not valores_meses and not valores_recreios:
        raise serializers.ValidationError({"meses": MENSAGEM_MESES_OBRIGATORIO})
    meses = _validar_meses(valores_meses, usuario)
    recreios, meses_dos_recreios = _validar_recreios(valores_recreios, usuario)
    return meses, recreios, set(meses) | meses_dos_recreios


def _validar_meses(valores, usuario):
    """Devolve os pares (mes, ano) sem duplicados, em ordem cronológica.

    Cada mês precisa ter solicitação regular aprovada pela CODAE.
    """
    if not valores:
        return []
    pares = {_interpretar_mes(*_partir_mes(valor)) for valor in valores}
    if not pares <= meses_regulares_permitidos(usuario):
        raise serializers.ValidationError(
            {"meses": "Mês de referência não permitido para consulta."}
        )
    return sorted(pares, key=lambda par: (par[1], par[0]))


def _validar_recreios(valores, usuario):
    """Devolve os UUIDs sem duplicados (em ordem cronológica) e seus meses/anos.

    Cada recreio precisa ter solicitação aprovada pela CODAE; o mês/ano dele é o
    da solicitação.
    """
    if not valores:
        return [], set()
    uuids = {str(valor) for valor in valores}
    permitidos = recreios_permitidos(usuario)
    if not uuids <= set(permitidos):
        raise serializers.ValidationError(
            {
                "recreios_nas_ferias": (
                    "Recreio nas férias inexistente, fora do escopo do usuário "
                    "ou sem medição aprovada pela CODAE."
                )
            }
        )
    ordenados = sorted(
        uuids, key=lambda uuid: (min(permitidos[uuid], key=_chave_mes_ano), uuid)
    )
    return ordenados, set().union(*(permitidos[uuid] for uuid in uuids))


def _chave_mes_ano(par):
    return par[1], par[0]


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
    meses, recreios, meses_do_periodo = _validar_meses_e_recreios(dados, usuario)
    dres = _lista(dados, "dres")
    lotes = _lista(dados, "lotes")
    subprefeituras = _lista(dados, "subprefeituras")
    tipos_unidades = _lista(dados, "tipos_unidades")
    _validar_dres(dres, usuario)
    _validar_lotes(lotes, dres, usuario)
    _validar_subprefeituras(subprefeituras, dres, lotes)
    grupos_dos_tipos = _validar_tipos_unidades(tipos_unidades)
    _validar_unidades(
        _lista(dados, "unidades_educacionais"),
        dres,
        lotes,
        subprefeituras,
        tipos_unidades,
        usuario,
    )
    _validar_tipos_alimentacao(
        _lista(dados, "tipos_alimentacao"), grupos_dos_tipos, tipos_unidades
    )
    _validar_periodo(dados, meses_do_periodo)
    return meses, recreios


def _validar_dres(dres, usuario):
    """Exige ao menos uma DRE dentro do escopo do usuário."""
    if not dres:
        raise serializers.ValidationError(
            {
                "dres": (
                    StringsValidationErrors.INFORME_AO_MENOS_UMA_DIRETORIA_REGIONAL.value
                )
            }
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
    """Valida os tipos e devolve, para cada um, os nomes dos grupos a que pertence.

    Tipos de grupos diferentes são aceitos; nenhum grupo é completado.
    """
    if not uuids:
        return []
    tipos = list(
        TipoUnidadeEscolar.objects.filter(uuid__in=uuids).prefetch_related(
            "grupounidadeescolar_set"
        )
    )
    if len(tipos) != len(set(uuids)):
        raise serializers.ValidationError(
            {"tipos_unidades": "Tipo de unidade inexistente."}
        )
    return [_nomes_dos_grupos(tipo) for tipo in tipos]


def _nomes_dos_grupos(tipo):
    nomes = {grupo.nome for grupo in tipo.grupounidadeescolar_set.all()}
    if not nomes:
        raise serializers.ValidationError(
            {"tipos_unidades": "Tipo de unidade sem grupo cadastrado."}
        )
    return nomes


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


def _todos_no_grupo_1(grupos_dos_tipos):
    return bool(grupos_dos_tipos) and all(
        GrupoUnidadeEscolar.GRUPO_1 in nomes for nomes in grupos_dos_tipos
    )


def _validar_tipos_alimentacao(uuids, grupos_dos_tipos, tipos_unidades):
    """Recusa tipo de alimentação quando todos os tipos de unidade são do Grupo 1.

    Nos demais casos, o tipo precisa existir e ser aplicável aos tipos de unidade.
    """
    if _todos_no_grupo_1(grupos_dos_tipos):
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


def _validar_periodo(dados, meses):
    """De e Até vão juntos, De não passa de Até e cada data cai em um mês selecionado."""
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
            "required": (
                StringsValidationErrors.INFORME_AO_MENOS_UMA_DIRETORIA_REGIONAL.value
            ),
            "empty": (
                StringsValidationErrors.INFORME_AO_MENOS_UMA_DIRETORIA_REGIONAL.value
            ),
        }
        return serializers.ListField(**campo)
    campo["required"] = False
    campo["default"] = list
    return serializers.ListField(**campo)


class FiltrosRelatorioAlimentacoesServidasSerializer(serializers.Serializer):
    """Valida os filtros do Relatório de Alimentações Servidas.

    O usuário é lido de ``context['usuario']``.
    """

    meses = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        error_messages={"not_a_list": MENSAGEM_MESES_OBRIGATORIO},
    )
    recreios_nas_ferias = _campo_uuids()
    dres = _campo_uuids(obrigatorio=True)
    lotes = _campo_uuids()
    subprefeituras = _campo_uuids()
    tipos_unidades = _campo_uuids()
    unidades_educacionais = _campo_uuids()
    tipos_alimentacao = _campo_uuids()
    periodo_lancamento_de = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    periodo_lancamento_ate = serializers.CharField(
        required=False, allow_blank=True, default=""
    )

    def validate(self, attrs):
        meses, recreios = _validar_regras(attrs, self.context.get("usuario"))
        attrs["meses"] = [f"{mes:02d}_{ano}" for mes, ano in meses]
        attrs["recreios_nas_ferias"] = recreios
        return attrs
