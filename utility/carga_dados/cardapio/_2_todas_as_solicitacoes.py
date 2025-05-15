"""
    Antes de rodar isso vc deve ter rodado as escolas e as fixtures
"""
import datetime
import random

import numpy as np
from faker import Faker
from xworkflows import InvalidTransitionError

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    AlteracaoCardapio,
    MotivoAlteracaoCardapio,
)
from sme_sigpae_api.cardapio.base.models import Cardapio, TipoAlimentacao
from sme_sigpae_api.cardapio.inversao_dia_cardapio.models import InversaoCardapio
from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    MotivoSuspensao,
    QuantidadePorPeriodoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
)
from sme_sigpae_api.escola.models import DiretoriaRegional, Escola, PeriodoEscolar
from sme_sigpae_api.inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
    InclusaoAlimentacaoNormal,
    MotivoInclusaoContinua,
    MotivoInclusaoNormal,
    QuantidadePorPeriodo,
)
from sme_sigpae_api.kit_lanche.models import (
    EscolaQuantidade,
    KitLanche,
    SolicitacaoKitLanche,
    SolicitacaoKitLancheAvulsa,
    SolicitacaoKitLancheUnificada,
)
from sme_sigpae_api.perfil.models import Usuario

f = Faker("pt-br")
f.seed(420)
hoje = datetime.date.today() - datetime.timedelta(days=180)


def _get_random_cardapio(dias_pra_frente=None):
    if dias_pra_frente:
        hoje = datetime.date.today()
        prox_dias = hoje + datetime.timedelta(days=dias_pra_frente)
        return Cardapio.objects.filter(data__gte=prox_dias).order_by("?").first()
    return Cardapio.objects.order_by("?").first()


def _get_random_motivo_continuo():
    return MotivoInclusaoContinua.objects.order_by("?").first()


def _get_random_motivo_suspensao():
    return MotivoSuspensao.objects.order_by("?").first()


def _get_kit_lanches():
    return KitLanche.objects.all()


def _get_random_motivo_normal():
    return MotivoInclusaoNormal.objects.order_by("?").first()


def _get_random_motivo_altercao_cardapio():
    return MotivoAlteracaoCardapio.objects.order_by("?").first()


def _get_random_escola():
    return Escola.objects.filter(id__lte=2).order_by("?").first()


def _get_random_dre():
    return DiretoriaRegional.objects.filter(id__lte=2).order_by("?").first()


def _get_random_periodo_escolar():
    return PeriodoEscolar.objects.order_by("?").first()


def _get_random_tipos_alimentacao():
    num_alimentacoes = random.randint(2, 5)
    alimentacoes = []
    for i in range(num_alimentacoes):
        alim = TipoAlimentacao.objects.order_by("?").first()
        alimentacoes.append(alim)
    return alimentacoes


def fluxo_escola_felix(obj, user):  # noqa: C901
    # print(f'aplicando fluxo ESCOLA feliz em {obj}')
    obj.inicia_fluxo(user=user, notificar=True)
    if random.random() < 0.3:
        return

    if random.random() >= 0.1:
        obj.dre_valida(user=user, notificar=True)
        if random.random() >= 0.2:
            obj.codae_autoriza(user=user, notificar=True)
            if random.random() >= 0.3:
                obj.terceirizada_toma_ciencia(user=user, notificar=True)
                if random.random() >= 0.8:
                    try:
                        obj.cancelar_pedido(user=user)
                    except InvalidTransitionError:
                        return
        else:
            if random.random() <= 0.2:
                obj.codae_nega(user=user, notificar=True)
    else:
        if random.random() >= 0.1:
            obj.dre_pede_revisao(user=user, notificar=True)
        else:
            obj.dre_nao_valida(user=user, notificar=True)


def fluxo_informativo_felix(obj, user):
    obj.informa(user=user)
    if random.random() >= 0.5:
        obj.terceirizada_toma_ciencia(user=user)


