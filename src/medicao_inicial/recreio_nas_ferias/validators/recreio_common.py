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


def agrupar_tipos_alimentacao_por_categoria(
    tipos_alimentacao: QuerySet,
) -> dict[str, list]:
    """Agrupa tipos de alimentação por categoria removendo duplicados.

    Os tipos de alimentação são agrupados pelo nome da categoria e os
    valores duplicados são removidos preservando a ordem de inserção.

    Args:
        tipos_alimentacao (QuerySet):
            QuerySet contendo os tipos de alimentação com os relacionamentos
            ``categoria`` e ``tipo_alimentacao``.

    Returns:
        dict[str, list]: Dicionário onde a chave é o nome da categoria e o valor é a
            lista de tipos de alimentação sem duplicados.
    """
    agrupados = defaultdict(list)

    for tipo in tipos_alimentacao.select_related(
        "categoria",
        "tipo_alimentacao",
    ):
        agrupados[tipo.categoria.nome].append(tipo.tipo_alimentacao.nome)

    resultado = {
        categoria: list(dict.fromkeys(itens)) for categoria, itens in agrupados.items()
    }

    return resultado


def valida_campo_participantes(
    instance: SolicitacaoMedicaoInicial, informacoes_participantes: dict[str, int]
) -> None:
    """Cria valores de medição para o campo ``participantes``.

    Garante que exista um registro de ``ValorMedicao`` para o campo
    ``participantes`` da categoria ``ALIMENTAÇÃO`` para cada grupo e para
    todos os dias do período do Recreio nas Férias associado à solicitação
    de medição.

    Caso a medição do grupo ainda não exista, ela será criada. Os valores
    de medição são criados apenas quando ainda não existirem para evitar
    duplicidades.

    Args:
        instance (SolicitacaoMedicaoInicial): Instância da solicitação de medição inicial vinculada ao
            Recreio nas Férias.
        informacoes_participantes (dict[str, int]): Dicionário contendo a quantidade de participantes por grupo,
            onde a chave representa o nome do grupo e o valor a quantidade de participantes
    """
    recreio = instance.recreio_nas_ferias
    categoria = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
    grupos = list(informacoes_participantes.keys())
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
