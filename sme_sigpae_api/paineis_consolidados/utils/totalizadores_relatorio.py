from collections import Counter

from sme_sigpae_api.dieta_especial.models import (
    AlergiaIntolerancia,
    ClassificacaoDieta,
    SolicitacaoDietaEspecial,
)
from sme_sigpae_api.escola.models import Escola, Lote, TipoGestao, TipoUnidadeEscolar


def count_query_set_sem_duplicados(query_set):
    return len(set(query_set.values_list("uuid", flat=True)))


def filtro_geral_totalizadores(request, model, queryset, map_filtros_=None):
    tipo_doc = request.data.get("tipos_solicitacao", [])
    tipo_doc = model.map_queryset_por_tipo_doc(tipo_doc)

    unidades_educacionais = request.data.get("unidades_educacionais", [])
    lotes = request.data.get("lotes", [])
    terceirizada = request.data.get("terceirizada", [])
    tipos_unidade = request.data.get("tipos_unidade", [])
    periodo_datas = {
        "data_evento": request.data.get("de", None),
        "data_evento_fim": request.data.get("ate", None),
    }

    queryset = model.busca_periodo_de_datas(
        queryset,
        data_evento=periodo_datas["data_evento"],
        data_evento_fim=periodo_datas["data_evento_fim"],
    )
    if not map_filtros_:
        map_filtros = {
            "lote_uuid__in": lotes,
            "escola_uuid__in": unidades_educacionais,
            "terceirizada_uuid": terceirizada,
            "tipo_doc__in": tipo_doc,
            "escola_tipo_unidade_uuid__in": tipos_unidade,
        }
    else:
        map_filtros = map_filtros_
    filtros = {
        key: value for key, value in map_filtros.items() if value not in [None, []]
    }
    queryset = queryset.filter(**filtros)
    return queryset


def totalizador_rede_municipal(request, queryset, list_cards_totalizadores):
    cei_polo = request.data.get("cei_polo", False)
    recreio_nas_ferias = request.data.get("recreio_nas_ferias", False)
    tipo_doc = request.data.get("tipos_solicitacao", [])
    unidades_educacionais = request.data.get("unidades_educacionais", [])
    lotes = request.data.get("lotes", [])
    terceirizada = request.data.get("terceirizada", [])
    tipos_unidade = request.data.get("tipos_unidade", [])
    periodo_datas = {
        "data_evento": request.data.get("de", None),
        "data_evento_fim": request.data.get("ate", None),
    }

    if cei_polo or recreio_nas_ferias:
        return list_cards_totalizadores

    nenhum_filtro = (
        not tipo_doc
        and not unidades_educacionais
        and not lotes
        and not terceirizada
        and not tipos_unidade
        and not periodo_datas["data_evento"]
        and not periodo_datas["data_evento_fim"]
    )
    if nenhum_filtro:
        key = (
            "Total"
            if request.user.tipo_usuario
            in ["escola", "diretoriaregional", "terceirizada"]
            else "Rede Municipal de Educação"
        )
        list_cards_totalizadores.append({key: count_query_set_sem_duplicados(queryset)})
    return list_cards_totalizadores


def totalizador_total(request, model, queryset, list_cards_totalizadores):
    tipo_doc = request.data.get("tipos_solicitacao", [])
    unidades_educacionais = request.data.get("unidades_educacionais", [])
    lotes = request.data.get("lotes", [])
    terceirizada = request.data.get("terceirizada", [])
    tipos_unidade = request.data.get("tipos_unidade", [])
    periodo_datas = {
        "data_evento": request.data.get("de", None),
        "data_evento_fim": request.data.get("ate", None),
    }

    nenhum_filtro = (
        not tipo_doc
        and not unidades_educacionais
        and not lotes
        and not terceirizada
        and not tipos_unidade
    )

    if (
        nenhum_filtro
        or periodo_datas["data_evento"]
        or periodo_datas["data_evento_fim"]
    ):
        return list_cards_totalizadores

    queryset = filtro_geral_totalizadores(request, model, queryset)
    list_cards_totalizadores.append({"Total": count_query_set_sem_duplicados(queryset)})
    return list_cards_totalizadores


