from datetime import datetime
from typing import Optional, Union

from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string

from src.dieta_especial.protocolo_padrao.models import (
    Alimento,
    ProtocoloPadraoDietaEspecial,
    SubstituicaoAlimento,
)
from src.dieta_especial.solicitacao_dieta_especial.models import (
    AlergiaIntolerancia,
    ClassificacaoDieta,
    SolicitacaoDietaEspecial,
)


def atualiza_historico_protocolo(
    instance: SolicitacaoDietaEspecial, dados_protocolo_novo: dict
) -> str:
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
            f"Ocorreu um erro ao gerar as informações do histórico: {e}"
        )


def remove_tag_p(html_conteudo: str) -> str:
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
    if data_termino is None:
        texto = "Sem data término"
    else:
        texto = f"Com data de término {data_termino.strftime('%d/%m/%Y')}"
    return texto


def _compara_informacoes_adicionais(
    instance: SolicitacaoDietaEspecial, nova_informacao: Optional[str]
) -> Optional[dict]:
    if not nova_informacao:
        return None
    informacoes_adicionais = instance.informacoes_adicionais
    if informacoes_adicionais != nova_informacao:
        texto_instance = remove_tag_p(informacoes_adicionais)
        texto_novo = remove_tag_p(nova_informacao)
        return {"de": texto_instance, "para": texto_novo}
    return None


def normalizar_substituicao(sub: Union[SubstituicaoAlimento, dict]) -> dict:
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
    return [
        {"tipo": "ITEM EXCLUÍDO", "dados": dados}
        for alimento, dados in atuais_dict.items()
        if alimento not in novos_dict
    ]


def _identifica_incluidos(atuais_dict: dict, novos_dict: dict) -> list[dict]:
    return [
        {"tipo": "ITEM INCLUÍDO", "dados": dados}
        for alimento, dados in novos_dict.items()
        if alimento not in atuais_dict
    ]


def _identifica_alterados(atuais_dict: dict, novos_dict: dict) -> list[dict]:
    return [
        {
            "tipo": "ITEM ALTERADO",
            "de": {"tipo": "ITEM ALTERADO DE", "dados": atuais_dict[alimento]},
            "para": {"tipo": "ITEM ALTERADO PARA", "dados": dados},
        }
        for alimento, dados in novos_dict.items()
        if alimento in atuais_dict and dados != atuais_dict[alimento]
    ]
