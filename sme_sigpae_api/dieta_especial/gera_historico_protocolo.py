from datetime import datetime
from typing import Optional, Union

from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string

from .models import (
    AlergiaIntolerancia,
    Alimento,
    ClassificacaoDieta,
    ProtocoloPadraoDietaEspecial,
    SolicitacaoDietaEspecial,
    SubstituicaoAlimento,
)


def atualiza_historico_protocolo(
    instance: SolicitacaoDietaEspecial, dados_protocolo_novo: dict
) -> str:
    """
    Atualiza o histórico de alterações de um protocolo de dieta especial.
    Compara os dados atuais do protocolo com os novos dados e gera um HTML com as diferenças.

    Args:
        instance (SolicitacaoDietaEspecial): Instância do modelo SolicitacaoDietaEspecial a ser comparada.
        dados_protocolo_novo (dict): Dicionário com os novos dados do protocolo.

    Raises:
        ValidationError: Se ocorrer algum erro durante o processamento das alterações.

    Returns:
        str: HTML com as alterações identificadas ou string vazia se não houver alterações.
    """
    try:
        alteracoes = {
            "Relação por Diagnóstico": _compara_alergias(
                instance, dados_protocolo_novo.get("alergias_intolerancias")
            ),
            "Classificação da Dieta": _compara_classificacao(
                instance, dados_protocolo_novo.get("classificacao")
            ),
            "Nome do Protocolo Padrão": _compara_protocolo(
                instance, dados_protocolo_novo.get("protocolo_padrao")
            ),
            "Orientações Gerais": _compara_orientacoes(
                instance, dados_protocolo_novo.get("orientacoes_gerais")
            ),
            "Substituições de Alimentos": _compara_substituicoes(
                instance, dados_protocolo_novo.get("substituicoes")
            ),
            "Data de término": _compara_data_de_termino(
                instance, dados_protocolo_novo.get("data_termino")
            ),
            "Informações adicionais": _compara_informacoes_adicionais(
                instance,
                dados_protocolo_novo.get("informacoes_adicionais"),
            ),
        }
        alteracoes_validas = {k: v for k, v in alteracoes.items() if v is not None}
        if alteracoes_validas:
            html_content = render_to_string(
                "dieta_especial/historico_atualizacao_dieta.html",
                {"alteracoes": alteracoes_validas},
            )
            return html_content
        return ""
    except Exception as e:
        raise ValidationError(
            f"Occoreu um erro ao gerar as informações do histórico: {e}"
        )


def remove_tag_p(html_conteudo: str) -> str:
    """
    Remove a primeira tag <p> e seu fechamento </p> de um conteúdo HTML,
    caso não existam listas (<ul>, <ol>) ou tabelas (<table>) em nenhuma parte do conteúdo.
    Caso haja qualquer uma dessas tags, mantém o HTML original.

    Args:
        html_conteudo (str): String contendo o HTML a ser processado.

    Returns:
        str: HTML modificado, sem o primeiro <p> se aplicável, ou o HTML original.
    """
    html_conteudo = html_conteudo.strip()
    if not html_conteudo.lower().startswith("<p>"):
        return html_conteudo

    soup = BeautifulSoup(html_conteudo, "html.parser")
    if soup.find(["ul", "ol", "table"]):
        return html_conteudo

    indice_fechamento = html_conteudo.lower().find("</p>")
    if indice_fechamento != -1:
        return (
            html_conteudo[len("<p>") : indice_fechamento]
            + html_conteudo[indice_fechamento + len("</p>") :]
        )

    return html_conteudo


def _compara_alergias(
    instance: SolicitacaoDietaEspecial, novas_alergias: Optional[list[str]]
) -> Optional[dict]:
    """
    Compara as alergias/intolerâncias atuais com as novas.

    Args:
        instance (SolicitacaoDietaEspecial): Instância do modelo SolicitacaoDietaEspecial com as alergias/intolerâncias atuais.
        novas_alergias (list[str]): Lista de IDs das novas alergias/intolerâncias.

    Returns:
        Optional[dict]: Dicionário com as descrições antigas e novas se houver diferença, None caso contrário.
    """
    if not novas_alergias:
        return None
    alergias = instance.alergias_intolerancias.all().order_by("descricao")
    ids_alergias_atuais = set(alergias.values_list("id", flat=True))
    ids_alergias_novas = set(map(int, novas_alergias))
    if ids_alergias_atuais != ids_alergias_novas:
        nome_novas_alergias = (
            AlergiaIntolerancia.objects.filter(id__in=list(ids_alergias_novas))
            .order_by("descricao")
            .values_list("descricao", flat=True)
        )
        return {
            "de": ", ".join(alergia.descricao for alergia in alergias),
            "para": ", ".join(nome_novas_alergias),
        }
    return None