def totalizador_lote(
    request, model, queryset, list_cards_totalizadores, string_polo_ou_recreio=None
):
    eh_relatorio_dietas_autorizadas = request.data.get(
        "relatorio_dietas_autorizadas", None
    )
    tipo_doc = request.data.get("tipos_solicitacao", [])
    tipo_doc = model.map_queryset_por_tipo_doc(tipo_doc)
    unidades_educacionais = (
        request.data.get("unidades_educacionais_selecionadas", [])
        if eh_relatorio_dietas_autorizadas
        else request.data.get("unidades_educacionais", [])
    )
    terceirizada = request.data.get("terceirizada", [])
    tipos_unidade = (
        request.data.get("tipos_unidades_selecionadas", [])
        if eh_relatorio_dietas_autorizadas
        else request.data.get("tipos_unidade", [])
    )
    classificacoes = request.data.get("classificacoes_selecionadas", [])
    alergias_ids = request.data.get("alergias_intolerancias_selecionadas", [])
    cei_polo = request.data.get("cei_polo", False)
    recreio_nas_ferias = request.data.get("recreio_nas_ferias", False)

    map_filtros = {
        "tipo_doc__in": tipo_doc,
        "terceirizada_uuid": terceirizada,
    }
    if eh_relatorio_dietas_autorizadas:
        map_filtros["escola_destino_tipo_unidade_uuid__in"] = tipos_unidade
        map_filtros["escola_destino_uuid__in"] = unidades_educacionais
        map_filtros["classificacao_id__in"] = classificacoes
        lotes = lotes_relatorio_dietas_autorizadas(request)
    else:
        map_filtros["escola_tipo_unidade_uuid__in"] = tipos_unidade
        map_filtros["escola_uuid__in"] = unidades_educacionais
        lotes = request.data.get("lotes", [])
    if not eh_relatorio_dietas_autorizadas and (not lotes or unidades_educacionais):
        return list_cards_totalizadores
    if eh_relatorio_dietas_autorizadas and not lotes:
        return list_cards_totalizadores
    queryset = filtro_geral_totalizadores(request, model, queryset, map_filtros)

    for lote_uuid in lotes:
        lote = Lote.objects.get(uuid=lote_uuid)
        if eh_relatorio_dietas_autorizadas:
            qs = queryset.filter(lote_escola_destino_uuid=lote_uuid)
            lista_uuids = [uuid for uuid in set(qs.values_list("uuid", flat=True))]
            qs = SolicitacaoDietaEspecial.objects.filter(uuid__in=lista_uuids)
            qs = queryset_dietas_lote(
                qs, alergias_ids, cei_polo, recreio_nas_ferias, string_polo_ou_recreio
            )
        else:
            qs = queryset.filter(lote_uuid=lote_uuid)
        list_cards_totalizadores.append(
            {
                f"{lote.nome} - {lote.diretoria_regional.nome if lote.diretoria_regional else 'sem DRE'}": count_query_set_sem_duplicados(
                    qs
                )
            }
        )
    return list_cards_totalizadores


