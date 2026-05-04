from django.db import connection
from rest_framework.pagination import PageNumberPagination

MAPEAMENTO_STATUS_LABEL = {
    "CODAE_AUTORIZOU_RECLAMACAO": "RECLAMACAO_DE_PRODUTO",
    "CODAE_SUSPENDEU": "PRODUTOS_SUSPENSOS",
    "CODAE_QUESTIONADO": "PRODUTOS_AGUARDANDO_CORRECAO",
    "CODAE_PEDIU_ANALISE_RECLAMACAO": "PRODUTOS_ANALISE_RECLAMACAO",
    "CODAE_PEDIU_ANALISE_SENSORIAL": "PRODUTOS_AGUARDANDO_ANALISE_SENSORIAL",
    "CODAE_PENDENTE_HOMOLOGACAO": "PRODUTOS_PENDENTES_HOMOLOGACAO",
    "CODAE_HOMOLOGADO": "PRODUTOS_HOMOLOGADOS",
    "CODAE_NAO_HOMOLOGADO": "PRODUTOS_NAO_HOMOLOGADOS",
    "ESCOLA_OU_NUTRICIONISTA_RECLAMOU": "PRODUTOS_ANALISE_RECLAMACAO",
    "TERCEIRIZADA_RESPONDEU_RECLAMACAO": "PRODUTOS_ANALISE_RECLAMACAO",
}

SQL_RELATORIO_QUANTITATIVO = """
    SELECT terceirizada_terceirizada.nome_fantasia nome_terceirizada,
       produto_HomologacaoProduto.status,
       count(*)
    FROM django_content_type,
         perfil_vinculo,
         perfil_usuario,
         produto_HomologacaoProduto,
         produto_produto,
         terceirizada_terceirizada
    WHERE perfil_vinculo.content_type_id = django_content_type.id
      AND terceirizada_terceirizada.id = object_id
      AND perfil_vinculo.usuario_id = perfil_usuario.id
      AND produto_produto.criado_por_id = perfil_usuario.id
      AND produto_HomologacaoProduto.produto_id = produto_produto.id
      AND django_content_type.app_label = 'terceirizada'
      AND django_content_type.model = 'terceirizada'
      AND status != 'HOMOLOGACAO_INATIVA'
      {0}
    GROUP BY nome_terceirizada, status
    ORDER BY nome_terceirizada
"""

SQL_RELATORIO_QUANTITATIVO_POR_NOME = (
    "AND LOWER(terceirizada_terceirizada.nome_fantasia) LIKE %s"
)
SQL_RELATORIO_QUANTITATIVO_A_PARTIR_DE = "AND produto_produto.criado_em >= %s"
SQL_RELATORIO_QUANTITATIVO_ATE = (
    "AND produto_produto.criado_em < (to_date(%s, 'YYYY-MM-DD') + 1)"
)


def obtem_dados_relatorio_quantitativo(form_data):  # noqa C901
    extra_where_clauses = []
    extra_arguments = []

    if form_data["nome_terceirizada"] != "":
        extra_where_clauses.append(SQL_RELATORIO_QUANTITATIVO_POR_NOME)
        extra_arguments.append("%{0}%".format(form_data["nome_terceirizada"].lower()))
    if form_data["data_inicial"] is not None:
        extra_where_clauses.append(SQL_RELATORIO_QUANTITATIVO_A_PARTIR_DE)
        extra_arguments.append(form_data["data_inicial"].isoformat())
    if form_data["data_final"] is not None:
        extra_where_clauses.append(SQL_RELATORIO_QUANTITATIVO_ATE)
        extra_arguments.append(form_data["data_final"].isoformat())

    sql = SQL_RELATORIO_QUANTITATIVO.format(" ".join(extra_where_clauses))
    with connection.cursor() as cursor:
        cursor.execute(sql, extra_arguments)
        rows = cursor.fetchall()

    ultima_terceirizada = None
    lista_dados = []
    dados_terc_atual = {}
    total_produtos_terc_atual = 0

    for row in rows:
        if ultima_terceirizada is not None and row[0] != ultima_terceirizada:
            dados_terc_atual["total_produtos"] = total_produtos_terc_atual
            lista_dados.append(dados_terc_atual)
            ultima_terceirizada = None
            total_produtos_terc_atual = 0
        if ultima_terceirizada is None:
            dados_terc_atual = {
                "nome_terceirizada": row[0],
                "qtde_por_status": [{"status": row[1], "qtde": row[2]}],
            }
            ultima_terceirizada = row[0]
            total_produtos_terc_atual += row[2]
        elif row[0] == ultima_terceirizada:
            dados_terc_atual["qtde_por_status"].append(
                {"status": row[1], "qtde": row[2]}
            )
            total_produtos_terc_atual += row[2]

    if dados_terc_atual != {}:
        dados_terc_atual["total_produtos"] = total_produtos_terc_atual
        lista_dados.append(dados_terc_atual)

    retorno = {"results": lista_dados}

    if form_data["data_inicial"] is not None and form_data["data_final"] is not None:
        retorno["dias"] = (form_data["data_final"] - form_data["data_inicial"]).days
    return retorno


def transforma_dados_relatorio_quantitativo(dados):  # noqa C901
    qtde_por_status_zerado = {}
    relatorio = []
    total_produtos = 0

    for status in MAPEAMENTO_STATUS_LABEL.values():
        qtde_por_status_zerado[status] = 0

    for dados_terceirizada in dados["results"]:
        qtde_por_status = qtde_por_status_zerado.copy()
        total_produtos_terceirizada = 0
        for status_e_qtde in dados_terceirizada["qtde_por_status"]:
            qtde = status_e_qtde["qtde"]
            total_produtos_terceirizada += qtde
            total_produtos += qtde
            try:
                qtde_por_status[
                    MAPEAMENTO_STATUS_LABEL[status_e_qtde["status"]]
                ] += qtde
            except Exception:  # nosec
                pass
        relatorio.append(
            {
                "nomeTerceirizada": dados_terceirizada["nome_terceirizada"],
                "qtdePorStatus": qtde_por_status,
                "totalProdutos": total_produtos_terceirizada,
            }
        )

    retorno = {
        "totalProdutos": total_produtos,
        "detalhes": relatorio,
    }
    if "dias" in dados:
        retorno["qtdeDias"] = dados["dias"]
    return retorno


def serializa_emails_terceirizadas(query_emails):
    lista_emails = []
    if query_emails.count() > 0:
        for email in query_emails:
            data_email = {}
            data_email["uuid"] = email.uuid
            data_email["email"] = email.email
            data_email["modulo"] = email.modulo.nome
            lista_emails.append(data_email)

    return lista_emails


class TerceirizadasEmailsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
