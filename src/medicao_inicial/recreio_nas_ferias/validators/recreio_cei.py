import datetime
from collections import defaultdict
from datetime import timedelta

from django.db.models import QuerySet

from src.escola.models import FaixaEtaria
from src.medicao_inicial.models import (
    CategoriaMedicao,
    GrupoMedicao,
    Medicao,
    SolicitacaoMedicaoInicial,
    ValorMedicao,
)
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_emef_emei_ceu_gesto_cieja import (
    existe_colaborador,
    get_classificacoes_dietas_recreio,
    get_tipos_alimentacao_recreio,
)

CATEGORIA_ALIMENTACAO_NOME = "ALIMENTAÇÃO"
CATEGORIA_DIETA_TIPO_A_ENTERAL_RESTRICAO_NOME = (
    "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
)
CATEGORIA_DIETA_TIPO_A = "DIETA ESPECIAL - TIPO A"


def cria_valores_medicao_participantes_cei(instance: SolicitacaoMedicaoInicial) -> None:
    """Cria os valores de medição de participantes do Recreio nas Férias de unidades CEI.

    Cria registros de ``ValorMedicao`` para cada dia do período do recreio,
    considerando os grupos participantes disponíveis na unidade escolar.

    Os valores são criados apenas quando ainda não existem para o dia,
    categoria e grupo informados.

    Args:
        instance (SolicitacaoMedicaoInicial): Solicitação de medição inicial vinculada ao recreio.
    """
    recreio = instance.recreio_nas_ferias
    participantes = recreio.unidades_participantes.filter(
        unidade_educacional=instance.escola
    ).first()

    informacoes_participantes = {
        "Recreio nas Férias": participantes.num_inscritos,
    }
    if existe_colaborador(participantes):
        informacoes_participantes["Colaboradores"] = participantes.num_colaboradores

    grupos = list(informacoes_participantes.keys())

    categoria = CategoriaMedicao.objects.get(nome=CATEGORIA_ALIMENTACAO_NOME)
    grupos_medicao_existentes = {
        medicao.grupo.nome: medicao
        for medicao in instance.medicoes.filter(grupo__nome__in=grupos).select_related(
            "grupo"
        )
    }
    grupos_obj = {
        grupo.nome: grupo for grupo in GrupoMedicao.objects.filter(nome__in=grupos)
    }

    valores_medicao_a_criar = []
    inicio_recreio = recreio.data_inicio
    dias_totais = (recreio.data_fim - inicio_recreio).days

    for numero_dia in range(dias_totais + 1):
        dia = f"{(inicio_recreio + timedelta(days=numero_dia)).day:02d}"
        for grupo in grupos:
            medicao = grupos_medicao_existentes.get(grupo)
            if medicao is None:
                medicao = Medicao.objects.create(
                    solicitacao_medicao_inicial=instance,
                    grupo=grupos_obj[grupo],
                )
                grupos_medicao_existentes[grupo] = medicao

            if not medicao.valores_medicao.filter(
                categoria_medicao=categoria,
                dia=dia,
                nome_campo="participantes",
            ).exists():
                valores_medicao_a_criar.append(
                    ValorMedicao(
                        medicao=medicao,
                        categoria_medicao=categoria,
                        dia=dia,
                        nome_campo="participantes",
                        valor=informacoes_participantes[grupo],
                    )
                )

    ValorMedicao.objects.bulk_create(valores_medicao_a_criar)


def cria_valores_medicao_participantes_dietas_autorizadas_cei(
    instance: SolicitacaoMedicaoInicial,
) -> None:
    """Cria os valores de medição de dietas autorizadas do recreio CEI.

    Cria registros de ``ValorMedicao`` para categorias de dietas especiais
    durante o período do Recreio nas Férias, utilizando os logs de dietas
    autorizadas da escola indexados por data, faixa etária e classificação..

    Os valores são criados para cada combinação de categoria, dia e faixa
    etária, apenas quando ainda não existir um registro correspondente.

    Somente categorias que possuam logs compatíveis no período do recreio
    são consideradas para criação dos valores.

    Args:
        instance (SolicitacaoMedicaoInicial): Solicitação de medição inicial vinculada ao recreio.
    """
    escola = instance.escola
    recreio = instance.recreio_nas_ferias
    inicio_recreio = recreio.data_inicio
    fim_recreio = recreio.data_fim

    logs_do_recreio = escola.logs_dietas_autorizadas_recreio_ferias_cei.filter(
        data__range=[inicio_recreio, fim_recreio],
        faixa_etaria__isnull=False,
    )
    logs_por_dia = indexar_logs_dieta_autorizadas_por_data(logs_do_recreio)

    grupo = "Recreio nas Férias"
    categorias = list(
        CategoriaMedicao.objects.filter(
            nome__in=[CATEGORIA_DIETA_TIPO_A, "DIETA ESPECIAL - TIPO B"]
        )
    )
    tipos_alimentacao = get_tipos_alimentacao_recreio(instance)
    categorias_validas = get_classificacoes_dietas_recreio(
        categorias, tipos_alimentacao
    )
    categorias_com_logs = [
        categoria
        for categoria in categorias_validas
        if _categoria_tem_logs_dieta_autorizada_cei(categoria, logs_por_dia)
    ]

    if not categorias_com_logs:
        return

    medicao = instance.medicoes.get(grupo__nome=grupo)
    valores_existentes = set(
        medicao.valores_medicao.filter(
            categoria_medicao__in=categorias_com_logs,
            nome_campo="dietas_autorizadas",
        ).values_list("categoria_medicao_id", "dia", "faixa_etaria")
    )
    resultados_ordenados = sorted(
        valores_existentes, key=lambda x: (int(x[1]), x[2], x[0])
    )

    valores_medicao_a_criar = []
    dias_totais = (fim_recreio - inicio_recreio).days
    faixas = FaixaEtaria.objects.filter(ativo=True)
    for numero_dia in range(dias_totais + 1):
        data = inicio_recreio + timedelta(days=numero_dia)
        dia = f"{data.day:02d}"
        for categoria in categorias_com_logs:
            for faixa_etaria in faixas:
                if (categoria.id, dia, faixa_etaria.id) in resultados_ordenados:
                    continue
                valor = retorna_valor_para_log_dieta_autorizada_cei(
                    categoria, logs_por_dia, data, faixa_etaria
                )
                valores_medicao_a_criar.append(
                    ValorMedicao(
                        medicao=medicao,
                        categoria_medicao=categoria,
                        dia=dia,
                        nome_campo="dietas_autorizadas",
                        valor=valor,
                        faixa_etaria=faixa_etaria,
                    )
                )

    ValorMedicao.objects.bulk_create(valores_medicao_a_criar)