def totalizador_tipo_solicitacao(request, model, queryset, list_cards_totalizadores):
    tipo_doc = request.data.get("tipos_solicitacao", [])
    lotes = request.data.get("lotes", [])
    terceirizada = request.data.get("terceirizada", [])
    tipos_unidade = request.data.get("tipos_unidade", [])
    unidades_educacionais = request.data.get("unidades_educacionais", [])

    if not tipo_doc:
        return list_cards_totalizadores

    map_filtros = {
        "lote_uuid__in": lotes,
        "escola_uuid__in": unidades_educacionais,
        "terceirizada_uuid": terceirizada,
        "escola_tipo_unidade_uuid__in": tipos_unidade,
    }
    queryset = filtro_geral_totalizadores(request, model, queryset, map_filtros)

    de_para_tipos_solicitacao = {
        "INC_ALIMENTA": "Inclusão de Alimentação",
        "ALT_CARDAPIO": "Alteração do tipo de Alimentação",
        "KIT_LANCHE_UNIFICADO": "Kit Lanche Unificado",
        "KIT_LANCHE_AVULSA": "Kit Lanche Passeio",
        "INV_CARDAPIO": "Inversão de dia de Cardápio",
        "SUSP_ALIMENTACAO": "Suspensão de Alimentação",
    }

    for tipo_solicitacao in tipo_doc:
        tipos_solicitacao_filtrar = model.map_queryset_por_tipo_doc([tipo_solicitacao])
        list_cards_totalizadores.append(
            {
                de_para_tipos_solicitacao[
                    tipo_solicitacao
                ]: count_query_set_sem_duplicados(
                    queryset.filter(tipo_doc__in=tipos_solicitacao_filtrar)
                )
            }
        )
    return list_cards_totalizadores


def totalizador_tipo_unidade(
    request, model, queryset, list_cards_totalizadores, string_polo_ou_recreio=None
):
    eh_relatorio_dietas_autorizadas = request.data.get(
        "relatorio_dietas_autorizadas", None
    )
    tipo_doc = request.data.get("tipos_solicitacao", [])
    tipo_doc = model.map_queryset_por_tipo_doc(tipo_doc)
    unidades_educacionais = (
        request.data.get("unidades_educacionais_selecionadas", [])
        if eh_relatorio_dietas_autorizadas
        else request.data.get("unidades_educacionais", [])
    )
    terceirizada = request.data.get("terceirizada", [])
    tipos_unidade = (
        request.data.get("tipos_unidades_selecionadas", [])
        if eh_relatorio_dietas_autorizadas
        else request.data.get("tipos_unidade", [])
    )
    classificacoes = request.data.get("classificacoes_selecionadas", [])
    alergias_ids = request.data.get("alergias_intolerancias_selecionadas", [])
    cei_polo = request.data.get("cei_polo", False)
    recreio_nas_ferias = request.data.get("recreio_nas_ferias", False)

    if not eh_relatorio_dietas_autorizadas and (
        not tipos_unidade or unidades_educacionais
    ):
        return list_cards_totalizadores
    if eh_relatorio_dietas_autorizadas and not tipos_unidade:
        return list_cards_totalizadores

    map_filtros = {
        "tipo_doc__in": tipo_doc,
        "terceirizada_uuid": terceirizada,
    }
    if eh_relatorio_dietas_autorizadas:
        lote = request.data.get("lote", [])
        map_filtros["lote_escola_destino_uuid"] = lote
        map_filtros["escola_destino_uuid__in"] = unidades_educacionais
        map_filtros["classificacao_id__in"] = classificacoes
    else:
        lotes = request.data.get("lotes", [])
        map_filtros["lote_uuid__in"] = lotes
    queryset = filtro_geral_totalizadores(request, model, queryset, map_filtros)

    for tipo_unidade_uuid in tipos_unidade:
        tipo_unidade = TipoUnidadeEscolar.objects.get(uuid=tipo_unidade_uuid)
        if eh_relatorio_dietas_autorizadas:
            qs = queryset.filter(escola_destino_tipo_unidade_uuid=tipo_unidade_uuid)
            lista_uuids = [uuid for uuid in set(qs.values_list("uuid", flat=True))]
            qs = SolicitacaoDietaEspecial.objects.filter(uuid__in=lista_uuids)
            qs = queryset_dietas_tipo_unidade(
                qs, alergias_ids, cei_polo, recreio_nas_ferias, string_polo_ou_recreio
            )
        else:
            qs = queryset.filter(escola_tipo_unidade_uuid=tipo_unidade_uuid)
        list_cards_totalizadores.append(
            {tipo_unidade.iniciais: count_query_set_sem_duplicados(qs)}
        )
    return list_cards_totalizadores


