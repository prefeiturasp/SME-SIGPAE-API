from datetime import datetime

from bs4 import BeautifulSoup
from django.template.loader import render_to_string

from .models import (
    AlergiaIntolerancia,
    Alimento,
    ClassificacaoDieta,
    ProtocoloPadraoDietaEspecial,
    SubstituicaoAlimento,
)


def atualiza_historico_protocolo(instance, dados_protocolo_novo):
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


def _extrair_texto_html(html):
    return BeautifulSoup(html, "html.parser").get_text(strip=True)


def _compara_alergias(instance, novas_alergias):
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


def _compara_classificacao(instance, nova_classificacao):
    if not nova_classificacao:
        return None

    classificacao = instance.classificacao
    id_classificacao_nova = int(nova_classificacao)
    if classificacao.id != id_classificacao_nova:
        classificacao_nova = ClassificacaoDieta.objects.get(id=id_classificacao_nova)
        return {"de": classificacao.nome, "para": classificacao_nova.nome}
    return None


def _compara_protocolo(instance, uuid_novo_procotolo):
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


def _compara_orientacoes(instance, nova_orientacao):
    if not nova_orientacao:
        return None
    orientacoes_gerais = instance.orientacoes_gerais
    if str(orientacoes_gerais) != nova_orientacao:
        texto_instance = _extrair_texto_html(orientacoes_gerais)
        texto_novo = _extrair_texto_html(nova_orientacao)
        return {"de": texto_instance, "para": texto_novo}
    return None


def _compara_data_de_termino(instance, nova_data_termino):
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


def _formata_data_termino(data_termino):
    if data_termino is None:
        texto = "Sem data término"
    else:
        texto = f"Com data de término {data_termino.strftime("%d/%m/%Y")}"
    return texto


def _compara_informacoes_adicionais(instance, nova_informacao):
    if not nova_informacao:
        return None
    informacoes_adicionais = instance.informacoes_adicionais
    if str(informacoes_adicionais) != nova_informacao:
        texto_instance = _extrair_texto_html(informacoes_adicionais)
        texto_novo = _extrair_texto_html(nova_informacao)
        return {"de": texto_instance, "para": texto_novo}
    return None


def normalizar_substituicao(sub):
    if isinstance(sub, SubstituicaoAlimento):
        info = {
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
        info = {
            "alimento": alimento.nome,
            "tipo": dict(SubstituicaoAlimento.TIPO_CHOICES).get(sub["tipo"]).upper(),
            "substitutos": [s.nome for s in alimentos_substitutos],
        }
    else:
        info = {}
    return info


def _compara_substituicoes(instance, substituicoes_novas):
    atuais = [
        normalizar_substituicao(s)
        for s in instance.substituicaoalimento_set.all().order_by("alimento__nome")
    ]
    novas = [normalizar_substituicao(s) for s in substituicoes_novas]
    inc, exc, alt = [], [], []

    alimentos_atuais = {s["alimento"]: s for s in atuais}
    alimentos_novos = {s["alimento"]: s for s in novas}

    for alimento, dados in alimentos_atuais.items():
        if alimento not in alimentos_novos:
            exc.append({"tipo": "ITEM EXCLUÍDO", "dados": dados})

    for alimento, dados in alimentos_novos.items():
        if alimento not in alimentos_atuais:
            inc.append({"tipo": "ITEM INCLUÍDO", "dados": dados})
        elif dados != alimentos_atuais[alimento]:
            alt.append(
                {
                    "tipo": "ITEM ALTERADO",
                    "de": {
                        "tipo": "ITEM ALTERADO DE",
                        "dados": alimentos_atuais[alimento],
                    },
                    "para": {"tipo": "ITEM ALTERADO PARA", "dados": dados},
                }
            )

    if not (inc or exc or alt):
        return None
    return {"incluidos": inc, "excluidos": exc, "alterados": alt}
