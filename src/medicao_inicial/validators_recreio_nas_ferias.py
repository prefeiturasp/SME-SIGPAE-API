from collections import defaultdict
from datetime import timedelta

from django.db.models import QuerySet

from src.medicao_inicial.models import (
    CategoriaMedicao,
    GrupoMedicao,
    Medicao,
    SolicitacaoMedicaoInicial,
    ValorMedicao,
)
from src.medicao_inicial.recreio_nas_ferias.utils import gerar_dias_letivos_recreio
from src.medicao_inicial.utils import get_name_campo
from src.medicao_inicial.validators import checa_valor_observacao, erros_unicos


def cria_valores_medicao_participantes_emef_emei(
    instance: SolicitacaoMedicaoInicial,
) -> None:
    """Cria os valores de medição de participantes do Recreio nas Férias.

    Cria registros de ``ValorMedicao`` para cada dia do período do recreio,
    considerando os grupos participantes disponíveis na unidade escolar.

    Os valores são criados apenas quando ainda não existem para o dia,
    categoria e grupo informados.

    Args:
        instance (SolicitacaoMedicaoInicial): Solicitação de medição inicial vinculada ao recreio.
    """
    valores_medicao_a_criar = []
    recreio = instance.recreio_nas_ferias

    participantes = recreio.unidades_participantes.first()
    informacoes_participantes = {
        "Recreio nas Férias": participantes.num_inscritos,
        "Colaboradores": participantes.num_colaboradores,
    }
    grupos = [
        grupo
        for grupo, quantidade in informacoes_participantes.items()
        if quantidade > 0
    ]

    categoria = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
    inicio_recreio = recreio.data_inicio
    dias_totais = (recreio.data_fim - inicio_recreio).days
    for numero_dia in range(dias_totais + 1):
        data = inicio_recreio + timedelta(days=numero_dia)
        dia = data.day
        for grupo in grupos:
            try:
                medicao = instance.medicoes.get(grupo__nome=grupo)
            except Medicao.DoesNotExist:
                medicao = Medicao.objects.create(
                    solicitacao_medicao_inicial=instance,
                    grupo=GrupoMedicao.objects.get(nome=grupo),
                )
            if not medicao.valores_medicao.filter(
                categoria_medicao=categoria,
                dia=f"{dia:02d}",
                nome_campo="participantes",
            ).exists():
                valor_medicao = ValorMedicao(
                    medicao=medicao,
                    categoria_medicao=categoria,
                    dia=f"{dia:02d}",
                    nome_campo="participantes",
                    valor=informacoes_participantes[grupo],
                )
                valores_medicao_a_criar.append(valor_medicao)

    ValorMedicao.objects.bulk_create(valores_medicao_a_criar)


def cria_valores_medicao_participantes_dietas_autorizadas_emef_emei(
    instance: SolicitacaoMedicaoInicial,
) -> None:
    """Cria os valores de medição de dietas autorizadas do recreio.

    Cria registros de ``ValorMedicao`` para categorias de dietas especiais
    durante o período do Recreio nas Férias, utilizando os logs de dietas
    autorizadas da escola.

    Os valores são criados apenas quando ainda não existem para o dia,
    categoria e grupo informados

    Args:
        instance (SolicitacaoMedicaoInicial): Solicitação de medição inicial vinculada ao recreio.
    """
    escola = instance.escola
    valores_medicao_a_criar = []
    recreio = instance.recreio_nas_ferias
    inicio_recreio = recreio.data_inicio
    fim_recreio = recreio.data_fim

    logs_do_recreio = escola.logs_dietas_autorizadas_recreio_ferias.filter(
        data__gte=inicio_recreio,
        data__lte=fim_recreio,
    )
    grupo = "Recreio nas Férias"
    categorias = CategoriaMedicao.objects.filter(nome__icontains="dieta")

    dias_totais = (fim_recreio - inicio_recreio).days
    for numero_dia in range(dias_totais + 1):
        data = inicio_recreio + timedelta(days=numero_dia)
        dia = data.day
        for categoria in categorias:
            medicao = instance.medicoes.get(grupo__nome=grupo)
            if checa_se_existe_ao_menos_um_log_quantidade_maior_que_0(
                categoria, logs_do_recreio
            ):
                continue
            if not medicao.valores_medicao.filter(
                categoria_medicao=categoria,
                dia=f"{dia:02d}",
                nome_campo="dietas_autorizadas",
            ).exists():
                valor = retorna_valor_para_log_dieta_autorizada(
                    categoria, logs_do_recreio, dia
                )
                valor_medicao = ValorMedicao(
                    medicao=medicao,
                    categoria_medicao=categoria,
                    dia=f"{dia:02d}",
                    nome_campo="dietas_autorizadas",
                    valor=valor,
                )
                valores_medicao_a_criar.append(valor_medicao)
    ValorMedicao.objects.bulk_create(valores_medicao_a_criar)