def totalizador_unidade_educacional(
    request, model, queryset, list_cards_totalizadores, string_polo_ou_recreio=None
):
    eh_relatorio_dietas_autorizadas = request.data.get(
        "relatorio_dietas_autorizadas", None
    )
    tipo_doc = request.data.get("tipos_solicitacao", [])
    tipo_doc = model.map_queryset_por_tipo_doc(tipo_doc)
    terceirizada = request.data.get("terceirizada", [])
    tipos_unidade = request.data.get("tipos_unidades_selecionadas", [])
    unidades_educacionais = (
        request.data.get("unidades_educacionais_selecionadas", [])
        if eh_relatorio_dietas_autorizadas
        else request.data.get("unidades_educacionais", [])
    )
    classificacoes = request.data.get("classificacoes_selecionadas", [])
    alergias_ids = request.data.get("alergias_intolerancias_selecionadas", [])
    cei_polo = request.data.get("cei_polo", False)
    recreio_nas_ferias = request.data.get("recreio_nas_ferias", False)

    if not unidades_educacionais:
        return list_cards_totalizadores

    map_filtros = {
        "tipo_doc__in": tipo_doc,
        "terceirizada_uuid": terceirizada,
    }
    if eh_relatorio_dietas_autorizadas:
        map_filtros["escola_destino_tipo_unidade_uuid__in"] = tipos_unidade
        map_filtros["classificacao_id__in"] = classificacoes
    queryset = filtro_geral_totalizadores(request, model, queryset, map_filtros)
    nomes_escolas = Escola.objects.filter(tipo_gestao__nome="TERC TOTAL").values_list(
        "uuid", "nome"
    )

    for unidade_educacional_uuid in unidades_educacionais:
        if eh_relatorio_dietas_autorizadas:
            lista_uuids = [
                uuid for uuid in set(queryset.values_list("uuid", flat=True))
            ]
            dietas = SolicitacaoDietaEspecial.objects.filter(uuid__in=lista_uuids)
            dietas_filtradas = dietas.filter(
                escola_destino__uuid=unidade_educacional_uuid
            )
            contagem = contagem_dietas_unidade_educacional(
                dietas_filtradas,
                alergias_ids,
                cei_polo,
                recreio_nas_ferias,
                string_polo_ou_recreio,
            )
        else:
            queryset = queryset.values("uuid", "escola_uuid", "escola_nome")
            campo_uuid_escola = "escola_uuid"
            contagem = len(
                set(
                    [
                        s["uuid"]
                        for s in queryset
                        if str(s[campo_uuid_escola]) == unidade_educacional_uuid
                    ]
                )
            )
        list_cards_totalizadores.append(
            {nomes_escolas.get(uuid=unidade_educacional_uuid)[1]: contagem}
        )
    return list_cards_totalizadores


def totalizador_periodo(request, model, queryset, list_cards_totalizadores):
    queryset = filtro_geral_totalizadores(request, model, queryset)
    periodo_datas = {
        "data_evento": request.data.get("de", None),
        "data_evento_fim": request.data.get("ate", None),
    }

    if periodo_datas["data_evento"] and not periodo_datas["data_evento_fim"]:
        list_cards_totalizadores.append(
            {
                f"Período: a partir de {periodo_datas['data_evento']}": count_query_set_sem_duplicados(
                    queryset
                )
            }
        )
    elif not periodo_datas["data_evento"] and periodo_datas["data_evento_fim"]:
        list_cards_totalizadores.append(
            {
                f"Período: até {periodo_datas['data_evento_fim']}": count_query_set_sem_duplicados(
                    queryset
                )
            }
        )
    elif periodo_datas["data_evento"] and periodo_datas["data_evento_fim"]:
        list_cards_totalizadores.append(
            {
                f"Período: {periodo_datas['data_evento']} até "
                f"{periodo_datas['data_evento_fim']}": count_query_set_sem_duplicados(
                    queryset
                )
            }
        )
    return list_cards_totalizadores