def indexar_logs_dieta_autorizadas_por_data(
    logs_do_recreio: QuerySet,
) -> dict[datetime.date, dict[str, int]]:
    """Indexa logs de dietas autorizadas por data, faixa etária e classificação.

    Agrupa os logs por data e faixa etária, somando as quantidades para cada
    classificação de dieta correspondente. Os nomes das classificações são
    convertidos para minúsculas para facilitar buscas e comparações.

    Estrutura retornada:

        {
            data: {
                faixa_etaria: {
                    classificacao_nome: quantidade
                }
            }
        }

    Args:
        logs_do_recreio (QuerySet): QuerySet contendo os logs de dietas autorizadas
            para o período do recreio, com campos 'data', 'faixa_etaria', classificacao__nome' e 'quantidade'.

    Returns:
        dict[datetime.date, dict[str, int]]: Dicionário indexado por data, onde cada
            data mapeia para um dicionário de nomes de classificação (minúsculos) para
            a soma das quantidades.
    """
    logs_por_dia = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for (
        data_log,
        faixa_etaria,
        classificacao_nome,
        quantidade,
    ) in logs_do_recreio.values_list(
        "data", "faixa_etaria", "classificacao__nome", "quantidade"
    ):
        logs_por_dia[data_log][faixa_etaria][classificacao_nome.lower()] += quantidade

    return logs_por_dia


def _categoria_tem_logs_dieta_autorizada_cei(
    categoria: CategoriaMedicao,
    logs_por_dia: dict[datetime.date, dict[str, int]],
) -> bool:
    """Verifica se uma categoria de medição possui registros de dietas autorizadas.

    Percorre os logs indexados por data e faixa etária para identificar se há
    registros compatíveis com a categoria informada.

    Para a categoria especial ``TIPO A``, verifica a existência de qualquer
    classificação contendo ``"tipo a"`` nos logs.

    Para as demais categorias, extrai o termo da categoria a partir do nome
    (segmento após ``" - "``) e verifica se esse termo está presente nas
    classificações registradas.

    Os dados recebidos possuem a seguinte estrutura:

        {
            data: {
                faixa_etaria: {
                    classificacao_nome: quantidade
                }
            }
        }


    Args:
        categoria (CategoriaMedicao): A categoria de medição a ser verificada.
        logs_por_dia (dict[datetime.date, dict[str, int]]): Dados indexados dos logs por data.

    Returns:
        bool: True se a categoria possui logs autorizados, False caso contrário.
    """
    if categoria.nome == CATEGORIA_DIETA_TIPO_A:
        return any(
            any(
                "tipo a" in nome
                for logs_por_faixa in logs_por_dia_do_dia.values()
                for nome in logs_por_faixa
            )
            for logs_por_dia_do_dia in logs_por_dia.values()
        )

    termo = categoria.nome.split(" - ")[1].lower()
    return any(
        any(
            termo in nome
            for logs_por_faixa in logs_por_dia_do_dia.values()
            for nome in logs_por_faixa
        )
        for logs_por_dia_do_dia in logs_por_dia.values()
    )


def retorna_valor_para_log_dieta_autorizada_cei(
    categoria: CategoriaMedicao,
    logs_por_dia: dict[datetime.date, dict[str, int]],
    data: datetime.date,
    faixa_etaria: FaixaEtaria,
) -> int:
    """Retorna a quantidade autorizada para uma categoria, data e faixa etária.

    Os logs são indexados por data e faixa etária, contendo as classificações
    das dietas autorizadas e suas respectivas quantidades acumuladas.

    Estrutura esperada:

        {
            data: {
                faixa_etaria: {
                    classificacao_nome: quantidade
                }
            }
        }

    Para a categoria especial ``TIPO A``, realiza a soma de todas as
    classificações que contenham ``"tipo a"``.

    Para as demais categorias, retorna a primeira quantidade registrada para a
    faixa etária e data informadas.

    Args:
        categoria (CategoriaMedicao): Categoria de medição da dieta.
        logs_por_dia (dict): Logs de dietas autorizadas indexados por data e faixa etária..
        data (datetime.date): Data utilizada para filtrar os logs.
        faixa_etaria (FaixaEtaria): Faixa etária utilizada para filtrar os logs.

    Returns:
        int: Quantidade total autorizada para a categoria na data e faixa etária informado. Retorna ``0`` quando não houver registros.
    """
    logs_do_dia = logs_por_dia.get(data, {}).get(faixa_etaria.id, {})
    if categoria.nome == CATEGORIA_DIETA_TIPO_A:
        return sum(
            quantidade for nome, quantidade in logs_do_dia.items() if "tipo a" in nome
        )
    return next((quantidade for _, quantidade in logs_do_dia.items()), 0)