def checa_se_existe_ao_menos_um_log_quantidade_maior_que_0(
    categoria: CategoriaMedicao, logs_do_mes: QuerySet
) -> bool:
    """Verifica se existem logs com quantidade maior que zero.

    Para categorias do tipo enteral/restrição de aminoácidos, considera
    ambas as classificações no filtro.

    Args:
        categoria (CategoriaMedicao):  Categoria de medição da dieta.
        logs_do_mes (QuerySet): Queryset contendo os logs de dietas autorizadas.

    Returns:
        bool: ``True`` quando não existem logs válidos para a categoria.
            ``False`` quando existem logs com quantidade maior que zero.
    """
    if categoria == CategoriaMedicao.objects.get(
        nome="DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
    ):
        if not logs_do_mes.filter(
            classificacao__nome__in=[
                "Tipo A ENTERAL",
                "Tipo A RESTRIÇÃO DE AMINOÁCIDOS",
            ],
            quantidade__gt=0,
        ).exists():
            return True
    else:
        if (
            not logs_do_mes.filter(
                classificacao__nome__icontains=categoria.nome.split(" - ")[1],
                quantidade__gt=0,
            )
            .exclude(classificacao__nome__icontains="enteral")
            .exclude(classificacao__nome__icontains="aminoácidos")
            .exists()
        ):
            return True
    return False


def retorna_valor_para_log_dieta_autorizada(
    categoria: CategoriaMedicao,
    logs_do_mes: QuerySet,
    dia: int,
) -> int:
    """Retorna o valor total autorizado para a categoria e dia informados.

    Para categorias do tipo enteral/restrição de aminoácidos, realiza a soma
    das duas classificações.


    Args:
        categoria (CategoriaMedicao): Categoria de medição da dieta.
        logs_do_mes (QuerySet): Queryset contendo os logs de dietas autorizadas.
        dia (int): Dia do mês utilizado para filtrar os logs.

    Returns:
        int:  Quantidade total autorizada para a categoria no dia informado.
    """
    if categoria == CategoriaMedicao.objects.get(
        nome="DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
    ):
        log_enteral = logs_do_mes.filter(
            classificacao__nome__icontains="enteral",
            data__day=dia,
        ).first()
        log_restricao_aminoacidos = logs_do_mes.filter(
            classificacao__nome__icontains="aminoácidos",
            data__day=dia,
        ).first()
        valor = (log_enteral.quantidade if log_enteral else 0) + (
            log_restricao_aminoacidos.quantidade if log_restricao_aminoacidos else 0
        )
    else:
        log = (
            logs_do_mes.filter(
                classificacao__nome__icontains=categoria.nome.split(" - ")[1],
                data__day=dia,
            )
            .exclude(classificacao__nome__icontains="enteral")
            .exclude(classificacao__nome__icontains="aminoácidos")
            .first()
        )
        valor = log.quantidade if log else 0
    return valor


def validate_lancamento_alimentacoes_medicao_recreio(
    solicitacao: SolicitacaoMedicaoInicial, lista_erros: list
) -> list:
    """Valida o preenchimento das alimentações do recreio.

    Verifica se todos os dias letivos do período do recreio possuem
    lançamentos preenchidos para os grupos e alimentações esperadas.

    Quando existem dias sem preenchimento e sem justificativa
    de observação, adiciona erro à lista de erros.

    Args:
        solicitacao (SolicitacaoMedicaoInicial): Solicitação de medição inicial do recreio.
        lista_erros (list): Lista acumulada de erros de validação.

    Returns:
        list: Lista de erros sem duplicidade.
    """

    recreio = solicitacao.recreio_nas_ferias
    participantes = recreio.unidades_participantes.first()

    tipos_alimentacao = participantes.tipos_alimentacao.filter(
        categoria__nome__in=["Inscritos", "Colaboradores"]
    )
    tipos_alimentacao_map = agrupar_tipos_alimentacao_por_categoria(tipos_alimentacao)
    informacoes_alimentacao = {
        "Recreio nas Férias": tipos_alimentacao_map.get("Inscritos", [])
    }
    if participantes.num_colaboradores > 0:
        informacoes_alimentacao["Colaboradores"] = tipos_alimentacao_map.get(
            "Colaboradores", []
        )

    grupos = list(informacoes_alimentacao.keys())

    categoria_medicao = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
    dias_letivos_geral = gerar_dias_letivos_recreio(
        recreio.data_inicio, recreio.data_fim
    )
    dias_letivos_geral_formatado = [f"{dia:02d}" for dia in dias_letivos_geral]

    for grupo in grupos:
        linhas_da_tabela = get_linhas_da_tabela_recreio(informacoes_alimentacao[grupo])
        lista_erros = buscar_valores_lancamento_alimentacoes_recreio(
            linhas_da_tabela,
            solicitacao,
            grupo,
            dias_letivos_geral_formatado,
            categoria_medicao,
            lista_erros,
        )
    return erros_unicos(lista_erros)