def totalizador_tipo_de_gestao(
    request, model, queryset, list_cards_totalizadores, string_polo_ou_recreio=None
):
    filtros = _obter_filtros_totalizador_tipo_de_gestao(request)
    if not filtros["tipo_gestao_uuid"]:
        return list_cards_totalizadores

    queryset = _aplicar_filtros_base(queryset, request, model, filtros)

    qs = _filtrar_solicitacoes_dieta(queryset, filtros, string_polo_ou_recreio)

    tipo_gestao_nome = (
        TipoGestao.objects.only("nome").get(uuid=filtros["tipo_gestao_uuid"]).nome
    )

    total = qs.distinct().count()
    list_cards_totalizadores.append({tipo_gestao_nome: total})
    return list_cards_totalizadores


def _obter_filtros_totalizador_tipo_de_gestao(request):
    return {
        "tipo_gestao_uuid": request.data.get("tipo_gestao"),
        "classificacoes": request.data.get("classificacoes_selecionadas", []),
        "tipos_unidade": request.data.get("tipos_unidades_selecionadas", []),
        "lote": request.data.get("lote", []),
        "unidades_educacionais": request.data.get(
            "unidades_educacionais_selecionadas", []
        ),
        "alergias_ids": request.data.get("alergias_intolerancias_selecionadas", []),
        "cei_polo": request.data.get("cei_polo", False),
        "recreio_nas_ferias": request.data.get("recreio_nas_ferias", False),
    }


def _aplicar_filtros_base(queryset, request, model, filtros):
    map_filtros = {
        "escola_tipo_gestao_uuid": filtros["tipo_gestao_uuid"],
        "classificacao_id__in": filtros["classificacoes"],
        "escola_destino_tipo_unidade_uuid__in": filtros["tipos_unidade"],
        "lote_escola_destino_uuid": filtros["lote"],
        "escola_destino_uuid__in": filtros["unidades_educacionais"],
    }
    return filtro_geral_totalizadores(request, model, queryset, map_filtros)


def _filtrar_solicitacoes_dieta(queryset, filtros, string_polo_ou_recreio):
    lista_uuids = queryset.values_list("uuid", flat=True).distinct()
    qs = SolicitacaoDietaEspecial.objects.filter(uuid__in=lista_uuids)

    if filtros["alergias_ids"]:
        qs = qs.filter(alergias_intolerancias__id__in=filtros["alergias_ids"])

    cei = filtros["cei_polo"]
    recreio = filtros["recreio_nas_ferias"]

    if cei and recreio:
        filtro = "polo" if string_polo_ou_recreio == "polo" else "recreio"
        qs = qs.filter(motivo_alteracao_ue__nome__icontains=filtro)
    elif cei:
        qs = qs.filter(motivo_alteracao_ue__nome__icontains="polo")
    elif recreio:
        qs = qs.filter(motivo_alteracao_ue__nome__icontains="recreio")

    return qs


