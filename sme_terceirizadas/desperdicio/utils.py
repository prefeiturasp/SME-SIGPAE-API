from django.db import connection
from django.core.paginator import Paginator, EmptyPage

SQL_RELATORIO_CONTROLE_RESTOS = """
    with medicao as (
        select mis.escola_id,
            (mis.ano || '-' || mis.mes || '-' || miv.dia)::date as data_medicao,
            sum(case when miv.nome_campo = 'frequencia' then miv.valor::numeric else 0 end) as frequencia,
            sum(case when miv.tipo_alimentacao_id is not null then miv.valor::numeric else 0 end) as num_refeicoes
        from medicao_inicial_solicitacaomedicaoinicial mis
        join medicao_inicial_medicao mim on mim.solicitacao_medicao_inicial_id = mis.id
        join medicao_inicial_valormedicao miv on miv.medicao_id = mim.id
        where (mis.ano || '-' || mis.mes || '-' || miv.dia)::date between %s::date and %s::date
        group by 1, 2
    ),
    restos as (
        select cr.escola_id, cr.data_medicao as data_medicao, cr.periodo,
            sum(cr.quantidade_distribuida) as quantidade_distribuida_soma,
            sum(cr.peso_resto) as peso_resto_soma
        from desperdicio_controlerestos cr
        join escola_escola e on e.id = cr.escola_id
        where cr.data_medicao between %s::date and %s::date
        [EXTRA_WHERE_CLAUSES]
        group by 1, 2, 3
    ),
    relatorio as (
        select m.data_medicao,
            r.periodo,
            dre.nome as dre_nome,
            ee.nome as escola_nome,
            r.quantidade_distribuida_soma,
            r.peso_resto_soma,
            m.num_refeicoes,
            CASE WHEN m.frequencia = 0 THEN 0 ELSE (r.peso_resto_soma / m.frequencia::numeric) END as resto_per_capita,
            CASE WHEN r.quantidade_distribuida_soma = 0 THEN 0 ELSE (r.peso_resto_soma / r.quantidade_distribuida_soma) END as percent_resto
        from medicao m
        join escola_escola ee on ee.id = m.escola_id
        join escola_diretoriaregional dre on dre.id = ee.diretoria_regional_id
        join restos r on m.escola_id = r.escola_id and m.data_medicao::date = r.data_medicao::date
        order by 1, 3
    )	
    select 
        r.*,
        (
            select dc.descricao from desperdicio_classificacao dc 
            where r.percent_resto <= dc.valor and dc.tipo = 'CR'
            order by valor
            limit 1
        ) as classificacao
    from relatorio r
"""

SQL_RELATORIO_CONTROLE_SOBRAS = """
    with medicao as (
        select mis.escola_id, (mis.ano || '-' || mis.mes || '-' || miv.dia)::date as data_medicao,
            case
                when miv.tipo_alimentacao_id is not null then miv.tipo_alimentacao_id
                when miv.nome_campo = 'repeticao_refeicao' then 2
                when miv.nome_campo = 'repeticao_sobremesa' then 4
            else null end as tipo_alimentacao_id,
            sum(case when miv.nome_campo like 'repeticao_%%' then 0 else miv.valor::numeric end) as total_primeira_oferta,
            sum(case when miv.nome_campo like 'repeticao_%%' then miv.valor::numeric else 0 end) as total_repeticao,
            sum(miv.valor::numeric) as total_refeicao
        from medicao_inicial_solicitacaomedicaoinicial mis
        join medicao_inicial_medicao mim on mim.solicitacao_medicao_inicial_id = mis.id
        join medicao_inicial_valormedicao miv on miv.medicao_id = mim.id
        where (miv.tipo_alimentacao_id is not null or miv.nome_campo ilike ('repeticao_%%'))
            and (mis.ano || '-' || mis.mes || '-' || miv.dia)::date between %s::date and %s::date
        group by 1, 2, 3
    ),
    frequencia as (
        select mis.escola_id, (mis.ano || '-' || mis.mes || '-' || miv.dia)::date as data_medicao, sum(miv.valor::numeric) as frequencia
        from medicao_inicial_solicitacaomedicaoinicial mis
        join medicao_inicial_medicao mim on mim.solicitacao_medicao_inicial_id = mis.id
        join medicao_inicial_valormedicao miv on miv.medicao_id = mim.id
        where miv.nome_campo = 'frequencia'
            and (mis.ano || '-' || mis.mes || '-' || miv.dia)::date between %s::date and %s::date
        group by 1, 2
    ),
    sobras as (
        select cs.escola_id, cs.data_medicao, cs.tipo_alimentacao_id, 
            ta.nome as tipo_alimento_nome, cs.periodo,
            sum(cs.peso_alimento) as peso_alimento,
            sum(cs.peso_sobra) as peso_sobra
        from desperdicio_controlesobras cs
        join produto_tipoalimento ta on ta.id = cs.tipo_alimento_id
        join escola_escola e on e.id = cs.escola_id
        where cs.data_medicao between %s::date and %s::date
        [EXTRA_WHERE_CLAUSES]
        group by 1, 2, 3, 4, 5
    ),
    relatorio as (
	    select m.data_medicao,
	        s.periodo,
	        dre.nome as dre_nome,
	        ee.nome as escola_nome,
	        ta.nome as tipo_alimentacao_nome,
	        s.tipo_alimento_nome,
	        coalesce((s.peso_alimento - s.peso_sobra), 0) as quantidade_distribuida,
	        coalesce(s.peso_sobra, 0) as peso_sobra,
	        coalesce(f.frequencia, 0) as frequencia,
	        coalesce(m.total_primeira_oferta, 0) as total_primeira_oferta,
	        coalesce(m.total_repeticao, 0) as total_repeticao,
	        CASE WHEN (s.peso_alimento - s.peso_sobra) = 0 THEN 0 ELSE (s.peso_sobra / (s.peso_alimento - s.peso_sobra)) END as percentual_sobra,
	        CASE WHEN f.frequencia = 0 THEN 0 ELSE (s.peso_sobra / f.frequencia) END as media_por_aluno,
	        CASE WHEN m.total_refeicao = 0 THEN 0 ELSE (s.peso_sobra / m.total_refeicao) END as media_por_refeicao
	    from medicao m
	    join escola_escola ee on ee.id = m.escola_id
	    join escola_diretoriaregional dre on dre.id = ee.diretoria_regional_id
	    join cardapio_tipoalimentacao ta on ta.id = m.tipo_alimentacao_id
	    join sobras s on s.escola_id = m.escola_id and s.data_medicao = m.data_medicao and s.tipo_alimentacao_id = m.tipo_alimentacao_id
	    join frequencia f on f.escola_id = m.escola_id and f.data_medicao = m.data_medicao and f.escola_id = s.escola_id and f.data_medicao = s.data_medicao
	    order by 1, 3, 4, 6	     
 	)
 	select 
        r.*,
        (
            select dc.descricao from desperdicio_classificacao dc 
            where r.percentual_sobra <= dc.valor and dc.tipo = 'CS'
            order by valor
            limit 1
        ) as classificacao
    from relatorio r
"""


