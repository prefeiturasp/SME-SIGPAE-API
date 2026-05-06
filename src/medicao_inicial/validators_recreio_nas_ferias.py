from datetime import timedelta

from django.db.models import QuerySet

from src.medicao_inicial.models import (
    CategoriaMedicao,
    GrupoMedicao,
    Medicao,
    SolicitacaoMedicaoInicial,
    ValorMedicao,
)


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
