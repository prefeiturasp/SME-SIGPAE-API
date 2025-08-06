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
    alteracoes = {}
    alteracoes["Relação por Diagnóstico"] = _compara_alergias(
        instance=instance,
        novas=dados_protocolo_novo.get("alergias_intolerancias"),
    )
    alteracoes["Classificação da Dieta"] = _compara_classificacao(
        instance=instance,
        nova=dados_protocolo_novo.get("classificacao"),
    )
    alteracoes["Nome do Protocolo Padrão"] = _compara_protocolo(
        instance=instance,
        uuid_novo_procotolo=dados_protocolo_novo.get("protocolo_padrao"),
    )
    alteracoes["Orientações Gerais"] = _compara_orientacoes(
        instance=instance,
        nova_orientacao=dados_protocolo_novo.get("orientacoes_gerais"),
    )
    alteracoes["Substituições de Alimentos"] = _compara_substituicoes(
        instance=instance, substituicoes_novas=dados_protocolo_novo.get("substituicoes")
    )
    alteracoes["Data de término"] = _compara_data_de_termino(
        instance=instance,
        nova_data_termino=dados_protocolo_novo.get("data_termino"),
    )
    alteracoes["Informações adicionais"] = _compara_informacoes_adicionais(
        instance=instance,
        nova_informacao=dados_protocolo_novo.get("informacoes_adicionais"),
    )
    alteracoes_validas = {k: v for k, v in alteracoes.items() if v is not None}
    if alteracoes_validas:
        html_content = render_to_string(
            "dieta_especial/historico_atualizacao_dieta.html",
            {"alteracoes": alteracoes_validas},
        )
        with open(
            "/home/priscyla/spassu/pmsp/repositorios/SME-SIGPAE-API/log_protocolo.html",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(html_content)

        return html_content
    return ""


def _compara_alergias(instance, novas):
    if novas:
        alergias = instance.alergias_intolerancias.all().order_by("descricao")
        ids_alergias_atuais = set(alergias.values_list("id", flat=True))
        ids_alergias_novas = set(map(int, novas))
        if ids_alergias_atuais != ids_alergias_novas:
            nome_novas_alergias = (
                AlergiaIntolerancia.objects.filter(id__in=list(ids_alergias_novas))
                .values_list("descricao", flat=True)
                .order_by("descricao")
            )
            return {
                "de": ", ".join(alergia.descricao for alergia in alergias),
                "para": ", ".join(nome_novas_alergias),
            }
    return None


def _compara_classificacao(instance, nova):
    if nova:
        classificacao = instance.classificacao
        id_classificacao_nova = int(nova)
        if classificacao.id != id_classificacao_nova:
            classificacao_nova = ClassificacaoDieta.objects.get(
                id=id_classificacao_nova
            )
            return {"de": classificacao.nome, "para": classificacao_nova.nome}
    return None


def _compara_protocolo(instance, uuid_novo_procotolo):
    if uuid_novo_procotolo:
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
    if nova_orientacao:
        orientacoes_gerais = instance.orientacoes_gerais
        if str(orientacoes_gerais) != nova_orientacao:
            texto_instance = BeautifulSoup(orientacoes_gerais, "html.parser").get_text(
                strip=True
            )
            texto_novo = BeautifulSoup(nova_orientacao, "html.parser").get_text(
                strip=True
            )
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
        if data_termino_instance is None:
            de = "Sem data término"
        else:
            de = f"Com data de término {data_termino_instance.strftime("%d/%m/%Y")}"

        if nova_data_termino is None:
            para = "Sem data término"
        else:
            para = f"Com data de término {nova_data_termino.strftime("%d/%m/%Y")}"
        return {"de": de, "para": para}
    return None


def _compara_informacoes_adicionais(instance, nova_informacao):
    if nova_informacao:
        informacoes_adicionais = instance.informacoes_adicionais
        if str(informacoes_adicionais) != nova_informacao:
            texto_instance = BeautifulSoup(
                informacoes_adicionais, "html.parser"
            ).get_text(strip=True)
            texto_novo = BeautifulSoup(nova_informacao, "html.parser").get_text(
                strip=True
            )
            return {"de": texto_instance, "para": texto_novo}
    return None


def normalizar_substituicao(sub):
    if isinstance(sub, SubstituicaoAlimento):
        info = {
            "alimento": sub.alimento.nome,
            "tipo": dict(SubstituicaoAlimento.TIPO_CHOICES).get(sub.tipo).upper(),
            "substitutos": [s.nome for s in sub.alimentos_substitutos.all()],
        }
    elif "substitutos" in sub:
        alimento = Alimento.objects.get(id=int(sub["alimento"]))
        alimentos_substitutos = [
            Alimento.objects.get(uuid=s) for s in sub["substitutos"]
        ]
        info = {
            "alimento": alimento.nome,
            "tipo": dict(SubstituicaoAlimento.TIPO_CHOICES).get(sub["tipo"]).upper(),
            "substitutos": [s.nome for s in alimentos_substitutos],
        }
    else:
        info = {}
    return info


def _compara_substituicoes(instance, substituicoes_novas):
    substituicoes_atuais = instance.substituicaoalimento_set.all()
    atuais_normalizadas = [normalizar_substituicao(s) for s in substituicoes_atuais]
    novas_normalizadas = [normalizar_substituicao(s) for s in substituicoes_novas]

    informacoes_substituicao = {
        "incluidos": [],
        "excluidos": [],
        "alterados": [],
    }

    for sub in atuais_normalizadas:
        if not any(item["alimento"] == sub["alimento"] for item in novas_normalizadas):
            informacoes_substituicao["excluidos"].append(
                {"tipo": "ITEM EXCLUÍDO", "dados": sub}
            )

    for sub in novas_normalizadas:
        if not any(item["alimento"] == sub["alimento"] for item in atuais_normalizadas):
            informacoes_substituicao["incluidos"].append(
                {"tipo": "ITEM INCLUÍDO", "dados": sub}
            )

    for sub_atual in atuais_normalizadas:
        for sub_novo in novas_normalizadas:
            if sub_atual["alimento"] == sub_novo["alimento"] and sub_atual != sub_novo:
                informacoes_substituicao["alterados"].append(
                    {
                        "tipo": "ITEM ALTERADO",
                        "de": {"tipo": "ITEM ALTERADO DE", "dados": sub_atual},
                        "para": {"tipo": "ITEM ALTERADO PARA", "dados": sub_novo},
                    }
                )

    esta_vazio = all(
        not informacoes_substituicao.get(chave, [])
        for chave in informacoes_substituicao.keys()
    )
    return None if esta_vazio else informacoes_substituicao