def totalizador_classificacao_dieta(
    request, model, queryset, list_cards_totalizadores, string_polo_ou_recreio=None
):
    classificacoes = request.data.get("classificacoes_selecionadas", [])
    tipo_gestao_uuid = request.data.get("tipo_gestao", [])
    tipos_unidade = request.data.get("tipos_unidades_selecionadas", [])
    lote = request.data.get("lote", [])
    unidades_educacionais = request.data.get("unidades_educacionais_selecionadas", [])
    alergias_ids = request.data.get("alergias_intolerancias_selecionadas", [])
    cei_polo = request.data.get("cei_polo", False)
    recreio_nas_ferias = request.data.get("recreio_nas_ferias", False)

    if not classificacoes:
        return list_cards_totalizadores

    map_filtros = {
        "classificacao_id__in": classificacoes,
        "escola_tipo_gestao_uuid": tipo_gestao_uuid,
        "escola_destino_tipo_unidade_uuid__in": tipos_unidade,
        "lote_escola_destino_uuid": lote,
        "escola_destino_uuid__in": unidades_educacionais,
    }
    queryset = filtro_geral_totalizadores(request, model, queryset, map_filtros)
    lista_uuids = [uuid for uuid in set(queryset.values_list("uuid", flat=True))]
    dietas = SolicitacaoDietaEspecial.objects.filter(uuid__in=lista_uuids)

    for classificacao_id in classificacoes:
        classificacao = ClassificacaoDieta.objects.get(id=classificacao_id)
        dietas_filtradas = dietas.filter(classificacao__id=classificacao_id)
        contagem = dietas_filtradas.count()
        contagem = contagem_dietas_classificacao_dieta(
            contagem,
            alergias_ids,
            dietas_filtradas,
            cei_polo,
            recreio_nas_ferias,
            string_polo_ou_recreio,
        )
        list_cards_totalizadores.append({classificacao.nome: contagem})
    return list_cards_totalizadores


def totalizador_relacao_diagnostico(
    request, model, queryset, list_cards_totalizadores, string_polo_ou_recreio=None
):
    alergias_ids = request.data.get("alergias_intolerancias_selecionadas", [])
    tipo_gestao_uuid = request.data.get("tipo_gestao", [])
    tipos_unidade = request.data.get("tipos_unidades_selecionadas", [])
    lote = request.data.get("lote", [])
    unidades_educacionais = request.data.get("unidades_educacionais_selecionadas", [])
    classificacoes = request.data.get("classificacoes_selecionadas", [])
    cei_polo = request.data.get("cei_polo", False)
    recreio_nas_ferias = request.data.get("recreio_nas_ferias", False)

    if not alergias_ids:
        return list_cards_totalizadores

    map_filtros = {
        "escola_tipo_gestao_uuid": tipo_gestao_uuid,
        "escola_destino_tipo_unidade_uuid__in": tipos_unidade,
        "lote_escola_destino_uuid": lote,
        "escola_destino_uuid__in": unidades_educacionais,
        "classificacao_id__in": classificacoes,
    }

    queryset = filtro_geral_totalizadores(request, model, queryset, map_filtros)
    lista_uuids = queryset.values_list("uuid", flat=True).distinct()
    dietas = SolicitacaoDietaEspecial.objects.filter(
        uuid__in=lista_uuids
    ).prefetch_related("alergias_intolerancias")
    dietas = dietas_polo_recreio_relacao_diagnostico(
        dietas, cei_polo, recreio_nas_ferias, string_polo_ou_recreio
    )
    alergias = AlergiaIntolerancia.objects.filter(id__in=alergias_ids)
    alergias_dict = {a.id: a.descricao for a in alergias}
    contagens = Counter()

    for dieta in dietas:
        for alergia in dieta.alergias_intolerancias.all():
            if alergia.id in alergias_dict:
                contagens[alergia.id] += 1

    for alergia_id, descricao in alergias_dict.items():
        list_cards_totalizadores.append({descricao: contagens.get(alergia_id, 0)})

    return list_cards_totalizadores


