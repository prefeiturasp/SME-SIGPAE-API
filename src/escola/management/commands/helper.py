def calcula_total_alunos_por_escola(request_json_data: dict) -> dict:
    escola_total = {}
    escolas_quantidades_alunos = request_json_data["results"]

    for escola_data in escolas_quantidades_alunos:
        codigo_escola = escola_data["cd_escola"]
        total_corrente = escola_data["total"]
        if codigo_escola not in escola_total:
            escola_total[codigo_escola] = total_corrente
        else:
            escola_total[codigo_escola] += total_corrente

    return escola_total


def calcula_total_alunos_por_escola_por_periodo(request_json_data: dict) -> dict:
    """Recebe requisição da api do eol e trata.

    :param request_json_data: retorno da api do EOL
    :return: dict com várias chaves assim: '000078': {'manha': 163, 'intermediario': 161,
    'tarde': 0, 'vespertino': 186, 'noite': 175, 'integral': 0, 'total': 685}
    """
    response = {}
    totais_por_periodo = request_json_data["results"]

    for parcial_periodo in totais_por_periodo:
        codigo_escola = parcial_periodo["cd_escola"]

        manha = parcial_periodo["manha"]
        intermediario = parcial_periodo["intermediario"]
        tarde = parcial_periodo["tarde"]
        vespertino = parcial_periodo["vespertino"]
        noite = parcial_periodo["noite"]
        integral = parcial_periodo["integral"]
        total = parcial_periodo["total"]
        if codigo_escola not in response:
            response[codigo_escola] = {
                "manha": manha,
                "intermediario": intermediario,
                "tarde": tarde,
                "vespertino": vespertino,
                "noite": noite,
                "integral": integral,
                "total": total,
            }
        else:
            response[codigo_escola]["manha"] += manha
            response[codigo_escola]["intermediario"] += intermediario
            response[codigo_escola]["tarde"] += tarde
            response[codigo_escola]["vespertino"] += vespertino
            response[codigo_escola]["noite"] += noite
            response[codigo_escola]["integral"] += integral
            response[codigo_escola]["total"] += total
    return response