def agrupar_tipos_alimentacao_por_categoria(
    tipos_alimentacao: QuerySet,
) -> dict[str, list]:
    """Agrupa tipos de alimentação por categoria.

    Args:
        tipos_alimentacao (QuerySet):
            Queryset contendo os tipos de alimentação.

    Returns:
        dict[str, list]: Dicionário com os tipos de alimentação agrupados
            pelo nome da categoria.
    """
    agrupados = defaultdict(list)

    for tipo in tipos_alimentacao.select_related(
        "categoria",
        "tipo_alimentacao",
    ):
        agrupados[tipo.categoria.nome].append(tipo.tipo_alimentacao.nome)

    return dict(agrupados)


def get_linhas_da_tabela_recreio(alimentacoes: list[str]) -> list[str]:
    """Monta as linhas esperadas da tabela de alimentações.

    Adiciona os campos obrigatórios de participantes e frequência,
    além das alimentações configuradas para o grupo.

    Também adiciona os campos de repetição quando aplicável.

    Args:
        alimentacoes (list[str]): Lista de alimentações configuradas para o grupo.

    Returns:
        list[str]:   Lista contendo os nomes dos campos esperados na tabela de lançamento.
    """
    linhas_da_tabela = ["participantes", "frequencia"]
    for alimentacao in alimentacoes:
        nome_formatado = get_name_campo(alimentacao)
        linhas_da_tabela.append(nome_formatado)
        if nome_formatado == "refeicao":
            linhas_da_tabela.append("repeticao_refeicao")
        if nome_formatado == "sobremesa":
            linhas_da_tabela.append("repeticao_sobremesa")
    return linhas_da_tabela


def buscar_valores_lancamento_alimentacoes_recreio(
    linhas_da_tabela: list[str],
    solicitacao: SolicitacaoMedicaoInicial,
    grupo: str,
    dias_letivos: list[str],
    categoria_medicao: CategoriaMedicao,
    lista_erros: list,
) -> list:
    """Valida os lançamentos das alimentações do recreio.

    Verifica se todos os campos esperados da tabela possuem
    valores preenchidos para todos os dias letivos do período.

    Quando existem dias sem preenchimento e sem observação
    justificando a ausência, adiciona erro na lista.

    Args:
        linhas_da_tabela (list[str]): Lista de campos esperados na tabela.
        solicitacao (SolicitacaoMedicaoInicial):  Solicitação de medição inicial.
        grupo (str):  Nome do grupo validado.
        dias_letivos (list[str]):  Lista de dias letivos formatados.
        categoria_medicao (CategoriaMedicao): Categoria de medição utilizada na validação.
        lista_erros (list): Lista acumulada de erros.

    Returns:
        list: Lista atualizada de erros encontrados.
    """
    periodo_com_erro = False
    for nome_campo in linhas_da_tabela:
        valores_da_medicao = (
            ValorMedicao.objects.filter(
                medicao__solicitacao_medicao_inicial=solicitacao,
                nome_campo=nome_campo,
                medicao__grupo__nome=grupo,
                dia__in=dias_letivos,
                categoria_medicao=categoria_medicao,
            )
            .exclude(valor=None)
            .values_list("dia", flat=True)
        )
        valores_da_medicao = list(set(valores_da_medicao))
        if len(valores_da_medicao) != len(dias_letivos):
            diferenca = list(set(dias_letivos) - set(valores_da_medicao))
            for dia_sem_preenchimento in diferenca:
                valor_observacao = ValorMedicao.objects.filter(
                    medicao__solicitacao_medicao_inicial=solicitacao,
                    nome_campo="observacao",
                    medicao__grupo__nome=grupo,
                    dia=dia_sem_preenchimento,
                    categoria_medicao=categoria_medicao,
                ).exclude(valor=None)
                periodo_com_erro = checa_valor_observacao(
                    valor_observacao, periodo_com_erro
                )
    if periodo_com_erro:
        lista_erros.append(
            {
                "periodo_escolar": grupo,
                "erro": "Restam dias a serem lançados nas alimentações.",
            }
        )
    return lista_erros