def totalizador_cei_polo_recreio_ferias(
    request, model, queryset, list_cards_totalizadores, string_polo_ou_recreio=None
):
    cei_polo = request.data.get("cei_polo", False)
    recreio_nas_ferias = request.data.get("recreio_nas_ferias", False)
    tipo_gestao_uuid = request.data.get("tipo_gestao", [])
    tipos_unidade = request.data.get("tipos_unidades_selecionadas", [])
    lote = request.data.get("lote", [])
    unidades_educacionais = request.data.get("unidades_educacionais_selecionadas", [])
    classificacoes = request.data.get("classificacoes_selecionadas", [])
    alergias_ids = request.data.get("alergias_intolerancias_selecionadas", [])

    if not (cei_polo or recreio_nas_ferias):
        return list_cards_totalizadores

    map_filtros = {
        "escola_tipo_gestao_uuid": tipo_gestao_uuid,
        "escola_destino_tipo_unidade_uuid__in": tipos_unidade,
        "lote_escola_destino_uuid": lote,
        "escola_destino_uuid__in": unidades_educacionais,
        "classificacao_id__in": classificacoes,
    }
    queryset = filtro_geral_totalizadores(request, model, queryset, map_filtros)
    lista_uuids = [uuid for uuid in set(queryset.values_list("uuid", flat=True))]
    dietas = SolicitacaoDietaEspecial.objects.filter(uuid__in=lista_uuids)
    if alergias_ids:
        dietas = dietas.filter(alergias_intolerancias__in=alergias_ids).distinct()
    if cei_polo and not recreio_nas_ferias:
        dietas_filtradas = dietas.filter(motivo_alteracao_ue__nome__icontains="polo")
        list_cards_totalizadores.append({"CEI POLO": dietas_filtradas.count()})
    if recreio_nas_ferias and not cei_polo:
        dietas_filtradas = dietas.filter(motivo_alteracao_ue__nome__icontains="recreio")
        list_cards_totalizadores.append(
            {"RECREIO NAS FÉRIAS": dietas_filtradas.count()}
        )
    if cei_polo and recreio_nas_ferias:
        titulo_card = (
            "CEI POLO" if string_polo_ou_recreio == "polo" else "RECREIO NAS FÉRIAS"
        )
        dietas_cei_polo = dietas.filter(motivo_alteracao_ue__nome__icontains="polo")
        dietas_recreio_nas_ferias = dietas.filter(
            motivo_alteracao_ue__nome__icontains="recreio"
        )
        quantidade = (
            dietas_cei_polo.count()
            if string_polo_ou_recreio == "polo"
            else dietas_recreio_nas_ferias.count()
        )
        list_cards_totalizadores.append({titulo_card: quantidade})
    return list_cards_totalizadores


def dietas_polo_recreio_relacao_diagnostico(
    dietas, cei_polo, recreio_nas_ferias, string_polo_ou_recreio
):
    if cei_polo and not recreio_nas_ferias:
        dietas = dietas.filter(motivo_alteracao_ue__nome__icontains="polo")
    if recreio_nas_ferias and not cei_polo:
        dietas = dietas.filter(motivo_alteracao_ue__nome__icontains="recreio")
    if cei_polo and recreio_nas_ferias:
        dietas_ = dietas
        dietas_cei_polo = dietas_.filter(motivo_alteracao_ue__nome__icontains="polo")
        dietas_recreio_nas_ferias = dietas_.filter(
            motivo_alteracao_ue__nome__icontains="recreio"
        )
        dietas = (
            dietas_cei_polo
            if string_polo_ou_recreio == "polo"
            else dietas_recreio_nas_ferias
        )
    return dietas


def contagem_dietas_classificacao_dieta(
    contagem,
    alergias_ids,
    dietas_filtradas,
    cei_polo,
    recreio_nas_ferias,
    string_polo_ou_recreio,
):
    if alergias_ids:
        contagem = (
            dietas_filtradas.filter(alergias_intolerancias__in=alergias_ids)
            .distinct()
            .count()
        )
    if cei_polo and not recreio_nas_ferias:
        contagem = dietas_filtradas.filter(
            motivo_alteracao_ue__nome__icontains="polo"
        ).count()
    if recreio_nas_ferias and not cei_polo:
        contagem = dietas_filtradas.filter(
            motivo_alteracao_ue__nome__icontains="recreio"
        ).count()
    if cei_polo and recreio_nas_ferias:
        dietas_filtradas_ = dietas_filtradas
        dietas_filtradas_cei_polo = dietas_filtradas_.filter(
            motivo_alteracao_ue__nome__icontains="polo"
        )
        dietas_filtradas_recreio_nas_ferias = dietas_filtradas_.filter(
            motivo_alteracao_ue__nome__icontains="recreio"
        )
        dietas_filtradas = (
            dietas_filtradas_cei_polo
            if string_polo_ou_recreio == "polo"
            else dietas_filtradas_recreio_nas_ferias
        )
        contagem = dietas_filtradas.count()
    return contagem