def _compara_classificacao(
    instance: SolicitacaoDietaEspecial, nova_classificacao: Optional[str]
) -> Optional[dict]:
    """
    Compara a classificação atual da dieta com a nova.

    Args:
        instance (SolicitacaoDietaEspecial): Instância do modelo SolicitacaoDietaEspecial com a classificação atual.
        nova_classificacao (str): ID da nova classificação.

    Returns:
        Optional[dict]: Dicionário com os nomes antigo e novo se houver diferença, None caso contrário.ription_
    """
    if not nova_classificacao:
        return None

    classificacao = instance.classificacao
    id_classificacao_nova = int(nova_classificacao)
    if classificacao.id != id_classificacao_nova:
        classificacao_nova = ClassificacaoDieta.objects.get(id=id_classificacao_nova)
        return {"de": classificacao.nome, "para": classificacao_nova.nome}
    return None


def _compara_protocolo(
    instance: SolicitacaoDietaEspecial, uuid_novo_procotolo: Optional[str]
) -> Optional[dict]:
    """
    Compara o protocolo padrão atual com o novo.

    Args:
        instance (SolicitacaoDietaEspecial): Instância do modelo SolicitacaoDietaEspecial com o protocolo atual.
        uuid_novo_procotolo (Optional[str]): UUID do novo protocolo.

    Returns:
        Optional[dict]:  Dicionário com os nomes antigo e novo se houver diferença,  None caso contrário.
    """
    if not uuid_novo_procotolo:
        return None

    protocolo_padrao = instance.protocolo_padrao
    if str(protocolo_padrao.uuid) != uuid_novo_procotolo:
        protocolo_novo = ProtocoloPadraoDietaEspecial.objects.get(
            uuid=uuid_novo_procotolo
        )
        return {
            "de": protocolo_padrao.nome_protocolo,
            "para": protocolo_novo.nome_protocolo,
        }
    return None


def _compara_orientacoes(
    instance: SolicitacaoDietaEspecial, nova_orientacao: str
) -> Optional[dict]:
    """
    Compara as orientações gerais atuais com as novas.

    Args:
        instance (SolicitacaoDietaEspecial): Instância do modelo SolicitacaoDietaEspecial com as orientações atuais.
        nova_orientacao (str): Novas orientações em formato HTML

    Returns:
        Optional[dict]:  Dicionário com os textos antigo e novo se houver diferença, None caso contrário
    """
    if not nova_orientacao:
        return None
    orientacoes_gerais = instance.orientacoes_gerais
    if orientacoes_gerais != nova_orientacao:
        texto_instance = remove_tag_p(orientacoes_gerais)
        texto_novo = remove_tag_p(nova_orientacao)
        return {"de": texto_instance, "para": texto_novo}
    return None


def _compara_data_de_termino(
    instance: SolicitacaoDietaEspecial, nova_data_termino: Optional[str]
) -> Optional[dict]:
    """
    Compara a data de término atual com a nova.

    Args:
        instance (SolicitacaoDietaEspecial): Instância do modelo SolicitacaoDietaEspecial com a data atual.
        nova_data_termino (Optional[str]): Nova data de término no formato YYYY-MM-DD.

    Returns:
        Optional[dict]: Dicionário com as datas formatadas antiga e nova se houver diferença, None caso contrário
    """
    data_termino_instance = instance.data_termino
    nova_data_termino = (
        datetime.strptime(nova_data_termino, "%Y-%m-%d").date()
        if nova_data_termino
        else None
    )
    if data_termino_instance != nova_data_termino:
        return {
            "de": _formata_data_termino(data_termino_instance),
            "para": _formata_data_termino(nova_data_termino),
        }
    return None


def _formata_data_termino(data_termino: Optional[datetime.date]) -> str:
    """
    Formata a data de término para exibição.

    Args:
        data_termino (Optional[datetime.date]): Data a ser formatada.

    Returns:
        str: Texto formatado da data.
    """
    if data_termino is None:
        texto = "Sem data término"
    else:
        texto = f"Com data de término {data_termino.strftime("%d/%m/%Y")}"
    return texto


def _compara_informacoes_adicionais(
    instance: SolicitacaoDietaEspecial, nova_informacao: Optional[str]
) -> Optional[dict]:
    """
    Compara as informações adicionais atuais com as novas.

    Args:
        instance (SolicitacaoDietaEspecial):  Instância do modelo SolicitacaoDietaEspecial com as informações atuais.
        nova_informacao (Optional[str]): Novas informações adicionais em formato HTML.

    Returns:
        Optional[dict]: Dicionário com os textos antigo e novo se houver diferença, None caso contrário.
    """
    if not nova_informacao:
        return None
    informacoes_adicionais = instance.informacoes_adicionais
    if informacoes_adicionais != nova_informacao:
        texto_instance = remove_tag_p(informacoes_adicionais)
        texto_novo = remove_tag_p(nova_informacao)
        return {"de": texto_instance, "para": texto_novo}
    return None