def obtem_dados_relatorio_controle_restos(form_data, user):
    extra_where_clauses = ""

    data_inicial = form_data['data_inicial'].strftime('%Y-%m-%d')
    data_final = form_data['data_final'].strftime('%Y-%m-%d')

    extra_arguments = [
        data_inicial, data_final,
        data_inicial, data_final
    ]

    if user.tipo_usuario == 'escola':
        extra_where_clauses = "AND cr.escola_id = %s"
        extra_arguments.append(user.vinculo_atual.instituicao.id)
    elif form_data['escola']:
        extra_where_clauses = "AND cr.escola_id = %s"
        extra_arguments.append(form_data['escola'].id)
    elif form_data['dre']:
        extra_where_clauses = "AND e.diretoria_regional_id = %s"
        extra_arguments.append(form_data['dre'].id)

    sql = SQL_RELATORIO_CONTROLE_RESTOS.replace('[EXTRA_WHERE_CLAUSES]', extra_where_clauses)

    with connection.cursor() as cursor:
        cursor.execute(sql, extra_arguments)
        rows = cursor.fetchall()

    return rows


def obtem_dados_relatorio_controle_sobras(form_data, user):
    extra_where_clauses = ""

    data_inicial = form_data['data_inicial'].strftime('%Y-%m-%d')
    data_final = form_data['data_final'].strftime('%Y-%m-%d')

    extra_arguments = [
        data_inicial, data_final,
        data_inicial, data_final,
        data_inicial, data_final
    ]

    if user.tipo_usuario == 'escola':
        extra_where_clauses = "AND cs.escola_id = %s"
        extra_arguments.append(user.vinculo_atual.instituicao.id)
    elif form_data['escola']:
        extra_where_clauses = "AND cs.escola_id = %s"
        extra_arguments.append(form_data['escola'].id)
    elif form_data['dre']:
        extra_where_clauses = "AND e.diretoria_regional_id = %s"
        extra_arguments.append(form_data['dre'].id)

    sql = SQL_RELATORIO_CONTROLE_SOBRAS.replace('[EXTRA_WHERE_CLAUSES]', extra_where_clauses)

    with connection.cursor() as cursor:
        cursor.execute(sql, extra_arguments)
        rows = cursor.fetchall()

    return rows


def paginate_list(request, items_list, serializer, per_page=10):
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', per_page)

    paginator = Paginator(items_list, per_page)

    try:
        paginated_items = paginator.page(page)
    except EmptyPage:
        paginated_items = []

    data = {
        'count': paginator.count,
        'page_size': per_page,
        'results': [serializer(item) for item in paginated_items]
    }
    
    return data