def fluxo_dre_felix(obj, user):
    # print(f'aplicando fluxo DRE feliz em {obj}')
    obj.inicia_fluxo(user=user)
    if random.random() >= 0.1:
        obj.codae_autoriza(user=user, notificar=True)
        if random.random() >= 0.3:
            obj.terceirizada_toma_ciencia(user=user, notificar=True)
            if random.random() >= 0.8:
                try:
                    obj.cancelar_pedido(user=user)
                except InvalidTransitionError:
                    pass


def fluxo_escola_loop(obj, user):
    # print(f'aplicando fluxo loop revisao dre-escola em {obj}')
    obj.inicia_fluxo(user=user)
    obj.dre_pede_revisao(user=user)
    obj.escola_revisa(user=user)
    obj.dre_valida(user=user)


def cria_inclusoes_continuas(qtd=50):
    user = Usuario.objects.get(email="escola@admin.com")
    for i in range(qtd):
        try:
            inclusao_continua = InclusaoAlimentacaoContinua.objects.create(
                motivo=_get_random_motivo_continuo(),
                escola=_get_random_escola(),
                outro_motivo=f.text()[:20],
                observacao=f.text()[:20],
                descricao=f.text()[:160],
                criado_por=user,
                dias_semana=list(np.random.randint(6, size=4)),
                data_inicial=hoje + datetime.timedelta(days=random.randint(1, 180)),
                data_final=hoje + datetime.timedelta(days=random.randint(100, 200)),
            )

            QuantidadePorPeriodo.objects.create(
                periodo_escolar=_get_random_periodo_escolar(),
                numero_alunos=random.randint(10, 200),
                inclusao_alimentacao_continua=inclusao_continua,
            )
            # q.tipos_alimentacao.set(_get_random_tipos_alimentacao())

            fluxo_escola_felix(inclusao_continua, user)
        except InvalidTransitionError:
            pass


def cria_inclusoes_normais(qtd=50):
    user = Usuario.objects.get(email="escola@admin.com")
    for i in range(qtd):
        try:
            grupo_inclusao_normal = GrupoInclusaoAlimentacaoNormal.objects.create(
                descricao=f.text()[:160], criado_por=user, escola=_get_random_escola()
            )
            QuantidadePorPeriodo.objects.create(
                periodo_escolar=_get_random_periodo_escolar(),
                numero_alunos=random.randint(10, 200),
                grupo_inclusao_normal=grupo_inclusao_normal,
            )
            # q.tipos_alimentacao.set(_get_random_tipos_alimentacao())
            InclusaoAlimentacaoNormal.objects.create(
                motivo=_get_random_motivo_normal(),
                outro_motivo=f.text()[:40],
                grupo_inclusao=grupo_inclusao_normal,
                data=hoje + datetime.timedelta(days=random.randint(1, 180)),
            )
            fluxo_escola_felix(grupo_inclusao_normal, user)
        except InvalidTransitionError:
            pass


def cria_solicitacoes_kit_lanche_unificada(qtd=50):
    user = Usuario.objects.get(email="dre@admin.com")
    for i in range(qtd):
        try:
            base = SolicitacaoKitLanche.objects.create(
                data=hoje + datetime.timedelta(days=random.randint(1, 180)),
                motivo=f.text()[:40],
                descricao=f.text()[:160],
                tempo_passeio=SolicitacaoKitLanche.QUATRO,
            )
            kits = _get_kit_lanches()[:2]
            base.kits.set(kits)

            unificada = SolicitacaoKitLancheUnificada.objects.create(
                criado_por=user,
                outro_motivo=f.text()[:40],
                local=f.text()[:150],
                lista_kit_lanche_igual=True,
                diretoria_regional=_get_random_dre(),
                solicitacao_kit_lanche=base,
            )
            for _ in range(2, 5):
                EscolaQuantidade.objects.create(
                    quantidade_alunos=random.randint(10, 100),
                    solicitacao_unificada=unificada,
                    escola=_get_random_escola(),
                )

            fluxo_dre_felix(unificada, user)
        except InvalidTransitionError:
            pass