def normalizar_substituicao(sub: Union[SubstituicaoAlimento, dict]) -> dict:
    """
    Normaliza os dados de substituição de alimento para comparação.

    Args:
        sub (Union[SubstituicaoAlimento, dict]): Pode ser uma instância de SubstituicaoAlimento ou um dicionário com os dados da substituição.

    Returns:
        dict: Dicionário normalizado com alimento, tipo e substitutos.
    """
    if isinstance(sub, SubstituicaoAlimento):
        return {
            "alimento": sub.alimento.nome,
            "tipo": dict(SubstituicaoAlimento.TIPO_CHOICES).get(sub.tipo).upper(),
            "substitutos": [
                s.nome for s in sub.alimentos_substitutos.all().order_by("nome")
            ],
        }
    elif "substitutos" in sub:
        alimento = Alimento.objects.get(id=int(sub["alimento"]))
        alimentos_substitutos = Alimento.objects.filter(
            uuid__in=sub["substitutos"]
        ).order_by("nome")
        return {
            "alimento": alimento.nome,
            "tipo": dict(SubstituicaoAlimento.TIPO_CHOICES).get(sub["tipo"]).upper(),
            "substitutos": [s.nome for s in alimentos_substitutos],
        }
    return None


def _compara_substituicoes(
    instance: SolicitacaoDietaEspecial, substituicoes_novas: list[dict]
) -> dict:
    """
    Compara as substituições de alimentos atuais com as novas.

    Args:
        instance (SolicitacaoDietaEspecial):  Instância do modelo SolicitacaoDietaEspecial com as substituições atuais..
        substituicoes_novas (list[dict]): Lista de novas substituições.

    Returns:
        dict: Dicionário com itens incluídos, excluídos e alterados se houver diferença, None caso contrário.
    """
    atuais = [
        normalizar_substituicao(s)
        for s in instance.substituicaoalimento_set.all().order_by("alimento__nome")
    ]
    novas = [normalizar_substituicao(s) for s in substituicoes_novas]
    alimentos_atuais = {s["alimento"]: s for s in atuais if s is not None}
    alimentos_novos = {s["alimento"]: s for s in novas if s is not None}

    incluidos = _identifica_incluidos(alimentos_atuais, alimentos_novos)
    excluidos = _identifica_excluidos(alimentos_atuais, alimentos_novos)
    alterados = _identifica_alterados(alimentos_atuais, alimentos_novos)

    if not (incluidos or excluidos or alterados):
        return None
    return {"incluidos": incluidos, "excluidos": excluidos, "alterados": alterados}


def _identifica_excluidos(atuais_dict: dict, novos_dict: dict) -> list[dict]:
    """
    Identifica itens que foram excluídos nas substituições.

    Args:
        atuais_dict (dict): Dicionário com substituições atuais.
        novos_dict (dict): Dicionário com novas substituições.

    Returns:
        list[dict]: Lista de dicionários com os itens excluídos.
    """
    return [
        {"tipo": "ITEM EXCLUÍDO", "dados": dados}
        for alimento, dados in atuais_dict.items()
        if alimento not in novos_dict
    ]


def _identifica_incluidos(atuais_dict: dict, novos_dict: dict) -> list[dict]:
    """
    Identifica itens que foram incluídos nas substituições.

    Args:
        atuais_dict (dict): Dicionário com substituições atuais.
        novos_dict (dict): Dicionário com novas substituições.

    Returns:
        list[dict]: Lista de dicionários com os itens incluídos.
    """
    return [
        {"tipo": "ITEM INCLUÍDO", "dados": dados}
        for alimento, dados in novos_dict.items()
        if alimento not in atuais_dict
    ]


def _identifica_alterados(atuais_dict: dict, novos_dict: dict) -> list[dict]:
    """
    Identifica itens que foram alterados nas substituições.

    Args:
        atuais_dict (dict): Dicionário com substituições atuais.
        novos_dict (dict): Dicionário com novas substituições.

    Returns:
        list[dict]: Lista de dicionários com os itens alterados.
    """
    return [
        {
            "tipo": "ITEM ALTERADO",
            "de": {"tipo": "ITEM ALTERADO DE", "dados": atuais_dict[alimento]},
            "para": {"tipo": "ITEM ALTERADO PARA", "dados": dados},
        }
        for alimento, dados in novos_dict.items()
        if alimento in atuais_dict and dados != atuais_dict[alimento]
    ]
