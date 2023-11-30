from random import sample

from sme_terceirizadas.dados_comuns.models import Contato
from sme_terceirizadas.escola.models import DiretoriaRegional
from sme_terceirizadas.terceirizada.data.contratos import data_contratos
from sme_terceirizadas.terceirizada.data.editais import data_editais
from sme_terceirizadas.terceirizada.data.nutricionistas import data_nutricionistas
from sme_terceirizadas.terceirizada.data.terceirizadas import data_terceirizadas
from sme_terceirizadas.terceirizada.data.vigencias import data_vigencias
from sme_terceirizadas.terceirizada.models import (
    Contrato,
    Edital,
    Lote,
    Nutricionista,
    Terceirizada,
    VigenciaContrato,
)
from utility.carga_dados.helper import ja_existe, progressbar


def cria_edital():
    for item in progressbar(data_editais, "Edital"):
        _, created = Edital.objects.get_or_create(
            numero=item["numero"],
            tipo_contratacao=item["tipo_contratacao"],
            processo=item["processo"],
            objeto=item["objeto"],
        )
        if not created:
            ja_existe("Edital", item["numero"])


def cria_contratos():
    # FK e M2M
    # Valores randomicos
    lotes = list(Lote.objects.all())
    dres = list(DiretoriaRegional.objects.all())
    # Deleta contratos existentes.
    Contrato.objects.all().delete()
    edital = Edital.objects.first()
    for item in progressbar(data_contratos, "Contrato"):
        terceirizada = Terceirizada.objects.get(cnpj=item["terceirizada_cnpj"])
        lote_amostra = sample(lotes, 2)
        dre_amostra = sample(dres, 2)
        contrato = Contrato.objects.create(
            numero=item["numero"],
            processo=item["processo"],
            data_proposta=item["data_proposta"],
            edital=edital,
            terceirizada=terceirizada,
        )
        for item in lote_amostra:
            contrato.lotes.add(item)
        for item in dre_amostra:
            contrato.diretorias_regionais.add(item)


def cria_terceirizadas():
    for item in progressbar(data_terceirizadas, "Terceirizada"):
        terceirizada, created = Terceirizada.objects.get_or_create(
            cnpj=item["cnpj"],
            nome_fantasia=item["nome_fantasia"],
            razao_social=item["razao_social"],
            representante_legal=item["representante_legal"],
            representante_telefone=item["representante_telefone"],
            representante_email=item["representante_email"],
        )
        if not created:
            ja_existe("Terceirizada", item["cnpj"])


def adiciona_contato_em_terceirizada():
    contatos = list(Contato.objects.all())
    terceirizadas = Terceirizada.objects.all()
    for terceirizada in terceirizadas:
        contato_amostra = sample(contatos, 2)
        for item in contato_amostra:
            terceirizada.contatos.add(item)