def cria_solicitacoes_kit_lanche_avulsa(qtd=50):
    user = Usuario.objects.get(email="escola@admin.com")
    for i in range(qtd):
        try:
            base = SolicitacaoKitLanche.objects.create(
                data=hoje + datetime.timedelta(days=random.randint(1, 180)),
                motivo=f.text()[:40],
                descricao=f.text()[:160],
                tempo_passeio=SolicitacaoKitLanche.QUATRO,
            )
            kits = _get_kit_lanches()[:2]
            base.kits.set(kits)
            avulsa = SolicitacaoKitLancheAvulsa.objects.create(
                criado_por=user,
                quantidade_alunos=random.randint(20, 200),
                local=f.text()[:150],
                escola=_get_random_escola(),
                solicitacao_kit_lanche=base,
            )
            fluxo_escola_felix(avulsa, user)
        except InvalidTransitionError:
            pass


def cria_inversoes_cardapio(qtd=50):
    user = Usuario.objects.get(email="escola@admin.com")
    for i in range(qtd):
        try:
            inversao = InversaoCardapio.objects.create(
                criado_por=user,
                observacao=f.text()[:100],
                motivo=f.text()[:40],
                escola=_get_random_escola(),
                cardapio_de=_get_random_cardapio(dias_pra_frente=1),
                cardapio_para=_get_random_cardapio(dias_pra_frente=10),
            )
            fluxo_escola_felix(inversao, user)
        except InvalidTransitionError:
            pass


def cria_suspensoes_alimentacao(qtd=50):
    user = Usuario.objects.get(email="escola@admin.com")
    for i in range(qtd):
        suspensao_grupo = GrupoSuspensaoAlimentacao.objects.create(
            criado_por=user,
            escola=_get_random_escola(),
        )
        for _ in range(random.randint(2, 5)):
            SuspensaoAlimentacao.objects.create(
                outro_motivo=f.text()[:50],
                grupo_suspensao=suspensao_grupo,
                data=hoje + datetime.timedelta(days=random.randint(1, 180)),
                motivo=_get_random_motivo_suspensao(),
            )
            QuantidadePorPeriodoSuspensaoAlimentacao.objects.create(
                numero_alunos=random.randint(100, 420),
                periodo_escolar=_get_random_periodo_escolar(),
                grupo_suspensao=suspensao_grupo,
            )
            # q.tipos_alimentacao.set(_get_random_tipos_alimentacao())
        fluxo_informativo_felix(suspensao_grupo, user)


def cria_alteracoes_cardapio(qtd=50):
    # TODO terminar os relacionamentos...
    user = Usuario.objects.get(email="escola@admin.com")
    for i in range(qtd):
        alteracao_cardapio = AlteracaoCardapio(
            data_inicial=hoje + datetime.timedelta(random.randint(1, 15)),
            data_final=hoje + datetime.timedelta(random.randint(16, 30)),
            criado_por=user,
            escola=_get_random_escola(),
            motivo=_get_random_motivo_altercao_cardapio(),
        )
        fluxo_escola_felix(alteracao_cardapio, user)


QTD_PEDIDOS = 50

print("-> criando inclusoes continuas")
cria_inclusoes_continuas(QTD_PEDIDOS)
print("-> criando inclusoes normais")
cria_inclusoes_normais(QTD_PEDIDOS)
print("-> criando solicicitacoes kit lanche avulsa")
cria_solicitacoes_kit_lanche_avulsa(QTD_PEDIDOS)
# print('-> criando inversoes de cardapio')
# cria_inversoes_cardapio(QTD_PEDIDOS)      # FIXME: ta dando problema
print("-> criando suspensoes alimentação")
cria_suspensoes_alimentacao(QTD_PEDIDOS)
print("-> criando alterações de cardapio")
cria_alteracoes_cardapio(QTD_PEDIDOS)

print("-> criando solicicitacoes kit lanche unificada")
cria_solicitacoes_kit_lanche_unificada(QTD_PEDIDOS)