def contagem_dietas_unidade_educacional(
    dietas_filtradas, alergias_ids, cei_polo, recreio_nas_ferias, string_polo_ou_recreio
):
    if alergias_ids:
        dietas_filtradas = dietas_filtradas.filter(
            alergias_intolerancias__in=alergias_ids
        ).distinct()
    if cei_polo and not recreio_nas_ferias:
        dietas_filtradas = dietas_filtradas.filter(
            motivo_alteracao_ue__nome__icontains="polo"
        )
    if recreio_nas_ferias and not cei_polo:
        dietas_filtradas = dietas_filtradas.filter(
            motivo_alteracao_ue__nome__icontains="recreio"
        )
    if cei_polo and recreio_nas_ferias:
        dietas_filtradas_ = dietas_filtradas
        dietas_filtradas_cei_polo = dietas_filtradas_.filter(
            motivo_alteracao_ue__nome__icontains="polo"
        )
        dietas_filtradas_recreio_nas_ferias = dietas_filtradas_.filter(
            motivo_alteracao_ue__nome__icontains="recreio"
        )
        dietas_filtradas = (
            dietas_filtradas_cei_polo
            if string_polo_ou_recreio == "polo"
            else dietas_filtradas_recreio_nas_ferias
        )
    contagem = dietas_filtradas.count()
    return contagem


def queryset_dietas_tipo_unidade(
    qs, alergias_ids, cei_polo, recreio_nas_ferias, string_polo_ou_recreio
):
    if alergias_ids:
        qs = qs.filter(alergias_intolerancias__in=alergias_ids).distinct()
    if cei_polo and not recreio_nas_ferias:
        qs = qs.filter(motivo_alteracao_ue__nome__icontains="polo")
    if recreio_nas_ferias and not cei_polo:
        qs = qs.filter(motivo_alteracao_ue__nome__icontains="recreio")
    if cei_polo and recreio_nas_ferias:
        qs_ = qs
        qs_cei_polo = qs_.filter(motivo_alteracao_ue__nome__icontains="polo")
        qs_recreio_nas_ferias = qs_.filter(
            motivo_alteracao_ue__nome__icontains="recreio"
        )
        qs = qs_cei_polo if string_polo_ou_recreio == "polo" else qs_recreio_nas_ferias
    return qs


def queryset_dietas_lote(
    qs, alergias_ids, cei_polo, recreio_nas_ferias, string_polo_ou_recreio
):
    if alergias_ids:
        qs = qs.filter(alergias_intolerancias__in=alergias_ids)
    if cei_polo and not recreio_nas_ferias:
        qs = qs.filter(motivo_alteracao_ue__nome__icontains="polo")
    if recreio_nas_ferias and not cei_polo:
        qs = qs.filter(motivo_alteracao_ue__nome__icontains="recreio")
    if cei_polo and recreio_nas_ferias:
        qs_ = qs
        qs_cei_polo = qs_.filter(motivo_alteracao_ue__nome__icontains="polo")
        qs_recreio_nas_ferias = qs_.filter(
            motivo_alteracao_ue__nome__icontains="recreio"
        )
        qs = qs_cei_polo if string_polo_ou_recreio == "polo" else qs_recreio_nas_ferias
    return qs


def lotes_relatorio_dietas_autorizadas(request):
    if request.data.get("lote"):
        lotes = [request.data.get("lote")]
    else:
        lotes = []
    return lotes
