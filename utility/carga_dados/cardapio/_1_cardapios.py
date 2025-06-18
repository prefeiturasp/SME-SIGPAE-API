"""
Antes de rodar isso vc deve ter rodado as escolas e as fixtures
"""

import datetime
import random

from faker import Faker

from sme_sigpae_api.cardapio.base.models import Cardapio, TipoAlimentacao
from sme_sigpae_api.dados_comuns.utils import eh_dia_util
from sme_sigpae_api.escola.models import TipoUnidadeEscolar
from sme_sigpae_api.terceirizada.models import Edital

f = Faker("pt-br")
f.seed(420)
hoje = datetime.datetime.today()

edital = Edital.objects.first()


def gera_muitos_cardapios(qtd=360):
    tipos_alimentacao = TipoAlimentacao.objects.all()
    cont = 0
    alimentacoes_selecionadas = []
    for i in range(qtd):
        for _ in range(5):
            x = random.choice(tipos_alimentacao)
            alimentacoes_selecionadas.append(x)

        novodia = hoje + datetime.timedelta(days=i)
        if eh_dia_util(novodia):
            cardapio, created_cardapio = Cardapio.objects.get_or_create(
                data=novodia, edital=edital, descricao=f.text()
            )
            if created_cardapio:
                cont += 1
                cardapio.tipos_alimentacao.set(
                    alimentacoes_selecionadas
                )  # vincula tp alim para cardapio
                print(f"Criado cardapio {cardapio}")
        alimentacoes_selecionadas = []
    print(f"Total de cardapios criados... {cont}")


gera_muitos_cardapios(qtd=720)


def vincula_unidades_escolares_a_cardapios():
    ues = TipoUnidadeEscolar.objects.all()
    cardapios = Cardapio.objects.all()
    for ue in ues:
        ue.cardapios.set(cardapios)


vincula_unidades_escolares_a_cardapios()
