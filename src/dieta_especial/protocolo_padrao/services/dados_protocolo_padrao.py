import json
from datetime import datetime


def preparar_dados_protocolo_padrao(protocolo):
    historico = json.loads(protocolo.historico) if protocolo.historico else []
    datas_atualizacao = []

    for registro in historico:
        data_atualizacao = registro.get("updated_at")

        if data_atualizacao:
            data_convertida = datetime.strptime(
                data_atualizacao,
                "%Y-%m-%d %H:%M:%S",
            )
            datas_atualizacao.append(data_convertida)

    ultima_atualizacao = protocolo.criado_em.date()

    if datas_atualizacao:
        ultima_atualizacao = max(datas_atualizacao).date()

    substituicoes = (
        protocolo.substituicoes
        .select_related("alimento")
        .prefetch_related("alimentos_substitutos", "substitutos")
        .order_by("alimento__nome")
    )

    return {
        "nome_protocolo": protocolo.nome_protocolo,
        "orientacoes_gerais": protocolo.orientacoes_gerais,
        "substituicoes": substituicoes,
        "editais": protocolo.editais.order_by("numero"),
        "data_ultima_atualizacao": ultima_atualizacao.strftime("%d/%m/%Y"),
    }
